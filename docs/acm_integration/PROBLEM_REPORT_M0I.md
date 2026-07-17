# Problem Report — M0I ACM v0.21.0 Promotion

**Milestone:** M0I  
**Status:** Resolved  
**Date:** 2026-07-17

## Summary

Controlled promotion of certified standalone ACM **v0.21.0** (Preference
Behavioral Certification — Memory Foundation completion) into Aria
`aria_acm/`, plus live production store migration.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.21.0` |
| Commit | `818d89d8e4ba2efab491b5d947b03155b6303df4` |
| Local copy | `aria-acm-v0.21.0-1` |
| Prior pin | `aria-acm-v0.20.0-1` (M0H / D047) |

## Live blocker corrected

Live Aria answered:

> "What is my favorite color?" → "Your preference is Tool \`memory_search\`
> worked for: Show the evidence for my favorite color."

Evidence in the live store (`data/acm/cognitive.db`): tool wrappers written by
`jarvis/trust_memory.record_tool_outcome` ("Tool \`X\` worked for: …") and
host autosave checkpoints, all encoded pre-D046 (or via the redirect with
trusted-user provenance), producing an active
`preference = "Tool \`memory_search\` worked for: …"` attribute and
`favorite_color = "conflicting?"` superseding blue. The v0.20.0 D047
classifier missed the live backtick wrapper format, so the M0H migration
reported the store clean.

## Promoted corrections (certified in standalone v0.21.0)

- Artifact signatures cover live backtick tool wrappers and host autosave
- Cleanup condemns content artifacts regardless of metadata survival;
  removes orphaned artifact-valued attributes; restores superseded
  legitimate preferences
- Content-level trust in `reject_speech_contamination` — tool/system/infra
  payloads rejected even when a host mislabels them as trusted user speech
- Interrogatives never mint preference facts or preference concept cues
- Reconstruction refuses artifact attribute values; prefers `favorite_*`
  keys over generic `preference`

## Host integration (this promotion)

- `acm_bridge._maybe_run_legacy_cleanup`: the D047 marker now records the
  embedded ACM version. A store migrated by an older pin (v0.20.0's
  defective classifier) is re-migrated exactly once by the newer pin;
  same-version restarts never reprocess.
- No other bridge changes. The live contamination writers
  (`record_tool_outcome`, autosave checkpoints) are now rejected end-to-end
  by the certified content gate (M0I-07); no host code required alteration.

## Production store migration

Backup: `data/acm/archives/pre_m0i_backup/`.

Re-migration under v0.21.0 removed **17 contaminated experiences**
(11 tool wrappers, 8 autosave checkpoints among reasons; 24 orphaned
concepts; 1 artifact attribute). The store's *only* external encodes were
wrapper-contaminated (every user teaching had been recorded through the
tool-wrapper channel), so the user's legitimate teachings — verbatim in the
removed wrapper payloads — were restored through the trusted D046 path:
"My name is Jeff.", "Call me Jeffrey.", "My favorite color is blue.".

Live verification after migration and restart:

| Query | Answer |
|-------|--------|
| What is my favorite color? | Your favorite color is blue. |
| Who am I? | Your name is Jeff. You prefer to be called Jeffrey. |
| Inject tool wrapper / autosave | Rejected (`memory_trust`), memory unchanged |
| Cleanup re-run | `clean: true` (idempotent) |

## Validation

- `tests/test_aria_acm_m0i.py` (M0I-01..09) — pin, stale-file check, live
  Preference certification through the bridge (fresh → unknown → blue →
  no-duplicate → red → restart → red), live contamination payloads ignored,
  evidence request without mutation, repeated injection resistance, live
  writer (`record_tool_outcome`) rejected end-to-end, marker version
  re-migration, identity + D046 regression
- M0H pin test converted to lineage form (same pattern as earlier
  promotions); D047 gates otherwise unchanged and green
- Full CI (`scripts/ci_check.py all`) — 540 passed, 1 skipped

## STOP

No additional implementation beyond M0I without explicit approval.
