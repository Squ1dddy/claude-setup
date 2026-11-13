# claude-setup

A complete Claude Code setup: global rules, 53 skills, subagents, hooks, a status band mod, and a Brain memory vault (Obsidian + `brain.py`), packaged so another person's agent can install it.

## Quick start (for the person)
1. Clone this repo.
2. Open a terminal in the cloned folder and run `claude`.
3. Paste: `Read AGENTS.md and set this up for me, then brief me using BRIEFING.md.`

Your agent will ask a few questions, scan the skills, do a dry run, install (merging with anything you already have, with backups), interview you to personalise it, and then explain how it all works.

## Files
- [AGENTS.md](AGENTS.md): install brief for the agent.
- [BRIEFING.md](BRIEFING.md): how the agent explains the setup to you.
- [SKILLS.md](SKILLS.md): every skill, plus plugins to install from upstream.
- `install.py`: the installer (`--dry-run` first).
- `claude/`: everything that goes in `~/.claude`.
- `brain/`: an empty vault plus the memory engine.

No personal notes, credentials or history from the author are included.
