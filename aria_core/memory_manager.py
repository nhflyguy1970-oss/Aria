"""Aria Core Memory Manager — authoritative Memory organ (Phase 7).

Storage, schema, and jarvis.modules.memory implementation stay underneath.
Core owns the API, observability, and write path for Cap Bus / future apps.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

PUBLISHER = "aria_core.memory"
MEMORY_VERSION = "2.0-phase7"

_LOCK = threading.RLock()
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
    "retrievals": 0,
    "superseded": 0,
    "ranking_decisions": 0,
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
    with _LOCK:
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
    with _LOCK:
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
    """Write memory.

    M3: when ARIA_ACM_PRIMARY (and not ROLLBACK), encode via ACM — no legacy SoT write.
    M1 Shadow: optional dual-call after legacy write when still legacy-authoritative.
    """
    from aria_core import acm_bridge

    if acm_bridge.acm_is_authoritative():
        # SUP-02: never fall through to MemoryStore while ACM is authoritative.
        t0 = time.perf_counter()
        entry = acm_bridge.primary_remember(
            content, entry_type=entry_type, tags=tags, namespace=namespace
        )
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
            authoritative="acm",
            acm_verb="encode",
            user_visible_changed=True,
        )
        return entry

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
    shadow_meta: dict[str, Any] | None = None
    try:
        shadow_meta = acm_bridge.shadow_remember_after_legacy(
            content, entry_type=entry_type, tags=tags, namespace=namespace
        )
    except Exception:
        shadow_meta = None
    _record(
        "write",
        entry_id=entry_id,
        entry_type=entry_type,
        namespace=namespace,
        content_len=len(content or ""),
        duration_ms=duration_ms,
        decision="committed",
        authoritative="legacy",
        acm_verb=(shadow_meta or {}).get("acm_verb"),
        shadow_ms=(shadow_meta or {}).get("duration_ms"),
        user_visible_changed=False,
    )
    return entry


def forget(entry_id: str | None = None, *, index: int | None = None) -> bool:
    """Delete / cool memory.

    M3 PRIMARY: soft cool via ACM (never hard-delete Experiences).
    """
    from aria_core import acm_bridge

    if acm_bridge.acm_is_authoritative():
        out = acm_bridge.primary_forget(entry_id=entry_id)
        ok = bool(out.get("ok") or out.get("cooled"))
        _bump("deletes")
        _emit("MemoryDeleted", entry_id=entry_id, index=index, ok=ok, soft=True)
        _record(
            "delete",
            entry_id=entry_id,
            index=index,
            ok=ok,
            decision="cooled" if ok else "miss",
            authoritative="acm",
            acm_verb="cool",
        )
        return ok

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
    from aria_core import acm_bridge

    if acm_bridge.acm_is_authoritative() and content is not None:
        out = acm_bridge.primary_correct(experience_id=entry_id, text=content)
        ok = bool(out.get("ok"))
        _bump("updates")
        _emit("MemoryUpdated", entry_id=entry_id, ok=ok)
        _record(
            "update",
            entry_id=(out.get("entry") or {}).get("id") or entry_id,
            ok=ok,
            content_len=len(content),
            decision="revised" if ok else "miss",
            authoritative="acm",
            acm_verb="revise",
        )
        return ok

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
    """Search / recall memory.

    M3 PRIMARY: ACM what_do_i_remember (optional empty→legacy read fallback).
    M1 Shadow: dual-call after legacy search when legacy-authoritative.
    """
    from aria_core import acm_bridge

    if acm_bridge.acm_is_authoritative():
        t0 = time.perf_counter()
        hits = acm_bridge.primary_search(query, limit=limit, namespace=namespace)
        if (
            not hits
            and acm_bridge.legacy_read_fallback_enabled()
            and not acm_bridge.rollback_enabled()
        ):
            store = _store()
            legacy_hits = store.search(query, limit=limit, namespace=namespace)
            if legacy_hits:
                acm_bridge.note_legacy_fallback_read()
                hits = list(legacy_hits)
                for h in hits:
                    if isinstance(h, dict):
                        h.setdefault("source", "legacy_fallback")
        duration_ms = round((time.perf_counter() - t0) * 1000, 3)
        _bump("searches")
        _bump("reads")
        hit_ids = [h.get("id") for h in hits if isinstance(h, dict)]
        _emit(
            "MemorySearch",
            query_len=len(query or ""),
            hit_count=len(hits),
            duration_ms=duration_ms,
        )
        _emit("MemoryRead", hit_count=len(hits), mode="search")
        last = acm_bridge.last_primary_op() or {}
        _record(
            "search",
            query_len=len(query or ""),
            hit_count=len(hits),
            hit_ids=hit_ids[:20],
            duration_ms=duration_ms,
            namespace=namespace,
            authoritative="acm",
            acm_verb="cognitive_respond",
            shadow_ms=last.get("duration_ms"),
            user_visible_changed=True,
        )
        return list(hits)

    t0 = time.perf_counter()
    store = _store()
    hits = store.search(query, limit=limit, namespace=namespace)
    duration_ms = round((time.perf_counter() - t0) * 1000, 3)
    _bump("searches")
    _bump("reads")
    hit_ids = [h.get("id") for h in hits if isinstance(h, dict)]
    _emit("MemorySearch", query_len=len(query or ""), hit_count=len(hits), duration_ms=duration_ms)
    _emit("MemoryRead", hit_count=len(hits), mode="search")
    shadow_meta: dict[str, Any] | None = None
    try:
        shadow_meta = acm_bridge.shadow_search_after_legacy(query, list(hits))
    except Exception:
        shadow_meta = None
    _record(
        "search",
        query_len=len(query or ""),
        hit_count=len(hits),
        hit_ids=hit_ids[:20],
        duration_ms=duration_ms,
        namespace=namespace,
        authoritative="legacy",
        acm_verb=(shadow_meta or {}).get("acm_verb"),
        shadow_agree=(shadow_meta or {}).get("shadow_agree"),
        shadow_ms=(shadow_meta or {}).get("duration_ms"),
        user_visible_changed=False,
    )
    return list(hits)


def get_memory(entry_id: str) -> dict[str, Any] | None:
    """Read one memory entry by id."""
    from aria_core import acm_bridge

    if acm_bridge.acm_is_authoritative():
        hit = acm_bridge.primary_get(entry_id)
        _bump("reads")
        _emit("MemoryRead", hit_count=1 if hit else 0, mode="get", entry_id=entry_id)
        _record(
            "read",
            entry_id=entry_id,
            hit_count=1 if hit else 0,
            mode="get",
            authoritative="acm",
        )
        if hit:
            return hit
        if acm_bridge.legacy_read_fallback_enabled():
            store = _store()
            legacy = store.get(entry_id)
            if legacy:
                acm_bridge.note_legacy_fallback_read()
                return legacy
        return None

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
    """Merge keep+drop contents; M4 uses revise+cool when ACM authoritative."""
    from aria_core import acm_bridge

    if acm_bridge.acm_is_authoritative():
        keep = acm_bridge.primary_get(keep_id)
        drop = acm_bridge.primary_get(drop_id)
        if not keep or not drop:
            return {
                "ok": False,
                "error": "entry not found",
                "keep_id": keep_id,
                "drop_id": drop_id,
                "authoritative": "acm",
            }
        plan = {
            "ok": True,
            "keep_id": keep_id,
            "drop_id": drop_id,
            "apply": apply,
            "keep_len": len(str(keep.get("content") or "")),
            "drop_len": len(str(drop.get("content") or "")),
            "authoritative": "acm",
        }
        if not apply:
            return plan
        merged = f"{keep.get('content') or ''}{separator}{drop.get('content') or ''}".strip()
        revised = acm_bridge.primary_correct(experience_id=keep_id, text=merged)
        cooled = acm_bridge.primary_forget(entry_id=drop_id)
        ok = bool(revised.get("ok")) and bool(cooled.get("ok") or cooled.get("cooled") or True)
        new_id = (revised.get("entry") or {}).get("id") or keep_id
        _bump("merges")
        _bump("updates")
        _bump("deletes")
        _emit("MemoryMerged", keep_id=new_id, drop_id=drop_id, ok=ok)
        _emit("MemoryUpdated", entry_id=new_id, ok=bool(revised.get("ok")))
        _emit("MemoryDeleted", entry_id=drop_id, ok=True, soft=True)
        _record(
            "merge",
            keep_id=new_id,
            drop_id=drop_id,
            ok=ok,
            authoritative="acm",
            acm_verb="revise+cool",
        )
        return {**plan, "ok": ok, "keep_id": new_id}

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
    )
    return {**plan, "ok": bool(updated and deleted)}


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
    with _LOCK:
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
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            dash = acm_bridge.acm_dashboard()
            return {
                "owner": "aria_acm",
                "version": "acm-cognitive-dashboard.v1",
                "counters": dash.get("cognitive_activity") or {},
                "history_size": len(dash.get("recent_cognitive_events") or []),
                "store": {
                    "entry_count": dash.get("entry_count"),
                    "experiences": (dash.get("experiences") or {}).get("count"),
                    "concepts": (dash.get("concepts") or {}).get("count"),
                    "provider": "aria_acm",
                },
                "duplicates_detected": 0,
            }
    except Exception:
        pass
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
    with _LOCK:
        counters = dict(_STATS)
        history_size = len(_HISTORY)
        duplicates = _STATS.get("duplicates_detected", 0)
    return {
        "owner": "aria_core.memory",
        "version": MEMORY_VERSION,
        "counters": counters,
        "history_size": history_size,
        "store": store_stats,
        "duplicates_detected": duplicates,
    }


def memory_health() -> dict[str, Any]:
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            dash = acm_bridge.acm_dashboard()
            mh = dash.get("memory_health") or {}
            return {
                "ok": bool(mh.get("ok", True)),
                "owner": "aria_acm",
                "implementation": "embedded ACM (aria_acm)",
                "store_reachable": bool(mh.get("cognitive_store_reachable", True)),
                "experience_count": mh.get("experience_count"),
                "concept_count": mh.get("concept_count"),
            }
    except Exception:
        pass
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
    with _LOCK:
        _HISTORY.clear()


def reset_stats() -> None:
    with _LOCK:
        for k in _STATS:
            _STATS[k] = 0


def record_retrieval_decision(decision: dict[str, Any]) -> dict[str, Any]:
    """Record ranking/retrieval diagnostics — ids and scores only, never contents."""
    _bump("retrievals")
    _bump("searches")
    _bump("ranking_decisions")
    clean = {
        "query_len": len(str(decision.get("query") or "")),
        "normalized_query": str(decision.get("normalized_query") or "")[:80],
        "intent": decision.get("intent"),
        "selected_id": decision.get("selected_id"),
        "selected_type": decision.get("selected_type"),
        "candidate_count": decision.get("candidate_count"),
        "confidence": decision.get("confidence"),
        "ranking_latency_ms": decision.get("ranking_latency_ms"),
        "reason_selected": decision.get("reason_selected"),
        "rejected_count": len(decision.get("rejected") or []),
        "decision": "ranked",
        "duration_ms": decision.get("ranking_latency_ms"),
    }
    return _record("retrieval", **clean)


def record_update_supersede(
    *,
    new_id: str | None,
    superseded_ids: list[str] | None = None,
    topic: str = "",
    removed: int = 0,
) -> dict[str, Any]:
    """Record that an update superseded prior active facts on the same topic."""
    _bump("updates")
    for _ in superseded_ids or []:
        _bump("superseded")
    return _record(
        "update",
        entry_id=new_id,
        superseded_ids=list(superseded_ids or [])[:8],
        topic=(topic or "")[:80],
        removed=removed,
        decision="supersede",
    )


def reset_for_tests() -> None:
    clear_history()
    reset_stats()
    try:
        from aria_core import acm_bridge

        acm_bridge.reset_for_tests()
    except Exception:
        pass


def mission_control_panel(*, limit: int = 100) -> dict[str, Any]:
    """Operational Memory view — ACM Cognitive Dashboard when authoritative."""
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            return acm_bridge.acm_dashboard(limit=limit)
    except Exception:
        pass
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
    retrieval_rows = [r for r in hist if r.get("op") == "retrieval"]
    ranking_latencies = [
        r.get("ranking_latency_ms") or r.get("duration_ms")
        for r in retrieval_rows
        if (r.get("ranking_latency_ms") or r.get("duration_ms")) is not None
    ]
    update_rows = [r for r in hist if r.get("op") == "update" or r.get("decision") == "supersede"]
    delete_rows = [r for r in hist if r.get("op") in ("delete", "forget")]
    active_facts = None
    superseded_facts = counters.get("superseded", 0)
    duplicate_groups = counters.get("duplicates_detected", 0)
    try:
        store = _store()
        entries = store.list_entries() if hasattr(store, "list_entries") else []
        active_facts = sum(
            1
            for e in entries
            if e.get("type") in ("fact", "preference")
            and "superseded" not in (e.get("tags") or [])
            and e.get("type") not in ("strategy", "auto", "failure")
        )
        superseded_facts = sum(1 for e in entries if "superseded" in (e.get("tags") or []))
    except Exception:
        pass
    latency = {
        "samples": len(latencies),
        "max_ms": max(latencies) if latencies else None,
        "p50_ms": sorted(latencies)[len(latencies) // 2] if latencies else None,
        "avg_retrieval_ms": (
            round(sum(ranking_latencies) / len(ranking_latencies), 3) if ranking_latencies else None
        ),
        "avg_ranking_ms": (
            round(sum(ranking_latencies) / len(ranking_latencies), 3) if ranking_latencies else None
        ),
    }
    # Lifecycle metadata only — never contents.
    lifecycle_counts: dict[str, int] = {
        "created": 0,
        "updated": 0,
        "merged": 0,
        "referenced": 0,
        "last_used": 0,
    }
    lifecycle_rows: list[dict[str, Any]] = []
    for r in hist:
        op = str(r.get("op") or "")
        stage = {
            "write": "created",
            "commit": "created",
            "update": "updated",
            "merge": "merged",
            "read": "referenced",
            "search": "referenced",
            "hit": "last_used",
        }.get(op, op or "unknown")
        if stage in lifecycle_counts:
            lifecycle_counts[stage] += 1
        lifecycle_rows.append(
            {
                "id": r.get("entry_id") or r.get("id"),
                "iso": r.get("iso"),
                "stage": stage,
                "op": op,
                "confidence": r.get("confidence"),
                "origin": r.get("origin") or r.get("namespace") or r.get("source") or "memory",
                "consumers": r.get("consumers")
                or ["capability_bus", "cognitive_orchestrator", "learning"],
                "last_used_ts": r.get("ts"),
                "duration_ms": r.get("duration_ms"),
            }
        )
    shadow_block: dict[str, Any] = {
        "shadow_enabled": False,
        "authoritative": "legacy",
        "note": "M1 Shadow off / ROLLBACK path",
    }
    try:
        from aria_core import acm_bridge

        shadow_block = acm_bridge.panel_observables()
    except Exception as exc:
        shadow_block = {
            "shadow_enabled": False,
            "authoritative": "legacy",
            "error": type(exc).__name__,
        }
    return {
        "ok": bool(health.get("ok")),
        "title": "Aria Core Memory (ROLLBACK)",
        "owner": "aria_core.memory",
        "version": MEMORY_VERSION,
        "implementation": "jarvis.modules.memory (ROLLBACK only)",
        "provider": "aria_core.memory → jarvis.modules.memory",
        "authoritative": shadow_block.get("authoritative", "legacy"),
        "entry_count": entry_count,
        "health": health,
        "statistics": stats,
        "counters": counters,
        "reads": counters.get("reads", 0),
        "writes": counters.get("writes", 0),
        "updates": counters.get("updates", 0) or len(update_rows),
        "deletes": counters.get("deletes", 0) or len(delete_rows),
        "retrievals": counters.get("retrievals", 0) or len(retrieval_rows),
        "searches": counters.get("searches", 0),
        "merges": counters.get("merges", 0),
        "learning_commits": learning_commits,
        "duplicates_detected": stats.get("duplicates_detected", 0),
        "duplicate_detection": stats.get("duplicates_detected", 0),
        "duplicate_groups": duplicate_groups,
        "active_facts": active_facts,
        "superseded_facts": superseded_facts,
        "ranking_decisions": counters.get("ranking_decisions", 0) or len(retrieval_rows),
        "growth": entry_count,
        "fragmentation": fragmentation,
        "namespaces": namespaces,
        "history": hist,
        "retrieval_history": retrieval_rows[-limit:],
        "memory_health": {
            "ok": bool(health.get("ok")),
            "active_facts": active_facts,
            "superseded_facts": superseded_facts,
            "duplicate_groups": duplicate_groups,
            "avg_retrieval_ms": latency.get("avg_retrieval_ms"),
            "avg_ranking_ms": latency.get("avg_ranking_ms"),
        },
        "lifecycle": {
            "stages": [
                "Created",
                "Updated",
                "Merged",
                "Referenced",
                "Last Used",
                "Confidence",
                "Origin",
                "Consumers",
            ],
            "counts": lifecycle_counts,
            "rows": lifecycle_rows[-limit:],
            "note": "Lifecycle metadata only — memory contents are not exposed by default.",
        },
        "latency": latency,
        "latency_hint": "see history duration_ms fields",
        "shadow": shadow_block,
        "consumers": ["capability_bus", "cognitive_orchestrator", "learning", "nlu/adapters"],
        "note": (
            "ROLLBACK façade only. With ARIA_ACM_PRIMARY (default), "
            "mission_control_panel returns acm_dashboard() instead."
        ),
        "legacy_disconnected": False,
    }
