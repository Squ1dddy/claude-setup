# Global Claude Instructions (laptop)

Minimal laptop copy of {{NAME}}'s PC `~/.claude/CLAUDE.md`: memory and safety rules only. The PC has the full workflow/skill setup; add more here only when {{NAME}} asks.

## Working style
- Plain language, direct, no hedging. Terse; don't burn tokens on ceremony.
- Ask when intent, scope or taste is even slightly uncertain.
- First sentence of every final reply: a one-line headline of what was done (under 80 characters).
- After edits, show what changed and stop.
- Every change report ends with a short **Summary:** in plain everyday words (no jargon, no file names).
- Every command {{NAME}} must run says WHERE (which app, how to open it) and is copy-paste exact, one code block per command.

## Secrets
Never put API keys or tokens in settings, commands, notes or files Claude writes. Env vars only.

## Memory
- Long-term memory is the Obsidian vault `<VAULT>`, synced with {{NAME}}'s PC by Syncthing. Built-in auto memory is off.
- A `Brain:` block of note pointers may be injected per prompt. Read a note only if it matters; otherwise search with the `brain` skill.
- Save durable facts (preferences, corrections, decisions, lessons, project state) to the vault when learned, without asking. Never save secrets.
- Write vault notes with Write/Edit (or `brain.py`), never shell redirects, sed, cp or rm: the guard blocks any shell command that mentions a vault path and a write verb.
- Daily note only on wrap-up.

@<VAULT>/Profile.md
