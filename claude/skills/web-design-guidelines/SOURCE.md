# Source
- Skill: vercel-labs/agent-skills @ 063bee94c3f4df8453406c830b0a7df0f2860278, `skills/web-design-guidelines` (original fetched rules live from an unpinned URL each run).
- Rules: vercel-labs/web-interface-guidelines @ e3d624baaf29dc1fc645aff3e38f03e564d2d6b1, `command.md` copied verbatim to `guidelines.md`.
- Local changes (2026-10-04): rules vendored instead of fetched; description narrowed so it does not take impeccable's "audit design / review UX" triggers.
- Scan 2026-10-04: SkillSpector skill 0/LOW (no issues), rules repo 20/LOW SAFE. Manual review: plain review checklist, no scripts, no network, no prompt injection.
- To update: re-clone both repos, diff `command.md`, rescan, update pins here.
