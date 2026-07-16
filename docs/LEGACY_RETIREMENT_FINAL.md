# Legacy Retirement Final — Cognitive Infrastructure

**Date:** 2026-07-15  
**Decision:** A010  
**Prior:** M4 `docs/acm_integration/LEGACY_RETIREMENT_REPORT.md`

## Statement

Under default production (`ARIA_ACM_PRIMARY=1`, not ROLLBACK):

- Legacy cognition **does not execute** as SoT.
- Legacy cognition **does not answer** requests.
- Legacy cognition **does not influence** responses (store façades + Cap Bus terminate in ACM).
- Mission Control Memory panel shows **ACM Cognitive Dashboard** only.
- Conversation Trace reports **ACM diagnostics** only (`memory_operation.v3`).

There is exactly **one** cognitive memory implementation inside Aria: **embedded ACM**
(`aria_acm/`).

## What remains (justified)

| Artifact | Role |
|----------|------|
| JSON/SQLite memory files | Cold vault / forensic / harvest source |
| `ARIA_ACM_ROLLBACK` | Emergency façade restore (non-default) |
| Vault / harvest scripts | Operator tools |
| Inert DualWrite module | Supremacy-checked non-authority |
| Platform UI string “Memory” | Layout host; payload is ACM |

## Archived for rollback

No additional archive tree required beyond existing vault tooling and ROLLBACK flag.
Legacy code paths remain in-tree but are non-authoritative under PRIMARY.

## Remaining legacy *references*

Must be zero as **cognitive SoT**. Textual imports of `jarvis.modules.memory` for
façades, vault, and tests are expected and justified.
