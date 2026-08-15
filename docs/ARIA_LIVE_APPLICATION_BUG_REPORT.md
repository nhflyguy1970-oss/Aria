# ARIA — Live Application Bug Report

**Date:** 2026-08-10  
**Phase:** Complete live application / room-by-room acceptance (discovery only)  
**Rule:** No fixes applied during this phase.  
**Evidence root:** `/tmp/aria-app-accept/`

---

## BUG-001

```text
BUG ID: BUG-001
SEVERITY: P1
ROOM: Shell / Workspace boot
SCREEN: Bare browser `/` vs Living Workspace
FUNCTION: Living Workspace enablement
USER ACTION: Open http://127.0.0.1:8765/ as a normal browser user
EXPECTED RESULT: With prefs.livingWorkspace === true, Jeff gets the Living Workspace (or a clear choice)
ACTUAL RESULT: Legacy shell loads; living-workspace class is NOT applied. Living Workspace requires ?workspace=1 / Electron / ?app=1 (workspace.js prefsEnabled)
REPRODUCTION STEPS:
  1. Confirm AriaUiPrefs.livingWorkspace === true
  2. Open /
  3. Observe legacy tabs shell; documentElement lacks living-workspace
  4. Open /?workspace=1 → Living Workspace appears
REPRODUCTION RATE: 100%
EVIDENCE: Live CDP prefs dump; workspace.js prefsEnabled logic; screenshots of both surfaces
ERROR MESSAGE: (none — silent wrong surface)
LOG / TRACE: n/a
AFFECTED COMPONENT: jarvis/gui/static/workspace/workspace.js
LIKELY ROOT CAUSE: Browser default path ignores livingWorkspace pref unless query/Electron markers present
USER IMPACT: Browser users miss the intended house experience and hit legacy shell
WORKAROUND: Use /?workspace=1 or Electron shell
BLOCKS RELEASE: YES
```

---

## BUG-002

```text
BUG ID: BUG-002
SEVERITY: P1
ROOM: audio
SCREEN: Audio studio
FUNCTION: AUDIO-001 load status bar
USER ACTION: Enter Audio via Front Door or AriaHouse.enter('audio')
EXPECTED RESULT: Status shows Whisper/ffmpeg/TTS/devices (API /api/audio/status returns ok:true)
ACTUAL RESULT: UI shows “Could not load audio status.” (and toast). API independently returns 200 OK with full device payload.
REPRODUCTION STEPS:
  1. Open /?workspace=1
  2. Front Door → Audio
  3. Observe status text “Could not load audio status.”
  4. curl /api/audio/status → ok:true
REPRODUCTION RATE: High during live session (reproduced on enter; API always healthy)
EVIDENCE: accept_log AUDIO-UI / ROOM-audio; a11y snapshot name “Could not load audio status.”; /tmp/aria-app-accept/api/probe3.txt
ERROR MESSAGE: Could not load audio status.
LOG / TRACE: Client catch in audio.js loadAudioStatus()
AFFECTED COMPONENT: jarvis/gui/static/audio.js (+ living stage mount timing)
LIKELY ROOT CAUSE: Client-side exception while rendering status (or aborted/racy fetch) despite healthy API; needs stack capture in repair phase
USER IMPACT: Audio room appears broken; blocks trust in audio/TTS workflows
WORKAROUND: Use Voice room / API; refresh sometimes
BLOCKS RELEASE: YES
```

---

## BUG-003

```text
BUG ID: BUG-003
SEVERITY: P1
ROOM: Activity Center (global)
SCREEN: Notifications inbox
FUNCTION: ACTC-001 durable failure inbox integrity
USER ACTION: Use the app (including room navigation)
EXPECTED RESULT: Actionable, titled failures; inbox not flooded with empty/noise events; production integrity remains readable
ACTUAL RESULT: 200 unread, ~30 failures, ~22 warnings. Top errors include Planner/Calendar/Integrations/Capabilities/Home load failed. 137/200 items have empty titles. Many look like toast→inbox spam from aborted loads.
REPRODUCTION STEPS:
  1. Open Living Workspace
  2. Navigate multiple rooms (or run room sweep)
  3. Inspect Activity Center summary / GET /api/activity/inbox?limit=200
REPRODUCTION RATE: 100% in this environment
EVIDENCE: /tmp/aria-app-accept/api/activity_inbox.json; a11y “200 unread in Activity Center”
ERROR MESSAGE: Integrations load failed; Capabilities load failed; Planner load failed — retry from the view; Home load failed; Calendar load failed; etc.
LOG / TRACE: Activity items source=toast, meta={}
AFFECTED COMPONENT: activity_store / showAriaToast → inbox; room home loaders
LIKELY ROOT CAUSE: Fetch aborts / races on rapid navigation recorded as durable errors; empty-title info events not filtered
USER IMPACT: Jeff cannot trust the inbox; real failures buried; Production Integrity noise
WORKAROUND: Manually clear inbox (does not fix root)
BLOCKS RELEASE: YES
```

---

## BUG-004

```text
BUG ID: BUG-004
SEVERITY: P2
ROOM: home, planner, calendar, capabilities, integrations (multi)
SCREEN: Product homes
FUNCTION: Room home load under navigation
USER ACTION: Enter room (especially during concurrent chat/stop or rapid room changes)
EXPECTED RESULT: Homes load or show a single recoverable error
ACTUAL RESULT: Toast/inbox “X load failed” even though corresponding APIs return 200 when called directly afterward (dashboard/home, planner, capabilities/product/home, integrations/product/home, calendar/day)
REPRODUCTION STEPS:
  1. Sweep rooms quickly via AriaHouse.enter
  2. Observe toasts / inbox errors
  3. curl the same product home endpoints → ok:true
REPRODUCTION RATE: Intermittent; high under rapid navigation
EVIDENCE: activity inbox; API probe2/probe3; accept_log
ERROR MESSAGE: Home load failed; Planner load failed — retry from the view; …
LOG / TRACE: toast-sourced activity events
AFFECTED COMPONENT: dashboard_home.js, planner.js, calendar.js, capabilities_home.js, integrations_home.js + fetch lifecycle
LIKELY ROOT CAUSE: Unhandled AbortError / navigation tear-down treated as hard failure
USER IMPACT: False “broken room” signals; trains distrust
WORKAROUND: Re-enter room / Refresh
BLOCKS RELEASE: NO (but amplifies BUG-003)
```

---

## BUG-005

```text
BUG ID: BUG-005
SEVERITY: P2
ROOM: chat
SCREEN: Living Room composer
FUNCTION: CHAT-001 / CHAT-002 reply lifecycle UI
USER ACTION: Send “Reply with exactly: ACK LIVEAPP-001”; later Stop
EXPECTED RESULT: Thinking clears when reply arrives; Stop only while in-flight; status returns to listening
ACTUAL RESULT: UI showed Thinking… past 60s with empty assistant bubble while Form /api/chat ACK completed in ~18s in parallel. After Stop, reply text was present but status later stuck on “Stopping…”.
REPRODUCTION STEPS:
  1. /?workspace=1#chat
  2. Send ACK LIVEAPP-001 via UI
  3. Observe long Thinking / empty bubble
  4. Optionally Stop; observe Stopping… persistence
REPRODUCTION RATE: Reproduced once in session (UI path); API path reliable
EVIDENCE: screenshots 02-chat-after-send; CDP chat tails; /tmp/aria-app-accept/api/chat_ack.json; status Stopping… still visible later
ERROR MESSAGE: (UI) Thinking… / Stopping…
LOG / TRACE: n/a captured server-side
AFFECTED COMPONENT: chat_send / living room stream UI
LIKELY ROOT CAUSE: Stream/UI state machine desync vs non-stream completion
USER IMPACT: Chat feels hung; Stop leaves sticky state
WORKAROUND: Use API or reload UI
BLOCKS RELEASE: NO (major UX; escalate if persistent hang without reply)
```

---

## BUG-006

```text
BUG ID: BUG-006
SEVERITY: P2
ROOM: mission
SCREEN: Mission Control health
FUNCTION: MISSION-001 health summary honesty
USER ACTION: Read Mission Control / GET /api/mission-control/health
EXPECTED RESULT: critical_issues lists only real issues; overall status matches list
ACTUAL RESULT: overall=degraded while critical_issues includes “All clear” alongside “Long-run stability warning”
REPRODUCTION STEPS:
  1. curl /api/mission-control/health
  2. Observe critical_issues array
REPRODUCTION RATE: 100% during session
EVIDENCE: /tmp/aria-app-accept/api/mission_health.json
ERROR MESSAGE: n/a
LOG / TRACE: n/a
AFFECTED COMPONENT: mission_control aggregator / health composer
LIKELY ROOT CAUSE: Sentinel “All clear” not filtered when other warnings present
USER IMPACT: Conflicting ops story; undermines Mission Control trust
WORKAROUND: Ignore “All clear” when degraded
BLOCKS RELEASE: NO
```

---

## BUG-007

```text
BUG ID: BUG-007
SEVERITY: P2
ROOM: home_automation
SCREEN: Home Automation
FUNCTION: HA-001 status / entity load
USER ACTION: Enter Home Automation
EXPECTED RESULT: Stable Connected/setup state; entity refresh honest
ACTUAL RESULT: First enter showed “Home failed” / “Could not load HA entities” in activity; later enter showed “Connected · http://127.0.0.1:8123”. /api/homeassistant/status ok connected; wrong path /api/ha/entities 404 (UI uses other routes).
REPRODUCTION STEPS:
  1. Enter home_automation during load contention
  2. Note failure toasts
  3. Re-enter → Connected
REPRODUCTION RATE: Intermittent
EVIDENCE: room_sweep home_automation preview; activity “Could not load HA entities”; smarthome product home 200
ERROR MESSAGE: Home failed; Could not load HA entities
LOG / TRACE: activity toast items
AFFECTED COMPONENT: smarthome / HA panel loaders
LIKELY ROOT CAUSE: Race + possibly stale endpoint references in some paths
USER IMPACT: Smart home looks broken then fine
WORKAROUND: Refresh / re-enter
BLOCKS RELEASE: NO
```

---

## BUG-008

```text
BUG ID: BUG-008
SEVERITY: P2
ROOM: memory / chat
SCREEN: Chat remember flow
FUNCTION: MEMORY chat store quality (CHAT-011)
USER ACTION: “Please remember for testing: my acceptance token is ACCEPT_TOKEN_…. Confirm you stored it.”
EXPECTED RESULT: Stores clean fact (token value / concise proposition)
ACTUAL RESULT: Stored verbose string including instructional tail (“Confirm you stored it.”). Recall returned token (pass) but memory quality is dirty.
REPRODUCTION STEPS:
  1. POST /api/chat remember prompt
  2. Ask “What is my acceptance token?”
  3. Inspect stored phrasing in reply/memory
REPRODUCTION RATE: 100% for this prompt shape
EVIDENCE: /tmp/aria-app-accept/api/journey.json
ERROR MESSAGE: n/a
LOG / TRACE: n/a
AFFECTED COMPONENT: ACM remember / memory engine normalization
LIKELY ROOT CAUSE: Insufficient scrubbing of imperative/confirmational clauses on store
USER IMPACT: Pollutes autobiography; confusing Memory room entries
WORKAROUND: Manually forget / restate cleanly
BLOCKS RELEASE: NO
```

---

## BUG-009

```text
BUG ID: BUG-009
SEVERITY: P2
ROOM: integrity
SCREEN: Truth / Integrity room
FUNCTION: INTEGRITY-001 mount
USER ACTION: AriaHouse.enter('integrity')
EXPECTED RESULT: Integrity panel visible with score/controls every time
ACTUAL RESULT: Intermittent empty panel (0 controls / empty preview) during sweep; Integrity region also remains in accessibility tree while other rooms are current (stale mount)
REPRODUCTION STEPS:
  1. Sweep rooms including integrity
  2. Observe empty integrity enter
  3. Later, while in chat, a11y still exposes Integrity “Truth / Score 100”
REPRODUCTION STEPS RATE: Intermittent empty; stale DOM common
EVIDENCE: accept_log ROOM-integrity; a11y snapshots; CDP integrityInDom:true while current=chat
ERROR MESSAGE: (empty UI)
LOG / TRACE: n/a
AFFECTED COMPONENT: house_host / integrity room mount
LIKELY ROOT CAUSE: Native room mount/unmount incomplete
USER IMPACT: Integrity hard to reach intermittently; a11y/confusion
WORKAROUND: Re-enter / use Mission tools
BLOCKS RELEASE: NO
```

---

## BUG-010

```text
BUG ID: BUG-010
SEVERITY: P3
ROOM: platform
SCREEN: OpenAPI
FUNCTION: Developer/API schema endpoint
USER ACTION: GET /openapi.json
EXPECTED RESULT: 200 OpenAPI document
ACTUAL RESULT: HTTP 500 Internal Server Error
REPRODUCTION STEPS: curl http://127.0.0.1:8765/openapi.json
REPRODUCTION RATE: 100%
EVIDENCE: /tmp/aria-app-accept/api/probe2.txt
ERROR MESSAGE: Internal Server Error
LOG / TRACE: not present as error_id in jarvis.log tail during capture
AFFECTED COMPONENT: FastAPI OpenAPI generation / route registration
LIKELY ROOT CAUSE: Schema generation exception (duplicate operation ids or bad annotations)
USER IMPACT: Tooling/docs discovery broken; not Jeff daily path
WORKAROUND: Use code/routes inventory
BLOCKS RELEASE: NO
```

---

## BUG-011

```text
BUG ID: BUG-011
SEVERITY: P3
ROOM: Front Door / chat
SCREEN: Living chrome
FUNCTION: NAV-002 door close + status copy
USER ACTION: Open Front Door, select Audio; also after Stop on chat
EXPECTED RESULT: Door closes on destination; status never stuck on Stopping…
ACTUAL RESULT: Observed Front Door still presenting room list after Audio selection until Return; chat status “Stopping…” remained visible after stop completed
REPRODUCTION STEPS:
  1. Open Front Door → Audio
  2. Note door still in a11y tree
  3. After chat Stop, note Stopping… status
REPRODUCTION RATE: Intermittent / session-observed
EVIDENCE: browser snapshots during Audio select; CDP stoppingVisible:true
ERROR MESSAGE: Stopping…
LOG / TRACE: n/a
AFFECTED COMPONENT: AriaFrontDoor + living status line
LIKELY ROOT CAUSE: State not cleared on navigation/cancel completion
USER IMPACT: Confusing chrome; feels unfinished
WORKAROUND: Return / reload
BLOCKS RELEASE: NO
```

---

## Non-bug observations

### Missing capability
- Bare browser has no obvious in-UI switch to force Living Workspace when prefs say on but shell stays legacy (users must know `?workspace=1`).

### Design problem
- Activity Center conflates ephemeral toast failures with durable “needs attention,” so Mission/Notifications feel permanently dirty.
- Accessibility tree exposes many hidden dialogs/modals at once (lock, inpaint, rule editor, etc.), making automation/a11y noisy.

### Performance problem
- Living UI chat path felt much slower / stickier than direct `/api/chat` Form (~18s) for the same trivial ACK.
- Room home loads under contention produce cascading failure toasts.

### Reliability problem
- Home Automation, Planner/Calendar/Home/Capabilities/Integrations loaders are race-sensitive.
- Audio status UI fails while API is healthy.

### Documentation problem
- Inventory of correct product API paths is not discoverable via `/openapi.json` (500).
- Living vs legacy entry conditions are not obvious to a browser user.

### Research quality note (not graded as app crash)
- Live research reply claimed “Python 3.16” as current stable from python.org snippets. Trust-suite architecture previously passed; treat as residual synthesis/source-ranking observation for repair backlog, not a room-load bug.

---

## Bug summary counts

| Severity | Count |
| -------- | ----: |
| P0       |     0 |
| P1       |     3 |
| P2       |     6 |
| P3       |     2 |
| **Total**| **11** |
