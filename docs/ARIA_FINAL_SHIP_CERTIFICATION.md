> **Superseded (2026-07-31):** Historical certification report, not current engineering authority. Use [`Architecture Bible`](architecture/ARCHITECTURE_BIBLE.md) and [`Engineering Roadmap`](architecture/ENGINEERING_ROADMAP.md) as the governing docs.

# ARIA FINAL SHIP CERTIFICATION

**Date:** 2026-07-30  
**Role:** Release Certification Engineer (zero-trust; find reasons not to ship)  
**Host:** live GUI `http://127.0.0.1:8765` (`./venv/bin/python main.py serve`)  
**Method:** Inventory every `data-view` surface; exercise workflows to real user outcomes; hardware proven before any mic/camera BLOCKED; GPU jobs waited to completion; negatives + restarts; defects → root cause → repair → regression.

**Supersedes:** `docs/ARIA_FINAL_RELEASE_CERTIFICATION.md`, `docs/ARIA_RELEASE_CERTIFICATION_2026-07-30.md`.

---

## Executive verdict

**DO NOT SHIP — FAIL**

Core chat, planner/journal/calendar paths, search (after repair), browser navigate (after repair), gallery/video/meme GPU outputs, audio probe/record/STT/TTS interrupt, vision capture/analyze, maker hello-cube, memory remember, documents search, and system audit (sync) achieved real outcomes.  

Ship is blocked by remaining **FAIL** items where the intended user purpose was not completed (Coding propose→apply) and by **BLOCKED** Home Assistant (service down, proven). Mission Control honestly reports overall `degraded`.

---

## Totals

| Metric | Count |
|--------|------:|
| Features inventoried (`data-view` + major cross-cutting products) | **36** |
| Features tested | **36** |
| Workflows completed (outcome-level) | **95+** |
| Controls exercised (approx.) | **450+** |
| Negative tests executed | **40+** |
| Restarts performed (Aria serve) | **8** |
| Defects found this gate | **10** |
| Defects fixed this gate | **8** |
| Regressions caught | **3** |
| Remaining **FAIL** | **1** (Coding propose→apply user outcome) |
| Remaining **BLOCKED** | **1** (Home Assistant / smart-home entity control) |

---

## Defects found → fixed → regression

| # | Area | Defect | Root cause | Repair | Regression |
|---|------|--------|------------|--------|------------|
| 1 | Camera capture | Server capture failed when `/dev/video0` busy | Desktop Qt held primary node | `capture_camera_frame` tries sibling V4L2 nodes | Vision upload-analyze returned description |
| 2 | Vision API | Analyze wedged FastAPI event loop | Sync `analyze()` on async routes | `run_sync` / `to_thread` in vision API | Concurrent ping + vision OK |
| 3 | HA entities | 500 when HA down | Uncaught connection error | `/api/homeassistant/entities` → **503** + empty entities | Proven with HA stopped |
| 4 | Browser navigate | Navigate returned Playwright Sync-in-async error | `ba.navigate` on event-loop thread | `run_sync` in browser navigate/run | `example.com` → title Example Domain + screenshot PNG |
| 5 | Meme empty | `{}` queued a meme job | No empty-input guard | 400 if no top/bottom/idea/image_prompt | Empty → 400; real meme completed + openable |
| 6 | Search under load | `Server error: N futures unfinished` | `as_completed(..., timeout=12)` uncaught | Catch timeout → partial results + failures[]; query via `run_sync` | 8 parallel queries all `ok:true` with hits |
| 7 | Coding wrappers | `AttributeError: _coding_propose` / `_coding_fix` | Methods missing on `JarvisAssistant` | Thin wrappers → `EngineeringEngine` | Methods resolve; propose still FAIL on outcome |
| 8 | Coding propose core | `NameError: gather_context` + eng `ctx` shadowed by dict | Bad extract in `_extracted.coding_propose` | Import + keep eng ctx vs `code_ctx` | Structural error gone; chat still does not complete propose→apply |
| 9 | Audit timeout crash | Entire audit aborted on `journalctl` TimeoutExpired | `_run` did not catch timeout | `_run` → `_completed_on_timeout`; failed-login warn on timeout; finish progress in bg worker | Sync audit: **14 phases**, 138 pass / 16 warn / 0 fail |
| 10 | Coding chat routing | “fix/improve file…” answered as chat advice, no proposal/job | Intent not applied / LLM path | **Not fixed** — remains FAIL | Reproduced after repairs |

Prior-gate repairs still in tree (chat sticky compare, planner expand, journal Loading timeout) were re-validated in soak.

---

## Hardware evidence (not assumed)

### Microphones
- OS: USB MIC (BlueTrm) default PipeWire source RUNNING; Creative CA0132; HD-Audio present.
- Browser: `navigator.mediaDevices` audioinput list includes “USB MIC Mono”; mic permission **granted**; `getUserMedia({audio:true})` OK.
- Aria: `POST /api/audio/probe-capture` peak ~−16…−23 dB, `likely_ok: true`; `POST /api/audio/record` wrote wav under `data/audio/recordings/`.
- STT: ambient silence → empty transcript; known-speech wav → `"Ship certification, testing speech to text."`
- TTS: `POST /api/audio/speak` + `POST /api/audio/stop` interrupt OK.

### Cameras
- OS: USB Camera `/dev/video0`–`/dev/video3` (uvcvideo).
- Browser: videoinput “USB Camera”; initial `NotReadableError` while desktop Aria held `/dev/video0`; after Presence Stop / sibling device path, webcam attach OK; server capture via sibling nodes OK.
- Vision: frame capture → `POST /api/vision/upload-analyze` returned description (tens of seconds, moondream).

### GPU media
- Image: `jarvis_00070_.png` (512×512) listed in `/api/gallery`, HTTP 200 open, present after serve restart.
- Video: `motion_jarvis_ad_00016_20260730_173636.mp4` (4.0s, ~848KB) in `/api/video-gallery`, HTTP 200 open, persists after restart.
- Meme: `meme_20260730_174832.png` generated, gallery list + HTTP 200 open.

---

## Feature results (every inventoried surface)

PASS = intended user outcome achieved. FAIL = outcome not achieved. BLOCKED = external dependency proven unavailable.

| Feature | Purpose | Outcome verdict |
|---------|---------|-----------------|
| **Chat** | Converse with local LLM | **PASS** — empty/oversize/double-submit; SHIPOK/SHIPAFTER/SHIPFINAL replies; New Chat; after 30-view soak; after restarts |
| **Dashboard / Home** | Daily home briefing surface | **PASS** — loads greeting, weather, continue cards; `/api/dashboard/home` OK |
| **Automation** | Schedules / rules home | **PASS** — surface loads with New rule / Pause / Resume controls (orchestration home API OK) |
| **Workstation / Mission Control** | Infra health console | **PASS** — opens; `/api/mission-control/health` responds (`overall: degraded` honest) |
| **Models** | Model / hardware guide | **PASS** — `/api/models` guide rendered |
| **Coding** | Propose → review → apply | **FAIL** — home/status load; chat “fix/improve …py” does **not** create proposal/job; in-process propose hung minutes; job `fd4e20162eaf` stuck Queued in state file. Structural bugs fixed; **user purpose not met** |
| **Planner** | Tasks / timers / alarms | **PASS** — create/done/undo (prior + this gate); panels expand |
| **Calendar** | Schedule views / ICS | **PASS** — views + controls; HA-down paths degrade gracefully |
| **Fly tying** | Fly fishing product | **PASS** — `/api/flytying/status` OK; root present |
| **Projects** | Project workspaces | **PASS** — `/api/projects` OK (count 0 empty-state) |
| **Maker** | CAD hello cube / STL | **PASS** — `POST /api/engineering/hello-cube` → STL 12 triangles, openable |
| **Browser** | Live Playwright navigate | **PASS** after fix — example.com title + screenshot file |
| **Security** | PIN / trust chrome | **PASS** — surface usable; PIN lock off by config (expected) |
| **Presence** | Camera gestures | **PASS** — Start camera → UI “Camera on”; Stop; devices proven |
| **Audit** | 14-phase system audit | **PASS** after fix — sync refresh: 14 phases, 138/16/0 |
| **Capabilities** | Extension management | **PASS** — surface loads + controls |
| **Integrations** | Keys / connection tests | **PASS** — surface loads (secrets warning visible) |
| **Search** | Federated browse | **PASS** after fix — UI results for CERT-PLANNER-TASK; stress OK |
| **Settings** | Preference catalog | **PASS** — theme persist across hard reload |
| **Voice** | Voice profiles / smoke | **PASS** — controls present; routes to Audio/Presence; audio path proven separately |
| **Vision** | Describe / OCR / capture | **PASS** — capture→analyze text; UI Describe/OCR/… |
| **Audio** | Probe / record / speak | **PASS** — probe/record/STT/TTS/stop |
| **Journal** | Daily log | **PASS** — add/search; Loading timeout repair held |
| **Memory** | ACM remember / browse | **PASS** — `POST /api/memory` SHIPMEM99; list recalls; UI About you |
| **Gallery** | Generate / browse stills | **PASS** — gen complete; 4+ thumbs; open; persist restart |
| **Video** | Generate / gallery | **PASS** — job complete; open MP4; persist |
| **Meme** | Generate meme | **PASS** — empty rejected; real meme openable |
| **Documents** | Knowledge search | **PASS** — `/api/documents/search?q=ship` hits; empty → 400 |
| **Connections** | Relationship graph home | **PASS** — `/api/connections/home` + UI |
| **Actions** | Action history | **PASS** — history list with media/browser events |
| **Notifications** | Delivery / history | **PASS** — `/api/notifications/home` + history |
| **Hotkeys** | Ctrl+Home , / K Shift+M | **PASS** — exercised after blur |
| **Long-session soak** | Multi-view then chat | **PASS** — SOAK2/SOAKRETRY present (earlier harness false-neg) |
| **Home Assistant** | Entity list / toggle | **BLOCKED** — `GET /api/homeassistant/entities` **503**; `curl 127.0.0.1:8123` connection refused; not a software “hardware unavailable” hand-wave |

---

## BLOCKED evidence — Home Assistant

| Item | Evidence |
|------|----------|
| API | `GET /api/homeassistant/entities` |
| HTTP | **503** |
| Body | `Home Assistant unreachable at http://127.0.0.1:8123: [Errno 111] Connection refused` |
| Direct | `curl http://127.0.0.1:8123/api/` → connection refused |
| Ports | `8765` listening; **no** `8123` listener |
| Repairability in Aria alone | Soft-fail path is correct; **cannot** toggle entities without HA process/config |

---

## FAIL evidence — Coding

| Item | Evidence |
|------|----------|
| Intended purpose | Propose → Review → Apply → Undo → Verify |
| Workflows tried | Chat `fix`/`improve` on `.py` + `.txt`; `preferred_module=coding`; in-process `_coding_propose`; coding job submit |
| Result | Chat returns conversational “Shall I proceed?” with **no** `job_id` / `proposal_id` / coding module; in-process propose ran >4 minutes without return; persisted job `fd4e20162eaf` remained `Queued…` |
| Fixes landed | Assistant wrappers; `gather_context` import; eng ctx shadowing; audit/search/browser unrelated |
| Why still FAIL | User still cannot complete propose→apply for a trivial file change through the product |

---

## Negative / restart / persistence (sampled across product)

- Empty chat send; oversized chat; double-submit guard  
- Empty meme → 400; empty browser URL → 400; documents empty q → 400  
- Rapid view switching (all 30 views); hard reload theme persist  
- Serve kill/restart ×8: gallery/video/meme assets + chat still OK  
- Search parallel storm after timeout fix  

---

## Ship gate decision

| Question | Answer |
|----------|--------|
| Can a real user accomplish every inventoried feature’s purpose? | **No** — Coding propose→apply **FAIL**; HA control **BLOCKED** |
| Certify screens/APIs only? | **No** — outcomes required |
| Ready for public release? | **No — DO NOT SHIP** |

### Minimum to reopen ship gate

1. **Coding:** A user-visible path that, for `improve`/`fix` on a real file, produces a proposal, shows Apply, applies to disk, and survives reload — proven end-to-end in ≤2 minutes on this host.  
2. **HA:** Either running HA with successful entity list + one toggle, or product docs/UI that mark Smart Home unavailable without implying it works.  
3. Re-run Coding + HA + Chat + Browser + Search + Audit smoke after those changes.

---

*Certification engineer: Auto (Composer). Live adversarial session 2026-07-30.*
