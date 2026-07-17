# Problem Report — M0G ACM v0.19.0 Promotion

**Milestone:** M0G  
**Status:** Resolved  
**Date:** 2026-07-17

## Summary

Controlled promotion of certified standalone ACM **v0.19.0** (D046 Trusted
Memory Ingestion) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.19.0` |
| Commit | `48938bc3c340a427b007527feff256ede34fc61a` |
| Local copy | `aria-acm-v0.19.0-1` |
| Prior pin | `aria-acm-v0.18.4-1` (M0F / D045) |

## Promoted correction

- D046 Trusted Memory Ingestion: explicit actor / host-operation / message-role
  provenance evaluated before Semantic Extraction
- Only trusted user statements, teachings, and corrections are eligible for
  autobiographical encoding
- Tool output, memory-search output, diagnostic output, reflection output,
  system messages, prompt fragments, infrastructure messages, implementation
  metadata, and missing/unknown provenance are rejected fail-closed with zero
  graph mutation
- Source actor, entry operation, message role, and eligibility reason are
  durably recorded in Experience/Concept provenance
- Prior intact: D038 · D039 · D040 · D041 · D042 · D043 · D044 · D045

## Explicitly not promoted / not implemented

Future ACM backlog items remain deferred (teach vs query, evidence intent,
evidence presentation, conflict explanation, read-only diagnostics, preference
editing/correction UX, assistant self-encoding, relationship/projects/goals
subsystems, explainability presentation, etc.).

## Integration notes

- No Aria bridge redesign; Cap Bus / `acm_bridge` continue existing primary_*
  façades.
- M0 import bootstrap (`sys.modules["acm"]`) preserved.
- Only intentional delta vs standalone ACM: Aria M0 `acm` import bootstrap.
- D046 host-contract change: `acm_bridge.encode_from_host`,
  `acm_bridge.primary_remember`, `acm_bridge.primary_correct`, and
  `acm_harvest` now declare explicit trusted user ingestion provenance
  (`TRUSTED_USER_TEACHING` / `TRUSTED_USER_CORRECTION`) because these paths
  carry user-supplied knowledge entering through Aria's memory API. Harvest
  legacy lineage stamping is unchanged.
- Existing D038 contamination gates in M0A/M0B/M0C tests now declare trusted
  provenance so the denylist layer itself remains the layer under test behind
  the D046 trust gate.

## Validation

- `tests/test_aria_acm_m0g.py` — pin, trust model, missing/unknown rejection,
  untrusted-source rejection with zero graph mutation, user knowledge encoding,
  tool-artifact non-contamination, durable source provenance, identity
  regression, preference regression, contamination defense, persistence restart
- Regression M0–M4 / M0A–M0F / CIC / phase7 / phase8 suites
- Full CI (`scripts/ci_check.py all`) — 519 passed, 1 skipped

## STOP

No additional implementation beyond M0G without explicit approval.  
Next approved step: Trusted Memory Ingestion Behavioral Certification.
