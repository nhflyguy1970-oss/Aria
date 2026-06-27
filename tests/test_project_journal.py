"""Project journal and journal learning tests."""

from pathlib import Path

import pytest

from jarvis.journal_learning import (
    JOURNAL_LEARN_TAG,
    extract_journal_learnings,
    learn_from_project_journal,
)
from jarvis.modules.memory import MemoryStore
from jarvis.project_journal import ProjectJournal, list_projects, resolve_project


@pytest.fixture
def journal_env(data_dir, monkeypatch):
    projects = data_dir / "journal" / "projects"
    projects.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.project_journal.PROJECTS_DIR", projects)
    monkeypatch.setattr("jarvis.project_journal.INDEX_FILE", projects / "index.json")
    return projects


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("JARVIS_VECTOR_BACKEND", raising=False)
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [0.1, 0.2] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_resolve_project():
    assert resolve_project("log to jarvis project journal: test") == "jarvis"
    assert resolve_project("learn from aria project journal") == "aria"


def test_project_journal_daily(journal_env):
    j = ProjectJournal("jarvis")
    j.ensure(title="Jarvis")
    b = j.daily_add("Shipped memory graph integration")
    assert b["content"]
    assert "Shipped" in j.format_daily()
    assert list_projects()


def test_learn_from_project_journal(monkeypatch, store, journal_env):
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: '{"facts": ["Jarvis memory graph uses Memgraph on port 7687."]}',
    )
    j = ProjectJournal("jarvis")
    j.daily_add("Memgraph running on 7687 for relationship graph")
    result = learn_from_project_journal(store, "jarvis", namespace="jarvis")
    assert result["ok"]
    entries = store.list_entries(namespace="jarvis")
    assert any(JOURNAL_LEARN_TAG in (e.get("tags") or []) for e in entries)


def test_extract_journal_learnings(monkeypatch):
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: '{"facts": ["Decided to use Chroma for vectors."]}',
    )
    facts = extract_journal_learnings("Today we picked ChromaDB.", project="jarvis", day="2026-06-17")
    assert len(facts) == 1
