# Removal Plan — Legacy Aria Memory

**Status:** DESIGN ONLY  
**Rule:** Nothing removed until migration validated (M3 green + UAT). Supremacy Rules 1/3/6.

---

## Phased disposition

| Phase | Removals allowed |
|-------|------------------|
| M0–M2 | **None** — add façades/vendoring only |
| M3 | Stop **writes** to legacy SoT when PRIMARY (reads optional fallback) |
| M4 | Delete/disable cognitive SoT paths; cold vault optional |

---

## Subsystem inventory

| Subsystem | Path(s) | Keep until | Final disposition |
|-----------|---------|------------|-------------------|
| Core memory façade | `aria_core/memory.py`, `memory_manager.py` | Forever (retargeted) | Keep as façade → ACM |
| Memory store JSON/SQLite | `jarvis/modules/memory.py`, `memory_sqlite.py`, `memory_common.py` | M4 (+ rollback window) | **Retire** cognitive SoT; optional cold vault |
| Memory migrate helpers | `jarvis/modules/memory_migrate.py` | M2 harvest | Retire or convert to ACM harvest tool |
| DualWrite adapter | `jarvis/modules/memory_adapter_store.py`, `platform_memory.py` | M2 optional | **Retire** authority |
| Semantic / vectors | `semantic_memory_adapter_store.py`, `vector_store.py`, `memory_embeddings.py`, `platform_semantic_memory.py` | optional plugin | Keep only as Activation plugin; never SoT |
| Hierarchy layer SoT | `jarvis/memory/hierarchy.py` | M3 | Retarget to ACM stages/tags; remove SoT semantics |
| Retrieval diagnostics | `jarvis/memory/retrieval_diagnostics.py` | M3 | Retarget why-codes to ACM; keep Trace hook |
| Behavior engine | `jarvis/behaviors/memory/*` | Forever | Keep action names; purge CRUD store calls |
| Extension API/routes | `jarvis/extensions/memory/*` | Forever | Keep routes; façades |
| Learning writers | `*_learning.py`, `explicit_teaching.py`, `journal_learning.py`, … | M3 | Writers → `encode` only |
| Domain parallel modules | `experience_memory.py`, `relationship_memory.py`, `trust_memory.py` | M3 migrate | **Remove** or thin ACM clients |
| Consolidation SoT | `memory_consolidation.py` | M3 | Replace distill-write with sleep+propose |
| Brain toggles | `brain_memory.py` | Forever | KEEP-HOST flags |
| Graph relationship DB | `jarvis/modules/graph_store.py` | M3 facts migrated | Not cognitive SoT; optional viz |
| Cap Bus registry | `capability_registry.py` remember/recall | Forever | Point to façades |
| Tests tied to CRUD SoT | `tests/test_memory*.py` (subset) | M4 | Rewrite against ACM / façades |

---

## File kill list (M4 candidate — after validation)

Removal PRs only after M3+UAT+rollback window. Exact list verified by CI grep:

**Cognitive SoT writers (must not remain as authority):**

- Direct `MemoryStore.add` / `store.add` from learning modules  
- DualWrite CRUD bridge as primary  
- `experience_memory` / `relationship_memory` parallel persistence (if not rewritten as ACM clients)

**Cold vault (optional):**

- Copy final legacy `memory.db` / `memory.json` to `JARVIS_DATA_DIR/vault/memory_pre_acm_<date>.{db,json}`  
- Read-only; TTL policy operator-defined (default: retain ≥ 90 days)  
- Not queried by Cap Bus when PRIMARY

---

## Sequenced deletion plan (design)

1. **M4a** — CI forbid: no imports of `create_memory_store` outside bridge rollback module.  
2. **M4b** — Remove DualWrite cognitive path; document Platform projection if any.  
3. **M4c** — Delete or stub parallel domain modules.  
4. **M4d** — Remove hierarchy/namespace SoT semantics.  
5. **M4e** — Archive legacy store files to vault; remove active path config.  
6. **M4f** — Update docs (`MEMORY_RETRIEVAL_BEHAVIOR.md`, `aria_core/MEMORY.md`) to ACM-authoritative.

---

## Temporary keep

Legacy store + façades until M4 rollback window closes (see [`ROLLBACK_PLAN.md`](ROLLBACK_PLAN.md)).

## Forbidden “temporary”

Permanent dual write after M3 primary without sunset date — violates Single Cognitive Authority.

## Operator checklist (post-M4)

- [ ] `ARIA_ACM_PRIMARY=true`, rollback flag unused  
- [ ] Legacy write counters = 0 for 7 days  
- [ ] Vault checksum recorded  
- [ ] CI supremacy linters green  
- [ ] DECISION_LOG note: M4 complete
