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
  model="$(grep -m1 '^- \[ \]' "$note" | grep -o -E '\[(opus|sonnet|haiku)\]' | tr -d '[]')"; model="${model:-opus}"  # per-chunk tag, default opus
  echo "model: $model" >> "$log"
  claude -p "You are a headless auto-run worker. Follow the auto-run skill's Worker steps for this run note: $note" \
    --model "$model" --permission-mode bypassPermissions >> "$log" 2>&1
  echo "=== exit $? $(date +%T) ===" >> "$log"
  [ "$(md5sum "$note")" != "$before" ] || { echo "EXIT: chunk run $i left the run note unchanged (see log)"; exit 1; }
done
echo "EXIT: hit max-chunks ($max) with status still active"
