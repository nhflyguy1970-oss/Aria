# Aria Core V2.0 — Phase 6

**Status:** Complete when CI green  
**Scope:** Cognitive Orchestrator · Cap Bus coordination · MC Cognition view · no organ moves  

## Non-goals

- Move Memory / Knowledge / Planning / Reasoning  
- Change Cap Bus verb results  
- Application migrations  

## Artifacts

| Artifact | Path |
|----------|------|
| Orchestrator | `aria_core/cognitive_orchestrator.py` |
| Public API | `aria_core/cognition.py` |
| Cap Bus wiring | `aria_core/capability_bus.py` |
| Docs | `docs/aria_core/COGNITION.md` |
| Tests | `tests/test_aria_core_phase6.py` |

## Verification

```bash
bash scripts/aria_core_compat.sh
python scripts/ci_check.py all
bash scripts/ci-local.sh
```

## Success checklist

- [x] Cognitive Orchestrator exists  
- [x] Cap Bus delegates through it  
- [x] Organs unchanged  
- [x] MC Cognition view  
- [x] Orchestration events  
- [x] Compat + CI green (pending GHA after push)  
