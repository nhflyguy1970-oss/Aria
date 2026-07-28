"""Browser product package coverage."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.browser_product.downloads import check_download_safe
from jarvis.browser_product.history import add_bookmark, list_bookmarks, list_history, record_visit
from jarvis.browser_product.multi_tab import merge_findings, plan_research
from jarvis.browser_product.session import append_step, steps
from jarvis.browser_product.terminology import BOUNDARIES


def test_boundaries():
    assert "live_page_automation" in BOUNDARIES["owns"]
    assert "full_chrome_replacement" in BOUNDARIES["does_not_own"]


def test_history_and_bookmarks(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.browser_product.history.HIST_FILE", tmp_path / "h.json")
    monkeypatch.setattr("jarvis.browser_product.history.BOOK_FILE", tmp_path / "b.json")
    record_visit("https://example.com", title="Example")
    assert list_history(query="example")["total"] >= 1
    add_bookmark("https://example.com", title="Ex")
    assert list_bookmarks()["items"]


def test_steps_log():
    append_step("test", "detail")
    assert any(s.get("action") == "test" for s in steps())


def test_multi_tab_plan():
    plan = plan_research("cats", ["https://a.com", "https://b.com"])
    assert plan["ok"] is True
    assert len(plan["tabs"]) == 2
    assert plan["auto_run"] is False
    merged = merge_findings()
    assert merged["ok"] is True


def test_download_confirm_types():
    out = check_download_safe("https://x.com/file.bin")
    assert out["ok"] is False
    assert out.get("needs_confirm") or "confirm" in (out.get("message") or "").lower() or "Unlisted" in (
        out.get("message") or ""
    )


def test_dom_snapshot_without_page():
    with patch("jarvis.browser_product.session.get_page", return_value=None):
        from jarvis.browser_dom_agent import get_page_snapshot

        snap = get_page_snapshot()
        assert snap["ok"] is False
