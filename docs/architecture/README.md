# Aria Architecture Documentation

**Authority:** Principal Software Architect · **Date:** 2026-07-31  
**Mode:** Research and planning. Implementation requires explicit approval.

| Document | Role |
|----------|------|
| [ARCHITECTURE_REVIEW.md](./ARCHITECTURE_REVIEW.md) | Complete architecture review — how Aria works today |
| [ARCHITECTURE_BIBLE.md](./ARCHITECTURE_BIBLE.md) | Authoritative per-subsystem reference (v2) |
| [ENGINEERING_AUDIT.md](./ENGINEERING_AUDIT.md) | Strengths, weaknesses, duplicate ownership, risks |
| [ENGINEERING_ROADMAP.md](./ENGINEERING_ROADMAP.md) | Prioritized improvements (Critical → Low) — **not approved for implementation** |
| [LIFECYCLE_MAPS.md](./LIFECYCLE_MAPS.md) | Request/startup/job lifecycle maps |
| [MEMORY_TRANSITION_REVIEW.md](./MEMORY_TRANSITION_REVIEW.md) | Hostile design review of Batch D plan |
| [BATCH_D_MEMORY_TRANSITION_PLAN.md](./BATCH_D_MEMORY_TRANSITION_PLAN.md) | ACM memory transition (rev 2) — R1 done; R2+ blocked |
| [PHASE2_BATCHES_0ABC_EVIDENCE.md](./PHASE2_BATCHES_0ABC_EVIDENCE.md) | Evidence for Batches 0–C |
| [batch0/](./batch0/) | Measured inventories (graphs, matrices) |
| [batch_d/](./batch_d/) | R1 checkpoint evidence |

## Fixed decisions

- **ACM is the permanent cognitive memory platform.** Do not replace it. Do not add a second memory platform.
- Products own data. Dashboard / Mission Control / Certification observe or aggregate.
- HTTP 200 / toast is not success.

## Scale (measured)

~1,441 app Python files · ~266k LOC · ~1,200 routes · 16 products · 11 extensions · 309 test files · ~43k JS LOC.
