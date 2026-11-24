#!/usr/bin/env bash
# auto-run loop: one headless worker per chunk, each a fresh context.
# Usage: run.sh <run-note-path> [max-chunks]
# Exits when the note's status leaves "active", a chunk changes nothing, or max-chunks is hit.
set -u
export PATH="$HOME/.local/bin:$PATH"  # claude.exe lives here; background shells may not have it
note="$1"; max="${2:-25}"
[ -f "$note" ] || { echo "EXIT: run note not found: $note"; exit 2; }

field() { grep -m1 "^$1:" "$note" | sed "s/^$1:[[:space:]]*//; s/[[:space:]]*#.*$//; s/^\"//; s/\"$//"; }

repo="$(field repo)"
cd "$repo" || { echo "EXIT: cannot cd to repo: $repo"; exit 2; }
log="${TMPDIR:-${TEMP:-/tmp}}/auto-run-$(basename "$note" .md | tr ' ' '-').log"
echo "log: $log"

for i in $(seq 1 "$max"); do
  status="$(field status)"
  [ "$status" = active ] || { echo "EXIT: status=$status after $((i-1)) chunk(s)"; exit 0; }
  before="$(md5sum "$note")"
  echo "=== chunk run $i $(date +%T) ===" >> "$log"
  model="$(grep -m1 '^- \[ \]' "$note" | grep -o -E '\[(opus|sonnet|haiku)\]' | tr -d '[]')"; model="${model:-sonnet}"  # per-chunk tag, default sonnet (2026-11-19)
  echo "model: $model" >> "$log"
  claude -p "You are a headless auto-run worker. Read the '## Worker steps' section of {{HOME}}/.claude/skills/auto-run/SKILL.md and follow it for this run note: $note" \
    --model "$model" --permission-mode bypassPermissions --strict-mcp-config --disable-slash-commands --setting-sources project >> "$log" 2>&1
  # Lean worker ({{NAME}}, 2026-11-17): no MCP servers (~250k input tokens per call), no skills, no user settings/CLAUDE.md/hooks.
  # Measured in secret-history: a bare call fell from ~355k to ~7k input tokens. Workers get their rules from the repo's CLAUDE.md and the run note.
  echo "=== exit $? $(date +%T) ===" >> "$log"
  [ "$(md5sum "$note")" != "$before" ] || { echo "EXIT: chunk run $i left the run note unchanged (see log)"; exit 1; }
done
echo "EXIT: hit max-chunks ($max) with status still active"
