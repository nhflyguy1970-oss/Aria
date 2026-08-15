"""Unified fly-tying search — Blackfly scraped/gold JSONL only."""

from __future__ import annotations

from typing import Any

from jarvis.flytying import index as recipe_index
from jarvis.flytying.aliases import query_variants
from jarvis.flytying.config import blackfly_data_available


def _rank_rows(rows: list[dict[str, Any]], q: str) -> list[dict[str, Any]]:
    """Prefer name hits for what Jeff typed; then quality."""
    needle = (q or "").strip().lower()
    tokens = [t for t in needle.split() if t]

    def key(r: dict[str, Any]) -> tuple:
        name = str(r.get("name") or "").lower()
        if needle and needle in name:
            name_rank = 0
        elif tokens and all(t in name for t in tokens):
            name_rank = 1
        elif tokens and any(t in name for t in tokens):
            name_rank = 2
        else:
            name_rank = 3
        return (name_rank, -float(r.get("quality_score") or 0), name)

    return sorted(rows, key=key)


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

    hook_n: int | None = None
    if hook_size is not None and str(hook_size).strip().isdigit():
        hook_n = int(str(hook_size).strip())

    raw_q = (q or "").strip()
    variants, alias_terms = query_variants(raw_q)
    if not variants:
        variants = [""]

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    mode = "browse"
    for variant in variants:
        rows, m, _total = recipe_index.search(
            variant, fly_type=fly_type, limit=max(limit, 80), offset=0, hook_size=hook_n
        )
        if m not in ("browse", "empty", "unavailable"):
            mode = "alias" if alias_terms else m
        elif not raw_q:
            mode = m
        for r in rows:
            rid = str(r.get("recipe_id") or r.get("name") or "")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            merged.append(r)

    if semantic and raw_q and len(raw_q.split()) > 1:
        try:
            from jarvis.flytying import bridge

            hybrid_rows, hybrid_mode = bridge.list_recipes(q=raw_q, fly_type=fly_type, limit=limit)
            if hybrid_mode == "hybrid" and hybrid_rows:
                for r in hybrid_rows:
                    rid = str(r.get("recipe_id") or r.get("name") or "")
                    if not rid or rid in seen:
                        continue
                    seen.add(rid)
                    merged.append(r)
                mode = "hybrid"
        except Exception:
            pass

    if min_quality:
        merged = [r for r in merged if float(r.get("quality_score") or 0) >= min_quality]

    if favorites_only:
        try:
            from jarvis.flytying.user_store import list_favorites

            fav = set(list_favorites())
            merged = [r for r in merged if r.get("recipe_id") in fav or r.get("name") in fav]
        except Exception:
            pass

    ranked = _rank_rows(merged, raw_q)
    off = max(0, int(offset or 0))
    lim = max(1, int(limit or 50))
    page = ranked[off : off + lim]

    return {
        "ok": True,
        "count": len(page),
        "total": len(ranked),
        "offset": off,
        "results": page,
        "search_mode": mode,
    }
