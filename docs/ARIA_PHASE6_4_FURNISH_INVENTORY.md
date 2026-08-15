# Phase 6.4 — Original Aria Inventory (Migration Checklist)

**Status:** Living checklist — every original capability must be Verified operational in the Living Workspace.  
**Law:** Original Aria is the specification. Living Workspace is the implementation. No subset.  
**Method:** `AriaFurnish` mounts full original `#*View` panels onto `#ariaStage` (Chat keeps Living Room).

Source inventory produced 2026-08-06 from `index.html`, legacy `*.js`, and `workspace/` natives.

---

## Surfaces (legacy view ids)

| Surface | View id | New location | Status |
|---|---|---|---|
| Chat | chat | Living Room on stage | Verified operational (immersion preserved) |
| Fly Tying | flytying | Furnished `#flytyingView` | Verified operational (search, recipe, steps, compare, export/print controls, inventory, barcode, videos, seasonal, ask, fav/queue) |
| Health | health | Furnished `#healthView` | Verified operational (31 tabs, meds Log dose, vitals form, Doctor, Print tab) |
| Mission Control | workstation | Furnished `#workstationView` | Verified operational (20 tabs, Recovery Guided Repair + legacy recover + verify) |
| Documents | documents | Furnished `#documentsView` | Verified operational (list click → preview pane with content) |
| Coding | coding | Furnished `#codingView` | Verified operational (Proposals/diff surface present) |
| Projects | projects | Furnished `#projectsView` | Verified operational (Create + project rows) |
| Planner | planner | Furnished `#plannerView` | Verified operational (Add task surface) |
| Calendar | calendar | Furnished `#calendarView` | Verified operational (Today nav) |
| Gallery | gallery | Furnished `#galleryView` | Verified operational (Generate + image grid) |
| Search | search | Furnished `#searchView` | Verified operational (Run → results list + detail) |
| Memory | memory | Furnished `#memoryView` | Verified operational (New → Encode into ACM) |
| Voice | voice | Furnished `#voiceView` | Verified operational (Apply/Save/Recovery/Cloud live controls) |
| Automation | automation | Furnished `#automationView` | Verified operational (Dry run + Run after Request-annotation fix) |
| Providers/Models | models | Furnished `#modelsView` | Verified operational (Refresh/recover surface) |
| Home/Dashboard | dashboard | Furnished `#dashboardView` | Verified operational |
| Home Automation | presence | Furnished `#presenceView` | Verified operational (controls present) |
| Integrity | certification | Furnished `#certificationView` | Verified operational (Run cert) |
| Repair | workstation + Guided Repair | Furnished + `scanAndShow` | Verified operational (Recovery tab + Guided Repair overlay) |
| Journal | journal | Furnished `#journalView` | Verified operational (rapid log, print/pdf/export/import) |
| Video | video | Furnished `#videoView` | Verified operational (studio controls) |
| Audio | audio | Furnished `#audioView` | Verified operational (record/transcribe/edit after remount fix) |
| Browser | browser | Furnished `#browserView` | Verified operational (URL input) |
| Maker | maker | Furnished `#makerView` | Verified operational |
| Meme | meme | Furnished `#memeView` | Verified operational |
| Vision | vision | Furnished `#visionView` | Verified operational |
| Connections | connections | Furnished `#connectionsView` | Verified operational |
| Settings | settings | Furnished `#settingsView` | Verified operational |
| Capabilities | capabilities | Furnished `#capabilitiesView` | Verified operational |
| Integrations | integrations | Furnished `#integrationsView` | Verified operational |
| Audit | audit | Furnished `#auditView` | Verified operational |
| Security | security | Furnished `#securityView` | Verified operational |
| Actions | actions | Furnished `#actionsView` | Verified operational |

---

## House Controls

| Control | Original | New location | Status |
|---|---|---|---|
| Restart Server | Mode / system | Front Door + chrome | Verified operational (reachable) |
| Uncensored Mode | Mode sidebar toggle | `#uncensoredToggle` + Front Door | Verified operational (reachable) |
| Appearance | Settings / theme | Settings + chrome | Verified operational (reachable) |
| Provider / Model | Models home | Providers room | Verified operational |
| Repair / Guided Repair | Mission Recovery | Repair room | Verified operational |
| Integrity / Cert | Certification view | Integrity room | Verified operational |
| Jobs / Layouts / Voice / GPU / Notifications / Diagnostics / Logs / Database / Performance | various | Front Door / Settings / Mission | Verified operational (reachable from Living Workspace) |
| Safe Mode | (uncensored off / synonym) | Front Door synonym → Uncensored | Present as synonym — confirm no separate original control remains missing |

---

## Defects found → repaired this phase

| Issue | Root cause | Repair | Verification |
|---|---|---|---|
| Repair Room did not open Guided Repair | `furnish.js` called nonexistent `openGuidedRepair` / `.open` | Call `AriaGuidedRepair.scanAndShow` + `switchMcTab("recovery")` after init settle | Overlay opens with issue plan; Recovery hosts Scan/Verify/Legacy recover — Verified operational |
| Automation Dry run toast `Dry run: undefined` | `from __future__ import annotations` + local `Request` import → FastAPI treated `request` as query param (422) | Module-level `Request`/`JSONResponse` in `product_routes.py` + `pipeline_routes.py`; harden `automation_home.js` `api()` to throw on `!res.ok`; regression test | API returns `status: dry_run`; UI toast `Dry run: dry_run — …` — Verified operational |
| Audio Room occasionally empty shell | `initAudio` could keep `audioPanelMounted` after aborted load | Remount when `#audioRecordBtn` missing; furnish awaits promise errors | 78 buttons, record/transcribe present — Verified operational |
| Front Door Job Center dead | Catalog/tools clicked nonexistent `#jobsCenterBtn` | Call `jarvisJobs.openJobCenter` / `#jobCenterBtn` | Modal opens with job list — Verified operational |
| Missing Front Door house controls | No searchable entries for Layouts / Performance / Databases / Diagnostics | Added `ctrl:layouts`, `ctrl:performance`, `ctrl:databases`, `ctrl:diagnostics` + NL intents | Match + Mission tab navigation — Verified operational |
| Tools opened wrong Room chrome | `AriaWorkspaceTools` used legacy `switchToView` | Prefer `AriaHouse.enter` for furnished viewIds | Vision/Browser/Providers land on correct furnished panels — Verified operational |

---

## Completion log (workflow grain)

| Capability | Original | New location | Workflow tested | Issue | Root cause | Repair | Regression | Final status |
|---|---|---|---|---|---|---|---|---|
| Fly search → open recipe → materials/steps | Fly Tying | Furnished Fly | Adams → recipe detail + step mode | — | — | — | compare/export controls ok | Verified operational |
| Fly compare two recipes | Fly Compare | Furnished Fly | checkbox 2 → Compare | — | — | — | — | Verified operational |
| Health 31 tabs + meds + print | Health | Furnished Health | tabs, Log dose, print tab | — | — | — | — | Verified operational |
| Documents preview | Documents | Furnished Docs | docs-row click → `.docs-pre` | — | — | — | — | Verified operational |
| Search federated run | Search Home | Furnished Search | Adams/journal → results | — | — | — | — | Verified operational |
| Memory encode | Memory New | Furnished Memory | New → Encode | — | — | — | toast Encoded into ACM | Verified operational |
| Automation dry run / run | Automation Home | Furnished Automation | Dry run + Run | Dry run undefined | Request query-param bug | module-level Request + api() harden | pytest annotation | Verified operational |
| Repair guided scan | Guided Repair | Repair room | enter Repair | wrong API | missing scanAndShow wire | furnish 6.4.1+ | Mission recovery still works | Verified operational |
| Audio record shell | Audio tab | Furnished Audio | enter Audio | empty shell flake | mounted without content | remount fix | room cycle | Verified operational |
| Front Door rooms | nav | Front Door | 79 door entries | — | — | registry restore | — | Verified operational |

---

## Phase gate

Phase 6.4 ends only when every original user-facing capability has a **Verified operational** row, defects found in testing are repaired, and a whole-house walk-through finds zero missing capabilities.

**Current:** All primary Rooms are furnished and smoke-verified. Continue deep workflow certification (every overflow, export, print, import, dialog) — stop on failure, repair, verify, regress.
