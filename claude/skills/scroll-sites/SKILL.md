---
name: scroll-sites
description: Use when building a website, landing page, or one-page site whose visuals move with scroll (scroll-scrubbed scenes, Apple-style image-sequence animation, scroll storytelling, parallax depth) using AI-generated images or video from fal.ai or kie.ai pay-as-you-go APIs. Also use when setting up the fal.ai MCP or a kie.ai key for site visuals. Takes precedence over 10k-websites and any Higgsfield-based website skill.
---

# Scroll Sites

A scroll site is a page built as a run of **scroll scenes**: short AI-generated clips exported as image sequences, drawn to a canvas, and scrubbed frame by frame as the visitor scrolls. Each scene pins while its story plays, then releases into real content. Nothing autoplays. The visitor's scroll is the playhead, in both directions, on every screen.

Stack: plain HTML, CSS and vanilla JS with the tested engine in `templates/scroll-scenes.js` + `.css`. No framework, no build step, one folder.

Pipeline: Claude Code builds. **fal.ai** (official MCP, tools `search_models`, `get_model_schema`, `get_pricing`, `upload_file`, `submit_job`, `check_job`) and **kie.ai** (cheapest, flaky; driven by `scripts/media.mjs`) generate. Deploy where the user chooses (`references/deploy.md`). Never Higgsfield; never another website skill's workflow mixed in.

**Design skills** (CLAUDE.md Frontend rule): impeccable sets direction at Phase 3; web-visual-fx for effects; pull in ui-ux-pro-max (palettes, fonts) and design-motion-principles (motion) when that part is in play. Applied through Phase 6.

## Working with the user

- Clickable choices for every decision (recommended option first). Typing only for their idea and feedback in their own words.
- **Money before it moves:** every price in USD before spending, and a running total against the project budget. Nothing generates without a price said out loud.
- Plain words, short sentences. Say when something takes minutes. Inspect everything yourself before showing it.
- GATE means never skip. Numbers in references are proven defaults: deviate when the project calls for it, and say so.

## Phase 0: Setup check (verify, never assume)

Scan first, then report a ✓/✗ checklist:

1. **fal**: `claude mcp get fal-ai`. "Connected" means ready. HTTP 401 means `FAL_KEY` is not set in the environment.
2. **kie**: `node <skill>/scripts/media.mjs credits`. Exit code 2 means `KIE_API_KEY` is not set.
3. `ffmpeg -version` and `node --version`.

At least one provider must pass. Missing keys are a user step, and the user does it themselves: create the key on fal.ai/dashboard/keys or kie.ai/api-key, add funds (small amounts on kie), then set it as a Windows user environment variable (Start → "Edit environment variables for your account" → New → `FAL_KEY` / `KIE_API_KEY`) and fully restart the Claude app. **Never ask for a key in chat, never write a key into any file or command.** After restart, re-run the checks.

Then ask the **project budget** in USD (options: $5 / $10 (Recommended) / $20). Every kie run passes `--budget`; every fal job is logged with `media.mjs log` so `media.mjs spent` stays true.

## Phase 1: Brief and research

One question at a time: what it is and who it's for (real thing with photos / invented brand / real business without photos / digital product with screenshots), the feeling, references, existing assets (logo, product photos: drag into chat). Then research real buyer language (reviews, forums): pains, desired outcomes, objections. Copy uses their words; the page funnels to ONE call to action.

## Phase 2: Scene plan (the keystone)

Design the page first, then the scenes that carry it. The generator never knows it is making a website.

| Scene type | Visitor sees | Built from | Typical cost |
|---|---|---|---|
| **Sequence** | footage advances as they scroll | start still + one 5s image-to-video clip | ~$0.40 to 0.90 |
| **Bridge** | one section's world transforms into the next | start + end frame video (both stills generated first) | ~$0.40 to 0.90 |
| **Journey** | one continuous 10 to 20s camera move | chained clips, last frame → next start | per clip |
| **Depth** | a still scene in layers drifting at different speeds | 1 to 3 stills + background removal, `data-speed` | cents |

- 2 to 4 motion scenes per page. Alternate scene and content so scrolling has rhythm; never stack two long scenes back to back.
- Scene length: 250 to 500vh each (more for journeys). Total pinned scroll under about 1600vh.
- Write the **scene map and design package** (`references/design-package.md`): every scene's start frame, motion, end frame, length, band copy, mobile behavior, and price, plus sections, palette, type, copy. **GATE: one approval of the package before any money moves.**

Read `references/scene-laws.md` before writing any prompt.

## Phase 3: Design direction

Invoke the required sub-skills. Hold the bar in `references/scroll-engine.md` → Design direction: one committed direction from the footage's world, one signature element, rare accent, no pure black/white, no AI-cliché palettes.

## Phase 4: Generate (money watched)

Details and model ids in `references/providers.md`.

1. **Preflight** the exact call: fal `get_pricing`; kie pricing page. Say the USD price. Stills first (cheap), video second.
2. **Stills**: generate every start/end frame. Inspect each yourself (trademarks, anatomy, brand coherence, negative space for text), then show the user.
3. **Model choice**: preflight the same clip on 2 to 3 video models, present real prices, recommend one, user picks.
4. **Clips**: route to kie first when its key works (cheapest). If `media.mjs run` exits 4 (stall/timeout) or 5 (failed), or the model isn't on kie, run the same job on fal (`submit_job` + `check_job`, never `run_model` for video). Log fal jobs with `media.mjs log`.
5. Extract start/mid/end frames and inspect. **⛔ SCENE GATE (every clip):** rebuild `media.mjs gallery`, have the user watch the clip, give your honest critique plus the re-roll price and budget left. Three failed attempts on one concept → change the concept, not the prompt.

Renders take minutes: say so, scaffold the page meanwhile, show nothing finished before the gate passes.

## Phase 5: Process

`references/ffmpeg-recipes.md`: desktop and mobile frame sequences, poster, stills, byte budgets. Raw files and `review/` stay outside the deploy folder.

## Phase 6: Build

Copy `templates/scroll-scenes.js` and `.css` into the site's `assets/`. Follow `references/scroll-engine.md` exactly: markup contract, band pacing, legibility system, text choreography, motion system, quality floor. Everything below and between scenes is a real website: real copy in buyers' words, proof, objections answered, one form or CTA, nav, footer (fictional-brand disclosure when invented).

**Copy GATE before showing anyone:** grep for em dashes and the words leverage, seamless, empower, unlock, robust, actionable, data-driven, solutions, testament, landscape, delve, elevate. Zero hits, whole file. Deliberate brand devices from the package stay.

## Phase 7: Self-test

Run the checklist in `references/scroll-engine.md` before the user sees anything. If the app's preview pane is hidden, rAF never fires and the page looks dead: test with the Playwright MCP instead. Preview for the user over a local server (`npx http-server` in the site folder), opened in their real browser. Then take feedback in rounds: structure, polish, motion.

## Phase 8: Ship and polish

`references/deploy.md`. Verify live with real requests, measure page weight and load, have the user test on their phone. After launch you are their on-call developer: plain-words change → edit → redeploy.

## References

- `references/providers.md`: fal MCP and kie API usage, model ids, prices, routing, logging, budget
- `references/scene-laws.md`: laws for footage that scrubs well, prompt templates, chaining, bridges
- `references/scroll-engine.md`: engine contract, pacing, legibility, choreography, motion, design bar, quality floor, self-test
- `references/ffmpeg-recipes.md`: sequences, posters, stills, trims, joins
- `references/design-package.md`: the scene map + package template
- `references/deploy.md`: static deploy and live verification
- `references/troubleshooting.md`: symptom → cause → fix
