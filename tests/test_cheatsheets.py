"""Cheatsheets stored in memory."""

import pytest
from jarvis.cheatsheets import (
    CHEATSHEET_NAMESPACE,
    find_by_key,
    list_cheatsheets,
    reset_cheatsheet,
    seed_cheatsheets,
    upsert_cheatsheet,
)
from jarvis.modules.memory import MemoryStore
from jarvis.router import route
from jarvis.session import SessionContext


@pytest.fixture
def session():
    return SessionContext()


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_seed_cheatsheets_idempotent(store):
    first = seed_cheatsheets(store)
    assert "memory" in first
    second = seed_cheatsheets(store)
    assert second == []
    assert len(list_cheatsheets(store)) >= 8


def test_cheatsheet_namespace_and_key(store):
    seed_cheatsheets(store, keys=["memory"])
    entry = find_by_key(store, "memory")
    assert entry is not None
    assert entry["namespace"] == CHEATSHEET_NAMESPACE
    assert "key:memory" in entry.get("tags", [])


def test_upsert_and_reset(store):
    seed_cheatsheets(store, keys=["coding"])
    upsert_cheatsheet(store, "coding", "# Custom\n\nMy notes.")
    assert "My notes" in find_by_key(store, "coding")["content"]
    reset_cheatsheet(store, "coding")
    assert "Custom" not in find_by_key(store, "coding")["content"]


def test_cheatsheet_show_route(session):
    intent = route("memory cheatsheet", session)
    assert intent["action"] == "cheatsheet_show"
    assert intent["params"].get("key") == "memory"


def test_cheatsheet_list_route(session):
    intent = route("list cheatsheets", session)
    assert intent["action"] == "cheatsheet_list"


def test_cheatsheet_handler(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0])
    result = assistant.process("memory cheatsheet")
    assert result["ok"] is True
    assert "Quick Reference" in result["message"] or "cheatsheet" in result["message"].lower()
