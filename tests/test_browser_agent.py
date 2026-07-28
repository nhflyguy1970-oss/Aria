"""Browser agent — truthful navigation, screenshots, security, routing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _reset_browser():
    from jarvis import browser_agent as ba
    from jarvis.browser_product import session as sess

    with patch.object(sess, "close_session", return_value={"ok": True, "closed": True}):
        ba.stop()
    yield
    with patch.object(sess, "close_session", return_value={"ok": True, "closed": True}):
        ba.stop()


def test_navigate_fails_closed_without_playwright(monkeypatch):
    from jarvis import browser_agent as ba

    monkeypatch.setattr(ba, "_playwright_available", lambda: False)
    result = ba.navigate("https://example.com")
    assert result["ok"] is False
    assert "did not occur" in (result.get("message") or "").lower() or "not available" in (
        result.get("message") or ""
    ).lower()
    assert result.get("recovery")


def test_navigate_system_fallback_when_requested(monkeypatch):
    from jarvis import browser_agent as ba

    monkeypatch.setattr(ba, "_playwright_available", lambda: False)
    monkeypatch.setattr("jarvis.browser_util.open_url", lambda url, **kw: True)
    result = ba.navigate("https://example.com", allow_system_fallback=True)
    assert result["ok"] is True
    assert result.get("fallback") is True
    assert "system browser" in (result.get("message") or "").lower()
    st = ba.status()
    assert st["status"] == "external"


def test_navigate_real_goto(monkeypatch):
    from jarvis import browser_agent as ba

    monkeypatch.setattr(ba, "_playwright_available", lambda: True)
    monkeypatch.setattr(
        "jarvis.browser_product.session.goto",
        lambda url, **kw: {"ok": True, "url": url, "title": "Example"},
    )
    monkeypatch.setattr(
        ba,
        "screenshot",
        lambda **kw: {"ok": True, "path": "/tmp/x.png"},
    )
    monkeypatch.setattr(ba, "_sync_page_ref", lambda: None)
    result = ba.navigate("https://example.com")
    assert result["ok"] is True
    assert "Navigated" in (result.get("message") or "")
    assert "Opened" not in (result.get("message") or "") or "Navigated" in result["message"]


def test_screenshot_skipped_on_fallback():
    from jarvis import browser_agent as ba

    with ba._LOCK:
        ba._STATE.update({"fallback": True, "url": "https://example.com"})
    shot = ba.screenshot()
    assert shot.get("skipped") is True
    assert shot.get("ok") is False


def test_url_policy_blocks_file():
    from jarvis.browser_agent import check_url_safe

    out = check_url_safe("file:///etc/passwd")
    assert out["ok"] is False


def test_url_policy_blocks_checkout_without_risky():
    from jarvis.browser_agent import _check_url_safe

    ok, reason = _check_url_safe("https://paypal.com/checkout")
    assert ok is False
    assert "checkout" in reason.lower() or "confirm" in reason.lower()


def test_download_safety():
    from jarvis.browser_product.downloads import check_download_safe

    bad = check_download_safe("https://ex.com/malware.exe")
    assert bad["ok"] is False
    good = check_download_safe("https://ex.com/report.pdf")
    assert good["ok"] is True


def test_search_browse_query_parser():
    from jarvis.extensions.browser.routes import _search_browse_query

    assert "cats" in _search_browse_query("search the web for cats and open")
    assert "python" in _search_browse_query("find python tutorials and browse")


def test_playwright_stack_probe():
    from jarvis.browser_playwright import browser_stack_ready

    stack = browser_stack_ready(probe_chromium=False)
    assert "playwright" in stack
    assert "chromium" in stack


def test_run_agent_task_requires_page(monkeypatch):
    from jarvis import browser_agent as ba

    monkeypatch.setattr(ba, "_playwright_available", lambda: True)
    monkeypatch.setattr(
        "jarvis.browser_product.session.ensure_session",
        lambda **kw: {"ok": True},
    )
    monkeypatch.setattr("jarvis.browser_product.session.get_page", lambda: None)
    monkeypatch.setattr(ba, "_sync_page_ref", lambda: None)
    out = ba.run_agent_task("click login")
    assert out["ok"] is False
    assert "navigate" in (out.get("message") or "").lower() or "page" in (
        out.get("message") or ""
    ).lower()


def test_browser_home_snapshot(monkeypatch):
    monkeypatch.setattr(
        "jarvis.browser_agent.status",
        lambda: {
            "agent_ready": False,
            "status": "idle",
            "modes_available": {"dom": False, "vlm": False},
        },
    )
    from jarvis.browser_product.home import browser_home_snapshot

    snap = browser_home_snapshot()
    assert snap["ok"] is True
    assert snap["product"] == "browser"
    assert "Ctrl+Shift+B" in snap["shortcut"]


def test_browser_read_requires_approval():
    from jarvis.automation.pipelines.actions import execute_action

    out = execute_action("browser_read", {"url": "https://example.com"}, {}, approve_experimental=False)
    assert out["ok"] is False
    assert out.get("permission_required") is True


def test_extension_routes_nonempty():
    from jarvis.extensions.browser.routes import browser_routes

    rules = browser_routes()
    assert len(rules) >= 4
    names = {r.action for r in rules}
    assert "browse_web" in names


def test_cheatsheet_browser_default():
    from jarvis.cheatsheets import load_default_content, normalize_key

    assert normalize_key("browse") == "browser"
    content = load_default_content("browser")
    assert content and "Ctrl+Shift+B" in content


def test_browser_ui_wired():
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert 'id="browserView"' in html
    assert "browser_home.js" in html
    assert "browser_panel.js" in html
    assert "browserHomeBody" in html
    assert "browserStepLog" in html
    assert "Ctrl+Shift+B" in html
