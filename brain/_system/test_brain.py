"""Regression tests for brain.py. Stdlib only; never touches the real vault's notes.

  python {{HOME}}\\Brain\\_system\\test_brain.py

Guard cases feed commands to `brain.py guard` (nothing is executed). Hook, session, lint and autocommit
run against a throwaway fixture vault in %TEMP% via the BRAIN_VAULT override.
"""
import datetime, json, os, shutil, subprocess, sys, tempfile, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRAIN = HERE / 'brain.py'
sys.path.insert(0, str(HERE))
import brain  # noqa: E402

V = str(brain.VAULT)                                  # works on any machine/username
VP = '/' + V[0].lower() + V[2:].replace('\\', '/')    # git-bash style: /c/Users/<name>/Brain
failures = []


def check(name, ok, detail=''):
    print(('ok    ' if ok else 'FAIL  ') + name + ('' if ok else f'  -> {detail}'))
    if not ok:
        failures.append(name)


def run(mode, payload, env=None, args=()):
    r = subprocess.run([sys.executable, str(BRAIN), mode, *args], input=json.dumps(payload), capture_output=True,
                       text=True, encoding='utf-8', env={**os.environ, **(env or {})})
    return r.returncode, r.stdout, r.stderr


# ---------- tokenizer ----------
for a, b in [('page', 'pages'), ('image', 'images'), ('share', 'shared'), ('bug', 'bugs'), ('stop', 'stopped'),
             ('class', 'classes'), ('library', 'libraries'), ('call', 'called'), ('window', 'windows')]:
    check(f'stem {a}/{b}', brain.tokens(a) == brain.tokens(b), (brain.tokens(a), brain.tokens(b)))
check('stopwords dropped after stemming', brain.tokens('changes updates running') == [], brain.tokens('changes updates running'))

# ---------- guard ----------
GUARD = [  # (command, cwd, should_block)
    (f'cat "{V}\\Projects\\Traksy.md"', 'C:/x', False),
    (f'python "{V}\\_system\\brain.py" delete "Runs/2026-09-30 smoke test"', 'C:/x', False),
    (f'rm "{V}\\Runs\\x.md"', 'C:/x', True),
    (f'cd {VP}/Projects && cat >> Traksy.md <<EOF\nhi\nEOF', 'C:/x', True),
    (f'python - <<EOF\np=r"{V}\\Projects\\Traksy.md"\ns=open(p).read()\nif len(s)>2: print(s)\nEOF', 'C:/x', False),
    (f'python - <<EOF\np=r"{V}\\Projects\\Traksy.md"\nopen(p,"w").write("x")\nEOF', 'C:/x', True),
    (f'Set-Content -Path "{V}\\Home.md" -Value x', 'C:/x', True),
    (f'Get-Content "{V}\\Home.md" -Encoding utf8', 'C:/x', False),
    (f'python {V}\\_system\\brain.py search "traksy" 2>&1 | head', 'C:/x', False),
    (f'git -C {V} log --oneline -5', 'C:/x', False),
    (f'git -C {V} reset --hard HEAD~1', 'C:/x', True),
    (f'grep -rn foo {VP} > /tmp/out.txt', 'C:/x', False),
    ('echo hi > Inbox/new.md', V, True),
    ('ls -la', V, False),
    (f'rm -rf {VP}/Inbox', 'C:/x', True),
    (f'sed -i s/a/b/ "{V}/Home.md"', 'C:/x', True),
    ('echo hi > notes.md', r'{{HOME}}\Projects\HSC PREPARATION', False),
    ('Remove-Item "{{HOME}}\\Projects\\HSC PREPARATION\\Brain\\x.md"', 'C:/x', False),
    ('npm run build > build.log', r'{{HOME}}\Desktop\AgenticOS\Traksy', False),
    (f"cd {VP} && git commit -q -F - <<'EOF'\nmsg\n\nCo-Authored-By: C <n@a.com>\nEOF", 'C:/x', False),
    (f"cat > {VP}/Inbox/x.md <<'EOF'\nhi\nEOF", 'C:/x', True),
    (f"python - <<'EOF'\nopen(r'{V}\\Home.md','a').write('x')\nEOF", 'C:/x', True),
    (f'true || echo x >> {VP}/Inbox/guard-test.md', 'C:/x', True),
]
for cmd, cwd, block in GUARD:
    code, _, err = run('guard', {'tool_input': {'command': cmd}, 'cwd': cwd})
    check(f'guard {"blocks" if block else "allows"}: {cmd.splitlines()[0][:70]}', (code == 2) == block, err[:120])

# ---------- resume age ----------
today = datetime.date(2026, 9, 21)
check('resume age from checkpoint date', brain.resume_age('## Resume\n_Checkpoint 2026-09-11 x_', today) == 10)
check('resume age none without date', brain.resume_age('## Resume\nno date', today) is None)

# ---------- fixture vault ----------
root = Path(tempfile.mkdtemp(prefix='brain-test-'))
fx, repo = root / 'vault', root / 'repo'
(repo / 'src').mkdir(parents=True)
old = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
now = datetime.date.today().isoformat()
NOTES = {
    'Profile.md': '---\ntype: profile\nsummary: who the user is, dev server rules\n---\n# Profile\n',
    'Projects/Alpha.md': f'---\ntype: project\nsummary: Alpha scoreboard app\ntags: [alpha]\nrepo: {repo}\n---\n# Alpha\n'
                         f'## Setup\nnpm stuff\n## Resume\n_Checkpoint {old}_\n- **Next:** ship the scoreboard\n'
                         f'## Resume: other-branch\n_Checkpoint {now}_\n- **Next:** unrelated\n',
    'Knowledge/Rules.md': '---\ntype: knowledge\nsummary: rules from incidents, each with the date and what broke\ntags: [rules, incidents]\n---\n# Rules\n'
                          + ''.join(f'## Rule {i}\nfiller text about topic{i}\n' for i in range(20))
                          + '## Never build while a dev server is running\nThe build overwrote .next and the server crashed.\n',
    'People/Bob.md': '---\ntype: person\nsummary: Bob handles all dev\n---\n# Bob\n',
    'Projects/Stacked.md': '---\ntype: project\nsummary: stacked history\nrepo: C:\\nope\\missing\n---\n# S\n'
                           '## STATUS: phase DONE\nx\n## Resume\n_a_\n## Resume\n_b_\n',
    'Projects/Alpha History.md': '---\ntype: archive\nsummary: Alpha scoreboard finished work history\n---\n# H\n'
                                 '## Done: scoreboard polish\nshipped the scoreboard polish\n',
    'Projects/NoFolder.md': '---\ntype: project\nsummary: a project with no code folder, used to test repo none\ntags: [nofolder, fixture]\nrepo: none\n---\n# N\n',
}
for rel, text in NOTES.items():
    (fx / rel).parent.mkdir(parents=True, exist_ok=True)
    (fx / rel).write_text(text, encoding='utf-8')
import socket  # noqa: E402
ENV = {'BRAIN_VAULT': str(fx), 'BRAIN_NO_AUTO_ARCHIVE': '1',    # the startup sweep would move fixture notes mid-test
       'BRAIN_ARCHIVE_HOST': socket.gethostname()}
sid = uuid.uuid4().hex

code, out, _ = run('hook', {'prompt': 'the dev server keeps crashing', 'session_id': sid, 'cwd': str(root)}, ENV)
check('hook points at the matching section', 'Knowledge/Rules.md:' in out and 'Never build' in out, out)
check('hook ignores a single common word (Bob "dev")', 'Bob' not in out, out)
check('hook skips Profile', 'Profile' not in out, out)
code, out2, _ = run('hook', {'prompt': 'the dev server keeps crashing', 'session_id': sid, 'cwd': str(root)}, ENV)
check('hook shows a pointer once per session', out2.strip() == '', out2)
code, out, _ = run('hook', {'prompt': 'alpha scoreboard polish history', 'session_id': uuid.uuid4().hex, 'cwd': str(root)}, ENV)
check('hook never pushes archive notes', 'History' not in out, out)
code, out, _ = run('hook', {'prompt': '<task-notification> dev server build crashing </task-notification>',
                            'session_id': uuid.uuid4().hex, 'cwd': str(root)}, ENV)
check('hook skips harness notices', out.strip() == '', out)
code, out, _ = run('search', {}, ENV, ('alpha', 'scoreboard', 'history'))
check('search hides archive notes but says they exist', 'Alpha History' in out and '1 archived match' in out
      and not any(l.strip().startswith(tuple('0123456789')) and 'History' in l for l in out.splitlines()), out)
code, out, _ = run('search', {}, ENV, ('alpha', 'scoreboard', 'history', '--all'))
check('search --all lists archive notes', 'Alpha History' in out and 'archived match' not in out, out)
blk = brain.resume_blocks({'body': '## Resume: feat/x  [checkpoint 2026-09-28 late]\n- a\n', 'offset': 0})
check('resume branch ignores a trailing [checkpoint] tag', blk and blk[0][1] == 'feat/x', blk)

code, out, _ = run('session', {'session_id': sid, 'cwd': str(repo / 'src'), 'source': 'startup'}, ENV)
ctx = json.loads(out)['hookSpecificOutput']['additionalContext'] if out.strip() else ''
check('session injects Resume for a folder inside repo', 'ship the scoreboard' in ctx, ctx)
check('session flags an old checkpoint', '30 days old' in ctx and 'verify harder' in ctx, ctx)
check('session lists other branches without injecting them', 'other-branch' in ctx and 'unrelated' not in ctx, ctx)
code, out, _ = run('session', {'session_id': sid, 'cwd': str(root), 'source': 'startup'}, ENV)
check('session silent outside any repo', out.strip() == '', out)
code, out, _ = run('session', {'session_id': sid, 'cwd': str(root), 'source': 'clear'}, ENV)
check('session adds RESUME CHECK on clear', 'RESUME CHECK' in out, out)

code, out, _ = run('lint', {}, ENV)
check('lint flags stacked STATUS heading', 'STATUS: phase DONE' in out, out)
check('lint flags duplicate Resume', '2 Resume sections' in out, out)
check('lint flags missing repo path', 'repo path missing' in out, out)
check('lint accepts repo: none', 'NoFolder.md: project note has no repo' not in out, out)
check('lint flags missing tags', 'Bob.md: 0 tags' in out, out)
check('lint flags a too-short summary', 'Bob.md: summary is' in out, out)
check('lint passes a long note that has ## headings', '"##" headings' not in out, out)
check('lint flags an orphan note', 'Projects/Alpha History.md: orphan' in out, out)
(fx / 'Knowledge/Dupe.md').write_text('---\ntype: knowledge\nsummary: a note whose tag near-duplicates rules\n'
                                      'tags: [rule, Bad_Tag, one]\n---\n# D\n## Notes\nx\n', encoding='utf-8')
code, _, err = run('check', {'tool_input': {'file_path': str(fx / 'Knowledge/Dupe.md')}}, ENV)
check('check blocks a note with near-duplicate, non-kebab tag and generic heading',
      code == 2 and 'near-duplicates' in err and 'not lowercase-kebab' in err and 'too generic' in err, err)
code, _, err = run('check', {'tool_input': {'file_path': str(fx / 'Projects/NoFolder.md')}}, ENV)
check('check passes a well-formed note', code == 0 and not err, err)
code, _, err = run('check', {'tool_input': {'file_path': str(root / 'elsewhere.md')}}, ENV)
check('check ignores files outside the vault', code == 0 and not err, err)
(fx / 'Knowledge/Dupe.md').unlink()

(fx / 'Knowledge/Linker.md').write_text('---\ntype: knowledge\nsummary: links bob\n---\n# L\nsee [[Bob]]\n', encoding='utf-8')
code, out, _ = run('delete', {}, ENV, ['Bob'])
check('delete refuses a linked note', code == 1 and 'linked from' in out and (fx / 'People/Bob.md').exists(), out)
code, out, _ = run('delete', {}, ENV, ['Nothing Here'])
check('delete refuses a non-exact name', code == 1 and (fx / 'Projects/NoFolder.md').exists(), out)
code, out, _ = run('delete', {}, ENV, ['Projects/NoFolder'])
check('delete removes an unlinked note by path', code == 0 and not (fx / 'Projects/NoFolder.md').exists(), out)

code, out, _ = run('show', {}, ENV, ['Rules', 'never build'])
check('show prints one section', out.startswith('Knowledge/Rules.md:') and 'overwrote .next' in out and 'topic3' not in out, out)

# ---------- section ----------
def cli(args, stdin=''):
    r = subprocess.run([sys.executable, str(BRAIN), *args], input=stdin, capture_output=True, text=True,
                       encoding='utf-8', env={**os.environ, **ENV})
    return r.returncode, r.stdout


SEC = fx / 'Projects/Sec.md'
SEC_TEXT = ('---\ntype: project\nsummary: section tests\nupdated: 2020-01-01\n---\n# Sec\n## Setup\nnpm i\n'
            '## Resume: feat/x  [checkpoint 2026-01-01]\n_Checkpoint 2026-01-01_\n### Detail\nold detail\n'
            '```\n## not a heading\n```\n- **Next:** old\n## Resume: other\n- **Next:** theirs\n## Open threads\n- a\n')
SEC.write_text(SEC_TEXT, encoding='utf-8')
code, out = cli(['section', 'Projects/Sec', 'Resume: feat/x'])
check('section read prints the section and mtime', code == 0 and out.startswith('Projects/Sec.md:9  mtime ')
      and 'old detail' in out and 'theirs' not in out, out)
mt = out.split('mtime ')[1].split('\n')[0]
code, out = cli(['section', 'Projects/Sec', 'Resume: feat/x', '--from', '-', '--mtime', mt],
                '_Checkpoint 2026-10-07_\n- **Next:** new\n')
txt = SEC.read_text(encoding='utf-8')
check('section replaces only its own section', code == 0 and '- **Next:** new' in txt and 'old detail' not in txt
      and '## not a heading' not in txt and '- **Next:** theirs' in txt and 'npm i' in txt and '## Open threads\n- a' in txt,
      out + txt)
check('section keeps one blank line before the next heading', '- **Next:** new\n\n## Resume: other' in txt, txt)
check('section bumps updated', f'updated: {datetime.date.today().isoformat()}' in txt, txt)
code, out = cli(['section', 'Projects/Sec', 'Resume: feat/x', '--from', '-', '--mtime', mt], '- **Next:** stale\n')
check('section refuses a stale mtime', code == 1 and 'changed since' in out and 'stale' not in SEC.read_text(encoding='utf-8'), out)
before = SEC.read_text(encoding='utf-8')
code, out = cli(['section', 'Projects/Sec', 'Resume: feat/x', '--from', '-'], '## Resume: other\n- hijack\n')
check('section refuses content for a different heading', code == 1 and SEC.read_text(encoding='utf-8') == before, out)
code, out = cli(['section', 'Projects/Sec', 'Resume: feat/x', '--from', '-'], '- a\n## Sneaky\n- b\n')
check('section refuses content that adds a heading', code == 1 and SEC.read_text(encoding='utf-8') == before, out)
code, out = cli(['section', 'Projects/Sec', 'Resume: feat/x', '--from', '-', '--dry-run'], '- dry\n')
check('section dry run writes nothing', code == 0 and 'dry run' in out and '+- dry' in out
      and SEC.read_text(encoding='utf-8') == before, out)
src = root / 'resume.md'
src.write_text('## Resume: feat/y  [checkpoint 2026-10-07]\n- **Next:** y\n', encoding='utf-8')
code, out = cli(['section', 'Sec', 'Resume: feat/y', '--from', str(src)])
txt = SEC.read_text(encoding='utf-8')
check('section appends a missing section from a file', code == 0 and 'appended' in out
      and txt.endswith('- a\n\n## Resume: feat/y  [checkpoint 2026-10-07]\n- **Next:** y\n'), out + txt)
code, out = cli(['section', 'Projects/Stacked', 'Resume', '--from', '-'], '- x\n')
check('section refuses duplicate sections', code == 1 and '2 sections match' in out, out)
code, out = cli(['section', 'Projects/Nope', 'Resume', '--from', '-'], '- x\n')
check('section refuses an unknown note', code == 1 and not (fx / 'Projects/Nope.md').exists(), out)
code, _, err = run('guard', {'tool_input': {'command': f'python "{V}\\_system\\brain.py" section "Projects/X" "Resume: b" '
                                                      "--from - <<'EOF'\n- rm old files, copy > new.md\nEOF"}, 'cwd': 'C:/x'})
check('guard allows brain.py section with a heredoc body', code == 0, err[:120])
code, _, err = run('guard', {'tool_input': {'command': f'python "{V}\\_system\\brain.py" section "Projects/X" "Resume" '
                                                      f"--from - <<'EOF'\n- x\nEOF\nrm \"{V}\\Home.md\""}, 'cwd': 'C:/x'})
check('guard still blocks a write chained after brain.py section', code == 2, err[:120])

git = lambda *a: subprocess.run(['git', '-C', str(fx), *a], capture_output=True, text=True)
git('init', '-q', '-b', 'main'); git('config', 'user.email', 't@t'); git('config', 'user.name', 't')
git('config', 'core.autocrlf', 'false'); git('add', '-A'); git('commit', '-qm', 'base')
run('autocommit', {'session_id': 'abcdef1234'}, ENV)
check('autocommit no-op when clean', git('log', '--oneline').stdout.count('\n') == 1)
(fx / 'Inbox').mkdir(exist_ok=True)
(fx / 'Inbox' / 'probe.md').write_text('x', encoding='utf-8')
run('autocommit', {'session_id': 'abcdef1234'}, ENV)
last = git('log', '-1', '--format=%s').stdout.strip()
check('autocommit commits changes', last == 'auto: probe [session abcdef12]' and not git('status', '--porcelain').stdout, last)

(fx / '.gitignore').write_text('.stversions/\n*.sync-conflict-*\n', encoding='utf-8')
(fx / '.stversions').mkdir(exist_ok=True)
(fx / '.stversions' / 'Old~20260101.md').write_text('x', encoding='utf-8')
git('add', '-f', '.stversions/Old~20260101.md'); git('add', '.gitignore'); git('commit', '-qm', 'tracked junk')
run('autocommit', {'session_id': 'abcdef1234'}, ENV)
check('autocommit untracks files .gitignore now covers', '.stversions/Old~20260101.md' not in git('ls-files').stdout
      and (fx / '.stversions' / 'Old~20260101.md').exists() and not git('status', '--porcelain').stdout, git('status', '--porcelain').stdout)

# ---------- aliases ----------
(fx / 'Knowledge/Exams.md').write_text('---\ntype: knowledge\nsummary: exam preparation schedule and past papers for Year 12\n'
                                       'tags: [exams, schedule]\naliases: [atar, "hsc rank"]\n---\n# Exams\n', encoding='utf-8')
code, out, _ = run('hook', {'prompt': 'what atar do I need for the cadetship', 'session_id': uuid.uuid4().hex, 'cwd': str(root)}, ENV)
check('hook matches a note by its alias', 'Knowledge/Exams.md' in out, out)
code, out = cli(['show', 'atar'])
check('show resolves an alias', 'Knowledge/Exams.md' in out, out)
(fx / 'Knowledge/Clash.md').write_text('---\ntype: knowledge\nsummary: a note whose alias clashes with another note name\n'
                                       'tags: [clash, fixture]\naliases: [Exams]\n---\n# Clash\n', encoding='utf-8')
code, out, _ = run('lint', {}, ENV)
check('lint flags an alias that clashes with a note name', 'Clash.md: alias "Exams"' in out, out)
(fx / 'Knowledge/Clash.md').unlink()

# ---------- index cache ----------
import hashlib  # noqa: E402
cache = Path(tempfile.gettempdir()) / f"brain-index-{hashlib.md5(str(fx).encode()).hexdigest()[:10]}.json"
run('search', {}, ENV, ('scoreboard',))
t0 = cache.stat().st_mtime_ns
run('search', {}, ENV, ('scoreboard',))
check('index cache is reused when no note changed', cache.exists() and cache.stat().st_mtime_ns == t0)
check('index cache dropped the deleted note', 'Projects/NoFolder.md' not in json.loads(cache.read_text(encoding='utf-8'))['notes'])
(fx / 'Knowledge/Rules.md').write_text((fx / 'Knowledge/Rules.md').read_text(encoding='utf-8') + 'zebracrossing happened\n', encoding='utf-8')
code, out, _ = run('search', {}, ENV, ('zebracrossing',))
check('edited note is re-indexed', 'Knowledge/Rules.md' in out and cache.stat().st_mtime_ns != t0, out)
cache.write_text('{not json', encoding='utf-8')
code, out, _ = run('search', {}, ENV, ('scoreboard',))
check('corrupt index cache is rebuilt', code == 0 and 'Alpha' in out, out)
cache.unlink(missing_ok=True)

# ---------- archive ----------
import time  # noqa: E402


def aged(path, days):
    ts = time.time() - days * 86400
    os.utime(path, (ts, ts))


def mk(rel, text, days=0):
    (fx / rel).parent.mkdir(parents=True, exist_ok=True)
    (fx / rel).write_text(text, encoding='utf-8')
    if days:
        aged(fx / rel, days)


RUN_FM = '---\ntype: run\nsummary: an auto-run note used by the archive tests\ntags: [run, fixture]\n---\n# Run\n'
mk('Runs/2026-01-01 old run.md', RUN_FM, 60)
mk(f'Runs/{now} new run.md', RUN_FM)
filler = '\n'.join(f'filler line {i}' for i in range(200))
BIG = ('---\ntype: knowledge\nsummary: an oversized note with old and new dated sections\ntags: [big, fixture]\n---\n# Big\n'
       f'## Setup\n{filler}\n## 2026-01-05 old experiment\nold details\n## {now} fresh experiment\nnew details\n'
       '## Resume: main\n_Checkpoint 2020-01-01_\n- **Next:** go\n')
mk('Knowledge/Big.md', BIG)
code, out = cli(['archive', '--auto', '--dry-run'])
check('archive dry run lists moves and writes nothing', code == 0 and 'old run' in out and 'Alpha History' in out and 'Big' in out
      and (fx / 'Runs/2026-01-01 old run.md').exists() and 'old experiment' in (fx / 'Knowledge/Big.md').read_text(encoding='utf-8'), out)
code, out = cli(['archive', '--auto'])
moved = fx / 'Archive/Runs/2026-01-01 old run.md'
check('auto-archive moves an old run, marks it archive and keeps what it was',
      code == 0 and moved.exists() and not (fx / 'Runs/2026-01-01 old run.md').exists()
      and all(s in moved.read_text(encoding='utf-8') for s in ('type: archive', 'was_type: run', 'archived: ')), out)
check('auto-archive leaves a recent run', (fx / f'Runs/{now} new run.md').exists(), out)
check('auto-archive sweeps an existing archive-type note into Archive/', (fx / 'Archive/Projects/Alpha History.md').exists()
      and not (fx / 'Projects/Alpha History.md').exists(), out)
big, hist = (fx / 'Knowledge/Big.md').read_text(encoding='utf-8'), fx / 'Archive/Knowledge/Big History.md'
check('roll-up moves only the old dated section', 'old details' not in big and 'fresh experiment' in big and '## Resume: main' in big
      and '## Setup' in big and '[[Big History]]' in big, big[-300:])
check('roll-up creates the History note in Archive/', hist.exists() and 'old details' in hist.read_text(encoding='utf-8')
      and 'type: archive' in hist.read_text(encoding='utf-8'), out)
code, _, err = run('check', {'tool_input': {'file_path': str(hist)}}, ENV)
check('a created History note passes the navigation check', code == 0 and not err, err)
code, out = cli(['archive', '--auto'])
check('auto-archive is idempotent', code == 0 and out.strip() == 'nothing to archive', out)
(fx / 'Knowledge/Big.md').write_text((fx / 'Knowledge/Big.md').read_text(encoding='utf-8') + '## 2026-01-06 second experiment\nsecond details\n', encoding='utf-8')
cli(['archive', '--auto'])
h = hist.read_text(encoding='utf-8')
check('a later roll-up lands above the older one in the existing History', 'second details' in h and h.index('second details') < h.index('old details'), h)
code, out = cli(['show', 'Alpha History'])
check('show still finds an archived note by name', 'Archive/Projects/Alpha History.md' in out, out)
code, out = cli(['archive', 'Knowledge/Linker'])
check('manual archive moves one note', code == 0 and (fx / 'Archive/Knowledge/Linker.md').exists(), out)
code, out = cli(['archive', 'Profile'])
check('manual archive refuses Profile', code == 1 and (fx / 'Profile.md').exists(), out)
mk('Runs/2026-01-02 second old run.md', RUN_FM, 60)
code, out, _ = run('session', {'session_id': uuid.uuid4().hex, 'cwd': str(root), 'source': 'startup'},
                   {**ENV, 'BRAIN_NO_AUTO_ARCHIVE': '', 'BRAIN_ARCHIVE_HOST': 'some-other-machine'})
check('auto-archive does not run on a machine that is not the archive host', (fx / 'Runs/2026-01-02 second old run.md').exists()
      and 'Auto-archive' not in out, out)
code, out, _ = run('session', {'session_id': uuid.uuid4().hex, 'cwd': str(root), 'source': 'startup'}, {**ENV, 'BRAIN_NO_AUTO_ARCHIVE': ''})
check('startup session auto-archives and says so', 'Auto-archive moved' in out and (fx / 'Archive/Runs/2026-01-02 second old run.md').exists(), out)
mk('Runs/2026-01-03 third old run.md', RUN_FM, 60)
code, out, _ = run('session', {'session_id': uuid.uuid4().hex, 'cwd': str(root), 'source': 'startup'}, {**ENV, 'BRAIN_NO_AUTO_ARCHIVE': ''})
check('auto-archive runs only once a day', (fx / 'Runs/2026-01-03 third old run.md').exists() and 'Auto-archive' not in out, out)

shutil.rmtree(root, ignore_errors=True)
print(f'\n{len(failures)} failure(s)' + (': ' + ', '.join(failures) if failures else ''))
sys.exit(1 if failures else 0)
