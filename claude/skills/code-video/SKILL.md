---
name: code-video
description: Make animated promo, explainer or motion-graphics videos as code (canvas scenes + synthesised sound effects) and export MP4, optionally synced to a voiceover. Use when {{NAME}} wants a promo, explainer, pitch video, motion graphic or animated clip, or wants a video re-timed to his recording.
---

# Code video

A video here is one HTML file: `BEATS` (one scene per spoken line), `SCENES` (a pure `render(t)` per scene on a 1920x1080 canvas) and `sfxEvents` (Web Audio sounds, no files). `render.mjs` steps it frame by frame in headless Chromium and pipes to ffmpeg. Nothing is AI-generated footage, so every change is a precise code edit.

`template/` is the first real one: the Traksy pilot pitch (warm neumorphic cards, Traksy palette). Start from it.

## Steps

1. **Brief.** Audience, length and shape (16:9 or 9:16), voice (his own / AI / none), look. Done when all four are answered.
2. **Script.** One line per beat, about 2.4 spoken words per second (130 words ≈ 55 s). Each claim must be true of the product: check Brain or the repo. Done when {{NAME}} has approved the lines.
3. **Build.** Copy `template/` into the project folder, `npm i playwright-core@1.55.0` (matches the Chromium already in `%LOCALAPPDATA%\ms-playwright`). Rewrite `BEATS`, the palette `C`, `SCENES` and `sfxEvents`. Keep in-scene timings at 4 s or less, or a fast read cuts the animation short.
4. **Check stills.** `node render.mjs --stills 5,13,...` (one mid-scene time each), tile them with ffmpeg `xstack`, read the sheet. Done when every scene reads clearly and nothing overlaps.
5. **Render.** `node render.mjs --name <name>` → `out/<name>.mp4` (55 s renders in about 45 s). Check with `ffprobe` and `volumedetect`.
6. **Voiceover sync.** {{NAME}} records (phone memo is fine), then:
   `whisper-ctranslate2 vo.m4a --model small --device cpu --compute_type int8 --language en --word_timestamps True --output_format json --output_dir out`
   `node render.mjs --voice vo.m4a --words out/vo.json --name <name>`
   Scenes start on each line's opening words; the match tries word pairs 1-2, 2-3, 3-4, so one misheard word is fine (Whisper hears "Traksy" as "Traxy"). If it reports a line it can't find, the recording strayed from the script: fix that beat's `line` to what he said. Done when frames grabbed just after three cue words show the right scenes.

## Preview

Open `index.html` in a browser: Play, scrub, Sound, Loop, Load voiceover, Load word timings (the same JSON). `?capture` is the render mode.
