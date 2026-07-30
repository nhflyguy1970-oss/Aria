# Aria Platform Certification — System Integration Validation (SIV)

**Date:** 2026-07-29  
**Scope:** Post-refactor integration & wiring audit (no new features)  
**Baseline commits:** Search → Settings → Dashboard → Layouts → Notifications → Shell → Calendar → Provider Health (`5b85299`)

---

## Executive verdict

| Gate | Result |
|------|--------|
| Product registration & ownership | **PASS** (with known dual-layer notes) |
| Search / Settings / Dashboard / MC / Notifications / Shell / Calendar / Provider Health wiring | **PASS** |
| Chat stream keepalive (SSE heartbeat) | **PASS** |
| Chat first-token reliability (“What day is today?”) | **FAIL at provider** — Ollama `/api/generate` hangs with 0 bytes (VRAM contention / wedged daemon). Aria pipeline + PH classification repaired; generation itself blocked at Ollama. |
| Automated product tests (sampled) | **PASS** after repairs |
| Release readiness | **CONDITIONAL** — software wiring certified; operator must free VRAM / restore Ollama generate before declaring chat production-ready |

---

## Phase 1 — Platform inventory (summary)

### Product packages (`*_product` + named)

Search, Settings, Dashboard, Layouts, Notifications, Provider Health, Shell, Integrations, Capabilities, Voice, Vision, Gallery, Image Gen, Video Gen, Browser, Models, Coding, Fly Tying, Smart Home / HA, Automation, Intelligence, Calendar (module set), Planner (store + extension), Memory / Journal / Documents / Projects (extension + services).

### Route registrars

- `jarvis/gui/server.py` → `register_extension_api` + `extra_routes.register_routes` + large inline surface (chat, models, coding, MC).
- `jarvis/gui/extra_routes.py` registers product APIs (gallery, image/video, voice, vision, capabilities, integrations, search, settings, dashboard, layouts, notifications, shell, calendar, provider_health, intelligence, automation, specialists).

### Background workers

Custom daemon threads (no APScheduler): `platform_runtime`, `proactive_scheduler`, `intelligence/automation_engine`, server/services watchdogs, media/coding job queues, Provider Health in-request watchdog (not a background thread).

### Dependency graph (high level)

```
Shell / GUI
  ├─ Product Homes & APIs (extra_routes + extensions)
  ├─ Chat → assistant → provider (Ollama…) ← Provider Health (watchdog/recover)
  ├─ Search (federated RETRIEVERS)
  ├─ Settings (catalog indexes; products own stores)
  ├─ Dashboard aggregate (widgets from product bridges)
  ├─ Mission Control enrich_snapshot (product mission bridges)
  └─ Notifications pipeline (product publishers)
```

Full inventory detail: see exploration notes from SIV inventory agent (products, bridges, workers, orphans).

---

## Phase 2 — Architecture certification

| Concern | Owner | Notes |
|---------|-------|-------|
| Federated search | Search | Owns `RETRIEVERS` |
| Preference catalog | Settings | Indexes; products own stores |
| Home glance | Dashboard | Aggregates only |
| Shell presentation | Layouts + Shell | Density shared |
| Operator attention | Notifications | |
| Inference reliability | Provider Health | Providers own generation |
| Infrastructure console | Mission Control | Displays; does not own product data |
| Schedule | Calendar | |
| Tasks | Planner | Extension + store |

**Duplicate / dual layers (accepted, not redesigned):** Voice/Flytying/Smart Home (extension + product APIs); Models/Coding routes still in `server.py`; Automation Home vs Intelligence automation engine; three plugin concepts (intelligence SDK, capabilities, extensibility).

**Orphans repaired this SIV:** Image/Video `mission_bridge` + Calendar `mission_status` were not attached to `enrich_snapshot` — now wired.

---

## Phase 3–7 — Product / API / wiring

### Live API smoke (GUI `:8765`)

| Endpoint | Result |
|----------|--------|
| `/api/ping` | 200 |
| `/api/provider/health\|stats\|diagnostics\|providers` | 200 |
| `/api/search/product/home` | 200 |
| `/api/settings/product/home` | 200 |
| `/api/layouts/home` | 200 |
| `/api/notifications/home` | 200 |
| `/api/shell/product`, `/api/shell/product-home` | 200 |
| `/api/calendar/product`, `/api/calendar/mission` | 200 |
| `/api/dashboard/product` | 200 |
| `/api/dashboard/home` | 200 (~7.9s latency — slow but OK) |
| `/api/mission-control/overview` | 200 (`platform_status: degraded`) |

### Search

- Facets ↔ `RETRIEVERS` ↔ `DEFAULT_ENABLED` aligned (including `provider_health`).
- Known gap (not expanded this SIV): no dedicated corpora for models/browser/coding/voice/vision/integrations/capabilities (Settings links exist; adding retrievers would be new feature scope).

---

## Phase 4–5 — Provider & chat pipeline

### Instrumented path (“What day is today?”)

| Stage | Observation |
|-------|-------------|
| Browser / HTTP Form `/api/chat` | Accepted |
| SSE `status: Processing…` | Emitted |
| SSE `heartbeat` | Emitted every ~5s (Provider Health) |
| Ollama `/api/tags` | OK (40 models) |
| Ollama `/api/ps` | Empty (no loaded models) |
| Ollama `/api/generate` (3b / 1.7b) | **Timeout, 0 bytes** |
| First token / first SSE token | **Never** |
| Free VRAM | Effectively exhausted (`free_vram_mb: 0`); ComfyUI running |
| MCP `jarvis_chat` | Misrouted to `memory_search` before NLU repair |

### Root cause (runtime)

**Ollama generate is wedged / cannot load models while GPU VRAM is held (ComfyUI).** Tags respond; generate never returns. This is not an Aria idle-timer misclassification.

### Root cause (software, repaired)

1. NLU could classify date questions as memory → `memory_search` (“No matching memories”).
2. Server heartbeats forever with no first-progress cutoff → clients without idle timers hang indefinitely.
3. Mission bridges for Image/Video/Calendar orphaned from MC enrich.

---

## Issues found & fixes applied

| # | Severity | Location | Root cause | Impact | Fix | Files |
|---|----------|----------|------------|--------|-----|-------|
| 1 | **High** | `nlu/mapping.py`, `nlu/confidence.py` | Date/calendar fact questions routed to memory / clarification | Simple prompts fail via MCP/router | Deterministic `is_calendar_fact_question` → `chat`, skip clarify | `jarvis/nlu/mapping.py`, `jarvis/nlu/confidence.py`, `tests/test_nlu_routing.py` |
| 2 | **High** | `gui/server.py` chat SSE | Heartbeats forever when provider never tokens | Operator hung with no classified failure | Server-side `first_progress_ms` → `FIRST_PROGRESS_TIMEOUT` + cancel | `jarvis/gui/server.py`, `tests/test_provider_health.py` |
| 3 | **Medium** | `chat_send.js` | Server `error`/`done` timeout codes not mapped to recovery path | Recovery card skipped on server timeout | Treat server timeout codes like client timeouts | `jarvis/gui/static/chat_send.js` |
| 4 | **Medium** | `mission_control_ops/enrich.py` | Calendar / Image / Video bridges unused | MC missing product health panels | Wire existing bridges into `enrich_snapshot` | `jarvis/mission_control_ops/enrich.py` |
| 5 | **Critical (runtime)** | Ollama + VRAM | Generate hangs; VRAM 0; ComfyUI up | Chat cannot complete | **Operator action:** unload ComfyUI / free VRAM / restart Ollama; then re-verify prompt | *No Aria redesign* |

---

## Phase 8–14 — Cross-product checks

| Area | Status |
|------|--------|
| Search registrations | Certified for registered corpora |
| Settings catalog | Provider Health prefs present; products linked |
| Notifications | Product home 200; PH notify path exists |
| Mission Control | Overview 200; PH + Calendar + Image + Video enrich keys present after fix |
| Shell | Product + product-home 200 |
| Persistence | Not corrupted in smoke; no migrations run this SIV |
| Workers | Inventory complete; no dead APScheduler |

---

## Phase 15–18 — Workflows & tests

### Workflows

| Workflow | Result |
|----------|--------|
| Product Home APIs | Pass |
| Provider Health diagnostics | Pass |
| Chat simple question end-to-end | **Blocked** at Ollama generate |
| NLU date → chat | Pass (unit) |

### Tests executed

- `tests/test_provider_health.py` — pass  
- `tests/test_nlu_routing.py` — pass (includes “What day is today?”)  
- Earlier batch: calendar, shell, notifications — pass (aside from NLU failures fixed afterward)  
- Search product suite — run in parallel during report write  

---

## Phase 19 — Hygiene notes (no mass deletion)

- Dual extension/product APIs remain intentional compatibility layers — **do not remove**.
- Models/Coding still registered in `server.py` — architectural debt, not broken.
- Silent `try/except` around product registration in `extra_routes` can hide import failures — monitor logs; do not blanket-remove.
- Uncommitted WIP remains: Planner enhancements, Intelligence platform, GUI polish docs — **out of SIV commit scope**.

---

## Remaining known issues / risk

1. **Ollama generate hang under VRAM pressure** — blocks all chat until GPU freed / Ollama restarted.  
2. **Dashboard `/api/dashboard/home` ~8s** — functional but slow; profile later if needed (not redesigned here).  
3. **Search corpus gaps** for some Product Homes — documentation debt, not wiring breaks.  
4. **MC overview UI** does not yet render every enrich key as cards (data present after enrich fix).  
5. **Provider Health recover** against wedged generate may report alive (tags OK) while generate still hangs — classification improved; operator restart still required when probe generate fails.

---

## Release readiness

**Software integration:** Certified for core product wiring after SIV repairs.  

**Operational chat:** Not certified until Ollama `/api/generate` returns tokens on a small prompt with free VRAM.

### Operator checklist to clear chat gate

1. Pause/unload ComfyUI (or other VRAM holders).  
2. Confirm `free_vram_mb > 0` and Ollama generate works:  
   `curl -m 60 http://127.0.0.1:11434/api/generate -d '{"model":"qwen2.5:3b","prompt":"hi","stream":false,"options":{"num_predict":8}}'`  
3. Retry GUI: “What day is today?”  
4. Confirm first token + completion (or classified recovery UX if still failing).

---

## SIV stop condition

No new products were added. Architecture was not redesigned. Defects found during verification were repaired; runtime provider blockage is documented for operator remediation.
