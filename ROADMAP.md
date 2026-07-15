# Aria / Jarvis Roadmap

**Last updated:** 2026-07-15

## Active — Memory replacement (design approved pending sign-off)

| Item | Status | Notes |
|------|--------|-------|
| **ACM Integration Blueprint** (design only) | **READY TO IMPLEMENT** | `docs/acm_integration/` · Decision A001 |
| Phase M0 — Vendor ACM copy into `jarvis/aria_acm/` | Not started | Blocked on blueprint approval |
| Phase M1 — Shadow measure | Not started | Closes ACM cert Condition 1 vs live Aria |
| Phase M2 — Harvest migrate INTO ACM | Not started | No automatic migration |
| Phase M3 — ACM primary cognition | Not started | Legacy fallback optional |
| Phase M4 — Retire legacy cognitive SoT | Not started | After UAT + rollback window |

Standalone ACM (`/media/jeff/AI/ACM`) remains the research/reference implementation. Aria receives an **independent** production copy — no shared library, no auto-sync.

See: [`docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md`](docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md)

## Platform & product (ongoing)

See [`docs/PHASE_ROADMAP.md`](docs/PHASE_ROADMAP.md) (Phases 1–3) and [`UPGRADES.md`](UPGRADES.md).

## Explicit non-goals (this epoch)

- Implementing ACM inside Aria before blueprint approval  
- Treating ACM as a pip runtime dependency  
- Dual cognitive SoTs as a permanent architecture  
- Mission Control redesign as part of memory cutover
