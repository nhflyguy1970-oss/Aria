"""One Notifications publish pipeline."""

from __future__ import annotations

import time
from typing import Any

from jarvis.notifications_product.history import append_history
from jarvis.notifications_product.preferences import load_preferences, route_decision
from jarvis.notifications_product.schema import normalize_event, to_activity_payload, validate_event

# In-memory recent ring for API / MC / dashboard (not a second DB — mirrors Activity)
_RECENT: list[dict[str, Any]] = []
_MAX_RECENT = 120


def publish(raw: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """
    Canonical publish entry — products call this (or /api/notifications/publish).

    Compatibility: accepts legacy fields (message, tone, kind, fix).
    """
    payload = dict(raw or {})
    payload.update({k: v for k, v in kwargs.items() if v is not None})
    evt = normalize_event(payload)
    errs = validate_event(evt)
    if errs:
        return {"ok": False, "error": "invalid_event", "validation": errs}

    prefs = load_preferences()
    routing = route_decision(evt, prefs)
    evt["routing"] = routing
    evt["published_at"] = time.time()

    if not routing.get("deliver") and not routing.get("activity"):
        append_history({**evt, "suppressed": True, "suppress_reason": routing.get("reason")})
        return {
            "ok": True,
            "suppressed": True,
            "reason": routing.get("reason"),
            "event": evt,
            "activity": to_activity_payload(evt),
            "routing": routing,
        }

    append_history(evt)
    _RECENT.insert(0, evt)
    del _RECENT[_MAX_RECENT:]
    activity_payload = to_activity_payload(evt)
    inbox_result: dict[str, Any] | None = None
    if routing.get("activity"):
        try:
            from jarvis.activity_inbox import publish as publish_activity

            inbox_result = publish_activity(
                kind=evt["severity"],
                title=evt["title"],
                body=evt.get("summary") or evt.get("detail") or "",
                source=evt.get("source") or "notifications",
                meta={
                    **(evt.get("metadata") or {}),
                    "category": evt.get("category"),
                    "type": evt.get("type"),
                    "severity": evt.get("severity"),
                    "notification": activity_payload,
                },
                event_id=evt["id"],
            )
        except Exception as exc:
            inbox_result = {"ok": False, "error": str(exc)[:200]}

    # Also feed Mission Control platform notifications for critical/error (ops echo, not inbox)
    if evt["severity"] in ("critical", "error"):
        try:
            from jarvis.platform_notifications import notify as platform_notify

            platform_notify(
                evt["title"],
                level=evt["severity"],
                detail=evt.get("summary") or "",
                component=evt.get("source") or "notifications",
            )
        except Exception:
            pass

    return {
        "ok": True,
        "suppressed": False,
        "event": evt,
        "activity": activity_payload,
        "activity_inbox": inbox_result,
        "routing": routing,
        "client_action": {
            "type": "ingest_notification",
            "activity": activity_payload,
            "toast": routing.get("toast"),
            "desktop": routing.get("desktop"),
            "voice": routing.get("voice"),
        },
    }


def add(raw: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for AriaActivity.add / legacy emitters."""
    return publish(raw, **kwargs)


def push(raw: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for AriaActivity.push."""
    return publish(raw, **kwargs)


def recent(*, limit: int = 40) -> list[dict[str, Any]]:
    return list(_RECENT)[:limit]


def unread_summary() -> dict[str, Any]:
    items = [e for e in _RECENT if not e.get("read") and not e.get("dismissed") and not e.get("suppressed")]
    # Activity Center is the durable inbox — survive restarts when in-memory ring is empty.
    try:
        from jarvis.activity_inbox import list_items

        inbox = (list_items(include_dismissed=False, limit=100) or {}).get("items") or []
        inbox_unread = [e for e in inbox if not e.get("read") and not e.get("dismissed")]
        if len(inbox_unread) > len(items):
            items = [
                {
                    "title": e.get("title"),
                    "severity": e.get("kind") or e.get("severity") or "info",
                    "read": e.get("read"),
                    "dismissed": e.get("dismissed"),
                }
                for e in inbox_unread
            ]
    except Exception:
        pass
    critical = [e for e in items if e.get("severity") in ("critical", "error", "warning")]
    return {
        "unread": len(items),
        "critical": len(critical),
        "titles": [e.get("title") for e in items[:5]],
        "critical_titles": [e.get("title") for e in critical[:5]],
    }
