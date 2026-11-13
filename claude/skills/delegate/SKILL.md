---
name: delegate
description: Hand a build ticket to the sonnet-coder worker - when to delegate vs build inline, the brief, the acceptance check. Use when /implement starts a ticket, or {{NAME}} says delegate or sonnet.
---

Opus is the **lead**: it owns the overall build, scopes each ticket, and decides what counts as done. Sonnet (`sonnet-coder`) is the **builder**. Evidence: the Sonnet Subagent Benchmark in Brain (Sonnet matched Opus on every graded ticket; the lead's scoping was where Opus earned its cost).

## 1. Delegate or build inline
A spawn has a fixed cost: ~20k tokens of cold start even for a 3-line fix, plus the brief and the acceptance check. Round 3 of the benchmark (2026-10-13) measured plan-then-build at about 2x the tokens and time of a solo run, with no accuracy gain. So delegate only when ALL hold:
- **The lead is Opus.** In a Sonnet session, build inline: there is no model saving, only spawn overhead.
- **The ticket is big:** 3 or more files, or about 10 or more edits, or the builder would read and run a lot the lead doesn't need in its context.
- **The brief fits:** under ~600 words with a done checklist and a test command. If you can't write that, the ticket isn't clear enough: ask {{NAME}} or scope more.

Build **inline** everything else, and always these:
- 2 files or fewer: one-file fixes, config tweaks, copy edits.
- Debugging with an unknown cause.
- Vague or product-decision work.
- Auth, RLS, Supabase tables, Server Actions, API routes, secrets or personal data: the lead builds these itself, or delegates and then reads the diff (step 5).

Plan in this session; never spawn a separate Opus planner. Haiku is not a builder here: it matched accuracy but took 2-5x the tool calls, and its saving in plan usage is unproven. Use it only for mechanical sweeps that a test exit code verifies, and only if {{NAME}} asks.

## 2. Scope
Explore until you can name **every piece of existing code the ticket overlaps or conflicts with**: features doing something similar, RLS policies, call sites, shared types. This is the step that matters most. In the benchmark, solo runs half-replaced an existing delete feature and left a security hole; the lead's scoping caught it.

Any **product decision** you find (keep or replace an existing feature, user-visible behaviour, data handling) goes to {{NAME}} before the brief. Ask him; don't decide it in the brief.

## 3. Brief
One brief, under ~600 words:
- **Goal**: one or two sentences.
- **Behaviour**: what must be true, including edge cases and security rules you can foresee.
- **Overlaps**: the existing code from step 2 and what to do with each piece, with file paths.
- **Decisions**: product calls {{NAME}} made, stated as settled.
- **Done checklist**: observable behaviours, each checkable by a test or command.
- **Commands**: test and typecheck commands. If a dev server may be running, say "tests and tsc only, no build".

Send it with the Agent tool, `subagent_type: sonnet-coder`.

## 4. Acceptance check
Check **what** was done, not how:
1. Run the test and typecheck commands yourself. They must pass.
2. Confirm each done-checklist item: the test exists and passes, or the command shows it.
3. Read the worker's **Open** list. Product questions go to {{NAME}}.

Skip reading the diff for style or approach. If an item fails, send ONE fix request naming the failing item. A ticket that fails twice comes back to {{NAME}} with what failed.

The worker owns the code on a delegated ticket. Your fixes go through it, so the report stays true to what was built.

## 5. Security tickets
When a ticket touches auth, RLS or Supabase tables, Server Actions or API routes, secrets, or personal data, run the `security-checklist` skill against the change after the acceptance check. This is the one place where reading the diff earns its cost.

## 6. Close
Then continue the normal workflow: `review-changes` and `verification-before-completion` when the branch is done, commit, and checkpoint to Brain.
