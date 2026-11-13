# ShaderGradient (ruucm/shadergradient)

Animated 3D mesh gradients rendered with three.js via React Three Fiber (R3F). A noise-displaced plane, water plane or sphere is lit and shaded with three colors, optionally with a halftone "grain" post pass. Verified against `@shadergradient/react` v2.4.24 source.

## When to use

- Use for: hero backgrounds, full-page fixed backgrounds, feature section backdrops, "liquid" or "aurora" brand moments where motion and depth are the point.
- Use a CSS gradient instead when: the gradient is static or a simple linear/radial blend, the page is text-heavy or perf-critical (low-end mobile, many sections), you are not in React, or you need it inside email or print. ShaderGradient costs a WebGL context, the three.js + R3F bundle, and continuous GPU work.
- One instance per viewport. Each `ShaderGradientCanvas` is its own WebGL context; browsers cap live contexts (~8-16).

## Install

```
npm i @shadergradient/react @react-three/fiber three three-stdlib camera-controls
npm i -D @types/three
```

(README install line. `three-stdlib`, `camera-controls` and `query-string` are dev deps bundled into the dist, so strictly only the peers are required, but follow the README.)

Peer deps (package.json): `react ^18.2.0 || ^19.0.0`, `react-dom` same, `three >=0.150.0`, `@react-three/fiber >=8.0.0`. README recommends `three >=0.158.0`.

Compatibility (README):

| Environment | React | @react-three/fiber | three |
| --- | --- | --- | --- |
| Next 15 App Router | `^19.0.0` | `^9.0.0` (v8 breaks) | `>=0.158.0` |
| Next 14, Next 15 Pages, Vite, etc. | `^18` or `^19` | matching `8.x` (React 18) / `9.x` (React 19) | `>=0.158.0` |

No `next.config` aliases or `transpilePackages` needed on these combos. ESM only (`dist/index.mjs`).

Exports: `ShaderGradientCanvas`, `ShaderGradient`, types (`GradientT`, `MeshT`, ...), `presets`, `presetsArray`, `formatUrlString`, Framer helpers.

Non-React: no vanilla JS/Vue/Webflow build (listed as future plan). Framer: paste `https://framer.com/m/ShaderGradient-oWuS.js` onto the Framer canvas. Figma: community plugin 1203016883447870818.

## Basic usage

```tsx
import { ShaderGradientCanvas, ShaderGradient } from '@shadergradient/react'

<ShaderGradientCanvas style={{ position: 'absolute', inset: 0 }} pixelDensity={1.5} fov={45}>
  <ShaderGradient cDistance={32} cPolarAngle={125} />
</ShaderGradientCanvas>
```

`ShaderGradient` must be a child of `ShaderGradientCanvas` (it uses R3F hooks). The canvas renders a wrapper `div` sized `width:100%; height:100%` merged with `style`, so the parent must have a real size.

### Next.js (App Router)

The package has no `'use client'` directive. Put it in a client component:

```tsx
// components/GradientBg.tsx
'use client'
import { ShaderGradientCanvas, ShaderGradient } from '@shadergradient/react'

export default function GradientBg() {
  return (
    <ShaderGradientCanvas pointerEvents='none' style={{ position: 'fixed', inset: 0, zIndex: -1 }}>
      <ShaderGradient type='waterPlane' color1='#ff5005' color2='#dbba95' color3='#d0bce1' grain='off' />
    </ShaderGradientCanvas>
  )
}
```

Optional (official App Router example does this): skip SSR and keep three.js out of the server bundle.

```tsx
'use client'
import dynamic from 'next/dynamic'
const GradientBg = dynamic(() => import('@/components/GradientBg'), { ssr: false })
```

`dynamic(..., { ssr: false })` must itself live in a client component in Next 15.

## ShaderGradientCanvas props

| Prop | Type | Default | Notes |
| --- | --- | --- | --- |
| `children` | ReactNode | required | Put `<ShaderGradient />` here |
| `style` | CSSProperties | `{}` | Applied to the wrapper div (merged over 100%/100%) |
| `className` | string | - | Applied to the R3F `<Canvas>`, not the wrapper |
| `pixelDensity` | number | `1` | Canvas DPR. 1 fast, 2 sharp and slow |
| `fov` | number | `45` | Camera field of view |
| `pointerEvents` | `'none' \| 'auto'` | undefined | On the canvas element. Set `'none'` for backgrounds (see Gotchas) |
| `envBasePath` | string | `https://ruucm.github.io/shadergradient/ui@0.0.0/assets/hdr/` | Folder with `city.hdr`, `dawn.hdr`, `lobby.hdr`, used when `lightType='env'` |
| `lazyLoad` | boolean | `true` | IntersectionObserver: Canvas mounts only while in view, unmounts when out |
| `threshold` | number | `0.1` | IntersectionObserver threshold |
| `rootMargin` | string | `'0px'` | IntersectionObserver rootMargin |
| `preserveDrawingBuffer` | boolean | undefined | Needed for canvas screenshots/export |
| `powerPreference` | `WebGLPowerPreference` | undefined | `'default' \| 'high-performance' \| 'low-power'` |

Fixed internally: `linear: true`, `flat: true`, `resize={{ offsetSize: true }}`, canvas `id='gradientCanvas'`. Changing `pixelDensity` or `fov` remounts the whole Canvas (it is the React `key`). No `frameloop` passthrough.

## ShaderGradient props

Defaults: every prop falls back to the `halo` preset (`{ ...presets.halo.props, ...props }`), except in `control='query'` mode (see URL config).

### Shape and motion (MeshT)

| Prop | Type | Default (halo) | Notes |
| --- | --- | --- | --- |
| `type` | `'plane' \| 'sphere' \| 'waterPlane'` | `'plane'` | plane: 10x10, 1x192 segments. waterPlane: 192x192 segments (heavier). sphere: icosahedron |
| `shader` | string | `'defaults'` | One of `'defaults' \| 'positionMix' \| 'cosmic' \| 'glass'` (each has all 3 types). Anything else crashes |
| `animate` | `'on' \| 'off'` | `'on'` | Off stops the clock; `uTime` stays at its prop value |
| `uTime` | number | `0` | Start time / frozen frame when `animate='off'` |
| `uSpeed` | number | `0.4` | Animation speed |
| `uStrength` | number | `4` | Noise displacement strength |
| `uDensity` | number | `1.3` | Noise density |
| `uFrequency` | number | `5.5` | Wave frequency |
| `uAmplitude` | number | `1` | Wave amplitude; only used by sphere vertex shaders |
| `range` | `'enabled' \| 'disabled' \| string` | `'disabled'` | When `'enabled'`, time loops rangeStart to rangeEnd |
| `rangeStart` | number | `0` | Seconds |
| `rangeEnd` | number | `40` | Seconds, must be > rangeStart |
| `loop` | `'on' \| 'off'` | undefined (off) | Seamless loop; takes priority over `range` |
| `loopDuration` | number | undefined (5 in shader) | Seconds per loop |
| `positionX/Y/Z` | number | `-1.4 / 0 / 0` | Mesh position |
| `rotationX/Y/Z` | number | `0 / 10 / 50` | Mesh rotation in degrees |
| `color1/2/3` | string | `'#ff5005' / '#dbba95' / '#d0bce1'` | Must be 6-digit `#rrggbb` or `rgb(r, g, b)`. Named colors throw; `#fff` renders black |
| `reflection` | number | `0.1` | Material roughness = 1 - reflection (ignored by glass) |
| `wireframe` | boolean | `false` | Typed but not wired up in v2 (no effect) |
| `rotSpringOption`, `posSpringOption` | any | - | Typed, unused in v2 |

### Camera, light, effects (GradientT)

| Prop | Type | Default (halo) | Notes |
| --- | --- | --- | --- |
| `cAzimuthAngle` | number | `180` | Camera azimuth, degrees |
| `cPolarAngle` | number | `90` | Camera polar angle, degrees |
| `cDistance` | number | `3.6` | Camera distance; used for plane/waterPlane only |
| `cameraZoom` | number | `1` | Camera zoom; used for sphere only (sphere distance fixed at 14) |
| `enableTransition` | boolean | `true` | Camera animates to new angles/distance; `false` snaps |
| `smoothTime` | number | `0.05` | camera-controls damping |
| `zoomOut` | boolean | undefined | Forces a fixed zoomed-out view (editor tool) |
| `lightType` | `'3d' \| 'env'` | `'3d'` | 3d: ambient light. env: HDR environment (network fetch) |
| `brightness` | number | `1.2` | Only for `lightType='3d'` (ambient intensity x PI) |
| `envPreset` | `'city' \| 'dawn' \| 'lobby'` | `'city'` | Only for `lightType='env'` |
| `grain` | `'on' \| 'off'` | `'on'` | On adds a halftone post-processing pass (extra full-screen pass) |
| `grainBlending` | number | - | Typed, not wired up in v2 |
| `toggleAxis` | boolean | undefined | Shows axis helper (debug) |
| `control` | `'query' \| 'props'` | undefined (props) | `'query'` reads config from `urlString` |
| `urlString` | string | - | Customizer URL or query string, used with `control='query'` |
| `onCameraUpdate` | `(u: Partial<GradientT>) => void` | - | Fires after user drags/zooms: `cAzimuthAngle`, `cPolarAngle`, plus `cDistance` (planes) or `cameraZoom` (sphere) |
| `isFigmaPlugin`, `hoverState`, `enableCameraUpdate` | - | - | Typed, unused by the renderer |

Preset objects also contain `pixelDensity` and `fov`; those do nothing on `ShaderGradient`. Set them on the canvas.

## Presets

`import { presets, presetsArray } from '@shadergradient/react'`. Keys and look:

| Key | Title | type | Colors |
| --- | --- | --- | --- |
| `halo` | Halo (the default) | plane | `#ff5005 #dbba95 #d0bce1`, grain on |
| `pensive` | Pensive | sphere | `#809bd6 #910aff #af38ff`, grain on |
| `mint` | Mint | waterPlane | `#94ffd1 #6bf5ff #ffffff` |
| `interstella` | Interstella | sphere, lightType env | `#73bfc4 #ff810a #8da0ce`, grain on |
| `nightyNight` | Nighty night | waterPlane | `#606080 #8d7dca #212121`, grain on |
| `violaOrientalis` | Viola | sphere | `#ffffff #ffbb00 #0700ff` |
| `universe` | Universe | waterPlane | `#5606ff #fe8989 #000000` |
| `sunset` | Sunset | sphere, envPreset dawn | `#ff7a33 #33a0ff #ffc53d` |
| `mandarin` | Mandarin | waterPlane | `#ff6a1a #c73c00 #FD4912` |
| `cottonCandy` | Cotton Candy | waterPlane | `#ebedff #f3f2f8 #dbf8ff` |

Use and override (non-halo presets infer `type` as `string`, so cast for TS):

```tsx
import { presets, type GradientT } from '@shadergradient/react'
<ShaderGradient {...(presets.mint.props as GradientT)} grain='off' color3='#e0f7ff' />
```

Extra preset keys (`frameRate`, `format`, `embedMode`, ...) are harmless.

## URL config (shadergradient.co customizer)

1. Design at https://www.shadergradient.co/customize, copy the page URL.
2. Pass it with `control='query'`:

```tsx
<ShaderGradient
  control='query'
  urlString='https://www.shadergradient.co/customize?animate=on&cDistance=3.6&cPolarAngle=90&color1=%2352ff89&color2=%23dbba95&color3=%23d0bce1&lightType=3d&shader=defaults&type=plane&uFrequency=5.5&uSpeed=0.4&uStrength=4'
/>
```

How it works (source): `formatUrlString` strips only the prefixes `https://www.shadergradient.co/customize`, `https://shadergradient.co/customize` and `http://localhost:3001/customize`, then `query-string` parses the rest with `parseNumbers` and `parseBooleans`. So:
- Pass the full customizer URL or just `?key=value&...`. Any other host prefix breaks parsing.
- In query mode the parsed object replaces props entirely: halo defaults are NOT merged and other JSX props (like `grain='off'`) are ignored. Missing keys become undefined, so keep the full customizer URL; `shader` and `type` must be present or the mesh crashes.
- `pixelDensity`/`fov` in the URL are ignored; set them on `ShaderGradientCanvas`.
- `onCameraUpdate` still works in query mode.

To tweak a customizer design in code, convert the URL params to props instead (query-string decodes `%23` to `#`).

## Performance

- `pixelDensity`: default 1. Use 1 on mobile and for full-screen backgrounds; 1.5 max on desktop. Do not toggle it at runtime (remounts the Canvas and recompiles shaders).
- `grain='off'` removes a full-screen post pass. Halo default is on.
- Prefer `plane` over `waterPlane` (192x192 segments) on weak devices.
- `lightType='env'` downloads three HDR files (all three are loaded regardless of `envPreset`) from GitHub Pages. Prefer `'3d'`, or self-host and set `envBasePath`.
- Offscreen: `lazyLoad` (default true) unmounts the Canvas when not intersecting, which frees the GPU but causes a remount and shader compile on scroll-back. For a hero that users scroll back to, consider `rootMargin='200px'`. For a `position: fixed` background it is always in view, so it never pauses.
- `animate='off'` freezes the gradient but R3F still renders every frame (frameloop is `'always'`, not configurable). To truly stop GPU work, unmount the canvas.
- `powerPreference='low-power'` on laptops/mobile to prefer the integrated GPU.

Reduced motion:

```tsx
'use client'
import { useEffect, useState } from 'react'

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false)
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReduced(mq.matches)
    const on = (e: MediaQueryListEvent) => setReduced(e.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return reduced
}

// <ShaderGradient animate={reduced ? 'off' : 'on'} uTime={2} ... />
// Or for zero GPU cost: render a static CSS gradient / image when reduced.
```

## Gotchas

- Camera controls are always attached: drag rotates, wheel dollies/zooms, one-finger touch rotates. On backgrounds this steals page scroll and moves the view. Always set `pointerEvents='none'` on `ShaderGradientCanvas` for backgrounds.
- Give the parent a size, or the wrapper div is 0px tall.
- Place content above with z-index. The package sets no scene background, so where the mesh does not cover the view the page behind shows through; tune `cDistance`/position/rotation if edges show.
- Colors: 6-digit hex only (or `rgb()`).
- React 19 + Next 15 App Router needs R3F v9.

## Example: full-screen fixed background

```tsx
'use client'
import { ShaderGradientCanvas, ShaderGradient } from '@shadergradient/react'

export default function Page() {
  return (
    <>
      <ShaderGradientCanvas
        pointerEvents='none'
        pixelDensity={1}
        style={{ position: 'fixed', inset: 0, zIndex: -1 }}
      >
        <ShaderGradient
          type='plane'
          color1='#ff5005'
          color2='#dbba95'
          color3='#d0bce1'
          uSpeed={0.2}
          grain='off'
          lightType='3d'
          brightness={1.2}
        />
      </ShaderGradientCanvas>
      <main style={{ position: 'relative' }}>{/* content */}</main>
    </>
  )
}
```

## Example: hero section

```tsx
'use client'
import { ShaderGradientCanvas, ShaderGradient, presets, type GradientT } from '@shadergradient/react'

export function Hero() {
  return (
    <section style={{ position: 'relative', height: '100svh', overflow: 'hidden' }}>
      <ShaderGradientCanvas
        pointerEvents='none'
        pixelDensity={1.5}
        rootMargin='200px'
        style={{ position: 'absolute', inset: 0 }}
      >
        <ShaderGradient {...(presets.nightyNight.props as GradientT)} grain='off' />
      </ShaderGradientCanvas>
      <div style={{ position: 'relative', zIndex: 1, display: 'grid', placeItems: 'center', height: '100%' }}>
        <h1>Headline</h1>
      </div>
    </section>
  )
}
```
