"""Mixin helpers: MemoryStore backends divert cognitive reads to ACM when authoritative.

Legacy JSON/SQLite remain forensic/vault storage only under PRIMARY.
"""

from __future__ import annotations

from typing import Any


def acm_list_entries(
    entry_type: str | None = None,
    *,
    namespace: str | None = None,
    query: str | None = None,
    include_embedding: bool = False,
) -> list[dict[str, Any]] | None:
    """Return ACM projection when authoritative; else None (caller uses legacy)."""
    from aria_core import acm_bridge

    if not acm_bridge.acm_is_authoritative():
        return None
    rows = acm_bridge.project_list_entries(entry_type, namespace=namespace, query=query, limit=500)
    if include_embedding:
        for r in rows:
            r.setdefault("embedding", None)
    return rows


def acm_search(
    query: str,
    limit: int = 10,
    *,
    namespace: str | None = None,
    user_facing_only: bool = False,
) -> list[dict[str, Any]] | None:
    from aria_core import acm_bridge

    if not acm_bridge.acm_is_authoritative():
        return None
    _ = user_facing_only  # ACM speak path is already user-facing
    return acm_bridge.project_search(query, limit=limit, namespace=namespace)


def acm_get(entry_id: str) -> dict[str, Any] | None:
    from aria_core import acm_bridge

    if not acm_bridge.acm_is_authoritative():
        return None
    return acm_bridge.primary_get(entry_id)


def acm_similar_exists(content: str, threshold: float = 0.88) -> bool | None:
    from aria_core import acm_bridge

    if not acm_bridge.acm_is_authoritative():
        return None
    return acm_bridge.acm_similar_exists(content, threshold=threshold)


def acm_delete_id(entry_id: str) -> bool | None:
    from aria_core import acm_bridge

    if not acm_bridge.acm_is_authoritative():
        return None
    out = acm_bridge.primary_forget(entry_id=entry_id)
    return bool(out.get("ok") or out.get("cooled"))


def acm_update(
    entry_id: str,
    *,
    content: str | None = None,
    entry_type: str | None = None,
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> bool | None:
    from aria_core import acm_bridge

    if not acm_bridge.acm_is_authoritative():
        return None
    if content is None:
        return False
    _ = (entry_type, tags, namespace)
    out = acm_bridge.primary_correct(experience_id=entry_id, text=content)
    return bool(out.get("ok"))
