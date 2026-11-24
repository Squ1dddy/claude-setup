# claude-setup

A complete Claude Code setup: global rules, 53 skills, subagents, hooks, a status band mod, and a Brain memory vault (Obsidian + `brain.py`), packaged so another person's agent can install it.

## Quick start (for the person)
1. Install Claude Code and sign in.
2. Open Claude Code in any empty folder and paste this one message:

   `Clone https://github.com/Squ1dddy/claude-setup into a temp folder, read its AGENTS.md and set it up for me, then brief me using BRIEFING.md.`

That is all you do. Your agent runs every command itself. It only stops for things it cannot do, such as signing in or an admin prompt.

Your agent will ask a few questions, scan the skills, do a dry run, install (merging with anything you already have, with backups), interview you to personalise it, and then explain how it all works.

## Updating
Already installed? Paste this to your agent:

`Pull the latest https://github.com/Squ1dddy/claude-setup into a temp folder and update my setup from it, following the "Updating an existing install" section of AGENTS.md. Then show me what is new.`

It updates your files (with backups), shows you the feature guide and what changed once, and then stays quiet until the next version.

## Files
- [AGENTS.md](AGENTS.md): install and update brief for the agent.
- [WHATS-NEW.md](WHATS-NEW.md): every feature, when to use it, and what changed in this version.
- [BRIEFING.md](BRIEFING.md): how the agent explains the setup to you.
- [SKILLS.md](SKILLS.md): every skill, plus plugins to install from upstream.
- `install.py`: the installer (`--dry-run` first).
- `claude/`: everything that goes in `~/.claude`.
- `brain/`: an empty vault plus the memory engine.

No personal notes, credentials or history from the author are included.
