#!/usr/bin/env python3
"""Install the claude-setup kit into ~/.claude and a Brain vault.

Safe by default:
  * never overwrites an existing file (reports it as a conflict instead; --overwrite backs up then replaces)
  * merges settings.json / settings.local.json (adds hooks, permissions, env, plugins; keeps your values)
  * backs up every settings file it touches to ~/.claude/backups/claude-setup-<timestamp>/
  * --dry-run prints everything it would do and changes nothing

Usage:
  python install.py --name "Sam" --dry-run
  python install.py --name "Sam"
Options: --vault PATH (default ~/Brain), --hostname NAME (default this machine), --skip-rtk, --overwrite
"""
import argparse, datetime, json, os, platform, shutil, socket, subprocess, sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
TEXT_EXT = {'.md', '.py', '.js', '.mjs', '.ts', '.tsx', '.json', '.sh', '.ps1', '.txt', '.yaml', '.yml', '.toml',
            '.html', '.css', '.cmd', '.template', ''}

ap = argparse.ArgumentParser()
ap.add_argument('--name', required=True, help="the person's first name, used in rules and notes")
ap.add_argument('--vault', default=str(Path.home() / 'Brain'))
ap.add_argument('--hostname', default=socket.gethostname())
ap.add_argument('--dry-run', action='store_true')
ap.add_argument('--overwrite', action='store_true')
ap.add_argument('--skip-rtk', action='store_true', help='leave out the rtk command-rewrite hook')
a = ap.parse_args()

HOME = Path.home()
CLAUDE = HOME / '.claude'
VAULT = Path(a.vault).expanduser().resolve()
fwd = lambda p: str(p).replace('\\', '/')
PY = 'python' if platform.system() == 'Windows' else 'python3'
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
BACKUP = CLAUDE / 'backups' / f'claude-setup-{STAMP}'
TOKENS = [('{{HOME}}/Brain', fwd(VAULT)), ('{{HOME}}\\\\Brain', fwd(VAULT)), ('{{HOME}}\\Brain', fwd(VAULT)),('{{HOME}}', fwd(HOME)), ('{{NAME}}', a.name),
          ('{{HOSTNAME}}', a.hostname.lower()), ('{{DATE}}', datetime.date.today().isoformat())]
report = {'installed': [], 'conflicts': [], 'skipped': [], 'notes': []}


def fill(text):
    for k, v in TOKENS:
        text = text.replace(k, v)
    return text


def read_kit(src):
    if src.suffix.lower() in TEXT_EXT:
        try:
            return fill(src.read_text(encoding='utf-8')).encode('utf-8')
        except UnicodeDecodeError:
            pass
    return src.read_bytes()


def backup(path):
    if path.exists() and not a.dry_run:
        dst = BACKUP / path.relative_to(HOME)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)


def put(src, dst):
    data = read_kit(src)
    if dst.exists():
        if dst.read_bytes() == data:
            return
        if not a.overwrite:
            report['conflicts'].append(fwd(dst))
            return
        backup(dst)
    report['installed'].append(fwd(dst))
    if not a.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        if src.suffix in ('.sh', '') and os.name != 'nt':
            dst.chmod(0o755)


def put_tree(src, dst):
    for p in sorted(src.rglob('*')):
        if p.is_file():
            put(p, dst / p.relative_to(src))


def load_json(p):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def merge_settings(template, target):
    t = json.loads(fill(template.read_text(encoding='utf-8')))
    s = load_json(target)
    before = json.dumps(s, sort_keys=True)
    for k, v in t.items():
        if k == 'hooks':
            hooks = s.setdefault('hooks', {})
            have = {h.get('command') for gs in hooks.values() for g in gs for h in g.get('hooks', [])}
            for ev, groups in v.items():
                for g in groups:
                    g = dict(g)
                    g['hooks'] = [h for h in g['hooks'] if h['command'] not in have and keep_hook(h['command'])]
                    if g['hooks']:
                        hooks.setdefault(ev, []).append(g)
        elif k == 'permissions':
            perms = s.setdefault('permissions', {})
            allow = perms.setdefault('allow', [])
            allow += [p for p in v.get('allow', []) if p not in allow]
        elif k == 'env':
            env = s.setdefault('env', {})
            for ek, ev_ in v.items():
                if ek == 'CLAUDE_CODE_PLUGIN_DIRS' and env.get(ek) and ev_ not in env[ek]:
                    env[ek] = env[ek] + os.pathsep + ev_
                else:
                    env.setdefault(ek, ev_)
        elif isinstance(v, dict):
            d = s.setdefault(k, {})
            for kk, vv in v.items():
                d.setdefault(kk, vv)
        else:
            s.setdefault(k, v)
    s = json.loads(json.dumps(s).replace('python \\"', f'{PY} \\"'))
    if json.dumps(s, sort_keys=True) != before:
        backup(target)
        report['installed'].append(f'{fwd(target)} (merged)')
        if not a.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(s, indent=2) + '\n', encoding='utf-8')


def keep_hook(cmd):
    if 'rtk-rewrite' in cmd and (a.skip_rtk or not shutil.which('rtk')):
        report['skipped'].append('rtk-rewrite hook (rtk not on PATH or --skip-rtk)')
        return False
    return True


# 1. ~/.claude content
c = KIT / 'claude'
for sub in ('agents', 'hooks', 'skills', 'mods', 'plugins'):
    put_tree(c / sub, CLAUDE / sub)

# 2. CLAUDE.md: install if absent, else drop next to it for the agent to merge
target = CLAUDE / 'CLAUDE.md'
if target.exists() and target.read_bytes() == read_kit(c / 'CLAUDE.md.template'):
    pass
elif target.exists():
    side = CLAUDE / 'CLAUDE.md.claude-setup'
    put(c / 'CLAUDE.md.template', side)
    report['notes'].append(f'Existing CLAUDE.md kept. Kit version written to {fwd(side)}: merge by hand.')
else:
    put(c / 'CLAUDE.md.template', target)

# 3. settings
merge_settings(c / 'settings.template.json', CLAUDE / 'settings.json')
merge_settings(c / 'settings.local.template.json', CLAUDE / 'settings.local.json')

# 4. Brain vault (only adds missing files)
put_tree(KIT / 'brain', VAULT)
if not (VAULT / '.git').exists():
    report['notes'].append(f'git init {fwd(VAULT)} (needed by the autocommit hook)')
    if not a.dry_run:
        VAULT.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'init', '-b', 'main', str(VAULT)], check=False)
        subprocess.run(['git', '-C', str(VAULT), 'config', 'core.autocrlf', 'false'], check=False)

# 5. prerequisites check
for tool in ('node', 'git', 'gh', PY, 'bash', 'rtk'):
    if not shutil.which(tool):
        report['notes'].append(f'missing on PATH: {tool}')

print(('DRY RUN - nothing written\n' if a.dry_run else '') + json.dumps(report, indent=2))
if not a.dry_run and BACKUP.exists():
    print(f'Backups: {fwd(BACKUP)}')
