"""SQLite memory backend and embedding sidecar tests."""

import pytest

from jarvis.modules.memory import JsonMemoryStore, MemoryStore, create_memory_store
from jarvis.modules.memory_embeddings import EmbeddingSidecar
from jarvis.modules.memory_sqlite import SqliteMemoryStore


@pytest.fixture
def sqlite_store(data_dir, monkeypatch):
    # Legacy vault unit tests — not ACM PRIMARY projection
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    db = data_dir / "mem.db"
    vec = data_dir / "mem_vectors.db"
    return SqliteMemoryStore(path=db, embeddings=EmbeddingSidecar(vec))


def test_sqlite_add_search_and_sidecar(sqlite_store):
    sqlite_store.add("fact", "User prefers tabs over spaces", namespace="default")
    hits = sqlite_store.search("tabs")
    assert len(hits) == 1
    assert sqlite_store.stats()["backend"] == "sqlite"
    assert sqlite_store.stats()["vectors"] >= 1


def test_sqlite_export_without_embeddings(sqlite_store):
    sqlite_store.add("fact", "Export test fact")
    payload = sqlite_store.export_data()
    assert payload["entries"]
    assert "embedding" not in payload["entries"][0]


def test_sqlite_branch_summary_upsert(sqlite_store):
    entry = sqlite_store.upsert_branch_summary("main", "Conversation summary: discussed memory.")
    assert entry["namespace"] == "branch:main"
    again = sqlite_store.upsert_branch_summary("main", "Conversation summary: updated topic.")
    assert again["id"] == entry["id"]
    assert "updated" in again["content"].lower()


def test_create_memory_store_json_path(data_dir, monkeypatch):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    path = data_dir / "memory.json"
    store = create_memory_store(path)
    assert isinstance(store, JsonMemoryStore)
    store.add("fact", "json path store")
    assert path.exists()


def test_memory_store_facade_sqlite(data_dir, monkeypatch):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setenv("JARVIS_MEMORY_BACKEND", "sqlite")
    monkeypatch.setattr("jarvis.config.MEMORY_DB_FILE", data_dir / "memory.db")
    monkeypatch.setattr("jarvis.config.MEMORY_FILE", data_dir / "memory.json")
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    store = MemoryStore()
    store.add("preference", "User runs Ollama locally")
    assert store.stats()["total"] == 1
    assert (data_dir / "memory.db").exists()


def test_json_embeddings_moved_to_sidecar(data_dir, monkeypatch):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.5] if t else [])
    path = data_dir / "memory.json"
    path.write_text(
        '{"entries":[{"id":"abc","type":"fact","content":"hello","tags":[],"namespace":"default",'
        '"timestamp":"2026-01-01T00:00:00+00:00","access_count":0,"relevance":1.0,'
        '"embedding":[1.0,0.5]}],"version":2}',
        encoding="utf-8",
    )
    store = JsonMemoryStore(path=path, embeddings=EmbeddingSidecar(data_dir / "vectors.db"))
    raw = path.read_text(encoding="utf-8")
    assert "embedding" not in raw
    assert store._embeddings.get("abc") == [1.0, 0.5]
