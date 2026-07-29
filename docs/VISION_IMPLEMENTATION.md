# Vision Implementation

Aria's visual understanding product — one shared Ollama VLM pipeline for every entry point.

## Product identity

**Vision owns:** image understanding, OCR / structured OCR, compare, region analysis, PDF pages, video frames, webcam-for-analysis, profiles, history, import pipeline, routing.

**Vision does not own:** Image Generation, Gallery library, Presence/gestures, Browser navigation, Coding apply, Audio Studio, Documents store, Memory store, Mission Control.

Entry points (Chat attach, Vision Home, Gallery, Browser, Coding, Planner, Journal, Calendar, Automation, API, Voice) are front doors to **`jarvis.vision_product.engine.analyze`**.

## Architecture

```
jarvis/vision_product/
  engine.py           # analyze() — shared pipeline
  ocr.py              # classic / VLM / hybrid OCR
  import_pipeline.py  # vision_import() for Journal/Planner/Calendar/…
  profiles.py         # Document OCR, Fast Scan, Coding, Naturalist, …
  history.py          # searchable ledger + censored presentation
  honesty.py          # model / VRAM / latency warnings
  batch.py            # progress / cancel / retry
  status_bus.py       # vision_state WS events
  mission_bridge.py   # Mission Control panel
  voice_bridge.py     # Voice → Vision (speak via Voice product)
  experimental.py     # env-gated features
  api.py              # /api/vision/*
  settings.py         # unified settings
  terminology.py      # ownership boundaries
```

Core VLM calls still use `VisionEngine` (`modules/vision.py`) + `vision_media.py` helpers. Chat behaviors in `behaviors/vision/engine.py` **must** call `vision_product.engine.analyze` — no parallel Chat Vision engine.

## One pipeline

```
Media (image | webcam | PDF | video frame | browser | gallery | automation | API | Voice)
  → Vision Engine (analyze)
  → Intent / action
  → Analysis (describe / OCR / compare / …)
  → Optional Import (confirm)
  → History + Activity
  → Mission Control
  → Completion
```

## Actions (post-attach rail)

Describe · OCR · Structured OCR · Tables · Identify · Compare · UI→Code · Remember · Import · Translate · Summarize

## Model / VRAM honesty

`GET /api/vision/honesty?task=` returns model, Fast/Quality, estimated VRAM, latency, fallback, warnings **before** heavy runs. Shown on Vision strip, Models sidebar, attach preview, and Vision Home.

Installed-model listing uses tags-only Ollama polls (`check_ollama(soft_probe=False)`) so honesty never blocks on generate probes.

## OCR modes

`classic` (tesseract) · `vlm` · `hybrid` · `auto` — via `vision_product.ocr.run_ocr`.  
`document_intel.ocr_image` routes here (no module-level phantoms).

## Shared import

`vision_import(path=…, target=journal|planner|calendar|memory|documents|gallery|preview)`  
Planner / Calendar / Journal all use this path. Writes require confirmation.

## Profiles

Built-ins: Document OCR, Research, Accessibility, Coding, UI Review, Fast Scan, Deep Analysis, Naturalist.

## History & censored/uncensored

One history store. Uncensored-origin entries remain intact when viewing under a censored profile — presentation redacts until reveal (`presentation_for_profile`). Storage and pipeline stay shared.

## Mission Control

`enrich_snapshot` attaches `vision` panel: model, VRAM, batch jobs, warnings, deep links.

## Voice

Optional `speak_results` / `speak=true` / Voice intents ("OCR this", "describe this", "what's on my screen?") use **Voice** `speak_text` via `voice_bridge` — never a separate TTS path.

## Compare UX

Drop two images → auto compare mode · A/B previews · visual diff path · confidence when available · side-by-side send.

## UI

- Vision tab / Vision Home (`#visionView`) — honesty, profiles, OCR mode, batch, history, experimental
- Vision strip (`#ariaVisionStrip`)
- Chat post-attach action rail
- Shortcuts: `Ctrl+Shift+I` Vision Home
- Command palette: Go to Vision

## Accessibility

Action rail toolbar roles · crop ARIA labels · strip `aria-live` · Vision Home status regions · keyboard shortcut to Home.

## Experimental (env-gated)

| Flag env | Feature |
|----------|---------|
| `JARVIS_VISION_EXP_CONTINUOUS` | Continuous scene (consent; never always-on) |
| `JARVIS_VISION_EXP_TEMPORAL` | Temporal compare |
| `JARVIS_VISION_EXP_KG` | Knowledge-graph link staging |
| `JARVIS_VISION_EXP_HA_CAMERA` | HA camera snapshot (confirm) |
| `JARVIS_VISION_EXP_CLUSTER` | Visual memory clustering (history only) |
| `JARVIS_VISION_EXP_TIMELINE` | Scene timeline |

## Testing

```bash
.venv/bin/pytest tests/test_vision_product.py tests/test_vision.py tests/test_vision_features.py tests/test_vision_preprocess.py tests/test_vision_resolve.py -q
```

## Roadmap

1. Stronger classic OCR packaging / language packs  
2. Continuous scene assistant (experimental + consent)  
3. HA camera snapshot with explicit confirm  
4. Knowledge-graph linking from captions  

## Do not build

Separate Chat/Browser/Gallery OCR engines · always-on ambient camera · emotion detection · auto-apply Coding · silent Memory ingest · ComfyUI as Vision (Image Gen only).
