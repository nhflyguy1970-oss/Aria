# Video Generation Implementation

**Product:** Aria Video Generation — local motion engine  
**Primary surface:** Video Studio (`Ctrl`-ish via palette · view `video`)  
**Status:** Production-oriented local motion product (one shared pipeline)

## Philosophy

Video Generation **creates motion**. Video Studio is the create UI + library. Gallery owns stills.

| Video Generation owns | Does not own |
|-----------------------|--------------|
| Text → video | Gallery stills library |
| Image → motion (Ken Burns / storyboard) | Image Generation (stills) |
| AnimateDiff + Ken Burns | Chat conversation |
| Presets, enhance, motion planning | Mission Control health UI |
| Shared `submit_video` / `submit_storyboard` | Timeline / CapCut-style editor |
| Media-queue jobs | Cloud video backends |

## One pipeline

```
Video Studio / Chat / MCP / Automation / Voice / API
        ↓
submit_video()  or  submit_storyboard()
        ↓
normalize_params (+ optional preset)
        ↓
optional enhance (transparent)
        ↓
media_jobs → MediaHandler.generate_video | storyboard_video
        ↓
VideoEngine → comfyui_video.generate_motion_clip
        ├─ AnimateDiff
        └─ Ken Burns (Comfy keyframe + ffmpeg)
        ↓
generated_videos + metadata → Library / Activity / Job Center
```

## Package layout

```
jarvis/video_generation/
  engine.py           # submit_video, submit_storyboard, last settings
  params.py           # normalize_params
  presets.py          # built-ins + CRUD
  enhance.py          # preview_enhance
  fallback.py         # recovery advisor
  mission_bridge.py   # health + deep links
  experimental.py     # coach, shot planner, recommenders
  metadata.py         # provenance + censored visibility
  api.py              # /api/video-generation/*
  terminology.py
```

## Engines

- **auto** — AnimateDiff when ready; VRAM-aware retry; Ken Burns fallback  
- **animatediff** — real motion (SD 1.5); no silent KB fallback  
- **ken_burns** — keyframe still + ffmpeg zoompan  

Per-job overrides (engine, duration, fps, size, frames, seed, checkpoints) are honored end-to-end.

## Storyboards

`POST /api/video/storyboard` and `/api/video-generation/storyboard` enqueue **`storyboard_video`** on the **media** queue (not coding_jobs). Cancel / Job Center / cache invalidation apply.

## Censored / uncensored

One engine. Policy and model/checkpoint selection may differ; queue action and code path do not. Restricted library items show placeholders when the viewer profile is censored; assets are never regenerated or deleted by a mode switch.

## Testing

```
pytest tests/test_video_generation.py tests/test_video_settings.py tests/test_video_ops.py -q
```

## Roadmap

- Richer reference-image / hybrid AD+KB shot sequences (operator-approved)  
- Better ETA in Job Center  
- Project-bound clip collections
