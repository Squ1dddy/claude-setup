# liquid-logo (collidingScopes/liquid-logo)

Liquid metal / chrome / plasma animation clipped to a logo's shape. One WebGL1 fragment shader over a full-screen quad, driven by a transparent PNG of the logo. Live tool: https://collidingscopes.github.io/liquid-logo

## What it is
- A standalone static web app (vanilla JS, global scripts, dat.GUI from CDN, bundled mp4-muxer). **Not an npm library**: no package.json, no exports, no build. Scripts share globals (`gl`, `canvas`, `params`) and are loaded in order by index.html: shaders.js, presets.js, mp4-muxer, canvasVideoExport.js, background-removal.js, gui-controls.js, main.js.
- Shader derived from XorDev's "Plasma" shader (README acknowledgment). Simplex noise block is the standard Ashima/McEwan webgl-noise `snoise`, pasted without its header.
- The tool's index.html also loads Umami analytics; don't copy that into a client site.

## Choose a path
**(a) Export from the tool, embed the file (default for most sites).** Zero runtime GPU cost, no WebGL code to maintain, works everywhere.
- Upload logo, pick a preset / tweak / press R to randomize, then export.
- PNG export (`S`): transparent background (single still frame).
- Video export (`V` start/stop, length is however long you record, animation time resets on start): desktop Chromium/Safari use WebCodecs `VideoEncoder` (`avc1.4d0032`, 16 Mbps, 30 fps) + mp4-muxer; iOS/Android/Firefox use `canvas.captureStream(30)` + `MediaRecorder`. The mobile path passes `{ type: 'video/mp4' }`, which is not a MediaRecorder option (it's `mimeType`), so the file is the browser default container (e.g. WebM on Firefox) despite the `.mp4` name. Check the file.
- **H.264 has no alpha**: the transparent area in the MP4 will not stay transparent (expect black; verify). Place it on a matching solid background, or on a black section. For transparency over arbitrary backgrounds use path (b).
- No GIF export (README's gif was made externally). Convert if needed: `ffmpeg -i in.mp4 -vf "fps=24,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" out.gif`. Prefer MP4/WebM over GIF (smaller, sharper).
- Loops are not seamless: time feeds `cos(...+time)` and 3D noise, nothing is periodic. Keep clips long, or crossfade the ends in an editor.
- Embed: `<video autoplay muted loop playsinline preload="metadata" poster="logo-still.png" width height aria-label="...">`.

**(b) Port the shader as a live canvas.** Use when you need true transparency over changing backgrounds, runtime param changes (hover, scroll, theme), responsive crispness at any DPR, or tiny payload vs a long video. Costs a full-screen fragment shader with up to 15 loop iterations plus 6 texture reads per logo pixel every frame.

## How the shader works (fragment-shader.glsl)
Vertex shader is just `gl_Position = vec4(aVertexPosition, 0.0, 1.0);` over a 4-vertex TRIANGLE_STRIP quad (-1..1).

Per fragment:
1. `uv = gl_FragCoord.xy / u_resolution`; `logoUV = (uv - 0.5) / u_logoScale + 0.5`; `logoUV.y = 1.0 - logoUV.y` (shader does its own flip, texture uploaded without UNPACK_FLIP_Y).
2. **Mask**: `logoAlpha = texture2D(u_logoTexture, logoUV).a`; inside if `alpha > 0.1`. Outside the shape (or outside 0..1 logoUV) the pixel is transparent / discarded. Only alpha defines the shape; logo colours are ignored except in edge detection.
3. **Edges** (no distance field): `detectEdges` samples center + 4 neighbours at 1 canvas pixel (`1/u_resolution`) and sums RGBA differences, `smoothstep(0, 0.2, diff)`, times `u_logoInteractStrength`. So internal colour boundaries in the logo also count as edges.
4. **Flow field**: `p = (FC*2 - r) / r.y` (aspect-correct, resolution independent). `l.x = abs(u_dotFactor - dot(p,p)) * u_dotMultiplier` (radial ring term). `v = p*(1-l.x)/u_scale`, plus edge push `vec2(sin(edge*10), cos(edge*8)) * edge*20`, plus `snoise(vec3(p*2, time*0.15)) * u_noiseIntensity`.
5. **Plasma loop**: `for i < 16, break at u_iterations`: `v += cos(v.yx*idx + vec2(0,idx) + time)/idx + u_vOffset` (offset multiplied by `1+edge*4` near edges); `o += (sin(v.xyyx)+1) * abs(v.x-v.y) * u_intensityFactor`.
6. Colour: optional channel rotate `o = o.wxyz*colorShift + o*(1-colorShift)`; then manual tanh of `exp(p.y*u_colorFactors) * exp(-u_expFactor*l.x) / o` (vertical colour gradient per channel).
7. Film grain (`random`, fixed amplitude), `liquidMetalEffect` edge highlight, clamp; inside logo mixes toward `o*0.8+0.2`, adds `pow(edge*1.2,4)*vec3(0.6,0.7,0.8)` rim highlight, alpha `+0.4`.
`time = u_time * u_speed`, `u_time` in seconds.

### Uniforms
| Uniform | Type | Effect | GUI range |
|---|---|---|---|
| u_resolution | vec2 | drawing-buffer px; used for uv, p, edge step, grain | - |
| u_time | float | seconds (paused time held) | - |
| u_speed | float | time multiplier | 0.1-2.0 |
| u_iterations | float | plasma loop count, **hard-capped at 16 in shader** (GUI allows 24, "Color Smoothing") | 3-24 |
| u_scale | float | pattern zoom (bigger = larger features) | 0.1-4.0 |
| u_dotFactor | float | radius of the radial ring term | 0.1-1.2 |
| u_dotMultiplier | float | strength of ring term (0 = off) | 0-2 |
| u_vOffset | float | constant drift added each iteration | 0-10 |
| u_intensityFactor | float | accumulation gain (lower = brighter after tanh) | 0.05-0.5 |
| u_expFactor | float | how much the ring term darkens/tints | 0.1-5 |
| u_colorFactors | vec3 | per-channel vertical gradient (red/green/blueFactor) | -3..3 each |
| u_colorShift | float | channel rotation blend | 0-2 |
| u_noiseIntensity | float | simplex flow distortion | 0-10 |
| u_logoTexture | sampler2D | logo, unit 0 | - |
| u_logoScale | float | logo zoom within canvas (presets force 1.0) | 0.5-3 |
| u_logoInteractStrength | float | edge interaction; presets exceed GUI range | 0-0.3 |
| u_logoOpacity, u_logoAspectRatio, u_logoBlendMode | float/float/int | **declared but no effect**: `applyBlendMode` and `applyNoiseDistortion` are never called; aspect is unused | - |

Defaults in gui-controls.js `params`: speed 2.2, iterations 13, scale 0.05, dotFactor 0.1, vOffset 6.4, intensityFactor 0.23, expFactor 0.6, dotMultiplier 0.3, noiseIntensity 4.0, colours 0, colorShift 0, logoOpacity 1, logoScale 1, logoInteractStrength 0.4. Page load applies preset "Galaxy" on top.

### Presets (presets.js)
Order: speed, iterations, scale, dotFactor, dotMultiplier, vOffset, intensityFactor, expFactor, noiseIntensity, r, g, b, colorShift, logoInteractStrength. `-` = key missing in preset, so the tool keeps the previous value; in a port set it explicitly (defaults: dotMultiplier 0.3, noiseIntensity 4.0).
| Preset | spd | it | scale | dotF | dotM | vOff | int | exp | noise | r | g | b | cShift | edge |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Glow | 0.34 | 15 | 3.11 | 0.66 | 0.36 | 6.0 | 0.1 | 1.8 | 0.5 | 0.2 | 0.0 | -0.2 | 0.5 | 0.66 |
| Wisp | 0.7 | 11 | 0.112 | 0.28 | - | 0.0 | 0.12 | 0.1 | - | 1.5 | 1.1 | 1.0 | 0.8 | 0.5 |
| Smoke | 1.42 | 6 | 0.17 | 0.27 | 0.0 | 4.8 | 0.16 | 4.9 | - | -0.4 | -0.3 | 0.1 | 0.0 | 0.25 |
| Oil Slick | 0.67 | 8 | 0.22 | 0.15 | 0.79 | 6.3 | 0.2 | 0.1 | - | -0.9 | -1.9 | -0.2 | 2.0 | 0.35 |
| Chrome | 0.4 | 15 | 3.12 | 0.04 | 0.21 | 5.1 | 0.07 | 0.2 | - | 1.1 | 0.7 | 0.9 | 0.9 | 0.4 |
| Rainbow | 0.56 | 11 | 1.2 | 0.699 | 0.56 | 6.1 | 0.258 | 3.0 | - | -0.2 | 1.1 | -1.7 | 0 | 0.38 |
| Liquid | 0.33 | 14 | 1.49 | 0.03 | 0.66 | 0.1 | 0.07 | 3.5 | - | -1.2 | 0.6 | 0.6 | 0.2 | 0.39 |
| Magic | 0.5 | 5 | 1.05 | 0.269 | 0.79 | 6.5 | 0.315 | 4.0 | 1.7 | -0.1 | 1.9 | 0.2 | 0.3 | 0.5 |
| Dusk | 0.45 | 15 | 2.8 | 0.02 | 0.56 | 6.1 | 0.2 | 0.5 | - | 1.9 | 0.3 | 0.4 | 0.9 | 0.52 |
| Galaxy | 0.44 | 8 | 2.63 | 0.03 | 0.61 | 0.0 | 0.37 | 0.5 | - | 1.0 | -0.3 | 1.6 | 0.1 | 0.1 |
Best way to get params for a port: tune in the live tool, open the console, `copy(JSON.stringify(params))`.

## Logo image requirements
- Transparent PNG (or SVG rasterised to canvas). Shape = alpha > 0.1, so alpha must be clean; soft/feathered edges shrink the shape.
- The tool pads the logo into a **square** canvas (centered, longest side capped at `MAX_DIMENSION = 1500`, dims rounded to multiples of 4) and sizes the WebGL canvas to that same square. The shader maps the whole canvas to the texture, so **a non-square canvas stretches the logo**. Keep canvas square, or pad the texture to the canvas aspect yourself.
- Solid, bold shapes read best; thin strokes and small text get lost (edge band is ~1 canvas px, plasma needs area). Flat colour logos are ideal; gradients/photos inside the logo create extra internal "edges".
- 1000-1500 px on the long side is plenty.
- background-removal.js (tool upload only, demo logos skip it): samples the 4 corners; if they agree and luminance is > 200 (white) or < 30 (black), flood-fills from the corners with colour threshold 30 and sets alpha 0. Anything else is left untouched. It does not reach enclosed background (inside an "O") and leaves anti-aliased halos. Prefer supplying a real transparent PNG. On failure the tool falls back to the raw image (no transparency = whole square animates).
- Demo logos in `assets/` (Apple, Nike, PlayStation, etc.) are third-party trademarks; never ship them.

## Port: minimal vanilla WebGL
Copy `vertex-shader.glsl` and `fragment-shader.glsl` verbatim (inline as strings or import `?raw` in Vite). Keep the MIT notice (see License).
```js
export function createLiquidLogo(canvas, { src, params, maxDpr = 2 }) {
  const gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: false, antialias: true,
    depth: false, stencil: false, preserveDrawingBuffer: false }); // tool uses true only for PNG export
  if (!gl) return null;                                            // caller shows fallback <img>
  const sh = (type, s) => { const x = gl.createShader(type); gl.shaderSource(x, s); gl.compileShader(x);
    if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(x)); return x; };
  const prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog); gl.useProgram(prog);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(prog, 'aVertexPosition');
  gl.enableVertexAttribArray(aPos); gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
  const U = n => gl.getUniformLocation(prog, 'u_' + n);
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); // same as tool, keeps its look

  const tex = gl.createTexture(); let ready = false;
  const img = new Image(); img.crossOrigin = 'anonymous';
  img.onload = () => {                          // pad into a square, like resizeAndCreateLogoTexture
    const s = Math.min(1500, Math.max(img.width, img.height)), k = s / Math.max(img.width, img.height);
    const c = document.createElement('canvas'); c.width = c.height = s;
    const w = img.width * k, h = img.height * k;
    c.getContext('2d').drawImage(img, (s - w) / 2, (s - h) / 2, w, h);
    gl.bindTexture(gl.TEXTURE_2D, tex);         // NPOT ok: clamp + linear, no mipmaps
    for (const p of [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T]) gl.texParameteri(gl.TEXTURE_2D, p, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c);
    ready = true;
  };
  img.src = src;

  const resize = () => {                        // square canvas, DPR-aware backing store
    const css = canvas.clientWidth, dpr = Math.min(devicePixelRatio || 1, maxDpr);
    canvas.width = canvas.height = Math.round(css * dpr);
  };
  const ro = new ResizeObserver(resize); ro.observe(canvas); resize();

  let raf = 0, t = 0, last = performance.now(), running = false;
  const frame = now => {
    t += (now - last) / 1000; last = now;       // accumulated time: no jump after pause
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    if (ready) {
      const P = params;
      gl.uniform2f(U('resolution'), canvas.width, canvas.height); gl.uniform1f(U('time'), t);
      for (const k of ['speed','iterations','scale','dotFactor','dotMultiplier','vOffset',
        'intensityFactor','expFactor','noiseIntensity','colorShift','logoScale','logoInteractStrength'])
        gl.uniform1f(U(k), P[k]);
      gl.uniform3f(U('colorFactors'), P.redFactor, P.greenFactor, P.blueFactor);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(U('logoTexture'), 0);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
    if (running) raf = requestAnimationFrame(frame);
  };
  const start = () => { if (!running) { running = true; last = performance.now(); raf = requestAnimationFrame(frame); } };
  const stop = () => { running = false; cancelAnimationFrame(raf); };
  const renderOnce = () => { last = performance.now(); frame(last); }; // for reduced motion
  const destroy = () => { stop(); ro.disconnect(); gl.deleteTexture(tex); gl.deleteBuffer(buf);
    gl.deleteProgram(prog); gl.getExtension('WEBGL_lose_context')?.loseContext(); };
  return { start, stop, renderOnce, destroy };
}
```
Notes: cache uniform locations in a real build (lookups per frame are cheap but wasteful). `params` needs every key listed (use a preset table row + defaults). Cross-origin logo needs CORS headers or the texture upload throws. Handle `webglcontextlost` if the page is long-lived (re-init on `webglcontextrestored`). Canvas CSS: `aspect-ratio: 1; width: min(60vw, 480px)`.

## React wrapper
```jsx
export function LiquidLogo({ src, params, fallback, alt, className }) {
  const ref = useRef(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;                                   // render the static fallback instead
    const fx = createLiquidLogo(ref.current, { src, params });
    if (!fx) { setFailed(true); return; }
    const io = new IntersectionObserver(([e]) => (e.isIntersecting ? fx.start() : fx.stop()));
    io.observe(ref.current);
    const vis = () => (document.hidden ? fx.stop() : fx.start());
    document.addEventListener('visibilitychange', vis);
    return () => { io.disconnect(); document.removeEventListener('visibilitychange', vis); fx.destroy(); };
  }, [src]);                                              // params: pass a ref/object mutated in place to avoid re-init
  const reduce = typeof window !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (failed || reduce) return <img src={fallback} alt={alt} className={className} />;
  return <canvas ref={ref} role="img" aria-label={alt} className={className} />;
}
```
StrictMode mounts twice in dev: the cleanup must fully destroy (it does, via loseContext). Next.js: mark `'use client'` and avoid reading `matchMedia` during SSR (use a state set in an effect to prevent hydration mismatch).

## R3F alternative (three ShaderMaterial)
Use plain `ShaderMaterial` (not Raw): three injects GLSL1 compat defines (`texture2D`, `gl_FragColor`) under WebGL2, so the fragment file works unchanged. Replace the vertex shader, since three's attribute is `position`:
```jsx
const vert = 'void main(){ gl_Position = vec4(position.xy, 0.0, 1.0); }';
function LiquidLogoMesh({ url, p }) {
  const tex = useTexture(url, t => { t.flipY = false; });  // shader flips itself; three defaults flipY=true
  const mat = useRef();
  const uniforms = useMemo(() => ({
    u_time: { value: 0 }, u_resolution: { value: new THREE.Vector2() }, u_logoTexture: { value: tex },
    u_colorFactors: { value: new THREE.Vector3(p.redFactor, p.greenFactor, p.blueFactor) },
    ...Object.fromEntries(['speed','iterations','scale','dotFactor','dotMultiplier','vOffset','intensityFactor',
      'expFactor','noiseIntensity','colorShift','logoScale','logoInteractStrength'].map(k => ['u_' + k, { value: p[k] }])),
  }), [tex]);
  useFrame((s, dt) => { const u = mat.current.uniforms; u.u_time.value += dt;
    s.gl.getDrawingBufferSize(u.u_resolution.value); });
  return <mesh frustumCulled={false}><planeGeometry args={[2, 2]} />
    <shaderMaterial ref={mat} vertexShader={vert} fragmentShader={FRAG} uniforms={uniforms}
      transparent depthWrite={false} /></mesh>;
}
```
Caveats: the shader uses `gl_FragCoord` over the whole drawing buffer, so the mesh must fill a dedicated square `<Canvas>`; it cannot be a logo placed inside a larger 3D scene without rewriting uv/p from varyings. The texture must be square-padded (do it on a 2D canvas and use `CanvasTexture`, flipY false). Use `frameloop="demand"` + `invalidate()` or `<Canvas frameloop={visible ? 'always' : 'never'}>` for pausing. Blending differs slightly from the tool (three's normal blending); visually close.

## Perf and accessibility
- Cost scales with canvas pixel count x iterations. Cap DPR at 2 (1.5 on mobile), keep canvas at display size, fewer iterations (6-10) for large canvases. Only logo pixels run the loop; transparent pixels exit early.
- Pause when offscreen (IntersectionObserver) and when tab hidden; one instance per page ideally (browsers cap live WebGL contexts, ~16).
- `prefers-reduced-motion: reduce`: show a static PNG (export one from the tool with `S`) or call `renderOnce()` and never start the loop. For MP4 embeds, drop `autoplay` and show the poster.
- Alt text: canvas gets `role="img"` + `aria-label="<Brand> logo"`; fallback `<img alt>` the same. If the logo is decorative next to a visible brand name, `aria-hidden="true"` and empty alt. Autoplaying video over 5 s needs a pause control (WCAG 2.2.2), or keep it muted, short and non-essential with reduced-motion honoured.
- Provide the static logo as the no-WebGL fallback.

## License
MIT, Copyright (c) 2025 Alan Ang (LICENSE.txt; README: "feel free to use it for personal or commercial purposes").
- Allowed: use, copy, modify, merge, publish, distribute, sublicense, sell, including commercial/client sites.
- Required: include the copyright notice and permission notice "in all copies or substantial portions of the Software". Porting the shader counts: put the MIT notice in a comment at the top of the shader/module file (and in a third-party notices file if the project keeps one).
- Videos/PNGs exported with the tool are output, not the Software; MIT imposes nothing on them (credit is courtesy).
- No warranty, no liability.
- Upstream bits: the simplex noise is Ashima Arts/McEwan webgl-noise (MIT, notice stripped in this repo; keep one if you want to be tidy). The XorDev "Plasma" origin has no license file in the repo; low risk, but flag for strict client legal review.
