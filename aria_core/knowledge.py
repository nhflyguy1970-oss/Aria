"""Aria Core — Knowledge (delegates to jarvis.knowledge)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("knowledge")


def registry() -> Any:
    from jarvis.knowledge import registry as _registry

    return _registry


def search(query: str, **kwargs: Any) -> Any:
    """Delegate knowledge search when available."""
    try:
        from jarvis.knowledge import search as _search

        if hasattr(_search, "search"):
            return _search.search(query, **kwargs)
        if callable(_search):
            return _search(query, **kwargs)
    except Exception:
        pass
    try:
        from jarvis.knowledge.search import search as _search_fn

        return _search_fn(query, **kwargs)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "query": query, "hits": []}
