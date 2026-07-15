# Memory Replacement Blueprint — Aria ← ACM Copy

**Status:** APPROVED / LOCKED — implementation in progress by milestone  
**Date:** 2026-07-15  
**M0:** Complete (`aria_acm/` · `aria-acm-v0.14.0-1`)  
**M1:** Complete (Shadow · `aria_core/acm_bridge.py` · authoritative=legacy)  
**M2:** Complete (Harvest · `aria_core/acm_harvest.py` · `scripts/acm_harvest.py`)  
**Governing policy:** [`ARIA_ACM_ARCHITECTURE.md`](ARIA_ACM_ARCHITECTURE.md) (**ACM SUPREMACY RULES**)  
**ACM decisions:** D036 · D037  
**Aria decisions:** A001 · A002 · A003 · A004 ([`DECISION_LOG.md`](../../DECISION_LOG.md))

---

## One-sentence mission

Replace every Aria cognitive memory subsystem with an **independent production copy** of certified ACM — without losing functionality, without dual cognition, without making ACM pretend to be CRUD legacy memory.

---

## Supremacy citation (mandatory)

All workstreams obey **ACM SUPREMACY RULES 1–6** in [`ARIA_ACM_ARCHITECTURE.md`](ARIA_ACM_ARCHITECTURE.md):

1. Single Cognitive Authority  
2. No Lost Functionality  
3. No Legacy Overrides  
4. No Duplicate Cognition  
5. Migration Direction INTO ACM only  
6. Architectural Regression Prohibited without re-certification  

Any design that proposes permanent beside-ACM cognition, legacy override, or “Aria reimplements remembering” is **out of blueprint**.

---

## Document set (user Parts 1–10 ↔ files)

| User part | Document |
|-----------|----------|
| Architecture (policy) | [`ARIA_ACM_ARCHITECTURE.md`](ARIA_ACM_ARCHITECTURE.md) |
| 1 Matrix | [`MEMORY_REPLACEMENT_MATRIX.md`](MEMORY_REPLACEMENT_MATRIX.md) |
| 2 Import | [`ARIA_ACM_IMPORT_PLAN.md`](ARIA_ACM_IMPORT_PLAN.md) |
| 3 API | [`MEMORY_API_MAPPING.md`](MEMORY_API_MAPPING.md) |
| 4 Data migration | [`DATA_MIGRATION_PLAN.md`](DATA_MIGRATION_PLAN.md) |
| 5 Mission Control | [`MC_AND_TRACE_IMPACT.md`](MC_AND_TRACE_IMPACT.md) §5 |
| 6 Conversation Trace | [`MC_AND_TRACE_IMPACT.md`](MC_AND_TRACE_IMPACT.md) §6 |
| 7 Removal | [`REMOVAL_PLAN.md`](REMOVAL_PLAN.md) |
| 8 Test strategy | [`INTEGRATION_TEST_PLAN.md`](INTEGRATION_TEST_PLAN.md) |
| 9 Rollback | [`ROLLBACK_PLAN.md`](ROLLBACK_PLAN.md) |
| 10 Meta docs | This blueprint + Aria `ROADMAP.md` / `PROJECT_HISTORY.md` / `CHANGELOG.md` / `DECISION_LOG.md` |

Flat path aliases under `docs/*.md` point here. Index: [`README.md`](README.md).

---

## Locked design decisions (pre-implementation)

| Decision | Value |
|----------|-------|
| Vendored path | `jarvis/aria_acm/` |
| Import namespace | `aria_acm.acm` |
| Baseline pin | ACM `v0.14.0` / commit `454dcb90…` / `0.14.1` |
| Bridge | `aria_core/acm_bridge.py` (later) informed by ACM `aria_memory_adapter` reference — not copied as runtime dual adapter |
| Shadow thresholds | ≥85% (M2), ≥92% (M3); see test plan |
| Latency | p95 ≤ max(1.25×legacy, legacy+150ms) |
| Learning | Host Learning Manager = coordinator only; ACM owns Learning verbs; delay Learning cutover via promote if organ maturity insufficient — **never** rebuild Learning in Aria |
| Prediction/Simulation/Analogy | Available ACM capabilities; product may hide UI; not Daily Use blockers for encode/recall cutover |
| DualWrite | Retire as cognitive authority |

---

## Phased cutover (design)

| Phase | Name | Authoritative cognition | Allowed | Status |
|-------|------|-------------------------|---------|--------|
| M0 | Import copy + build | Legacy | Compile/vendoring only | **Complete** |
| M1 | Shadow measure | **Legacy** | ACM parallel; no user-visible ACM truth | **Complete** |
| M2 | Harvest migrate | Legacy | Encode history INTO ACM | **Complete** |
| M3 | ACM primary | **ACM** | Legacy read fallback optional | Not started |
| M4 | Retire legacy | **ACM only** | Remove bypass paths (Rule 3) | Not started |

Shadow never becomes permanent dual authority (Rule 1).

---

## Certification carry-forward

ACM Operational Certification: **CERTIFIED WITH CONDITIONS** (`ACM` `docs/ACM_CERTIFIED_v1.md`).

Blueprint-mandated acceptance gates before M3:

- Shadow agreement re-measured against **real** Aria legacy recall (closes Condition 1).  
- Absolute latency vs Aria SLOs (test plan).  
- Supremacy checklist signed (no duplicate organs).

---

## Final recommendation (this blueprint)

# READY TO IMPLEMENT

Blueprint is complete: every inventoried capability is mapped; import path/namespace/pin locked; API field maps defined; migration/schema/idempotency specified; MC/Trace impact documented; removal sequenced; tests quantified; rollback steps exact; Aria governance updated (A001).

Implementation must **not** start until this blueprint is **approved**. Certification conditions and Learning-organ maturity become **acceptance tests / promote gates**, not excuses to build parallel cognition.

### Pre-flight (acceptance gates — not blueprint blockers)

- Close ACM cert Condition 1 during Phase M1 Shadow on live Aria.  
- If ACM Learning organ maturity insufficient at M3, keep Learning write path on propose/`encode`/`learn` with delayed assent promote — do not reimplement Learning in Aria.  
- Confirm packaging discovery with maintainers during M0.

### Would force NOT READY / redesign

- Plans that keep forever-dual memory SoTs.  
- Plans that reimplement ACM organs in Aria.  
- Plans that reshape ACM into Aria CRUD semantics as the goal.  
- Starting implementation before blueprint approval.
