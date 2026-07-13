# Aria Core Memory — Phase 7

**Status:** Active
**Owner:** `aria_core.memory` (`aria_core.memory_manager`)
**Underneath:** `jarvis.modules.memory` (storage / schema unchanged)

## Behavior (unchanged)

```text
Core Memory API
  → jarvis.modules.memory.MemoryStore
    → existing JSON/SQLite persistence
```

No new storage. No schema changes. No database migration.
Applications and Cap Bus see the same remember/recall results.

## Public API

| API | Role |
|-----|------|
| `remember` | Write via MemoryStore.add |
| `forget` | Delete via delete_id / delete |
| `update_memory` | Update via MemoryStore.update |
| `search_memory` | Search via MemoryStore.search |
| `get_memory` | Get by id |
| `retrieve_context` | Context-oriented search |
| `merge_memories` | Merge via update + delete_id |
| `propose_memory` / `commit_memory` | Proposal + commit (default commit = remember) |
| `rollback_memory` | Delete by id or history mark |
| `memory_history` / `memory_statistics` / `memory_health` | Observability |
| `MemoryStore` / `create_memory_store` | Organ façade |

## Events

MemoryRequested · MemoryCreated · MemoryWritten · MemoryUpdated · MemoryDeleted ·
MemoryRead · MemorySearch · MemoryMerged · MemoryCommit · MemoryRollback

Payloads carry ids/counts/latency only — **not** memory contents.

## Mission Control

**Memory** tab → `aria_core.memory.mission_control_panel()`

Operational visibility: health, reads/writes/searches/merges, history, growth,
duplicate signals, fragmentation proxy, consumers, latency. Contents not shown by default.

## Ownership

From Phase 7 onward, Memory writes go through Aria Core Memory.
Capability Bus `remember` / `recall` call the Core Memory Manager.

## Non-goals

Knowledge / Planning / Reasoning / Runtime migration — **not** this phase.
Persistence rewrite — **not** this phase.
