# Aria ← ACM Integration Blueprint (Complete)

**Status:** M0–M4 COMPLETE — ACM is Aria's sole cognitive SoT  
**Verdict:** Blueprint implemented end-to-end. Further cognition changes need Rule 6 re-certification.  
**Governing policy:** [`ARIA_ACM_ARCHITECTURE.md`](ARIA_ACM_ARCHITECTURE.md) — **ACM SUPREMACY RULES 1–6**  
**ACM decisions:** D036 · D037 · **Aria:** A001–A006 · [Retirement report](LEGACY_RETIREMENT_REPORT.md)

---

## Part index (user brief Parts 1–10)

| Part | Document | Purpose |
|------|----------|---------|
| — | [`ARIA_ACM_ARCHITECTURE.md`](ARIA_ACM_ARCHITECTURE.md) | Independent embedded ACM copy + **Supremacy Rules** + locked path |
| 1 | [`MEMORY_REPLACEMENT_MATRIX.md`](MEMORY_REPLACEMENT_MATRIX.md) | Every capability → MIGRATE / INTERFACE / RETIRE / KEEP-HOST |
| 2 | [`ARIA_ACM_IMPORT_PLAN.md`](ARIA_ACM_IMPORT_PLAN.md) | Vendoring layout, pin, include/exclude, packaging |
| 3 | [`MEMORY_API_MAPPING.md`](MEMORY_API_MAPPING.md) | Host APIs → ACM verbs; field maps; façades only |
| 4 | [`DATA_MIGRATION_PLAN.md`](DATA_MIGRATION_PLAN.md) | Historical data **INTO ACM** only |
| 5–6 | [`MC_AND_TRACE_IMPACT.md`](MC_AND_TRACE_IMPACT.md) | Mission Control / Conversation Trace (impact only) |
| 7 | [`REMOVAL_PLAN.md`](REMOVAL_PLAN.md) | Legacy retirement after validated M3/M4 |
| 8 | [`INTEGRATION_TEST_PLAN.md`](INTEGRATION_TEST_PLAN.md) | Gates including supremacy + quantified SLOs |
| 9 | [`ROLLBACK_PLAN.md`](ROLLBACK_PLAN.md) | Restore legacy authority pre-M4; forensic ACM retain |
| 10 | Aria root `ROADMAP.md` · `PROJECT_HISTORY.md` · `CHANGELOG.md` · `DECISION_LOG.md` | Governance |
| Index | [`MEMORY_REPLACEMENT_BLUEPRINT.md`](MEMORY_REPLACEMENT_BLUEPRINT.md) | Mission, phases M0–M4, verdict |

Flat aliases: `docs/MEMORY_REPLACEMENT_BLUEPRINT.md` → this folder.

---

## Non-negotiables

- Replace Aria cognitive memory **with ACM** — do not make ACM behave like Aria CRUD.  
- One cognitive authority in Aria = vendored ACM (`jarvis/aria_acm/`).  
- Standalone ACM ≠ shared library ≠ auto-sync.  
- No permanent dual cognition · no legacy override · no Aria-reimplemented ACM organs.

## Explicitly out of scope for this blueprint phase

Implementation code · copying ACM into Aria · data migration execution · Aria runtime edits · Mission Control redesign.
