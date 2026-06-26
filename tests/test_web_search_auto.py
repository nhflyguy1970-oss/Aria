"""Tests for auto web search heuristics."""

from jarvis import web_search


def test_should_auto_search_questions():
    assert web_search.should_auto_search("Who is the CEO of Nvidia?")
    assert web_search.should_auto_search("What is the latest news about Linux?")


def test_should_not_auto_search_coding():
    assert not web_search.should_auto_search("fix coding/main.py")
    assert not web_search.should_auto_search("search the web for cats")


def test_format_results_for_llm():
    hits = [{"title": "A", "url": "https://a.test", "snippet": "hello"}]
    text = web_search.format_results_for_llm(hits)
    assert "[1]" in text
    assert "https://a.test" in text
