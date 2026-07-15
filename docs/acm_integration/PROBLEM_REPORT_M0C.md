# Problem Report — M0C ACM v0.17.0 Promotion

**Milestone:** M0C  
**Status:** Resolved  
**Date:** 2026-07-15

## Summary

Controlled promotion of certified standalone ACM **v0.17.0** (D040 End-to-End Cognitive Dispatch) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.17.0` |
| Commit | `af108d0893c7aee11f21f96fba51e8641f219ae2` |
| Local copy | `aria-acm-v0.17.0-1` |
| Prior pin | `aria-acm-v0.16.0-1` (M0B / D039) |

## Integration notes

- Aria `acm_bridge` calls `route_request` → `dispatch_request` → `cognitive_respond` → `speak_cognitive_result`.
- Aria does not determine ownership, dispatch cognition, invent memory, or terminate in infrastructure.
- M0 import bootstrap (`sys.modules["acm"]`) preserved.
- D038 Memory Authority and D039 Intent Classification remain active.

## Validation

- `tests/test_aria_acm_m0c.py` — dispatch + organ-termination gates  
- Regression M0–M4 / M0A / M0B ACM suites  
- Full CI (`scripts/ci_check.py all`)

## STOP

No additional implementation beyond M0C without explicit approval.  
Next approved step after approval: rerun Daily Use Test 1 unchanged and compare results.
