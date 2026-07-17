# Problem Report — M0J ACM v0.22.0 Promotion

**Milestone:** M0J  
**Status:** Resolved  
**Date:** 2026-07-17

## Summary

Controlled promotion of certified standalone ACM **v0.22.0** (Teaching
Recognition — valid preference teaching regression corrected) into Aria
`aria_acm/`. Promotion only — no ACM or Aria redesign. Teaching Recognition
is integrated exactly as released in the standalone reference implementation.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.22.0` |
| Commit | `2dd3715c211f1fdc5e1147dccf9c827be5af801b` |
| Local copy | `aria-acm-v0.22.0-1` |
| Prior pin | `aria-acm-v0.21.0-1` (M0I / Preference Certification) |
| Tree SHA-256 | `22e8218100c4fbc2b54c1ab95863a23cb1bafbeda84bea317398205d24ef2f64` |

## Live blocker corrected (standalone v0.22.0)

After M0I, Preference certification still failed on a *valid* teaching:

> "My favorite color is green." → "What is my favorite color?" → "blue"

Invalid teachings (tool wrappers, questions) were correctly rejected. The
defect was that declarative teachings spoke through Memory Authority
(`cognitive_respond`) were dispatched as *retrievals* and never encoded.
Standalone ACM v0.22.0 adds Teaching Recognition: declarative,
non-interrogative requests with extracted cognitive facts are encoded
(through the full D046 trust gate and content-level artifact protection)
before dispatch.

## Promoted surfaces

- `acm/authority/teaching.py` — `detect_teaching`
- `acm/authority/pipeline.py` — `_teach_if_declarative` before dispatch
- Reasoning path markers: `teaching_detected` / `teaching_encoded` /
  `teaching_rejected:<reason>`

No host bridge redesign. `primary_cognitive_respond` /
`primary_cognitive_speak` already call vendored `cognitive_respond`, so
Teaching Recognition is active for conversational Memory Authority paths
without Aria code changes beyond the vendored tree and promotion metadata.

## Verification

| Check | Result |
|-------|--------|
| Version / tag / commit pin | Match v0.22.0 / `2dd3715…` |
| Tree checksum | Matches `VERSION.json` |
| No mixed versions | `_version.py` = 0.22.0 only |
| No local cognition mods | Tree matches source except Aria import bootstrap |
| Host independence | Teaching module classifies without Aria/host imports |
| blue → green via `cognitive_respond` | Green; blue retired |
| Evidence | Teaching history; no mutation |
| Restart | Green preserved |
| Artifacts / interrogatives | Non-teaching |
| Identity + D046 regression | Pass |
| Prior M0I / M0H lineage gates | Pass |

## Validation

- `tests/test_aria_acm_m0j.py` (M0J-01..07)
- M0I pin test converted to lineage form (same pattern as earlier promotions)
- Full CI (`scripts/ci_check.py all`)

## STOP

No additional implementation beyond M0J without explicit approval.
