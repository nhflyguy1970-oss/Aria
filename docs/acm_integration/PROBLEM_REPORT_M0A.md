# Problem Report — M0A ACM v0.15.0 Promotion

**Milestone:** M0A  
**Status:** Resolved  
**Date:** 2026-07-15

## Summary

Controlled promotion of certified standalone ACM **v0.15.0** (D038 Memory Authority) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.15.0` |
| Commit | `b78a85747291b024252ddf3e5baafe5247f5ff5d` |
| Local copy | `aria-acm-v0.15.0-1` |

## Integration notes

- Aria `acm_bridge` routes authoritative recall through `cognitive_respond` + `speak_cognitive_result`.
- Host keyword search cues (non-classified as memory requests) are wrapped at the façade as `What do you remember about {cue}?` — ACM still performs all reconstruction.
- Aria M0 bootstrap (`sys.modules["acm"]` registration) preserved in vendored `acm/__init__.py`.

## Validation

- `tests/test_aria_acm_m0a.py` — promotion + Memory Authority gates  
- Full CI (`scripts/ci_check.py all`) — 450 passed, 1 skipped

## STOP

No additional integration work beyond M0A without explicit approval.
