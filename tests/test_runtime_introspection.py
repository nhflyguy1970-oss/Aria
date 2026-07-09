"""Tests for runtime introspection — self-knowledge without RAG or web search."""

from __future__ import annotations

from unittest.mock import patch


def test_runtime_introspection_detects_platform_mode_question():
    from jarvis.runtime_introspection import is_runtime_introspection_question

    assert is_runtime_introspection_question(
        "Am I running standalone or attached to AI Platform?"
    )
    assert is_runtime_introspection_question("Are you attached to AI Platform?")
    assert is_runtime_introspection_question("What are you running on?")
    assert is_runtime_introspection_question("What model are you using?")
    assert is_runtime_introspection_question("What services are running?")
    assert is_runtime_introspection_question("What is your health?")


def test_runtime_introspection_rejects_general_knowledge():
    from jarvis.runtime_introspection import is_runtime_introspection_question

    assert not is_runtime_introspection_question("What is a transformer neural network?")
    assert not is_runtime_introspection_question("Who invented PostgreSQL?")


def test_route_runtime_introspection_returns_action():
    from jarvis.runtime_introspection import route_runtime_introspection

    hit = route_runtime_introspection("Are you attached to AI Platform?")
    assert hit is not None
    assert hit["action"] in (
        "runtime_status",
        "runtime_mode",
        "runtime_platform",
    )


def test_classify_runtime_models_question():
    from jarvis.runtime_introspection import classify_runtime_action

    assert classify_runtime_action("What model are you using?") == "runtime_models"


def test_general_knowledge_excludes_runtime_questions():
    from jarvis.router import is_general_knowledge_question

    assert not is_general_knowledge_question("Am I running standalone or attached to AI Platform?")


@patch("jarvis.web_search.search")
def test_should_auto_search_skips_runtime_questions(mock_search):
    from jarvis.web_search import should_auto_search

    assert not should_auto_search("Are you attached to AI Platform?")
    mock_search.assert_not_called()


def test_execution_mode_returns_string():
    from jarvis.runtime_introspection import execution_mode

    mode = execution_mode()
    assert mode in ("standalone", "attached", "compatibility", "platform-authoritative")


def test_collect_runtime_status_shape():
    from jarvis.runtime_introspection import collect_runtime_status

    data = collect_runtime_status()
    assert data.get("ok") is True
    assert "execution_mode" in data
    assert "identity" in data
    assert "providers" in data


def test_runtime_action_result_has_message():
    from jarvis.runtime_introspection import runtime_action_result

    result = runtime_action_result("runtime_mode")
    assert result["ok"] is True
    assert "Execution mode" in result["message"]
    assert "data" in result


def test_router_quick_route_runtime_question():
    from jarvis.router import _quick_route
    from jarvis.session import SessionContext

    session = SessionContext()
    hit = _quick_route("Am I running standalone or attached to AI Platform?", None, session)
    assert hit is not None
    assert hit["action"].startswith("runtime_")
