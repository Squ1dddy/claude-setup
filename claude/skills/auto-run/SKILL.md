---
name: auto-run
description: Run a long task unattended across fresh contexts - this session plans chunks into a Brain run note, then a background loop runs one headless worker per chunk until the run stops or finishes. Use when a task is large (3+ tickets or more than one fresh context: suggest it, start on his yes), when {{NAME}} says "auto-run" or "resume auto-run", or when you are a headless auto-run worker.
---

# Auto-run

One **run note** is the whole memory. The **conductor** ({{NAME}}'s session) plans, launches `run.sh` in the background, and sleeps: a background command wakes it only on exit, so the loop costs it nothing per chunk. `run.sh` starts a headless **worker** (`claude -p`, Opus, bypassPermissions) per **chunk**; each is a fresh process, so a fresh context. The loop ends when the note's `status` leaves `active`, when a worker leaves the note unchanged, or at the chunk cap.

## Run note

`{{HOME}}/Brain/Runs/<YYYY-MM-DD> <task>.md`. Recall past runs with `brain.py search "<task>"`.

```markdown
---
type: run
summary: Auto-run of <task> for <project> - <what it builds>
updated: <YYYY-MM-DD>
status: active            # active | stopped | done
stop_reason:
project: "[[<Project>]]"
repo: C:/path/to/repo     # forward slashes; the worker runs here
branch: <run branch>
---
# Run: <task> (<date>)
Goal: <one line>. Spec/tickets: <paths or links>.

## Summary
(conductor fills at the end)

## Chunks
- [ ] 1. [sonnet] <vertical slice sized for one fresh context, with its done-criterion>
<!-- optional model tag per chunk: [opus] | [sonnet] | [haiku]; run.sh uses the first unticked chunk's tag, default opus. Opus for design-heavy, security, vague or cross-cutting chunks; Sonnet for well-specified ones. -->

## Log
<!-- worker appends one entry per chunk:
### Chunk N - HH:MM
Done: ... | Decisions: ... | Files: ... | Verified: <command + result> | Commit: <sha> | Problems: ... | Next: ... -->
```

## Stops

The worker sets `status: stopped` and a one-line `stop_reason` on:
- the same test or check failing twice;
- a scope or taste question {{NAME}}'s "ask when uncertain" rule covers, unless the run note has `away: true` (set by the conductor when {{NAME}} says he is away): then take the reversible option, log it under "Decided while you were away" in the run note, and carry on;
- anything needing a push (commits stay local on `branch`).

After the last chunk it sets `status: done`.

## Conductor steps

1. **Announce**: tell {{NAME}} the task spans several contexts and you'll auto-run it; list the chunks. Done when he says go.
2. **Prepare**: create or switch to the run branch with a clean tree, and write the run note from the template, each chunk with a checkable done-criterion.
3. **Launch**: `bash ~/.claude/skills/auto-run/run.sh "<note path>"` with `run_in_background: true`. Tell {{NAME}} it's running and where the log is. While it runs, answer him from the note and log only.
4. **On exit**: read the note, the exit line and the log's last lines.
   - **Usage limit** (unchanged note, log mentions a limit): `get_usage` gives `resetsAt`; relaunch in the background as `sleep <seconds to reset + 120> && bash .../run.sh "<note>"`. No ping.
   - `stopped`, or any other unchanged-note/cap exit: `PushNotification` {{NAME}} with the reason, then run **Lean check**. When he answers, update the note (`status: active`, clear `stop_reason`, add his decision to the log) and relaunch.
   - `done`: write `## Summary` (what shipped, decisions, open problems, commits), replace the project note's Resume per the brain skill, `PushNotification` {{NAME}}, and ask him about pushing.

## Lean conductor

The conductor stays lean: it reads only the note, the exit line and log tails, never the diff or full log. Chunk work belongs to workers.

**Lean check** (at a stop, while {{NAME}}'s answer is pending): `get_usage`. Over 150k tokens: write `## Conductor resume` in the note (the pending question, anything from the chat the note lacks), tell {{NAME}} "Clearing to stay lean. Reply `resume auto-run: <your answer>`.", then `clear_session("self")`.

**Resume** (`resume auto-run`, or a fresh session asked to continue a run): find the run in `{{HOME}}/Brain/Runs/` whose `status` is `stopped` or `active` (ask {{NAME}} if several), read it including `## Conductor resume`, apply his answer, delete that section, and continue from step 4.

## Worker steps

1. **Load**: read the run note. Check `git status` and `git log --oneline -5` against the log. The chunk is the first unticked box.
2. **Build**: do that one chunk under {{NAME}}'s normal workflow (tdd at seams, `verification-before-completion`). Done when its done-criterion holds with evidence.
3. **Commit**: one local commit for the chunk on `branch`.
4. **Log**: append the chunk's log entry, tick its box, and set `status: done` if no boxes remain. On a stop, log what happened and set `status: stopped` with `stop_reason` instead of ticking.
5. **Exit**: end with a one-line result. The loop starts the next chunk.
