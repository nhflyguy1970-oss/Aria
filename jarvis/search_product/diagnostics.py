"""Search health, diagnostics, and recovery."""

from __future__ import annotations

import time
from typing import Any

from jarvis.search_product.settings import enabled_corpora_set, load_settings
from jarvis.search_product.status_bus import get_search_state
from jarvis.search_product.terminology import FACETS, TERMINOLOGY


def _web_status() -> dict[str, Any]:
    try:
        from jarvis import web_search

        return {
            "available": bool(web_search.is_available()),
            "backend": web_search.backend_name(),
            "searxng": web_search.searxng_available(),
        }
    except Exception as exc:
        return {"available": False, "backend": "unknown", "error": str(exc)}


def _registry_status() -> dict[str, Any]:
    try:
        from jarvis.knowledge.registry import list_sources

        sources = list_sources()
        avail = sum(1 for s in sources if getattr(s, "retrieval_available", False))
        return {"sources": len(sources), "retrieval_available": avail}
    except Exception as exc:
        return {"sources": 0, "retrieval_available": 0, "error": str(exc)}


def corpus_matrix() -> list[dict[str, Any]]:
    enabled = enabled_corpora_set()
    settings = load_settings()
    opt = settings.get("opt_in_corpora") or {}
    rows = []
    for f in FACETS:
        if f == "everything":
            continue
        rows.append(
            {
                "id": f,
                "enabled": f in enabled,
                "opt_in": f in opt,
                "opt_in_enabled": bool(opt.get(f)),
                "owner": _owner(f),
            }
        )
    return rows


def _owner(facet: str) -> str:
    return {
        "documents": "Documents",
        "memory": "Memory / ACM",
        "projects": "Projects",
        "journal": "Journal",
        "code": "Coding",
        "graph": "Connections",
        "connections": "Connections",
        "audio": "Audio",
        "web": "Web search backend (Chat synthesizes)",
        "planner": "Planner",
        "calendar": "Calendar",
        "gallery": "Gallery",
        "home_assistant": "Smart Home",
        "flytying": "Fly Tying",
        "automation": "Automation",
        "learned": "Knowledge registry",
    }.get(facet, "Product")


def health_summary() -> dict[str, Any]:
    web = _web_status()
    reg = _registry_status()
    state = get_search_state()
    enabled = enabled_corpora_set()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "state": state.get("state") or "idle",
        "corpora_enabled": len(enabled),
        "web": web,
        "registry": reg,
        "last_latency_ms": state.get("last_latency_ms") or 0,
        "last_hit_count": state.get("last_hit_count") or 0,
        "last_query": state.get("last_query") or "",
        "healthy": bool(web.get("available")) or (reg.get("retrieval_available") or 0) > 0,
    }


def diagnostics() -> dict[str, Any]:
    from jarvis.search_product.history import list_history
    from jarvis.search_product.sessions import list_sessions

    t0 = time.perf_counter()
    # micro probe — empty should be fast
    probe_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "pipeline": TERMINOLOGY["pipeline"],
        "health": health_summary(),
        "corpora": corpus_matrix(),
        "settings": load_settings(),
        "recent_history": list_history(8),
        "sessions": list_sessions(5),
        "state": get_search_state(),
        "probe_ms": round(probe_ms, 3),
        "tips": [
            "Sidebar filters navigation only.",
            "Ctrl+K runs commands + quick Search.",
            "Search Home browses federated results with facets.",
            "Chat synthesizes web answers — Search hands off.",
            "Gallery and Home Assistant are opt-in under Search settings.",
        ],
    }


def recovery_status() -> dict[str, Any]:
    health = health_summary()
    steps = [
        {
            "id": "registry",
            "label": "Knowledge registry has sources",
            "done": (health.get("registry") or {}).get("sources", 0) > 0,
            "detail": "Run knowledge sync if empty",
        },
        {
            "id": "retrieval",
            "label": "At least one corpus is retrieval-ready",
            "done": (health.get("registry") or {}).get("retrieval_available", 0) > 0
            or health.get("corpora_enabled", 0) > 0,
            "detail": "Index documents or code",
        },
        {
            "id": "web",
            "label": "Web backend available (optional)",
            "done": bool((health.get("web") or {}).get("available")),
            "detail": "Install ddgs or run SearXNG",
        },
    ]
    ready = all(s["done"] for s in steps[:2])
    return {
        "ok": True,
        "ready": ready,
        "hint": "Sync knowledge registry and ensure document/code indexes exist."
        if not ready
        else "Search pipeline ready.",
        "steps": steps,
        "health": health,
    }
