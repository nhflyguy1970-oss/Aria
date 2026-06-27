"""Observation learning tests."""

import pytest

from jarvis.observation_learning import (
    OBSERVATION_NAMESPACE,
    OBSERVATION_TAG,
    extract_observation_notes,
    is_observe_log,
    is_observation_recall,
    observe_terminal,
    observe_text,
    parse_terminal_text,
)
from jarvis.modules.memory import MemoryStore


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("JARVIS_VECTOR_BACKEND", raising=False)
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [0.1, 0.2] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_parse_intents():
    assert is_observe_log("observe the jarvis log")
    assert is_observation_recall("what did you observe about pytest")
    assert "FAILED" in parse_terminal_text("observe terminal:\n```\nFAILED tests\n```")


def test_extract_notes(monkeypatch):
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: '{"notes": ["pytest failed on test_duration", "disk nearly full"]}',
    )
    notes = extract_observation_notes("ERROR disk 95%\nFAILED test_duration", source_type="terminal")
    assert len(notes) == 2


def test_observe_text_stores_notes(monkeypatch, store, data_dir):
    monkeypatch.setattr("jarvis.observation_learning.OBSERVATIONS_DIR", data_dir / "observations")
    monkeypatch.setattr("jarvis.observation_learning.REGISTRY_FILE", data_dir / "observation_learning.json")
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: '{"notes": ["Service restarted successfully on port 8765"]}',
    )

    result = observe_text(
        store,
        "INFO Uvicorn running on http://127.0.0.1:8765\nINFO Started server",
        source_type="log",
        title="jarvis.log",
    )
    assert result.ok
    assert len(result.notes) == 1

    entries = store.list_entries(entry_type="note", namespace=OBSERVATION_NAMESPACE)
    assert any(OBSERVATION_TAG in (e.get("tags") or []) for e in entries)


def test_observe_terminal(store, data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.observation_learning.OBSERVATIONS_DIR", data_dir / "observations")
    monkeypatch.setattr("jarvis.observation_learning.REGISTRY_FILE", data_dir / "observation_learning.json")
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: '{"notes": ["Build exited with code 1"]}',
    )
    result = observe_terminal(store, "$ make test\nmake: *** Error 1")
    assert result.ok
