"""Digest engine — Today / Needs attention / Critical / Failures / Morning / End of day."""

from __future__ import annotations

import time
from typing import Any

from jarvis.notifications_product.history import load_history
from jarvis.notifications_product.pipeline import recent


def _day_start(ts: float | None = None) -> float:
    import datetime as dt

    now = dt.datetime.fromtimestamp(ts or time.time())
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.timestamp()


def build_digest(kind: str = "today") -> dict[str, Any]:
    kind = (kind or "today").lower()
    items = recent(limit=80) or load_history(limit=80)
    start = _day_start()
    today = [e for e in items if float(e.get("timestamp") or 0) >= start or float(e.get("recorded_at") or 0) >= start]

    def is_fail(e: dict[str, Any]) -> bool:
        return str(e.get("severity") or "") in ("critical", "error", "warning")

    def needs(e: dict[str, Any]) -> bool:
        return not e.get("read") and not e.get("dismissed") and not e.get("resolved") and is_fail(e)

    if kind in ("critical",):
        selected = [e for e in today if e.get("severity") in ("critical", "error")]
        title = "Critical"
    elif kind in ("failures", "failure"):
        selected = [e for e in today if is_fail(e)]
        title = "Failures"
    elif kind in ("needs", "attention", "needs_attention"):
        selected = [e for e in items if needs(e)][:20]
        title = "Needs attention"
    elif kind in ("morning",):
        selected = [e for e in today if needs(e) or e.get("severity") in ("critical", "error")][:12]
        title = "Morning digest"
    elif kind in ("eod", "end_of_day", "evening"):
        selected = today[:20]
        title = "End of day"
    else:
        selected = today[:20]
        title = "Today"

    lines = [f"• {e.get('title')}" for e in selected[:12]]
    summary = f"{title}: {len(selected)} event(s)."
    if lines:
        summary += " " + " ".join(lines[:5])
    return {
        "ok": True,
        "kind": kind,
        "title": title,
        "count": len(selected),
        "summary": summary,
        "events": selected,
        "lines": lines,
        "experimental": False,
    }


def group_events(events: list[dict[str, Any]] | None = None, *, by: str = "source") -> dict[str, Any]:
    events = events if events is not None else recent(limit=60)
    groups: dict[str, list[dict[str, Any]]] = {}
    for e in events:
        if by == "day":
            import datetime as dt

            ts = float(e.get("timestamp") or time.time())
            key = dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        elif by == "category":
            key = str(e.get("category") or "system")
        elif by == "incident" or by == "correlation":
            key = str(e.get("correlationId") or e.get("groupId") or e.get("source") or "ungrouped")
        else:
            key = str(e.get("source") or "system")
        groups.setdefault(key, []).append(e)
    return {
        "ok": True,
        "by": by,
        "groups": [{"key": k, "count": len(v), "events": v[:10]} for k, v in groups.items()],
    }
