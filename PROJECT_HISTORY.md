# Project History — Aria / Jarvis

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
