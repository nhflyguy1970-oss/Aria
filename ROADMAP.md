# Aria / Jarvis Roadmap

**Last updated:** 2026-07-15

## Active — Memory replacement (ACM)

| Item | Status | Notes |
|------|--------|-------|
| ACM Integration Blueprint | Approved / locked | `docs/acm_integration/` · A001 |
| Phase M0 — Vendor ACM into `aria_acm/` | **Complete** | `aria-acm-v0.14.0-1` |
| Phase M1 — Shadow measure | **Complete** | `ARIA_ACM_SHADOW`; authoritative=legacy |
| **Phase M2 — Harvest migrate INTO ACM** | **Complete** | `scripts/acm_harvest.py` · `aria_core/acm_harvest.py` |
| Phase M3 — ACM primary cognition | Not started | Awaiting approval after M2 |
| Phase M4 — Retire legacy cognitive SoT | Not started | |

Standalone ACM remains research/reference. Aria production copy: `aria_acm/`.

See: [`docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md`](docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md)

## Platform & product (ongoing)

See [`docs/PHASE_ROADMAP.md`](docs/PHASE_ROADMAP.md) and [`UPGRADES.md`](UPGRADES.md).

## Explicit non-goals (this epoch)

- Beginning M3+ without explicit approval  
- Automatic / background harvest  
- Dual cognitive SoTs as a permanent architecture
