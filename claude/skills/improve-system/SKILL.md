---
name: improve-system
description: Mine {{NAME}}'s recent Claude Code session transcripts for repeated mistakes, missing context, skill candidates and automation candidates, then propose fixes. Use when {{NAME}} says /improve-system, "improve my setup", "what am I doing wrong with Claude", or "what skills should I build".
---

# Improve system

Turn recent sessions into concrete setup improvements. Transcripts stay on this machine: never send their contents to a web service, MCP connector or subagent.

## 1. Build the digest

```bash
python ~/.claude/skills/improve-system/digest.py --days 7 --out "<scratchpad>/digest.md"
```

Use `--days 14` if {{NAME}} asks for a wider window. The script keeps only what {{NAME}} typed plus friction signals and redacts secret-shaped strings. If the digest is over ~150 KB, rerun with fewer days rather than reading part of it.

## 2. Load what already exists

Before suggesting anything, check it isn't already covered:
- `~/.claude/CLAUDE.md` and `Brain/Profile.md` (already in context)
- `ls ~/.claude/skills` and the skill list in context
- `Brain/Knowledge/Working Rules Learned.md` and `Brain/Knowledge/Claude Code Setup.md`

## 3. Analyse

Read the digest and find, with evidence (session id + short quote):

1. **Repeated Claude mistakes**: the same correction 2+ times. Fix = a rule in CLAUDE.md, Profile, Working Rules Learned, or a skill tweak. Name the exact file and line to add.
2. **Missing context**: things {{NAME}} re-explains across sessions (project facts, preferences, paths). Fix = a Brain note or CLAUDE.md line.
3. **Skill candidates**: a multi-step workflow {{NAME}} asked for 2+ times in different sessions that no existing skill covers.
4. **Automation candidates**: recurring manual jobs that could be a scheduled task, a hook, or a script. Estimate time saved per week only from what the digest shows.
5. **Friction**: recurring tool errors and permission denials that a safe permission rule or setup fix would remove (never propose widening Claude's own access; list it for {{NAME}} to decide).
6. **{{NAME}}'s habits**: prompts that caused rework (vague scope, missing acceptance criteria). Be direct, one line each.

Drop anything seen only once. No padding: an empty section says "nothing found".

## 4. Report

Write the report to `Brain/Inbox/Improve System YYYY-MM-DD.md` (create the folder if missing) and show a short version in chat: a ranked top 5 by impact, each with evidence, the fix, and effort (S/M/L). End with a **Summary:** in plain words.

## 5. Act only on his yes

Ask which items to apply. Then:
- Rules and context: edit the named file.
- New skill: draft it with `writing-for-agents` conventions in `~/.claude/skills/<name>/`, show it, and wait for "lock it".
- Automation: draft the hook or scheduled task, show it, wait for approval.

Durable lessons he confirms go to Brain per the vault guide.
