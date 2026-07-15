# Problem Report — M0B ACM v0.16.0 Promotion

**Milestone:** M0B  
**Status:** Resolved  
**Date:** 2026-07-15

## Summary

Controlled promotion of certified standalone ACM **v0.16.0** (D039 Cognitive Intent Classification & Routing) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.16.0` |
| Commit | `6f6d0f89d0af35b018c2a781a38748d21e303ae0` |
| Local copy | `aria-acm-v0.16.0-1` |
| Prior pin | `aria-acm-v0.15.0-1` (M0A / D038) |

## Integration notes

- Aria `acm_bridge` calls `route_request` then `cognitive_respond` then `speak_cognitive_result`.
- Aria does not determine cognitive ownership or invent memory.
- M0 import bootstrap (`sys.modules["acm"]`) preserved.
- Memory Authority (D038) remains active and compatible.

## Validation

- `tests/test_aria_acm_m0b.py` — promotion + routing gates  
- Regression M0–M4 ACM suites  
- Full CI (`scripts/ci_check.py all`)

## STOP

No additional implementation beyond M0B without explicit approval.  
Next approved step after approval: rerun Daily Use Test 1 unchanged and compare results.
