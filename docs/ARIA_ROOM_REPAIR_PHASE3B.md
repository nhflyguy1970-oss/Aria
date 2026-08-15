# ARIA — Room Repair Phase 3B (Tier 3B)

**Date:** 2026-08-12  
**Mode:** Core Room functional repair. **STOP before Tier 3C.**  
**Baseline (unchanged):** `docs/ARIA_COMPLETE_ROOM_FUNCTIONALITY_AUDIT.md`  
**Prior phases:** `docs/ARIA_ROOM_REPAIR_PHASE1.md`, `PHASE2`, `PHASE3A`  
**Evidence:** `docs/evidence/room_repair_phase3b/`

**No Room is CERTIFIED FUNCTIONAL.** Final certification remains reserved for complete 34-Room owner residency.

Live serve after Tier 3B: PID from `:8765` after Projects/Health restarts (see evidence timestamps).

---

## Verdict

Tier 3B is **complete for its authorized scope**: seven Core Rooms repaired or proven through owner UI where defects remained, production protected, Integrity clean. **STOP.**

Aria is still **not** Owner-Residency certified. Domain/UNKNOWN Rooms remain for Tier 3C+.

---

## Room status summary

| Room | Starting (audit) | Tier 3B status |
| --- | --- | --- |
| Health | DEF-HEA-01 PHR fail | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Home | Load failed / identity issues | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Audio | Status fail / empty | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Projects | Loading… hang | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Providers | Thin / incomplete surface | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Home Automation | Status / identity issues | **REPAIRED — AWAITING FINAL CERTIFICATION** |
| Mission Control | Slow + incomplete E2E | **REPAIRED — AWAITING FINAL CERTIFICATION** |

---

## 1. HEALTH

### Starting condition
Audit: “Health failed to load” (DEF-HEA-01).

### Reproduction / diagnosis
- Live APIs `/api/health/home`, `/medications`, `/overview` returned 200 with Vitamin D3 `med_39bcc7df3187`.
- Playwright owner UI (`#health`) loaded furnished PHR; 31 tabs opened without fail cues (`health_tab_census.json`).
- Original walk failure likely abort/rapid-nav (Tier 1 class), not PHR corruption.

### Defect discovered & repaired
| ID | Symptom | Root cause | Repair |
| --- | --- | --- | --- |
| DEF-HEA-RESTORE-500 | Wrong backup password → **500** Internal Server Error | `decrypt_bundle` ValueError uncaught; safety backup created before password validation | Catch wrong password → **400** owner message; validate password **before** safety backup (`backup.py`, `api.py`) |

### Capabilities proven
**Live (read-only):** Room enter; Vitamin D3 on Meds; search “Vitamin D3”; leave→chat→return→Meds; 31 tabs load without error cues.  
**Isolated disposable serve `:8766` / `/tmp/aria-tier3b-health-isol` (destroyed after):** create med, dose, vitals, check-in, activity, encrypted backup, UI dose/check-in/backup, edit med, delete med, restart persistence, wrong-password 400, correct restore 200.

### Production protection
Live inventory after all Health work: **only** `med_39bcc7df3187` Vitamin D3; vitals/checkins/activities/backups **0**. Isol directory removed.

### Performance
Health enter usable ~seconds (SPA boot); overview/home APIs tens–hundreds of ms.

### Remaining / honest limits
- Not every Health form cancel/retry path exhaustively UI-scripted.
- Live mic-less; encryption step-up PIN not exercised against live PIN.
- Final certification still required at 34-Room residency.

---

## 2. HOME

### Starting condition
Audit: Home unavailable / duplicate dashboard fetches; identity confusion with Home Automation (Tier 3A map fixed).

### Owner UI proof
- Front Door / `goRoom('home')` → `body.dataset.room=home`, hash `#dashboard`.
- Welcome/greeting/widgets present (weather Charlestown, Health, Planner, Projects, etc.).
- Leave → chat → return → Home still loads.
- Evidence: `home_ok.png`, `core_rooms_proof.json`.

### Root cause notes
Load path healthy after Tier 1/3A. No additional backend patch required in 3B.

### Remaining
- Cold dashboard can still report occasional widget diagnostic noise; primary foyer is usable.
- Not every widget deep-link exhaustively clicked.

---

## 3. AUDIO

### Starting condition
Audit: “Could not load audio status”; 2 buttons.

### Owner UI proof
- Room `audio` loads furnished panel with **90** controls (record/transcribe/TTS/music/library).
- `/api/audio/status` 200 (~0.6s).
- No “could not load audio status” fail cue.

### Remaining / dependency
- Mic/device capture and wake-word install paths need hardware permissions — mark those controls as **owner-device dependent** for final residency, not silently skipped.
- Did not run long recording jobs against live library as certification (would mutate owner audio store).

---

## 4. PROJECTS

### Starting condition
Audit: stuck on **Loading…**.

### Root cause
`/api/projects/home` paid **~3s** every load via live assistant **`memory.search`** (ACM) in `_today_workspace` / `_memory_section`, plus duplicate `_coding_section` git work. In-process without ACM search was ~0.25s; HTTP matched the ACM cost.

### Repair
- Replace Project Home memory pulls with **local namespace listing** (`list_entries` / `list` / `get_all` filter) — no semantic search on every poll.
- Pass coding section once into `_today_workspace`.
- Frontend: paint list + clear `projectsActive` “Loading…” from fast `/api/projects` before full home enrich.
- Cache-bust `projects.js?v=5.17.3-tier3b`.

### Proof
- `/api/projects/home` after repair: **~15–32 ms** (was ~3000 ms).
- Owner UI: Active workspace `home-lab`, project list visible, home panel rendered (~1.6s enter including SPA).
- Evidence: `projects_ok.png`, timings in `core_rooms_proof.json`.

### Remaining
- Create/import/archive mutation not written into live production (isolation). Final residency should prove create/switch/archive on disposable DATA_DIR + one real owner switch Jeff confirms.

---

## 5. PROVIDERS

### Starting condition
Audit: thin Providers surface.

### Owner UI proof
- Room `providers` / Models panel: Overview, Roles, Catalog, Providers after Refresh.
- Text includes ollama/model/provider content (`hasModels`).
- `/api/models/home` ~0.7s.

### Remaining
- Did **not** write test credentials into production.
- Provider connect/save/remove with real secrets left for Jeff-attended final residency where required.

---

## 6. HOME AUTOMATION

### Starting condition
Audit: HA status / wrong Room identity.

### Owner UI proof
- `goRoom('home_automation')` → `body.dataset.room=home_automation` (not Home/Presence/Mission).
- Status **Connected** to `http://127.0.0.1:8123`; lights/scenes visible (~9 `light.` entities in panel text).
- Tier 3A presence/home map remains intact.

### Remaining
- **Physical light toggle not auto-executed** (avoid surprising house state). Actuation should be Jeff-confirmed in final residency.
- One entity shows `unavailable` in UI (Lamp) — dependency/device truth, not hidden.

---

## 7. MISSION CONTROL

### Starting condition
Audit: slow health + incomplete E2E. Tier 3A fixed warm lite paths.

### Owner UI proof
- Room `mission` loads; health line **Live · degraded** (honest, not fake healthy).
- Refresh works; Routing tab reachable.
- Warm `/api/mission-control` **~16 ms** cached; health-brief **~4 ms**.
- First miss after process start still **~3.6 s** full enrich (product panels / voice diagnose) — **not hidden**.

### Remaining
- Cold full attach cost remains known (Tier 3A documented).
- Do not treat degraded overall as a functional UI defect; it is operator truth.

---

## Systemic defect found during 3B

| ID | Rooms | Cause | Repair |
| --- | --- | --- | --- |
| SYS-P01-class (Projects) | Projects (+ any poll using memory.search) | Semantic ACM search on Project Home | Local namespace list |
| DEF-HEA-RESTORE-500 | Health backups | Wrong password → 500 | 400 + validate-before-safety |

No other cross-Core systemic defect required stopping the sequence.

---

## Performance snapshot (post-3B)

| Path | ms |
| --- | ---: |
| `/api/projects/home` | ~15–32 |
| `/api/dashboard/home?stale_ok=true` | ~67 |
| `/api/audio/status` | ~647 |
| `/api/models/home` | ~706 |
| `/api/smarthome/product/home` | ~5 |
| `/api/mission-control` warm | ~16 |
| `/api/mission-control` cold | ~3600 |
| `/api/mission-control/health-brief` | ~4 |

---

## Regression / integrity / isolation / Activity

| Check | Result |
| --- | --- |
| Integrity | **clean / 100 / 0 findings** |
| QA header → live planner | **403** |
| Test-shaped planner text | **400** |
| Activity `room-leave` in owner inbox | **false** |
| Live Health meds | **only Vitamin D3** `med_39bcc7df3187` |

---

## Unresolved / blockers for final certification

1. Cold Mission full enrich ~3.6s (known; not certified-away).
2. HA physical actuation not auto-proven.
3. Audio hardware-dependent controls not device-proven.
4. Provider credential mutation not live-proven (correct isolation).
5. Projects create/archive not live-proven (isolation).
6. Complete 31-tab Health mutation matrix only on disposable isol (destroyed).
7. SYS-P03 (151 scripts) still open from Tier 3A.
8. 27 non-Core Rooms untouched (Tier 3C / 3D / final residency).

---

## Exact remaining Tier 3C workload

Use live 34-Room registry. After Core Rooms, remaining work includes (non-exhaustive vs registry): Fly Tying, Journal, Gallery, Browser, Voice, Video, Maker, Audit, Memory, Connections, Meme, Presence, Calendar, Planner, Documents, Coding, Search, Repair, Integrity, Settings, Capabilities, Integrations, Security, Actions, Automation, Chat/Living Room — plus any other registry Rooms not in the Core seven.

Do **not** start Tier 3C until authorized.

---

## Absolute status line

**Tier 3B complete. STOP. Awaiting authorization for Tier 3C.**  
**0 / 34 CERTIFIED FUNCTIONAL. Seven Core Rooms: REPAIRED — AWAITING FINAL CERTIFICATION.**
