"""Playwright session manager — real page lifecycle.

Playwright's sync API is greenlet-bound: every call must run on the same thread
that started sync_playwright(). The HTTP server uses a thread pool, so we pin
all Playwright work onto one dedicated daemon thread.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.browser.session")

_LOCK = threading.RLock()
_PW = None
_BROWSER = None
_CONTEXT = None
_PAGE = None
_PROFILE_SLUG = ""
_HEADLESS = True
_LAUNCHED_AT = 0.0
_STEPS: list[dict[str, Any]] = []
_STACK_CACHE: dict[str, Any] = {"ts": 0.0, "stack": {}}
_STACK_TTL = 30.0

_PW_JOBS: queue.Queue = queue.Queue()
_PW_THREAD: threading.Thread | None = None
_PW_THREAD_ID: int | None = None

T = TypeVar("T")


def _is_greenlet_error(exc: BaseException) -> bool:
    msg = str(exc or "")
    return "greenlet" in msg.lower() or "cannot switch to a different thread" in msg.lower()


def _owner_error(exc: BaseException) -> str:
    if _is_greenlet_error(exc):
        return "Browser session needed a clean restart"
    return str(exc)


def _pw_worker() -> None:
    global _PW_THREAD_ID
    _PW_THREAD_ID = threading.get_ident()
    while True:
        job = _PW_JOBS.get()
        if job is None:
            break
        fn, args, kwargs, box = job
        try:
            box["result"] = fn(*args, **kwargs)
            box["ok"] = True
        except BaseException as exc:  # noqa: BLE001 — marshalled to caller
            box["error"] = exc
            box["ok"] = False
        finally:
            box["event"].set()


def _ensure_pw_thread() -> None:
    global _PW_THREAD
    with _LOCK:
        if _PW_THREAD and _PW_THREAD.is_alive():
            return
        _PW_THREAD = threading.Thread(target=_pw_worker, name="aria-playwright", daemon=True)
        _PW_THREAD.start()


def run_on_browser_thread(
    fn: Callable[..., T], *args: Any, timeout: float = 120.0, **kwargs: Any
) -> T:
    """Run callable on the dedicated Playwright thread (re-entrant)."""
    if _PW_THREAD_ID is not None and threading.get_ident() == _PW_THREAD_ID:
        return fn(*args, **kwargs)
    _ensure_pw_thread()
    box: dict[str, Any] = {"event": threading.Event(), "ok": False}
    _PW_JOBS.put((fn, args, kwargs, box))
    if not box["event"].wait(timeout):
        raise TimeoutError("Browser action timed out")
    if not box["ok"]:
        raise box["error"]
    return box["result"]


def get_page():
    """Shared live page handle (or None). Prefer session helpers — page is thread-bound."""
    with _LOCK:
        return _PAGE


def open_isolated_page():
    """A page of the caller's own, inside the shared browser context.

    Autonomous callers used the one shared page, so two of them navigating at
    the same time read each other's content. A tab per caller is real isolation
    within the same profile and the same Playwright thread.
    """
    result = ensure_session()
    if isinstance(result, dict) and result.get("ok") is False:
        raise RuntimeError(result.get("error") or "browser session unavailable")

    def _new():
        with _LOCK:
            context = _CONTEXT
        if context is None:
            raise RuntimeError("no live browser context")
        return context.new_page()

    return run_on_browser_thread(_new)


def close_isolated_page(page) -> None:
    """Close one caller's page without touching the shared session."""
    if page is None:
        return

    def _close():
        try:
            page.close()
        except Exception:  # noqa: BLE001 - closing must not raise
            pass

    try:
        run_on_browser_thread(_close, timeout=30.0)
    except Exception:  # noqa: BLE001
        pass


def _agent_paused_flags() -> tuple[bool, bool]:
    from jarvis import browser_agent as ba

    with ba._LOCK:
        return bool(ba._STATE.get("paused")), bool(ba._STATE.get("takeover"))


def is_paused() -> bool:
    paused, takeover = _agent_paused_flags()
    return paused or takeover


def append_step(
    action: str, detail: str = "", *, ok: bool = True, extra: dict | None = None
) -> dict[str, Any]:
    step = {
        "ts": time.time(),
        "action": action,
        "detail": (detail or "")[:500],
        "ok": ok,
        **(extra or {}),
    }
    with _LOCK:
        _STEPS.append(step)
        del _STEPS[:-100]
    return step


def steps(*, limit: int = 40) -> list[dict[str, Any]]:
    with _LOCK:
        return list(_STEPS[-limit:])


def clear_steps() -> None:
    with _LOCK:
        _STEPS.clear()


def stack_ready(*, force: bool = False) -> dict[str, bool]:
    now = time.time()
    with _LOCK:
        if (
            not force
            and _STACK_CACHE.get("stack")
            and now - float(_STACK_CACHE.get("ts") or 0) < _STACK_TTL
        ):
            return dict(_STACK_CACHE["stack"])
    from jarvis.browser_playwright import browser_stack_ready

    # Lightweight import check; chromium check may launch — cache aggressively
    stack = browser_stack_ready(probe_chromium=True)
    with _LOCK:
        _STACK_CACHE["ts"] = now
        _STACK_CACHE["stack"] = dict(stack)
    return dict(stack)


def profile_dir(slug: str | None = None) -> Path:
    from jarvis.active_project import browser_session_dir_for, get_active_slug

    slug = (slug or "").strip() or (get_active_slug() or "")
    if slug:
        return Path(browser_session_dir_for(slug))
    try:
        from jarvis.active_project import browser_session_dir

        raw = browser_session_dir()
        p = Path(raw) if not isinstance(raw, Path) else raw
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        path = DATA_DIR / "browser_profiles" / "_default"
        path.mkdir(parents=True, exist_ok=True)
        return path


def _ensure_session_impl(
    *,
    headless: bool | None = None,
    slug: str | None = None,
    headed_for_takeover: bool = False,
) -> dict[str, Any]:
    """Launch Playwright browser + page if needed. Must run on Playwright thread."""
    global _PW, _BROWSER, _CONTEXT, _PAGE, _PROFILE_SLUG, _HEADLESS, _LAUNCHED_AT

    stack = stack_ready()
    if not (stack.get("playwright") and stack.get("chromium")):
        return {
            "ok": False,
            "error": "Playwright/Chromium not available",
            "recovery": "Use Install Playwright in Browser, or: pip install playwright && playwright install chromium",
            "stack": stack,
        }

    want_headless = True if headless is None else bool(headless)
    if headed_for_takeover:
        want_headless = False

    target_slug = (slug or "").strip()
    if not target_slug:
        try:
            from jarvis.active_project import get_active_slug

            target_slug = get_active_slug() or ""
        except Exception:
            target_slug = ""

    with _LOCK:
        # Relaunch if profile or headless mode changed
        if _PAGE is not None and (_PROFILE_SLUG != target_slug or _HEADLESS != want_headless):
            _close_unlocked()
        if _PAGE is not None:
            return {
                "ok": True,
                "reused": True,
                "url": getattr(_PAGE, "url", "") or "",
                "profile": _PROFILE_SLUG,
                "headless": _HEADLESS,
            }

        try:
            from playwright.sync_api import sync_playwright

            user_dir = profile_dir(target_slug)
            user_dir.mkdir(parents=True, exist_ok=True)
            _PW = sync_playwright().start()
            # Persistent context gives per-project cookies/storage
            _CONTEXT = _PW.chromium.launch_persistent_context(
                str(user_dir / "pw_profile"),
                headless=want_headless,
                accept_downloads=False,
                viewport={"width": 1280, "height": 800},
            )
            _BROWSER = _CONTEXT  # persistent context acts as browser+context
            pages = _CONTEXT.pages
            _PAGE = pages[0] if pages else _CONTEXT.new_page()
            _PROFILE_SLUG = target_slug
            _HEADLESS = want_headless
            _LAUNCHED_AT = time.time()
            append_step("launch", f"profile={target_slug or '_default'} headless={want_headless}")
            return {
                "ok": True,
                "reused": False,
                "url": getattr(_PAGE, "url", "") or "",
                "profile": _PROFILE_SLUG,
                "headless": _HEADLESS,
                "profile_dir": str(user_dir),
            }
        except Exception as exc:
            log.exception("ensure_session failed")
            _close_unlocked()
            return {
                "ok": False,
                "error": _owner_error(exc),
                "recovery": "Check Playwright install and Chromium dependencies",
            }


def ensure_session(
    *,
    headless: bool | None = None,
    slug: str | None = None,
    headed_for_takeover: bool = False,
) -> dict[str, Any]:
    """Launch Playwright browser + page if needed. Fail closed if stack missing."""
    try:
        return run_on_browser_thread(
            _ensure_session_impl,
            headless=headless,
            slug=slug,
            headed_for_takeover=headed_for_takeover,
        )
    except Exception as exc:
        log.exception("ensure_session dispatch failed")
        return {
            "ok": False,
            "error": _owner_error(exc),
            "recovery": "Retry Open, or Restart the browser session",
        }


def _close_unlocked() -> None:
    global _PW, _BROWSER, _CONTEXT, _PAGE, _PROFILE_SLUG, _LAUNCHED_AT
    for obj, meth in (
        (_CONTEXT, "close"),
        (_BROWSER, "close"),
    ):
        try:
            if obj is not None and hasattr(obj, meth):
                getattr(obj, meth)()
        except Exception:
            pass
    try:
        if _PW is not None:
            _PW.stop()
    except Exception:
        pass
    _PW = None
    _BROWSER = None
    _CONTEXT = None
    _PAGE = None
    _PROFILE_SLUG = ""
    _LAUNCHED_AT = 0.0


def close_session() -> dict[str, Any]:
    def _impl() -> dict[str, Any]:
        with _LOCK:
            had = _PAGE is not None
            _close_unlocked()
            if had:
                append_step("close", "session closed")
        return {"ok": True, "closed": had}

    try:
        return run_on_browser_thread(_impl)
    except Exception as exc:
        log.exception("close_session failed")
        with _LOCK:
            _close_unlocked()
        return {"ok": True, "closed": True, "warning": _owner_error(exc)}


def session_info() -> dict[str, Any]:
    def _impl() -> dict[str, Any]:
        with _LOCK:
            page = _PAGE
            url = ""
            if page is not None:
                try:
                    url = getattr(page, "url", "") or ""
                except Exception:
                    url = ""
            return {
                "active": page is not None,
                "url": url,
                "profile": _PROFILE_SLUG,
                "headless": _HEADLESS,
                "launched_at": _LAUNCHED_AT,
                "steps": list(_STEPS[-20:]),
                "profile_dir": str(profile_dir(_PROFILE_SLUG)) if page else "",
            }

    try:
        return run_on_browser_thread(_impl)
    except Exception:
        with _LOCK:
            return {
                "active": _PAGE is not None,
                "url": "",
                "profile": _PROFILE_SLUG,
                "headless": _HEADLESS,
                "launched_at": _LAUNCHED_AT,
                "steps": list(_STEPS[-20:]),
                "profile_dir": "",
            }


def _goto_impl(url: str, timeout_ms: int) -> dict[str, Any]:
    ensured = _ensure_session_impl()
    if not ensured.get("ok"):
        return {"ok": False, **ensured}
    page = _PAGE
    if page is None:
        return {
            "ok": False,
            "error": "No page after launch",
            "recovery": "Retry Open or Restart session",
        }
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=min(8000, timeout_ms))
        except Exception:
            pass  # some pages never networkidle
        final = page.url
        title = page.title()
        append_step("navigate", final, ok=True)
        return {"ok": True, "url": final, "title": title}
    except Exception as exc:
        if _is_greenlet_error(exc):
            # Stale handle from a pre-thread session — relaunch once on this thread.
            log.warning("goto greenlet fault — relaunching session")
            with _LOCK:
                _close_unlocked()
            ensured = _ensure_session_impl()
            if not ensured.get("ok"):
                return {"ok": False, **ensured}
            page = _PAGE
            if page is None:
                return {
                    "ok": False,
                    "error": "Browser session needed a clean restart",
                    "recovery": "Retry Open",
                }
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                final = page.url
                title = page.title()
                append_step("navigate", final, ok=True, extra={"relaunched": True})
                return {"ok": True, "url": final, "title": title, "relaunched": True}
            except Exception as exc2:
                append_step("navigate", url, ok=False, extra={"error": str(exc2)})
                return {
                    "ok": False,
                    "error": _owner_error(exc2),
                    "url": url,
                    "recovery": "Retry Open or Restart the browser session",
                }
        append_step("navigate", url, ok=False, extra={"error": str(exc)})
        return {
            "ok": False,
            "error": _owner_error(exc),
            "url": url,
            "recovery": "Check the URL, network, or try again after Install Playwright",
        }


def goto(url: str, *, timeout_ms: int = 30000) -> dict[str, Any]:
    """Navigate the live page. Fail closed on errors."""
    try:
        return run_on_browser_thread(
            _goto_impl, url, timeout_ms, timeout=max(60.0, timeout_ms / 1000.0 + 15.0)
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": _owner_error(exc),
            "url": url,
            "recovery": "Retry Open or Restart the browser session",
        }


def click_selector(selector: str, *, timeout_ms: int = 10000) -> dict[str, Any]:
    if is_paused():
        return {"ok": False, "message": "Agent paused — Resume or finish Takeover first"}

    def _impl() -> dict[str, Any]:
        page = _PAGE
        if not page:
            return {"ok": False, "message": "No browser page — navigate first"}
        try:
            page.click(selector, timeout=timeout_ms)
            append_step("click", selector)
            return {"ok": True, "selector": selector}
        except Exception as exc:
            append_step("click", selector, ok=False, extra={"error": str(exc)})
            return {"ok": False, "message": _owner_error(exc), "selector": selector}

    try:
        return run_on_browser_thread(_impl)
    except Exception as exc:
        return {"ok": False, "message": _owner_error(exc), "selector": selector}


def fill_selector(selector: str, text: str, *, timeout_ms: int = 10000) -> dict[str, Any]:
    if is_paused():
        return {"ok": False, "message": "Agent paused — Resume or finish Takeover first"}

    def _impl() -> dict[str, Any]:
        page = _PAGE
        if not page:
            return {"ok": False, "message": "No browser page — navigate first"}
        try:
            page.fill(selector, str(text), timeout=timeout_ms)
            append_step("fill", selector)
            return {"ok": True, "selector": selector, "filled": True}
        except Exception as exc:
            append_step("fill", selector, ok=False, extra={"error": str(exc)})
            return {"ok": False, "message": _owner_error(exc)}

    try:
        return run_on_browser_thread(_impl)
    except Exception as exc:
        return {"ok": False, "message": _owner_error(exc)}


def select_option(selector: str, value: str, *, timeout_ms: int = 10000) -> dict[str, Any]:
    if is_paused():
        return {"ok": False, "message": "Agent paused"}

    def _impl() -> dict[str, Any]:
        page = _PAGE
        if not page:
            return {"ok": False, "message": "No browser page"}
        try:
            page.select_option(selector, value, timeout=timeout_ms)
            append_step("select", f"{selector}={value}")
            return {"ok": True, "selector": selector, "value": value}
        except Exception as exc:
            append_step("select", selector, ok=False, extra={"error": str(exc)})
            return {"ok": False, "message": _owner_error(exc)}

    try:
        return run_on_browser_thread(_impl)
    except Exception as exc:
        return {"ok": False, "message": _owner_error(exc)}


def scroll_by(dy: int = 600) -> dict[str, Any]:
    if is_paused():
        return {"ok": False, "message": "Agent paused"}

    def _impl() -> dict[str, Any]:
        page = _PAGE
        if not page:
            return {"ok": False, "message": "No browser page"}
        try:
            page.mouse.wheel(0, int(dy))
            append_step("scroll", f"dy={dy}")
            return {"ok": True, "dy": dy}
        except Exception as exc:
            return {"ok": False, "message": _owner_error(exc)}

    try:
        return run_on_browser_thread(_impl)
    except Exception as exc:
        return {"ok": False, "message": _owner_error(exc)}


def extract_text(*, limit: int = 8000) -> dict[str, Any]:
    def _impl() -> dict[str, Any]:
        page = _PAGE
        if not page:
            return {"ok": False, "message": "No browser page"}
        try:
            text = page.inner_text("body")
            append_step("extract", f"{len(text)} chars")
            return {
                "ok": True,
                "text": (text or "")[:limit],
                "url": page.url,
                "title": page.title(),
            }
        except Exception as exc:
            return {"ok": False, "message": _owner_error(exc)}

    try:
        return run_on_browser_thread(_impl)
    except Exception as exc:
        return {"ok": False, "message": _owner_error(exc)}


def wait_ms(ms: int = 500) -> dict[str, Any]:
    import time as _t

    if is_paused():
        return {"ok": False, "message": "Agent paused"}
    _t.sleep(min(5.0, max(0.05, int(ms) / 1000.0)))
    append_step("wait", f"{ms}ms")
    return {"ok": True, "waited": True}
