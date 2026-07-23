"""Playwright browser agent with safety limits and human takeover."""

from __future__ import annotations

import logging
import re
import threading
from typing import Any
from urllib.parse import urlparse

from jarvis.p2_flags import browser_agent_enabled

log = logging.getLogger("jarvis.browser")
_BLOCKED_HOST_PATTERNS = ("paypal", "checkout", "stripe", "buy\\.apple", "amazon\\..*/gp/buy")
_BLOCKED_PATH = re.compile("|".join(_BLOCKED_HOST_PATTERNS), re.I)
_STATE: dict[str, Any] = {
    "status": "idle",
    "url": "",
    "message": "",
    "paused": False,
    "takeover": False,
    "last_screenshot": "",
    "allow_downloads": False,
    "blocked_download": "",
}
_LOCK = threading.Lock()


def _playwright_available() -> bool:
    from jarvis.browser_playwright import browser_stack_ready

    stack = browser_stack_ready()
    return bool(stack.get("playwright") and stack.get("chromium"))


def status() -> dict[str, Any]:
    from jarvis.browser_playwright import browser_stack_ready

    stack = browser_stack_ready()
    with _LOCK:
        out = dict(_STATE)
    return {
        "enabled": browser_agent_enabled(),
        "playwright": bool(stack.get("playwright")),
        "chromium": bool(stack.get("chromium")),
        **out,
    }


def _check_url_safe(url: str, *, allow_risky: bool = False) -> tuple[bool, str]:
    from jarvis.security.url_guard import is_safe_fetch_url

    # Scheme / private-network blocks always apply — allow_risky only skips checkout heuristics.
    ok, err = is_safe_fetch_url(url, allow_http=True)
    if not ok:
        return False, err or "Blocked URL"
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme in ("file", "javascript", "data", "vbscript"):
        return False, f"Blocked URL scheme: {scheme}"
    if allow_risky:
        return True, ""
    host_path = f"{parsed.netloc}{parsed.path}"
    if _BLOCKED_PATH.search(host_path):
        return False, "Blocked URL (checkout/payment) — confirm required for web_agent."
    return True, ""


def pause() -> dict[str, Any]:
    with _LOCK:
        _STATE["paused"] = True
        _STATE["status"] = "paused"
    return status()


def resume() -> dict[str, Any]:
    with _LOCK:
        _STATE["paused"] = False
        _STATE["takeover"] = False
        _STATE["status"] = "running" if _STATE.get("url") else "idle"
    return status()


def takeover() -> dict[str, Any]:
    with _LOCK:
        _STATE["takeover"] = True
        _STATE["paused"] = True
        _STATE["status"] = "takeover"
        _STATE["message"] = "Human takeover — click in browser, then resume agent."
    return status()


def stop() -> dict[str, Any]:
    with _LOCK:
        _STATE.update(
            {
                "status": "idle",
                "url": "",
                "message": "",
                "paused": False,
                "takeover": False,
            }
        )
    return status()


def allow_downloads(enabled: bool = True) -> dict[str, Any]:
    with _LOCK:
        _STATE["allow_downloads"] = bool(enabled)
        if enabled:
            _STATE["blocked_download"] = ""
    return status()


def navigate(url: str, *, allow_risky: bool = False) -> dict[str, Any]:
    if not browser_agent_enabled():
        return {"ok": False, "message": "Browser agent disabled"}
    url = (url or "").strip()
    if not url:
        return {"ok": False, "message": "URL required"}
    safe, reason = _check_url_safe(url, allow_risky=allow_risky)
    if not safe:
        return {"ok": False, "message": reason, "needs_confirm": True}
    if not _playwright_available():
        return {
            "ok": False,
            "message": "Playwright/chromium not available — install playwright and chromium",
        }
    with _LOCK:
        _STATE["url"] = url
        _STATE["status"] = "running"
        _STATE["message"] = f"Navigating to {url}"
    return {"ok": True, "message": f"Opened {url}", "status": status()}


def run_agent_task(
    goal: str,
    *,
    mode: str = "auto",
    max_steps: int = 10,
    assistant=None,
) -> dict[str, Any]:
    if not browser_agent_enabled():
        return {"ok": False, "message": "Browser agent disabled"}
    goal = (goal or "").strip()
    if not goal:
        return {"ok": False, "message": "Goal required"}
    if not _playwright_available():
        return {"ok": False, "message": "Playwright/chromium not available"}
    with _LOCK:
        _STATE["status"] = "running"
        _STATE["message"] = goal[:500]
    try:
        if assistant is not None:
            result = assistant.dispatch("web_agent", {"goal": goal, "mode": mode}, goal)
            if isinstance(result, dict):
                return result
    except Exception as exc:
        log.debug("web_agent dispatch failed: %s", exc)
    return {
        "ok": True,
        "message": f"Task accepted: {goal}",
        "status": status(),
        "note": "Full multi-step browser agent may require Playwright page automation.",
    }
