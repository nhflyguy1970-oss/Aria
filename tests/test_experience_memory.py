"""Experience memory — successes and failures."""

import pytest

from jarvis.experience_memory import (
    EXPERIENCE_NAMESPACE,
    experience_context_for_chat,
    parse_experience_remember,
    recall_experiences,
    record_experience,
    record_failure,
    record_success,
)
from jarvis.modules.memory import MemoryStore
from jarvis.trust_memory import trust_context_for_chat, trust_status


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_VECTOR_BACKEND", raising=False)
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: True)

    def _embed(text: str) -> list[float]:
        if not text:
            return []
        h = abs(hash(text))
        return [float((h >> i) & 0xFF) / 255.0 for i in range(0, 64, 8)]

    monkeypatch.setattr("jarvis.llm.embed_text", _embed)
    return MemoryStore(path=data_dir / "memory.json")


def test_record_failure_and_success(store):
    fail = record_failure(store, path="foo.py", error="AssertionError", task="fix foo")
    assert fail and fail["type"] == "failure"
    assert fail["namespace"] == EXPERIENCE_NAMESPACE
    ok = record_success(store, paths=["foo.py"], note="tests pass", task="fix foo")
    assert ok and ok["type"] == "success"
    assert fail["id"] != ok["id"]


def test_failure_then_success_distinct(store):
    record_failure(store, path="bar.py", error="TypeError", task="fix bar module")
    ok = record_success(store, paths=["bar.py"], note="tests pass", task="fix bar module")
    assert ok
    assert len(store.list_entries(entry_type="failure")) >= 1
    assert len(store.list_entries(entry_type="success")) >= 1


def test_parse_experience_remember():
    assert parse_experience_remember("remember that worked: using tabs") == ("success", "using tabs")
    assert parse_experience_remember("that failed: chmod missing") == ("failure", "chmod missing")


def test_recall_experiences_semantic(store):
    record_experience(
        store,
        outcome="failure",
        task="pytest unique task alpha",
        detail="import error in foo.py",
        module="coding",
    )
    hits = recall_experiences(store, "pytest unique task alpha")
    assert hits and hits[0]["type"] == "failure"


def test_experience_context_injected(store):
    record_experience(
        store,
        outcome="failure",
        task="debug unique foo.py",
        detail="NameError",
        module="coding",
    )
    ctx = experience_context_for_chat(store, "help me debug unique foo.py")
    assert "Past experiences" in ctx
    assert "NameError" in ctx


def test_trust_status_counts_experiences(store):
    record_success(store, task="image gen unique", detail="flux schnell worked")
    record_failure(store, error="OOM unique", task="sdxl unique")
    status = trust_status(store)
    assert status["successes"] >= 1
    assert status["failures"] >= 1


def test_trust_context_merges_experience(store):
    record_experience(
        store,
        outcome="success",
        task="coding_fix unique",
        detail="patch imports",
        module="tool",
    )
    ctx = trust_context_for_chat(store, "fix imports in my script")
    assert "Past experiences" in ctx or "Succeeded" in ctx
