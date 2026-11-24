# Lean build

Build the smallest change that fully meets the done check, at the quality a reviewer would accept. Less code and less output must not cost correctness. Both hold at once.

1. **Need:** a requirement nobody stated (future-proofing, "for later") is skipped. Say so in one line.
2. **Reuse order:** existing code in this repo, then the standard library or platform feature, then an already-installed dependency, then a new dependency. Add a new dependency only when it removes real complexity.
3. **Do not hand-roll what is hard to get right:** dates, time zones and DST, money, crypto, auth, parsing (HTML, CSV, URLs), unicode, concurrency. Use the library. Hand-roll only what is trivial (a clock display from `Date` is fine; a calendar engine is not).
4. **No unrequested structure:** no interface with one implementation, no factory for one product, no config for a value that never changes, no scaffolding. Follow the repo's existing patterns.
5. **Smallest readable diff:** fewest files, edit in place, delete dead code you touch. Short and clear beats short and clever.
6. **Never cut:** validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, edge-case correctness, anything the brief or Beau asked for, and one small runnable check for non-trivial logic (a branch, loop, parser, money or security path). Security tickets still follow `security-checklist`.
7. **Shortcut with a known ceiling** (global lock, O(n squared) scan): one comment naming the ceiling and the upgrade path.
8. **Spend fewer tokens:** read only the files and ranges you need, do not re-read a file you just edited, filter command output to results and errors, rerun only the failed check. No full-suite or full-pipeline run per edit.
9. **Report:** code or diff first, then the short report. No unrequested prose and no restating the diff. If you chose simpler than asked, say it in one line ("Used X; Y would add Z. Say so if you want Y"). If Beau insists on the fuller version, build it without re-arguing.
