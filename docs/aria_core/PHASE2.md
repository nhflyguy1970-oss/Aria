# Aria Core V2.0 — Phase 2

**Status:** Complete (local CI green; GHA after push)  
**Scope:** Build Core API skeleton · wrap/delegate only · no organ moves  

## Non-goals

- Migrate memory/knowledge/planning/learning/runtime  
- Merge repos / rename packages  
- Redesign Mission Control or applications  
- Behavior changes  

## Artifacts

| Artifact | Path |
|----------|------|
| Package | `aria_core/` |
| Ownership registry | `aria_core/ownership.py` |
| API doc | `docs/aria_core/ARIA_CORE_API.md` |
| Tests | `tests/test_aria_core_phase2.py` |

## Verification

```bash
bash scripts/aria_core_compat.sh
python scripts/ci_check.py all
```

## Rollback

Revert the Phase 2 commit(s). No runtime wiring required for daily use yet.

## Success checklist

- [x] Aria Core package exists  
- [x] Major subsystems have Core interfaces  
- [x] Implementations remain underneath  
- [x] Compat harness (standard + uncensored)  
- [x] Local CI green (pending GHA after push)  
