# Changelog — Aria / Jarvis

## [Unreleased] — 2026-07-15

### Added

- **M0C:** Promoted certified standalone ACM **v0.17.0** (D040 End-to-End Cognitive Dispatch) into `aria_acm/` as `aria-acm-v0.17.0-1`. Cap Bus / Core / MemoryEngine use `classify_request` → `route_request` → `dispatch_request` → `cognitive_respond` → `speak_cognitive_result`.
- M0C gates: `tests/test_aria_acm_m0c.py` (M0C-01..M0C-07); wired into CI.

- **M0B:** Promoted certified standalone ACM **v0.16.0** (D039 Cognitive Intent Classification & Routing) into `aria_acm/` as `aria-acm-v0.16.0-1`. Cap Bus / Core / MemoryEngine use `classify_request` → `route_request` → `cognitive_respond` → `speak_cognitive_result`.
- M0B gates: `tests/test_aria_acm_m0b.py` (M0B-01..M0B-07); wired into CI.

- **M0A:** Promoted certified standalone ACM **v0.15.0** (D038 Memory Authority) into `aria_acm/` as `aria-acm-v0.15.0-1`. Cap Bus / Core / MemoryEngine recall routes through `classify_request` → `cognitive_respond` → `CognitiveMemoryResult` → `speak_cognitive_result`.
- M0A gates: `tests/test_aria_acm_m0a.py` (M0A-01..M0A-05); wired into CI.

- **M4:** ACM is Aria's sole cognitive memory SoT. PRIMARY defaults on; DualWrite retired; legacy store writes redirect to ACM; specialized writers are ACM clients; hierarchy SoT consolidate disabled under PRIMARY; supremacy CI + vault operator tool; retirement report.
- M4 gates: `tests/test_aria_acm_m4.py` (M4-01..M4-03); `scripts/acm_supremacy_check.py`.

- **M3:** Controlled ACM primary authority — Cap Bus / Core / MemoryEngine route encode/recall/cool/revise through vendored ACM when `ARIA_ACM_PRIMARY=1` (and not `ARIA_ACM_ROLLBACK`). Optional legacy read fallback (default off after M4).
- M3 gates: `tests/test_aria_acm_m3.py` (M3-01..M3-06); wired into CI.

- **M2:** Operator-triggered harvest of legacy MemoryStore **INTO** vendored ACM (`aria_core/acm_harvest.py`, `scripts/acm_harvest.py`).
- **M1:** ACM Shadow measure.
- **M0:** Vendored certified ACM into `aria_acm/` (baseline `aria-acm-v0.14.0-1`; current pin `aria-acm-v0.17.0-1` via M0C).
- ACM Integration Blueprint; governance A001–A009.

### Notes

- Production: ACM only. ROLLBACK flag retained for M4 window only. Vault via `scripts/acm_vault_legacy_memory.py`. No DualWrite SoT.
