# Aria Core V2.0 — Phase 1

**Status:** Implementation  
**Scope (frozen):** Inventory SSOT · Behavioral Compatibility Contract · Compatibility Harness · Learning Governor (passthrough) · Documentation · Baselines  

## Non-goals (do not do in Phase 1)

- Move code outside this scope  
- Merge repositories / rename packages  
- Change public APIs, startup, or deployment  
- Change Learning Governor policy beyond passthrough  

## Golden rule

Behavior before == behavior after (unless intentional UX improvement).  
Aria must never become less capable.

## Artifacts

| Artifact | Path |
|----------|------|
| Capability Inventory | `docs/aria_core/CAPABILITY_INVENTORY.md` |
| Behavioral Contract | `docs/aria_core/BEHAVIORAL_CONTRACT.json` |
| Learning Governor | `jarvis/learning_governor.py` (Aria) |
| Compat harness | `scripts/aria_core_compat.sh` |
| Baseline capture | `scripts/aria_core_baseline.py` |

## Learning Governor

- Default **on** (`ARIA_LEARNING_GOVERNOR=1`)  
- Passthrough: propose → immediate commit via legacy writer  
- Disable: `ARIA_LEARNING_GOVERNOR=0`  
- Optional audit: `ARIA_LEARNING_GOVERNOR_AUDIT=1`  

Wired into:

- `jarvis.nlu.learning.record_correction`  
- `jarvis.modules.memory_adapter_store` memory `add` (covers JSON + SQLite backends)

## Profiles

Harness runs against **standard** and **uncensored** (`JARVIS_UNCENSORED=1`) for unit-level protected checks.

## Rollback

1. `ARIA_LEARNING_GOVERNOR=0` or revert Governor call sites  
2. Revert Phase 1 commits  
3. Re-run `scripts/aria_core_compat.sh`  

## Success checklist

- [x] Inventory complete  
- [x] Behavioral Contract complete  
- [x] Compat harness operational  
- [x] Learning Governor inserted (passthrough)  
- [x] No behavioral differences (tests)  
- [x] Local CI green  
- [ ] GitHub Actions green  
- [ ] Production Smoke / Acceptance / Startup unchanged (no Phase 1 code on those paths)
