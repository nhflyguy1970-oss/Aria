# Aria Phase 5 — Native Room Migration
## Priority 1 + Priority 2 + Remaining Flagships

**Date:** 2026-08-06  
**Status:** Flagship Rooms **NATIVE** (Workspace mode). Proof: `docs/_phase5_flagship_proof.json` — **PASS**  
**Backend:** Unchanged  
**House Integrity:** Preserved  

No polish. Native first. Consistency before perfection.

---

## Priority 2 (requested) — all six

| Room | Native root | Atmosphere |
|---|---|---|
| Documents | `#documentsRoom` | Private library |
| Coding | `#codingRoom` | Engineering studio |
| Projects | `#projectsRoom` | Creative workshop |
| Planner | `#plannerRoom` | Leather notebook |
| Gallery | `#galleryRoom` | Museum |
| Search | `#searchRoom` | Research study |

**Evidence:** Each mounts as `nativeRoom` on `#ariaStage`; legacy `#*View` panels never on stage; House `isNative` true; Activity Engine entry works.

---

## Continued without pause — Priority 3 + remaining flagships

| Room | Native root |
|---|---|
| Memory | `#memoryRoom` |
| Voice | `#voiceRoom` |
| Repair | `#repairRoom` |
| Integrity | `#integrityRoom` |
| Automation | `#automationRoom` |
| Providers | `#providersRoom` |
| Home automation | `#homeAutoRoom` |
| Home (foyer) | `#homeRoom` |
| Calendar | `#calendarRoom` |

Plus Priority 1: Fly Tying, Health, Mission, and Chat (Living Room).

**Registered natives:** 18 via `AriaRoomKit` (+ Chat Living Room).

---

## Architecture (unchanged house)

```
#ariaStage  →  exactly one native Room root
AriaHouse.enter(room)  →  AriaRoomKit.get(room).enter()
view_router  →  skips legacy init* when native exists
legacy .app  →  inert inventory (compatibility path only)
```

Shared craft: `room_kit.js` (`defineRoom`), `native_rooms.css`.

---

## Legacy bridges removed (Workspace)

| Removed behavior |
|---|
| Mounting `#documentsView`, `#codingView`, `#projectsView`, `#plannerView`, `#galleryView`, `#searchView`, and all other flagship `#*View` panels onto the stage |
| Calling `initDocumentsTab` / `initCodingHome` / `initProjects` / `initPlanner` / `loadGallery` / `initSearchHome` / … under Workspace when natives exist |
| All `#*View` migration skins in `house.css` (23 rules deleted) |

Legacy JS/HTML still ships for `?workspace=0` only — not painted in Living Workspace. No new investment in that path.

---

## Technical debt / simplification

| Change | Effect |
|---|---|
| `priority2_rooms.js` + `priority3_rooms.js` | One defineRoom pattern for remaining flagships |
| `house_host.js` 5.1.0 | Kit-first; no per-room mount adapters for flagships |
| `view_router.js` 2.2.0 | Single `hasNativeRoom` gate |
| `house.css` | Variables only for house-* — no panel decoration |
| Proof walk | 19 rooms, always 1 stage child, 0 legacy panels on stage |

---

## Performance observations

- Room enter loads only its API surface (home/list/query) — no legacy panel bind/render tree
- Stage swap parks prior native root in `#ariaNativeHold` (no dual paint)
- Full walk (~19 enters) completed headless in ~17s including network
- Pre-existing unrelated pageerrors in shell soft-tip remain (not Room regressions)

---

## Remaining (honest)

| Item | Status |
|---|---|
| Flagship Rooms native in Workspace | **Done** |
| Deep workflows (barcode inventory, 30 health tabs, full MC tabs) | Intentionally not re-dashboarded — extend via overflow/tools when daily use demands |
| Delete legacy `*.js` / `#*View` HTML from repo | Deferred until Runtime Independence retires `?workspace=0` |
| Non-registry surfaces (maker, browser, settings, journal, video…) | Tools/secondary — migrate when they become Rooms or stay tools |
| Polish | **Stopped** until product asks — Phase 5 goal was native birth, not perfection |

---

## Phase 5 stopping condition

| Criterion | Status |
|---|---|
| Every flagship Room native | **PASS** (registry Rooms) |
| No migrated interiors on stage | **PASS** |
| No content bridges for flagships in Workspace | **PASS** |
| One Workspace / one rendering model | **PASS** |
| Visual polish of every Room | Out of scope (explicit) |

**Phase 5 flagship migration: COMPLETE for Living Workspace.**  
Polish and legacy-asset deletion are follow-ons, not blockers for “born inside Aria.”

---

## Files

- `workspace/rooms/room_kit.js` 5.1.0  
- `workspace/rooms/priority2_rooms.js`  
- `workspace/rooms/priority3_rooms.js`  
- `workspace/rooms/native_rooms.css`  
- `workspace/rooms/house_host.js` 5.1.0  
- `view_router.js` 2.2.0  
- `workspace/rooms/house.css` (skins removed)  
- `docs/_phase5_flagship_proof.json`  
- `docs/ARIA_PHASE5_NATIVE_ROOMS.md` (this report)
