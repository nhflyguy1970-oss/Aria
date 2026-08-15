# ARIA — Complete Room Functionality & Performance Audit

**Date:** 2026-08-11  
**Mode:** Audit and architectural assessment only. No code changes. No repairs. No optimizations. No UI redesign.  
**Runtime:** Living Workspace `http://127.0.0.1:8765/?workspace=1` (PID 3255320)  
**Entry path:** Front Door catalog `AriaFrontDoorCatalog.goRoom` + owner UI clicks  
**Evidence:** locked Cursor browser tab `3b1a59`; in-page fetch spy; `/tmp/aria-room-audit/`

---

## FINAL CERTIFICATION QUESTION

> **If Jeff opened every Room in Aria today and attempted to use every intended function of every Room through the normal owner UI, would every Room load completely, every function work end-to-end, every required dependency work, every result persist correctly, and the system remain reasonably responsive?**

**NO.**

Zero Rooms are **CERTIFIED FUNCTIONAL**.  
Jeff’s inspection matches the live product: most Rooms fail complete intended function; the house is not reasonably responsive as a whole.

This document is the truth baseline for the repair phase. It does not begin repairs.

---

## Verdict in one page

| Metric | Count |
| --- | ---: |
| Total Rooms (live registry) | 34 |
| CERTIFIED FUNCTIONAL | **0** |
| NOT CERTIFIED — FUNCTIONAL DEFECT | 22 |
| NOT CERTIFIED — PERFORMANCE DEFECT (Room-level only) | 0 (see systemic) |
| NOT CERTIFIED — DEPENDENCY BLOCKED (Room-level) | 0 (several *capabilities* are) |
| OWNER N/A | 0 |
| UNKNOWN (loads; complete function set not proven) | 12 |
| Total Tools (live registry) | 18 |
| Tools fully proven E2E | 0 |
| Systemic functional defects | 8 |
| Systemic performance defects | 5 |
| Isolated defects | 18 |
| Room mount after workspace is up (DOM ready) | 6–39 ms |
| Room enter including settle wait | ~709–743 ms |
| Slow shared APIs | 0.5–2.5 s |
| Activity Center at audit start | ~199 unread / 183 failures / 15 warnings |
| SPA DOM | 6900 nodes, 151 scripts, 49 dialogs/overlays |

Room mount is fast. Jeff’s slowness is **systemic**, not “each Room’s HTML is slow to attach.”

---

# 1. Authoritative Room inventory

Source of truth: live `AriaWorkspaceRegistry.rooms` in `jarvis/gui/static/workspace/registry.js`, confirmed in the running Living Workspace. Front Door opened with 35 door tiles (34 Rooms + skip/current). Not taken from prior residency lists (those had **27** Rooms).

| Room | route / viewId | hash | Front Door | Alt entries | Purpose (registry + catalog) | Tools | Auth | Persist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chat | `chat` | `#chat` | yes | Living Room, Ctrl+K ask | Conversation | — | session | threads |
| Fly Tying | `flytying` | `#flytying` | yes | Tools gallery/browser | Pattern bench | browser, gallery | — | catalog/session |
| Health | `health` | `#health` | yes | — | Personal Health Record | notifications | local | PHR |
| Mission Control | `workstation` | `#workstation` | yes | Ctrl+Shift+M | Infrastructure health | repair, integrity, providers, notifications | — | — |
| Documents | `documents` | `#documents` | yes | OCR tool | Private library | ocr, search, clipboard | — | files/index |
| Planner | `planner` | `#planner` | yes | N/P/F/T/U | Today’s actionable work | calendar, notifications | — | tasks/events |
| Calendar | `calendar` | `#calendar` | yes | Planner “Open Calendar” | Commitments | notifications | — | events |
| Gallery | `gallery` | `#gallery` | yes | Ctrl+Shift+G | Local image product | vision | — | media |
| Search | `search` | `#search` | yes | Ctrl+K, tool search | Federated search | — | — | saved searches |
| Coding | `coding` | `#coding` | yes | Ctrl+Shift+C, git/terminal tools | Propose→Apply→Undo | git, terminal, projects | — | proposals |
| Projects | `projects` | `#projects` | yes | tool projects | Workspace identity | git, terminal | — | project store |
| Memory | `memory` | `#memory` | yes | — | ACM autobiography | clipboard | — | ACM |
| Voice | `voice` | `#voice` | yes | voice HUD | Speak / STT / TTS / cloud live | — | cloud creds | settings |
| Repair | `workstation` | `#workstation` | yes | Guided Repair tool | Restoration / evidence | integrity, providers | — | repair plans |
| Integrity | `integrity` (native `#integrityRoom`) | `#integrity` | yes | Integrity tool | Production truth | repair | — | integrity store |
| Home | `dashboard` | `#dashboard` | yes | Ctrl+Home | Foyer / orientation | search | — | layout |
| Automation | `automation` | `#automation` | yes | Ctrl+Shift+O | Skills / rules / workflows | notifications | — | rules |
| Providers | `models` | `#models` | yes | Ctrl+Shift+., models tool | Model routing | — | provider keys | models store |
| Home Automation | `homeAutomation` | `#homeAutomation` | yes | HA token dialog | Lights / scenes / HA | automation | HA token | HA |
| Presence | `presence` | `#presence` | yes | Security | Camera / gestures | — | camera | gesture settings |
| Journal | `journal` | `#journal` | yes | Planner Journal | Daily pages | calendar, clipboard | optional encrypt | journal |
| Video | `video` | `#video` | yes | Gallery | Motion studio | gallery | Comfy/GPU | jobs |
| Audio | `audio` | `#audio` | yes | Voice | Sound / transcribe | voice | — | audio store |
| Browser | `browser` | `#browser` | yes | Ctrl+Shift+B, browser tool | Playwright agent | — | Playwright | sessions |
| Maker | `maker` | `#maker` | yes | — | CAD / slice / print | gallery | OpenSCAD/etc | CAD |
| Meme | `meme` | `#meme` | yes | Gallery | Meme generator | gallery | — | meme lib |
| Vision | `vision` | `#vision` | yes | Ctrl+Shift+I, vision tool | See / OCR | ocr, gallery | Ollama vision | settings |
| Connections | `connections` | `#connections` | yes | Memory link | Relationship graph | search | — | graph |
| Settings | `settings` | `#settings` | yes | Ctrl+, | Preference catalog | — | — | prefs |
| Capabilities | `capabilities` | `#capabilities` | yes | — | Extensions | — | — | loader |
| Integrations | `integrations` | `#integrations` | yes | — | Keys / health | — | secrets | secrets |
| Audit | `audit` | `#audit` | yes | — | System audit | repair | journalctl | reports |
| Security | `security` | `#security` | yes | lock overlay | PIN / trust | — | PIN | lock |
| Actions | `actions` | `#actions` | yes | — | Action history | — | — | log |

**18 Tools:** ocr, voice, vision, browser, clipboard, docker, git, notifications, providers, automation, repair, integrity, models, calendar, gallery, search, projects, terminal.

**House note:** Repair and Mission share `viewId: workstation`. Integrity is a **native** room (`#integrityRoom`), not furnished `#integrityView` / `#certificationView`. Phase 6.4 inventory still claimed Integrity = Certification Dashboard. That catalog is stale.

---

# 2. Intended capability set (not invented)

Taken from: live registry metaphors/heroes, Front Door blurbs, visible Room chrome, product copy on each surface, Tool registry, and established flagship docs. Capabilities listed below are what Aria **represents** as belonging to the Room. Absence in the live UI is a defect, not a reason to drop the capability.

Flagship / mature products expected complete: Health, ACM/Memory, Documents, Coding, Mission Control, Fly Tying, plus Planner/Calendar/Journal/Gallery/Search as daily-driver surfaces.

---

# 3–13. Owner-path test method

- Living Workspace only (`?workspace=1`).
- Enter via `AriaFrontDoorCatalog.goRoom` (same run as Front Door tiles).
- Mutations via owner controls (`plannerAddTaskBtn`, Delete, Memory Search, Fly Search, Home Retry, OCR tool invoke).
- APIs used only as **dependency / persistence witnesses**, never as proof the owner UI worked.
- No git reset, no app edits, no production-behavior changes.
- Audit-created planner task `AUDIT-ROOM-1786504544420` was deleted via the owner Delete control after persistence was confirmed.

**Coverage honesty:** Every Room was entered and its visible surface inspected. Every meaningful control in every Room was **not** individually driven to completion (Fly Tying alone exposes 235 controls). Untested controls are **UNKNOWN**. Under the certification rule, UNKNOWN blocks CERTIFIED FUNCTIONAL.

---

# 23. Master Room certification matrix

| Room | Loads | Complete Surface | Every Function | Every Control | Workflows | Persistence | Navigation | Dependencies | Performance | Final Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chat | Y | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | Y | systemic | **UNKNOWN** |
| Fly Tying | Y | Partial | N (search) | N | N | UNKNOWN | Y | catalog Y | systemic | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Health | Y | N | N | N | N | UNKNOWN | Y | PHR fail | systemic | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Mission Control | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | n/a | Y* | health API slow | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Documents | Y | Partial | UNKNOWN | UNKNOWN | OCR open only | UNKNOWN | Y | UNKNOWN | systemic | **UNKNOWN** |
| Planner | Y | N (Focus lie) | N | N | N | Partial | Y | focus 2.5s | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Calendar | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | month 610ms | **UNKNOWN** |
| Gallery | Y | N | N | N | N | UNKNOWN | Y | ComfyUI unavail | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Search | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | UNKNOWN | systemic | **UNKNOWN** |
| Coding | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | UNKNOWN | systemic | **UNKNOWN** |
| Projects | Y | N | N | N | N | N | Y | load hang | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Memory | Y | N | N | N | Partial | Partial | Y | ACM mixed | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Voice | Y | N | N | N | N | UNKNOWN | Y | cloud live | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Repair | Y | N (wrong Room) | N | N | N | n/a | **N** | shares MC | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Integrity | Y | N | N | N | N | UNKNOWN | Y | score 85 vs empty deductions | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Home | Y | N | N | N | N | n/a | Y | dashboard fail | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Automation | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | UNKNOWN | systemic | **UNKNOWN** |
| Providers | Y | N (2 controls) | N | N | N | UNKNOWN | Y | UNKNOWN | systemic | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Home Automation | Y | N | N | N | N | UNKNOWN | Y | HA “Home failed” | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Presence | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N (bodyRoom leak) | camera | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Journal | Y | N | N | N | N | UNKNOWN | Y | legend/stats fail | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Video | Y | N | N | N | N | UNKNOWN | Y | settings fail | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Audio | Y | N | N | N | N | N | Y | status fail | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Browser | Y | N | N | N | N | UNKNOWN | Y | Playwright unavail | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Maker | Y | N | N | N | N | UNKNOWN | Y | CAD undefined | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Meme | Y | N | N | N | N | N | Y | library abort | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Vision | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | moondream present | **UNKNOWN** |
| Connections | Y | N | N | N | N | N | Y | abort on leave | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Settings | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | Stores 9/12 earlier | **UNKNOWN** |
| Capabilities | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | loader | **UNKNOWN** |
| Integrations | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Y | secrets | **UNKNOWN** |
| Audit | Y | N | N | N | N | UNKNOWN | Y | journalctl timeout | **NOT CERTIFIED — FUNCTIONAL DEFECT** |
| Security | Y | Partial | UNKNOWN | UNKNOWN | PIN not configured | n/a | Y | PIN off | **UNKNOWN** |
| Actions | Y | Partial | UNKNOWN | UNKNOWN | UNKNOWN | log visible | Y | — | **UNKNOWN** |

\*Repair navigates to the same `#workstation` Mission Control surface (wrong destination for Repair).

**CERTIFIED FUNCTIONAL requires every column to pass. None do.**

---

# 24. Master capability matrix

| Capability | Room | Owner workflow | End-to-end result | Persistence | Performance | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Open Living Room | Chat | Front Door / hash `#chat` | Hearth loads; starter chips | n/a | ready 18ms | walk | **UNKNOWN** (send/persist untested) |
| Fly catalog browse | Fly Tying | Enter Room | 271 patterns; index ready | n/a | ready 39ms | walk | Partial |
| Fly search Adams | Fly Tying | type Adams → Search | No result cards; leftover “Session: Adams dry fly olive · step 2” | n/a | ~2s | CDP search | **NOT FUNCTIONAL** |
| Health PHR load | Health | Enter Room | “Health failed to load” | n/a | ready 20ms | walk | **NOT FUNCTIONAL** |
| Mission health console | Mission | Enter Room | Console chrome present | n/a | `/api/mission-control/health` 1031–1816ms | fetch spy | **NOT CERTIFIED** (slow + incomplete E2E) |
| Document library | Documents | Enter + OCR tool | Room opens; OCR UI present | untested | 930ms tool | OCR invoke | **UNKNOWN** |
| Add planner task | Planner | Input + Add | POST 200 **and** row created; first Add toasted “Add task failed”; Daily Focus still “0 tasks / No open tasks” | Yes after leave/return | focus GET 2513ms | fetch + leave/return | **NOT FUNCTIONAL** (owner outcome broken) |
| Delete planner task | Planner | Delete on AUDIT-ROOM | Removed from UI and `/api/planner` | Yes | <1s | delete test | **FUNCTIONAL** (this control) |
| Daily Focus accuracy | Planner | View Daily Focus | Lies: 0 tasks while 3–4 open tasks exist | n/a | 2.5s | UI vs API | **NOT FUNCTIONAL** |
| Calendar month | Calendar | Enter Room | August 2026 chrome | untested | month API 610ms | walk | **UNKNOWN** |
| Gallery generate/browse | Gallery | Enter Room | “ComfyUI settings unavailable” | n/a | — | walk | **NOT FUNCTIONAL** / dep |
| Federated search | Search | type planner → Run | Chrome only; results not proven | untested | 2.6s script | CDP | **UNKNOWN** |
| Coding propose/apply | Coding | Enter Room | Propose chrome present; E2E not run | untested | — | walk | **UNKNOWN** |
| Project list | Projects | Enter Room | Stuck “Loading…”; 7 controls | No | hang | walk | **NOT FUNCTIONAL** |
| Memory search | Memory | Search “Jeff” | Profile/preference hits visible | n/a | click search | snapshot | **FUNCTIONAL** (search display) |
| Memory profile/health | Memory | Enter Room | “Could not load profile”; health/sleep “Loading…”; Conflicts unavailable during rapid walk | n/a | abort-sensitive | walk | **NOT FUNCTIONAL** |
| Memory checkboxes | Memory | Brain learning etc. | `readonly` — cannot toggle | n/a | — | snapshot | **NOT FUNCTIONAL** |
| Voice cloud live | Voice | Enter Room | “Cloud live unavailable”; cheatsheet failed | n/a | — | walk | **DEPENDENCY BLOCKED** + functional gap |
| Repair as own Room | Repair | Front Door Repair | Title **Mission Control**; same `#workstation` | n/a | — | walk | **NOT FUNCTIONAL** |
| Integrity truth | Integrity | Enter native room | Score 85; “No deductions on record”; 3 buttons; QA planner leftovers shown | n/a | ready 10–27ms | native inspect | **NOT FUNCTIONAL** |
| Home foyer cards | Home | Enter + Retry | “Home unavailable Load failed”; Retry not found on later pass; Activity storm duplicated | n/a | dashboard 516–536ms | walk | **NOT FUNCTIONAL** |
| Automation home | Automation | Enter Room | Orchestration chrome present | untested | — | walk | **UNKNOWN** |
| Models/providers config | Providers | Enter Room | **2 buttons** only — incomplete Models surface | untested | — | walk | **NOT FUNCTIONAL** |
| HA lights/scenes | Home Automation | Enter Room | “Home failed”; Geeni bulbs “unavailable” | n/a | entities 364ms | walk | **NOT FUNCTIONAL** / dep |
| Presence camera | Presence | Enter Room | Controls present; `bodyRoom` stayed `home_automation` while hash `#presence` | untested | — | walk | **NOT FUNCTIONAL** (nav state) |
| Journal legend/stats | Journal | Enter Room | “Key legend unavailable”; “Journal stats unavailable”; Typewriter Loading… | n/a | — | walk | **NOT FUNCTIONAL** |
| Video settings/library | Video | Enter Room | “Could not load video settings”; library Loading… | n/a | presets 529ms | walk | **NOT FUNCTIONAL** |
| Audio studio | Audio | Enter Room | “Could not load audio status.”; **2 buttons** | n/a | — | walk | **NOT FUNCTIONAL** |
| Browser live session | Browser | Enter Room | “Failed Live session”; “Browser agent unavailable” | n/a | — | walk | **NOT FUNCTIONAL** / dep |
| Maker CAD | Maker | Enter Room | “CAD status: undefined” | n/a | — | walk | **NOT FUNCTIONAL** |
| Meme library | Meme | Enter Room | “Failed to load memes — aria-room-leave” | n/a | abort | walk | **NOT FUNCTIONAL** |
| Vision describe/OCR | Vision | Enter Room | Idle; `moondream:latest`; E2E not run | untested | — | walk | **UNKNOWN** |
| Connections graph | Connections | Enter Room | “Could not load Connections: aria-room-leave” | n/a | abort | walk | **NOT FUNCTIONAL** |
| Settings stores | Settings | Enter Room | Chrome present; earlier Stores 9/12 | untested | — | walk | **UNKNOWN** |
| Capabilities loader | Capabilities | Enter Room | Counts present | untested | — | walk | **UNKNOWN** |
| Integrations secrets | Integrations | Enter Room | Secret storage reachable | untested | — | walk | **UNKNOWN** |
| System audit run | Audit | Enter Room | “Loading audit…” / prior “Audit in progress…”; Run disabled; failed-login scan timed out | n/a | journalctl | walk | **NOT FUNCTIONAL** |
| PIN lock | Security | Enter Room | PIN lock off; setup not completed | n/a | — | walk | **UNKNOWN** / not configured |
| Action history | Actions | Enter Room | Log rows visible | log | — | walk | **UNKNOWN** |
| Front Door open | House | Open FD | Opens ~252ms; 34 rooms listed | n/a | 252ms | CDP | Partial (Tools tab not found as labeled) |
| OCR tool | Documents | invoke ocr | Lands `#documents`; OCR UI present | untested E2E | 930ms | CDP | **UNKNOWN** (open only) |

---

# 25. Master control matrix (tested + blocking)

Untested controls are **UNKNOWN** and therefore block Room certification. Counts are live `button,a,[role=button],input,select,textarea` on the visible surface after enter.

| Room | Control | Intended action | Tested | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| Front Door | Open | Show catalog | Y | Opened; 35 tiles | **FUNCTIONAL** |
| Front Door | Close | Dismiss | Y | Closed (`isOpen` false) | **FUNCTIONAL** |
| Front Door | Room tiles | goRoom | Y (all 34) | All hashes set; Repair wrong title | Mixed |
| Front Door | Tools wing | List/invoke tools | Partial | 14/18 tools listed; labeled Tools tab not found | **UNKNOWN** / incomplete |
| Planner | `#plannerTaskInput` | Enter task text | Y | Value set | **FUNCTIONAL** |
| Planner | `#plannerAddTaskBtn` | Create task | Y | First path toasted fail; POST 200 created row; Focus still 0 | **NOT FUNCTIONAL** |
| Planner | Delete AUDIT-ROOM | Remove task | Y | Removed UI+API | **FUNCTIONAL** |
| Planner | Daily Focus | Show open tasks | Y | “No open tasks” with 3–4 open | **NOT FUNCTIONAL** |
| Planner | HA Focus mode checkbox | Toggle | Observed | `readonly` | **NOT FUNCTIONAL** |
| Fly Tying | `#flytyingSearchInput` | Query | Y | Accepted “Adams” | Partial |
| Fly Tying | `#flytyingSearchBtn` | Search | Y | No result cards | **NOT FUNCTIONAL** |
| Memory | Search memories | Filter ACM | Y | Jeff hits shown | **FUNCTIONAL** |
| Memory | Brain learning + 5 more | Toggle prefs | Observed | `readonly` | **NOT FUNCTIONAL** |
| Memory | Keep A / Keep B (×20) | Resolve conflicts | N | Present after settle | **UNKNOWN** |
| Memory | Edit / Correct / Forget | Mutate memories | N | Present | **UNKNOWN** |
| Home | Retry | Reload foyer | Y | Button missing on retry pass | **NOT FUNCTIONAL** |
| Integrity | Refresh / Repair / ··· | Scan / repair | N | Only 3 controls | **UNKNOWN** / thin |
| Audio | (status surface) | Show studio | Y | Failed; 2 buttons | **NOT FUNCTIONAL** |
| Projects | Create / Import | Manage projects | N | Behind “Loading…” | **NOT FUNCTIONAL** |
| Repair | (own surface) | Guided Repair | Enter | Opens Mission Control | **NOT FUNCTIONAL** |
| All other visible controls | as labeled | as labeled | N | Inventoried by count only | **UNKNOWN** |

**Control census (visible after enter):** Chat 34, Fly Tying 235, Health 41, Mission 24, Documents 35, Planner 42, Calendar 35, Gallery 79, Search 49, Coding 26, Projects 7, Memory 38 (snapshot later showed 169 interactive including conflict/edit rows), Voice 18, Repair 24, Integrity 3, Home 16, Automation 22, Providers 2, Home Automation 44, Presence 7, Journal 45, Video 35, Audio 2, Browser 24, Maker 23, Meme 9, Vision 24, Connections 17, Settings 24, Capabilities 11, Integrations 10, Audit 20, Security 6, Actions 5.

Approximate total meaningful controls: **~1000+**.  
Tested to outcome: **~20**.  
Proven functional: **6** (FD open/close, planner input, planner delete, memory search display).  
Proven not functional: **12+**.  
Remainder: **UNKNOWN**.

---

# 26. Performance matrix

Enter times include a ~700ms settle wait in the walker; **readyMs** is time until a ≥200×200 surface existed.

| Room | Load Time (readyMs) | Usable Time | Primary Action Time | Navigation Time | Data Time | Tool Time | Major Bottleneck | Status |
| --- | ---: | --- | --- | ---: | --- | --- | --- | --- |
| Chat | 18 | chrome immediate | send untested | 721 | — | — | global SPA | systemic |
| Fly Tying | 39 | catalog chrome | search ~2s no cards | 743 | catalog local | — | search no results | functional fail |
| Health | 20 | error state | — | 722 | PHR fail | — | Health load | fail |
| Mission | 13 | chrome | health 1.0–1.8s | 714 | `/api/mission-control/health` | — | health API | slow dep |
| Documents | 16 | chrome | OCR open 930ms | 730 | — | 930ms | — | unknown |
| Planner | 16 | Focus stale | Add 55ms API / Focus 2513ms | 719 | `/api/planner` 328ms; `/api/planner/focus` **2513ms** | — | focus API + honesty | fail |
| Calendar | 15 | month chrome | — | 716 | `/api/calendar/month` 610ms | — | calendar API | unknown |
| Gallery | 14 | ComfyUI error | — | 719 | — | — | ComfyUI | fail |
| Search | 18 | chrome | run ~2.6s unproven | 726 | — | — | — | unknown |
| Coding | 14 | chrome | — | 723 | — | — | — | unknown |
| Projects | 18 | never left Loading… | — | 720 | hang | — | projects API/UI | fail |
| Memory | 17 | mixed Loading… | Jeff search worked | 721 | abort-sensitive | — | room-leave abort | fail |
| Voice | 10 | error banners | — | 711 | cloud-live 517ms | — | cloud live | fail |
| Repair | 11 | wrong surface | — | 712 | same as Mission | — | shared view | fail |
| Integrity | 10–27 | Score 85 thin | — | 711–828 | `/api/integrity/home` 784ms | — | incomplete truth | fail |
| Home | 9 | Load failed | Retry missing | 712 | `/api/dashboard/home` 516–536ms **duplicated** | — | dashboard + activity | fail |
| Automation | 10 | chrome | — | 711 | — | — | — | unknown |
| Providers | 9 | 2 buttons | — | 710 | — | — | incomplete surface | fail |
| Home Automation | 21 | Home failed | — | 723 | HA entities 364ms | — | HA status | fail |
| Presence | 8 | chrome | — | 709 | gestures 482ms | — | nav leak | fail |
| Journal | 10 | legend/stats fail | — | 711 | — | — | journal APIs | fail |
| Video | 8 | settings fail | — | 709 | presets 529ms | — | video settings | fail |
| Audio | 6 | total fail | — | 710 | status fail | — | audio status | fail |
| Browser | 10 | agent fail | — | 712 | — | — | Playwright | fail |
| Maker | 25 | CAD undefined | — | 726 | — | — | CAD status | fail |
| Meme | 9 | abort error | — | 710 | — | — | aria-room-leave | fail |
| Vision | 10 | idle chrome | — | 712 | — | — | — | unknown |
| Connections | 7 | abort error | — | 709 | — | — | aria-room-leave | fail |
| Settings | 18 | chrome | — | 721 | — | — | — | unknown |
| Capabilities | 10 | chrome | — | 712 | — | — | — | unknown |
| Integrations | 10 | chrome | — | 712 | — | — | — | unknown |
| Audit | 17 | Loading audit… | — | 719 | journalctl timeout | — | audit phases | fail |
| Security | 11 | PIN off | — | 712 | tools/status 531ms | — | — | unknown |
| Actions | 9 | log visible | — | 711 | — | — | — | unknown |
| Front Door | — | 252ms open | — | — | — | — | catalog render | ok-ish |
| Idle (8s on Planner) | — | 2 requests | — | — | wakeword + editor | — | not a poll storm **while idle** | — |

**Where timing is not meaningful:** Rooms that never become usable (Audio, Projects, Home fail, Health fail) have no honest “primary action time.” Integrity/Repair “primary action” was not executed (would mutate production integrity / repair).

**Range of Room readyMs:** 6–39 ms.  
**Average readyMs (34 Rooms):** ~14 ms.  
**Average enterMs with 700ms settle:** ~718 ms.

Jeff’s “the whole app is very slow” is **not** explained by Room mount. See §16–18.

---

# 27. Dependency map

```
Room
 └─ Capability
     └─ Dependency → live state → owner-visible result

Health → PHR / health API → FAILED → “Health failed to load”
Home → /api/dashboard/home (×2) 516–536ms → FAILED → “Home unavailable Load failed”
Planner → /api/planner 200 55–328ms → OK (data)
Planner → /api/planner/focus 2513ms → WRONG → “0 tasks” with open tasks
Mission/Repair → /api/mission-control/health 1031–1816ms → SLOW → console usable-late
Integrity → /api/integrity/home 784ms → Score 85, no deductions listed → dishonest/incomplete
Gallery/Video → ComfyUI settings → UNAVAILABLE → settings banners
Voice → /api/voice/cloud-live/status 517ms → UNAVAILABLE → “Cloud live unavailable”
Browser → Playwright agent → UNAVAILABLE → “Failed Live session”
Home Automation → HA + /api/homeassistant/entities 364ms → “Home failed”; bulbs unavailable
Audio → audio status API → FAILED → empty studio
Journal → key legend / stats APIs → FAILED
Projects → projects store/API → HUNG Loading…
Meme/Connections/Memory slices → AriaNet abort (`aria-room-leave`) → owner-visible failure
Audit → journalctl → TIMEOUT on failed-login scan
Memory → ACM → mixed (search works; profile/health/conflicts fail under abort)
Activity Center → /api/activity/inbox 376ms + /api/activity/publish ×4 → 183 failures → storm
Global → /api/resources 1097ms, /api/environment 671–827ms → shared latency
Vision → Ollama moondream:latest → PRESENT (E2E untested)
Documents/OCR → documents + OCR sheet → OPENED (E2E untested)
Fly Tying → local catalog 271 patterns → PRESENT; search results UI missing
Security/PIN → JARVIS_PIN_LOCK not set → not configured (not a fail of lock-when-on)
```

Shared dependencies affecting many Rooms: Activity publish/inbox, Mission Control health, AriaNet room-leave abort, dashboard home, environment/resources, Integrity score, ComfyUI, Home Assistant, Playwright, Ollama.

---

# 28. Defect register

### Systemic

| ID | Symptom | Rooms | Likely layer | Severity | Evidence |
| --- | --- | --- | --- | --- | --- |
| SYS-F01 | `aria-room-leave` / AbortError shown as owner errors instead of silent cancel | Meme, Connections, Memory, others on rapid enter | `AriaNet` + product catch blocks that still render the abort string | P0 | “Failed to load memes — aria-room-leave”; “Could not load Connections: aria-room-leave” |
| SYS-F02 | Activity Center failure storm | All | shared publish on every failed/partial load | P0 | 199 unread / 183 failures / 15 warnings; duplicate “Mission Control · critical health” |
| SYS-F03 | Repair is not a Room — it is Mission Control | Repair | registry `viewId: workstation` + furnish | P0 | Title “Mission Control”; hash `#workstation` |
| SYS-F04 | One SPA mounts the entire house | All | `index.html` + 151 scripts + 49 dialogs | P0 | 6900 DOM nodes always present |
| SYS-F05 | Room-enter treated as Room-functional in prior cert | All | certification process | P0 | Phase 6.4 “Verified operational (reachable)”; soak script |
| SYS-F06 | Production QA leftovers | Planner, Integrity, Memory | test isolation failure | P1 | `ARIA-REPAIR-E2E-PLAN-*`, `ARIA-FINAL-PLAN-*`; namespace `oc-cert-project-596282` |
| SYS-F07 | Integrity catalog drift | Integrity | native `#integrityRoom` vs old `#certificationView` | P1 | Phase 6.4 still maps Integrity → certification |
| SYS-F08 | Presence `bodyRoom` leak | Presence / Home Automation | house enter / dataset | P1 | hash `#presence`, `bodyRoom=home_automation` |

| ID | Symptom | Rooms | Likely layer | Severity | Evidence |
| --- | --- | --- | --- | --- | --- |
| SYS-P01 | Slow shared APIs | Mission, Planner Focus, Integrity, Home, Calendar | backend | P0 | health 1–1.8s; focus **2.5s**; resources 1.1s |
| SYS-P02 | Duplicate fetches | Home, Activity | frontend init | P1 | `/api/dashboard/home` ×2; `/api/activity/publish` ×4 |
| SYS-P03 | Global JS payload | All first paint | 151 scripts (gallery 796ms, memory_browser 784ms) | P0 | resource timing |
| SYS-P04 | Failure→publish→more work | All | Activity Center | P0 | 183 failures keep the house “busy” |
| SYS-P05 | Idle polling is *not* the main issue | Planner idle 8s | only 2 reqs | info | fetch spy |

### Isolated (selected)

| ID | Room | Control / capability | Symptom | Expected | Actual | Layer | Sev |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEF-PLN-01 | Planner | Add | Owner sees failure | Task appears; input clears; Focus updates | Toast “Add task failed”; input uncleared; Focus 0; **API did create the row** | UI honesty / Focus | P0 |
| DEF-PLN-02 | Planner | Daily Focus | Accurate top tasks | Open tasks listed | “No open tasks — add one below” with 3–4 open | `/api/planner/focus` | P0 |
| DEF-FLY-01 | Fly Tying | Search | Adams results | Result cards | 0 cards; Adams only in leftover session line | search UI | P0 |
| DEF-HEA-01 | Health | Load | PHR | “Health failed to load” | health API | P0 |
| DEF-HOM-01 | Home | Foyer | Cards | “Home unavailable Load failed” | dashboard | P0 |
| DEF-AUD-01 | Audio | Studio | Full surface | 2 buttons + status fail | audio status | P0 |
| DEF-PRJ-01 | Projects | List | Projects | Eternal “Loading…” | projects load | P0 |
| DEF-INT-01 | Integrity | Truth | Score + deductions | 85 with “No deductions on record” + QA tasks | integrity product | P0 |
| DEF-VOI-01 | Voice | Cloud live / cheatsheet | Available or honest N/A | “unavailable” / “Could not load cheatsheet” | voice APIs | P1 |
| DEF-GAL-01 | Gallery | ComfyUI settings | Settings or honest block | “ComfyUI settings unavailable” | ComfyUI | P1 |
| DEF-BRW-01 | Browser | Live session | Agent or honest block | Failed / agent unavailable | Playwright | P1 |
| DEF-HA-01 | Home Automation | Status / lights | HA home | “Home failed”; bulbs unavailable | HA | P1 |
| DEF-JRN-01 | Journal | Legend / stats | Available | both unavailable; Typewriter Loading… | journal APIs | P1 |
| DEF-VID-01 | Video | Settings / library | Load | settings fail; library Loading… | video APIs | P1 |
| DEF-MAK-01 | Maker | CAD status | Real status | `undefined` | CAD probe | P1 |
| DEF-PRV-01 | Providers | Models surface | Full config | 2 buttons | furnish/init | P0 |
| DEF-ADT-01 | Audit | Run audit | Completes | Loading / in progress; Run disabled; journalctl timeout | audit engine | P1 |
| DEF-MEM-01 | Memory | Pref checkboxes | Toggleable | `readonly` | UI | P1 |
| DEF-MEM-02 | Memory | Profile/health | Load | Could not load / Loading… | ACM APIs + abort | P1 |

Reproduction for all Room-enter defects: Front Door → that Room on `http://127.0.0.1:8765/?workspace=1`. No repair performed.

---

# 21. Why previous Owner Residency certification disagrees

Previous seal: `docs/ARIA_PHASE7_OWNER_RESIDENCY_CERTIFICATION.md` (2026-08-08) — **27/27 Rooms**, Integrity 100, soak 153/451 laps 0 issues, signed “No known engineering reason Jeff should encounter a broken workflow.”

**That seal does not describe this product, and it did not test this audit’s standard.** Proof:

1. **Different inventory.** Residency certified **27** Rooms. Live registry now has **34**. Seven Rooms were never in that 27/27 set (including several that now fail: Video/Audio/Meme/Connections/Capabilities/Integrations/Audit-class surfaces depending on the cut).

2. **“Verified operational” meant reachable.** `docs/ARIA_PHASE6_4_FURNISH_INVENTORY.md` marks every surface “Verified operational” with parentheticals like “Add task surface”, “URL input”, “reachable”. That is **surface presence**, not E2E owner outcome. Planner “Add task surface” is exactly what still fails honesty/Focus today.

3. **Soaks did not drive the owner UI.** `scripts/aria_ui_soak.py` states: *“Does not drive a browser.”* Each lap: GET `/api/health`, `/api/live`, `/api/world-state`, `/api/homeassistant/status`, `/api/comfyui/settings`, `/api/memory/settings`, then GET `/{base}/#{view}`. The hash is **not sent to the server**. “View cycling” is fetching the same SPA shell. 153 laps / 0 issues = 153 rounds of **API 2xx**. That cannot detect “Health failed to load,” Focus lying, or Repair opening Mission Control.

4. **Credential/residency docs already admitted enter-only coverage.** `docs/ARIA_PHASE7_3_CREDENTIAL_REVALIDATION.md`: soak = “Room cycling — no credential completion”; Security = “hash OK — not PIN lifecycle”; journal export = **cancel only**. That gap was filed as “coverage,” then Phase 7.2 still signed the house complete.

5. **Evidence directory is gone.** `/tmp/aria-residency/` (`A50.json`, `PARITY58.json`, soak JSON, etc.) is not on disk. The seal cannot be re-examined. Historical evidence is the markdown claims plus the soak **script**, which still exists and proves the method.

6. **Integrity 100 vs 85.** Residency removed `qa_wf` and reported Score 100. Tonight Integrity is **85**, shows QA planner tasks, and says “No deductions on record.” Either scoring is lying, or contamination returned, or both. Previous “clean” is not the current state.

7. **PARITY58 was a spot-check list**, not every function of every Room. Coding dual-cycle was one of the few true E2E workflows. Fly “search Adams” was claimed in notes; tonight Adams search produces **no cards**.

8. **Certification criteria were weaker than tonight’s 18-point rule.** Room entered + hash correct + soak API 200 + a few hero workflows ≠ “every intended function.”

**Precise lesson:** Prior certification measured **shell reachability and infrastructure liveness**. This audit measures **owner outcome**. Those are different products of testing. The discrepancy is not mysterious and not “Jeff is wrong.”

---

# 29. Final numbers

| Item | Number |
| --- | ---: |
| Total Rooms | 34 |
| Rooms fully functional (CERTIFIED FUNCTIONAL) | **0** |
| Rooms NOT CERTIFIED — FUNCTIONAL DEFECT | 22 |
| Rooms NOT CERTIFIED — PERFORMANCE DEFECT (alone) | 0 |
| Rooms NOT CERTIFIED — DEPENDENCY BLOCKED (whole Room) | 0 |
| Rooms OWNER N/A | 0 |
| Rooms UNKNOWN | 12 |
| Total Tools | 18 |
| Tools fully E2E | 0 |
| Tools opened (OCR) | 1 (open only) |
| Capability rows in matrix | 42 |
| Capabilities fully functional | 2 (Front Door open/close; Memory search display; Planner delete) — **none of these certify a Room** |
| Capabilities not functional | 24 |
| Capabilities UNKNOWN | 16 |
| Meaningful controls (approx) | ~1000+ |
| Controls tested to outcome | ~20 |
| Controls functional | 6 |
| Controls not functional | 12+ |
| Controls UNKNOWN | remainder |
| Systemic functional defects | 8 |
| Systemic performance defects | 5 |
| Isolated defects (named) | 18 |
| Room readyMs average / range | ~14 ms / 6–39 ms |
| Shared API latency range | 364–2513 ms |
| Activity failures at start | 183 |

A Room with 19 working functions and 1 broken function is still **NOT CERTIFIED**. Several Rooms do not even reach “19 working.”

---

# 16–18 / 30. Architectural assessment

### A. Why are so many Rooms currently failing?

Because the house is one SPA that **enters** Rooms by showing a panel, while many panels depend on APIs that fail, abort, hang, or return data the UI does not render honestly. Failures are then published into Activity Center, which makes the next Room feel broken too. Several Rooms are incomplete migrations (Repair=Mission, Integrity native thin, Providers 2 buttons, Audio empty). This is the product Jeff is actually using, not the 2026-08-08 seal.

### B. Individual bugs or shared architecture?

**Both, dominated by shared architecture.**

Shared: AriaNet abort leakage (SYS-F01), Activity storm (SYS-F02), monolithic load (SYS-F04), shared slow APIs (SYS-P01), duplicate init fetches (SYS-P02), wrong Room identity (SYS-F03).

Isolated: Health PHR, Audio status, Projects hang, Fly search cards, Planner Focus lie, Maker CAD undefined, etc. Many “isolated” failures still share the abort/publish pattern.

### C. Why is Aria slow?

Not because `#flytyingView` takes 2 seconds to attach (it takes ~39ms). Because:

1. **First load** pulls ~151 scripts (gallery/memory hundreds of ms each) and ~6900 nodes / 49 dialogs.
2. **Backend** endpoints Jeff’s foyer/mission/planner depend on take 0.5–2.5s (`/api/planner/focus` 2513ms, mission health 1–1.8s, `/api/resources` 1097ms).
3. **Activity Center** is already holding ~183 failures; each Room enter can add more (`/api/activity/publish` repeated).
4. **Retries / aborted loads** surface as errors and extra work.
5. **Model inference** (when used) is separate and can be legitimately slow; that is not what this audit measured as Room mount.

Idle on Planner for 8s produced only 2 requests. The problem is **startup + shared APIs + failure storm**, not a 1Hz poll loop on that Room.

### D. Is the performance problem systemic?

**Yes.** SYS-P01–P04. No Room is uniquely “the slow Room.” The house is slow as a platform. Room-level **NOT CERTIFIED — PERFORMANCE DEFECT** is not used because the Rooms that fail already fail **functionally**; remaining UNKNOWN Rooms still inherit systemic latency and cannot be certified responsive as a product.

### E. Why did previous certification miss this?

See §21. It tested **reachability and API 2xx**, used a soak that **does not drive a browser**, certified 27 Rooms against a 34-Room house, treated “surface present” as operational, and signed completeness while later docs already recorded enter-only/cancel-only gaps. Evidence files were ephemeral (`/tmp/aria-residency` gone).

### F. What must change so this cannot happen again?

Process (do not implement in this phase):

1. **Binary Room certification = this document’s 18-point rule.** No “verified operational (reachable).”
2. **Owner UI only.** Soak/API 200 is infrastructure evidence, never Room evidence.
3. **Every intended control has a row** in the control matrix with pass/fail/blocked/N/A.
4. **Abort must be silent** when leaving a Room; never an owner-visible failure.
5. **Activity Center must not accumulate engineering failures** as Jeff’s unread work.
6. **Durable evidence** in-repo, not `/tmp`.
7. **Inventory from live registry**, not the last certification’s room count.
8. **Production isolation:** QA planner tasks and `oc-cert-*` namespaces must never land in the live workspace (already law; currently violated).

### G. Correct repair order (do not begin)

1. **Stop the failure amplifier:** AriaNet abort leakage + Activity publish of abort/init errors (SYS-F01, SYS-F02, SYS-P04).  
2. **Fix dishonest/wrong Rooms:** Repair identity (SYS-F03), Integrity score/deductions/QA leftovers (DEF-INT-01, SYS-F06), Planner Add/Focus (DEF-PLN-01/02).  
3. **Unblock empty/hung Rooms:** Audio, Projects, Health, Home, Providers surface, Home Automation status.  
4. **Dependency honesty:** ComfyUI, Playwright, cloud live, HA bulbs — either work or OWNER N/A / ENVIRONMENT-BLOCKED without fake chrome.  
5. **Then** Fly search results, Journal/Video/Maker/Audit remaining functions.  
6. **Then** systemic payload (SYS-P03) and slow APIs (SYS-P01) — measure again; do not optimize blindly.  
7. **Last** UNKNOWN Rooms: full control-by-control E2E until each is CERTIFIED FUNCTIONAL or still failed.

No optimizations or refactors during this audit. None were performed.

---

## Comparison table (residency vs tonight)

| Claim (2026-08-08) | Tonight |
| --- | --- |
| 27/27 Rooms certified | 34 Rooms; **0** certified |
| Integrity 100 | Integrity **85**; deductions empty; QA tasks present |
| Soak 153/451 laps, 0 issues | Soak script = API GETs + `/#hash` shell fetch; not owner UI |
| Fly search Adams | Search button runs; **0 result cards** |
| Planner Add task surface | POST creates row; UI can toast **failure**; Focus says 0 tasks |
| Audio remount 78 buttons | **2 buttons**; “Could not load audio status” |
| Home/Dashboard verified | “Home unavailable Load failed” |
| Repair verified (Guided Repair) | Repair **is** Mission Control |
| `/tmp/aria-residency` evidence | **Missing** |

---

## Method limits (honest)

- This audit did **not** click every one of ~1000 controls to completion. Those are UNKNOWN, which **forbids** CERTIFIED FUNCTIONAL.
- Chat send, Coding propose→apply, Gallery generate, HA scene run, Vision describe, Document ingest, Journal write, Calendar create, Automation dry-run were **not** completed as full owner workflows (several would mutate Jeff’s life data or take minutes of model time). They remain UNKNOWN or blocked by already-failed surfaces.
- Restart/recovery of the server was **not** re-run (prior session already refreshed PID 3255320); per-Room restart-during-operation is UNKNOWN.
- Voice/Jeff-speak and keyboard chords were inventoried from the shortcuts overlay, not fully exercised.
- No application code was changed. The audit planner task was created and then deleted through the owner Delete control.

Those limits do not soften the answer. They make CERTIFIED impossible. The observed failures already make **NO** unavoidable.

---

## FINAL ANSWER (exact)

**NO — every Room does not work completely and responsively.**

- **Failing Rooms (NOT CERTIFIED — FUNCTIONAL DEFECT):** Fly Tying, Health, Mission Control, Planner, Gallery, Projects, Memory, Voice, Repair, Integrity, Home, Providers, Home Automation, Presence, Journal, Video, Audio, Browser, Maker, Meme, Connections, Audit.
- **UNKNOWN Rooms (cannot certify):** Chat, Documents, Calendar, Search, Coding, Automation, Vision, Settings, Capabilities, Integrations, Security, Actions.
- **CERTIFIED FUNCTIONAL:** none.
- **Functions that fail:** listed in §24 and §28 (Health load, Home load, Audio status, Projects hang, Planner Add/Focus honesty, Fly search results, Repair destination, Integrity truth, plus abort-tainted loads).
- **Controls that fail:** Planner Add (owner-visible), Daily Focus, Fly Search, Home Retry, Memory preference checkboxes, Repair entry, Audio/Projects/Providers/Integrity thin or empty surfaces.
- **Dependencies that fail or block:** Health PHR, dashboard home, planner focus, ComfyUI, cloud live, Playwright, HA home/lights, audio status, journal legend/stats, video settings, CAD status, journalctl audit, Integrity scoring.
- **Performance:** systemic (SYS-P01–P04). Room mount is fast; the house is not.
- **Systemic causes:** SYS-F01–F08 and SYS-P01–P04.

Repair begins only when Jeff starts the repair phase. This file is the baseline.
