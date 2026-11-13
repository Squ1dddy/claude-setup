"""Brain vault tool: search, hooks, show, section, backlinks, recent, lint, delete. Stdlib only.

  python brain.py search "query words" [-n 8] [--all]   # --all includes archived notes
  python brain.py archive "Folder/Note" | --auto [--dry-run]   # finished work -> Archive/ (auto runs daily at startup)
  python brain.py show "Note Name" [section words]   # resolve a [[link]]; long notes print an outline
  python brain.py section "Folder/Note" "Resume: branch" [--from FILE|- [--mtime N] [--dry-run]]
                                                     # print one section, or replace/append it (checkpoints)
  python brain.py backlinks "Note Name"
  python brain.py recent [-n 10]
  python brain.py lint

Hooks (read hook JSON on stdin; never block the session on error):
  hook        UserPromptSubmit: up to 3 note/section pointers, each shown once per session
  session     SessionStart: inject the Resume of the project note whose `repo:` contains the cwd
  guard       PreToolUse (Bash|PowerShell): refuse shell writes into the vault (use Edit/Write)
  autocommit  Stop (async): git-commit any vault changes so nothing is lost or clobbered silently
"""
import datetime, difflib, hashlib, json, math, os, re, socket, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

VAULT = Path(os.environ.get('BRAIN_VAULT') or Path(__file__).resolve().parent.parent)   # override: tests only
SKIP_DIRS = {'_system', '.obsidian', '.trash', '.git', '.stversions', '.stfolder'}   # .st*: Syncthing version copies
CONFLICT_MARK = '.sync-conflict-'            # Syncthing's copy of a note edited on two devices; never indexed, lint reports it
ARCHIVE_DIR = 'Archive'                      # finished work: never pushed, hidden from `search` unless --all
HOOK_SKIP_DIRS = {'Daily', ARCHIVE_DIR}      # dated logs are too noisy for auto-recall; archives are never pushed
ARCHIVE_HOST = os.environ.get('BRAIN_ARCHIVE_HOST', '{{HOSTNAME}}').lower()   # only this machine runs the daily sweep: Syncthing shares the vault, and two machines moving notes at once would collide
ARCHIVE_RUN_DAYS = 14                       # a Runs note untouched this long is finished
ARCHIVE_INBOX_DAYS = 30                      # an Inbox note untouched this long was never acted on
ARCHIVE_SECTION_DAYS = 21                    # a dated ## section this old moves to its note's History when the note is over the cap
HOOK_SKIP_NOTES = {'Profile.md', 'Home.md'}  # Profile is already loaded; Home is only an index
HOOK_SKIP_TYPES = {'archive', 'run'}              # finished-work history: reached by search/show, never pushed
HARNESS_NOTICE = re.compile(r'\s*(<task-notification|\[Cross-session (delivery|idle) notice\]|\[SYSTEM NOTIFICATION)')
HOOK_MIN_SCORE = 2.0
HOOK_MAX = 3
HOOK_SHORT = 6           # prompts with fewer informative words than this need a title/tag match or 3+ shared words
COMMON_DF = 0.5          # a term in more than half the notes can't justify a pointer on its own
LONG_NOTE = 40           # notes longer than this get section pointers and outlines
MAX_NOTE_BYTES = 12000   # reading a note whole costs bytes/4 tokens; 150 lines of 250 chars is 9k tokens
RESUME_CAP = 80         # max Resume lines injected at session start
STALE_DAYS = 7           # an older Resume gets a "verify harder" warning
FIELD_WEIGHT = {'title': 3.0, 'summary': 2.0, 'tags': 2.0, 'aliases': 2.0, 'body': 1.0}
META_FIELDS = ('title', 'summary', 'tags', 'aliases')   # a hit here is a deliberate label, unlike a body match
STOP = set('''a an and are as at be but by can could did do does for from get got had has have how i if in into is it its
just let like make me my need no not of on or our please so some than that the their them then there these they this to
up us was we what when where which who why will with would you your can't don't i'm it's im dont cant ok okay yeah
fix add build create use new update help want check run show change work look try thing stuff keep still
ask tell know whatever about all any also more something anything well brain'''.split())
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*$')
RESUME = re.compile(r'^##\s+Resume(?:\s*:\s*(.+?))?\s*$')

for stream in (sys.stdout, sys.stdin):
    try:
        stream.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ---------- text ----------

def stem(w):
    """Light, consistent stemmer: singular/plural and -ing/-ed forms of a word land on the same token."""
    if len(w) > 4 and w.endswith('ies'):
        w = w[:-3] + 'y'
    elif len(w) > 5 and w.endswith('ing'):
        w = w[:-3]
        if len(w) > 3 and w[-1] == w[-2] and w[-1] not in 'aeiouls':
            w = w[:-1]
    elif len(w) > 4 and w.endswith('ed') and not w.endswith('eed'):
        w = w[:-2]
        if len(w) > 3 and w[-1] == w[-2] and w[-1] not in 'aeiouls':
            w = w[:-1]
    elif len(w) > 3 and w.endswith('s') and not w.endswith(('ss', 'us', 'is')):
        w = w[:-1]
    if len(w) > 3 and w.endswith('e'):
        w = w[:-1]
    return w


STOP_STEMS = {stem(w) for w in STOP}


def tokens(text):
    out = []
    for w in re.findall(r"[a-z0-9][a-z0-9'_-]*", text.lower()):
        w = w.strip("'-_")
        if len(w) < 2 or w in STOP:
            continue
        w = stem(w)
        if len(w) < 2 or w in STOP_STEMS:
            continue
        out.append(w)
    return out


def norm_path(p):
    return re.sub(r'/+', '/', str(p).replace('\\', '/')).rstrip('/').lower()


# ---------- notes ----------

def parse(path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    meta, body, offset = {}, text, 0
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?', text, re.S)
    if m:
        body, offset = text[m.end():], text[:m.end()].count('\n')
        for ln in m.group(1).splitlines():
            if ':' in ln and not ln.startswith((' ', '-')):
                k, v = ln.split(':', 1)
                meta[k.strip()] = v.strip().strip('"\'')
    return meta, body, offset


def notes():
    for p in sorted(VAULT.rglob('*.md')):
        rel = p.relative_to(VAULT)
        if rel.parts[0] in SKIP_DIRS or CONFLICT_MARK in p.name:
            continue
        yield p, rel


def sync_conflicts():
    return [p.relative_to(VAULT).as_posix() for p in sorted(VAULT.rglob('*.md'))
            if CONFLICT_MARK in p.name and p.relative_to(VAULT).parts[0] not in SKIP_DIRS]


def sections(body, offset):
    """[(line_no 1-based in file, level, heading, text until the next heading)]."""
    out, cur = [], None
    for i, ln in enumerate(body.split('\n')):
        m = HEADING.match(ln)
        if m:
            if cur:
                out.append(cur)
            cur = [offset + i + 1, len(m.group(1)), m.group(2), []]
        elif cur:
            cur[3].append(ln)
    if cur:
        out.append(cur)
    return [(n, lvl, h, '\n'.join(t)) for n, lvl, h, t in out]


def repos(meta):
    return [norm_path(r.strip()) for r in meta.get('repo', '').split(';') if r.strip()]


class Doc(dict):
    """An indexed note. `body` loads on first use: most commands only need the cached token counts."""
    def __missing__(self, key):
        if key != 'body':
            raise KeyError(key)
        self['body'] = parse(self['path'])[1]
        return self['body']


def index_entry(p):
    """Everything build() needs from one note except its body text: meta plus per-field token counts."""
    meta, body, offset = parse(p)
    flat = lambda key: re.sub(r'[\[\],]', ' ', meta.get(key, ''))
    fields = {'title': tokens(p.stem), 'summary': tokens(meta.get('summary', '')), 'tags': tokens(flat('tags')),
              'aliases': tokens(flat('aliases')), 'body': tokens(body)}
    return {'meta': meta, 'offset': offset, 'lines': offset + body.count('\n') + 1,
            'fields': {k: dict(Counter(v)) for k, v in fields.items()}}


def index_file():
    return Path(tempfile.gettempdir()) / f"brain-index-{hashlib.md5(str(VAULT).encode()).hexdigest()[:10]}.json"


def code_sig():
    """Editing brain.py (stemmer, stop words, fields) invalidates every cached token count."""
    st = Path(__file__).stat()
    return [st.st_mtime_ns, st.st_size]


def load_index():
    try:
        data = json.loads(index_file().read_text(encoding='utf-8'))
        return data['notes'] if data.get('code') == code_sig() else {}
    except Exception:
        return {}


def save_index(entries):
    """Atomic, best effort: another session may write at the same time, and a lost write only costs a re-index."""
    try:
        fd, tmp = tempfile.mkstemp(dir=tempfile.gettempdir(), prefix='brain-index-', suffix='.tmp')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump({'code': code_sig(), 'notes': entries}, f, separators=(',', ':'))
        os.replace(tmp, index_file())
    except Exception:
        pass


def build(skip_top=(), skip_notes=()):
    """Per-note index, re-tokenizing only notes whose mtime or size changed since the cache was written."""
    cache, live = load_index(), list(notes())
    kept = {rel.as_posix() for _, rel in live}
    fresh = {k: v for k, v in cache.items() if k in kept}
    dirty = len(fresh) != len(cache)
    docs = []
    for p, rel in live:
        key = rel.as_posix()
        if rel.parts[0] in skip_top or key in skip_notes:
            continue
        st = p.stat()                    # stat before reading, so a write in between just re-indexes next time
        sig = [st.st_mtime_ns, st.st_size]
        e = fresh.get(key)
        if not e or e['sig'] != sig:
            e = fresh[key] = {**index_entry(p), 'sig': sig}
            dirty = True
        fields = {k: Counter(v) for k, v in e['fields'].items()}
        docs.append(Doc(path=p, rel=rel, meta=e['meta'], fields=fields, offset=e['offset'], lines=e['lines'],
                        len=sum(fields['body'].values()) + 1))
    if dirty:
        save_index(fresh)
    return docs


def search(query, n=8, skip_top=(), skip_notes=(), boost=None):
    """BM25 over title/summary/tags/body. Returns [(score, info, doc)]; info has matched/strong term sets + idf."""
    docs = build(skip_top, skip_notes)
    q = set(tokens(query))
    if not docs or not q:
        return []
    N, avg = len(docs), sum(d['len'] for d in docs) / len(docs)
    df = {t: sum(1 for d in docs if any(t in f for f in d['fields'].values())) for t in q}
    idf = {t: math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5)) for t in q if df[t]}
    k1, b = 1.2, 0.75
    results = []
    for d in docs:
        score, matched, strong = 0.0, set(), set()
        for t in idf:
            tf = sum(FIELD_WEIGHT[name] * f[t] for name, f in d['fields'].items())
            if not tf:
                continue
            if df[t] / N <= COMMON_DF:
                matched.add(t)
                if d['fields']['title'][t] or d['fields']['tags'][t] or d['fields']['aliases'][t]:
                    strong.add(t)
            score += idf[t] * tf * (k1 + 1) / (tf + k1 * (1 - b + b * d['len'] / avg))
        if boost and boost(d):
            score *= 1.5
        if score > 0:
            results.append((score, {'matched': matched, 'strong': strong, 'idf': idf}, d))
    results.sort(key=lambda r: -r[0])
    return results[:n]


def best_section(d, terms, idf):
    terms = (set(terms) - set(d['fields']['title'])) or set(terms)   # the title picked the note, not the section
    best, best_score = None, 0.0
    for line_no, _, heading, text in sections(d['body'], d['offset']):
        c, head = Counter(tokens(heading + '\n' + text)), set(tokens(heading))
        s = sum(idf.get(t, 0) * (min(c[t], 5) + 2 * (t in head)) for t in terms)
        if s > best_score:
            best, best_score = (line_no, heading), s
    return best


def line(d, where=None):
    loc = d['rel'].as_posix() + (f':{where[0]} ({where[1]})' if where else '')
    return f"{loc} | {d['meta'].get('summary', '(no summary)')}"


def read_hook_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def emit(event, text):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': event, 'additionalContext': text}}))


def state_file(session_id):
    return Path(tempfile.gettempdir()) / f"brain-hook-{re.sub(r'[^A-Za-z0-9_-]', '', session_id or 'default')}.json"


def load_shown(session_id):
    try:
        return set(json.loads(state_file(session_id).read_text(encoding='utf-8')))
    except Exception:
        return set()


def save_shown(session_id, shown):
    try:
        state_file(session_id).write_text(json.dumps(sorted(shown)), encoding='utf-8')
    except Exception:
        pass


def meta_hit(d, terms, idf):
    """True if a term is in the title, summary, tags or the best section's heading: a big note's body alone
    matches nearly any prompt."""
    if any(d['fields'][f][t] for t in terms for f in META_FIELDS):
        return True
    where = best_section(d, terms, idf) if d['lines'] > LONG_NOTE else None
    return bool(where and set(tokens(where[1])) & set(terms))


def cwd_matches(d, cwd):
    c = norm_path(cwd)
    return any(c == r or c.startswith(r + '/') for r in repos(d['meta']))


# ---------- commands ----------

def is_archived(d):
    return d['rel'].parts[0] == ARCHIVE_DIR or d['meta'].get('type') == 'archive'


def cmd_search(args):
    show_all = '--all' in args
    args = [a for a in args if a != '--all']
    n = int(args[args.index('-n') + 1]) if '-n' in args else 8
    query = ' '.join(a for i, a in enumerate(args) if a != '-n' and (i == 0 or args[i - 1] != '-n'))
    res = search(query, 40)
    live = [r for r in res if show_all or not is_archived(r[2])][:n]
    hidden = [r for r in res if is_archived(r[2])] if not show_all else []
    if not live:
        print('no matches')
    for score, info, d in live:
        where = best_section(d, info['matched'] or set(info['idf']), info['idf']) if d['lines'] > LONG_NOTE else None
        print(f'{score:5.1f}  {line(d, where)}')
    if hidden:
        print(f'+{len(hidden)} archived match(es), best: {hidden[0][2]["rel"].as_posix()} '
              '(search --all to list them, or show "<name>")')


def cmd_hook(_):
    inp = read_hook_input()
    prompt, sid, cwd = inp.get('prompt', ''), inp.get('session_id', ''), inp.get('cwd', '')
    prompt = re.sub(r'https?://\S+', ' ', prompt)    # a pasted link's host and path words match notes by chance
    if len(tokens(prompt)) < 2 or HARNESS_NOTICE.match(prompt):
        return
    res = search(prompt, 10, HOOK_SKIP_DIRS, HOOK_SKIP_NOTES, boost=(lambda d: cwd_matches(d, cwd)) if cwd else None)
    need = 2 if len(tokens(prompt)) >= HOOK_SHORT else 3   # a short prompt has few words to share, so weak overlap is likelier chance
    res = [r for r in res if r[0] >= HOOK_MIN_SCORE and r[2]['meta'].get('type') not in HOOK_SKIP_TYPES
           and (r[1]['strong'] or (len(r[1]['matched']) >= need and meta_hit(r[2], r[1]['matched'], r[1]['idf'])))]
    if not res:
        return
    top = res[0][0]
    shown, out = load_shown(sid), []
    for score, info, d in res[:HOOK_MAX]:      # rank-capped before dedupe, so repeats don't pull in weaker notes
        if score < top * 0.5:
            break
        where = best_section(d, info['matched'], info['idf']) if d['lines'] > LONG_NOTE else None
        key = d['rel'].as_posix() + (f':{where[0]}' if where else '')
        injected = d['rel'].as_posix() in shown      # the session hook already put this note's Resume in context
        if key in shown or (injected and (not where or where[1].lower().startswith('resume'))):
            continue
        shown.add(key)
        out.append('- ' + line(d, where))
    if not out:
        return
    save_shown(sid, shown)
    print('Brain (notes that may matter; read only if relevant. Paths are under ' + VAULT.as_posix() + '; '
          'path:N means the section starts at line N, so Read from offset N):')
    print('\n'.join(out))


def git_branch(cwd):
    try:
        r = subprocess.run(['git', '-C', cwd, 'rev-parse', '--abbrev-ref', 'HEAD'],
                           capture_output=True, text=True, timeout=2)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def resume_blocks(d):
    """[(line_no, branch_or_None, text)] for each `## Resume` / `## Resume: <branch>` section."""
    out, lines = [], d['body'].split('\n')
    for i, ln in enumerate(lines):
        m = RESUME.match(ln)
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not re.match(r'^#{1,2}\s', lines[j]):
            j += 1
        # branch names have no spaces, so drop any trailing "[checkpoint ...]" tag a session wrote into the heading
        branch = (m.group(1) or '').strip('` ').split(' ')[0].strip('` ') or None
        out.append((d['offset'] + i + 1, branch, '\n'.join(lines[i:j]).rstrip()))
    return out


def resume_age(text, today=None):
    """Days since the first YYYY-MM-DD date in a Resume (its `_Checkpoint <date>` line), or None."""
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if not m:
        return None
    try:
        return ((today or datetime.date.today()) - datetime.date(*map(int, m.groups()))).days
    except ValueError:
        return None


def cmd_session(_):
    inp = read_hook_input()
    sid, cwd, source = inp.get('session_id', ''), inp.get('cwd', ''), inp.get('source', 'startup')
    if source in ('clear', 'compact'):
        try:
            state_file(sid).unlink()
        except Exception:
            pass
    matches = [d for d in build() if d['meta'].get('type') == 'project' and cwd_matches(d, cwd)] if cwd else []
    parts = []
    moved = archive_due() if source == 'startup' else []
    if moved:
        parts.append('Auto-archive moved finished work out of the live notes (nothing deleted, git has it):\n- '
                     + '\n- '.join(moved[:8]) + (f'\n- ... +{len(moved) - 8} more' if len(moved) > 8 else ''))
    if source in ('clear', 'compact'):
        why = 'was just compacted (details were summarised away)' if source == 'compact' else 'was just cleared'
        parts.append(f'RESUME CHECK: this session {why}. Treat any summary or Resume below as a claim, not truth: '
                     'verify against git status and the files before continuing from "Next".')
    if matches:
        branch = git_branch(cwd)
        shown, plan = set(), []
        for d in sorted(matches, key=lambda d: -max(len(r) for r in repos(d['meta']))):
            blocks = resume_blocks(d)
            mine = [b for b in blocks if b[1] and branch and b[1].strip('` ').lower() == branch.lower()] \
                or [b for b in blocks if not b[1]]
            plan.append((d, blocks, mine))
        any_resume = any(mine for _, _, mine in plan)
        for d, blocks, mine in plan:
            rel = d['rel'].as_posix()
            shown.add(rel)
            others = [b for b in blocks if b not in mine]
            head = f"Brain project note for this folder: {rel} | {d['meta'].get('summary', '')}"
            if branch:
                head += f' (current branch: {branch})'
            parts.append(head)
            for ln, _, text in mine:
                body = text.split('\n')
                age = resume_age(text)
                if age is not None:     # own line, so a session copying the heading back doesn't copy the tag
                    body.insert(1, f'(checkpoint {age} day{"s" if age != 1 else ""} old' + (
                        ': state has likely moved on, verify harder before trusting it)' if age >= STALE_DAYS else ')'))
                if len(body) > RESUME_CAP:
                    body = body[:RESUME_CAP] + [f'... (truncated; read {rel} from line {ln + RESUME_CAP})']
                parts.append(f'{rel}:{ln}\n' + '\n'.join(body))
            if others:
                parts.append('Other Resume sections: ' + ', '.join(f'{rel}:{ln} ({br})' for ln, br, _ in others))
            if not mine and not any_resume:
                outline = [f'{n} {h}' for n, lvl, h, _ in sections(d['body'], d['offset']) if lvl == 2]
                if d['lines'] > LONG_NOTE and outline:
                    parts.append('No Resume for this branch. Sections by line (read only what the task needs): '
                                 + '; '.join(outline))
                else:
                    parts.append(f'No Resume; the note is {d["lines"]} lines, read it if the task needs project context.')
        save_shown(sid, load_shown(sid) | shown)
    elif source in ('clear', 'compact'):
        parts.append('If the user continues project work, find its note with '
                     f'python {VAULT}\\_system\\brain.py search "<project>" and read its Resume.')
    if parts:
        emit('SessionStart', '\n\n'.join(parts))


# ---------- guard: shell commands that touch the vault and write ----------

VAULT_TAIL = '/'.join(norm_path(VAULT).split('/')[-3:])   # e.g. users/<name>/brain
VAULT_REFS = (VAULT_TAIL, '~/brain', '$home/brain', '$env:userprofile/brain', '%userprofile%/brain')
WRITE_VERBS = re.compile(
    r"(?:^|[\s;|&(])(?:tee|rm|rmdir|mv|cp|del|erase|ren|rename|move|copy|truncate|touch|mkdir|ni|ri|mi|ci|"
    r"set-content|add-content|out-file|clear-content|remove-item|move-item|copy-item|new-item|rename-item|sc|ac)"
    r"(?=[\s;|&)]|$)"
    r"|sed\s+(?:-[a-z]*\s+)*-i|\.write_text\(|\.write_bytes\(|\.write\(|writealltext|writealllines|appendalltext|"
    r"\bopen\([^)]*,\s*['\"][wax]|os\.remove|os\.rename|os\.replace|shutil\.|unlink\(|writefilesync|appendfilesync|"
    r"fs\.write|fs\.rename|fs\.unlink|fs\.rm")
REDIRECT = re.compile(r"(?<![-=<>0-9&])>{1,2}(?![=&>])\s*(['\"]?)([^\s'\";|&)]+)")
GIT_DESTRUCTIVE = re.compile(r'\bgit\b[^;&|]*\s(?:rm|clean|reset\s+--hard|checkout\s+--|restore|stash|filter-branch)\b')
SAFE_SINKS = ('/dev/null', '$null', 'nul')


def strip_heredocs(c):
    """Drop heredoc bodies: text like `<a@b.com>` inside them is data, not a redirect."""
    out, lines, i = [], c.split('\n'), 0
    while i < len(lines):
        out.append(lines[i])
        delims = re.findall(r"<<-?\s*['\"]?([\w.-]+)['\"]?", lines[i])
        i += 1
        for dl in delims:
            while i < len(lines) and lines[i].strip() != dl:
                i += 1
            i += 1
    return '\n'.join(out)


def in_vault(target, relative_is_vault):
    t = norm_path(target)
    if any(r in t for r in VAULT_REFS):
        return True
    return relative_is_vault and not re.match(r'^([a-z]:|/|~|\$)', t)


def guard_reason(cmd, cwd):
    c = norm_path(cmd)
    cwd_in = bool(cwd) and (norm_path(cwd) + '/').startswith(norm_path(VAULT) + '/')
    cds_in = bool(re.search(r'(?:^|[\s;&|(])(?:cd|set-location|pushd|sl)\s+["\']?[^;&|]*' + re.escape(VAULT_TAIL), c))
    if not (cwd_in or any(r in c for r in VAULT_REFS)):
        return None
    for _, target in REDIRECT.findall(strip_heredocs(c)):
        if target not in SAFE_SINKS and in_vault(target, cwd_in or cds_in):
            return f'redirect into the vault ({target})'
    if GIT_DESTRUCTIVE.search(c):
        return 'destructive git command in the vault'
    if re.match(r'^\s*git\b', c) and not re.search(r'[;&|]', c):
        return None
    bare = strip_heredocs(c)   # a lone `brain.py section` call: its heredoc is note text (data), not code
    if re.match(r'^\s*(?:python3?|py)\s+["\']?[^"\'\s]*/_system/brain\.py["\']?\s+section\s', bare) \
            and not re.search(r'[;&|`\n]|\$\(', bare.strip()):
        return None
    m = WRITE_VERBS.search(c)
    if m:
        return f'write/move/delete ({m.group(0).strip()}) in a command that touches the vault'
    return None


def cmd_guard(_):
    inp = read_hook_input()
    reason = guard_reason((inp.get('tool_input') or {}).get('command', ''), inp.get('cwd', ''))
    if not reason:
        return
    sys.stderr.write(
        f'BRAIN GUARD: blocked shell {reason}. Vault notes ({VAULT}) are shared by every session, so '
        'write them only with the Edit tool (or Write for a brand-new note): Edit refuses when another session changed '
        'the file since you read it, shell writes clobber silently. Delete a note with `brain.py delete "Folder/Note"`; '
        'renames/moves: ask {{NAME}} to do them in Obsidian (keeps links working). Reading is fine; if this was a read the guard misjudged, use the Read tool '
        'or brain.py show instead.\n')
    sys.exit(2)


def git(*args, timeout=10):
    return subprocess.run(['git', '-C', str(VAULT), *args], capture_output=True, text=True, timeout=timeout)


def cmd_autocommit(_):
    inp = read_hook_input()
    if not (VAULT / '.git').exists() or (VAULT / '.git' / 'index.lock').exists():
        return
    stale = git('ls-files', '-ci', '--exclude-standard').stdout.splitlines()   # tracked before .gitignore covered them
    if stale:
        git('rm', '-r', '--cached', '-q', '--ignore-unmatch', '--', *stale)   # index only: files stay on disk, history keeps them
    status = git('status', '--porcelain', '-uall').stdout.splitlines()   # -uall: name notes, not new folders
    if not status:
        return
    names = [Path(s[3:].strip().strip('"')).stem for s in status][:3]
    more = f' +{len(status) - 3}' if len(status) > 3 else ''
    sid = (inp.get('session_id') or 'manual')[:8]
    if git('add', '-A').returncode == 0:
        git('commit', '-q', '-m', f"auto: {', '.join(names)}{more} [session {sid}]")


def resolve(name):
    target = name.strip().strip('[]').split('|')[0].split('#')[0].removesuffix('.md').replace('\\', '/').lower()
    all_notes = list(notes())
    for p, rel in all_notes:
        if rel.as_posix().lower().removesuffix('.md') == target or p.stem.lower() == target:
            return p, rel
    part = [(p, rel) for p, rel in all_notes if target in p.stem.lower()]
    if len(part) == 1:
        return part[0]
    by_alias = [(p, rel) for p, rel in all_notes if target in (a.lower() for a in inline_list(parse(p)[0], 'aliases'))]
    if len(by_alias) == 1:
        return by_alias[0]
    res = search(name, 1)
    return (res[0][2]['path'], res[0][2]['rel']) if res else (None, None)


def cmd_show(args):
    if not args:
        print('usage: brain.py show "Note Name" [section words]'); return
    p, rel = resolve(args[0])
    if not p:
        print(f'no note matches "{args[0]}"'); return
    meta, body, offset = parse(p)
    text = p.read_text(encoding='utf-8', errors='ignore')
    secs = sections(body, offset)
    if len(args) > 1:
        want = set(tokens(' '.join(args[1:])))
        scored = [(len(want & set(tokens(h))), -n, n, lvl) for n, lvl, h, _ in secs]
        scored = [s for s in scored if s[0]]
        if not scored:
            print(f'{rel.as_posix()}: no heading matches; sections:')
            for n, lvl, h, _ in secs:
                print(f'  {n:4}  {"  " * (lvl - 1)}{h}')
            return
        _, _, start, lvl = max(scored)
        lines = text.split('\n')
        end = next((n - 1 for n, l2, _, _ in secs if n > start and l2 <= lvl), len(lines))
        print(f'{rel.as_posix()}:{start}')
        print('\n'.join(lines[start - 1:end]).rstrip())
        return
    total = text.count('\n') + 1
    if total <= 80:
        print(f'{rel.as_posix()}\n{text.rstrip()}')
        return
    print(f"{rel.as_posix()} | {meta.get('summary', '')}  ({total} lines; outline only)")
    for n, lvl, h, _ in secs:
        print(f'  {n:4}  {"  " * (lvl - 1)}{h}')
    print(f'Read one section: brain.py show "{p.stem}" <heading words>')


def exact_note(name):
    """(path, rel) for an exact vault-relative path or exact note name, else (None, hit count)."""
    target = name.strip().strip('[]').removesuffix('.md').replace('\\', '/').lower()
    hits = [(p, rel) for p, rel in notes() if rel.as_posix().lower().removesuffix('.md') == target]
    hits = hits or [(p, rel) for p, rel in notes() if p.stem.lower() == target]
    return hits[0] if len(hits) == 1 else (None, len(hits))


def heading_key(h):
    """Comparable form of a heading: Resume headings compare by branch (ignoring a trailing tag), others by text."""
    m = RESUME.match('## ' + h.strip())
    if m:
        branch = (m.group(1) or '').strip('` ').split(' ')[0].strip('` ').lower()
        return ('resume', branch)
    return ('text', re.sub(r'\s+', ' ', h.strip()).lower())


def replace_section(text, level, heading, new_block):
    """Replace the `level` heading matching `heading` (up to the next heading of that level or higher) with
    new_block, or append new_block if there is none. Returns (new_text, start_line or None, old_block).
    Raises ValueError when more than one section matches. Headings inside ``` fences don't count."""
    lines, key, hits, fence = text.split('\n'), heading_key(heading), [], False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith('```'):
            fence = not fence
        m = None if fence else HEADING.match(ln)
        if m and len(m.group(1)) == level and heading_key(m.group(2)) == key:
            hits.append(i)
    if len(hits) > 1:
        raise ValueError(f'{len(hits)} sections match (lines {", ".join(str(i + 1) for i in hits)}); merge them with Edit first')
    new = new_block.rstrip('\n').split('\n')
    if not hits:
        body = text.rstrip('\n').split('\n')
        return '\n'.join(body + [''] + new) + '\n', None, ''
    start, end, fence = hits[0], len(lines), False
    for j in range(start + 1, len(lines)):
        if lines[j].lstrip().startswith('```'):
            fence = not fence
        m = None if fence else HEADING.match(lines[j])
        if m and len(m.group(1)) <= level:
            end = j
            break
    old = '\n'.join(lines[start:end]).rstrip('\n')
    tail = lines[end:]
    return '\n'.join(lines[:start] + new + ([''] if tail else []) + tail).rstrip('\n') + '\n', start + 1, old


def cmd_section(args):
    """Read or replace one section of a note. Safe, guard-friendly way to rewrite a `## Resume: <branch>`."""
    usage = ('usage: brain.py section "Folder/Note" "Heading" [--from FILE|-] [--mtime N] [--dry-run]\n'
             '  no --from: print the section and the note mtime (pass it back as --mtime when writing)\n'
             '  --from: replace that section (or append it) with FILE / stdin; content may start with the heading line\n'
             '  heading "Resume: feat/x" matches by branch; prefix #s ("### Foo") for a level other than 2')
    flags = {'--from': None, '--mtime': None}
    pos, dry, i = [], False, 0
    while i < len(args):
        if args[i] in flags and i + 1 < len(args):
            flags[args[i]] = args[i + 1]; i += 2
        elif args[i] == '--dry-run':
            dry = True; i += 1
        else:
            pos.append(args[i]); i += 1
    if len(pos) != 2:
        print(usage); sys.exit(1)
    p, rel = exact_note(pos[0])
    if not p:
        print(f'refused: {rel} notes match "{pos[0]}" exactly; give the vault-relative path'); sys.exit(1)
    hm = re.match(r'^(#{1,6})\s+(.*)$', pos[1].strip())
    level, heading = (len(hm.group(1)), hm.group(2)) if hm else (2, pos[1].strip())
    raw = p.read_bytes().decode('utf-8')
    crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n')
    mtime = p.stat().st_mtime
    if flags['--from'] is None:
        try:
            _, start, old = replace_section(text, level, heading, '')
        except ValueError as e:
            print(f'refused: {e}'); sys.exit(1)
        print(f'{rel.as_posix()}:{start}  mtime {mtime!r}\n{old}' if start else
              f'{rel.as_posix()}: no "{"#" * level} {heading}" section (writing one appends it)  mtime {mtime!r}')
        return
    if flags['--mtime'] is not None and abs(float(flags['--mtime']) - mtime) > 1e-6:
        print(f'refused: {rel.as_posix()} changed since mtime {flags["--mtime"]} (now {mtime!r}); re-read it and redo '
              'your section from the current text'); sys.exit(1)
    src = sys.stdin.read() if flags['--from'] == '-' else Path(flags['--from']).read_text(encoding='utf-8')
    src = src.replace('\r\n', '\n').strip('\n')
    if not src.strip():
        print('refused: new section is empty'); sys.exit(1)
    first = HEADING.match(src.split('\n')[0])
    if first:
        if len(first.group(1)) != level or heading_key(first.group(2)) != heading_key(heading):
            print(f'refused: content starts with "{src.split(chr(10))[0]}", not the "{"#" * level} {heading}" heading')
            sys.exit(1)
    else:
        src = f'{"#" * level} {heading}\n{src}'
    if re.search(r'^#{1,%d}\s' % level, '\n'.join(src.split('\n')[1:]), re.M):
        print(f'refused: content has its own level-1..{level} heading, which would split it into several sections')
        sys.exit(1)
    try:
        new, start, old = replace_section(text, level, heading, src)
    except ValueError as e:
        print(f'refused: {e}'); sys.exit(1)
    fm = re.match(r'---\n.*?\n---\n', new, re.S)
    if fm:   # bump `updated:` if the note has one
        head = re.sub(r'^updated:.*$', f'updated: {datetime.date.today().isoformat()}', fm.group(0), count=1, flags=re.M)
        new = head + new[fm.end():]
    diff = list(difflib.unified_diff(old.split('\n') if old else [], src.split('\n'), lineterm='', n=0))
    plus = sum(1 for d in diff if d.startswith('+') and not d.startswith('+++'))
    minus = sum(1 for d in diff if d.startswith('-') and not d.startswith('---'))
    what = f'replaced line {start}' if start else 'appended'
    summary = f'{rel.as_posix()}: {what} "{src.split(chr(10))[0]}" ({len(old.split(chr(10))) if old else 0} -> ' \
              f'{len(src.split(chr(10)))} lines, +{plus} -{minus})'
    if dry:
        print('dry run, nothing written\n' + summary + '\n' + '\n'.join(diff[2:]))
        return
    if crlf:
        new = new.replace('\n', '\r\n')
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix='.section-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(new.encode('utf-8'))
        if p.stat().st_mtime != mtime:
            raise RuntimeError('note changed while writing')
        os.replace(tmp, p)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    print(summary)


def cmd_backlinks(args):
    target = ' '.join(args).strip().removesuffix('.md').lower()
    pat = re.compile(r'\[\[([^\]|#]+)')
    hits = [rel.as_posix() for p, rel in notes()
            if any(m.strip().lower() == target for m in pat.findall(p.read_text(encoding='utf-8', errors='ignore')))]
    print('\n'.join(hits) or 'no backlinks')


def cmd_delete(args):
    """Delete one note by exact path or name. Refuses notes other notes link to; git keeps it recoverable."""
    if len(args) != 1:
        print('usage: brain.py delete "Folder/Note" (exact path or exact note name, one note)'); sys.exit(1)
    if args[0] in sync_conflicts():           # Syncthing conflict copies are not indexed notes, so exact_note can't see them
        (VAULT / args[0]).unlink()
        print(f'deleted {args[0]} (conflict copy; the Stop hook commits it)'); return
    p, rel = exact_note(args[0])
    if not p:
        print(f'refused: {rel} notes match "{args[0]}" exactly; give the vault-relative path'); sys.exit(1)
    if rel.as_posix() in ('Profile.md', 'Home.md'):
        print(f'refused: {rel.as_posix()} is core; edit it instead'); sys.exit(1)
    pat = re.compile(r'\[\[([^\]|#]+)')
    linked = [r.as_posix() for q, r in notes() if q != p and any(
        m.strip().lower() in (p.stem.lower(), rel.as_posix().lower().removesuffix('.md'))
        for m in pat.findall(q.read_text(encoding='utf-8', errors='ignore')))]
    if linked:
        print(f'refused: linked from {", ".join(linked)}; remove or repoint those links first'); sys.exit(1)
    p.unlink()
    print(f'deleted {rel.as_posix()} (the Stop hook commits it; recover with git -C "{VAULT}" log --diff-filter=D)')


# ---------- archive: finished work moves out of the live notes, nothing is deleted ----------

DATE = re.compile(r'(\d{4})-(\d{2})-(\d{2})')


def first_date(text):
    m = DATE.search(text)
    try:
        return datetime.date(*map(int, m.groups())) if m else None
    except ValueError:
        return None


def read_text(p):
    """(text with \\n newlines, was_crlf, mtime): the mtime lets a later write detect another session's edit."""
    mtime = p.stat().st_mtime
    raw = p.read_bytes().decode('utf-8')
    return raw.replace('\r\n', '\n'), '\r\n' in raw, mtime


def write_text(p, text, crlf=False, mtime=None):
    """Atomic write (temp file + replace); refuses if p changed since `mtime`, like `section`."""
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix='.archive-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write((text.replace('\n', '\r\n') if crlf else text).encode('utf-8'))
        if mtime is not None and p.stat().st_mtime != mtime:
            raise RuntimeError(f'{p.name} changed while archiving; try again')
        os.replace(tmp, p)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def bump_updated(text, today):
    fm = re.match(r'---\n.*?\n---\n', text, re.S)
    if not fm:
        return text
    return re.sub(r'^updated:.*$', f'updated: {today.isoformat()}', fm.group(0), count=1, flags=re.M) + text[fm.end():]


def level2_blocks(lines):
    """[(start, end, heading)] line indexes of each `## ` section; headings inside ``` fences don't count."""
    out, fence, cur = [], False, None
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith('```'):
            fence = not fence
        m = None if fence else HEADING.match(ln)
        if m and len(m.group(1)) <= 2:
            if cur:
                out.append((cur[0], i, cur[1]))
            cur = (i, m.group(2)) if len(m.group(1)) == 2 else None
    if cur:
        out.append((cur[0], len(lines), cur[1]))
    return out


def move_note(p, rel, today, dry):
    """Move one note to Archive/<same path> and mark it type: archive. Name links ([[Note]]) keep working
    because Obsidian and brain.py resolve by name; path-style links would break, so those refuse."""
    dst = VAULT / ARCHIVE_DIR / rel
    if dst.exists():
        raise ValueError(f'{dst.relative_to(VAULT).as_posix()} already exists')
    path_link = rel.as_posix().removesuffix('.md').lower()
    users = [r.as_posix() for q, r in notes() if q != p and f'[[{path_link}' in q.read_text(encoding='utf-8', errors='ignore').lower()]
    if users:
        raise ValueError(f'linked by path from {", ".join(users)}; use the plain name in those links first')
    text, crlf, mtime = read_text(p)
    fm = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not fm:
        raise ValueError('no frontmatter')
    head, old = fm.group(1), re.search(r'^type:\s*(.*?)\s*$', fm.group(1), re.M)
    if old and old.group(1) != 'archive':
        head = re.sub(r'^type:.*$', 'type: archive', head, count=1, flags=re.M) + f'\nwas_type: {old.group(1)}'
    elif not old:
        head += '\ntype: archive'
    if not re.search(r'^archived:', head, re.M):
        head += f'\narchived: {today.isoformat()}'
    msg = f'{rel.as_posix()} -> {ARCHIVE_DIR}/{rel.as_posix()}'
    if dry:
        return msg
    dst.parent.mkdir(parents=True, exist_ok=True)
    write_text(dst, f'---\n{head}\n---\n' + text[fm.end():], crlf)
    if p.stat().st_mtime != mtime:
        dst.unlink()
        raise RuntimeError(f'{rel.as_posix()} changed while archiving; try again')
    p.unlink()
    return msg


def old_sections(lines, today):
    """Level-2 sections whose first heading date is over ARCHIVE_SECTION_DAYS old. Resume and undated stay."""
    out = []
    for start, end, heading in level2_blocks(lines):
        d = first_date(heading)
        if d and not RESUME.match('## ' + heading) and (today - d).days >= ARCHIVE_SECTION_DAYS:
            out.append((start, end, heading))
    return out


def roll_up(p, rel, today, dry):
    """Move a note's old dated sections into `<Note> History` (created in Archive/ if missing); None if nothing to move."""
    text, crlf, mtime = read_text(p)
    lines = text.split('\n')
    old = old_sections(lines, today)
    if not old:
        return None
    name = f'{p.stem} History'
    msg = f'{rel.as_posix()}: {len(old)} section(s) -> {name} (' + '; '.join(h[:40] for _, _, h in old) + ')'
    if dry:
        return msg
    blocks = ['\n'.join(lines[s:e]).rstrip('\n') for s, e, _ in old]
    hp, hits = exact_note(name)
    if hp is None and hits:
        raise ValueError(f'{hits} notes are named "{name}"; rename or merge them first')
    if hp is None:
        tags = [t for t in tag_list(parse(p)[0]) if t != 'history'][:6] or [re.sub(r'[^a-z0-9]+', '-', p.stem.lower()).strip('-')]
        hp = VAULT / ARCHIVE_DIR / rel.parent / f'{name}.md'
        hp.parent.mkdir(parents=True, exist_ok=True)
        write_text(hp, f'---\ntype: archive\nsummary: Finished work moved out of {p.stem} by brain.py archive, newest first; '
                       f'{p.stem} itself keeps only the current state\ntags: [{", ".join(tags + ["history"])}]\n'
                       f'updated: {today.isoformat()}\n---\n# {name}\nMoved here from [[{p.stem}]] once over '
                       f'{ARCHIVE_SECTION_DAYS} days old.\n\n' + '\n\n'.join(blocks) + '\n')
    else:
        htext, hcrlf, hmtime = read_text(hp)
        hl = htext.split('\n')
        first = next(iter(level2_blocks(hl)), None)
        if first:
            new = '\n'.join(hl[:first[0]]) + '\n' + '\n\n'.join(blocks) + '\n\n' + '\n'.join(hl[first[0]:])
        else:
            new = htext.rstrip('\n') + '\n\n' + '\n\n'.join(blocks) + '\n'
        write_text(hp, bump_updated(new, today), hcrlf, hmtime)
    drop = {i for s, e, _ in old for i in range(s, e)}     # the History copy is written first: a failure here duplicates, never loses
    new = '\n'.join(ln for i, ln in enumerate(lines) if i not in drop).rstrip('\n') + '\n'
    if f'[[{name.lower()}' not in new.lower():
        new += f'\n_Older finished work: [[{name}]]._\n'
    write_text(p, bump_updated(new, today), crlf, mtime)
    return msg


def note_age(p, today):
    """Days since the later of the date in the file name and the file's last edit."""
    stamps = [datetime.date.fromtimestamp(p.stat().st_mtime), first_date(p.stem)]
    return (today - max(s for s in stamps if s)).days


def auto_archive(today, dry):
    """One sweep: finished notes into Archive/, old dated sections of oversized notes into their History.
    Returns a message per action; a failing item is reported and skipped, never fatal."""
    msgs = []
    for p, rel in list(notes()):
        top, meta = rel.parts[0], parse(p)[0]
        if rel.as_posix() in HOOK_SKIP_NOTES or top in ('Daily', ARCHIVE_DIR):
            continue
        try:
            if meta.get('type') == 'archive':
                msgs.append(move_note(p, rel, today, dry))
            elif top == 'Runs' and meta.get('type') == 'run' and note_age(p, today) >= ARCHIVE_RUN_DAYS:
                msgs.append(move_note(p, rel, today, dry))
            elif top == 'Inbox' and note_age(p, today) >= ARCHIVE_INBOX_DAYS:
                msgs.append(move_note(p, rel, today, dry))
            elif meta.get('type') in ('project', 'knowledge') and (p.stat().st_size > MAX_NOTE_BYTES
                                                                   or p.read_bytes().count(b'\n') > 150):
                m = roll_up(p, rel, today, dry)
                if m:
                    msgs.append(m)
        except Exception as e:
            msgs.append(f'skipped {rel.as_posix()}: {e}')
    return msgs


def archive_due():
    """Run the sweep at most once a day, from the first startup session. Never raises."""
    marker = Path(tempfile.gettempdir()) / f"brain-archive-{hashlib.md5(str(VAULT).encode()).hexdigest()[:10]}.txt"
    today = datetime.date.today()
    try:
        if os.environ.get('BRAIN_NO_AUTO_ARCHIVE') or socket.gethostname().lower() != ARCHIVE_HOST \
                or (marker.exists() and marker.read_text() == today.isoformat()):
            return []
        marker.write_text(today.isoformat())     # claim the day first, so two sessions starting together don't both sweep
        return auto_archive(today, False)
    except Exception:
        return []


def cmd_archive(args):
    usage = ('usage: brain.py archive "Folder/Note"        move one finished note to Archive/ (type: archive)\n'
             '       brain.py archive --auto [--dry-run]   sweep: old Runs/Inbox notes and any archive-type note into Archive/,\n'
             f'                                             old dated sections of oversized notes into "<Note> History"')
    dry = '--dry-run' in args
    rest = [a for a in args if a != '--dry-run']
    today = datetime.date.today()
    if rest == ['--auto']:
        out = auto_archive(today, dry)
        print(('dry run, nothing written\n' if dry else '') + ('\n'.join(out) or 'nothing to archive'))
        return
    if len(rest) != 1:
        print(usage); sys.exit(1)
    p, rel = exact_note(rest[0])
    if not p:
        print(f'refused: {rel} notes match "{rest[0]}" exactly; give the vault-relative path'); sys.exit(1)
    if rel.as_posix() in HOOK_SKIP_NOTES or rel.parts[0] == ARCHIVE_DIR:
        print(f'refused: {rel.as_posix()} is core or already archived'); sys.exit(1)
    try:
        print(('dry run: ' if dry else 'archived ') + move_note(p, rel, today, dry) + ('' if dry else ' (the Stop hook commits it)'))
    except (ValueError, RuntimeError) as e:
        print(f'refused: {e}'); sys.exit(1)


def cmd_recent(args):
    n = int(args[args.index('-n') + 1]) if '-n' in args else 10
    items = sorted(notes(), key=lambda x: -x[0].stat().st_mtime)[:n]
    for p, rel in items:
        print(line({'rel': rel, 'meta': parse(p)[0]}))


def branch_exists(repo, branch):
    try:
        r = subprocess.run(['git', '-C', repo, 'branch', '-a', '--list', branch, f'*/{branch}'],
                           capture_output=True, text=True, timeout=3)
        return r.returncode != 0 or bool(r.stdout.strip())
    except Exception:
        return True


NAV_EXEMPT = {'Daily'}                      # dated logs: not navigated by topic
TAG_OK = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


def inline_list(meta, key):
    m = re.match(r'^\[(.*)\]$', meta.get(key, '').strip())
    return [t.strip().strip('"\'') for t in m.group(1).split(',') if t.strip()] if m else []


def tag_list(meta):
    return inline_list(meta, 'tags')


def tag_key(t):
    k = t.replace('-', '')
    return k[:-1] if k.endswith('s') and len(k) > 3 else k


def nav_issues(d, vocab):
    """Navigation quality: what the per-prompt hook and `show` rank and jump on (summary, tags, headings)."""
    meta, out = d['meta'], []
    if d['rel'].parts[0] in NAV_EXEMPT or d['rel'].as_posix() in HOOK_SKIP_NOTES:
        return out
    summ = meta.get('summary', '')
    if summ and not 40 <= len(summ) <= 300:
        out.append(f'summary is {len(summ)} chars; aim for 40-300, one specific line naming the concrete things in it')
    tags = tag_list(meta)
    if not 2 <= len(tags) <= 8:
        out.append(f'{len(tags)} tags (need an inline list [a, b] of 2-8): lowercase-kebab nouns someone would search for')
    for t in tags:
        if not TAG_OK.match(t):
            out.append(f'tag "{t}" is not lowercase-kebab')
        for other, n in vocab.items():
            if other != t and tag_key(other) == tag_key(t) and n >= vocab.get(t, 0):
                out.append(f'tag "{t}" near-duplicates existing tag "{other}" ({n} notes); reuse that one')
                break
    if meta.get('aliases', '').strip() and not 1 <= len(inline_list(meta, 'aliases')) <= 10:
        out.append('aliases must be an inline list [a, b] of 1-10 other names someone would search by (e.g. [atar, hsc-rank])')
    h2 = [h for _, lvl, h, _ in sections(d['body'], d['offset']) if lvl == 2]
    if d['lines'] > 40 and len(h2) < 2 and meta.get('type') != 'archive':
        out.append(f'{d["lines"]} lines but {len(h2)} "##" headings; add descriptive ## sections so show/hook can jump to the right part')
    for h in h2:
        if re.fullmatch(r'(notes?|misc|other|stuff|info|details|todo|more)', h.strip(), re.I):
            out.append(f'heading "## {h}" is too generic to navigate by; name what the section holds')
    return out


def tag_vocab(docs):
    return Counter(t for d in docs if d['rel'].parts[0] not in NAV_EXEMPT for t in tag_list(d['meta']))


def cmd_check(args):
    """PostToolUse hook (or `brain.py check <file>`): lint one vault note right after it is written."""
    inp = read_hook_input()
    fp = (inp.get('tool_input') or {}).get('file_path') or (args[0] if args else '')
    try:
        target = Path(fp).resolve()
        rel = target.relative_to(VAULT.resolve())
    except Exception:
        return
    if target.suffix != '.md' or rel.parts[0] in SKIP_DIRS or not target.exists():
        return
    docs = build()
    mine = next((d for d in docs if d['path'].resolve() == target), None)
    if not mine:
        return
    issues = nav_issues(mine, tag_vocab([d for d in docs if d is not mine]))
    if issues:
        sys.stderr.write(f'BRAIN CHECK {rel.as_posix()}: fix so search and show can navigate this note:\n- '
                         + '\n- '.join(issues) + '\nSee Knowledge/Vault Writing Guide.md "Navigation quality".\n')
        sys.exit(2)


def cmd_lint(_):
    names = {p.stem.lower() for p, _ in notes()}
    problems = 0

    def warn(rel, msg):
        nonlocal problems
        print(f'{rel}: {msg}')
        problems += 1

    for rel in sync_conflicts():
        warn(rel, 'Syncthing conflict copy: merge anything wanted into the real note, then delete this file')
    docs = build()
    vocab = tag_vocab(docs)
    linked ={m.strip().lower() for d in docs for m in re.findall(r'\[\[([^\]|#]+)', d['body'])}
    for d in docs:
        rel, meta, body = d['rel'].as_posix(), d['meta'], d['body']
        for msg in nav_issues(d, vocab):
            warn(rel, msg)
        for a in inline_list(meta, 'aliases'):
            if a.lower() in names or any(a.lower() == b.lower() for o in docs if o is not d for b in inline_list(o['meta'], 'aliases')):
                warn(rel, f'alias "{a}" is already another note\'s name or alias; aliases must be unique so [[links]] and show resolve')
        if d['rel'].parts[0] in ('Knowledge', 'Projects', 'People') and d['path'].stem.lower() not in linked:
            warn(rel, 'orphan: no note links to it; add it to Home or its parent note so it can be navigated to')
        clean = re.sub(r'<!--.*?-->|```.*?```|`[^`\n]*`', '', body, flags=re.S)
        for key in ('type', 'summary'):
            if not meta.get(key):
                warn(rel, f'missing {key}')
        for link in re.findall(r'\[\[([^\]|#]+)', clean):
            if link.strip().lower() not in names:
                warn(rel, f'broken link [[{link}]]')
        if d['rel'].parts[0] != 'Daily' and meta.get('type') != 'archive' and d['lines'] > 150:
            warn(rel, f'{d["lines"]} lines, over 150: split it or cut history')
        size = len(d['path'].read_bytes())
        if d['rel'].parts[0] != 'Daily' and meta.get('type') not in ('archive', 'run') and size > MAX_NOTE_BYTES:
            warn(rel, f'{size // 1024} KB (about {size // 4000}k tokens to read whole), over {MAX_NOTE_BYTES // 1000} KB: '
                      'split by topic or move finished history to an archive note; lines count less than bytes')
        for n, _, h, _ in sections(body, d['offset']):
            if re.search(r'\bSTATUS\b', h) or re.search(r'superseded|\bupdate:|\bstatus:', h, re.I):
                warn(rel, f'line {n} heading "{h}" looks like stacked history; keep one current state')
        blocks = resume_blocks(d)
        for br, k in Counter((br or '').strip('` ').lower() for _, br, _ in blocks).items():
            if k > 1:
                warn(rel, f'{k} Resume sections for "{br or "(no branch)"}"; replace, don\'t append')
        if meta.get('type') == 'project':
            rs = [r.strip() for r in meta.get('repo', '').split(';') if r.strip() and r.strip().lower() != 'none']
            if not meta.get('repo', '').strip():
                warn(rel, 'project note has no repo: field (use "repo: none" if it has no folder), so the session '
                          'hook can\'t match it to a folder')
            for r in rs:
                if not Path(r).exists():
                    warn(rel, f'repo path missing on disk: {r}')
            for ln, br, _ in blocks:
                if br and rs and (Path(rs[0]) / '.git').exists() and not branch_exists(rs[0], br.strip('` ')):
                    warn(rel, f'line {ln} Resume for branch "{br}" but that branch no longer exists; collapse it')
    profile = VAULT / 'Profile.md'
    if profile.exists():
        plines = profile.read_text(encoding='utf-8').splitlines()
        if len(plines) > 45:
            warn('Profile.md', 'over 45 lines, it loads every session; trim it')
        projects = {p.stem.lower() for p, rel in notes() if rel.parts[0] == 'Projects'}
        for n, ln in enumerate(plines, 1):
            linked = {x.strip().lower() for x in re.findall(r'\[\[([^\]|#]+)', ln)}
            if len(ln) > 200 and linked & projects:
                warn('Profile.md', f'line {n} carries project detail ({len(ln)} chars); keep a one-line pointer '
                                   'and move the detail to the project note')
    print(f'{problems} problem(s)')


if __name__ == '__main__':
    cmds = {'search': cmd_search, 'hook': cmd_hook, 'session': cmd_session, 'guard': cmd_guard,
            'autocommit': cmd_autocommit, 'show': cmd_show, 'backlinks': cmd_backlinks, 'recent': cmd_recent,
            'lint': cmd_lint, 'check': cmd_check, 'delete': cmd_delete, 'section': cmd_section, 'archive': cmd_archive}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(1)
    try:
        cmds[sys.argv[1]](sys.argv[2:])
    except SystemExit:
        raise
    except Exception:
        if sys.argv[1] in ('hook', 'session', 'guard', 'autocommit'):
            sys.exit(0)     # never break a session over a vault tool bug
        raise
