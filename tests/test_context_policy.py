"""Context assembly policy — lazy retrieval for simple vs complex prompts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.parametrize(
    "message",
    [
        "Hello",
        "Hi",
        "Good morning",
        "Thanks",
        "What is 2+2?",
        "What day is today?",
        "What time is it?",
        "Tell me a joke.",
    ],
)
def test_lightweight_chat_skips_heavy_sources(message: str) -> None:
    from jarvis.context.policy import context_needs, is_lightweight_chat

    assert is_lightweight_chat(message)
    needs = context_needs(message)
    assert needs.lightweight
    assert not needs.memory
    assert not needs.planning_tasks
    assert not needs.weather
    assert not needs.knowledge_topics
    assert not needs.documents
    assert not needs.web_search
    assert not needs.project_extras
    assert not needs.flytying
    assert not needs.relationships


def test_date_question_gets_local_clock_only() -> None:
    from jarvis.context.policy import context_needs

    needs = context_needs("What day is today?")
    assert needs.local_clock
    assert not needs.weather


def test_weather_narrow_path() -> None:
    from jarvis.context.policy import context_needs

    needs = context_needs("What's the weather today?")
    assert needs.weather
    assert not needs.documents
    assert not needs.knowledge_topics
    assert not needs.web_search
    assert not needs.project_extras


def test_schedule_narrow_path() -> None:
    from jarvis.context.policy import context_needs

    needs = context_needs("Schedule a meeting tomorrow.")
    assert needs.planning_tasks
    assert not needs.weather
    assert not needs.documents


def test_documents_path() -> None:
    from jarvis.context.policy import context_needs

    needs = context_needs("Summarize this PDF")
    assert needs.documents
    assert not needs.weather
    assert not needs.planning_tasks


def test_ordinary_chat_skips_memory_and_web() -> None:
    from jarvis.context.policy import context_needs
    from jarvis.web_search import should_auto_search

    msg = "Can you develop a resistance band exercise plan for a 56-year-old male?"
    needs = context_needs(msg)
    assert not needs.lightweight
    assert not needs.memory
    assert not needs.documents
    assert not needs.knowledge_topics
    assert not needs.web_search
    assert not should_auto_search(msg)


def test_bare_today_does_not_fetch_weather() -> None:
    from jarvis.context.policy import needs_weather
    from jarvis.behaviors.planning.engine import PlanningEngine

    assert not needs_weather("What day is today?")
    parts, _ = PlanningEngine.prepare_context(
        SimpleNamespace(journal=SimpleNamespace(format_open_tasks=lambda limit=8: "No open journal tasks.")),
        "What day is today?",
        include_weather=False,
        include_tasks=False,
    )
    assert parts == []


def test_build_context_prefix_hello_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.behaviors.conversation import ConversationEngine
    from jarvis.context.policy import last_inventory

    called = {"memory": 0, "planning": 0, "knowledge": 0}

    class MemBeh:
        def prepare_context(self, *a, **k):
            called["memory"] += 1
            return ["SHOULD NOT"], []

    class PlanBeh:
        def prepare_context(self, *a, **k):
            called["planning"] += 1
            return ["SHOULD NOT"], []

    class KnowBeh:
        def prepare_context(self, *a, **k):
            called["knowledge"] += 1
            return ["SHOULD NOT"], []

    monkeypatch.setattr("jarvis.behaviors.memory.get_memory_behavior", lambda: MemBeh())
    monkeypatch.setattr("jarvis.behaviors.planning.get_planning_behavior", lambda: PlanBeh())
    monkeypatch.setattr("jarvis.behaviors.knowledge.get_knowledge_behavior", lambda: KnowBeh())
    monkeypatch.setattr("jarvis.router.is_general_knowledge_question", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.router.is_meta_self_question", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.runtime_routing.is_runtime_routing_question", lambda *a, **k: False)

    eng = ConversationEngine(SimpleNamespace(session=SimpleNamespace()))
    prefix, _warnings, _citations = eng.build_context_prefix("Hello")
    assert "SHOULD NOT" not in prefix
    assert called == {"memory": 0, "planning": 0, "knowledge": 0}
    inv = last_inventory()
    assert inv.get("lightweight") is True
    assert inv["sources"]["memory"]["required"] is False
    assert inv["sources"]["planning"]["required"] is False
    assert inv["sources"]["knowledge"]["required"] is False


def test_build_context_prefix_warranty_calls_knowledge(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.behaviors.conversation import ConversationEngine

    class MemBeh:
        def prepare_context(self, *a, **k):
            return ["Memory: likes tea"], [{"source": "memory", "type": "preference"}]

    class KnowBeh:
        def prepare_context(self, *a, **k):
            assert k.get("include_documents") is True
            return ["Doc: warranty"], [{"id": "doc-1", "type": "document"}]

    class PlanBeh:
        def prepare_context(self, *a, **k):
            raise AssertionError("planning should not run for warranty")

    monkeypatch.setattr("jarvis.behaviors.memory.get_memory_behavior", lambda: MemBeh())
    monkeypatch.setattr("jarvis.behaviors.knowledge.get_knowledge_behavior", lambda: KnowBeh())
    monkeypatch.setattr("jarvis.behaviors.planning.get_planning_behavior", lambda: PlanBeh())
    monkeypatch.setattr("jarvis.router.is_general_knowledge_question", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.router.is_meta_self_question", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.runtime_routing.is_runtime_routing_question", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.resource_router.chat_busy_hint", lambda: None)

    eng = ConversationEngine(SimpleNamespace(session=SimpleNamespace(), memory=SimpleNamespace()))
    prefix, _warnings, citations = eng.build_context_prefix("What is my warranty?")
    assert "Doc: warranty" in prefix
    assert any(c.get("id") == "doc-1" for c in citations)
