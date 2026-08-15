"""Tests for Aria next-generation intelligence platform."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _intel_test_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JARVIS_HYBRID_RAG_EMBED", "0")
    monkeypatch.setenv("JARVIS_REASONING_LLM", "0")


def test_hybrid_rag_query_expansion_and_empty():
    from jarvis.intelligence.hybrid_rag import expand_query, hybrid_search

    variants = expand_query("how do I fix the bug")
    assert variants
    assert any("how to" in v.lower() for v in variants)

    empty = hybrid_search("")
    assert empty["ok"] is False

    result = hybrid_search("documentation overview", limit=3)
    assert result["ok"] is True
    assert "hits" in result
    assert "citations" in result
    assert "mode" in result


def test_reasoning_plan_and_confidence(data_dir):
    from jarvis.intelligence.reasoning import reason

    out = reason("Plan a morning routine. Verify provider health. Summarize memory.")
    assert out["ok"] is True
    assert out["plan"]
    assert 0 < out["confidence"] <= 1
    assert out["trace_id"]
    assert out["checks"]


def test_knowledge_graph_extract_and_ingest(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_GRAPH_BACKEND", "sqlite")
    from jarvis.modules.graph_store import SqliteGraphStore, reset_graph_store_for_tests
    from jarvis.intelligence.knowledge_graph import extract_entities, extract_relationships, ingest_text, search_graph

    store = SqliteGraphStore(Path(data_dir) / "relationship_graph.db")
    reset_graph_store_for_tests(store)
    try:
        text = "Aria works at Home Lab. Aria uses Ollama. Project Atlas is a research system."
        ents = extract_entities(text)
        assert any(e["name"] == "Aria" or e["name"] == "Ollama" for e in ents)
        rels = extract_relationships(text)
        assert rels

        ingested = ingest_text(text, namespace="test")
        assert ingested["ok"] is True
        assert ingested["nodes_merged"] >= 1

        found = search_graph("Aria", limit=5)
        assert found["ok"] is True
        assert found["backend"] == "sqlite"
    finally:
        reset_graph_store_for_tests(None)


def test_automation_rules_crud_and_run(data_dir, monkeypatch):
    from jarvis.automation.engine import delete_rule, list_rules, run_rule, upsert_rule

    rules = data_dir / "automation_product" / "rules.json"
    rules.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.automation.engine._rules_path", lambda: rules)
    monkeypatch.setattr("jarvis.automation.engine._rules", [])

    rule = upsert_rule(
        {
            "name": "Test interval",
            "kind": "interval",
            "expression": "3600",
            "action": "memory_consolidate",
            "enabled": True,
        }
    )
    assert rule["id"]
    assert any(r["id"] == rule["id"] for r in list_rules())
    result = run_rule(rule["id"])
    assert "ok" in result
    assert delete_rule(rule["id"])["deleted"] == 1


def test_workflow_template_run(data_dir, monkeypatch):
    from jarvis.intelligence.workflow_engine import run_workflow, save_workflow, workflow_from_template

    dags = data_dir / "automation_product" / "workflow_dags"
    dags.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.automation.paths.AUTOMATION_ROOT", data_dir / "automation_product")
    monkeypatch.setattr("jarvis.automation.paths.WORKFLOW_DAGS_DIR", dags)
    monkeypatch.setattr("jarvis.intelligence.workflow_engine.WORKFLOW_DIR", dags)
    monkeypatch.setattr(
        "jarvis.automation.pipelines.engine.execute_action",
        lambda action, params, variables, **kw: {"ok": True, "result": action, "dry_run": kw.get("dry_run")},
    )
    wf = workflow_from_template("morning_routine")
    save_workflow(wf)
    result = run_workflow(wf.id, emit_bridges=False)
    assert result["ok"] is True
    assert result["log"]
    assert all(step.get("ok") or step.get("skipped") for step in result["log"])


def test_workflow_retry_on_failure(data_dir, monkeypatch):
    from jarvis.intelligence.workflow_engine import WorkflowDef, WorkflowStep, run_workflow, save_workflow

    dags = data_dir / "automation_product" / "workflow_dags"
    dags.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.automation.paths.AUTOMATION_ROOT", data_dir / "automation_product")
    monkeypatch.setattr("jarvis.automation.paths.WORKFLOW_DAGS_DIR", dags)
    monkeypatch.setattr("jarvis.intelligence.workflow_engine.WORKFLOW_DIR", dags)

    def exec_action(action, params, variables, *, dry_run=False, approve_experimental=False):
        if action == "builtin:fail":
            return {"ok": False, "error": params.get("error") or "boom"}
        return {"ok": True, "message": params.get("msg")}

    monkeypatch.setattr("jarvis.automation.pipelines.engine.execute_action", exec_action)

    wf = WorkflowDef(
        id="retrydemo",
        name="Retry Demo",
        entry="fail",
        steps=[
            WorkflowStep(
                id="fail",
                name="Fail once path",
                action="builtin:fail",
                params={"error": "boom"},
                retries=1,
                on_failure=["recover"],
            ),
            WorkflowStep(id="recover", name="Recover", action="builtin:log", params={"msg": "recovered"}),
        ],
    )
    save_workflow(wf)
    result = run_workflow(wf.id, emit_bridges=False)
    assert result["log"]
    assert result["log"][0]["ok"] is False
    assert result["log"][-1]["ok"] is True


def test_plugin_sdk_example(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(data_dir))
    # PLUGIN_DIR uses DATA_DIR imported at module load — recreate via create_example_plugin
    from jarvis.intelligence import plugin_sdk

    path = plugin_sdk.create_example_plugin()
    assert (path / "aria_plugin.json").is_file()
    loaded = plugin_sdk.load_plugin(path)
    assert loaded.error == ""
    assert loaded.manifest.id == "hello_aria"


def test_connectors_registry_and_cache():
    from jarvis.intelligence.connectors import ConnectorConfig, register_connector, list_connectors

    register_connector(
        ConnectorConfig(
            name="unit_test_conn",
            base_url="http://127.0.0.1:9",
            cache_ttl_sec=30,
            max_retries=0,
            rate_limit_per_min=1000,
        )
    )
    names = [c["name"] for c in list_connectors()]
    assert "unit_test_conn" in names


def test_document_intel_csv_and_tags(tmp_path):
    from jarvis.intelligence.document_intel import analyze_document, auto_tags, parse_extended

    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,score\nalpha,1\nbeta,2\n", encoding="utf-8")
    parsed = parse_extended(csv_path)
    assert parsed["ok"] is True
    assert "alpha" in (parsed["pages"][0] or "")

    tags = auto_tags("Memory retrieval quality improves with embeddings and consolidation pipelines.")
    assert "memory" in tags or "embeddings" in tags or "retrieval" in tags

    analyzed = analyze_document(csv_path)
    assert analyzed["ok"] is True
    assert "tags" in analyzed


def test_multi_agent_resolve_specialists():
    from jarvis.intelligence.multi_agent import resolve_specialists

    roles = resolve_specialists("Research and implement a fix, then document it")
    assert "researcher" in roles or "coder" in roles or "planner" in roles
    vision = resolve_specialists("OCR this screenshot please")
    assert "vision" in vision


def test_platform_intelligent_query(data_dir, monkeypatch):
    monkeypatch.setenv("JARVIS_GRAPH_BACKEND", "sqlite")
    from jarvis.intelligence.platform_bus import intelligent_query

    out = intelligent_query("What is Aria memory consolidation?", use_agents=False)
    assert out["ok"] is True
    assert "parts" in out
    assert "reasoning" in out["parts"]
    assert "rag" in out["parts"]


def test_intelligence_routes_registered():
    from fastapi import FastAPI

    from jarvis.intelligence.routes import register_intelligence_routes

    app = FastAPI()
    register_intelligence_routes(app, assistant=None)
    paths = {getattr(route, "path", None) for route in app.routes}
    for required in (
        "/api/intelligence/status",
        "/api/intelligence/query",
        "/api/intelligence/rag/search",
        "/api/intelligence/reason",
        "/api/intelligence/agents/run",
        "/api/intelligence/graph/search",
        "/api/intelligence/automation",
        "/api/intelligence/workflows",
        "/api/intelligence/plugins",
        "/api/intelligence/connectors",
        "/api/intelligence/documents/analyze",
    ):
        assert required in paths, f"missing route {required}"


def test_intelligence_status_endpoint():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from jarvis.intelligence.routes import register_intelligence_routes

    app = FastAPI()
    register_intelligence_routes(app, assistant=None)
    res = TestClient(app).get("/api/intelligence/status")
    assert res.status_code == 200
    data = res.json()
    assert "subsystems" in data
    assert "memory" in data["subsystems"]
    assert "rag" in data["subsystems"]


def test_intelligence_rag_endpoint():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from jarvis.intelligence.routes import register_intelligence_routes

    app = FastAPI()
    register_intelligence_routes(app, assistant=None)
    res = TestClient(app).post("/api/intelligence/rag/search", json={"query": "planner", "limit": 3})
    assert res.status_code == 200
    data = res.json()
    assert data.get("ok") is True
    assert "citations" in data


def test_document_pipeline_accepts_csv(tmp_path, monkeypatch):
    from jarvis.document_pipeline import DOCUMENT_EXTENSIONS, parse_document

    assert ".csv" in DOCUMENT_EXTENSIONS
    assert ".xlsx" in DOCUMENT_EXTENSIONS
    p = tmp_path / "notes.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    doc = parse_document(p, use_cache=False)
    assert doc.char_count > 0
