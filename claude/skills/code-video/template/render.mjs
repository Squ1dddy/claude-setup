// Render index.html to MP4: steps the canvas frame by frame in headless Chromium, pipes JPEGs to ffmpeg,
// then mixes the synthesised sound effects with the voiceover.
//
//   node render.mjs                                   -> out/pitch.mp4 (estimated timings, SFX only)
//   node render.mjs --voice vo.m4a --words vo.json    -> scenes synced to Whisper word timings, voice + SFX
//   node render.mjs --stills 2,9,17                   -> out/still_<t>.png for quick checks
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, all) => (v.startsWith('--') && a.push([v.slice(2), all[i + 1]]), a), []));
const FPS = Number(args.fps || 30);
const OUT = resolve('out'); mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(resolve('index.html')).href + '?capture');
await page.evaluate(() => window.__ready);

if (args.words) {
  const j = JSON.parse(readFileSync(args.words, 'utf8'));
  const words = (j.segments || []).flatMap(s => s.words || []);
  const err = await page.evaluate(w => window.__useWords(w), words);
  if (err) { console.error(err); process.exit(1); }
}
const total = await page.evaluate(() => window.__total());

if (args.stills) {
  for (const t of args.stills.split(',').map(Number)) {
    await page.evaluate(t => window.__render(t), t);
    await page.locator('canvas').screenshot({ path: `${OUT}/still_${t}.png` });
  }
  console.log(`stills written to ${OUT}`); await browser.close(); process.exit(0);
}

// Sound effects track
writeFileSync(`${OUT}/sfx.wav`, Buffer.from(await page.evaluate(() => window.__sfx()), 'base64'));

// Video frames -> ffmpeg
const silent = `${OUT}/frames.mp4`;
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
const frames = Math.ceil(total * FPS);
for (let f = 0; f < frames; f++) {
  const b64 = await page.evaluate(t => window.__frameJpeg(t), f / FPS);
  if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
  if (f % (FPS * 5) === 0) process.stdout.write(`\rframe ${f}/${frames}`);
}
ff.stdin.end(); await new Promise(r => ff.on('close', r));
await browser.close();
console.log(`\rframes done (${frames})        `);

// Mix: voice at full level, SFX ducked underneath it
const final = `${OUT}/${args.name || 'pitch'}.mp4`;
const mix = args.voice
  ? ['-i', silent, '-i', args.voice, '-i', `${OUT}/sfx.wav`, '-filter_complex',
     '[1:a]aresample=48000,volume=1.0[v];[2:a]aresample=48000,volume=0.45[s];[v][s]amix=inputs=2:duration=longest:normalize=0[a]',
     '-map', '0:v', '-map', '[a]']
  : ['-i', silent, '-i', `${OUT}/sfx.wav`, '-map', '0:v', '-map', '1:a'];
await new Promise((res, rej) => spawn('ffmpeg', ['-y', '-loglevel', 'error', ...mix, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', final],
  { stdio: 'inherit' }).on('close', c => c ? rej(new Error('ffmpeg mix failed')) : res()));
console.log(`wrote ${final} (${total.toFixed(1)} s)`);
