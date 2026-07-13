# Aria Core V2.0 — Phase 5

**Status:** Complete when CI green  
**Scope:** Learning ownership → Aria Core · passthrough behavior · MC Learning view · no other organ moves  

## Non-goals

- Migrate Memory / Knowledge / Planning / Runtime  
- Change propose→commit→apply semantics  
- Application migrations  

## Artifacts

| Artifact | Path |
|----------|------|
| Learning Manager | `aria_core/learning_manager.py` |
| Public API | `aria_core/learning.py` |
| Contracts | `aria_core/learning_contracts.py` |
| Compat shim | `jarvis/learning_governor.py` |
| MC Learning tab | Platform aggregator + app.js + desktop |
| Docs | `docs/aria_core/LEARNING.md` |
| Tests | `tests/test_aria_core_phase5.py` |

## Verification

```bash
bash scripts/aria_core_compat.sh
python scripts/ci_check.py all
bash scripts/ci-local.sh
```

## Success checklist

- [x] Learning owned by Aria Core  
- [x] Existing writers underneath (shim)  
- [x] Applications unchanged  
- [x] Memory/Knowledge unchanged  
- [x] MC Learning view  
- [x] Event Bus learning lifecycle  
- [x] Compat + CI green (pending GHA after push)  
