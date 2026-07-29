"""Unified search across all knowledge sources — delegates to Search product engine."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.knowledge.search")

# Re-export strategy helpers for tests that import _pick_strategies / _search_memory
from jarvis.knowledge import search_legacy as _legacy  # noqa: E402

_pick_strategies = _legacy._pick_strategies
_search_memory = _legacy._search_memory
_search_documents = _legacy._search_documents
_search_code = _legacy._search_code
_search_journal = _legacy._search_journal
_search_project_docs = _legacy._search_project_docs
_search_learned = _legacy._search_learned
_STRATEGY_HINTS = _legacy._STRATEGY_HINTS


def unified_search(
    query: str,
    *,
    limit: int = 12,
    refresh_registry: bool = False,
    facets: list[str] | None = None,
) -> dict[str, Any]:
    """Search all knowledge sources via the one Search engine; legacy hit shape for chat/palette."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "query required", "hits": []}

    if refresh_registry:
        try:
            from jarvis.knowledge.registry import sync_registry

            sync_registry()
        except Exception as exc:
            logger.debug("registry refresh: %s", exc)

    from jarvis.search_product.contract import to_legacy_hit
    from jarvis.search_product.pipeline import run_search

    # Default federation excludes opt-in gallery/HA unless settings enable them.
    result = run_search(
        query,
        facets=facets,
        limit=limit,
        record_history=True,
        session=False,
    )
    hits = [to_legacy_hit(r) for r in (result.get("results") or [])]
    return {
        "ok": bool(result.get("ok")),
        "query": query,
        "strategies": result.get("corpora") or [],
        "searched": result.get("searched") or [],
        "hit_count": len(hits),
        "hits": hits,
        "results": result.get("results") or [],
        "latency_ms": result.get("latency_ms"),
        "intent": result.get("intent"),
        "contract": "SearchResult",
        "pipeline": "shared_search_pipeline",
        "sources_available": len(result.get("corpora") or []),
        "error": result.get("error"),
    }


def format_unified_results(result: dict[str, Any]) -> str:
    if result.get("results") is not None and result.get("pipeline") == "shared_search_pipeline":
        try:
            from jarvis.search_product.pipeline import format_search_message

            # Prefer contract results when present
            wrapped = {
                "ok": result.get("ok"),
                "query": result.get("query"),
                "results": result.get("results"),
                "searched": result.get("searched"),
                "error": result.get("error"),
                "web_handoff": None,
            }
            return format_search_message(wrapped)
        except Exception:
            pass
    if not result.get("ok"):
        return f"Search failed: {result.get('error', 'unknown error')}"
    query = result.get("query", "")
    hits = result.get("hits") or []
    if not hits:
        return f"No matches for **{query}** across workstation knowledge."
    lines = [
        f"**Unified search:** _{query}_",
        f"_{len(hits)} result(s) from {', '.join(result.get('searched') or result.get('strategies') or [])}_",
        "",
    ]
    for hit in hits:
        label = hit.get("source_label") or hit.get("source_type")
        title = hit.get("title") or "untitled"
        excerpt = (hit.get("excerpt") or "").strip().replace("\n", " ")[:280]
        lines.append(f"- **[{label}]** {title} — {excerpt}")
    return "\n".join(lines)
