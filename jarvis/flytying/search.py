"""Unified fly-tying search — Blackfly scraped/gold JSONL only."""

from __future__ import annotations

from typing import Any

from jarvis.flytying import index as recipe_index
from jarvis.flytying.aliases import expand_query
from jarvis.flytying.config import blackfly_data_available


def unified_search(
    q: str | None = None,
    *,
    fly_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    min_quality: float = 0,
    favorites_only: bool = False,
    hook_size: str | int | None = None,
    semantic: bool = True,
) -> dict[str, Any]:
    if not blackfly_data_available():
        return {
            "ok": False,
            "count": 0,
            "total": 0,
            "offset": 0,
            "results": [],
            "search_mode": "unavailable",
            "message": "Blackfly scraped database not found — set JARVIS_FLYTYING_ROOT",
        }

    expanded, alias_terms = expand_query(q or "")
    search_q = expanded or (q or "")
    hook_n: int | None = None
    if hook_size is not None and str(hook_size).strip().isdigit():
        hook_n = int(str(hook_size).strip())

    rows, mode, total = recipe_index.search(
        search_q, fly_type=fly_type, limit=limit, offset=offset, hook_size=hook_n
    )

    if semantic and (q or "").strip() and len((q or "").strip().split()) > 1:
        try:
            from jarvis.flytying import bridge

            hybrid_rows, hybrid_mode = bridge.list_recipes(q=q, fly_type=fly_type, limit=limit)
            if hybrid_mode == "hybrid" and hybrid_rows:
                rows = hybrid_rows
                mode = "hybrid"
        except Exception:
            pass

    if alias_terms and mode == "keyword":
        mode = "alias"

    if min_quality:
        rows = [r for r in rows if float(r.get("quality_score") or 0) >= min_quality]

    if favorites_only:
        try:
            from jarvis.flytying.user_store import list_favorites

            fav = set(list_favorites())
            rows = [r for r in rows if r.get("recipe_id") in fav or r.get("name") in fav]
            total = len(rows)
        except Exception:
            pass

    return {
        "ok": True,
        "count": len(rows),
        "total": total,
        "offset": max(0, int(offset or 0)),
        "results": rows,
        "search_mode": mode,
    }
