---
name: ux-feel
description: Checklist of 20 small UX details (skeletons, optimistic updates, undo toasts, command menu, tabular numbers, safe areas, OTP autofill, idempotency, etc.) plus the Doherty 400ms rules, for making an app feel fast and expensive. Use when auditing or building product UI (forms, lists, mutations, loading states, mobile sheets) and the question is "does it feel right", not "what should it look like". Pairs with impeccable (direction) and design-motion-principles (motion). Source: saved Instagram reels (murphmaxxing 20-tips list, brochbuilds Doherty rules), rewritten, not copied; the creators' full prompts were not obtained.
---

# ux-feel

Run as an audit: for each item, grep the code, mark HAVE / GAP / N/A for this product, and only propose the GAPs that fit the product's register. Respect the project's PRODUCT.md / DESIGN.md first: a calm desk tool may reject motion-heavy items (view transitions, swipe, spring physics).

## Doherty rules (respond under ~400 ms)
1. Every tap acknowledges instantly (pressed state, even if the work is async).
2. Show the result first, save in the background (optimistic), roll back with a message on failure.
3. Start slow work early (prefetch, pre-render, upload while the user is still typing the caption).
4. Loading: a skeleton shaped like the page, not a spinner.
5. Anything longer than a few seconds: a real progress indicator.

## The 20
Loading and speed
1. Skeleton loaders (route-level `loading.tsx`, matching layout).
2. Optimistic updates (`useOptimistic` / local state), with rollback.
3. Stale-while-revalidate: show cached data, refresh behind it.
4. Pre-rendering / prefetch the likely next screen.
5. BlurHash / dominant-colour placeholders for images.

Keyboard and power use
6. Command menu (Cmd/Ctrl+K): jump to anything, run common actions.
7. Shortcut hints shown beside actions (`<kbd>`).
8. Undo toasts instead of confirm dialogs for reversible actions.

Motion and touch
9. View transitions between routes (only if the product's motion rules allow).
10. Swipe-to-dismiss bottom sheets on mobile.
11. Interruptible animations (reversing mid-flight, no queue-up).
12. Predictive back (Android PWA back gesture preview).
13. Hit slop: tap target at least 44px even when the visual is smaller.
14. Safe-area insets (`env(safe-area-inset-*)`) on fixed bars and sheets.
15. One-time-code autofill (`autocomplete="one-time-code"`, numeric inputmode).

Typography and shape
16. Tabular numbers (`tabular-nums`) on scores, prices, tables, timers.
17. Balanced headlines (`text-wrap: balance`).
18. Continuous (squircle) corners (`corner-shape: squircle` with a normal `border-radius` fallback).

Correctness under repeat taps
19. Idempotency keys on mutations, so a double tap or retry never double-writes.
20. Safe triangle for hover flyout menus (cursor path to a submenu doesn't close it).

## Output
A table: item, HAVE / GAP / N/A, evidence (file:line), and for GAPs a one-line fit verdict (worth it / skip because the register rejects it). No code changes until asked.
