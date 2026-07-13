"""Aria Core Memory Manager — authoritative Memory organ (Phase 7).

Storage, schema, and jarvis.modules.memory implementation stay underneath.
Core owns the API, observability, and write path for Cap Bus / future apps.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

PUBLISHER = "aria_core.memory"
MEMORY_VERSION = "2.0-phase7"

_HISTORY: list[dict[str, Any]] = []
_HISTORY_LIMIT = 500
_STATS: dict[str, int] = {
    "reads": 0,
    "writes": 0,
    "searches": 0,
    "updates": 0,
    "deletes": 0,
    "merges": 0,
    "commits": 0,
    "rollbacks": 0,
    "duplicates_detected": 0,
}


def _store(*args: Any, **kwargs: Any) -> Any:
    from jarvis.modules.memory import MemoryStore

    return MemoryStore(*args, **kwargs)


def _emit(name: str, **payload: Any) -> None:
    try:
        from aria_core.event_bus import safe_publish

        safe_publish(name, source=PUBLISHER, **payload)
    except Exception:
        pass


def _bump(key: str) -> None:
    _STATS[key] = int(_STATS.get(key, 0)) + 1


def _record(op: str, **fields: Any) -> dict[str, Any]:
    rec = {
        "id": str(uuid.uuid4()),
        "op": op,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        # Never store memory contents in history by default
        "content_len": fields.pop("content_len", None),
        **fields,
    }
    _HISTORY.append(rec)
    if len(_HISTORY) > _HISTORY_LIMIT:
        del _HISTORY[: len(_HISTORY) - _HISTORY_LIMIT]
    return dict(rec)


def MemoryStore(*args: Any, **kwargs: Any) -> Any:
    """Existing Jarvis MemoryStore facade (organ underneath)."""
    return _store(*args, **kwargs)


def create_memory_store(*args: Any, **kwargs: Any) -> Any:
    from jarvis.modules.memory import create_memory_store as _create

    return _create(*args, **kwargs)


def remember(
    content: str,
    *,
    entry_type: str = "fact",
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> Any:
    """Write memory — delegates to MemoryStore.add."""
    t0 = time.perf_counter()
    store = _store()
    if hasattr(store, "similar_exists") and store.similar_exists(content):
        _bump("duplicates_detected")
    entry = store.add(entry_type, content, tags=tags, namespace=namespace)
    duration_ms = round((time.perf_counter() - t0) * 1000, 3)
    _bump("writes")
    _bump("commits")
    entry_id = (entry or {}).get("id") if isinstance(entry, dict) else None
    _emit("MemoryWritten", entry_id=entry_id, entry_type=entry_type, namespace=namespace)
    _emit("MemoryCreated", entry_id=entry_id, entry_type=entry_type, namespace=namespace)
    _emit("MemoryCommit", entry_id=entry_id, ok=True, duration_ms=duration_ms)
    _record(
        "write",
        entry_id=entry_id,
        entry_type=entry_type,
        namespace=namespace,
        content_len=len(content or ""),
        duration_ms=duration_ms,
        decision="committed",
    )
    return entry


def forget(entry_id: str | None = None, *, index: int | None = None) -> bool:
    """Delete memory — delegates to MemoryStore.delete_id / delete."""
    store = _store()
    ok = False
    if entry_id:
        ok = bool(store.delete_id(entry_id))
    elif index is not None:
        ok = bool(store.delete(index))
    _bump("deletes")
    _emit("MemoryDeleted", entry_id=entry_id, index=index, ok=ok)
    _record("delete", entry_id=entry_id, index=index, ok=ok, decision="deleted" if ok else "miss")
    return ok


def update_memory(
    entry_id: str,
    *,
    content: str | None = None,
    entry_type: str | None = None,
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> bool:
    store = _store()
    ok = bool(
        store.update(
            entry_id,
            content=content,
            entry_type=entry_type,
            tags=tags,
            namespace=namespace,
        )
    )
    _bump("updates")
    _emit("MemoryUpdated", entry_id=entry_id, ok=ok)
    _record(
        "update",
        entry_id=entry_id,
        ok=ok,
        content_len=len(content) if content is not None else None,
        decision="updated" if ok else "miss",
    )
    return ok


def search_memory(
    query: str,
    *,
    limit: int = 10,
    namespace: str | None = None,
) -> list[dict[str, Any]]:
    t0 = time.perf_counter()
    store = _store()
    hits = store.search(query, limit=limit, namespace=namespace)
    duration_ms = round((time.perf_counter() - t0) * 1000, 3)
    _bump("searches")
    _bump("reads")
    # Strip content from event payloads — ids/counts only
    hit_ids = [h.get("id") for h in hits if isinstance(h, dict)]
    _emit("MemorySearch", query_len=len(query or ""), hit_count=len(hits), duration_ms=duration_ms)
    _emit("MemoryRead", hit_count=len(hits), mode="search")
    _record(
        "search",
        query_len=len(query or ""),
        hit_count=len(hits),
        hit_ids=hit_ids[:20],
        duration_ms=duration_ms,
        namespace=namespace,
    )
    return list(hits)


def get_memory(entry_id: str) -> dict[str, Any] | None:
    """Read one memory entry by id — delegates to MemoryStore.get."""
    store = _store()
    hit = store.get(entry_id)
    _bump("reads")
    _emit("MemoryRead", hit_count=1 if hit else 0, mode="get", entry_id=entry_id)
    _record("read", entry_id=entry_id, hit_count=1 if hit else 0, mode="get")
    return hit


def retrieve_context(
    query: str,
    *,
    limit: int = 8,
    namespace: str | None = None,
) -> list[dict[str, Any]]:
    """Context retrieval — same organ search with context-oriented defaults."""
    return search_memory(query, limit=limit, namespace=namespace)


def merge_memories(
    keep_id: str,
    drop_id: str,
    *,
    apply: bool = True,
    separator: str = "\n",
) -> dict[str, Any]:
    """Merge via existing update + delete_id (no schema change)."""
    store = _store()
    keep = store.get(keep_id)
    drop = store.get(drop_id)
    if not keep or not drop:
        return {"ok": False, "error": "entry not found", "keep_id": keep_id, "drop_id": drop_id}
    plan = {
        "ok": True,
        "keep_id": keep_id,
        "drop_id": drop_id,
        "apply": apply,
        "keep_len": len(str(keep.get("content") or "")),
        "drop_len": len(str(drop.get("content") or "")),
    }
    if not apply:
        return plan
    merged = f"{keep.get('content') or ''}{separator}{drop.get('content') or ''}".strip()
    updated = store.update(keep_id, content=merged)
    deleted = store.delete_id(drop_id)
    _bump("merges")
    _bump("updates")
    _bump("deletes")
    _emit("MemoryMerged", keep_id=keep_id, drop_id=drop_id, ok=bool(updated and deleted))
    _emit("MemoryUpdated", entry_id=keep_id, ok=bool(updated))
    _emit("MemoryDeleted", entry_id=drop_id, ok=bool(deleted))
    _record(
        "merge",
        keep_id=keep_id,
        drop_id=drop_id,
        ok=bool(updated and deleted),
        content_len=len(merged),
        decision="merged" if updated and deleted else "partial",
    )
    return {
        "ok": bool(updated and deleted),
        "keep_id": keep_id,
        "drop_id": drop_id,
        "updated": updated,
        "deleted": deleted,
    }


def propose_memory(
    content: str,
    *,
    entry_type: str = "fact",
    tags: list[str] | None = None,
    namespace: str | None = None,
    reason: str = "",
) -> dict[str, Any]:
    """Create a memory proposal (Phase 7: commit still immediate when committed)."""
    proposal = {
        "proposal_id": str(uuid.uuid4()),
        "content_len": len(content or ""),
        "entry_type": entry_type,
        "tags": list(tags or []),
        "namespace": namespace,
        "reason": reason,
        "decision": "pending",
        "ts": time.time(),
        "_content": content,  # private to commit; not exposed in MC panel
    }
    _record(
        "propose",
        proposal_id=proposal["proposal_id"],
        entry_type=entry_type,
        namespace=namespace,
        content_len=proposal["content_len"],
        decision="pending",
        reason=reason,
    )
    return proposal


def commit_memory(proposal: dict[str, Any], apply: Callable[[], T] | None = None) -> Any:
    """Commit memory proposal — default apply writes via remember()."""
    if apply is not None:
        result = apply()
        _bump("commits")
        _emit("MemoryCommit", proposal_id=proposal.get("proposal_id"), ok=True)
        _record(
            "commit",
            proposal_id=proposal.get("proposal_id"),
            decision="committed",
            custom_apply=True,
        )
        return result
    content = proposal.get("_content") or ""
    entry = remember(
        content,
        entry_type=str(proposal.get("entry_type") or "fact"),
        tags=list(proposal.get("tags") or []),
        namespace=proposal.get("namespace"),
    )
    return entry


def rollback_memory(
    proposal_id: str | None = None, *, entry_id: str | None = None
) -> dict[str, Any]:
    """History/mark rollback — does not invent restore storage (Phase 7).

    If entry_id given, forget() via existing delete. Otherwise mark history only.
    """
    if entry_id:
        ok = forget(entry_id)
        _bump("rollbacks")
        _emit("MemoryRollback", entry_id=entry_id, ok=ok)
        return {"ok": ok, "entry_id": entry_id, "mode": "delete"}
    _bump("rollbacks")
    _emit("MemoryRollback", proposal_id=proposal_id, ok=True, mode="history")
    _record("rollback", proposal_id=proposal_id, decision="rolled_back")
    return {"ok": True, "proposal_id": proposal_id, "mode": "history"}


def memory_history(*, limit: int = 100, op: str = "") -> list[dict[str, Any]]:
    items = list(_HISTORY)
    if op:
        items = [r for r in items if r.get("op") == op]
    # Never return private _content
    out = []
    for r in items[-limit:]:
        clean = {k: v for k, v in r.items() if not str(k).startswith("_")}
        out.append(clean)
    return out


def memory_statistics() -> dict[str, Any]:
    store_stats: dict[str, Any] = {}
    try:
        store = _store()
        entries = store.list_entries() if hasattr(store, "list_entries") else []
        namespaces: dict[str, int] = {}
        for e in entries:
            ns = str((e or {}).get("namespace") or "default")
            namespaces[ns] = namespaces.get(ns, 0) + 1
        store_stats = {
            "entry_count": len(entries),
            "namespaces": namespaces,
            "provider": "jarvis.modules.memory",
        }
    except Exception as exc:
        store_stats = {"entry_count": None, "error": type(exc).__name__}
    return {
        "owner": "aria_core.memory",
        "version": MEMORY_VERSION,
        "counters": dict(_STATS),
        "history_size": len(_HISTORY),
        "store": store_stats,
        "duplicates_detected": _STATS.get("duplicates_detected", 0),
    }


def memory_health() -> dict[str, Any]:
    try:
        store = _store()
        _ = store.list_entries() if hasattr(store, "list_entries") else []
        return {
            "ok": True,
            "owner": "aria_core.memory",
            "implementation": "jarvis.modules.memory",
            "store_reachable": True,
        }
    except Exception as exc:
        return {
            "ok": False,
            "owner": "aria_core.memory",
            "implementation": "jarvis.modules.memory",
            "store_reachable": False,
            "error": type(exc).__name__,
        }


def clear_history() -> None:
    _HISTORY.clear()


def reset_stats() -> None:
    for k in _STATS:
        _STATS[k] = 0


def reset_for_tests() -> None:
    clear_history()
    reset_stats()


def mission_control_panel(*, limit: int = 100) -> dict[str, Any]:
    """Operational Memory view — no memory contents by default."""
    stats = memory_statistics()
    health = memory_health()
    hist = memory_history(limit=limit)
    learning_commits = sum(1 for r in hist if r.get("op") in ("write", "commit"))
    counters = stats.get("counters") or {}
    entry_count = (stats.get("store") or {}).get("entry_count")
    namespaces = (stats.get("store") or {}).get("namespaces") or {}
    ns_count = len(namespaces) or 1
    # Fragmentation proxy only — no content inspection / schema change
    fragmentation = {
        "namespace_count": len(namespaces),
        "entries_per_namespace_avg": round((entry_count or 0) / ns_count, 2)
        if entry_count is not None
        else None,
        "duplicate_signals": counters.get("duplicates_detected", 0),
        "note": "Operational proxy; storage layout unchanged",
    }
    latencies = [r.get("duration_ms") for r in hist if r.get("duration_ms") is not None]
    latency = {
        "samples": len(latencies),
        "max_ms": max(latencies) if latencies else None,
        "p50_ms": sorted(latencies)[len(latencies) // 2] if latencies else None,
    }
    return {
        "ok": bool(health.get("ok")),
        "title": "Aria Core Memory",
        "owner": "aria_core.memory",
        "version": MEMORY_VERSION,
        "implementation": "jarvis.modules.memory (underneath)",
        "provider": "aria_core.memory → jarvis.modules.memory",
        "entry_count": entry_count,
        "health": health,
        "statistics": stats,
        "counters": counters,
        "reads": counters.get("reads", 0),
        "writes": counters.get("writes", 0),
        "searches": counters.get("searches", 0),
        "merges": counters.get("merges", 0),
        "learning_commits": learning_commits,
        "duplicates_detected": stats.get("duplicates_detected", 0),
        "duplicate_detection": stats.get("duplicates_detected", 0),
        "growth": entry_count,
        "fragmentation": fragmentation,
        "namespaces": namespaces,
        "history": hist,
        "latency": latency,
        "latency_hint": "see history duration_ms fields",
        "consumers": ["capability_bus", "cognitive_orchestrator", "learning", "nlu/adapters"],
        "note": (
            "Core-owned Memory API; organ storage unchanged. "
            "Operational metadata only — contents not exposed by default."
        ),
    }
