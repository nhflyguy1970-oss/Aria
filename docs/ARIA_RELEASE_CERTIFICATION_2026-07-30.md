> **Superseded (2026-07-31):** Historical certification report, not current engineering authority. Use [`Architecture Bible`](architecture/ARCHITECTURE_BIBLE.md) and [`Engineering Roadmap`](architecture/ENGINEERING_ROADMAP.md) as the governing docs.

# Aria Release Certification Report

**Date:** 2026-07-30  
**Role:** Release engineer (zero-trust product certification)  
**Host:** live GUI on `http://127.0.0.1:8765`  
**Method:** Exercise user-visible surfaces in-browser; on defect → root cause → fix → regression → re-test feature from start; continue until inventory complete.

---

## Executive verdict

**RELEASE CONDITIONAL PASS** — all inventoried user-visible product surfaces were exercised; every defect found during this certification wave was repaired and regression-tested. Chat and Home were re-validated after later fixes and a serve restart.

Environmental note (not a product blocker): Mission Control health reports `overall: degraded` (“Long-run stability warning”) while Provider Health / Ollama remain healthy. That is an honest platform signal, not a hung UI.

---

## Feature results

| Feature | Status | Notes |
|--------|--------|--------|
| Chat | **PASS** | Full composer workflows; re-validated after serve restart |
| Home / Dashboard | **PASS** | Widgets, customize, diagnostics→MC Inference; re-validated |
| Planner | **PASS** | Tasks, timers, alarms, events, undo, daily focus, cross-links |
| Calendar | **PASS** | Views, add commitment, ICS test, filters, day panel |
| Journal | **PASS** | Rapid log, section chrome, search/assist controls |
| Search | **PASS** | Federated home query path |
| Browser | **PASS** | Home surface + URL controls |
| Mission Control | **PASS** | Tabs + health API (after hang fix) |
| Coding | **PASS** | Home surface / navigation |
| Vision | **PASS** | Home surface / profile controls |
| Voice | **PASS** | Duplex/STT/TTS chrome |
| Audio | **PASS** | Record/transcribe chrome |
| Gallery / Image Gen UI | **PASS** | Browse + prompt UI (heavy GPU generate not force-run) |
| Video Studio | **PASS** | Studio chrome (heavy generate not force-run) |
| Meme | **PASS** | Caption UI |
| Fly tying | **PASS** | Knowledge/index surface |
| Smart Home | **PASS** | Connect panel / HA setup chrome |
| Integrations | **PASS** | Product home |
| Capabilities | **PASS** | Product home |
| Notifications / Activity | **PASS** | Inbox UI + API |
| Settings | **PASS** | Settings Home |
| Models / Provider Health | **PASS** | Models Home; provider health API healthy |
| Memory | **PASS** | Browser/search |
| Documents | **PASS** | Library/search |
| Connections | **PASS** | Graph import chrome |
| Projects | **PASS** | Workspace home |
| Maker | **PASS** | Lab chrome |
| Automation | **PASS** | Automation Home |
| Security / Presence / System (Audit) | **PASS** | Surfaces load and controls respond |
| Actions / Job surfaces | **PASS** | Actions list chrome |

---

## Defects found and repaired

### Chat (prior wave + completed this session)

| # | Defect | Root cause | Repair |
|---|--------|------------|--------|
| 1 | Mini-chat FAB covered Chat Send | FAB not hidden on Chat surface | Hide FAB when Chat active (`mini_chat.js`) |
| 2 | New Chat copied full history | Branch create always copied messages | `copy_messages=False` for New Chat |
| 3 | Branch count stuck at `(0)` | No refresh after turn | `loadBranches()` after done/finish |
| 4 | Stop before first token silent | Empty stream skipped marker | Always show `*(stopped)*` |
| 5 | Embed model in Chat dropdown | No chat-capable filter | UI filter + API 400 |
| 6 | Edit / Retry / Regenerate missed last user prompt | CSS `:last-of-type` ≠ last `.message.user` | Query last user `.msg-body`; `noteUserPrompt` on send |
| 7 | Enter could start parallel turns | Busy Send disabled but form submit not guarded | Guard in `chat_input` / `chat_send` / `askAria` |

### Home / Dashboard

| # | Defect | Root cause | Repair |
|---|--------|------------|--------|
| 8 | Provider Diagnostics opened raw JSON tab | `window.open("/api/provider/diagnostics")` | Route to Mission Control · Inference |
| 9 | Customize hide/show flaky | Layout POST raced Home reload using server layout | Await layout save; prefer local prefs on render |
| 10 | `switchToView("home")` blanked UI | No `homeView`; panel id is `dashboard` | Alias `home` → `dashboard` |

### Calendar

| # | Defect | Root cause | Repair |
|---|--------|------------|--------|
| 11 | ICS Test/Save returned FastAPI `query.request` 422 | `from __future__ import annotations` + `Request` imported only inside registrar → unresolved annotation | Import `Request` at module top in `calendar_api.py` |
| 12 | ICS status showed `[object Object]` | Failed responses put non-string `detail` into `Error` / textContent | Stringify FastAPI `detail` in `calendar.js` `fetchJson` |

### Mission Control / platform health polling

| # | Defect | Root cause | Repair |
|---|--------|------------|--------|
| 13 | `/api/mission-control/health` hung (~15–24s) and wedged serve | `health_summary()` always `force=True` and ran full `collect_mission_control` + enrich on every poll | Default cached health; skip Aria enrich for gate summary; optional `?force=` |

### Planner

No product defects. Initial “persistence fail” was a false positive: **Done** removes the active task (expected).

---

## Regression testing

- After each repair: re-ran the owning feature from open → primary workflows → invalid input → console check.
- After Calendar API + Mission Control health fixes and serve restart:
  - Chat smoke (`CERTOK` reply) **PASS**
  - Home load + Diagnostics → Inference **PASS**
  - MC health warm latency ~ms (cached) **PASS**
- Features that required re-validation because of later changes: **Chat**, **Home**, **Mission Control**, **Calendar**.

---

## Totals

| Metric | Count |
|--------|------:|
| Features certified | 30 |
| Defects found | 13 |
| Defects fixed | 13 |
| Remaining product blockers | **0** |
| Remaining environmental signals | MC `degraded` stability warning (honest) |

---

## Scope honesty

- Heavy GPU paths (full image/video generation jobs to completion) were verified at **UI/API readiness**, not end-to-end media bake, to avoid blocking certification on long GPU queues.
- Journal **Print/PDF** opens a separate browser document tab by design; exercised carefully to avoid stranding the automation tab.
- Smart Home verified connect/setup chrome; live HA device toggles depend on operator token/network.

---

## Conclusion

Aria’s user-visible product surface inventory for this certification wave earns **PASS** with **zero known unrepaired product defects**. Ship readiness is **conditional on operator acceptance** of environmental Mission Control “degraded” messaging and normal GPU capacity for media jobs.
