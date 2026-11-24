# WHATS-NEW.md: show this to your user after an install or an update

Agent: read this to your user in plain words, a part at a time. It has two parts: **A** is everything the setup gives them and when to use each piece; **B** is what changed in this version. Show it once per version (see "Updating an existing install" in AGENTS.md), then record that you did. On a first install, BRIEFING.md already covered the basics: show A as a quick reference and B as the current state.

The version is in the `VERSION` file.

---

## A. What you have, and when to use what

### Just talk to it
Most of the time you only type what you want. The setup picks the right skill. Small jobs (a question, a one-file fix) are done directly with no ceremony.

### Memory: the Brain
- A notes folder (`~/Brain`, Obsidian-friendly). One note per project, plus Profile (who you are) and Decisions.
- **Use it:** say "remember that I prefer X". Ask "what did we decide about Y?" to recall.
- **Resume after /clear:** when a chunk of work ends, Claude saves a `Resume` section and tells you it is safe to `/clear`. Paste the prompt it gives you. Next time you open the project, the Resume loads by itself.

### Doing real work
| You want to | Type | What happens |
|---|---|---|
| Think an idea through | `/grill-me` (no repo) or `/grill-with-docs` (in a repo) | Claude asks questions, each with its own recommended answer, until the idea is clear. Reply "recommendation" to accept. |
| Write it down | `/to-spec` | Turns the talk into a spec. |
| Split it into steps | `/to-tickets` | Small slices, each with a size estimate. |
| Build | `/implement` | One ticket at a time, tests first, real checks before "done". |
| Tidy the code | `/simplify` | Finds reuse and cleanup chances. Claude double-checks each find. |
| Not sure which to use | `/ask-matt` | Names the right skill for your situation. |
| Something is broken | say "debug this" | `diagnosing-bugs` runs a reproduce, narrow, fix loop. |
| Check before a commit or PR | automatic | `verification-before-completion` runs the real checks. `pr` writes the PR body. |
| A hard decision | `/council` | Five advisors answer apart, review each other, then give a verdict. |
| A big job (3+ tickets) | say "auto-run" | Runs tickets unattended in the background, each in a fresh context. Claude suggests it when a job is large. |
| Learn from a rough ticket | `/retro` | Turns repeated mistakes into checks, not more rules. |
| Improve the setup itself | `/improve-system` | Reads your recent sessions for repeated friction and proposes fixes. |

### Models and cost
- **Sonnet is the default.** It costs less and matches Opus on specced work. **Opus** is for grilling, planning, design, security and hard bugs: start those in a fresh Opus session.
- Effort defaults to medium. Ask for a harder think when you need one.
- If Claude fails twice on one problem, it asks a stronger reviewer (`advisor`) once, then tells you to move to Opus. It does not grind.

### Design and media (only when relevant)
- Websites and UI: `impeccable` (direction and critique), `ui-ux-pro-max`, `design-motion-principles`, `web-visual-fx`, `ux-feel`. Small tweaks need none of them.
- Video and media: `watch-video` (send a link, get a breakdown), `code-video`, `brag-slim` (launch video).
- Research: `research` (primary sources into a Markdown file), `agent-reach` (Reddit, X and other sites a normal fetch cannot read).
- Safety: `security-checklist` runs while you build anything with logins, data or APIs. `skill-inspector` scans any new skill before you install it.

### Status band
The line above the prompt shows context fullness, plan usage and time since the last Brain save. When it goes red or the save is stale, ask Claude to checkpoint.

### Rules it follows
It runs commands itself, asks only when a wrong guess is costly, never puts secrets in files, never deletes real data, and ends finished jobs with a bold **Summary** in plain words.

---

## B. What is new in this version (2026-11-24)

1. **It runs commands for you.** Claude runs every command itself and only hands over sign-ins, secrets and admin prompts. The installer brief and your CLAUDE.md both say so.
2. **Sonnet by default, effort medium.** New sessions start on Sonnet. Use Opus for planning, design and security.
3. **Lean build rules** (`~/.claude/lean-build.md`). All code Claude writes, inline or through subagents, follows one short rulebook: the smallest change that meets the goal, reuse before new code, never cut security or validation, fewer wasted tokens.
4. **New `haiku-scout` helper.** A cheap read-only assistant for narrow lookups (classify files, list matches, short summaries). It never edits.
5. **Batched grill questions.** `/grill-me` and `/grill-with-docs` group their questions with a recommended answer each, so you can answer "recommendation" instead of many round trips.
6. **Size estimates up front.** `/to-tickets` and `auto-run` say how big a job is before it starts, so you can decide.
7. **Plain Summary at the end.** Finished jobs end with a bold **Summary** line and two to four plain sentences.
8. **`/improve-system` fixes.** The session digest now handles denied tool calls and side sessions correctly.
9. **One-paste install and update.** The README has a single message to paste for each.

**Heads-up:** if unattended jobs (`auto-run`) fail with a sign-in error, run `claude auth login` once in a terminal.

---

When you finish, ask which part they want to try first. A good first try: open a project folder, run `claude`, and say "set up a Brain note for this project".
