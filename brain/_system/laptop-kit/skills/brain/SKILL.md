---
name: brain
description: {{NAME}}'s long-term memory vault (<VAULT>). Use to recall past projects, decisions, people, preferences or lessons; to save something worth remembering across sessions; or to write the daily note when {{NAME}} wraps up.
---

# Brain vault

Obsidian vault at `<VAULT>`, synced between {{NAME}}'s PC and laptop by Syncthing (git history is NOT synced: each machine has its own, or none). Plain Markdown. Nothing is bulk-loaded: hooks inject small pointers, and you read only what the task needs. Tool: `python <VAULT>\_system\brain.py <command>`.

Sync caveat: if {{NAME}} used the vault on the other machine just before, check Syncthing shows "Up to Date" before editing, and look for `*.sync-conflict-*` files (merge by hand, then delete the conflict copy with the Edit/brain.py route, never shell).

## Recall
1. **Session start:** if the session opened inside a project's repo, a `Brain project note for this folder` block is already in context with that project's `## Resume` for the current branch. Use it: don't search for or re-read the note. Verify it against `git status` before acting.
2. **Per prompt:** a `Brain:` block may list up to 3 pointers. `path:N (heading)` means the relevant section starts at line N: Read with `offset: N` and a small `limit`, not the whole note. Each pointer is shown once per session.
3. **Otherwise search:** `brain.py search "<words>"` (ranked `path[:line] | summary`). Also `recent`, `backlinks "<Note>"`.
4. **Follow a `[[Link]]`:** `brain.py show "Note"` prints a short note whole or a long note's outline with line numbers; `brain.py show "Note" <heading words>` prints just that section.
5. Never bulk-read folders. Notes are point-in-time: verify paths, flags and state against reality. Project `repo:` paths in notes may be the PC's paths; the laptop's repos can live elsewhere.

## Save (without being asked)
Save when you learn something a future session would need and can't get from the code or git:
- {{NAME}}'s preferences or corrections -> `Profile.md` if it applies to every session, else `Knowledge/`
- Project facts: purpose, location, stack, current state, open threads -> `Projects/<Name>.md`
- Decisions with their reason; lessons from mistakes with the incident -> `Knowledge/`
- People and their role -> `People/<Name>.md`

Don't save: secrets/keys/tokens (ever), things derivable from the repo, one-off task chatter, anything already in a note.

**How to write (several sessions may be editing at once):**
- Change notes only with the **Edit** tool (Write only for a brand-new note). Edit refuses if another session changed the file since you read it: re-read and retry. Shell writes into the vault (`>>`, `Set-Content`, Python `open(..,'w')`, `mv`, `rm`, `sed -i`) are blocked by a hook.
- Delete a note with `brain.py delete "Folder/Note"` (exact path; refuses if other notes link to it, so repoint those first). Renames and moves: ask {{NAME}} (Obsidian keeps links working).
- A Stop hook git-commits the vault after each turn if the vault is a git repo (no-op otherwise). Fix wrong facts in place (no superseded blocks or stacked STATUS sections). **Finished work moves to `<Project> History.md`** (`type: archive`) as a condensed dated entry; it is kept, not deleted. Details: Vault Writing Guide rule 3.

## Note format
```yaml
---
type: project | person | knowledge | decision | daily | inbox | archive | run
summary: One specific line. Search ranks on this, so name the concrete things.
tags: [short, lowercase]
repo: C:\path\to\repo          # project notes only; `;` between several. Lets the session hook find the note.
updated: YYYY-MM-DD
---
```
- Writing rules in full: `Brain/Knowledge/Vault Writing Guide.md`.
- Append to an existing note before creating a new one. Search first.
- One topic per note, one owner per fact: link, don't copy. Title = filename = what someone would search for.
- If a fact changed, edit it in place and bump `updated`.
- New project note -> `repo:` in frontmatter and one line under `## Projects` in `Home.md`.
- `Profile.md` loads every session: keep it under ~40 lines, terse bullets.
- Tell {{NAME}} in one line what you saved.

## Checkpoint and resume (context handoff)
Full rules and template: `Brain/Knowledge/Vault Writing Guide.md`.
- **Checkpoint** at the end of each chunk/phase, before {{NAME}} clears, or when context is heavy: commit or note uncommitted work, then **replace** the `## Resume: <branch>` section (plain `## Resume` for non-git work) in the project or phase note, using `brain.py section "<Note>" "Resume: <branch>"` (read, then write with `--mtime` and `--from -` heredoc; steps in the guide). Touch only your branch's section; other branches' Resumes belong to other sessions. Keep it under ~40 lines (the command bumps `updated`). Tell {{NAME}} it's safe to clear.
- **Resume:** the session hook injects it when the session starts in the repo. If not (different folder), `brain.py search "<project>"` and `brain.py show "<Note>" resume`. Run its verify commands and `git status`, start at Next.
- When a branch merges, move its Resume to `<Project> History.md` as a condensed entry; open items go to the main note's `## Open threads` (lint flags Resumes for deleted branches).

## Daily note (wrap-up only)
Only when {{NAME}} signals he's done ("done", "wrap up", "goodnight") or asks. Check the real date first. `Daily/YYYY-MM-DD.md` from `_system/templates/Daily.md`: Done / Open / Decisions, terse bullets, links to touched notes. If it exists, re-read it right before editing and append a `## Session <HH:MM>` section (time, not a counter, so parallel sessions don't collide).

## Maintenance
`brain.py lint` checks frontmatter, broken links, notes over 150 lines, stacked STATUS/superseded headings, duplicate or stale-branch Resumes, missing `repo:` and Profile size. Run it after big edits. After changing `brain.py` itself, run `_system/test_brain.py` (must end with 0 failures).
