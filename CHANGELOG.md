# Changelog — Aria / Jarvis

## [Unreleased] — 2026-07-15

### Added

- **M1:** ACM Shadow measure — `aria_core/acm_bridge.py` dual-calls vendored ACM on Core `remember`/`search_memory` while **legacy remains authoritative**.
- Shadow metrics on Mission Control memory panel (`shadow` block) and Conversation Trace `memory_operation.v2` fields.
- M1 gates: `tests/test_aria_acm_m1.py` (M1-01..M1-04 + SUP-04); wired into CI.
- Env knobs documented in `jarvis.env.example`: `ARIA_ACM_SHADOW`, `ARIA_ACM_PRIMARY`, `ARIA_ACM_ROLLBACK`, `ARIA_ACM_PERSIST_PATH`, `ARIA_ACM_AUTO_PERSIST`.

- **M0:** Vendored certified ACM into `aria_acm/` (pin `v0.14.0` / commit `454dcb90…`, local `aria-acm-v0.14.0-1`).
- ACM Integration Blueprint under `docs/acm_integration/`; governance A001/A002/A003.

### Notes

- User-visible memory answers are unchanged under M1 (`user_visible_changed=false`).
- No harvest (M2), no PRIMARY cutover (M3).
