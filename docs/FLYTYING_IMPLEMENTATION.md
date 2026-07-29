# Fly Tying Implementation

Aria's dedicated **Fly Tying** product — patterns, inventory, sessions, hatch guidance, RAG, videos, barcodes, suggestions, profiles, and history.

## Product identity

Fly Tying owns the tying workflow. It does **not** own Vision, Voice, Gallery, Planner, Calendar, Documents, Mission Control, or Models — those products integrate through bridges.

Censored and uncensored modes share **one Fly Tying engine**. Differences are presentation / response policy only. History, inventory, sessions, and recipes are never regenerated or deleted when switching profiles.

## One pipeline

```
Pattern Library → Inventory → Barcode → Vision → Voice → Planner → Gallery → Documents
        → Fly Tying Engine → Search → Suggestions → Recipe → Session → History
        → Mission Control → Completion
```

## Architecture

| Layer | Package / module | Role |
|-------|------------------|------|
| Core library | `jarvis.flytying.*` | Index, search, bridge, barcode, videos, hatch, chat, nightly |
| Product facade | `jarvis.flytying_product.*` | Home, profiles, sessions, history, inventory summary, bridges |
| HTTP | `/api/flytying/*` + `/api/flytying/product/*` | Extension + product APIs |
| Chat fast-path | `extensions/flytying/handlers` + `routes` | Status, recipe, ask, search |
| UI | `#flytyingView`, `flytying.js`, `flytying_home.js` | Inventory-first Home |

### Product modules

- `engine.py` — product status, recovery, home, search/suggest wrappers
- `inventory.py` — inventory-first summary, low stock, recent scans
- `sessions.py` — first-class tying sessions (steps, timers, notes, photos)
- `profiles.py` — Beginner, Competition, Bass, Trout, Saltwater, Travel Kit, Minimal Bench, …
- `history.py` — shared JSONL with presentation-only redaction
- `mission_bridge.py` — Mission Control panel
- `vision_bridge.py` — material / finished-fly ID via `vision_product`
- `voice_bridge.py` — bench next/prev/repeat/read via `voice_product`
- `gallery_bridge.py` — finished-fly metadata + collections
- `planner_bridge.py` / `calendar_bridge.py` — candidate previews only
- `qr_local.py` — offline QR / printable labels
- `hatch_packs.py` — regional hatch import / export / activate
- `experimental.py` — env-gated KG, coach, clustering, trip advisor, …

## Inventory

Inventory is the primary differentiator. Home surfaces count, low stock, queue, and **Suggest a fly**. Barcode scan → learn mapping → structured inventory items. Vision may propose drafts; operators confirm before write.

## Patterns & search

Blackfly scraped/gold JSONL via `jarvis.flytying.index` + `bridge`. Unified search, favorites, quality filters, Pattern of the Day (`nightly.pattern_of_the_day`), seasonal hatch suggestions.

## Videos

`video_fetch.discover_videos_from_url` (alias of `fetch_videos_from_url`) + `videos_store` custom/cache APIs returning `{ok: …}` shapes.

## Sessions

Start from a recipe → steps + materials checklist → pause/resume → next/prev → complete. Voice bench commands advance session state; Voice only speaks.

## Vision / Voice

Never duplicate engines. Fly Tying calls `vision_product.engine.analyze` and `voice_product.engine.speak_text`.

## Mission Control

`mission_control_ops.enrich` attaches `snap["flytying"]` from `flytying_mission_panel()` — corpus, RAG, nightly, inventory, session, recovery, deep links. Overview UI renders a Fly Tying card.

## Nightly

`proactive_scheduler` calls `flytying.nightly.run_scheduled` each tick (hour window). Sync library, video cache, Pattern of the Day memory seed when enabled.

## Chat integration

`flytying_context_for_chat` injects library context into main Chat (`behaviors/conversation.py`). Dedicated Fly Tying chat streams `{type: token|recipes|done}` via `ask_stream`.

## Local QR

Labels use `flytying_product.qr_local` — no cloud QR APIs. Optional `qrcode` package; stdlib SVG fallback for short `FT:` payloads.

## Regional hatch packs

Bundled: `hatch_northeast.json`, `hatch_rockies.json`. Operators import/export/activate packs; activation writes `hatch_operator_active.json`.

## Testing

```bash
.venv/bin/pytest tests/test_flytying*.py -q
```

Coverage includes search, inventory, barcode, videos, sessions, suggestions, profiles, QR, hatch packs, bridges, Mission Control panel shape, accessibility contracts, and reliability fixes (POTD, video shape, discover alias, handlers routes).

## Roadmap

- Deeper Planner/Calendar write-back (still candidate-first)
- Richer session coach (experimental, confirmation-gated)
- Bench lighting via Home Assistant (experimental, never auto)
- Pattern evolution / regional intelligence (experimental)

## Do not build

Separate Fly Tying LLM, duplicate Vision/Voice/search engines, social feed, marketplace, cloud-first architecture, auto purchasing, GIS maps, always-on bench camera, silent Memory ingestion.
