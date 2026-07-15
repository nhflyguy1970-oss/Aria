# Changelog — Aria / Jarvis

## [Unreleased] — 2026-07-15

### Added

- **M3:** Controlled ACM primary authority — Cap Bus / Core / MemoryEngine route encode/recall/cool/revise through vendored ACM when `ARIA_ACM_PRIMARY=1` (and not `ARIA_ACM_ROLLBACK`). Default PRIMARY **off**. Optional legacy read fallback. Observability/provenance retained. No legacy deletion.
- M3 gates: `tests/test_aria_acm_m3.py` (M3-01..M3-06); wired into CI.

- **M2:** Operator-triggered harvest of legacy MemoryStore **INTO** vendored ACM (`aria_core/acm_harvest.py`, `scripts/acm_harvest.py`). Idempotent `legacy_id` mapping, revise lineage when known, identity assent, migration report. Legacy remains authoritative.
- M2 gates: `tests/test_aria_acm_m2.py` (M2-01..M2-04); wired into CI.

- **M1:** ACM Shadow measure — `aria_core/acm_bridge.py` dual-calls vendored ACM on Core `remember`/`search_memory` while **legacy remains authoritative**.
- **M0:** Vendored certified ACM into `aria_acm/` (`aria-acm-v0.14.0-1`).
- ACM Integration Blueprint under `docs/acm_integration/`; governance A001–A005.

### Notes

- PRIMARY is opt-in (not global default). Rollback via `ARIA_ACM_ROLLBACK`. No legacy deletion (M4).
