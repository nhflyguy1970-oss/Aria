# Problem Report — M0D ACM v0.18.1 Promotion

**Milestone:** M0D  
**Status:** Resolved  
**Date:** 2026-07-16

## Summary

Controlled promotion of certified standalone ACM **v0.18.1** (D042 Identity Pipeline
Implementation Correction, including D041 Semantic Extraction) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.18.1` |
| Commit | `137c24a40e6332744b972f6cb726ccb624248e5d` |
| Local copy | `aria-acm-v0.18.1-1` |
| Prior pin | `aria-acm-v0.17.0-1` (M0C / D040) |

## Promoted fixes

- D042 Identity pipeline correction (attribute confidence, schema pollution prevention, structured rendering)
- D041 Semantic Extraction (included in 0.18.0→0.18.1 lineage)
- Prior intact: D038 · D039 · D040

## Integration notes

- No Aria bridge redesign; Cap Bus / `acm_bridge` continue to call existing primary_* façades.
- Encode path consumes vendored Semantic Extraction automatically.
- M0 import bootstrap (`sys.modules["acm"]`) preserved.
- No new Aria cognitive behavior beyond corrected ACM implementation.

## Validation

- `tests/test_aria_acm_m0d.py` (M0D-01..06) — version pin, SE/trace, identity teach→retrieve, persistence, D038–D040 intact, no assistant/user confusion  
- Tree fidelity: only intentional Aria delta vs standalone is M0 `sys.modules["acm"]` bootstrap in `aria_acm/acm/__init__.py`  
- Full CI (`scripts/ci_check.py all`): **490 passed, 1 skipped**

## STOP

No additional implementation beyond M0D without explicit approval.  
Next approved step: rerun Identity Behavioral Validation scenario and verify correct behavior.
