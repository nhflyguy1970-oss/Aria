# OPERATIONAL CERTIFICATION REPORT
## Aria Next Generation — Phase 6.3

**Residency mode:** Live in the house. One interruption at a time. Repair. Verify. Certify.  
**Date:** 2026-08-06  
**Ledger:** `docs/OPERATIONAL_CERTIFICATION_LEDGER.md`

---

## Whole-house answer

**Yes — for native Living Workspace primary workflows exercised in this residency.**

Jeff can enter Rooms through the Front Door / House, accomplish the primary work listed below without hitting the interruptions that were found and repaired, and navigate without listener death on re-entry. Chat streams. Provider recover works. Documents open. Projects create/switch. Gallery can queue generation. Memory can write. Coding can review diffs. Mission can recover the provider and offer Restart Aria. Health check-in and timeline load.

**Still incomplete relative to full legacy depth (logged, not ignored):** Fly video/print/export/compare, Health medication CRUD / vitals entry / doctor print beyond overflow links, Voice wake/listen controls, Documents OCR/export/print, Gallery still library is empty on disk (generate works), Home Automation device toggles beyond status. Those are next interruptions if Jeff hits them — not claimed certified here.

---

## Interruptions repaired (this residency)

### OC-1 — Layouts script SyntaxError (house-wide)
| Field | Detail |
|---|---|
| **Room** | House / Layouts |
| **Workflow** | Boot / any page load |
| **Severity** | High — `workspace_layouts.js` failed to parse |
| **Root cause** | `??` mixed with `\|\|` without parentheses (invalid in JS) |
| **Repair** | Parenthesize: `filterQ ?? ($("layoutsTypeahead")?.value \|\| "")` |
| **Files** | `jarvis/gui/static/workspace_layouts.js`, `index.html` cache bump |
| **Before** | `SyntaxError: missing ) after argument list`; `AriaLayouts` undefined |
| **After** | Script parses; `typeof AriaLayouts === "object"` |
| **Verification** | Playwright load + `new Function(body)` on served file `?v=1.1.1-oc` |
| **Regression** | Living Workspace + Chat on stage still present |
| **Certification** | Verified |

### OC-2 — Soft tip crash (`tipDismissed` object)
| Field | Detail |
|---|---|
| **Room** | House / Discoverability |
| **Workflow** | Soft tip after ~4s |
| **Severity** | Medium — pageerror every boot |
| **Root cause** | Prefs default `tipDismissed: {}` but code did `new Set(prefs().tipDismissed \|\| [])` — objects are not iterable |
| **Repair** | Coerce array/object keys; default prefs to `[]` |
| **Files** | `discoverability.js`, `ui_prefs.js`, shell bundle cache bump |
| **Before** | `object is not iterable` |
| **After** | Tip renders; no pageerror; object legacy prefs coerced |
| **Verification** | Wait 5s; tip text present; force object prefs + dismiss path |
| **Certification** | Verified |

### OC-3 — Provider recover API broken (Chat recovery)
| Field | Detail |
|---|---|
| **Room** | Chat / Providers / Mission |
| **Workflow** | Auto-recover after `FIRST_PROGRESS_TIMEOUT` |
| **Severity** | Critical — Chat recovery path 422’d |
| **Root cause** | `from __future__ import annotations` + *local* `from fastapi import Request` → FastAPI treated `request` as a required **query** param |
| **Repair** | Module-level `Request` / `JSONResponse` imports; regression test |
| **Files** | `jarvis/provider_health/api.py`, `tests/test_provider_health.py` |
| **Before** | `{"detail":[{"loc":["query","request"],...}]}` |
| **After** | `POST /api/provider/recover` → `ok: true`, `usable: true`; Chat stream returns `PONG` |
| **Verification** | Server restart to load fix; curl recover; multipart chat stream tokens; UI send → `PONG` |
| **Regression** | Front Door, stage mount, living workspace intact |
| **Certification** | Verified |

### OC-4 — Documents Open/Preview missing
| Field | Detail |
|---|---|
| **Room** | Documents |
| **Workflow** | Browse → Open → Preview |
| **Severity** | High — list only, rows not actionable |
| **Root cause** | Native room rendered inert rows; no `/api/documents/preview` wiring |
| **Repair** | Clickable rows + preview pane via preview API |
| **Files** | `priority2_rooms.js`, `native_rooms.css`, `index.html` |
| **Before** | Click did nothing |
| **After** | Vision + memory cheatsheets open with character counts and body text |
| **Verification** | Playwright open two docs; re-enter Chat/Fly still mounts |
| **Certification** | Verified |

### OC-5 — Room re-enter destroyed event listeners
| Field | Detail |
|---|---|
| **Room** | Mission, Health, Fly Tying, all `defineRoom` Rooms |
| **Workflow** | Leave Room → return → interact |
| **Severity** | High — forms/overflow silently dead |
| **Root cause** | `buildShell` always rewrote `innerHTML` while `dataset.wired` blocked re-binding |
| **Repair** | `dataset.shellBuilt` — build/wire once; refresh data on enter |
| **Files** | `mission_room.js`, `health_room.js`, `flytying_room.js`, `room_kit.js` |
| **Before** | Second enter: overflow/check-in/search dead |
| **After** | Mission recover after re-enter; Health check-in after re-enter; Fly search after re-enter |
| **Verification** | Playwright leave/return loops |
| **Certification** | Verified |

### OC-6 — Mission missing Recover / Restart / Providers card
| Field | Detail |
|---|---|
| **Room** | Mission Control |
| **Workflow** | Recover provider, Restart Aria, see provider status |
| **Severity** | High for ops residency |
| **Repair** | Overflow: Recover provider, Restart Aria (confirm); Providers card |
| **Files** | `mission_room.js` |
| **Verification** | Recover click → status path; Providers card shows `ollama`; Restart confirm dismissed in test |
| **Certification** | Verified (Restart confirm path present; not force-restarted in final pass) |

### OC-7 — Gallery Generation missing
| Field | Detail |
|---|---|
| **Room** | Gallery |
| **Workflow** | Generation |
| **Severity** | High — browse-only walls |
| **Repair** | Generate form → `POST /api/gallery/generate` |
| **Files** | `priority2_rooms.js` |
| **Before** | Empty walls, no create path |
| **After** | Queue message with job position |
| **Note** | Library has 0 stills on disk (videos only) — empty browse is truthful |
| **Certification** | Verified |

### OC-8 — Projects Create / Switch missing
| Field | Detail |
|---|---|
| **Room** | Projects |
| **Workflow** | Create, Open/Switch |
| **Repair** | Create form + clickable switch via `/api/projects` + `/api/projects/switch` |
| **Verification** | Created two projects; switched both ways |
| **Certification** | Verified |

### OC-9 — Memory Write missing
| Field | Detail |
|---|---|
| **Room** | Memory |
| **Workflow** | Write, Search/filter |
| **Root cause** | Read-only list; write went to active project namespace and vanished from home list |
| **Repair** | Remember form → `POST /api/memory` with `namespace: profile`; merge `/api/memory/all`; local prepend + filter |
| **Verification** | Wrote `OC memory write …`; appeared in list and filter |
| **Certification** | Verified |

### OC-10 — Coding Diff / Apply missing
| Field | Detail |
|---|---|
| **Room** | Coding |
| **Workflow** | Diffs, Apply |
| **Repair** | Open proposals list; Diff via `/api/proposals/{id}`; Apply via `/api/apply` with confirm |
| **Verification** | Six proposals listed; Diff showed unified diff text |
| **Certification** | Diff Verified; Apply path present (confirm-gated) |

### OC-11 — Health Timeline missing / Automation Run missing
| Field | Detail |
|---|---|
| **Rooms** | Health, Automation |
| **Repair** | Health side Timeline from `/api/health/timeline`; Automation pipelines list + Run |
| **Verification** | Timeline shows check-ins; Automation lists 16 pipelines with Run |
| **Certification** | Verified |

---

## Room certification status

| Room | Status | Primary workflows verified | Notes |
|---|---|---|---|
| Chat | **Certified** | Conversation, streaming, send | Recover path fixed; long/voice/attach not fully re-exercised this pass |
| Front Door | **Certified** | Open (Ctrl+K / house), doors to Rooms | 18 doors |
| Fly Tying | **Certified (core)** | Browse, search, choose, materials, steps nav | Video/print/export/compare not in native Room |
| Health | **Certified (core)** | Check-in, meds display, timeline, doctor/emergency links | Meds CRUD / vitals entry not native |
| Mission | **Certified (core)** | Status, jobs, providers, hardware, recover, restart, repair link | Full legacy MC tabs not rebuilt |
| Documents | **Certified (core)** | Browse, search, open/preview | OCR/export/print not wired |
| Coding | **Certified (core)** | Workspace status, proposals, diff, apply affordance | Editor/search depth remains Chat/legacy |
| Projects | **Certified** | Create, switch, list | |
| Planner | **Certified** | Tasks list, add task, calendar link | |
| Gallery | **Certified (core)** | Generate queue, browse (empty library truthful) | Preview/export when stills exist — next |
| Search | **Certified** | Query, results, room routing sample | |
| Memory | **Certified** | Recall, write, filter | |
| Voice | **Partial** | Status cards load | Wake/listen/playback controls not native |
| Repair | **Certified (core)** | Evidence from mission+integrity | Approval flows via Guided repair activity |
| Integrity | **Certified (core)** | Score, deductions list | Demo leftover path is integrity finding, not UI stub |
| Automation | **Certified (core)** | Home cards, pipeline list, Run | |
| Providers | **Certified (core)** | Models home | |
| Home Automation | **Partial** | Status room loads | Device/scene execution not deepened this pass |
| Home | **Certified** | Orientation / presence | |
| Calendar | **Certified (core)** | Week view loads | |

---

## Regression evidence (shared)

After repairs, residency confirmed repeatedly:

- `#ariaStage` mounts exactly one Room  
- Front Door / house icon present  
- Chat returns to `#ariaStage #chatView`  
- No `coming soon` / `not implemented` placeholders in registered native Rooms  
- Provider recover + Chat stream healthy after server restart  

---

## Final certification statement

Operational Certification for Phase 6.3 **native primary workflows** is **passed** for the Rooms and paths listed as Certified above.

If Jeff moved into Aria today and used the Living Workspace as the house — Chat, Front Door, Fly bench core, Health check-in/timeline, Mission recover, Documents open, Coding diffs, Projects, Planner, Gallery generate, Search, Memory write, Automation run — he would not hit the broken primary paths that blocked this residency.

Deeper legacy capabilities not yet restored into native Rooms remain explicit next interruptions, not silent failures.
