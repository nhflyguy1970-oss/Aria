# ARIA — Room Repair Phase 3A (Tier 3A)

**Date:** 2026-08-12  
**Mode:** Shared infrastructure + measured house-wide performance root causes. **STOP before Tier 3B.**  
**Baseline (unchanged):** `docs/ARIA_COMPLETE_ROOM_FUNCTIONALITY_AUDIT.md`  
**Prior phases (unchanged):** `docs/ARIA_ROOM_REPAIR_PHASE1.md`, `docs/ARIA_ROOM_REPAIR_PHASE2.md`  
**Evidence:** `docs/evidence/room_repair_phase3a/`

Aria remains **not** functional as a product. **Zero Rooms** are CERTIFIED FUNCTIONAL. No Room is marked “repaired awaiting final certification” yet — Tier 3A did not complete Room-level capability contracts.

Live serve after Tier 3A: PID **3820804** (`main.py serve` on `:8765`).

---

## Verdict

Tier 3A is **complete for its authorized scope**: measure → identify systemic causes → repair shared roots → remeasure → Integrity/isolation regression → **STOP**.

The house is **faster on the shared poll paths that were killing Mission / Focus / health-brief**. That is **not** Room certification and **not** “Aria is functional.”

---

## Measured baseline (pre-repair)

Source: `docs/evidence/room_repair_phase3a/baseline_timings.json` (+ `layer_profile.json`, `enrich_breakdown.json`, `panel_timings.json`).

| Path | Cold (pass1) | Warm (pass2) |
| --- | ---: | ---: |
| `/api/mission-control/health` | **3242 ms** | 35 ms |
| `/api/mission-control/health-brief` | **2419 ms** | **2032 ms** |
| `/api/mission-control` | **1604 ms** | **1667 ms** |
| `/api/planner/focus` | **1583 ms** | **1754 ms** |
| `/api/dashboard/home?stale_ok=true` | 5 ms | (cached) |
| Script tags in shell | **151** | — |

Layer findings:

- Product-panel fan-out in enrich summed ~4s cold; **voice alone ~2.6s** (`diagnose()` / whisper backend import).
- Split caches: jarvis MC vs `automation_gate` platform collect vs metrics flag thrash.
- Planner Focus called `what_am_i_working_on` → ACM `memory.search` on every Focus poll (in-process Focus without that path was ~2 ms).
- SYS-F08: `#presence` → activity `home_automation` → wrong `body.dataset.room`.
- SYS-P02: multiple callers of `/api/dashboard/home` without coalesce.
- SYS-P03: 151 scripts / heavy DOM — measured, **not repaired** in 3A.

---

## Defects repaired (systemic)

| ID | Symptom | Root cause | Repair | Affected surfaces |
| --- | --- | --- | --- | --- |
| SYS-P01 (MC) | health / health-brief / MC multi-second polls | Full enrich + product panels on every poll; split caches | Shared `_RAW`/`_LITE`/`_FULL` caches; `enrich="lite"|"full"`; health-brief & health_summary use **lite** | Mission Control, Automation gate, status polls |
| SYS-P01 (gate) | Duplicate platform collect | `automation_gate` re-collected Platform MC | Delegate to `health_summary()` | Automation health gate |
| SYS-P01 (Focus) | Focus ~1.5–1.7s | ACM briefing on every poll | Local briefing from planner tasks/events only | Planner Focus / Home widgets consuming Focus |
| SYS-P01 (voice panel) | Full enrich voice ~2.6s | Uncached `diagnose()` | 45s voice mission panel cache | Mission full enrich |
| SYS-F08 | `#presence` → `home_automation` room | Hash→activity map wrong; no presence/home activities | Map `presence→presence`, `dashboard→home`; add activities | Presence, Home foyer boot |
| SYS-P02 | Duplicate home fetches | Independent `fetch` callers | `AriaSharedFetch.dashboardHome` coalesce + 2.5s TTL | living_interface, dashboard_home, living_room_presence, Home Room |

**Not claimed fixed:** SYS-P03 (151 scripts), Room-level functional defects from the audit, UNKNOWN Rooms.

---

## Post-repair measurements

Source: `docs/evidence/room_repair_phase3a/post_repair_timings.json`.

| Path | Cold (pass1) | Warm (pass2) | Δ warm vs baseline |
| --- | ---: | ---: | --- |
| `/api/mission-control/health` | 1746 ms | **3 ms** | still cold platform collect; warm OK |
| `/api/mission-control/health-brief` | **5 ms** | **2 ms** | was **~2032 ms** warm |
| `/api/mission-control` | **785 ms** | **15 ms** | was **~1667 ms** warm |
| `/api/planner/focus` | **5 ms** | **3 ms** | was **~1754 ms** warm |
| Script tags | **151** | — | unchanged (SYS-P03 remains) |

Notes:

- Cold health (~1.7s) is still Platform `collect_mission_control` cost on first miss — shared cache prevents thrash after that.
- Full Mission cold (~785 ms) still pays first product-panel attach (incl. voice diagnose once); warm full returns from `_FULL_CACHE` (~15–22 ms).
- Focus briefing is local (e.g. active project line) — no ACM poll on Focus.

---

## Regression / integrity

Source: `docs/evidence/room_repair_phase3a/post_repair_regression.json`.

| Check | Result |
| --- | --- |
| Integrity scan (`trigger=tier3a-verify`) | **clean / 100 / 0 findings** |
| QA header write to live planner | **403** `production_isolation` |
| Test-shaped planner text | **400** refuse |
| Activity inbox contains `room-leave` | **false** (Tier 1 preserved) |
| Unit tests | `tests/test_phase3a_infrastructure.py` + MC cache updates — **pass** |

Production isolation was **not** weakened. No Health / ACM / Journal writes as part of 3A.

---

## Code touchpoints

- `jarvis/mission_control.py` — shared caches + lite/full
- `jarvis/mission_control_ops/enrich.py` — lite skips product panels; panel TTL
- `jarvis/mission_control_ops/automation_gate.py` — delegate to health_summary
- `jarvis/gui/server.py` — health-brief lite; MC full
- `jarvis/planner_services.py` — Focus local briefing
- `jarvis/voice_product/mission_bridge.py` — panel TTL
- `jarvis/gui/static/aria_shared_fetch.js` — coalesce
- `jarvis/gui/static/workspace/workspace.js` + `registry.js` — SYS-F08
- Callers: `living_interface.js`, `dashboard_home.js`, `living_room_presence.js`, `priority3_rooms.js`
- `jarvis/gui/static/index.html` — script include + cache-bust
- `tests/test_phase3a_infrastructure.py`

---

## What became functional (systemic only)

- Mission health-brief / health_summary no longer re-fan-out product panels every poll.
- Planner Focus no longer pays ACM search on every poll.
- `#presence` / `#dashboard` boot map points at Presence / Home activities (served JS verified).
- Duplicate Home dashboard GETs share one in-flight request when `AriaSharedFetch` is loaded.

**No Room** meets CERTIFIED FUNCTIONAL. Core Room defects (Health load, Home failure paths, Audio, Projects, etc.) remain for **Tier 3B**.

---

## What remains broken / unproven

- All **22** audit functional-defect Rooms (and **12** UNKNOWN) — Room contracts not run in 3A.
- SYS-P03: **151** scripts / house payload weight.
- Cold Platform MC collect (~1.7s) on first miss — still real.
- Cold full Mission first product-panel attach (~0.8s) — better than before, still not “instant.”
- Owner-browser confirmation of SYS-F08 `body.dataset.room === "presence"` was attempted via IDE browser; the automation tab did not receive a painted document (`documentElement` null). Served static map + unit guard are evidence; owner UI confirm should be rechecked in Jeff’s real Chrome/Electron before Presence Room work in 3B/3C.

---

## Contamination status

- Integrity **clean / 100**
- Isolation guards intact
- Tier 2 Health deletions remain the authority (not re-touched)
- Focus unit test uses disposable `DB_PATH` under pytest tmp

---

## Next authorized batch (do not start until Jeff says)

**Tier 3B — Core Rooms** (after this STOP):

1. Health (isolated test state only; protect live PHR)
2. Home
3. Audio
4. Projects
5. Providers
6. Home Automation
7. Mission Control

Then 3C domain Rooms → 3D UNKNOWN → final 34-Room owner residency only after complete proof.

---

## Absolute status line

**Tier 3A complete. STOP. Awaiting authorization for Tier 3B.**
