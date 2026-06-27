"""Explicit teaching tests."""

import pytest

from jarvis.explicit_teaching import (
    TEACHING_NAMESPACE,
    apply_explicit_teaching,
    explicit_teaching_context_for_chat,
    explicit_teaching_system_block,
    infer_teaching_kind,
    list_teachings,
    parse_teach_message,
    parse_teach_recall_query,
    TeachIntent,
)
from jarvis.modules.memory import MemoryStore


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_GRAPH_BACKEND", raising=False)
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [0.1, 0.2] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_parse_teach_typed_and_bare():
    p = parse_teach_message("teach rule: always use bullet points")
    assert p and p.kind == "rule"
    p = parse_teach_message("teach ARIA that I prefer local Ollama models")
    assert p and p.kind == "preference"
    assert "Ollama" in p.content


def test_infer_kind():
    assert infer_teaching_kind("First pull the model, then run ollama serve") == "procedure"
    assert infer_teaching_kind("Never suggest cloud APIs") == "rule"


def test_apply_explicit_teaching_fact(store):
    result = apply_explicit_teaching(store, TeachIntent(kind="fact", content="Jarvis lives at /media/jeff/AI/jarvis"))
    assert result.entry["type"] == "teaching"
    assert result.entry["namespace"] == TEACHING_NAMESPACE
    assert EXPLICIT_TEACH_TAG in result.entry["tags"] if (EXPLICIT_TEACH_TAG := "explicit-teach") else True
    assert len(list_teachings(store)) >= 1


def test_apply_explicit_teaching_rule(store):
    result = apply_explicit_teaching(store, TeachIntent(kind="rule", content="Keep answers concise"))
    assert result.kind == "rule"
    assert store.list_entries(entry_type="strategy")


def test_teach_recall_query():
    assert "tabs" in parse_teach_recall_query("what did I teach you about tabs")


def test_system_and_chat_context(store):
    apply_explicit_teaching(store, TeachIntent(kind="rule", content="Never use cloud APIs"))
    block = explicit_teaching_system_block(store)
    assert "Explicit teachings" in block
    ctx = explicit_teaching_context_for_chat(store, "should I use a cloud API?")
    assert "cloud" in ctx.lower() or "Explicit" in ctx or "teachings" in ctx.lower()
