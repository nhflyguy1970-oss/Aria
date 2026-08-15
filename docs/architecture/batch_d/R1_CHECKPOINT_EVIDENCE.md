# R1 Checkpoint Evidence Summary

**Date:** 2026-07-31  
**Scope:** Checkpoint write/read SoT alignment only  
**Machine evidence:** [`R1_CHECKPOINT_EVIDENCE.json`](./R1_CHECKPOINT_EVIDENCE.json)

## Result

**17/17** scripted checks passed. **42** related pytest cases passed (`test_checkpoint_r1` + host audit + ACM M4 + retrieval consistency).

## Verified

| Check | Result |
|-------|--------|
| Checkpoint create → ACM | Pass |
| Checkpoint update → latest is newest ACM | Pass |
| Checkpoint lookup ignores legacy poison | Pass |
| Project resume workflow | Pass |
| Restart / persist reload | Pass |
| Rollback: write+read both legacy | Pass |
| JSON + SQLite adapter paths | Pass |
| No PRIMARY read from legacy vault | Pass |

## Code impact (R1 only)

| Change | Files |
|--------|-------|
| Added | `acm_bridge.project_latest_checkpoint`, `acm_store_facade.acm_latest_checkpoint`, `tests/test_checkpoint_r1.py` |
| Changed | `MemoryStore.latest_checkpoint`, `SqliteMemoryStore.latest_checkpoint` |
| Deleted | None |
| Not touched | ACM organs, vault delete, DualWrite, graph, hierarchy tags (R2), Connections |

## Next

Request approval for **R2 only** (hierarchy tags-only update). No automatic continuation.
