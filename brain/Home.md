---
type: index
summary: Map of the Brain vault, its folders and how Claude uses it
updated: {{DATE}}
---
# Brain

Long-term memory for every Claude Code session on this machine. Plain Markdown; Claude searches it on demand instead of loading it.

| Folder | Holds |
|---|---|
| `Projects/` | One note per project: what it is, where it lives (`repo:`), current state, `## Resume: <branch>` checkpoints |
| `People/` | People who come up in work, one note each |
| `Knowledge/` | Decisions, lessons learned from mistakes, how-tos, tool notes |
| `Daily/` | Session logs, written on wrap-up only (`YYYY-MM-DD.md`) |
| `Inbox/` | Unsorted captures, file them later |
| `Runs/` | auto-run progress notes |
| `Archive/` | Finished work, moved here by `brain.py archive` |
| `_system/` | `brain.py` (search tool + hooks) and templates. Not notes. |

[[Profile]] is the only note loaded into every session. Keep it short. How to write notes: [[Vault Writing Guide]].

## Projects
<!-- one line per project: [[Name]] - status -->

## Knowledge
- [[Style]] - how Claude writes replies
- [[Vault Writing Guide]] - note format, checkpoint and resume protocol
- [[Decisions]] - choices and why
- [[Working Rules Learned]] - lessons from mistakes
- [[Claude Code Setup]] - what is installed and where
