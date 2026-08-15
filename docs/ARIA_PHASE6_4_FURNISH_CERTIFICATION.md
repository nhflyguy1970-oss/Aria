# Phase 6.4 — Furnish the House — Certification Report

**Date:** 2026-08-06  
**Law:** Original Aria is the specification. Living Workspace is the implementation. No subset.  
**Method:** `AriaFurnish` mounts full original `#*View` panels onto `#ariaStage`. Chat remains Living Room.

---

## Verdict

**Functional migration of original surfaces: Verified operational at Room / House Control grain.**  
All **32** legacy view panels are reachable from the Living Workspace. Whole-house enter sweep: **32/32 ok**. Front Door + status chrome restore House Controls.

Certification continues at overflow/dialog grain whenever a defect is found — identify → repair → verify → regress.

---

## Architecture (unchanged backends)

| Layer | Status |
|---|---|
| Backend APIs / storage / services | Reused — not rewritten |
| Living Workspace stage (`#ariaStage`) | One Room at a time |
| `AriaFurnish` | Mounts full `#*View` + `runLegacyInit` |
| Chat | Living Room immersion preserved |

---

## Surfaces — Verified operational

All rooms in `docs/ARIA_PHASE6_4_FURNISH_INVENTORY.md` Surfaces table: **Verified operational** (mount + primary workflows exercised through native Living Workspace).

Includes previously missing: Journal, Video, Audio, Browser, Maker, Meme, Vision, Connections, Settings, Capabilities, Integrations, Audit, Security, Actions.

---

## House Controls — Verified operational

| Control | Reachability |
|---|---|
| Restart Server | Front Door `ctrl:restart` |
| Uncensored / Safe Mode synonym | Front Door `ctrl:uncensored` → auth modal |
| Appearance / Theme | Front Door `ctrl:theme` + Settings |
| Providers / Model Selection | Providers room + Front Door |
| Repair / Guided Repair | Repair room → Recovery + `scanAndShow` |
| Production Integrity | Integrity room |
| GPU / Free VRAM | Front Door `ctrl:gpu` |
| Notifications / Activity | Status bar + Front Door |
| Job Center | Status bar + Front Door `tool:jobs` (`jarvisJobs.openJobCenter`) |
| Workspace Layouts | Status bar + Front Door `ctrl:layouts` |
| Performance / Databases / Diagnostics | Front Door → Mission tabs |
| Security / Settings / Voice / Audio / Memory | Front Door + Rooms |

---

## Defects repaired this phase (must not regress)

1. **Repair Guided Repair wiring** — wrong API → `AriaGuidedRepair.scanAndShow` + Recovery tab (`furnish.js` 6.4.1+).  
2. **Automation dry-run `undefined`** — FastAPI `Request` query-param bug → module-level imports; `api()` harden; pytest regression.  
3. **Audio empty shell** — remount when `#audioRecordBtn` missing (`audio.js`).  
4. **Job Center Front Door dead** — `#jobsCenterBtn` typo → `jarvisJobs.openJobCenter` / `#jobCenterBtn`.  
5. **Missing searchable House Controls** — layouts / performance / databases / diagnostics entries.  
6. **Mission Connection/Routing stuck Loading** — `mcFetch` timeout + orphan Loading recovery (`mission_control.js` 1.2.1).  
7. **Tools bypassed Furnish** — `switchToView` left wrong room chrome → `AriaHouse.enter` for tool `viewId`s (`tools.js` 2.0.3).

---

## Whole-house walk-through (Living Workspace only)

| Check | Result |
|---|---|
| Enter every furnished Room | 32/32 Verified operational |
| Front Door open (house icon / Ctrl+K path) | Verified operational |
| Health 31 tabs | Verified operational |
| Mission 20 tabs | Verified operational (after Loading race repair) |
| Fly search → recipe → compare → print → export → barcode | Verified operational |
| Documents preview + summarize/ask actions | Verified operational |
| Search federated run | Verified operational |
| Memory New → Encode | Verified operational |
| Journal rapid log + export/print controls | Verified operational |
| Automation dry run / run / pause / resume | Verified operational |
| Planner add task | Verified operational |
| Gallery / Video / Maker / Meme / Vision / Browser | Verified operational |
| Job Center / Layouts / Activity / Uncensored from LW chrome | Verified operational |

---

## Proof artifacts

- Inventory / completion log: `docs/ARIA_PHASE6_4_FURNISH_INVENTORY.md`
- Key code: `jarvis/gui/static/workspace/rooms/furnish.js`, `house_host.js`, `front_door_catalog.js`, `tools.js`
- Automation regression: `tests/test_automation_product.py::test_automation_request_annotation_resolves`

---

## Ongoing duty

Phase 6.4’s stopping condition is zero missing user-facing capabilities. Room furniture restores the original action surfaces; any future failure discovered in daily use follows the same stop → diagnose → repair → verify → regress loop under Phase 6 residency.
