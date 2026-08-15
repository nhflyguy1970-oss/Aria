# Aria Architecture Bible

**Version:** 2.0 · **Date:** 2026-07-31 · **Authority:** Principal Software Architect  
**Stance:** Inherited codebase. Prior certifications and product claims are evidence, not truth.  
**Companion:** [ARCHITECTURE_REVIEW.md](./ARCHITECTURE_REVIEW.md) · [ENGINEERING_AUDIT.md](./ENGINEERING_AUDIT.md) · [ENGINEERING_ROADMAP.md](./ENGINEERING_ROADMAP.md)

This document is the **authoritative engineering reference**. Where product `terminology.py` BOUNDARIES conflict with this Bible, **update both**.

---

## 0. System identity

| Question | Answer |
|----------|--------|
| What is Aria? | Local AI workstation (chat, media, life ops, coding, smart home, voice, vision) |
| Package name | `jarvis` (Python) · UI brand "Aria" |
| What is AI-Platform? | Optional sibling repo (`/media/jeff/AI/AI-Platform`) for Mission Control aggregation |
| Default mode | Aria **standalone** must work without Platform |
| Process topology | Tray (`daemon.py`) → child `main.py serve` → Uvicorn → one `JarvisAssistant` |
| UI | Single SPA megapage (`gui/static/index.html` + ~130 JS IIFEs) · ~31 views |
| Cognitive memory | **ACM permanent** (`aria_acm` + `aria_core/acm_bridge` → `data/acm/cognitive.db`) |
| Scale | ~1,441 app py files · ~266k LOC · ~1,200 routes · 16 products · 11 extensions |

### Layer cake

```
┌─ SPA (index.html + static/*.js IIFEs) ───────────────────────────┐
├─ FastAPI app ────────────────────────────────────────────────────┤
│  L1 Monolith routes: gui/server.py + gui/extra_routes.py         │
│  L2 Extensions: jarvis/extensions/* (register_api)               │
│  L3 Products: jarvis/*_product/ (register_product_routes)        │
│  L4 External: aria_acm, aria_core, optional aiplatform           │
├─ JarvisAssistant + BranchManager + engines                       │
├─ handlers/registry + behaviors/* + router/nlu/inference          │
└─ data/ persistence (SQLite ×12+ + JSON ×40+ + media trees)       │
```

**Boot order is load-bearing** (FastAPI first-match-wins). Gallery product must register before `/api/gallery/{name}`. Extensions register before `extra_routes` before `server.py` body.

---

## 1. Global principles (enforced)

### Required per subsystem

| Field | Rule |
|-------|------|
| Owner | One package/module owns behavior |
| Source of Truth | One place answers “what is true?” |
| Persistence owner | One writer for durable state |
| Public API | One stable surface (HTTP and/or Python) |
| Lifecycle | One documented create→use→destroy path |
| Responsibility | Single job |

### Forbidden patterns

| Pattern | Why |
|---------|-----|
| `try: register_product… except: pass` without ledger | Broken products vanish |
| Dual-write as steady state | Guarantees drift |
| Toast / HTTP 200 as success | False PASS |
| Second store “for convenience” | Multi-truth |
| Re-implementing sync and stream pipelines separately | Permanent divergence |
| God modules absorbing new domains | Unmaintainable |
| New memory platform / second cognitive SoT | ACM is permanent |
| READY_TO_SHIP without full required evidence | Certification lie |

### Real ACM flags (do not invent others)

| Flag | Default | Role |
|------|---------|------|
| `ARIA_ACM_PRIMARY` | on (`1`) | ACM authoritative |
| `ARIA_ACM_ROLLBACK` | off | Force legacy façades |
| `ARIA_ACM_LEGACY_READ_FALLBACK` | off | Empty-ACM → legacy read (manager path) |
| `ARIA_ACM_AUTO_PERSIST` | on | Flush durable store |
| `ARIA_ACM_PERSIST_PATH` | `data/acm/cognitive.db` | Engine DB |
| `ARIA_ACM_SHADOW` | off | Parallel measurement |

Precedence: `ROLLBACK` > `PRIMARY` > legacy.

---

## 2. Entry points & process model

| Field | Value |
|-------|--------|
| **Purpose** | Start Aria, supervise serve, expose MCP |
| **Owner** | `main.py`, `jarvis/daemon.py`, `jarvis/gui/server.py`, `jarvis/assistant_instance.py`, `jarvis/jarvis_mcp.py` |
| **SoT** | Process topology; assistant singleton via `set_assistant` / `get_assistant` |
| **Public API** | CLI modes `tray` \| `serve` \| `gui`; MCP tool surface |
| **Internal deps** | env_loader, platform_cutover, platform_* attachers, services, watchdog |
| **External deps** | Ollama (expected), ComfyUI (optional), Home Assistant (optional), aiplatform (optional) |
| **Data flow** | tray supervises → serve owns HTTP → MCP attaches to same process or forks |
| **State ownership** | Daemon owns watchdogs/scheduler; serve owns assistant/routes/jobs |
| **Persistence** | `data/jarvis.env`, `data/platform/cutover.json`, logs under `data/logs/` |
| **Failure modes** | Env read fail-open; cutover corrupt → dual_write; MCP standalone assistant fork; serve-only skips scheduler + job resume |
| **Recovery** | ServerWatchdog restart (15s, 3 failures); SIGUSR1 restart; media drain wait up to 600s |
| **Debt** | `get_assistant()` in daemon constructs second assistant; `main.py` discards attach reports; no SIGUSR2 handler despite `server_shutdown.py` |

---

## 3. Conversation engine (`JarvisAssistant`)

| Field | Value |
|-------|--------|
| **Purpose** | Orchestrate message → route → action → response; hold engines & branches |
| **Owner** | `jarvis/assistant.py` (~2041 LOC) — **god module** |
| **SoT** | In-process assistant + `BranchManager` messages |
| **Public API** | `process()`, `process_stream()`, branch CRUD, `apply_proposal`, `auto_checkpoint`, `get_status` |
| **Internal deps** | router, conversation_pipeline, behaviors/*, handlers/registry, llm, memory, branches, coding/media engines |
| **External deps** | Ollama/LiteLLM via llm/gateway |
| **Data flow** | See ARCHITECTURE_REVIEW §4 |
| **State ownership** | Live `session`, `pending_proposals`, `last_apply_backups` (RAM), engines |
| **Persistence** | Via branches persist + proposal_store; undo **not** persisted |
| **Failure modes** | Sync lock unbounded; stream re-routes; `process(voice=)` TypeError at voice callers; double persist |
| **Recovery** | Branch persist on decorate/shutdown (best-effort) |
| **Debt** | Sync≠stream; TD-instant unreachable set; `_stream_lite_ui` dead; god-module sprawl |

### Conversation pipeline (partial)

| Field | Value |
|-------|--------|
| **Purpose** | Shared normalize / dispatch / decorate |
| **Owner** | `jarvis/conversation_pipeline.py` |
| **SoT** | — (stateless helpers) |
| **Public API** | `normalize_action_params`, `apply_editor_params_if_coding`, `dispatch_action`, `decorate_result` |
| **Debt** | Stream path uses only normalize + editor hook — **not unified** |

---

## 4. Routing & NLU

| Field | Value |
|-------|--------|
| **Purpose** | Utterance → action + params |
| **Owner** | `jarvis/router.py` (cascade) · `jarvis/nlu/*` (classifier) · `handlers/registry.py` (action catalog) |
| **SoT** | In-memory `_REGISTRY`; NLU placement `data/nlu_placement.json`; confidence env thresholds |
| **Public API** | `route(message, session, attachment)`; `register_action` / `call_action` |
| **Internal deps** | reflex, cognition, mapping, semantic classifier, capability_routing |
| **External deps** | Placement LLM (`qwen3:14b` today) |
| **Data flow** | 17-stage short-circuit cascade (ARCHITECTURE_REVIEW §4.3) |
| **State** | `session.pending_clarification`; learned intents |
| **Persistence** | `data/nlu_placement.json`, `data/nlu_*` if present |
| **Failure modes** | Classifier 0% accuracy still gates; `_quick_route` 950 LOC regex; three unsynced action catalogs |
| **Recovery** | Fall through to chat |
| **Debt** | `router.ACTIONS` ≠ registry; `plan_request` twice/turn; placement hardware fingerprint ≠ execution fingerprint |

---

## 5. Inference, models, providers

| Field | Value |
|-------|--------|
| **Purpose** | Choose model + backend; execute LLM calls |
| **Owner** | Split: `model_store` (config) · `model_policy` (selection) · `execution_policy` (benchmark) · `inference/gateway` · `llm.py` |
| **SoT** | `data/model_settings.json` · `data/execution_routing_policy.json` · `data/execution_benchmark_latest.json` |
| **Public API** | `select_model_for_role`, `chat_with_usage`, `stream_chat`, `llm.ask*` |
| **Internal deps** | ollama_health, personalization, capability_routing, nlu.placement options |
| **External deps** | Ollama; LiteLLM (opt-in); cloud prefixes via LiteLLM |
| **Data flow** | role → candidates → overlay → route → ollama/litellm |
| **State** | Provider health history JSONL |
| **Persistence** | model settings, routing policy, `data/provider_health/history.jsonl` |
| **Failure modes** | Overlay twice; stream bypasses gateway; uncached litellm health (2s); cloud→ollama when litellm down |
| **Recovery** | litellm→ollama only; `provider_health/recovery.py` reconnects Ollama |
| **Debt** | Five stub providers; hardcoded hardware strings in model_store; gateway↔llm embed cycle |

---

## 6. Context assembly

| Field | Value |
|-------|--------|
| **Purpose** | Build per-turn context prefix for chat |
| **Owner** | `behaviors/conversation.ConversationEngine.build_context_prefix` · `context/policy.py` · `context/builder.py` |
| **SoT** | Ephemeral per turn; system prompt in branch msg[0] |
| **Public API** | `build_context_prefix`, `messages_for_llm`, `context_needs` |
| **Internal deps** | memory prepare_context, knowledge, planning, relationships, flytying |
| **Data flow** | regex needs → timed fetches → join → inject into **last user message** |
| **Debt** | Prefix stored into history; fragile `display_chat_user_content` strip; `needs_memory_lookup` identical branches |

---

## 7. Branches & chat sessions

| Field | Value |
|-------|--------|
| **Purpose** | Multi-branch conversation history + thread naming |
| **Owner** | `jarvis/branches.py` (messages) · `jarvis/chat_sessions.py` (meta) |
| **SoT** | **`data/chat_branches.json` authoritative** · `data/chat_sessions.db` sidecar |
| **Public API** | BranchManager CRUD; chat_sessions create/list/pin/rename |
| **Data flow** | persist full-file JSON; sessions optional gated by feature flag |
| **Failure modes** | Delete branch orphans sessions; create_new_chat not transactional; import-time DB seed |
| **Debt** | Double persist/turn; unbounded growth; flag gates reads not writes |

---

## 8. Memory (ACM — permanent)

| Field | Value |
|-------|--------|
| **Purpose** | Durable cognitive facts, preferences, project checkpoints, recall |
| **Owner** | ACM engine `aria_acm` · bridge `aria_core/acm_bridge` · façades `memory_manager` + `acm_store_facade` · host adapter `modules/memory*.py` |
| **SoT** | `data/acm/cognitive.db` when authoritative |
| **Public API** | Cap Bus remember/recall; MemoryStore methods; `/api/memory/*` (extensions/memory); behaviors memory actions |
| **Internal deps** | behaviors/memory, hierarchy (vestigial under ACM), memory_services, trust_memory, search retrieve_memory |
| **External deps** | None required (engine vendored) |
| **Data flow** | Writes fail-closed to ACM; reads project from ACM; checkpoints R1-aligned |
| **State** | Engine singleton under RLock (not held on all reads) |
| **Persistence** | DurableCognitiveStore snapshots; vaults `memory.db`/`memory.json` forensic |
| **Failure modes** | Read fail-open to legacy; tag-only update no-op; Memory Home `acm_metrics` ImportError; hierarchy consolidate disabled |
| **Recovery** | `ARIA_ACM_ROLLBACK`; harvest script; cognitive reset/archive scripts |
| **Debt** | DualWrite adapter dead but present; semantic adapter ACM-unguarded; relationship dual-write; auto_persist full-store flush; Batch D R2+ open |

**Forbidden:** replacing ACM; adding a second cognitive platform; new memory façade modules.

---

## 9. Search

| Field | Value |
|-------|--------|
| **Purpose** | Federated find across corpora |
| **Owner** | `jarvis/search_product/` |
| **SoT** | Does not own corpora; owns `data/search_product/{settings,history,saved,sessions}.json` |
| **Public API** | `/api/search/product/*` · `run_search()` |
| **Internal deps** | 23 retrievers (memory→ACM, code, journal, …) |
| **Data flow** | intent → corpora → ThreadPool → rank → dedupe |
| **Failure modes** | `_safe` swallows retriever errors; `ok: True` even if all fail; default everything skips 9 corpora |
| **Debt** | Dead bridge shims; latency facet invisible; confidence = restated score |

---

## 10. Planner

| Field | Value |
|-------|--------|
| **Purpose** | Tasks, events, timers, alarms, focus, triage |
| **Owner** | `planner_store.py` + `planner_services.py` + `extensions/planner/api.py` |
| **SoT** | `data/planner.db` |
| **Public API** | `/api/planner/*` (~40) |
| **Failure modes** | No WAL/busy_timeout; HA focus can `ok: True` with `ha_ok: False` |
| **Debt** | Router smuggles system routes; `add_task` can't set due/priority; private `_conn` imports from journal |

---

## 11. Calendar

| Field | Value |
|-------|--------|
| **Purpose** | Read-model schedule over many sources; event mutation router to Planner |
| **Owner** | `calendar_schedule.py` + `calendar_api.py` + satellites |
| **SoT** | User-created events: `planner.db`; read model projects journal notes/legacy events + ICS + work schedule + holidays + timers |
| **Public API** | `/api/calendar/*` (~28) |
| **External deps** | Optional ICS URL; HA prefs |
| **Debt** | ICS URL saved via `movie_tiers`; month view O(days×sources); legacy journal event bullets still project into Calendar |

---

## 12. Journal

| Field | Value |
|-------|--------|
| **Purpose** | Bullet journal (daily/weekly/monthly, habits, wellness) |
| **Owner** | `modules/journal.py` (+ bujo mixin) · routes in `extra_routes` (~86) |
| **SoT** | `data/journal/bullet_journal.json` (+ `.history` sidecar) |
| **Public API** | `/api/journal/*` |
| **External deps** | Open-Meteo; optional IP geo (`ip-api.com`) |
| **Failure modes** | Corrupt JSON → empty store → next save wipes; GET enrich can write |
| **Debt** | Extension API stub; full rewrite/deepcopy per mutation; promote_to_planner private SQL |

---

## 13. Coding

| Field | Value |
|-------|--------|
| **Purpose** | Propose → apply → verify → undo; agent jobs; LSP; code search |
| **Owner** | Split: `assistant.apply_proposal` · `coding_product` · `behaviors/engineering` · `coding_jobs` · routes in server + extra_routes + engineering ext |
| **SoT** | `data/pending_proposals.json` · `data/coding_proposal_history.json` · `data/coding_jobs_state.json` · `data/code_index.json` (~90 MB) |
| **Public API** | `/api/coding/*`, `/api/apply-proposal`, `/api/undo-apply`, `/api/lsp/*` |
| **Failure modes** | Undo RAM-only; multi-file apply non-atomic; job timeout checked after return; apply `ok` with verify failures in text |
| **Debt** | Guardrails advisory; index linear scan; three registration sites |

---

## 14. Browser

| Field | Value |
|-------|--------|
| **Purpose** | Playwright browsing + agent loop |
| **Owner** | `browser_product` + `extensions/browser/api.py` + `browser_agent.py` |
| **SoT** | Process globals for live session; JSON history/bookmarks; `data/browser_screenshots|downloads/` |
| **Public API** | `/api/browser/*` |
| **External deps** | Playwright + Chromium |
| **Debt** | System-browser fallback `ok: True` with no page; downloads disabled but subsystem present; unbounded screenshots |

---

## 15. Voice & audio

| Field | Value |
|-------|--------|
| **Purpose** | STT → intent → assistant → TTS |
| **Owner** | `voice_product` + `extensions/voice` + `modules/audio.py` |
| **SoT** | **Triple settings:** `voice_product/settings.json` ↔ `voice_settings.json` ↔ `audio_settings.json` |
| **Public API** | `/api/voice/*` (product + extension overlap) |
| **External deps** | whisper/RealtimeSTT, piper/espeak/ffmpeg, optional Gemini Live |
| **Debt** | Extension owns chat-session routes; AudioEngine god-object; progress jobs never evicted; `process(voice=True)` TypeError |

---

## 16. Vision

| Field | Value |
|-------|--------|
| **Purpose** | Analyze / OCR / compare / import |
| **Owner** | `vision_product` (+ `modules/vision.py`, behaviors/vision) |
| **SoT** | `data/vision_product/history.jsonl` · uploads under `data/uploads/` |
| **Public API** | `/api/vision/*` |
| **Debt** | Honesty gate inert (`pass`); ERROR: prefix-only failure detection; upload filename unsanitized |

---

## 17. Image generation

| Field | Value |
|-------|--------|
| **Purpose** | Text → PNG via ComfyUI |
| **Owner** | `image_generation` · `handlers/media` · `modules/image` · `comfyui.py` · `comfyui_settings` |
| **SoT** | Files in `data/generated/` · metadata `data/gallery_product/metadata.json` · settings `data/comfyui_settings.json` |
| **Public API** | `/api/image-generation/*` · chat/media queue actions |
| **External deps** | ComfyUI |
| **Failure / recovery** | Offline/GPU fallback; `recover_stale_jobs`; refuse Complete without file |
| **Debt** | `last_seed` on function attribute; experimental endpoints without clients |

---

## 18. Video generation

| Field | Value |
|-------|--------|
| **Purpose** | AnimateDiff or Ken Burns clip |
| **Owner** | `video_generation` · `comfyui_video` · `comfyui_animatediff` · `modules/video` |
| **SoT** | `data/generated_videos/` · `data/video_settings.json` |
| **Public API** | `/api/video-generation/*` (+ legacy gallery/settings routes) |
| **Debt** | Module-level mutable result globals; duplicate visibility vs gallery; dual storyboard enqueue |

---

## 19. Gallery

| Field | Value |
|-------|--------|
| **Purpose** | Browse/organize/trash generated stills |
| **Owner** | `gallery_product` |
| **SoT** | Filesystem `data/generated/` · `metadata.json` · trash `data/gallery_trash/` |
| **Public API** | `/api/gallery/*` (product before path-param) |
| **Strength** | Soft-delete + chat scrub + job missing-asset reconcile |
| **Debt** | Legacy DELETE skips activity event; two visibility implementations |

---

## 20. Projects

| Field | Value |
|-------|--------|
| **Purpose** | Workspace identity — rebinds memory ns, coding root, browser profile, etc. |
| **Owner** | `active_project.py` · `project_registry.py` · `project_services.py` · `extensions/projects` |
| **SoT** | `data/active_project.json` · `data/projects/{slug}/` |
| **Public API** | `/api/projects/*` |
| **Debt** | Ambient `get_active_slug()` in 18 modules; persist-before-apply without rollback; cert fixtures in live data |

---

## 21. Notifications & Activity

| Field | Value |
|-------|--------|
| **Purpose** | Cross-product activity stream + notifications |
| **Owner** | Claimed: `activity_inbox` · Also: `notifications_product` · Client: `activity_store.js` |
| **SoT** | **Contested** — `data/activity/inbox.jsonl` vs notifications history vs localStorage |
| **Public API** | `/api/activity/{inbox,publish,dismiss,read}` · `/api/notifications/*` |
| **Debt** | Bulk mutations local-only; desktop `notify-send` bypasses DND; outbox truncate non-atomic; circular settings mirror |

---

## 22. Dashboard

| Field | Value |
|-------|--------|
| **Purpose** | Honest widget aggregation |
| **Owner** | `dashboard_product` |
| **SoT** | Almost none — `last_good_home.json`, `layout.json` only |
| **Public API** | `/api/dashboard/*` |
| **Strength** | Per-widget unavailable + coach; stale cache labeled |
| **Debt** | Layout ownership collides with Layouts + ui_prefs |

---

## 23. Mission Control

| Field | Value |
|-------|--------|
| **Purpose** | Observe infrastructure health |
| **Owner** | `mission_control.py` → **aiplatform** · Aria ops in `mission_control_ops/` |
| **SoT** | Observes only (plus small Aria caches) |
| **Public API** | `/api/mission-control/*` |
| **External deps** | **Hard import** of aiplatform aggregator |
| **Debt** | Blocking collect on request thread; inconsistent ImportError handling |

---

## 24. Settings, Layouts, Shell

| Field | Value |
|-------|--------|
| **Purpose** | Preference index / workspace layouts / chrome tokens |
| **Owner** | `settings_product` (index) · `layouts_product` · `shell/` |
| **SoT** | Settings owns appearance; most prefs live in product files (13+ stores). Layouts: server JSON + client localStorage. Shell tokens in Python **not** linked to `style.css` |
| **Public API** | `/api/settings/*`, `/api/layouts/*`, `/api/shell/*` |
| **Debt** | Catalog drift; circular notification mirror; layouts apply success without client verify; design token dual SoT |

---

## 25. Automation

| Field | Value |
|-------|--------|
| **Purpose** | Scheduled/triggered actions + pipelines |
| **Owner** | Engine in `intelligence/automation_engine.py` · product in `jarvis/automation/` |
| **SoT** | `data/automation_product/rules.json` **and** permanent mirror `data/user_automations.json` |
| **Public API** | `/api/automation/*` · inbound webhook |
| **Strength** | `normalize_result` (skipped ≠ ok); inbound secret fail-closed |
| **Debt** | Circular package; dual-write; engine package location wrong |

---

## 26. Certification

| Field | Value |
|-------|--------|
| **Purpose** | Evidence-based ship gate |
| **Owner** | `certification_product` |
| **SoT** | `data/certification/runs/*` |
| **Public API** | `/api/certification/*` |
| **Gates** | `READY_TO_SHIP` · `SMOKE_PASS` · `DO_NOT_SHIP` |
| **Rule** | `skip_image` ⇒ cannot READY_TO_SHIP |
| **Debt** | Stale READY artifacts; fabricated screenshots; package untracked in git historically; not in CI pytest paths |

---

## 27. Frontend

| Field | Value |
|-------|--------|
| **Purpose** | Entire workstation UI |
| **Owner** | Split — **no single owner** (critical debt) |
| **SoT** | Server for most domains; localStorage for ui_prefs + partial activity |
| **Public API** | Views via `view_router.js`; network via patched `fetch` |
| **Internal deps** | 129 script tags; load order = graph |
| **Debt** | Globals; ariaMutate unused; media API key in query; manual `?v=` cache bust; 35-branch view router |

---

## 28. Background jobs

| Queue | Owner | Persists | Recovery |
|-------|-------|----------|----------|
| Media (GPU serial) | `media_jobs.py` | `media_jobs_state.json` | `recover_stale_jobs` → failed |
| Coding | `coding_jobs.py` | `coding_jobs_state.json` | load on start |
| Audio progress | `audio_progress.py` | **RAM only** | none |
| Checkpointed/agent | `jobs/checkpointed.py` | per-job JSON | full re-run (not mid-step) |
| Specialists / pipelines | respective modules | JSON deques | none |
| ComfyUI settings jobs | `comfyui_settings_jobs.py` | RAM | none |

`jobs_center.snapshot` aggregates with seven `except: pass` blocks.

---

## 29. Auth & security

| Field | Value |
|-------|--------|
| **Purpose** | API key, PIN lock, network guard, path/URL confinement, uncensored auth |
| **Owner** | `auth.py`, `security/*`, `lan.py`, `uncensored_auth.py` |
| **SoT** | Env `JARVIS_API_KEY`; PIN/uncensored JSON under `data/` |
| **Rule** | API-key exemption = **loopback only** (lan/remote always require key when configured) |
| **Strength** | LAN bind SystemExit without key; path_confine; url_guard DNS rebind check |
| **Debt** | Middleware order → PIN before NetworkGuard; `/api/health` prefix unlocks `/api/health/full` for PIN; query-string media keys; global handler leaks `str(exc)` paths |

---

## 30. Persistence map (clusters)

| Cluster | Examples | Problem |
|---------|----------|---------|
| Cognitive | `acm/cognitive.db` | Full-store snapshot/encode |
| Legacy memory | `memory.db`, `memory.json`, vectors | Cold / orphaned under PRIMARY |
| Chat | `chat_branches.json`, `chat_sessions.db` | Dual ownership |
| Life ops | `planner.db`, `journal/*`, calendar JSONs | Calendar multi-source |
| Media | `generated/`, `generated_videos/`, gallery meta/trash | Strong |
| Indexes | `code_index.json` ~90 MB, `rag_index`, `documents_index` | Heap + sync scan |
| Platform | `platform/cutover.json` | Dual_write narrative |
| Logs | `data/logs/` ~13 GB | No rotation |

---

## 31. Testing honesty limits

| Limit | Reality |
|-------|---------|
| CI coverage | 84/309 test files |
| Frontend | Source greps, not runtime |
| Streaming | Near-zero |
| Auth middleware | Near-zero |
| Job restart recovery | Incomplete |
| e2e | One optional Playwright file |

---

## 32. Document authority

| Document | Role |
|----------|------|
| **This Bible v2** | Authoritative architecture reference |
| ARCHITECTURE_REVIEW | Narrative understanding of the system as-is |
| ENGINEERING_AUDIT | Strengths/weaknesses inventory |
| ENGINEERING_ROADMAP | Prioritized improvements (approval required) |
| MEMORY_TRANSITION_* | Batch D memory plan (R1 done; R2+ gated) |
| Top-level `docs/ARIA_*CERTIFICATION*.md` | **Historical / contradictory — not authority** |

---

*End of Architecture Bible v2. Implementation requires explicit approval.*
