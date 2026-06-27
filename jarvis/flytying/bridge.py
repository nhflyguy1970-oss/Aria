"""Bridge to the Blackfly fly-tying scraped dataset (external project)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from jarvis.flytying import index as recipe_index
from jarvis.flytying.config import (
    blackfly_data_available,
    blackfly_enablement,
    ensure_blackfly_on_path,
    gold_recipes_path,
    images_root,
    scraped_dataset_path,
)
from jarvis.flytying.export import compare_recipes, export_recipe
from jarvis.flytying.hatch import hatch_context
from jarvis.flytying.library_health import library_health
from jarvis.flytying.search import unified_search
from jarvis.flytying.stats import read_status
from jarvis.flytying.substitutions import substitutions_for_recipe

API_VERSION = 3
_blackfly_ready: bool | None = None
_blackfly_checked_at: float = 0
_BLACKFLY_RETRY_SEC = 120


def reset_blackfly_cache() -> None:
    global _blackfly_ready, _blackfly_checked_at
    _blackfly_ready = None
    _blackfly_checked_at = 0


def _prepare_blackfly(*, force: bool = False) -> bool:
    global _blackfly_ready, _blackfly_checked_at
    now = time.monotonic()
    if not force and _blackfly_ready is not None and now - _blackfly_checked_at < _BLACKFLY_RETRY_SEC:
        return bool(_blackfly_ready)
    ready = False
    if blackfly_data_available():
        ensure_blackfly_on_path()
        try:
            import blackfly_rag  # noqa: F401

            ready = True
        except Exception:
            ready = False
    _blackfly_ready = ready
    _blackfly_checked_at = now
    return ready


def available() -> bool:
    return _prepare_blackfly()


def gold_available() -> bool:
    return blackfly_data_available()


def status() -> dict[str, Any]:
    st = read_status()
    st["api_version"] = API_VERSION
    st["blackfly_import"] = _prepare_blackfly()
    st["semantic_usable"] = bool(st["blackfly_import"])
    if st.get("blackfly_loaded") and st.get("semantic_usable"):
        st["index_note"] = "Blackfly scraped DB + semantic (blackfly_rag)"
    elif st.get("blackfly_loaded"):
        st["index_note"] = "Blackfly scraped DB — keyword/alias search (install blackfly_rag for semantic)"
    else:
        st["index_note"] = "Blackfly scraped database missing"
    try:
        st["library_health"] = library_health()
    except Exception:
        pass
    try:
        from jarvis.flytying.nightly import pattern_of_the_day

        st["pattern_of_the_day"] = pattern_of_the_day()
    except Exception:
        pass
    try:
        st["hatch"] = hatch_context()
    except Exception:
        pass
    return st


def build_gold(**kwargs) -> dict[str, Any]:
    if not blackfly_data_available() and not scraped_dataset_path().is_file():
        return {"ok": False, "message": "Blackfly scraped dataset missing"}
    ensure_blackfly_on_path()
    try:
        from blackfly_ai import DATASET_PATH  # type: ignore
        from blackfly_gold import build_gold_dataset, gold_path  # type: ignore
        import blackfly_rag as br  # type: ignore
    except Exception as exc:
        return {"ok": False, "message": f"Blackfly build modules unavailable: {exc}"}
    source = kwargs.get("source") or DATASET_PATH
    stats = build_gold_dataset(
        source,
        gold_path(),
        min_quality=float(kwargs.get("min_quality", 70)),
        min_materials=int(kwargs.get("min_materials", 2)),
        min_steps=int(kwargs.get("min_steps", 2)),
    )
    index_result: dict[str, Any] = {}
    if kwargs.get("build_index", True):
        index_result = br.GLOBAL_GOLD_INDEX.build()
    recipe_index.invalidate()
    reset_blackfly_cache()
    return {"ok": True, "stats": stats, "index": index_result}


def _recipe_name(recipe: dict[str, Any]) -> str:
    return str(recipe.get("fly_name") or recipe.get("name") or recipe.get("instruction") or "Unknown")


def _format_recipe_plain(recipe: dict[str, Any]) -> str:
    name = _recipe_name(recipe)
    fly_type = recipe.get("type") or "?"
    lines = [f"**{name}** ({fly_type})"]
    if recipe.get("hook"):
        lines.append(f"Hook: {recipe['hook']}")
    mats = recipe.get("materials") or []
    if mats:
        lines.append("Materials: " + "; ".join(str(m) for m in mats[:20]))
    steps = recipe.get("steps") or []
    if steps:
        lines.append("")
        lines.append("Steps:")
        for i, step in enumerate(steps[:25], 1):
            lines.append(f"{i}. {step}")
    return "\n".join(lines)


def _enrich_search_row(row: dict[str, Any], recipe: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(row)
    if recipe:
        from jarvis.flytying.media import recipe_videos, resolve_recipe_images

        subs = substitutions_for_recipe(recipe)
        if subs:
            out["substitutions"] = subs
        images = resolve_recipe_images(recipe)
        if images:
            out["thumbnail"] = images[0].get("url", "")
            out["image_urls"] = [img.get("url", "") for img in images if img.get("url")]
        videos = recipe_videos(recipe)
        if videos:
            out["videos"] = videos
            if not out.get("thumbnail") and videos[0].get("thumbnail"):
                out["thumbnail"] = videos[0]["thumbnail"]
    return out


def search_recipes(query: str | None, *, fly_type: str | None = None, limit: int = 20, **kwargs) -> list[dict[str, Any]]:
    payload = unified_search(query or "", fly_type=fly_type, limit=limit, **kwargs)
    rows = list(payload.get("results") or [])
    results: list[dict[str, Any]] = []
    for row in rows:
        rid = str(row.get("recipe_id") or row.get("name") or "")
        recipe = recipe_index.find_recipe(rid)
        enriched = _enrich_search_row(row, recipe)
        enriched["search_mode"] = payload.get("search_mode")
        results.append(enriched)
    return results


def get_recipe(name_or_id: str | None) -> dict[str, Any] | None:
    recipe = recipe_index.find_recipe(name_or_id or "")
    if not recipe:
        return None
    from jarvis.flytying.media import recipe_videos, resolve_recipe_images

    formatted = _format_recipe_plain(recipe)
    name = _recipe_name(recipe)
    rid = str(recipe.get("recipe_id") or recipe.get("content_hash") or "")
    if _prepare_blackfly():
        try:
            from blackfly_rag import format_recipe_card, recipe_id as bf_recipe_id, recipe_name as bf_recipe_name

            formatted = format_recipe_card(recipe)
            name = bf_recipe_name(recipe)
            rid = bf_recipe_id(recipe)
        except Exception:
            pass
    images = resolve_recipe_images(recipe)
    videos = recipe_videos(recipe)
    thumb = ""
    if images:
        thumb = images[0].get("url", "")
    elif recipe.get("hero_image"):
        thumb = str(recipe.get("hero_image"))
    elif videos and videos[0].get("thumbnail"):
        thumb = str(videos[0]["thumbnail"])
    payload: dict[str, Any] = {
        "ok": True,
        "name": name,
        "recipe_id": rid,
        "type": recipe.get("type") or "",
        "hook": recipe.get("hook") or "",
        "quality_score": float(recipe.get("quality_score") or 0),
        "materials": recipe.get("materials") or [],
        "steps": recipe.get("steps") or [],
        "source_url": recipe.get("source_url") or "",
        "images": images,
        "image_urls": [img.get("url", "") for img in images if img.get("url")],
        "videos": videos,
        "thumbnail": thumb,
        "recipe": recipe,
        "formatted": formatted,
    }
    subs = substitutions_for_recipe(recipe)
    if subs:
        payload["substitutions"] = subs
    try:
        similar = recipe_index.similar_recipes(rid or name, limit=6)
        if similar:
            payload["similar"] = similar
    except Exception:
        pass
    return payload


def ask_fly_tying(question: str | None, *, fly_type: str | None = None, limit: int = 4) -> dict[str, Any]:
    from jarvis.flytying.chat import chat_turn

    result = chat_turn([{"role": "user", "content": question or ""}], fly_type=fly_type)
    hits = search_recipes(question, fly_type=fly_type, limit=limit)
    return {
        "ok": result.get("ok", False),
        "message": result.get("message", ""),
        "answer": result.get("answer", ""),
        "recipes": hits or result.get("recipes") or [],
        "model": result.get("model"),
    }


def export_recipe_markdown(name_or_id: str | None, *, fmt: str = "markdown") -> str | None:
    row = get_recipe(name_or_id)
    if not row:
        return None
    recipe = row.get("recipe") if isinstance(row.get("recipe"), dict) else row
    return export_recipe(recipe, fmt=fmt)


def compare_recipes_by_id(ids: list[str]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for rid in ids:
        row = get_recipe(rid)
        if not row:
            continue
        recipe = row.get("recipe") if isinstance(row.get("recipe"), dict) else row
        rows.append(recipe)
    if not rows:
        return {"ok": False, "message": "no recipes found"}
    return {"ok": True, "count": len(rows), "markdown": compare_recipes(rows), "recipes": rows}


def seasonal_suggestions(*, month: int | None = None, limit: int = 8) -> dict[str, Any]:
    ctx = hatch_context(month=month)
    terms = list(ctx.get("hatches") or []) + list(ctx.get("suggest_types") or [])
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for term in terms:
        for hit in search_recipes(str(term), limit=3):
            rid = str(hit.get("recipe_id") or hit.get("name") or "")
            if not rid or rid in seen:
                continue
            seen.add(rid)
            results.append(hit)
            if len(results) >= limit:
                break
        if len(results) >= limit:
            break
    return {"ok": True, "hatch": ctx, "results": results[:limit]}


def list_recipes(*, q: str | None = None, fly_type: str | None = None, limit: int = 50):
    cap = max(1, min(limit, 500))
    needle = (q or "").strip()
    rows, mode, _total = recipe_index.search(q, fly_type=fly_type, limit=cap)
    if needle and len(needle.split()) > 1 and _prepare_blackfly():
        try:
            from blackfly_rag import hybrid_search, recipe_id as bf_recipe_id

            type_filter = (fly_type or "").strip().lower()
            semantic_rows: list[dict[str, Any]] = []
            seen: set[str] = set()
            for recipe in hybrid_search(needle, fly_type=None, limit=cap):
                rid = str(bf_recipe_id(recipe))
                if rid in seen:
                    continue
                rtype = str(recipe.get("type") or "").lower()
                if type_filter and rtype != type_filter:
                    continue
                seen.add(rid)
                semantic_rows.append(recipe_index.recipe_row(recipe))
            if semantic_rows:
                merged: list[dict[str, Any]] = []
                seen_ids: set[str] = set()
                for row in semantic_rows + rows:
                    rid = str(row.get("recipe_id") or row.get("name") or "")
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                    merged.append(row)
                merged.sort(key=lambda r: (-float(r.get("quality_score") or 0), r.get("name", "").lower()))
                return merged[:cap], "hybrid"
        except Exception:
            pass
    return rows, mode


def suggest_from_materials(materials: list[str] | None, *, limit: int = 8) -> list[dict[str, Any]]:
    mats = [str(m).strip().lower() for m in (materials or []) if str(m).strip()]
    if not mats or not blackfly_data_available():
        return []
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in recipe_index.recipes():
        blob = " ".join(
            [
                _recipe_name(item).lower(),
                " ".join(str(x).lower() for x in (item.get("materials") or [])),
                " ".join(str(x).lower() for x in (item.get("steps") or [])),
            ]
        )
        hits = sum(1 for m in mats if m in blob)
        if hits:
            scored.append((hits, recipe_index.recipe_row(item)))
    scored.sort(key=lambda pair: (-pair[0], -float(pair[1].get("quality_score") or 0), pair[1].get("name", "").lower()))
    return [row for _, row in scored[: max(1, limit)]]


def list_videos(*, q: str | None = None, limit: int = 50):
    if not blackfly_data_available():
        return []
    from jarvis.flytying.media import list_all_videos

    return list_all_videos(q=q or "", limit=limit, recipes=recipe_index.recipes())


def resolve_image_file(name: str | None) -> Path | None:
    root = images_root().resolve()
    if not name or ".." in name.replace("\\", "/"):
        return None
    candidate = (root / Path(name)).resolve()
    try:
        if candidate.is_file() and candidate.is_relative_to(root):
            return candidate
    except ValueError:
        return None
    return None
