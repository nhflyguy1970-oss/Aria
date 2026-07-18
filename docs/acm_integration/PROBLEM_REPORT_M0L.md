# Problem Report — M0L ACM v0.24.0 Promotion

**Milestone:** M0L  
**Status:** Resolved  
**Date:** 2026-07-17

## Summary

Controlled promotion of certified standalone ACM **v0.24.0** (memory
explanation + active-only personal summary) into Aria `aria_acm/`. Corrects
the final live M0K manual validation failures: explanation-style queries and
personal summary through the Aria routing path.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.24.0` |
| Commit | `3c3bdbc0b1e7566da7922df422c72578e5550df5` |
| Local copy | `aria-acm-v0.24.0-1` |
| Prior pin | `aria-acm-v0.23.0-1` (M0K / multi-domain + evidence) |

## Root causes

1. **Explanation routing (Aria host)** — Why-questions about preferences matched
   NLU `knowledge`/`web_search` plus `_LIVE_STATE` (`my`) and were forced to
   Mission Control (`runtime`).
2. **Explanation classification (ACM)** — `Why isn't blue active?` /
   `What replaced pizza?` / `Why is brown trout active?` were not remembering
   cues, so lineage never reconstructed.
3. **Personal summary (ACM)** — `What do you know about me?` did not assemble
   active identity + preference attributes from certified evidence.

## Corrections (no ACM redesign)

### Host (Aria)

- `_USER_MEMORY` / `resolve_memory_route` / `apply_intent_guards`: autobiographical
  why/replaced/active cues → `memory` / `memory_about_user` with full prompt.
- `runtime_routing._USER_MEMORY_EXCLUDE`: same cues never Mission Control.

### Vendored ACM v0.24.0

- `memory_explanation_cue` classification ahead of preference.
- Remembering: lineage explanations (why favorite / why not active / what
  replaced / why active) and active-only personal summary; read-only.

## Validation

- `tests/test_aria_acm_m0l.py` — pin, full Aria NLU→Memory Authority path,
  definition-of-done conversation, multi-domain explanation, active-only summary
- Prior M0K lineage gates green
- Full CI (`scripts/ci_check.py all`)

## STOP

No additional implementation beyond M0L without explicit approval.
