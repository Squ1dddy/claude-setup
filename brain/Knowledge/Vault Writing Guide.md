---
type: knowledge
summary: How to write in the Brain vault - note format, what to save, keeping notes short and searchable, and the checkpoint/resume protocol for clearing context mid-project
tags: [brain, vault, memory, checkpoint, resume, handoff, context, obsidian]
updated: 2026-10-11
---
# Vault Writing Guide

The vault is how sessions hand work to each other. One lead session owns the work (the `sonnet-coder` builder only takes single tickets; see [[Decisions]] Models), so that session does the work, writes a checkpoint here, and {{NAME}} clears context. The next session picks up from the note. A bad note costs a whole session of re-discovery, so write for a stranger with zero context.

## Principles
1. **Write for search.** `brain.py search` ranks on title and `summary`. Put the concrete nouns people will search for in both: project name, feature, file, tool.
2. **One topic per note, one owner per fact.** Before creating, search. Append to the note that owns the subject. Link instead of copying.
3. **Current state up front, finished work remembered separately.** In the main note, edit facts in place and bump `updated`; don't stack "update:" paragraphs, "STATUS: ... DONE" sections or "superseded" blocks. Wrong facts just get fixed (git keeps the old text). **Finished work is kept, not deleted ({{NAME}}, 2026-09-30):** when a branch, phase or task is done, move it to the project's history note `<Project> History.md` (`type: archive`, newest first) as a condensed dated entry: what shipped, decisions and why, lessons, key commits/files. Drop step-by-step next-actions (git has the exact text). The main note keeps a one-line link `History: [[<Project> History]]`. Archive notes live in `Archive/` (`brain.py archive --auto` moves any others there, so don't move them by hand), are found by `brain.py search --all`/`show "<name>"`, never pushed by the per-prompt hook, and are exempt from the 150-line cap. Old dated `##` sections of an oversized note roll into its History automatically; a whole finished note goes with `brain.py archive "<path>"`.
4. **Short and dense.** Bullets, not prose. Cut filler. A note someone skims in 30 seconds beats a complete one nobody reads. Split a note before it gets past ~150 lines.
5. **Facts, not narration.** "Auth uses JWT tenant claim, see `lib/auth.ts:40`", not "we spent a while looking at auth and found...".
6. **Only what the repo can't tell you.** Save decisions and their reasons, gotchas, preferences, where things live, and what's next. Don't save code, diffs, or anything `git log` already shows.
7. **Never secrets.** No keys, tokens, passwords or personal data about others. Name the env var instead.
8. **Date things that go stale.** Versions, prices, limits and "currently broken" facts get a date.

## Note format
Frontmatter on every note (template: `_system/templates/Note.md`):
```yaml
---
type: project | person | knowledge | decision | daily | inbox | archive | run
summary: One specific line naming the concrete things in the note
tags: [short, lowercase]
repo: C:\path\to\repo    # project notes only, `;` between several
updated: YYYY-MM-DD
---
```
- `repo:` lets the session hook inject this note's Resume when a session opens in that folder. Without it the project is invisible at startup.
- Title = filename = what someone would search for. No dates in titles except Daily notes.
- Wikilinks only to notes that exist and matter.
- New project note: add one line under `## Projects` in [[Home]].
- [[Profile]] loads in every session: keep it under ~40 lines, and only put in it what applies everywhere.

## Navigation quality
Claude never reads linked notes wholesale: the hook ranks on `summary`/`tags`/title and points at a `## ` section, and `show` jumps by heading. So these three fields are the navigation system. A PostToolUse hook (`brain.py check`) runs after every Edit/Write of a vault note and blocks (exit 2, with the reasons) until the note passes; `brain.py lint` checks the whole vault.
- **Summary:** 40-300 chars, one line, concrete nouns (project, tool, file, decision), what the note answers. No changelogs in it.
- **Tags:** inline list `[a, b, c]`, 2-8, lowercase-kebab nouns someone would search for. **Reuse before inventing:** run `brain.py search` or check existing tags first; a near-duplicate (`cost`/`costs`, `nightshift`/`night-shift`) is rejected. Include the project name, the tool/tech, and the topic. Home, Profile and Daily are exempt.
- **Headings:** every note over 40 lines needs 2+ `## ` sections, each named for what it holds ("Hooks", "Open threads", "Rule: never build with dev server running"), never "Notes", "Misc", "Other", "Details". One topic per section so `show "Note" <words>` returns just that part.
- **Links:** every Knowledge/Projects/People note must be linked from Home or its parent note (lint reports orphans). Link where the reader would need it next, and prefer `[[Note]]` plus a few words on why to follow it, so Claude can skip links that don't matter.
- **Run notes** (`Runs/`) and Inbox captures need 2+ tags too: project name plus `auto-run` / `night-shift` / `inbox`.

## Where things go
| What | Where |
|---|---|
| Preference or correction that applies to every session | [[Profile]] |
| Project purpose, location, stack, state, next steps | `Projects/<Name>.md` |
| Big project phase with its own handoff | `Projects/<Name> <Phase>.md`, linked from the parent |
| Decision with its reason | [[Decisions]] |
| Lesson from a mistake, with the incident | [[Working Rules Learned]] |
| Tool/config facts | [[Claude Code Setup]] |
| Unsorted capture | `Inbox/` |
| End-of-day log (wrap-up only) | `Daily/YYYY-MM-DD.md` |

## Checkpoint protocol (before clearing context)
**When:** at the end of each chunk or phase, before {{NAME}} runs `/clear` or starts a new session, and whenever the context feels heavy (long tool outputs, many screenshots, 100+ turns).

**Where:** in the project note, or in the phase note if the project has one, under `## Resume: <branch>` (plain `## Resume` for work with no git branch). One section per branch: **replace yours**, never append a second, and don't touch other branches' sections (another session may own them). Keep it under ~40 lines; the session hook injects it at startup, so every line costs tokens in every resumed session.

**Template:**
```markdown
## Resume: <branch>
_Checkpoint YYYY-MM-DD HH:MM, session topic_
- **Goal:** what the overall piece of work is, one line.
- **Where:** repo path, branch, last commit hash (or "uncommitted").
- **Done:** chunks finished and verified (how: tests, build, visual check).
- **In progress:** exactly what was half-done and which files are touched.
- **Next:** the first concrete action for the next session, then the rest in order.
- **Decisions this session:** choice + reason (also copy durable ones to [[Decisions]]).
- **Open questions for {{NAME}}:** anything blocked on him.
- **Verify on resume:** commands to confirm state (e.g. `git status`, `npm test`).
- **Gotchas:** traps hit this session that the next one would hit again.
```

**Steps:**
1. Commit or note uncommitted work (never discard it).
2. Replace your branch's Resume section with `brain.py section` (never a python/sed/node script; the guard blocks those). It also bumps `updated` and appends the section if the note has none:
   - Read: `python {{HOME}}\Brain\_system\brain.py section "Projects/X" "Resume: <branch>"` prints the current section and an `mtime`.
   - Write (Bash heredoc, or `--from <file>` from PowerShell): `python {{HOME}}\Brain\_system\brain.py section "Projects/X" "Resume: <branch>" --mtime <mtime> --from - <<'EOF'` then the section body, then `EOF`. It refuses if the note changed since that mtime, if two sections match, or if the body adds its own `##` heading. `--dry-run` shows the diff without writing.
3. Move durable lessons out to [[Working Rules Learned]] or [[Decisions]]. Resume is for state and should get thrown away as work moves on.
4. Tell {{NAME}} one line: what was saved and that it's safe to clear.

## Resume protocol (fresh session)
1. Opened in the project's repo: the Resume is already injected ("Brain project note for this folder"). Elsewhere: `brain.py search "<project>"`, then `brain.py show "<Note>" resume`.
2. Treat it as a claim, not truth: run the "Verify on resume" commands and check `git status`/`git log -3` before acting.
3. Start at **Next**. Ask {{NAME}} about the open questions only if they block that step.

## Concurrent sessions
Several sessions can write the vault at once. The rules that keep that safe:
- Edit notes only with the Edit tool (Write for new notes). Edit refuses when the file changed since you read it; re-read and retry. Shell writes into the vault are blocked by the `brain.py guard` hook.
- Resume sections are per branch, so parallel branches don't overwrite each other.
- Daily notes: re-read right before editing and append `## Session <HH:MM>`.
- Renames, moves and deletes are {{NAME}}'s, in Obsidian.
- A Stop hook commits after every turn (`auto: <notes> [session <id>]`). To see or undo a change: `git -C {{HOME}}\Brain log -p -- "<note path>"`, then put the old text back with Edit.

## Maintenance
- `python {{HOME}}\Brain\_system\brain.py lint` after big edits: navigation quality (summary length, tags, generic or missing headings, orphans), frontmatter, broken links, notes over 150 lines, stacked STATUS/superseded headings, duplicate or stale-branch Resumes, missing `repo:`, Profile size.
- When a branch merges or a project finishes, move its Resume into `<Project> History.md` as a condensed dated entry (rule 3); anything still open goes to the main note's `## Open threads`.
