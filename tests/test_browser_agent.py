"""Browser agent fixes — fallback state, routing, playwright stack."""

from __future__ import annotations

from unittest.mock import patch


def test_navigate_fallback_updates_state(monkeypatch):
    from jarvis import browser_agent as ba

    ba.stop()
    monkeypatch.setattr(ba, "_playwright_available", lambda: False)
    monkeypatch.setattr("jarvis.browser_util.open_url", lambda url, **kw: True)
    result = ba.navigate("https://example.com")
    assert result["ok"] is True
    assert result["fallback"] is True
    st = ba.status()
    assert st["url"] == "https://example.com"
    assert st["status"] == "external"


def test_screenshot_skipped_on_fallback(monkeypatch):
    from jarvis import browser_agent as ba

    ba.stop()
    monkeypatch.setattr(ba, "_PAGE", None)
    with ba._LOCK:
        ba._STATE.update({"fallback": True, "url": "https://example.com"})
    shot = ba.screenshot()
    assert shot.get("skipped") is True
    ba.stop()


def test_search_browse_query_parser():
    from jarvis.extensions.browser.routes import _search_browse_query

    assert "cats" in _search_browse_query("search the web for cats and open")
    assert "python" in _search_browse_query("find python tutorials and browse")


def test_router_search_and_open(session):
    from jarvis.router import route_intent

    intent = route_intent("search the web for example.com and open", session)
    assert intent["action"] == "search_and_browse"
    assert "example" in intent["params"].get("query", "")


def test_router_web_search_without_open(session):
    from jarvis.router import route_intent

    intent = route_intent("search the web for cats", session)
    assert intent["action"] == "web_search"


def test_playwright_stack_probe():
    from jarvis.browser_playwright import browser_stack_ready

    stack = browser_stack_ready()
    assert "playwright" in stack
    assert "chromium" in stack
