# Aria Product Certification — Progress Report

**Date:** 2026-07-24  
**Stance:** Zero-trust product UX / capability / architecture audit  
**Browser policy:** Single persistent session; no reload loops (reload only for startup/restart recovery)  
**Status:** **INCOMPLETE for full charter stop-condition** — additional defects found and fixed; exhaustive every-control modernization not finished

## Executive Summary

Phase 1 inventory is complete (21 primary tabs, ~499 live `/api` routes, 11 extensions, Mission Control 17 UI tabs, Cap Bus 16 verbs). Zero-trust exercise continues against a live workstation (`8765`) with AI-Platform Mission Control (`8780`).

This wave proved and repaired:

1. Disconnected UI APIs (audio stop/sink, Playwright install, journal projects) — prior wave  
2. Phantom PIN exemption for missing `/api/homeassistant/daylight`  
3. Mission Control async tab race (Connection overwrite of Knowledge)  
4. Missing AI-Platform `databases` tab loader + Aria `connection` tab proxy  
5. Browser status line falsely reported “Playwright not installed” when stack was ready  
6. MongoDB “up” + “container stopped” contradictory detail copy  

Primary tabs, MC tabs, planner task add, journal gratitude/writes, memory list, calendar, settings modal, documents/gallery/video/meme/audio/flytying/maker/security/presence/voice/actions/dashboard all **smoke-rendered** in one persistent browser session.

**Full charter stop-condition is not met.** God-`app.js`, a11y, visual coherence, command palette, deep Comfy/HA/coding/voice-live workflows, multi-monitor soak, and long-session leak profiling remain open.

## Complete product inventory (Phase 1)

### Primary view tabs (21)

| View | Panel id | Init hook |
|------|----------|-----------|
| Chat | `chatView` | default |
| Dashboard | `dashboardView` | `initDashboard` |
| Mission Control | `workstationView` | `initWorkstation` |
| Planner | `plannerView` | `initPlanner` |
| Calendar | `calendarView` | `initCalendar` |
| Fly tying | `flytyingView` | `initFlytying` |
| Projects | `projectsView` | `initProjects` |
| Maker | `makerView` | `initMakerLab` |
| Browser | `browserView` | `initBrowserPanel` |
| Security | `securityView` | `initSecurity` |
| Presence | `presenceView` | `initPresence` |
| System (audit) | `auditView` | `initAudit` |
| Voice | `voiceView` | `initVoiceTab` |
| Audio | `audioView` | `initAudio` |
| Bullet Journal | `journalView` | `initJournal` |
| Memory | `memoryView` | `loadMemoryBrowser` |
| Gallery | `galleryView` | `loadGallery` |
| Video | `videoView` | `loadVideoGallery` |
| Meme | `memeView` | `loadMemeGallery` |
| Documents | `documentsView` | `loadDocumentsTab` |
| Actions | `actionsView` | `loadActions` |

### Sidebar / chrome

Mode · Capabilities · Services · Mission Control shortcuts · Integrations · Agent tools · Video · Smart home · Chat & data · Coding · Model settings · Tips · Job Center · floating docks (HA/Maker/Browser/Printer when flagged)

### Extensions (11)

`browser`, `engineering`, `flytying`, `git`, `journal`, `memory`, `planner`, `projects`, `security`, `smarthome`, `voice`

### HTTP API surface

~499 registered `/api` routes + WS; auth: NetworkGuard → RateLimit → APIKey → PinLock.  
Inventory detail: [Inventory Aria GUI](76561828-7f8b-48b7-ab17-b47732f0567a).

### Execution map

```
UI control → fetch(/api/…) / Cap Bus / chat action
  → jarvis.gui.server / extension routes
    → aria_core / ACM / jarvis organs / aiplatform
      → JSON / FileResponse → DOM / toast / panel refresh
```

## Features / capabilities exercised (this certification)

| Surface | Result |
|---------|--------|
| All 21 view tabs switch + render | PASS (persistent browser) |
| All 17 MC tabs (incl. connection/databases) | PASS after race + loader fixes |
| MC tab race (connection → knowledge) | Was **FAIL** → **FIXED** |
| Planner add task | PASS (persisted via `/api/planner`) |
| Journal gratitude + daily API | PASS |
| Memory `/api/memory/all` | PASS (entries present; ACM bridge) |
| Calendar month + day click | PASS |
| Settings modal open | PASS |
| Browser status truthfulness | Was **FAIL** → **FIXED** |
| Documents / Gallery / Video / Meme / Audio / Flytying / Maker | PASS smoke render |
| HA entities | Expected fail when HA down (500) |
| UI↔route string scan | ~279/284 matched (template false-positives only) |

## Broken features discovered → fixes

| Bug | Root cause | Fix |
|-----|------------|-----|
| Audio stop / output sink 404 | Missing routes + `stop_playback` | Implemented + tests |
| Browser Install Playwright 404 | Missing route | Route → `ensure_playwright` |
| Journal projects 404 | Missing routes | `extra_routes` → `ProjectJournal` |
| Phantom PIN exempt daylight | Exempt without route | Removed exempt; regression |
| MC tab content race | Async `renderMcTab` no generation guard | `_mcRenderGen` / `stillCurrent()` |
| `/api/mission-control/databases` | Tab in `_TABS` but no loader | AI-Platform `_TAB_LOADERS["databases"]` |
| `/api/mission-control/connection` | Not a platform tab | Aria `get_tab` → `runtime_connection_status` |
| Browser “Playwright not installed” | UI required `agent_ready`; API lacked it | API `agent_ready` + UI fallback |
| Mongo “up” + “container stopped” | Health TCP vs docker detail | Clearer detail string |
| Dashboard Skills & workflows dead | No JS + missing `/api/skills` `/api/workflows` | Routes + `loadSkillsWorkflows` wiring |
| Maker Iterate/Clear/Export dead | Buttons never bound | Bound to edit/clear/STL download |
| Settings Speak replies dead | `settingsSpeakToggle` unwired | Synced with `speakRepliesToggle` |
| Calendar/Planner/Flytying/Security silent fails | Missing ok checks / empty catches | Toasts + empty states |
| Skill defaults / `skill_run` routing | Empty `skill_defaults`; NLU stole “run … skill” | Bundled defaults + router priority |
| Dashboard workflows show `null` | `list_workflows` treated `index.json` as a workflow | Skip index; require slug/name |
| LSP Check stuck on `…` | Deep mypy diagnostics hang UI (~40s+) | Quick `deep=0` default + AbortController timeout |
| MC tab actions dead | `mc$("#id")` with `getElementById` | Strip leading `#` in `mc$` |
| Printer model select ignored | UI never sent `model` | Wire select + API `model=` |
| Inpaint denoise ignored | Hardcoded 0.82 | Read `#inpaintDenoise` |
| Face unlock / router warm / voice smoke | Missing DOM or POST vs GET | Added controls; smoke GET (+ POST alias) |
| Sidebar video status static | Never refreshed | `refreshSidebarVideoStatus` via `/api/resources` |
| Upgrade stuck at `apply_failed` with no Clear | Clear API existed; no UI control | `upgradeClearBtn` → `/api/upgrade/clear` |
| Gallery had settings but no Generate | Discoverability gap | Gallery prompt + Generate → chat `generate image:` |
| MC Repair toast said “started” after sync recover | Misleading feedback | Toast reports repair completion summary |

## Technical debt removed

| Item | Action |
|------|--------|
| `jarvis/gui/static/security.js` | **Deleted** (superseded by `security_settings.js`) |
| Orphan `jarvis/api.py` | Still present (documented; not wired) |

## Audit follow-up

[Audit dead UI / stubs](eb7159fd-6ed7-47ce-9439-cddd86030dc5) P1 findings addressed in this wave.

## Regression tests

`tests/test_product_ui_api_wiring.py` — disconnected routes, PIN exempts, MC databases/connection loaders, browser `agent_ready` + UI wiring.  
AI-Platform: `tests/test_mission_control.py::test_get_tab_databases`.

## Remaining deferred (blocks full YES)

1. Deep workflows: ComfyUI full render soak, video render, Gemini live, coding LSP apply, HA scenes when HA up, Maker STL print path  
2. God `app.js` split / navigation modernization  
3. Accessibility (keyboard, contrast, SR)  
4. Visual consistency / theme coherence  
5. Command palette / global search  
6. Multi-monitor + long-session memory profiling  
7. Alias/duplicate API cleanup; orphan `jarvis/api.py` removal  
8. Every modal/wizard/context-menu full exercise  
9. Gallery Generate still delegates to chat (no dedicated `/api/image/generate`) — acceptable path, but in-tab job progress would be better  

## Latest wave (2026-07-24)

- Live verified: Upgrade Clear clears `apply_failed` → idle; Gallery Generate switches to chat with `generate image: …`; MC Repair toast wording fixed.  
- Assets: `app.js?v=5.16.77`, `mission_control.js?v=1.0.3`  
- Regressions: `tests/test_product_ui_api_wiring.py` extended for Clear/Gallery/Repair wiring (11 tests pass in wiring+upgrade clear suite).

## A11y / UX debt wave (from audit scan)

Addressed P0/P1 from a11y scan:

1. Esc closes product modals (not lock) + Tab focus cycle within top modal  
2. `toolConfirmTitle` id + `aria-labelledby`  
3. Icon-only detach/lightbox/gallery controls: `aria-label`  
4. Merged unreachable `voice_state` handlers (cloud-live path live)  
5. `--muted` alias → `--text-muted`; meme `.error` styled  
6. MC “Models & Services” → `workstationInference` (no duplicate Dashboard target)  
7. Gallery generate CTA (prior wave) + clearer empty-state guidance  

Assets: `style.css` / `app.js` / `voice_bar.js` `?v=5.16.78`, `mission_control.js?v=1.0.4`.

## Verdict question

Would I proudly ship Aria today as a polished, modern, production-quality AI operating environment that I would personally use every day as my primary interface?

**NO**

Evidence: critical wiring and MC correctness improved, and daily tabs smoke-pass, but the charter requires every control/workflow polished and modernized. Significant architecture (god `app.js`), discoverability (no command palette), a11y, visual consistency, and deep generative/HA/coding workflows remain uncertified.
