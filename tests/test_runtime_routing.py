"""Regression tests — runtime prompts must never reach web search."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

RUNTIME_KEYWORD_PROMPTS = [
    "Status",
    "What is my GPU?",
    "How much VRAM is free?",
    "CPU load?",
    "What models are loaded?",
    "Is ollama running?",
    "postgres status",
    "redis connected?",
    "What services are running?",
    "platform health",
    "mission control status",
    "show hardware",
    "active jobs",
    "memory provider",
    "knowledge provider",
    "mongodb status",
    "qdrant health",
    "litellm status",
    "grafana up?",
    "prometheus running?",
    "n8n status",
]


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_runtime_keyword_prompts_never_route_web_search(mock_get_client):
    client = MagicMock()
    client.snapshot.return_value = {
        "ok": True,
        "overview": {"execution_mode": "platform-attached"},
        "services": [],
        "applications": [],
        "inference": {},
        "hardware": {},
        "jobs": {},
        "recovery": {},
    }
    mock_get_client.return_value = client

    from jarvis.router import route
    from jarvis.session import SessionContext

    session = SessionContext()
    for prompt in RUNTIME_KEYWORD_PROMPTS:
        intent = route(prompt, session, None)
        assert intent.get("action") != "web_search", prompt
        assert intent.get("action") != "chat", prompt
        action = intent.get("action")
        assert action.startswith("runtime_") or action == "status_summary", (
            f"{prompt} -> {action}"
        )
        trace = intent.get("route_trace") or {}
        assert trace.get("route") == "Runtime" or action.startswith("runtime_"), prompt


@patch("jarvis.web_search.search")
def test_general_knowledge_gpu_prompt_routes_runtime_not_web_search(mock_search):
    from jarvis.router import is_general_knowledge_question, route
    from jarvis.session import SessionContext

    prompt = "What GPU are you using?"
    assert not is_general_knowledge_question(prompt)
    intent = route(prompt, SessionContext(), None)
    assert intent.get("action") != "web_search"
    mock_search.assert_not_called()


@patch("jarvis.web_search.search")
def test_should_auto_search_false_for_runtime_keywords(mock_search):
    from jarvis.web_search import should_auto_search

    for prompt in RUNTIME_KEYWORD_PROMPTS:
        assert not should_auto_search(prompt), prompt
    mock_search.assert_not_called()


@patch("jarvis.web_search.search")
def test_finalize_intent_blocks_web_search_for_runtime(mock_search):
    from jarvis.router import _finalize_intent
    from jarvis.session import SessionContext

    session = SessionContext()
    intent = {"action": "web_search", "params": {"query": "gpu vram status"}}
    out = _finalize_intent(intent, "What is my GPU and VRAM?", session)
    assert out.get("action") != "web_search"
    assert out.get("action", "").startswith("runtime_") or out.get("action") == "status_summary"
    mock_search.assert_not_called()


def test_runtime_routing_trace_metadata():
    from jarvis.runtime_routing import route_runtime_priority

    hit = route_runtime_priority("postgres status")
    assert hit is not None
    assert hit.get("route_handler") == "RuntimeClient"
    assert hit.get("action") == "runtime_services"


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_router_logs_route_trace(mock_get_client):
    client = MagicMock()
    client.snapshot.return_value = {
        "ok": True,
        "overview": {"execution_mode": "platform-attached"},
        "services": [{"id": "ollama", "running": True}],
        "applications": [],
        "inference": {"current_model": "llama3"},
        "hardware": {"gpu_name": "RTX"},
        "jobs": {},
        "recovery": {},
    }
    mock_get_client.return_value = client

    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("What model are you using?", SessionContext(), None)
    trace = intent.get("route_trace") or {}
    assert trace.get("intent", "").startswith("runtime_") or trace.get("intent") == "status_summary"
    assert trace.get("handler") == "RuntimeClient"
    assert trace.get("prompt")


@patch("jarvis.web_search.search")
@patch("jarvis.runtime_introspection.get_runtime_client")
def test_knowledge_engine_skips_web_for_runtime_keywords(mock_get_client, mock_search):
    from jarvis.behaviors.knowledge.engine import KnowledgeEngine
    from jarvis.behaviors.knowledge.context import KnowledgeContext

    client = MagicMock()
    mock_get_client.return_value = client

    class _Mem:
        pass

    class _Session:
        last_file = None
        recent_files = []

    class _Asst:
        session = _Session()
        memory = _Mem()

    ctx = KnowledgeContext.from_orchestrator(_Asst())
    parts, _citations, _warnings = KnowledgeEngine.prepare_context(
        ctx, "What is my GPU?", general=False, skip_project_context=True
    )
    joined = "\n".join(parts)
    assert "Web search snippets" not in joined
