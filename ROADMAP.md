# Aria / Jarvis Roadmap

**Last updated:** 2026-07-17

## Active — Memory replacement (ACM)

| Item | Status | Notes |
|------|--------|-------|
| ACM Integration Blueprint | Approved / locked | `docs/acm_integration/` · A001 |
| Phase M0 — Vendor ACM into `aria_acm/` | **Complete** | `aria-acm-v0.24.0-1` (M0L promoted) |
| Phase M1 — Shadow measure | **Complete** | Measure phase ended for production |
| Phase M2 — Harvest migrate INTO ACM | **Complete** | Operator harvest CLI |
| Phase M3 — ACM primary cognition | **Complete** | Flag-gated authority |
| **Phase M4 — Retire legacy cognitive SoT** | **Complete** | ACM sole SoT · A006 |
| **Phase M0A — Promote ACM v0.15.0 (Memory Authority)** | **Complete** | D038 · `aria-acm-v0.15.0-1` · A007 |
| **Phase M0B — Promote ACM v0.16.0 (Cognitive Intent)** | **Complete** | D039 · `aria-acm-v0.16.0-1` · A008 |
| **Phase M0C — Promote ACM v0.17.0 (Cognitive Dispatch)** | **Complete** | D040 · `aria-acm-v0.17.0-1` · A009 |
| **Phase M0D — Promote ACM v0.18.1 (Identity Pipeline)** | **Complete** | D042 (+D041) · `aria-acm-v0.18.1-1` · A012 |
| **Phase M0E — Promote ACM v0.18.3 (Identity Rendering)** | **Complete** | D044 (+D043) · `aria-acm-v0.18.3-1` · A013 |
| **Phase M0F — Promote ACM v0.18.4 (Preference Reconstruction)** | **Complete** | D045 · `aria-acm-v0.18.4-1` · A014 |
| **Phase M0G — Promote ACM v0.19.0 (Trusted Memory Ingestion)** | **Complete** | D046 · `aria-acm-v0.19.0-1` · A015 |
| **Phase M0H — Promote ACM v0.20.0 (Legacy Memory Cleanup)** | **Complete** | D047 · `aria-acm-v0.20.0-1` · A016 |
| **Phase M0I — Promote ACM v0.21.0 (Preference Certification)** | **Complete** | `aria-acm-v0.21.0-1` · A018 |
| **Phase M0J — Promote ACM v0.22.0 (Teaching Recognition)** | **Complete** | `aria-acm-v0.22.0-1` · A019 |
| **Phase M0K — Promote ACM v0.23.0 (Multi-domain + Evidence)** | **Complete** | `aria-acm-v0.23.0-1` · A020 |
| **Phase M0L — Promote ACM v0.24.0 (Explanation + Summary)** | **Complete** | `aria-acm-v0.24.0-1` · A021 |
| **Memory Foundation v1.0 — Behavioral Certification** | **CERTIFIED** | D038–D047 · [`docs/MEMORY_FOUNDATION_V1_CERTIFICATION.md`](docs/MEMORY_FOUNDATION_V1_CERTIFICATION.md) · A017 |
| **Cognitive Infrastructure Conversion** | **Complete** | ACM sole brain · MC/Trace ACM · A010 |
| **Cognitive Memory Reset v1** | **Complete** | Clean post-D041 autobiographical baseline · A011 |

**Memory Foundation is complete.** Future work begins as independent
cognitive subsystems built on the certified foundation (examples, future
only: relationships, goals, projects, planning, long-term reasoning,
explainability, evidence, teach/query recognition, user editing). None of
these are part of Memory Foundation v1.0; each requires its own controlled
engineering decision and approval.

Standalone ACM remains research/reference. Aria production copy: `aria_acm/`.

See: [`docs/COGNITIVE_MEMORY_RESET_v1.md`](docs/COGNITIVE_MEMORY_RESET_v1.md) · [`docs/COGNITIVE_INFRASTRUCTURE_CONVERSION.md`](docs/COGNITIVE_INFRASTRUCTURE_CONVERSION.md) · [`docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md`](docs/acm_integration/MEMORY_REPLACEMENT_BLUEPRINT.md) · [`LEGACY_RETIREMENT_FINAL.md`](docs/LEGACY_RETIREMENT_FINAL.md)

## Platform & product (ongoing)

See [`docs/PHASE_ROADMAP.md`](docs/PHASE_ROADMAP.md) and [`UPGRADES.md`](UPGRADES.md).

## Explicit non-goals (this epoch)

- Reintroducing legacy MemoryStore as cognitive primary without re-certification  
- Dual cognitive SoTs / DualWrite as authority  
- Rebuilding ACM organs inside Aria
