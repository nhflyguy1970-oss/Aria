# Problem Report — M0F ACM v0.18.4 Promotion

**Milestone:** M0F  
**Status:** Resolved  
**Date:** 2026-07-17

## Summary

Controlled promotion of certified standalone ACM **v0.18.4** (D045 Preference
Reconstruction Fix) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.18.4` |
| Commit | `3023ed85b1de5a9b19c5058509f1fda870f45555` |
| Local copy | `aria-acm-v0.18.4-1` |
| Prior pin | `aria-acm-v0.18.3-1` (M0E / D044) |

## Promoted fixes

- D045 Preference reconstruction competitor admissibility
- Lexical support concepts excluded from primary/competing recollections
- Lexical metadata excluded from answer rendering
- Artificial `competing_recollections` eliminated; true semantic conflicts preserved
- Prior intact: D038 · D039 · D040 · D041 · D042 · D043 · D044

## Explicitly not promoted / not implemented

Future ACM backlog items remain deferred (teach vs query, evidence intent,
diagnostics UX, preference editing, explainability presentation, etc.).

## Integration notes

- No Aria bridge redesign; Cap Bus / `acm_bridge` continue existing primary_* façades.
- M0 import bootstrap (`sys.modules["acm"]`) preserved.
- Only intentional delta vs standalone ACM: Aria M0 `acm` import bootstrap.

## Validation

- `tests/test_aria_acm_m0f.py` — pin, preference matrix, lexical non-conflict, true conflict, identity regression  
- Aria regression fixtures aligned to D045 reconstructable preferences (phase7 roundtrip, M1 shadow golden set)  
- Regression M0–M4 / M0A–M0E / CIC suites  
- Full CI (`scripts/ci_check.py all`) — 508 passed, 1 skipped

## STOP

No additional implementation beyond M0F without explicit approval.  
Next approved step: Preference Behavioral Certification.
