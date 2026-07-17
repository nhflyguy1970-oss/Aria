# Problem Report — M0H ACM v0.20.0 Promotion

**Milestone:** M0H  
**Status:** Resolved  
**Date:** 2026-07-17

## Summary

Controlled promotion of certified standalone ACM **v0.20.0** (D047 Legacy
Memory Contamination Cleanup) into Aria `aria_acm/`.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.20.0` |
| Commit | `b996fe8128c8104c4f1a7a0e633f8b28087a780d` |
| Local copy | `aria-acm-v0.20.0-1` |
| Prior pin | `aria-acm-v0.19.0-1` (M0G / D046) |

## Promoted correction

- D047 one-time legacy contamination cleanup
  (`cleanup_legacy_contamination`, engine entry point + provenance module)
- Legacy provenance evaluation: D046-era records with ineligible recorded
  sources removed fail-closed; pre-D046 external encodes removed only on
  affirmative non-user artifact signatures (tool, memory-search, diagnostic,
  reflection, system, prompt, infrastructure, metadata)
- Safe removal cascade: contaminated Experiences, solely-derived Concepts,
  contaminated attributes, orphaned associations / hierarchy edges /
  working-memory entries, and provenance of removed artifacts
- Restoration of legitimate attributes superseded by contaminated encodes
  (probe-yellow → blue)
- Idempotent migration behavior (checksum-equal no-op on clean graphs)
- Prior intact: D038 · D039 · D040 · D041 · D042 · D043 · D044 · D045 · D046

## Host integration (upgrade path)

`aria_core.acm_bridge.get_engine()` runs the migration exactly once per
durable store: after engine creation, `_maybe_run_legacy_cleanup` executes
`cleanup_legacy_contamination()` unless a completion marker
(`<persist>.d047_cleanup.json`) already exists, then records the report in
the marker. Already-migrated stores are never processed again;
`legacy_cleanup_report()` exposes the recorded result.

**Production store execution:** `data/acm/cognitive.db` was migrated during
validation — report `clean: true`, 21 experiences examined, **0 removals**
(the store was already a clean post-Reset-v1, D046-gated baseline). Marker
recorded; no further runs.

## Explicitly not promoted / not implemented

Future ACM backlog items remain deferred (teach vs query, evidence intent,
explainability, read-only diagnostics, assistant self-encoding,
relationship/goals/projects subsystems, user editing workflows, etc.).
Trusted Memory Ingestion (D046) is unmodified.

## Integration notes

- No Aria bridge redesign; the only host change is the one-time upgrade hook
  in `get_engine()` plus `legacy_cleanup_report()`.
- M0 import bootstrap (`sys.modules["acm"]`) preserved.
- Only intentional delta vs standalone ACM: Aria M0 `acm` import bootstrap.
- Test fixture `tests/fixtures/pre_d046_contaminated_snapshot.json` copied
  verbatim from ACM `v0.20.0` (genuine v0.18.4-generated contaminated graph).

## Validation

- `tests/test_aria_acm_m0h.py` (M0H-01..12) — pin, vendored migration,
  pre-cleanup contaminated recall, artifact removal with preservation of
  Jeff / blue / Sarah / journal memories, blue restoration, identity
  regression, idempotency, upgrade-path run-once + marker, clean-store no-op,
  D046 rejection matrix post-cleanup, injection resistance, host teach/recall
  regression
- Regression M0–M4 / M0A–M0G / CIC / phase7 / phase8 suites
- Full CI (`scripts/ci_check.py all`) — 531 passed, 1 skipped

## STOP

No additional implementation beyond M0H without explicit approval.  
Next approved step: Legacy Memory Cleanup Behavioral Certification.
