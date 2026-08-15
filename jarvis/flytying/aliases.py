"""Pattern name aliases for fly-tying search."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent / "data" / "aliases.json"


@lru_cache(maxsize=1)
def alias_map() -> dict[str, list[str]]:
    if not _DATA.is_file():
        return {}
    try:
        raw = json.loads(_DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[str]] = {}
    for key, vals in raw.items():
        k = str(key).strip().lower()
        if not k:
            continue
        aliases = [str(v).strip().lower() for v in (vals if isinstance(vals, list) else [vals]) if str(v).strip()]
        out[k] = list(aliases)
        for a in aliases:
            out.setdefault(a, []).append(k)
    return out


def query_variants(q: str) -> tuple[list[str], list[str]]:
    """Return (OR search variants, alias keys used).

    Aliases are alternate phrasings. Never AND-join them into one keyword query —
    that made “elk hair caddis” require sparkle+pupa and hide real recipes.
    """
    needle = (q or "").strip().lower()
    if not needle:
        return [], []
    amap = alias_map()
    variants: list[str] = []
    used: list[str] = []
    seen: set[str] = set()

    def _add(term: str, mark: str | None = None) -> None:
        t = (term or "").strip().lower()
        if not t or t in seen:
            return
        seen.add(t)
        variants.append(t)
        if mark and mark not in used:
            used.append(mark)

    _add(needle)

    if needle in amap:
        used.append(needle)
        for a in amap[needle]:
            _add(a, needle)

    for canon, als in amap.items():
        if needle in als:
            _add(canon, needle)
            for a in als:
                _add(a, needle)

    return variants, used


def expand_query(q: str) -> tuple[str, list[str]]:
    """Compatibility helper. Prefer query_variants() for search."""
    variants, used = query_variants(q)
    return " ".join(variants), used


def aliases_for_name(name: str) -> list[str]:
    low = (name or "").strip().lower()
    if not low:
        return []
    amap = alias_map()
    hits = set(amap.get(low, []))
    for key, vals in amap.items():
        if low in vals or key in low or low in key:
            hits.add(key)
            hits.update(vals)
    hits.discard(low)
    return sorted(hits)[:12]
