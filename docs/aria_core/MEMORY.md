# Aria Core Memory

**Status:** M4 complete — ACM is the sole cognitive SoT  
**Owner:** `aria_core.memory` (`aria_core.memory_manager`) → façades into vendored ACM (`aria_acm/`)  
**Underneath (retired as cognitive SoT):** `jarvis.modules.memory` JSON/SQLite — cold vault / ROLLBACK window only

## Behavior (M4)

```text
Cap Bus / Core Memory API / MemoryEngine
  → aria_core.acm_bridge (PRIMARY default on)
    → aria_acm.acm.api.engine.CognitiveEngine
      → encode / what_do_i_remember / cool_memory / revise_experience
```

Legacy MemoryStore `.add` redirects to ACM when authoritative. DualWrite cognitive
authority is retired. Hierarchy consolidate does not mutate SoT under PRIMARY.

## Public API (stable names)

| API | ACM verb |
|-----|----------|
| `remember` | `encode` |
| `forget` | `cool_memory` (soft) |
| `update_memory` | `revise_experience` |
| `search_memory` / Cap Bus `recall` | `what_do_i_remember` |
| `get_memory` | store public view / experience id |
| `retrieve_context` / `prepare_context` | ACM fragments + Aria prompt packaging |
| `MemoryStore` / `create_memory_store` | Forensic / harvest / ROLLBACK only |

## Flags

| Flag | M4 default | Role |
|------|------------|------|
| `ARIA_ACM_PRIMARY` | **on** | ACM authoritative |
| `ARIA_ACM_ROLLBACK` | off | Temporary legacy façades (window only) |
| `ARIA_ACM_LEGACY_READ_FALLBACK` | **off** | Do not supplement ACM with legacy reads |
| `ARIA_ACM_SHADOW` | off | Retired measure phase |

## Mission Control

`mission_control_panel()` → `authoritative=acm` when PRIMARY; shadow metrics optional.

## Ownership

Cognitive memory **only** in vendored ACM. Aria owns orchestration, workflows,
reasoning, planning, permissions, presentation, diagnostics, user interaction.
