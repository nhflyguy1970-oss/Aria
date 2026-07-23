# Production Readiness Audit — ACM & Aria

**Status:** COMPLETE (production-ready with documented host follow-ons)  
**ACM:** v0.45.0  
**Aria pin:** `aria-acm-v0.45.0-1` @ ACM `e6a71fb`  
**Date:** 2026-07-23  
**Scope:** Engineering audit of the practical ACM platform + Aria vendor; refine,
do not redesign.

## Mission outcome

The practical ACM platform (through v0.44.0) was treated as feature-complete.
This audit searched for governance holes, dual-import hazards, persistence
risks, and behavioral gaps. Justified small fixes were implemented and
permanently certified. Larger host UX follow-ons are documented, not redesigned
into ACM.

## Architecture findings

| Finding | Severity | Action |
|---------|----------|--------|
| Nested Aria vendor (`aria_acm.acm` vs `acm`) split class identity | CRITICAL | **Fixed** — MetaPathFinder + alias sync; dual-import regression test |
| Duck-typing in policy gates (pre-existing) | MEDIUM | Retained as defense-in-depth; dual-import now identity-safe |
| PolicyGates duplication / apply_* assent defaults | MEDIUM | Documented; no redesign (backward compatible) |
| Memory Authority / Cognitive Ownership | — | Intact; audit did not introduce host-owned cognition |
| Legacy identity extract (B46) | LOW | Formally retained; research for future parity |

## Behavioral findings

| Finding | Severity | Action |
|---------|----------|--------|
| `assent_identity` mutated attributes without Experience | CRITICAL | **Fixed** — encode + provenance; L34 |
| Read-only diagnostic mode ignored by encode/cool/reactivate | CRITICAL | **Fixed** |
| Soft forget via `cool_memory` from Aria host | INFO | Correct for soft forget; B36 erase/prune UX is ACM-complete, host Cap Bus wiring deferred |
| Identity `auto_revise` on trusted encode | INFO | Intentional for trusted-user path; documented, not removed |
| Adversarial / long-conversation suites | — | Existing behavioral + learning gates retained; audit gates added |

## Dependency findings

| Finding | Action |
|---------|--------|
| No unjustified dependency replacements | None — stdlib SQLite persistence remains correct for determinism |
| Aria embeds ACM (no pip acm required for production path) | Retained |

## Performance findings

| Finding | Severity | Action |
|---------|----------|--------|
| Unbounded SQLite snapshot growth under auto_persist | HIGH | **Fixed** — `max_snapshots` default 32 + prune |
| Full-store scans / O(C×A) activation neighbors | MEDIUM | Documented for post-1.0; no algorithm redesign in audit |
| Aria auto-persist inherits ACM prune | — | Automatic via vendored backend |

## Security & governance findings

| Finding | Severity | Action |
|---------|----------|--------|
| Read-only write spine bypass | CRITICAL | **Fixed** + permanent cert |
| Identity assent without lineage | CRITICAL | **Fixed** + L34 |
| Aria `ARIA_TEACHING_DEBUG` defaulted on | HIGH | **Fixed** — default `"0"` |
| Host `primary_forget` / `primary_correct` use soft cool / revise | MEDIUM | Soft paths are correct; full B20/B36 Cap Bus preview/assent UX deferred |
| Auto-memory stamped `TRUSTED_USER_TEACHING` | MEDIUM | Deferred — requires provenance taxonomy refinement without breaking learning |
| Legal erase / envelope deletion | MEDIUM | Existing B36 policy retained; Experiences never deleted on soft paths |
| No privilege escalation into Memory Authority from host without Cap Bus | — | Unchanged |

## API findings

| Finding | Action |
|---------|--------|
| `CognitiveEngine(..., max_snapshots=)` optional | **Added** (passthrough to durable store) |
| `assent_identity` return shape enriched (`experience_id`, lineage flags) | Compatible extension |
| Aria dual-import public surface unchanged | Shim restored after every vendor |

## Documentation findings

| Finding | Action |
|---------|--------|
| Missing production-audit report | **This document** |
| CHANGELOG / learning cert runner lacked L34 | **Updated** |
| Host Cap Bus B20/B36 wiring not documented as deferred | Covered below |

## Code-quality / debt removed

- Write-spine holes under `read_only()`
- Silent identity assent without Experience
- Unbounded snapshot retention
- Dual-import class-identity split (Aria)
- Teaching debug log noise by default (Aria)

## Technical debt retained (justified)

| Item | Rationale |
|------|-----------|
| Duck-typed policy gates | Defense-in-depth if a third import path appears |
| Legacy identity extract | B46 closed; semantic parity unmet |
| Duplicated PolicyGate patterns | Safe refactor is large; defer |
| Activation neighbor scan cost | Requires measured redesign + cert |

## Recommendations not implemented (with rationale)

1. **Wire Aria Cap Bus to full B20/B36 preview→assent UX** — Large host surface change; ACM already complete; soft cool/revise remain correct defaults for forget/correct. Schedule as Aria host program, not ACM redesign.
2. **Split auto-memory vs user-teaching provenance** — Touches learning weights and certification corpus; defer to dedicated provenance refinement.
3. **Replace SQLite** — No better deterministic, zero-dep alternative justified.
4. **Retire duck-typing** — Keep until dual-import has long soak evidence.
5. **Activation index redesign** — Performance research; not a 1.0 blocker after snapshot prune.

## Bugs discovered → permanently prevented

| Bug | Permanent gate |
|-----|----------------|
| encode under read_only | `test_audit_encode_blocked_under_read_only` |
| cool/reactivate under read_only | `test_audit_cool_and_reactivate_blocked_under_read_only` |
| assent_identity without Experience | `test_audit_assent_identity_births_experience` + L34 |
| snapshot unbounded growth | `test_audit_sqlite_snapshot_prunes` |
| dual-import class split | `tests/test_aria_acm_dual_import.py` |

## Certification totals (this release)

| Suite | Runs | Result |
|-------|------|--------|
| ACM functional (`tests/cognitive`) | ×2 | PASS (419 each) |
| ACM behavioral (`tests/behavioral`) | ×2 | PASS (136 each) |
| ACM learning (`scripts/acm_learning_certification.py` + L34) | ×2 | PASS (107 each) |
| ACM long-duration (`tests/performance` + framework) | ×2 | PASS (20 + 8/8 gates) |
| Aria ACM promotion suite (`tests/test_aria_acm_*.py`) | ×2 | PASS (198 each) |
| Aria dual-import / teaching-debug defaults | covered | PASS |

Framework `certified` flag remains false by design until an explicit 1.0
certification ceremony; all readiness gates passed.

## Final assessment

### ACM
**Production-ready as a cognitive memory engine (v0.45.0).** Governance write spine,
identity assent lineage, and durable snapshot retention meet 1.0 engineering bar
for the practical platform. Remaining items are research, future depth, or host UX.

### Aria
**Production-ready for ACM-as-PRIMARY Soft Memory Authority** with vendored
`aria-acm-v0.45.0-1`, dual-import identity safety, and quieter teaching diagnostics.
Full conversational assent UX for erase/identity at the Cap Bus layer remains a
**host follow-on**, not an ACM defect.

### Production readiness verdict
**Yes — declare ACM + Aria practical 1.0-ready** for the certified scope, with the
explicit caveats listed under recommendations not implemented.
