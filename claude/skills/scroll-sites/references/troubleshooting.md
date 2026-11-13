# Troubleshooting: Symptom → Cause → Fix

## Setup and providers

| Symptom | Cause | Fix |
|---|---|---|
| `claude mcp get fal-ai` shows HTTP 401 | `FAL_KEY` not set, or the app was started before it was set | User sets the Windows user env var, then fully restarts the Claude app (env is read at launch) |
| `media.mjs` exits 2 | `KIE_API_KEY` not set in this process | Same as above; meanwhile route everything to fal |
| `media.mjs` exits 3 | Budget cap would be passed | Tell the user the numbers and ask before raising `--budget` |
| `media.mjs` exits 4 | kie task stalled or timed out (common) | Run the identical job on fal; after two kie failures in a session, stop using kie for the session |
| `media.mjs` exits 5 | kie task failed | Read the failMsg. Safety flag on innocent abstract prompts: rewrite in plain product-photography words. Check kie.ai/logs for charges |
| JSON parse error "Unexpected token" on a payload | File written with a BOM or by a shell redirect | The script strips BOMs; otherwise write payloads with the editor tool |
| fal `run_model` times out on video | Video must be queued | `submit_job` then `check_job` every 20 to 30s |
| kie result URL 404s later | Result URLs expire after about 24h | `run` downloads immediately; for manual jobs use `media.mjs download` right away |
| A model's input field is rejected | Schemas differ per model and version | fal: `get_model_schema`. kie: fetch that model's docs.kie.ai Market page, copy fields exactly |

## Generation

| Symptom | Cause | Fix |
|---|---|---|
| Scrubbing shows stutter or jumps though the engine is fine | The clip has speed bursts or flicker | Steadiness check in `ffmpeg-recipes.md`; trim the burst out or re-roll with "slow, steady, constant speed, no flashes" |
| Pausing mid-scroll shows ugly in-between frames | Subject with fragile intermediate states (faces, hands, blur smears) | Law 5: forgiving materials, keep detail distant, or trim to the clean stretch |
| Bridge transition is a messy morph | Start and end stills compositionally unrelated | Regenerate the stills with shared horizon, subject position, and light direction; motivate the change (mist, light sweep) |
| Real logo or trademark appears | The model slipped a brand mark in | Cheap image edit before animating; never animate a trademarked frame |
| Journey shows a cut at a join | Texture re-imagined at a rest-to-rest seam | Crossfade join; storyboard future seams inside motion |
| Model paints black side panels | Prompt named "empty darkness" for captions | Describe one continuous world with a calm region |
| Three failed clips on one concept | Concept problem | Change the concept |

## The engine

| Symptom | Cause | Fix |
|---|---|---|
| Page looks dead in the app preview pane: canvas never appears, bands at opacity 0 | Hidden pane stops `requestAnimationFrame` | Test with Playwright MCP or a real browser; not a site bug |
| Everything static on a machine where motion should run | The OS has reduced motion on (the preview pane often reports it) | Expected behavior; test motion with a scratch copy that overrides the media query |
| Canvas stays hidden, `.has-missing-frames` on the scene | Wrong `data-frames` template or count, or frames numbered from 0 | Frames must be `f_0001...` (ffmpeg default starts at 1); `data-count` equals the file count |
| Last frames of a scene never show | `data-count` larger than the real file count | Recount the folder |
| After jumping (anchor link, fast drag) into a scene still loading, it shows an early frame that doesn't match the band text | Loop rested on the nearest loaded frame and never redrew when the right frame arrived (fixed in the template 2026-09-15) | Use the current template: frame loads closer to the wanted frame trigger a redraw. Test: jump to 0.85 of a cold scene, wait, `drawn` equals `round(target*(count-1))` |
| Scene jumps instead of easing when first reached | Normal: the engine snaps to the current position when a scene enters the load margin | Only a problem if visible on screen; increase `LOAD_MARGIN` |
| Subject cropped out on phones | Portrait cover crop at the wrong focus | `data-focus-x` on the scene and the mobile crop focus in ffmpeg; or `data-mobile="static"` |
| Page heavy / slow on phones | Mobile falls back to desktop frames | Export the mobile sequence and set `data-frames-mobile` |
| Parallax element jumps or drifts away | Custom code measuring its own transformed position | Use the engine's `data-speed`; it measures untransformed position |
| Captions flash past | Scene `--len` too short for its bands | Grow `--len` or merge bands; flick test |

## The page

| Symptom | Cause | Fix |
|---|---|---|
| An entrance never plays | Later rule won the cascade over the start state | Prefix start/end states with the container class |
| Hovers on 2nd/3rd staggered items lag | Stagger-retire rule less specific than nth-child delays | Match or beat the specificity, then prove by hovering |
| Scroll-driven style stops after entrance | `animation-fill-mode: forwards` owns the property | Entrance on the parent, dynamic style on a child |
| Letter tails clipped | Masked text without breathing room | Em-based padding with matching negative margin |
| Page drags sideways | `overflow-x: hidden` alone or a wide decoration | `overflow-x: clip` on both `html` and `body` |
| Mojibake after a scripted edit | Shell read/wrote UTF-8 with the wrong encoding | Editor tool for all text edits; recovery: decode as UTF-8, encode Windows-1252 bytes, decode UTF-8, save |

## Deploy

| Symptom | Cause | Fix |
|---|---|---|
| Directory listing or 404 | Zip contains the folder, not its contents | Re-zip with `index.html` at the top level |
| Review files or raws live on the site | They were inside the deploy folder | Keep `review/` outside, always |
| Old version still showing | Cache | Hard refresh; verify a changed string |

**Two-hang rule:** a second consecutive hang on the same tool means it is down. Stop, say so, restart or switch provider. A render job reporting progress is not a hang.
