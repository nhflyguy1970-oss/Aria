# Memory Transition Review (Hostile Design Review)

**Date:** 2026-07-31  
**Scope:** Transition plan only — ACM is permanent and **not** under review.  
**Code changes:** None (review + plan update only).  
**Verdict:** The original Batch D plan is **materially wrong**. Implementing it as written would increase complexity and risk data loss / silent regressions.

---

## 1. Executive verdict

| Claim in original plan | Reality |
|------------------------|---------|
| D2: build new `jarvis.memory_api` façade | **Wrong.** Write façade already exists (`aria_core/memory_manager` + `redirect_legacy_write_to_acm`). Read façade already exists (`aria_core/acm_store_facade`). A third façade violates Bible (“one public API”) and the plan’s own non-goal. |
| D3: migrate reads to ACM | **Largely done.** `list_entries` / `get` / `search` / `stats` / `export` / Search `retrieve_memory` already prefer ACM when `acm_is_authoritative()`. |
| Convert MemoryStore to ACM adapter then delete vault | **Half wrong.** Conversion **already shipped**. Delete of vaults is premature until `latest_checkpoint` is fixed. |
| `memory_adapter_store` risk Low; delete after flag check | **Understated process risk.** Runtime is triple-off, but CI (`acm_supremacy_check`) + tests import it — same-commit update required. |
| `relationship_graph.db` is memory-SoT conflict (Med) | **Misframed.** It backs **Connections / graph_store**, not cognitive ACM. Risk if deleted = **High** product breakage. Not Batch D cognitive work. |
| Rollback flag `JARVIS_MEMORY_LEGACY_READ` | **Invented.** Real flags: `ARIA_ACM_PRIMARY` (default on), `ARIA_ACM_ROLLBACK`, `ARIA_ACM_LEGACY_READ_FALLBACK`. |
| Path `jarvis/aria_core/acm_bridge.py` | **Wrong path.** Real: `aria_core/acm_bridge.py` (sibling of `jarvis/`). |
| Inventory complete | **Missing:** `semantic_memory_adapter_store.py` (hot import on every `MemoryStore()`), `aria_core/acm_store_facade.py`, `aria_core/memory_manager.py`, vault scripts, `brain_memory.py` (KEEP — not SoT). |

**Measured ground truth (this host):**

| File | Size | Last modified |
|------|------|----------------|
| `data/acm/cognitive.db` | ~236 MB | **today (hot)** |
| `data/memory.db` | 258 KB | Jul 23 (cold) |
| `data/memory.json` | 27 KB | Jun 26 (cold) |
| `data/memory_vectors.db` | 3.3 MB | Jul 30 |
| `data/relationship_graph.db` | 40 KB | Jul 27 |

`acm_is_authoritative()` → **True** (ARIA_ACM_PRIMARY defaults to on).  
`memory_adapter_enabled()` → **False**.  
`wrap_memory_store` → **identity**.

---

## 2. What already works (do not rebuild)

```
Remember / add
  → MemoryStore.add
  → redirect_legacy_write_to_acm
  → ACM (raises if redirect fails — legacy write fenced)

Recall / list / search / stats / export
  → acm_store_facade first when authoritative
  → Search retrieve_memory → acm_bridge.primary_search first
```

**Bible alignment:** Cognitive SoT is already ACM. Transition work is **cleanup of dead theater + fix remaining split-brain reads**, not a greenfield migration.

---

## 3. Challenge every original recommendation

### 3.1 Retire `platform_cutover` dual_write for cognitive memory

| Question | Answer |
|----------|--------|
| What breaks if dual_write UI disappears? | Cutover Mission Control panels / `/api/platform/cutover*` status — not chat remember/recall |
| Who depends? | Ops UI, docs `PLATFORM_CUTOVER.md` |
| Delete now? | **Not the whole module.** Label cognitive dual_write obsolete; stop implying memory still dual-writes |
| Safer order? | After documenting ACM-only in Bible; before deleting vaults |
| Data loss? | No if ACM untouched |
| Silent failure? | Today: cutover can claim dual_write while adapter is no-op — **already a silent lie** |

**Review recommendation:** Keep cutover shell; **honest status** for memory (“ACM authoritative; dual_write N/A”). Do not “migrate via cutover backfill” as primary path — ACM harvest/vault scripts already exist.

### 3.2 Delete `memory_adapter_store.py`

| Question | Answer |
|----------|--------|
| What breaks? | Runtime: nothing if flags stay off. CI: `scripts/acm_supremacy_check.py`, `tests/test_memory_adapter.py`, `tests/test_aria_acm_m4.py` |
| Can delete now? | **Yes, with same-commit CI/test updates** |
| Safer order? | First cleanup item after freeze docs |

### 3.3 “Convert MemoryStore then delete sqlite/json”

| Question | Answer |
|----------|--------|
| Convert? | **Already done** — do not re-convert |
| Delete vaults now? | **No.** `latest_checkpoint` still reads `self._data["entries"]` / SQL while `upsert_checkpoint` writes ACM → **live stale checkpoint recall** |
| Who depends on MemoryStore class? | `assistant.py`, `general.py`, `memory_manager`, harvest, behaviors, ~18 tests — **must keep class as ACM adapter façade** |
| Could delete create data loss? | Deleting vault before checkpoint fix → **no**; deleting vault while `latest_checkpoint` unfixed → **functional regression** (empty checkpoints), not ACM data loss |
| Silent failure? | **Yes today:** checkpoint write succeeds to ACM; resume reads empty legacy → silent wrong UX |

**Review recommendation:** Rename mental model to “MemoryStore = ACM adapter (keep)”; vault delete only after checkpoint divert.

### 3.4 Fold / delete `memory_vectors.db` + semantic adapters

| Question | Answer |
|----------|--------|
| What breaks? | `create_embedding_sidecar` → **unconditional** import of `semantic_memory_adapter_store`; EmbeddingSidecar / legacy semantic search |
| Can delete now? | **No** without replacing sidecar construction |
| Must stay temp? | **Yes** until D5 ADR (one vector SoT) |
| Missing from plan? | **Yes — critical omission** |

### 3.5 `relationship_graph.db`

| Question | Answer |
|----------|--------|
| Cognitive SoT conflict? | **No** — separate Connections/graph product |
| Delete in Batch D? | **Forbidden** without separate Connections migration |
| Risk if removed? | High — ~21 call sites (`connections_services`, router relationship recall, conversation) |

**Review recommendation:** Remove from cognitive Batch D scope. Track under Connections / graph ADR.

### 3.6 Collapse `memory/hierarchy.py`

| Question | Answer |
|----------|--------|
| What breaks? | `/api/memory/hierarchy`, consolidate, chat actions |
| Hidden bug? | Tags-only `memory.update(..., tags=)` → `acm_update` returns False when `content is None` → **hierarchy tags never persist under PRIMARY** |
| Delete now? | **No** |
| Must fix before consolidate trust? | **Yes** — otherwise “simplify hierarchy” papers over silent no-op |

### 3.7 Align/delete `intelligence/memory_platform.py`

| Question | Answer |
|----------|--------|
| Dead code? | Hostile review found `export_memories` / `import_memories` / `search_memories` call nonexistent module-level APIs → permanent soft-fail |
| Delete whole file? | **No** — routes still register; fix or thin first |
| Safer? | Delete/repair **dead functions** first; keep route surface until ACM-native intel API |

### 3.8 Retarget `behaviors/memory/engine.py`

| Question | Answer |
|----------|--------|
| Already ACM-aware? | **Yes** in places (`acm_bridge.primary_*`) |
| “Retarget to ACM API” as big rewrite? | **Overkill** — keep engine; fix callers of broken `latest_checkpoint` |
| Risk of rewrite? | High regression on 18 chat actions |

### 3.9 Thin `extensions/memory/`

| Question | Answer |
|----------|--------|
| Delete extension? | **No** — 30+ REST routes; Memory GUI |
| Change? | Ensure routes use ACM-authoritative store methods (most already do via MemoryStore) |

### 3.10 `memory_candidates.json`

| Question | Answer |
|----------|--------|
| Delete now? | **No** — Memory UI candidate review |
| Cognitive SoT? | Staging, not ACM SoT — separate cleanup |

### 3.11 Cutover backfill as one-shot migrate-to-ACM

| Question | Answer |
|----------|--------|
| Needed? | Cognitive data already in ACM (hot DB). Backfill from cold vault may **duplicate or confuse** if run blindly |
| Safer? | Use existing vault/export scripts; verify counts; do **not** mass-backfill without dry-run parity |

---

## 4. Critical live defect the plan missed

### Split-brain: checkpoints

```
upsert_checkpoint (PRIMARY) → ACM via add()
latest_checkpoint           → legacy self._data["entries"] only  ❌
```

Callers: `behaviors/memory/engine.py` (~188, 291, 887) — project resume / checkpoint recall.

| Risk | Severity |
|------|----------|
| Stale / empty checkpoint after remember | **High** |
| User thinks project state saved; resume fails | **High** |
| Certification/smoke may not cover checkpoint | Medium |

**Must be first implementation item** when Batch D is approved — still **no ACM redesign**, only divert read through ACM projection (same pattern as `list_entries`).

---

## 5. Dependency matrix (challenged)

| Artifact | Can delete now? | Must keep temp? | Breakage if removed now |
|----------|-----------------|-----------------|-------------------------|
| ACM `cognitive.db` / `acm_bridge` | **Never** | — | Total |
| `modules/memory.py` MemoryStore class | **No** | Yes — **is** the adapter | Assistant boot fails |
| `modules/memory_sqlite.py` | No | Yes | Default backend construction |
| `memory_adapter_store.py` | Yes + CI update | No | Tests/CI only |
| `semantic_memory_adapter_store.py` | No alone | Yes | Every `MemoryStore()` import path |
| `data/memory.db` / `memory.json` | Not until checkpoint fix + vault | Yes vault | Checkpoint + rollback forensic |
| `memory_vectors.db` | No | Yes pending ADR | Sidecar / semantic |
| `relationship_graph.db` | **Out of scope** | Yes | Connections product |
| `memory/hierarchy.py` | No | Yes (+ tags fix) | Hierarchy APIs |
| `intelligence/memory_platform.py` | Partial dead fns | Yes | Intel routes |
| `behaviors/memory/` | No | Yes | Chat memory actions |
| `extensions/memory/` | No | Yes | Memory GUI |
| `brain_memory.py` | No (not SoT conflict) | Keep | Feeds |
| `platform_memory` attach | Soft-fail often | Optional cleanup | Boot noise |
| Search `retrieve_memory` | No | Yes | Federated memory facet |
| Cert product | Barely touches memory | — | Don’t conflate with OS “memory” audit |

---

## 6. Sequencing improvements (safer than original D1–D5)

Original D2/D3 **rebuild façades** → rejected.

### Revised order (lower risk)

| Step | Work | Why first |
|------|------|-----------|
| **R0** | Freeze docs: Bible + PLATFORM_CUTOVER say ACM-only cognitive; invent no new flags | Prevent dual narratives |
| **R1** | Fix `latest_checkpoint` (+ sqlite twin) to ACM projection | Kill live split-brain |
| **R2** | Fix tags-only update / hierarchy persist under PRIMARY | Kill silent no-op |
| **R3** | Delete `memory_adapter_store` + update supremacy CI/tests | Dead dual-write theater |
| **R4** | Honest cutover status for cognitive memory; stop dual_write as cognitive story | Remove lying UI |
| **R5** | Dead function cleanup in `intelligence/memory_platform` (no behavior change) | Reduce false failures |
| **R6** | Vault cold `memory.db`/`memory.json` after R1 proven; keep offline backup | Forensic only |
| **R7** | ADR: vectors (`memory_vectors`) vs ACM semantic — **decide before delete** | Avoid data loss |
| **R8** | Explicitly exclude `relationship_graph` from cognitive Batch D | Ownership clarity |

**Do not:** introduce `jarvis.memory_api`.  
**Do not:** mass cutover backfill without dry-run.  
**Do not:** delete MemoryStore class.  
**Do not:** modify ACM engine internals.

---

## 7. Bible / certification / search / workflow concerns

| Area | Concern | Plan impact |
|------|---------|-------------|
| Architecture Bible | Must state MemoryStore is **adapter**, not competing SoT | Update on R0 |
| Search | Already ACM-first; empty ACM fallthrough to local is intentional safety | Keep fallthrough until vault gone; then remove |
| Certification | Smoke suites barely exercise memory; checkpoint bug won’t fail cert | Add acceptance probes for remember + checkpoint + search when implementing |
| Conversation | Context already ACM-aware in places | Don’t rewrite conversation for Batch D |
| Events / Activity | Not memory SoT | Out of scope |
| PLATFORM_CUTOVER.md | Still describes dual_write as memory mode | **Violates Bible** until R0/R4 — doc lie is itself a defect |

---

## 8. Data loss / stale / silent failure checklist

| Failure mode | Present today? | Original plan worsen? |
|--------------|----------------|----------------------|
| Checkpoint stale | **Yes** | Yes if vault deleted before R1 |
| Hierarchy tags silent fail | **Yes** | Yes if “collapse hierarchy” without fix |
| Dual-write theater lie | **Yes** | Improved by R3/R4 |
| New façade drift | No | **Yes if D2 executed** |
| Vector wipe without ADR | No | Yes if D5 rushed as delete |
| Graph wipe as “memory cleanup” | No | Yes if relationship_graph in Batch D |
| Blind backfill duplicates | Possible | Yes if cutover backfill treated as migrate |

---

## 9. Would another engineer approve the original plan?

**No.** It asks to rebuild completed work, invents flags/paths, mis-scopes Connections graph as cognitive memory, and misses the only production split-brain still on the hot path.

---

## 10. Gate for implementation

Implementation of Batch D remains **not approved** until:

1. This review is accepted.  
2. Revised plan (below) is accepted.  
3. Explicit go-ahead for **R1+ only** (or a named subset).

ACM code / engine remains untouched unless a later approval explicitly allows **read-path diversion in MemoryStore** (adapter layer), not ACM redesign.
