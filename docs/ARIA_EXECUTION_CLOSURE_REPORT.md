# ARIA Execution Closure Report

Generated: 2026-08-10T21:56:10.063080+00:00

## Verdict

`EXECUTION CLOSURE COMPLETE — BUGS FOUND`

No application code was modified. No bugs were repaired.

## Exact counts

```text
DISCOVERED ACTIONABLE (ledger): 2188
EXECUTED (PASS+FAIL+NOT TESTABLE): 2188
PASS: 1458
FAIL: 707
NOT TESTABLE: 23
UNTESTED ACTIONABLE FUNCTIONS: 0
UNACCOUNTED: 0
APPLICABLE STATES: 111
STATES PASS: 109
STATES FAIL: 2
UNTESTED APPLICABLE STATES: 0
WORKFLOWS EXECUTED: 5
INFRASTRUCTURE FAILURE EVENTS: 30
```

## Distinction

| Category | Meaning | Count |
|---|---|---:|
| DISCOVERED | Actionable controls/workflows in ledger | 2188 |
| EXECUTED | Live UI exercise attempted with recorded status | 2188 |
| VERIFIED PASS | Expected behavior positively observed | 1458 |
| FAIL | Executed; expected behavior not met | 707 |
| NOT TESTABLE | Safety-blocked real-data/system side effect | 23 |
| UNTESTED | Still PENDING — not executed | 0 |

## Untested actionable by room

- none

## Cross-room workflows

- `WF-BUG-023`: **PASS**
- `WF-CHAT-MEMORY`: **FAIL**
- `WF-KEYBOARD`: **FAIL**
- `WF-NAV-LIVING`: **PASS**
- `WF-SETTINGS-PERSIST`: **PASS**

## Infrastructure failures

Harness/browser crashes and CDP failures are recorded as **BUG-INFRA-001** / infra events (30).
These are never converted into PASS.

## Evidence

- `/tmp/aria-execution-closure/summary.json`
- `/tmp/aria-execution-closure/ledger.json`
- `/tmp/aria-execution-closure/by_id/`
- `/tmp/aria-execution-closure/by_state/`
- `/tmp/aria-execution-closure/workflows/`
- `/tmp/aria-execution-closure/logs/`

## Infrastructure honesty

- Browser/CDP crashes occurred during execution (`chrome-error://chromewebdata/`).
- Failed harness attempts are recorded as **FAIL / BUG-INFRA-001**, never PASS.
- After recovery, every PENDING ledger control and every applicable state was re-queued until accounted.
- Large BUG-024 counts include label-rediscovery misses for conditional/tab-scoped controls; these remain FAIL until proven otherwise.

## Workflow results

- `WF-CHAT-MEMORY`: FAIL (BUG-013 still observed)
- `WF-KEYBOARD`: FAIL (Ctrl+K palette not confirmed open)
- `WF-BUG-023`: PASS in this pass (no `/api/health/report` anchors found); earlier exploratory run still recorded ejection — treat as intermittent / surface-dependent
- `WF-SETTINGS-PERSIST`: PASS
- `WF-NAV-LIVING`: PASS

## Final verdict

`EXECUTION CLOSURE COMPLETE — BUGS FOUND`

