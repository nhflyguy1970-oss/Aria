# Problem Report — M0K ACM v0.23.0 Promotion

**Milestone:** M0K  
**Status:** Resolved  
**Date:** 2026-07-17

## Summary

Controlled promotion of certified standalone ACM **v0.23.0** (multi-domain
preference isolation + evidence lineage) into Aria `aria_acm/`. Corrects live
manual certification failures discovered through the conversational interface.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.23.0` |
| Commit | `82a9499103314d57d9c8291e2f3886921281f49c` |
| Local copy | `aria-acm-v0.23.0-1` |
| Prior pin | `aria-acm-v0.22.0-1` (M0J / Teaching Recognition) |

## Live failures corrected

1. **Evidence** — after color updates blue→…→black, `Show me the evidence.`
   returned unknown / no_reliable_reconstruction.
2. **Domain collapse** — teaching/querying favorite food or fish answered with
   favorite color (or conflicted across domains).
3. **Cross-domain overwrite risk** — shared `favorite` token made every
   `favorite_*` attribute answerable for every preference cue.

## Promoted corrections (standalone v0.23.0)

- Cue tokens strip punctuation; favorite-domain extraction stops at the domain
  noun (`My favorite food is pizza.` → domain `food`).
- Remembering answerability requires the named domain for `favorite_*` keys;
  `color`/`colour` normalize as one domain.
- Evidence cues classify as remembering ahead of preference; Remembering
  reconstructs attribute version lineage (active/retired + teaching text)
  read-only (no reconsolidation).

## Host integration

No Aria redesign. Teaching Recognition routing fix (declarative → Memory
Authority with full prompt) remains. Vendored ACM provides domain isolation
and evidence reconstruction.

## Validation

- `tests/test_aria_acm_m0k.py` (M0K-01..05) — pin, definition-of-done conversation,
  cross-domain isolation, restart, teaching-response domain match
- Prior M0J/M0I lineage gates green
- Full CI (`scripts/ci_check.py all`)

## STOP

No additional implementation beyond M0K without explicit approval.
