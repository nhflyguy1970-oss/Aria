# Aria Core V2.0 — Phase 4

**Status:** Complete when CI green  
**Scope:** Event Bus · contracts · MC Events view · Timeline subscriber · Governor/Cap Bus publish · no organ moves  

## Non-goals

- External brokers / networking  
- Migrating organs or applications  
- Changing Learning Governor or Capability Bus behavior beyond additive publish  

## Artifacts

| Artifact | Path |
|----------|------|
| Event Bus | `aria_core/event_bus.py` |
| Types / Contracts | `aria_core/event_types.py`, `event_contracts.py` |
| Timeline bridge | `aiplatform/mission_control/event_bus_bridge.py` |
| Docs | `docs/aria_core/EVENT_BUS.md`, `EVENT_CONTRACTS.md` |
| Tests | `tests/test_aria_core_phase4.py` |

## Verification

```bash
bash scripts/aria_core_compat.sh
python scripts/ci_check.py all
bash scripts/ci-local.sh   # Platform
```

## Success checklist

- [x] Event Bus exists  
- [x] Event contracts complete  
- [x] Mission Control visualizes events  
- [x] Timeline subscribes  
- [x] Learning Governor publishes  
- [x] Capability Bus publishes  
- [x] No implementations moved  
- [x] Compat harness  
- [x] Local CI green (pending GHA after push)  
