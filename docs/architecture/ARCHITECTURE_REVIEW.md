# Aria Complete Architecture Review

**Role:** Principal Software Architect  
**Date:** 2026-07-31  
**Mode:** Repository understanding only — no implementation  
**Companions:** [ARCHITECTURE_BIBLE.md](./ARCHITECTURE_BIBLE.md) · [ENGINEERING_AUDIT.md](./ENGINEERING_AUDIT.md) · [ENGINEERING_ROADMAP.md](./ENGINEERING_ROADMAP.md)

---

## 1. What Aria is

Aria (also called Jarvis in the package namespace) is a **local AI workstation application**: chat, coding, media generation, life ops (journal/planner/calendar), smart home, voice, vision, browser automation, and federated search — running primarily against local models via Ollama, with optional ComfyUI for image/video and optional AI-Platform for Mission Control.

It is **not** a clean microservice architecture. It is an inherited monolith with product packages layered on top of a god orchestrator, two FastAPI route gods, and a permanent ACM cognitive memory engine.

---

## 2. Scale (measured 2026-07-31)

| Metric | Value |
|--------|------:|
| App Python files (excl. venv) | 1,441 |
| App Python LOC | ~265,700 |
| `jarvis/` | 933 files · ~162k LOC |
| `aria_acm/` (cognition engine) | 128 files · ~31k LOC |
| `aria_core/` (ACM bridge) | 39 files · ~9k LOC |
| Tests | 309 files · ~27k LOC · 1,830 collected cases |
| Frontend JS | 134 files · ~43k LOC |
| HTTP route decorators | ~1,206 |
| Unique (method, path) pairs | ~1,196 |
| Exact duplicate routes | 7 |
| Product packages (`*_product`) | 16 |
| Extensions | 11 |
| SQLite DBs under `data/` | 12+ |
| `data/` total size | ~42 GB (ACM archives ~27 GB, logs ~13 GB) |
| Largest god modules | `gui/server.py` 3953 · `extra_routes.py` 2747 · `router.py` 2267 · `assistant.py` 2041 |

---

## 3. Process topology

```
User
 ├─ python main.py tray     → daemon.py (supervisor)
 │                             ├─ start/monitor serve child
 │                             ├─ ServicesWatchdog / ServerWatchdog
 │                             ├─ proactive_scheduler (briefings, git sync, nightly)
 │                             └─ wake word (opt-in)
 ├─ python main.py serve    → gui/server.py (uvicorn FastAPI)
 │                             └─ JarvisAssistant singleton (set_assistant)
 └─ MCP host                → jarvis_mcp.py → get_assistant()
                                ⚠ may construct a SECOND assistant if serve never registered one
```

**Boot (serve process), measured order:**
1. `load_jarvis_env()` (fail-open on OSError)
2. `apply_cutover_state_on_startup()` (fail-open on corrupt JSON)
3. Nine `attach_platform_*()` (never raise; return values discarded in `main.py`)
4. Import `gui/server.py` → constructs `JarvisAssistant()` at module import (heavy, fail-loud)
5. Extension API registration → middleware → `extra_routes` → `server.py` body routes
6. Lifespan: `recover_stale_jobs()`, activity/notification load, wakeword config

**Critical asymmetry:** `main.py serve` attaches Platform without validating; `daemon.py` attaches *and* validates — but in a different process. Platform attach state is per-process.

---

## 4. How a chat request actually flows

### 4.1 Sync path (MCP, voice, some HTTP)

```
process(message)
  → acquire _request_lock (UNBOUNDED wait)
  → route(message)                    # jarvis/router.py — 17-stage cascade
  → conversation_pipeline.normalize_action_params
  → conversation_pipeline.dispatch_action   # media/bg/coding queues → registry → _chat
  → conversation_pipeline.decorate_result   # log_action, trust, persist
```

### 4.2 Stream path (primary GUI SSE)

```
process_stream(message)
  → acquire _request_lock (3s timeout)
  → route(message)                    # FIRST route
  → ~15 hand-written SSE special cases (coding, media, vision, …)
  → if action != "chat":
        _process_unlocked(...)       # SECOND route of same message
  → else:
        ConversationEngine.execute_stream
          → build_context_prefix
          → resolve_conversation_model
          → llm.ask_stream            # bypasses inference gateway
```

**Verified fact:** stream imports only `normalize_action_params` + `apply_editor_params_if_coding` from `conversation_pipeline`. It does **not** call `dispatch_action` or `decorate_result`. Sync and stream are **not** unified.

### 4.3 Routing cascade (short-circuit first hit)

pending clarification → routing explain → follow-ups → skills → automation → specialists → workflows → reflex → cognitive compose → memory verbs → **NLU pipeline** → `_quick_route` (~950 lines regex) → LLM tool-calling → LLM JSON router → keyword fallback → `chat`.

**Verified fact:** production NLU classifier placement (`data/nlu_placement.json`) selected `qwen3:14b` with **0% measured intent accuracy** across all candidates — chosen on latency alone. Confidence gates still sit at 0.95 / 0.70.

---

## 5. How models and providers are selected

Three overlapping layers claim ownership:

| Layer | Module | Persists |
|-------|--------|----------|
| Role → configured model | `model_store.py` | `data/model_settings.json` |
| Role → selected model | `model_policy.py` | — |
| Workload → benchmark winner | `inference/execution_policy.py` | `data/execution_routing_policy.json` |
| Backend (ollama/litellm) | `inference/policy.py` | env |

**Verified contradictions:**
- Benchmark overlay applied **twice** on sync chat (capability_routing → gateway).
- Streaming chat **bypasses** `gateway.stream_chat` and may silently substitute a different model via personalization / VRAM downshift.
- Five of seven "providers" in `provider_health` are inert stubs.
- Real runtime: Ollama primary; LiteLLM opt-in twice (`JARVIS_INFERENCE_GATEWAY` + `JARVIS_ROUTE_VIA_LITELLM`).

---

## 6. How ACM memory works today

**Decision (fixed):** ACM is the permanent cognitive memory platform. Do not replace it.

```
Write (PRIMARY):
  MemoryStore.add/update/delete_id
    → redirect_legacy_write_to_acm / acm_update / acm_delete_id
    → FAIL-CLOSED RuntimeError if redirect fails

Read (PRIMARY):
  list_entries / get / search / similar_exists
    → acm_store_facade projection
    → FAIL-OPEN: bare except Exception → legacy vault  ⚠ SPLIT-BRAIN

Checkpoint (R1 done 2026-07-31):
  upsert_checkpoint → ACM
  latest_checkpoint → ACM (no legacy fallthrough under PRIMARY)
```

| Store | Role |
|-------|------|
| `data/acm/cognitive.db` (~235 MB) | **Cognitive SoT** |
| `data/memory.db` / `memory.json` | Cold forensic vault |
| `data/memory_vectors.db` | Embedding sidecar (orphaned under PRIMARY) |
| `data/relationship_graph.db` | Connections product (dual-writes with ACM for links) |
| `data/memory_candidates.json` | Staging queue, not SoT |

**Flags (real):** `ARIA_ACM_PRIMARY` default on · `ARIA_ACM_ROLLBACK` · `ARIA_ACM_LEGACY_READ_FALLBACK` · `ARIA_ACM_AUTO_PERSIST` default on · `ARIA_ACM_PERSIST_PATH`.

**Verified cost:** with `auto_persist=True`, every encode flushes a **full-store JSON snapshot** into SQLite (`engine.py:790-791`). Live DB capped at 32 snapshots ≈ 225 MB; archives on disk ≈ 27 GB.

---

## 7. Product map (who owns what)

| Domain | Owner | SoT | Notes |
|--------|-------|-----|-------|
| Chat history | `branches.py` | `data/chat_branches.json` | Authoritative for messages |
| Chat session meta | `chat_sessions.py` | `data/chat_sessions.db` | Naming/pinning sidecar; orphans on delete |
| Cognitive memory | ACM | `data/acm/cognitive.db` | Permanent |
| Search | `search_product` | settings/history JSON | Federates 23 retrievers; default "everything" skips 9 |
| Planner | `planner_store` | `data/planner.db` | Also owns events dual-used by Calendar |
| Calendar | `calendar_schedule` | **read-model over 7 sources** | No single write SoT |
| Journal | `modules/journal.py` | `data/journal/bullet_journal.json` | Full rewrite per save; GET can mutate |
| Coding | `assistant.apply_proposal` + `coding_product` | proposals JSON + RAM undo | Undo not durable |
| Browser | `browser_product` + ext | process globals + JSON | Playwright |
| Voice | `voice_product` + ext | **3 settings files** | Overlapping |
| Vision | `vision_product` | history.jsonl | Most honest failure reporting |
| Image gen | `image_generation` + ComfyUI | `data/generated/` | Queue verifies on-disk output |
| Video gen | `video_generation` + ComfyUI | `data/generated_videos/` | Ken Burns / AnimateDiff |
| Gallery | `gallery_product` | filesystem + metadata.json | Soft-delete + chat scrub (strong) |
| Projects | `active_project` + registry | `data/active_project.json` + `data/projects/` | Ambient global; 18 importers |
| Activity | `activity_inbox` | `data/activity/inbox.jsonl` | Claimed server-authoritative; bulk mutations still local |
| Notifications | `notifications_product` | history.jsonl | Parallel store; desktop notify bypasses DND |
| Dashboard | `dashboard_product` | almost nothing | Aggregator (honest widgets) |
| Mission Control | `mission_control.py` → aiplatform | observes only | Hard import of Platform |
| Settings | `settings_product` | appearance + catalog | Index, not owner of most prefs |
| Layouts / Shell | `layouts_product` / `shell` | JSON + `style.css` | Client mutates chrome |
| Automation | `intelligence/automation_engine` + `automation/` | dual-write rules JSON | Engine in wrong package |
| Certification | `certification_product` | `data/certification/` | Evidence-based; skip_image → SMOKE_PASS |

---

## 8. Frontend architecture

- **129 classic `<script>` IIFEs** + 3 ES modules + 1 server-concatenated shell bundle.
- **100% of JS files** touch `window.*`. No bundler. Load order in `index.html` is the dependency graph.
- Auth: monkey-patched `window.fetch` injects `X-API-Key`; media URLs put the key in the **query string**.
- `aria_mutate.js` exists to forbid toast-on-HTTP-200 — **called only from its own definition**. ~476 mutating fetches bypass it.
- Client-authoritative state: activity pin/snooze/mute, workspace layouts, recorded workflows, command usage — all `localStorage`.

---

## 9. Persistence reality

**Healthy:** most stores have a single owner. Activity inbox uses atomic tmp+replace. Media queue refuses Complete without on-disk artifact. Gallery soft-delete scrubs chat embeds.

**Unhealthy:**
- ACM full-store snapshot on every encode
- `chat_branches.json` full rewrite (often twice) per chat turn
- Journal full rewrite + GET-side mutation
- `code_index.json` ~88–92 MB loaded into RAM; linear cosine scan on chat path
- `data/logs/` ~13 GB, no rotation
- Multi-writer: gestures, settings↔notifications mirror, automation dual-write, activity three-store split
- Shutdown (`server.py` lifespan): `branches.persist` + `auto_checkpoint` share one `except: pass`; ACM flush in another — last turn can vanish silently

---

## 10. Testing & certification reality

| Fact | Evidence |
|------|----------|
| CI command | `python scripts/ci_check.py all` → ruff → format → supremacy → pytest |
| CI subset | **84 of 309** test files |
| Current CI gate (this host) | ruff fail (15) · format fail (21) · pytest 9 fail / 695 pass when forced |
| Source-text asserts | ~15% of suite; `test_product_ui_api_wiring.py` alone ~493 |
| Browser e2e | One file, module-skipped without Playwright |
| Server start in tests | Never |
| Auth middleware tests | Essentially one function, not in CI |
| Stream path tests | Near zero |
| Certification | Can block READY_TO_SHIP on `skip_image` (**verified**); stale READY_TO_SHIP artifact still on disk; screenshots can be fabricated canvas text |

**Prior claim verification (independent):**

| Claim | Verdict |
|-------|---------|
| Registration fail-loud, 21 OK / 0 failed | **PARTIAL** — count real; only 5/23 `required=True` |
| Cert cannot READY_TO_SHIP with skip_image | **VERIFIED** (code); stale artifact remains |
| Clear/verify fail-closed | **PARTIAL** — chat clear yes; coding_verify / health probes no |
| Activity server-authoritative | **PARTIAL/FALSE** for bulk mutations |
| Conversation pipeline unified | **FALSE** |
| Auth exemption loopback-only | **VERIFIED** |

---

## 11. Architectural strengths (preserve)

1. ACM as sole cognitive SoT with fail-closed writes and rollback drill.
2. Media queue: serial GPU worker, on-disk output verification, gallery↔job reconciliation.
3. Gallery soft-delete + chat embed scrub/restore.
4. Automation `normalize_result`: skipped ≠ success.
5. Dashboard honest unavailable widgets with coach/reason.
6. LAN bind refuses to start without API key (`SystemExit`).
7. Path confinement + URL SSRF guard (DNS re-resolve).
8. Product registration ledger visible on `/api/health`.
9. Checkpoint SoT alignment (Batch D R1, 2026-07-31).
10. Vision honesty reports attached to failures.

---

## 12. Architectural weaknesses (do not soft-pedal)

1. Sync vs stream pipelines still divergent (double route, missing decorate).
2. NLU classifier in production with 0% measured accuracy.
3. Memory reads fail-open to legacy vault on ACM exception.
4. God modules: `assistant.py`, `router._quick_route`, `server.py`, `extra_routes.py`, `modules/audio.py`, `modules/journal.py`.
5. Frontend: 476 unverified mutations; 129 global IIFEs.
6. Activity / notifications / localStorage three-store split.
7. ACM encode → full-store snapshot write amplification.
8. Daemon `get_assistant()` constructs a second assistant.
9. Shutdown silent data loss.
10. Certification/docs pile mutually contradictory; CI does not run most new tests.
11. Calendar dual event ownership (planner.db vs journal).
12. Coding undo is RAM-only; apply reports ok when verify failed.

---

## 13. Ownership principles (for all future work)

1. **One SoT per concern.** If two stores hold the same fact, name the loser and retire it.
2. **ACM is permanent for cognition.** Strengthen ACM; remove legacy ownership around it. Never add a second cognitive platform.
3. **HTTP 200 / toast is not success.** Verify before declaring outcome.
4. **Sync and stream must share one dispatch + decorate path.**
5. **Products own data; Dashboard / Mission Control / Certification observe or aggregate.**
6. **Fail closed for security, media output, and cognitive writes. Fail loud for product registration of required surfaces.**
7. **No new façades when an existing one already does the job.**

---

## 14. Stop condition for this research

Research complete. Deliverables written. **No code was modified** as part of this research pass (architecture docs only).

**Do not implement recommendations until explicitly approved.**
