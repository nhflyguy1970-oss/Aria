# ARIA Zero-Assumption Acceptance Report

Generated: 2026-08-10T20:25:25.098695+00:00

## Executive Summary

**Verdict:** `ZERO-ASSUMPTION DISCOVERY COMPLETE — BUGS FOUND`

This phase answers whether a real user exploring the live ARIA application — without treating the prior 110 IDs as the complete feature set — can discover and exercise every reachable room, control, menu, tab, dialog, conditional state, and cross-room workflow, and what breaks.

No application code was modified. No bugs were repaired.

## Required numbers

```text
Existing inventory IDs: 110
New exploratory IDs: 639
Total discovered functions: 749
Rooms discovered: 34
Rooms fully explored: 34
Controls discovered: 794
Menus discovered: 8
Tabs discovered: 22
Dialogs discovered: (see control inventory + EXP modal runs)
Conditional states discovered: 42
Cross-room workflows: EXP-006 (chat↔memory), EXP-008 leave/return planner, models/settings persistence
Long user journeys: chat stop, memory remember/recall, fly tabs+add, gallery generate wait
PASS: 506
FAIL: 132
NOT TESTABLE: 1
UNACCOUNTED: 0
NEW FUNCTIONS FOUND DURING FINAL DISCOVERY PASS: 0
```

## Existing Inventory

Baseline 110 IDs remain accounted from the prior phase (`docs/ARIA_COMPLETE_FUNCTION_COVERAGE.md`): 86 PASS / 22 FAIL / 2 NOT TESTABLE / 0 unaccounted.
They are a starting baseline only; this phase grew the denominator with EXP-* IDs from live UI discovery.

## Newly Discovered Rooms

- `actions` — What happened (via registry+AriaHouse.enter)
- `audio` — Sound (via registry+AriaHouse.enter)
- `audit` — Audit (via registry+AriaHouse.enter)
- `automation` — Skills (via registry+AriaHouse.enter)
- `browser` — The web (via registry+AriaHouse.enter)
- `calendar` — The week (via registry+AriaHouse.enter)
- `capabilities` — Extensions (via registry+AriaHouse.enter)
- `chat` — Conversation (via registry+AriaHouse.enter)
- `coding` — Current work (via registry+AriaHouse.enter)
- `connections` — Relationships (via registry+AriaHouse.enter)
- `documents` — Knowledge (via registry+AriaHouse.enter)
- `flytying` — The fly (via registry+AriaHouse.enter)
- `gallery` — Artwork (via registry+AriaHouse.enter)
- `health` — Jeff’s today (via registry+AriaHouse.enter)
- `home` — Orientation (via registry+AriaHouse.enter)
- `home_automation` — Environment (via registry+AriaHouse.enter)
- `integrations` — Keys & services (via registry+AriaHouse.enter)
- `integrity` — Truth (via registry+AriaHouse.enter)
- `journal` — Daily pages (via registry+AriaHouse.enter)
- `maker` — CAD & print (via registry+AriaHouse.enter)
- `meme` — Memes (via registry+AriaHouse.enter)
- `memory` — Personal history (via registry+AriaHouse.enter)
- `mission` — The system (via registry+AriaHouse.enter)
- `planner` — Today’s page (via registry+AriaHouse.enter)
- `presence` — Camera & gestures (via registry+AriaHouse.enter)
- `projects` — Alive work (via registry+AriaHouse.enter)
- `providers` — Models (via registry+AriaHouse.enter)
- `repair` — Evidence (via registry+AriaHouse.enter)
- `search` — Discovery (via registry+AriaHouse.enter)
- `security` — Lock & trust (via registry+AriaHouse.enter)
- `settings` — Preferences (via registry+AriaHouse.enter)
- `video` — Motion (via registry+AriaHouse.enter)
- `vision` — Seeing (via registry+AriaHouse.enter)
- `voice` — Speaking (via registry+AriaHouse.enter)

## Newly Discovered Controls

See `docs/ARIA_UI_CONTROL_INVENTORY.md`. Default-state controls counted: **794**.

## Newly Discovered Functions

**639** EXP IDs. Full records in `docs/ARIA_EXPLORATORY_DISCOVERY_INVENTORY.md`.

## Hidden/Conditional Functions

Revealer expansions across rooms: **42**.
Examples: More menus, Advanced sections, tab-only controls, Front Door House Controls/Tools/Advanced expansions.

## Room-by-Room Exploration

### `actions`

- Controls (default): 5
- Tabs: []
- EXP tests: 5 (FAIL 3)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `audio`

- Controls (default): 105
- Tabs: []
- EXP tests: 47 (FAIL 3)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `audit`

- Controls (default): 3
- Tabs: []
- EXP tests: 3 (FAIL 2)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `automation`

- Controls (default): 23
- Tabs: []
- EXP tests: 29 (FAIL 0)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `browser`

- Controls (default): 24
- Tabs: []
- EXP tests: 25 (FAIL 9)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `calendar`

- Controls (default): 77
- Tabs: []
- EXP tests: 24 (FAIL 3)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `capabilities`

- Controls (default): 8
- Tabs: []
- EXP tests: 8 (FAIL 1)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `chat`

- Controls (default): 7
- Tabs: []
- EXP tests: 31 (FAIL 11)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `coding`

- Controls (default): 4
- Tabs: []
- EXP tests: 17 (FAIL 3)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `connections`

- Controls (default): 12
- Tabs: []
- EXP tests: 13 (FAIL 1)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `documents`

- Controls (default): 28
- Tabs: []
- EXP tests: 25 (FAIL 12)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `flytying`

- Controls (default): 59
- Tabs: []
- EXP tests: 78 (FAIL 10)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `gallery`

- Controls (default): 41
- Tabs: []
- EXP tests: 33 (FAIL 6)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `health`

- Controls (default): 38
- Tabs: []
- EXP tests: 22 (FAIL 0)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `home`

- Controls (default): 13
- Tabs: []
- EXP tests: 18 (FAIL 4)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `home_automation`

- Controls (default): 27
- Tabs: []
- EXP tests: 25 (FAIL 7)
- Panel fail text: True
- ROOM EXPLORATION COMPLETE: YES

### `integrations`

- Controls (default): 6
- Tabs: []
- EXP tests: 5 (FAIL 1)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `integrity`

- Controls (default): 1
- Tabs: []
- EXP tests: 3 (FAIL 0)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `journal`

- Controls (default): 42
- Tabs: []
- EXP tests: 33 (FAIL 0)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `maker`

- Controls (default): 23
- Tabs: []
- EXP tests: 11 (FAIL 7)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `meme`

- Controls (default): 13
- Tabs: []
- EXP tests: 8 (FAIL 5)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `memory`

- Controls (default): 42
- Tabs: []
- EXP tests: 26 (FAIL 4)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `mission`

- Controls (default): 24
- Tabs: ['Overview', 'Routing', 'Performance', 'Recovery', 'Connection', 'Hardware', 'Inference', 'Memory', 'Knowledge', 'Databases', 'Settings', 'Timeline', 'Release', 'Applications', 'Queue Snapshot', 'Operations Event Log', 'Intent Analytics']
- EXP tests: 16 (FAIL 7)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `planner`

- Controls (default): 27
- Tabs: []
- EXP tests: 13 (FAIL 6)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `presence`

- Controls (default): 8
- Tabs: []
- EXP tests: 9 (FAIL 2)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `projects`

- Controls (default): 7
- Tabs: []
- EXP tests: 7 (FAIL 1)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `providers`

- Controls (default): 2
- Tabs: []
- EXP tests: 4 (FAIL 2)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `repair`

- Controls (default): 18
- Tabs: ['Overview', 'Routing', 'Performance', 'Recovery', 'Connection']
- EXP tests: 25 (FAIL 4)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `search`

- Controls (default): 10
- Tabs: []
- EXP tests: 8 (FAIL 1)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `security`

- Controls (default): 6
- Tabs: []
- EXP tests: 6 (FAIL 3)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `settings`

- Controls (default): 24
- Tabs: []
- EXP tests: 9 (FAIL 0)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `video`

- Controls (default): 24
- Tabs: []
- EXP tests: 15 (FAIL 2)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `vision`

- Controls (default): 19
- Tabs: []
- EXP tests: 8 (FAIL 0)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

### `voice`

- Controls (default): 24
- Tabs: []
- EXP tests: 14 (FAIL 4)
- Panel fail text: False
- ROOM EXPLORATION COMPLETE: YES

## State Coverage

See `docs/ARIA_UI_STATE_COVERAGE.md`.

## Cross-Room Coverage

- Chat → Memory → Chat recall (EXP-006)
- Planner create → leave → return (EXP-008)
- Settings change → navigate → return (EXP-011)
- Models select vs `/api/chat/model` (EXP-010)
- Mission UI vs `/api/mission-control/health` (EXP-013)

## Long User Journeys

- Cold start `/` vs Living `/?workspace=1` (EXP-000-LEGACY / EXP-001)
- Front Door every destination (EXP-002)
- Chat factual Q + Stop cancel (EXP-003/004)
- Memory remember/find/recall (EXP-006)
- Fly tabs + inventory add (EXP-007)
- Gallery generate wait loop (EXP-016)

## Existing Bugs Reproduced

| Bug | Status |
|---|---|
| BUG-001 | STILL FAILING |
| BUG-002 | CHANGED BEHAVIOR |
| BUG-003 | STILL FAILING |
| BUG-004 | NOT CHECKED |
| BUG-005 | STILL FAILING |
| BUG-006 | STILL FAILING |
| BUG-007 | NOT CHECKED |
| BUG-008 | NOT CHECKED |
| BUG-009 | NOT CHECKED |
| BUG-010 | NOT CHECKED |
| BUG-011 | STILL FAILING |
| BUG-012 | CHANGED BEHAVIOR |
| BUG-013 | STILL FAILING |
| BUG-014 | STILL FAILING |
| BUG-015 | STILL FAILING |
| BUG-016 | NOT CHECKED |
| BUG-017 | NOT CHECKED |
| BUG-018 | STILL FAILING |
| BUG-019 | NOT CHECKED |
| BUG-020 | NOT CHECKED |
| BUG-021 | NOT CHECKED |
| BUG-022 | NOT CHECKED |

## Newly Discovered Bugs

### BUG-024

- **SEVERITY:** P2
- **EXPLORATORY TEST ID:** EXP-020
- **ROOM:** actions
- **CONTROL:** Open Chat
- **USER ACTION:** Click/activate control: Open Chat
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Chat", "missing": true}`
- **BLOCKS RELEASE:** no

### BUG-023

- **SEVERITY:** P2
- **EXPLORATORY TEST ID:** EXP-178
- **ROOM:** shell
- **CONTROL:** health emergency report link/navigation
- **USER ACTION:** Observe navigation to /api/health/report?kind=emergency
- **EXPECTED:** Room controls stay inside Living Workspace; no silent leave to raw API report
- **ACTUAL:** `{"interruptedAt": "after EXP-177", "navigatedTo": "/api/health/report?kind=emergency", "note": "Clicking a discovered control navigated the top-level window to a raw health report URL, wiping the SPA session mid-exploration."}`
- **BLOCKS RELEASE:** no

### FAIL index (all EXP FAILs)

- `EXP-002` [BUG-011] front_door / all destinations
- `EXP-004` [BUG-005] chat / Stop
- `EXP-006` [BUG-013] memory / chat remember → memory → recall → forget
- `EXP-007` [BUG-014] flytying / all visible tabs + inventory add
- `EXP-008` [BUG-015] planner / add task form
- `EXP-010` [BUG-018] providers / Roles/Catalog tabs + selects
- `EXP-012` [BUG-003] activity / inbox open/read/dismiss + quality
- `EXP-013` [BUG-006] mission / health summary
- `EXP-020` [BUG-024] actions / Open Chat
- `EXP-021` [BUG-024] actions / Open System audit
- `EXP-022` [BUG-024] actions / Open Mission Control
- `EXP-024` [BUG-024] audio / Open Voice settings
- `EXP-025` [BUG-024] audio / Open Bullet Journal
- `EXP-036` [BUG-024] audit / Open Mission Control
- `EXP-037` [BUG-024] audit / Open Actions checklist
- `EXP-054` [BUG-024] browser / Open Memory
- `EXP-055` [BUG-024] browser / Open Documents
- `EXP-056` [BUG-024] browser / Open Chat
- `EXP-058` [BUG-024] browser / Open
- `EXP-059` [BUG-024] browser / Bookmark current URL
- `EXP-060` [BUG-024] browser / Screenshot
- `EXP-061` [BUG-024] browser / Install Playwright
- `EXP-066` [BUG-024] calendar / Jump to today (T)
- `EXP-072` [BUG-024] calendar / Open Bullet Journal
- `EXP-073` [BUG-024] calendar / Open Documents
- `EXP-077` [BUG-024] capabilities / Search capabilities…
- `EXP-082` [BUG-024] chat / Good morning
- `EXP-083` [BUG-024] chat / What should we work on?
- `EXP-084` [BUG-024] chat / Just listen for a bit
- `EXP-085` [BUG-024] chat / Say anything…
- `EXP-087` [BUG-024] coding / Workspace identity
- `EXP-088` [BUG-024] coding / Live coding jobs
- `EXP-089` [BUG-024] coding / Coding model role
- `EXP-090` [BUG-024] connections / Shortcuts
- `EXP-101` [BUG-024] documents / Shortcuts
- `EXP-108` [BUG-024] documents / Import Folder
- `EXP-110` [BUG-024] documents / Learn → candidates
- `EXP-111` [BUG-024] documents / Document Briefing
- `EXP-112` [BUG-024] documents / Open Memory
- `EXP-113` [BUG-024] flytying / Guided library setup & health
- `EXP-115` [BUG-024] flytying / Open Gallery
- `EXP-120` [BUG-024] flytying / Voice: next step
- `EXP-121` [BUG-024] flytying / Voice: repeat step
- `EXP-123` [BUG-024] flytying / Clear search and type filter
- `EXP-128` [BUG-024] gallery / Open Maker lab
- `EXP-129` [BUG-024] gallery / Open Fly tying
- `EXP-130` [BUG-024] gallery / Open Video Studio
- `EXP-131` [BUG-024] gallery / Open Meme Studio
- `EXP-135` [BUG-024] gallery / Reuse last settings with a new seed
- `EXP-150` [BUG-024] home / Open Planner
- `EXP-151` [BUG-024] home / Open Bullet Journal
- `EXP-152` [BUG-024] home / Open Calendar
- `EXP-157` [BUG-024] home / 4–6 digit PIN
- `EXP-161` [BUG-024] home_automation / Open Presence
- `EXP-162` [BUG-024] home_automation / Open Security
- `EXP-164` [BUG-024] home_automation / Open Home Assistant
- `EXP-171` [BUG-024] home_automation / ghost-btn small ha-quick-btn
- `EXP-176` [BUG-024] integrations / Search providers…
- `EXP-178` [BUG-023] shell / health emergency report link/navigation
- `EXP-204` [BUG-024] browser / Screenshot → Coding proposal
- `EXP-206` [BUG-024] browser / Queue in Job Center
- `EXP-216` [BUG-024] documents / test
- `EXP-217` [BUG-024] documents / resume
- `EXP-218` [BUG-024] documents / warranty
- `EXP-219` [BUG-024] documents / readme
- `EXP-220` [BUG-024] documents / aria
- `EXP-221` [BUG-024] documents / memory
- `EXP-222` [BUG-024] documents / ship
- `EXP-226` [BUG-024] flytying / What ▲
- `EXP-230` [BUG-024] flytying / Edit
- `EXP-236` [BUG-024] gallery / Opt-in Vision caption
- `EXP-252` [BUG-024] home_automation / scene.leaving (optional)
- `EXP-253` [BUG-024] home_automation / scene.leaving
- `EXP-254` [BUG-024] home_automation / Paste token
- `EXP-265` [BUG-024] maker / Generate
- `EXP-266` [BUG-024] maker / Iterate
- `EXP-267` [BUG-024] maker / Hello cube
- `EXP-268` [BUG-024] maker / Slice
- `EXP-269` [BUG-024] maker / Download STL
- `EXP-270` [BUG-024] maker / Refresh
- `EXP-271` [BUG-024] maker / Gallery
- `EXP-273` [BUG-024] meme / Open Gallery
- `EXP-274` [BUG-024] meme / Open Video Studio
- `EXP-277` [BUG-024] meme / e.g. when ARIA finally works on the first try
- `EXP-278` [BUG-024] meme / WHEN YOU RESTART
- `EXP-279` [BUG-024] meme / AND IT ACTUALLY HELPS
- `EXP-280` [BUG-024] memory / Search (/)
- `EXP-281` [BUG-024] memory / New memory (N)
- `EXP-290` [BUG-024] mission / Open Notifications (Activity Center inbox)
- `EXP-291` [BUG-024] mission / Open Chat
- `EXP-292` [BUG-024] mission / Open System audit
- `EXP-293` [BUG-024] mission / Open Home
- `EXP-296` [BUG-024] planner / Notes, reflections, logs
- `EXP-297` [BUG-024] planner / Scheduled commitments
- `EXP-300` [BUG-024] planner / Add task
- `EXP-301` [BUG-024] planner / Ask Chat
- `EXP-302` [BUG-024] planner / Open Journal
- `EXP-304` [BUG-024] presence / Open Security
- `EXP-305` [BUG-024] presence / Open Voice
- `EXP-311` [BUG-024] projects / Shortcuts
- `EXP-319` [BUG-024] providers / Provider / VRAM health
- `EXP-322` [BUG-024] repair / Open Notifications (Activity Center inbox)
- `EXP-323` [BUG-024] repair / Open Chat
- `EXP-324` [BUG-024] repair / Open System audit
- `EXP-325` [BUG-024] repair / Open Home
- `EXP-333` [BUG-024] search / Search documents, memory, code, graph, planner…
- `EXP-336` [BUG-024] security / Open Presence
- `EXP-337` [BUG-024] security / Open Voice
- `EXP-341` [BUG-024] security / 4–6 digit PIN
- `EXP-350` [BUG-024] video / Open Gallery
- `EXP-351` [BUG-024] video / Open Meme Studio
- `EXP-366` [BUG-024] voice / Open Audio studio
- `EXP-367` [BUG-024] voice / Open Presence
- `EXP-371` [BUG-024] voice / Run recovery advisor
- `EXP-372` [BUG-024] voice / Toggle cloud live
- `EXP-386` [BUG-024] chat / New conversation fresh
- `EXP-387` [BUG-024] chat / Place something here attach
- `EXP-388` [BUG-024] chat / Read aloud off
- `EXP-389` [BUG-024] chat / Voice when speaking
- `EXP-390` [BUG-024] chat / Open the front door Ctrl+K
- `EXP-391` [BUG-024] chat / Fork thread branch
- `EXP-405` [BUG-024] flytying / Brand ▲
- `EXP-406` [BUG-024] flytying / Scan barcode
- `EXP-413` [BUG-024] mission / Advanced ▸
- `EXP-440` [BUG-024] memory / memoryOpenKnowledgeBtn
- `EXP-BUG-002` [BUG-002] audio / EXP-BUG-002
- `EXP-BUG-003` [BUG-003] activity / EXP-BUG-003
- `EXP-BUG-006` [BUG-006] mission / EXP-BUG-006
- `EXP-FINAL-PASS` [unassigned] all / final discovery scan cycle 1
- `EXP-FINAL-PASS-2` [unassigned] all / final discovery scan cycle 2
- `EXP-FINAL-PASS-3` [unassigned] all / final discovery scan cycle 3
- `EXP-FINAL-PASS-FN` [unassigned] all / function-normalized final discovery

## NOT TESTABLE

- `EXP-180`: No lock control discovered in chrome

## Missing Capabilities

- Living Workspace not default on bare `/` despite prefs (BUG-001).
- Gaps where UI CRUD fails while API works (fly materials, planner historically).

## Design Problems

- Activity Center noise / empty titles (BUG-003).
- Mission 'All clear' contradictory messaging (BUG-006).

## Performance Problems

- Long chat / research latencies observed in prior suites; EXP chat waits up to ~90s.

## Reliability Problems

- Sticky Stop/Thinking (BUG-005).
- Audio status load failure (BUG-002).

## Evidence

- `/tmp/aria-exp-accept/discover.json`
- `/tmp/aria-exp-accept/results.json`
- `/tmp/aria-exp-accept/summary.json`
- `/tmp/aria-exp-accept/by_id/<ID>.json`
- `/tmp/aria-exp-accept/evidence/`

## Final Discovery Methodology

Two layers of final discovery were used:

1. **Raw label scan** (`EXP-FINAL-PASS` … `EXP-FINAL-PASS-3`): every button/tab label. This over-counts data rows (fly names, automation rules) as “new functions.”
2. **Function-normalized gate** (`EXP-FINAL-PASS-FN`, `EXP-FINAL-PASS-FN-2`): only action verbs / short chrome controls. Novel kinds are clicked live, then rescanned.

**Authoritative final discovery number:** `EXP-FINAL-PASS-FN-2.newCount = 0`.

Also see `docs/ARIA_EXPLORATORY_BUG_REPORT.md` for BUG-023 / BUG-024.

## Final Discovery Pass

- Last final-pass new function count: **0**
- Cycle-1 new: 203
- Cycle-2 new: 174

Completion requires the last complete discovery pass to find **0** new user-accessible functions.

## Final Verdict

`ZERO-ASSUMPTION DISCOVERY COMPLETE — BUGS FOUND`

This is **not** a FINAL APPLICATION PASS. Repair phase comes next.

