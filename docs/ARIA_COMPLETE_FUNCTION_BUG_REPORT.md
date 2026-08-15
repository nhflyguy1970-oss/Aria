# ARIA — Complete Function Bug Report

**Date:** 2026-08-10  
**Phase:** Complete function-by-function live test (discovery only — **no fixes**)  
**Evidence:** `/tmp/aria-fn-accept/evidence/by_id/<TEST-ID>.json`  
**Coverage:** [`ARIA_COMPLETE_FUNCTION_COVERAGE.md`](./ARIA_COMPLETE_FUNCTION_COVERAGE.md)  
**Prior bugs:** BUG-001…BUG-011 remain open (see [`ARIA_LIVE_APPLICATION_BUG_REPORT.md`](./ARIA_LIVE_APPLICATION_BUG_REPORT.md))

---

## Existing bugs reproduced this phase

| Bug | Reproduced via | Notes |
| --- | --- | --- |
| BUG-001 | NAV-007 / LEGACY-001 | Bare `/` living=false while prefs true |
| BUG-002 | AUDIO-001/002 | “Could not load audio status.” |
| BUG-003 | ACTC-003 | 114 empty titles, 9 load-failed of 200 |
| BUG-005 | CHAT-002 | Stop leaves Stop button / incomplete cancel UI |
| BUG-006 | XJ-007 | Mission critical_issues includes “All clear” while degraded |
| BUG-011 | CHAT-010 | Front Door open2 still true after destination click |

---

## BUG-012

```text
BUG ID: BUG-012
SEVERITY: P1
TEST ID: CHAT-001 (also related CHAT-004)
ROOM: chat
SCREEN: Living Room
FUNCTION: Send message / model select
USER ACTION: Type “Reply with exactly: FNACCEPT-ACK-…” + Send; inspect Chat model control
EXPECTED RESULT: Assistant replies with ACK marker; Chat exposes a working model selector
ACTUAL RESULT: Reply stream/content unrelated (image negative-prompt style text “Avoiding: blurry…”); no model <select> with options found in Chat UI
REPRODUCTION STEPS:
  1. Open /?workspace=1#chat
  2. Send ACK marker message via composer Send
  3. Wait for completion; inspect transcript
  4. Search Chat UI for model select options
REPRODUCTION RATE: 1/1 in fire-poll suite
ERROR MESSAGE: (none)
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/CHAT-001.json ; CHAT-004.json
LOG / TRACE: n/a
AFFECTED COMPONENT: chat send / living room composer / chat_model_select
LIKELY ROOT CAUSE: Wrong route/model/context for living chat; model control not wired in living chrome
USER IMPACT: Chat answers incorrectly; cannot change model from Chat
WORKAROUND: /api/chat Form path; Models room (partial)
BLOCKS RELEASE: YES
```

---

## BUG-013

```text
BUG ID: BUG-013
SEVERITY: P1
TEST ID: XJ-001 (related MEMORY-008 partial)
ROOM: chat / memory
SCREEN: Living Room → Memory
FUNCTION: Remember fact then recall across rooms
USER ACTION: Remember QA nickname marker; open Memory; ask chat for nickname
EXPECTED RESULT: Marker stored and recalled
ACTUAL RESULT: chatHas=false, memHas=false for marker XJ1-*
REPRODUCTION STEPS:
  1. Chat: remember marker
  2. Enter Memory room
  3. Chat: ask for nickname
REPRODUCTION RATE: 1/1 this run (earlier API remember/recall had passed in prior audit)
ERROR MESSAGE: n/a
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/XJ-001.json
LOG / TRACE: n/a
AFFECTED COMPONENT: living chat memory path / ACM store visibility
LIKELY ROOT CAUSE: Living UI chat path not completing remember/recall reliably (ties to BUG-012)
USER IMPACT: Memory via Chat untrustworthy in Living Workspace
WORKAROUND: Direct /api/chat Form (prior evidence)
BLOCKS RELEASE: YES
```

---

## BUG-014

```text
BUG ID: BUG-014
SEVERITY: P1
TEST ID: FLY-004 (FLY-005/FLY-006 related)
ROOM: flytying
SCREEN: Streamside cabin / inventory
FUNCTION: Add material via UI; queue pattern
USER ACTION: Attempt Add material with FNACCEPT-MAT-* via visible inputs/buttons; queue pattern
EXPECTED RESULT: Material appears in inventory; queue control works
ACTUAL RESULT: Could not complete add via visible UI controls; queue button not found/clicked false
REPRODUCTION STEPS:
  1. Enter flytying
  2. Open inventory/materials
  3. Fill add fields and click Add/Save
  4. Attempt Queue
REPRODUCTION RATE: 1/1
ERROR MESSAGE: n/a
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/FLY-004.json ; FLY-006.json
LOG / TRACE: n/a
AFFECTED COMPONENT: flytying.js inventory UI
LIKELY ROOT CAUSE: Add/queue controls not discoverable or not wired in living-mounted panel
USER IMPACT: Cannot manage materials/queue from UI as inventoried
WORKAROUND: JSON POST /api/flytying/materials/add (API works; not a UI substitute)
BLOCKS RELEASE: YES
```

---

## BUG-015

```text
BUG ID: BUG-015
SEVERITY: P2
TEST ID: PLAN-002
ROOM: planner
SCREEN: Leather notebook
FUNCTION: Add task via UI
USER ACTION: Enter task text FNACCEPT-TASK-* and click Add/Save
EXPECTED RESULT: Task appears after leave/return and in /api/planner
ACTUAL RESULT: found=false; task not created via UI controls exercised
REPRODUCTION STEPS:
  1. Enter planner
  2. Type into first text input
  3. Click add/save/create
  4. Leave and return; check /api/planner
REPRODUCTION RATE: 1/1
ERROR MESSAGE: n/a
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/PLAN-002.json
LOG / TRACE: n/a
AFFECTED COMPONENT: planner.js living mount
LIKELY ROOT CAUSE: Wrong input targeted or add handler not bound in living stage
USER IMPACT: Cannot create tasks from Planner UI reliably
WORKAROUND: JSON POST /api/planner/tasks
BLOCKS RELEASE: NO
```

---

## BUG-016

```text
BUG ID: BUG-016
SEVERITY: P2
TEST ID: JOURNAL-002
ROOM: journal
SCREEN: Bullet journal
FUNCTION: Add journal entry
USER ACTION: Type t: FNACCEPT-J-* into editor and save
EXPECTED RESULT: Entry appears in journal view
ACTUAL RESULT: hasEditor=true but found=false after save attempt
REPRODUCTION STEPS:
  1. Enter journal
  2. Type into textarea/contenteditable
  3. Click save/add
REPRODUCTION RATE: 1/1
ERROR MESSAGE: n/a
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/JOURNAL-002.json
LOG / TRACE: n/a
AFFECTED COMPONENT: journal UI
LIKELY ROOT CAUSE: Save path not triggered by generic controls / wrong editor field
USER IMPACT: Journal write from UI fails in tested path
WORKAROUND: unknown without deeper UI map
BLOCKS RELEASE: NO
```

---

## BUG-017

```text
BUG ID: BUG-017
SEVERITY: P2
TEST ID: DOCS-002 / XJ-002
ROOM: documents / search
SCREEN: Documents / Search
FUNCTION: Document/search text query
USER ACTION: Set search input value programmatically / UI search
EXPECTED RESULT: Text query accepted; results shown
ACTUAL RESULT: InvalidStateError setting value on file input (first input is type=file)
REPRODUCTION STEPS:
  1. Enter documents (or search in cross journey)
  2. Target first input for query
REPRODUCTION RATE: 1/1
ERROR MESSAGE: Failed to set the 'value' property on 'HTMLInputElement': This input element accepts a filename…
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/DOCS-002.json ; XJ-002.json
LOG / TRACE: DOM exception
AFFECTED COMPONENT: documents/search UI input ordering / labeling
LIKELY ROOT CAUSE: Primary interactive input is file upload; text search control not first/obvious
USER IMPACT: Easy to miss text search; automation and users may hit upload instead
WORKAROUND: Locate dedicated search box if present deeper in panel
BLOCKS RELEASE: NO
```

---

## BUG-018

```text
BUG ID: BUG-018
SEVERITY: P2
TEST ID: MODELS-002
ROOM: providers
SCREEN: Models
FUNCTION: Switch model via UI select
USER ACTION: Enter Models; change role/select
EXPECTED RESULT: Select options available; backend model updates
ACTUAL RESULT: hasSelect=false in Models room panel
REPRODUCTION STEPS:
  1. AriaHouse.enter('providers')
  2. Look for select controls / role editors
REPRODUCTION RATE: 1/1
ERROR MESSAGE: n/a
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/MODELS-002.json
LOG / TRACE: n/a
AFFECTED COMPONENT: models home UI in living workspace
LIKELY ROOT CAUSE: Selects inside nested tabs not mounted until further clicks; or living mount incomplete
USER IMPACT: Cannot verify/switch models from Models room as tested
WORKAROUND: API /api/chat/model ; /api/models/switch
BLOCKS RELEASE: NO
```

---

## BUG-019

```text
BUG ID: BUG-019
SEVERITY: P2
TEST ID: SETTINGS-002
ROOM: settings
SCREEN: Settings
FUNCTION: Change theme/density and persist
USER ACTION: Toggle theme/density/checkbox controls
EXPECTED RESULT: Pref values change and persist after navigate
ACTUAL RESULT: changed=false; theme remained dark before/mid/after
REPRODUCTION STEPS:
  1. Enter settings
  2. Click theme/density/checkbox controls found
  3. Navigate away and back
REPRODUCTION RATE: 1/1
ERROR MESSAGE: n/a
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/SETTINGS-002.json
LOG / TRACE: n/a
AFFECTED COMPONENT: settings UI / AriaUiPrefs bindings
LIKELY ROOT CAUSE: Clicked controls did not map to prefs writers; or living settings is display-only subset
USER IMPACT: Settings changes appear not to apply
WORKAROUND: Direct AriaUiPrefs in console (not user path)
BLOCKS RELEASE: NO
```

---

## BUG-020

```text
BUG ID: BUG-020
SEVERITY: P2
TEST ID: HA-001
ROOM: home_automation
SCREEN: Home control
FUNCTION: Room open / status
USER ACTION: Enter home_automation
EXPECTED RESULT: Connected or clear setup without hard failure text
ACTUAL RESULT: Panel shows failure text matching /failed|Could not load/ during enter check
REPRODUCTION STEPS:
  1. Enter home_automation
  2. Read status strip
REPRODUCTION RATE: Intermittent historically; FAIL this run
ERROR MESSAGE: (panel text includes failure phrasing — see evidence)
EVIDENCE FILE: /tmp/aria-fn-accept/evidence/by_id/HA-001.json
LOG / TRACE: n/a
AFFECTED COMPONENT: smarthome panel
LIKELY ROOT CAUSE: Race / entity load failure messaging
USER IMPACT: Smart home looks broken on enter
WORKAROUND: Re-enter; /api/homeassistant/status often ok
BLOCKS RELEASE: NO
```

---

## BUG-021

```text
BUG ID: BUG-021
SEVERITY: P2
TEST ID: CHAT-008 / CHAT-010 / NAV-003
ROOM: chat / Front Door
SCREEN: Living chrome
FUNCTION: Open tasks; Front Door enter+close; House Controls
USER ACTION: Click Open tasks; Front Door → Memory; open House Controls
EXPECTED RESULT: Tasks surface; door closes on enter; House Controls section opens
ACTUAL RESULT: Open tasks click false; Front Door remained open after Memory click (cur stayed chat); House Controls not opened
REPRODUCTION STEPS: See evidence JSON for each TEST ID
REPRODUCTION RATE: 1/1 this suite
ERROR MESSAGE: n/a
EVIDENCE FILE: CHAT-008.json ; CHAT-010.json ; NAV-003.json
LOG / TRACE: n/a
AFFECTED COMPONENT: living chrome / Front Door / task affordances
LIKELY ROOT CAUSE: Controls not labeled as expected or door selection doesn’t call enter/close reliably
USER IMPACT: Navigation/control discovery broken in places
WORKAROUND: AriaHouse.enter / hash routes
BLOCKS RELEASE: NO
```

---

## BUG-022

```text
BUG ID: BUG-022
SEVERITY: P3
TEST ID: HEALTH-004 / ONBOARD-002 / CHAT-013
ROOM: health / onboarding / chat
SCREEN: various
FUNCTION: Health upload; Help learn dialog; empty send
USER ACTION: Find health file input; open Help ARIA learn; send empty message
EXPECTED RESULT: Upload control present; onboarding help reachable; empty send no-op without busy Stop
ACTUAL RESULT: No health file input found; Help learn not opened; empty send observed Stop still true (busy state leak)
REPRODUCTION STEPS: See per-id evidence
REPRODUCTION RATE: 1/1
ERROR MESSAGE: n/a
EVIDENCE FILE: HEALTH-004.json ; ONBOARD-002.json ; CHAT-013.json
LOG / TRACE: n/a
AFFECTED COMPONENT: health upload affordance; onboarding entry; chat busy state
LIKELY ROOT CAUSE: Missing/hidden upload; onboarding entry not in current chrome; Stop sticky from prior chat (BUG-005 family)
USER IMPACT: Minor–moderate UX gaps
WORKAROUND: vary
BLOCKS RELEASE: NO
```

---

## Bug counts (this phase new)

| Severity | New IDs | Count |
| -------- | --- | ----: |
| P0 | — | 0 |
| P1 | BUG-012, BUG-013, BUG-014 | 3 |
| P2 | BUG-015…BUG-021 | 7 |
| P3 | BUG-022 | 1 |

**Prior open (BUG-001…011):** still valid; several reproduced above.

---

## Non-bug findings

### MISSING CAPABILITY
- Isolated coding sandbox / dry-run Apply for safe live acceptance of CODING-002 apply step.
- Safe HA QA scene entity for HA-002.

### DESIGN PROBLEM
- Documents/Search primary input can be a file input (BUG-017).
- Front Door destination click does not always close/enter (BUG-021 / BUG-011).

### PERFORMANCE PROBLEM
- Chat UI waits are long; ACK path failed with unrelated content (routing more than latency).

### RELIABILITY PROBLEM
- HA status failure text on enter; Activity Center spam (BUG-003).

### DOCUMENTATION/DISCOVERABILITY
- House Controls / Open tasks / Help-learn entry points not reliably discoverable by label.
