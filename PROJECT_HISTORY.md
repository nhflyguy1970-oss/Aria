# Project History — Aria / Jarvis

## 2026-07-15 — M1: ACM Shadow measure

Implemented blueprint Phase **M1** only:

- Added `aria_core/acm_bridge.py` (thin façade; Shadow compare; panel observables)
- Dual-call from Core `remember` / `search_memory` when `ARIA_ACM_SHADOW=1`
- Authoritative route remains **legacy**; ACM answers never user-visible in M1
- Mission Control `shadow` counters; Conversation Trace `memory_operation.v2`
- Tests M1-01..M1-04 green; CI updated

No data harvest. No PRIMARY. No legacy removal.

## 2026-07-15 — M0: Vendor ACM into Aria

Implemented blueprint Phase **M0** only:

- Copied certified ACM package (`acm/`) + `LICENSE` into `aria_acm/` at pin `v0.14.0` / `454dcb90a352a3f1daa44aa95ff7b2801994f4e3`
- Wrote `VERSION.json`, `NOTICE`, package marker; minimal `acm` import bootstrap for nested literal copy
- Packaging/CI discovery; M0-01..M0-03 tests green
- Legacy memory still authoritative; no M1 Shadow, no data migration

Problem report: `docs/acm_integration/PROBLEM_REPORT_M0.md` (version harvest vs schema example).

## 2026-07-15 — ACM Integration Blueprint (design only)

ACM Operational Certification completed and ACM approved for integration into Aria.

Produced a **design-only** engineering blueprint for full cognitive memory replacement. Authoritative docs: `docs/acm_integration/` · Decision **A001**.

## Prior eras

Product and platform history continues in `docs/PHASE_ROADMAP.md` and `UPGRADES.md`.
