"""Dashboard engine — product status and Home payload."""

from __future__ import annotations

import os
import threading
import time
from typing import Any

from jarvis.dashboard_product.cache import load_last_good, load_layout
from jarvis.dashboard_product.terminology import BOUNDARIES, MENTAL_MODEL, ROLE_LAYOUTS, TERMINOLOGY
from jarvis.dashboard_product.widgets import list_widget_defs

# Serve last-good immediately under this age (seconds) when stale_ok=True.
# Longer than this still serves cache, but kicks a background rebuild.
_FRESH_S = float(os.getenv("JARVIS_DASHBOARD_FRESH_S", "45"))

_build_lock = threading.Lock()
_inflight: dict[str, Any] | None = None
_inflight_key: str | None = None
_bg_lock = threading.Lock()
_bg_running = False


def product_status(*, assistant: Any = None) -> dict[str, Any]:
    defs = list_widget_defs()
    layout = load_layout()
    cache = load_last_good()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["operator_name"],
        "pipeline": TERMINOLOGY["pipeline"],
        "widget_count": len(defs),
        "roles": list(ROLE_LAYOUTS),
        "layout": layout,
        "cache_present": cache is not None,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
    }


def _present_cache(cached: dict[str, Any], *, fresh: bool) -> dict[str, Any]:
    """Normalize last-good cache into a Home payload the UI can render."""
    out = dict(cached)
    out["ok"] = True
    out["product"] = out.get("product") or "Dashboard"
    out["home"] = out.get("home") or "Home"
    out["from_cache"] = True
    out["degraded"] = not fresh
    out["layout"] = out.get("layout") or load_layout()
    out.setdefault("widgets", [])
    out.setdefault("attention", {"items": [], "empty": True, "count": 0})
    out.setdefault("daily_brief", {"available": False})
    out.setdefault("greeting", {"greeting": "Hello", "welcome": "Welcome back"})
    out.setdefault("diagnostics", {})
    if isinstance(out["diagnostics"], dict):
        out["diagnostics"] = {
            **out["diagnostics"],
            "from_cache": True,
            "cache_age_s": cached.get("cache_age_s"),
            "cache_fresh": fresh,
        }
    return out


def _build_now(*, assistant: Any, news_category: str) -> dict[str, Any]:
    from jarvis.dashboard_product.aggregate import build_home_aggregate

    return build_home_aggregate(assistant=assistant, news_category=news_category)


def _singleflight_build(*, assistant: Any, news_category: str) -> dict[str, Any]:
    """One in-flight aggregate at a time — concurrent Home callers share the result."""
    global _inflight, _inflight_key
    key = news_category or ""
    with _build_lock:
        if _inflight is not None and _inflight_key == key:
            waiter = _inflight
        else:
            waiter = {"event": threading.Event(), "result": None, "error": None}
            _inflight = waiter
            _inflight_key = key

            def _run() -> None:
                global _inflight, _inflight_key
                try:
                    waiter["result"] = _build_now(assistant=assistant, news_category=news_category)
                except Exception as exc:
                    waiter["error"] = exc
                finally:
                    waiter["event"].set()
                    with _build_lock:
                        if _inflight is waiter:
                            _inflight = None
                            _inflight_key = None

            threading.Thread(target=_run, name="dashboard-home-build", daemon=True).start()

    waiter["event"].wait(timeout=120)
    if waiter.get("error") is not None:
        raise waiter["error"]
    if waiter.get("result") is None:
        raise TimeoutError("dashboard home build timed out")
    return waiter["result"]


def _kick_background_refresh(*, assistant: Any, news_category: str) -> None:
    """Refresh last-good without blocking the owner request."""
    global _bg_running
    with _bg_lock:
        if _bg_running:
            return
        _bg_running = True

    def _run() -> None:
        global _bg_running
        try:
            _singleflight_build(assistant=assistant, news_category=news_category)
        except Exception:
            pass
        finally:
            with _bg_lock:
                _bg_running = False

    threading.Thread(target=_run, name="dashboard-home-bg", daemon=True).start()


def home_payload(
    *,
    assistant: Any = None,
    news_category: str = "",
    stale_ok: bool = False,
) -> dict[str, Any]:
    """
    Home aggregate.

    When stale_ok=True (API default), return last-good immediately if present so
    Living Room presence / rapid room switches cannot wedge the browser behind a
    5–13s rebuild (news + attention + weather). Background refresh keeps cache warm.
    """
    cached = load_last_good()
    if stale_ok and cached:
        age = float(cached.get("cache_age_s") or 9999)
        fresh = age <= _FRESH_S
        if not fresh:
            _kick_background_refresh(assistant=assistant, news_category=news_category)
        # Always serve cache when stale_ok — never block the house on news/attention.
        return _present_cache(cached, fresh=fresh)

    try:
        return _singleflight_build(assistant=assistant, news_category=news_category)
    except Exception as exc:
        if stale_ok:
            cached = load_last_good()
            if cached:
                cached["ok"] = True
                cached["degraded"] = True
                cached["error"] = str(exc)
                return cached
        return {
            "ok": False,
            "product": "Dashboard",
            "home": "Home",
            "error": str(exc),
            "widgets": [],
            "attention": {"items": [], "empty": True, "count": 0},
            "daily_brief": {"available": False, "coach": "Home aggregate failed."},
            "greeting": {"greeting": "Hello", "welcome": "Welcome back"},
        }
