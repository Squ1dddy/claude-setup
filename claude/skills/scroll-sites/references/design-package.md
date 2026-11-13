# The Design Package

The single deliverable of Phase 2: every creative and cost decision, written before any money moves, approved once, then consumed by the build. Copy in it ships verbatim. Numbers are starting points validated by the flick test.

## 1. Brand premise

One short paragraph built on ONE real word or idea from the subject's world. Every scene, section, and the interactive moment serve it.

## 2. Page rhythm

The page top to bottom as one list, alternating scenes and content:

```
nav
SCENE 1  "pour"      sequence   420vh
section  problem     (depth scene, data-speed layers)
SCENE 2  "unfold"    bridge     350vh
section  how it works / proof
SCENE 3  "arrive"    sequence   300vh   -> settles into the CTA
section  FAQ, form, footer
```

## 3. Scene map

One block per scene:

| Field | Content |
|---|---|
| Type | sequence / bridge / journey (n segments) / depth |
| Carries | which page beat or message this scene delivers |
| Start frame | full still description (what the scene shows before pinning) |
| Motion | camera move + subject journey, at steady speed |
| End frame | full still description; how it hands off to the next section |
| Length | `--len` in vh (starting point) |
| Mobile | portrait crop at focus x=__ / static |
| Model + price | chosen model, preflighted USD for stills + clip |

## 4. Band map (per scene)

| Scene | Band | Range | Footage moment | Copy (verbatim) | Entrance |
|---|---|---|---|---|---|
| 1 | 1 | 0.00 to 0.30 | what the frames show | "The exact words." | drift down |
| 1 | 2 | 0.34 to 0.66 | ... | "..." | scatter |

Plus the `data-static` band per scene: the one composed line static visitors see.

## 5. Palette tokens

Direction named from the storyboard now; exact values sampled from approved footage after the gates.

```css
:root{--canvas:#___;--panel:#___;--accent:#___;--accent-hover:#___;--accent-muted:#___;--text-primary:#___;--text-secondary:#___}
```

## 6. Type trio

Display (characterful, from the brand's world, never Inter/Roboto), body, mono. Faces and exact weights.

## 7. Content sections

Each section between scenes with verbatim copy, in buyers' language: problem, how it works, proof/testimonials, pricing if a product, FAQ answering the researched objections, the one form or CTA (and where its submissions honestly go), footer (fictional-brand disclosure when invented). Name the one interactive moment and its section, and the vector layer (self-drawing lines, motifs, particles).

## 8. Budget

| Item | Model | Provider | USD |
|---|---|---|---|
| Scene 1 start frame | | | |
| Scene 1 clip | | | |
| ... | | | |
| **Total** | | | **$__ of $__ budget** |

Plus one line: expected re-roll cost per clip.

## 9. Gates inherited by the build

Package approval → still inspection → scene gate per clip → copy grep gate → self-test checklist (`scroll-engine.md`) → user preview → live verification.
