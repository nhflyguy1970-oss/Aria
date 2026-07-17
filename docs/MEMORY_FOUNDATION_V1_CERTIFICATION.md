# Memory Foundation v1.0 — Behavioral Certification

**Milestone:** Memory Foundation v1.0  
**Status:** CERTIFIED  
**Date:** 2026-07-17  
**Repository:** Aria (`/media/jeff/AI/jarvis`) · embedded ACM `aria_acm/`  
**Embedded ACM:** `aria-acm-v0.20.0-1` (standalone tag `v0.20.0`, commit `b996fe8128c8104c4f1a7a0e633f8b28087a780d`)

This document formally certifies the completion of the Memory Foundation —
the project's first major cognitive milestone. The core autobiographical
memory system is behaviorally certified and is the stable platform for all
future cognitive development. This is a documentation-only milestone: no
implementation, architecture, or roadmap work is part of it.

---

## 1. Certified Decisions

| Decision | Capability |
|----------|------------|
| D038 | Memory Authority |
| D039 | Intent Classification |
| D040 | Cognitive Dispatch |
| D041 | Semantic Extraction |
| D042 | User Identity |
| D043 | Assistant Identity |
| D044 | Identity Rendering Isolation |
| D045 | Preference Reconstruction |
| D046 | Trusted Memory Ingestion |
| D047 | Legacy Memory Contamination Cleanup |

Each decision was implemented and certified in the standalone ACM reference
implementation first, then promoted into Aria as a controlled vendor
promotion.

## 2. Promotion History

Promotion lineage (each stage building on the previous certified state):

M0A → M0B → M0C → M0D → M0E → M0F → M0G → M0H

| Promotion | ACM version | Decision(s) | Local copy | Record |
|-----------|-------------|-------------|------------|--------|
| M0A | v0.15.0 | D038 Memory Authority | `aria-acm-v0.15.0-1` | A007 |
| M0B | v0.16.0 | D039 Cognitive Intent | `aria-acm-v0.16.0-1` | A008 |
| M0C | v0.17.0 | D040 Cognitive Dispatch | `aria-acm-v0.17.0-1` | A009 |
| M0D | v0.18.1 | D042 User Identity (+D041) | `aria-acm-v0.18.1-1` | A012 |
| M0E | v0.18.3 | D044 Identity Rendering (+D043) | `aria-acm-v0.18.3-1` | A013 |
| M0F | v0.18.4 | D045 Preference Reconstruction | `aria-acm-v0.18.4-1` | A014 |
| M0G | v0.19.0 | D046 Trusted Memory Ingestion | `aria-acm-v0.19.0-1` | A015 |
| M0H | v0.20.0 | D047 Legacy Memory Cleanup | `aria-acm-v0.20.0-1` | A016 |

Every promotion was completed only after all of the following passed:

1. Behavioral validation (promotion gate suite against the vendored copy)
2. Regression (full Aria test suite, all prior gates intact)
3. Integration (host bridge, persistence, primary cognition paths)
4. Performance (latency/perf budgets)
5. CI (`scripts/ci_check.py all` — lint, format, supremacy guard, pytest)
6. GitHub verification (remote HEAD match + green GitHub Actions run)
7. Promotion approval (explicit operator approval before each stage)

## 3. Foundation Capabilities

Memory Foundation v1.0 provides:

- **Autobiographical memory** — durable Experiences, Concepts, and
  Attributes with evidence links, persisted in SQLite
- **Identity modeling** — user identity pipeline (Jeff) with dedicated
  identity concepts and rendering (D041/D042)
- **Assistant identity** — separate assistant profile (ARIA) that never
  leaks into or from user identity (D043/D044)
- **Preference memory** — preference encoding and recall (favorite color:
  blue) with certified reconstruction (D045)
- **Preference updates** — new statements supersede prior values without
  artificial conflicts
- **Conflict handling** — true semantic conflicts preserved and surfaced;
  artificial conflicts eliminated (D045)
- **Memory Authority** — ACM is the sole cognitive source of truth (D038,
  M4 legacy retirement)
- **Intent classification** — teach/query/other cognitive intent (D039)
- **Cognitive dispatch** — intent-routed cognition (D040)
- **Semantic extraction** — natural language to structured cognitive facts
  (D041)
- **Trusted memory ingestion** — fail-closed provenance gate; only trusted
  user statements, teachings, and corrections enter memory (D046)
- **Durable provenance** — immutable actor / host-operation / message-role
  records for every artifact
- **Legacy contamination cleanup** — one-time idempotent migration removing
  pre-D046 contamination, wired into Aria's upgrade path (D047)
- **Behavioral certification** — deterministic gate suites for every
  promoted behavior
- **Promotion governance** — pinned vendor promotions with tree hashes,
  problem reports, decision records, and STOP discipline

## 4. Architectural Invariants

The following principles were preserved throughout D038–D047:

- No cognitive organ redesign
- No architectural rewrites
- Behavior-first engineering (behavioral gates define correctness)
- Reference implementation first (standalone ACM leads)
- Standalone ACM certification before Aria promotion
- Controlled vendor promotions (pinned tag + commit + tree hash; no
  automatic synchronization)
- Minimal host integration (thin `acm_bridge`; approved M0 import
  bootstrap is the only vendored delta)
- Fail-closed trust boundaries (untrusted or unknown provenance rejected
  with zero graph mutation)
- Deterministic behavioral validation (repeatable gates, no flaky
  certification)

## 5. Metrics at Certification

| Metric | Value |
|--------|-------|
| Certified decisions | 10 (D038–D047) |
| Promotion count | 8 (M0A–M0H), on the M0–M4 integration baseline |
| Behavioral gate count (promotion suites) | 66 gates across `test_aria_acm_m0a`–`m0h` (5·7·7·6·8·10·11·12) |
| Supporting ACM gates | 31 across `test_aria_acm_m0`, `m1`–`m4`; +18 phase7/phase8 cognition gates |
| Regression coverage (Aria) | 531 passed, 1 skipped — full suite green |
| Regression coverage (standalone ACM v0.20.0) | 325 passed |
| Performance gates | Greeting/latency budgets (`test_greeting_latency.py`, 8 gates) + M1 shadow timing budgets — green |
| CI status | `scripts/ci_check.py all` green (ruff, format, supremacy guard, pytest) |
| GitHub status | HEAD `5b3d10a223c6ab1e00ad4d0277977d40f5391f75` pushed; GitHub Actions run green |
| Behavioral certification status | CERTIFIED (Identity · Preference · Trusted Ingestion · Legacy Cleanup) |
| Production memory store | Clean D046-gated baseline; D047 migration ran once, 0 removals |

## 6. Next Phase

**Memory Foundation is complete.**

Future work begins as independent cognitive subsystems built on top of this
foundation. Examples (future work only — NOT part of Memory Foundation
v1.0):

- Relationships
- Goals
- Projects
- Planning
- Long-term reasoning
- Explainability
- Evidence
- Teach/query recognition
- User editing

Future cognitive subsystems may build upon this foundation without
revisiting the certified behavior of D038–D047, except through future
controlled engineering decisions.

## 7. References

- `aria_acm/VERSION.json` · `aria_acm/NOTICE` — embedded pin
- `docs/acm_integration/PROBLEM_REPORT_M0A.md` … `PROBLEM_REPORT_M0H.md`
- `DECISION_LOG.md` A007–A016 (promotions), A017 (this milestone)
- Standalone ACM: `docs/DECISION_LOG.md` D038–D047, `CHANGELOG.md`
  v0.15.0–v0.20.0

---

**STOP.** No further implementation without explicit approval. The next
cognitive subsystem begins only after operator approval.
