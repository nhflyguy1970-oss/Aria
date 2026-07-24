# Aria Product Certification — Progress Report

**Date:** 2026-07-24  
**Stance:** Zero-trust product UX / capability audit  
**Status:** **INCOMPLETE for full charter stop-condition** — critical disconnected UI wiring fixed; exhaustive every-control modernization not finished

## Executive Summary

Phase 1 inventory and live smoke of all primary view tabs completed. Zero-trust API/UI wiring audit discovered **four user-visible controls that called missing backends (HTTP 404)**. Those are fixed with permanent regression coverage. All **21** primary view tabs switch and render without JS exceptions in a live browser session.

This report does **not** claim every button, dialog, and long-running workflow across Gallery/Video/Fly-tying/HA/Coding has been deep-certified. Remaining work is deferred as an ongoing product-quality backlog.

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

### Sidebar sections

Mode · Capabilities · Services · Mission Control shortcuts · Integrations · Agent tools · Video · Smart home · Chat & data · Coding · Model settings · Tips

### Extensions (11)

`browser`, `engineering`, `flytying`, `git`, `journal`, `memory`, `planner`, `projects`, `security`, `smarthome`, `voice`

### HTTP API surface

**494** OpenAPI paths under `/api/*` (groups include audio 59, journal 61, flytying 39, mission-control 20, security 16, voice 9, memory 18, …).

### Static UI modules

`app.js` (~5.8k LOC) plus specialized panels: `mission_control.js`, `journal.js`, `flytying.js`, `audio*.js`, `calendar.js`, `planner.js`, `browser_panel.js`, `security*.js`, `voice_*.js`, `projects.js`, `maker.js`, `video_studio.js`, `meme_studio.js`, `lock_screen.js`, …

### Execution map (canonical)

```
UI control (view-tab / button / form)
  → fetch(/api/…) or Cap Bus / chat action
    → jarvis.gui.server / extension register_routes
      → aria_core (memory/learning/cognition) when cognitive
        → ACM / jarvis organs / aiplatform (optional)
          → JSON / FileResponse
            → DOM update / toast / panel refresh
```

## Capabilities exercised (this pass)

| Surface | Result |
|---------|--------|
| All 21 view tabs switch | PASS (browser Runtime.evaluate) |
| `/api/live`, health, memory, MC, gallery, journal, … | PASS smoke |
| Audio Stop button path | Was **404** → **FIXED** |
| Audio output sink selector | Was **404** → **FIXED** |
| Browser Install Playwright | Was **404** → **FIXED** |
| Journal → Projects panel | Was **404** → **FIXED** |
| Home Assistant (sidebar) | Unreachable locally (expected if HA down) |

## Broken features discovered → fixes

| Bug | Root cause | Fix |
|-----|------------|-----|
| Stop speaking / audio stop | No `/api/audio/stop`; `stop_playback` missing though TTS imported it | Implemented `stop_playback` + route; interruptible Popen playback |
| Output device dropdown | No `/api/audio/output-sink` | Route + `list_output_sinks` + settings persist |
| Browser Install button | No `/api/browser/install-playwright` | Route → `ensure_playwright(install=True)` |
| Project journals UI | No `/api/journal/projects*` | Routes on `extra_routes` → `ProjectJournal` |

## Regression tests

`tests/test_product_ui_api_wiring.py` (registered in `scripts/ci_check.py`)

## Documentation / commits

See git history for this pass. Inventory and deferred backlog live in this document.

## Remaining deferred (blocks full YES under this charter)

1. Deep workflow certification per subsystem (Fly tying, ComfyUI, Video, Coding LSP, HA scenes, Automation inbound, Maker STL, Gemini live, …)
2. Usability modernization of god `app.js` / navigation density
3. Accessibility audit (keyboard, contrast, screen readers)
4. Multi-monitor / window lifecycle soak
5. Long-duration UI memory leak profiling
6. Visual consistency / theme pass
7. Command palette completeness
8. Every modal/wizard/context-menu exercise

## Verdict question

Under the **full** stop-condition of this charter (every control, every workflow, polished modernization), Aria is **not yet fully certified**.

Under the **operational daily-use** charter (Core/ACM certified; primary tabs load; critical wiring repaired), Aria remains usable as the workstation AI environment — with the deferred backlog above.
