# Providers: fal.ai and kie.ai

Two pay-as-you-go aggregators. Same underlying models (Kling, Seedance, Veo, Nano Banana, GPT Image), different price and reliability. Prices below were checked September 2026 and drift monthly: always preflight, never quote this file as a price.

| | fal.ai | kie.ai |
|---|---|---|
| Access | Official MCP `fal-ai` (hosted, key in `FAL_KEY`) | REST via `scripts/media.mjs` (key in `KIE_API_KEY`) |
| Price | list price, a little higher | cheapest, often 20 to 40% under fal |
| Reliability | high | outages, slow queues, failed jobs; refunds disputed |
| Price check | `get_pricing` tool | kie.ai/pricing page (fetch it), `creditsConsumed` after |
| Role | default for finals and anything kie fails | first try when its key works, drafts, stills |

**Routing rule:** kie first when `media.mjs credits` works and the model exists there. On exit code 4 (stall or timeout) or 5 (task failed), or a model kie lacks, run the identical job on fal. Two consecutive kie failures in one session: stop using kie for the session and say so.

## Rough prices (for planning talk only, preflight real numbers)

| Model | Use | kie | fal |
|---|---|---|---|
| GPT Image 2 | stills, start/end frames | ~$0.03 (1K), $0.05 (2K), $0.08 (4K) | a few cents more |
| Nano Banana Pro / 2 | stills, edits, logo placement | cents | cents |
| Kling 3.0 std | workhorse image-to-video, start+end frames | ~$0.07/s (5s ≈ $0.35) | pro ~$0.112/s no audio |
| Seedance 2.0 Fast | smooth physical motion, loops | cheap | ~$0.24/s |
| Veo 3.1 Fast | premium realism, first+last frame | ~official | $0.10/s no audio, 720p/1080p |

Scroll scenes never need audio: always turn sound/audio off (it roughly doubles video price). Generate at 1080p max; 720p is enough for most sequences (frames export at 1280px wide).

Typical page: 3 scenes × (2 stills + 1 clip) + 3 section stills ≈ $2 to $4 on kie, $3 to $6 on fal, plus re-rolls. Present that shape during the package talk.

## fal.ai via MCP

1. `recommend_model` or `search_models` with a plain query ("kling 3 image to video", "veo 3.1 first last frame", "nano banana pro edit", "background removal"). Model ids change with versions; never hardcode one from memory.
2. `get_model_schema` on the chosen id: read the exact input names (image url field, `end_image_url`/last-frame field, duration, resolution, audio toggle, aspect ratio).
3. `get_pricing` for that id and those parameters → say the USD price.
4. Local file as input: `upload_file` → returns a fal CDN URL to pass as the image field.
5. Stills (seconds): `run_model` is fine. **Video: always `submit_job`, then `check_job` every 20 to 30 seconds** (run_model times out on video).
6. Download every output immediately: `node media.mjs download <url> --out review --name scene1-clip`.
7. Log it: `node media.mjs log --out review --provider fal --model <id> --prompt "<prompt>" --usd <price> --file review/scene1-clip.mp4 --job <request id>`.

## kie.ai via scripts/media.mjs

All generation goes through one Market endpoint. Input schemas differ per model, so **before the first call to any model, fetch its page on docs.kie.ai (Market section) and copy the exact `model` id and `input` fields.** Confirmed shape for Kling 3.0:

```json
{
  "model": "kling-3.0/video",
  "input": {
    "prompt": "One continuous shot, no cuts. ...",
    "image_urls": ["<start frame url>", "<optional end frame url>"],
    "duration": "5",
    "mode": "std",
    "sound": false,
    "multi_shots": false
  }
}
```

Flow (write the payload with the editor tool, not a shell redirect):

```
node media.mjs upload review/scene1-start.png                  -> prints a temp URL (valid 24h)
node media.mjs run review/payloads/scene1.json --out review --name scene1-clip --usd 0.35 --budget 10
node media.mjs gallery --out review                            -> review/gallery.html for the gate
node media.mjs spent --out review                              -> running total
```

`run` creates the task, polls until success, downloads every result URL (they expire in about 24 hours), and appends a line to `review/generations.jsonl` with model, prompt, input, credits, USD, files. Exit codes: 2 no key, 3 over budget (ask the user before raising it), 4 stalled/timeout, 5 failed (check kie.ai/logs that nothing was charged). Veo on kie uses a separate endpoint the script does not cover: run Veo on fal.

Rate limit: 20 new tasks per 10 seconds. Chained segments are serial anyway.

## The prompt log and gallery

Every generation, both providers, lands in `review/generations.jsonl`. The gallery is how the user reviews at every gate: rebuild it after each batch and tell them to open `review/gallery.html` (double-click works). The log also answers "what prompt made that one?" when re-rolling.

## Budget discipline

- Project cap set in Phase 0; `--budget` enforces it on kie runs; check `spent` before every fal job.
- Before each batch: "This batch is about $X. Spent so far $Y of $Z."
- Failed jobs: verify on the provider dashboard before counting them as free.
