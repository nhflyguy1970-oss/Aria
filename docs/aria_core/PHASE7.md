# Aria Core V2.0 — Phase 7

**Status:** Complete when CI green
**Scope:** Memory ownership → Aria Core · organ storage underneath · MC Memory view · no other organ moves

## Non-goals

- Migrate Knowledge / Planning / Reasoning / Runtime
- Rewrite storage, schema, or databases
- Migrate persisted data
- Change Cap Bus / Cognitive Orchestrator public contracts

## Artifacts

| Artifact | Path |
|----------|------|
| Memory Manager | `aria_core/memory_manager.py` |
| Public API | `aria_core/memory.py` |
| Cap Bus wiring | `aria_core/capability_bus.py` (remember/recall → Core) |
| Events | `event_types.py` / `event_contracts.py` |
| MC Memory tab | Platform aggregator + app.js + desktop + server |
| Docs | `docs/aria_core/MEMORY.md` |
| Tests | `tests/test_aria_core_phase7.py` |

## Flow

```text
Cap Bus remember/recall
  → Cognitive Orchestrator (unchanged)
    → aria_core.memory_manager
      → jarvis.modules.memory.MemoryStore
```

## Verification

```bash
bash scripts/aria_core_compat.sh
python scripts/ci_check.py all
bash scripts/ci-local.sh
```

## Success checklist

- [x] Memory owned by Aria Core
- [x] Existing MemoryStore underneath
- [x] Applications unchanged
- [x] Capability Bus / Cognitive Orchestrator behavior preserved
- [x] MC Memory operational view (no contents by default)
- [x] Event Bus memory lifecycle
- [ ] Compat + CI green (pending run / GHA)
