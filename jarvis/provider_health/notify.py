"""Provider Health → Notifications (meaningful events only)."""

from __future__ import annotations

import time
from typing import Any

from jarvis.provider_health.prefs import load_preferences

_last_notify: dict[str, float] = {}
_COOLDOWN_SEC = 45.0


def _should_notify(key: str) -> bool:
    now = time.time()
    last = _last_notify.get(key, 0)
    if now - last < _COOLDOWN_SEC:
        return False
    _last_notify[key] = now
    return True


def _publish(title: str, summary: str, severity: str = "warning", **meta: Any) -> None:
    prefs = load_preferences()
    if not prefs.get("notify_recoveries", True) and severity == "info":
        return
    try:
        from jarvis.notifications_product.pipeline import publish

        publish(
            {
                "title": title,
                "summary": summary,
                "severity": severity,
                "source": "provider_health",
                "category": "provider",
                "deepLink": "workstation",
                "meta": meta,
            }
        )
    except Exception:
        pass


def notify_timeout(classified: dict[str, Any], *, provider: str = "", model: str = "") -> None:
    cls = classified.get("class") or "unknown"
    if not _should_notify(f"timeout:{cls}:{provider}"):
        return
    _publish(
        classified.get("title") or "Provider timeout",
        classified.get("explanation") or "",
        severity="error" if cls in ("provider_unreachable", "model_crashed", "oom") else "warning",
        class_=cls,
        provider=provider,
        model=model,
    )


def notify_recovery(*, classified: dict[str, Any], usable: bool, provider: str = "", model: str = "") -> None:
    key = f"recovery:{usable}:{provider}"
    if not _should_notify(key):
        return
    if usable:
        _publish(
            "Provider recovered",
            f"{provider or 'Provider'} is reachable again — retry the prompt.",
            severity="info",
            provider=provider,
            model=model,
            class_=classified.get("class"),
        )
    else:
        _publish(
            "Provider still unavailable",
            classified.get("explanation") or "Automatic recovery did not restore the provider.",
            severity="error",
            provider=provider,
            model=model,
            class_=classified.get("class"),
        )
