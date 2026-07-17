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

---

## A012 — M0D complete: promote ACM v0.18.1 Identity Pipeline Correction (2026-07-16)

**Status:** Accepted  
**Related:** A001–A011 · standalone ACM D042 (includes D041) · tag `v0.18.1` · commit `137c24a…`

### Decision

M0D promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.18.1** (`aria-acm-v0.18.1-1`). Identity formation/retrieval/confidence/rendering corrections are active. Semantic Extraction (D041) is included. Cap Bus / Core continue to use existing ACM façades without bridge redesign. D038–D040 remain intact.

### Consequences

- Embedded pin: tag `v0.18.1`, commit `137c24a40e6332744b972f6cb726ccb624248e5d`  
- Local copy: `aria-acm-v0.18.1-1`  
- Problem report: `docs/acm_integration/PROBLEM_REPORT_M0D.md`  
- Gates: `tests/test_aria_acm_m0d.py`  
- **STOP** — wait for approval; next approved step is Identity Behavioral Validation rerun

---

## A013 — M0E complete: promote ACM v0.18.3 Identity Rendering Isolation (2026-07-16)

**Status:** Accepted  
**Related:** A001–A012 · standalone ACM D044 (includes D043) · tag `v0.18.3` · commit `7a69527…`

### Decision

M0E promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.18.3** (`aria-acm-v0.18.3-1`). Assistant and User identity rendering are fully isolated. D043 Assistant Identity and D044 rendering isolation are active. Cap Bus / Core continue to use existing ACM façades without bridge redesign. D038–D042 remain intact.

### Consequences

- Embedded pin: tag `v0.18.3`, commit `7a695275f6311f3c782e14721892dabfa5b42823`  
- Local copy: `aria-acm-v0.18.3-1`  
- Problem report: `docs/acm_integration/PROBLEM_REPORT_M0E.md`  
- Gates: `tests/test_aria_acm_m0e.py`  
- **STOP** — wait for approval; next step is final Identity Behavioral Validation

---

## A014 — M0F complete: promote ACM v0.18.4 Preference Reconstruction Fix (2026-07-17)

**Status:** Accepted  
**Related:** A001–A013 · standalone ACM D045 · tag `v0.18.4` · commit `3023ed8…`

### Decision

M0F promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.18.4** (`aria-acm-v0.18.4-1`). Preference reconstruction competitor admissibility (D045) is active. Artificial `competing_recollections` from lexical support concepts is eliminated; true semantic preference conflicts remain. Cap Bus / Core continue to use existing ACM façades without bridge redesign. D038–D044 remain intact. No future ACM backlog items were implemented.

### Consequences

- Embedded pin: tag `v0.18.4`, commit `3023ed85b1de5a9b19c5058509f1fda870f45555`  
- Local copy: `aria-acm-v0.18.4-1`  
- Problem report: `docs/acm_integration/PROBLEM_REPORT_M0F.md`  
- Gates: `tests/test_aria_acm_m0f.py`  
- **STOP** — wait for approval; next step is Preference Behavioral Certification

---

## A015 — M0G complete: promote ACM v0.19.0 Trusted Memory Ingestion (2026-07-17)

**Status:** Accepted  
**Related:** A001–A014 · standalone ACM D046 · tag `v0.19.0` · commit `48938bc…`

### Decision

M0G promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.19.0** (`aria-acm-v0.19.0-1`). Trusted Memory Ingestion (D046) is active: every external encode carries explicit actor / host-operation / message-role provenance evaluated before Semantic Extraction. Only trusted user statements, teachings, and corrections are eligible; tool output, memory-search output, diagnostic output, reflection output, system messages, infrastructure messages, implementation metadata, and unknown provenance are rejected fail-closed with zero graph mutation. Aria's host write paths (`acm_bridge.encode_from_host`, `acm_bridge.primary_remember`, `acm_bridge.primary_correct`, `acm_harvest`) declare trusted user provenance because they carry user-supplied knowledge through Aria's memory API. Source eligibility persists in Experience/Concept provenance. D038–D045 remain intact. No future ACM backlog items were implemented.

### Consequences

- Embedded pin: tag `v0.19.0`, commit `48938bc3c340a427b007527feff256ede34fc61a`  
- Local copy: `aria-acm-v0.19.0-1`  
- Problem report: `docs/acm_integration/PROBLEM_REPORT_M0G.md`  
- Gates: `tests/test_aria_acm_m0g.py`  
- **STOP** — wait for approval; next step is Trusted Memory Ingestion Behavioral Certification

---

## A016 — M0H complete: promote ACM v0.20.0 Legacy Memory Contamination Cleanup (2026-07-17)

**Status:** Accepted  
**Related:** A001–A015 · standalone ACM D047 · tag `v0.20.0` · commit `b996fe8…`

### Decision

M0H promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.20.0** (`aria-acm-v0.20.0-1`). Legacy Memory Contamination Cleanup (D047) is available and wired into Aria's upgrade path: `acm_bridge.get_engine` runs `cleanup_legacy_contamination()` exactly once per durable store, recording the report in a `<persist>.d047_cleanup.json` completion marker so already-migrated stores are never processed again. The migration removes pre-D046 contaminated memories — D046-era records whose recorded sources are ineligible, and pre-D046 external encodes matching non-user artifact signatures (tool, memory-search, diagnostic, reflection, system, prompt, infrastructure, metadata) — together with solely-derived concepts, contaminated attributes, orphaned associations, hierarchy edges, working-memory entries, and provenance of removed artifacts, and reactivates legitimate attributes the artifacts superseded. It is idempotent and checksum-neutral on clean graphs. Aria's production store was verified already clean (21 experiences examined, 0 removals). D046 Trusted Memory Ingestion is unchanged; D038–D045 remain intact. No future ACM backlog items were implemented.

### Consequences

- Embedded pin: tag `v0.20.0`, commit `b996fe8128c8104c4f1a7a0e633f8b28087a780d`  
- Local copy: `aria-acm-v0.20.0-1`  
- Problem report: `docs/acm_integration/PROBLEM_REPORT_M0H.md`  
- Gates: `tests/test_aria_acm_m0h.py`  
- **STOP** — wait for approval; next step is Legacy Memory Cleanup Behavioral Certification

---

## A017 — MILESTONE: Memory Foundation v1.0 behaviorally certified (2026-07-17)

**Status:** Accepted  
**Related:** A001–A016 · standalone ACM D038–D047 · embedded `aria-acm-v0.20.0-1`

### Decision

Memory Foundation v1.0 is formally certified as the project's first major cognitive milestone. The core autobiographical memory system — Memory Authority (D038), Intent Classification (D039), Cognitive Dispatch (D040), Semantic Extraction (D041), User Identity (D042), Assistant Identity (D043), Identity Rendering Isolation (D044), Preference Reconstruction (D045), Trusted Memory Ingestion (D046), and Legacy Memory Contamination Cleanup (D047) — is behaviorally certified and serves as the stable platform for all future cognitive development. Each capability was certified in the standalone ACM reference implementation first and promoted into Aria through the controlled lineage M0A→M0B→M0C→M0D→M0E→M0F→M0G→M0H, each promotion gated by behavioral validation, regression, integration, performance, CI, GitHub verification, and explicit approval. Metrics at certification: 10 certified decisions, 8 promotions, 66 promotion behavioral gates (plus 31 M0/M1–M4 and 18 phase7/phase8 gates), Aria regression 531 passed / 1 skipped, standalone ACM 325 passed, CI and GitHub Actions green, production store clean.

### Consequences

- Certification document: `docs/MEMORY_FOUNDATION_V1_CERTIFICATION.md`  
- Future cognitive subsystems (relationships, goals, projects, planning, long-term reasoning, explainability, evidence, teach/query recognition, user editing) are independent future work — NOT part of Memory Foundation v1.0  
- The certified behavior of D038–D047 is not revisited except through future controlled engineering decisions  
- Documentation-only milestone: no implementation, no architecture changes, no refactoring, no roadmap work  
- **STOP** — await approval before beginning the next cognitive subsystem

---

## A018 — M0I complete: promote ACM v0.21.0 Preference Behavioral Certification (2026-07-17)

**Status:** Accepted  
**Related:** A001–A017 · standalone ACM v0.21.0 (Preference Behavioral Certification) · tag `v0.21.0` · commit `818d89d…`

### Decision

M0I promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.21.0** (`aria-acm-v0.21.0-1`). The live Preference certification blocker — favorite-color recall answering with a stored tool wrapper — is corrected end-to-end: artifact signatures match live backtick tool wrappers and host autosave lines; the encode boundary applies content-level trust (tool/system/infrastructure payloads are rejected even when a host mislabels them as trusted user speech); interrogatives never mint preference facts or cues; cleanup removes orphaned artifact-valued attributes and restores superseded legitimate preferences; reconstruction refuses artifact values. Host integration: the bridge's one-time D047 marker now records the embedded ACM version, so stores migrated by v0.20.0's defective classifier were re-migrated exactly once; same-version restarts never reprocess. The live production store was migrated (17 contaminated experiences removed — tool wrappers and autosave checkpoints; backup in `data/acm/archives/pre_m0i_backup/`), the user's legitimate teachings were restored through the trusted D046 path, and live answers verified: favorite color **blue**, identity **Jeff/Jeffrey**, injection attempts rejected, cleanup idempotent. Live Preference behavioral certification passes through the bridge. D038–D047 remain intact.

### Consequences

- Embedded pin: tag `v0.21.0`, commit `818d89d8e4ba2efab491b5d947b03155b6303df4`  
- Local copy: `aria-acm-v0.21.0-1`  
- Problem report: `docs/acm_integration/PROBLEM_REPORT_M0I.md`  
- Gates: `tests/test_aria_acm_m0i.py` (M0I-01..09)  
- Preference behavioral certification is complete in both standalone ACM and Aria  
- **STOP** — await approval before beginning the next cognitive subsystem

---

## A019 — M0J complete: promote ACM v0.22.0 Teaching Recognition (2026-07-17)

**Status:** Accepted  
**Related:** A001–A018 · standalone ACM v0.22.0 (Teaching Recognition) · tag `v0.22.0` · commit `2dd3715…`

### Decision

M0J promotion is complete. Aria's vendored copy at `aria_acm/` matches certified standalone ACM **v0.22.0** (`aria-acm-v0.22.0-1`). Teaching Recognition is promoted exactly as released: declarative, non-interrogative user statements with extracted cognitive facts encode through `cognitive_respond` before dispatch (full D046 Trusted Memory Ingestion and content-level artifact protection unchanged). Live Preference certification sequence through the bridge: fresh → unknown → "My favorite color is blue." → blue → "My favorite color is green." → green with blue retired → evidence reflects history without mutation → restart preserves green. Artifacts and interrogatives remain non-teaching. Identity certification and prior M0I protections remain intact. No ACM or Aria redesign; host bridge unchanged beyond the vendored tree. Permanent architecture backlog created at `docs/architecture-ideas.md`.

### Consequences

- Embedded pin: tag `v0.22.0`, commit `2dd3715c211f1fdc5e1147dccf9c827be5af801b`  
- Local copy: `aria-acm-v0.22.0-1`  
- Problem report: `docs/acm_integration/PROBLEM_REPORT_M0J.md`  
- Gates: `tests/test_aria_acm_m0j.py` (M0J-01..07)  
- Architecture backlog: `docs/architecture-ideas.md`  
- **STOP** — await approval before beginning the next cognitive subsystem

