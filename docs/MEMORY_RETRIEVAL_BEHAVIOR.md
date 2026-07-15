# Memory Retrieval Behavior

Canonical reference for Everyday / Daily Use memory behavior after **M4**.  
Owner: `aria_core.memory` → vendored ACM (`CognitiveEngine`).  
Legacy JSON/SQLite ranking helpers remain for ROLLBACK/forensic windows only.

## Memory classes

| Class | ACM mapping | Recall | Search | Notes |
|-------|-------------|--------|--------|-------|
| User facts | Experiences + Concepts | Yes | Yes | Spoken via `what_do_i_remember` |
| Preferences | Concepts / preference encode | Yes | Yes | |
| Profile / identity | Identity + Policy Gate | Summary | Rare | High-impact assent |
| Notes | Experiences | List | Yes | |
| Strategies | Concepts (not spoken by default) | No | Limited | KEEP-HOST policy filters remain |
| Telemetry / tool-outcome | Prefer KEEP-HOST diagnostics | No | No | |
| Superseded / revised | `revise_experience` lineage | Newest | Diagnostics | Experiences immutable |

## Retrieval precedence

1. Imperative memory verbs (`remember` / `forget` / `correct`) short-circuit routing → ACM.
2. Fact questions → ACM reconstruction answers (no CRUD dump).
3. Explicit search → ACM remember + host formatting.
4. Preference / about-me → ACM identity/preference views.

## Update / forget

- Corrections → `revise_experience` (immutable lineage).  
- Forget → `cool_memory` (soft accessibility; no Experience hard-delete by default).

## Forbidden

- Serving legacy MemoryStore answers when PRIMARY (except `ARIA_ACM_ROLLBACK`).  
- DualWrite / Platform CRUD as cognitive SoT.  
- Reimplementing Remembering / Activation in Aria.

See: `docs/acm_integration/MEMORY_API_MAPPING.md`, `REMOVAL_PLAN.md`.
