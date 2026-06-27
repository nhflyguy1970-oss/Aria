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


def expand_query(q: str) -> tuple[str, list[str]]:
    """Return (expanded_query_string, alias_terms_used)."""
    needle = (q or "").strip().lower()
    if not needle:
        return "", []
    amap = alias_map()
    terms = [needle]
    used: list[str] = []
    for tok in needle.split():
        low = tok.lower()
        if low in amap:
            used.append(low)
            terms.extend(amap[low])
    if needle in amap:
        used.append(needle)
        terms.extend(amap[needle])
    seen: set[str] = set()
    unique: list[str] = []
    for t in terms:
        t = t.strip().lower()
        if t and t not in seen:
            seen.add(t)
            unique.append(t)
    return " ".join(unique), used


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
