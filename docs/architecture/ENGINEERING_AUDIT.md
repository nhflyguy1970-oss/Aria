# Aria Engineering Audit

**Date:** 2026-07-31  
**Role:** Principal Software Architect  
**Mode:** Research only — no implementation recommendations executed  
**Companions:** [ARCHITECTURE_REVIEW.md](./ARCHITECTURE_REVIEW.md) · [ARCHITECTURE_BIBLE.md](./ARCHITECTURE_BIBLE.md) · [ENGINEERING_ROADMAP.md](./ENGINEERING_ROADMAP.md)

Independent verification was performed against the live tree. Prior certification docs were **not** trusted at face value.

---

## 1. Verdict

Aria is a capable local AI workstation with several islands of excellent engineering (ACM write path, media output verification, gallery consistency, automation result semantics, LAN bind fail-closed). It is **not** release-clean as a coherent product architecture.

The dominant failure mode is **false success**: HTTP 200 / toast / `ok: True` / green cert badges without verified outcomes. The second is **split ownership**: sync≠stream, activity×3, calendar events×2, settings mirrors, dual automation rules files.

**Ship stance (engineering, not product marketing):** Do not treat top-level `ARIA_*CERTIFICATION*.md` greens as authority. Use this audit + Bible + evidence artifacts.

---

## 2. Architectural strengths

| # | Strength | Evidence |
|---|----------|----------|
| S1 | ACM permanent cognitive SoT; fail-closed writes | `modules/memory*.py` raise on redirect failure; M3/M4 tests |
| S2 | Checkpoint write/read SoT aligned (R1) | `latest_checkpoint` divert; `tests/test_checkpoint_r1.py`; evidence JSON |
| S3 | Media queue refuses Complete without on-disk artifact | `media_jobs.py` missing-path check |
| S4 | Gallery soft-delete scrubs/restores chat embeds | `gallery_product/consistency.py` |
| S5 | Automation skipped ≠ success | `automation/execution.py` normalize_result |
| S6 | Dashboard honest unavailable widgets | `dashboard_product/aggregate.py` `_safe` + coach |
| S7 | LAN bind SystemExit without API key | `lan.require_api_key_for_lan_bind` |
| S8 | Path confinement + URL SSRF (DNS re-resolve) | `security/path_confine.py`, `url_guard.py` |
| S9 | Auth key exemption = loopback only | `auth.is_loopback_client` / `api_key_required_for` — **verified** |
| S10 | Product registration ledger on `/api/health` | `product_registration.py` |
| S11 | Vision attaches honesty report on failure | `vision_product/engine.py` |
| S12 | Inbound automation webhook rejects query secrets | `extra_routes` automation inbound |
| S13 | Activity inbox atomic tmp+replace | `activity_inbox._write_all` |
| S14 | Batch0 architecture inventories exist | `docs/architecture/batch0/*` |

---

## 3. Architectural weaknesses

### 3.1 Critical

| ID | Weakness | Evidence |
|----|----------|----------|
| W1 | Sync vs stream pipelines divergent | Stream omits `dispatch_action`/`decorate_result`; re-routes message |
| W2 | Production NLU classifier 0% intent accuracy | `data/nlu_placement.json` all `intent_accuracy: 0.0` |
| W3 | Memory reads fail-open to legacy vault | `list_entries`/`get`/`search`/`similar_exists` bare `except` |
| W4 | Frontend success theater | `ariaMutate` defined, **zero product callers**; ~476 mutating fetches |
| W5 | Shutdown can silently lose last turn / ACM delta | `server.py` lifespan `except: pass` around persist+checkpoint and flush |
| W6 | Daemon constructs second `JarvisAssistant` | `get_assistant()` fallback in resume_incomplete_jobs / wake / scheduler |
| W7 | ACM auto_persist full-store snapshot per encode | `aria_acm` `flush(kind="encode")`; ~225 MB live; ~27 GB archives |
| W8 | Activity not actually server-authoritative for bulk ops | `markAllRead`/`clearRead`/`clearAll` local only |

### 3.2 High

| ID | Weakness | Evidence |
|----|----------|----------|
| W9 | Three unsynchronized action catalogs | registry · `router.ACTIONS` · capability map |
| W10 | `_quick_route` ~950 LOC sequential regex | `router.py` |
| W11 | Stream bypasses inference gateway | `llm.ask_stream` → ollama directly |
| W12 | Benchmark overlay applied twice (sync) | capability_routing + gateway |
| W13 | Coding undo RAM-only; apply ok with verify fail text | `last_apply_backups`; `apply_proposal` |
| W14 | Calendar dual event ownership | planner.db events vs journal bullets |
| W15 | Search `ok: True` on total federation failure | `pipeline.run_search` |
| W16 | Registration fail-loud only for 5/23 products | `required=True` only on media quintet |
| W17 | CI covers 84/309 tests; current gates red (ruff/format) | `ci_check.py` · local run |
| W18 | Certification stale READY_TO_SHIP artifact | run without image_lifecycle still in history |
| W19 | Journal corrupt → empty → wipe on save | `journal._load` |
| W20 | `code_index.json` ~90 MB sync linear scan on chat path | `code_index.py` |

### 3.3 Medium

| ID | Weakness |
|----|----------|
| W21 | Voice/settings triple-store mirror |
| W22 | Notifications ↔ Settings circular mirror |
| W23 | Automation dual-write rules + engine in wrong package |
| W24 | Flytying product routes registered twice |
| W25 | Git extension `register_api` missing → dead routes |
| W26 | Home Assistant product registration bypasses ledger (`except: pass`) |
| W27 | Tag-only memory update no-op under PRIMARY (Batch D R2) |
| W28 | Memory Home `acm_metrics` ImportError → unknown SoT |
| W29 | Provider health shows 5 stub providers |
| W30 | PinLock prefix exempts `/api/health/full` |
| W31 | Global exception handler leaks paths; does not log |
| W32 | Layout state in three places (layouts, dashboard, ui_prefs) |
| W33 | Desktop notify-send bypasses DND/quiet hours |
| W34 | Relationship triples dual-written ACM + graph DB |
| W35 | Docs certification pile mutually contradictory |

---

## 4. Duplicate ownership

| Concern | Owners | Risk |
|---------|--------|------|
| Turn dispatch | `conversation_pipeline` (sync) vs inline stream | Behavior drift |
| Action catalog | registry / router.ACTIONS / capability map | LLM router lies |
| Chat messages vs session meta | branches.json / chat_sessions.db | Orphans |
| Cognitive memory vs vault | ACM / memory.db / memory.json | Split-brain reads |
| Calendar events | planner.db / journal | Duplicates |
| Activity | inbox.jsonl / notifications history / localStorage | Divergent UI |
| Voice settings | 3 JSON files | Last-write-wins |
| Notification prefs | settings_product ↔ notifications_product | Circular |
| Automation rules | automation_product/rules.json + user_automations.json | Dual-write |
| Gallery delete | product soft-delete vs legacy DELETE | Missing activity |
| Visibility/restriction | gallery vs video_generation | Drift |
| Design tokens | shell/design_tokens.py vs style.css | Dual SoT |
| Layout/density | layouts / dashboard / ui_prefs | Triple |
| Mission Control | aiplatform aggregator vs mission_control_ops | Import fragility |
| Model selection | model_store / model_policy / execution_policy / llm stream | Wrong model silent |

---

## 5. Dead code (representative)

| Item | Why dead / unreachable |
|------|------------------------|
| `memory_adapter_store` DualWrite ~300 LOC | wrap is identity under ACM |
| `intelligence/memory_platform` search/import/export | Calls nonexistent module APIs |
| `mission_control_panel` legacy branch | Unreachable under PRIMARY |
| Stream `instant` set | Unreachable boolean short-circuit |
| `_stream_lite_ui` | Assigned, never read |
| `extensions/journal/api.py` | Stub `del app, assistant` |
| `extensions/git/api.py` | No `register_api` on extension |
| Search bridge shims (5 files) | Unimported |
| Browser download safety | `accept_downloads=False` |
| `server_shutdown.py` / `gaming_shutdown.py` | Zero callers |
| Duplicate `gesture_settings.py` ×2 | Unimported |
| Six `register_routes` aliases | No callers |
| `jarvis/error_handling.py` | Unused in production |
| Voice extension chat-session routes | Wrong owner (alive but misplaced) |

---

## 6. Hidden coupling

1. **Project slug ambient global** — 18 modules call `get_active_slug()`; media metadata stamped four times with copy-paste.
2. **Route registration order** — extensions → extra_routes → server.py; Gallery comment is the only enforcement; Mission Control latency survives by accident.
3. **Context prefix in user turns** — couples retrieval to history storage forever.
4. **Cap Bus / ACM engine.context** — shared mutable context; lock not held on all reads.
5. **Platform attach env vars** — per-process; daemon validates different process than serve.
6. **Frontend load order** — `aria_mutate.js` near end; globals last-writer-wins (`escapeHtml` ×8, `activeBranchId` ×9).
7. **certification writes appearance settings** — cross-product store mutation.
8. **Calendar month view** — triggers journal enrich paths that can write disk.

---

## 7. God modules

| Module | LOC | Absorbs |
|--------|----:|---------|
| `gui/server.py` | ~3953 | Device/ops routes + assistant construct |
| `gui/extra_routes.py` | ~2747 | Content routes + product registrar |
| `router.py` | ~2267 | Entire intent cascade + `_quick_route` |
| `assistant.py` | ~2041 | Orchestration + proposals + status + coding helpers |
| `aria_acm/.../engine.py` | ~2431 | Cognition API surface |
| `modules/journal.py` | ~1524 | Entire BuJo + CLI |
| `behaviors/engineering/_extracted.py` | ~1350 | Coding agent |
| `acm_bridge.py` | ~1296 | All ACM translation |
| `search_product/retrievers.py` | ~1049 | All corpora |
| `modules/audio.py` | ~969 | Record/STT/TTS/edit/song |
| `behaviors/memory/engine.py` | ~1012 | Memory chat surface |
| `platform_cutover.py` | ~878 | Dead-by-default cutover theater |
| `index.html` / `style.css` | ~3450 / ~6911 | Entire UI shell |

---

## 8. Performance risks

| Risk | Mechanism |
|------|-----------|
| ACM encode latency/disk | Full-store JSON snapshot every encode |
| Chat turn I/O | Double full rewrite of `chat_branches.json` |
| NLU hot path | 14B classifier ~730 ms warm; can thrash VRAM |
| Code search | 90 MB index in heap; O(n) cosine; sync on request path |
| Search federation | Unbounded chat_branches parse; project rglob |
| `project_list_entries` | Full experience scan; called repeatedly for stats |
| Litellm health | Uncached 2s probe inside `select_route` |
| Activity inbox | Full rewrite of ≤500 rows per event |
| Journal save | Deepcopy + full rewrite + history append |
| Logs | `data/logs` ~13 GB, no rotation |
| Mission Control collect | Multi-second blocking on request thread |

---

## 9. Reliability risks

| Risk | Impact |
|------|--------|
| Shutdown `except: pass` | Lost last messages / checkpoint / ACM delta |
| SIGKILL after 8s | Lifespan teardown skipped |
| Second assistant in daemon | Divergent branches/memory |
| Memory read fail-open | Stale vault answers while ACM is SoT |
| Journal corruption | Silent wipe |
| Media persist non-atomic | Watchdog may restart through GPU work |
| Coding hang | Worker timeout checked after `fn()` returns; pool size 1 |
| Checkpointed "resume" | Full re-execution, not mid-step |
| Audio/comfyui jobs | RAM-only — disappear on restart |
| Stream double-route | Clarification state can change action between routes |

---

## 10. UX risks

| Risk | Impact |
|------|--------|
| Toast without verify | User believes save/apply/delete worked |
| Search empty vs failed | Indistinguishable |
| Apply proposal "success" with failing tests | Broken code marked applied |
| Undo unavailable after restart | Irreversible applies |
| Browser system-fallback "navigated" | Agent continues with no page |
| Vision non-ERROR refusals | Confident wrong answers |
| Memory Home SoT "unknown" | UI lies about ACM |
| Cert green stale READY | Operator ships on old gate |
| Activity pin/mute per-browser | Preferences don't sync |
| Voice settings three-way | Settings flip-flop |

---

## 11. Maintainability risks

| Risk | Impact |
|------|--------|
| 129 IIFE globals | Any reorder breaks behavior |
| Manual `?v=` cache bust | Guaranteed stale clients |
| Product template 8-file spam | Dead experimental modules |
| Dual Json/Sqlite MemoryStore copies | ACM contract changes ×2 |
| Conflicting certification docs | Operators pick the green one |
| Source-grep "tests" | Pass while runtime broken |
| `*_product` naming ≠ has router | Registration audits manual |
| Seven job queues, four lifecycles | No unified drain/shutdown |

---

## 12. Prior claim verification (summary)

| Claim | Verdict |
|-------|---------|
| Registration fail-loud; 21 OK / 0 failed | **PARTIAL** |
| Cert skip_image → not READY_TO_SHIP | **VERIFIED** (code); stale artifact remains |
| Clear/verify fail-closed | **PARTIAL** |
| Activity server-authoritative | **PARTIAL / FALSE** for bulk |
| Conversation pipeline unified | **FALSE** |
| Auth exemption loopback-only | **VERIFIED** |

---

## 13. What this audit does **not** do

- Does not implement fixes.
- Does not redesign ACM.
- Does not propose a second memory platform.
- Does not declare READY_TO_SHIP or DO_NOT_SHIP as a product decision — it states engineering facts for that decision.

See [ENGINEERING_ROADMAP.md](./ENGINEERING_ROADMAP.md) for prioritized improvements with acceptance criteria. **Implementation requires explicit approval.**
