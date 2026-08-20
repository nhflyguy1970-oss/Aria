"""Live certification: computer-use sessions must not share one browser page.

Two sessions navigating at the same time read each other's content, and what
they extracted was attributed to the URL they had asked for — evidence pointing
at a source it never came from.
"""

from __future__ import annotations

import os
import threading

import pytest

from jarvis.computer_use import engine, sessions


class FakePage:
    """A page that only knows where it was told to go."""

    def __init__(self):
        self.url = "about:blank"
        self._closed = False

    def goto(self, url, timeout=None):
        self.url = url

    def title(self):
        return f"title of {self.url}"

    def inner_text(self, _selector):
        return f"body of {self.url}"

    def is_closed(self):
        return self._closed

    def close(self):
        self._closed = True


@pytest.fixture
def isolated_pages(monkeypatch):
    """Every open_isolated_page() call yields a distinct page, as a real
    context.new_page() would."""
    made: list[FakePage] = []

    def _open():
        page = FakePage()
        made.append(page)
        return page

    monkeypatch.setattr("jarvis.browser_product.session.open_isolated_page", _open)
    monkeypatch.setattr(
        "jarvis.browser_product.session.close_isolated_page",
        lambda page: page.close() if page else None,
    )
    monkeypatch.setattr(
        "jarvis.browser_product.session.run_on_browser_thread",
        lambda fn, *a, timeout=None, **kw: fn(*a, **kw),
    )
    engine._SESSION_PAGES.clear()
    yield made
    engine._SESSION_PAGES.clear()


def _drive(session_id: str, url: str, allow_local: bool = True) -> dict:
    drv = engine.PlaywrightDriver(allow_local=allow_local, session_id=session_id)
    drv.navigate(url)
    return drv.extract(10_000)


def test_each_session_keeps_its_own_page(isolated_pages, data_dir):
    a = sessions.create(owner="research_specialist")["id"]
    b = sessions.create(owner="research_specialist")["id"]

    _drive(a, "https://a.example/")
    _drive(b, "https://b.example/")

    assert _drive(a, "https://a.example/")["url"] == "https://a.example/"
    assert engine._SESSION_PAGES[a] is not engine._SESSION_PAGES[b]
    assert len(isolated_pages) == 2, "sessions shared a page"


def test_one_session_cannot_read_anothers_page(isolated_pages, data_dir):
    a = sessions.create(owner="research_specialist")["id"]
    b = sessions.create(owner="research_specialist")["id"]

    _drive(a, "https://mine.example/")
    _drive(b, "https://theirs.example/")

    out = engine.PlaywrightDriver(allow_local=True, session_id=a).extract(10_000)
    assert out["url"] == "https://mine.example/"
    assert "theirs" not in out["text"]


def test_concurrent_sessions_do_not_contaminate_each_other(isolated_pages, data_dir):
    ids = [sessions.create(owner="research_specialist")["id"] for _ in range(4)]
    urls = [f"https://site{i}.example/" for i in range(4)]
    seen: dict[str, str] = {}
    barrier = threading.Barrier(len(ids))

    def run(session_id, url):
        barrier.wait()
        for _ in range(3):
            out = _drive(session_id, url)
            seen[session_id] = out["url"]

    threads = [threading.Thread(target=run, args=(s, u)) for s, u in zip(ids, urls)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    for session_id, url in zip(ids, urls):
        assert seen[session_id] == url, f"{session_id} read another session's page"


def test_a_session_keeps_the_same_page_across_calls(isolated_pages, data_dir):
    sid = sessions.create(owner="research_specialist")["id"]
    _drive(sid, "https://one.example/")
    first = engine._SESSION_PAGES[sid]
    _drive(sid, "https://two.example/")
    assert engine._SESSION_PAGES[sid] is first, "a session should not leak a tab per call"


def test_closing_one_session_leaves_the_others_alone(isolated_pages, data_dir):
    a = sessions.create(owner="research_specialist")["id"]
    b = sessions.create(owner="research_specialist")["id"]
    _drive(a, "https://a.example/")
    _drive(b, "https://b.example/")

    engine.PlaywrightDriver(allow_local=True, session_id=a).close()

    assert a not in engine._SESSION_PAGES
    assert engine._SESSION_PAGES[b].is_closed() is False
    assert _drive(b, "https://b.example/")["url"] == "https://b.example/"


def test_an_expired_session_does_not_leak_its_tab(isolated_pages, data_dir, monkeypatch):
    sid = sessions.create(owner="research_specialist")["id"]
    _drive(sid, "https://a.example/")
    page = engine._SESSION_PAGES[sid]

    monkeypatch.setitem(sessions.LIMITS, "session_ttl_s", -1)
    engine.open_session(owner="research_specialist")

    assert sid not in engine._SESSION_PAGES
    assert page.is_closed() is True


def test_isolation_does_not_bypass_the_host_policy(isolated_pages, data_dir):
    """A session-owned page must satisfy the same URL policy browser_agent
    applies to the shared page."""
    from jarvis.computer_use import actions as A

    sid = sessions.create(owner="research_specialist")["id"]
    drv = engine.PlaywrightDriver(allow_local=False, session_id=sid)
    with pytest.raises((A.NavigationBlocked, engine.NavigationFailure)):
        drv.navigate("http://127.0.0.1:8765/api/ping")


def test_screenshot_retention_is_actually_enforced(data_dir, monkeypatch, tmp_path):
    """The policy existed and was reachable by hand, but nothing ran it, so
    screenshots grew one file per navigation forever."""
    import time

    from jarvis.computer_use import engine, retention

    shots = tmp_path / "shots"
    shots.mkdir()
    monkeypatch.setattr(retention, "screenshot_dir", lambda: shots)
    old = time.time() - 7200
    for i in range(12):
        path = shots / f"shot-{i}.png"
        path.write_bytes(b"x" * 100)
        os.utime(path, (old + i, old + i))

    monkeypatch.setattr(retention, "MAX_SCREENSHOTS", 5)
    engine.open_session(owner="research_specialist")

    remaining = sorted(p.name for p in shots.glob("*.png"))
    assert len(remaining) == 5, f"retention not applied: {remaining}"
    # The newest survive; the oldest are reclaimed.
    assert "shot-11.png" in remaining and "shot-0.png" not in remaining


def test_a_live_browser_is_not_reported_as_missing(monkeypatch):
    """The health probe launched a second Chromium against the profile this
    process already holds. It failed, and ARIA declared its own running browser
    unavailable — refusing every new session while research was using it."""
    from jarvis.browser_product import session as sess

    probed = {"count": 0}

    def _never_probe(**kw):
        probed["count"] += 1
        return {"playwright": False, "chromium": False}

    monkeypatch.setattr("jarvis.browser_playwright.browser_stack_ready", _never_probe)
    monkeypatch.setattr(sess, "_PAGE", object())

    assert sess.stack_ready() == {"playwright": True, "chromium": True}
    assert probed["count"] == 0, "probed while a live browser was already open"


def test_without_a_live_browser_the_probe_still_runs(monkeypatch):
    from jarvis.browser_product import session as sess

    monkeypatch.setattr(sess, "_PAGE", None)
    monkeypatch.setattr(sess, "_CONTEXT", None)
    sess._STACK_CACHE["ts"] = 0.0
    sess._STACK_CACHE["stack"] = {}
    monkeypatch.setattr(
        "jarvis.browser_playwright.browser_stack_ready",
        lambda **kw: {"playwright": True, "chromium": False},
    )
    assert sess.stack_ready() == {"playwright": True, "chromium": False}
