"""Sticky vision / document context must not swallow unrelated questions.

Both rules live in router._follow_up_route, which runs before NLU, _quick_route
and the LLM router, and hard-routes. Before the repair they triggered on any
broad question prefix, or on any short question ending in "?" (vision), or on a
bare question word anywhere with no length bound at all (document) — so
"What is 7 plus 7?", "Who wrote Hamlet?" and "what is my GPU?" were silently
answered from the previous image or document.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.router import _follow_up_route, route
from jarvis.session import SessionContext

DOC_ACTIONS = {"document_query", "document_summarize"}


def vision_session() -> SessionContext:
    s = SessionContext()
    s.last_image = "/tmp/prev.png"
    s.last_module = "vision"
    return s


def document_session() -> SessionContext:
    s = SessionContext()
    s.last_document_path = "/tmp/prev.pdf"
    s.last_module = "document"
    return s


def _action(message: str, session: SessionContext) -> str | None:
    return (_follow_up_route(message, session) or {}).get("action")


# --- vision: genuine follow-ups still route to the image -------------------


@pytest.mark.parametrize(
    "message",
    [
        "What color is this?",
        "Can you read this?",
        "What am I looking at?",
        "What is this?",
        "In this picture, what is the object?",
        "What are the objects in this picture?",
        "Based on the image, what is this?",
        "What does this image show?",
        "What's this?",
        "What text does it show?",
    ],
)
def test_vision_follow_up_still_routes_to_image(message: str) -> None:
    assert _action(message, vision_session()) == "analyze_image", message


def test_bare_deictic_question_stays_vision() -> None:
    """Product decision: "What is this?" after an image is a vision follow-up."""
    assert _action("What is this?", vision_session()) == "analyze_image"


# --- vision: unrelated questions must escape -------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "What is 7 plus 7? Just the number.",
        "What time is it?",
        "Who wrote Hamlet?",
        "Why?",
        "what is my GPU?",
        "How do I restart the server?",
        "What is the capital of France?",
        "What are the benefits of Python?",
        "What is 100 divided by 4?",
        "Why is the sky blue?",
        "What is 2 times 8?",
    ],
)
def test_unrelated_question_escapes_sticky_vision(message: str) -> None:
    assert _action(message, vision_session()) != "analyze_image", message


def test_length_no_longer_decides_whether_a_question_is_visual() -> None:
    """The old rule keyed on len(message) < 240; length must not be the test."""
    short = "Who wrote Hamlet?"
    padded = short + " " + "x" * 300
    assert _action(short, vision_session()) != "analyze_image"
    assert _action(padded, vision_session()) != "analyze_image"
    # A genuine follow-up is visual regardless of how long it is.
    long_visual = "Can you read this? " + "Please be thorough. " * 20
    assert _action(long_visual, vision_session()) == "analyze_image"


# --- document: genuine follow-ups still route to the document --------------


@pytest.mark.parametrize(
    "message",
    [
        "What does the warranty cover?",
        "When does it expire?",
        "What is the coverage?",
        "Find the termination clause.",
        "Is there a section about returns?",
        "What does it say about liability?",
        "What's on page 3?",
        "What is the deductible?",
        "What does the document say?",
        "Does that clause apply to me?",
        "What are the terms and conditions?",
    ],
)
def test_document_follow_up_still_routes_to_document(message: str) -> None:
    assert _action(message, document_session()) in DOC_ACTIONS, message


def test_explicit_document_reference_routes_to_document() -> None:
    assert _action("What does the contract say?", document_session()) in DOC_ACTIONS


# --- document: unrelated questions must escape -----------------------------


@pytest.mark.parametrize(
    "message",
    [
        "What is 7 plus 7?",
        "What time is it?",
        "Who wrote Hamlet?",
        "Why?",
        "How do I restart the server?",
        "what is my GPU?",
        "What is the capital of France?",
        "Why is the sky blue?",
    ],
)
def test_unrelated_question_escapes_sticky_document(message: str) -> None:
    assert _action(message, document_session()) not in DOC_ACTIONS, message


# --- precedence: sticky context must not override a strong intent ----------


@pytest.fixture
def _no_runtime_client():
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock:
        mock.return_value = MagicMock()
        yield


@pytest.mark.parametrize(
    "message,expected",
    [("what is my GPU?", "runtime_gpu"), ("search the web for docker", "web_search")],
)
def test_sticky_vision_does_not_override_strong_intent(
    message: str, expected: str, _no_runtime_client
) -> None:
    assert route(message, vision_session(), None).get("action") == expected


@pytest.mark.parametrize(
    "message,expected",
    [("what is my GPU?", "runtime_gpu"), ("search the web for docker", "web_search")],
)
def test_sticky_document_does_not_override_strong_intent(
    message: str, expected: str, _no_runtime_client
) -> None:
    assert route(message, document_session(), None).get("action") == expected


def test_sticky_vision_still_wins_for_a_real_follow_up(_no_runtime_client) -> None:
    intent = route("What is this?", vision_session(), None)
    assert intent.get("action") == "analyze_image"
    assert intent.get("params", {}).get("path") == "/tmp/prev.png"


def test_unrelated_question_reaches_normal_routing_under_both_contexts(
    _no_runtime_client,
) -> None:
    """Neither last_image nor last_document_path may capture a generic question."""
    for session in (vision_session(), document_session()):
        intent = route("What is 7 plus 7? Just the number.", session, None)
        assert intent.get("action") not in ({"analyze_image"} | DOC_ACTIONS), intent


def test_stale_context_alone_does_not_make_a_question_sticky() -> None:
    """last_image / last_document_path present but the question is unrelated."""
    assert _action("Who wrote Hamlet?", vision_session()) is None
    assert _action("Who wrote Hamlet?", document_session()) is None


def test_sticky_vision_does_not_override_confident_nlu(
    monkeypatch, _no_runtime_client
) -> None:
    """Follow-up runs first, but an unrelated question must still reach NLU."""
    nlu_calls: list[str] = []

    def _nlu(message, session, attachment=None):
        nlu_calls.append(message)
        return {
            "action": "web_search",
            "params": {"query": message},
            "thinking": "nlu",
            "confidence": 0.94,
        }

    monkeypatch.setattr("jarvis.nlu.pipeline.nlu_enabled", lambda: True)
    monkeypatch.setattr("jarvis.nlu.pipeline.route_via_nlu", _nlu)
    intent = route("Who wrote Hamlet?", vision_session(), None)
    assert intent.get("action") == "web_search"
    assert nlu_calls == ["Who wrote Hamlet?"]


def test_non_vision_action_does_not_mutate_sticky_vision_routing(
    _no_runtime_client,
) -> None:
    """A successful non-vision route must not change later vision/non-vision results."""
    session = vision_session()
    gpu = route("what is my GPU?", session, None)
    assert gpu.get("action") == "runtime_gpu"
    assert session.last_image == "/tmp/prev.png"
    assert session.last_module == "vision"
    assert route("What is this?", session, None).get("action") == "analyze_image"
    assert (
        route("What is 7 plus 7? Just the number.", session, None).get("action")
        != "analyze_image"
    )


def test_sticky_document_does_not_override_confident_nlu(
    monkeypatch, _no_runtime_client
) -> None:
    def _nlu(message, session, attachment=None):
        return {
            "action": "web_search",
            "params": {"query": message},
            "thinking": "nlu",
            "confidence": 0.94,
        }

    monkeypatch.setattr("jarvis.nlu.pipeline.nlu_enabled", lambda: True)
    monkeypatch.setattr("jarvis.nlu.pipeline.route_via_nlu", _nlu)
    intent = route("Who wrote Hamlet?", document_session(), None)
    assert intent.get("action") == "web_search"


def test_vision_prefix_alone_is_not_visual() -> None:
    """Removing only the 240-char clause is not enough; prefixes must not suffice."""
    assert _action("What color is the sky?", vision_session()) != "analyze_image"
    assert _action("Can you see why the server failed?", vision_session()) != "analyze_image"

