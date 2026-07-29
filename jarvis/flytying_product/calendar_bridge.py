"""Calendar bridge — structured candidate payloads (does not invent full Calendar APIs)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def calendar_candidates(
    *,
    kind: str = "hatch_weeks",
    title: str = "",
    notes: str = "",
    month: int | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    """
    Return preview candidates for Calendar integration.
    Caller confirms before creating calendar events.
    """
    kind = (kind or "hatch_weeks").strip().lower()
    candidates: list[dict[str, Any]] = []
    today = date.today()
    m = month or today.month

    if kind in ("hatch_weeks", "seasonal_reminders"):
        from jarvis.flytying.hatch import hatch_context

        ctx = hatch_context(month=m)
        hatches = ", ".join(str(h) for h in (ctx.get("hatches") or [])[:8])
        start = date(today.year, m, 1)
        end = start + timedelta(days=13)
        candidates.append(
            {
                "title": title or f"Hatch window — {ctx.get('region')}",
                "notes": notes or f"{hatches}. {ctx.get('notes') or ''}".strip(),
                "kind": kind,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "all_day": True,
                "region": ctx.get("region"),
                "suggest_types": ctx.get("suggest_types") or [],
                "source": "flytying_hatch",
                "selected": True,
            }
        )
        for h in (ctx.get("hatches") or [])[:5]:
            candidates.append(
                {
                    "title": f"Hatch window: {h}",
                    "notes": f"{h} — {ctx.get('region')}",
                    "kind": kind,
                    "month": m,
                    "year": today.year,
                    "source": "flytying_hatch",
                    "selected": True,
                }
            )

    elif kind in ("bench_sessions", "preparation"):
        from jarvis.flytying_product.sessions import active_session, get_session

        session = get_session(session_id) if session_id else active_session()
        name = (session or {}).get("recipe_name") or (session or {}).get("recipe_id") or "Bench session"
        candidates.append(
            {
                "title": title or f"Bench: {name}",
                "notes": notes or (session or {}).get("notes") or "Fly Tying bench session",
                "kind": kind,
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
                "all_day": False,
                "session_id": (session or {}).get("id") or "",
                "recipe_id": (session or {}).get("recipe_id") or "",
                "source": "flytying_session",
                "selected": True,
            }
        )

    elif kind == "trips":
        from jarvis.flytying.hatch import hatch_context

        ctx = hatch_context(month=m)
        start = date(today.year, m, min(15, 28))
        candidates.append(
            {
                "title": title or f"Trip prep — {ctx.get('region')}",
                "notes": notes or f"Prep patterns for: {', '.join(str(h) for h in (ctx.get('hatches') or [])[:6])}",
                "kind": kind,
                "start_date": start.isoformat(),
                "end_date": (start + timedelta(days=2)).isoformat(),
                "all_day": True,
                "source": "flytying_trip",
                "selected": True,
            }
        )
    else:
        candidates.append(
            {
                "title": title or "Fly Tying event",
                "notes": notes,
                "kind": kind,
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
                "source": "flytying",
                "selected": True,
            }
        )

    return {
        "ok": True,
        "product": "Fly Tying",
        "target": "Calendar",
        "requires_confirmation": True,
        "kind": kind,
        "candidates": candidates,
        "message": "Preview only — confirm in Calendar to create events.",
        "pipeline": "flytying_calendar_bridge",
    }


def hatch_week_candidates(*, month: int | None = None) -> dict[str, Any]:
    return calendar_candidates(kind="hatch_weeks", month=month)


def bench_session_event_preview(*, recipe_name: str = "", minutes: int = 60) -> dict[str, Any]:
    title = f"Tying session: {recipe_name}" if recipe_name else "Fly tying bench session"
    return {
        "ok": True,
        "target": "calendar",
        "requires_confirmation": True,
        "candidates": [{"title": title, "duration_minutes": minutes, "selected": True}],
        "pipeline": "flytying_calendar_bridge",
    }
