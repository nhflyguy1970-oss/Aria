# Decision Log — Aria / Jarvis

## A001 — Full cognitive memory replacement via independent ACM copy (2026-07-15)

**Status:** Accepted (design) — implementation gated on blueprint approval  
**Related ACM:** D036 · D037

### Decision

Replace Aria’s existing cognitive memory system entirely with an **independent production copy** of certified ACM, vendored at `jarvis/aria_acm/`.

- Standalone ACM repository remains research/reference only.  
- Not a shared library; not a runtime pip dependency; not auto-synced.  
- Future improvements move only through **explicit promotion**.  
- Legacy cognitive SoTs retire after validated cutover (phases M0–M4).  
- ACM Supremacy Rules 1–6 bind all integration work (see `docs/acm_integration/ARIA_ACM_ARCHITECTURE.md`).

### Consequences

- Cap Bus / MemoryEngine / REST keep stable names where needed; implementations become thin façades into `CognitiveEngine`.  
- Parallel SoTs (CRUD MemoryStore authority, DualWrite CRUD authority, journal-as-memory, etc.) are forbidden as end state.  
- Intentional retirements (hard-delete default, namespace-DBs, silent distill-as-SoT) are approved here with user-visible behavior notes in the matrix.  
- Implementation must not begin until the blueprint package is approved.

### Rejected alternatives

- Shared-library / monorepo runtime coupling to `/media/jeff/AI/ACM`  
- Permanent dual-write legacy + ACM cognition  
- Reshaping ACM to mimic Aria CRUD semantics as the product goal  
- Reimplementing ACM organs inside Aria

---

## A002 — M0 complete: ACM vendored; proceed only with explicit M1 approval (2026-07-15)

**Status:** Accepted  
**Related:** A001 · blueprint M0

### Decision

M0 implementation is complete: certified ACM is vendored at `aria_acm/` (`aria-acm-v0.14.0-1`). Legacy cognitive memory remains authoritative until later milestones. **M1+ must not start without explicit approval.**

### Notes

PR-M0-001 documented and closed via harvest-from-pin (`source_version` 0.14.0 at commit `454dcb90…`).

---

## A003 — M1 complete: Shadow measure; wait for M2 approval (2026-07-15)

**Status:** Accepted  
**Related:** A001 · A002 · blueprint M1

### Decision

M1 Shadow is complete: Cap Bus / Core memory dual-calls vendored ACM for measurement only. **Authoritative cognition remains legacy.** ACM answers are not user-visible. **M2+ must not start without explicit approval.**

### Consequences

- `ARIA_ACM_SHADOW=1` enables dual-call; default remains off for production until operators opt in  
- `ARIA_ACM_PRIMARY` must remain false until M3  
- Mission Control exposes shadow agreement counters without contents

---

## A004 — M2 complete: harvest INTO ACM; wait for M3 approval (2026-07-15)

**Status:** Accepted  
**Related:** A001–A003 · blueprint M2 · DATA_MIGRATION_PLAN

### Decision

M2 harvest is complete: operator-triggered encoding of legacy MemoryStore history into vendored ACM. **Authoritative cognition remains legacy.** **M3+ must not start without explicit approval.**

### Consequences

- Harvest via `python scripts/acm_harvest.py` only — never automatic  
- Idempotent `legacy_id` + `LEGACY_IMPORT` provenance  
- Known revise links only (`revises:<legacy_id>`); unresolved supersedes reported, never invented  
- `ARIA_ACM_PRIMARY` remained false until M3 (opt-in after A005)

---

## A005 — M3 complete: ACM primary opt-in; wait for M4 approval (2026-07-15)

**Status:** Accepted  
**Related:** A001–A004 · blueprint M3 · ROLLBACK_PLAN

### Decision

M3 authority transition is complete for Cap Bus / Core Memory Manager and MemoryEngine memory verbs. When `ARIA_ACM_PRIMARY=true` and `ARIA_ACM_ROLLBACK` is unset, **ACM is authoritative** for remember / recall / search / soft forget / correct / prepare_context. **Default PRIMARY remains false** (not enabled globally). **M4 must not start without explicit approval.**

### Consequences

- Flag precedence: `ROLLBACK` → legacy; else `PRIMARY` → acm; else legacy  
- SUP-02: no legacy MemoryStore writes while PRIMARY  
- Optional `ARIA_ACM_LEGACY_READ_FALLBACK` for empty ACM reads only  
- Soft `cool_memory` / `revise_experience` — no Experience hard-delete  
- Legacy cognitive SoT retirement deferred to M4  
- Operators enable PRIMARY per environment; rollout is controlled, not automatic

---

## A006 — M4 complete: ACM sole cognitive SoT; legacy retirement (2026-07-15)

**Status:** Accepted  
**Related:** A001–A005 · blueprint M4 · REMOVAL_PLAN · LEGACY_RETIREMENT_REPORT

### Decision

M4 is complete. **Vendored ACM is Aria's only cognitive memory implementation.** Legacy MemoryStore / DualWrite / parallel domain writers are retired as cognitive authority. Cap Bus, Core Memory Manager, and MemoryEngine serve ACM. Reintroducing legacy as cognitive primary requires a new DECISION_LOG entry and Supremacy Rule 6 re-certification.

### Consequences

- `ARIA_ACM_PRIMARY` defaults **on**; `ARIA_ACM_LEGACY_READ_FALLBACK` defaults **off**  
- DualWrite wrap is a no-op unless emergency `JARVIS_ALLOW_DUALWRITE_LEGACY` (and never while ACM authoritative)  
- `MemoryStore.add` redirects to ACM encode when authoritative  
- Specialized modules are ACM clients; hierarchy SoT consolidate disabled under PRIMARY  
- CI `acm_supremacy_check` enforces M4 gates  
- Cold vault via operator script; ROLLBACK flag is window-only  
- See `docs/acm_integration/LEGACY_RETIREMENT_REPORT.md`
