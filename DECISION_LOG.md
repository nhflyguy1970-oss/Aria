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

---

## A007 — M0A complete: promote ACM v0.15.0 Memory Authority (2026-07-15)

**Status:** Accepted  
**Related:** A001–A006 · standalone ACM D038 · tag `v0.15.0` · commit `b78a857…`

### Decision

M0A promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.15.0** (`aria-acm-v0.15.0-1`). Memory requests in Aria route through the Memory Authority pipeline (`classify_request` → ACM reconstruction → `CognitiveMemoryResult` → faithful `speak_cognitive_result`). Aria does not reconstruct, supplement, or invent cognitive memory.

### Consequences

- Embedded pin: tag `v0.15.0`, commit `b78a85747291b024252ddf3e5baafe5247f5ff5d`  
- `aria_core/acm_bridge.py` exposes `primary_cognitive_respond` / `primary_cognitive_speak`  
- Host search cues translate to memory-request text at the façade only (`_memory_request_for_search`)  
- Encode protection (`llm_generated`, speech contamination) active in vendored ACM  
- **STOP** — no further integration milestones without explicit approval

---

## A008 — M0B complete: promote ACM v0.16.0 Cognitive Intent Classification (2026-07-15)

**Status:** Accepted  
**Related:** A001–A007 · standalone ACM D039 · tag `v0.16.0` · commit `6f6d0f89…`

### Decision

M0B promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.16.0** (`aria-acm-v0.16.0-1`). Cognitive Intent Classification and Cognitive Routing are active. Memory requests route through `classify_request` → `route_request` → owning organs → `CognitiveMemoryResult` → `speak_cognitive_result`. Aria does not determine cognitive ownership, invent memory, or alter ACM results. Memory Authority (D038 / A007) remains intact.

### Consequences

- Embedded pin: tag `v0.16.0`, commit `6f6d0f89d0af35b018c2a781a38748d21e303ae0`  
- `aria_core/acm_bridge.py` exposes `primary_route_request`  
- Assistant vs user identity routing active  
- Goal / project / reflection / learning / association ownership via ACM  
- Uncertain self-referent classifications remain cognitive-conservative  
- **STOP** — no further implementation without explicit approval; next approved step is Daily Use Test 1 comparison

---

## A009 — M0C complete: promote ACM v0.17.0 End-to-End Cognitive Dispatch (2026-07-15)

**Status:** Accepted  
**Related:** A001–A008 · standalone ACM D040 · tag `v0.17.0` · commit `af108d08…`

### Decision

M0C promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.17.0** (`aria-acm-v0.17.0-1`). End-to-End Cognitive Dispatch is active. Memory requests route through `classify_request` → `route_request` → `dispatch_request` → owning organs → `CognitiveMemoryResult` → `speak_cognitive_result`. Aria does not determine ownership, perform dispatch, invent memory, or terminate cognition in infrastructure. D038 Memory Authority and D039 Intent Classification remain intact.

### Consequences

- Embedded pin: tag `v0.17.0`, commit `af108d0893c7aee11f21f96fba51e8641f219ae2`  
- `aria_core/acm_bridge.py` exposes `primary_dispatch_request`  
- Diagnostics expose `terminated_at`, ownership, dispatch path  
- Organ-only termination enforced by vendored ACM  
- **STOP** — no further implementation without explicit approval; next approved step is Daily Use Test 1 comparison

---

## A010 — Cognitive Infrastructure Conversion complete (2026-07-15)

**Status:** Accepted  
**Related:** A001–A009 · embedded ACM v0.17.0 (D038–D040)

### Decision

Final Aria cognitive infrastructure conversion is complete. Embedded ACM is the sole cognitive memory implementation. Every cognitive capability under PRIMARY depends only on ACM (bridge + store façades). Mission Control Memory panel is an ACM Cognitive Dashboard. Conversation Trace reports ACM cognition (`memory_operation.v3`). Standalone ACM repository was not modified.

### Consequences

- Store façades: `aria_core/acm_store_facade.py`  
- Dashboard: `acm_bridge.acm_dashboard` via `mission_control_panel`  
- Trace: intent / owner / dispatch / termination / confidence / provenance  
- Legacy JSON/SQLite retained as vault + ROLLBACK only  
- CIC-01..06 gates; docs package under `docs/`  
- **STOP** — wait for approval before further implementation; authentic Daily Use Test 1 still gated on explicit approval

---

## A011 — Cognitive Memory Reset v1: clean post-D041 autobiographical baseline (2026-07-16)

**Status:** Accepted  
**Related:** A001–A010 · standalone ACM D038–D041

### Decision

Aria’s embedded ACM durable autobiographical store is archived as **Pre-D041 Behavioral Validation** (contaminated identity; research only) and replaced with an **empty** live `cognitive.db`. ACM architecture, organs, code, configuration, documentation, and tests are unchanged. Standalone ACM is not modified. No new autobiographical teaching until explicit approval.

### Consequences

- Archive: `data/acm/archives/pre_d041_behavioral_validation_20260716T125819Z/` (gitignored data)  
- Operator: `scripts/acm_cognitive_memory_reset.py`  
- Doc: `docs/COGNITIVE_MEMORY_RESET_v1.md`  
- Official clean behavioral baseline for future memory formation  
- **STOP** — wait for approval before teaching Aria any new memories
