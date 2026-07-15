# Aria / Jarvis Roadmap

**Last updated:** 2026-07-15

## Active — Memory replacement (ACM)

| Item | Status | Notes |
|------|--------|-------|
| ACM Integration Blueprint | Approved / locked | `docs/acm_integration/` · A001 |
| Phase M0 — Vendor ACM into `aria_acm/` | **Complete** | `aria-acm-v0.14.0-1` |
| **Phase M1 — Shadow measure** | **Complete** | `ARIA_ACM_SHADOW`; authoritative=legacy; `aria_core/acm_bridge.py` |
| Phase M2 — Harvest migrate INTO ACM | Not started | Awaiting approval after M1 |
| Phase M3 — ACM primary cognition | Not started | |
| Phase M4 — Retire legacy cognitive SoT | Not started | |

Standalone ACM remains research/reference. Aria production copy: `aria_acm/`.

See: [`docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md`](docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md)

## Platform & product (ongoing)

See [`docs/PHASE_ROADMAP.md`](docs/PHASE_ROADMAP.md) and [`UPGRADES.md`](UPGRADES.md).

## Explicit non-goals (this epoch)

- Beginning M2+ without explicit approval  
- Serving ACM answers while Shadow only (user_visible_changed must stay false)  
- Dual cognitive SoTs as a permanent architecture
