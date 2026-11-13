---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

For each ticket, use /delegate first: it decides whether `sonnet-coder` builds the ticket or you build it inline.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /review-changes to review the work.

Commit your work to the current branch.
