# Image Generation Implementation

**Product:** Aria Image Generation — still-image diffusion engine  
**Surfaces:** Gallery (primary), Chat, MCP, Automation, Voice, API  
**Status:** Production-oriented local engine (one pipeline, one queue)

## Philosophy

Image Generation **creates** stills. Gallery **owns** the library (browse, organize, edit, collections, history visibility).

| Image Generation owns | Does not own |
|-----------------------|--------------|
| Prompt → image | Gallery library UX |
| ComfyUI execution | Chat conversation |
| Prompt enhancement | Video / Meme studios |
| Diffusion params & presets | Documents / Memory |
| GPU / CPU execution policy hooks | Mission Control health UI |
| Shared media-queue job `generate_image` | Job Center UI (consumes jobs) |

## One pipeline

```
Gallery / Chat / MCP / Automation / Voice / API
        ↓
normalize_params (+ optional Generation Preset)
        ↓
optional enhance (transparent — never silent-only)
        ↓
media queue → MediaHandler.generate_image
        ↓
ImageEngine.generate → comfyui.generate
        ↓
PNG → Gallery metadata → Activity / Job Center
```

There is **no** second diffusion backend and **no** Chat-only or Gallery-only generator.

Entry point: `jarvis.image_generation.engine.submit_generation`.

## Package layout

```
jarvis/image_generation/
  engine.py           # submit_generation, last settings
  params.py           # normalize_params, aspect presets, seed coerce
  presets.py          # built-in + custom + per-project presets
  enhance.py          # preview_enhance (original vs enhanced)
  fallback.py         # recovery advisor (retry GPU/CPU, open MC)
  mission_bridge.py   # ComfyUI / VRAM / queue snapshot + deep links
  experimental.py     # coach, recommendations, seed explorer, evolve
  api.py              # /api/image-generation/*
  terminology.py
```

## Parameters (honored end-to-end)

Prompt, negative, enhance / enhanced_prompt (editable), seed / random / reuse,
steps, CFG, sampler, scheduler, width/height / aspect ratio, checkpoint,
workflow path, style preset, variations (max 4).

MediaHandler passes these into `ImageEngine.generate` → `comfyui.generate` /
workflow patch. Seeds are stored in Gallery metadata via `mark_generation`.

## Prompt enhancement

- Operators can preview (`POST /api/image-generation/enhance-preview`)
- Edit enhanced text before generate
- Disable enhance
- Never the only path: original is always retained in metadata

## GPU → CPU fallback

`comfyui.generate` detects GPU failures, calls `services.fallback_comfyui_to_cpu`,
retries once. Failures return actionable copy + Gallery recovery actions
(Retry GPU / Retry CPU / Mission Control / Job Center). Import errors must not crash.

## Generation Presets

Built-ins: Fast Draft, High Quality, Photoreal Portrait, Landscape, Anime,
Pixel Art, Product Photography, Concept Art.

CRUD + export/import via `/api/image-generation/presets*`. Applying a preset
fills empty operator fields and may append a style template to the prompt
(visible — not silent-only rewrite of the whole prompt).

## Censored / uncensored

**One engine.** Modes differ only by policy/config (prompt system note, model
roles, checkpoint preference). Queue action is always `generate_image`.

Assets created uncensored keep metadata; in censored profile Gallery shows a
restricted placeholder (no regen/delete). Switching modes never duplicates history.

## Gallery parity

Gallery Generation panel supports: cancel, VRAM preflight, enhance preview/edit,
advanced params progressive disclosure, presets, Generate another, progress /
recovery, Mission Control + Job Center deep links — same backend as Chat.

## Mission Control

`/api/image-generation/status` exposes ComfyUI running state, mode, VRAM, queue,
and deep links. MC owns health UI; Image Generation only bridges.

## Testing

```
pytest tests/test_image_prompt.py tests/test_image_uncensored.py tests/test_image_generation.py -q
```

## Roadmap

- Richer reference-image conditioning UX (still edit_image / shared queue)
- Prompt favorites UI polish
- Workflow recommendation learning from successful runs
- Performance metrics in Job Center ETA
