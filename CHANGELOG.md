# Changelog — Aria / Jarvis

## [M5-ACM-CAP5-TEMPORAL] — 2026-07-23

Promote certified ACM **v0.32.0** (`2ce664b`) as `aria-acm-v0.32.0-1`.
Includes M5 Cap1–Cap5 (concept hierarchies, evidence weighting, counterfactual
prediction audit, multi-level abstraction, temporal pattern recognition) plus
prior M4 AML. Gates: `tests/test_aria_acm_m5_cap5.py` and updated pin asserts.

## [M4-ACM-AML] — 2026-07-23

Promote certified ACM **v0.27.0** (`1850ad7`) as `aria-acm-v0.27.0-1`.
Adaptive Memory & Learning: B29 diagnostic privacy/redaction, assent apply,
goal/lifecycle learning, B03/B18 explainability, daily learning summary,
`adopt_knowledge()` MVP, host-callable `sleep()`/`consolidate()`, learning
certification. Host fix: assistant-identity cues (`Who are you?`) route to
Memory Authority before NLU/chat.

## [M1] — 2026-07-19

Promote certified ACM **v0.25.0** (`d71a6af`) as `aria-acm-v0.25.0-1`.
Episodic autobiographical memory (event teaching, temporal reconstruction,
evidence) via unchanged ACM package. No Aria host episodic cognition.

See [`docs/acm_integration/PROBLEM_REPORT_M1.md`](docs/acm_integration/PROBLEM_REPORT_M1.md).

## [M0L Certified] — 2026-07-19

**Frozen.** See [`docs/acm_integration/M0L_CERTIFICATION.md`](docs/acm_integration/M0L_CERTIFICATION.md).

Certified against standalone ACM **v0.24.0** (`3c3bdbc`). Aria tags: `m0l-certified`.

### Certified capabilities

- Teaching Recognition  
- Multi-domain memory  
- Memory updates + lineage  
- Evidence reconstruction  
- Explanation (why / replaced / active)  
- Active-only personal summary  
- Promotion fidelity verification  
- Aria routing validation (Memory Authority path; evidence → `memory_about_user`)

### Integration pin

- Aria evidence routing: `7343faa`  
- M0L promotion: `adc722f` · `aria-acm-v0.24.0-1`

## [Unreleased] — 2026-07-17

### Added

- **M0L:** Promoted certified standalone ACM **v0.24.0** into `aria_acm/` as `aria-acm-v0.24.0-1` (commit `3c3bdbc…`). Fixes final live explanation/summary failures: Why/replaced/active questions reconstruct from certified lineage; `What do you know about me?` summarizes active memories only; Aria NLU/runtime guards keep these on Memory Authority (never Mission Control). Gates: `tests/test_aria_acm_m0l.py`.

- **Evidence routing:** Evidence cues (`Show me the evidence.`, etc.) route to `memory_about_user` with the full original prompt (never `memory_search`). Gates: `tests/test_evidence_routing.py`. Commit `7343faa`.

- **M0K:** Promoted certified standalone ACM **v0.23.0** into `aria_acm/` as `aria-acm-v0.23.0-1` (commit `82a9499…`). Fixes live multi-domain preference collapse (favorite food/fish no longer answer as favorite color) and evidence reconstruction (`Show me the evidence.` returns active/retired lineage without mutating memory). Domains remain independent across updates and restart. Gates: `tests/test_aria_acm_m0k.py`.

### Fixed

- **Teaching Recognition live routing:** After M0J, declarative teachings such as "My favorite color is green." were classified by NLU as `intent=memory` but collapsed to `memory_search` with only the semantic *subject* (`favorite color`). Teaching Recognition never saw the statement, EncodeAuthority never ran, and recall stayed on the prior value. Unresolved declarative memory intents now route to Memory Authority (`memory_about_user`) with the **full** prompt so ACM Teaching Recognition → encode → supersede runs. Temporary `[TeachingRecognition]` DEBUG logging on `primary_cognitive_respond` (disable with `ARIA_TEACHING_DEBUG=0`). Gates: `tests/test_teaching_recognition_routing.py`.

### Added (prior)

- **M0J:** Promoted certified standalone ACM **v0.22.0** (Teaching Recognition) into `aria_acm/` as `aria-acm-v0.22.0-1`. Source commit `2dd3715…`. Restores Preference behavioral certification for *valid* teachings spoken through Memory Authority: declarative statements such as "My favorite color is green." encode through `cognitive_respond` before dispatch (D046 trust gate and content-level artifact protection unchanged), so blue → green retires the previous preference correctly; evidence reflects teaching history; restart preserves green; artifacts and interrogatives remain non-teaching. Identity certification and prior M0I protections intact. Permanent architecture backlog started at `docs/architecture-ideas.md`.
- M0J gates: `tests/test_aria_acm_m0j.py` (M0J-01..07); wired into CI.
- Architecture backlog extended with Skills registry, memory viewer, sensitive-data redaction, tool relevance filtering, always-on daemon, sidecar/multi-client, permission boundaries, and assistant state visualization (backlog only).
- **M0I:** Promoted certified standalone ACM **v0.21.0** (Preference Behavioral Certification) into `aria_acm/` as `aria-acm-v0.21.0-1`. Source commit `818d89d…`. Corrects the live Preference blocker ("Your preference is Tool \`memory_search\` worked for: …"): artifact signatures now match live backtick tool wrappers and host autosave; content-level trust rejects tool/system/infra payloads even when mislabeled as trusted user speech; interrogatives never mint preference facts; reconstruction refuses artifact values. Bridge D047 marker is version-aware — stores migrated by v0.20.0's defective classifier were re-migrated exactly once. Live production store: 17 contaminated experiences removed (backup in `data/acm/archives/pre_m0i_backup/`), legitimate teachings restored via the trusted path; live answers verified ("blue", "Jeff/Jeffrey"). D038–D047 intact.
- M0I gates: `tests/test_aria_acm_m0i.py` (M0I-01..09) incl. live Preference behavioral certification through the bridge; wired into CI.
- **Memory Foundation v1.0 — Behavioral Certification (milestone, documentation only):** formally certifies completion of the core autobiographical memory system covering D038–D047 (Memory Authority, Intent Classification, Cognitive Dispatch, Semantic Extraction, User Identity, Assistant Identity, Identity Rendering Isolation, Preference Reconstruction, Trusted Memory Ingestion, Legacy Memory Contamination Cleanup) and the M0A→M0H promotion lineage. Embedded ACM: `aria-acm-v0.20.0-1`. Future cognitive subsystems (relationships, goals, projects, planning, explainability, etc.) build on this foundation as independent work. See `docs/MEMORY_FOUNDATION_V1_CERTIFICATION.md` (A017). No code changes.
- **M0H:** Promoted certified standalone ACM **v0.20.0** (D047 Legacy Memory Contamination Cleanup) into `aria_acm/` as `aria-acm-v0.20.0-1`. Source commit `b996fe8…`. One-time idempotent migration removes pre-D046 contaminated memories (tool, memory-search, diagnostic, reflection, system, infrastructure, prompt, metadata artifacts) with their solely-derived concepts, attributes, associations, hierarchy edges, working-memory entries, and provenance, and restores legitimate attributes the artifacts superseded. Aria upgrade path (`acm_bridge.get_engine`) runs the migration exactly once per durable store via a completion marker; production store verified already clean (0 removals). D046 Trusted Memory Ingestion unchanged; Identity/Preference D038–D045 intact.
- M0H gates: `tests/test_aria_acm_m0h.py` (M0H-01..12); wired into CI.
- **M0G:** Promoted certified standalone ACM **v0.19.0** (D046 Trusted Memory Ingestion) into `aria_acm/` as `aria-acm-v0.19.0-1`. Source commit `48938bc…`. Every external encode declares actor / host-operation / message-role provenance; tool, diagnostic, reflection, system, infrastructure, and unknown sources are rejected before Semantic Extraction with zero graph mutation. Host write paths (`acm_bridge`, `acm_harvest`) declare trusted user provenance. Identity/Preference D038–D045 remain intact.
- M0G gates: `tests/test_aria_acm_m0g.py` (M0G-01..11); wired into CI.

### Added (prior)

- **M0F:** Promoted certified standalone ACM **v0.18.4** (D045 Preference Reconstruction Fix) into `aria_acm/` as `aria-acm-v0.18.4-1`. Source commit `3023ed8…`. Artificial preference conflicts eliminated; true semantic conflicts preserved. Identity D038–D044 remain intact.
- M0F gates: `tests/test_aria_acm_m0f.py` (M0F-01..10); wired into CI.

### Added (prior)

- **M0E:** Promoted certified standalone ACM **v0.18.3** (D044 Identity Rendering Isolation; includes D043 Assistant Identity) into `aria_acm/` as `aria-acm-v0.18.3-1`. Source commit `7a69527…`. Who am I? / Who are you? fully isolated via bridge.
- M0E gates: `tests/test_aria_acm_m0e.py` (M0E-01..08); wired into CI.

### Added (prior)

- **M0D:** Promoted certified standalone ACM **v0.18.1** (D042 Identity Pipeline Correction; includes D041 Semantic Extraction) into `aria_acm/` as `aria-acm-v0.18.1-1`. Source commit `137c24a…`. Identity teach→retrieve works via Cap Bus / ACM bridge.
- M0D gates: `tests/test_aria_acm_m0d.py` (M0D-01..06); wired into CI.

### Changed

- **Cognitive Memory Reset v1:** Archived Pre-D041 embedded ACM autobiographical store (contaminated identity) and reset durable `data/acm/cognitive.db` to empty baseline. Architecture/organs/code unchanged. Operator: `scripts/acm_cognitive_memory_reset.py`. See `docs/COGNITIVE_MEMORY_RESET_v1.md`.

## [Unreleased] — 2026-07-15

### Added

- **Cognitive Infrastructure Conversion (A010):** ACM is Aria’s sole cognitive brain. MemoryStore search/list/get/update/delete façades divert to ACM; system prompt + knowledge search use ACM; Mission Control Memory panel → ACM Cognitive Dashboard; Conversation Trace `memory_operation.v3` with intent/owner/dispatch/termination/diagnostics. Docs: `COGNITIVE_INFRASTRUCTURE_CONVERSION.md`, `DEPENDENCY_AUDIT.md`, `DEPENDENCY_GRAPH.md`, `MISSION_CONTROL_ACM.md`, `CONVERSATION_TRACE_ACM.md`, `LEGACY_RETIREMENT_FINAL.md`. Gates: `tests/test_cognitive_infrastructure_conversion.py` (CIC-01..06).

- **M0C:** Promoted certified standalone ACM **v0.17.0** (D040 End-to-End Cognitive Dispatch) into `aria_acm/` as `aria-acm-v0.17.0-1`. Cap Bus / Core / MemoryEngine use `classify_request` → `route_request` → `dispatch_request` → `cognitive_respond` → `speak_cognitive_result`.
- M0C gates: `tests/test_aria_acm_m0c.py` (M0C-01..M0C-07); wired into CI.

- **M0B:** Promoted certified standalone ACM **v0.16.0** (D039 Cognitive Intent Classification & Routing) into `aria_acm/` as `aria-acm-v0.16.0-1`. Cap Bus / Core / MemoryEngine use `classify_request` → `route_request` → `cognitive_respond` → `speak_cognitive_result`.
- M0B gates: `tests/test_aria_acm_m0b.py` (M0B-01..M0B-07); wired into CI.

- **M0A:** Promoted certified standalone ACM **v0.15.0** (D038 Memory Authority) into `aria_acm/` as `aria-acm-v0.15.0-1`. Cap Bus / Core / MemoryEngine recall routes through `classify_request` → `cognitive_respond` → `CognitiveMemoryResult` → `speak_cognitive_result`.
- M0A gates: `tests/test_aria_acm_m0a.py` (M0A-01..M0A-05); wired into CI.

- **M4:** ACM is Aria's sole cognitive memory SoT. PRIMARY defaults on; DualWrite retired; legacy store writes redirect to ACM; specialized writers are ACM clients; hierarchy SoT consolidate disabled under PRIMARY; supremacy CI + vault operator tool; retirement report.
- M4 gates: `tests/test_aria_acm_m4.py` (M4-01..M4-03); `scripts/acm_supremacy_check.py`.

- **M3:** Controlled ACM primary authority — Cap Bus / Core / MemoryEngine route encode/recall/cool/revise through vendored ACM when `ARIA_ACM_PRIMARY=1` (and not `ARIA_ACM_ROLLBACK`). Optional legacy read fallback (default off after M4).
- M3 gates: `tests/test_aria_acm_m3.py` (M3-01..M3-06); wired into CI.

- **M2:** Operator-triggered harvest of legacy MemoryStore **INTO** vendored ACM (`aria_core/acm_harvest.py`, `scripts/acm_harvest.py`).
- **M1:** ACM Shadow measure.
- **M0:** Vendored certified ACM into `aria_acm/` (baseline `aria-acm-v0.14.0-1`; current pin `aria-acm-v0.19.0-1` via M0G).
- ACM Integration Blueprint; governance A001–A015.

### Notes

- Production: ACM only. ROLLBACK flag retained for M4 window only. Vault via `scripts/acm_vault_legacy_memory.py`. No DualWrite SoT.
