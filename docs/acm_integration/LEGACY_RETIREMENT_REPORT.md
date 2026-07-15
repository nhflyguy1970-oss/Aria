# Legacy Retirement Report — M4

**Date:** 2026-07-15  
**Decision:** A006  
**Status:** Complete (M4)

For every blueprint-scheduled retirement, ACM replacement, migration, validation, removal, and rollback.

| Legacy component | Purpose | ACM replacement | Migration | Validation | Removed / disabled | Rollback available | Verification |
|------------------|---------|-----------------|-----------|------------|--------------------|--------------------|--------------|
| Cap Bus / Core memory as CRUD SoT | Authoritative remember/recall | `acm_bridge` → `CognitiveEngine` encode/remember | M2 harvest + M3 PRIMARY + M4 default on | M3-01..06, M4 sole-SoT tests | Authority retired; façades kept | `ARIA_ACM_ROLLBACK` window → legacy façades; post-window ACM snapshot | PASS |
| `MemoryStore.add` cognitive writes | JSON/SQLite SoT writes | `redirect_legacy_write_to_acm` → Cap Bus encode | N/A (live redirect) | `test_m4_store_add_redirects_to_acm` | Writes redirected under PRIMARY | ROLLBACK disables redirect | PASS |
| DualWrite `memory_adapter_store` | Platform CRUD dual SoT | None (Platform projection only if re-enabled emergency) | N/A | M4-02, supremacy CI | **Disabled by default** (`memory_adapter_enabled=False`) | `JARVIS_ALLOW_DUALWRITE_LEGACY` + not ACM authoritative | PASS |
| Platform `JARVIS_PLATFORM_DATA_AUTHORITATIVE` | Platform as read SoT | Forbidden | N/A | adapter tests | Returns false when DualWrite retired | Emergency DualWrite allow flag | PASS |
| `experience_memory` parallel persist | success/failure CRUD | `primary_remember` ACM client | M4c | M4-03 | Writers → ACM under PRIMARY | ROLLBACK + store.add | PASS |
| `relationship_memory` parallel persist | Graph relationship SoT | ACM encode + graph **viz only** | M4c | M4-03 | Cognitive → ACM; graph KEEP-HOST viz | ROLLBACK Cap Bus remember | PASS |
| `trust_memory` cognitive writers | strategy/failure SoT | ACM encode | M4c | M4-03 | Writers → ACM; KEEP-HOST filters retained | ROLLBACK store path | PASS |
| `memory_consolidation` distill-write | LLM distill → MemoryStore | ACM `primary_remember` | M4c | consolidation path under PRIMARY | Distill SoT write retired | ROLLBACK store.add | PASS |
| Hierarchy `consolidate` promote/prune | Layer SoT mutation | No-op under PRIMARY (ACM accessibility) | M4d | `test_m4_hierarchy_consolidate_noop` | SoT mutate disabled when ACM auth | ROLLBACK restores legacy consolidate | PASS |
| Legacy read fallback default | Supplement ACM with legacy | Off | M4 | supremacy source check | Default `ARIA_ACM_LEGACY_READ_FALLBACK=0` | Env `=1` optional | PASS |
| Shadow permanent dual authority | Dual measure | Ended as product path | M1–M2 phase | Docs | Shadow optional forensic only; PRIMARY default on | N/A | PASS |
| Active legacy DB as Cap Bus SoT | memory.json/db | ACM persist path | M2 harvest; operator vault tool | vault script | Cognitive authority removed; files optional vault | `scripts/acm_vault_legacy_memory.py`; ROLLBACK | PASS |
| Learning `*.add` bypass writers | Parallel autobiography | Redirection + Cap Bus | M4a | redirect + supremacy | Closed when PRIMARY | ROLLBACK | PASS |
| CRUD-authority tests | Assert MemoryStore SoT | Rewritten / PRIMARY-off forensic | M4 | CI 445 passed | Retrieval quality pinned PRIMARY=0 forensic | N/A | PASS |

## Not deleted (blueprint temporary keep / KEEP-HOST)

| Component | Reason |
|-----------|--------|
| `jarvis/modules/memory.py` / sqlite / memory_common | Façade + ROLLBACK/harvest/vault IO; not Cap Bus SoT |
| `aria_core/memory_manager.py` | Forever façade → ACM |
| `jarvis/behaviors/memory/*` | Action names kept; ACM path when PRIMARY |
| `trust_memory` filters / scrubbers | KEEP-HOST policy |
| `graph_store` | Optional viz — not cognitive SoT after M4 |
| `brain_memory` toggles | KEEP-HOST flags |
| `ARIA_ACM_ROLLBACK` flag | M4 rollback window only (pre ACM-snapshot-only era) |
| DualWrite class body | Archival; wrap is no-op |

## Operator checklist

- [x] `ARIA_ACM_PRIMARY` default **true**
- [x] Rollback flag unused by default
- [x] Legacy write counters 0 under PRIMARY (SUP-02 / M4 tests)
- [x] Vault tool available (`scripts/acm_vault_legacy_memory.py`)
- [x] CI supremacy linters green (`scripts/acm_supremacy_check.py`)
- [x] DECISION_LOG A006 M4 complete

## Post-M4 rollback

Per `ROLLBACK_PLAN.md`: prefer ACM snapshot restore. Reintroducing legacy as product primary requires new DECISION_LOG + Rule 6 re-certification.
