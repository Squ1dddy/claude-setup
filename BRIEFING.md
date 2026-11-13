# BRIEFING.md: how to explain this setup to your user

Agent: after installing, walk your user through this in plain words, one part at a time. Check they follow before moving on. Keep each part to a few sentences plus one thing they can try.

## Interview (do this first, fills Profile.md)
Ask, one at a time: what they want to be called; what they're working on now and their top 1-3 priorities; their skills; how they like replies (short and direct, or more explanation); whether they want you to ask before guessing (the default here) or just act. Then go through each "Working preferences" bullet in `Profile.md`: keep, change or drop.

## 1. The big idea
- Claude Code forgets everything when a session ends. This setup gives it a **long-term memory** (the Brain vault) and a **fixed way of working** (CLAUDE.md), so every session acts the same and picks up where the last one stopped.

## 2. The Brain (memory)
- A folder of Markdown notes (`~/Brain`), browsable in Obsidian. One note per project, plus Profile (who you are), Style (how replies read), Decisions, Working Rules Learned.
- Nothing is bulk-loaded. On each message a hook (`brain.py hook`) finds up to 3 relevant notes and gives Claude pointers; Claude reads only what it needs.
- Profile.md is the one note loaded into every session. Keep it short.
- Every turn, a hook auto-commits the vault to git, so any bad edit can be undone.
- A guard hook stops shell commands from writing into the vault, so notes are only edited carefully.
- Try: "remember that I prefer TypeScript" and see it saved to Profile or Decisions.

## 3. Checkpoint and resume (how work survives /clear)
- Long sessions get slow and forgetful. At the end of a chunk of work, or when the context passes 150k tokens (the context-guard hook nags), Claude writes a `## Resume: <branch>` section into the project note: goal, done, next step, gotchas.
- You then `/clear`. Claude gives you the exact prompt to paste. Next session, if you open it in the project folder, the Resume is injected automatically.
- Each project note needs a `repo:` line with the project folder path for that to work.

## 4. The status band (the mod)
- Above the prompt in the terminal: how full the context is (colour goes red as it fills), your plan usage limits, how long since the last Brain save, and the project's next step. When the save goes stale, checkpoint.

## 5. How real work runs
- Small stuff (questions, one-file fixes): Claude just does it.
- Real features: **grill** (Claude questions you until the idea is clear) → **spec** → **tickets** (small vertical slices) → **implement** one ticket at a time with tests → **simplify** → **review + verify** (evidence before saying "done") → commit → checkpoint.
- Commands you type: `/grill-me` or `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/implement`, `/retro`. `/ask-matt` tells you which one fits.
- **Opus leads, Sonnet builds:** the main session (Opus) plans and checks; multi-file tickets go to the cheaper `sonnet-coder` subagent via `/delegate`.
- Big jobs: `auto-run` runs tickets unattended in fresh contexts in the background, tracked in a Brain run note.
- Decisions: `/council` runs 5 advisor viewpoints and a verdict.

## 6. Other skills worth knowing
- Design: `impeccable` (direction and critique), `ui-ux-pro-max`, `design-motion-principles`, `web-visual-fx`, `ux-feel`.
- Bugs: `diagnosing-bugs`. Security while building: `security-checklist`. Safety of new skills: `skill-inspector`.
- Video and media: `watch-video`, `code-video`, `brag-slim`. Research: `research`, `agent-reach`.
- Full list in SKILLS.md.

## 7. Rules it follows
- Asks when unsure instead of guessing. Argues back when you're wrong.
- Never puts secrets in files; keys go in env vars you set yourself.
- Never deletes real data; scans every new skill/plugin before installing.
- Starts each final reply with a one-line headline and ends change reports with a plain **Summary:**.

End by asking which part they want to try first, and suggest: open a project folder, run `claude`, and say "set up a Brain note for this project".
