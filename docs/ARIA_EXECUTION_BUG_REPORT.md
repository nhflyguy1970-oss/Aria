# ARIA Execution Closure Bug Report

Generated: 2026-08-10T21:56:10.063080+00:00

## Existing bugs rechecked / still observed

| Bug | Status in execution phase |
|---|---|
| BUG-001 | STILL FAILING (0 execution hits) |
| BUG-002 | STILL FAILING (1 execution hits) |
| BUG-003 | STILL FAILING (2 execution hits) |
| BUG-004 | NOT CHECKED (0 execution hits) |
| BUG-005 | STILL FAILING (1 execution hits) |
| BUG-006 | STILL FAILING (2 execution hits) |
| BUG-007 | NOT CHECKED (0 execution hits) |
| BUG-008 | NOT CHECKED (0 execution hits) |
| BUG-009 | NOT CHECKED (0 execution hits) |
| BUG-010 | NOT CHECKED (0 execution hits) |
| BUG-011 | STILL FAILING (1 execution hits) |
| BUG-012 | CHANGED BEHAVIOR (0 execution hits) |
| BUG-013 | STILL FAILING (1 execution hits) |
| BUG-014 | STILL FAILING (1 execution hits) |
| BUG-015 | STILL FAILING (1 execution hits) |
| BUG-016 | NOT CHECKED (0 execution hits) |
| BUG-017 | NOT CHECKED (0 execution hits) |
| BUG-018 | STILL FAILING (1 execution hits) |
| BUG-019 | NOT CHECKED (0 execution hits) |
| BUG-020 | NOT CHECKED (0 execution hits) |
| BUG-021 | NOT CHECKED (0 execution hits) |
| BUG-022 | NOT CHECKED (0 execution hits) |

## New / infrastructure bugs

### BUG-023 — P1 — SPA ejection via raw `/api/` navigation
- Hits in execution ledger: **1**
- Expected: remain in Living Workspace
- Actual: control/link navigates to `/api/...` or ejects SPA
- BLOCKS RELEASE: yes

### BUG-024 — P2 — Discovered control missing on re-enter
- Hits: **661**
- BLOCKS RELEASE: no

### BUG-025 — P1 — UI TypeError / crash text after control activation
- Hits: **0**
- BLOCKS RELEASE: yes if reproducible in interactive use

### BUG-026 — P2 — Applicable UI state not successfully induced/verified
- Hits: **0**

### BUG-INFRA-001 — Test infrastructure failure
- Hits: **30**
- Meaning: browser crash, chrome-error page, CDP timeout, or harness exception — NOT an application PASS
- BLOCKS RELEASE: no (blocks closure confidence)

## Workflow failures

- `WF-BUG-023`: PASS bug=None
- `WF-CHAT-MEMORY`: FAIL bug=BUG-013
- `WF-KEYBOARD`: FAIL bug=None
- `WF-NAV-LIVING`: PASS bug=None
- `WF-SETTINGS-PERSIST`: PASS bug=None
