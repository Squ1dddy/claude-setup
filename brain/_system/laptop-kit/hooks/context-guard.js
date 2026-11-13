#!/usr/bin/env node
// Context guard (laptop copy; path-neutral). Mirrors the PC's ~/.claude/hooks/context-guard.js.
//
//   node context-guard.js prompt   UserPromptSubmit: once context passes the threshold, tell Claude to
//                                  checkpoint to Brain and tell {{NAME}} to /clear. Fires again every STEP tokens.
//
// Context size = input + cache_read + cache_creation tokens of the last main-thread assistant message in
// the transcript. Never blocks: any error exits 0 silently.
// Env overrides: CONTEXT_GUARD_THRESHOLD (default 150000), CONTEXT_GUARD_STEP (default 50000).

const fs = require('fs');
const os = require('os');
const path = require('path');

const THRESHOLD = parseInt(process.env.CONTEXT_GUARD_THRESHOLD || '150000', 10);
const STEP = parseInt(process.env.CONTEXT_GUARD_STEP || '50000', 10);
const TAIL_BYTES = 2 * 1024 * 1024;

function readStdin() {
  try { return JSON.parse(fs.readFileSync(0, 'utf8') || '{}'); } catch { return {}; }
}

function contextTokens(transcriptPath) {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return null;
  const size = fs.statSync(transcriptPath).size;
  const start = Math.max(0, size - TAIL_BYTES);
  const fd = fs.openSync(transcriptPath, 'r');
  const buf = Buffer.alloc(size - start);
  fs.readSync(fd, buf, 0, buf.length, start);
  fs.closeSync(fd);
  const lines = buf.toString('utf8').split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i];
    if (!line.includes('"usage"')) continue;
    let d;
    try { d = JSON.parse(line); } catch { continue; } // first line may be cut mid-record
    if (d.type !== 'assistant' || d.isSidechain) continue;
    const u = d.message && d.message.usage;
    if (!u) continue;
    return (u.input_tokens || 0) + (u.cache_read_input_tokens || 0) + (u.cache_creation_input_tokens || 0);
  }
  return null;
}

function emit(event, text) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: { hookEventName: event, additionalContext: text },
  }));
}

function prompt(input) {
  const tokens = contextTokens(input.transcript_path);
  if (tokens == null) return;
  const stateFile = path.join(os.tmpdir(), `context-guard-${input.session_id || 'default'}.json`);
  let lastBucket = -1;
  try { lastBucket = JSON.parse(fs.readFileSync(stateFile, 'utf8')).bucket; } catch {}

  if (tokens < THRESHOLD) {
    if (lastBucket !== -1) fs.writeFileSync(stateFile, JSON.stringify({ bucket: -1 }));
    return;
  }
  const bucket = Math.floor((tokens - THRESHOLD) / STEP);
  if (bucket <= lastBucket) return;
  fs.writeFileSync(stateFile, JSON.stringify({ bucket }));

  const k = Math.round(tokens / 1000);
  emit('UserPromptSubmit',
    `CONTEXT GUARD: this session's context is ~${k}k tokens (threshold ${THRESHOLD / 1000}k). ` +
    'Every turn re-reads all of it, so cost grows with each reply. Handle the user\'s message first, but do not ' +
    'start a new chunk of work. At the next natural boundary (end of the current ticket/step), write a Brain ' +
    'checkpoint: replace the project note\'s "## Resume" section per the brain skill / Vault Writing Guide, commit ' +
    'or note uncommitted work, then tell the user in one line that it is safe to /clear and resume in a fresh ' +
    'session, and always give them the exact prompt to paste after clearing, in its own fenced code block ' +
    '(e.g. "Resume <project> from Brain: <what is next>"), so the fresh session picks up from the Resume section. ' +
    'If this session is not project work (a quick question, config chat), just mention the size in one line.');
}

try {
  const mode = process.argv[2];
  const input = readStdin();
  if (mode === 'prompt') prompt(input);
} catch {
  // never block the session
}
process.exit(0);
