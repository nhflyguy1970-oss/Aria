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
