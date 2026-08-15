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
    ("What is my favorite coffee?", "memory_about_user"),
    ("What do you know about me?", "memory_about_user"),
    ("What do you remember about me?", "memory_about_user"),
    ("Who are you?", "memory_about_user"),
    ("What's your name?", "memory_about_user"),
    ("Search memory for fly tying.", "memory_search"),
    # BUG-025: "remember" in a recall question must not store.
    ("What exact ARIA-FINAL-MEMORY marker did I ask you to remember?", "memory_about_user"),
    ("Can you remember what I told you about my project?", "memory_about_user"),
    ("Tell me what you remember about X.", "memory_about_user"),
    ("Remind me of the unique acceptance memory marker I just stored.", "memory_about_user"),
    ("What was the ARIA-FINAL-MEMORY marker? It starts with ARIA-FINAL-MEMORY-.", "memory_about_user"),
    ("Please remember ARIA-FINAL-MEMORY-UNIQUE-ZETA", "remember"),
]


@pytest.mark.parametrize("prompt,expected", CASES)
def test_resolve_memory_route_verbs(prompt, expected):
    resolved = resolve_memory_route(prompt)
    assert resolved is not None, prompt
    assert resolved["action"] == expected
    if expected == "remember":
        text = resolved["params"]["text"]
        assert text
        if "dark roast" in prompt:
            assert "dark roast" in text
        elif "Zeus" in prompt:
            assert "Zeus" in text
        elif "ARIA-FINAL-MEMORY" in prompt:
            assert "ARIA-FINAL-MEMORY" in text
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


def test_remember_strips_confirmational_tail():
    """BUG-008: store clean propositions without QA/confirm framing."""
    from jarvis.modules.memory_common import parse_remember

    content, etype, _ns = parse_remember(
        "Please remember for testing: my acceptance token is TOK-9. Confirm you stored it."
    )
    assert etype == "fact"
    assert content == "my acceptance token is TOK-9"
    assert "confirm" not in content.lower()
    assert "for testing" not in content.lower()

    resolved = resolve_memory_route(
        "Please remember for testing: my acceptance token is TOK-9. Confirm you stored it."
    )
    assert resolved is not None
    assert resolved["action"] == "remember"
    assert resolved["params"]["text"] == "my acceptance token is TOK-9"
