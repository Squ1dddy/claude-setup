# AGENTS.md: install brief for the agent setting this up

You are a Claude Code agent. Your user's friend (the kit's author) packaged their whole Claude Code setup here so your user can run Claude Code the same way. Your job has two parts:

1. **Install it** into your user's machine, safely, merged with whatever they already have.
2. **Brief your user** on how it all works, using [BRIEFING.md](BRIEFING.md).

Read this file fully, then [SKILLS.md](SKILLS.md), then skim [claude/CLAUDE.md.template](claude/CLAUDE.md.template) and [brain/Knowledge/Vault Writing Guide.md](brain/Knowledge/Vault%20Writing%20Guide.md). Those two are the heart of the setup.

## What is in the kit

| Path | Goes to | What it is |
|---|---|---|
| `claude/CLAUDE.md.template` | `~/.claude/CLAUDE.md` | Global rules: the workflow (grill, spec, tickets, implement, verify, checkpoint), Opus-leads/Sonnet-builds, Brain memory rules, secrets, frontend and tool rules. |
| `claude/settings.template.json` | merged into `~/.claude/settings.json` | Hooks, permission allowlist, model defaults (`opus`, effort `high`, `autoMemoryEnabled: false`), plugins, marketplaces, the env var that loads the status mod. |
| `claude/settings.local.template.json` | merged into `~/.claude/settings.local.json` | The impeccable design-check hook after Edit/Write. |
| `claude/agents/` | `~/.claude/agents/` | `sonnet-coder` (builder subagent), `council-advisor`, four impeccable helpers. |
| `claude/skills/` | `~/.claude/skills/` | 53 skills, see SKILLS.md. |
| `claude/hooks/` | `~/.claude/hooks/` | `context-guard.js` (checkpoint nudge past 150k tokens), `rtk-rewrite.sh` (rewrites shell commands through `rtk` to save tokens), caveman hooks (unused unless the caveman plugin is turned on). |
| `claude/mods/checkpoint-band/` | `~/.claude/mods/checkpoint-band/` | **The status mod.** A band above the prompt in the terminal UI: context size and %, plan usage limits, time since the last Brain save, the current project's Resume "Next" line. Loaded through `CLAUDE_CODE_PLUGIN_DIRS`. This is the live status display; `statusLine` is intentionally unset. |
| `claude/plugins/claude-hud/` | `~/.claude/plugins/claude-hud/` | Optional older statusline (ships disabled). To use it instead: enable `claude-hud@claude-hud` and set `"statusLine": {"type": "command", "command": "node \"~/.claude/plugins/claude-hud/statusline.mjs\""}` with the real home path. |
| `brain/` | `~/Brain` (the vault) | An empty Obsidian vault plus `_system/brain.py`, the memory engine. No personal notes from the author are included. |
| `install.py` | run it | Copies and merges everything above, fills placeholders. |

Placeholders filled by `install.py`: `{{HOME}}` (home dir, forward slashes), `{{NAME}}` (your user's first name), `{{HOSTNAME}}` (this machine, used by brain.py's daily archive sweep), `{{DATE}}`. Left for you to fill during the interview: `{{ABOUT}}` and `{{PRIORITIES}}` in `Profile.md`.

Mentions of projects like Traksy in a few skills (code-video template, security-checklist, web-visual-fx) are the author's examples. Leave them or swap them for your user's projects.

## Install steps

Do these in order. Ask your user before anything that is hard to undo.

1. **Ask first:** their OS, their first name, where they want the vault (default `~/Brain`), and whether they already use Claude Code with their own `CLAUDE.md`, hooks or skills.
2. **Prerequisites.** Check and help install what is missing: `git`, `node` (18+), Python 3.10+, `gh` (optional), Obsidian (optional, for browsing the vault), `bash` (on Windows: Git for Windows provides it). Optional: `rtk` for the token-saving hook, `uv` for SkillSpector.
3. **Scan before installing.** The setup's own rule: every skill/plugin gets scanned before install. Run SkillSpector (see SKILLS.md) on `claude/skills/<name>` one skill at a time, or at least read the scripts in skills that ship code (`impeccable/scripts`, `anatomy`, `code-video`, `agent-reach`, `skill-inspector`). Tell your user the verdict. Note: `impeccable/scripts/bin/windows-x64/impeccable.exe` is a bundled binary (upstream impeccable engine v0.1.5). On macOS/Linux reinstall impeccable from upstream instead.
4. **Dry run:** `python install.py --name "<Name>" --vault "<path>" --dry-run`. Read the report: `installed`, `conflicts` (files that already exist and differ; never overwritten unless `--overwrite`, which backs them up first), `skipped`, `notes`.
5. **Install:** same command without `--dry-run`. It backs up every settings file it touches to `~/.claude/backups/claude-setup-<timestamp>/`, merges settings (adds hooks/permissions/env, keeps the user's existing values such as `model`), and `git init`s the vault (the autocommit hook needs git).
6. **CLAUDE.md:** if your user had one, the kit's version is at `~/.claude/CLAUDE.md.claude-setup`. Merge the two with them, section by section. Keep the `@<vault>/Profile.md` import line at the bottom.
7. **Plugins:** install the ones in SKILLS.md that your user wants: `claude plugin marketplace add <owner/repo>` then `claude plugin install <name>@<marketplace>`. For `claude-seo` and `floorplan`, clone the repo at the pinned commit into `~/.claude/vendor/<name>` and add it as a directory marketplace. Add context7 MCP if they want library-docs lookup.
8. **Interview and personalise.** Read [BRIEFING.md](BRIEFING.md) "Interview" and fill `Profile.md` About/Priorities, then walk the Working preferences list and keep, change or drop each one. `Knowledge/Style.md` is the author's reply style (lean and direct, plus an "explain mode"): ask if your user wants it as is.
9. **Verify** (show your user the output):
   - `python <vault>/_system/test_brain.py` ends with `0 failure(s)`.
   - `python <vault>/_system/brain.py lint` ends with `0 problem(s)`.
   - Start a new `claude` session in a terminal: the checkpoint band shows above the prompt; a prompt that mentions something in the vault gets a `Brain:` pointer block.
   - `/skills` (or the skill list) shows the kit skills.
10. **Record it:** fill `Knowledge/Claude Code Setup.md` in the vault (date, what was installed, what was skipped and why).
11. **Brief your user** using BRIEFING.md.

## Platform notes

- The author runs Windows 11 with PowerShell as the main shell and Git Bash for the Bash tool. Hook commands use `python`; on macOS/Linux the installer writes `python3`.
- `brain.py guard` blocks shell commands that write inside the vault (`rm`, `>`, `sed -i`, `cp` ...) if the command mentions a vault path. Notes are edited only with Claude's Edit/Write tools. That is intentional: it keeps concurrent sessions from clobbering notes.
- `brain.py` runs its archive sweep only on the machine named by `BRAIN_ARCHIVE_HOST` (the installer sets it to this machine). Set `BRAIN_NO_AUTO_ARCHIVE=1` to turn it off.
- `checkpoint-band` reads the vault at the path written into `mods/checkpoint-band/hooks/register.tsx` (`const BRAIN = ...`). If you move the vault, update it.
- The mod uses Claude Code's terminal mod API; it shows in the CLI, not in the desktop app.
- `CLAUDE_CODE_SUBAGENT_MODEL` is set to `opus`. The `sonnet-coder` agent pins itself to Sonnet in its own frontmatter.

## Rules you must keep while installing

- Never copy secrets into settings, commands or notes. API keys go in user env vars that your user sets themselves.
- Never overwrite your user's existing files without asking. The installer will not; neither should you.
- Do not run install scripts inside skills during review.
- Report what you skipped and why.
