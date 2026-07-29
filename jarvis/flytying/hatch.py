"""Seasonal hatch calendar for fly-tying suggestions."""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent / "data" / "hatch_northeast.json"
_OPERATOR = Path(__file__).resolve().parent / "data" / "hatch_operator_active.json"


@lru_cache(maxsize=2)
def _calendar(path_key: str = "default") -> dict[str, Any]:
    path = _OPERATOR if path_key == "operator" and _OPERATOR.is_file() else _DATA
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def hatch_context(*, month: int | None = None) -> dict[str, Any]:
    cal = _calendar("operator" if _OPERATOR.is_file() else "default")
    m = month or datetime.now().month
    month_data = (cal.get("months") or {}).get(str(m)) or {}
    return {
        "region": cal.get("region") or "Northeast US",
        "month": m,
        "hatches": list(month_data.get("hatches") or []),
        "suggest_types": list(month_data.get("suggest_types") or []),
        "notes": str(month_data.get("notes") or ""),
    }


def hatch_context_text(*, month: int | None = None) -> str:
    ctx = hatch_context(month=month)
    hatches = ", ".join(str(h) for h in ctx.get("hatches") or [])
    types = ", ".join(str(t) for t in ctx.get("suggest_types") or [])
    lines = [f"Seasonal context ({ctx.get('region')}, month {ctx.get('month')}):"]
    if hatches:
        lines.append(f"Typical hatches: {hatches}.")
    if types:
        lines.append(f"Suggested fly types: {types}.")
    if ctx.get("notes"):
        lines.append(str(ctx["notes"]))
    return " ".join(lines)


def suggest_patterns_for_season(*, month: int | None = None, limit: int = 8) -> list[str]:
    ctx = hatch_context(month=month)
    terms: list[str] = []
    for h in ctx.get("hatches") or []:
        terms.append(str(h))
    for t in ctx.get("suggest_types") or []:
        terms.append(str(t))
    return terms[: max(1, limit)]
