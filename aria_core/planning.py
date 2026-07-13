"""Aria Core — Planning (delegates to jarvis.agents / planner)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("planning")


def coordinator_available() -> bool:
    try:
        from jarvis.agents import coordinator  # noqa: F401

        return True
    except ImportError:
        return False


def get_coordinator() -> Any:
    from jarvis.agents import coordinator

    return coordinator


def planner_store_path() -> str | None:
    try:
        from jarvis import planner_store

        path = getattr(planner_store, "DB_PATH", None) or getattr(planner_store, "_DB", None)
        return str(path) if path else None
    except Exception:
        return None
