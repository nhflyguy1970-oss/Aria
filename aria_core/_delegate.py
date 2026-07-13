"""Shared delegation helpers for Aria Core (Phase 2)."""

from __future__ import annotations

from typing import Any


def soft_import(module_path: str) -> Any | None:
    """Import a module or return None if unavailable."""
    try:
        parts = module_path.split(".")
        mod = __import__(module_path, fromlist=[parts[-1]])
        return mod
    except ImportError:
        return None


def require_import(module_path: str) -> Any:
    """Import a module or raise ImportError with Core context."""
    mod = soft_import(module_path)
    if mod is None:
        raise ImportError(f"Aria Core delegate missing implementation module: {module_path}")
    return mod
