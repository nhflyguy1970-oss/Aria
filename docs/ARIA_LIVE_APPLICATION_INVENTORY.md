# ARIA — Live Application Inventory

**Date:** 2026-08-10  
**Authority:** Running application at `http://127.0.0.1:8765` (UI version 5.16.74, app 3.1.0)  
**Surfaces discovered:** Living Workspace (`/?workspace=1`) and Legacy Shell (`/`)  
**Rule:** Discovery only — no code fixes during this phase.

---

## Surface map

### A. Living Workspace (Jeff’s intended house)

| Condition | Result |
| --- | --- |
| `/?workspace=1` or Electron (`jarvis-app` / `?shell=electron` / `?app=1`) | Living Workspace enabled |
| Bare `/` in browser even when `livingWorkspace: true` in prefs | **Legacy shell** — living class not applied |

Primary chrome:

- Living Room / Chat composition (“Aria is here”, Say anything…)
- Front Door (“Where would you like to go?”) — room list, House Controls, Tools, Advanced
- Mini chat, More menu, Hold to talk, Send / Stop
- Activity Center / Notifications (durable inbox)
- Modals: New Chat, Memory sheet, Command palette, Job center, Lock, Settings shortcuts, Layouts, View Paths, Rule editor, etc.

### B. Legacy Shell

Visible when Living Workspace is off: classic `.app` shell with ~32 `view-tab` destinations (Chat, Home, Automation, Mission Control, Models, Coding, Planner, Calendar, Fly tying, Projects, Maker, Browser, Security, Presence, System, Cert, Capabilities, Integrations, Search, Settings, Voice, Vision, Audio, Bullet Journal, Health, Memory, Gallery, Video, Meme, Documents, Connections, Actions).

---

## Rooms (registry = source of truth)

34 rooms from `AriaWorkspaceRegistry.rooms`:

| ID | Metaphor / hero | viewId | Test ID prefix |
| --- | --- | --- | --- |
| chat | Living room / Conversation | chat | CHAT |
| flytying | Streamside cabin / The fly | flytying | FLY |
| health | Wellness clinic / Jeff’s today | health | HEALTH |
| mission | Aerospace ops / The system | workstation | MISSION |
| documents | Private library / Knowledge | documents | DOCS |
| planner | Leather notebook / Today’s page | planner | PLAN |
| calendar | Wall calendar / The week | calendar | CAL |
| gallery | Museum / Artwork | gallery | GALLERY |
| search | Research study / Discovery | search | SEARCH |
| coding | Engineering studio / Current work | coding | CODING |
| projects | Creative workshop / Alive work | projects | PROJ |
| memory | Memory archive / Personal history | memory | MEMORY |
| voice | Presence / Speaking | voice | VOICE |
| repair | Restoration bench / Evidence | workstation | REPAIR |
| integrity | Quiet caretaker / Truth | integrity | INTEGRITY |
| home | Foyer / Orientation | dashboard | HOME |
| automation | Automation loft / Skills | automation | AUTO |
| providers | Provider bay / Models | models | MODELS |
| home_automation | Home control / Environment | homeAutomation | HA |
| presence | Presence / Camera & gestures | presence | PRES |
| journal | Bullet journal / Daily pages | journal | JOURNAL |
| video | Video studio / Motion | video | VIDEO |
| audio | Audio studio / Sound | audio | AUDIO |
| browser | Browser / The web | browser | BROWSER |
| maker | Maker lab / CAD & print | maker | MAKER |
| meme | Meme studio / Memes | meme | MEME |
| vision | Vision bench / Seeing | vision | VISION |
| connections | Connections / Relationships | connections | CONN |
| settings | Settings / Preferences | settings | SETTINGS |
| capabilities | Capabilities / Extensions | capabilities | CAPS |
| integrations | Integrations / Keys & services | integrations | INTEG |
| audit | System audit / Audit | audit | AUDIT |
| security | Security / Lock & trust | security | SEC |
| actions | Action history / What happened | actions | ACT |

### Activities (intent → room)

converse, coding, flytying, doctor_visit, health, planning, calendar, research, reading, search, image_creation, projects, (+ systems/automation family from registry).

### Tools (sheet / hud / mission / spotlight)

ocr, voice, vision, browser, clipboard, docker, git, notifications, providers, automation, repair, integrity, models, calendar, gallery, search, projects, terminal.

---

## Inventory entries (ROOM → SCREEN → FUNCTION → USER ACTION → EXPECTED → DEPENDENCIES)

### CHAT — Living Room

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| CHAT-001 | Send message | Type + Send | Reply in thread; status returns to listening | `/api/chat`, Ollama |
| CHAT-002 | Stop responding | Click Stop | Stream/request cancels; UI leaves Stopping/Thinking | chat cancel path |
| CHAT-003 | New chat | New Chat dialog | Fresh thread created | `/api/chat/new` |
| CHAT-004 | Model select | Change Chat model control | Subsequent replies use selected model | `/api/chat/model`, `/api/models/*` |
| CHAT-005 | Attach | Attach file/image | Attachment accepted or clear error | upload APIs |
| CHAT-006 | Hold to talk | PTT | Transcription into composer or clear error | `/api/audio/*`, Whisper |
| CHAT-007 | Read aloud | Toggle | TTS of reply | Piper/TTS |
| CHAT-008 | Open tasks | Open tasks | Planner/tasks surface | planner |
| CHAT-009 | Mini chat | Open mini chat | Floating chat works | same chat API |
| CHAT-010 | Front Door | Open the Front Door | Destination list; enter room; door closes | `AriaFrontDoor` |
| CHAT-011 | Memory via chat | “Remember …” then recall | Fact stored + retrieved without inventing | ACM / memory |
| CHAT-012 | Research via chat | “Research online …” | Search + synthesis + sources | web_search |
| CHAT-013 | Empty send | Send empty | No-op or validation | UI |
| CHAT-014 | Double send | Rapid double Submit | No duplicate corruption; busy guard | chat lock |

### FRONT DOOR / NAV

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| NAV-001 | List rooms | Open Front Door | All rooms listed | registry |
| NAV-002 | Enter room | Choose destination | Correct room mounts; door closes | `AriaHouse.enter` |
| NAV-003 | House Controls | Open control | Controls available (models, theme, integrity…) | chrome |
| NAV-004 | Tools | Invoke tool | Tool sheet/hud opens | tools registry |
| NAV-005 | Return | Return | Door closes; prior room remains | Front Door |
| NAV-006 | Hash deep-link | `/?workspace=1#flytying` | Lands in fly room | workspace boot |
| NAV-007 | Legacy vs living | Open `/` vs `/?workspace=1` | Documented surface difference | workspace.js prefsEnabled |
| NAV-008 | Cross-room A→B→A | Navigate sequence | No stale/duplicate UI; state rules honored | house stage |
| NAV-009 | Reload | Browser refresh | Session/prefs restore as designed | localStorage + APIs |

### MEMORY

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| MEMORY-001 | Open Memory room | Enter memory | Home loads (about you, beliefs, conflicts…) | `/api/memory/home` |
| MEMORY-002 | Browse namespaces | Filter/list | Entries listed | `/api/memory/all` |
| MEMORY-003 | Search | Query | Relevant hits | memory search |
| MEMORY-004 | Forget | Forget flow | Preview + confirm removes | `/api/memory/{id}/forget*` |
| MEMORY-005 | Conflicts | Resolve | Conflict coach/resolve works | `/api/memory/conflicts*` |
| MEMORY-006 | Import/export | Export then import | Round-trip | `/api/memory/export\|import` |
| MEMORY-007 | Settings | Change auto-memory prefs | Persists | `/api/memory/settings` |
| MEMORY-008 | Chat→Memory | Remember in chat; open Memory | Fact visible in Memory UI | ACM bridge |

### FLY TYING

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| FLY-001 | Open room | Enter flytying | Catalog status, pattern of day, models | `/api/flytying/product/home` |
| FLY-002 | Search patterns | Search “woolly bugger” | Pattern results | fly search index |
| FLY-003 | Inventory list | View materials | Items listed | `/api/flytying/product/inventory` |
| FLY-004 | Add material | Add via UI | Item persists; appears in list | `POST /api/flytying/materials/add` (JSON) |
| FLY-005 | Update/delete material | Edit/remove | CRUD completes | PATCH/DELETE materials |
| FLY-006 | Queue | Add to queue | Queue updates | `/api/flytying/queue/add` |
| FLY-007 | Session | Start bench session | Session starts | product/sessions |
| FLY-008 | Fly chat | Ask fly question in room | Fly-scoped help, no steal of unrelated | `/api/flytying/chat` |
| FLY-009 | Gallery link | Open Gallery from fly | Gallery mounts | house nav |

### HEALTH

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| HEALTH-001 | Open Health | Enter health | Today / PHR surfaces without writing live PHR from QA | health APIs |
| HEALTH-002 | Log reading | Add safe test metric if UI allows | Persists only if intended store | health product |
| HEALTH-003 | Doctor visit activity | Start doctor_visit | Confirmable activity | activity engine |
| HEALTH-004 | Upload | Upload doc | Accept/reject gracefully | upload |

### PLANNER / CALENDAR / JOURNAL

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| PLAN-001 | Open Planner | Enter planner | Tasks/events/timers load | `/api/planner` |
| PLAN-002 | Add task | Create task | Task appears; persists after leave/return | `POST /api/planner/tasks` JSON `{text}` |
| PLAN-003 | Complete/delete task | Complete / delete | State updates; undo if offered | planner APIs |
| PLAN-004 | Events/timers/alarms | Create each | Persist | planner APIs |
| CAL-001 | Open Calendar | Enter calendar | Day/week loads | `/api/calendar/day` |
| CAL-002 | Navigate days | Next/prev | Correct day | calendar |
| JOURNAL-001 | Open Journal | Enter journal | Pages/keys load | `/api/journal` |
| JOURNAL-002 | Add entry | Write note | Persists | journal APIs |
| JOURNAL-003 | Promote to Planner | Promote task | Appears in Planner | planner bridge |

### SEARCH / DOCUMENTS / CONNECTIONS

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| SEARCH-001 | Open Search | Enter search | Federated search home | search product |
| SEARCH-002 | Run search | Query / empty / nonsense | Results or empty state; no crash | search APIs |
| SEARCH-003 | Facets/history/saved | Use filters/save | Persist saved searches | search product |
| DOCS-001 | Open Documents | Enter documents | Library lists | `/api/documents` |
| DOCS-002 | Search docs | Query | Hits match corpus | `/api/documents/search` |
| DOCS-003 | Upload/open/delete | CRUD file | Lifecycle works | documents APIs |
| CONN-001 | Open Connections | Enter connections | Relationship home | `/api/connections/home` |

### CODING / PROJECTS

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| CODING-001 | Open Coding | Enter coding | Coding home | `/api/coding/home` |
| CODING-002 | Propose/apply | Propose change | Proposal → review → apply/undo honesty | `/api/apply`, proposals |
| PROJ-001 | Open Projects | Enter projects | Project list / active | `/api/projects` |
| PROJ-002 | Switch project | Select project | Context switches | projects |
| PROJ-003 | Ask in project | Chat about project | Correct project context | chat + projects |

### GALLERY / VIDEO / MEME / VISION / MAKER

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| GALLERY-001 | Open Gallery | Enter gallery | Images list | `/api/gallery` |
| GALLERY-002 | Generate/edit | Generate / inpaint | Job Center tracks; result appears | Comfy/media jobs |
| VIDEO-001 | Open Video | Enter video | Studio UI | video APIs |
| MEME-001 | Open Meme | Enter meme | Gallery empty-or-list | `/api/meme-gallery` |
| VISION-001 | Open Vision | Enter vision | Product home / analyze | `/api/vision/*` |
| MAKER-001 | Open Maker | Enter maker | CAD/print UI | maker APIs |

### AUDIO / VOICE / PRESENCE

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| AUDIO-001 | Open Audio | Enter audio | Status bar loads (Whisper/ffmpeg/TTS/devices) | `/api/audio/status` |
| AUDIO-002 | Recent library | Browse recent | Lists recordings/generated | `/api/audio/recent` |
| VOICE-001 | Open Voice | Enter voice | Voice prefs/state | `/api/voice/settings` |
| PRES-001 | Open Presence | Enter presence | Camera/gesture UI or clear unavailable | presence |

### HOME AUTOMATION / SECURITY / AUTOMATION

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| HA-001 | Open Home Automation | Enter home_automation | Status Connected or clear setup | `/api/homeassistant/status`, smarthome product |
| HA-002 | Scenes/favorites | Apply scene | Device action or honest failure | HA |
| HA-003 | Entity search | Search entities | Results or empty | smarthome APIs |
| SEC-001 | Open Security | Enter security | Lock/PIN/trust controls | security APIs |
| AUTO-001 | Open Automation | Enter automation | Rules list | `/api/automation/rules` |
| AUTO-002 | Rule editor | Create/edit rule | Saves; enable works | automation engine |

### MISSION / REPAIR / INTEGRITY / CAPS / INTEG / AUDIT / ACTIONS / HOME / SETTINGS / MODELS / BROWSER

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| MISSION-001 | Open Mission Control | Enter mission | Health/ops cards | `/api/mission-control/health` |
| REPAIR-001 | Open Repair | Enter repair | Guided Repair evidence | workstation |
| INTEGRITY-001 | Open Integrity | Enter integrity | Truth score / scan | `/api/integrity/home` |
| CAPS-001 | Open Capabilities | Enter capabilities | Capability list | `/api/capabilities/product/home` |
| INTEG-001 | Open Integrations | Enter integrations | Provider list | `/api/integrations/product/home` |
| AUDIT-001 | Open Audit | Enter audit | Audit status | `/api/audit/status` |
| ACT-001 | Open Actions | Enter actions | Action history | `/api/actions` |
| HOME-001 | Open Home/Dashboard | Enter home | Greeting + cards | `/api/dashboard/home` |
| SETTINGS-001 | Open Settings | Enter settings | Pref categories | prefs + settings UI |
| SETTINGS-002 | Change + persist | Toggle theme/density/etc | Immediate + after leave/return | `AriaUiPrefs` |
| MODELS-001 | Open Models | Enter providers | Roles/catalog/providers | `/api/models*` |
| MODELS-002 | Switch model | Assign role / chat model | Backend matches UI | models switch |
| BROWSER-001 | Open Browser agent | Enter browser | Idle status / navigate | `/api/browser/status` |

### ACTIVITY CENTER / GLOBAL

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| ACTC-001 | Open notifications | Open inbox | Readable events with titles/bodies | `/api/activity/inbox` |
| ACTC-002 | Mark read/dismiss | M / Delete | State updates | activity APIs |
| ACTC-003 | Failure surfacing | Trigger room load error | Actionable, not spam flood | toast→inbox bridge |

---

## Cross-room journeys (mandatory)

| Journey ID | Path | Expected |
| --- | --- | --- |
| XJ-001 | Chat remember → Memory room → recall in Chat | Same fact |
| XJ-002 | Research in Chat → Documents/Search find related | Consistent corpus |
| XJ-003 | Fly add material → Fly search inventory → Chat ask about material | Inventory agrees |
| XJ-004 | Planner task → Calendar/Journal promotion paths | No double/missing |
| XJ-005 | Coding propose → Projects context → Actions history | Honest apply record |
| XJ-006 | Front Door Audio → Voice → Journal | Nav clean; no stuck Stopping |
| XJ-007 | Mission degraded → Repair/Integrity | Consistent health story |

---

## Evidence locations

- `/tmp/aria-app-accept/room_sweep.json` — enter-all-rooms sweep  
- `/tmp/aria-app-accept/accept_log.json` — paced room + function probes  
- `/tmp/aria-app-accept/api/` — API probe dumps, activity inbox, journeys  
- `/tmp/aria-app-accept/screenshots/` — UI captures  

---

## Supplemental inventory (discovered during function-complete phase)

| Test ID | Function | User action | Expected | Dependencies |
| --- | --- | --- | --- | --- |
| ONBOARD-001 | What's New | Open What's New | Dialog opens/closes | shell modal |
| ONBOARD-002 | Help ARIA learn about you | Open learn/onboarding help | Dialog reachable | onboarding modal |
| CMD-001 | Command palette | Ctrl+K / open palette | Palette opens | command_palette.js |
| JOBS-001 | Job center | Open Job center | Job center opens | jobs modal |
| LOCK-001 | Lock screen | Open lock affordance | Lock UI present (no PIN change) | lock_screen.js |
| LEGACY-001 | Legacy shell tabs | Open bare `/` | Legacy tabs; living off | workspace.js |

---

## Inventory counts (discovered)

| Category | Count |
| --- | ---: |
| Living Workspace rooms | 34 |
| Front Door destinations (sampled) | 43–82 UI entries (rooms + controls + tools) |
| Legacy view-tabs (approx) | 32 |
| Activities (registry) | 20+ |
| Tools (registry) | 18 |
| Assigned test IDs (base inventory) | 104 unique |
| Supplemental test IDs | 6 |
| **Total test IDs** | **110** |
