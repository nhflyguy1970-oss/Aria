# ARIA Pre-Repair Final Report

Generated: 2026-08-11T03:46:00+00:00

## Verdict

`PRE-REPAIR TRIAGE COMPLETE — READY FOR REPAIR`

No application code was modified. No bugs were repaired.

## Execution coverage (prior phase)

- 2,188 / 2,188 executed; PASS 1458 / FAIL 707 / NOT TESTABLE 23
- 0 untested; 0 unaccounted
- States: 111 applicable; 109 PASS / 2 FAIL

## 707 failure classification

| Category | Count |
|---|---|
| REAL APPLICATION BUG | 12 |
| DUPLICATE | 0 |
| TEST ARTIFACT | 665 |
| INFRASTRUCTURE | 30 |
| UNKNOWN | 0 |
| UNCLASSIFIED | 0 |

Those **12** ledger REAL rows are historical product bugs already known (BUG-002/003/005/006/011/013/014/015/018/023). They collapse into fewer repair roots in the queue.

Deduplicated repair items: **20** (product roots still failing on retest + harness note + infra retest context).

## BUG-024 (661) — harness/discovery, not 661 product bugs

```
BUG-024 REAL APPLICATION FAILURES = 0
BUG-024 TEST ARTIFACTS = 661
BUG-024 DUPLICATES = 0
BUG-024 UNKNOWN = 0
```

Evidence: stratified sample **n=72** (DEFAULT 30 / CONDITIONAL 16 / TAB 26) all TEST_ARTIFACT after placeholder/id-aware rematch and live spot-checks (Advanced ▾ present; Export CSV/Markdown vs bare CSV/Markdown; id vs visible label; concatenated chips).

Confidence: **HIGH** for sampled IDs; **MEDIUM** for non-sampled inheritance from 100% artifact strata. Residual risk: an unsampled true missing control could still exist — promote to ROOT-024-CONFIRMED if found during repair.

## Historical regression

- HISTORICAL P0 UNCHECKED: **0**
- HISTORICAL P1 UNCHECKED: **0**
- Still failing P0: **0**
- Still failing P1: **5** — BUG-001, BUG-002, BUG-003, BUG-013, BUG-014
- Still failing P2: **10** — BUG-004, BUG-005, BUG-006, BUG-008, BUG-009, BUG-015, BUG-016, BUG-018, BUG-019, BUG-020
- Still failing P3: **2** — BUG-010, BUG-022
- Not reproducible / changed: BUG-007, BUG-011, BUG-012, BUG-017, BUG-021, BUG-023

## NOT TESTABLE review (23/23)

- VALID: **6**
- SHOULD HAVE BEEN TESTABLE: **17** (disposable audio deletes + calendar work-block)

## Infrastructure (30/30)

- All **30** are `chrome_error` browser crashes
- Not application bugs; all retest-required

## E2E workflows

- **42** rows; results: PASS 20 / FAIL 13 / NOT TESTABLE 8 / CHANGED BEHAVIOR 1
- **NOT EXECUTED = 0**
- See `docs/ARIA_E2E_WORKFLOW_MATRIX.md`

## Recommended repair order

1. P1: BUG-001 (bare `/` living), BUG-002 (audio status), BUG-003 (activity inbox), BUG-013 (chat→memory recall), BUG-014 (fly inventory)
2. P2: BUG-005 cancel, BUG-006 mission honesty, BUG-008/009 memory/integrity, BUG-015/016 planner/journal, BUG-018/019 models/settings, BUG-004/020
3. P3: BUG-010 openapi, BUG-022 health polish
4. Harness-only: ROOT-024-HARNESS-STATE (do not product-repair 661 artifact rows)
5. Retest 30 INFRA-masked execution IDs after browser stability

## Deliverables

| Doc | Path |
|---|---|
| Failure triage | `docs/ARIA_FAILURE_TRIAGE_REPORT.md` |
| Repair queue | `docs/ARIA_ROOT_CAUSE_REPAIR_QUEUE.md` |
| Regression matrix | `docs/ARIA_REGRESSION_MATRIX.md` |
| E2E matrix | `docs/ARIA_E2E_WORKFLOW_MATRIX.md` |
| NOT TESTABLE review | `docs/ARIA_NOT_TESTABLE_REVIEW.md` |
| Infrastructure | `docs/ARIA_INFRASTRUCTURE_FAILURE_REPORT.md` |
| Evidence root | `/tmp/aria-triage/` |
