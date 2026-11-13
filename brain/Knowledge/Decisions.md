---
type: decision
summary: Durable decisions with their reasons - models (Opus leads, Sonnet builds), tools, workflow choices
tags: [decisions, models, workflow]
updated: {{DATE}}
---
# Decisions

## Models
- **Opus leads, Sonnet builds.** The main session (Opus) plans, scopes, accepts work and talks to the user. Multi-file build tickets go to the `sonnet-coder` subagent via `/delegate`; small jobs stay inline. Reason: Opus is better at judgement, Sonnet is cheaper and good enough for a well-briefed single ticket.

## Workflow
<!-- Add: date - decision - reason -->
