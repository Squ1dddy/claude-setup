# ffmpeg Recipes

Every command here was run and verified. On Windows use them as-is in PowerShell (quote paths with spaces).

## Folder discipline

```
<site-name>/                 deploy folder: index.html + assets/ only
  assets/scenes/<scene>/     desktop frames + poster.jpg
  assets/scenes/<scene>-m/   mobile frames
review/                      OUTSIDE the deploy folder: raws, payloads, frames for inspection,
                             generations.jsonl, gallery.html
```

Nothing in the deploy folder that should not ship.

## Inspect a raw clip (before the scene gate)

```
ffmpeg -ss 0 -i review/scene1-clip.mp4 -frames:v 1 -q:v 2 review/inspect/scene1-start.jpg
ffmpeg -ss 2.5 -i review/scene1-clip.mp4 -frames:v 1 -q:v 2 review/inspect/scene1-mid.jpg
ffmpeg -sseof -0.1 -i review/scene1-clip.mp4 -update 1 -frames:v 1 -q:v 2 review/inspect/scene1-end.jpg
```

**Steadiness check (law 2 and the ending):** a per-frame motion curve. Spikes mean stutter when scrubbed; a tail that stays high means the ending never rests.

```
ffmpeg -i review/scene1-clip.mp4 -vf "tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG" -f null -
```

## Tail or head trim (cheaper than a re-roll)

Cut to the last steady frame, or skip a shaky opening. Scenes map scroll to frames, not seconds, so a shorter clip costs nothing:

```
ffmpeg -ss 0.3 -i review/scene1-clip.mp4 -t 4.2 -c:v libx264 -crf 16 -pix_fmt yuv420p -an review/scene1-trim.mp4
```

## Desktop frame sequence (the one that matters)

```
ffmpeg -i review/scene1-clip.mp4 -vf "fps=16,scale=1280:-2:flags=lanczos" -c:v libwebp -quality 68 -compression_level 6 assets/scenes/scene1/f_%04d.webp
```

- `fps`: sets the frame count. Aim for 1 frame per 4 to 6vh of the scene's `--len`: a 5s clip at fps=16 gives 80 frames, right for about 400vh. Longer scenes or journeys: raise fps or use the clip's native rate.
- `-quality 68`: start here. Busy detail (particles, fabric) tolerates 55 to 60; smooth gradients band first, so hold 70+ and check the calm frames.
- Set `data-count` to the number of files produced (`(Get-ChildItem assets/scenes/scene1).Count`).
- Over the 5 MB scene budget: lower fps first, then quality, then width.

## HD sequence (large screens, always ship for full-bleed scenes)

```
ffmpeg -i review/scene1-clip.mp4 -vf "fps=16,scale='min(1920,iw)':-2:flags=lanczos" -c:v libwebp -quality 85 -compression_level 6 assets/scenes/scene1-hd/f_%04d.webp
```

Same fps as the desktop set so `data-count-hd` matches. Raise the desktop set to `-quality 78` too: 72 bands visibly in dark footage.

## Mobile portrait sequence

Crops a 9:16 window out of the 16:9 clip at a horizontal focus point (0 = left edge, 0.5 = center, 1 = right edge), fewer frames, smaller:

```
ffmpeg -i review/scene1-clip.mp4 -vf "fps=10,crop=ih*9/16:ih:(iw-ih*9/16)*0.5:0,scale=720:-2:flags=lanczos" -c:v libwebp -quality 64 -compression_level 6 assets/scenes/scene1-m/f_%04d.webp
```

Pick the focus from the inspect frames so the subject stays in the window for the whole clip. If the subject travels across the frame, the portrait crop can't hold it: use `data-mobile="static"` for that scene instead.

## Poster

```
ffmpeg -i review/scene1-clip.mp4 -frames:v 1 -q:v 2 assets/scenes/scene1/poster.jpg
```

Build posters from the clip at full resolution, never from the 1280px frames: reduced-motion visitors (including anyone with Windows "Animation effects" off) see the poster full-bleed, and a 1280px poster looks pixelated on large screens.

For static visitors the poster should be the scene's most composed frame. When that is the last frame, point `data-poster` at a jpg made from the final webp instead.

## Chaining: last frame as full-quality PNG

```
ffmpeg -sseof -0.1 -i review/seg1.mp4 -update 1 -frames:v 1 review/seg1-last.png
```

Upload that PNG as the next segment's start frame. Never chain from a jpg.

## Joining journey segments

Preferred, one encode so joins cannot mismatch:

```
ffmpeg -i review/seg1.mp4 -i review/seg2.mp4 -i review/seg3.mp4 -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 16 -an review/journey.mp4
```

Crossfade rescue when a seam shows (offset = first clip length minus fade; for three clips the second offset is the joined length so far minus the fade):

```
ffmpeg -i review/seg1.mp4 -i review/seg2.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.25:offset=4.75,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 16 -an review/journey.mp4
```

Clips from different models or resolutions: add `scale=1920:1080,fps=24,setsar=1` to each input first (`[0:v]scale=1920:1080,fps=24,setsar=1[a];...`). Then export `journey.mp4` as a frame sequence like any clip.

## Section stills

```
ffmpeg -i review/section-proof.png -vf scale=1920:-2 -q:v 2 assets/img/proof.jpg
```

Screenshots and sharp UI stay PNG or lossless WebP.

## Depth layers (transparent PNG → WebP with alpha)

```
ffmpeg -i review/layer-front.png -vf scale=1920:-2 -c:v libwebp -quality 80 -compression_level 6 assets/img/layer-front.webp
```

## Measure

```
"{0:N2} MB" -f ((Get-ChildItem -Recurse assets/scenes/scene1 | Measure-Object Length -Sum).Sum/1MB)
```

Verify after every export: open a middle frame and the last frame. A silent bad export caught now is free.
