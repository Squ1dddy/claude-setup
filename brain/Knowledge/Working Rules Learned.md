---
type: knowledge
summary: Lessons learned from mistakes, each with the incident that taught it - data safety, verification, tooling traps
tags: [rules, lessons, mistakes]
updated: {{DATE}}
---
# Working Rules Learned

<!-- One section per rule: "## Rule: <short rule>", then the incident (date, what went wrong) and what to do instead.
     Mechanical mistakes should become checks (lint, hook, CI), not more rules. -->

## Rule: never delete or overwrite real data
- Only exercise delete/overwrite/drop paths against fake data the test itself created.

## Rule: measure before estimating
- Check sizes, counts and timings with a command before quoting them. Verify CLI flags against the installed `--help`.
