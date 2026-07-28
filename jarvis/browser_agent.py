"""Playwright browser agent with safety limits and human takeover.

Facade over jarvis.browser_product.session — never reports success without a real action.
"""

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
    "screenshot_stale": False,
    "allow_downloads": False,
    "blocked_download": "",
    "fallback": False,
    "last_error": "",
}
_LOCK = threading.Lock()

# Back-compat aliases used by DOM/VLM modules
_PAGE = None  # updated via _sync_page_ref


def _sync_page_ref() -> None:
    global _PAGE
    from jarvis.browser_product.session import get_page

    _PAGE = get_page()


def _playwright_available() -> bool:
    from jarvis.browser_product.session import stack_ready

    stack = stack_ready()
    return bool(stack.get("playwright") and stack.get("chromium"))


def _agent_paused() -> bool:
    with _LOCK:
        return bool(_STATE.get("paused") or _STATE.get("takeover"))


def _modes_available() -> dict[str, Any]:
    ready = _playwright_available()
    page = False
    try:
        from jarvis.browser_product.session import get_page

        page = get_page() is not None
    except Exception:
        page = False
    return {
        "dom": ready,
        "vlm": ready,  # still needs vision model at runtime
        "auto": ready,
        "page_live": page,
        "unavailable_reason": (
            ""
            if ready
            else "Playwright/Chromium not installed — use Install Playwright"
        ),
    }


def status() -> dict[str, Any]:
    from jarvis.browser_product.session import session_info, stack_ready, steps

    stack = stack_ready()
    info = session_info()
    with _LOCK:
        out = dict(_STATE)
    playwright = bool(stack.get("playwright"))
    chromium = bool(stack.get("chromium"))
    ready = playwright and chromium
    if info.get("active") and info.get("url"):
        out["url"] = info["url"] or out.get("url") or ""
    modes = _modes_available()
    return {
        **out,
        "enabled": browser_agent_enabled(),
        "playwright": playwright,
        "chromium": chromium,
        "agent_ready": ready,
        "session_active": bool(info.get("active")),
        "profile": info.get("profile") or out.get("profile") or "",
        "profile_dir": info.get("profile_dir") or "",
        "headless": info.get("headless", True),
        "steps": steps(limit=30),
        "modes_available": modes,
        "playwright_hint": (
            ""
            if ready
            else "Install Playwright: pip install playwright && playwright install chromium"
        ),
    }


def _check_url_safe(url: str, *, allow_risky: bool = False) -> tuple[bool, str]:
    from jarvis.security.url_guard import is_safe_fetch_url

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
        return False, "Blocked URL (checkout/payment) — confirm required (allow_risky)."
    return True, ""


def check_url_safe(url: str, *, allow_risky: bool = False) -> dict[str, Any]:
    ok, reason = _check_url_safe(url, allow_risky=allow_risky)
    return {"ok": ok, "message": reason, "needs_confirm": (not ok and "checkout" in reason.lower()) or (not ok and "confirm" in reason.lower())}


def _emit(event_type: str, message: str = "", **detail) -> None:
    try:
        from jarvis.browser_product.activity_bridge import emit_browser_event

        emit_browser_event(event_type, message=message, detail=detail)
    except Exception:
        pass


def pause() -> dict[str, Any]:
    with _LOCK:
        _STATE["paused"] = True
        _STATE["status"] = "paused"
        _STATE["message"] = "Paused — agent will not click/fill until Resume"
    try:
        from jarvis.browser_product.screenshots import capture

        shot = capture(label="pause", reason="pause")
        if shot.get("ok"):
            with _LOCK:
                _STATE["last_screenshot"] = shot["path"]
                _STATE["screenshot_stale"] = False
    except Exception:
        pass
    _emit("browser_paused", "Browser agent paused")
    return status()


def resume() -> dict[str, Any]:
    with _LOCK:
        _STATE["paused"] = False
        _STATE["takeover"] = False
        _STATE["status"] = "running" if (_STATE.get("url") or _PAGE) else "idle"
        _STATE["message"] = "Resumed"
    _emit("browser_resumed", "Browser agent resumed")
    return status()


def takeover() -> dict[str, Any]:
    """Pause agent; attempt headed session when possible."""
    with _LOCK:
        _STATE["takeover"] = True
        _STATE["paused"] = True
        _STATE["status"] = "takeover"
        _STATE["message"] = "Human takeover — interact with the page, then Resume"
    try:
        from jarvis.browser_product.session import ensure_session

        # Prefer headed window for takeover when session can relaunch
        ensure_session(headed_for_takeover=True)
        _sync_page_ref()
    except Exception as exc:
        log.debug("takeover headed launch: %s", exc)
    _emit("browser_takeover", "Operator takeover")
    return status()


def stop() -> dict[str, Any]:
    from jarvis.browser_product.session import close_session

    close_session()
    _sync_page_ref()
    with _LOCK:
        _STATE.update(
            {
                "status": "idle",
                "url": "",
                "message": "Stopped",
                "paused": False,
                "takeover": False,
                "fallback": False,
                "last_error": "",
                "screenshot_stale": True,
            }
        )
    _emit("browser_stopped", "Browser session stopped")
    return status()


def allow_downloads(enabled: bool = True) -> dict[str, Any]:
    with _LOCK:
        _STATE["allow_downloads"] = bool(enabled)
        if enabled:
            _STATE["blocked_download"] = ""
    return status()


def screenshot(*, label: str = "manual", reason: str = "") -> dict[str, Any]:
    """Capture a real screenshot from the live page."""
    with _LOCK:
        if _STATE.get("fallback"):
            return {
                "ok": False,
                "skipped": True,
                "message": "No Playwright page (system-browser fallback) — screenshot skipped",
            }
    from jarvis.browser_product.screenshots import capture

    shot = capture(label=label, reason=reason or label)
    if shot.get("ok"):
        with _LOCK:
            _STATE["last_screenshot"] = shot["path"]
            _STATE["screenshot_stale"] = False
            _STATE["message"] = f"Screenshot captured ({reason or label})"
        return shot
    return {
        "ok": False,
        "message": shot.get("error") or "Screenshot failed",
        "recovery": shot.get("recovery"),
        "skipped": False,
    }


def navigate(
    url: str,
    *,
    allow_risky: bool = False,
    allow_system_fallback: bool = False,
) -> dict[str, Any]:
    """Navigate for real via Playwright. Fail closed unless explicit system fallback."""
    if not browser_agent_enabled():
        return {
            "ok": False,
            "message": "Browser agent disabled",
            "recovery": "Set JARVIS_BROWSER_AGENT=1",
        }
    url = (url or "").strip()
    if not url:
        return {"ok": False, "message": "URL required", "recovery": "Enter an https:// URL"}
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    safe, reason = _check_url_safe(url, allow_risky=allow_risky)
    if not safe:
        _emit("browser_blocked_url", reason, url=url)
        return {
            "ok": False,
            "message": reason,
            "needs_confirm": True,
            "recovery": "Confirm risky navigation with allow_risky, or choose another URL",
        }

    if not _playwright_available():
        if allow_system_fallback:
            try:
                from jarvis.browser_util import open_url

                opened = open_url(url)
            except Exception as exc:
                opened = False
                log.debug("system fallback failed: %s", exc)
            if opened:
                with _LOCK:
                    _STATE.update(
                        {
                            "url": url,
                            "status": "external",
                            "fallback": True,
                            "message": f"Opened in system browser (Playwright unavailable): {url}",
                            "last_error": "",
                        }
                    )
                _emit("browser_navigate_fallback", url, url=url)
                return {
                    "ok": True,
                    "fallback": True,
                    "message": f"Opened in system browser (agent automation unavailable): {url}",
                    "status": status(),
                }
        return {
            "ok": False,
            "message": "Playwright/Chromium not available — navigation did not occur",
            "recovery": "Click Install Playwright, then retry Open",
            "agent_ready": False,
        }

    with _LOCK:
        _STATE["status"] = "navigating"
        _STATE["message"] = f"Navigating to {url}"
        _STATE["fallback"] = False
        _STATE["last_error"] = ""

    from jarvis.browser_product.session import goto

    result = goto(url)
    _sync_page_ref()
    if not result.get("ok"):
        with _LOCK:
            _STATE["status"] = "error"
            _STATE["last_error"] = result.get("error") or "Navigate failed"
            _STATE["message"] = _STATE["last_error"]
        _emit("browser_navigate_failed", result.get("error") or "", url=url)
        return {
            "ok": False,
            "message": result.get("error") or "Navigation failed — page was not loaded",
            "recovery": result.get("recovery") or "Retry Open or check network",
            "status": status(),
        }

    final_url = result.get("url") or url
    shot = screenshot(label="nav", reason="after_navigate")
    with _LOCK:
        _STATE["url"] = final_url
        _STATE["status"] = "running"
        _STATE["message"] = f"Navigated to {final_url}"
        _STATE["fallback"] = False
    _emit("browser_navigated", final_url, url=final_url)
    out = {
        "ok": True,
        "message": f"Navigated to {final_url}",
        "url": final_url,
        "title": result.get("title"),
        "screenshot_ok": bool(shot.get("ok")),
        "status": status(),
    }
    if not shot.get("ok"):
        out["screenshot_warning"] = shot.get("message") or shot.get("error")
    return out


def click_selector(selector: str) -> dict[str, Any]:
    from jarvis.browser_product.session import click_selector as _click

    out = _click(selector)
    if out.get("ok"):
        screenshot(label="click", reason=f"after_click:{selector[:40]}")
    return out


def run_agent_task(
    goal: str,
    *,
    mode: str = "auto",
    max_steps: int = 10,
    assistant=None,
) -> dict[str, Any]:
    """Run DOM/VLM agent against the live page. Never claim success without steps."""
    if not browser_agent_enabled():
        return {"ok": False, "message": "Browser agent disabled", "recovery": "Enable JARVIS_BROWSER_AGENT"}
    goal = (goal or "").strip()
    if not goal:
        return {"ok": False, "message": "Goal required"}
    modes = _modes_available()
    mode = (mode or "auto").lower()
    if mode not in ("auto", "dom", "vlm"):
        return {"ok": False, "message": f"Unknown mode: {mode}", "recovery": "Use auto, dom, or vlm"}
    if not modes.get("dom") and not modes.get("vlm"):
        return {
            "ok": False,
            "message": modes.get("unavailable_reason") or "Browser stack not ready",
            "recovery": "Install Playwright, then Navigate to a page",
            "modes_available": modes,
        }

    from jarvis.browser_product.session import clear_steps, ensure_session, get_page

    ensured = ensure_session()
    if not ensured.get("ok"):
        return {
            "ok": False,
            "message": ensured.get("error") or "Could not start browser session",
            "recovery": ensured.get("recovery"),
        }
    _sync_page_ref()
    if get_page() is None:
        return {
            "ok": False,
            "message": "No live page — navigate to a URL before running a task",
            "recovery": "Enter a URL and click Open, then Run",
        }

    clear_steps()
    with _LOCK:
        _STATE["status"] = "running"
        _STATE["paused"] = False
        _STATE["message"] = goal[:500]
        _STATE["last_error"] = ""

    _emit("browser_task_start", goal[:200], mode=mode)

    # Direct DOM / VLM loop on the live page (never re-enter Chat action handlers)
    from jarvis.browser_product.agent_loop import run_loop

    result = run_loop(
        goal,
        mode=mode,
        max_steps=max_steps,
        assistant=assistant,
        pause_check=_agent_paused,
        on_step_screenshot=lambda label: screenshot(label=label, reason=label),
    )
    with _LOCK:
        if result.get("ok"):
            _STATE["status"] = "idle" if not _STATE.get("url") else "running"
            _STATE["message"] = result.get("message") or "Task complete"
        else:
            _STATE["status"] = "error" if not _STATE.get("paused") else _STATE["status"]
            _STATE["last_error"] = result.get("message") or result.get("error") or "Task failed"
            _STATE["message"] = _STATE["last_error"]
    if result.get("ok"):
        _emit("browser_task_complete", result.get("message") or goal[:120])
    else:
        _emit("browser_task_failed", result.get("message") or "", goal=goal[:120])
    result["status"] = status()
    result["steps"] = status().get("steps") or []
    return result


# Re-export download check for tests
def _check_download_safe(url: str, filename: str = "") -> tuple[bool, str]:
    from jarvis.browser_product.downloads import _check_download_safe as _inner

    ok, reason, _meta = _inner(url, filename=filename)
    return ok, reason
