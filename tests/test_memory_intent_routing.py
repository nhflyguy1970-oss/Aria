"""Regression: imperative memory commands must not collapse to memory dump."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.nlu.mapping import resolve_memory_route
from jarvis.session import SessionContext

CASES = [
    ("Remember that my favorite coffee is dark roast.", "remember"),
    ("Remember my dog's name is Zeus.", "remember"),
    ("Forget my coffee preference.", "memory_forget"),
    ("Update my favorite coffee.", "memory_correct"),
    ("What is my favorite coffee?", "memory_search"),
    ("What do you know about me?", "memory_about_user"),
    ("What do you remember about me?", "memory_about_user"),
    ("Search memory for fly tying.", "memory_search"),
]


@pytest.mark.parametrize("prompt,expected", CASES)
def test_resolve_memory_route_verbs(prompt, expected):
    resolved = resolve_memory_route(prompt)
    assert resolved is not None, prompt
    assert resolved["action"] == expected
    if expected == "remember":
        assert "dark roast" in resolved["params"]["text"] or "Zeus" in resolved["params"]["text"]
    if expected == "memory_forget":
        assert "coffee" in resolved["params"]["query"].lower()
    if expected == "memory_search" and "fly tying" in prompt.lower():
        assert "fly tying" in resolved["params"]["query"].lower()


@pytest.mark.parametrize("prompt,expected", CASES)
def test_router_memory_verbs(prompt, expected):
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route(prompt, SessionContext(), None)
        assert intent.get("action") == expected, (prompt, intent)


def test_remember_does_not_dump():
    from jarvis.router import route

    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        intent = route(
            "Remember that my favorite coffee is dark roast.",
            SessionContext(),
            None,
        )
        assert intent["action"] == "remember"
        assert intent["action"] != "recall"
        assert "dark roast" in (intent.get("params") or {}).get("text", "")


def test_gpu_what_is_my_stays_runtime():
    """'What is my GPU?' must not be captured by memory fact recall."""
    assert resolve_memory_route("What is my GPU?") is None
    assert resolve_memory_route("What is my current GPU?") is None
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route("What is my GPU?", SessionContext(), None)
        action = intent.get("action") or ""
        assert action.startswith("runtime_") or action == "status_summary", intent


def test_nlu_mapping_remember_not_recall():
    from jarvis.nlu.mapping import nlu_to_router_intent
    from jarvis.nlu.types import (
        GrammarAnalysis,
        MorphologyAnalysis,
        NLUResult,
        SemanticClassification,
        SyntaxAnalysis,
    )

    result = NLUResult(
        prompt="Remember that my favorite coffee is dark roast.",
        grammar=GrammarAnalysis(mood="instruction"),
        morphology=MorphologyAnalysis(),
        syntax=SyntaxAnalysis(verb="remember"),
        semantic=SemanticClassification(intent="memory", confidence=0.95),
    )
    intent = nlu_to_router_intent(result)
    assert intent is not None
    assert intent["action"] == "remember"
