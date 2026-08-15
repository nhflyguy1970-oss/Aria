# ARIA Exploratory Discovery Inventory

Generated: 2026-08-10T20:25:25.092645+00:00

Includes the prior 110 function IDs (baseline) plus every newly discovered EXP-* function.
Authority: the live application UI, not the prior inventory denominator.

## Summary counts

- Existing inventory IDs: **110**
- New exploratory IDs: **639**
- Total discovered functions in this phase artifacts: **749** (baseline + EXP)
- PASS (EXP suite): **506**
- FAIL (EXP suite): **132**
- NOT TESTABLE (EXP suite): **1**
- UNACCOUNTED (EXP suite): **0**

## Baseline 110 (from prior function acceptance)

See `docs/ARIA_COMPLETE_FUNCTION_COVERAGE.md` and `/tmp/aria-fn-accept/`.
Prior graded snapshot available: **True** (110 keys).

| ID | Status |
|---|---|
| `ACT-001` | PASS |
| `ACTC-001` | PASS |
| `ACTC-002` | PASS |
| `ACTC-003` | FAIL |
| `AUDIO-001` | PASS |
| `AUDIO-002` | FAIL |
| `AUDIT-001` | PASS |
| `AUTO-001` | PASS |
| `AUTO-002` | PASS |
| `BROWSER-001` | PASS |
| `CAL-001` | PASS |
| `CAL-002` | PASS |
| `CAPS-001` | PASS |
| `CHAT-001` | FAIL |
| `CHAT-002` | FAIL |
| `CHAT-003` | PASS |
| `CHAT-004` | FAIL |
| `CHAT-005` | PASS |
| `CHAT-006` | PASS |
| `CHAT-007` | PASS |
| `CHAT-008` | FAIL |
| `CHAT-009` | PASS |
| `CHAT-010` | FAIL |
| `CHAT-011` | PASS |
| `CHAT-012` | PASS |
| `CHAT-013` | FAIL |
| `CHAT-014` | PASS |
| `CMD-001` | PASS |
| `CODING-001` | PASS |
| `CODING-002` | NOT TESTABLE |
| `CONN-001` | PASS |
| `DOCS-001` | PASS |
| `DOCS-002` | FAIL |
| `DOCS-003` | PASS |
| `FLY-001` | PASS |
| `FLY-002` | PASS |
| `FLY-003` | PASS |
| `FLY-004` | FAIL |
| `FLY-005` | PASS |
| `FLY-006` | FAIL |
| `FLY-007` | PASS |
| `FLY-008` | PASS |
| `FLY-009` | PASS |
| `GALLERY-001` | PASS |
| `GALLERY-002` | PASS |
| `HA-001` | FAIL |
| `HA-002` | NOT TESTABLE |
| `HA-003` | PASS |
| `HEALTH-001` | PASS |
| `HEALTH-002` | PASS |
| `HEALTH-003` | PASS |
| `HEALTH-004` | FAIL |
| `HOME-001` | PASS |
| `INTEG-001` | PASS |
| `INTEGRITY-001` | PASS |
| `JOBS-001` | PASS |
| `JOURNAL-001` | PASS |
| `JOURNAL-002` | FAIL |
| `JOURNAL-003` | PASS |
| `LEGACY-001` | PASS |
| `LOCK-001` | PASS |
| `MAKER-001` | PASS |
| `MEME-001` | PASS |
| `MEMORY-001` | PASS |
| `MEMORY-002` | PASS |
| `MEMORY-003` | PASS |
| `MEMORY-004` | PASS |
| `MEMORY-005` | PASS |
| `MEMORY-006` | PASS |
| `MEMORY-007` | PASS |
| `MEMORY-008` | PASS |
| `MISSION-001` | PASS |
| `MODELS-001` | PASS |
| `MODELS-002` | FAIL |
| `NAV-001` | PASS |
| `NAV-002` | PASS |
| `NAV-003` | FAIL |
| `NAV-004` | PASS |
| `NAV-005` | PASS |
| `NAV-006` | PASS |
| `NAV-007` | PASS |
| `NAV-008` | PASS |
| `NAV-009` | PASS |
| `ONBOARD-001` | PASS |
| `ONBOARD-002` | FAIL |
| `PLAN-001` | PASS |
| `PLAN-002` | FAIL |
| `PLAN-003` | PASS |
| `PLAN-004` | PASS |
| `PRES-001` | PASS |
| `PROJ-001` | PASS |
| `PROJ-002` | PASS |
| `PROJ-003` | PASS |
| `REPAIR-001` | PASS |
| `SEARCH-001` | PASS |
| `SEARCH-002` | PASS |
| `SEARCH-003` | PASS |
| `SEC-001` | PASS |
| `SETTINGS-001` | PASS |
| `SETTINGS-002` | FAIL |
| `VIDEO-001` | PASS |
| `VISION-001` | PASS |
| `VOICE-001` | PASS |
| `XJ-001` | FAIL |
| `XJ-002` | FAIL |
| `XJ-003` | PASS |
| `XJ-004` | PASS |
| `XJ-005` | PASS |
| `XJ-006` | PASS |
| `XJ-007` | FAIL |

## Exploratory IDs (this phase)

### EXP-000-LEGACY

- **ROOM:** shell
- **CONTROL:** bare / vs ?workspace=1
- **HOW DISCOVERED:** cold-start
- **STATE:** DEFAULT
- **USER ACTION:** Open / then /?workspace=1
- **EXPECTED:** Legacy then Living
- **ACTUAL:** `{"legacyLiving": false, "prefsLiving": true, "livingSession": true}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-000-LEGACY.json`
- **BUG:** BUG-001
- **START TIME:** None
- **END TIME:** None
- **DURATION:** None ms

### EXP-001

- **ROOM:** shell
- **CONTROL:** entry /
- **HOW DISCOVERED:** cold-start
- **STATE:** DEFAULT
- **USER ACTION:** Inspect living class on current living URL then note legacy evidence
- **EXPECTED:** Living Workspace when ?workspace=1; legacy on /
- **ACTUAL:** `{"href": "http://127.0.0.1:8765/?workspace=1#actions", "living": true}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-001.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:27:24.922Z
- **END TIME:** 2026-08-10T19:27:24.922Z
- **DURATION:** 0 ms

### EXP-002

- **ROOM:** front_door
- **CONTROL:** all destinations
- **HOW DISCOVERED:** Front Door open
- **STATE:** MODAL
- **USER ACTION:** Open Front Door and enter each room destination
- **EXPECTED:** Each destination opens matching room; door closes
- **ACTUAL:** `{"failClose": 33, "failEnter": 0, "sample": [{"cur": "chat", "label": "\u25c7ChatSit down. Talk.\u25cb", "open": true}, {"cur": "chat", "label": "\u223fFly TyingThe bench by the water\u25cb", "open": true}, {"cur": "chat", "label": "\u2661HealthHow you\u2019re doing today\u25cb", "open": true}, {"cur": "chat", "label": "\u25ceMission ControlHow the house is breathing\u25cb", "open": true}, {"cur": "chat", "label": "\u2630DocumentsYour private library\u25cb", "open": true}, {"cur": "chat", "label`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-002.json`
- **BUG:** BUG-011
- **START TIME:** 2026-08-10T19:27:24.922Z
- **END TIME:** 2026-08-10T19:28:03.706Z
- **DURATION:** 38784 ms

### EXP-003

- **ROOM:** chat
- **CONTROL:** composer Send
- **HOW DISCOVERED:** Living Room default
- **STATE:** DEFAULT
- **USER ACTION:** Ask a clear factual question and judge answer relevance
- **EXPECTED:** Relevant answer to the question asked
- **ACTUAL:** `{"has12": true, "tail": "Aria is here\nListening quietly\nA\n\nYou\nWhat is 7 plus 5? Reply with only the number.\nA\n12"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-003.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:28:03.706Z
- **END TIME:** 2026-08-10T19:29:34.239Z
- **DURATION:** 90533 ms

### EXP-004

- **ROOM:** chat
- **CONTROL:** Stop
- **HOW DISCOVERED:** during generation
- **STATE:** LOADING
- **USER ACTION:** Start long reply then Stop; verify stable state
- **EXPECTED:** Stop clears; no stuck Thinking/Stopping/Stop button
- **ACTUAL:** `{"sticky": false, "still": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-004.json`
- **BUG:** BUG-005
- **START TIME:** 2026-08-10T19:29:34.239Z
- **END TIME:** 2026-08-10T19:29:38.046Z
- **DURATION:** 3807 ms

### EXP-005

- **ROOM:** chat
- **CONTROL:** More menu
- **HOW DISCOVERED:** Living chrome More button
- **STATE:** MENU
- **USER ACTION:** Open More menu and list items
- **EXPECTED:** Menu opens with actionable items
- **ACTUAL:** `{"items": [], "opened": true}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-005.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:29:38.047Z
- **END TIME:** 2026-08-10T19:29:38.853Z
- **DURATION:** 806 ms

### EXP-006

- **ROOM:** memory
- **CONTROL:** chat remember → memory → recall → forget
- **HOW DISCOVERED:** cross-room workflow
- **STATE:** DEFAULT
- **USER ACTION:** Store unique fact via chat, find in Memory, recall, forget if possible
- **EXPECTED:** Fact stored, visible, recallable, forgettable
- **ACTUAL:** `{"chatTail": "ou\nPlease remember exactly: my exploratory acceptance code is ARIA-EXP-MEM-1786390178854\nA\nMEMORY\nStored via ACM:\n\nexactly: my exploratory acceptance code is ARIA-EXP-MEM-1786390178854\nYou\nWhat is my exploratory acceptance code?\nA\nexactly: my exploratory acceptance code is ARIA-EXP-MEM-1786390178854", "inMemory": false, "marker": "ARIA-EXP-MEM-1786390178854", "recalled": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-006.json`
- **BUG:** BUG-013
- **START TIME:** 2026-08-10T19:29:38.854Z
- **END TIME:** 2026-08-10T19:31:43.730Z
- **DURATION:** 124876 ms

### EXP-007

- **ROOM:** flytying
- **CONTROL:** all visible tabs + inventory add
- **HOW DISCOVERED:** room tabs + inventory
- **STATE:** TAB/EDITING
- **USER ACTION:** Open each fly tab; attempt inventory add ARIA-EXP-FLY-*
- **EXPECTED:** Tabs switch; material add via UI succeeds
- **ACTUAL:** `{"add": true, "found": false, "inputCount": 60, "name": "ARIA-EXP-FLY-1786390311357", "tabLabels": ["Gallery", "Open inventory", "Start session", "Search fly patterns", "Favorite pattern", "Unfavorite pattern", "Unfavorite pattern", "Unfavorite pattern", "Unfavorite pattern", "Unfavorite pattern", "Favorite pattern", "Favorite pattern", "Favorite pattern", "Favorite pattern", "Favorite pattern"]}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-007.json`
- **BUG:** BUG-014
- **START TIME:** 2026-08-10T19:31:43.730Z
- **END TIME:** 2026-08-10T19:31:52.859Z
- **DURATION:** 9129 ms

### EXP-008

- **ROOM:** planner
- **CONTROL:** add task form
- **HOW DISCOVERED:** planner default
- **STATE:** EDITING
- **USER ACTION:** Create task ARIA-EXP-PLAN-* via UI
- **EXPECTED:** Task appears in planner UI and persists leave/return
- **ACTUAL:** `{"found": false, "hasInput": true, "name": "ARIA-EXP-PLAN-1786390313861"}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-008.json`
- **BUG:** BUG-015
- **START TIME:** 2026-08-10T19:31:52.859Z
- **END TIME:** 2026-08-10T19:32:00.834Z
- **DURATION:** 7975 ms

### EXP-009

- **ROOM:** documents
- **CONTROL:** text search vs file input
- **HOW DISCOVERED:** documents panel inputs
- **STATE:** SEARCH
- **USER ACTION:** Locate text search control and search 'proposal'
- **EXPECTED:** Text search works without touching file input
- **ACTUAL:** `{"err": null, "fileInputCount": 1, "preview": "Aria \u00b7 Private library Listening quietly Documents Personal document intelligence \u2014 local files, grounded search, Memory candidates. Not Drive, SharePoint, or Notion. Documents = library \u00b7 Knowledge = briefs \u00b7 Connections = graph \u00b7 Memory = autobiography \u00b7 Search index = retrieval ? Drop files or Up", "searchType": "search", "textInputCount": 2}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-009.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:00.834Z
- **END TIME:** 2026-08-10T19:32:03.338Z
- **DURATION:** 2504 ms

### EXP-010

- **ROOM:** providers
- **CONTROL:** Roles/Catalog tabs + selects
- **HOW DISCOVERED:** conditional after tab click
- **STATE:** TAB
- **USER ACTION:** Open Roles/Catalog/Providers tabs; change a select if present
- **EXPECTED:** Model configuration controls appear and can change selection
- **ACTUAL:** `{"before": {"chat_model": "", "default": "qwen2.5:7b"}, "changed": false, "selectCount": 0, "tabsClicked": ["Overview", "Roles", "Catalog", "Providers", "Recommend", "Downloads", "Setup"]}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-010.json`
- **BUG:** BUG-018
- **START TIME:** 2026-08-10T19:32:03.339Z
- **END TIME:** 2026-08-10T19:32:16.419Z
- **DURATION:** 13080 ms

### EXP-011

- **ROOM:** settings
- **CONTROL:** theme/density nested controls
- **HOW DISCOVERED:** settings tabs/sections
- **STATE:** EDITING
- **USER ACTION:** Open settings sections; toggle theme/atmosphere/density
- **EXPECTED:** Pref value changes and persists after navigate
- **ACTUAL:** `{"afterTheme": "light", "beforeTheme": "dark", "changed": true, "density": ["standard", "operator", "operator"], "interacted": 10, "midTheme": "light"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-011.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:16.420Z
- **END TIME:** 2026-08-10T19:32:20.789Z
- **DURATION:** 4369 ms

### EXP-012

- **ROOM:** activity
- **CONTROL:** inbox open/read/dismiss + quality
- **HOW DISCOVERED:** global chrome
- **STATE:** MODAL
- **USER ACTION:** Open notifications; inspect titles; dismiss one if possible
- **EXPECTED:** Readable titled events; dismiss works; not spam-dominated
- **ACTUAL:** `{"empty": 123, "loadFails": 10, "top": ["Calendar load failed", "", "", "Notification", "Could not save memory setting"], "total": 200}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-012.json`
- **BUG:** BUG-003
- **START TIME:** 2026-08-10T19:32:20.789Z
- **END TIME:** 2026-08-10T19:32:22.166Z
- **DURATION:** 1377 ms

### EXP-013

- **ROOM:** mission
- **CONTROL:** health summary
- **HOW DISCOVERED:** mission room
- **STATE:** DEFAULT
- **USER ACTION:** Open Mission Control; compare UI to /api/mission-control/health
- **EXPECTED:** No 'All clear' while overall degraded
- **ACTUAL:** `{"critical": ["All clear", "Long-run stability warning"], "overall": "degraded", "preview": "Aria \u00b7 Aerospace ops\nListening quietly\nMission Control\n\nInfrastructure health console \u2014 providers, runtime, hardware, recovery, routing, and performance. Not Job Center or Activity Center.\n\nRefresh\nOpen Job Center\nOpen Notifications\nChat\nAudit\nHome\nC"}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-013.json`
- **BUG:** BUG-006
- **START TIME:** 2026-08-10T19:32:22.166Z
- **END TIME:** 2026-08-10T19:32:37.957Z
- **DURATION:** 15791 ms

### EXP-014

- **ROOM:** audio
- **CONTROL:** status bar
- **HOW DISCOVERED:** audio default
- **STATE:** DEFAULT
- **USER ACTION:** Enter Audio; read status
- **EXPECTED:** Status loads (not Could not load)
- **ACTUAL:** `{"fail": false, "preview": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\n\u2713 Whisper (medium)\n\u2713 ffmpeg\n\u2713 Piper \u00b7 \u266b transformers\n\ud83d\udd0a alsa_output.pci-0000_05_00.0.iec958-stereo\n\ud83c\udfa4 Microphone \u00b7 100% \u2713\n\nRecord & transcribe\n\nChat mic uses browser speech-to-text. This tab uses faster-whisper locally.\n\n"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-014.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:37.957Z
- **END TIME:** 2026-08-10T19:32:39.462Z
- **DURATION:** 1505 ms

### EXP-015

- **ROOM:** home_automation
- **CONTROL:** status + entity search
- **HOW DISCOVERED:** HA room
- **STATE:** SEARCH
- **USER ACTION:** Enter HA; read status; search light
- **EXPECTED:** Connected/setup clear; search runs
- **ACTUAL:** `{"hardFail": false, "hasSearch": true, "preview": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control the room around you.\n\nSearch\nOpen HA\nStatus\n\nConnected \u00b7 http://127.0.0.1:8123\n\nFavorites\nPin devices from search\nScenes\nFocus mode\nRelax\nMovie mode\nWork mode\nSunlight\nRooms\nNo rooms"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-015.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:39.462Z
- **END TIME:** 2026-08-10T19:32:42.168Z
- **DURATION:** 2706 ms

### EXP-016

- **ROOM:** gallery
- **CONTROL:** generate
- **HOW DISCOVERED:** gallery generate button
- **STATE:** LOADING→SUCCESS/ERROR
- **USER ACTION:** Start image generation with ARIA-EXP marker prompt; wait for terminal state
- **EXPECTED:** Job progresses to complete/error without stuck Generating
- **ACTUAL:** `{"hasPrompt": true, "preview": "Aria \u00b7 Museum Listening quietly Gallery Local AI image product \u2014 generate, browse, organize, and edit stills. Video and Meme stay separate. Chat converses; Documents store knowledge. Refresh Job Center Models Maker Fly tying Video Meme Ctrl+Shift+G 9 images \u00b7 showing 9 Running\u2026 (5%) Generation Stays in Gallery \u2014 same shared Image Generation pipelin", "terminal": true}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-016.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:42.168Z
- **END TIME:** 2026-08-10T19:32:46.882Z
- **DURATION:** 4714 ms

### EXP-017

- **ROOM:** coding
- **CONTROL:** propose UI
- **HOW DISCOVERED:** coding home
- **STATE:** EDITING
- **USER ACTION:** Open propose flow; do not apply to jarvis tree
- **EXPECTED:** Propose UI available; Apply gated without sandbox
- **ACTUAL:** `{"applyPresent": false, "preview": "Aria \u00b7 Engineering studio\nListening quietly\nCoding\n\nPropose \u2192 Review \u2192 Apply \u2192 Undo \u2192 Verify. Projects identify workspaces; Job Center tracks execution; Models configures the coding model.\n\nRefresh\nProjects\nJob Center\nModels\nCtrl+Shift+C\nLoading\u2026", "propose": false}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-017.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:46.882Z
- **END TIME:** 2026-08-10T19:32:50.695Z
- **DURATION:** 3813 ms

### EXP-018

- **ROOM:** command_palette
- **CONTROL:** palette commands
- **HOW DISCOVERED:** Ctrl+K
- **STATE:** MODAL
- **USER ACTION:** Open palette; run a navigation command
- **EXPECTED:** Command executes and navigates
- **ACTUAL:** `{"clicked": true, "cur": "planner", "hasInput": true}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-018.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:50.696Z
- **END TIME:** 2026-08-10T19:32:52.677Z
- **DURATION:** 1981 ms

### EXP-019

- **ROOM:** actions
- **CONTROL:** Clear
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Clear
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Action history\nListening quietly\nAction history\nAll modules\nCoding\nHome Assistant\nDocuments\nImage\n Clear Chat Aud", "before": "Aria \u00b7 Action history\nListening quietly\nAction history\nAll modules\nCoding\nHome Assistant\nDocuments\nImage\n Clear Chat Aud", "crashed": false, "label": "Clear"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-019.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:52.680Z
- **END TIME:** 2026-08-10T19:32:54.286Z
- **DURATION:** 1606 ms

### EXP-020

- **ROOM:** actions
- **CONTROL:** Open Chat
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Chat
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Chat", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-020.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:32:54.287Z
- **END TIME:** 2026-08-10T19:32:55.189Z
- **DURATION:** 902 ms

### EXP-021

- **ROOM:** actions
- **CONTROL:** Open System audit
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open System audit
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open System audit", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-021.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:32:55.190Z
- **END TIME:** 2026-08-10T19:32:56.093Z
- **DURATION:** 903 ms

### EXP-022

- **ROOM:** actions
- **CONTROL:** Open Mission Control
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Mission Control
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Mission Control", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-022.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:32:56.094Z
- **END TIME:** 2026-08-10T19:32:56.997Z
- **DURATION:** 903 ms

### EXP-023

- **ROOM:** actions
- **CONTROL:** All modules Coding Home Assistant Documents Image
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: All modules Coding Home Assistant Documents Image
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Action history\nListening quietly\nAction history\nAll modules\nCoding\nHome Assistant\nDocuments\nImage\n Clear Chat Aud", "before": "Aria \u00b7 Action history\nListening quietly\nAction history\nAll modules\nCoding\nHome Assistant\nDocuments\nImage\n Clear Chat Aud", "crashed": false, "label": "All modules Coding Home Assistant Documents Image"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-023.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:32:56.997Z
- **END TIME:** 2026-08-10T19:32:58.603Z
- **DURATION:** 1606 ms

### EXP-024

- **ROOM:** audio
- **CONTROL:** Open Voice settings
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Voice settings
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Voice settings", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-024.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:32:58.603Z
- **END TIME:** 2026-08-10T19:32:59.510Z
- **DURATION:** 907 ms

### EXP-025

- **ROOM:** audio
- **CONTROL:** Open Bullet Journal
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Bullet Journal
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Bullet Journal", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-025.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:32:59.513Z
- **END TIME:** 2026-08-10T19:33:00.423Z
- **DURATION:** 910 ms

### EXP-026

- **ROOM:** audio
- **CONTROL:** Test mic (2s)
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Test mic (2s)
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\n\u2713 Whisper (medium)\n\u2713 ffmpeg\n\u2713 Piper \u00b7 \u266b transformers\n\ud83d\udd0a alsa_", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\n\u2713 Whisper (medium)\n\u2713 ffmpeg\n\u2713 Piper \u00b7 \u266b transformers\n\ud83d\udd0a alsa_", "crashed": false, "label": "Test mic (2s)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-026.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:00.424Z
- **END TIME:** 2026-08-10T19:33:02.033Z
- **DURATION:** 1609 ms

### EXP-027

- **ROOM:** audio
- **CONTROL:** Record only
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Record only
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\n\u2713 Whisper (medium)\n\u2713 ffmpeg\n\u2713 Piper \u00b7 \u266b transformers\n\ud83d\udd0a alsa_", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\n\u2713 Whisper (medium)\n\u2713 ffmpeg\n\u2713 Piper \u00b7 \u266b transformers\n\ud83d\udd0a alsa_", "crashed": false, "label": "Record only"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-027.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:02.033Z
- **END TIME:** 2026-08-10T19:33:03.640Z
- **DURATION:** 1607 ms

### EXP-028

- **ROOM:** audio
- **CONTROL:** Record + transcribe
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Record + transcribe
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Record + transcribe"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-028.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:03.640Z
- **END TIME:** 2026-08-10T19:33:05.248Z
- **DURATION:** 1608 ms

### EXP-029

- **ROOM:** audio
- **CONTROL:** Play on Sound Blaster
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Play on Sound Blaster
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Play on Sound Blaster"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-029.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:05.248Z
- **END TIME:** 2026-08-10T19:33:06.855Z
- **DURATION:** 1607 ms

### EXP-030

- **ROOM:** audio
- **CONTROL:** Copy
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Copy
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Copy"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-030.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:06.856Z
- **END TIME:** 2026-08-10T19:33:08.464Z
- **DURATION:** 1608 ms

### EXP-031

- **ROOM:** audio
- **CONTROL:** Add to journal
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Add to journal
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Add to journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-031.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:08.464Z
- **END TIME:** 2026-08-10T19:33:10.074Z
- **DURATION:** 1610 ms

### EXP-032

- **ROOM:** audio
- **CONTROL:** Summarize
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Summarize
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Summarize"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-032.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:10.075Z
- **END TIME:** 2026-08-10T19:33:11.685Z
- **DURATION:** 1610 ms

### EXP-033

- **ROOM:** audio
- **CONTROL:** Apply trim
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Apply trim
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Apply trim"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-033.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:11.685Z
- **END TIME:** 2026-08-10T19:33:13.292Z
- **DURATION:** 1607 ms

### EXP-034

- **ROOM:** audio
- **CONTROL:** Normalize
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Normalize
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Normalize"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-034.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:13.292Z
- **END TIME:** 2026-08-10T19:33:14.907Z
- **DURATION:** 1615 ms

### EXP-035

- **ROOM:** audio
- **CONTROL:** Edit
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Edit
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "before": "Aria \u00b7 Audio studio\nListening quietly\nAudio\nVoice Journal\n\nCould not load audio status.\n\nRecord & transcribe\n\nChat mic u", "crashed": false, "label": "Edit"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-035.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:14.910Z
- **END TIME:** 2026-08-10T19:33:16.519Z
- **DURATION:** 1609 ms

### EXP-036

- **ROOM:** audit
- **CONTROL:** Open Mission Control
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Mission Control
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Mission Control", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-036.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:16.519Z
- **END TIME:** 2026-08-10T19:33:17.422Z
- **DURATION:** 903 ms

### EXP-037

- **ROOM:** audit
- **CONTROL:** Open Actions checklist
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Actions checklist
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Actions checklist", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-037.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:17.423Z
- **END TIME:** 2026-08-10T19:33:18.325Z
- **DURATION:** 902 ms

### EXP-038

- **ROOM:** automation
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-038.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:18.325Z
- **END TIME:** 2026-08-10T19:33:19.931Z
- **DURATION:** 1606 ms

### EXP-039

- **ROOM:** automation
- **CONTROL:** Pause all
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Pause all
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Pause all"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-039.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:19.932Z
- **END TIME:** 2026-08-10T19:33:21.537Z
- **DURATION:** 1605 ms

### EXP-040

- **ROOM:** automation
- **CONTROL:** Resume
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Resume
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Resume"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-040.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:21.537Z
- **END TIME:** 2026-08-10T19:33:23.144Z
- **DURATION:** 1607 ms

### EXP-041

- **ROOM:** automation
- **CONTROL:** New rule
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: New rule
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "New rule"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-041.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:23.144Z
- **END TIME:** 2026-08-10T19:33:24.752Z
- **DURATION:** 1608 ms

### EXP-042

- **ROOM:** automation
- **CONTROL:** Specialist team
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Specialist team
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Specialist team"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-042.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:24.752Z
- **END TIME:** 2026-08-10T19:33:26.357Z
- **DURATION:** 1605 ms

### EXP-043

- **ROOM:** automation
- **CONTROL:** Specialists
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Specialists
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Specialists"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-043.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:26.357Z
- **END TIME:** 2026-08-10T19:33:27.963Z
- **DURATION:** 1606 ms

### EXP-044

- **ROOM:** automation
- **CONTROL:** Team history
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Team history
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Team history"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-044.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:27.963Z
- **END TIME:** 2026-08-10T19:33:29.569Z
- **DURATION:** 1605 ms

### EXP-045

- **ROOM:** automation
- **CONTROL:** View Paths
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: View Paths
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "View Paths"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-045.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:29.569Z
- **END TIME:** 2026-08-10T19:33:31.191Z
- **DURATION:** 1622 ms

### EXP-046

- **ROOM:** automation
- **CONTROL:** Webhook
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Webhook
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Webhook"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-046.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:31.193Z
- **END TIME:** 2026-08-10T19:33:32.806Z
- **DURATION:** 1613 ms

### EXP-047

- **ROOM:** automation
- **CONTROL:** Export
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Export
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Export"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-047.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:32.806Z
- **END TIME:** 2026-08-10T19:33:34.412Z
- **DURATION:** 1606 ms

### EXP-048

- **ROOM:** automation
- **CONTROL:** Import
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Import
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Import"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-048.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:34.412Z
- **END TIME:** 2026-08-10T19:33:36.023Z
- **DURATION:** 1610 ms

### EXP-049

- **ROOM:** automation
- **CONTROL:** Draft from NL
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Draft from NL
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "crashed": false, "label": "Draft from NL"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-049.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:36.024Z
- **END TIME:** 2026-08-10T19:33:37.630Z
- **DURATION:** 1606 ms

### EXP-050

- **ROOM:** browser
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "before": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-050.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:37.631Z
- **END TIME:** 2026-08-10T19:33:39.237Z
- **DURATION:** 1606 ms

### EXP-051

- **ROOM:** browser
- **CONTROL:** Projects
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Projects
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Creative workshop\nListening quietly\nProjects\n\nWorkspace identity layer \u2014 one slug connects coding, memory, journa", "before": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "crashed": false, "label": "Projects"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-051.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:39.237Z
- **END TIME:** 2026-08-10T19:33:40.858Z
- **DURATION:** 1621 ms

### EXP-052

- **ROOM:** browser
- **CONTROL:** Job Center
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Job Center
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "before": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "crashed": false, "label": "Job Center"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-052.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:40.858Z
- **END TIME:** 2026-08-10T19:33:42.465Z
- **DURATION:** 1607 ms

### EXP-053

- **ROOM:** browser
- **CONTROL:** Coding
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Coding
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Engineering studio\nListening quietly\nCoding\n\nPropose \u2192 Review \u2192 Apply \u2192 Undo \u2192 Verify. Projects identify workspac", "before": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "crashed": false, "label": "Coding"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-053.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:42.465Z
- **END TIME:** 2026-08-10T19:33:44.108Z
- **DURATION:** 1643 ms

### EXP-054

- **ROOM:** browser
- **CONTROL:** Open Memory
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Memory
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Memory", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-054.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:44.109Z
- **END TIME:** 2026-08-10T19:33:45.012Z
- **DURATION:** 903 ms

### EXP-055

- **ROOM:** browser
- **CONTROL:** Open Documents
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Documents
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Documents", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-055.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:45.012Z
- **END TIME:** 2026-08-10T19:33:45.915Z
- **DURATION:** 903 ms

### EXP-056

- **ROOM:** browser
- **CONTROL:** Open Chat
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Chat
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Chat", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-056.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:45.916Z
- **END TIME:** 2026-08-10T19:33:46.818Z
- **DURATION:** 902 ms

### EXP-057

- **ROOM:** browser
- **CONTROL:** Detach browser panel
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Detach browser panel
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "before": "Aria \u00b7 Browser\nListening quietly\nBrowser\n\nLive web interaction agent \u2014 Playwright navigation, screenshots, DOM/Vision ta", "crashed": false, "label": "Detach browser panel"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-057.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:46.819Z
- **END TIME:** 2026-08-10T19:33:48.428Z
- **DURATION:** 1609 ms

### EXP-058

- **ROOM:** browser
- **CONTROL:** Open
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-058.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:48.428Z
- **END TIME:** 2026-08-10T19:33:49.331Z
- **DURATION:** 903 ms

### EXP-059

- **ROOM:** browser
- **CONTROL:** Bookmark current URL
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Bookmark current URL
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Bookmark current URL", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-059.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:49.331Z
- **END TIME:** 2026-08-10T19:33:50.235Z
- **DURATION:** 904 ms

### EXP-060

- **ROOM:** browser
- **CONTROL:** Screenshot
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Screenshot
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Screenshot", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-060.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:50.235Z
- **END TIME:** 2026-08-10T19:33:51.139Z
- **DURATION:** 904 ms

### EXP-061

- **ROOM:** browser
- **CONTROL:** Install Playwright
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Install Playwright
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Install Playwright", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-061.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:51.140Z
- **END TIME:** 2026-08-10T19:33:52.051Z
- **DURATION:** 911 ms

### EXP-062

- **ROOM:** calendar
- **CONTROL:** Planner
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Planner
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Leather notebook\nListening quietly\nPlanner\n\nToday\u2019s actionable work \u00b7 Journal for notes \u00b7 Calendar for commitment", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Planner"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-062.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:52.052Z
- **END TIME:** 2026-08-10T19:33:53.685Z
- **DURATION:** 1633 ms

### EXP-063

- **ROOM:** calendar
- **CONTROL:** Journal
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Journal
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Bullet journal\nListening quietly\nBullet Journal\n\nNotes, thoughts, reflections \u00b7 promote actionable items to Plann", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-063.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:53.685Z
- **END TIME:** 2026-08-10T19:33:55.302Z
- **DURATION:** 1617 ms

### EXP-064

- **ROOM:** calendar
- **CONTROL:** Previous
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Previous
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Previous"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-064.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:55.302Z
- **END TIME:** 2026-08-10T19:33:56.909Z
- **DURATION:** 1607 ms

### EXP-065

- **ROOM:** calendar
- **CONTROL:** Next
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Next
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Next"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-065.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:56.909Z
- **END TIME:** 2026-08-10T19:33:58.516Z
- **DURATION:** 1607 ms

### EXP-066

- **ROOM:** calendar
- **CONTROL:** Jump to today (T)
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Jump to today (T)
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Jump to today (T)", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-066.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:33:58.516Z
- **END TIME:** 2026-08-10T19:33:59.419Z
- **DURATION:** 903 ms

### EXP-067

- **ROOM:** calendar
- **CONTROL:** Month
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Month
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Month"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-067.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:33:59.420Z
- **END TIME:** 2026-08-10T19:34:01.029Z
- **DURATION:** 1609 ms

### EXP-068

- **ROOM:** calendar
- **CONTROL:** Week
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Week
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Week"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-068.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:01.030Z
- **END TIME:** 2026-08-10T19:34:02.639Z
- **DURATION:** 1609 ms

### EXP-069

- **ROOM:** calendar
- **CONTROL:** Agenda
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Agenda
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Agenda"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-069.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:02.639Z
- **END TIME:** 2026-08-10T19:34:04.248Z
- **DURATION:** 1609 ms

### EXP-070

- **ROOM:** calendar
- **CONTROL:** Timeline
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Timeline
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Timeline"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-070.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:04.248Z
- **END TIME:** 2026-08-10T19:34:05.855Z
- **DURATION:** 1607 ms

### EXP-071

- **ROOM:** calendar
- **CONTROL:** Open Planner
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Planner
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Leather notebook\nListening quietly\nPlanner\n\nToday\u2019s actionable work \u00b7 Journal for notes \u00b7 Calendar for commitment", "before": "Aria \u00b7 Wall calendar\nListening quietly\nCalendar\n\nScheduled commitments \u00b7 use Planner for today\u2019s actionable work \u00b7 Journ", "crashed": false, "label": "Open Planner"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-071.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:05.855Z
- **END TIME:** 2026-08-10T19:34:07.468Z
- **DURATION:** 1612 ms

### EXP-072

- **ROOM:** calendar
- **CONTROL:** Open Bullet Journal
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Bullet Journal
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Bullet Journal", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-072.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:07.468Z
- **END TIME:** 2026-08-10T19:34:08.371Z
- **DURATION:** 903 ms

### EXP-073

- **ROOM:** calendar
- **CONTROL:** Open Documents
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Documents
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Documents", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-073.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:08.371Z
- **END TIME:** 2026-08-10T19:34:09.274Z
- **DURATION:** 903 ms

### EXP-074

- **ROOM:** capabilities
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "before": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-074.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:09.275Z
- **END TIME:** 2026-08-10T19:34:10.884Z
- **DURATION:** 1609 ms

### EXP-075

- **ROOM:** capabilities
- **CONTROL:** Load enabled
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Load enabled
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "before": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "crashed": false, "label": "Load enabled"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-075.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:10.884Z
- **END TIME:** 2026-08-10T19:34:12.490Z
- **DURATION:** 1606 ms

### EXP-076

- **ROOM:** capabilities
- **CONTROL:** Diagnostics
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Diagnostics
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "before": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "crashed": false, "label": "Diagnostics"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-076.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:12.491Z
- **END TIME:** 2026-08-10T19:34:14.098Z
- **DURATION:** 1607 ms

### EXP-077

- **ROOM:** capabilities
- **CONTROL:** Search capabilities…
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search capabilities…
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Search capabilities\u2026", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-077.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:14.098Z
- **END TIME:** 2026-08-10T19:34:15.002Z
- **DURATION:** 904 ms

### EXP-078

- **ROOM:** capabilities
- **CONTROL:** Filter by layer
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Filter by layer
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "before": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "crashed": false, "label": "Filter by layer"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-078.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:15.002Z
- **END TIME:** 2026-08-10T19:34:16.608Z
- **DURATION:** 1606 ms

### EXP-079

- **ROOM:** capabilities
- **CONTROL:** Filter by category
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Filter by category
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "before": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "crashed": false, "label": "Filter by category"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-079.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:16.609Z
- **END TIME:** 2026-08-10T19:34:18.216Z
- **DURATION:** 1607 ms

### EXP-080

- **ROOM:** capabilities
- **CONTROL:** Filter by trust
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Filter by trust
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "before": "Aria \u00b7 Capabilities\nListening quietly\nCapabilities\n\nUnified management for everything that extends Aria. Products stay p", "crashed": false, "label": "Filter by trust"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-080.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:18.217Z
- **END TIME:** 2026-08-10T19:34:19.822Z
- **DURATION:** 1605 ms

### EXP-081

- **ROOM:** chat
- **CONTROL:** More
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: More
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria is here\nI'm here\nNEARBY\nNew conversation\nfresh\nPlace something here\nattach\nModel\nChat model: (default)\nRead aloud\no", "before": "Aria is here\nI'm here\nYou\nWhat fly tying materials are in my inventory?\nA\nSure thing! To check your fly tying inventory,", "crashed": false, "label": "More"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-081.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:19.823Z
- **END TIME:** 2026-08-10T19:34:21.436Z
- **DURATION:** 1613 ms

### EXP-082

- **ROOM:** chat
- **CONTROL:** Good morning
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Good morning
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Good morning", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-082.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:21.437Z
- **END TIME:** 2026-08-10T19:34:22.339Z
- **DURATION:** 902 ms

### EXP-083

- **ROOM:** chat
- **CONTROL:** What should we work on?
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: What should we work on?
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "What should we work on?", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-083.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:22.339Z
- **END TIME:** 2026-08-10T19:34:23.241Z
- **DURATION:** 902 ms

### EXP-084

- **ROOM:** chat
- **CONTROL:** Just listen for a bit
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Just listen for a bit
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Just listen for a bit", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-084.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:23.242Z
- **END TIME:** 2026-08-10T19:34:24.144Z
- **DURATION:** 902 ms

### EXP-085

- **ROOM:** chat
- **CONTROL:** Say anything…
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Say anything…
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Say anything\u2026", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-085.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:24.144Z
- **END TIME:** 2026-08-10T19:34:25.047Z
- **DURATION:** 903 ms

### EXP-086

- **ROOM:** coding
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Engineering studio\nListening quietly\nCoding\n\nPropose \u2192 Review \u2192 Apply \u2192 Undo \u2192 Verify. Projects identify workspac", "before": "Aria \u00b7 Engineering studio\nListening quietly\nCoding\n\nPropose \u2192 Review \u2192 Apply \u2192 Undo \u2192 Verify. Projects identify workspac", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-086.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:25.048Z
- **END TIME:** 2026-08-10T19:34:26.654Z
- **DURATION:** 1606 ms

### EXP-087

- **ROOM:** coding
- **CONTROL:** Workspace identity
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Workspace identity
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Workspace identity", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-087.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:26.655Z
- **END TIME:** 2026-08-10T19:34:27.562Z
- **DURATION:** 907 ms

### EXP-088

- **ROOM:** coding
- **CONTROL:** Live coding jobs
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Live coding jobs
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Live coding jobs", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-088.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:27.568Z
- **END TIME:** 2026-08-10T19:34:28.472Z
- **DURATION:** 904 ms

### EXP-089

- **ROOM:** coding
- **CONTROL:** Coding model role
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Coding model role
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Coding model role", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-089.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:28.472Z
- **END TIME:** 2026-08-10T19:34:29.376Z
- **DURATION:** 904 ms

### EXP-090

- **ROOM:** connections
- **CONTROL:** Shortcuts
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Shortcuts
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Shortcuts", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-090.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:29.376Z
- **END TIME:** 2026-08-10T19:34:30.279Z
- **DURATION:** 903 ms

### EXP-091

- **ROOM:** connections
- **CONTROL:** Search
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-091.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:30.280Z
- **END TIME:** 2026-08-10T19:34:31.886Z
- **DURATION:** 1606 ms

### EXP-092

- **ROOM:** connections
- **CONTROL:** Browse
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Browse
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Browse"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-092.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:31.887Z
- **END TIME:** 2026-08-10T19:34:33.493Z
- **DURATION:** 1606 ms

### EXP-093

- **ROOM:** connections
- **CONTROL:** New (N)
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: New (N)
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "New (N)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-093.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:33.494Z
- **END TIME:** 2026-08-10T19:34:35.105Z
- **DURATION:** 1611 ms

### EXP-094

- **ROOM:** connections
- **CONTROL:** Import
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Import
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Import"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-094.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:35.106Z
- **END TIME:** 2026-08-10T19:34:36.718Z
- **DURATION:** 1612 ms

### EXP-095

- **ROOM:** connections
- **CONTROL:** Cleanup
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Cleanup
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Cleanup"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-095.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:36.719Z
- **END TIME:** 2026-08-10T19:34:38.325Z
- **DURATION:** 1606 ms

### EXP-096

- **ROOM:** connections
- **CONTROL:** Assistant
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Assistant
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Assistant"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-096.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:38.326Z
- **END TIME:** 2026-08-10T19:34:39.932Z
- **DURATION:** 1606 ms

### EXP-097

- **ROOM:** connections
- **CONTROL:** Undo
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Undo
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Undo"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-097.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:39.933Z
- **END TIME:** 2026-08-10T19:34:41.539Z
- **DURATION:** 1606 ms

### EXP-098

- **ROOM:** connections
- **CONTROL:** Clear
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Clear
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Clear"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-098.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:41.539Z
- **END TIME:** 2026-08-10T19:34:43.145Z
- **DURATION:** 1606 ms

### EXP-099

- **ROOM:** connections
- **CONTROL:** Search connections
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search connections
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Search connections"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-099.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:43.146Z
- **END TIME:** 2026-08-10T19:34:44.753Z
- **DURATION:** 1607 ms

### EXP-100

- **ROOM:** connections
- **CONTROL:** Search mode
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search mode
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "before": "Aria \u00b7 Connections\nListening quietly\nConnections\n\nRelationship explorer \u2014 models how things relate. Not Memory, not Docu", "crashed": false, "label": "Search mode"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-100.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:44.754Z
- **END TIME:** 2026-08-10T19:34:46.359Z
- **DURATION:** 1605 ms

### EXP-101

- **ROOM:** documents
- **CONTROL:** Shortcuts
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Shortcuts
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Shortcuts", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-101.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:46.360Z
- **END TIME:** 2026-08-10T19:34:47.263Z
- **DURATION:** 903 ms

### EXP-102

- **ROOM:** documents
- **CONTROL:** Import
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Import
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "before": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "crashed": false, "label": "Import"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-102.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:47.263Z
- **END TIME:** 2026-08-10T19:34:48.873Z
- **DURATION:** 1610 ms

### EXP-103

- **ROOM:** documents
- **CONTROL:** Search
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "before": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "crashed": false, "label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-103.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:48.875Z
- **END TIME:** 2026-08-10T19:34:50.483Z
- **DURATION:** 1608 ms

### EXP-104

- **ROOM:** documents
- **CONTROL:** Rebuild Search Index
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Rebuild Search Index
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "before": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "crashed": false, "label": "Rebuild Search Index"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-104.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:50.484Z
- **END TIME:** 2026-08-10T19:34:52.100Z
- **DURATION:** 1616 ms

### EXP-105

- **ROOM:** documents
- **CONTROL:** Briefing
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Briefing
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "before": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "crashed": false, "label": "Briefing"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-105.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:52.104Z
- **END TIME:** 2026-08-10T19:34:53.714Z
- **DURATION:** 1610 ms

### EXP-106

- **ROOM:** documents
- **CONTROL:** Clear
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Clear
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "before": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "crashed": false, "label": "Clear"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-106.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:53.714Z
- **END TIME:** 2026-08-10T19:34:55.326Z
- **DURATION:** 1611 ms

### EXP-107

- **ROOM:** documents
- **CONTROL:** Upload
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Upload
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "before": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "crashed": false, "label": "Upload"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-107.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:55.326Z
- **END TIME:** 2026-08-10T19:34:56.935Z
- **DURATION:** 1609 ms

### EXP-108

- **ROOM:** documents
- **CONTROL:** Import Folder
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Import Folder
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Import Folder", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-108.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:56.936Z
- **END TIME:** 2026-08-10T19:34:57.838Z
- **DURATION:** 902 ms

### EXP-109

- **ROOM:** documents
- **CONTROL:** Summarize
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Summarize
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria is here\nI'm here\nYou\nWhat fly tying materials are in my inventory?\nA\nSure thing! To check your fly tying inventory,", "before": "Aria \u00b7 Private library\nListening quietly\nDocuments\n\nPersonal document intelligence \u2014 local files, grounded search, Memor", "crashed": false, "label": "Summarize"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-109.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:34:57.839Z
- **END TIME:** 2026-08-10T19:34:59.461Z
- **DURATION:** 1622 ms

### EXP-110

- **ROOM:** documents
- **CONTROL:** Learn → candidates
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Learn → candidates
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Learn \u2192 candidates", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-110.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:34:59.461Z
- **END TIME:** 2026-08-10T19:35:00.364Z
- **DURATION:** 903 ms

### EXP-111

- **ROOM:** documents
- **CONTROL:** Document Briefing
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Document Briefing
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Document Briefing", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-111.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:00.365Z
- **END TIME:** 2026-08-10T19:35:01.268Z
- **DURATION:** 903 ms

### EXP-112

- **ROOM:** documents
- **CONTROL:** Open Memory
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Memory
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Memory", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-112.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:01.268Z
- **END TIME:** 2026-08-10T19:35:02.172Z
- **DURATION:** 904 ms

### EXP-113

- **ROOM:** flytying
- **CONTROL:** Guided library setup & health
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Guided library setup & health
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Guided library setup & health", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-113.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:02.173Z
- **END TIME:** 2026-08-10T19:35:03.081Z
- **DURATION:** 908 ms

### EXP-114

- **ROOM:** flytying
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "before": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-114.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:03.082Z
- **END TIME:** 2026-08-10T19:35:04.691Z
- **DURATION:** 1609 ms

### EXP-115

- **ROOM:** flytying
- **CONTROL:** Open Gallery
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Gallery
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Gallery", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-115.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:04.691Z
- **END TIME:** 2026-08-10T19:35:05.594Z
- **DURATION:** 903 ms

### EXP-116

- **ROOM:** flytying
- **CONTROL:** Suggest a fly
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Suggest a fly
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "before": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "crashed": false, "label": "Suggest a fly"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-116.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:05.595Z
- **END TIME:** 2026-08-10T19:35:07.205Z
- **DURATION:** 1610 ms

### EXP-117

- **ROOM:** flytying
- **CONTROL:** Open inventory
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open inventory
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "before": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "crashed": false, "label": "Open inventory"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-117.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:07.205Z
- **END TIME:** 2026-08-10T19:35:08.816Z
- **DURATION:** 1611 ms

### EXP-118

- **ROOM:** flytying
- **CONTROL:** Start session
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Start session
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "before": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "crashed": false, "label": "Start session"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-118.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:08.816Z
- **END TIME:** 2026-08-10T19:35:10.431Z
- **DURATION:** 1615 ms

### EXP-119

- **ROOM:** flytying
- **CONTROL:** Apply profile
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Apply profile
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "before": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "crashed": false, "label": "Apply profile"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-119.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:10.432Z
- **END TIME:** 2026-08-10T19:35:12.048Z
- **DURATION:** 1616 ms

### EXP-120

- **ROOM:** flytying
- **CONTROL:** Voice: next step
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Voice: next step
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Voice: next step", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-120.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:12.049Z
- **END TIME:** 2026-08-10T19:35:12.953Z
- **DURATION:** 904 ms

### EXP-121

- **ROOM:** flytying
- **CONTROL:** Voice: repeat step
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Voice: repeat step
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Voice: repeat step", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-121.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:12.953Z
- **END TIME:** 2026-08-10T19:35:13.856Z
- **DURATION:** 903 ms

### EXP-122

- **ROOM:** flytying
- **CONTROL:** Search fly patterns
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search fly patterns
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "before": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "crashed": false, "label": "Search fly patterns"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-122.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:13.857Z
- **END TIME:** 2026-08-10T19:35:15.465Z
- **DURATION:** 1608 ms

### EXP-123

- **ROOM:** flytying
- **CONTROL:** Clear search and type filter
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Clear search and type filter
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Clear search and type filter", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-123.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:15.466Z
- **END TIME:** 2026-08-10T19:35:16.368Z
- **DURATION:** 902 ms

### EXP-124

- **ROOM:** flytying
- **CONTROL:** Seasonal
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Seasonal
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "before": "Aria \u00b7 Streamside cabin\nListening quietly\nFly tying\n\n271 catalog patterns \u00b7 library connected \u00b7 smart search on \u00b7 index ", "crashed": false, "label": "Seasonal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-124.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:16.369Z
- **END TIME:** 2026-08-10T19:35:17.975Z
- **DURATION:** 1606 ms

### EXP-125

- **ROOM:** gallery
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "before": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-125.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:17.976Z
- **END TIME:** 2026-08-10T19:35:19.604Z
- **DURATION:** 1628 ms

### EXP-126

- **ROOM:** gallery
- **CONTROL:** Job Center
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Job Center
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "", "before": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "crashed": false, "label": "Job Center"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-126.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:19.604Z
- **END TIME:** 2026-08-10T19:35:21.215Z
- **DURATION:** 1611 ms

### EXP-127

- **ROOM:** gallery
- **CONTROL:** Models
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Models
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Provider bay\nListening quietly\nModels\n\nAI model configuration and routing center \u2014 roles, catalog, providers, pre", "before": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "crashed": false, "label": "Models"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-127.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:21.216Z
- **END TIME:** 2026-08-10T19:35:22.844Z
- **DURATION:** 1628 ms

### EXP-128

- **ROOM:** gallery
- **CONTROL:** Open Maker lab
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Maker lab
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Maker lab", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-128.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:22.844Z
- **END TIME:** 2026-08-10T19:35:23.748Z
- **DURATION:** 904 ms

### EXP-129

- **ROOM:** gallery
- **CONTROL:** Open Fly tying
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Fly tying
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Fly tying", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-129.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:23.749Z
- **END TIME:** 2026-08-10T19:35:24.651Z
- **DURATION:** 902 ms

### EXP-130

- **ROOM:** gallery
- **CONTROL:** Open Video Studio
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Video Studio
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Video Studio", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-130.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:24.652Z
- **END TIME:** 2026-08-10T19:35:25.554Z
- **DURATION:** 902 ms

### EXP-131

- **ROOM:** gallery
- **CONTROL:** Open Meme Studio
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Meme Studio
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Meme Studio", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-131.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:25.555Z
- **END TIME:** 2026-08-10T19:35:26.458Z
- **DURATION:** 903 ms

### EXP-132

- **ROOM:** gallery
- **CONTROL:** Generate
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "before": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "crashed": false, "label": "Generate"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-132.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:26.459Z
- **END TIME:** 2026-08-10T19:35:28.069Z
- **DURATION:** 1610 ms

### EXP-133

- **ROOM:** gallery
- **CONTROL:** Preview enhance
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Preview enhance
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "before": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "crashed": false, "label": "Preview enhance"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-133.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:28.071Z
- **END TIME:** 2026-08-10T19:35:29.680Z
- **DURATION:** 1609 ms

### EXP-134

- **ROOM:** gallery
- **CONTROL:** Advanced
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Advanced
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "before": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "crashed": false, "label": "Advanced"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-134.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:29.680Z
- **END TIME:** 2026-08-10T19:35:31.289Z
- **DURATION:** 1609 ms

### EXP-135

- **ROOM:** gallery
- **CONTROL:** Reuse last settings with a new seed
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Reuse last settings with a new seed
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Reuse last settings with a new seed", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-135.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:31.290Z
- **END TIME:** 2026-08-10T19:35:32.193Z
- **DURATION:** 903 ms

### EXP-136

- **ROOM:** gallery
- **CONTROL:** Mission Control
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Mission Control
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "", "before": "Aria \u00b7 Museum\nListening quietly\nGallery\n\nLocal AI image product \u2014 generate, browse, organize, and edit stills. Video and", "crashed": false, "label": "Mission Control"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-136.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:32.194Z
- **END TIME:** 2026-08-10T19:35:33.815Z
- **DURATION:** 1621 ms

### EXP-137

- **ROOM:** health
- **CONTROL:** Doctor visit
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Doctor visit
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Doctor visit"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-137.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:33.816Z
- **END TIME:** 2026-08-10T19:35:35.886Z
- **DURATION:** 2070 ms

### EXP-138

- **ROOM:** health
- **CONTROL:** Emergency
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Emergency
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Emergency"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-138.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:35.887Z
- **END TIME:** 2026-08-10T19:35:37.886Z
- **DURATION:** 1999 ms

### EXP-139

- **ROOM:** health
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-139.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:37.887Z
- **END TIME:** 2026-08-10T19:35:39.887Z
- **DURATION:** 2000 ms

### EXP-140

- **ROOM:** health
- **CONTROL:** Timeline
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Timeline
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Timeline"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-140.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:39.889Z
- **END TIME:** 2026-08-10T19:35:41.888Z
- **DURATION:** 1999 ms

### EXP-141

- **ROOM:** health
- **CONTROL:** Dashboard
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Dashboard
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Dashboard"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-141.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:41.890Z
- **END TIME:** 2026-08-10T19:35:43.886Z
- **DURATION:** 1996 ms

### EXP-142

- **ROOM:** health
- **CONTROL:** Check-in
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Check-in
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Check-in"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-142.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:43.887Z
- **END TIME:** 2026-08-10T19:35:45.886Z
- **DURATION:** 1999 ms

### EXP-143

- **ROOM:** health
- **CONTROL:** Activity
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Activity
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Activity"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-143.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:45.887Z
- **END TIME:** 2026-08-10T19:35:47.885Z
- **DURATION:** 1998 ms

### EXP-144

- **ROOM:** health
- **CONTROL:** Workouts
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Workouts
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Workouts"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-144.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:47.886Z
- **END TIME:** 2026-08-10T19:35:49.886Z
- **DURATION:** 2000 ms

### EXP-145

- **ROOM:** health
- **CONTROL:** Goals
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Goals
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Goals"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-145.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:49.887Z
- **END TIME:** 2026-08-10T19:35:51.885Z
- **DURATION:** 1998 ms

### EXP-146

- **ROOM:** health
- **CONTROL:** Trends
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Trends
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Trends"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-146.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:51.886Z
- **END TIME:** 2026-08-10T19:35:53.885Z
- **DURATION:** 1999 ms

### EXP-147

- **ROOM:** health
- **CONTROL:** Meds
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Meds
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Meds"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-147.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:53.887Z
- **END TIME:** 2026-08-10T19:35:55.894Z
- **DURATION:** 2007 ms

### EXP-148

- **ROOM:** health
- **CONTROL:** Supplements
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Supplements
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "before": "Aria \u00b7 Wellness clinic\nListening quietly\nHealth\n\nPersonal Health Record \u2014 local, private, printable. Not an EMR. Aria do", "crashed": false, "label": "Supplements"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-148.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:55.895Z
- **END TIME:** 2026-08-10T19:35:57.887Z
- **DURATION:** 1992 ms

### EXP-149

- **ROOM:** home
- **CONTROL:** Open Mission Control
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Mission Control
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Aerospace ops\nListening quietly\nMission Control\n\nInfrastructure health console \u2014 providers, runtime, hardware, re", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "Open Mission Control"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-149.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:35:57.888Z
- **END TIME:** 2026-08-10T19:35:59.888Z
- **DURATION:** 2000 ms

### EXP-150

- **ROOM:** home
- **CONTROL:** Open Planner
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Planner
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Planner", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-150.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:35:59.888Z
- **END TIME:** 2026-08-10T19:36:00.890Z
- **DURATION:** 1002 ms

### EXP-151

- **ROOM:** home
- **CONTROL:** Open Bullet Journal
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Bullet Journal
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Bullet Journal", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-151.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:36:00.891Z
- **END TIME:** 2026-08-10T19:36:01.890Z
- **DURATION:** 999 ms

### EXP-152

- **ROOM:** home
- **CONTROL:** Open Calendar
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Calendar
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Calendar", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-152.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:36:01.891Z
- **END TIME:** 2026-08-10T19:36:02.889Z
- **DURATION:** 998 ms

### EXP-153

- **ROOM:** home
- **CONTROL:** Automation Home
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Automation Home
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Automation loft\nListening quietly\nAutomation Home\n\nOrchestrates schedules, rules, skills, and workflows. Not Job ", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "Automation Home"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-153.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:02.890Z
- **END TIME:** 2026-08-10T19:36:04.887Z
- **DURATION:** 1997 ms

### EXP-154

- **ROOM:** home
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-154.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:04.887Z
- **END TIME:** 2026-08-10T19:36:06.886Z
- **DURATION:** 1999 ms

### EXP-155

- **ROOM:** home
- **CONTROL:** Scan action log
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Scan action log
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "Scan action log"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-155.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:06.887Z
- **END TIME:** 2026-08-10T19:36:08.885Z
- **DURATION:** 1998 ms

### EXP-156

- **ROOM:** home
- **CONTROL:** Set PIN
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Set PIN
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "Set PIN"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-156.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:08.886Z
- **END TIME:** 2026-08-10T19:36:10.886Z
- **DURATION:** 2000 ms

### EXP-157

- **ROOM:** home
- **CONTROL:** 4–6 digit PIN
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 4–6 digit PIN
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "4\u20136 digit PIN", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-157.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:36:10.887Z
- **END TIME:** 2026-08-10T19:36:11.887Z
- **DURATION:** 1000 ms

### EXP-158

- **ROOM:** home
- **CONTROL:** First-flight checklist ▾
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: First-flight checklist ▾
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "First-flight checklist \u25be"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-158.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:11.888Z
- **END TIME:** 2026-08-10T19:36:13.893Z
- **DURATION:** 2005 ms

### EXP-159

- **ROOM:** home
- **CONTROL:** Skills & learned workflows ▾
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Skills & learned workflows ▾
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "Skills & learned workflows \u25be"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-159.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:13.894Z
- **END TIME:** 2026-08-10T19:36:15.888Z
- **DURATION:** 1994 ms

### EXP-160

- **ROOM:** home
- **CONTROL:** Security ▾
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Security ▾
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "before": "Aria \u00b7 Foyer\nListening quietly\n\nWelcome back\n\nGood afternoon\n\nMonday, August 10\n\nMission Control Planner Journal Calenda", "crashed": false, "label": "Security \u25be"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-160.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:15.888Z
- **END TIME:** 2026-08-10T19:36:17.888Z
- **DURATION:** 2000 ms

### EXP-161

- **ROOM:** home_automation
- **CONTROL:** Open Presence
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Presence
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Presence", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-161.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:36:17.889Z
- **END TIME:** 2026-08-10T19:36:18.888Z
- **DURATION:** 999 ms

### EXP-162

- **ROOM:** home_automation
- **CONTROL:** Open Security
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Security
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Security", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-162.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:36:18.889Z
- **END TIME:** 2026-08-10T19:36:19.887Z
- **DURATION:** 998 ms

### EXP-163

- **ROOM:** home_automation
- **CONTROL:** Search
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-163.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:19.888Z
- **END TIME:** 2026-08-10T19:36:21.887Z
- **DURATION:** 1999 ms

### EXP-164

- **ROOM:** home_automation
- **CONTROL:** Open Home Assistant
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Home Assistant
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Open Home Assistant", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-164.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:36:21.888Z
- **END TIME:** 2026-08-10T19:36:22.887Z
- **DURATION:** 999 ms

### EXP-165

- **ROOM:** home_automation
- **CONTROL:** Status
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Status
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "Status"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-165.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:22.888Z
- **END TIME:** 2026-08-10T19:36:24.887Z
- **DURATION:** 1999 ms

### EXP-166

- **ROOM:** home_automation
- **CONTROL:** Apply
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Apply
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "Apply"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-166.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:24.888Z
- **END TIME:** 2026-08-10T19:36:26.887Z
- **DURATION:** 1999 ms

### EXP-167

- **ROOM:** home_automation
- **CONTROL:** haPasteTokenBtn
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: haPasteTokenBtn
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "haPasteTokenBtn"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-167.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:26.889Z
- **END TIME:** 2026-08-10T19:36:28.886Z
- **DURATION:** 1997 ms

### EXP-168

- **ROOM:** home_automation
- **CONTROL:** haTokenModalBtn
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: haTokenModalBtn
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "haTokenModalBtn"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-168.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:28.887Z
- **END TIME:** 2026-08-10T19:36:30.889Z
- **DURATION:** 2002 ms

### EXP-169

- **ROOM:** home_automation
- **CONTROL:** haTestBtn
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: haTestBtn
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "haTestBtn"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-169.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:30.890Z
- **END TIME:** 2026-08-10T19:36:32.887Z
- **DURATION:** 1997 ms

### EXP-170

- **ROOM:** home_automation
- **CONTROL:** haSaveBtn
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: haSaveBtn
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "haSaveBtn"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-170.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:36:32.888Z
- **END TIME:** 2026-08-10T19:37:11.888Z
- **DURATION:** 39000 ms

### EXP-171

- **ROOM:** home_automation
- **CONTROL:** ghost-btn small ha-quick-btn
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: ghost-btn small ha-quick-btn
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "ghost-btn small ha-quick-btn", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-171.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:37:11.889Z
- **END TIME:** 2026-08-10T19:38:11.894Z
- **DURATION:** 60004 ms

### EXP-172

- **ROOM:** home_automation
- **CONTROL:** haSetupWizardBtn
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: haSetupWizardBtn
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "before": "Aria \u00b7 Home control\nListening quietly\nHome Automation\nPresence Security\n\nLights, scenes, and Home Assistant \u2014 control th", "crashed": false, "label": "haSetupWizardBtn"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-172.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:38:11.895Z
- **END TIME:** 2026-08-10T19:40:11.886Z
- **DURATION:** 119991 ms

### EXP-173

- **ROOM:** integrations
- **CONTROL:** Refresh
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "before": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "crashed": false, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-173.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:40:11.887Z
- **END TIME:** 2026-08-10T19:42:11.885Z
- **DURATION:** 119998 ms

### EXP-174

- **ROOM:** integrations
- **CONTROL:** Test configured
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Test configured
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "before": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "crashed": false, "label": "Test configured"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-174.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:42:11.886Z
- **END TIME:** 2026-08-10T19:44:11.887Z
- **DURATION:** 120001 ms

### EXP-175

- **ROOM:** integrations
- **CONTROL:** Diagnostics
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Diagnostics
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "before": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "crashed": false, "label": "Diagnostics"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-175.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:44:11.888Z
- **END TIME:** 2026-08-10T19:46:11.886Z
- **DURATION:** 119998 ms

### EXP-176

- **ROOM:** integrations
- **CONTROL:** Search providers…
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search providers…
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"label": "Search providers\u2026", "missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-176.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:46:11.888Z
- **END TIME:** 2026-08-10T19:47:11.884Z
- **DURATION:** 59996 ms

### EXP-177

- **ROOM:** integrations
- **CONTROL:** Filter by category
- **HOW DISCOVERED:** recursive control inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Filter by category
- **EXPECTED:** Control responds without crash; UI remains usable
- **ACTUAL:** `{"after": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "before": "Aria \u00b7 Integrations\nListening quietly\nIntegrations\n\nProvider credentials, connection tests, and unlock matrix. Products ", "crashed": false, "label": "Filter by category"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-177.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:47:11.885Z
- **END TIME:** 2026-08-10T19:49:11.886Z
- **DURATION:** 120001 ms

### EXP-178

- **ROOM:** shell
- **CONTROL:** health emergency report link/navigation
- **HOW DISCOVERED:** during candidate click exploration; page left Living Workspace
- **STATE:** ERROR
- **USER ACTION:** Observe navigation to /api/health/report?kind=emergency
- **EXPECTED:** Room controls stay inside Living Workspace; no silent leave to raw API report
- **ACTUAL:** `{"interruptedAt": "after EXP-177", "navigatedTo": "/api/health/report?kind=emergency", "note": "Clicking a discovered control navigated the top-level window to a raw health report URL, wiping the SPA session mid-exploration."}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-178.json`
- **BUG:** BUG-023
- **START TIME:** 2026-08-10T19:51:52.494Z
- **END TIME:** 2026-08-10T19:51:52.494Z
- **DURATION:** 0 ms

### EXP-179

- **ROOM:** chat
- **CONTROL:** research current info
- **HOW DISCOVERED:** chat workflow
- **STATE:** LOADING→SUCCESS
- **USER ACTION:** Ask for current Ubuntu LTS version; verify answer quality
- **EXPECTED:** Relevant current-info answer (not image-prompt garbage)
- **ACTUAL:** `{"tail": "Aria is here\nListening quietly\nA\n\nCome in. Sit down.\nI'm here whenever you are.\n\nYou\nWhat is the current latest Ubuntu LTS version?\nA\nThe current latest Ubuntu LTS version is 26.04 LTS (Resolute Raccoon). [1]\n\nSources\n[1] Ubuntu Releases \u2014 https://releases.ubuntu.com/"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-179.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:51:52.496Z
- **END TIME:** 2026-08-10T19:53:33.047Z
- **DURATION:** 100551 ms

### EXP-180

- **ROOM:** lock
- **CONTROL:** lock screen open/cancel
- **HOW DISCOVERED:** chrome / settings
- **STATE:** MODAL
- **USER ACTION:** Attempt lock UI if present; cancel without weakening security
- **EXPECTED:** Lock UI reachable or clearly absent; cancel returns
- **ACTUAL:** `{"lockBtn": false, "locked": false}`
- **STATUS:** **NOT TESTABLE**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-180.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:33.049Z
- **END TIME:** 2026-08-10T19:53:34.158Z
- **DURATION:** 1108 ms

### EXP-181

- **ROOM:** jobs
- **CONTROL:** job center / media queue
- **HOW DISCOVERED:** chrome / mission
- **STATE:** DEFAULT
- **USER ACTION:** Open jobs/queue UI if present
- **EXPECTED:** Job list/status visible
- **ACTUAL:** `{"btn": true, "preview": "Aria is here\nListening quietly\nA\n\nCome in. Sit down.\nI'm here whenever you are.\n\nYou\nWhat is the current latest Ubuntu LTS version?\nA\nThe current latest Ubuntu LTS version is 26.04 LTS (Resolute Raccoon). [1]\n\nSources\n[1] Ubuntu Releases \u2014 https://releases.ubuntu.com/"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-181.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:34.158Z
- **END TIME:** 2026-08-10T19:53:34.962Z
- **DURATION:** 804 ms

### EXP-182

- **ROOM:** onboarding
- **CONTROL:** What's New / tour
- **HOW DISCOVERED:** chrome / help
- **STATE:** MODAL
- **USER ACTION:** Open What's New or tour if present; close
- **EXPECTED:** Opens and can be dismissed without breaking prefs
- **ACTUAL:** `{"btn": true, "open": true}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-182.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:34.962Z
- **END TIME:** 2026-08-10T19:53:35.667Z
- **DURATION:** 705 ms

### EXP-183

- **ROOM:** audio
- **CONTROL:** Convert
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Convert
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Convert"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-183.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:35.670Z
- **END TIME:** 2026-08-10T19:53:37.077Z
- **DURATION:** 1407 ms

### EXP-184

- **ROOM:** audio
- **CONTROL:** Transcribe upload
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Transcribe upload
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Transcribe upload"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-184.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:37.078Z
- **END TIME:** 2026-08-10T19:53:38.481Z
- **DURATION:** 1403 ms

### EXP-185

- **ROOM:** audio
- **CONTROL:** Transcribe path
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Transcribe path
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Transcribe path"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-185.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:38.482Z
- **END TIME:** 2026-08-10T19:53:39.885Z
- **DURATION:** 1403 ms

### EXP-186

- **ROOM:** audio
- **CONTROL:** Generate speech
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate speech
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Generate speech"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-186.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:39.886Z
- **END TIME:** 2026-08-10T19:53:41.290Z
- **DURATION:** 1404 ms

### EXP-187

- **ROOM:** audio
- **CONTROL:** Generate + play
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate + play
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Generate + play"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-187.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:41.292Z
- **END TIME:** 2026-08-10T19:53:42.695Z
- **DURATION:** 1403 ms

### EXP-188

- **ROOM:** audio
- **CONTROL:** Upload
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Upload
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"fileInputPresent": true}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-188.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:42.696Z
- **END TIME:** 2026-08-10T19:53:43.497Z
- **DURATION:** 801 ms

### EXP-189

- **ROOM:** audio
- **CONTROL:** Transform genre
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Transform genre
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Transform genre"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-189.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:43.498Z
- **END TIME:** 2026-08-10T19:53:44.904Z
- **DURATION:** 1406 ms

### EXP-190

- **ROOM:** audio
- **CONTROL:** Generate song
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate song
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Generate song"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-190.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:44.906Z
- **END TIME:** 2026-08-10T19:53:46.312Z
- **DURATION:** 1406 ms

### EXP-191

- **ROOM:** automation
- **CONTROL:** NL draft
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: NL draft
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "NL draft"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-191.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:46.313Z
- **END TIME:** 2026-08-10T19:53:47.735Z
- **DURATION:** 1422 ms

### EXP-192

- **ROOM:** automation
- **CONTROL:** Propose team
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Propose team
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Propose team"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-192.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:47.736Z
- **END TIME:** 2026-08-10T19:53:49.140Z
- **DURATION:** 1404 ms

### EXP-193

- **ROOM:** automation
- **CONTROL:** Gallery
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Gallery
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Gallery"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-193.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:49.145Z
- **END TIME:** 2026-08-10T19:53:50.549Z
- **DURATION:** 1404 ms

### EXP-194

- **ROOM:** automation
- **CONTROL:** History
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: History
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "History"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-194.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:50.550Z
- **END TIME:** 2026-08-10T19:53:51.953Z
- **DURATION:** 1403 ms

### EXP-195

- **ROOM:** automation
- **CONTROL:** Search automation
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search automation
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Search automation"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-195.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:51.953Z
- **END TIME:** 2026-08-10T19:53:53.356Z
- **DURATION:** 1403 ms

### EXP-196

- **ROOM:** automation
- **CONTROL:** Natural language automation
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Natural language automation
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Natural language automation"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-196.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:53.357Z
- **END TIME:** 2026-08-10T19:53:54.760Z
- **DURATION:** 1403 ms

### EXP-197

- **ROOM:** automation
- **CONTROL:** Search pipelines
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search pipelines
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Search pipelines"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-197.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:54.760Z
- **END TIME:** 2026-08-10T19:53:56.163Z
- **DURATION:** 1403 ms

### EXP-198

- **ROOM:** automation
- **CONTROL:** on
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: on
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "on"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-198.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:56.164Z
- **END TIME:** 2026-08-10T19:53:57.567Z
- **DURATION:** 1403 ms

### EXP-199

- **ROOM:** browser
- **CONTROL:** Pause
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Pause
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Pause"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-199.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:57.568Z
- **END TIME:** 2026-08-10T19:53:58.973Z
- **DURATION:** 1405 ms

### EXP-200

- **ROOM:** browser
- **CONTROL:** Resume
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Resume
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Resume"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-200.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:53:58.974Z
- **END TIME:** 2026-08-10T19:54:00.377Z
- **DURATION:** 1403 ms

### EXP-201

- **ROOM:** browser
- **CONTROL:** Takeover
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Takeover
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Takeover"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-201.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:00.378Z
- **END TIME:** 2026-08-10T19:54:01.781Z
- **DURATION:** 1403 ms

### EXP-202

- **ROOM:** browser
- **CONTROL:** Stop
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Stop
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Stop"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-202.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:01.782Z
- **END TIME:** 2026-08-10T19:54:03.185Z
- **DURATION:** 1403 ms

### EXP-203

- **ROOM:** browser
- **CONTROL:** Save to Documents
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Save to Documents
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Save to Documents"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-203.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:03.186Z
- **END TIME:** 2026-08-10T19:54:04.590Z
- **DURATION:** 1404 ms

### EXP-204

- **ROOM:** browser
- **CONTROL:** Screenshot → Coding proposal
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Screenshot → Coding proposal
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-204.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:04.592Z
- **END TIME:** 2026-08-10T19:54:05.398Z
- **DURATION:** 806 ms

### EXP-205

- **ROOM:** browser
- **CONTROL:** Run
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Run
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Run"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-205.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:05.405Z
- **END TIME:** 2026-08-10T19:54:06.809Z
- **DURATION:** 1404 ms

### EXP-206

- **ROOM:** browser
- **CONTROL:** Queue in Job Center
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Queue in Job Center
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-206.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:06.810Z
- **END TIME:** 2026-08-10T19:54:07.611Z
- **DURATION:** 801 ms

### EXP-207

- **ROOM:** calendar
- **CONTROL:** 2026-08-01
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-01
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-01"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-207.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:07.612Z
- **END TIME:** 2026-08-10T19:54:09.017Z
- **DURATION:** 1405 ms

### EXP-208

- **ROOM:** calendar
- **CONTROL:** 2026-08-02
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-02
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-02"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-208.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:09.018Z
- **END TIME:** 2026-08-10T19:54:10.423Z
- **DURATION:** 1405 ms

### EXP-209

- **ROOM:** calendar
- **CONTROL:** 2026-08-03
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-03
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-03"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-209.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:10.424Z
- **END TIME:** 2026-08-10T19:54:11.834Z
- **DURATION:** 1410 ms

### EXP-210

- **ROOM:** calendar
- **CONTROL:** 2026-08-04
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-04
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-04"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-210.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:11.835Z
- **END TIME:** 2026-08-10T19:54:13.239Z
- **DURATION:** 1404 ms

### EXP-211

- **ROOM:** calendar
- **CONTROL:** 2026-08-05
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-05
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-05"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-211.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:13.240Z
- **END TIME:** 2026-08-10T19:54:14.644Z
- **DURATION:** 1404 ms

### EXP-212

- **ROOM:** calendar
- **CONTROL:** 2026-08-06
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-06
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-06"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-212.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:14.645Z
- **END TIME:** 2026-08-10T19:54:16.048Z
- **DURATION:** 1403 ms

### EXP-213

- **ROOM:** calendar
- **CONTROL:** 2026-08-07
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-07
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-07"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-213.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:16.049Z
- **END TIME:** 2026-08-10T19:54:17.453Z
- **DURATION:** 1404 ms

### EXP-214

- **ROOM:** calendar
- **CONTROL:** 2026-08-08
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 2026-08-08
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "2026-08-08"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-214.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:17.454Z
- **END TIME:** 2026-08-10T19:54:18.858Z
- **DURATION:** 1404 ms

### EXP-215

- **ROOM:** documents
- **CONTROL:** Open Projects
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Projects
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Open Projects"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-215.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:18.858Z
- **END TIME:** 2026-08-10T19:54:20.269Z
- **DURATION:** 1411 ms

### EXP-216

- **ROOM:** documents
- **CONTROL:** test
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: test
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-216.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:20.271Z
- **END TIME:** 2026-08-10T19:54:21.073Z
- **DURATION:** 802 ms

### EXP-217

- **ROOM:** documents
- **CONTROL:** resume
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: resume
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-217.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:21.075Z
- **END TIME:** 2026-08-10T19:54:21.877Z
- **DURATION:** 802 ms

### EXP-218

- **ROOM:** documents
- **CONTROL:** warranty
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: warranty
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-218.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:21.878Z
- **END TIME:** 2026-08-10T19:54:22.680Z
- **DURATION:** 802 ms

### EXP-219

- **ROOM:** documents
- **CONTROL:** readme
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: readme
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-219.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:22.680Z
- **END TIME:** 2026-08-10T19:54:23.482Z
- **DURATION:** 802 ms

### EXP-220

- **ROOM:** documents
- **CONTROL:** aria
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: aria
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-220.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:23.483Z
- **END TIME:** 2026-08-10T19:54:24.284Z
- **DURATION:** 801 ms

### EXP-221

- **ROOM:** documents
- **CONTROL:** memory
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: memory
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-221.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:24.285Z
- **END TIME:** 2026-08-10T19:54:25.088Z
- **DURATION:** 803 ms

### EXP-222

- **ROOM:** documents
- **CONTROL:** ship
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: ship
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-222.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:25.089Z
- **END TIME:** 2026-08-10T19:54:25.891Z
- **DURATION:** 802 ms

### EXP-223

- **ROOM:** flytying
- **CONTROL:** Hide
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Hide
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Hide"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-223.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:25.892Z
- **END TIME:** 2026-08-10T19:54:27.296Z
- **DURATION:** 1404 ms

### EXP-224

- **ROOM:** flytying
- **CONTROL:** Add
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Add
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Add"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-224.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:27.297Z
- **END TIME:** 2026-08-10T19:54:28.700Z
- **DURATION:** 1403 ms

### EXP-225

- **ROOM:** flytying
- **CONTROL:** Save list
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Save list
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Save list"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-225.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:28.702Z
- **END TIME:** 2026-08-10T19:54:30.105Z
- **DURATION:** 1403 ms

### EXP-226

- **ROOM:** flytying
- **CONTROL:** What ▲
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: What ▲
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-226.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:30.107Z
- **END TIME:** 2026-08-10T19:54:30.910Z
- **DURATION:** 803 ms

### EXP-227

- **ROOM:** flytying
- **CONTROL:** Color
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Color
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Color"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-227.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:30.911Z
- **END TIME:** 2026-08-10T19:54:32.315Z
- **DURATION:** 1404 ms

### EXP-228

- **ROOM:** flytying
- **CONTROL:** Size
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Size
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Size"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-228.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:32.316Z
- **END TIME:** 2026-08-10T19:54:33.719Z
- **DURATION:** 1403 ms

### EXP-229

- **ROOM:** flytying
- **CONTROL:** Brand
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Brand
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Brand"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-229.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:33.720Z
- **END TIME:** 2026-08-10T19:54:35.123Z
- **DURATION:** 1403 ms

### EXP-230

- **ROOM:** flytying
- **CONTROL:** Edit
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Edit
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-230.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:35.124Z
- **END TIME:** 2026-08-10T19:54:35.926Z
- **DURATION:** 802 ms

### EXP-231

- **ROOM:** gallery
- **CONTROL:** Simple
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Simple
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Simple"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-231.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:35.927Z
- **END TIME:** 2026-08-10T19:54:37.331Z
- **DURATION:** 1404 ms

### EXP-232

- **ROOM:** gallery
- **CONTROL:** Expert
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Expert
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Expert"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-232.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:37.332Z
- **END TIME:** 2026-08-10T19:54:38.735Z
- **DURATION:** 1403 ms

### EXP-233

- **ROOM:** gallery
- **CONTROL:** Search
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-233.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:38.736Z
- **END TIME:** 2026-08-10T19:54:40.140Z
- **DURATION:** 1404 ms

### EXP-234

- **ROOM:** gallery
- **CONTROL:** → Video storyboard
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: → Video storyboard
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "\u2192 Video storyboard"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-234.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:40.141Z
- **END TIME:** 2026-08-10T19:54:41.549Z
- **DURATION:** 1408 ms

### EXP-235

- **ROOM:** gallery
- **CONTROL:** New collection
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: New collection
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "New collection"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-235.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:41.550Z
- **END TIME:** 2026-08-10T19:54:42.957Z
- **DURATION:** 1407 ms

### EXP-236

- **ROOM:** gallery
- **CONTROL:** Opt-in Vision caption
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Opt-in Vision caption
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-236.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:54:42.958Z
- **END TIME:** 2026-08-10T19:54:43.759Z
- **DURATION:** 801 ms

### EXP-237

- **ROOM:** gallery
- **CONTROL:** Describe
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Describe
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Describe"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-237.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:43.760Z
- **END TIME:** 2026-08-10T19:54:45.166Z
- **DURATION:** 1406 ms

### EXP-238

- **ROOM:** gallery
- **CONTROL:** Save caption to Documents
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Save caption to Documents
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Save caption to Documents"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-238.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:45.168Z
- **END TIME:** 2026-08-10T19:54:46.575Z
- **DURATION:** 1407 ms

### EXP-239

- **ROOM:** health
- **CONTROL:** Recovery
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Recovery
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Recovery"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-239.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:46.576Z
- **END TIME:** 2026-08-10T19:54:47.980Z
- **DURATION:** 1404 ms

### EXP-240

- **ROOM:** health
- **CONTROL:** History
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: History
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "History"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-240.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:47.981Z
- **END TIME:** 2026-08-10T19:54:49.385Z
- **DURATION:** 1404 ms

### EXP-241

- **ROOM:** health
- **CONTROL:** Journal
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Journal
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-241.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:49.386Z
- **END TIME:** 2026-08-10T19:54:50.789Z
- **DURATION:** 1403 ms

### EXP-242

- **ROOM:** health
- **CONTROL:** Knowledge
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Knowledge
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Knowledge"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-242.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:50.790Z
- **END TIME:** 2026-08-10T19:54:52.193Z
- **DURATION:** 1403 ms

### EXP-243

- **ROOM:** health
- **CONTROL:** Providers
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Providers
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Providers"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-243.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:52.194Z
- **END TIME:** 2026-08-10T19:54:53.598Z
- **DURATION:** 1404 ms

### EXP-244

- **ROOM:** health
- **CONTROL:** Procedures
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Procedures
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Procedures"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-244.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:53.600Z
- **END TIME:** 2026-08-10T19:54:55.003Z
- **DURATION:** 1403 ms

### EXP-245

- **ROOM:** health
- **CONTROL:** Family
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Family
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Family"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-245.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:55.004Z
- **END TIME:** 2026-08-10T19:54:56.407Z
- **DURATION:** 1403 ms

### EXP-246

- **ROOM:** health
- **CONTROL:** Preventive
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Preventive
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Preventive"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-246.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:56.408Z
- **END TIME:** 2026-08-10T19:54:57.811Z
- **DURATION:** 1403 ms

### EXP-247

- **ROOM:** home_automation
- **CONTROL:** haSceneSaveBtn
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: haSceneSaveBtn
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "haSceneSaveBtn"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-247.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:57.812Z
- **END TIME:** 2026-08-10T19:54:59.219Z
- **DURATION:** 1407 ms

### EXP-248

- **ROOM:** home_automation
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-248.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:54:59.220Z
- **END TIME:** 2026-08-10T19:55:00.629Z
- **DURATION:** 1409 ms

### EXP-249

- **ROOM:** home_automation
- **CONTROL:** Discover Kasa
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Discover Kasa
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Discover Kasa"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-249.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:00.630Z
- **END TIME:** 2026-08-10T19:55:02.035Z
- **DURATION:** 1405 ms

### EXP-250

- **ROOM:** home_automation
- **CONTROL:** Search Smart Home entities
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search Smart Home entities
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Search Smart Home entities"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-250.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:02.037Z
- **END TIME:** 2026-08-10T19:55:03.441Z
- **DURATION:** 1404 ms

### EXP-251

- **ROOM:** home_automation
- **CONTROL:** http://127.0.0.1:8123
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: http://127.0.0.1:8123
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "http://127.0.0.1:8123"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-251.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:03.442Z
- **END TIME:** 2026-08-10T19:55:04.846Z
- **DURATION:** 1404 ms

### EXP-252

- **ROOM:** home_automation
- **CONTROL:** scene.leaving (optional)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: scene.leaving (optional)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-252.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:04.847Z
- **END TIME:** 2026-08-10T19:55:05.650Z
- **DURATION:** 803 ms

### EXP-253

- **ROOM:** home_automation
- **CONTROL:** scene.leaving
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: scene.leaving
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-253.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:05.651Z
- **END TIME:** 2026-08-10T19:55:06.454Z
- **DURATION:** 803 ms

### EXP-254

- **ROOM:** home_automation
- **CONTROL:** Paste token
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Paste token
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-254.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:06.455Z
- **END TIME:** 2026-08-10T19:55:07.259Z
- **DURATION:** 804 ms

### EXP-255

- **ROOM:** integrity
- **CONTROL:** More
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: More
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "More"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-255.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:07.260Z
- **END TIME:** 2026-08-10T19:55:08.664Z
- **DURATION:** 1404 ms

### EXP-256

- **ROOM:** journal
- **CONTROL:** Daily
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Daily
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Daily"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-256.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:08.665Z
- **END TIME:** 2026-08-10T19:55:10.070Z
- **DURATION:** 1405 ms

### EXP-257

- **ROOM:** journal
- **CONTROL:** Weekly
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Weekly
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Weekly"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-257.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:10.073Z
- **END TIME:** 2026-08-10T19:55:11.477Z
- **DURATION:** 1404 ms

### EXP-258

- **ROOM:** journal
- **CONTROL:** Monthly
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Monthly
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Monthly"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-258.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:11.478Z
- **END TIME:** 2026-08-10T19:55:12.881Z
- **DURATION:** 1403 ms

### EXP-259

- **ROOM:** journal
- **CONTROL:** Habits
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Habits
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Habits"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-259.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:12.883Z
- **END TIME:** 2026-08-10T19:55:14.286Z
- **DURATION:** 1403 ms

### EXP-260

- **ROOM:** journal
- **CONTROL:** Wellness
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Wellness
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Wellness"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-260.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:14.287Z
- **END TIME:** 2026-08-10T19:55:15.691Z
- **DURATION:** 1404 ms

### EXP-261

- **ROOM:** journal
- **CONTROL:** Future
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Future
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Future"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-261.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:15.693Z
- **END TIME:** 2026-08-10T19:55:17.096Z
- **DURATION:** 1403 ms

### EXP-262

- **ROOM:** journal
- **CONTROL:** Index
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Index
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Index"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-262.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:17.099Z
- **END TIME:** 2026-08-10T19:55:18.502Z
- **DURATION:** 1403 ms

### EXP-263

- **ROOM:** journal
- **CONTROL:** Collections
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Collections
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Collections"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-263.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:18.503Z
- **END TIME:** 2026-08-10T19:55:19.906Z
- **DURATION:** 1403 ms

### EXP-264

- **ROOM:** maker
- **CONTROL:** Detach maker lab panel
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Detach maker lab panel
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Detach maker lab panel"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-264.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:19.908Z
- **END TIME:** 2026-08-10T19:55:21.315Z
- **DURATION:** 1407 ms

### EXP-265

- **ROOM:** maker
- **CONTROL:** Generate
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-265.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:21.316Z
- **END TIME:** 2026-08-10T19:55:22.118Z
- **DURATION:** 802 ms

### EXP-266

- **ROOM:** maker
- **CONTROL:** Iterate
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Iterate
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-266.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:22.119Z
- **END TIME:** 2026-08-10T19:55:22.920Z
- **DURATION:** 801 ms

### EXP-267

- **ROOM:** maker
- **CONTROL:** Hello cube
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Hello cube
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-267.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:22.922Z
- **END TIME:** 2026-08-10T19:55:23.724Z
- **DURATION:** 802 ms

### EXP-268

- **ROOM:** maker
- **CONTROL:** Slice
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Slice
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-268.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:23.725Z
- **END TIME:** 2026-08-10T19:55:24.527Z
- **DURATION:** 802 ms

### EXP-269

- **ROOM:** maker
- **CONTROL:** Download STL
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Download STL
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-269.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:24.528Z
- **END TIME:** 2026-08-10T19:55:25.330Z
- **DURATION:** 802 ms

### EXP-270

- **ROOM:** maker
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-270.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:25.332Z
- **END TIME:** 2026-08-10T19:55:26.133Z
- **DURATION:** 801 ms

### EXP-271

- **ROOM:** maker
- **CONTROL:** Gallery
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Gallery
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-271.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:26.135Z
- **END TIME:** 2026-08-10T19:55:26.936Z
- **DURATION:** 801 ms

### EXP-272

- **ROOM:** meme
- **CONTROL:** Generate in chat
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate in chat
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Generate in chat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-272.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:26.937Z
- **END TIME:** 2026-08-10T19:55:28.368Z
- **DURATION:** 1431 ms

### EXP-273

- **ROOM:** meme
- **CONTROL:** Open Gallery
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Gallery
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-273.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:28.369Z
- **END TIME:** 2026-08-10T19:55:29.183Z
- **DURATION:** 814 ms

### EXP-274

- **ROOM:** meme
- **CONTROL:** Open Video Studio
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Video Studio
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-274.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:29.184Z
- **END TIME:** 2026-08-10T19:55:29.986Z
- **DURATION:** 802 ms

### EXP-275

- **ROOM:** meme
- **CONTROL:** Quick preview (text only)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Quick preview (text only)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Quick preview (text only)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-275.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:29.987Z
- **END TIME:** 2026-08-10T19:55:31.394Z
- **DURATION:** 1407 ms

### EXP-276

- **ROOM:** meme
- **CONTROL:** Generate meme
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate meme
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Generate meme"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-276.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:31.395Z
- **END TIME:** 2026-08-10T19:55:32.798Z
- **DURATION:** 1403 ms

### EXP-277

- **ROOM:** meme
- **CONTROL:** e.g. when ARIA finally works on the first try
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: e.g. when ARIA finally works on the first try
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-277.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:32.799Z
- **END TIME:** 2026-08-10T19:55:33.600Z
- **DURATION:** 801 ms

### EXP-278

- **ROOM:** meme
- **CONTROL:** WHEN YOU RESTART
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: WHEN YOU RESTART
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-278.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:33.603Z
- **END TIME:** 2026-08-10T19:55:34.404Z
- **DURATION:** 801 ms

### EXP-279

- **ROOM:** meme
- **CONTROL:** AND IT ACTUALLY HELPS
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: AND IT ACTUALLY HELPS
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-279.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:34.406Z
- **END TIME:** 2026-08-10T19:55:35.208Z
- **DURATION:** 802 ms

### EXP-280

- **ROOM:** memory
- **CONTROL:** Search (/)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search (/)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-280.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:35.209Z
- **END TIME:** 2026-08-10T19:55:36.014Z
- **DURATION:** 805 ms

### EXP-281

- **ROOM:** memory
- **CONTROL:** New memory (N)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: New memory (N)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-281.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:36.015Z
- **END TIME:** 2026-08-10T19:55:36.818Z
- **DURATION:** 803 ms

### EXP-282

- **ROOM:** memory
- **CONTROL:** Briefing
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Briefing
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Briefing"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-282.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:36.819Z
- **END TIME:** 2026-08-10T19:55:38.222Z
- **DURATION:** 1403 ms

### EXP-283

- **ROOM:** memory
- **CONTROL:** Assist
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Assist
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Assist"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-283.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:38.224Z
- **END TIME:** 2026-08-10T19:55:39.628Z
- **DURATION:** 1404 ms

### EXP-284

- **ROOM:** memory
- **CONTROL:** ?
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: ?
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "?"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-284.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:39.629Z
- **END TIME:** 2026-08-10T19:55:41.033Z
- **DURATION:** 1404 ms

### EXP-285

- **ROOM:** memory
- **CONTROL:** Update profile
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Update profile
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Update profile"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-285.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:41.034Z
- **END TIME:** 2026-08-10T19:55:42.438Z
- **DURATION:** 1404 ms

### EXP-286

- **ROOM:** memory
- **CONTROL:** Edit answers
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Edit answers
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Edit answers"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-286.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:42.440Z
- **END TIME:** 2026-08-10T19:55:43.843Z
- **DURATION:** 1403 ms

### EXP-287

- **ROOM:** memory
- **CONTROL:** Save preferences
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Save preferences
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Save preferences"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-287.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:43.844Z
- **END TIME:** 2026-08-10T19:55:45.248Z
- **DURATION:** 1404 ms

### EXP-288

- **ROOM:** mission
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-288.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:45.249Z
- **END TIME:** 2026-08-10T19:55:46.654Z
- **DURATION:** 1404 ms

### EXP-289

- **ROOM:** mission
- **CONTROL:** Open Job Center
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Job Center
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Open Job Center"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-289.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:46.654Z
- **END TIME:** 2026-08-10T19:55:48.059Z
- **DURATION:** 1405 ms

### EXP-290

- **ROOM:** mission
- **CONTROL:** Open Notifications (Activity Center inbox)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Notifications (Activity Center inbox)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-290.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:48.060Z
- **END TIME:** 2026-08-10T19:55:48.862Z
- **DURATION:** 802 ms

### EXP-291

- **ROOM:** mission
- **CONTROL:** Open Chat
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Chat
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-291.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:48.864Z
- **END TIME:** 2026-08-10T19:55:49.666Z
- **DURATION:** 802 ms

### EXP-292

- **ROOM:** mission
- **CONTROL:** Open System audit
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open System audit
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-292.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:49.668Z
- **END TIME:** 2026-08-10T19:55:50.470Z
- **DURATION:** 802 ms

### EXP-293

- **ROOM:** mission
- **CONTROL:** Open Home
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Home
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-293.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:50.471Z
- **END TIME:** 2026-08-10T19:55:51.273Z
- **DURATION:** 802 ms

### EXP-294

- **ROOM:** mission
- **CONTROL:** Overview
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Overview
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Overview"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-294.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:51.274Z
- **END TIME:** 2026-08-10T19:55:52.679Z
- **DURATION:** 1405 ms

### EXP-295

- **ROOM:** mission
- **CONTROL:** Routing
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Routing
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Routing"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-295.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:52.680Z
- **END TIME:** 2026-08-10T19:55:54.084Z
- **DURATION:** 1404 ms

### EXP-296

- **ROOM:** planner
- **CONTROL:** Notes, reflections, logs
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Notes, reflections, logs
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-296.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:54.086Z
- **END TIME:** 2026-08-10T19:55:54.888Z
- **DURATION:** 802 ms

### EXP-297

- **ROOM:** planner
- **CONTROL:** Scheduled commitments
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Scheduled commitments
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-297.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:54.890Z
- **END TIME:** 2026-08-10T19:55:55.692Z
- **DURATION:** 802 ms

### EXP-298

- **ROOM:** planner
- **CONTROL:** Documents
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Documents
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Documents"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-298.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:55.693Z
- **END TIME:** 2026-08-10T19:55:57.105Z
- **DURATION:** 1412 ms

### EXP-299

- **ROOM:** planner
- **CONTROL:** Add
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Add
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Add"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-299.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:55:57.106Z
- **END TIME:** 2026-08-10T19:55:58.513Z
- **DURATION:** 1407 ms

### EXP-300

- **ROOM:** planner
- **CONTROL:** Add task
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Add task
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-300.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:58.515Z
- **END TIME:** 2026-08-10T19:55:59.316Z
- **DURATION:** 801 ms

### EXP-301

- **ROOM:** planner
- **CONTROL:** Ask Chat
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Ask Chat
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-301.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:55:59.317Z
- **END TIME:** 2026-08-10T19:56:00.119Z
- **DURATION:** 802 ms

### EXP-302

- **ROOM:** planner
- **CONTROL:** Open Journal
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Journal
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-302.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:00.120Z
- **END TIME:** 2026-08-10T19:56:00.922Z
- **DURATION:** 802 ms

### EXP-303

- **ROOM:** planner
- **CONTROL:** Start
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Start
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Start"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-303.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:00.923Z
- **END TIME:** 2026-08-10T19:56:02.330Z
- **DURATION:** 1407 ms

### EXP-304

- **ROOM:** presence
- **CONTROL:** Open Security
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Security
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-304.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:02.331Z
- **END TIME:** 2026-08-10T19:56:03.141Z
- **DURATION:** 810 ms

### EXP-305

- **ROOM:** presence
- **CONTROL:** Open Voice
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Voice
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-305.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:03.142Z
- **END TIME:** 2026-08-10T19:56:03.944Z
- **DURATION:** 802 ms

### EXP-306

- **ROOM:** presence
- **CONTROL:** Start camera
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Start camera
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Start camera"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-306.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:03.945Z
- **END TIME:** 2026-08-10T19:56:05.357Z
- **DURATION:** 1412 ms

### EXP-307

- **ROOM:** presence
- **CONTROL:** Stop
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Stop
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Stop"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-307.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:05.360Z
- **END TIME:** 2026-08-10T19:56:06.763Z
- **DURATION:** 1403 ms

### EXP-308

- **ROOM:** presence
- **CONTROL:** Enroll face
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Enroll face
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Enroll face"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-308.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:06.764Z
- **END TIME:** 2026-08-10T19:56:08.170Z
- **DURATION:** 1406 ms

### EXP-309

- **ROOM:** presence
- **CONTROL:** Calibrate gestures
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Calibrate gestures
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Calibrate gestures"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-309.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:08.171Z
- **END TIME:** 2026-08-10T19:56:09.576Z
- **DURATION:** 1405 ms

### EXP-310

- **ROOM:** presence
- **CONTROL:** Off Preview only Control — pinch click, fist drag panels CPU-only (low FPS)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Off Preview only Control — pinch click, fist drag panels CPU-only (low FPS)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Off Preview only Control \u2014 pinch click, fist drag panels CPU-only (low FPS)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-310.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:09.578Z
- **END TIME:** 2026-08-10T19:56:10.984Z
- **DURATION:** 1406 ms

### EXP-311

- **ROOM:** projects
- **CONTROL:** Shortcuts
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Shortcuts
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-311.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:10.990Z
- **END TIME:** 2026-08-10T19:56:11.816Z
- **DURATION:** 826 ms

### EXP-312

- **ROOM:** projects
- **CONTROL:** Create
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Create
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Create"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-312.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:11.817Z
- **END TIME:** 2026-08-10T19:56:13.224Z
- **DURATION:** 1407 ms

### EXP-313

- **ROOM:** projects
- **CONTROL:** Import
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Import
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Import"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-313.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:13.228Z
- **END TIME:** 2026-08-10T19:56:14.631Z
- **DURATION:** 1403 ms

### EXP-314

- **ROOM:** projects
- **CONTROL:** Search projects
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search projects
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Search projects"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-314.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:14.633Z
- **END TIME:** 2026-08-10T19:56:16.036Z
- **DURATION:** 1403 ms

### EXP-315

- **ROOM:** projects
- **CONTROL:** New project name
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: New project name
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "New project name"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-315.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:16.038Z
- **END TIME:** 2026-08-10T19:56:17.441Z
- **DURATION:** 1403 ms

### EXP-316

- **ROOM:** projects
- **CONTROL:** Description
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Description
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Description"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-316.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:17.443Z
- **END TIME:** 2026-08-10T19:56:18.847Z
- **DURATION:** 1404 ms

### EXP-317

- **ROOM:** projects
- **CONTROL:** Git path
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Git path
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Git path"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-317.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:18.848Z
- **END TIME:** 2026-08-10T19:56:20.252Z
- **DURATION:** 1404 ms

### EXP-318

- **ROOM:** providers
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-318.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:20.254Z
- **END TIME:** 2026-08-10T19:56:21.671Z
- **DURATION:** 1417 ms

### EXP-319

- **ROOM:** providers
- **CONTROL:** Provider / VRAM health
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Provider / VRAM health
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-319.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:21.679Z
- **END TIME:** 2026-08-10T19:56:22.482Z
- **DURATION:** 803 ms

### EXP-320

- **ROOM:** repair
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-320.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:22.484Z
- **END TIME:** 2026-08-10T19:56:23.893Z
- **DURATION:** 1409 ms

### EXP-321

- **ROOM:** repair
- **CONTROL:** Open Job Center
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Job Center
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Open Job Center"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-321.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:23.894Z
- **END TIME:** 2026-08-10T19:56:25.301Z
- **DURATION:** 1407 ms

### EXP-322

- **ROOM:** repair
- **CONTROL:** Open Notifications (Activity Center inbox)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Notifications (Activity Center inbox)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-322.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:25.303Z
- **END TIME:** 2026-08-10T19:56:26.108Z
- **DURATION:** 805 ms

### EXP-323

- **ROOM:** repair
- **CONTROL:** Open Chat
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Chat
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-323.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:26.110Z
- **END TIME:** 2026-08-10T19:56:26.913Z
- **DURATION:** 803 ms

### EXP-324

- **ROOM:** repair
- **CONTROL:** Open System audit
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open System audit
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-324.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:26.914Z
- **END TIME:** 2026-08-10T19:56:27.716Z
- **DURATION:** 802 ms

### EXP-325

- **ROOM:** repair
- **CONTROL:** Open Home
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Home
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-325.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:27.717Z
- **END TIME:** 2026-08-10T19:56:28.520Z
- **DURATION:** 803 ms

### EXP-326

- **ROOM:** repair
- **CONTROL:** Overview
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Overview
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Overview"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-326.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:28.524Z
- **END TIME:** 2026-08-10T19:56:29.932Z
- **DURATION:** 1408 ms

### EXP-327

- **ROOM:** repair
- **CONTROL:** Routing
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Routing
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Routing"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-327.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:29.935Z
- **END TIME:** 2026-08-10T19:56:31.341Z
- **DURATION:** 1406 ms

### EXP-328

- **ROOM:** search
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-328.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:31.343Z
- **END TIME:** 2026-08-10T19:56:32.754Z
- **DURATION:** 1411 ms

### EXP-329

- **ROOM:** search
- **CONTROL:** Save search
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Save search
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Save search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-329.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:32.755Z
- **END TIME:** 2026-08-10T19:56:34.160Z
- **DURATION:** 1405 ms

### EXP-330

- **ROOM:** search
- **CONTROL:** Diagnostics
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Diagnostics
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Diagnostics"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-330.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:34.164Z
- **END TIME:** 2026-08-10T19:56:35.571Z
- **DURATION:** 1407 ms

### EXP-331

- **ROOM:** search
- **CONTROL:** Search
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-331.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:35.572Z
- **END TIME:** 2026-08-10T19:56:36.976Z
- **DURATION:** 1404 ms

### EXP-332

- **ROOM:** search
- **CONTROL:** Clear history
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Clear history
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Clear history"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-332.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:36.978Z
- **END TIME:** 2026-08-10T19:56:38.381Z
- **DURATION:** 1403 ms

### EXP-333

- **ROOM:** search
- **CONTROL:** Search documents, memory, code, graph, planner…
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search documents, memory, code, graph, planner…
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-333.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:38.384Z
- **END TIME:** 2026-08-10T19:56:39.186Z
- **DURATION:** 802 ms

### EXP-334

- **ROOM:** search
- **CONTROL:** Browse or answer mode
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Browse or answer mode
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Browse or answer mode"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-334.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:39.187Z
- **END TIME:** 2026-08-10T19:56:40.590Z
- **DURATION:** 1403 ms

### EXP-335

- **ROOM:** search
- **CONTROL:** Code search mode
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Code search mode
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Code search mode"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-335.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:40.592Z
- **END TIME:** 2026-08-10T19:56:41.995Z
- **DURATION:** 1403 ms

### EXP-336

- **ROOM:** security
- **CONTROL:** Open Presence
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Presence
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-336.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:41.996Z
- **END TIME:** 2026-08-10T19:56:42.799Z
- **DURATION:** 803 ms

### EXP-337

- **ROOM:** security
- **CONTROL:** Open Voice
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Voice
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-337.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:42.801Z
- **END TIME:** 2026-08-10T19:56:43.603Z
- **DURATION:** 802 ms

### EXP-338

- **ROOM:** security
- **CONTROL:** Set PIN
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Set PIN
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Set PIN"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-338.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:43.604Z
- **END TIME:** 2026-08-10T19:56:45.008Z
- **DURATION:** 1404 ms

### EXP-339

- **ROOM:** security
- **CONTROL:** Lock now
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Lock now
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Lock now"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-339.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:45.009Z
- **END TIME:** 2026-08-10T19:56:46.418Z
- **DURATION:** 1409 ms

### EXP-340

- **ROOM:** security
- **CONTROL:** Presence
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Presence
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Presence"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-340.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:46.421Z
- **END TIME:** 2026-08-10T19:56:47.831Z
- **DURATION:** 1410 ms

### EXP-341

- **ROOM:** security
- **CONTROL:** 4–6 digit PIN
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 4–6 digit PIN
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-341.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:47.833Z
- **END TIME:** 2026-08-10T19:56:48.635Z
- **DURATION:** 802 ms

### EXP-342

- **ROOM:** settings
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-342.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:48.637Z
- **END TIME:** 2026-08-10T19:56:50.047Z
- **DURATION:** 1410 ms

### EXP-343

- **ROOM:** settings
- **CONTROL:** Voice & Chat
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Voice & Chat
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Voice & Chat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-343.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:50.051Z
- **END TIME:** 2026-08-10T19:56:51.458Z
- **DURATION:** 1407 ms

### EXP-344

- **ROOM:** settings
- **CONTROL:** Diagnostics
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Diagnostics
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Diagnostics"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-344.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:51.459Z
- **END TIME:** 2026-08-10T19:56:52.863Z
- **DURATION:** 1404 ms

### EXP-345

- **ROOM:** settings
- **CONTROL:** Export
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Export
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Export"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-345.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:52.864Z
- **END TIME:** 2026-08-10T19:56:54.268Z
- **DURATION:** 1404 ms

### EXP-346

- **ROOM:** settings
- **CONTROL:** Search
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Search
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-346.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:54.271Z
- **END TIME:** 2026-08-10T19:56:55.680Z
- **DURATION:** 1409 ms

### EXP-347

- **ROOM:** settings
- **CONTROL:** Reset appearance
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Reset appearance
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Reset appearance"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-347.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:55.683Z
- **END TIME:** 2026-08-10T19:56:57.089Z
- **DURATION:** 1406 ms

### EXP-348

- **ROOM:** settings
- **CONTROL:** Activate
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Activate
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Activate"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-348.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:57.091Z
- **END TIME:** 2026-08-10T19:56:58.496Z
- **DURATION:** 1405 ms

### EXP-349

- **ROOM:** settings
- **CONTROL:** Save profile
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Save profile
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Save profile"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-349.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:56:58.498Z
- **END TIME:** 2026-08-10T19:56:59.944Z
- **DURATION:** 1446 ms

### EXP-350

- **ROOM:** video
- **CONTROL:** Open Gallery
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Gallery
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-350.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:56:59.948Z
- **END TIME:** 2026-08-10T19:57:00.752Z
- **DURATION:** 804 ms

### EXP-351

- **ROOM:** video
- **CONTROL:** Open Meme Studio
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Meme Studio
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-351.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:57:00.753Z
- **END TIME:** 2026-08-10T19:57:01.557Z
- **DURATION:** 804 ms

### EXP-352

- **ROOM:** video
- **CONTROL:** Mission Control
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Mission Control
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Mission Control"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-352.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:01.564Z
- **END TIME:** 2026-08-10T19:57:02.983Z
- **DURATION:** 1419 ms

### EXP-353

- **ROOM:** video
- **CONTROL:** Generate
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Generate"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-353.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:02.984Z
- **END TIME:** 2026-08-10T19:57:04.392Z
- **DURATION:** 1408 ms

### EXP-354

- **ROOM:** video
- **CONTROL:** Preview enhance
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Preview enhance
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Preview enhance"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-354.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:04.393Z
- **END TIME:** 2026-08-10T19:57:05.802Z
- **DURATION:** 1409 ms

### EXP-355

- **ROOM:** video
- **CONTROL:** Advanced
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Advanced
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Advanced"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-355.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:05.803Z
- **END TIME:** 2026-08-10T19:57:07.208Z
- **DURATION:** 1405 ms

### EXP-356

- **ROOM:** video
- **CONTROL:** Generate another
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Generate another
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Generate another"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-356.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:07.213Z
- **END TIME:** 2026-08-10T19:57:08.620Z
- **DURATION:** 1407 ms

### EXP-357

- **ROOM:** video
- **CONTROL:** Simple
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Simple
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Simple"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-357.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:08.621Z
- **END TIME:** 2026-08-10T19:57:10.024Z
- **DURATION:** 1403 ms

### EXP-358

- **ROOM:** vision
- **CONTROL:** Chat attach
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Chat attach
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Chat attach"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-358.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:10.028Z
- **END TIME:** 2026-08-10T19:57:11.452Z
- **DURATION:** 1424 ms

### EXP-359

- **ROOM:** vision
- **CONTROL:** Gallery
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Gallery
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Gallery"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-359.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:11.453Z
- **END TIME:** 2026-08-10T19:57:12.867Z
- **DURATION:** 1414 ms

### EXP-360

- **ROOM:** vision
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-360.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:12.868Z
- **END TIME:** 2026-08-10T19:57:14.273Z
- **DURATION:** 1405 ms

### EXP-361

- **ROOM:** vision
- **CONTROL:** Apply profile
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Apply profile
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Apply profile"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-361.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:14.274Z
- **END TIME:** 2026-08-10T19:57:15.680Z
- **DURATION:** 1406 ms

### EXP-362

- **ROOM:** vision
- **CONTROL:** Speak OCR (Voice)
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Speak OCR (Voice)
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Speak OCR (Voice)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-362.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:15.684Z
- **END TIME:** 2026-08-10T19:57:17.093Z
- **DURATION:** 1408 ms

### EXP-363

- **ROOM:** vision
- **CONTROL:** Refresh batch
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh batch
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh batch"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-363.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:17.095Z
- **END TIME:** 2026-08-10T19:57:18.503Z
- **DURATION:** 1408 ms

### EXP-364

- **ROOM:** vision
- **CONTROL:** Vision image or PDF page path for OCR
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Vision image or PDF page path for OCR
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Vision image or PDF page path for OCR"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-364.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:18.505Z
- **END TIME:** 2026-08-10T19:57:19.909Z
- **DURATION:** 1404 ms

### EXP-365

- **ROOM:** vision
- **CONTROL:** Compare image path B
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Compare image path B
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Compare image path B"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-365.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:19.911Z
- **END TIME:** 2026-08-10T19:57:21.314Z
- **DURATION:** 1403 ms

### EXP-366

- **ROOM:** voice
- **CONTROL:** Open Audio studio
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Audio studio
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-366.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:57:21.315Z
- **END TIME:** 2026-08-10T19:57:22.118Z
- **DURATION:** 803 ms

### EXP-367

- **ROOM:** voice
- **CONTROL:** Open Presence
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Open Presence
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-367.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:57:22.120Z
- **END TIME:** 2026-08-10T19:57:22.921Z
- **DURATION:** 801 ms

### EXP-368

- **ROOM:** voice
- **CONTROL:** Apply profile
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Apply profile
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Apply profile"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-368.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:22.923Z
- **END TIME:** 2026-08-10T19:57:24.327Z
- **DURATION:** 1404 ms

### EXP-369

- **ROOM:** voice
- **CONTROL:** Save settings
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Save settings
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Save settings"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-369.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:24.334Z
- **END TIME:** 2026-08-10T19:57:25.740Z
- **DURATION:** 1406 ms

### EXP-370

- **ROOM:** voice
- **CONTROL:** Refresh
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Refresh
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-370.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:25.746Z
- **END TIME:** 2026-08-10T19:57:27.150Z
- **DURATION:** 1404 ms

### EXP-371

- **ROOM:** voice
- **CONTROL:** Run recovery advisor
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Run recovery advisor
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-371.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:57:27.152Z
- **END TIME:** 2026-08-10T19:57:27.954Z
- **DURATION:** 802 ms

### EXP-372

- **ROOM:** voice
- **CONTROL:** Toggle cloud live
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: Toggle cloud live
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-372.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:57:27.960Z
- **END TIME:** 2026-08-10T19:57:28.762Z
- **DURATION:** 802 ms

### EXP-373

- **ROOM:** voice
- **CONTROL:** 220
- **HOW DISCOVERED:** resume candidate inventory
- **STATE:** DEFAULT
- **USER ACTION:** Click/activate control: 220
- **EXPECTED:** Responds without leaving SPA / crash
- **ACTUAL:** `{"label": "220"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-373.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:28.764Z
- **END TIME:** 2026-08-10T19:57:30.168Z
- **DURATION:** 1404 ms

### EXP-374

- **ROOM:** chat
- **CONTROL:** Skip — open UI now
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Skip — open UI now
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Skip \u2014 open UI now"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-374.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:06.208Z
- **END TIME:** 2026-08-10T19:58:07.413Z
- **DURATION:** 1205 ms

### EXP-375

- **ROOM:** chat
- **CONTROL:** Menu
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Menu
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Menu"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-375.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:07.414Z
- **END TIME:** 2026-08-10T19:58:08.618Z
- **DURATION:** 1204 ms

### EXP-376

- **ROOM:** chat
- **CONTROL:** Wake: —
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Wake: —
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Wake: \u2014"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-376.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:08.620Z
- **END TIME:** 2026-08-10T19:58:09.823Z
- **DURATION:** 1203 ms

### EXP-377

- **ROOM:** chat
- **CONTROL:** Cursor · not synced
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Cursor · not synced
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Cursor \u00b7 not synced"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-377.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:09.824Z
- **END TIME:** 2026-08-10T19:58:11.035Z
- **DURATION:** 1211 ms

### EXP-378

- **ROOM:** chat
- **CONTROL:** New Chat
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control New Chat
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "New Chat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-378.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:11.036Z
- **END TIME:** 2026-08-10T19:58:12.244Z
- **DURATION:** 1208 ms

### EXP-379

- **ROOM:** chat
- **CONTROL:** Fork
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Fork
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Fork"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-379.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:12.245Z
- **END TIME:** 2026-08-10T19:58:13.450Z
- **DURATION:** 1205 ms

### EXP-380

- **ROOM:** chat
- **CONTROL:** Trim
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Trim
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Trim"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-380.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:13.452Z
- **END TIME:** 2026-08-10T19:58:14.656Z
- **DURATION:** 1204 ms

### EXP-381

- **ROOM:** chat
- **CONTROL:** Clear Main
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Clear Main
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Clear Main"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-381.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:14.658Z
- **END TIME:** 2026-08-10T19:58:15.862Z
- **DURATION:** 1204 ms

### EXP-382

- **ROOM:** chat
- **CONTROL:** Voice input
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Voice input
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Voice input"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-382.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:15.863Z
- **END TIME:** 2026-08-10T19:58:17.067Z
- **DURATION:** 1204 ms

### EXP-383

- **ROOM:** chat
- **CONTROL:** Read aloud
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Read aloud
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Read aloud"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-383.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:17.069Z
- **END TIME:** 2026-08-10T19:58:18.272Z
- **DURATION:** 1203 ms

### EXP-384

- **ROOM:** chat
- **CONTROL:** Compare
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Compare
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Compare"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-384.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:18.273Z
- **END TIME:** 2026-08-10T19:58:19.476Z
- **DURATION:** 1203 ms

### EXP-385

- **ROOM:** chat
- **CONTROL:** Webcam
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Webcam
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Webcam"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-385.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:19.478Z
- **END TIME:** 2026-08-10T19:58:20.682Z
- **DURATION:** 1204 ms

### EXP-386

- **ROOM:** chat
- **CONTROL:** New conversation fresh
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control New conversation fresh
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-386.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:20.684Z
- **END TIME:** 2026-08-10T19:58:21.385Z
- **DURATION:** 701 ms

### EXP-387

- **ROOM:** chat
- **CONTROL:** Place something here attach
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Place something here attach
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-387.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:21.387Z
- **END TIME:** 2026-08-10T19:58:22.088Z
- **DURATION:** 701 ms

### EXP-388

- **ROOM:** chat
- **CONTROL:** Read aloud off
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Read aloud off
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-388.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:22.091Z
- **END TIME:** 2026-08-10T19:58:22.792Z
- **DURATION:** 701 ms

### EXP-389

- **ROOM:** chat
- **CONTROL:** Voice when speaking
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Voice when speaking
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-389.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:22.794Z
- **END TIME:** 2026-08-10T19:58:23.496Z
- **DURATION:** 702 ms

### EXP-390

- **ROOM:** chat
- **CONTROL:** Open the front door Ctrl+K
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Open the front door Ctrl+K
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-390.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:23.497Z
- **END TIME:** 2026-08-10T19:58:24.199Z
- **DURATION:** 702 ms

### EXP-391

- **ROOM:** chat
- **CONTROL:** Fork thread branch
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Fork thread branch
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-391.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:24.201Z
- **END TIME:** 2026-08-10T19:58:24.903Z
- **DURATION:** 702 ms

### EXP-392

- **ROOM:** chat
- **CONTROL:** Dismiss
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Dismiss
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Dismiss"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-392.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:24.905Z
- **END TIME:** 2026-08-10T19:58:26.108Z
- **DURATION:** 1203 ms

### EXP-393

- **ROOM:** chat
- **CONTROL:** Stop responding
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Stop responding
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Stop responding"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-393.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:26.109Z
- **END TIME:** 2026-08-10T19:58:27.313Z
- **DURATION:** 1203 ms

### EXP-394

- **ROOM:** flytying
- **CONTROL:** Setup
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Setup
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Setup"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-394.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:27.314Z
- **END TIME:** 2026-08-10T19:58:28.519Z
- **DURATION:** 1205 ms

### EXP-395

- **ROOM:** flytying
- **CONTROL:** Rebuild
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Rebuild
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Rebuild"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-395.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:28.521Z
- **END TIME:** 2026-08-10T19:58:29.725Z
- **DURATION:** 1204 ms

### EXP-396

- **ROOM:** flytying
- **CONTROL:** Gallery
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Gallery
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Gallery"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-396.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:29.728Z
- **END TIME:** 2026-08-10T19:58:30.945Z
- **DURATION:** 1217 ms

### EXP-397

- **ROOM:** flytying
- **CONTROL:** Next step
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Next step
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Next step"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-397.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:30.947Z
- **END TIME:** 2026-08-10T19:58:32.152Z
- **DURATION:** 1205 ms

### EXP-398

- **ROOM:** flytying
- **CONTROL:** Repeat
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Repeat
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Repeat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-398.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:32.154Z
- **END TIME:** 2026-08-10T19:58:33.357Z
- **DURATION:** 1203 ms

### EXP-399

- **ROOM:** flytying
- **CONTROL:** Clear
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Clear
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Clear"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-399.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:33.359Z
- **END TIME:** 2026-08-10T19:58:34.563Z
- **DURATION:** 1204 ms

### EXP-400

- **ROOM:** flytying
- **CONTROL:** Show
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Show
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Show"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-400.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:34.565Z
- **END TIME:** 2026-08-10T19:58:35.768Z
- **DURATION:** 1203 ms

### EXP-401

- **ROOM:** flytying
- **CONTROL:** Compare
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Compare
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Compare"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-401.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:35.771Z
- **END TIME:** 2026-08-10T19:58:36.974Z
- **DURATION:** 1203 ms

### EXP-402

- **ROOM:** flytying
- **CONTROL:** Export
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Export
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Export"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-402.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:36.976Z
- **END TIME:** 2026-08-10T19:58:38.180Z
- **DURATION:** 1204 ms

### EXP-403

- **ROOM:** flytying
- **CONTROL:** Print
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Print
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Print"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-403.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:38.182Z
- **END TIME:** 2026-08-10T19:58:39.386Z
- **DURATION:** 1204 ms

### EXP-404

- **ROOM:** flytying
- **CONTROL:** What
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control What
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "What"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-404.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:39.387Z
- **END TIME:** 2026-08-10T19:58:40.592Z
- **DURATION:** 1205 ms

### EXP-405

- **ROOM:** flytying
- **CONTROL:** Brand ▲
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Brand ▲
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-405.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:40.593Z
- **END TIME:** 2026-08-10T19:58:41.296Z
- **DURATION:** 703 ms

### EXP-406

- **ROOM:** flytying
- **CONTROL:** Scan barcode
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Scan barcode
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-406.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:41.297Z
- **END TIME:** 2026-08-10T19:58:42.000Z
- **DURATION:** 703 ms

### EXP-407

- **ROOM:** flytying
- **CONTROL:** Stop
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Stop
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Stop"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-407.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:42.002Z
- **END TIME:** 2026-08-10T19:58:43.206Z
- **DURATION:** 1204 ms

### EXP-408

- **ROOM:** health
- **CONTROL:** Add
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Add
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Add"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-408.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:43.208Z
- **END TIME:** 2026-08-10T19:58:44.412Z
- **DURATION:** 1204 ms

### EXP-409

- **ROOM:** mission
- **CONTROL:** Open Notifications
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Open Notifications
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Open Notifications"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-409.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:44.414Z
- **END TIME:** 2026-08-10T19:58:45.678Z
- **DURATION:** 1264 ms

### EXP-410

- **ROOM:** mission
- **CONTROL:** Chat
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Chat
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Chat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-410.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:45.681Z
- **END TIME:** 2026-08-10T19:58:46.902Z
- **DURATION:** 1221 ms

### EXP-411

- **ROOM:** mission
- **CONTROL:** Audit
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Audit
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Audit"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-411.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:46.904Z
- **END TIME:** 2026-08-10T19:58:48.123Z
- **DURATION:** 1219 ms

### EXP-412

- **ROOM:** mission
- **CONTROL:** Home
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Home
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Home"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-412.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:48.124Z
- **END TIME:** 2026-08-10T19:58:49.339Z
- **DURATION:** 1215 ms

### EXP-413

- **ROOM:** mission
- **CONTROL:** Advanced ▸
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Advanced ▸
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-413.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:58:49.341Z
- **END TIME:** 2026-08-10T19:58:50.044Z
- **DURATION:** 703 ms

### EXP-414

- **ROOM:** documents
- **CONTROL:** Ask
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Ask
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Ask"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-414.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:50.046Z
- **END TIME:** 2026-08-10T19:58:51.251Z
- **DURATION:** 1205 ms

### EXP-415

- **ROOM:** planner
- **CONTROL:** Journal
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Journal
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-415.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:51.252Z
- **END TIME:** 2026-08-10T19:58:52.466Z
- **DURATION:** 1214 ms

### EXP-416

- **ROOM:** planner
- **CONTROL:** Calendar
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Calendar
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Calendar"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-416.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:52.468Z
- **END TIME:** 2026-08-10T19:58:53.684Z
- **DURATION:** 1216 ms

### EXP-417

- **ROOM:** planner
- **CONTROL:** From Journal
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control From Journal
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "From Journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-417.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:53.686Z
- **END TIME:** 2026-08-10T19:58:54.901Z
- **DURATION:** 1215 ms

### EXP-418

- **ROOM:** planner
- **CONTROL:** Focus 25m
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Focus 25m
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Focus 25m"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-418.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:54.907Z
- **END TIME:** 2026-08-10T19:58:56.115Z
- **DURATION:** 1208 ms

### EXP-419

- **ROOM:** calendar
- **CONTROL:** Today
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Today
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Today"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-419.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:56.117Z
- **END TIME:** 2026-08-10T19:58:57.321Z
- **DURATION:** 1204 ms

### EXP-420

- **ROOM:** calendar
- **CONTROL:** Documents
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Documents
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Documents"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-420.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:57.324Z
- **END TIME:** 2026-08-10T19:58:58.544Z
- **DURATION:** 1220 ms

### EXP-421

- **ROOM:** calendar
- **CONTROL:** Add commitment
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Add commitment
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Add commitment"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-421.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:58.545Z
- **END TIME:** 2026-08-10T19:58:59.752Z
- **DURATION:** 1207 ms

### EXP-422

- **ROOM:** calendar
- **CONTROL:** Ask Chat
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Ask Chat
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Ask Chat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-422.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:58:59.754Z
- **END TIME:** 2026-08-10T19:59:00.973Z
- **DURATION:** 1219 ms

### EXP-423

- **ROOM:** gallery
- **CONTROL:** Maker
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Maker
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Maker"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-423.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:00.974Z
- **END TIME:** 2026-08-10T19:59:02.189Z
- **DURATION:** 1215 ms

### EXP-424

- **ROOM:** gallery
- **CONTROL:** Fly tying
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Fly tying
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Fly tying"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-424.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:02.192Z
- **END TIME:** 2026-08-10T19:59:03.414Z
- **DURATION:** 1222 ms

### EXP-425

- **ROOM:** gallery
- **CONTROL:** Video
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Video
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Video"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-425.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:03.415Z
- **END TIME:** 2026-08-10T19:59:04.628Z
- **DURATION:** 1213 ms

### EXP-426

- **ROOM:** gallery
- **CONTROL:** Meme
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Meme
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Meme"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-426.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:04.629Z
- **END TIME:** 2026-08-10T19:59:05.840Z
- **DURATION:** 1211 ms

### EXP-427

- **ROOM:** gallery
- **CONTROL:** Cancel generation
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Cancel generation
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Cancel generation"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-427.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:05.842Z
- **END TIME:** 2026-08-10T19:59:07.047Z
- **DURATION:** 1205 ms

### EXP-428

- **ROOM:** gallery
- **CONTROL:** Generate another
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Generate another
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Generate another"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-428.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:07.049Z
- **END TIME:** 2026-08-10T19:59:08.254Z
- **DURATION:** 1205 ms

### EXP-429

- **ROOM:** gallery
- **CONTROL:** Install NSFW checkpoints
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Install NSFW checkpoints
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Install NSFW checkpoints"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-429.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:08.256Z
- **END TIME:** 2026-08-10T19:59:09.461Z
- **DURATION:** 1205 ms

### EXP-430

- **ROOM:** gallery
- **CONTROL:** Generate metadata
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Generate metadata
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Generate metadata"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-430.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:09.462Z
- **END TIME:** 2026-08-10T19:59:10.672Z
- **DURATION:** 1210 ms

### EXP-431

- **ROOM:** gallery
- **CONTROL:** Load more
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Load more
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Load more"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-431.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:10.675Z
- **END TIME:** 2026-08-10T19:59:11.879Z
- **DURATION:** 1204 ms

### EXP-432

- **ROOM:** gallery
- **CONTROL:** Reuse
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Reuse
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Reuse"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-432.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:11.881Z
- **END TIME:** 2026-08-10T19:59:13.089Z
- **DURATION:** 1208 ms

### EXP-433

- **ROOM:** gallery
- **CONTROL:** Favorite prompt
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Favorite prompt
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Favorite prompt"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-433.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:13.093Z
- **END TIME:** 2026-08-10T19:59:14.298Z
- **DURATION:** 1205 ms

### EXP-434

- **ROOM:** gallery
- **CONTROL:** Delete saved prompt
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Delete saved prompt
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Delete saved prompt"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-434.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:14.300Z
- **END TIME:** 2026-08-10T19:59:15.505Z
- **DURATION:** 1205 ms

### EXP-435

- **ROOM:** coding
- **CONTROL:** Projects
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Projects
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Projects"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-435.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:15.508Z
- **END TIME:** 2026-08-10T19:59:16.733Z
- **DURATION:** 1225 ms

### EXP-436

- **ROOM:** coding
- **CONTROL:** Job Center
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Job Center
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Job Center"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-436.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:16.736Z
- **END TIME:** 2026-08-10T19:59:17.940Z
- **DURATION:** 1204 ms

### EXP-437

- **ROOM:** coding
- **CONTROL:** Models
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Models
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Models"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-437.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:17.943Z
- **END TIME:** 2026-08-10T19:59:19.174Z
- **DURATION:** 1231 ms

### EXP-438

- **ROOM:** memory
- **CONTROL:** Search
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Search
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-438.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:19.175Z
- **END TIME:** 2026-08-10T19:59:20.380Z
- **DURATION:** 1205 ms

### EXP-439

- **ROOM:** memory
- **CONTROL:** New
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control New
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "New"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-439.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:20.382Z
- **END TIME:** 2026-08-10T19:59:21.586Z
- **DURATION:** 1204 ms

### EXP-440

- **ROOM:** memory
- **CONTROL:** memoryOpenKnowledgeBtn
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control memoryOpenKnowledgeBtn
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"missing": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-440.json`
- **BUG:** BUG-024
- **START TIME:** 2026-08-10T19:59:21.588Z
- **END TIME:** 2026-08-10T19:59:22.290Z
- **DURATION:** 702 ms

### EXP-441

- **ROOM:** memory
- **CONTROL:** Open Connections
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Open Connections
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Open Connections"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-441.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:22.292Z
- **END TIME:** 2026-08-10T19:59:23.504Z
- **DURATION:** 1212 ms

### EXP-442

- **ROOM:** voice
- **CONTROL:** Audio
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Audio
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Audio"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-442.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:23.506Z
- **END TIME:** 2026-08-10T19:59:24.726Z
- **DURATION:** 1220 ms

### EXP-443

- **ROOM:** voice
- **CONTROL:** Presence
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Presence
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Presence"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-443.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:24.728Z
- **END TIME:** 2026-08-10T19:59:25.938Z
- **DURATION:** 1210 ms

### EXP-444

- **ROOM:** voice
- **CONTROL:** Recovery
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Recovery
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Recovery"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-444.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:25.941Z
- **END TIME:** 2026-08-10T19:59:27.144Z
- **DURATION:** 1203 ms

### EXP-445

- **ROOM:** voice
- **CONTROL:** Warm router
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Warm router
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Warm router"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-445.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:27.146Z
- **END TIME:** 2026-08-10T19:59:28.351Z
- **DURATION:** 1205 ms

### EXP-446

- **ROOM:** voice
- **CONTROL:** Voice smoke
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Voice smoke
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Voice smoke"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-446.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:28.353Z
- **END TIME:** 2026-08-10T19:59:29.557Z
- **DURATION:** 1204 ms

### EXP-447

- **ROOM:** voice
- **CONTROL:** Start cloud live
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Start cloud live
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Start cloud live"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-447.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:29.559Z
- **END TIME:** 2026-08-10T19:59:30.763Z
- **DURATION:** 1204 ms

### EXP-448

- **ROOM:** repair
- **CONTROL:** Open Notifications
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Open Notifications
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Open Notifications"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-448.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:30.765Z
- **END TIME:** 2026-08-10T19:59:32.028Z
- **DURATION:** 1263 ms

### EXP-449

- **ROOM:** repair
- **CONTROL:** Chat
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Chat
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Chat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-449.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:32.031Z
- **END TIME:** 2026-08-10T19:59:33.258Z
- **DURATION:** 1227 ms

### EXP-450

- **ROOM:** repair
- **CONTROL:** Audit
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Audit
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Audit"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-450.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:33.260Z
- **END TIME:** 2026-08-10T19:59:34.477Z
- **DURATION:** 1217 ms

### EXP-451

- **ROOM:** repair
- **CONTROL:** Home
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Home
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Home"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-451.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:34.480Z
- **END TIME:** 2026-08-10T19:59:35.694Z
- **DURATION:** 1214 ms

### EXP-452

- **ROOM:** repair
- **CONTROL:** Advanced ▾
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Advanced ▾
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Advanced \u25be"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-452.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:35.696Z
- **END TIME:** 2026-08-10T19:59:36.901Z
- **DURATION:** 1205 ms

### EXP-453

- **ROOM:** repair
- **CONTROL:** Hardware
- **HOW DISCOVERED:** final discovery pass cycle 1
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Hardware
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Hardware"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-453.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:36.902Z
- **END TIME:** 2026-08-10T19:59:38.107Z
- **DURATION:** 1205 ms

### EXP-454

- **ROOM:** flytying
- **CONTROL:** Sculpin streamer fly
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Sculpin streamer fly
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Sculpin streamer fly"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-454.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:14.179Z
- **END TIME:** 2026-08-10T20:00:15.386Z
- **DURATION:** 1207 ms

### EXP-455

- **ROOM:** flytying
- **CONTROL:** Unfavorite pattern
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Unfavorite pattern
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Unfavorite pattern"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-455.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:15.388Z
- **END TIME:** 2026-08-10T20:00:16.594Z
- **DURATION:** 1206 ms

### EXP-456

- **ROOM:** flytying
- **CONTROL:** Adams dry fly #16 terrestrial · 9 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams dry fly #16 terrestrial · 9 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams dry fly #16 terrestrial \u00b7 9 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-456.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:16.596Z
- **END TIME:** 2026-08-10T20:00:17.801Z
- **DURATION:** 1205 ms

### EXP-457

- **ROOM:** flytying
- **CONTROL:** Favorite pattern
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Favorite pattern
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Favorite pattern"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-457.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:17.802Z
- **END TIME:** 2026-08-10T20:00:19.006Z
- **DURATION:** 1204 ms

### EXP-458

- **ROOM:** flytying
- **CONTROL:** Adams dry fly #18 dry · 23 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams dry fly #18 dry · 23 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams dry fly #18 dry \u00b7 23 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-458.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:19.009Z
- **END TIME:** 2026-08-10T20:00:20.213Z
- **DURATION:** 1204 ms

### EXP-459

- **ROOM:** flytying
- **CONTROL:** Adams dry fly olive terrestrial · 10 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams dry fly olive terrestrial · 10 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams dry fly olive terrestrial \u00b7 10 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-459.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:20.216Z
- **END TIME:** 2026-08-10T20:00:21.423Z
- **DURATION:** 1207 ms

### EXP-460

- **ROOM:** flytying
- **CONTROL:** Adams Irresistible dry · 21 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams Irresistible dry · 21 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams Irresistible dry \u00b7 21 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-460.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:21.425Z
- **END TIME:** 2026-08-10T20:00:22.631Z
- **DURATION:** 1206 ms

### EXP-461

- **ROOM:** flytying
- **CONTROL:** Adams Irresistible dry · 12 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams Irresistible dry · 12 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams Irresistible dry \u00b7 12 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-461.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:22.634Z
- **END TIME:** 2026-08-10T20:00:23.838Z
- **DURATION:** 1204 ms

### EXP-462

- **ROOM:** flytying
- **CONTROL:** Adams Irresistible #12 dry · 6 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams Irresistible #12 dry · 6 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams Irresistible #12 dry \u00b7 6 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-462.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:23.840Z
- **END TIME:** 2026-08-10T20:00:25.045Z
- **DURATION:** 1205 ms

### EXP-463

- **ROOM:** flytying
- **CONTROL:** Adams Irresistible #14 terrestrial · 11 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams Irresistible #14 terrestrial · 11 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams Irresistible #14 terrestrial \u00b7 11 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-463.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:25.049Z
- **END TIME:** 2026-08-10T20:00:26.253Z
- **DURATION:** 1204 ms

### EXP-464

- **ROOM:** flytying
- **CONTROL:** Adams parachute dry · 3 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams parachute dry · 3 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams parachute dry \u00b7 3 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-464.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:26.255Z
- **END TIME:** 2026-08-10T20:00:27.459Z
- **DURATION:** 1204 ms

### EXP-465

- **ROOM:** flytying
- **CONTROL:** Adams parachute #14 dry · 12 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams parachute #14 dry · 12 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams parachute #14 dry \u00b7 12 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-465.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:27.461Z
- **END TIME:** 2026-08-10T20:00:28.668Z
- **DURATION:** 1207 ms

### EXP-466

- **ROOM:** flytying
- **CONTROL:** Adams parachute #14 dry · 16 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams parachute #14 dry · 16 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams parachute #14 dry \u00b7 16 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-466.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:28.670Z
- **END TIME:** 2026-08-10T20:00:29.874Z
- **DURATION:** 1204 ms

### EXP-467

- **ROOM:** flytying
- **CONTROL:** Adams parachute chartreuse post dry · 7 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams parachute chartreuse post dry · 7 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams parachute chartreuse post dry \u00b7 7 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-467.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:29.878Z
- **END TIME:** 2026-08-10T20:00:31.082Z
- **DURATION:** 1204 ms

### EXP-468

- **ROOM:** flytying
- **CONTROL:** Adams parachute chartreuse post dry · 8 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams parachute chartreuse post dry · 8 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams parachute chartreuse post dry \u00b7 8 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-468.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:31.085Z
- **END TIME:** 2026-08-10T20:00:32.289Z
- **DURATION:** 1204 ms

### EXP-469

- **ROOM:** flytying
- **CONTROL:** Adams parachute orange post terrestrial · 10 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams parachute orange post terrestrial · 10 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams parachute orange post terrestrial \u00b7 10 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-469.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:32.292Z
- **END TIME:** 2026-08-10T20:00:33.497Z
- **DURATION:** 1205 ms

### EXP-470

- **ROOM:** flytying
- **CONTROL:** Adams rusty spinner #18 dry · 9 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams rusty spinner #18 dry · 9 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams rusty spinner #18 dry \u00b7 9 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-470.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:33.499Z
- **END TIME:** 2026-08-10T20:00:34.705Z
- **DURATION:** 1206 ms

### EXP-471

- **ROOM:** flytying
- **CONTROL:** Adams snowshoe terrestrial · 12 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams snowshoe terrestrial · 12 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams snowshoe terrestrial \u00b7 12 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-471.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:34.707Z
- **END TIME:** 2026-08-10T20:00:35.912Z
- **DURATION:** 1205 ms

### EXP-472

- **ROOM:** flytying
- **CONTROL:** Adams snowshoe #16 dry · 10 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams snowshoe #16 dry · 10 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams snowshoe #16 dry \u00b7 10 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-472.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:35.918Z
- **END TIME:** 2026-08-10T20:00:37.123Z
- **DURATION:** 1205 ms

### EXP-473

- **ROOM:** flytying
- **CONTROL:** Adams Wulff terrestrial · 7 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams Wulff terrestrial · 7 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams Wulff terrestrial \u00b7 7 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-473.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:37.127Z
- **END TIME:** 2026-08-10T20:00:38.332Z
- **DURATION:** 1205 ms

### EXP-474

- **ROOM:** flytying
- **CONTROL:** Adams Wulff streamer · 22 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Adams Wulff streamer · 22 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Adams Wulff streamer \u00b7 22 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-474.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:38.337Z
- **END TIME:** 2026-08-10T20:00:39.542Z
- **DURATION:** 1205 ms

### EXP-475

- **ROOM:** flytying
- **CONTROL:** Alexandra streamer streamer · 17 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Alexandra streamer streamer · 17 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Alexandra streamer streamer \u00b7 17 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-475.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:39.544Z
- **END TIME:** 2026-08-10T20:00:40.749Z
- **DURATION:** 1205 ms

### EXP-476

- **ROOM:** flytying
- **CONTROL:** Anchovy fly terrestrial · 9 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Anchovy fly terrestrial · 9 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Anchovy fly terrestrial \u00b7 9 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-476.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:40.751Z
- **END TIME:** 2026-08-10T20:00:41.955Z
- **DURATION:** 1204 ms

### EXP-477

- **ROOM:** flytying
- **CONTROL:** Anchovy fly dry · 14 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Anchovy fly dry · 14 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Anchovy fly dry \u00b7 14 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-477.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:41.958Z
- **END TIME:** 2026-08-10T20:00:43.161Z
- **DURATION:** 1203 ms

### EXP-478

- **ROOM:** flytying
- **CONTROL:** Anchovy fly olive nymph · 15 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Anchovy fly olive nymph · 15 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Anchovy fly olive nymph \u00b7 15 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-478.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:43.163Z
- **END TIME:** 2026-08-10T20:00:44.368Z
- **DURATION:** 1205 ms

### EXP-479

- **ROOM:** flytying
- **CONTROL:** Anchovy fly olive dry · 8 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Anchovy fly olive dry · 8 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Anchovy fly olive dry \u00b7 8 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-479.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:44.370Z
- **END TIME:** 2026-08-10T20:00:45.574Z
- **DURATION:** 1204 ms

### EXP-480

- **ROOM:** flytying
- **CONTROL:** Anchovy fly white dry · 9 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Anchovy fly white dry · 9 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Anchovy fly white dry \u00b7 9 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-480.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:45.576Z
- **END TIME:** 2026-08-10T20:00:46.780Z
- **DURATION:** 1204 ms

### EXP-481

- **ROOM:** flytying
- **CONTROL:** Ant pattern CDC terrestrial · 6 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Ant pattern CDC terrestrial · 6 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Ant pattern CDC terrestrial \u00b7 6 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-481.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:46.784Z
- **END TIME:** 2026-08-10T20:00:47.988Z
- **DURATION:** 1204 ms

### EXP-482

- **ROOM:** flytying
- **CONTROL:** Ant pattern cinnamon terrestrial · 8 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Ant pattern cinnamon terrestrial · 8 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Ant pattern cinnamon terrestrial \u00b7 8 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-482.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:47.990Z
- **END TIME:** 2026-08-10T20:00:49.195Z
- **DURATION:** 1205 ms

### EXP-483

- **ROOM:** flytying
- **CONTROL:** Ant pattern winged terrestrial · 6 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Ant pattern winged terrestrial · 6 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Ant pattern winged terrestrial \u00b7 6 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-483.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:49.197Z
- **END TIME:** 2026-08-10T20:00:50.402Z
- **DURATION:** 1205 ms

### EXP-484

- **ROOM:** flytying
- **CONTROL:** Baitfish articulated streamer · 7 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Baitfish articulated streamer · 7 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Baitfish articulated streamer \u00b7 7 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-484.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:50.405Z
- **END TIME:** 2026-08-10T20:00:51.609Z
- **DURATION:** 1204 ms

### EXP-485

- **ROOM:** flytying
- **CONTROL:** Baitfish pattern terrestrial · 7 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Baitfish pattern terrestrial · 7 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Baitfish pattern terrestrial \u00b7 7 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-485.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:51.612Z
- **END TIME:** 2026-08-10T20:00:52.817Z
- **DURATION:** 1205 ms

### EXP-486

- **ROOM:** flytying
- **CONTROL:** Baitfish pearl dry · 9 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Baitfish pearl dry · 9 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Baitfish pearl dry \u00b7 9 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-486.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:52.819Z
- **END TIME:** 2026-08-10T20:00:54.024Z
- **DURATION:** 1205 ms

### EXP-487

- **ROOM:** flytying
- **CONTROL:** Baitfish pearl dry · 5 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Baitfish pearl dry · 5 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Baitfish pearl dry \u00b7 5 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-487.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:54.029Z
- **END TIME:** 2026-08-10T20:00:55.234Z
- **DURATION:** 1205 ms

### EXP-488

- **ROOM:** flytying
- **CONTROL:** Baitfish pearl dry · 8 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Baitfish pearl dry · 8 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Baitfish pearl dry \u00b7 8 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-488.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:55.237Z
- **END TIME:** 2026-08-10T20:00:56.442Z
- **DURATION:** 1205 ms

### EXP-489

- **ROOM:** flytying
- **CONTROL:** Baitfish tan dry · 7 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Baitfish tan dry · 7 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Baitfish tan dry \u00b7 7 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-489.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:56.444Z
- **END TIME:** 2026-08-10T20:00:57.648Z
- **DURATION:** 1204 ms

### EXP-490

- **ROOM:** flytying
- **CONTROL:** Baitfish UV dry · 4 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Baitfish UV dry · 4 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Baitfish UV dry \u00b7 4 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-490.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:57.651Z
- **END TIME:** 2026-08-10T20:00:58.857Z
- **DURATION:** 1206 ms

### EXP-491

- **ROOM:** flytying
- **CONTROL:** Big Game streamer articulated streamer · 29 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Big Game streamer articulated streamer · 29 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Big Game streamer articulated streamer \u00b7 29 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-491.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:00:58.859Z
- **END TIME:** 2026-08-10T20:01:00.063Z
- **DURATION:** 1204 ms

### EXP-492

- **ROOM:** flytying
- **CONTROL:** Blue Wing Olive parachute dry · 7 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Blue Wing Olive parachute dry · 7 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Blue Wing Olive parachute dry \u00b7 7 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-492.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:00.066Z
- **END TIME:** 2026-08-10T20:01:01.271Z
- **DURATION:** 1205 ms

### EXP-493

- **ROOM:** flytying
- **CONTROL:** Crayfish brown dry · 8 steps 100
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Crayfish brown dry · 8 steps 100
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Crayfish brown dry \u00b7 8 steps 100"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-493.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:01.273Z
- **END TIME:** 2026-08-10T20:01:02.477Z
- **DURATION:** 1204 ms

### EXP-494

- **ROOM:** coding
- **CONTROL:** Overview
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Overview
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Overview"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-494.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:02.480Z
- **END TIME:** 2026-08-10T20:01:03.687Z
- **DURATION:** 1207 ms

### EXP-495

- **ROOM:** coding
- **CONTROL:** Proposals
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Proposals
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Proposals"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-495.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:03.690Z
- **END TIME:** 2026-08-10T20:01:04.893Z
- **DURATION:** 1203 ms

### EXP-496

- **ROOM:** coding
- **CONTROL:** History
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control History
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "History"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-496.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:04.896Z
- **END TIME:** 2026-08-10T20:01:06.101Z
- **DURATION:** 1205 ms

### EXP-497

- **ROOM:** coding
- **CONTROL:** Jobs
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Jobs
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Jobs"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-497.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:06.105Z
- **END TIME:** 2026-08-10T20:01:07.310Z
- **DURATION:** 1205 ms

### EXP-498

- **ROOM:** coding
- **CONTROL:** LSP & Git
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control LSP & Git
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "LSP & Git"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-498.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:07.312Z
- **END TIME:** 2026-08-10T20:01:08.518Z
- **DURATION:** 1206 ms

### EXP-499

- **ROOM:** coding
- **CONTROL:** Preferences
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Preferences
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Preferences"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-499.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:08.521Z
- **END TIME:** 2026-08-10T20:01:09.725Z
- **DURATION:** 1204 ms

### EXP-500

- **ROOM:** coding
- **CONTROL:** Advanced
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Advanced
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Advanced"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-500.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:09.728Z
- **END TIME:** 2026-08-10T20:01:10.932Z
- **DURATION:** 1204 ms

### EXP-501

- **ROOM:** coding
- **CONTROL:** Analyze & propose
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Analyze & propose
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Analyze & propose"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-501.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:10.937Z
- **END TIME:** 2026-08-10T20:01:12.141Z
- **DURATION:** 1204 ms

### EXP-502

- **ROOM:** coding
- **CONTROL:** Plan & propose
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Plan & propose
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Plan & propose"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-502.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:12.143Z
- **END TIME:** 2026-08-10T20:01:13.347Z
- **DURATION:** 1204 ms

### EXP-503

- **ROOM:** memory
- **CONTROL:** View
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control View
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "View"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-503.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:13.350Z
- **END TIME:** 2026-08-10T20:01:14.560Z
- **DURATION:** 1210 ms

### EXP-504

- **ROOM:** memory
- **CONTROL:** Edit
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Edit
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Edit"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-504.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:14.562Z
- **END TIME:** 2026-08-10T20:01:15.769Z
- **DURATION:** 1207 ms

### EXP-505

- **ROOM:** memory
- **CONTROL:** Reset default
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Reset default
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Reset default"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-505.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:15.772Z
- **END TIME:** 2026-08-10T20:01:16.978Z
- **DURATION:** 1206 ms

### EXP-506

- **ROOM:** memory
- **CONTROL:** Journal
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Journal
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-506.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:16.981Z
- **END TIME:** 2026-08-10T20:01:18.194Z
- **DURATION:** 1213 ms

### EXP-507

- **ROOM:** memory
- **CONTROL:** Projects
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Projects
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Projects"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-507.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:18.198Z
- **END TIME:** 2026-08-10T20:01:19.410Z
- **DURATION:** 1212 ms

### EXP-508

- **ROOM:** memory
- **CONTROL:** Browser
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Browser
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Browser"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-508.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:19.412Z
- **END TIME:** 2026-08-10T20:01:20.625Z
- **DURATION:** 1213 ms

### EXP-509

- **ROOM:** memory
- **CONTROL:** Documents
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Documents
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Documents"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-509.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:20.628Z
- **END TIME:** 2026-08-10T20:01:21.842Z
- **DURATION:** 1214 ms

### EXP-510

- **ROOM:** memory
- **CONTROL:** Knowledge Briefs
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Knowledge Briefs
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Knowledge Briefs"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-510.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:21.844Z
- **END TIME:** 2026-08-10T20:01:23.056Z
- **DURATION:** 1212 ms

### EXP-511

- **ROOM:** memory
- **CONTROL:** Export
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Export
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Export"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-511.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:23.059Z
- **END TIME:** 2026-08-10T20:01:24.263Z
- **DURATION:** 1204 ms

### EXP-512

- **ROOM:** memory
- **CONTROL:** Import
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Import
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Import"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-512.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:24.265Z
- **END TIME:** 2026-08-10T20:01:25.469Z
- **DURATION:** 1204 ms

### EXP-513

- **ROOM:** memory
- **CONTROL:** Prune stale
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Prune stale
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Prune stale"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-513.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:25.471Z
- **END TIME:** 2026-08-10T20:01:26.675Z
- **DURATION:** 1204 ms

### EXP-514

- **ROOM:** memory
- **CONTROL:** Scrub test junk
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Scrub test junk
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Scrub test junk"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-514.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:26.678Z
- **END TIME:** 2026-08-10T20:01:27.882Z
- **DURATION:** 1204 ms

### EXP-515

- **ROOM:** repair
- **CONTROL:** Inference
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Inference
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Inference"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-515.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:27.884Z
- **END TIME:** 2026-08-10T20:01:29.091Z
- **DURATION:** 1207 ms

### EXP-516

- **ROOM:** repair
- **CONTROL:** Memory
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Memory
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Memory"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-516.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:29.094Z
- **END TIME:** 2026-08-10T20:01:30.299Z
- **DURATION:** 1205 ms

### EXP-517

- **ROOM:** repair
- **CONTROL:** Knowledge
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Knowledge
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Knowledge"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-517.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:30.302Z
- **END TIME:** 2026-08-10T20:01:31.507Z
- **DURATION:** 1205 ms

### EXP-518

- **ROOM:** repair
- **CONTROL:** Databases
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Databases
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Databases"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-518.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:31.510Z
- **END TIME:** 2026-08-10T20:01:32.714Z
- **DURATION:** 1204 ms

### EXP-519

- **ROOM:** repair
- **CONTROL:** Settings
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Settings
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Settings"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-519.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:32.717Z
- **END TIME:** 2026-08-10T20:01:33.921Z
- **DURATION:** 1204 ms

### EXP-520

- **ROOM:** repair
- **CONTROL:** Timeline
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Timeline
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Timeline"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-520.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:33.925Z
- **END TIME:** 2026-08-10T20:01:35.130Z
- **DURATION:** 1205 ms

### EXP-521

- **ROOM:** repair
- **CONTROL:** Release
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Release
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Release"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-521.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:35.133Z
- **END TIME:** 2026-08-10T20:01:36.338Z
- **DURATION:** 1205 ms

### EXP-522

- **ROOM:** repair
- **CONTROL:** Applications
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Applications
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Applications"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-522.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:36.341Z
- **END TIME:** 2026-08-10T20:01:37.546Z
- **DURATION:** 1205 ms

### EXP-523

- **ROOM:** repair
- **CONTROL:** Queue Snapshot
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Queue Snapshot
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Queue Snapshot"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-523.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:37.549Z
- **END TIME:** 2026-08-10T20:01:38.753Z
- **DURATION:** 1204 ms

### EXP-524

- **ROOM:** repair
- **CONTROL:** Operations Event Log
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Operations Event Log
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Operations Event Log"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-524.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:38.756Z
- **END TIME:** 2026-08-10T20:01:39.960Z
- **DURATION:** 1204 ms

### EXP-525

- **ROOM:** repair
- **CONTROL:** Intent Analytics
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Intent Analytics
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Intent Analytics"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-525.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:39.962Z
- **END TIME:** 2026-08-10T20:01:41.167Z
- **DURATION:** 1205 ms

### EXP-526

- **ROOM:** integrity
- **CONTROL:** Refresh
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Refresh
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Refresh"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-526.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:41.169Z
- **END TIME:** 2026-08-10T20:01:42.374Z
- **DURATION:** 1205 ms

### EXP-527

- **ROOM:** integrity
- **CONTROL:** Repair
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Repair
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Repair"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-527.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:42.377Z
- **END TIME:** 2026-08-10T20:01:43.595Z
- **DURATION:** 1218 ms

### EXP-528

- **ROOM:** home
- **CONTROL:** Mission Control
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Mission Control
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Mission Control"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-528.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:43.597Z
- **END TIME:** 2026-08-10T20:01:44.806Z
- **DURATION:** 1209 ms

### EXP-529

- **ROOM:** home
- **CONTROL:** Planner
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Planner
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Planner"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-529.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:44.808Z
- **END TIME:** 2026-08-10T20:01:46.022Z
- **DURATION:** 1214 ms

### EXP-530

- **ROOM:** home
- **CONTROL:** Journal
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Journal
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-530.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:46.025Z
- **END TIME:** 2026-08-10T20:01:47.241Z
- **DURATION:** 1216 ms

### EXP-531

- **ROOM:** home
- **CONTROL:** Calendar
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Calendar
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Calendar"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-531.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:47.244Z
- **END TIME:** 2026-08-10T20:01:48.459Z
- **DURATION:** 1215 ms

### EXP-532

- **ROOM:** home
- **CONTROL:** Retry
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Retry
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Retry"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-532.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:48.462Z
- **END TIME:** 2026-08-10T20:01:49.666Z
- **DURATION:** 1204 ms

### EXP-533

- **ROOM:** home
- **CONTROL:** Running…
- **HOW DISCOVERED:** final discovery pass cycle 2
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Running…
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Running\u2026"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-533.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:49.668Z
- **END TIME:** 2026-08-10T20:01:50.873Z
- **DURATION:** 1205 ms

### EXP-534

- **ROOM:** automation
- **CONTROL:** Run
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Run
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Run"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-534.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:02:26.917Z
- **END TIME:** 2026-08-10T20:02:28.121Z
- **DURATION:** 1204 ms

### EXP-535

- **ROOM:** automation
- **CONTROL:** Dry run
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Dry run
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Dry run"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-535.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:02:28.124Z
- **END TIME:** 2026-08-10T20:02:29.327Z
- **DURATION:** 1203 ms

### EXP-536

- **ROOM:** automation
- **CONTROL:** Enable
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Enable
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Enable"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-536.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:02:29.330Z
- **END TIME:** 2026-08-10T20:02:30.549Z
- **DURATION:** 1219 ms

### EXP-537

- **ROOM:** automation
- **CONTROL:** Edit
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Edit
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Edit"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-537.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:02:30.559Z
- **END TIME:** 2026-08-10T20:02:31.768Z
- **DURATION:** 1209 ms

### EXP-538

- **ROOM:** automation
- **CONTROL:** Mute
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Mute
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Mute"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-538.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:02:31.772Z
- **END TIME:** 2026-08-10T20:02:32.977Z
- **DURATION:** 1205 ms

### EXP-539

- **ROOM:** automation
- **CONTROL:** Delete
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Delete
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Delete"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-539.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:02:32.981Z
- **END TIME:** 2026-08-10T20:12:44.437Z
- **DURATION:** 611456 ms

### EXP-540

- **ROOM:** automation
- **CONTROL:** Schedule
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Schedule
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Schedule"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-540.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:44.441Z
- **END TIME:** 2026-08-10T20:12:45.646Z
- **DURATION:** 1205 ms

### EXP-541

- **ROOM:** automation
- **CONTROL:** Create
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Create
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Create"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-541.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:45.649Z
- **END TIME:** 2026-08-10T20:12:46.854Z
- **DURATION:** 1205 ms

### EXP-542

- **ROOM:** automation
- **CONTROL:** Details
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Details
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Details"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-542.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:46.857Z
- **END TIME:** 2026-08-10T20:12:48.061Z
- **DURATION:** 1204 ms

### EXP-543

- **ROOM:** providers
- **CONTROL:** Mission Control · Inference
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Mission Control · Inference
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Mission Control \u00b7 Inference"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-543.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:48.064Z
- **END TIME:** 2026-08-10T20:12:49.380Z
- **DURATION:** 1316 ms

### EXP-544

- **ROOM:** home_automation
- **CONTROL:** Presence
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Presence
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Presence"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-544.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:49.382Z
- **END TIME:** 2026-08-10T20:12:50.602Z
- **DURATION:** 1220 ms

### EXP-545

- **ROOM:** home_automation
- **CONTROL:** Security
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Security
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Security"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-545.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:50.604Z
- **END TIME:** 2026-08-10T20:12:51.820Z
- **DURATION:** 1216 ms

### EXP-546

- **ROOM:** home_automation
- **CONTROL:** Open HA
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Open HA
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Open HA"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-546.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:51.823Z
- **END TIME:** 2026-08-10T20:12:53.029Z
- **DURATION:** 1206 ms

### EXP-547

- **ROOM:** home_automation
- **CONTROL:** haCopyWebhookBtn
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control haCopyWebhookBtn
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "haCopyWebhookBtn"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-547.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:53.034Z
- **END TIME:** 2026-08-10T20:12:54.884Z
- **DURATION:** 1850 ms

### EXP-548

- **ROOM:** presence
- **CONTROL:** Security
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Security
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Security"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-548.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:54.888Z
- **END TIME:** 2026-08-10T20:12:56.885Z
- **DURATION:** 1997 ms

### EXP-549

- **ROOM:** presence
- **CONTROL:** Voice
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Voice
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Voice"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-549.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:56.889Z
- **END TIME:** 2026-08-10T20:12:58.884Z
- **DURATION:** 1995 ms

### EXP-550

- **ROOM:** journal
- **CONTROL:** Writing mode
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Writing mode
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Writing mode"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-550.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:12:58.888Z
- **END TIME:** 2026-08-10T20:13:00.890Z
- **DURATION:** 2002 ms

### EXP-551

- **ROOM:** journal
- **CONTROL:** Calendar
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Calendar
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Calendar"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-551.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:00.894Z
- **END TIME:** 2026-08-10T20:13:02.884Z
- **DURATION:** 1990 ms

### EXP-552

- **ROOM:** journal
- **CONTROL:** Planner
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Planner
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Planner"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-552.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:02.888Z
- **END TIME:** 2026-08-10T20:13:04.884Z
- **DURATION:** 1996 ms

### EXP-553

- **ROOM:** journal
- **CONTROL:** Memory
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Memory
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Memory"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-553.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:04.888Z
- **END TIME:** 2026-08-10T20:13:06.889Z
- **DURATION:** 2001 ms

### EXP-554

- **ROOM:** journal
- **CONTROL:** Reflect
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Reflect
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Reflect"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-554.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:06.896Z
- **END TIME:** 2026-08-10T20:13:08.884Z
- **DURATION:** 1988 ms

### EXP-555

- **ROOM:** journal
- **CONTROL:** Promote assist
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Promote assist
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Promote assist"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-555.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:08.887Z
- **END TIME:** 2026-08-10T20:13:10.884Z
- **DURATION:** 1997 ms

### EXP-556

- **ROOM:** journal
- **CONTROL:** Month-end
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Month-end
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Month-end"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-556.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:10.887Z
- **END TIME:** 2026-08-10T20:13:12.884Z
- **DURATION:** 1997 ms

### EXP-557

- **ROOM:** journal
- **CONTROL:** Documents
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Documents
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Documents"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-557.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:12.887Z
- **END TIME:** 2026-08-10T20:13:14.885Z
- **DURATION:** 1998 ms

### EXP-558

- **ROOM:** journal
- **CONTROL:** Audio
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Audio
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Audio"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-558.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:14.890Z
- **END TIME:** 2026-08-10T20:13:16.884Z
- **DURATION:** 1994 ms

### EXP-559

- **ROOM:** journal
- **CONTROL:** Print month
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Print month
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Print month"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-559.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:16.889Z
- **END TIME:** 2026-08-10T20:13:18.418Z
- **DURATION:** 1529 ms

### EXP-560

- **ROOM:** journal
- **CONTROL:** Export PDF
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Export PDF
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Export PDF"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-560.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:18.420Z
- **END TIME:** 2026-08-10T20:13:19.627Z
- **DURATION:** 1207 ms

### EXP-561

- **ROOM:** journal
- **CONTROL:** Export JSON
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Export JSON
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Export JSON"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-561.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:19.629Z
- **END TIME:** 2026-08-10T20:13:20.835Z
- **DURATION:** 1206 ms

### EXP-562

- **ROOM:** journal
- **CONTROL:** Export encrypted
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Export encrypted
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Export encrypted"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-562.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:20.838Z
- **END TIME:** 2026-08-10T20:13:22.046Z
- **DURATION:** 1208 ms

### EXP-563

- **ROOM:** journal
- **CONTROL:** Import
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Import
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Import"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-563.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:22.050Z
- **END TIME:** 2026-08-10T20:13:23.265Z
- **DURATION:** 1215 ms

### EXP-564

- **ROOM:** journal
- **CONTROL:** Import encrypted
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Import encrypted
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Import encrypted"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-564.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:23.274Z
- **END TIME:** 2026-08-10T20:13:24.485Z
- **DURATION:** 1211 ms

### EXP-565

- **ROOM:** journal
- **CONTROL:** Backup now
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Backup now
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Backup now"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-565.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:24.487Z
- **END TIME:** 2026-08-10T20:13:25.694Z
- **DURATION:** 1207 ms

### EXP-566

- **ROOM:** journal
- **CONTROL:** Voice log
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Voice log
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Voice log"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-566.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:25.696Z
- **END TIME:** 2026-08-10T20:13:26.902Z
- **DURATION:** 1206 ms

### EXP-567

- **ROOM:** journal
- **CONTROL:** Vision import
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Vision import
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Vision import"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-567.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:26.905Z
- **END TIME:** 2026-08-10T20:13:28.114Z
- **DURATION:** 1209 ms

### EXP-568

- **ROOM:** journal
- **CONTROL:** Shortcuts (?)
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Shortcuts (?)
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Shortcuts (?)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-568.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:28.117Z
- **END TIME:** 2026-08-10T20:13:29.326Z
- **DURATION:** 1209 ms

### EXP-569

- **ROOM:** journal
- **CONTROL:** Undo
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Undo
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Undo"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-569.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:29.329Z
- **END TIME:** 2026-08-10T20:13:30.538Z
- **DURATION:** 1209 ms

### EXP-570

- **ROOM:** journal
- **CONTROL:** Redo
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Redo
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Redo"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-570.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:30.541Z
- **END TIME:** 2026-08-10T20:13:31.748Z
- **DURATION:** 1207 ms

### EXP-571

- **ROOM:** journal
- **CONTROL:** Migrate month
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Migrate month
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Migrate month"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-571.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:31.750Z
- **END TIME:** 2026-08-10T20:13:32.958Z
- **DURATION:** 1208 ms

### EXP-572

- **ROOM:** journal
- **CONTROL:** Exit writing (Esc)
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Exit writing (Esc)
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Exit writing (Esc)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-572.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:32.962Z
- **END TIME:** 2026-08-10T20:13:34.172Z
- **DURATION:** 1210 ms

### EXP-573

- **ROOM:** video
- **CONTROL:** Gallery
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Gallery
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Gallery"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-573.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:34.176Z
- **END TIME:** 2026-08-10T20:13:35.404Z
- **DURATION:** 1228 ms

### EXP-574

- **ROOM:** video
- **CONTROL:** Meme
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Meme
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Meme"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-574.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:35.415Z
- **END TIME:** 2026-08-10T20:13:36.637Z
- **DURATION:** 1222 ms

### EXP-575

- **ROOM:** video
- **CONTROL:** Cancel generation
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Cancel generation
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Cancel generation"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-575.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:36.643Z
- **END TIME:** 2026-08-10T20:13:37.850Z
- **DURATION:** 1207 ms

### EXP-576

- **ROOM:** video
- **CONTROL:** Free VRAM before video
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Free VRAM before video
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Free VRAM before video"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-576.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:37.856Z
- **END TIME:** 2026-08-10T20:13:39.070Z
- **DURATION:** 1214 ms

### EXP-577

- **ROOM:** video
- **CONTROL:** Install AnimateDiff (~2 GB)
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Install AnimateDiff (~2 GB)
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Install AnimateDiff (~2 GB)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-577.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:39.073Z
- **END TIME:** 2026-08-10T20:13:40.283Z
- **DURATION:** 1210 ms

### EXP-578

- **ROOM:** video
- **CONTROL:** Install NSFW checkpoints
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Install NSFW checkpoints
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Install NSFW checkpoints"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-578.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:40.285Z
- **END TIME:** 2026-08-10T20:13:41.494Z
- **DURATION:** 1209 ms

### EXP-579

- **ROOM:** audio
- **CONTROL:** Journal
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Journal
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Journal"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-579.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:41.497Z
- **END TIME:** 2026-08-10T20:13:42.727Z
- **DURATION:** 1230 ms

### EXP-580

- **ROOM:** audio
- **CONTROL:** Start live record
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Start live record
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Start live record"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-580.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:42.730Z
- **END TIME:** 2026-08-10T20:13:43.940Z
- **DURATION:** 1210 ms

### EXP-581

- **ROOM:** audio
- **CONTROL:** Stop + transcribe
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Stop + transcribe
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Stop + transcribe"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-581.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:43.945Z
- **END TIME:** 2026-08-10T20:13:45.156Z
- **DURATION:** 1211 ms

### EXP-582

- **ROOM:** audio
- **CONTROL:** Record (VAD)
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Record (VAD)
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Record (VAD)"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-582.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:45.159Z
- **END TIME:** 2026-08-10T20:13:46.372Z
- **DURATION:** 1213 ms

### EXP-583

- **ROOM:** audio
- **CONTROL:** VAD + transcribe
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control VAD + transcribe
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "VAD + transcribe"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-583.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:46.379Z
- **END TIME:** 2026-08-10T20:13:47.591Z
- **DURATION:** 1212 ms

### EXP-584

- **ROOM:** audio
- **CONTROL:** Cancel job
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Cancel job
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Cancel job"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-584.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:47.593Z
- **END TIME:** 2026-08-10T20:13:48.801Z
- **DURATION:** 1208 ms

### EXP-585

- **ROOM:** audio
- **CONTROL:** Install live EQ
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Install live EQ
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Install live EQ"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-585.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:48.805Z
- **END TIME:** 2026-08-10T20:13:50.014Z
- **DURATION:** 1209 ms

### EXP-586

- **ROOM:** audio
- **CONTROL:** recording_ptt_20260730_161305_ptt_raw.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control recording_ptt_20260730_161305_ptt_raw.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "recording_ptt_20260730_161305_ptt_raw.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-586.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:50.018Z
- **END TIME:** 2026-08-10T20:13:51.226Z
- **DURATION:** 1208 ms

### EXP-587

- **ROOM:** audio
- **CONTROL:** live_20260730_164009_raw.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control live_20260730_164009_raw.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "live_20260730_164009_raw.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-587.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:51.230Z
- **END TIME:** 2026-08-10T20:13:52.436Z
- **DURATION:** 1206 ms

### EXP-588

- **ROOM:** audio
- **CONTROL:** recording_20260730_173355.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control recording_20260730_173355.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "recording_20260730_173355.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-588.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:52.439Z
- **END TIME:** 2026-08-10T20:13:53.658Z
- **DURATION:** 1219 ms

### EXP-589

- **ROOM:** audio
- **CONTROL:** recording_20260730_172933.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control recording_20260730_172933.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "recording_20260730_172933.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-589.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:53.661Z
- **END TIME:** 2026-08-10T20:13:54.869Z
- **DURATION:** 1208 ms

### EXP-590

- **ROOM:** audio
- **CONTROL:** recording_20260730_171640.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control recording_20260730_171640.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "recording_20260730_171640.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-590.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:54.872Z
- **END TIME:** 2026-08-10T20:13:56.080Z
- **DURATION:** 1208 ms

### EXP-591

- **ROOM:** audio
- **CONTROL:** recording_20260730_152137.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control recording_20260730_152137.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "recording_20260730_152137.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-591.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:56.084Z
- **END TIME:** 2026-08-10T20:13:57.294Z
- **DURATION:** 1210 ms

### EXP-592

- **ROOM:** audio
- **CONTROL:** live_20260726_185623.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control live_20260726_185623.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "live_20260726_185623.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-592.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:57.300Z
- **END TIME:** 2026-08-10T20:13:58.510Z
- **DURATION:** 1210 ms

### EXP-593

- **ROOM:** audio
- **CONTROL:** live_20260726_165807.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control live_20260726_165807.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "live_20260726_165807.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-593.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:58.513Z
- **END TIME:** 2026-08-10T20:13:59.722Z
- **DURATION:** 1209 ms

### EXP-594

- **ROOM:** audio
- **CONTROL:** ware_Foundation_2_About_the_Python_Sof.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control ware_Foundation_2_About_the_Python_Sof.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "ware_Foundation_2_About_the_Python_Sof.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-594.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:13:59.725Z
- **END TIME:** 2026-08-10T20:14:00.936Z
- **DURATION:** 1211 ms

### EXP-595

- **ROOM:** audio
- **CONTROL:** 1_For_more_about_the_foundation_s_missio.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control 1_For_more_about_the_foundation_s_missio.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "1_For_more_about_the_foundation_s_missio.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-595.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:00.939Z
- **END TIME:** 2026-08-10T20:14:02.152Z
- **DURATION:** 1213 ms

### EXP-596

- **ROOM:** audio
- **CONTROL:** The_official_website_of_the_Python_Softw.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control The_official_website_of_the_Python_Softw.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "The_official_website_of_the_Python_Softw.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-596.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:02.156Z
- **END TIME:** 2026-08-10T20:14:03.364Z
- **DURATION:** 1208 ms

### EXP-597

- **ROOM:** audio
- **CONTROL:** the_RTX_3090.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control the_RTX_3090.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "the_RTX_3090.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-597.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:03.367Z
- **END TIME:** 2026-08-10T20:14:04.577Z
- **DURATION:** 1210 ms

### EXP-598

- **ROOM:** audio
- **CONTROL:** Stored_via_ACM_exact_acceptance_token.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Stored_via_ACM_exact_acceptance_token.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Stored_via_ACM_exact_acceptance_token.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-598.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:04.581Z
- **END TIME:** 2026-08-10T20:14:05.789Z
- **DURATION:** 1208 ms

### EXP-599

- **ROOM:** audio
- **CONTROL:** provide_a_list_or_more_details_I_can_he.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control provide_a_list_or_more_details_I_can_he.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "provide_a_list_or_more_details_I_can_he.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-599.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:05.792Z
- **END TIME:** 2026-08-10T20:14:07.000Z
- **DURATION:** 1208 ms

### EXP-600

- **ROOM:** audio
- **CONTROL:** For_example_you_might_have_things_like.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control For_example_you_might_have_things_like.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "For_example_you_might_have_things_like.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-600.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:07.004Z
- **END TIME:** 2026-08-10T20:14:08.213Z
- **DURATION:** 1209 ms

### EXP-601

- **ROOM:** audio
- **CONTROL:** Sure_To_help_you_check_your_fly_tying_m.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Sure_To_help_you_check_your_fly_tying_m.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Sure_To_help_you_check_your_fly_tying_m.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-601.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:08.216Z
- **END TIME:** 2026-08-10T20:14:09.423Z
- **DURATION:** 1207 ms

### EXP-602

- **ROOM:** audio
- **CONTROL:** recording_20260610_194808_edited.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control recording_20260610_194808_edited.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "recording_20260610_194808_edited.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-602.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:09.425Z
- **END TIME:** 2026-08-10T20:14:10.634Z
- **DURATION:** 1209 ms

### EXP-603

- **ROOM:** audio
- **CONTROL:** Delete recording_20260610_194808_edited.wav
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Delete recording_20260610_194808_edited.wav
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Delete recording_20260610_194808_edited.wav"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-603.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:10.637Z
- **END TIME:** 2026-08-10T20:14:11.845Z
- **DURATION:** 1208 ms

### EXP-604

- **ROOM:** browser
- **CONTROL:** Memory
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Memory
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Memory"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-604.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:11.848Z
- **END TIME:** 2026-08-10T20:14:13.070Z
- **DURATION:** 1222 ms

### EXP-605

- **ROOM:** browser
- **CONTROL:** Documents
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Documents
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Documents"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-605.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:13.073Z
- **END TIME:** 2026-08-10T20:14:14.291Z
- **DURATION:** 1218 ms

### EXP-606

- **ROOM:** browser
- **CONTROL:** Chat
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Chat
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Chat"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-606.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:14.294Z
- **END TIME:** 2026-08-10T20:14:15.529Z
- **DURATION:** 1235 ms

### EXP-607

- **ROOM:** browser
- **CONTROL:** Overview
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Overview
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Overview"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-607.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:15.532Z
- **END TIME:** 2026-08-10T20:14:16.742Z
- **DURATION:** 1210 ms

### EXP-608

- **ROOM:** browser
- **CONTROL:** Session
- **HOW DISCOVERED:** final discovery pass cycle 3
- **STATE:** DEFAULT
- **USER ACTION:** Activate newly found control Session
- **EXPECTED:** Safe response inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Session"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-608.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:14:16.747Z
- **END TIME:** 2026-08-10T20:14:17.957Z
- **DURATION:** 1210 ms

### EXP-900

- **ROOM:** chat
- **CONTROL:** hold to talk
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind hold to talk
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Hold to talk"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-900.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:03.296Z
- **END TIME:** 2026-08-10T20:23:04.300Z
- **DURATION:** 1004 ms

### EXP-901

- **ROOM:** chat
- **CONTROL:** send
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind send
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Send"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-901.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:04.300Z
- **END TIME:** 2026-08-10T20:23:05.305Z
- **DURATION:** 1005 ms

### EXP-902

- **ROOM:** flytying
- **CONTROL:** remove
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind remove
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Remove material"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-902.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:05.305Z
- **END TIME:** 2026-08-10T20:23:06.310Z
- **DURATION:** 1005 ms

### EXP-903

- **ROOM:** flytying
- **CONTROL:** import
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind import
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Import lines"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-903.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:06.310Z
- **END TIME:** 2026-08-10T20:23:07.315Z
- **DURATION:** 1005 ms

### EXP-904

- **ROOM:** flytying
- **CONTROL:** send
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind send
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Send"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-904.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:07.315Z
- **END TIME:** 2026-08-10T20:23:08.323Z
- **DURATION:** 1008 ms

### EXP-905

- **ROOM:** health
- **CONTROL:** search
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind search
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-905.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:08.323Z
- **END TIME:** 2026-08-10T20:23:09.369Z
- **DURATION:** 1046 ms

### EXP-906

- **ROOM:** mission
- **CONTROL:** settings
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind settings
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Settings"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-906.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:09.369Z
- **END TIME:** 2026-08-10T20:23:10.376Z
- **DURATION:** 1007 ms

### EXP-907

- **ROOM:** documents
- **CONTROL:** ask aria
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind ask aria
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Ask Aria"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-907.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:10.376Z
- **END TIME:** 2026-08-10T20:23:11.385Z
- **DURATION:** 1009 ms

### EXP-908

- **ROOM:** documents
- **CONTROL:** cancel
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind cancel
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Cancel"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-908.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:11.385Z
- **END TIME:** 2026-08-10T20:23:12.389Z
- **DURATION:** 1004 ms

### EXP-909

- **ROOM:** documents
- **CONTROL:** close
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind close
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Close"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-909.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:12.389Z
- **END TIME:** 2026-08-10T20:23:13.393Z
- **DURATION:** 1004 ms

### EXP-910

- **ROOM:** memory
- **CONTROL:** refresh
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind refresh
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Refresh machine facts"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-910.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:13.393Z
- **END TIME:** 2026-08-10T20:23:14.396Z
- **DURATION:** 1003 ms

### EXP-911

- **ROOM:** journal
- **CONTROL:** search
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind search
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Search"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-911.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:14.396Z
- **END TIME:** 2026-08-10T20:23:15.400Z
- **DURATION:** 1004 ms

### EXP-912

- **ROOM:** journal
- **CONTROL:** add
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind add
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Add"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-912.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:15.400Z
- **END TIME:** 2026-08-10T20:23:16.405Z
- **DURATION:** 1005 ms

### EXP-913

- **ROOM:** video
- **CONTROL:** save
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind save
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Save clip settings"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-913.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:16.405Z
- **END TIME:** 2026-08-10T20:23:17.410Z
- **DURATION:** 1005 ms

### EXP-914

- **ROOM:** maker
- **CONTROL:** clear
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind clear
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Clear gallery"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-914.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:17.410Z
- **END TIME:** 2026-08-10T20:23:18.415Z
- **DURATION:** 1005 ms

### EXP-915

- **ROOM:** maker
- **CONTROL:** add
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind add
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Add"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-915.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:18.415Z
- **END TIME:** 2026-08-10T20:23:19.422Z
- **DURATION:** 1007 ms

### EXP-916

- **ROOM:** maker
- **CONTROL:** start
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind start
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Start print"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-916.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:19.422Z
- **END TIME:** 2026-08-10T20:23:20.434Z
- **DURATION:** 1012 ms

### EXP-917

- **ROOM:** connections
- **CONTROL:** cancel
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind cancel
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Cancel"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-917.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:20.434Z
- **END TIME:** 2026-08-10T20:23:21.442Z
- **DURATION:** 1008 ms

### EXP-918

- **ROOM:** connections
- **CONTROL:** close
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind close
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Close"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-918.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:21.442Z
- **END TIME:** 2026-08-10T20:23:22.447Z
- **DURATION:** 1005 ms

### EXP-919

- **ROOM:** capabilities
- **CONTROL:** new
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind new
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "New capability"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-919.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:22.447Z
- **END TIME:** 2026-08-10T20:23:23.450Z
- **DURATION:** 1003 ms

### EXP-920

- **ROOM:** audit
- **CONTROL:** run
- **HOW DISCOVERED:** live final absorb
- **STATE:** DEFAULT
- **USER ACTION:** Click novel function kind run
- **EXPECTED:** Responds inside SPA
- **ACTUAL:** `{"clicked": true, "label": "Run audit"}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-920.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:23.450Z
- **END TIME:** 2026-08-10T20:23:24.453Z
- **DURATION:** 1003 ms

### EXP-BUG-002

- **ROOM:** audio
- **CONTROL:** EXP-BUG-002
- **HOW DISCOVERED:** bug recheck
- **STATE:** DEFAULT
- **USER ACTION:** EXP-BUG-002
- **EXPECTED:** prior bug status
- **ACTUAL:** `{"fail": true}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-BUG-002.json`
- **BUG:** BUG-002
- **START TIME:** 2026-08-10T20:23:38.139Z
- **END TIME:** 2026-08-10T20:23:39.342Z
- **DURATION:** 1203 ms

### EXP-BUG-003

- **ROOM:** activity
- **CONTROL:** EXP-BUG-003
- **HOW DISCOVERED:** bug recheck
- **STATE:** DEFAULT
- **USER ACTION:** EXP-BUG-003
- **EXPECTED:** prior bug status
- **ACTUAL:** `{"empty": 183, "loadFails": 3, "total": 200}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-BUG-003.json`
- **BUG:** BUG-003
- **START TIME:** 2026-08-10T20:23:39.342Z
- **END TIME:** 2026-08-10T20:23:55.732Z
- **DURATION:** 16390 ms

### EXP-BUG-006

- **ROOM:** mission
- **CONTROL:** EXP-BUG-006
- **HOW DISCOVERED:** bug recheck
- **STATE:** DEFAULT
- **USER ACTION:** EXP-BUG-006
- **EXPECTED:** prior bug status
- **ACTUAL:** `{"critical": ["All clear", "Long-run stability warning"], "overall": "degraded"}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-BUG-006.json`
- **BUG:** BUG-006
- **START TIME:** 2026-08-10T20:23:55.732Z
- **END TIME:** 2026-08-10T20:23:56.740Z
- **DURATION:** 1008 ms

### EXP-BUG-011

- **ROOM:** front_door
- **CONTROL:** EXP-BUG-011
- **HOW DISCOVERED:** bug recheck
- **STATE:** DEFAULT
- **USER ACTION:** EXP-BUG-011
- **EXPECTED:** prior bug status
- **ACTUAL:** `{"open": false}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-BUG-011.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:56.740Z
- **END TIME:** 2026-08-10T20:23:57.922Z
- **DURATION:** 1182 ms

### EXP-FINAL-PASS

- **ROOM:** all
- **CONTROL:** final discovery scan cycle 1
- **HOW DISCOVERED:** final pass (resume)
- **STATE:** DEFAULT
- **USER ACTION:** Re-enter all rooms; collect labels not in inventory
- **EXPECTED:** Zero new user-accessible function labels
- **ACTUAL:** `{"cycle": 1, "newCount": 203, "sample": ["chat::Skip \u2014 open UI now", "chat::Menu", "chat::Wake: \u2014", "chat::Cursor \u00b7 not synced", "chat::New Chat", "chat::Fork", "chat::Trim", "chat::Clear Main", "chat::Voice input", "chat::Read aloud", "chat::Compare", "chat::Webcam", "chat::New conversation fresh", "chat::Place something here attach", "chat::Read aloud off", "chat::Voice when speaking", "chat::Open the front door Ctrl+K", "chat::Fork thread branch", "chat::Dismiss", "chat::Stop r`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-FINAL-PASS.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:57:30.170Z
- **END TIME:** 2026-08-10T19:58:06.206Z
- **DURATION:** 36036 ms

### EXP-FINAL-PASS-2

- **ROOM:** all
- **CONTROL:** final discovery scan cycle 2
- **HOW DISCOVERED:** final pass (resume)
- **STATE:** DEFAULT
- **USER ACTION:** Re-enter all rooms; collect labels not in inventory
- **EXPECTED:** Zero new user-accessible function labels
- **ACTUAL:** `{"cycle": 2, "newCount": 174, "sample": ["flytying::Sculpin streamer fly", "flytying::Unfavorite pattern", "flytying::Adams dry fly #16 terrestrial \u00b7 9 steps 100", "flytying::Favorite pattern", "flytying::Adams dry fly #18 dry \u00b7 23 steps 100", "flytying::Adams dry fly olive terrestrial \u00b7 10 steps 100", "flytying::Adams Irresistible dry \u00b7 21 steps 100", "flytying::Adams Irresistible dry \u00b7 12 steps 100", "flytying::Adams Irresistible #12 dry \u00b7 6 steps 100", "flytying:`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-2.json`
- **BUG:** —
- **START TIME:** 2026-08-10T19:59:38.109Z
- **END TIME:** 2026-08-10T20:00:14.175Z
- **DURATION:** 36066 ms

### EXP-FINAL-PASS-3

- **ROOM:** all
- **CONTROL:** final discovery scan cycle 3
- **HOW DISCOVERED:** final pass (resume)
- **STATE:** DEFAULT
- **USER ACTION:** Re-enter all rooms; collect labels not in inventory
- **EXPECTED:** Zero new user-accessible function labels
- **ACTUAL:** `{"cycle": 3, "newCount": 107, "sample": ["automation::Run", "automation::Dry run", "automation::Enable", "automation::Edit", "automation::Mute", "automation::Delete", "automation::Schedule", "automation::Create", "automation::Details", "providers::Mission Control \u00b7 Inference", "home_automation::Presence", "home_automation::Security", "home_automation::Open HA", "home_automation::haCopyWebhookBtn", "presence::Security", "presence::Voice", "journal::Writing mode", "journal::Calendar", "journa`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-3.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:01:50.876Z
- **END TIME:** 2026-08-10T20:02:26.914Z
- **DURATION:** 36038 ms

### EXP-FINAL-PASS-FN

- **ROOM:** all
- **CONTROL:** function-normalized final discovery
- **HOW DISCOVERED:** live final gate
- **STATE:** DEFAULT
- **USER ACTION:** Rescan rooms for novel function verbs
- **EXPECTED:** Zero new function kinds
- **ACTUAL:** `{"newCount": 21, "sample": ["chat::hold to talk", "chat::send", "flytying::remove", "flytying::import", "flytying::send", "health::search", "mission::settings", "documents::ask aria", "documents::cancel", "documents::close", "memory::refresh", "journal::search", "journal::add", "video::save", "maker::clear", "maker::add", "maker::start", "connections::cancel", "connections::close", "capabilities::new", "audit::run"]}`
- **STATUS:** **FAIL**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-FN.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:03.296Z
- **END TIME:** 2026-08-10T20:23:03.296Z
- **DURATION:** 17277 ms

### EXP-FINAL-PASS-FN-2

- **ROOM:** all
- **CONTROL:** second function-normalized final discovery
- **HOW DISCOVERED:** live final gate 2
- **STATE:** DEFAULT
- **USER ACTION:** Rescan after absorb
- **EXPECTED:** Zero new function kinds
- **ACTUAL:** `{"newCount": 0, "sample": []}`
- **STATUS:** **PASS**
- **EVIDENCE:** `/tmp/aria-exp-accept/by_id/EXP-FINAL-PASS-FN-2.json`
- **BUG:** —
- **START TIME:** 2026-08-10T20:23:38.139Z
- **END TIME:** 2026-08-10T20:23:38.139Z
- **DURATION:** 0 ms

