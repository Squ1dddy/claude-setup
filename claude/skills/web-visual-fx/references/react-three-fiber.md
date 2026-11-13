# React Three Fiber (R3F) reference

Verified against `pmndrs/react-three-fiber` source, `@react-three/fiber@9.7.0` (docs/, readme.md, packages/fiber). Anything marked `@react-three/drei` is a separate package; only helpers that appear in the R3F repo docs/examples are listed here.

## What it is

A React renderer for three.js. You write three.js objects as JSX (`<mesh>`, `<boxGeometry>`) inside `<Canvas>`; R3F creates, updates and disposes the underlying `THREE.*` instances. Nothing is wrapped or hidden: every three.js class and property is available, and a new three.js feature works without an R3F update.

### Reach for it when

- Hero section with a real 3D scene (rotating product, abstract geometry, model with lighting).
- Product / model viewer (GLTF with orbit controls, environment lighting).
- Interactive background canvas behind HTML content (particles, shader plane, pointer-reactive mesh).
- The site is already React (Vite, Next.js). R3F needs React; for a non-React site use plain three.js.

### Do NOT reach for it when

- The effect is a gradient, blur, glass, noise or simple parallax. CSS (or a small 2D canvas / single shader) is far cheaper; three + R3F + React adds a meaningful bundle and a GPU context.
- The page is content/SEO first (blog, docs, landing copy). Canvas content is not indexable or selectable; keep real text in HTML.
- The audience is heavily low-end mobile, or the 3D adds nothing the user needs. WebGL drains battery (docs: the 60fps loop "is what generally drains batteries the most").

## Install

```bash
npm install three @react-three/fiber
# optional helpers
npm install @react-three/drei
```

Version pairing (from `packages/fiber/package.json` peerDependencies and install docs):

| fiber | react / react-dom | three |
| --- | --- | --- |
| `@react-three/fiber@9` (9.7.0) | `>=19 <19.3` | `>=0.156` |
| `@react-three/fiber@8` | 18 | |

"Fiber is a React renderer, it must pair with a major version of React." fiber@8 pairs with react@18, fiber@9 with react@19. Install drei at the major whose peer deps accept fiber 9 (check `npm view @react-three/drei peerDependencies`; the repo's own example still pins an older drei, so don't copy that).

Ecosystem named in the readme: `@react-three/drei` (helpers), `@react-three/gltfjsx` (GLTF to JSX), `@react-three/postprocessing` (post-processing effects), `@react-three/uikit`, `@react-three/test-renderer`. Community: `r3f-perf` (perf overlay), `troika-three-text`, `THREE.MeshLine`, `THREE-CustomShaderMaterial`.

### Vite

Works out of the box (`npm create vite`, pick React, install the two packages).

### Next.js

- R3F docs: works out of the box, but add `transpilePackages: ['three']` to `next.config.js` (Next 13.1+) for untranspiled three add-ons. Official starter: `pmndrs/react-three-next`.
- App Router (Next.js convention, not in R3F docs): any file using `Canvas`, R3F hooks, or event handlers must be a Client Component, so put `'use client'` at the top of the scene file. If the scene touches `window`/`document` at module level, or you want it out of the server bundle entirely, load it with `next/dynamic` and `{ ssr: false }` from a client component. Verify against current Next docs.

## Canvas

`<Canvas>` fills its parent (it renders a `div` at `width: 100%; height: 100%`), so size the parent. It accepts normal div props (`className`, `style`, `aria-*`) because `CanvasProps` extends `React.HTMLAttributes<HTMLDivElement>`.

Defaults: `WebGLRenderer` with `antialias: true`, `alpha: true` (transparent background), `powerPreference: 'high-performance'`, `outputColorSpace = SRGBColorSpace`, `toneMapping = ACESFilmicToneMapping`. Perspective camera `{ fov: 75, near: 0.1, far: 1000, position: [0, 0, 5] }`.

| Prop | Notes |
| --- | --- |
| `camera` | Props for the default camera, or your own `THREE.Camera`. `camera={{ position: [0, 0, 8], fov: 45 }}` |
| `orthographic` | Use an orthographic camera |
| `dpr` | Pixel ratio. Default `[1, 2]`: clamps `devicePixelRatio` into [min, max]. Pass a number to fix it |
| `gl` | Renderer props `{ antialias: false }`, or a (sync/async) factory `gl={(defaults) => new Renderer(defaults)}` |
| `frameloop` | `'always'` (default), `'demand'` (render only on prop change or `invalidate()`), `'never'` (drive with `advance()`) |
| `shadows` | `true` for PCFSoft, or `'basic' \| 'percentage' \| 'soft' \| 'variance'`, or `gl.shadowMap` props |
| `flat` | `THREE.NoToneMapping` instead of ACESFilmic (use for exact brand colours / unlit look) |
| `linear` | Disable automatic sRGB colour space and gamma correction |
| `legacy` | Disables global `THREE.ColorManagement` |
| `scene`, `raycaster` | Props for the defaults, or your own instances |
| `events` | Event manager factory (`import { events } from '@react-three/fiber'`) |
| `eventSource` | `HTMLElement` or `RefObject<HTMLElement>` to subscribe pointer events on instead of the canvas wrapper. When set, the canvas wrapper gets `pointer-events: none` |
| `eventPrefix` | `'offset'` (default) \| `'client'` \| `'page'` \| `'layer'` \| `'screen'`. Use `'client'` for a fixed full-screen canvas with a shared event source |
| `resize` | react-use-measure options, default `{ scroll: true, debounce: { scroll: 50, resize: 0 } }` |
| `performance` | Regression defaults, e.g. `performance={{ min: 0.5 }}` |
| `fallback` | DOM content rendered inside `<canvas>` when WebGL is unsupported ("similar to img's alt prop") |
| `onCreated` | `(state) => {}` after first render |
| `onPointerMissed` | Clicks that hit no object |

Also guard against WebGL context crashes (disabled GPU, bad drivers) with an error boundary around `<Canvas>`; docs use `use-error-boundary`. Ideally the fallback is a seamless visual replacement (static image of the scene).

## JSX object model

- Every three.js class is a camelCase element: `THREE.Mesh` -> `<mesh>`, `THREE.MeshStandardMaterial` -> `<meshStandardMaterial>`.
- `args` = constructor arguments as an array: `<sphereGeometry args={[1, 32, 32]} />`. Changing `args` reconstructs the object.
- Props set properties. Anything with `.set()` takes its args: `position={[1, 2, 3]}`, `color="hotpink"`. Anything with `setScalar` takes a number: `scale={1.5}`.
- Pierce nested props with dashes: `rotation-x={1}`, `shadow-mapSize={[1024, 1024]}`, `material-uniforms-resolution-value={[512, 512]}`.
- `attach`: binds a child to a parent property. Materials auto-attach to `material`, geometries to `geometry`. Explicit: `attach="attributes-position"`, `attach="material-0"`, `attach="shadow-camera"`, or a function `(parent, self) => (parent.add(self), () => parent.remove(self))`.
- `<primitive object={existing} />` puts an existing object (e.g. `gltf.scene`) in the graph. An object can only be added once; clone to reuse. Primitives are NOT auto-disposed.
- `extend`: registers non-core classes. `extend({ OrbitControls })` then `<orbitControls args={[camera, gl.domElement]} />`; or v9 factory form `const Controls = extend(OrbitControls)` then `<Controls ... />`. Also used for tree-shaking with `createRoot`.
- Disposal: R3F calls `dispose()` on unmounted objects. Put `dispose={null}` on a mesh/group to opt out for shared/cached assets (applies to the whole subtree).
- `ShaderMaterial` uniforms: passing a new `uniforms` object merges into the existing one. Mutate `ref.current.uniforms.time.value` in `useFrame`, not your memoised object.
- TypeScript: `useRef<THREE.Mesh>(null!)`; props type `ThreeElements['mesh']`; custom elements via `declare module '@react-three/fiber' { interface ThreeElements { foo: ThreeElement<typeof Foo> } }`.

## Hooks (only inside `<Canvas>` children, never in the component that renders `<Canvas>`)

### `useFrame((state, delta, xrFrame) => {}, renderPriority?)`

Runs before every rendered frame; auto-unsubscribes on unmount. `delta` is seconds since last frame, `state.clock.elapsedTime` is total time.

- Mutate refs, never `setState` in here.
- Use `delta` so speed is refresh-rate independent: `ref.current.rotation.y += delta * 0.5`.
- A positive `renderPriority` takes over rendering (you must call `gl.render(scene, camera)`); used by effect composers. Negative values only order callbacks.

### `useThree(selector?)`

Reactive root state: `gl`, `scene`, `camera`, `raycaster`, `pointer` (normalised -1..1, replaces deprecated `mouse`), `clock`, `size` (px), `viewport` (three units; `viewport.width` spans the screen at z=0), `frameloop`, `performance`, `events`, plus `set`, `get`, `invalidate`, `advance`, `setSize`, `setDpr`, `setFrameloop`, `setEvents`.
Always select to avoid re-renders: `const viewport = useThree((s) => s.viewport)`. Selecting deep three internals (`s.camera.zoom`) is not reactive.

### `useLoader(Loader, url | url[], extensions?, onProgress?)`

Suspends until loaded, caches by URL (same URL anywhere = same asset). Wrap consumers in `<Suspense>`. Accepts a loader class or (v9) a loader instance. Results with a `.scene` get `{ nodes, materials }`. Preload: `useLoader.preload(GLTFLoader, '/model.glb')`. Draco via the extensions callback: `(loader) => loader.setDRACOLoader(draco)`. Don't mutate/dispose cached assets you reuse.

### `useGraph(object3d)`

Memoised `{ nodes, materials }` for any Object3D.

### Top-level exports worth knowing

`invalidate`, `advance`, `extend`, `createPortal`, `createRoot`, `events`, `applyProps`, `addEffect`, `addAfterEffect`, `addTail`.

## Events

Declared on any raycastable object: `onClick`, `onContextMenu`, `onDoubleClick`, `onWheel`, `onPointerUp`, `onPointerDown`, `onPointerOver`, `onPointerOut`, `onPointerEnter`, `onPointerLeave`, `onPointerMove`, `onPointerMissed`, `onUpdate`.

- Event includes DOM event data plus intersection: `object`, `eventObject`, `point`, `distance`, `intersections`, `ray`, `camera`, `unprojectedPoint`, `sourceEvent`, `delta` (px between down and up).
- Objects are transparent to events by default: the event hits the nearest object, bubbles through ancestors, then continues to farther objects. `e.stopPropagation()` stops delivery to objects behind. An occluding object needs its own handler that calls it.
- `onPointerEnter/Leave` behave exactly like Over/Out.
- Pointer capture: `e.target.setPointerCapture(e.pointerId)`.
- Raycasting only runs on user interaction; call `state.events.update()` if the camera moves under a still cursor.
- Hover cursor: set `document.body.style.cursor` in over/out handlers (plain DOM, no R3F API).

## @react-three/drei helpers confirmed in the R3F repo

| Helper | Use |
| --- | --- |
| `OrbitControls` | Camera orbit/zoom; `makeDefault`. Drei controls call `invalidate` for you under `frameloop="demand"` |
| `Environment` | Image-based lighting; `preset="sunset"`, `background` to show it |
| `useGLTF` | GLTF loader hook (`const { nodes, materials, scene } = useGLTF(url)`), `useGLTF.preload(url)` |
| `useTexture` | Texture loader; array or object form (`useTexture({ map: 'a.jpg', normalMap: 'b.jpg' })`, spread into material) |
| `useFBX` | FBX loader hook |
| `Html` | DOM inside the scene (`<Html center>`); good for loaders/labels |
| `useProgress` | Loading progress (`const { progress } = useProgress()`) |
| `Preload` | `<Preload all />` precompiles/uploads everything |
| `PerformanceMonitor` / `usePerformanceMonitor` | FPS-based `onIncline`/`onDecline`/`onChange({ factor })`/`onFallback`, `flipflops` |
| `Detailed` | LOD by camera distance: `<Detailed distances={[0, 10, 20]}>` |
| `Points`, `Line`, `Hud`, `PerspectiveCamera`, `TransformControls`, `Bounds`, `useFBO`, `useCamera` | Seen in repo examples |

### Web-design drei helpers (from pmndrs/drei docs via context7, drei 10.7.8, peers: react ^19, three >=0.159, fiber ^9)

| Helper | Key props (defaults) |
| --- | --- |
| `<Float>` | `speed` (1), `rotationIntensity` (1), `floatIntensity` (1), `floatingRange` ([-0.1, 0.1]), `autoInvalidate` (needed with `frameloop="demand"`) |
| `<MeshTransmissionMaterial>` | glass/liquid look on 3D meshes. Extends meshPhysicalMaterial: `transmission` (1), `thickness` (0), `roughness` (0), `chromaticAberration` (0.03), `anisotropicBlur` (0.1), `distortion` (0), `distortionScale` (0.5), `temporalDistortion` (0), `samples` (6), `resolution` (fullscreen; set e.g. 512 for perf), `backside` (false, costlier), `transmissionSampler` (false) |
| `<Text>` | SDF text (troika). Suspense-based. `font` (url), `color`, `anchorX`, `anchorY`, `characters` (preload glyphs) |
| `<ScrollControls>` + `useScroll()` | scroll-driven scenes. `pages` (1), `damping` (0.2s), `distance` (1), `horizontal` (false), `infinite` (false, experimental), `maxSpeed` (Infinity), `prepend`, `enabled`, `style` |
| `<ContactShadows>` | cheap grounding shadow: `opacity`, `scale`, `blur`, `far`, `resolution`, `color`, `frames={1}` for static objects |

For anything else in drei, check context7 `/pmndrs/drei` before use. Post-processing is `@react-three/postprocessing` (separate package, not documented here).

GLTF workflow: run the model through gltfjsx (`https://gltf.pmnd.rs/` or `npx gltfjsx`) to get a typed, reusable JSX component with `dispose={null}` and `useGLTF.preload`.

## Performance rules (from pitfalls.mdx + scaling-performance.mdx)

1. Never `setState` in `useFrame`, intervals, or fast events (`onPointerMove`). Mutate refs: `onPointerMove={(e) => (ref.current.position.x = e.point.x)}`.
2. Use `delta`, not fixed increments. Animate with `THREE.MathUtils.lerp` in `useFrame`, or `@react-spring/three` (`a.mesh`).
3. Don't bind fast-changing store state reactively; read it in `useFrame` (`api.getState().x` with zustand).
4. Don't allocate in the loop: create `new THREE.Vector3()` once (module scope or `useMemo`) and `.set()` it.
5. Share geometries and materials (`useMemo` or module scope) instead of one per mesh. Every material/light compiles.
6. Don't mount/unmount to switch views; toggle `visible`. Use `startTransition` for expensive state changes.
7. Draw calls: keep to a few hundred, never above ~1000. Use `<instancedMesh args={[null, null, count]}>` + `setMatrixAt` + `instanceMatrix.needsUpdate = true` for many similar objects.
8. `frameloop="demand"` for scenes that come to rest (product viewers). Call `invalidate()` after imperative mutations; it only flags one frame. With demand, `useFrame` animations stop when nothing invalidates.
9. Clamp `dpr`: default `[1, 2]` is sensible; `[1, 1.5]` for heavy scenes/backgrounds. Adapt with drei `PerformanceMonitor` (`onDecline={() => setDpr(1)}`).
10. Movement regression: call `state.performance.regress()` while controls move; read `state.performance.current` (1 = full, down to `min`) to scale dpr or skip effects: `setDpr(window.devicePixelRatio * current)`.
11. LOD with drei `Detailed`; nested `<Suspense>` to show a low-res model while the high-res one loads.
12. Load via `useLoader`/`useGLTF` (cached), never `new TextureLoader().load` in an effect per instance.
13. Dispose: automatic for JSX-created objects; you own disposal of `primitive` objects and anything created outside React. `root.unmount()` for `createRoot`.
14. Global materials/colours created outside Canvas: ensure `THREE.ColorManagement.enabled = true` (r150+).

## Accessibility and UX

- `prefers-reduced-motion`: read `window.matchMedia('(prefers-reduced-motion: reduce)').matches` and either skip motion in `useFrame` or use `frameloop="demand"` (static render). Not an R3F API; plain DOM.
- Always provide `fallback` (static image or HTML) and an error boundary. Content that matters (headings, CTAs, product info) lives in HTML, not the canvas.
- Decorative background canvas: `aria-hidden="true"` on the Canvas (it accepts div props).
- Don't block scroll or clicks: for a background canvas either set `pointer-events: none` via `style`, or give it an `eventSource` (the wrapper then gets `pointer-events: none` automatically while the scene still receives pointer data). OrbitControls on a full-page canvas hijacks wheel/touch; confine controls to a sized viewer, disable zoom on hero scenes.
- Suspense fallback (`<Html center>` with `useProgress`) so users see progress on large models.
- Mobile: lower `dpr`, fewer lights/shadows, compressed (Draco) GLTF; consider not mounting the canvas at all below a breakpoint.

## Example 1: basic scene

```jsx
import { useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'

function Box(props) {
  const ref = useRef()
  const [hovered, hover] = useState(false)
  const [active, setActive] = useState(false)
  useFrame((state, delta) => (ref.current.rotation.x += delta))
  return (
    <mesh
      {...props}
      ref={ref}
      scale={active ? 1.5 : 1}
      onClick={() => setActive(!active)}
      onPointerOver={(e) => (e.stopPropagation(), hover(true))}
      onPointerOut={() => hover(false)}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color={hovered ? 'hotpink' : 'orange'} />
    </mesh>
  )
}

export default function Scene() {
  return (
    <div style={{ height: '60vh' }}>
      <Canvas camera={{ position: [0, 0, 5] }} dpr={[1, 2]} fallback={<img src="/scene.jpg" alt="" />}>
        <ambientLight intensity={Math.PI / 2} />
        <pointLight position={[10, 10, 10]} />
        <Box position={[-1.2, 0, 0]} />
        <Box position={[1.2, 0, 0]} />
      </Canvas>
    </div>
  )
}
```

## Example 2: GLTF product hero (on-demand rendering)

```jsx
'use client' // Next.js App Router only
import { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { Environment, Html, OrbitControls, useGLTF, useProgress } from '@react-three/drei'

function Loader() {
  const { progress } = useProgress()
  return <Html center>{progress.toFixed(0)} %</Html>
}

function Model(props) {
  const { scene } = useGLTF('/product.glb')
  return <primitive object={scene} {...props} />
}
useGLTF.preload('/product.glb')

export default function ProductHero() {
  return (
    <div style={{ height: '80vh' }} aria-label="3D view of the product">
      <Canvas frameloop="demand" dpr={[1, 1.5]} camera={{ position: [0, 1, 4], fov: 40 }}
        fallback={<img src="/product.jpg" alt="Product" />}>
        <Suspense fallback={<Loader />}>
          <Model />
          <Environment preset="sunset" />
        </Suspense>
        <OrbitControls makeDefault enableZoom={false} />
      </Canvas>
    </div>
  )
}
```

`enableZoom` is a three.js OrbitControls property passed through. For a reusable model with correct disposal, prefer the gltfjsx output (`nodes`/`materials`, `<group dispose={null}>`).

## Example 3: full-page background canvas behind HTML

```jsx
import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

const reduceMotion =
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

function Blob() {
  const ref = useRef()
  const target = new THREE.Vector3()
  useFrame((state, delta) => {
    ref.current.rotation.y += delta * 0.2
    // follow pointer (normalised -1..1) in viewport units
    target.set((state.pointer.x * state.viewport.width) / 4, (state.pointer.y * state.viewport.height) / 4, 0)
    ref.current.position.lerp(target, 0.05)
  })
  return (
    <mesh ref={ref}>
      <icosahedronGeometry args={[1.5, 4]} />
      <meshStandardMaterial color="#6d5dfc" roughness={0.3} />
    </mesh>
  )
}

export default function Page() {
  const root = useRef()
  return (
    <div ref={root} style={{ position: 'relative' }}>
      <Canvas
        aria-hidden="true"
        style={{ position: 'fixed', inset: 0, zIndex: -1 }}
        eventSource={root}
        eventPrefix="client"
        frameloop={reduceMotion ? 'demand' : 'always'}
        dpr={[1, 1.5]}
        gl={{ antialias: false }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[3, 3, 5]} />
        <Blob />
      </Canvas>
      <main>{/* real, scrollable, selectable HTML content */}</main>
    </div>
  )
}
```

With `eventSource` set, the canvas wrapper is `pointer-events: none`, so scrolling, text selection and links work, while `state.pointer` still tracks the cursor over the whole page. `eventPrefix="client"` because the canvas is fixed to the viewport. In Next.js, read `matchMedia` in an effect (or use `setFrameloop` from `useThree`) to avoid hydration mismatch.

## v8 -> v9 migration gotchas

- Requires React 19 (`>=19 <19.3`). fiber 8 stays on React 18. Upgrade drei/postprocessing to their fiber-9-compatible majors at the same time.
- `gl` callback receives renderer constructor props, not the canvas: `gl={(props) => new WebGLRenderer(props)}`; may return a promise (WebGPU: `new THREE.WebGPURenderer(props)` + `await renderer.init()`, import from `three/webgpu`).
- Texture colour space: automatic sRGB conversion of texture props removed. Built-in materials handle colour maps; for custom shaders set `texture.colorSpace = THREE.SRGBColorSpace` (or `texture-colorSpace={THREE.SRGBColorSpace}`).
- StrictMode from the parent react-dom root now applies inside Canvas; remove nested `<StrictMode>` and expect dev-only double effects to surface side-effect bugs.
- Types: `Props` -> `CanvasProps`; `MeshProps` etc. removed, use `ThreeElements['mesh']`; `Node`/`Object3DNode`/`MaterialNode`... replaced by `ThreeElement<typeof X>`; global `JSX.IntrinsicElements` augmentation replaced by `declare module '@react-three/fiber' { interface ThreeElements {...} }`.
- `useLoader` accepts a loader instance; `extend(Class)` returns a component.
- Testing: `act` comes from `react`, not the renderer.
