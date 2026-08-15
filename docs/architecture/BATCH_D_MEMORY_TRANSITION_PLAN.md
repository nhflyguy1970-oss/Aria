# Batch D — Memory Transition Plan (ACM permanent)

**Status:** Rev 2 working plan · **R1 COMPLETE** · R2+ **not approved**  
**Date:** 2026-07-31 (rev 2 + R1 evidence)  
**Decision (fixed):** ACM **is** the memory platform. Do not replace it. Do not add a second platform or a third façade.  
**Companion:** [`MEMORY_TRANSITION_REVIEW.md`](./MEMORY_TRANSITION_REVIEW.md) · R1 evidence [`batch_d/R1_CHECKPOINT_EVIDENCE.json`](./batch_d/R1_CHECKPOINT_EVIDENCE.json)

---

## 0. What this plan is / is not

| Is | Is not |
|----|--------|
| Cleanup of dead dual-write theater | Rebuild of write/read façades |
| Fix remaining split-brain reads | ACM engine redesign |
| Vault / docs honesty | New `jarvis.memory_api` |
| ADR for vectors only | Migrating `relationship_graph` as “memory” |
| Adapter-layer fixes in `MemoryStore` | Replacing MemoryStore class |

**Measured fact:** With `ARIA_ACM_PRIMARY` default-on, remember/list/search/stats already route through ACM. Batch D is **not** a greenfield cutover.

---

## 1. Target end state

| Concern | Owner |
|---------|--------|
| Cognitive memory SoT | ACM (`aria_core/acm_bridge` → `data/acm/cognitive.db`) |
| Public API for products | Existing ACM façades only: `aria_core/memory_manager` (writes) + `aria_core/acm_store_facade` (reads) + `MemoryStore` as **thin adapter** |
| Persistence | ACM only for cognitive facts; cold vaults archived then removed |
| Observers | Search, dashboard, conversation — already ACM-first; keep until vault gone |
| Forbidden | New memory stores, dual-write re-enable, new abstraction layers, ACM replacement |
| Project checkpoints | **Same SoT for write and read** (R1 done) |

### Real env flags (do not invent others)

| Flag | Role |
|------|------|
| `ARIA_ACM_PRIMARY` | Authoritative mode (default **on**) |
| `ARIA_ACM_ROLLBACK` | Emergency legacy path |
| `ARIA_ACM_LEGACY_READ_FALLBACK` | Read fallthrough to vault |
| `JARVIS_ALLOW_DUALWRITE_LEGACY` | DualWrite adapter (must stay off / deleted) |

---

## 2. Inventory — challenged & corrected

| Path | Reality | Can delete now? | Dependents | Risk if removed wrongly |
|------|---------|-----------------|------------|-------------------------|
| ACM `cognitive.db` / `aria_core/acm_bridge.py` | Permanent SoT | **Never** | Everything cognitive | Catastrophic |
| `aria_core/memory_manager.py` + `acm_store_facade.py` | **Already** the write/read façades | No | MemoryStore, Search | High |
| `modules/memory.py` + `memory_sqlite.py` | **Already** ACM adapter; class must stay | No (class); vault files later | assistant, behaviors, harvest, tests | High |
| `modules/memory_adapter_store.py` | Dead dual-write (`adapter_enabled` False) | **Yes + same-commit CI/tests** | supremacy check, tests | Low runtime / Med process |
| `semantic_memory_adapter_store.py` | Hot import via EmbeddingSidecar | **No** until vectors ADR | Every `MemoryStore()` | High |
| Cold `data/memory.db` / `memory.json` | Stale forensic vault | After R6 backup | Rollback path only under `ARIA_ACM_ROLLBACK` | Med functional |
| `data/memory_vectors.db` | Live embeddings sidecar | After ADR only | semantic search | High data |
| `relationship_graph.db` | **Connections product**, not ACM SoT | **Out of Batch D** | ~21 Connections/graph callers | High product |
| `platform_cutover` dual_write story | Docs/UI lie; adapter no-op | Retire **narrative**; keep cutover shell | MC cutover UI | Med honesty |
| `memory/hierarchy.py` | Needed; tags-only update may no-op under PRIMARY | No — **fix first** | hierarchy APIs | Med silent |
| `intelligence/memory_platform.py` | Dead helpers soft-fail | Thin/fix dead fns; keep routes | intel routes | Med false fail |
| `behaviors/memory/engine.py` | Partially ACM-aware; checkpoint via MemoryStore | No rewrite | chat memory actions | High if rewrite |
| `extensions/memory/` | Memory GUI REST | No — keep thin | Memory UI | High |
| `memory_candidates.json` | Staging UI | Later cleanup | learning review | Low |
| Cutover backfill → ACM | **Not primary migrate path** — ACM already hot | Archive after optional dry-run | ops | Med duplicate risk |
| `brain_memory.py` | Feeds / not cognitive SoT | Keep | feeds | — |

---

## 3. Known live defects

### 3.1 Checkpoint split-brain — **FIXED (R1)**

- Was: `upsert_checkpoint` → ACM; `latest_checkpoint` → legacy vault  
- Now: under PRIMARY both → ACM (`acm_store_facade.acm_latest_checkpoint` / `project_latest_checkpoint`); under ROLLBACK both → legacy  
- Evidence: `batch_d/R1_CHECKPOINT_EVIDENCE.json`; tests `tests/test_checkpoint_r1.py`

### 3.2 Hierarchy tags-only update (P1) — **open (R2)**

- `acm_update` ignores tags when `content is None` → hierarchy tag updates may silently fail under PRIMARY

### 3.3 Honesty debt (P1) — **open (R0/R4)**

- Cutover / PLATFORM_CUTOVER still describe cognitive dual_write as real mode while runtime is ACM-only

---

## 4. Revised phases (implementation only after approval)

**Rejected from rev 1:** D2 new `jarvis.memory_api`, D3 “migrate reads” as if unfinished, treating MemoryStore conversion as future work, folding `relationship_graph` into cognitive Batch D.

### R0 — Freeze & document (no ACM code) — **partial** (Bible Memory section updated with R1)

- Bible: cognitive SoT = ACM; **MemoryStore = ACM adapter**, not competing SoT.  
- PLATFORM_CUTOVER: dual_write obsolete for cognitive memory — **still open**.  
- Paths: `aria_core/…` (not `jarvis/aria_core/…`).  
- No new flags.

### R1 — Fix `latest_checkpoint` (+ sqlite twin) — **DONE 2026-07-31**

- Divert read through existing ACM façade (same pattern as `list_entries`).  
- Acceptance met: upsert → latest round-trip ACM; legacy poison ignored; restart; rollback symmetric.  
- **No new façade module. No new flags. No vault delete.**

### R2 — Fix tags-only / hierarchy persist under PRIMARY — **blocked pending approval**

- Acceptance: hierarchy tag update visible on subsequent ACM list/get.  
- Then optional hierarchy simplification (not deletion).

### R3 — Delete dead DualWrite adapter — **blocked**

- Remove `memory_adapter_store.py`.  
- Update `scripts/acm_supremacy_check.py`, `tests/test_memory_adapter.py`, `tests/test_aria_acm_m4.py` **same commit**.  
- Leave `JARVIS_ALLOW_DUALWRITE_LEGACY` unused or remove.

### R4 — Honest cutover status — **blocked**

- Cognitive memory status: “ACM authoritative; dual_write N/A”.  
- Do not mass-backfill cold vault into ACM without dry-run parity counts.

### R5 — Intelligence dead-code cleanup — **blocked**

- Remove or repair soft-fail helpers that call nonexistent APIs.  
- Keep registered routes until ACM-native intel API exists.

### R6 — Vault cold cognitive DBs — **blocked** (requires R1 ✅)

- After R1 acceptance + offline backup: stop shipping hot path dependence on `memory.db` / `memory.json`.  
- Keep forensic archives outside runtime if needed.  
- Remove legacy read fallthrough only when certified unnecessary.

### R7 — Vectors ADR (decide before delete) — **blocked**

- One decision: ACM semantic **or** single sidecar — not both forever.  
- Until then: keep `memory_vectors.db` + `semantic_memory_adapter_store`.

### R8 — Explicit non-goals

- No `relationship_graph` migration in Batch D.  
- No new façade module.  
- No ACM engine rewrite.  
- No conversation pipeline rewrite for memory.

---

## 5. Files expected to change (when approved)

| Phase | Touch |
|-------|--------|
| R0 | Docs only (`ARCHITECTURE_BIBLE`, `PLATFORM_CUTOVER`, this plan) |
| R1–R2 | `jarvis/modules/memory.py`, `memory_sqlite.py`; possibly `acm_store_facade` **consume** helpers — not ACM redesign |
| R3 | `memory_adapter_store.py` delete; CI + tests |
| R4 | `platform_cutover.py` status/docs; not ACM |
| R5 | `intelligence/memory_platform.py` dead paths |
| R6 | vault paths / fallthrough flags after proof |
| R7 | ADR doc only until decision |

**Do not modify:** ACM cognitive engine internals, AI-Platform as second SoT, Connections graph DB.

---

## 6. Acceptance probes (when implementing)

1. Remember → appears in ACM dashboard / `primary_search`.  
2. Checkpoint upsert → `latest_checkpoint` returns same content (namespace).  
3. Hierarchy tag update → persists under PRIMARY.  
4. Search memory facet → ACM authority strategy.  
5. After R3: supremacy check passes without DualWrite module.  
6. Cert smoke does **not** mint green on memory without probes (add explicit memory probe if cert claims memory health).

---

## 7. Rollback plan

1. Keep ACM DB untouched.  
2. R1–R2: revert adapter divert only; leave ACM data.  
3. R3: restore adapter module from git if CI/process requires (runtime already unused).  
4. Use `ARIA_ACM_ROLLBACK` / legacy read fallback only for emergency forensic — document as temporary.  
5. Never “rollback” by inventing a second cognitive SoT.

---

## 8. Risk register (post-review)

| Risk | Severity | Mitigation |
|------|----------|------------|
| Implement rev-1 D2 (new façade) | Critical | **Forbidden** — rejected by review |
| Delete vault before R1 | High | Gate R6 on R1 acceptance |
| Delete `relationship_graph` as memory cleanup | High | R8 non-goal |
| Blind cutover backfill duplicates | Med | Dry-run parity; prefer no backfill |
| Silent hierarchy tag fail | Med | R2 before hierarchy “simplify” |
| Vectors wiped without ADR | High | R7 gate |
| Cert green without memory probes | Med | §6 probes |
| Doc/UI dual_write lie | Med | R0/R4 |

---

## 9. Approval gate

| Gate | Status |
|------|--------|
| Hostile review published | Done — `MEMORY_TRANSITION_REVIEW.md` |
| Plan revised to match review | Done — this document (rev 2) |
| User accepts review + plan | Done |
| **R1 checkpoint SoT alignment** | **Done** — evidence `batch_d/R1_CHECKPOINT_EVIDENCE.json` |
| R2 hierarchy tags | **Blocked** — request approval |
| R3+ | **Blocked** |
| ACM organ redesign | **Forbidden** |

**Stop:** No R2 work until explicitly approved.
