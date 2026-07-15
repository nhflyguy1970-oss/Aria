# Changelog — Aria / Jarvis

## [Unreleased] — 2026-07-15

### Added

- **M0:** Vendored certified ACM into `aria_acm/` (pin `v0.14.0` / commit `454dcb90…`, local `aria-acm-v0.14.0-1`).
- M0 gates: `tests/test_aria_acm_m0.py` (VERSION hash, import authority, encode/remember smoke); wired into `scripts/ci_check.py`.
- ACM Integration Blueprint (design) under `docs/acm_integration/` (earlier); governance docs A001.

### Notes

- Legacy memory remains authoritative. No Shadow (M1), harvest (M2), or cutover.
- PR-M0-001: blueprint schema example `source_version` 0.14.1 vs pin harvest 0.14.0 — resolved by harvest-from-pin.
