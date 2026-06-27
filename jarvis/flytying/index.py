"""In-memory index over Blackfly JSONL (scraped dataset or gold library)."""

from __future__ import annotations

import json
import threading
from typing import Any

from jarvis.flytying.config import blackfly_data_available, recipe_source_path
from jarvis.flytying.hook_utils import hook_matches_filter

_CACHE: dict[str, Any] = {
    "mtime": 0,
    "path": "",
    "recipes": [],
    "by_id": {},
    "by_name": {},
    "browse_sorted": [],
    "browse_rows": [],
}
_LOCK = threading.Lock()


def _recipe_name(item: dict[str, Any]) -> str:
    return str(item.get("fly_name") or item.get("name") or item.get("instruction") or "")


def _recipe_id(item: dict[str, Any]) -> str:
    return str(item.get("recipe_id") or item.get("content_hash") or item.get("id") or _recipe_name(item))


def _search_blob(item: dict[str, Any]) -> str:
    parts = [
        _recipe_name(item),
        str(item.get("type") or ""),
        str(item.get("hook") or ""),
        " ".join(str(m) for m in (item.get("materials") or [])),
        " ".join(str(s) for s in (item.get("steps") or [])),
        str(item.get("instruction") or ""),
        str(item.get("output") or ""),
    ]
    return " ".join(parts).lower()


def _recipe_lookup_rank(item: dict[str, Any]) -> tuple[int, float]:
    has_local = bool(item.get("saved_image_paths"))
    return (1 if has_local else 0, float(item.get("quality_score") or 0))


def _recipe_row(item: dict[str, Any], *, include_images: bool = False) -> dict[str, Any]:
    name = _recipe_name(item)
    row = {
        "recipe_id": _recipe_id(item),
        "name": name,
        "type": item.get("type") or "",
        "hook": item.get("hook") or "",
        "quality_score": float(item.get("quality_score") or 0),
        "steps_count": len(item.get("steps") or []),
    }
    if include_images:
        try:
            from jarvis.flytying.media import resolve_recipe_images

            images = resolve_recipe_images(item)
            if images:
                row["thumbnail"] = images[0].get("url", "")
                row["image_urls"] = [img.get("url", "") for img in images if img.get("url")]
        except Exception:
            pass
    return row


def _load() -> None:
    if not blackfly_data_available():
        _CACHE["mtime"] = 0
        _CACHE["path"] = ""
        _CACHE["recipes"] = []
        _CACHE["by_id"] = {}
        _CACHE["by_name"] = {}
        _CACHE["browse_sorted"] = []
        _CACHE["browse_rows"] = []
        return
    path = recipe_source_path()
    mtime = path.stat().st_mtime if path.is_file() else 0
    path_s = str(path)
    if _CACHE["mtime"] == mtime and _CACHE["path"] == path_s and _CACHE["recipes"]:
        return
    recipes: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    by_name: dict[str, dict[str, Any]] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(item, dict):
                continue
            recipes.append(item)
            rid = _recipe_id(item)
            name = _recipe_name(item).lower()
            by_id[rid] = item
            if name:
                prev = by_name.get(name)
                if prev is None or _recipe_lookup_rank(item) > _recipe_lookup_rank(prev):
                    by_name[name] = item
    _CACHE["mtime"] = mtime
    _CACHE["path"] = path_s
    _CACHE["recipes"] = recipes
    _CACHE["by_id"] = by_id
    _CACHE["by_name"] = by_name
    browse_sorted = sorted(
        recipes,
        key=lambda item: (-float(item.get("quality_score") or 0), _recipe_name(item).lower()),
    )
    _CACHE["browse_sorted"] = browse_sorted
    _CACHE["browse_rows"] = [_recipe_row(item) for item in browse_sorted]


def invalidate() -> None:
    with _LOCK:
        _CACHE["mtime"] = 0
        _CACHE["path"] = ""
        _CACHE["browse_sorted"] = []
        _CACHE["browse_rows"] = []
    try:
        from jarvis.cache_state import invalidate_flytying_list_cache

        invalidate_flytying_list_cache()
    except Exception:
        pass


def recipes() -> list[dict[str, Any]]:
    with _LOCK:
        _load()
        return list(_CACHE["recipes"])


def find_recipe(name_or_id: str | None) -> dict[str, Any] | None:
    needle = str(name_or_id or "").strip()
    if not needle:
        return None
    with _LOCK:
        _load()
        if needle in _CACHE["by_id"]:
            return _CACHE["by_id"][needle]
        lower = needle.lower()
        if lower in _CACHE["by_name"]:
            return _CACHE["by_name"][lower]
        matches = [item for item in _CACHE["recipes"] if _recipe_name(item).lower() == lower]
        if matches:
            matches.sort(key=lambda item: _recipe_lookup_rank(item), reverse=True)
            return matches[0]
    return None


def search(
    q: str | None,
    *,
    fly_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
    hook_size: int | None = None,
) -> tuple[list[dict[str, Any]], str, int]:
    if not blackfly_data_available():
        return [], "unavailable", 0
    with _LOCK:
        _load()
        items = list(_CACHE["recipes"])
    if not items:
        return [], "empty", 0
    needle = str(q or "").strip().lower()
    type_filter = str(fly_type or "").strip().lower()
    off = max(0, int(offset or 0))
    lim = max(1, limit)

    def _sort_key(item: dict[str, Any]) -> tuple[float, str]:
        return (-float(item.get("quality_score") or 0), _recipe_name(item).lower())

    if not needle:
        with _LOCK:
            _load()
            sorted_items = list(_CACHE.get("browse_sorted") or [])
            row_cache = list(_CACHE.get("browse_rows") or [])
        if type_filter:
            keep = [
                i
                for i, item in enumerate(sorted_items)
                if str(item.get("type") or "").lower() == type_filter
            ]
            sorted_items = [sorted_items[i] for i in keep]
            row_cache = [row_cache[i] for i in keep]
        if hook_size is not None:
            keep = [
                i
                for i, item in enumerate(sorted_items)
                if hook_matches_filter(item.get("hook"), size=hook_size)
            ]
            sorted_items = [sorted_items[i] for i in keep]
            row_cache = [row_cache[i] for i in keep]
        page_rows = row_cache[off : off + lim] if row_cache else [
            _recipe_row(item) for item in sorted_items[off : off + lim]
        ]
        return page_rows, "browse", len(sorted_items)
    matched: list[dict[str, Any]] = []
    tokens = [t for t in needle.split() if t]
    for item in items:
        if type_filter and str(item.get("type") or "").lower() != type_filter:
            continue
        if hook_size is not None and not hook_matches_filter(item.get("hook"), size=hook_size):
            continue
        blob = _search_blob(item)
        if needle in blob or all(tok in blob for tok in tokens):
            matched.append(item)
    matched.sort(key=_sort_key)
    page = matched[off : off + lim]
    return [_recipe_row(item) for item in page], "keyword", len(matched)


def similar_recipes(name_or_id: str | None, *, limit: int = 6) -> list[dict[str, Any]]:
    base = find_recipe(name_or_id)
    if not base:
        return []
    base_id = _recipe_id(base)
    base_type = str(base.get("type") or "").lower()
    base_mats = {str(m).lower() for m in (base.get("materials") or [])}
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in recipes():
        rid = _recipe_id(item)
        if rid == base_id:
            continue
        score = 0.0
        if base_type and str(item.get("type") or "").lower() == base_type:
            score += 2.0
        overlap = base_mats & {str(m).lower() for m in (item.get("materials") or [])}
        score += len(overlap) * 0.5
        score += float(item.get("quality_score") or 0) / 100.0
        if score > 0:
            scored.append((score, _recipe_row(item)))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("name", "").lower()))
    return [row for _, row in scored[: max(1, limit)]]


# Exposed for bridge hybrid merge
def recipe_row(item: dict[str, Any]) -> dict[str, Any]:
    return _recipe_row(item)
