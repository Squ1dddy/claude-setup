#!/usr/bin/env node
// media.mjs — generation helper for scroll-sites. Node 20+, zero dependencies.
//
//   node media.mjs credits                                   kie.ai balance
//   node media.mjs upload <file>                              kie.ai temp upload (24h) -> prints downloadUrl
//   node media.mjs run <payload.json> --out <dir> --name <n>  kie.ai createTask + poll + download + log
//        [--usd 0.35]                                         preflighted price, logged for running totals
//        [--budget 20]                                        refuses if logged total + --usd would pass this cap
//   node media.mjs download <url> --out <dir> --name <n>      save any result URL (fal outputs too)
//   node media.mjs log --out <dir> --provider fal --model <id> --prompt "<text>" --usd 0.56 --file <path> [--job <id>]
//   node media.mjs spent --out <dir>                          total USD logged so far
//   node media.mjs gallery --out <dir>                        writes <dir>/gallery.html from the log
//
// payload.json is exactly the kie Market body: {"model":"kling-3.0/video","input":{...}}
// The key comes from the KIE_API_KEY environment variable and is never printed or logged.

import { readFile, writeFile, appendFile, mkdir, stat } from 'node:fs/promises';
import { createWriteStream } from 'node:fs';
import { basename, extname, join, relative, resolve } from 'node:path';
import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';

const API = 'https://api.kie.ai';
const UPLOAD = 'https://kieai.redpandaai.co/api/file-stream-upload';
const POLL_MS = [5000, 8000, 12000, 15000];
const TIMEOUT_MS = 20 * 60 * 1000;
const STALL_MS = 8 * 60 * 1000;   // no state/progress change this long counts as a stall -> fall back to fal

const [cmd, ...rest] = process.argv.slice(2);
const args = { _: [] };
for (let i = 0; i < rest.length; i++) {
  if (rest[i].startsWith('--')) args[rest[i].slice(2)] = rest[i + 1]?.startsWith('--') || rest[i + 1] === undefined ? true : rest[++i];
  else args._.push(rest[i]);
}

const die = (msg, code = 1) => { console.error('ERROR: ' + msg); process.exit(code); };
const need = (k) => args[k] ?? die(`missing --${k}`);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function key() {
  const k = process.env.KIE_API_KEY;
  if (!k) die('KIE_API_KEY is not set. Set it as a user environment variable, restart the terminal/app, then retry. (Use fal via MCP meanwhile.)', 2);
  return k;
}

async function kie(path, init = {}) {
  const res = await fetch(API + path, {
    ...init,
    headers: { Authorization: `Bearer ${key()}`, 'Content-Type': 'application/json', ...(init.headers || {}) }
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || (body.code && body.code !== 200)) {
    throw new Error(`kie ${path} -> HTTP ${res.status} code ${body.code ?? '?'}: ${body.msg || 'no message'}`);
  }
  return body.data;
}

const logPath = (dir) => join(dir, 'generations.jsonl');

async function readLog(dir) {
  try {
    return (await readFile(logPath(dir), 'utf8')).split('\n').filter(Boolean).map(l => JSON.parse(l));
  } catch { return []; }
}

async function writeLog(dir, entry) {
  await mkdir(dir, { recursive: true });
  await appendFile(logPath(dir), JSON.stringify({ at: new Date().toISOString(), ...entry }) + '\n');
}

async function download(url, dir, name) {
  await mkdir(dir, { recursive: true });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download ${url} -> HTTP ${res.status}`);
  const type = res.headers.get('content-type') || '';
  let ext = extname(new URL(url).pathname);
  if (!ext) ext = type.includes('video') ? '.mp4' : type.includes('png') ? '.png' : type.includes('webp') ? '.webp' : '.jpg';
  let file = join(dir, name + ext);
  for (let n = 2; await stat(file).then(() => true, () => false); n++) file = join(dir, `${name}-${n}${ext}`);
  await pipeline(Readable.fromWeb(res.body), createWriteStream(file));
  return file;
}

async function spent(dir) {
  return (await readLog(dir)).reduce((sum, e) => sum + (Number(e.usd) || 0), 0);
}

const commands = {
  async credits() {
    const data = await kie('/api/v1/chat/credit');
    console.log(JSON.stringify({ credits: data }));
  },

  async upload() {
    const file = args._[0] || die('usage: upload <file>');
    const form = new FormData();
    form.append('file', new Blob([await readFile(file)]), basename(file));
    form.append('uploadPath', 'scroll-sites');
    form.append('fileName', basename(file));
    const res = await fetch(UPLOAD, { method: 'POST', headers: { Authorization: `Bearer ${key()}` }, body: form });
    const body = await res.json().catch(() => ({}));
    if (!res.ok || !body.success) die(`upload failed: HTTP ${res.status} ${body.msg || ''}`);
    console.log(body.data.downloadUrl);
  },

  async run() {
    const payloadFile = args._[0] || die('usage: run <payload.json> --out <dir> --name <n>');
    const out = need('out'), name = need('name');
    const payload = JSON.parse((await readFile(payloadFile, 'utf8')).replace(/^﻿/, ''));   // PowerShell writes a BOM
    if (args.usd != null && args.budget) {
      const total = (await spent(out)) + Number(args.usd);
      if (total > Number(args.budget)) die(`budget: this run could bring the total to $${total.toFixed(2)}, over the $${args.budget} cap. Ask before raising it.`, 3);
    }

    const { taskId } = await kie('/api/v1/jobs/createTask', { method: 'POST', body: JSON.stringify(payload) });
    console.log(`task ${taskId} created (${payload.model})`);

    const started = Date.now();
    let lastChange = Date.now(), lastSig = '', i = 0, d;
    for (;;) {
      await sleep(POLL_MS[Math.min(i++, POLL_MS.length - 1)]);
      try {
        d = await kie(`/api/v1/jobs/recordInfo?taskId=${encodeURIComponent(taskId)}`);
      } catch (e) {
        console.log('poll error (retrying): ' + e.message);
        continue;
      }
      const sig = `${d.state}:${d.progress ?? ''}`;
      if (sig !== lastSig) { lastSig = sig; lastChange = Date.now(); console.log(`  ${d.state}${d.progress != null ? ' ' + d.progress + '%' : ''}`); }
      if (d.state === 'success' || d.state === 'fail') break;
      if (Date.now() - lastChange > STALL_MS) die(`task ${taskId} stalled in "${d.state}" for ${STALL_MS / 60000} min. Fall back to fal.`, 4);
      if (Date.now() - started > TIMEOUT_MS) die(`task ${taskId} timed out. Fall back to fal.`, 4);
    }

    const prompt = payload.input?.prompt ?? '';
    if (d.state === 'fail') {
      await writeLog(out, { provider: 'kie', model: payload.model, job: taskId, prompt, input: payload.input, state: 'fail', error: d.failMsg, credits: d.creditsConsumed ?? 0 });
      die(`task ${taskId} failed: ${d.failMsg || d.failCode || 'no reason given'}. Check kie.ai/logs that no credits were taken.`, 5);
    }

    const result = JSON.parse(d.resultJson || '{}');
    const urls = result.resultUrls || [];
    if (!urls.length) die(`task ${taskId} succeeded but returned no resultUrls: ${d.resultJson}`);
    const files = [];
    for (const [n, url] of urls.entries()) files.push(await download(url, out, urls.length > 1 ? `${name}-${n + 1}` : name));
    const usd = args.usd != null ? Number(args.usd) : null;   // pass --usd with the preflighted price so the log totals are real
    await writeLog(out, { provider: 'kie', model: payload.model, job: taskId, prompt, input: payload.input, state: 'success', credits: d.creditsConsumed ?? null, usd, files: files.map(f => relative(out, f)) });
    console.log(JSON.stringify({ taskId, credits: d.creditsConsumed ?? null, files }));
  },

  async download() {
    const url = args._[0] || die('usage: download <url> --out <dir> --name <n>');
    console.log(await download(url, need('out'), need('name')));
  },

  async log() {
    const out = need('out');
    const file = args.file ? relative(out, resolve(args.file)) : undefined;
    await writeLog(out, { provider: need('provider'), model: need('model'), job: args.job, prompt: args.prompt ?? '', usd: args.usd != null ? Number(args.usd) : null, state: 'success', files: file ? [file] : [] });
    console.log(`logged. total so far: $${(await spent(out)).toFixed(2)}`);
  },

  async spent() {
    console.log(`$${(await spent(need('out'))).toFixed(2)}`);
  },

  async gallery() {
    const out = need('out');
    const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const entries = (await readLog(out)).filter(e => e.state === 'success').reverse();
    const cards = entries.flatMap(e => (e.files || []).map(f => {
      const src = f.split(/[\\/]/).map(encodeURIComponent).join('/');
      const media = /\.(mp4|webm|mov)$/i.test(f)
        ? `<video src="${src}" controls muted loop playsinline preload="metadata"></video>`
        : `<img src="${src}" loading="lazy" alt="">`;
      return `<figure>${media}<figcaption><b>${esc(f)}</b><span>${esc(e.provider)} · ${esc(e.model)}${e.usd != null ? ' · $' + Number(e.usd).toFixed(2) : ''}</span><p>${esc(e.prompt)}</p></figcaption></figure>`;
    }));
    const html = `<!doctype html><meta charset="utf-8"><title>Generations</title>
<style>body{margin:0;padding:24px;background:#141418;color:#ddd;font:13px/1.45 system-ui}h1{font-size:18px;margin:0 0 16px}
.grid{columns:320px;column-gap:16px}figure{break-inside:avoid;margin:0 0 16px;background:#1d1d23;border-radius:10px;overflow:hidden}
img,video{display:block;width:100%}figcaption{padding:10px 12px}figcaption span{display:block;color:#999;margin:2px 0 6px}p{margin:0;color:#bbb}</style>
<h1>${entries.length} generations · $${(await spent(out)).toFixed(2)} logged</h1><div class="grid">${cards.join('\n')}</div>`;
    const file = join(out, 'gallery.html');
    await writeFile(file, html);
    console.log(file);
  }
};

if (!commands[cmd]) {
  console.log('commands: ' + Object.keys(commands).join(', ') + '  (see header of media.mjs)');
  process.exit(cmd ? 1 : 0);
}
commands[cmd]().catch(e => die(e.message));
