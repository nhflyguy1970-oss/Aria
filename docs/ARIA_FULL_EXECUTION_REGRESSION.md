# ARIA Full Execution Regression — 2,188 Controls

Generated: 2026-08-11  
Evidence:
- Pre: `/tmp/aria-final-acceptance/pre_repair_ledger.json` (from `/tmp/aria-execution-closure/ledger.json`)
- Post: `/tmp/aria-final-acceptance/ledger/ledger.json`
- Compare: `/tmp/aria-final-acceptance/ledger/regression_compare.json`
- Post summary: `/tmp/aria-final-acceptance/ledger/summary.json`
- INFRA retest: `/tmp/aria-final-acceptance/ledger/infra_retest.json`

## Accounting (post-repair)

```text
DISCOVERED   2188
EXECUTED     2188
PASS         1297
FAIL          891
NOT TESTABLE    0
UNTESTED        0
UNACCOUNTED     0
```

Pre-repair:

```text
DISCOVERED   2188
EXECUTED     2188
PASS         1458
FAIL          707
NOT TESTABLE   23
UNTESTED        0
UNACCOUNTED     0
```

## Headline deltas

| Metric | Pre | Post | Δ |
|---|---:|---:|---:|
| PASS | 1458 | 1297 | −161 |
| FAIL | 707 | 891 | +184 |
| NOT TESTABLE | 23 | 0 | −23 |
| BUG-024 labeled FAILs | 661 | 816 | +155 |
| BUG-INFRA-001 | 30 | 75 | +45 |
| Changed status rows | — | 275 | — |
| PASS → FAIL | — | 213 | — |
| FAIL → PASS | — | 39 | — |

## Regression interpretation (critical)

From `regression_compare.json`:

```text
real_product_regressions_excl_infra_024 = 0
real_product_fixes_excl_024 = 0
pass_to_infra = 54
pass_to_024 = 159
fail_to_pass_was_024 = 18
```

**No PASS→FAIL transition carried a non-INFRA, non-BUG-024 product bug label.**

Meaning:
- Repair work did **not** introduce a labeled product regression set in the 2,188 ledger.
- Apparent PASS loss is explained by:
  1. **Chrome crashes during gallery chunks** → marked `BUG-INFRA-001` (75 during full run; all gallery).
  2. **BUG-024 harness/discovery labeling volatility** (661 → 816) — still harness artifacts, not 816 product bugs.
  3. Prior NOT TESTABLE (23) redistributed into PASS/FAIL (often BUG-024).

## INFRA retest (mandatory follow-up)

All 75 post-repair INFRA IDs were gallery controls. Clean retest:

| Result | Count |
|---|---:|
| Retested | 75 |
| PASS | 20 |
| FAIL (non-crash / BUG-024) | 10 |
| Still chrome-crash INFRA | **45** |

**Unresolved infrastructure failures after retest: 45** (gallery chrome crashes).  
These are **not** counted as product bugs; they still block a clean FINAL PASS gate requiring `infrastructure unresolved = 0`.

## Sample change shapes

### PASS → FAIL (INFRA)

```text
CONTROL ID: (gallery EXC-* during chrome-error chunks)
PRE-REPAIR: PASS
POST-REPAIR: FAIL
EXPECTED: Control exercisable
ACTUAL: chrome-error://chromewebdata/ mid-chunk
REGRESSION?: Infrastructure, not product
BUG FIXED?: n/a
NEW BUG?: No — BUG-INFRA-001
EVIDENCE: ledger_run.log CRASH href; infra_retest.json
```

### PASS → FAIL (BUG-024 relabel)

```text
CONTROL ID: various discovery IDs
PRE-REPAIR: PASS (or NT)
POST-REPAIR: FAIL bug=BUG-024
EXPECTED: Stable harness match
ACTUAL: Label/placeholder/id mismatch class (same BUG-024 family)
REGRESSION?: No product regression
BUG FIXED?: n/a
NEW BUG?: No — do not reopen BUG-024 as product
EVIDENCE: regression_compare.json pass_to_024=159
```

### FAIL → PASS (was BUG-024)

```text
CONTROL ID: e.g. EXC-0002 Open Chat
PRE-REPAIR: FAIL BUG-024
POST-REPAIR: PASS
EXPECTED: Control works
ACTUAL: PASS
REGRESSION?: No — improvement / harness luck
BUG FIXED?: Harness match improved; not a queued product bug
NEW BUG?: No
EVIDENCE: regression_compare.json
```

## States / workflows (ledger companion)

```text
STATES: 111 PASS / 0 FAIL / UNTESTED=0
WORKFLOWS: WF-CHAT-MEMORY PASS, WF-NAV-LIVING PASS, WF-SETTINGS-PERSIST PASS,
           WF-BUG-023 FAIL (raw /api/ anchor presence), WF-KEYBOARD FAIL (synthetic key)
```

See `ARIA_FINAL_ACCEPTANCE_RECONCILIATION.md` for states vs workflows accounting.

## Conclusion

The 2,188-control post-repair run is **fully accounted** (UNTESTED=0, UNACCOUNTED=0).  
Repairs did **not** create a measurable non-harness product regression set.  
Remaining release-relevant ledger debt is **unresolved gallery Chrome INFRA (45 after retest)** plus harness BUG-024 volatility (not product).
