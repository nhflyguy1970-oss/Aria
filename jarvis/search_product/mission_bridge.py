"""Mission Control bridge for Search."""

from __future__ import annotations

from typing import Any


def search_mission_panel() -> dict[str, Any]:
    from jarvis.search_product.diagnostics import health_summary, recovery_status
    from jarvis.search_product.engine import product_status
    from jarvis.search_product.settings import enabled_corpora_set
    from jarvis.search_product.status_bus import get_search_state

    status = product_status()
    health = health_summary()
    recovery = recovery_status()
    state = get_search_state()
    web = health.get("web") or {}
    reg = health.get("registry") or {}
    warnings = []
    if not web.get("available"):
        warnings.append("Web search backend unavailable")
    if (reg.get("retrieval_available") or 0) == 0 and (reg.get("sources") or 0) == 0:
        warnings.append("Knowledge registry empty — sync recommended")
    if state.get("error"):
        warnings.append(str(state.get("error"))[:120])

    return {
        "product": "Search",
        "state": state.get("state") or status.get("state") or "idle",
        "detail": state.get("detail") or state.get("last_query") or "",
        "corpora_enabled": len(enabled_corpora_set()),
        "latency_ms": state.get("last_latency_ms") or 0,
        "last_hit_count": state.get("last_hit_count") or 0,
        "web_backend": web.get("backend"),
        "web_ok": bool(web.get("available")),
        "registry_sources": reg.get("sources") or 0,
        "retrieval_available": reg.get("retrieval_available") or 0,
        "healthy": recovery.get("ready"),
        "warnings": warnings,
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
            "steps_done": sum(1 for s in (recovery.get("steps") or []) if s.get("done")),
            "steps_total": len(recovery.get("steps") or []),
        },
        "errors": [{"severity": "warning", "message": w} for w in warnings[:4]],
        "indexes": {
            "registry_sources": reg.get("sources") or 0,
            "retrieval_available": reg.get("retrieval_available") or 0,
        },
        "embeddings": {
            "note": "Embeddings live in product indexes (documents/code); Search does not own embedders.",
        },
        "deep_links": {
            "home": "#search",
            "status": "/api/search/product",
            "diagnostics": "/api/search/product/diagnostics",
            "recovery": "/api/search/product/recovery",
            "mission": "/api/search/product/mission",
            "query": "/api/search/product/query",
        },
    }
