# Cognitive Infrastructure Conversion

**Status:** Complete (A010)  
**Repository:** Aria / Jarvis only  
**Date:** 2026-07-15  
**Prerequisite:** M0–M4 · M0A–M0C (embedded ACM v0.17.0 / D038–D040)

## Objective

ACM is Aria’s brain. Every cognitive capability depends only on the embedded ACM
(`aria_acm/`). This is a complete cognitive infrastructure conversion — not a
MemoryEngine rename.

## Architectural rules

1. Exactly **one** cognitive memory implementation: embedded ACM.
2. Every cognitive capability terminates in ACM under `ARIA_ACM_PRIMARY` (default on).
3. Standalone `/media/jeff/AI/ACM` is research-only — **not modified** by this work.
4. Legacy JSON/SQLite MemoryStore remains forensic/vault + `ARIA_ACM_ROLLBACK` only.

## Conversion model

```
Conversation / Cap Bus / REST / Knowledge / Prompt
        ↓
ACM Bridge (aria_core.acm_bridge)
        ↓
Intent Classification → Cognitive Ownership → Cognitive Dispatch
        ↓
ACM Organ(s) → CognitiveMemoryResult → speak_cognitive_result
```

Store façades (`JsonMemoryStore` / `SqliteMemoryStore` search, list, get, update,
delete, similar_exists) divert to ACM projections when authoritative
(`aria_core.acm_store_facade`).

## Phases delivered

| Phase | Deliverable |
|-------|-------------|
| 1–2 | `docs/DEPENDENCY_AUDIT.md`, `docs/DEPENDENCY_GRAPH.md` |
| 3–4 | Store façades, system prompt, knowledge search → ACM |
| 5 | Mission Control `mission_control_panel` → `acm_dashboard` |
| 6 | Conversation Trace `memory_operation.v3` + cognition.acm |
| 7 | Legacy cognitive execution severed under PRIMARY; ROLLBACK retained |

## Validation

- `tests/test_cognitive_infrastructure_conversion.py` (CIC-01..06)
- Full `scripts/ci_check.py all`
- Authentic Daily Use Test 1 deferred pending explicit approval

## Related docs

- `docs/DEPENDENCY_AUDIT.md`
- `docs/DEPENDENCY_GRAPH.md`
- `docs/MISSION_CONTROL_ACM.md`
- `docs/CONVERSATION_TRACE_ACM.md`
- `docs/LEGACY_RETIREMENT_FINAL.md`
