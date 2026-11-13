# liquid-glass-js (dashersw/liquid-glass-js)

Apple "Liquid Glass" style refracting glass panels and buttons. MIT, (c) 2025 Armagan Amcalar. Single initial commit, demo at https://dashersw.github.io/liquid-glass-js/. Verified against source (container.js, button.js, glass.css, demo.js, controls.js).

## How it works (read before choosing it)

1. On the first `new Container()`/`new Button()`, it calls `html2canvas(document.body, { scale: 1, useCORS: true, allowTaint: true, backgroundColor: null })`, skipping any element with class `glass-container`, `glass-button` or `glass-button-text`. The result is stored once in the static `Container.pageSnapshot`.
2. Each instance owns a `<canvas>` with its **own WebGL 1 context** (`getContext('webgl', { preserveDrawingBuffer: true })`; the README says WebGL 2, the code does not use it). The snapshot is turned into a data URL and uploaded as a texture, once per instance.
3. A fragment shader samples the snapshot at the element's page position (`getBoundingClientRect()` center + `scrollY`), bends the lookup along a shape-aware normal (rounded rect / circle / pill SDF), applies an approx 13x13 Gaussian blur, a white-to-grey vertical tint and a tint sampled from the page, then masks to the shape.
4. Standalone instances re-render only on `window` `scroll` (passive listener). Buttons nested in a Container run a `requestAnimationFrame` loop forever, copying the parent canvas into their texture every frame (`texSubImage2D`) and refracting that.

Implications:
- It refracts a **static screenshot** of the page, not the live DOM. Animations, video, carousels, hover states, lazy-loaded images, content injected after capture and route changes do NOT show through until the snapshot is recaptured.
- html2canvas limits apply: cross-origin images without CORS headers, iframes, video, and CSS it does not implement (backdrop-filter, many filters and blend modes) are missing or wrong in the snapshot.
- Vertical scroll is tracked; horizontal scroll is not (only `scrollY` is fed to the shader). Works for `position: fixed` overlays over scrolling content (the demo does exactly this).
- The glass never refracts its own children or other glass elements (they are excluded from the capture). Only nested Buttons refract their parent Container.
- Cost: whole-body capture (slow on long or heavy pages, main-thread), one PNG encode + decode + full-page texture upload **per instance**, one WebGL context per instance (browsers drop the oldest after roughly 16), and roughly 800 texture fetches per pixel in the container shader. Keep glass elements few and small.
- Snapshot is taken at `scale: 1` and canvases are not DPR-scaled, so on retina screens the glass is rendered at CSS-pixel resolution (soft edges).
- Very tall pages can exceed `MAX_TEXTURE_SIZE` (often 4096 to 16384 px, lower on mobile) or iOS canvas area limits, and the upload fails silently or shows black.

Browser support: needs WebGL 1, ES2022 static class fields, optional chaining. Realistically Chrome/Edge 80+, Firefox 75+, Safari 14.1+. No WebGL: logs `WebGL not supported` and leaves a transparent box (no fallback built in).

## Install / load

Not on npm (no package.json; README roadmap still lists "Bundle for NPM"). No build step, no ES exports. Dependency: `html2canvas` as a **global** (called bare). Vendoring options:

- Plain HTML: copy `container.js`, `button.js`, `glass.css` into your project and load as classic scripts, in this order:
```html
<link rel="stylesheet" href="/vendor/liquid-glass/glass.css" />
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script src="/vendor/liquid-glass/container.js"></script>
<script src="/vendor/liquid-glass/button.js"></script>
```
  `class` declarations in classic scripts are global bindings but are NOT on `window` (`window.Container` is undefined; plain `Container` works).
- Bundlers (Vite/Next): `npm i html2canvas`, then concatenate container.js + button.js into one `liquid-glass.js`, add `import html2canvas from 'html2canvas'` at the top and `export { Container, Button }` at the bottom. Keep them in one file: `Container.addChild` references `Button` (`instanceof`), so separate modules would be circular. Keep the MIT notice at the top.

## API (from source)

### `new Container(options)`
| Option | Default | Notes |
| --- | --- | --- |
| `borderRadius` | `48` | px. Uses `||`, so `0` becomes 48. Overridden for `pill` (height/2) and `circle` (size/2). |
| `type` | `'rounded'` | `'rounded'`, `'circle'` (forced square from the larger side), `'pill'`. |
| `tintOpacity` | `0.2` | 0 to 1, per instance (`!== undefined` check, so 0 is allowed). |

No other options. Container has no `warp` (always off).

Properties: `element` (the `div.glass-container` to insert), `canvas`, `children`, `width`, `height`, `gl_refs` (gl + uniform locations), `webglInitialized`, `render()` (set after WebGL init).
Methods: `addChild(child)` (appends `child.element`, sets `child.parent`, sets up nested glass if child is a Button, returns child), `removeChild(child)`, `updateSizeFromDOM()` (measures on next rAF, resizes canvas and nested children), `getPosition()`.
Statics: `Container.instances` (every instance ever created, never pruned), `Container.pageSnapshot`, `Container.isCapturing`, `Container.waitingForSnapshot`.
No `destroy()`, no events, no resize handling.

### `new Button(options)` (extends Container)
| Option | Default | Notes |
| --- | --- | --- |
| `text` | `'Button'` | Set as `textContent` of `div.glass-button-text`. |
| `size` | `48` | Font size px, `parseInt`ed (strings OK). Drives the whole size. |
| `type` | `'rounded'` | rounded: radius = size, min box = textWidth + 2*size by 2.5*size. pill: textWidth + 2*size by 2.2*size, radius = h/2. circle: diameter 2.5*size. |
| `onClick` | `null` | Called as `onClick(text)` on `click`, after `e.preventDefault()`. |
| `warp` | `false` | Enables center (base) distortion. |
| `tintOpacity` | `0.2` | As Container. |

`borderRadius` is NOT a Button option (README example passes it; it is ignored). Text measured with `system-ui, -apple-system, sans-serif`.

### Nesting rules
- Only `Button` children get nested glass (they sample the parent's rendered canvas). A Container added to a Container is just appended and refracts the page snapshot on its own.
- Nested button blur default is 2.0 (vs 5.0 standalone); it waits (100 ms polling) for the parent's WebGL.
- Any other DOM can be appended to `container.element` directly (controls.js does this for its panel); the canvas sits at `z-index: -1` behind it.

### Global shader tuning: `window.glassControls`
Read once per instance at shader setup (define it before creating instances). Keys and fallback defaults: `edgeIntensity 0.01`, `rimIntensity 0.05`, `baseIntensity 0.01`, `edgeDistance 0.15`, `rimDistance 0.8`, `baseDistance 0.1`, `cornerBoost 0.02`, `rippleEffect 0.1`, `blurRadius 5.0` (nested: 2.0). Uses `||`, so a `0` falls back to the default. `tintOpacity` and `warp` in this object are only used by the demo's `updateAllGlassInstances()`, not by the library. README slider ranges: edgeIntensity 0-0.1, rimIntensity 0-0.2, baseIntensity 0-0.05, edgeDistance 0.05-0.5, rimDistance 0.1-2.0, baseDistance 0.05-0.3, cornerBoost 0-0.1, rippleEffect 0-0.5, blurRadius 1-15.
Live update (pattern from controls.js; each instance has one program, so this is safe):
```js
Container.instances.forEach(i => {
  const r = i.gl_refs; if (!r.gl) return
  r.gl.uniform1f(r.blurRadiusLoc, 8); r.gl.uniform1f(r.tintOpacityLoc, 0.3)
  i.render && i.render()
})
```

## Required CSS/HTML
- Include `glass.css`. It makes `.glass-container` `position: relative; display: flex; gap: 20px; padding: 10px`, and styles `.glass-button`, `.glass-button-circle`, `.glass-container-circle`, `.glass-container-pill`, `.glass-button-text` (absolute-centered, `color: white`, `pointer-events: none`, `white-space: nowrap`).
- The library creates all markup; you only append `instance.element`. Append it **in the same tick** you construct it: size is read from the DOM on the next animation frame. If you insert later, call `updateSizeFromDOM()` afterwards.
- An empty Container is only 20x20 (padding). Give it children or a CSS width/height.
- The canvas uses `z-index: -1`. If no ancestor forms a stacking context it can drop behind a section background. Add `.glass-container { isolation: isolate; }` (the demo avoids this via a fixed parent with `z-index: 9999`).
- There must be something visually busy behind the glass (image, gradient) or it looks like a grey box.

## Minimal plain-HTML example
```html
<!doctype html>
<html><head>
<link rel="stylesheet" href="glass.css" />
<style>
  body { margin: 0; min-height: 200vh; background: url(bg.jpg) center/cover; }
  #bar { position: fixed; top: 24px; left: 50%; transform: translateX(-50%); z-index: 10; }
</style>
</head><body>
<div id="bar"></div>
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script src="container.js"></script>
<script src="button.js"></script>
<script>
  // wait for images/fonts so they are in the snapshot
  window.addEventListener('load', async () => {
    await document.fonts.ready
    const nav = new Container({ type: 'pill', tintOpacity: 0.15 })
    document.getElementById('bar').appendChild(nav.element)
    ;['Home', 'Work', 'Contact'].forEach(t =>
      nav.addChild(new Button({ text: t, size: 16, type: 'pill', onClick: x => location.hash = x }))
    )
  })
</script>
</body></html>
```

## React / Next.js
- Client only: `'use client'` component, create instances inside `useEffect` (html2canvas and WebGL need `window`). Or `dynamic(() => import('./Glass'), { ssr: false })`. Render a CSS-fallback element in SSR so layout does not jump.
- Use the vendored ESM file (see Install). Append `instance.element` into a ref'd host div inside the effect.
- Cleanup is DIY (no destroy). In the effect cleanup: `el.remove()`; splice the instance(s) out of `Container.instances`; `gl.getExtension('WEBGL_lose_context')?.loseContext()`; set `inst.gl_refs = {}` so `render()` no-ops. The scroll listener (anonymous) and nested rAF loop keep running regardless; if you care, patch the vendored copy to store the listener and rAF id and add a `destroy()`.
- StrictMode mounts effects twice in dev: without cleanup you get duplicate glass and leaked contexts.
- The snapshot is static and global. On client-side route changes, set `Container.pageSnapshot = null` before creating instances, or new pages refract the old page.

## Gotchas
- Resize: the library ignores it. Copy demo.js's debounced (300 ms) `resize` handler, which recaptures with html2canvas and re-uploads textures for every instance (and resizes nested button textures). Layout shifts without scrolling also leave stale glass: call `inst.updateSizeFromDOM()` and `inst.render()`.
- Recapture after any meaningful DOM/content change behind the glass; it is expensive, so debounce and do it rarely.
- Mobile: full-page capture is slow and memory-heavy; texture size limits bite on long pages; per-instance contexts multiply memory. Prefer the CSS fallback on small screens or `pointer: coarse`.
- Motion: standalone glass is static between scrolls; nested buttons animate a rAF loop continuously (battery). The library has no `prefers-reduced-motion` handling; skip `warp` and nesting when it is set.
- `prefers-reduced-transparency: reduce` (limited browser support) and `prefers-contrast: more`: do not init the library, render an opaque surface instead. Also fall back when `!document.createElement('canvas').getContext('webgl')`.
- Accessibility: Buttons are `div`s with a click listener only: no `role`, no `tabindex`, no keyboard. Add `el.setAttribute('role','button')`, `tabIndex = 0`, an Enter/Space `keydown` handler, and `aria-label` for icon/emoji labels. Or put a real `<button>`/`<a>` inside a Container instead of using Button.
- Contrast: text is white on a lightly tinted, blurred copy of whatever is behind. Check contrast against the worst-case background; raise `tintOpacity`, add a `text-shadow`, or set a darker text color via `.glass-button-text`.
- Noise: logs `Capturing page snapshot...` to the console on every capture.
- License MIT: keep the copyright notice in vendored files.

## CSS-only fallback (use when the library is overkill)
Live, cheap, works over video and animations; no refraction, just blur and a rim.
```css
.glass {
  background: rgb(255 255 255 / 0.14);
  border: 1px solid rgb(255 255 255 / 0.28);
  border-radius: 999px;
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.45), inset 0 -1px 0 rgb(0 0 0 / 0.08),
    0 12px 32px rgb(0 0 0 / 0.18);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  backdrop-filter: blur(14px) saturate(160%);
  color: #fff;
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .glass { background: rgb(30 30 36 / 0.85); }
}
@media (prefers-reduced-transparency: reduce), (prefers-contrast: more) {
  .glass { background: rgb(30 30 36 / 0.95); -webkit-backdrop-filter: none; backdrop-filter: none; }
}
```
Rule of thumb: one or two hero glass elements over a static, image-heavy page -> liquid-glass-js. Navbars over scrolling/changing content, many elements, mobile-first -> CSS fallback.
