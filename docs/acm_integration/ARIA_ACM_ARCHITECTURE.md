# Aria ACM Architecture — Independent Embedded Copy

**Status:** DESIGN FREEZE — no implementation  
**Date:** 2026-07-15  
**Companions:** [`MEMORY_REPLACEMENT_BLUEPRINT.md`](MEMORY_REPLACEMENT_BLUEPRINT.md) · ACM `docs/DECISION_LOG.md` (D036–D037)  
**Aria decisions:** [`DECISION_LOG.md`](../../DECISION_LOG.md) (A001)

---

## Architectural decision

Aria performs a **full cognitive memory replacement**.

| Role | Reality after import |
|------|----------------------|
| **Aria Cognitive Memory** | Permanently independent **source copy** of certified ACM, vendored inside Aria at `jarvis/aria_acm/` |
| **Standalone ACM repo** (`/media/jeff/AI/ACM`) | Research / reference implementation only |
| **Relationship** | **Not** a pip/runtime dependency · **Not** a shared library · **Not** auto-synced |

Promotion path (only):

```text
Standalone ACM (reference)  --explicit promotion PR-->  jarvis/aria_acm/
```

Never automatic. Never bidirectional sync. Never runtime “import from sibling clone.”

### Purpose of this replacement

Replace Aria’s cognitive memory **with ACM**.  
**Do not** reshape ACM to imitate Aria’s old CRUD memory.  
Legacy surfaces become **thin translation façades into ACM** (temporary) or **retire**.

---

## Locked import identity (design freeze)

| Decision | Value |
|----------|-------|
| Vendored root | `jarvis/aria_acm/` (**chosen** — not `jarvis/vendor/acm/`, not `aria/acm/`) |
| Python import | `from aria_acm.acm import …` / `from aria_acm.acm.api.engine import CognitiveEngine` |
| Package layout | `aria_acm/acm/` = literal copy of ACM package `acm/` |
| Bridge (future) | `aria_core/acm_bridge.py` — thin façades only |
| Baseline pin | ACM tag `v0.14.0`, commit `454dcb90a352a3f1daa44aa95ff7b2801994f4e3`, project version `0.14.1` |

See [`ARIA_ACM_IMPORT_PLAN.md`](ARIA_ACM_IMPORT_PLAN.md) for include/exclude file lists.

---

## ACM SUPREMACY RULES (first-class policy)

These rules govern every matrix row, API mapping, migration step, test, and rollback option.  
Violations are architectural defects — not optional preferences.

### Rule 1 — Single Cognitive Authority

Aria contains **exactly one** cognitive memory implementation after cutover: the vendored ACM copy.

- No dual SoTs.  
- No “legacy authoritative forever.” Dual-write/Shadow may exist only as a **measured migration phase**, then ends.  
- Cap Bus / behaviors / Mission Control / Trace consume ACM cognition only after cutover.

### Rule 2 — No Lost Functionality

Every current Aria memory capability must be mapped to one of:

1. **Migrate into ACM** (Experiences / Concepts / Associations / Identity / Learning / …), or  
2. **Interface to ACM** (host UI, Cap Bus verb, MC panel calling ACM observables), or  
3. **Intentional retirement** — written approval + user-visible note (see DECISION_LOG).

No capability may vanish by omission.

### Rule 3 — No Legacy Overrides

After cutover, legacy memory code must **not**:

- replace ACM verbs  
- override ACM organs  
- bypass ACM for cognitive recall/encode  
- duplicate ACM cognitive results as a parallel truth  
- intercept ACM output to substitute “Aria-style” fabricated memory  

Temporary API façades may **only** translate host call shapes → ACM public API.

### Rule 4 — No Duplicate Cognition

Aria must **never** re-implement ACM cognitive organs or capabilities:

Identity · Experiences · Concepts · Associations · Remembering · Reflection · Learning · Offline Cognition · Attention · Accessibility · Prediction · Simulation · Recombination · Analogy · Reconciliation · Confidence / Uncertainty · Activation Architecture

Aria may own: routing, Cap Bus, UI, Mission Control presentation, conversation packaging, non-memory applications, **Learning Manager coordination** (propose/assent orchestration that calls ACM — not a parallel Learning organ).

### Rule 5 — Migration Direction (INTO ACM only)

Cognitive features move **into ACM** only.

| If… | Then… |
|-----|--------|
| Cognitive gap found in Aria needs | Implement in **standalone ACM** → certify → **promote** into Aria copy |
| Non-cognitive host need | Remain in Aria (UI / orchestration / IO) |
| Temptation to “just patch Aria memory” | **Forbidden** — violates Rules 1, 3, 4 |

### Rule 6 — Architectural Regression Prohibited

Moving cognition **from ACM back into Aria** (rebuilding legacy organs beside ACM) is forbidden without:

1. Explicit project approval, and  
2. Re-certification of ACM / Aria memory posture.

“Temporary forever” parallel cognition is a regression.

---

## Runtime shape (target)

```text
┌─────────────────────────────────────────────────────────────┐
│ Aria host: Cap Bus · Router · Behaviors · Mission Control   │
│ Conversation Trace · Learning Managers (propose only)       │
└────────────────────────────┬────────────────────────────────┘
                             │ thin translation façades only
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ jarvis/aria_acm/acm/   (VENDORED — Aria Cognitive Memory)   │
│ CognitiveEngine · CognitiveStore · organs · ValidationHarness│
└─────────────────────────────────────────────────────────────┘

Standalone /media/jeff/AI/ACM  ←──── explicit promotion only ────┘
(research & reference; never imported at Aria runtime)
```

---

## Parallel-SoT disposition (locked)

| Current parallel surface | End-state disposition |
|--------------------------|----------------------|
| `jarvis.modules.memory` JSON/SQLite | Retire as cognitive SoT after M4 |
| AI-Platform DualWrite CRUD mirror | Retire as cognitive authority; optional ACM **projection** export only |
| `personalization/preferences.json` | Usage telemetry KEEP-HOST; autobiographical prefs MIGRATE INTO ACM |
| `relationship_graph.db` | Relationship **facts** MIGRATE INTO ACM Concepts/Associations; graph DB not cognitive SoT after M4 (may KEEP-HOST as non-authoritative viz if projections-only) |
| Bullet Journal files | KEEP-HOST product store; cognitive residue only via ACM `encode` |
| Vector / embedding DBs | Activation assist plugin only — never memory SoT |
| Chat transcripts (`chat_branches.json`) | KEEP-HOST conversation packaging — not autobiographical SoT |
| Agent identity (`aria_core.identity` / config) | KEEP-HOST agent config; user identity memories MIGRATE INTO ACM Identity |

---

## Learning organ maturity (acceptance gate, not dual cognition)

ACM exposes `learn` / `assent_adaptation` / `rollback_adaptation` on `CognitiveEngine`. Aria Learning Manager becomes a **host coordinator** that only calls those verbs (plus `encode` / `reflect_on` / `sleep`).  
If ACM Learning organ maturity is insufficient at M3, **do not** rebuild Learning in Aria — delay Learning cutover behind Shadow/propose gates and promote ACM improvements (Rule 5). Autobiographical encode/recall must still cut over on ACM.

---

## Relationship to ACM Phase 2 adapter

ACM packaged `aria_memory_adapter` remains a **reference design** for verb translation and Shadow measurement.

Inside Aria:

- Build a **vendored** translation façade (`aria_core/acm_bridge.py`), informed by the adapter reference.  
- Do **not** copy `aria_memory_adapter/` into the runtime tree as a second adapter.  
- Shadow is a **migration phase**, not the end state (Rule 1).

See ACM D036 / D037.

---

## Versioning of the Aria copy

| Field | Practice |
|-------|----------|
| Provenance | `aria_acm/VERSION.json`: source tag, commit, copy date, tree hash |
| License | Preserve Apache-2.0 headers + root `LICENSE` / `NOTICE` |
| Local version | Aria may stamp `aria-acm-<source>-N` for fork commits inside Aria |
| Sync | **Manual promotion only** |

---

## Non-goals of this document

Implementation · data migration execution · Mission Control redesign · LLM as memory · shared library packaging.
