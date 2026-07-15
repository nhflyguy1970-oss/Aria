# Removal Plan — Legacy Aria Memory

**Status:** M4 IMPLEMENTED — see [`LEGACY_RETIREMENT_REPORT.md`](LEGACY_RETIREMENT_REPORT.md)  
**Rule:** Nothing removed until migration validated (M3 green + UAT). Supremacy Rules 1/3/6.

---

## Phased disposition

| Phase | Removals allowed |
|-------|------------------|
| M0–M2 | **None** — add façades/vendoring only |
| M3 | Stop **writes** to legacy SoT when PRIMARY (reads optional fallback) |
| M4 | Delete/disable cognitive SoT paths; cold vault optional — **DONE** |

---

## Subsystem inventory

| Subsystem | Path(s) | Keep until | Final disposition |
|-----------|---------|------------|-------------------|
| Core memory façade | `aria_core/memory.py`, `memory_manager.py` | Forever (retargeted) | Keep as façade → ACM |
| Memory store JSON/SQLite | `jarvis/modules/memory.py`, `memory_sqlite.py`, `memory_common.py` | M4 (+ rollback window) | **Retired as SoT**; vault / ROLLBACK IO only |
| Memory migrate helpers | `jarvis/modules/memory_migrate.py` | M2 harvest | JSON→SQLite legacy helper retained for vault installs |
| DualWrite adapter | `jarvis/modules/memory_adapter_store.py`, `platform_memory.py` | M2 optional | **Retired** (wrap no-op) |
| Semantic / vectors | `semantic_memory_adapter_store.py`, `vector_store.py`, `memory_embeddings.py`, `platform_semantic_memory.py` | optional plugin | Keep only as Activation plugin; never SoT |
| Hierarchy layer SoT | `jarvis/memory/hierarchy.py` | M3 | SoT consolidate disabled under PRIMARY |
| Retrieval diagnostics | `jarvis/memory/retrieval_diagnostics.py` | M3 | Forensic / ROLLBACK ranking |
| Behavior engine | `jarvis/behaviors/memory/*` | Forever | Action names; ACM path |
| Extension API/routes | `jarvis/extensions/memory/*` | Forever | Keep routes; façades |
| Learning writers | `*_learning.py`, `explicit_teaching.py`, `journal_learning.py`, … | M3 | Redirect / encode under PRIMARY |
| Domain parallel modules | `experience_memory.py`, `relationship_memory.py`, `trust_memory.py` | M3 migrate | **ACM clients** (+ KEEP-HOST filters/viz) |
| Consolidation SoT | `memory_consolidation.py` | M3 | Distill → ACM encode |
| Brain toggles | `brain_memory.py` | Forever | KEEP-HOST flags |
| Graph relationship DB | `jarvis/modules/graph_store.py` | M3 facts migrated | Not cognitive SoT; optional viz |
| Cap Bus registry | `capability_registry.py` remember/recall | Forever | Point to façades |
| Tests tied to CRUD SoT | `tests/test_memory*.py` (subset) | M4 | ACM façade tests + forensic PRIMARY=0 |

---

## Sequenced deletion plan — completion

1. **M4a** — CI forbid / redirect legacy SoT writers — **done** (`redirect_legacy_write_to_acm`, supremacy check)  
2. **M4b** — DualWrite cognitive path disabled — **done**  
3. **M4c** — Parallel domain modules → ACM clients — **done**  
4. **M4d** — Hierarchy SoT consolidate disabled under PRIMARY — **done**  
5. **M4e** — Vault operator tool — **done** (`scripts/acm_vault_legacy_memory.py`)  
6. **M4f** — Docs ACM-authoritative — **done** (`MEMORY.md`, `MEMORY_RETRIEVAL_BEHAVIOR.md`)

---

## Operator checklist (post-M4)

- [x] `ARIA_ACM_PRIMARY=true` (default)  
- [x] Rollback flag unused by default  
- [x] Legacy write counters = 0 under PRIMARY (tests)  
- [x] Vault tool + checksum path documented  
- [x] CI supremacy linters green  
- [x] DECISION_LOG note: M4 complete (A006)
