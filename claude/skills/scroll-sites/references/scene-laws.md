# Scene Laws and Prompt Construction

Scrubbed footage is judged differently from played footage. The visitor sees every frame at their own speed, forwards and backwards, and stops mid-motion to read. These laws predict which clips scrub beautifully and which burn money. Read them before writing any prompt.

## The laws

1. **The motion agrees with the scroll.** Scrolling down must feel like down, forward, opening, or arriving: a descent, a push-in, an unfolding, an assembly. A subject rising while the page moves down fights the visitor.

2. **Steady speed, no bursts.** Scrub exposes speed changes as stutter. Ask for a slow, constant camera move and constant subject motion. No whip pans, no sudden accelerations, no strobe or flicker lighting, no rapid cuts. "Slow, steady, continuous" belongs in every video prompt.

3. **One subject, one continuous motion, no cuts.** Transforming one thing into a different thing is the hardest AI shot. When a change of world is the point, use a **bridge scene** (law 9) instead of asking one prompt to morph.

4. **Lock the path, free the body.** Rigid trajectory, living subject and scene: ripple, drift, steam, shifting light. A frozen subject on a clean path reads as a slideshow when scrubbed.

5. **Every frame is a resting frame.** A visitor can stop anywhere. Avoid motion blur smears, half-open eyes, mid-blink faces, and in-between hand poses; prefer materials whose every intermediate state looks good: fluids, fabric, light, particles, mist, architecture, product assembly.

6. **Choose forgiving subjects.** Anatomy everyone knows up close (hands, faces, keyboards, animals in detail) breaks visibly when paused. Keep risky detail distant, simple, and moving.

7. **Compose for the layout.** Decide where the action lives and leave calm, continuous regions for the band copy. The action lane stays clear.

8. **Plan both ends.** The first frame is what the scene shows before it pins (and the poster for static visitors). The last frame is what the page rests on when the scene releases into the next section, so it must hand off cleanly to that section's colors and mood. Write both into the prompt.

9. **Bridges use start and end frames.** Generate the end-of-section-A still and the start-of-section-B still first, in the same world, then one start+end frame video (Kling, Veo first/last frame) travels between them. Keep the two stills compositionally related (similar horizon line, subject position, lighting direction) or the model invents a messy transition.

10. **Sell boundary crossings.** Passing through water, glass, mist, or a doorway gets its physical lens moment written in: droplets, a beat of blur, light bloom. Clean passes read fake.

11. **Text over footage earns its legibility**, and pacing is in scroll distance, not seconds. Both systems live in `scroll-engine.md`.

12. **Standing guards.** "No text, no logos, no lettering anywhere" in every image and video prompt. Audio off. Decline preset suggestions for designed shots. Nothing gets built around a clip the user hasn't approved at the scene gate.

## Still template (start/end frames, 16:9, 2K)

```
[SUBJECT] at [POSITION IN FRAME], composed as the [first / final] moment of a slow
continuous motion that [ONE-SENTENCE JOURNEY]. [LIGHTING: source, direction, mood].
[PALETTE as materials and light, not hex codes]. [AMBIENT LIFE]. The scene fills the
frame edge to edge; the calm region at [WHERE BAND COPY LIVES] is [soft shadow /
receding depth / plain surface]. Cinematic, photorealistic, 16:9.
No text, no logos, no lettering anywhere.
```

**Negative-space trap:** never ask for "empty darkness" or "blank space" for captions; models paint literal black panels. Describe one continuous world with a calm region. For centered subjects say "dead center, equal distance from left and right edges" and describe both halves identically.

Real people: only the user or someone who agreed to appear. Use their photo as a character reference, restate their recognizable details, inspect likeness.

## Video template (image-to-video, 5s, 720p to 1080p, audio off)

```
One continuous shot, no cuts. Slow, steady camera [MOVE: push forward / descend /
orbit left] at constant speed. [SUBJECT] [JOURNEY VERB] from [START STATE] to
[END STATE] along [EXPLICIT PATH]. The subject stays alive: [SMALL MOTION].
The scene stays alive: [AMBIENT LIFE]. [BOUNDARY MOMENT if any]. No sudden
movements, no flashes, no cuts. The shot ends on [THE FINAL FRAME, fully described].
No text or lettering anywhere.
```

Bridge variant: pass both stills (start and end frame fields per `get_model_schema` / kie docs) and describe only the travel between them: "The camera glides steadily from the first frame's [world] into the final frame's [world], [how the transition is motivated: through mist / as light shifts / along the river]."

## Journeys (chaining clips)

1. Generate and gate segment 1.
2. Grab its last frame as full-quality PNG (`ffmpeg-recipes.md`), upload it (fal `upload_file` or `media.mjs upload`), use it as the next segment's start frame.
3. The next prompt continues the motion: same heading, speed, lighting. If a segment ends near-empty (a point of light), say explicitly what grows out of it.
4. Gate each segment separately; a rejected segment is one cheap re-roll.
5. Middle segments end mid-motion; only the last one needs a composed rest.
6. **Seam law:** fine texture does not carry across a join. Land seams inside motion or a motivated refresh (blur, sweep, light shift). A visible seam anyway → crossfade join in `ffmpeg-recipes.md`.
7. Abstract worlds (light, particles, atmosphere) chain most reliably.

## Depth scenes (no video)

Generate one wide still, then separate layers: background removal model on the subject for a foreground layer, and a second generation or inpaint of the background with the subject removed. Stack as absolutely positioned images inside a normal section and give each a `data-speed` (background 0.05, mid 0.12, foreground 0.25). Cheap, light, and good between two heavy sequence scenes.

## Inspection (every asset)

Check for sneaked-in trademarks and logos, broken anatomy, composition vs layout plan, and brand coherence (the brand's signature color, mark, and materials are right). Inspection also catches gifts: when the model beats the plan, flex the layout to feature it.
