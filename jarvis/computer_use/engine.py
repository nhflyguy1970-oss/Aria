"""Computer-use engine — structured, bounded, permissioned browser actions.

Drives ARIA's existing Playwright stack (jarvis.browser_product.session) rather
than launching a browser of its own, so there is one browser thread, one
profile policy and one lifecycle.

The driver is injectable. Unit tests exercise the contract — validation,
permissions, bounds, redaction, error classification — with a fake driver, so
the suite never depends on a real browser or the internet; the browser tests
use the real driver against a local fixture server.

Every action returns the same structured envelope. A failed action is reported
as a failure with a classified reason: nothing here converts an incomplete
action into a success, and content that was never retrieved is never returned.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Protocol

from jarvis.computer_use import actions as A
from jarvis.computer_use import sessions

log = logging.getLogger("jarvis.computer_use")

# Error classes, so a caller can tell retryable from terminal.
ERR_NAVIGATION = "navigation"
ERR_TARGET = "target_not_found"
ERR_STALE = "stale_target"
ERR_TIMEOUT = "timeout"
ERR_BLOCKED = "blocked"
ERR_PERMISSION = "permission_denied"
ERR_SESSION = "session"
ERR_BROWSER = "browser_unavailable"
ERR_VALIDATION = "validation"
ERR_INTERNAL = "internal"


class Driver(Protocol):
    def navigate(self, url: str) -> dict[str, Any]: ...
    def state(self) -> dict[str, Any]: ...
    def extract(self, limit: int) -> dict[str, Any]: ...
    def click(self, target: str) -> dict[str, Any]: ...
    def type(self, target: str, text: str) -> dict[str, Any]: ...
    def select(self, target: str, value: str) -> dict[str, Any]: ...
    def scroll(self, amount: int) -> dict[str, Any]: ...
    def history(self, direction: str) -> dict[str, Any]: ...
    def screenshot(self, label: str) -> dict[str, Any]: ...
    def close(self) -> dict[str, Any]: ...


class PlaywrightDriver:
    """Adapter over ARIA's existing browser session thread.

    `allow_local` navigates the page directly instead of going through
    jarvis.browser_agent.navigate, whose host policy independently rejects
    loopback targets. The engine has already validated the URL at that point,
    so re-applying the policy here would make an authorised local target
    unreachable (local test fixtures, deliberate internal endpoints).
    """

    def __init__(self, *, allow_local: bool = False):
        self.allow_local = allow_local

    def _page(self):
        from jarvis.browser_product.session import ensure_session, get_page

        result = ensure_session()
        if isinstance(result, dict) and result.get("ok") is False:
            raise RuntimeError(result.get("error") or "browser session unavailable")
        page = get_page()
        if page is None:
            raise RuntimeError("no live browser page")
        return page

    def _run(self, fn, *args, timeout: float = 30.0, **kwargs):
        from jarvis.browser_product.session import run_on_browser_thread

        return run_on_browser_thread(fn, *args, timeout=timeout, **kwargs)

    def navigate(self, url: str) -> dict[str, Any]:
        if self.allow_local:

            def _go(page):
                page.goto(url, timeout=A.LIMITS["navigation_timeout_ms"])
                return {"url": page.url, "title": page.title()}

            try:
                return self._run(_go, self._page())
            except Exception as exc:  # noqa: BLE001
                raise NavigationFailure(str(exc)) from exc

        from jarvis.browser_agent import navigate as agent_navigate

        result = agent_navigate(url) or {}
        if not result.get("ok"):
            raise NavigationFailure(result.get("message") or "navigation failed")
        return self.state()

    def state(self) -> dict[str, Any]:
        def _read(page):
            return {"url": page.url, "title": page.title()}

        page = self._page()
        return self._run(_read, page)

    def extract(self, limit: int) -> dict[str, Any]:
        def _read(page):
            text = page.inner_text("body")
            return {"text": text[:limit], "truncated": len(text) > limit, "url": page.url}

        return self._run(_read, self._page())

    def _locate(self, page, target: str):
        """Prefer semantic targets; fall back to a selector. Never guess blindly."""
        if target.startswith(("#", ".", "//", "css=", "xpath=", "[")):
            return page.locator(target)
        loc = page.get_by_role("button", name=target)
        if loc.count():
            return loc.first
        loc = page.get_by_role("link", name=target)
        if loc.count():
            return loc.first
        loc = page.get_by_label(target)
        if loc.count():
            return loc.first
        loc = page.get_by_placeholder(target)
        if loc.count():
            return loc.first
        loc = page.get_by_text(target, exact=False)
        if loc.count():
            return loc.first
        return page.locator(target)

    def click(self, target: str) -> dict[str, Any]:
        def _do(page):
            loc = self._locate(page, target)
            if not loc.count():
                raise TargetNotFound(target)
            loc.first.click(timeout=A.LIMITS["action_timeout_ms"])
            return {"url": page.url, "title": page.title()}

        return self._run(_do, self._page())

    def type(self, target: str, text: str) -> dict[str, Any]:
        def _do(page):
            loc = self._locate(page, target)
            if not loc.count():
                raise TargetNotFound(target)
            loc.first.fill(text, timeout=A.LIMITS["action_timeout_ms"])
            return {"url": page.url, "title": page.title()}

        return self._run(_do, self._page())

    def select(self, target: str, value: str) -> dict[str, Any]:
        def _do(page):
            loc = self._locate(page, target)
            if not loc.count():
                raise TargetNotFound(target)
            loc.first.select_option(value, timeout=A.LIMITS["action_timeout_ms"])
            return {"url": page.url, "title": page.title()}

        return self._run(_do, self._page())

    def scroll(self, amount: int) -> dict[str, Any]:
        def _do(page):
            page.mouse.wheel(0, amount)
            return {"url": page.url, "title": page.title()}

        return self._run(_do, self._page())

    def history(self, direction: str) -> dict[str, Any]:
        def _do(page):
            if direction == "back":
                page.go_back(timeout=A.LIMITS["navigation_timeout_ms"])
            elif direction == "forward":
                page.go_forward(timeout=A.LIMITS["navigation_timeout_ms"])
            else:
                page.reload(timeout=A.LIMITS["navigation_timeout_ms"])
            return {"url": page.url, "title": page.title()}

        return self._run(_do, self._page())

    def screenshot(self, label: str) -> dict[str, Any]:
        from jarvis.browser_product.screenshots import capture

        result = capture(label=label, reason="computer_use") or {}
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "screenshot failed")
        return {"path": result.get("path") or ""}

    def close(self) -> dict[str, Any]:
        try:
            from jarvis.browser_product.session import close as close_session

            close_session()
        except Exception:  # noqa: BLE001 - closing must not raise
            pass
        return {"closed": True}


class NavigationFailure(RuntimeError):
    pass


class TargetNotFound(LookupError):
    pass


def _classify(exc: BaseException) -> str:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if isinstance(exc, A.NavigationBlocked):
        return ERR_BLOCKED
    if isinstance(exc, A.ActionError):
        return ERR_VALIDATION
    if isinstance(exc, sessions.SessionError):
        return ERR_SESSION
    # Browser-stack unavailability outranks the action-specific classes: a
    # missing browser is a retryable environment condition no matter which
    # action surfaced it, and reporting it as "navigation" hides that.
    if any(
        marker in text
        for marker in (
            "playwright",
            "chromium",
            "browser agent disabled",
            "no live browser page",
            "browser session unavailable",
        )
    ):
        return ERR_BROWSER
    if isinstance(exc, TargetNotFound) or "not found" in text or "no element" in text:
        return ERR_TARGET
    if isinstance(exc, NavigationFailure):
        return ERR_NAVIGATION
    if "timeout" in name or "timeout" in text:
        return ERR_TIMEOUT
    if "detached" in text or "stale" in text or "element is not attached" in text:
        return ERR_STALE
    if "browser" in text and ("unavailable" in text or "disabled" in text or "no live" in text):
        return ERR_BROWSER
    return ERR_INTERNAL


def _envelope(session_id: str, action: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "session_id": session_id,
        "action": action,
        "params": A.redact_params(action, params),
        "url": "",
        "title": "",
        "result": None,
        "error": None,
        "error_kind": None,
        "duration_ms": 0.0,
    }


def perform(
    session_id: str,
    action: str,
    params: dict[str, Any] | None = None,
    *,
    driver: Driver | None = None,
    agent_id: str = "",
    owner: str = "",
    allow_local: bool = False,
    cancel_check=None,
) -> dict[str, Any]:
    """Execute one bounded, permissioned computer-use action."""
    params = dict(params or {})
    started = time.perf_counter()
    out = _envelope(session_id, action, params)

    try:
        A.validate(action, params)

        # Agent permission is evaluated against the specialist's own definition.
        if agent_id:
            from jarvis.computer_use.permissions import check_agent_action

            check_agent_action(agent_id, action)

        session = sessions.require(session_id, owner=owner)

        if cancel_check is not None and cancel_check():
            out.update(error="cancelled at action boundary", error_kind="cancelled")
            return out

        drv = driver or PlaywrightDriver(allow_local=allow_local)

        if action == "navigate":
            url = A.check_url(params["url"], allow_local=allow_local)
            state = drv.navigate(url)
            out["result"] = state
        elif action in ("back", "forward", "reload"):
            out["result"] = drv.history(action)
        elif action == "inspect":
            out["result"] = drv.state()
        elif action == "extract":
            limit = min(
                int(params.get("limit") or A.LIMITS["max_extract_chars"]),
                A.LIMITS["max_extract_chars"],
            )
            out["result"] = drv.extract(limit)
        elif action == "screenshot":
            if not sessions.may_screenshot(session_id):
                out.update(
                    error=f"max_screenshots_per_session ({A.LIMITS['max_screenshots_per_session']}) reached",
                    error_kind="bounded",
                )
                return out
            out["result"] = drv.screenshot(str(params.get("label") or "computer_use"))
        elif action == "click":
            out["result"] = drv.click(str(params["target"]))
        elif action == "type":
            out["result"] = drv.type(str(params["target"]), str(params["text"]))
        elif action == "select":
            out["result"] = drv.select(str(params["target"]), str(params["value"]))
        elif action == "scroll":
            out["result"] = drv.scroll(int(params.get("amount") or 600))
        elif action == "wait":
            time.sleep(min(float(params.get("seconds") or 0.5), 5.0))
            out["result"] = drv.state()
        elif action == "close":
            out["result"] = drv.close()
            sessions.close(session_id)
        else:  # high-impact actions have no default implementation
            out.update(
                error=f"Action {action!r} is not implemented for autonomous use",
                error_kind=ERR_PERMISSION,
            )
            return out

        state = out["result"] if isinstance(out["result"], dict) else {}
        out["url"] = state.get("url") or session.get("url") or ""
        out["title"] = state.get("title") or ""
        out["ok"] = True
        sessions.record_action(session_id, action=action, url=out["url"], title=out["title"])
        # Never echo secrets back through the result payload.
        out["result"] = A.redact(out["result"])
    except Exception as exc:  # noqa: BLE001 - every failure is classified, never swallowed
        kind = _classify(exc)
        out.update(error=str(exc)[:500], error_kind=kind)
        if kind in (ERR_BROWSER, ERR_INTERNAL):
            log.warning("computer-use %s failed (%s): %s", action, kind, exc)
        if kind == ERR_BROWSER:
            sessions.fail(session_id, str(exc))
    finally:
        out["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return out


def open_session(*, owner: str = "", task_id: str = "", label: str = "") -> dict[str, Any]:
    sessions.reap_expired()
    return sessions.create(owner=owner, task_id=task_id, label=label)


def run_steps(
    session_id: str,
    steps: list[dict[str, Any]],
    *,
    driver: Driver | None = None,
    agent_id: str = "",
    owner: str = "",
    allow_local: bool = False,
    cancel_check=None,
) -> dict[str, Any]:
    """Run a bounded sequence, stopping at the first failure or cancellation."""
    results = []
    for step in steps:
        outcome = perform(
            session_id,
            str(step.get("action") or ""),
            step.get("params") or {},
            driver=driver,
            agent_id=agent_id,
            owner=owner,
            allow_local=allow_local,
            cancel_check=cancel_check,
        )
        results.append(outcome)
        if not outcome["ok"]:
            break
    return {
        "ok": all(r["ok"] for r in results) and bool(results),
        "session_id": session_id,
        "steps_run": len(results),
        "steps": results,
        "failed": next((r for r in results if not r["ok"]), None),
    }
