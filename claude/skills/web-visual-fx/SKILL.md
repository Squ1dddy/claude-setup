---
name: web-visual-fx
description: Implementation toolkit for premium visual effects on websites - 3D scenes (React Three Fiber), liquid/Apple-style glass UI (liquid-glass-js), animated shader gradient backgrounds (ShaderGradient), and liquid/chrome animated logos (liquid-logo shader). Use on ANY web design task - building, designing or redesigning a website, landing page, hero section, portfolio, product page, background, or UI component - and whenever the user mentions 3D, three.js, WebGL, shaders, glass, glassmorphism, gradients, animated backgrounds or logo effects. Runs after /impeccable sets direction; supplies the how, not the whether.
---

# Web Visual FX

Four effect libraries, one decision layer. Direction comes first: if `/impeccable` is in play, it decides the look. This skill only answers "does one of these effects serve that direction, and how do I build it properly".

## Step 1: Should any effect be used at all?

Default is NO effect unless it earns its place. Use one when:
- The direction calls for depth, motion or a signature moment (hero, brand intro, product showcase).
- It carries meaning (product shown in 3D, brand logo in brand material), not decoration.

Skip when: content/docs/dashboard/app UI where speed and legibility win, school or office tools (e.g. Traksy) beyond a subtle accent, low-end mobile audiences, or the page already has a hero effect. Max ONE heavy WebGL effect per viewport; never stack two canvases on screen.

## Step 2: Pick the tool

| Need | Use | Reference |
|---|---|---|
| Real 3D: models, product viewer, interactive scene, particles, custom shaders, scroll-driven 3D | React Three Fiber (+ drei) | `references/react-three-fiber.md` |
| Animated mesh-gradient / blob background for hero or section | ShaderGradient | `references/shadergradient.md` |
| Apple "liquid glass" refracting panels, buttons, nav bars | liquid-glass-js (or CSS `backdrop-filter` fallback) | `references/liquid-glass-js.md` |
| Logo rendered as liquid metal / chrome, animated | liquid-logo shader (export video, or port shader) | `references/liquid-logo.md` |

Cheaper alternatives to check first: static gradient or CSS `@property` animated gradient instead of ShaderGradient; `backdrop-filter: blur()` instead of liquid-glass-js; exported MP4/WebM loop instead of a live liquid-logo canvas. Pick the live version only when interactivity or crispness at any size matters.

Read ONLY the reference for the chosen tool. Do not load all four.

## Step 3: Non-negotiables for every effect

- **Stack fit:** R3F and ShaderGradient need React. In a plain HTML site use vanilla three.js or the vendored scripts instead. In Next.js: client component (`'use client'`) and dynamic import with `ssr: false` for canvas code.
- **Reduced motion:** honour `prefers-reduced-motion: reduce` (stop animation or show static frame). Glass: also check `prefers-reduced-transparency`.
- **Fallback:** page must look intended with WebGL off or failed (static image/gradient poster behind the canvas).
- **Performance:** clamp DPR (max 2, often 1.5), pause when offscreen (IntersectionObserver / `frameloop="demand"`), lazy-load below-the-fold effects, dispose on unmount. Test on mobile width.
- **Legibility:** text over effects must hit WCAG AA contrast; add a scrim if needed.
- **Layout:** background canvases `position: fixed/absolute; inset: 0; z-index: -1; pointer-events: none` unless interactive; never block scroll or steal touch.
- **Licenses:** check the reference's license notes before shipping commercially.
- Verify current API with context7 if a reference looks stale (references written 2026-09-21 from repo source).

## Sources

- https://github.com/pmndrs/react-three-fiber
- https://github.com/ruucm/shadergradient
- https://github.com/dashersw/liquid-glass-js
- https://github.com/collidingScopes/liquid-logo
