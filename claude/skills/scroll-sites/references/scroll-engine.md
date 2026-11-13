# The Scroll Engine and Build Standard

`templates/scroll-scenes.js` + `.css` are tested (desktop scrub frame-exact, phone cover-crop, static fallback, lazy loading, fast reverse flicks, parallax). Copy them into `assets/` unchanged and style around them. Change the engine only for a real need, and re-run the self-test when you do.

## Why image sequences, not video scrubbing

Video seeking stutters on long keyframe intervals, fails on hosts without HTTP Range, and is unreliable on iOS. A canvas drawing pre-decoded frames is frame-exact everywhere, works on phones, and reverses perfectly. The cost is bytes, which the budgets below control.

## Markup contract

```html
<link rel="stylesheet" href="assets/scroll-scenes.css">

<section class="scene" id="scene-pour" style="--len:420vh"
  data-frames="assets/scenes/pour/f_%04d.webp" data-count="80"
  data-frames-mobile="assets/scenes/pour-m/f_%04d.webp" data-count-mobile="48"
  data-poster="assets/scenes/pour/poster.jpg"
  data-focus-x="0.5" data-focus-y="0.5">
  <div class="scene__stage">
    <canvas class="scene__canvas" aria-hidden="true"></canvas>
    <div class="scene__scrim" aria-hidden="true"></div>
    <div class="band" data-in="0.00" data-out="0.30">...</div>
    <div class="band" data-in="0.34" data-out="0.66">...</div>
    <div class="band" data-in="0.70" data-out="1.00" data-static>...</div>
  </div>
</section>

<script src="assets/scroll-scenes.js" defer></script>
```

| Attribute | Meaning |
|---|---|
| `--len` | pinned scroll distance of the scene |
| `data-frames` / `data-count` | frame URL template (ffmpeg `%04d`, numbered from 1) and frame count |
| `data-frames-hd` / `data-count-hd` | native-resolution sequence for large screens (canvas width over 1400 device px). Ship it for any full-bleed scene: 1280px frames visibly pixelate on 1920px+ and Retina screens |
| `data-frames-mobile` / `data-count-mobile` | lighter portrait sequence for phones (optional) |
| `data-mobile="static"` | phones get the poster + `data-static` band instead of frames |
| `data-poster` | first frame jpg: paints instantly, and is the static-mode image |
| `data-focus-x/y` | cover-crop focal point 0 to 1 (keep the subject in frame on portrait) |
| `.band data-in/out` | the band's range of scene progress 0 to 1 |
| `.band data-ramp` | override the assembly window (default `min(0.025, len*0.35)`) |
| `.band data-static` | the one band static visitors see (else the last band) |
| `[data-speed]` | any element: parallax drift factor (0.05 subtle to 0.3 strong, negative reverses) |

Modes are decided live (rotation, resize, reduced-motion flips): `desktop`, `mobile` (mobile set if present, else desktop frames), `static` (reduced motion always; phones when `data-mobile="static"`). CSS hooks: `.scene.is-ready`, `.scene.is-static`, `.has-missing-frames`, `--load` 0 to 1 on the scene, `--k` 0 to 1 on each band. `window.ScrollScenes.scenes` exposes state for tests.

The engine already does: progressive loading (every 8th frame first, then fills in), loading 1.5 viewports ahead, nearest-loaded-frame drawing, dt-normalized lerp, a rAF loop that rests when converged, DPR capped at 2, delta-gated DOM writes, band opacity smoothstep, band one's load-time assembly, tab-hidden animation pause.

## Sizing and byte budgets

| | HD (large screens) | Desktop | Mobile |
|---|---|---|---|
| Frame width | clip native, max 1920px, WebP q85 | 1280px, WebP q78 | 720px portrait crop, q64 |
| Frames | same count as desktop | 1 per 4 to 6vh of `--len` (420vh → 70 to 100) | about 60% of desktop |
| Per-scene weight | ≤ 8 MB | ≤ 5 MB | ≤ 2 MB |
| Page total (all scenes) | ≤ 24 MB, lazy per scene | ≤ 15 MB | ≤ 6 MB |

Only one tier loads per visitor. Frame resolution can't exceed the generated clip: 1080p clips are the ceiling, so for razor-sharp 2560px/Retina full-bleed, generate at 4K or upscale the clip before export (both cost money; preflight).

Too heavy: drop frames (fps) before dropping width, then raise WebP compression. Measure with `ffmpeg-recipes.md`.

Scene length: 250 to 350vh for a simple sequence, 400 to 500vh for a sequence with 3 bands, about 1000vh for an 18s journey. Under-sized scenes make every caption flash past.

## Band pacing (in scroll distance)

- Every band gets a fully visible plateau of about 80 to 130vh, with short eased edges. Convert: band length in vh = `(out - in) * (len - 100vh)`.
- The first band of a scene has no fade-in and the last has no fade-out, so scenes start and end with words settled.
- **Flick test:** from the top, `window.scrollBy(0, step)` every 400ms with steps 120, 240, 360px, logging band opacities. Every band stays readable for 5 to 6 normal flicks; none is skippable at 360px. A failing band merges into a neighbor; never shrink ramps to squeeze it in.

## Legibility over footage

1. **Base scrim** (`.scene__scrim`, in the template): soft radial darkening, always on.
2. **Per-band scrim**: `::before` on the band, deepening with `--k`, dying out by 76% so corners stay alive:
   ```css
   .band::before{content:"";position:absolute;inset:-4%;z-index:-1;pointer-events:none;opacity:calc(.25 + .75*var(--k,1));background:radial-gradient(ellipse 74% 62% at 50% 50%,rgba(5,5,10,.66) 0%,rgba(5,5,10,.44) 46%,rgba(5,5,10,0) 76%)}
   ```
   Peak alpha 0.62 for quiet beats up to 0.72 for the hook. Subject centered with text both sides: two scrims, one per column, center lane untouched.
3. **Text shadow token** on bands, off on buttons: `--tshadow:0 1px 2px rgba(5,5,10,.95),0 3px 12px rgba(5,5,10,.78),0 10px 44px rgba(5,5,10,.8)`.
4. **Chip** for small labels over footage: `background:rgba(8,8,15,.55);border-radius:10px;backdrop-filter:blur(10px)`.

**Worst-frame audit:** for each band, take the frames in its range (`f = round(p * (count-1)) + 1` → `f_%04d.webp`), sample the text zone with the scrim alpha applied, and require worst-pixel contrast ≥ 3.5:1 against the text color. Tune against the worst frame, never the average. With Playwright: hide the glyphs (`visibility:hidden` on spans), screenshot at that scroll position, find the lightest pixel in the text box.

## Text choreography (one entrance per beat, echoing the footage)

Transform and opacity only, driven by the band's `--k`, fully reversible. Split headlines once at load into `.w` word and `.c` character spans with a seeded RNG (`s = (s*1664525 + 1013904223) >>> 0`) so offsets are identical every load; keep a visually-hidden full sentence for screen readers and `aria-hidden` on the split copy.

- **Scatter** (particles gathering): per char `--th` 0 to 0.55, `--jx/--jy/--jr` jitter.
  `.c{--kc:clamp(0,(var(--k,0) - var(--th,0))*2.6,1);opacity:var(--kc);transform:translate(calc((1 - var(--kc))*var(--jx,0px)),calc((1 - var(--kc))*var(--jy,0px))) rotate(calc((1 - var(--kc))*var(--jr,0deg)))}`
- **Grid snap**: scatter with horizontal jitter and ordered thresholds `index/total*spread`.
- **Blur-to-sharp** (mist clearing): two stacked copies, the soft one with a static `filter:blur(10px)`, crossfaded by `--k`. Never animate `filter`.
- **Word punch** (impact): `.w{--kc:clamp(0,(var(--k,0) - var(--th,0))*3,1);--ks:clamp(0,(var(--k,0) - var(--th,0) - .1)*3.2,1);opacity:var(--kc);transform:scale(calc(.6 + .52*var(--kc) - .12*var(--ks)))}`
- **Rise into staged settle** (arrival): words rise in order, subline at `(--k - .66)*4`, CTA at `(--k - .78)*5`.
- **Drift down** (a fall or pour): `translateY(calc((1 - var(--kc))*-24px))`.
- **Approach from depth** (push-in): `scale(calc(.82 + .18*var(--kc)))`.
- **Halves parting** (doors, folds), **weave** (threads): alternating signs of `--jx` / `--jy`.

The menu is examples. Invent the entrance that does to the words what the footage is doing.

## Between scenes: the whole-site-animated standard

- Nothing snaps. Two easing tokens used everywhere; the page itself eases in.
- Section entrances: IntersectionObserver adds `.in`; children stagger 60 to 150ms. Prefix start/end states with the container class so they win the cascade; retire stagger delays afterwards with a selector at least as specific as the nth-child delay rules.
- One living element per section at whisper level (4s+ cycles, negative delays, paused off-screen).
- Self-drawing SVG lines (`stroke-dashoffset` driven by section progress), depth scenes with `data-speed`, particles at whisper level.
- One designed interactive moment per site that performs the brand's one idea (press-and-hold that builds, eases back if released early, completes into revealed content; reduced motion gets the final state).
- Animate only transform and opacity. Never overwrite `el.style.transition` in JS; toggle classes.
- `overflow-x: clip` on both `html` and `body` (with `hidden` declared first).
- Reduced motion honored completely and live: final states shown, drives stopped; flipping back re-arms (the engine already handles scenes).

## Design direction (what expensive means)

- One committed direction from the footage's world driving palette, type, motion, imagery.
- One signature element; test: remove it, does the page meaningfully change?
- No two adjacent sections share a layout skeleton.
- Banned as default reaches (fine when truly the subject's world, said out loud): cream + serif + terracotta, near-black + acid green, near-black + amber + high-contrast serif, hairline brutalism.
- Accent in rare doses. Canvas never pure `#000`/`#fff`; tint toward the footage grade. One fixed background environment layer (grain, slow glow) behind everything.

## Quality floor

- Fonts trimmed to weights used, `preconnect`. Characterful display face (never Inter/Roboto as display), quiet body, mono for labels.
- `ch` max-widths on the text element itself, not a container.
- Contrast computed: 4.5:1 body, 3:1 large text and interactive borders.
- Landmarks: `<nav>`, `<main id="main" tabindex="-1">`, `<footer>`, skip link, real heading order, `aria-hidden` on decoration and canvases.
- `:focus-visible` in the accent; 44px touch targets under `(pointer:coarse)` without changing layout.
- `<title>`, meta description, `theme-color`, inline SVG favicon; `og:image`/`og:url` left as `<!-- DEPLOY STEP -->` until the live URL exists.
- Masked text gets em-based padding so g, y, p tails survive.
- The form's destination is honest (JS success state, mailto, a form service, or a link to real checkout), and the success state matches the truth.

## Self-test checklist (before the user sees anything)

Use the Playwright MCP when the app preview pane is hidden (rAF never fires there). Test-only overrides for media queries go in a scratch copy of the page, never the shipped one.

1. Screenshots at 1440×900, 1280×800, 390×844, 375×667.
2. Every scene: `ScrollScenes.scenes[i].drawn` equals `round(progress*(count-1))` at 0, 0.25, 0.5, 1 after settling. Fast back-and-forth scrolling converges to the right frame.
3. Scenes further down report `loaded: 0` until approached (lazy loading works).
4. Flick test on every scene's bands. Worst-frame legibility audit on every band.
5. Phone width: correct mode per scene, subject survives the crop (adjust `data-focus-x`), no horizontal overflow (`scrollWidth <= innerWidth`).
6. Reduced motion: every scene static with poster + `data-static` band, zero frame requests; flip it live both ways.
7. Delete one frame folder temporarily: poster still shows, page complete, no console errors besides the 404s.
8. Every entrance plays; every button, link and the form work; hovers on staggered siblings respond instantly.
9. Page weight per scene and total within budget (measure the folders).
10. Console clean at desktop and phone sizes.
11. **Fresh eyes last:** look as a first-time visitor. Anything unexplained, unequal, or filler gets fixed before the user sees it.

Report what you found and fixed.
