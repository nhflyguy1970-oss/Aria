# ARIA Repair Status

Updated: 2026-08-11 (release-blocking repair phase closed)

## P1

| BUG | Status |
|---|---|
| BUG-001 | FIXED |
| BUG-002 | FIXED |
| BUG-003 | FIXED |
| BUG-013 | FIXED |
| BUG-014 | FIXED |

## P2

| BUG | Status |
|---|---|
| BUG-004 | FIXED |
| BUG-005 | FIXED |
| BUG-006 | FIXED |
| BUG-008 | FIXED |
| BUG-009 | FIXED |
| BUG-015 | FIXED |
| BUG-016 | FIXED |
| BUG-018 | FIXED |
| BUG-019 | FIXED |
| BUG-020 | FIXED |

## P3

| BUG | Status |
|---|---|
| BUG-010 | FIXED |
| BUG-022 | FIXED |

## Non-product (do not fix as product)

| Item | Status |
|---|---|
| ROOT-024-HARNESS-STATE | DEFERRED (harness-only) — do not product-fix |
| BUG-INFRA-001 (gallery chrome) | CLEARED — isolated retest; UNRESOLVED CHROME=0 (see `ARIA_GALLERY_INFRA_FINAL_REPORT.md`) |

## Baselines (do not reopen unless regression)

| BUG | Baseline |
|---|---|
| BUG-007 | NOT REPRODUCIBLE |
| BUG-011 | NOT REPRODUCIBLE |
| BUG-012 | NOT REPRODUCIBLE |
| BUG-017 | CHANGED BEHAVIOR |
| BUG-021 | NOT REPRODUCIBLE |
| BUG-023 | FIXED (Health Emergency/Doctor SPA stay verified live) |

## Post-repair acceptance (intermediate)

| Item | Result |
|---|---|
| Report | `docs/ARIA_POST_REPAIR_ACCEPTANCE_REPORT.md` |
| Evidence | `/tmp/aria-post-repair/accept/` (+ per-bug `/tmp/aria-post-repair/bug*/`) |
| Inventory (110) | UNTESTED=0 · UNACCOUNTED=0 · PASS=93 · FAIL=15 · NT=2 |
| States (111) | UNTESTED=0 · PASS=111 |
| E2E repair journeys | 17/17 PASS · NOT EXECUTED=0 |
| Infra (gallery masks) | CLEARED in post-repair pass |
| Verdict then | PASS WITH REQUIRED FIXES |

## Final acceptance closure (2026-08-11)

| Item | Result |
|---|---|
| Report | `docs/ARIA_FINAL_ACCEPTANCE_REPORT.md` |
| Evidence | `/tmp/aria-final-acceptance/` |
| 2188 ledger | EXECUTED=2188 · UNTESTED=0 · UNACCOUNTED=0 |
| Inventory 15 | UNCLASSIFIED=0 · PRODUCT BUG=0 |
| New bugs (then) | BUG-026 P0 · BUG-025 P1 — both **FIXED** in closure repair |
| Infra unresolved after retest | was 45 → **CLEARED** (`UNRESOLVED CHROME CRASHES = 0`) |
| Verdict then | BLOCKED |
| Closure report | `docs/ARIA_BUG_025_026_REPAIR_REPORT.md`, `docs/ARIA_GALLERY_INFRA_FINAL_REPORT.md` |
| Closure evidence | `/tmp/aria-final-closure/` |
| Closure verdict | **FINAL PASS** |

## Release blockers (closure)

| BUG | Priority | Status |
|---|---|---|
| BUG-026 | P0 | **FIXED** — destructive wipe refused; no actionable command |
| BUG-025 | P1 | **FIXED** — remember≠recall; marker recall; forget hides |
| Gallery INFRA | — | **CLEARED** — 0 unresolved chrome crashes |
