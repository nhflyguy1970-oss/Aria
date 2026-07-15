# Project History — Aria / Jarvis

## 2026-07-15 — M0: Vendor ACM into Aria

Implemented blueprint Phase **M0** only:

- Copied certified ACM package (`acm/`) + `LICENSE` into `aria_acm/` at pin `v0.14.0` / `454dcb90a352a3f1daa44aa95ff7b2801994f4e3`
- Wrote `VERSION.json`, `NOTICE`, package marker; minimal `acm` import bootstrap for nested literal copy
- Packaging/CI discovery; M0-01..M0-03 tests green
- Legacy memory still authoritative; no M1 Shadow, no data migration

Problem report: `docs/acm_integration/PROBLEM_REPORT_M0.md` (version harvest vs schema example).

## 2026-07-15 — ACM Integration Blueprint (design only)

ACM Operational Certification completed and ACM approved for integration into Aria.

Produced a **design-only** engineering blueprint for full cognitive memory replacement:

- Independent vendored copy model (`aria_acm/`) — standalone ACM remains research/reference  
- ACM Supremacy Rules 1–6  
- Complete capability matrix, import/API/migration/MC/Trace/removal/test/rollback plans  

**Verdict:** READY TO IMPLEMENT — approved. Authoritative docs: `docs/acm_integration/` · Decision **A001**.

## Prior eras

Product and platform history continues in `docs/PHASE_ROADMAP.md` and `UPGRADES.md`.
