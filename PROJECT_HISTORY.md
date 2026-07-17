# Project History — Aria / Jarvis

## 2026-07-17 — M0K: Promote ACM v0.23.0 (Multi-domain preference + evidence)

Controlled promotion of certified standalone ACM v0.23.0 into `aria_acm/`
(`aria-acm-v0.23.0-1`). Live M0K manual certification failures corrected:
favorite food/fish no longer collapse into favorite color; `Show me the
evidence.` reconstructs active/retired lineage without mutation; domains
remain independent across updates and restart. Commit `82a9499…`. Gates
M0K-01..05. Full CI green.

## 2026-07-17 — M0J: Promote ACM v0.22.0 (Teaching Recognition)

Controlled promotion of certified standalone ACM v0.22.0 into `aria_acm/`
(`aria-acm-v0.22.0-1`). Restores Preference behavioral certification for
valid teachings spoken through Memory Authority: declarative statements
encode via `cognitive_respond` before dispatch, so blue → green retires
the previous preference; evidence reflects teaching history; restart
preserves green; artifacts and interrogatives remain non-teaching. Tree
matches source commit `2dd3715…` except the Aria import bootstrap. Identity
and prior M0I certifications remain valid (M0J-01..07). Permanent
architecture backlog started at `docs/architecture-ideas.md`. Full CI green.

## 2026-07-17 — M0I: Promote ACM v0.21.0 (Preference Behavioral Certification)

Controlled promotion of certified standalone ACM v0.21.0 into `aria_acm/`
(`aria-acm-v0.21.0-1`), completing the live Preference certification blocker.
Live Aria had answered favorite-color recall with a stored tool wrapper
("Your preference is Tool `memory_search` worked for: …") because v0.20.0's
D047 classifier missed live backtick wrapper formats and D046 trusted
declared provenance alone. v0.21.0 adds live artifact signatures,
content-level trust rejection, interrogative preference guards, orphaned
artifact-attribute cleanup, and render defense. Bridge D047 marker is now
version-aware; the live production store was re-migrated exactly once
(17 contaminated experiences removed, backup retained), legitimate teachings
restored via the trusted path, and live answers verified (blue / Jeff /
Jeffrey). Live Preference behavioral certification passes through the bridge
(M0I-01..09). Full CI green.

## 2026-07-17 — MILESTONE: Memory Foundation v1.0 — Behavioral Certification

First major cognitive milestone. The core autobiographical memory system is
formally certified: ten decisions (D038–D047) implemented and certified in
standalone ACM, then promoted into Aria through eight controlled vendor
promotions (M0A→M0H), each completed only after behavioral validation,
regression, integration, performance, CI, GitHub verification, and
promotion approval. Capabilities: autobiographical memory, user/assistant
identity modeling, identity rendering isolation, preference memory and
updates, conflict handling, memory authority, intent classification,
cognitive dispatch, semantic extraction, trusted memory ingestion, durable
provenance, legacy contamination cleanup, behavioral certification, and
promotion governance. Architectural invariants held throughout: no organ
redesign, no rewrites, behavior-first, reference-implementation-first,
fail-closed trust boundaries, deterministic validation. Future cognitive
subsystems (relationships, goals, projects, planning, explainability, …)
are independent future work built on this foundation. Documentation-only
milestone — no code changes.
See `docs/MEMORY_FOUNDATION_V1_CERTIFICATION.md` (A017).

## 2026-07-17 — M0H: Promote ACM v0.20.0 (Legacy Memory Cleanup / D047)

Controlled promotion of certified standalone ACM v0.20.0 into `aria_acm/`
(`aria-acm-v0.20.0-1`). One-time idempotent D047 migration removes pre-D046
contaminated memories (artifact signatures + legacy provenance evaluation),
restores superseded legitimate attributes, and cleans orphaned concepts,
associations, hierarchy edges, working-memory entries, and provenance.
Exposed through Aria's upgrade path with a run-once completion marker;
production store verified already clean (0 removals). D046 unchanged;
D038–D045 intact. No Aria bridge redesign. M0H-01..12 + full CI green.

## 2026-07-17 — M0G: Promote ACM v0.19.0 (Trusted Memory Ingestion / D046)

Controlled promotion of certified standalone ACM **v0.19.0** into `aria_acm/`
(`aria-acm-v0.19.0-1`). Only trusted user knowledge may enter autobiographical
memory; tool, diagnostic, reflection, system, infrastructure, and unknown
sources are rejected before Semantic Extraction with zero graph mutation. Host
write paths declare trusted user provenance. Identity/Preference D038–D045
intact. No Aria bridge redesign. M0G-01..11 + full CI green.

## 2026-07-17 — M0F: Promote ACM v0.18.4 (Preference Reconstruction / D045)

Controlled promotion of certified standalone ACM **v0.18.4** into `aria_acm/`
(`aria-acm-v0.18.4-1`). Lexical support concepts no longer manufacture Preference
conflicts; true semantic conflicts preserved. Identity D038–D044 intact. No Aria
bridge redesign. M0F-01..10 + full CI green.

## 2026-07-16 — M0E: Promote ACM v0.18.3 (Identity Rendering Isolation / D044)

Controlled promotion of certified standalone ACM **v0.18.3** into `aria_acm/`
(`aria-acm-v0.18.3-1`). Includes Assistant Identity (D043) and Identity rendering
isolation (D044). No Aria bridge redesign. M0E-01..08 + full CI green.

## 2026-07-16 — M0D: Promote ACM v0.18.1 (Identity Pipeline / D042)

Controlled promotion of certified standalone ACM **v0.18.1** into `aria_acm/`
(`aria-acm-v0.18.1-1`). Includes Semantic Extraction (D041) and Identity pipeline
correction (D042). No Aria bridge redesign. M0D-01..06 + full CI green.

## 2026-07-16 — Cognitive Memory Reset v1 (Post-D041 baseline)

Archived Pre-D041 embedded ACM autobiographical durable store (contaminated identity
data) under `data/acm/archives/`; reset live `cognitive.db` to empty. Code and
architecture unchanged. Official clean behavioral baseline for future teaching
(gated on approval). See `docs/COGNITIVE_MEMORY_RESET_v1.md`.

## 2026-07-15 — Cognitive Infrastructure Conversion (ACM sole brain)

Final conversion of Aria cognition onto embedded ACM (A010):

- MemoryStore JSON/SQLite **reads/updates/deletes** divert to ACM when PRIMARY
- System prompt + knowledge memory search → ACM
- Mission Control panel → ACM Cognitive Dashboard
- Conversation Trace → `memory_operation.v3` ACM diagnostics
- Dependency audit/graph + retirement docs
- CIC-01..06 + full CI

## 2026-07-15 — M4: Retire legacy cognitive SoT (ACM sole authority)

Implemented blueprint Phase **M4** (final integration milestone):

- `ARIA_ACM_PRIMARY` defaults **on**; legacy read fallback defaults **off**
- DualWrite cognitive path disabled (M4b); wrap is identity
- `MemoryStore.add` redirects to Cap Bus/ACM when authoritative (bypass closure)
- Parallel modules (experience / relationship / trust writers / consolidation) → ACM clients
- Hierarchy SoT consolidate no-op under PRIMARY (M4d)
- CI supremacy gate `scripts/acm_supremacy_check.py`; vault operator tool
- Legacy retirement report; docs ACM-authoritative
- M4-01..03 tests green; full CI green

## 2026-07-15 — M3: ACM primary authority (opt-in)

Implemented blueprint Phase **M3** only:

- Cap Bus / Core Memory Manager + MemoryEngine use ACM when `ARIA_ACM_PRIMARY=1` and not `ROLLBACK`
- Soft forget via `cool_memory`; corrections via `revise_experience`; `prepare_context` from ACM fragments
- Optional `ARIA_ACM_LEGACY_READ_FALLBACK` for empty ACM reads; no legacy **writes** while PRIMARY (SUP-02)
- Rollback drill: `ARIA_ACM_ROLLBACK=1` restores legacy façades; ACM data retained
- **Default PRIMARY remains off** — not enabled globally. Legacy Not removed (M4)
- Tests M3-01..M3-06 + SUP-02; CI updated

## 2026-07-15 — M2: Harvest migrate INTO ACM

Implemented blueprint Phase **M2** only:

- Operator CLI `scripts/acm_harvest.py` + `aria_core/acm_harvest.py`
- MemoryStore → ACM Experiences with `legacy_id` / `ProvenanceSource.LEGACY_IMPORT`
- Idempotent re-run; revise lineage via known `revises:` tags; identity assent option
- Journal / preference / project spot packs; completeness gate ≥99.5% P0
- Legacy still authoritative; no PRIMARY; no automatic background migrate

## 2026-07-15 — M1: ACM Shadow measure

Implemented blueprint Phase **M1** only:

- Added `aria_core/acm_bridge.py` (thin façade; Shadow compare; panel observables)
- Dual-call from Core `remember` / `search_memory` when `ARIA_ACM_SHADOW=1`
- Authoritative route remains **legacy**; ACM answers never user-visible in M1
- Mission Control `shadow` counters; Conversation Trace `memory_operation.v2`
- Tests M1-01..M1-04 green; CI updated

## 2026-07-15 — M0C: Promote ACM v0.17.0 (End-to-End Cognitive Dispatch)

Promoted standalone ACM tag `v0.17.0` / commit `af108d08…` into `aria_acm/` as `aria-acm-v0.17.0-1` (decision D040). Wired Aria façade through classify → route → dispatch → respond → speak. Tests M0C-01..M0C-07 green; full CI green.

## 2026-07-15 — M0B: Promote ACM v0.16.0 (Cognitive Intent Classification)

Promoted standalone ACM tag `v0.16.0` / commit `6f6d0f89…` into `aria_acm/` as `aria-acm-v0.16.0-1` (decision D039). Wired Aria façade through classify → route → cognitive_respond → speak. Tests M0B-01..M0B-07 green; full CI green.

## 2026-07-15 — M0A: Promote ACM v0.15.0 (Memory Authority)

Promoted standalone ACM tag `v0.15.0` / commit `b78a857…` into `aria_acm/` as `aria-acm-v0.15.0-1` (decision D038). Wired Aria recall/search through Memory Authority pipeline via `acm_bridge`. Tests M0A-01..M0A-05 green; full CI green.

## 2026-07-15 — M0: Vendor ACM into Aria

Implemented blueprint Phase **M0** only. Vendored ACM at pin `v0.14.0` / `454dcb90…` as `aria-acm-v0.14.0-1` (superseded by M0A promotion).

## 2026-07-15 — ACM Integration Blueprint (design only)

Authoritative docs: `docs/acm_integration/` · Decision **A001**.

## Prior eras

Product and platform history continues in `docs/PHASE_ROADMAP.md` and `UPGRADES.md`.
