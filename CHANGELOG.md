# Changelog — Aria / Jarvis

## [Unreleased] — 2026-07-15

### Added

- **M2:** Operator-triggered harvest of legacy MemoryStore **INTO** vendored ACM (`aria_core/acm_harvest.py`, `scripts/acm_harvest.py`). Idempotent `legacy_id` mapping, revise lineage when known, identity assent, migration report. Legacy remains authoritative.
- M2 gates: `tests/test_aria_acm_m2.py` (M2-01..M2-04); wired into CI.

- **M1:** ACM Shadow measure — `aria_core/acm_bridge.py` dual-calls vendored ACM on Core `remember`/`search_memory` while **legacy remains authoritative**.
- **M0:** Vendored certified ACM into `aria_acm/` (`aria-acm-v0.14.0-1`).
- ACM Integration Blueprint under `docs/acm_integration/`; governance A001–A004.

### Notes

- Harvest never runs automatically. No PRIMARY cutover (M3). No legacy deletion (M4).
