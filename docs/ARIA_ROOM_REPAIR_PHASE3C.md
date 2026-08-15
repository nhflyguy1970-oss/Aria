# ARIA Room Repair — Phase 3C (Tier 3C)

**Status:** 3C-A systemic batch **COMPLETE** — **STOPPED** per authorized batch stop condition.  
**Follow-on:** Tier 3C-B platform Rooms completed separately — see `docs/ARIA_ROOM_REPAIR_PHASE3C_B.md`.  
**Final certification:** **NOT** issued. Zero Rooms are `CERTIFIED FUNCTIONAL`.  
**Evidence:** `docs/evidence/room_repair_phase3c/`

Tier 3C is **not** finished. 3C-B / 3C-C / 3C-D remain for a later authorization. This document is the checkpoint after the first major systemic repair batch.

---

## 1. Live 34-Room registry (authoritative)

Source: `jarvis/gui/static/workspace/registry.js` + owner UI walk (`registry_and_walk.json`).

| Set | Rooms |
| --- | --- |
| **Total** | **34** |
| **Core (Tier 3B)** — REPAIRED — AWAITING FINAL CERTIFICATION | `health`, `home`, `audio`, `projects`, `providers`, `home_automation`, `mission` |
| **Remaining (27)** | `chat`, `flytying`, `documents`, `planner`, `calendar`, `gallery`, `search`, `coding`, `memory`, `voice`, `repair`, `integrity`, `automation`, `presence`, `journal`, `video`, `browser`, `maker`, `meme`, `vision`, `connections`, `settings`, `capabilities`, `integrations`, `audit`, `security`, `actions` |

---

## 2. Architectural triage (3C-A)

Shared architecture groups for the remaining 27:

| Group | Rooms | Shared surface |
| --- | --- | --- |
| Native systems | `repair`, `integrity`, `presence`, … | `priority3_rooms.js` / `AriaRoomKit` |
| Furnished flagships | `flytying`, `search`, `journal`, `planner`, `calendar`, `documents`, `gallery`, `coding`, `memory`, … | `furnish.js` → legacy panels |
| Platform / ops | `settings`, `capabilities`, `integrations`, `security`, `actions`, `automation`, `audit` | product homes + APIs |
| Media / devices | `voice`, `video`, `browser`, `audio` (core), `maker`, `meme`, `vision` | external/hardware deps |
| Living Room | `chat` | `AriaLivingRoom` |

### Systemic defects discovered

| ID | Defect | Severity | Affects |
| --- | --- | --- | --- |
| **SYS-3C-01** | `/api/repair/home` / `scan_issues` paid **~5.5s** every call via `provider_ollama.detect(force_probe=True)` (generate probe) + `docker diagnose(force=True)` + duplicate `product_status()` | High | Repair Room load, Guided Repair home, Mission repair panel |
| **SYS-3C-02** | Search pipeline used **no timeout** when a single heavy corpus was selected; `ThreadPoolExecutor` context manager **waited out hung corpora** after timeout | High | Search UI (`document` hung >20s with 0 bytes) |
| **SYS-3C-03** | Fast “everything” corpora omitted **flytying** — pattern-name queries (e.g. `Adams`) never hit Fly | High | Search → Fly navigation |
| **SYS-3C-04** | Repair Room had no owner entry to **Guided Repair Scan** (only Mission) | Medium | Repair completeness |
| **FALSE+** | Prior probe “Fly cards = 0” used wrong selectors (`.fly-card` vs `.flytying-recipe-item`) | — | Audit noise |
| **FALSE+** | Prior probe “Repair/Integrity 0 buttons” looked for missing `repairView` / `integrityView` instead of `repairRoom` / `integrityRoom` | — | Audit noise |
| **OPEN** | Documents RAG corpus still times out at wall (~12s) — partial failure, no hang | Medium | Search documents facet; Documents Room semantic search |
| **OPEN** | Federated Search warm path still ~3s (ACM/memory fan-out) | Low–Med | Search usable time |
| **OPEN** | Guided Repair open issues: proactive scheduler not running; HA connection | Known / Jeff-attended for HA actuation | Repair/Mission honesty |

---

## 3. Systemic repairs applied (3C-A)

### SYS-3C-01 — Repair home / scan latency

**Root cause:** Routine detect forced expensive probes.

**Repair:**
- `provider_ollama.detect` → `ping_provider(..., force_probe=False)`
- `docker_services.detect` → `diagnose(force=False)`
- `home_payload` calls `product_status()` once
- `scan_issues` short TTL cache (30s); `POST /api/repair/scan` still `force=True`

**Evidence (`systemic_perf.json`):**
- `/api/repair/home`: **~5.5s → ~0.8–1.0s** first, **~6–10ms** warm

### SYS-3C-02 — Search hang

**Root cause:** Single-corpus path had no timeout; executor shutdown waited for hung `documents_rag.search`.

**Repair:** Always run corpora in a pool with wall/one timeouts; `shutdown(wait=False, cancel_futures=True)`.

**Evidence:** `document` query returns **~12s** with honest corpus-timeout failure (no indefinite hang).

### SYS-3C-03 — Fly missing from fast everything

**Repair:** Add `flytying` to `_FAST_EVERYTHING` in `search_product/intent.py`.

**Evidence:** Search `Adams` returns Fly Tying result cards first (API + owner UI).

### SYS-3C-04 — Repair Room Guided Repair entry

**Repair:** Repair overflow **Scan** → `AriaGuidedRepair.scanAndShow()`; Repair load also reads `/api/repair/home` for open-issue evidence.

**Evidence:** Owner UI Scan opens Guided Repair overlay with live issues (`systemic_and_census.json`).

### Search → Fly open-in-context

**Repair:** `search_home.js` focus target `flytyingSearchInput` (was stale `flySearchInput`).

---

## 4. Room status after 3C-A

Status vocabulary (Tier 3C only): **REPAIRED — AWAITING FINAL CERTIFICATION** | **BLOCKED** | **NOT REPAIRED**  
(Plus internal **PROBED** for surface-only census — not a certification label.)

### Core (unchanged from Tier 3B)

All seven remain **REPAIRED — AWAITING FINAL CERTIFICATION**.

### Remaining — repaired this batch (owner UI + API)

| Room | Status | Notes |
| --- | --- | --- |
| **Search** | REPAIRED — AWAITING FINAL CERTIFICATION | Adams → Fly cards; document no longer hangs; documents corpus still times out (honest degraded) |
| **Repair** | REPAIRED — AWAITING FINAL CERTIFICATION | Native bench + Scan overlay + open repairs; HA/scheduler issues remain real |
| **Fly Tying** | REPAIRED — AWAITING FINAL CERTIFICATION | Search Adams → 80 recipe items + detail; leave/return ok |
| **Integrity** | REPAIRED — AWAITING FINAL CERTIFICATION | Score 100 / ready; native Truth surface |

### Remaining — surface-probed only (NOT fully capability-exercised)

`chat`, `documents`, `planner`, `calendar`, `gallery`, `coding`, `memory`, `voice`, `automation`, `presence`, `journal`, `video`, `browser`, `maker`, `meme`, `vision`, `connections`, `settings`, `capabilities`, `integrations`, `audit`, `security`, `actions`

These entered without load-fail cues and expose controls, but **complete workflow / every meaningful control** proof is **deferred to 3C-B/C**. Treat as **NOT REPAIRED** for certification purposes until that work lands.

### BLOCKED (dependency / Jeff-attended)

| Capability | Reason |
| --- | --- |
| HA physical actuation | Must not auto-toggle real devices |
| Security PIN / lock / credential mutation | Lockout risk — Jeff-attended residency |
| Voice cloud live / mic capture | Hardware + external; UI honestly shows unavailable where applicable |
| Documents semantic RAG under 12s | Corpus still times out — needs Documents pipeline repair in 3C-B/C |
| Integrations real credentials | No test credentials in production |

---

## 5. Production Integrity / isolation / Activity

| Check | Result |
| --- | --- |
| Integrity scan | **clean / 100** (`clean: true`, 0 findings) |
| QA header → live planner | **403** |
| Test-shaped planner mutation | **400** |
| Activity room-leave | **not** present as owner work (`room_leave: false` in probe) |
| Live Health Vitamin D3 | Untouched (no Health mutations in 3C-A) |
| ACM probe content | Not recreated |

---

## 6. Cross-Room regression (partial)

Proven in this batch:
- Search → Fly pattern results (federated)
- Repair → Guided Repair Scan overlay
- Repair → Integrity / Mission overflow navigation targets present
- Fly search leave/return (surface)

**Not yet run:** full matrix (Chat→Tools/Coding/Git, Journal encrypt, Integrations providers, Security protected rooms, etc.). Reserved for **3C-D**.

---

## 7. Performance (measured)

| Path | Before 3C-A | After 3C-A |
| --- | --- | --- |
| `/api/repair/home` | ~5500 ms | ~800–1000 ms cold / ~6–10 ms warm |
| Search `Adams` | Fly missing from everything | ~3.2 s with Fly hits |
| Search `document` | hung / curl 20s zero bytes | ~12 s bounded timeout + failure |
| Fly UI Adams | (false probe failure) | 80 cards, detail paints |

SYS-P03 (script count) unchanged — not cosmetic-cleaned.

---

## 8. Files touched (3C-A)

- `jarvis/repair_product/modules.py`
- `jarvis/repair_product/engine.py`
- `jarvis/search_product/pipeline.py`
- `jarvis/search_product/intent.py`
- `jarvis/gui/static/workspace/rooms/priority3_rooms.js` (`?v=5.1.14-tier3c`)
- `jarvis/gui/static/search_home.js` (`?v=1.0.2-tier3c`)
- `jarvis/gui/static/index.html` (cache-bust)

Evidence:
- `docs/evidence/room_repair_phase3c/registry_and_walk.json`
- `docs/evidence/room_repair_phase3c/deep_defects.json` (pre-correction)
- `docs/evidence/room_repair_phase3c/corrected_probes.json`
- `docs/evidence/room_repair_phase3c/systemic_and_census.json`
- `docs/evidence/room_repair_phase3c/systemic_perf.json`

---

## 9. Exact remaining work before final 34-Room certification

1. **Authorize 3C-B** — complete platform Rooms: Chat/Living Room, Memory, Coding, Settings, Capabilities, Integrations, Security, Actions, Automation (plus deepen Search beyond this batch).
2. **Authorize 3C-C** — domain Rooms: Journal (isol mutations), Gallery, Browser, Voice, Video, Maker, Audit, Connections, Meme, Presence, Calendar, Planner, Documents (incl. RAG hang root cause), and any registry leftovers.
3. **Authorize 3C-D** — full cross-Room regression matrix.
4. Only then: separate **34-Room Owner Residency** for final certification (not part of Tier 3C).

Do **not** claim 34/34. Do **not** issue Owner Residency from this checkpoint.

---

## 10. Stop

**STOPPED** after Tier 3C-A systemic repair batch.  
No final certification. No automatic start of 3C-B.
