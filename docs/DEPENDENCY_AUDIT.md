# Dependency Audit — Legacy Cognitive Memory → ACM

**Date:** 2026-07-15  
**Scope:** Aria / Jarvis repository only  
**Gate:** `ARIA_ACM_PRIMARY=1` (default) · `ARIA_ACM_ROLLBACK` emergency only

## Summary

All cognitive **execution** paths under PRIMARY terminate in embedded ACM via
`aria_core.acm_bridge` (and Cap Bus / MemoryEngine façades). Remaining
`MemoryStore` / SQLite references are:

1. **Façades** that divert to ACM when authoritative (`acm_store_facade`).
2. **ROLLBACK / vault / harvest / forensic** paths (justified non-production cognition).
3. **Tests / docs / operator tools**.

No cognitive request under PRIMARY may answer from legacy MemoryStore as SoT.

## P0 — Converted (were answering via legacy when PRIMARY on)

| Module | Legacy dependency | Replacement | Status |
|--------|-------------------|-------------|--------|
| `jarvis/modules/memory.py` JsonMemoryStore search/list/get/update/delete/similar | JSON entries | `acm_store_facade` → ACM | Converted |
| `jarvis/modules/memory_sqlite.py` same methods | SQLite rows | same | Converted |
| `jarvis/memory_context.py` `system_prompt_block` | `list_entries` | `system_prompt_from_acm` | Converted |
| `jarvis/knowledge/search.py` `_search_memory` | `assistant.memory.search` | `primary_search` | Converted |
| `aria_core/memory_manager.py` `mission_control_panel` / stats / health | legacy list counts | `acm_dashboard` | Converted |
| `aria_core/conversation_trace.py` memory_operation | thin shadow fields | v3 ACM diagnostics | Converted |
| Cap Bus / MemoryEngine / Core recall-write | already ACM PRIMARY | unchanged | Already ACM |

## P1 — Covered by store façades (callers now hit ACM)

| Area | Callers (examples) | Via |
|------|-------------------|-----|
| Identity / profile / preferences / facts | REST memory API, profile questionnaire, trust, experience writers | store façade / Cap Bus |
| Conversation context / summaries | prepare_context, context fragments | `primary_context_fragments` / Cap Bus |
| Specialized learning | correction / observation / teaching | M4 ACM clients + façades |
| Briefings / engineering notes | `list_entries` / `search` | façades |
| Memory GUI list/CRUD (Aria payload) | extensions/memory API | façades → ACM cool/revise |

## P2 — Justified remaining legacy references (non-cognitive SoT)

| Component | Why retained | Cognitive execution? |
|-----------|--------------|----------------------|
| JSON/SQLite storage files | Vault / forensic / harvest source | No under PRIMARY |
| `ARIA_ACM_ROLLBACK` branch | Emergency restore façades | Only when ROLLBACK=1 |
| `scripts/acm_vault_legacy_memory.py` | Operator vault | No |
| `aria_core/acm_harvest.py` | One-way migrate INTO ACM | Import only |
| DualWrite adapter module | Identity wrap; supremacy forbids authority | No |
| Tests asserting storage mechanics | Regression | N/A |
| AI-Platform Mission Control markup | Layout host; Aria supplies ACM payload | UI labels may still say “Memory” until Platform update |

## Explicit non-deps (not cognitive memory)

Journal files, cheatsheets as documents, RAG document index, HA state, calendar —
not ACM organs; not reclassified as cognitive SoT in this conversion.

## Zero-gap rule

Any new module that would call `MemoryStore.search/list_entries` for cognition
must either (a) call Cap Bus / `acm_bridge`, or (b) rely on the authoritative
store façades. Direct legacy SoT is forbidden under PRIMARY.
