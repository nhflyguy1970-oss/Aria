"""Connections (Knowledge Graph) — store, services, ACM mirror, pollution guards."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def graph_env(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_GRAPH_BACKEND", "sqlite")
    db = tmp_path / "relationship_graph.db"
    monkeypatch.setattr("jarvis.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.connections_services.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.connections_services.ACTIVITY_FILE", tmp_path / "connections_activity.json")
    monkeypatch.setattr("jarvis.connections_services.UNDO_FILE", tmp_path / "connections_undo.json")
    monkeypatch.setattr("jarvis.connections_services.PENDING_FILE", tmp_path / "connections_pending_ingest.json")
    monkeypatch.setattr("jarvis.memory_services.CANDIDATES_FILE", tmp_path / "memory_candidates.json")
    monkeypatch.setattr("jarvis.memory_services.DATA_DIR", tmp_path)

    from jarvis.modules.graph_store import SqliteGraphStore, reset_graph_store_for_tests

    store = SqliteGraphStore(db)
    reset_graph_store_for_tests(store)
    yield store
    reset_graph_store_for_tests(None)


def test_store_merge_search_delete_prune(graph_env):
    store = graph_env
    store.merge_relationship(
        "Aria",
        "USES",
        "Ollama",
        namespace="default",
        props={"source": "manual", "confidence": 0.9},
    )
    assert store.stats()["nodes"] >= 2
    assert store.stats()["edges"] >= 1
    hits = store.search_nodes("Aria")
    assert hits and hits[0]["name"] == "Aria"
    page = store.neighbors("Aria")
    assert any(t["predicate"] == "USES" for t in page)
    # orphan
    store.merge_node("Lonely", namespace="default", props={"source": "manual", "confidence": 1})
    pruned = store.prune_orphans()
    assert pruned["ok"]
    assert pruned["pruned"] >= 1
    deleted = store.delete_node("Aria", namespace="default")
    assert deleted["ok"]


def test_no_anonymous_relationship(graph_env):
    from jarvis.connections_services import create_relationship

    bad = create_relationship("A", "RELATED_TO", "B", source="unknown", confidence=0.9)
    assert bad["ok"] is False
    good = create_relationship("A", "RELATED_TO", "B", source="manual", confidence=0.9)
    assert good["ok"] is True


def test_propose_approve_not_auto_write(graph_env):
    from jarvis.connections_services import approve_pending_ingest, propose_ingest_from_text, search_connections
    from jarvis.modules.graph_store import get_graph_store

    before = get_graph_store().stats()["edges"]
    pending = propose_ingest_from_text(
        "Aria works at Home Lab. Aria uses Ollama.",
        namespace="test",
        source="ai_suggestion",
    )
    assert pending["ok"]
    assert get_graph_store().stats()["edges"] == before
    approved = approve_pending_ingest(pending["pending"]["id"])
    assert approved["ok"]
    assert approved["relationships"] >= 1
    found = search_connections("Aria", mode="entities")
    assert found["nodes"]


def test_query_soft_ingest_forbidden(graph_env):
    from jarvis.intelligence.knowledge_graph import ingest_text

    blocked = ingest_text("Aria uses Foo", namespace="queries", explicit=True)
    assert blocked["ok"] is False
    blocked2 = ingest_text("Aria uses Foo", explicit=False)
    assert blocked2["ok"] is False


def test_platform_bus_does_not_pollute(graph_env, monkeypatch):
    from jarvis.intelligence import platform_bus
    from jarvis.modules.graph_store import get_graph_store

    monkeypatch.setattr(
        "jarvis.intelligence.memory_platform.search_memories",
        lambda *a, **k: {"ok": True, "hits": []},
    )
    monkeypatch.setattr(
        "jarvis.intelligence.hybrid_rag.hybrid_search",
        lambda *a, **k: {"ok": True, "hits": [], "citations": []},
    )
    monkeypatch.setattr(
        "jarvis.intelligence.reasoning.reason",
        lambda *a, **k: {"ok": True, "plan": [], "confidence": 0.5, "trace_id": "t"},
    )
    before = get_graph_store().stats()["nodes"]
    out = platform_bus.intelligent_query("What about Aria and Ollama systems?")
    assert out["ok"]
    assert "graph" in out["parts"]
    assert get_graph_store().stats()["nodes"] == before


def test_merge_undo_and_cleanup_queries(graph_env):
    from jarvis.connections_services import (
        cleanup_queries_namespace,
        create_entity,
        create_relationship,
        merge_entities,
        undo_last,
    )
    from jarvis.modules.graph_store import get_graph_store

    create_entity("Jeff", kind="person", source="manual")
    create_entity("jeff", kind="person", source="manual", namespace="alt")
    # same namespace merge
    create_entity("Jeffrey", kind="person", source="manual")
    create_relationship("Jeff", "KNOWS", "Aria", source="manual", confidence=1)
    create_relationship("Jeffrey", "USES", "Ollama", source="manual", confidence=1)
    merged = merge_entities("Jeff", "Jeffrey", namespace="default")
    assert merged["ok"]
    undone = undo_last(merged.get("undo_id") or "")
    assert undone["ok"]

    # pollution namespace
    store = get_graph_store()
    store.merge_node("Polluted", namespace="queries", props={"source": "manual"})
    cleaned = cleanup_queries_namespace()
    assert cleaned["ok"]


def test_acm_mirror_on_adopt(graph_env, monkeypatch):
    from jarvis.connections_services import search_connections
    from jarvis.memory_services import adopt_candidate, propose_candidate
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(path=graph_env.path.parent / "memory.json")
    cand = propose_candidate(
        "link Aria -> USES -> Ollama",
        source="test",
        tags=["relationship", "pred:USES"],
        confidence=0.9,
    )
    assert cand["ok"]
    result = adopt_candidate(store, cand["candidate"]["id"])
    assert result["ok"]
    assert result.get("connections_mirror", {}).get("mirrored", 0) >= 1
    found = search_connections("Aria", mode="entities")
    assert any(n["name"] == "Aria" for n in found["nodes"])


def test_chat_grounding_requires_provenance(graph_env):
    from jarvis.connections_services import chat_grounding_context, create_relationship
    from jarvis.modules.graph_store import get_graph_store

    # Low confidence anonymous-ish should not ground — create with low conf but source manual still ok if conf high enough
    store = get_graph_store()
    store.merge_relationship(
        "Ghost",
        "RELATED_TO",
        "Void",
        namespace="default",
        props={"source": "unknown", "confidence": 0.2},
    )
    cold = chat_grounding_context("What is connected to Ghost?")
    assert cold["used"] is False

    create_relationship("Aria", "USES", "Ollama", source="memory", confidence=0.9, memory_id="mem1")
    hot = chat_grounding_context("What does Aria use? connections for Aria")
    assert hot["used"] is True
    assert "Trusted Connections" in hot["context"]
    assert "source=" in hot["context"]


def test_knowledge_graph_shim_search(graph_env):
    from jarvis import knowledge_graph as kg
    from jarvis.connections_services import create_entity

    create_entity("Atlas", kind="project", source="manual")
    hits = kg.search("Atlas")
    assert hits
    assert hits[0]["source"] == "connections"


def test_project_namespace(graph_env):
    from jarvis.connections_services import create_entity, create_relationship, project_namespace, project_subgraph

    ns = project_namespace("My App")
    assert ns.startswith("project:")
    create_entity("MainModule", kind="project", namespace=ns, source="manual", project="my-app")
    create_relationship("MainModule", "USES", "FastAPI", namespace=ns, source="manual", confidence=1, project="my-app")
    sub = project_subgraph("My App")
    assert sub["ok"]
    assert sub["nodes"]


def test_relationship_assistant_suggestions(graph_env):
    from jarvis.connections_services import create_entity, create_relationship, relationship_assistant

    create_entity("OrphanNode", source="manual")
    create_relationship("A", "RELATED_TO", "B", source="manual", confidence=0.2)
    tips = relationship_assistant()
    assert tips["ok"]
    assert tips["auto_modify"] is False
    types = {s["type"] for s in tips["suggestions"]}
    assert "orphans" in types or "low_confidence" in types


def test_explain_relationship(graph_env):
    from jarvis.connections_services import create_relationship, explain_relationship

    create_relationship("Aria", "USES", "Ollama", source="document", confidence=0.8, document="manual.md")
    exp = explain_relationship("Aria", "Ollama")
    assert exp["ok"]
    assert exp["explanations"]
    assert "source=" in exp["explanations"][0]["why"]


def test_home_and_health(graph_env):
    from jarvis.connections_services import connections_home, health

    h = health()
    assert h["product_name"] == "Connections"
    assert "Memory" in h["philosophy"] or "ACM" in h["philosophy"]
    home = connections_home()
    assert home["identity"]["connections"]
    assert home["identity"]["memory"]
