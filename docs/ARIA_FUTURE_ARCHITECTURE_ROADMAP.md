# ARIA Future Architecture & Capability Roadmap

**Status:** PLANNING / DISCOVERY ONLY — not an implementation authorization  
**Date:** 2026-08-16  
**HEAD inspected:** `1e18129` (`main`)  
**Constraint:** Capability-Driven Development, Production Integrity, Owner Vault, ACM as cognitive source of truth, and the 1.0 Engineering Constitution remain in force. This document proposes evolution of the *existing* personal OS — not a rewrite.

---

## Executive Summary

ARIA is already a **local-first personal operating environment**: systemd-owned HTTP server, 34 Living Workspace rooms, Owner Vault, ACM as cognitive source of truth, flagship products (Health, Journal, Coding, Fly Tying, Documents, Gallery, Browser, Automation, Connections), Guided Repair, and Production Integrity.

ARIA is **not** yet a persistent autonomous worker. Chat is a **router → handler → optional LLM** turn. Long-running work exists as **queues** (`coding_jobs`, media jobs, nightly knowledge research) and a **coding-only** checkpoint/pause store (`coding_tasks.py`). Intelligence-platform modules (reasoning, specialist teams, workflow DAGs, hybrid RAG) exist as APIs and are **partially integrated** — they are not the daily conversation loop.

The historical contamination of `data/` (certification/QA writing the live house) is the strongest argument for a **provenance / truth layer** and **harder production isolation** *before* adding more autonomous writers.

**Strategy:** extend existing organs (jobs, specialists, ACM, Guided Repair, browser agent, execution policy, plugin SDK) into one Agent Runtime. Do not replace rooms, ACM, vault, or Integrity. Do not chase Hermes messenger gateways, Perplexity-scale Search-as-Code, or a plugin marketplace.

**Recommended first moves (P0):** map and enforce ACM provenance onto room writers (do not invent a second provenance store); close remaining isolation holes (cert/Memgraph/MCP-to-live); unify task persistence. Then Agent Runtime. Then long-running execution. Then evidence-tagged research. Then subagents as a *promotion* of `jarvis.specialists`.

### Discovery corrections (second-pass audit)

Two read-only audits of core architecture and product rooms corrected the first-pass baseline. The important deltas:

1. **ACM already has a provenance module** (`aria_acm/acm/provenance/`: `ProvenanceRecord`, origins `told` / `perceived` / `inferred` / `legacy_import` / `learned` / …, trusted stamps `TRUSTED_USER_STATEMENT` / `TEACHING` / `CORRECTION`). The gap is **taxonomy mapping + uniform application**, not a missing store. Legacy `memory.json` entries have **no** provenance.
2. **`proactive_scheduler.py` does not start on the systemd serve path.** It starts from the tray/`daemon.py` path only. Serve lifespan *does* start the automation engine via `platform_runtime.bootstrap_runtime_connection()`. Nightly knowledge research and `reflection_loop.run_scheduled` are **not** called from the proactive loop. Overnight work must use the engine that actually runs under systemd, or the scheduler must be attached to serve — not assumed.
3. **`local_router.try_local_route()` is dead on production chat** despite `JARVIS_LOCAL_ROUTER` defaulting on. Chat uses NLU → `_quick_route` → `llm.route_with_tools`. Do not treat the local router as the live path.
4. **Specialist checkpointed jobs persist JSON but `checkpoint["resumable"]=False`** — restart **re-runs the whole team**, it does not resume mid-step.
5. **Media jobs already recover/resume** (`media_jobs.recover_stale_jobs`, `resume_interrupted_jobs` in serve lifespan). Coding jobs persist state; CodingAgent is bounded (`DEFAULT_MAX_STEPS = 5`).
6. **`ProductionIsolationMiddleware` + `production_guard.assert_environment_consistent()` already refuse QA/test env on live `DATA_DIR`.** Remaining hole is historical cert campaigns, shared Memgraph, and MCP that **HTTP-proxies the live serve**.
7. **Products previously under-classified:** Search, Automation, Connections (SQLite default, review-then-approve ingest), Maker, Browser (Playwright, fail-closed if Chromium missing), morning briefing, and `orchestration_policy.py` are **live COMPLETE** organs. Knowledge research *pipeline* is real; **auto-nightly is not on the daemon**. Presence/gestures are **client MediaPipe**, not a server vision loop. Capabilities loader works; **plugin sandbox does not isolate**.
8. **`certification` is a view alias of Integrity**, not a 35th room.
9. **Cloud inference is implemented and off** (`JARVIS_CLOUD_INFERENCE` default `0`). Local-first is already the production policy, not a future wish.
10. **Documents learn writes Memory *candidates* only** (never silent ACM). Connections ingest is the same pattern. Reuse that law for research claims.

---

## Current ARIA Baseline

Inspected from repository + live process identity (systemd `jarvis.service` → `scripts/aria-serve.sh` → `venv/bin/python main.py serve`, `JARVIS_DATA_DIR=/media/jeff/AI/jarvis/data`). Classifications are about **integrated production capability**, not file existence.

### Application / server

| Item | State | Evidence |
| --- | --- | --- |
| Production serve | **COMPLETE** | `~/.config/systemd/user/jarvis.service`; `jarvis/gui/server.py` FastAPI 3.1.0; `127.0.0.1:8765`; lifespan recovers media jobs, ACM flush on shutdown |
| Tray | **COMPLETE** (client) | `main.py tray` / `daemon.py` must not spawn a second serve when systemd owns it |
| Proactive scheduler | **EXISTS BUT NOT INTEGRATED** on systemd serve | `jarvis/proactive_scheduler.py` starts from tray/daemon only (briefing, health reminders, integrity scan, fly-tying nightly). **Not** in `gui/server.py` lifespan |
| Automation engine on serve | **COMPLETE** | `platform_runtime.bootstrap_runtime_connection()` → `start_automation=True`; rules in `data/automation_product/rules.json` |
| Runtime Independence (desktop shell) | **PARTIAL** | Charter (`docs/ARIA_NEXT_GENERATION_CHARTER.md`) approved Living Workspace; Phase 1 runtime spikes not the daily path — live UI is still the HTML workspace |
| Platform bootstrap | **PARTIAL** | `jarvis/intelligence/platform_bus.py` `bootstrap_platform()` wires connectors, example plugin, workflow templates |

### Frontend / rooms

34 rooms in `jarvis/gui/static/workspace/registry.js` (`AriaWorkspaceRegistry`). Front Door + hash routing (`view_router.js`). Rooms are **flagship destinations**; tools are contextual. This is production.

**COMPLETE as a room OS** (34 IDs in `AriaWorkspaceRegistry`; `certification` is a **view alias of Integrity**, not a room). Not complete as an Agent Command Center (no first-class Tasks / Research / Approvals / Agents surfaces). Jobs Center (`GET /api/jobs`) already aggregates media + coding + audio + Comfy + checkpointed specialist jobs.

### Memory / ACM / profile

| Item | Class | Why |
| --- | --- | --- |
| ACM cognitive store | **COMPLETE** (SoT) | `data/acm/cognitive.db`; `/api/memory/stats` `backend=acm`; first-run seeds `agent:aria` + cheatsheets |
| Legacy `memory.json` / `memory.db` | **PARTIAL** | Still on disk; API source of truth is ACM. Dual stores remain a contamination/confusion risk |
| Profile questionnaire | **COMPLETE** | `jarvis/profile_questionnaire.py` `save_answers()` → namespace `profile` |
| Cheatsheet seed | **COMPLETE** | `JarvisAssistant.__init__` → `seed_cheatsheets()` — first-run system knowledge, not user facts |
| ACM provenance module | **PARTIAL** | `aria_acm/acm/provenance/` `ProvenanceRecord` + `stamp_provenance` + ingestion evaluate. Origins: told/perceived/inferred/reconstructed/legacy_import/learned/reflective/reconciled/simulated/analogical/encode/adopted_knowledge/unknown. **Not** mapped to USER_STATED / TEST_DATA / WEB_SOURCE / environment. Not applied to Health/Journal/Jobs/research markdown |
| Provenance on room writers | **MISSING** as a uniform interceptor | Cheatsheet concepts currently surface in Memory “About you”; historical cert/QA mixed with user life |
| Trust strategies | **COMPLETE** as chat guardrail | `jarvis/trust_memory.py` `seed_default_strategies()` on system-prompt build; filters test artifacts. Not a truth engine |
| Explicit teaching (`explicit_teaching.py`) | **EXISTS BUT NOT INTEGRATED** | Chat “teach Aria” is ACM teaching; `explicit_teaching_system_block` unused by router (tests + document_learning only) |
| Reflection loop | **EXISTS BUT NOT INTEGRATED** | `reflection_loop.run_scheduled` never called from `proactive_scheduler`; status API exists |

### Agent / tools / orchestration

| Item | Class | Why |
| --- | --- | --- |
| Action registry | **COMPLETE** | `jarvis/handlers/registry.py` `ActionSpec` + extension handlers |
| NLU / router | **COMPLETE** for chat turns | `jarvis/router.py` cascade: clarification → skills → automation → specialists → NLU → `_quick_route` → `llm.route_with_tools` (`route_request` only). `orchestration_policy.py` is live |
| Local mini-router | **EXISTS BUT NOT INTEGRATED** | `jarvis/local_router.py` `try_local_route()` is **not** called from `router.route()` |
| Tool-calling LLM loop | **PARTIAL** | Routing-only function call, not a general tool-use agent loop. Capability `tool_calling` via `resolve_model_for_capability` |
| Specialist teams | **PARTIAL** | `jarvis/specialists/engine.py` `run_team()` — real organs, confirm gate, scratchpad. Router *can* send to specialists; not the default ASK path. Jobs: `jarvis/jobs/checkpointed.py` persist but **not mid-step resumable** |
| Reasoning module | **EXISTS BUT NOT INTEGRATED** into daily chat | `jarvis/intelligence/reasoning.py` — heuristic plan/self-check; API/platform, not every user turn |
| Persistent Agent Runtime (goal→plan→execute→evaluate→replan→verify) | **MISSING** | Pieces exist; no single runtime owns the loop across restart |
| Coding jobs queue | **COMPLETE** for coding | `jarvis/coding_jobs.py` — in-process workers, JSON state, cancel, timeout. **Not** a general agent runtime |
| CodingAgent loop | **COMPLETE** and **bounded** | `jarvis/coding_agent.py` plan→read/search/run/verify, `DEFAULT_MAX_STEPS = 5`. Pause is status+checkpoint dict, not a suspended coroutine |
| Coding task checkpoints | **COMPLETE** for coding only | `jarvis/coding_tasks.py` TaskManager → `data/coding_tasks.json` |
| Media GPU queue | **COMPLETE** | `jarvis/media_jobs.py` recover/resume on serve lifespan |
| Jobs Center | **COMPLETE** as snapshot | `jarvis/jobs_center.py` `GET /api/jobs` — not a general AgentTask model |
| Background chat actions | **COMPLETE** as adapters | `jarvis/background_jobs.py` — document_summarize, learn_about, knowledge_research_run, self_upgrade_run, aria_self_fix |
| Nightly knowledge research | **PARTIAL** | Pipeline real (`knowledge_research_daily.py`); **not** on systemd proactive loop; not open-ended Deep Research |
| Self-upgrade / self-fix | **COMPLETE** (gated) | `jarvis/self_upgrade.py` — git branch, test, **approval** to merge |
| MCP | **COMPLETE** as Cursor-dev, **PARTIAL** as house tool layer | `scripts/jarvis-mcp-server.py` FastMCP stdio; coding tools via `cursor_bridge`; domain tools **HTTP-proxy live serve**. systemd does not start it. No owner MCP client directory |

### Models / routing

| Item | Class | Why |
| --- | --- | --- |
| Ollama local catalog | **COMPLETE** | Large local inventory (Qwen, DeepSeek-R1, LLaVA, Moondream, coder variants, etc.) |
| Role → model store | **COMPLETE** | `jarvis/model_store.py` `data/model_settings.json`; canonical roles include conversation, reasoning, coding, vision, web_research, tool_calling, … |
| Capability routing | **COMPLETE** | `jarvis/capability_routing.py` `resolve_model_for_capability()` |
| Execution policy | **PARTIAL / EXPERIMENTAL** | `jarvis/inference/execution_policy.py` + optional `data/execution_routing_policy.json` from benchmarks; not required for serve |
| Cloud / LiteLLM | **COMPLETE** as code, **off** in production | `JARVIS_CLOUD_INFERENCE` default `0`; `inference/policy.py` gateway_mode `auto` |
| Provider health | **COMPLETE** as overlay | `jarvis/provider_health/` does not own inference |
| FunctionGemma local tool router | **EXPERIMENTAL / PARTIAL** | Checkpoints under `data/models/functiongemma-aria`; production chat path is NLU + `route_with_tools`, not this file |

### Security / integrity / tests

| Item | Class | Why |
| --- | --- | --- |
| Owner Vault | **COMPLETE** | `jarvis/security/owner/` `aria-owner-vault-v1`; one Master Password; no idle lock by policy |
| Health PHR gate | **COMPLETE** | Locked until owner unlock (`423` when locked) |
| Production Integrity product | **COMPLETE** as a scanner | `/api/integrity/*`; never auto-deletes |
| Pytest isolation | **COMPLETE** for unit tests *now* | `tests/conftest.py` `JARVIS_DATA_DIR=tmp_path`; `jarvis/live_data_guard.py` |
| Production isolation middleware | **COMPLETE** as request guard | `ProductionIsolationMiddleware` + `production_guard.assert_environment_consistent()` refuse QA/test env on live `DATA_DIR` |
| Isolation vs certification/room-repair/Memgraph/MCP | **PARTIAL / historically FAIL** | Live house was used as cert DB; Memgraph is a shared docker; MCP domain tools proxy the live serve |
| Owner capability catalog | **COMPLETE** as IAM list | `jarvis/security/owner/capabilities.py` — room/product IAM, **not** MCP ACLs |
| PIN / idle lock | **PARTIAL** / intentional | PIN default off; idle lock default 0 seconds (no automatic lock) |
| Proposal apply / undo | **COMPLETE** for coding | Not universal snapshot/rollback |

### Product rooms (flagships)

| Product | Class | Notes |
| --- | --- | --- |
| Health / PHR | **COMPLETE** | Isolated sqlite; owner-gated; do not let agents write without approval |
| Journal | **COMPLETE** | Bullet journal; first-run may enrich today’s page (quotes/prompts) |
| Planner / Calendar | **COMPLETE** | sqlite planner |
| Projects | **COMPLETE** | `project_registry.py`; namespaces per slug |
| Documents + RAG | **COMPLETE** (path wrinkle) | Real parse/RAG/Q&A; learn → Memory **candidates** only. `document_pipeline.DOCUMENTS_DIR` is not always `DATA_DIR`-aware |
| Fly Tying | **COMPLETE** as domain product | Dual API (legacy + product); Blackfly library; nightly hatch **is** on proactive_scheduler (tray path) |
| Gallery | **COMPLETE** | Real generate enqueue + library + soft-delete |
| Video | **PARTIAL** | Real media queue; no-op if Comfy/AnimateDiff down |
| Audio / voice | **COMPLETE** | Local STT/TTS/wake; first-run may download Piper/Whisper |
| Maker / CAD / print | **COMPLETE** (print hardware-gated) | build123d/OpenSCAD/slice/Moonraker; Bambu is honest Studio/SD **handoff**, not silent LAN |
| Browser | **COMPLETE** as Playwright product, **PARTIAL** vs Gemini computer-use | Dedicated session thread; DOM/VLM; fail-closed without Chromium; research plan/tab/merge APIs exist |
| Coding | **COMPLETE** as propose→apply | Bounded agent (5 steps) + jobs + verify workflow; not a 25-hour Codex loop |
| Automation | **COMPLETE** (two API surfaces) | Product engine + DAG pipelines are live; older `/api/intelligence/automation*` is a second real API, not chrome |
| Connections / graph | **COMPLETE** on SQLite | Default `JARVIS_GRAPH_BACKEND=sqlite`; ingest is **review-then-approve**; Memgraph optional Docker |
| Presence / face | **PARTIAL** | Face enroll/verify on server; gestures/webcam are **client MediaPipe** (`backend: "client"`) |
| Vision / OCR | **COMPLETE** as bench | Not a unified computer-use stack |
| Search | **COMPLETE** as federated search | `search_product` queries documents/ACM/code/journal/projects/graph/web/… Experimental multi-hop is a stub. **Not** Deep Research |
| Repair / Integrity | **COMPLETE** | Guided Repair approve→execute→verify; Integrity read-only scan. Integrity scan **is** on proactive_scheduler (tray path) |
| Capabilities / plugins | **PARTIAL** | Loader + `hello_aria` seed work; `plugin_sdk` sandbox **does not isolate**; WASM/signing are honest stubs |
| Integrations / providers | **COMPLETE** | Secret bus (vault then `jarvis.env`); test-connection is real |
| Home Automation | **COMPLETE** | HA integration; vault-backed token |
| Knowledge briefs | **PARTIAL** | `learn_topic` + nightly research **write real markdown**; auto-nightly **not** on systemd loop |
| Morning briefing | **COMPLETE** | Same builder for launch/chat; scheduler nudge is tray-path |

### Databases (production)

SQLite (WAL): ACM `cognitive.db`, `memory.db`, `memory_vectors.db`, `planner.db`, `health.db`, `chat_sessions.db`, `relationship_graph.db`. JSON stores for chat branches, jobs, journal, projects, automation. Memgraph optional (`JARVIS_GRAPH_BACKEND=memgraph`). External: Ollama, Home Assistant, Blackfly library on `/media/jeff/C/fly_fishing_project`, SearxNG if configured.

---

## Modern Agent Capability Benchmark

Comparison is of **capabilities**, not brands. Sources: OpenAI Agents SDK / Codex long-horizon runs; Anthropic Claude Code (loop + permissions + skills + MCP + subagents); Gemini Deep Research + Computer Use; Perplexity Deep Research / Computer / SPACE sandboxes; Nous Research Hermes Agent (persistent runtime, skills from experience, cron, subagents, MCP).

### OpenAI Agents SDK / Codex

| | |
| --- | --- |
| Capability | Agent + Runner loop; tools; handoffs vs agents-as-tools; input/output/tool guardrails; sessions; tracing; approval interruptions; Codex multi-hour plan→implement→validate→repair |
| Why it matters | Separates *model* from *runtime*. Long-horizon coding proves restart-coherent work is a product, not a demo |
| Strengths | Clear primitives; guardrails; observability; mid-run steering |
| Weaknesses | Cloud-centric; not a personal OS; weak local-life memory |
| ARIA equivalent | Turn router + coding jobs + Guided Repair approvals — **not** a Runner |
| Adopt? | **Concept yes** (runtime, guardrails, approvals). SDK-as-dependency **no** |
| Improve? | Bind the loop to ACM provenance, rooms, and local models |

### Anthropic Claude Code / Skills / MCP / Subagents

| | |
| --- | --- |
| Capability | Simple while-loop + tools; 7-mode permissions; skills as on-demand procedural packages (`SKILL.md`); MCP as access layer; subagents isolated from parent context; hooks |
| Why it matters | Clean split: **Skills = how**, **MCP = what systems**, **Subagents = where work runs**, **Hooks = guaranteed reactions** |
| Strengths | Context-efficient skills; production MCP; human authority |
| Weaknesses | IDE/coding-shaped; not Health/Journal/HA life OS |
| ARIA equivalent | Plugin SDK + cheatsheets + MCP *outbound to Cursor*; specialists |
| Adopt? | Skills + permission modes + subagent isolation **yes**. Replace Aria MCP-for-Cursor **no** |
| Improve? | Skills that call *rooms and organs*, not only a repo |

### Gemini Deep Research + Computer Use

| | |
| --- | --- |
| Capability | Autonomous multi-step research with plan refinement, citations, MCP, file search, max-time budgets; computer use via screenshot→UI actions with intent + confirmation + prompt-injection scan |
| Why it matters | Research and computer-use are **products**, not “the model browsed once” |
| Strengths | Depth, citations, async Max, safety metadata on actions |
| Weaknesses | Cloud; Google-shaped retrieval; not owner-private by default |
| ARIA equivalent | `knowledge_research_daily` + `web_search` + Playwright browser agent |
| Adopt? | Research loop + stopping criteria + computer-use *safety* **yes**. Depend on Gemini API **optional only** |
| Improve? | Local docs + PHR-never-leaves-machine + owner vault |

### Perplexity Deep Research / Computer / SPACE

| | |
| --- | --- |
| Capability | Plan → thousands of parallel retrievals (“Search as Code”); cited reports; sandboxed long-running code (SPACE) |
| Why it matters | Parallel retrieval quality; sandbox as first-class runtime |
| Strengths | Citation culture; scale |
| Weaknesses | Not local-first; compute cost; not a personal house |
| ARIA equivalent | SearxNG/web_search + document RAG — serial, small |
| Adopt? | Citation + sandbox for code/browser **yes**. Thousand-way parallel web **don’t chase** |
| Improve? | Personal corpus + web, with provenance |

### Nous Hermes Agent

| | |
| --- | --- |
| Capability | Persistent `AIAgent` loop; USER.md/MEMORY.md; FTS5 session search; autonomous skill creation; cron; subagents; MCP; many terminal backends; messenger gateways |
| Why it matters | Closest open “agent OS” to Aria’s *ambition* — learning loop + unattended work |
| Strengths | Persistence; skills-from-experience; not IDE-locked |
| Weaknesses | Not a 34-room life OS; self-improving skills without Aria’s Integrity culture are dangerous; messenger-first |
| ARIA equivalent | Chat + automation cron + cheatsheets + self-upgrade (approval) |
| Adopt? | Persistent runtime, cron delivery into Activity Center, skill *proposals* **yes**. Silent skill mutation **no**. Telegram-as-primary **don’t chase** |
| Improve? | Hermes loop **inside** Living Workspace + Vault + Integrity |

### MCP ecosystem (2026)

Stateless request/response core, OAuth, Tasks/Apps extensions. Aria should be an **MCP client** (discover owner-approved servers) and keep the existing **MCP server for Cursor** as a developer tool, not the owner runtime.

---

## Capability Gap Analysis

| Capability | ARIA now | Gap |
| --- | --- | --- |
| Persistent goal loop | Missing as a unified runtime | Chat is request-scoped; coding agent is a 5-step loop; specialist jobs re-run on restart |
| Restart-resume any task | Media jobs resume; coding tasks persist status; specialist `resumable=False` | General AgentTask mid-step resume missing |
| Overnight scheduling | Automation engine **does** run on systemd serve; `proactive_scheduler` does **not** | Briefing/integrity/knowledge-nightly/reflection can silently skip if tray never starts |
| Deep research | Several real pipelines (web, learn_topic, nightly, browser research) | No claim graph, contradiction, stopping criteria, citations as first-class; nightly not on systemd loop |
| Provenance | ACM `ProvenanceRecord` exists | Not mapped to TEST_DATA/WEB_SOURCE/environment; rooms don’t stamp uniformly |
| Subagents | Specialists on router cascade + `run_team` | Not default ASK; checkpoint not mid-step |
| Computer use | Playwright product COMPLETE | No desktop; Gemini-style intent/confirm/injection scan incomplete |
| Universal tools / MCP host | Handlers + Cursor MCP (proxies live serve) | No owner-facing MCP client directory; live-proxy is a risk |
| Skills | Plugins + cheatsheets + DAG templates | Sandbox does not isolate; no SKILL.md lifecycle |
| Model routing | Role store + capability routing COMPLETE; execution_policy experimental | Privacy class + “strongest permitted” research router |
| Observability | Action history, Jobs Center, Mission Control | No agent trace (plan/step/tool/subagent/evidence) |
| Universal rollback | Coding undo + Guided Repair | Not files+memory+graph+research snapshots |
| Isolation | Middleware + pytest guard COMPLETE | Historical cert-on-live; Memgraph; MCP-to-live |
| Isolation | Pytest guard | Cert/Memgraph/live campaigns historically wrote production |

---

## Target Architecture

Do **not** replace the Living Workspace. Place an Agent Runtime *beside* Conversation, using Rooms as organs.

```text
ARIA (Living Workspace)
│
├── Conversation          # Chat room — ASK path; existing router
├── Intent                # NLU + ASK/DO/RESEARCH/MONITOR classifier (extend orchestration_policy)
│
├── Agent Runtime         # NEW facade over coding_jobs + TaskManager + specialists
│   ├── Planner           # extend intelligence/reasoning.py + Planner room
│   ├── Executor          # handlers registry + tool router
│   ├── Evaluator         # NEW thin verifier (promote Guided Repair + critic_loop)
│   ├── Checkpoints       # generalize coding_tasks.checkpoint
│   └── Recovery          # systemd restart → resume RUNNING tasks
│
├── Research Engine       # promote knowledge_research_daily + web_search + documents
│   ├── Search / Read / Extract
│   ├── Claims + Evidence + Verification
│   └── Reports → Documents + Memory (provenance-tagged)
│
├── Subagent System       # promote jarvis.specialists (not a second catalog)
│
├── Tool Router
│   ├── Native handlers   # KEEP
│   ├── MCP client        # NEW — owner-approved servers
│   ├── Browser           # extend browser_agent
│   ├── Code              # CodingAgent
│   └── APIs / HA         # connectors + home_assistant
│
├── Model Router          # extend execution_policy + vault providers
│
├── Memory / ACM          # KEEP as SoT
│   ├── User / Project / Research / Evidence / System
│   └── Provenance (required on persist)
│
├── Skills                # promote plugin_sdk + cheatsheets + automation templates
├── Security              # KEEP vault; add agent/tool permission matrix
├── Scheduler             # KEEP automation engine; attach to Agent Runtime
├── Observability         # extend Action History + Jobs Center + Mission Control
└── UI
    ├── Rooms (KEEP flagships)
    └── Agent Command Center surfaces: Tasks, Research, Agents, Approvals
        (Home/Chat/Projects/Memory/Schedule/Activity/Settings already exist)
```

---

## Agent Engine

### What exists

```text
User message
  → router / NLU / orchestration_policy
  → ActionSpec.handler  OR  coding_jobs.submit(callable)
  → optional LLM
  → response
```

- Task IDs: job UUIDs in `coding_jobs`; `CodingTask.id` in `coding_tasks.py`.
- Persistence: `coding_jobs_state.json`, `coding_tasks.json` — **not** a general goal graph.
- Pause/resume/checkpoint: **coding tasks only**.
- Cancel: coding job cancel check.
- Timeouts: `JARVIS_CODING_JOB_TIMEOUT_SEC` (default 600).
- Specialist run: `run_team(..., confirm=, cancel_check=, on_progress=, critic_loop=)`.
- Reasoning: `intelligence/reasoning.py` heuristic steps + confidence.

### What must be built (extend, don’t replace)

A single **`AgentTask`** record (sqlite or JSON under `data/agent/` — isolated from tests):

`id, mode (do|research|monitor), goal, plan[], state, owner, organ, checkpoint, parent_id, verifier, provenance, budget, created, updated`

Loop (map to existing code):

```text
Goal
↓ Intent          # orchestration_policy + explicit user override
↓ Plan            # reasoning.plan + specialist composer
↓ Execute         # handlers / CodingAgent / browser_agent / research
↓ Observe         # tool results + organ APIs
↓ Evaluate        # verifier specialist + tests where coding
↓ Replan          # only if evaluate says NOT DONE and budget remains
↓ Verify          # Guided Repair-style evidence; never “DONE” without it
↓ Complete        # persist artifacts with provenance
```

**Do not** import OpenAI Agents SDK as the runtime. Implement the *shape* using Aria jobs + TaskManager.

---

## Long-Running Execution

**Requirement:** “Work on this until it is finished” survives browser close and Aria restart.

**How, using existing architecture:**

1. **systemd already keeps serve alive.** The gap is *task* durability, not process durability.
2. **Do not assume `proactive_scheduler` runs in production.** systemd serve starts the **automation engine**, recovers **media jobs**, and flushes ACM on shutdown. Attach overnight MONITOR/research either to `jarvis/automation/engine.py` (the path that actually runs) or start the proactive scheduler from serve lifespan — one loop, not two.
3. Generalize `coding_jobs` + `CodingTask` + `jobs/checkpointed.py` so a restart loads `state=running|paused` and re-queues. Today specialist jobs **re-run from the start** (`resumable=False`). Media jobs already resume.
4. Watchdog: Mission Control already monitors organs — add “stale RUNNING task” as a Guided Repair issue. Integrity/health nudges on the tray scheduler should be reachable under systemd too, or they silently skip when Jeff never opens the tray.
5. Budgets: wall clock, token/VRAM, step count, network — fail to `paused_needs_approval`, not silent infinite loop. CodingAgent already caps at 5 steps; general tasks need an explicit budget.
6. Indefinite MONITOR: first-class mode with cheap local model + heartbeat; never a 32B loop 24/7.

**Recovery classes:** crash (reload checkpoint), network (retry with backoff), model (execution_policy fallback), tool (specialist stop_on_error / repair).

---

## Deep Research

**Reuse:** `web_search.py` (SearxNG → ddgs → HTML fallback), `orchestration_policy.py`, `research_verification.py`, `research_context.py`, `documents_rag` / `hybrid_rag.py`, `knowledge/topics.py` `learn_topic`, `knowledge_research_daily.py`, Browser `/api/browser/research/plan|tab|merge`, Documents PDF/OCR, Connections **propose-then-approve** ingest, Search federated retrievers, Memory **candidates** (Documents learn already never silent-ACM).

**Build:** open-ended Research Task (not only `ai_news|ollama|zorin|dependencies`), question list, iterative search, source ranking/diversity, extract-with-span, claim objects, contradiction, confidence, stop when new evidence < ε or budget, citation-backed report in Documents, continuation. Wire nightly catch-up to the **systemd-owned** automation engine (today `run_scheduled` is unused).

**Build:** open-ended Research Task (not only `ai_news|ollama|zorin|dependencies`), question list, iterative search, source ranking/diversity, extract-with-span, claim objects, contradiction, confidence, stop when new evidence < ε or budget, citation-backed report in Documents, continuation.

```text
Objective → Questions → Search → Read → Extract Evidence → Evaluate
  → Gaps → Search again → Cross-check → Verify → Synthesize → Report
```

**Do not** auto-`remember` research into user profile. Write `source=WEB_SOURCE|DOCUMENT_SOURCE`, `verified=false` until Verification Agent or Jeff confirms.

---

## Evidence / Truth Layer

Mandatory after the 2026 contamination incident.

Every persist of a *belief* carries:

| Field | Purpose |
| --- | --- |
| `kind` | USER_STATED / USER_CONFIRMED / SYSTEM_OBSERVED / DOCUMENT_SOURCE / WEB_SOURCE / MODEL_INFERENCE / AGENT_DERIVED / TEST_DATA / SYSTEM_DEFAULT |
| `verified` | VERIFIED / UNVERIFIED / CONFLICTED / STALE |
| `source_uri` | file, URL, vault id, job id — never a secret value |
| `span` | passage / row id |
| `ts` | created / observed |
| `confidence` | 0–1 with reasons |
| `owner` | jeff / system / agent:<id> / test |
| `environment` | production / qa / test |

Trace:

```text
Claim → Evidence → Source → Passage → Timestamp → Verification → Confidence
```

**Protections:** TEST_DATA never writable when `JARVIS_ENVIRONMENT=production`; SYSTEM_DEFAULT (cheatsheets, habits, templates) labeled so Memory “About you” cannot present them as autobiography; prompt-injection: treat WEB_SOURCE as untrusted until extract+verify; Integrity scan flags missing provenance.

**Do not invent a second provenance database.** Extend `aria_acm/acm/provenance/ProvenanceRecord`.

Map ACM `origin` onto the house taxonomy (additive metadata, not a rename-and-break):

| House kind | Existing ACM `origin` (approx.) |
| --- | --- |
| USER_STATED / USER_CONFIRMED | `told` + trusted stamps `TRUSTED_USER_STATEMENT` / `CORRECTION` |
| SYSTEM_OBSERVED | `perceived` |
| MODEL_INFERENCE / AGENT_DERIVED | `inferred` / `learned` / `reflective` |
| DOCUMENT_SOURCE / WEB_SOURCE | add `metadata.source_kind` + URI (not present as first-class today) |
| TEST_DATA | **must be new and fail-closed in production** |
| SYSTEM_DEFAULT | cheatsheet / template seed — tag so About-you cannot claim autobiography |
| legacy | `legacy_import` / `unknown` — treat as UNVERIFIED |

Plus `verified` (VERIFIED / UNVERIFIED / CONFLICTED / STALE), `source_uri`, `span`, `environment` (production / qa / test), `owner`.

---

## Memory Architecture

Keep **ACM as sole cognitive SoT**. Legacy JSON/sqlite become forensic/migration only (already the stated direction).

Recommended namespaces (map to existing):

| Kind | Store | Notes |
| --- | --- | --- |
| User facts / preferences | ACM `profile` + explicit remember | Questionnaire remains the onboarding path |
| Episodic | ACM experiences | Chat/journal events — not graph-as-memory |
| Semantic / project | ACM + project namespace | `project_registry` already has memory_namespace |
| Task state | AgentTask store | **Not** ACM (operational, not autobiographical) |
| Research evidence | Documents + claim table | ACM only after verification |
| System knowledge | cheatsheet namespace | Already tagged `cheatsheet`/`protected` |
| Temporary / tool results | scratchpad | `specialists/scratchpad.py` — TTL |
| Test data | forbidden in production | Integrity + live_data_guard + env |

Lifecycle: create → verify → use → conflict → correct/forget (existing forget/cool paths) → expire.

**Do not replace ACM or its provenance module.** Stamp room writers through `stamp_provenance`; fix About-you to exclude SYSTEM_DEFAULT and cheatsheet concepts. Chat teaching stays ACM (`aria_acm/acm/authority/teaching.py`); do not revive `explicit_teaching.py` as a parallel brain.

---

## Subagents

**Reuse `jarvis.specialists` catalog** (planner, researcher, coder, writer, … mapped to real organs). Do not invent a parallel “Research Agent” type system.

Policy:

- **Hybrid:** one Owner conversation; specialists as **agents-as-tools** (manager retains control) by default; **handoff** only for long isolated jobs (coding, research) with their own AgentTask.
- Separate **model assignment** via execution_policy (coder → coder model, vision → llava/moondream).
- Isolation: specialist scratchpad + tool allowlist + `read_only` flag already in catalog.
- Permissions: inherit Owner session; writes need `approve_writes` (already on `run_team`).

New specialists only when an organ exists: Verification (critic_loop today), Browser, Linux/shell (tight sandbox), Data, Memory (candidates only).

---

## Agent Collaboration

Extend `SharedScratchpad` + `synthesize()`:

- Shared task id, evidence bag, message log.
- Dedup: same (tool, args-hash) cache.
- Anti-runaway: TeamBudget max specialists / steps / wall time (exists).
- No circular delegation: call graph DAG; forbid A→B→A.
- Conflict: Verification Agent + Jeff approval; never silent overwrite of USER_CONFIRMED.

---

## Verification Agent

Promote `critic_loop` + Guided Repair verification culture.

Before DONE:

- Objective satisfied? Requirements covered? Claims have evidence? Sources adequate? Contradictions? Unauthorized writes? Tests (if coding)? Budget leftover implying more work?

Output: `DONE` | `NOT DONE — continue` | `BLOCKED — approval` | `FAILED — rollback`.

Coding already has propose → verify path. Generalize that contract.

---

## Browser / Computer Use

**Extend `jarvis.browser_agent` + Playwright session thread** (`browser_product/session.py`). Capabilities today: navigate, screenshot, run-task, DOM/VLM, downloads gated, SSRF guard, project profile cookies.

**Add (carefully):** form fill, scroll, click with **intent string** (Gemini pattern), confirmation on purchase/credential/nav-off-allowlist, prompt-injection scan on page text/screenshot.

**Desktop computer-use:** **don’t chase** as P0. Linux desktop control is a high-risk organ; Browser + terminal (sandboxed) covers most “computer use” for Jeff. Revisit only after Agent Runtime + permissions.

---

## MCP / Tools

Keep native **ActionSpec** as the fast path for rooms.

Add **MCP client** (owner Integrations room): discover, enable, schema, health, audit, isolation. Map MCP tools into the same permission matrix as handlers.

Keep **`jarvis-mcp-server.py`** as Cursor-only (development). Domain tools already HTTP-proxy the live serve — **do not** point Health/Journal writes at it; treat that proxy as a standing risk until scoped to a non-production assistant or read-only tools.

Filesystem, terminal, git, HA, calendar: already native — wrap with the same audit, do not duplicate via MCP unless the server is external.

---

## Skills

Promote, don’t replace:

| Today | Future skill field |
| --- | --- |
| Cheatsheets | purpose + examples |
| `plugin_sdk` manifest | tools, permissions, activation |
| Automation DAG templates | procedures |
| Guided Repair modules | verification + failure |
| Hermes-style SKILL.md | version, disable, test |

**Self-improving skills:** only as Guided Repair proposals (“I saw this failure N times — here is a skill draft + isolated test”). No silent writes to production skills. `self_upgrade.py` already uses approval+tests — copy that law.

---

## Model Routing

**Reuse `execution_policy.py` REQUEST_CLASS_WORKLOAD** and vault providers.

Proposed routing (all local-first):

| Class | Default (this house) |
| --- | --- |
| Fast/simple | `qwen3:1.7b` / `qwen2.5:3b` |
| Coding | `qwen2.5-coder-32b-64k` or `devstral` / `deepseek-coder-v2` |
| Reasoning | `deepseek-r1:14b` |
| Vision | `moondream` / `llava:13b` / `qwen2.5vl:7b` |
| Private | local only; never cloud |
| Deep research | strongest **permitted** (local 32B or vault cloud if Jeff enabled) |
| Tool routing | FunctionGemma if healthy, else heuristics |

Fallbacks already sketched in policy; add **privacy class** on each task and **user override** in Providers room.

---

## Security

Keep Owner Vault and one Master Password.

Add agent permission levels:

| Level | Meaning |
| --- | --- |
| READ | Search, memory recall, HA status |
| SAFE WRITE | Project coding root, `data/generated`, research drafts |
| APPROVAL REQUIRED | Apply patch, journal write, PHR, graph ingest, send, install, systemd, credentials |
| AUTONOMOUS | Explicit per-task grant with budget + expiry |

Emergency stop: existing cancel + Owner Lock Aria (do not auto-click; document as the big red switch).

Audit: extend Action History with agent_id, tool, args-redacted, decision.

Sandbox: coding already proposes before apply; shell/MCP need the same.

---

## Rollback

**Reuse:** proposal undo, Guided Repair rollback, git for repo work.

**Add:** pre-flight snapshot manifest for AgentTask (paths + db export *of the task’s working set only* — never snapshot live PHR by default). Verify then keep or restore.

Health/Journal/Vault: **never** in autonomous snapshot-restore without Jeff.

---

## Observability

Extend Jobs Center + Action History + Mission Control into an **agent trace**:

current task, plan, step, tool calls, subagents, elapsed, VRAM/CPU, errors, retries, checkpoints, evidence count, pending approvals, verifier verdict.

Do not build a separate APM product. Wire traces into Mission Control cards.

---

## Agent Command Center

Living Workspace law: **rooms stay**. Add *surfaces* (or Home cards), not a 13th product farm:

| Surface | Maps to |
| --- | --- |
| HOME | existing foyer |
| CHAT | Living Room |
| TASKS | Jobs Center + new AgentTask list |
| RESEARCH | Memory/Search + research reports in Documents |
| PROJECTS | existing |
| MEMORY | existing (fixed About-you) |
| AGENTS | specialist team status (new panel, not a new organ) |
| TOOLS | Capabilities + Integrations (MCP enablement) |
| SCHEDULE | Planner + Automation |
| ACTIVITY | Action History |
| APPROVALS | Guided Repair + proposal Apply + agent grants |
| SETTINGS | existing |

Activities (`registry.js` ACTIVITIES) already intend “Jeff performs activities; Workspace assembles rooms+tools.” Agent tasks should be Activities, not a competing IA.

---

## ASK / DO / RESEARCH / MONITOR

Extend `orchestration_policy.py` (already steals greetings vs web_search vs research):

| Mode | Default | Override |
| --- | --- | --- |
| ASK | Chat, no persist of inferences | “just answer” |
| DO | AgentTask + approvals | “do this” / “work until finished” |
| RESEARCH | Research engine | “deep research” / Knowledge Briefs Run |
| MONITOR | Scheduler + cheap local model | “watch until / notify me” |

User override always wins. Never silently promote ASK → DO.

---

## Self-Improvement

Copy **Guided Repair + self_upgrade** exactly:

Detect recurring failure → analyze → propose skill/patch → isolated test (`tmp` data dir) → show evidence → Jeff approves → apply → verify → rollback.

**No silent self-modification.** Constitution Principle 5 (Integrity) and 4 (Repair→Verify).

---

## Testing / Evaluation

Keep pytest `tmp_path` + `live_data_guard`.

**Harden so 2026 contamination cannot recur:**

1. `JARVIS_ENVIRONMENT=production` on systemd unit; cert/QA runners **must** set `test` and a throwaway `JARVIS_DATA_DIR`.
2. Guard Memgraph: tests already `delenv JARVIS_GRAPH_BACKEND`; production cert must use ephemeral graph or sqlite in tmp.
3. Refuse `/api/certification/fixtures/*` when environment is production (403 already exists for some QA headers — extend).
4. Provenance: writes without `kind` fail closed in production.
5. New evals (isolated): task completion, citation accuracy, provenance, tool/model selection, delegation, recovery, checkpoint, injection, contradiction, UI empty-state honesty, **live path never opened**.

CI must not start `jarvis.service` against `data/`.

---

## Local-First Strategy

| Class | Policy |
| --- | --- |
| local only | PHR, vault, journal, default ASK |
| cloud allowed | research/coding if Jeff enabled provider in vault |
| cloud required | never a default |
| ask before cloud | first cloud call per session/task |
| sensitive blocked | Health, vault secrets, `jarvis.env` values never in prompts to cloud |

UI must show **where this inference ran** (local model vs provider). Providers room already exists.

---

## Competitive Matrix

| Capability | ARIA now | ARIA proposed | Hermes | OpenAI/Codex | Gemini | Perplexity |
| --- | --- | --- | --- | --- | --- | --- |
| Personal life OS (rooms) | Strong | Keep | Weak | Weak | Weak | Weak |
| Local models | Strong | Stronger routing | Strong | Weak | Weak | Weak |
| Owner vault / one password | Strong | Keep | Weak | Weak | Weak | Weak |
| Persistent agent loop | Weak | Strong (extend jobs) | Strong | Strong | Strong (research/CU) | Strong (Computer) |
| Deep research | Weak | Strong (local+web) | Medium | Medium | Strong | Strong |
| Computer use | Medium (browser) | Medium+ | Medium | Medium | Strong | Medium |
| Skills from experience | Weak | Approval-only | Strong | Weak | Weak | Medium |
| MCP | Dev-only | Owner client | Strong | Strong | Strong | Medium |
| Provenance / anti-contam | Weak | Strong | Weak | Weak | Weak | Weak |
| Subagents | Medium (API) | Strong | Strong | Strong | Medium | Medium |
| Messenger gateways | N/A | Don’t chase | Strong | Weak | Weak | Weak |
| Overnight unattended | Partial (systemd+cron) | Strong | Strong | Strong | Max research | SPACE |

### ARIA ADVANTAGES

Local-first house; ACM; Health/Journal/HA; Owner Vault; Integrity; 34 rooms; huge local model shelf; Guided Repair as approval culture.

### ARIA GAPS

Persistent runtime; deep research; provenance; computer-use safety; owner MCP; skill lifecycle; restart-resume.

### ARIA OPPORTUNITIES

Hermes-style loop **plus** Aria organs **plus** provenance **plus** local models — a personal worker no cloud OS can be, because it actually lives in Jeff’s files and house.

### DON’T CHASE

Telegram/Discord as primary UI; Perplexity thousand-way Search-as-Code; plugin marketplace; medical imaging models; desktop computer-use in Phase 1; replacing ACM; replacing rooms with a “chat-only agent”; silent self-modifying skills; running cert against live `data/`.

---

## Prioritized Roadmap

| ID | Work | Pri | Value | Complexity | Risk | Depends | Reuse | User benefit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0-1 | Map ACM provenance onto room writers + About-you filter (extend `ProvenanceRecord`, add TEST_DATA/environment) | P0 | High | Medium | Low | ACM provenance module | `aria_acm/acm/provenance/` | Trust |
| P0-2 | Production env lock remaining holes (cert, Memgraph, MCP-to-live); keep existing middleware | P0 | Transformational | Medium | Low | `production_guard`, live_data_guard | Integrity, conftest | Never repeat contamination |
| P0-3 | AgentTask store + unify jobs/tasks/checkpointed (make specialist jobs actually resumable) | P0 | Transformational | High | Medium | coding_jobs, coding_tasks, jobs/checkpointed, jobs_center | those modules | “Work until finished” |
| P0-4 | Attach overnight loop to systemd serve (automation engine *or* start proactive_scheduler from lifespan — pick one) | P0 | High | Low | Low | automation/engine, proactive_scheduler | those modules | Briefing/research/integrity actually run |
| P1-1 | Runtime loop (plan/execute/evaluate) on AgentTask | P1 | Transformational | High | Medium | P0-3, reasoning, specialists | intelligence/*, specialists | Real worker |
| P1-2 | Restart resume + budgets + watchdog | P1 | High | Medium | Medium | P1-1, systemd, Mission Control | MC, Guided Repair | Overnight |
| P1-3 | ASK/DO/RESEARCH/MONITOR in orchestration_policy | P1 | High | Low | Low | P1-1 | orchestration_policy | Predictable |
| P2-1 | Evidence types + claim objects | P1 | High | Medium | Low | P0-1 | ACM, documents | Why do we believe this? |
| P2-2 | Deep Research engine | P2 | High | High | Medium | P2-1, web_search, RAG, browser | knowledge_research_daily | Real investigation |
| P2-3 | Promote specialists to default DO path | P2 | High | Medium | Medium | P1-1 | specialists.engine | Delegation |
| P3-1 | Browser safety (intent, confirm, injection) | P2 | Medium | Medium | High | browser_agent | browser_product | Safer web work |
| P3-2 | MCP client in Integrations | P2 | Medium | Medium | Medium | permissions | plugin_sdk, connectors | Extensibility |
| P3-3 | Skills lifecycle (version/test/disable/propose) | P2 | High | Medium | Medium | Guided Repair, plugin_sdk | cheatsheets, DAGs | Reuse |
| P4-1 | Model router privacy class | P2 | Medium | Low | Low | execution_policy | Providers room | Right model |
| P4-2 | Observability traces + Approvals surface | P2 | High | Medium | Low | Action History, Jobs | existing UI | See work |
| P4-3 | Snapshot/rollback for AgentTask working set | P3 | High | High | High | P1-1 | proposal undo | Safety |
| P5-1 | Controlled self-improvement (skill proposals) | P3 | Medium | High | High | P3-3, P0-2 | self_upgrade, Guided Repair | Gets better |
| — | Desktop computer-use | P3 | Low | Extreme | High | P3-1 | — | Don’t chase yet |
| — | Messenger gateways | P3 | Low | Medium | Medium | — | — | Don’t chase |

---

## Dependencies

```text
P0-2 isolation ─┐
P0-1 ACM provenance map ─┼→ P0-3 AgentTask → P1-1 Runtime → P1-2 resume
P0-4 systemd overnight ─┘                      ├→ P1-3 modes
                                               ├→ P2-3 specialists on DO
                 └→ P2-1 evidence → P2-2 research
Browser/MCP/Skills after Runtime (need permission + task id)
Observability anytime after AgentTask exists
Self-improvement last (requires isolation + skills + repair)
```

**Phase order vs the original 13-phase list:** Evidence (originally phase 5) **moves before** Deep Research. Isolation is **phase 0**, not an afterthought. Subagents **follow** Runtime (they already exist as an API). Browser/MCP/Skills after permissions. Command Center UI after traces exist (otherwise empty chrome).

---

## Risks

| Risk | Mitigation |
| --- | --- |
| Second brain beside ACM | ACM remains SoT; AgentTask is operational only |
| Autonomous writers contaminate `data/` | P0-2 + provenance fail-closed |
| Runtime rewrite of Chat | Chat stays ASK; DO is opt-in |
| VRAM thrash from overnight 32B | Budgets; MONITOR uses small local model |
| MCP supply-chain | Owner enablement; no auto-trust |
| Scope explosion | Capability-Driven Development: only Jeff friction |
| Next-Gen Charter vs this doc | Rooms/Activities remain; this adds worker organs under the same workspace |

---

## Recommended Implementation Sequence

1. **P0 isolation remaining holes + ACM provenance mapping** (trust; contamination cannot return).  
2. **Attach the overnight loop to systemd serve** (one scheduler).  
3. **AgentTask + job unification** (one ID, persist, cancel; specialist jobs become resumable).  
4. **Runtime loop on DO tasks** using specialists + handlers.  
5. **Resume after systemd restart** + budgets.  
6. **Intent modes** in the existing router (`orchestration_policy` already live).  
7. **Evidence/claims** then **Deep Research**.  
8. **Browser safety**, **MCP client**, **Skills proposals**.  
9. **Routing + traces + Approvals UI**.  
10. **Task-scoped rollback**.  
11. **Self-improvement** only after the above are boringly reliable.

Do **not** spend a phase wiring `local_router.try_local_route` unless a measured gap remains after NLU + `route_with_tools`. Do **not** replace ACM provenance.

---

## Future-State Definition of Done

Jeff can say: “Work on this until it is finished,” close the UI, and find a verified result (or a blocked approval) after hours or a reboot.

Jeff can say: “Deep research X,” and get a cited report that does **not** silently become profile memory.

Jeff can ask: “Why do you believe this?” and see claim → evidence → source → span → time → verification.

No test, cert, or agent run can write live PHR/Journal/Vault/`data/` unless `JARVIS_ENVIRONMENT` and provenance allow it.

Rooms still work as rooms. One Master Password. ACM still the brain. Integrity still never auto-deletes.

---

## Appendix: Existing ARIA Components That Can Be Reused

| Component | Path | Role in future |
| --- | --- | --- |
| Action registry | `jarvis/handlers/registry.py` | Executor |
| Router / NLU / orchestration | `jarvis/router.py`, `nlu/`, `orchestration_policy.py` | Intent |
| Coding jobs | `jarvis/coding_jobs.py` | Worker pool |
| Coding tasks | `jarvis/coding_tasks.py` | Checkpoint/pause prototype |
| Jobs Center | `jarvis/jobs_center.py` | TASKS surface |
| Background actions | `jarvis/background_jobs.py` | Queue adapter |
| Specialists | `jarvis/specialists/*` | Subagents |
| Reasoning | `jarvis/intelligence/reasoning.py` | Planner seed |
| Workflow DAG | `jarvis/intelligence/workflow_engine.py` | Multi-step procedures |
| Automation engine | `jarvis/automation/engine.py` (not the deprecated intelligence re-export) | MONITOR/cron on **systemd serve** |
| Proactive scheduler | `jarvis/proactive_scheduler.py` | Briefing/integrity/health/flytying — **only if attached to serve** |
| Checkpointed specialist jobs | `jarvis/jobs/checkpointed.py` | Must become actually resumable |
| ACM provenance | `aria_acm/acm/provenance/` | Truth layer (extend, don’t replace) |
| ACM teaching | `aria_acm/acm/authority/teaching.py` | User-stated knowledge |
| Research verification | `jarvis/research_verification.py`, `research_context.py` | Research evaluate/verify seed |
| Search product | `jarvis/search_product/` | Federated retrieval |
| Browser research APIs | `jarvis/browser_product/` plan/tab/merge | Deep research browse |
| Production guard | `jarvis/production_guard.py` | Isolation (already on serve) |
| Owner capabilities | `jarvis/security/owner/capabilities.py` | Permission matrix seed |
| Hybrid RAG | `jarvis/intelligence/hybrid_rag.py` | Research read |
| Knowledge research | `jarvis/knowledge_research_daily.py`, `knowledge/topics.py` | Research seed |
| Web search | `jarvis/web_search.py` | Search |
| Browser agent | `jarvis/browser_agent.py` + `browser_product/session.py` | Computer-use (web) |
| Execution policy | `jarvis/inference/execution_policy.py` + `capability_routing.py` + `model_store.py` | Model router |
| Plugin SDK | `jarvis/intelligence/plugin_sdk.py` | Skills/tools (sandbox is a stub — don’t trust it) |
| Connectors | `jarvis/intelligence/connectors.py` | APIs |
| Graph | `jarvis/modules/graph_store.py` | Connections mirror |
| ACM | `aria_core` / `data/acm/cognitive.db` | Memory SoT |
| Profile | `jarvis/profile_questionnaire.py` | User facts |
| Owner vault | `jarvis/security/owner/` | Auth/secrets |
| Guided Repair | `jarvis/repair_product/` | Approvals + verify + rollback culture |
| Production Integrity | `jarvis/integrity_product/` | Contamination scans |
| live_data_guard | `jarvis/live_data_guard.py` | Test isolation |
| Self-upgrade | `jarvis/self_upgrade.py` | Approved self-change |
| MCP (Cursor) | `scripts/jarvis-mcp-server.py` | Dev tool (keep scoped) |
| Workspace registry | `gui/static/workspace/registry.js` | Rooms + Activities |
| systemd unit | `jarvis.service` | Process durability |

### Do not rewrite

Living Workspace rooms, Owner Vault, ACM authority **and ACM provenance module**, Health PHR, Journal product, Fly Tying product, Production Integrity (never auto-delete), Guided Repair approval law, pytest tmp isolation (extend it), systemd launch path, chat ASK path, `orchestration_policy`, coding propose→apply, Connections review-then-approve ingest, Documents-learn-as-candidates.

### Impossible / incomplete to assess without further residency

- Real browser-agent success rate on Jeff’s sites (Playwright stack-gated; not re-run this pass).  
- FunctionGemma router quality vs NLU + `route_with_tools` in production chat.  
- Next-Gen desktop runtime (Phase 1 spikes) vs HTML workspace — charter says runtime not selected until evidence; this roadmap assumes HTML workspace remains until that evidence exists.  
- Whether Memgraph is running in this house (code path exists; **default backend is SQLite**).  
- How often Jeff uses the tray (if never, proactive_scheduler work currently does not run).

Resolved by second-pass audit: specialist `run_team` **is** on the router cascade (not only a hidden API); default ASK still does not always delegate. `local_router` is confirmed unused on `router.route()`.

---

*Planning document only. No implementation implied.*
