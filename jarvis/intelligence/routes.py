"""FastAPI routes for the next-generation intelligence platform."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Request

log = logging.getLogger("jarvis.intelligence.routes")


def register_intelligence_routes(app, assistant: Any = None) -> None:
    """Register /api/intelligence/* endpoints on the Aria FastAPI app."""

    @app.get("/api/intelligence/status")
    def intelligence_status():
        from jarvis.intelligence.platform_bus import platform_status

        return platform_status()

    @app.post("/api/intelligence/bootstrap")
    def intelligence_bootstrap():
        from jarvis.intelligence.platform_bus import bootstrap_platform

        return bootstrap_platform(start_automation=True)

    @app.post("/api/intelligence/query")
    async def intelligence_query(request: Request):
        body = await request.json()
        from jarvis.intelligence.platform_bus import intelligent_query

        return intelligent_query(
            str(body.get("query") or ""),
            assistant=assistant,
            use_agents=bool(body.get("use_agents")),
            use_reasoning=body.get("use_reasoning", True),
            use_rag=body.get("use_rag", True),
            use_graph=body.get("use_graph", True),
            use_memory=body.get("use_memory", True),
        )

    @app.post("/api/intelligence/rag/search")
    async def intelligence_rag_search(request: Request):
        body = await request.json()
        from jarvis.intelligence.hybrid_rag import hybrid_search

        return hybrid_search(str(body.get("query") or ""), limit=int(body.get("limit") or 6))

    @app.post("/api/intelligence/reason")
    async def intelligence_reason(request: Request):
        body = await request.json()
        from jarvis.intelligence.reasoning import reason

        return reason(str(body.get("goal") or body.get("query") or ""), assistant=assistant)

    @app.post("/api/intelligence/agents/run")
    async def intelligence_agents_run(request: Request):
        body = await request.json()
        from jarvis.intelligence.multi_agent import run_multi_agent

        return run_multi_agent(
            assistant,
            str(body.get("goal") or ""),
            specialists=body.get("specialists"),
            stop_on_error=bool(body.get("stop_on_error")),
        )

    @app.get("/api/intelligence/memory/status")
    def intelligence_memory_status():
        from jarvis.intelligence.memory_platform import memory_status

        return memory_status()

    @app.post("/api/intelligence/memory/search")
    async def intelligence_memory_search(request: Request):
        body = await request.json()
        from jarvis.intelligence.memory_platform import search_memories

        return search_memories(str(body.get("query") or ""), limit=int(body.get("limit") or 10))

    @app.post("/api/intelligence/memory/consolidate")
    def intelligence_memory_consolidate():
        from jarvis.intelligence.memory_platform import consolidate_memories

        return consolidate_memories()

    @app.post("/api/intelligence/memory/export")
    def intelligence_memory_export():
        from jarvis.intelligence.memory_platform import export_memories

        return export_memories()

    @app.post("/api/intelligence/memory/import")
    async def intelligence_memory_import(request: Request):
        body = await request.json()
        from jarvis.intelligence.memory_platform import import_memories

        return import_memories(str(body.get("path") or ""))

    @app.post("/api/intelligence/graph/ingest")
    async def intelligence_graph_ingest(request: Request):
        body = await request.json()
        # Default: propose for review. Persist only when approve=true (explicit).
        from jarvis.connections_services import approve_pending_ingest, propose_ingest_from_text
        from jarvis.intelligence.knowledge_graph import ingest_text

        text = str(body.get("text") or "")
        namespace = str(body.get("namespace") or "default")
        if body.get("approve") is True or body.get("explicit") is True:
            return ingest_text(
                text,
                namespace=namespace,
                source=str(body.get("source") or "manual"),
                confidence=float(body.get("confidence") or 0.7),
                document=str(body.get("document") or ""),
                project=str(body.get("project") or ""),
                memory_id=str(body.get("memory_id") or ""),
                explicit=True,
            )
        return propose_ingest_from_text(
            text,
            namespace=namespace,
            source=str(body.get("source") or "ai_suggestion"),
            document=str(body.get("document") or ""),
            project=str(body.get("project") or ""),
        )

    @app.post("/api/intelligence/graph/approve")
    async def intelligence_graph_approve(request: Request):
        body = await request.json()
        from jarvis.connections_services import approve_pending_ingest

        return approve_pending_ingest(
            str(body.get("pending_id") or ""),
            selected_entities=body.get("entities"),
            selected_rels=body.get("relationships"),
        )

    @app.get("/api/intelligence/graph/search")
    def intelligence_graph_search(q: str = "", limit: int = 12):
        from jarvis.intelligence.knowledge_graph import search_graph

        return search_graph(q, limit=limit)

    @app.get("/api/intelligence/graph/neighbors")
    def intelligence_graph_neighbors(name: str, depth: int = 1, limit: int = 24):
        from jarvis.intelligence.knowledge_graph import neighbors

        return neighbors(name, depth=depth, limit=limit)

    @app.get("/api/intelligence/automation")
    def intelligence_automation_list():
        from jarvis.intelligence.automation_engine import status

        return status()

    @app.post("/api/intelligence/automation")
    async def intelligence_automation_upsert(request: Request):
        body = await request.json()
        from jarvis.intelligence.automation_engine import upsert_rule

        return {"ok": True, "rule": upsert_rule(body)}

    @app.delete("/api/intelligence/automation/{rule_id}")
    def intelligence_automation_delete(rule_id: str):
        from jarvis.intelligence.automation_engine import delete_rule

        return delete_rule(rule_id)

    @app.post("/api/intelligence/automation/{rule_id}/run")
    def intelligence_automation_run(rule_id: str):
        from jarvis.intelligence.automation_engine import run_rule

        return run_rule(rule_id)

    @app.post("/api/intelligence/automation/start")
    def intelligence_automation_start():
        from jarvis.intelligence.automation_engine import start_engine

        return start_engine()

    @app.get("/api/intelligence/workflows")
    def intelligence_workflows():
        from jarvis.automation.pipelines.storage import list_pipelines, list_templates

        return {
            "ok": True,
            "workflows": list_pipelines(),
            "templates": [t["id"] for t in list_templates()],
            "template_meta": list_templates(),
        }

    @app.post("/api/intelligence/workflows/from-template")
    async def intelligence_workflows_from_template(request: Request):
        body = await request.json()
        from jarvis.automation.pipelines.storage import create_from_template

        wf = create_from_template(str(body.get("template") or "morning_routine"), name=body.get("name"))
        return {"ok": True, "id": wf["id"], "path": f"automation_product/workflow_dags/{wf['id']}.json", "name": wf["name"], "reused": bool(wf.get("reused"))}

    @app.post("/api/intelligence/workflows/{workflow_id}/run")
    async def intelligence_workflows_run(workflow_id: str, request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.automation.pipelines.engine import run_pipeline

        return run_pipeline(
            workflow_id,
            variables=body.get("variables") if isinstance(body.get("variables"), dict) else {},
            dry_run=bool(body.get("dry_run")),
            approve_experimental=bool(body.get("approve_experimental")),
            from_step=body.get("from_step"),
            trigger=str(body.get("trigger") or "api"),
            emit_bridges=True,
        )

    @app.get("/api/intelligence/plugins")
    def intelligence_plugins():
        from jarvis.intelligence.plugin_sdk import list_plugins

        return {"ok": True, "plugins": list_plugins()}

    @app.post("/api/intelligence/plugins/load")
    def intelligence_plugins_load():
        from jarvis.intelligence.plugin_sdk import load_all

        return load_all()

    @app.get("/api/intelligence/connectors")
    def intelligence_connectors():
        from jarvis.intelligence.connectors import list_connectors

        return {"ok": True, "connectors": list_connectors()}

    @app.post("/api/intelligence/documents/analyze")
    async def intelligence_documents_analyze(request: Request):
        body = await request.json()
        from jarvis.intelligence.document_intel import analyze_document

        return analyze_document(str(body.get("path") or ""))

    @app.get("/api/intelligence/documents/extensions")
    def intelligence_documents_extensions():
        from jarvis.intelligence.document_intel import supported_extensions

        return {"ok": True, "extensions": supported_extensions()}

    log.info("Registered Aria intelligence platform routes under /api/intelligence/*")
