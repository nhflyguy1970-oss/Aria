"""Notifications diagnostics + experimental coaches."""

from __future__ import annotations

from typing import Any

from jarvis.notifications_product.history import load_history
from jarvis.notifications_product.outbox import outbox_status
from jarvis.notifications_product.pipeline import recent, unread_summary
from jarvis.notifications_product.preferences import load_preferences
from jarvis.notifications_product.schema import SCHEMA_VERSION
from jarvis.notifications_product.terminology import TERMINOLOGY


def health_summary() -> dict[str, Any]:
    prefs = load_preferences()
    hist = load_history(limit=20)
    summary = unread_summary()
    outboxes = outbox_status()
    pending = sum(max(0, o.get("pending") or 0) for o in outboxes)
    return {
        "product": TERMINOLOGY["product"],
        "healthy": prefs.get("enabled", True) and pending < 50,
        "schema_version": SCHEMA_VERSION,
        "enabled": bool(prefs.get("enabled")),
        "quiet_hours": bool(prefs.get("quiet_hours_enabled")),
        "dnd": bool(prefs.get("dnd")),
        "critical_only": bool(prefs.get("critical_only")),
        "recent_count": len(recent(limit=40)),
        "history_sample": len(hist),
        "unread_proxy": summary.get("unread"),
        "critical_proxy": summary.get("critical"),
        "outbox_pending": pending,
        "outboxes": outboxes,
        "version": "1.0.0",
    }


def voice_failure_script() -> dict[str, Any]:
    summary = unread_summary()
    if not summary.get("critical"):
        return {
            "ok": True,
            "experimental": True,
            "script": "No critical notification failures right now.",
            "auto_speak": False,
        }
    titles = ", ".join(summary.get("critical_titles") or []) or "several issues"
    return {
        "ok": True,
        "experimental": True,
        "script": f"You have {summary['critical']} critical notifications: {titles}. Open Notifications for details.",
        "auto_speak": False,
        "note": "Voice owns TTS; Notifications only provides the script. Never auto-spoken without intent.",
    }


def noise_classifier_hint(title: str = "", severity: str = "info") -> dict[str, Any]:
    """Heuristic only — optional; never invents alerts."""
    t = (title or "").lower()
    noise = any(x in t for x in ("copied", "saved layout", "layout saved", "theme", "welcome", "listening"))
    promote = severity in ("critical", "error", "warning") and not noise
    return {
        "ok": True,
        "experimental": True,
        "promote_to_activity": promote,
        "noise_likely": noise,
        "auto_apply": False,
    }
