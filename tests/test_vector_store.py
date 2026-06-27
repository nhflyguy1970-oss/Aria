"""Vector store backend tests."""

import pytest

from jarvis.modules.memory_common import search_pool
from jarvis.modules.vector_store import SqliteVectorStore, create_vector_store, resolve_vector_backend


@pytest.fixture
def mock_embed(monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: True)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if "tabs" in t.lower() else [0.0, 1.0])


def test_sqlite_vector_store_search(data_dir, mock_embed):
    store = SqliteVectorStore(data_dir / "vectors.db")
    store.upsert("a", [1.0, 0.0], namespace="default", entry_type="fact", content="tabs")
    store.upsert("b", [0.0, 1.0], namespace="default", entry_type="fact", content="spaces")
    hits = store.search([1.0, 0.0], limit=2, min_score=0.3)
    assert hits[0][0] == "a"
    assert hits[0][1] > hits[1][1]


def test_search_pool_uses_vector_store(data_dir, mock_embed):
    store = SqliteVectorStore(data_dir / "vectors.db")
    pool = [
        {"id": "a", "content": "tabs over spaces", "namespace": "default", "type": "fact", "relevance": 1.0, "access_count": 0, "timestamp": "2026-01-01T00:00:00+00:00"},
        {"id": "b", "content": "spaces over tabs", "namespace": "default", "type": "fact", "relevance": 1.0, "access_count": 0, "timestamp": "2026-01-01T00:00:00+00:00"},
    ]
    store.upsert("a", [1.0, 0.0], namespace="default", entry_type="fact", content=pool[0]["content"])
    store.upsert("b", [0.0, 1.0], namespace="default", entry_type="fact", content=pool[1]["content"])

    def _get(e):
        return store.get(e["id"])

    def _set(e, emb):
        store.upsert(e["id"], emb, namespace=e["namespace"], entry_type=e["type"], content=e["content"])

    results = search_pool(
        pool,
        "tabs",
        1,
        namespace=None,
        get_embedding=_get,
        set_embedding=_set,
        touch=lambda _id: None,
        flush_touches=lambda: None,
        vector_store=store,
    )
    assert len(results) == 1
    assert results[0]["id"] == "a"


def test_create_vector_store_sqlite_default(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_VECTOR_BACKEND", raising=False)
    store = create_vector_store(data_dir)
    assert store.backend == "sqlite"
    assert resolve_vector_backend() == "sqlite"


def test_create_vector_store_unknown_falls_back(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_VECTOR_BACKEND", "chroma")
    monkeypatch.setattr(
        "jarvis.modules.vector_store.ChromaVectorStore",
        None,
        raising=False,
    )
    # Force import error path by patching resolve to chroma then broken class
    import jarvis.modules.vector_store as vs

    class BrokenChroma:
        backend = "chroma"

        def __init__(self, path):
            raise ImportError("no chroma")

    monkeypatch.setattr(vs, "ChromaVectorStore", BrokenChroma)
    store = create_vector_store(data_dir)
    assert store.backend == "sqlite"
