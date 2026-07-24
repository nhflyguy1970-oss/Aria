# Production ACM Memory — Empty Start

**Date:** 2026-07-23  
**Status:** Production operational baseline

## Policy

For production deployment, ACM starts with an **empty** autobiographical store.

- ACM is the **single source of truth** for all cognitive memory operations.
- The Aria Memory UI is a **presentation layer** over ACM (PRIMARY), not an independent memory implementation.
- Legacy JSON/SQLite memory files under `data/` are forensic vault only and are not cognitive SoT under `ARIA_ACM_PRIMARY=1`.

## Empty-start procedure

```bash
# Stop Aria (release SQLite locks)
./scripts/jarvis-ctl.sh stop

# Destroy live durable store WITHOUT archiving (production wipe)
.venv/bin/python scripts/acm_cognitive_memory_reset.py --no-archive

# Validate empty + architecture
.venv/bin/python scripts/acm_cognitive_memory_reset.py --validate-only
```

Default persist path: `$JARVIS_DATA_DIR/acm/cognitive.db`  
(typically `/media/jeff/AI/jarvis/data/acm/cognitive.db`)

Retained after reset:

- SQLite schema (`meta`, `snapshots`, `ops`)
- Empty identity schema shells (≤3 concept nuclei)
- Optional structural agent `name` from `ARIA_ACM_AGENT_ID` (not autobiographical content)

Removed:

- All experiences, associations, goals, adaptations, learned concepts
- WAL/SHM sidecars
- Development/test/synthetic autobiographical content

## Memory UI → ACM

| UI operation | Backend |
|--------------|---------|
| Browse / search | `acm_list_entries` / `project_list_entries` |
| Add | `memory.add` → ACM encode |
| Edit | `acm_update` → `primary_correct` |
| Delete / forget | `acm_delete_id` → `primary_forget` (cool) |
| Stats / namespaces | `acm_stats` / `acm_namespaces` |
| Export | `acm_export_data` |
| Profile reset | cool/forget profile namespace via ACM |
| Mission Control memory tab | `acm_dashboard` |

Host-only surfaces (not ACM cognition): cheatsheets, memory settings toggles, env preference catalog cache.

Under `ARIA_ACM_PRIMARY=1` (production default), Memory REST (`/api/memory/*`) and Mission Control memory panels read/write exclusively through ACM projections (`acm_store_facade` / `acm_bridge`). Legacy JSON/SQLite vault files remain on disk for forensics only.
