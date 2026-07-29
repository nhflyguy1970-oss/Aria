"""Calendar → Notifications publish bridge (Calendar publishes; Notifications delivers)."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("jarvis.calendar.notify")


def publish_calendar_event(
    *,
    title: str,
    summary: str = "",
    severity: str = "info",
    category: str = "calendar",
    deep_link: str = "calendar",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Best-effort publish — never raises into Calendar mutation paths."""
    try:
        from jarvis.notifications_product.pipeline import publish

        return publish(
            {
                "title": title,
                "summary": summary or title,
                "severity": severity,
                "source": "calendar",
                "category": category,
                "deepLink": deep_link,
                "meta": meta or {},
            }
        )
    except Exception as exc:
        log.debug("calendar notify skipped: %s", exc)
        return {"ok": False, "skipped": True, "error": str(exc)}


def notify_commitment_created(item: dict[str, Any]) -> None:
    title = item.get("title") or (item.get("bullet") or {}).get("content") or "Event scheduled"
    day = item.get("day") or (item.get("proposal") or {}).get("day") or ""
    publish_calendar_event(
        title="Calendar: event created",
        summary=f"{title}" + (f" · {day}" if day else ""),
        severity="info",
        deep_link="calendar",
        meta={"item_id": item.get("item_id"), "target": item.get("target")},
    )


def notify_ics_issue(message: str) -> None:
    publish_calendar_event(
        title="Calendar: ICS sync issue",
        summary=message[:200],
        severity="warning",
        category="ics",
        deep_link="calendar",
    )


def notify_conflicts(day: str, count: int) -> None:
    if count <= 0:
        return
    publish_calendar_event(
        title="Calendar: schedule conflicts",
        summary=f"{count} overlapping commitment(s) on {day}",
        severity="warning",
        deep_link="calendar",
        meta={"day": day, "count": count},
    )
