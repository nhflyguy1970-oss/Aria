# Aria Core V2.0 — Phase 3

**Status:** Complete when CI green  
**Scope:** Capability Bus · Registry · Contracts · MC Capability view · no organ moves  

## Non-goals

- Migrate memory/knowledge/planning/learning/runtime  
- Migrate applications onto the bus  
- Redesign Mission Control beyond Capability visibility  
- Behavior changes  

## Artifacts

| Artifact | Path |
|----------|------|
| Capability Bus | `aria_core/capability_bus.py` |
| Registry | `aria_core/capability_registry.py` |
| Contracts | `aria_core/capability_contracts.py` |
| Bus doc | `docs/aria_core/CAPABILITY_BUS.md` |
| Contracts doc | `docs/aria_core/CAPABILITY_CONTRACTS.md` |
| MC tab | `capabilities` (aggregator + web + desktop) |
| Tests | `tests/test_aria_core_phase3.py` |

## Verification

```bash
bash scripts/aria_core_compat.sh
python scripts/ci_check.py all
# Platform
bash scripts/ci-local.sh
```

## Success checklist

- [x] Capability Bus exists  
- [x] Capability Registry complete  
- [x] Capability Contracts documented  
- [x] Mission Control visualizes capabilities  
- [x] All capabilities delegate to existing implementations  
- [x] No implementation has moved  
- [x] Compat harness (standard + uncensored)  
- [x] Local CI green (pending GHA after push)  
