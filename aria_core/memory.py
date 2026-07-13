"""Aria Core — Memory (delegates to jarvis.modules.memory)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("memory")


def MemoryStore(*args: Any, **kwargs: Any) -> Any:
    """Return the existing Jarvis MemoryStore facade."""
    from jarvis.modules.memory import MemoryStore as _MemoryStore

    return _MemoryStore(*args, **kwargs)


def create_memory_store(*args: Any, **kwargs: Any) -> Any:
    from jarvis.modules.memory import create_memory_store as _create

    return _create(*args, **kwargs)
