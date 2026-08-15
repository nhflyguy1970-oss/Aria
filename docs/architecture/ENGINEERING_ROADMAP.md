# Aria Engineering Roadmap

**Date:** 2026-07-31  
**Status:** Recommendations only — **implementation NOT approved**  
**Authority:** Principal Software Architect  
**Companions:** [ARCHITECTURE_REVIEW.md](./ARCHITECTURE_REVIEW.md) · [ARCHITECTURE_BIBLE.md](./ARCHITECTURE_BIBLE.md) · [ENGINEERING_AUDIT.md](./ENGINEERING_AUDIT.md)

### Rules for using this roadmap

1. Do not start work without explicit approval of a named item (or priority band).
2. Prefer one item at a time with evidence.
3. ACM is permanent — memory items strengthen ACM / remove legacy ownership around it. **Never replace ACM.**
4. Do not invent new façades, flags, or platforms.
5. Acceptance criteria are mandatory; “looks fine” is not acceptance.

---

## Critical

### C1 — Unify sync and stream conversation pipelines

| Field | Content |
|-------|---------|
| **Root cause** | Stream path never adopted `dispatch_action` / `decorate_result`; re-enters `_process_unlocked` and routes twice |
| **Why it matters** | Divergent behavior, missing action logs/trust updates, double NLU cost, clarification races |
| **Expected outcome** | One dispatch + decorate path; stream is an adapter over the same cascade |
| **Acceptance** | Stream calls shared dispatch/decorate; no second `route()` for non-chat; action log + trust updated on streamed turns; tests for chat + one queued action + one instant action on both paths |
| **Risks** | SSE event shape regressions; coding stream special-cases |
| **Files** | `jarvis/assistant.py`, `jarvis/conversation_pipeline.py`, `behaviors/conversation.py`, `behaviors/engineering/*`, tests for stream |

### C2 — Fix or demote production NLU classifier

| Field | Content |
|-------|---------|
| **Root cause** | Placement selected by latency with 0% measured intent accuracy; still gates at 0.95/0.70 |
| **Why it matters** | Misroutes, VRAM thrash from 14B classifier, false clarifications |
| **Expected outcome** | Classifier either proves ≥ threshold accuracy on a frozen eval set **or** is disabled/bypassed until it does; placement cannot win on latency alone |
| **Acceptance** | Documented accuracy gate in placement; `data/nlu_placement.json` cannot list winner with 0% accuracy; routing regression tests green for runtime introspection cases |
| **Risks** | Temporary reliance on regex/`_quick_route`; latency change |
| **Files** | `jarvis/nlu/{placement,benchmark,pipeline,confidence,mapping}.py`, `data/nlu_placement.json`, routing tests |

### C3 — Memory read fail-closed (or explicit counted fallback)

| Field | Content |
|-------|---------|
| **Root cause** | Host adapters swallow ACM exceptions and serve legacy vault |
| **Why it matters** | Silent split-brain; stale answers; unobservable drift |
| **Expected outcome** | Under PRIMARY, ACM read errors surface as errors (or single intentional fallback that increments `legacy_fallback_reads` and never silently mixes) |
| **Acceptance** | Injected ACM failure in list/get/search does not return legacy poison; metrics/log prove path; tests added; ACM itself unchanged in organ design |
| **Risks** | Stricter failures in UI if ACM briefly down |
| **Files** | `jarvis/modules/memory.py`, `memory_sqlite.py`, optionally `acm_store_facade.py`; tests |

### C4 — Frontend: verify-before-toast (`ariaMutate` adoption)

| Field | Content |
|-------|---------|
| **Root cause** | Helper exists; zero product callers; 476 mutating fetches toast on HTTP 200 |
| **Why it matters** | Users believe failed mutations succeeded |
| **Expected outcome** | All high-risk mutations (memory, gallery, planner, settings, coding apply, activity) use verify-before-toast |
| **Acceptance** | `ariaMutate` loaded before consumers; ≥ N critical call sites migrated; grep shows declining bare success toasts; no toast when `data.ok === false` |
| **Risks** | UX churn; some APIs lack `ok` field |
| **Files** | `gui/static/aria_mutate.js`, `index.html` order, product JS (gallery, planner, memory_browser, calendar, coding_home, …) |

### C5 — Shutdown durability

| Field | Content |
|-------|---------|
| **Root cause** | Shared `except: pass`; checkpoint skipped if persist fails; ACM flush swallowed; 8s SIGKILL |
| **Why it matters** | Lost last conversation turn and cognitive delta |
| **Expected outcome** | Ordered shutdown: persist → checkpoint → ACM flush → job drain signal; each step logged; failures visible |
| **Acceptance** | Kill -TERM with open chat leaves messages on disk; ACM flush error logged; separate try blocks; no silent pass |
| **Risks** | Longer shutdown; watchdog timing |
| **Files** | `jarvis/gui/server.py` lifespan, `daemon.stop_server`, media/coding drain hooks |

### C6 — Single assistant process ownership

| Field | Content |
|-------|---------|
| **Root cause** | `get_assistant()` constructs standalone instance in daemon/MCP/scheduler |
| **Why it matters** | Divergent branches/memory; corrupt writes |
| **Expected outcome** | Daemon never constructs full assistant for resume; resume via HTTP/API to serve process or shared IPC; MCP fails if serve not registered |
| **Acceptance** | No second BranchManager write from daemon; warning becomes hard error in production config; test/docs |
| **Risks** | Job resume redesign |
| **Files** | `assistant_instance.py`, `daemon.py`, `jobs/checkpointed.py`, `jarvis_mcp.py`, proactive_scheduler |

---

## High

### H1 — ACM persist amplification

| Field | Content |
|-------|---------|
| **Root cause** | `auto_persist` flushes full-store snapshot every encode |
| **Why it matters** | Disk/latency; 27 GB archives |
| **Expected outcome** | Incremental or amortized persist **without** redesigning cognition organs; document tradeoffs |
| **Acceptance** | Encode path does not insert full export every time (or rate-limited with crash-safe bound); size/latency evidence |
| **Risks** | Durability window; touches `aria_acm` persistence — requires explicit ACM-touch approval |
| **Files** | `aria_acm/acm/persistence/sqlite.py`, `api/engine.py`, `aria_core/acm_bridge.py` |

### H2 — Collapse action catalogs to registry

| Field | Content |
|-------|---------|
| **Root cause** | LLM router prose list drifts from `handlers/registry` |
| **Why it matters** | Routes to nonexistent actions |
| **Expected outcome** | `router.ACTIONS` generated from registry; capability map derived or checked in CI |
| **Acceptance** | CI fails if ACTIONS ⊈ registered actions; no hand list |
| **Files** | `handlers/registry.py`, `router.py`, `capability_routing.py`, `scripts/ci_check.py` |

### H3 — Stream uses inference gateway

| Field | Content |
|-------|---------|
| **Root cause** | `llm.ask_stream` bypasses gateway policy/trace |
| **Why it matters** | Silent model substitution; missing observability |
| **Expected outcome** | Stream and sync share gateway |
| **Acceptance** | Gateway trace on streamed chat; same model as `resolve_conversation_model` unless documented override |
| **Files** | `jarvis/llm.py`, `inference/gateway.py`, `behaviors/conversation.py` |

### H4 — Coding apply/undo durability

| Field | Content |
|-------|---------|
| **Root cause** | Undo pointer RAM-only; verify failures don't flip `ok` |
| **Why it matters** | Irreversible broken applies |
| **Expected outcome** | Durable undo journal; `ok` reflects verify; multi-file apply rolls back or stays pending |
| **Acceptance** | Restart after apply → undo still works; failing pytest ⇒ `ok: false` or explicit `applied_with_failures` |
| **Files** | `assistant.py`, `coding_product/*`, `coding_verify.py`, `proposal_store.py` |

### H5 — Activity single SoT completion

| Field | Content |
|-------|---------|
| **Root cause** | Three stores; bulk mutations local-only |
| **Why it matters** | Divergent activity across devices/reloads |
| **Expected outcome** | All mutations hit `activity_inbox`; localStorage cache only; notifications drain into inbox without browser echo requirement |
| **Acceptance** | markAllRead/clear* have APIs; offline cache labeled; no browser-required path for server events |
| **Files** | `activity_inbox.py`, `activity_api.py`, `activity_store.js`, `notifications_product/*` |

### H6 — Calendar single write owner for events

| Field | Content |
|-------|---------|
| **Root cause** | Planner events vs journal bullets both create “calendar items” |
| **Why it matters** | Duplicates; unclear edits |
| **Expected outcome** | One write SoT for user events; other is projection or migration |
| **Acceptance** | Creating an event writes one store; calendar read shows one; docs match |
| **Files** | `calendar_schedule.py`, `calendar_api.py`, `planner_store.py`, journal promotion paths |

### H7 — Search honest federation

| Field | Content |
|-------|---------|
| **Root cause** | `ok: True` always; default everything skips corpora; `_safe` hides failures |
| **Why it matters** | Empty results look like “no data” |
| **Expected outcome** | Partial/failed corpora in response; default corpora match FACETS; health reflects local corpora |
| **Acceptance** | All-fail ⇒ `ok: false` or `degraded: true` with failures[]; UI shows warnings |
| **Files** | `search_product/{pipeline,retrievers,intent,diagnostics,terminology}.py` |

### H8 — Product registration default strictness

| Field | Content |
|-------|---------|
| **Root cause** | Only 5/23 required; HA/flytying bypass ledger |
| **Why it matters** | Health green while routes missing |
| **Expected outcome** | Required set expanded; all products through ledger; extensions failures visible on health |
| **Acceptance** | Broken search/settings/cert registration fails boot or marks health not ok |
| **Files** | `product_registration.py`, `extra_routes.py`, `extensions/*/extension.py`, `loader.py` |

### H9 — CI truthfulness

| Field | Content |
|-------|---------|
| **Root cause** | 224 tests outside CI; ruff/format red; import-time assistant breaks app tests |
| **Why it matters** | False confidence |
| **Expected outcome** | Green `ci_check.py all`; new architecture/cert/memory tests in PYTEST_PATHS; server import testable |
| **Acceptance** | CI green on main; assistant not constructed at import (lazy) **or** tests don't import server module body |
| **Files** | `scripts/ci_check.py`, `gui/server.py`, tests/*, ruff |

### H10 — Certification artifact hygiene

| Field | Content |
|-------|---------|
| **Root cause** | Stale READY_TO_SHIP; fabricated screenshots; package historically untracked |
| **Why it matters** | Operators ship on lies |
| **Expected outcome** | Invalidate superseded runs; real screenshots or no credit; cert tests in CI |
| **Acceptance** | History cannot show READY without image_lifecycle evidence files; `test_certification_product` in CI |
| **Files** | `certification_product/*`, `certification_home.js`, `data/certification/`, tests |

---

## Medium

### M1 — Batch D R2: hierarchy tags-only update under PRIMARY
Aligns with approved memory plan. Fix `acm_update`/hierarchy so tags persist. **Files:** `acm_store_facade.py`, `memory/hierarchy.py`, `memory_manager.py`. ACM organs untouched if possible.

### M2 — Batch D R3–R4: delete DualWrite theater + honest cutover
Remove dead adapter; update supremacy CI; cutover UI says ACM authoritative. **Files:** `memory_adapter_store.py`, `platform_cutover.py`, docs.

### M3 — Fix Memory Home `acm_metrics` ImportError
**Files:** `memory_services.py`, `acm_bridge.py` (export or stop importing).

### M4 — Journal load fail-closed / quarantine
Corrupt JSON → quarantine file, don't overwrite with empty. **Files:** `modules/journal.py`.

### M5 — Code index off request path
Async/ANN or size cap; never `build_index` inside search GET. **Files:** `code_index.py`, `code_context.py`.

### M6 — Voice settings single SoT
One file; migrate mirrors. **Files:** `voice_product/settings.py`, legacy JSON.

### M7 — Notifications ↔ Settings one direction
Single owner for mirrored flags. **Files:** `settings_product`, `notifications_product/preferences.py`.

### M8 — Automation rules single file + move engine
End dual-write; relocate engine under `jarvis/automation/`. **Files:** `automation_engine.py`, `paths.py`.

### M9 — Deduplicate flytying registration; fix git `register_api`
**Files:** `extensions/flytying/*`, `extensions/git/extension.py`.

### M10 — Auth middleware order + health PIN scope
NetworkGuard before PIN; exact-match health exempts. **Files:** `gui/server.py`, `security/middleware.py`, `auth.py`.

### M11 — Global exception handler
Log with id; sanitize message. Use `error_handling.py`. **Files:** `gui/server.py`, `error_handling.py`.

### M12 — Layout SoT
One server store; ui_prefs cache. **Files:** `layouts_product`, `dashboard_product/cache.py`, `ui_prefs.js`, `workspace_layouts.js`.

### M13 — Desktop notify respects DND
**Files:** `notify_util.py`, `notifications_product/preferences.py`, `media_jobs.py`.

### M14 — Retire dead modules
server_shutdown, gaming_shutdown, gesture_settings dupes, search bridge shims, intelligence/memory_platform dead APIs. **Files:** listed in audit §5.

### M15 — Docs certification pile
Archive/supersede contradictory `ARIA_*CERTIFICATION*.md` with pointer to Bible + this roadmap. **Files:** `docs/*`.

### M16 — Relationship graph ownership ADR
Decide Connections vs ACM for triples; stop silent dual-write or document as intentional projection. **Files:** `relationship_memory.py`, `graph_store.py`.

### M17 — Provider health honesty
Don't list inert providers as available. **Files:** `provider_health/probe.py`.

### M18 — Log rotation
Cap/rotate `data/logs`. **Files:** daemon logging setup, ops scripts.

---

## Low

### L1 — Generate `view_router` registry from data, not 35 ifs
### L2 — ES module migration plan (incremental); stop new IIFEs
### L3 — Remove media API key from query string (blob URLs / cookie session)
### L4 — Design tokens → CSS build step or delete Python SoT claim
### L5 — Shrink god modules opportunistically after C1 (assistant/router)
### L6 — Planner API: stop smuggling system routes
### L7 — Vision honesty gate actually gates or remove `force` dead branch
### L8 — Browser download subsystem: enable or delete
### L9 — PinLock `/api/health/lite` stale exempt
### L10 — Seed cheatsheets / import-time side effects deferred to lifespan

---

## Suggested sequencing (when approved)

```
C5 Shutdown durability          (small, high severity)
C6 Single assistant ownership   (correctness)
C3 Memory read path             (ACM integrity; after R1)
C2 NLU accuracy gate            (routing truth)
C1 Pipeline unify               (largest behavior change — after C2 stabilizes routes)
C4 ariaMutate adoption          (can parallelize with C1 on UI)
H9 CI green                     (ongoing parallel)
H10 Cert hygiene                (parallel)
then H1 (needs ACM-touch approval), H2–H8, then Medium Batch D R2+, …
```

---

## Explicitly out of scope until separate approval

- Replacing ACM or adding another cognitive memory platform
- Full frontend rewrite / React migration
- Platform-mandatory mode
- Deleting `relationship_graph` without Connections ADR
- Vault deletion (Batch D R6) before R2–R5
- Broad `aria_acm` organ redesign

---

## Approval gate

| Item | Status |
|------|--------|
| Research complete | Done |
| Architecture Review | Done |
| Architecture Bible v2 | Done |
| Engineering Audit | Done |
| This Roadmap | Done |
| Implementation of any Critical/High/Medium/Low item | **Blocked pending explicit approval** |

**STOP. Do not modify application code until a named roadmap item is approved.**
