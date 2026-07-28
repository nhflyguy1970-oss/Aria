"""Live Playwright integration tests (skip if stack missing)."""

from __future__ import annotations

import pytest

from jarvis.browser_playwright import browser_stack_ready

STACK = browser_stack_ready(probe_chromium=True)
pytestmark = pytest.mark.skipif(
    not (STACK.get("playwright") and STACK.get("chromium")),
    reason="Playwright/Chromium not installed",
)


@pytest.fixture(autouse=True)
def _cleanup():
    from jarvis import browser_agent as ba

    yield
    ba.stop()


def test_real_navigate_and_screenshot():
    from jarvis import browser_agent as ba

    nav = ba.navigate("https://example.com")
    assert nav["ok"] is True
    assert "example.com" in (nav.get("url") or "")
    assert "Navigated" in (nav.get("message") or "")
    st = ba.status()
    assert st["agent_ready"] is True
    assert st["modes_available"].get("dom") is True
    assert st.get("last_screenshot")
    shot = ba.screenshot(label="test")
    assert shot["ok"] is True


def test_extract_after_navigate():
    from jarvis import browser_agent as ba
    from jarvis.browser_product.session import extract_text

    assert ba.navigate("https://example.com")["ok"]
    ext = extract_text(limit=2000)
    assert ext["ok"] is True
    assert "Example" in (ext.get("text") or ext.get("title") or "")


def test_modes_not_clobbered_by_state():
    from jarvis import browser_agent as ba

    st = ba.status()
    assert isinstance(st.get("modes_available"), dict)
    assert "dom" in st["modes_available"]
