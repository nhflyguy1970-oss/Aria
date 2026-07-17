# Changelog — Aria / Jarvis

## [Unreleased] — 2026-07-17

### Added

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
