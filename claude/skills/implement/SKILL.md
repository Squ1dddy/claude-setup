---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

## Size gate (decide first, say which lane in one line)

- **Small lane:** 2 files or fewer, about 50 changed lines or fewer, and no auth, RLS, Server Actions, API routes, secrets, personal data or deletes. Edit, run the ONE check that covers the change (a single test file, or typecheck), commit. Skip /delegate, /tdd and /review-changes. Add one test only if a bug fix needs a regression guard.
- **Standard lane:** everything else. Follow the steps below.

## Standard lane

For each ticket, use /delegate first: it decides whether `sonnet-coder` builds the ticket or you build it inline.

Use /tdd where possible, at pre-agreed seams.

**Test budget.** While editing: fast checks only (typecheck, the single test file you touched). Re-run only the check that failed. Run the full suite ONCE, at the end of the ticket, after the last edit. That run is the evidence for verification-before-completion; do not run it again unless code changed after it.

Once done, use /review-changes to review the work, unless the diff is under about 100 lines and not risky.

Commit your work to the current branch.
