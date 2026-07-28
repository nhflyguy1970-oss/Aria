# Browser Implementation

**Product:** Aria Browser — web interaction agent (Playwright)  
**Status:** Production-oriented agent runtime (fail-closed)  
**Shortcut:** `Ctrl+Shift+B` → Browser Home

## Philosophy

Browser is the **web interaction product** of the Aria AI Operating System. It owns live page automation under operator control. It is **not** Chrome, Firefox, Edge, a research database, Documents, Memory, Chat, Automation, or Mission Control.

Every implementation decision asks:

1. Does this make Browser genuinely functional?
2. Does this improve operator trust?
3. Does this preserve Browser as a web agent (not a browser fork)?
4. Does this avoid duplicating Documents / Chat / Mission Control?
5. Does this improve safety, transparency, and observability?

**Never fake success.** Never report "Opened", "Task accepted", or "Navigation complete" unless the action occurred.

## Product boundaries

| Browser owns | Does not own |
|--------------|--------------|
| Live page automation | Projects (workspace identity / profile path) |
| Navigation, screenshots, DOM / Vision | Documents (stored knowledge) |
| Safe browsing + download gates | Memory (remembered information) |
| Operator sessions & step logs | Automation (orchestration) |
| Browser Home & task execution | Mission Control (runtime health) |
| Activity events for browser actions | Chat (conversation) / Models (config) |

## Architecture

```
UI: Browser Home + live session
    browser_home.js · browser_panel.js · index.html
        ↓
API: /api/browser/*  (extensions/browser/api.py)
Chat: extensions/browser/handlers.py + routes.py
        ↓
Facade: jarvis/browser_agent.py
        ↓
jarvis/browser_product/
  session.py          Playwright lifecycle + DOM primitives
  screenshots.py      Capture after nav / steps / pause / fail
  agent_loop.py       DOM / VLM loop with pause checks
  downloads.py        Extension allow/deny + confirm
  history.py          Recent URLs + bookmarks
  home.py             Browser Home snapshot
  activity_bridge.py  Durable Activity events
  job_bridge.py       Long tasks → Job Center
  multi_tab.py        Coordinated research (operator-controlled)
  voice_bridge.py     Pause / resume / takeover / stop / summarize
  vision_to_coding.py Screenshot → Coding proposal only
  vision_support.py   browser_vision model role (no fake VRAM)
jarvis/browser_dom_agent.py · browser_vlm.py · browser_playwright.py
```

## Playwright lifecycle

1. `ensure_session` — fail closed if Playwright/Chromium missing  
2. Persistent context under Projects `browser_session` / `pw_profile`  
3. `goto` — real `page.goto` + readiness wait  
4. Screenshot after navigation and major steps  
5. Interact (click / fill / select / scroll / extract / wait)  
6. Pause / Resume / Takeover / Stop  
7. `close_session` — release browser  

Shared page: `session.get_page()`. Step log: `session.steps()`.

## DOM agent

Snapshot → model proposes JSON action → execute on live page → screenshot → repeat.  
Observable via step log; recoverable via Pause / Takeover / Stop.

## Vision agent

Screenshot → Models role `browser_vision` (falls back to `vision`) → coordinate clicks.  
Never autonomous purchases or destructive actions.

## Security

- SSRF / private-network guard (`url_guard`)
- Blocked schemes: `file`, `javascript`, `data`, `vbscript`
- Checkout / payment heuristics → `allow_risky` confirm
- Downloads: risky extensions blocked; unlisted types need confirmation
- `accept_downloads=False` by default on the Playwright context

## Sessions & Projects

Profile directory = Projects `browser_session` (`…/browser/pw_profile`).  
Browser Home shows active profile. Cookies / storage persist per project.

## Integrations

| Product | Integration |
|---------|-------------|
| Chat | `browse_web`, `browser_run_task`, `search_and_browse`, summarize, voice; `open_view` + prefill |
| Job Center | `async` / Queue → `job_bridge.submit_browser_task` |
| Activity | navigate, blocked, task, pause, takeover, stop |
| Documents | Save page extract (Documents owns storage) |
| Coding | Vision→Coding propose → operator apply only |
| Automation | `browser_read` with `approve_experimental` |
| Models | Canonical role `browser_vision` |
| Voice | Safe control verbs only (no buy/pay) |

## Browser Home

Overview · Session · History · Bookmarks · Research · Security  
Plus live session panel: URL, screenshot, controls, step log, queue.

## Accessibility

- Landmark labels on Home tabs / session status (`aria-live`)
- Screenshot `alt` text; controls labeled
- Keyboard: `Ctrl+Shift+B`; focusable tabpanel
- Step log updates announced politely

## Testing

```bash
.venv/bin/python -m pytest tests/test_browser_agent.py \
  tests/test_browser_util.py tests/test_browser_product.py -q
```

Coverage: fail-closed navigate, URL policy, downloads, home snapshot, voice blocks, history/bookmarks, multi-tab plan, DOM without page.

Live e2e requires: `pip install playwright && playwright install chromium`.

## Migration notes

- System-browser open is **opt-in** (`allow_system_fallback=True`) — not default success.
- `browser_vram` is a thin shim to `vision_support` (no placeholder GPU magic).
- Extension `routes()` returns real `browser_routes()`.

## Roadmap

- Richer headed takeover UX
- Resumable multi-tab research merge UI
- Download allowlist UI + destination picker
- Stronger page-metadata / search filters in Home
- Performance budgets for screenshot refresh

## Do not build

Chrome fork · extension marketplace · password manager · silent purchases/downloads · fake screenshots · second automation stack · uncontrolled browser fleets · replacing Search/Documents/Chat/Automation.
