# Memory API Mapping — Aria → ACM

**Status:** DESIGN ONLY  
**Policy:** Thin translation only. No legacy override of ACM cognition (Supremacy Rule 3).  
**Bridge (future):** `aria_core/acm_bridge.py` — not implemented in this phase.

---

## Principles

1. Host call names may stay during transition (`remember` / `recall`) for Cap Bus stability.  
2. Implementation **must** call vendored ACM `CognitiveEngine` (`aria_acm.acm`).  
3. Façades return host-shaped dicts when required — contents sourced from ACM public views.  
4. APIs that mutate parallel CRUD SoTs after M3 are **retired**.  
5. Shadow (M1–M2): façades may dual-call for measurement; **authoritative answer = legacy** until M3.

---

## Field map — `remember` / Cap Bus → `encode`

| Aria input | ACM `encode(...)` |
|------------|-------------------|
| `text` / `content` | `text` |
| `type=preference` | `kind="preference"` |
| `type=fact` / `note` / `auto` | `kind="experience"` (tag `legacy_type` in provenance meta via façade) |
| `type=teaching` / `success` / `failure` / `strategy` | `kind="experience"` + `context_tags` carrying class |
| `type=project` | `kind="experience"` + goal linkage via `open_goal` when checkpoint |
| `namespace` | `context_tags` including `ns:<namespace>` — **not** parallel stores |
| `tags` | folded into `context_tags` / Concept cues |
| `pin` / high-importance | `pin=True` |
| profile/identity signal | `kind="identity"` + Policy Gate / `assent` as required |
| image remember | `external_kind` + `envelope_ids` (multimodal) |
| journal remember | `context_tags+=("journal",)` |
| supersede of prior | after encode, or `revises_id=<prior experience id>` / `revise_experience` |

**Return shape (façade):** preserve host keys where possible (`id`, `ok`, `content` summary) mapped from ACM encode result (`experience_id`, `encoded`, `attention`, …). Never invent Experience text.

---

## Field map — recall / search → remembering

| Aria API | ACM API | Return adaptation |
|----------|---------|-------------------|
| `recall` / Cap Bus `recall` | `what_do_i_remember(cue)` | Spoken/list from reconstruction dict; no CoT |
| `search_memory` / `memory_search` | `remember(query)` + optional `how_related` | Host list of `{id, content, score}` from public view fields only |
| `memory_about_user` | `who_am_i()` + `what_do_i_remember("about me")` | Summary policy stays host (exclude journal megablobs via Attention/context) |
| `get_memory(id)` | store public view / timeline lookup by id | 404 if cool/absent per accessibility |
| `retrieve_context` / `prepare_context` | `remember` + `set_context` | **Prompt packaging KEEP-HOST**; bytes from ACM |

---

## aria_core.memory → ACM

| Aria Core API | Replacement ACM API | Façade notes | After M4 |
|---------------|---------------------|--------------|----------|
| `remember(text, …)` | `encode(...)` | Field map above | Keep name or alias |
| `forget(...)` | `cool_memory` (+ rare Policy erase) | Soft-first; map topic→concept_id | Keep name |
| `update_memory(...)` | `revise_experience` | Never overwrite Experience in place | Prefer `memory_correct` name |
| `search_memory(...)` | `what_do_i_remember` / `remember` | Rank using ACM activation metadata | Prefer `recall` |
| `get_memory(id)` | Experience/Concept public view | CognitiveStore lookup | Keep |
| `retrieve_context(...)` | remember + ContextFrame | Aria formats prompt | Keep |
| `merge_memories(...)` | Learning / Concept merge **proposals** | No silent merge | Gated |
| `propose_memory` / `commit_memory` | `learn` / `assent_adaptation` or `encode` | Learning Manager = coordinator | Keep pattern |
| `rollback_memory` | `rollback_adaptation` | No Experience delete | Keep |
| `memory_history` | ValidationHarness lifecycle + Trace | Observability | Keep |
| `memory_statistics` / `memory_health` | Harness + durable metrics | | Keep |
| `mission_control_panel` | Aggregate ACM observables | No content leak | Keep |
| `record_retrieval_decision` | Trace / Activation why-codes | | Keep instrumentation |
| `record_update_supersede` | revise lineage events | | Keep |
| `MemoryStore` / `create_memory_store` | **Retire as SoT** | Temporary shim reading ACM only | Remove |

---

## Capability Bus

| Cap Bus | ACM | Notes |
|---------|-----|-------|
| `remember` | `encode` | Stable external name |
| `recall` | `what_do_i_remember` | Stable external name |

Orchestrator remains Aria (KEEP-HOST). Cognition remains ACM (Rule 4).

---

## MemoryEngine actions → ACM

| Action | ACM | Temporary layer | Retire |
|--------|-----|-----------------|--------|
| `remember` | `encode` | MemoryEngine → bridge | CRUD `store.add` |
| `recall` / `memory_about_user` | `what_do_i_remember` / `who_am_i` | | CRUD path |
| `memory_search` | `remember` + associations | | embedding-as-SoT |
| `memory_forget` | `cool_memory` | | hard delete default |
| `memory_correct` | `revise_experience` (+ reconcile) | | silent update |
| `memory_prune` | forgetting cool proposals | | |
| `memory_consolidate` | `sleep` + optional LLM propose Reflective text | LLM **outside** ACM | distill-as-SoT |
| `memory_hierarchy` | stages / accessibility views | | layer SoT |
| `memory_summarize` | `who_am_i` + remember | | |
| `memory_namespace` | `set_context` / role tags | **no parallel namespaces SoT** | namespace stores |
| `project_checkpoint` | `open_goal` + `encode` | | checkpoint JSON SoT |
| `project_resume` | Goals + remember | | |
| `remember_image` | `encode` + envelopes | | |
| `journal_remember` | `encode` + journal tags | | journal parallel memory |
| `auto_remember` | `encode` + Attention | must remain policy-visible | silent shadow SoT |
| `prepare_context` | ACM remember + Aria prompt | prompt KEEP-HOST | |
| `cheatsheet_*` | KEEP-HOST docs UI | encode only if user teaches | — |

---

## REST surface (`jarvis/extensions/memory/api.py` + related)

| Endpoint family | Mapping | After M4 |
|-----------------|---------|----------|
| `GET/POST /api/memory*` CRUD | Façade → encode / cool / revise / remember | Preserve routes; purge CRUD SoT |
| `/api/memory/environment/preferences` | encode preferences + Concepts | Host env prefs if non-cognitive may stay |
| `/api/memory/export` / `import` | ACM `export_snapshot` / migration tooling | Import = operator tool, not auto |
| `/api/memory/conflicts*` | `how_should_memory_reconcile` | Preserve |
| `/api/memory/trust*` | Cognitive strategies → Concepts; scrub via cool | Policy remainder KEEP-HOST |
| `/api/cheatsheets*` | KEEP-HOST | — |
| `/api/profile/questionnaire*` | writes → encode / identity assent | — |
| `/api/journal/.../remember` | encode + journal tags | Journal files KEEP-HOST |
| `/api/mission-control/{tab}` memory | panel from ACM observables | — |
| `/api/memory/hierarchy` · consolidate | accessibility / `sleep` | — |

---

## Event contracts

| Current event | After ACM | Notes |
|---------------|-----------|-------|
| `MemoryCreated` | emit on successful `encode` | ids/counts only — no content |
| `MemoryUpdated` | `revise_experience` / assent | |
| `MemoryDeleted` | `cool_memory` (semantic: accessibility) | Do not imply hard erase |
| `MemoryRead` / `MemorySearch` | remember path | |
| `MemoryMerged` / `MemoryCommit` / `MemoryRollback` | Learning assent / rollback | |

---

## Bridge interface sketch (design — not code)

```text
AcmBridge
  encode_from_host(payload) -> host_dict
  recall_from_host(cue, mode) -> host_dict
  forget_from_host(topic) -> host_dict
  correct_from_host(topic, text) -> host_dict
  context_for_prompt(session) -> fragments
  panel_observables() -> dict
  shadow_compare(legacy_answer, acm_answer) -> metrics   # M1–M2 only
  authoritative_route() -> "legacy" | "acm" | "rollback"
```

Error model: map ACM skip (`low_attention`) to host-visible soft failure / retry message; never leak organ internals or prompts.

---

## Preserve vs retire

| Preserve (name / route) | Retire (implementation) |
|-------------------------|-------------------------|
| Cap Bus remember/recall | `jarvis.modules.memory` as cognitive SoT |
| Event names Memory* (ids only) | DualWrite CRUD mirroring as authority |
| MC panel entrypoint | Vector DB as memory model |
| Trace organ slot | `experience_memory` / `relationship_memory` parallel SoTs |
| REST `/api/memory*` paths | Silent hard-delete semantics |

---

## Forbidden façade behaviors

- Serving legacy answer when `ARIA_ACM_PRIMARY` is set (except explicit `ARIA_ACM_ROLLBACK`).  
- Mixing legacy + ACM into one “best guess” without reconciliation lineage.  
- Reimplementing spreading activation / Remembering in Aria.  
- Writing autobiographical facts to MemoryStore when PRIMARY.
