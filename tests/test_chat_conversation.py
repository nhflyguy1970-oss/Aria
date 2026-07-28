"""Chat conversation grounding — Memory/Documents citations, no auto-writes."""

from __future__ import annotations

from types import SimpleNamespace


def test_build_context_prefix_returns_citations(monkeypatch):
    from jarvis.behaviors.conversation import ConversationEngine

    mem_cites = [{"source": "memory", "type": "preference", "content": "likes tea", "date": "2026-01-01"}]
    doc_cites = [{"id": "doc-1", "source": "/tmp/a.md", "title": "a.md", "type": "document"}]

    class MemBeh:
        def prepare_context(self, *a, **k):
            return ["Memory: likes tea"], mem_cites

    class KnowBeh:
        def prepare_context(self, *a, **k):
            return ["Doc: warranty"], doc_cites

    class PlanBeh:
        def prepare_context(self, *a, **k):
            return [], []

    monkeypatch.setattr("jarvis.behaviors.memory.get_memory_behavior", lambda: MemBeh())
    monkeypatch.setattr("jarvis.behaviors.knowledge.get_knowledge_behavior", lambda: KnowBeh())
    monkeypatch.setattr("jarvis.behaviors.planning.get_planning_behavior", lambda: PlanBeh())
    monkeypatch.setattr("jarvis.router.is_general_knowledge_question", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.router.is_meta_self_question", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.runtime_routing.is_runtime_routing_question", lambda *a, **k: False)

    assistant = SimpleNamespace(session=SimpleNamespace())
    eng = ConversationEngine(assistant)
    prefix, warnings, citations = eng.build_context_prefix("What is my warranty?")
    assert prefix
    assert any(c.get("source") == "memory" or c.get("type") == "preference" for c in citations)
    assert any(c.get("id") == "doc-1" or "document" in str(c.get("type", "")).lower() for c in citations)


def test_memory_citations_do_not_auto_write(monkeypatch):
    """Chat citation plumbing must not imply Memory writes."""
    from jarvis.behaviors.conversation import ConversationEngine

    cites = [{"source": "memory", "type": "fact", "content": "home lab", "date": "2026-07-01"}]
    monkeypatch.setattr(
        ConversationEngine,
        "build_context_prefix",
        lambda self, msg, **k: ("ctx", [], cites),
    )
    wrote = {"n": 0}
    memory = SimpleNamespace(add=lambda *a, **k: wrote.__setitem__("n", wrote["n"] + 1))
    assistant = SimpleNamespace(memory=memory, session=SimpleNamespace())
    eng = ConversationEngine(assistant)
    prefix, warnings, citations = eng.build_context_prefix("remember?")
    assert citations == cites
    assert wrote["n"] == 0
