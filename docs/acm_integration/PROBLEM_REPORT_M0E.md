# Problem Report — M0E ACM v0.18.3 Promotion

**Milestone:** M0E  
**Status:** Resolved  
**Date:** 2026-07-16

## Summary

Controlled promotion of certified standalone ACM **v0.18.3** (D044 Identity Rendering
Isolation, including D043 Assistant Identity) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.18.3` |
| Commit | `7a695275f6311f3c782e14721892dabfa5b42823` |
| Local copy | `aria-acm-v0.18.3-1` |
| Prior pin | `aria-acm-v0.18.1-1` (M0D / D042) |

## Promoted fixes

- D043 Assistant Identity pipeline (operational profile, schema separation, collision prevention)
- D044 Identity rendering isolation (`isolate_identity_text`, no cross-identity blend)
- Prior intact: D038 · D039 · D040 · D041 · D042

## Integration notes

- No Aria bridge redesign; Cap Bus / `acm_bridge` continue existing primary_* façades.
- M0 import bootstrap (`sys.modules["acm"]`) preserved.
- M0E tests seed assistant operational profile via vendored `AssistantIdentityProfile`.

## Validation

- `tests/test_aria_acm_m0e.py` (M0E-01..08) — pin, modules, identity isolation, persistence  
- Regression M0–M4 / M0A–M0D / CIC suites  
- Full CI (`scripts/ci_check.py all`)

## STOP

No additional implementation beyond M0E without explicit approval.  
Next approved step: final Identity Behavioral Validation and formal certification.
