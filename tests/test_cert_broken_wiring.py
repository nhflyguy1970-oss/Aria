"""Live certification: callers referencing names their target never provided.

Each of these shipped as a guaranteed runtime failure — the caller and the
callee disagreed, and no test exercised the pair together.
"""

from __future__ import annotations

import inspect

import pytest


def test_similar_exists_accepts_the_namespace_callers_pass():
    """memory_consolidation passes namespace=; the stores did not accept it,
    so those calls raised TypeError."""
    from jarvis.modules.memory import JsonMemoryStore
    from jarvis.modules.memory_sqlite import SqliteMemoryStore

    for store in (JsonMemoryStore, SqliteMemoryStore):
        sig = inspect.signature(store.similar_exists)
        assert "namespace" in sig.parameters, f"{store.__name__} lost namespace support"


def test_similar_exists_is_scoped_to_the_namespace(data_dir, monkeypatch):
    """Only reachable when ACM is not the authority; ACM's own duplicate check
    has no namespace concept (recorded as a finding, not changed here)."""
    from aria_core import acm_bridge
    from jarvis.modules.memory_sqlite import SqliteMemoryStore

    monkeypatch.setattr(acm_bridge, "acm_is_authoritative", lambda *_a, **_k: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda *_a, **_k: None)

    store = SqliteMemoryStore(data_dir / "ns_memory.db")
    store.add("fact", "kingfishers dive for minnows", namespace="birds")

    assert store.similar_exists("kingfishers dive for minnows", namespace="birds")
    assert not store.similar_exists("kingfishers dive for minnows", namespace="tools"), (
        "one namespace suppressed a fact another has never recorded"
    )


def test_memory_consolidation_can_call_the_store_it_calls(data_dir, monkeypatch):
    """The real caller, with the real keyword — this raised TypeError."""
    from aria_core import acm_bridge
    from jarvis.modules.memory_sqlite import SqliteMemoryStore

    monkeypatch.setattr(acm_bridge, "acm_is_authoritative", lambda *_a, **_k: False)
    monkeypatch.setattr("jarvis.llm.embed_text", lambda *_a, **_k: None)
    store = SqliteMemoryStore(data_dir / "consolidation.db")

    assert store.similar_exists("some consolidated fact", namespace="work") is False


def test_document_path_resolution_has_no_phantom_import():
    from jarvis.behaviors.knowledge import context

    src = inspect.getsource(context.KnowledgeContext.resolve_document_path)
    assert "from jarvis.config import DATA_DIR, PROJECT_ROOT\n" in src
    from jarvis import config

    assert not hasattr(config, "UPLOAD_DIR"), "config gained UPLOAD_DIR; simplify the fix"


@pytest.mark.parametrize(
    "module_path,name",
    [
        ("jarvis.tool_permissions", "execute_confirm"),
    ],
)
def test_shared_helpers_exist(module_path, name):
    import importlib

    assert hasattr(importlib.import_module(module_path), name)
