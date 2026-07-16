# Conversation Trace — ACM Cognition

**Date:** 2026-07-15  
**Schema:** `memory_operation.v3` (additive; supersedes v2 field set)

## Displays (under PRIMARY)

| Field | Source |
|-------|--------|
| Intent | `last_primary_op.intent` |
| Primary cognitive owner | `primary_organ` |
| Supporting organs | `supporting_organs` |
| Dispatch path | classify → route → dispatch → organ |
| Reconstruction path | ACM verb / diagnostics path |
| Termination organ | `terminated_at` |
| Confidence | `CognitiveMemoryResult.confidence` |
| Uncertainty | classification / diag uncertain |
| Provenance | result / diag provenance |
| CognitiveMemoryResult summary | nested under `cognitive_memory_result` |

Also mirrored under `cognition.acm` for Mission Control / Trace UIs.

## Removed from cognitive reporting

- MemoryStore / MemoryEngine / KnowledgeEngine / SearchEngine as cognitive owners
- Legacy handler names as memory SoT
- Shadow-only `memory_operation.v2` as the sole schema (v3 required under ACM)

## Builder

`aria_core.conversation_trace.build_conversation_trace` → `_shadow_memory_fields()`.
