"""Material substitution hints."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent / "data" / "substitutions.json"


@lru_cache(maxsize=1)
def substitution_map() -> dict[str, list[str]]:
    if not _DATA.is_file():
        return {}
    try:
        raw = json.loads(_DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(k).strip().lower(): [str(v).strip() for v in vals if str(v).strip()]
        for k, vals in raw.items()
        if isinstance(vals, list)
    }


def suggest_substitutions(material: str) -> list[str]:
    low = (material or "").strip().lower()
    if not low:
        return []
    smap = substitution_map()
    if low in smap:
        return smap[low]
    for key, vals in smap.items():
        if key in low or low in key:
            return vals
    return []


def substitutions_for_recipe(materials: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for mat in materials or []:
        subs = suggest_substitutions(str(mat))
        if subs:
            out[str(mat)] = subs
    return out
