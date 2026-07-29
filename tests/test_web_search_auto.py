"""Auto web-search heuristics — restored coverage (was skipped stub)."""

from __future__ import annotations

import os

import pytest


def test_auto_search_enabled_env(monkeypatch):
    from jarvis import web_search

    monkeypatch.setenv("JARVIS_AUTO_WEB_SEARCH", "1")
    assert web_search.auto_search_enabled() is True
    monkeypatch.setenv("JARVIS_AUTO_WEB_SEARCH", "0")
    assert web_search.auto_search_enabled() is False
    monkeypatch.setenv("JARVIS_AUTO_WEB_SEARCH", "false")
    assert web_search.auto_search_enabled() is False


def test_should_auto_search_factual_questions(monkeypatch):
    from jarvis.web_search import should_auto_search

    monkeypatch.setattr("jarvis.runtime_routing.is_runtime_routing_question", lambda m: False)
    assert should_auto_search("Who is the president of France?")
    assert should_auto_search("What is the latest news today?")
    assert should_auto_search("How many moons does Jupiter have?")


def test_should_auto_search_skips_code_and_explicit_web(monkeypatch):
    from jarvis.web_search import should_auto_search

    monkeypatch.setattr("jarvis.runtime_routing.is_runtime_routing_question", lambda m: False)
    assert not should_auto_search("search the web for cats")
    assert not should_auto_search("fix this python function")
    assert not should_auto_search("remember my favorite color")
    assert not should_auto_search("hi")


def test_should_auto_search_skips_runtime(monkeypatch):
    from jarvis.web_search import should_auto_search

    monkeypatch.setattr("jarvis.runtime_routing.is_runtime_routing_question", lambda m: True)
    assert not should_auto_search("What model are you using right now?")
