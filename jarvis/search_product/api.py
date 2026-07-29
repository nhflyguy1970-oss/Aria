"""Search product HTTP API — one engine for all clients."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/search/product")
    def search_product_status():
        from jarvis.search_product.engine import product_status

        return product_status()

    @app.get("/api/search/product/home")
    def search_home(q: str = "", facet: str = ""):
        from jarvis.search_product.engine import home_payload

        return home_payload(q=q, facet=facet)

    @app.post("/api/search/product/query")
    async def search_query(request: Request):
        body = await request.json()
        from jarvis.search_product.pipeline import format_search_message, run_search

        q = str(body.get("query") or body.get("q") or "").strip()
        if not q:
            return JSONResponse(status_code=400, content={"ok": False, "error": "query required"})
        facets = body.get("facets") or body.get("facet")
        if isinstance(facets, str):
            facets = [facets] if facets else None
        result = run_search(
            q,
            facets=facets,
            limit=body.get("limit"),
            mode=body.get("mode"),
            code_mode=body.get("code_mode"),
            record_history=body.get("record_history"),
            context=body.get("context") if isinstance(body.get("context"), dict) else None,
            parallel=body.get("parallel"),
        )
        result["message"] = format_search_message(result)
        return result

    @app.get("/api/search/product/query")
    def search_query_get(
        q: str = "",
        facet: str = "",
        limit: int = 24,
        mode: str = "",
        code_mode: str = "",
    ):
        from jarvis.search_product.pipeline import format_search_message, run_search

        if not q.strip():
            return {"ok": False, "error": "q parameter required", "results": []}
        facets = [facet] if facet and facet != "everything" else None
        result = run_search(
            q.strip(),
            facets=facets,
            limit=limit,
            mode=mode or None,
            code_mode=code_mode or None,
        )
        result["message"] = format_search_message(result)
        return result

    @app.get("/api/search/product/facets")
    def search_facets():
        from jarvis.search_product.diagnostics import corpus_matrix
        from jarvis.search_product.terminology import FACETS

        return {"ok": True, "facets": list(FACETS), "corpora": corpus_matrix()}

    @app.get("/api/search/product/history")
    def search_history(limit: int = 30):
        from jarvis.search_product.history import list_history

        return {"ok": True, "history": list_history(limit)}

    @app.delete("/api/search/product/history")
    def search_history_clear():
        from jarvis.search_product.history import clear_history

        return clear_history()

    @app.get("/api/search/product/saved")
    def search_saved_list():
        from jarvis.search_product.history import list_saved

        return {"ok": True, "saved": list_saved()}

    @app.post("/api/search/product/saved")
    async def search_saved_create(request: Request):
        body = await request.json()
        from jarvis.search_product.history import save_search

        facets = body.get("facets")
        if isinstance(facets, str):
            facets = [facets]
        return save_search(str(body.get("query") or ""), name=str(body.get("name") or ""), facets=facets)

    @app.delete("/api/search/product/saved/{saved_id}")
    def search_saved_delete(saved_id: str):
        from jarvis.search_product.history import delete_saved

        return delete_saved(saved_id)

    @app.get("/api/search/product/sessions")
    def search_sessions(limit: int = 10):
        from jarvis.search_product.sessions import list_sessions

        return {"ok": True, "sessions": list_sessions(limit)}

    @app.get("/api/search/product/sessions/{session_id}")
    def search_session_get(session_id: str):
        from jarvis.search_product.sessions import get_session

        s = get_session(session_id)
        if not s:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        return {"ok": True, "session": s}

    @app.get("/api/search/product/health")
    def search_health():
        from jarvis.search_product.diagnostics import health_summary

        return health_summary()

    @app.get("/api/search/product/diagnostics")
    def search_diagnostics():
        from jarvis.search_product.diagnostics import diagnostics

        return diagnostics()

    @app.get("/api/search/product/recovery")
    def search_recovery():
        from jarvis.search_product.diagnostics import recovery_status

        return recovery_status()

    @app.get("/api/search/product/mission")
    def search_mission():
        from jarvis.search_product.mission_bridge import search_mission_panel

        return search_mission_panel()

    @app.get("/api/search/product/settings")
    def search_settings_get():
        from jarvis.search_product.settings import load_settings

        return {"ok": True, **load_settings()}

    @app.post("/api/search/product/settings")
    async def search_settings_set(request: Request):
        body = await request.json()
        from jarvis.search_product.settings import save_settings

        return {"ok": True, **save_settings(body if isinstance(body, dict) else {})}

    @app.get("/api/search/product/experimental")
    def search_experimental():
        from jarvis.search_product.experimental import experimental_status

        return experimental_status()

    @app.post("/api/search/product/experimental/answer-browse")
    async def search_exp_answer_browse(request: Request):
        body = await request.json()
        from jarvis.search_product.experimental import answer_vs_browse

        return answer_vs_browse(str(body.get("query") or ""))

    @app.get("/api/search/product/bridges/voice")
    def search_bridge_voice():
        from jarvis.search_product.bridges import voice_bridge

        return voice_bridge()

    @app.get("/api/search/product/bridges/vision")
    def search_bridge_vision():
        from jarvis.search_product.bridges import vision_bridge

        return vision_bridge()

    @app.get("/api/search/product/bridges/planner")
    def search_bridge_planner():
        from jarvis.search_product.bridges import planner_bridge

        return planner_bridge()

    @app.get("/api/search/product/bridges/automation")
    def search_bridge_automation():
        from jarvis.search_product.bridges import automation_bridge

        return automation_bridge()

    @app.get("/api/search/product/open")
    def search_open_context(result_id: str = "", view: str = "", query: str = ""):
        """Deep-link helper — returns open payload preserving query context."""
        return {
            "ok": True,
            "open": {
                "view": view or "search",
                "query": query,
                "result_id": result_id,
                "preserve_query": True,
            },
        }


def register_routes(app, assistant) -> None:
    register_product_routes(app, assistant)
