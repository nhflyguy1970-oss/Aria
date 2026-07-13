"""Aria Core — Memory public API (Phase 7 Core-owned)."""

from __future__ import annotations

from aria_core import memory_manager as _mgr
from aria_core.ownership import module_ownership

OWNER = module_ownership("memory")

MemoryStore = _mgr.MemoryStore
create_memory_store = _mgr.create_memory_store
remember = _mgr.remember
forget = _mgr.forget
update_memory = _mgr.update_memory
search_memory = _mgr.search_memory
get_memory = _mgr.get_memory
retrieve_context = _mgr.retrieve_context
merge_memories = _mgr.merge_memories
propose_memory = _mgr.propose_memory
commit_memory = _mgr.commit_memory
rollback_memory = _mgr.rollback_memory
memory_history = _mgr.memory_history
memory_statistics = _mgr.memory_statistics
memory_health = _mgr.memory_health
mission_control_panel = _mgr.mission_control_panel

__all__ = [
    "OWNER",
    "MemoryStore",
    "commit_memory",
    "create_memory_store",
    "forget",
    "get_memory",
    "memory_health",
    "memory_history",
    "memory_statistics",
    "merge_memories",
    "mission_control_panel",
    "propose_memory",
    "remember",
    "retrieve_context",
    "rollback_memory",
    "search_memory",
    "update_memory",
]
