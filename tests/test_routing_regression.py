"""Regression tests — route families must land on expected handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from jarvis.routing_inspector import classify_route, handler_for_action
from jarvis.session import SessionContext


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_search_prompts_route_to_web_search(mock_get_client):
    mock_get_client.return_value = MagicMock()

    from jarvis.router import route

    intent = route("search the web for latest Python release", SessionContext(), None)
    action = intent.get("action")
    assert action == "web_search"
    assert classify_route(action) == "Search"
    assert handler_for_action(action) == "WebSearch"


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_coding_prompts_route_to_coding_handlers(mock_get_client):
    mock_get_client.return_value = MagicMock()

    from jarvis.router import route

    intent = route("fix errors in main.py", SessionContext(), None)
    action = intent.get("action")
    assert action == "coding_fix"
    assert classify_route(action) == "Coding"
    assert handler_for_action(action) == "EngineeringEngine"


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_memory_prompts_route_to_memory_handlers(mock_get_client):
    mock_get_client.return_value = MagicMock()

    from jarvis.router import route

    intent = route("search my memory for vacation plans", SessionContext(), None)
    action = intent.get("action")
    assert action == "memory_search"
    assert classify_route(action) == "Memory"
    assert handler_for_action(action) == "MemoryStore"


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_knowledge_prompts_route_to_knowledge_handlers(mock_get_client):
    mock_get_client.return_value = MagicMock()

    from jarvis.router import route

    intent = route("learn about quantum computing", SessionContext(), None)
    action = intent.get("action")
    assert action == "learn_about"
    assert classify_route(action) == "Knowledge"
    assert handler_for_action(action) == "KnowledgeEngine"


@patch("jarvis.web_search.search")
@patch("jarvis.runtime_introspection.get_runtime_client")
def test_runtime_prompts_never_reach_web_search(mock_get_client, mock_search):
    mock_get_client.return_value = MagicMock()

    from jarvis.router import route

    intent = route("What GPU are you using?", SessionContext(), None)
    assert intent.get("action") != "web_search"
    assert classify_route(intent.get("action")) == "Runtime"
    mock_search.assert_not_called()
