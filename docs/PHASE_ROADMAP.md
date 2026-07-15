# ARIA upgrade phases

Structured roadmap after the Phase 1 bulletproofing pass (2026-06).

## Phase 1 — Bulletproof (complete)

| Item | Status |
|------|--------|
| Structured logging (daemon, watchdog) | Done |
| Shared `JarvisAssistant` for MCP / server | Done — `jarvis/assistant_instance.py` |
| Debug bundle API + sidebar button | Done — `GET /api/debug/bundle` |
| Unified job center API + UI panel | Done — `GET /api/jobs` |
| Background queue: document summarize, learn_about | Done — `jarvis/background_jobs.py` |
| Documents RAG hardening (stale index, keyword fallback, corrupt recovery) | Done |
| Daemon / watchdog / RAG / jobs tests | Done |
| UI vs server version hint in environment strip | Done |

---

## Phase 2 — Presence & abilities (complete)

Focus: surface existing backends; expand MCP; daily-use polish.

| # | Item | Status |
|---|------|--------|
| 1 | Voice loop end-to-end | Done |
| 2 | MCP tool expansion | Done |
| 3 | HA entity browser | Done |
| 4 | Document library tab | Done |
| 5 | Memory citations in chat | Done |
| 6 | Storyboard video mode | Done |
| 7 | Proactive scheduler | Done |
| 8 | Auto-strategy from corrections | Done |

---

## Phase 3 — Platform & extensibility (in progress)

Focus: de-monolith; make new features cheap to add.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | **Handler registry** | Done | `@register_action`, `jarvis/handlers/registry.py`, meta/git/journal modules |
| 2 | **Declarative router** | Partial | `router_table.py` — meta, journal, git, weather; legacy `_quick_route` remains |
| 3 | **Unified job framework** | Done | `jarvis/job_framework.py` over media/coding/audio |
| 4 | **Frontend ES modules** | Partial | `modules/jobs.mjs`, `modules/health.mjs`, `modules/util.mjs`; chat split pending |
| 5 | **Event bus** | Done | `jarvis/events.py`; hooks on job done + strategy memory |
| 6 | **OpenAPI / typed client** | Partial | `GET /api/registry/actions`, `GET /api/registry/router/rules` |
| 7 | **Contributor doc** | Done | `docs/ADDING_AN_ACTION.md` |
| 8 | **Split `assistant.py`** | Partial | Registry dispatch wired; ~10 actions extracted; streaming/coding remain |

**Next increments:** migrate coding/vision handlers, expand router table, extract `chat.js` job pollers.

Target: new ability = registry entry + handler + test (see `docs/ADDING_AN_ACTION.md`).

---

## Phase 4 — Cognitive memory replacement (ACM)

Focus: replace Aria cognitive memory with an **independent vendored ACM copy**.  
**Blueprint:** Approved / locked. **M0–M4:** Complete. ACM = sole cognitive SoT.

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Integration blueprint (Parts 1–10) | Done | `docs/acm_integration/` · A001 |
| 2 | M0 Vendor `aria_acm/` | **Done** | Pin ACM `v0.16.0` · `aria-acm-v0.16.0-1` (M0B) |
| 3 | M1 Shadow measure | **Done** | Measure phase complete |
| 4 | M2 Harvest INTO ACM | **Done** | `acm_harvest` · operator CLI |
| 5 | M3 ACM primary | **Done** | Flag-gated cutover · A005 |
| 6 | M4 Retire legacy SoT | **Done** | DualWrite off · ACM sole · A006 |

Canonical roadmap: root [`ROADMAP.md`](../ROADMAP.md).

---

## Deferred (unchanged)

- Portable SSD deployment (`UPGRADES.md`)
- Multi-agent swarms (not planned — 8GB VRAM)
- Cloud burst video/3D (optional, privacy tradeoff)
- Full frontend framework rewrite (only if ES modules insufficient)
