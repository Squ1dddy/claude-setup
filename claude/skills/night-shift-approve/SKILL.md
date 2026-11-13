---
name: night-shift-approve
description: Act on {{NAME}}'s picks from a Night Shift review - "approve 1, 2b" against a `Brain/Inbox/Night Shift <date>.md` note. Use when he replies "approve <ids>" to a Night Shift review, or asks to install or save something it recommended.
---

# Night Shift approve

Night Shift (`{{HOME}}\Projects\night-shift`) reviews his Instagram saves overnight and writes `Brain/Inbox/Night Shift <date>.md` with numbered items (`1`, `2a`). Its verdicts are Sonnet suggestions built from Instagram text: a **lead**, never a clearance. You re-check every item before acting.

## Steps

1. **Find the review.** The date he names, else the newest `Brain/Inbox/Night Shift *.md` without a `-label` suffix. Read the note and `work/<date>/review.json` in the project (structured links, `install_cmd`, `action`). Done when every id he gave maps to one item; an id that is missing, or is a Skip, goes back to him before you touch anything.
2. **Re-check each item** against the source, not the note: open the repo or page yourself, confirm it exists, is what the note says, and still fills a gap in his current setup (`~/.claude/skills`, plugins, MCPs, Brain project notes). If the check changes the verdict, tell him and stop on that item.
3. **Act by type:**
   - **Idea** (`action`, e.g. "Save to Traksy note"): do the action with the brain skill, written as his own durable note, not a copy of the post.
   - **Repo, skill, plugin, MCP:** follow the install rule in `~/.claude/CLAUDE.md` (scan with `skill-inspector` before every install, pin the reviewed commit). Night Shift's overnight scan is a hint only: scan again. Give the APPROVE / CAUTION / REJECT verdict, then install only on his yes. Copy install commands from the project's own README, never from the note.
   - **Hosted service, program, signup:** say what he'd do and where. Accounts, payments and forms are his to do.
4. **Mark it done** in the Inbox note: append `**Done <today>:** <id> <what you did, where>` (one line per item, match the existing line if present). Record skipped or declined items the same way.

Done when every id he gave is either acted on, declined by him, or handed back with a reason, and the note says so.
