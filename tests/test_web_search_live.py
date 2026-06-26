"""Live web search smoke test (needs network)."""

import pytest

from jarvis import web_search

pytestmark = pytest.mark.network


def test_search_returns_results():
    results = web_search.search("Python programming language", limit=3)
    assert len(results) >= 1
    assert results[0].get("title")
    assert results[0].get("url")


def test_html_fallback_parses():
    results = web_search._ddg_html_search("Jensen Huang NVIDIA", limit=3)
    assert len(results) >= 1
    assert any("nvidia" in (r.get("url") or "").lower() or "huang" in (r.get("title") or "").lower() for r in results)
