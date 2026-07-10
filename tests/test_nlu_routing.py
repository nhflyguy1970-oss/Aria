"""NLU routing validation — meaning-based routing, not keyword tables."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.nlu.mapping import apply_intent_guards, infer_intent_from_structure, nlu_to_router_intent
from jarvis.nlu.pipeline import analyze_prompt
from jarvis.nlu.types import GrammarAnalysis, MorphologyAnalysis, NLUResult, SemanticClassification, SyntaxAnalysis
from jarvis.routing_inspector import classify_route
from jarvis.session import SessionContext

VALIDATION_CASES = [
    ("What GPU am I using?", "runtime", "runtime_gpu"),
    ("What is a GPU?", "knowledge", "chat"),
    ("Show Docker Compose documentation.", "reference", "reference_search"),
    ("Explain Docker Compose.", "knowledge", "chat"),
    ("How do I configure Docker Compose?", "reference", "reference_search"),
    ("Search my memory for Docker.", "memory", "memory_search"),
    ("Search the web for Docker Compose.", "web_search", "web_search"),
]


def _result_for(prompt: str) -> NLUResult:
    with patch("jarvis.nlu.semantic.classify_semantic", return_value=None):
        return analyze_prompt(prompt, SessionContext())


@pytest.mark.parametrize("prompt,expected_intent,expected_action", VALIDATION_CASES)
def test_structure_routes_by_meaning(prompt, expected_intent, expected_action):
    result = _result_for(prompt)
    assert apply_intent_guards(result) == expected_intent
    intent = nlu_to_router_intent(result)
    assert intent is not None
    assert intent["action"] == expected_action
    assert intent.get("router") == "nlu" or intent.get("route_reason") == "nlu_semantic"


@pytest.mark.parametrize("prompt,expected_intent,expected_action", VALIDATION_CASES)
def test_router_uses_nlu_primary(prompt, expected_intent, expected_action):
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route(prompt, SessionContext(), None)
        assert intent.get("action") == expected_action
        if expected_intent == "runtime":
            assert classify_route(intent.get("action")) == "Runtime"
        elif expected_intent == "reference":
            assert classify_route(intent.get("action")) == "Reference"


def test_reference_never_runtime_client():
    result = _result_for("Show Docker Compose documentation.")
    intent = nlu_to_router_intent(result)
    assert intent is not None
    assert intent.get("route_handler") == "ReferenceEngine"
    assert classify_route(intent["action"]) == "Reference"


def test_runtime_never_web_search():
    with patch("jarvis.web_search.search") as mock_search:
        with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
            mock_client.return_value = MagicMock()
            from jarvis.router import route

            intent = route("What GPU am I using?", SessionContext(), None)
            assert intent.get("action") != "web_search"
            mock_search.assert_not_called()


def test_infer_intent_from_structure_gpu():
    result = NLUResult(
        prompt="What GPU am I using?",
        grammar=GrammarAnalysis(sentence_type="interrogative", question_type="what"),
        morphology=MorphologyAnalysis(),
        syntax=SyntaxAnalysis(subject="i", verb="using", object="gpu"),
        semantic=SemanticClassification(),
    )
    assert infer_intent_from_structure(result) == "runtime"
