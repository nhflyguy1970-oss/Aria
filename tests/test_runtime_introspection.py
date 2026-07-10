"""Tests for runtime introspection — self-knowledge without RAG or web search."""

from __future__ import annotations

from unittest.mock import patch

RUNTIME_PROMPTS = [
    "Am I running standalone or attached to AI Platform?",
    "What model are you using?",
    "What services are running?",
    "Am I attached to AI Platform?",
    "What GPU are you using?",
    "What databases are connected?",
]

RUNTIME_COMMANDS = [
    ("status", "status_summary"),
    ("health", "runtime_health"),
    ("services", "runtime_services"),
    ("models", "runtime_models"),
    ("memory", "runtime_providers"),
    ("providers", "runtime_providers"),
    ("gpu", "runtime_gpu"),
    ("jobs", "runtime_jobs"),
    ("runtime_status", "runtime_status"),
    ("runtime_mode", "runtime_mode"),
    ("runtime_health", "runtime_health"),
    ("runtime_platform", "runtime_platform"),
    ("runtime_services", "runtime_services"),
    ("runtime_models", "runtime_models"),
    ("runtime_gpu", "runtime_gpu"),
    ("runtime_jobs", "runtime_jobs"),
]


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
    assert classify_runtime_action("runtime_mode") == "runtime_mode"
    assert classify_runtime_action("runtime_gpu") == "runtime_gpu"


def test_general_knowledge_excludes_runtime_questions():
    from jarvis.router import is_general_knowledge_question

    assert not is_general_knowledge_question("Am I running standalone or attached to AI Platform?")


@patch("jarvis.web_search.search")
def test_should_auto_search_skips_runtime_questions(mock_search):
    from jarvis.web_search import should_auto_search

    for prompt in RUNTIME_PROMPTS:
        assert not should_auto_search(prompt), f"should_auto_search must be false: {prompt}"
    mock_search.assert_not_called()


def test_runtime_prompts_never_route_to_web_search():
    from jarvis.router import route
    from jarvis.session import SessionContext

    session = SessionContext()
    for prompt in RUNTIME_PROMPTS:
        intent = route(prompt, session, None)
        action = intent.get("action")
        assert action != "web_search", f"web_search for: {prompt}"
        assert action != "chat", f"chat fallback for: {prompt}"
        assert action.startswith("runtime_") or action == "status_summary", (
            f"unexpected action {action} for: {prompt}"
        )


def test_runtime_commands_never_route_to_web_search():
    from jarvis.router import route
    from jarvis.session import SessionContext

    session = SessionContext()
    for cmd, expected in RUNTIME_COMMANDS:
        intent = route(cmd, session, None)
        action = intent.get("action")
        assert action != "web_search", f"web_search for command: {cmd}"
        assert action == expected, f"{cmd} -> {action}, expected {expected}"


def test_router_table_does_not_override_runtime_services_question():
    from jarvis.router import _quick_route
    from jarvis.session import SessionContext

    hit = _quick_route("What services are running?", None, SessionContext())
    assert hit is not None
    assert hit["action"] == "runtime_services"
    assert hit["action"] != "capabilities"


def test_execution_mode_returns_string():
    from jarvis.runtime_introspection import execution_mode

    mode = execution_mode()
    assert mode in (
        "standalone",
        "attached",
        "compatibility",
        "platform-authoritative",
        "platform-attached",
        "disconnected",
    )


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_collect_runtime_status_shape(mock_get_client):
    from unittest.mock import MagicMock

    client = MagicMock()
    client.snapshot.return_value = {
        "ok": True,
        "ts": "2026-07-09T12:00:00",
        "overview": {"execution_mode": "platform-attached"},
        "services": [],
        "databases": [],
        "applications": [],
        "inference": {},
        "hardware": {},
        "jobs": {},
        "recovery": {},
    }
    mock_get_client.return_value = client

    from jarvis.runtime_introspection import collect_runtime_status

    data = collect_runtime_status()
    assert data.get("ok") is True
    assert data.get("source") == "mission_control"
    assert "execution_mode" in data
    assert "identity" in data


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_runtime_action_result_has_message(mock_get_client):
    from unittest.mock import MagicMock

    client = MagicMock()
    client.snapshot.return_value = {
        "ok": True,
        "overview": {"execution_mode": "platform-attached", "phase": {"phase": "production"}},
        "applications": [{"id": "aria", "running": True, "healthy": True}],
    }
    mock_get_client.return_value = client

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


@patch("jarvis.web_search.search")
def test_knowledge_engine_skips_web_search_for_runtime(mock_search):
    from jarvis.behaviors.knowledge.engine import KnowledgeEngine
    from jarvis.behaviors.knowledge.context import KnowledgeContext

    class _Mem:
        pass

    class _Session:
        last_file = None
        recent_files = []

    class _Asst:
        session = _Session()
        memory = _Mem()

    ctx = KnowledgeContext.from_orchestrator(_Asst())
    for prompt in RUNTIME_PROMPTS:
        parts, _citations, _warnings = KnowledgeEngine.prepare_context(
            ctx, prompt, general=False, skip_project_context=True
        )
        joined = "\n".join(parts)
        assert "Web search snippets" not in joined, f"web search in context for: {prompt}"
    mock_search.assert_not_called()
