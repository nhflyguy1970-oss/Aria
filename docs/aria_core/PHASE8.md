# Aria Core V2.0 — Phase 8

**Status:** Complete when CI green  
**Scope:** Reflex Layer before cognition · replace greeting hacks · MC Reflex view · no organ transplants  

## Non-goals

- Migrate Memory / Knowledge / Planning / Reasoning further  
- Change Cap Bus or Cognitive Orchestrator contracts  
- Grow ad-hoc regex lists in `router.py`  

## Artifacts

| Artifact | Path |
|----------|------|
| Reflex Engine | `aria_core/reflex_engine.py` |
| Public API | `aria_core/reflex.py` |
| Router wiring | `jarvis/router.py` → `try_reflex` before NLU |
| Handlers | `jarvis/handlers/meta.py` (reflex_reply, session_*) |
| Events | `event_types.py` / `event_contracts.py` |
| MC Reflex tab | Platform aggregator + app.js + desktop + server |
| Docs | `docs/aria_core/REFLEX.md` |
| Tests | `tests/test_aria_core_phase8.py` |

## Flow

```text
router.route
  → aria_core.reflex.try_reflex
      → hit:  handler (greeting / clear / …)  [bypass cognition]
      → miss: NLU → Cap Bus path unchanged
```

## Verification

```bash
bash scripts/aria_core_compat.sh
python scripts/ci_check.py all
bash scripts/ci-local.sh
```

## Success checklist

- [x] Reflex Layer exists  
- [x] Greeting hacks replaced by Reflex Engine  
- [x] Feature catalog (not regex sprawl)  
- [x] Simple interactions bypass cognition  
- [x] Mission Control Reflex view  
- [ ] Compat + CI green (pending run / GHA)  
