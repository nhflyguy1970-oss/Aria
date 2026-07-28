"""Automation Pipelines API — CRUD, run inspector, NL draft, promote, canvas.

Pipelines remain a subsystem of Automation (not a separate product).
"""

from __future__ import annotations

from typing import Any


def register_pipeline_routes(app, assistant) -> None:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.get("/api/automation/pipelines")
    def pipelines_list(
        q: str = "",
        tag: str = "",
        sort: str = "name",
        favorites: bool = False,
    ):
        from jarvis.automation.pipelines.storage import list_pipelines, list_templates, recent_pipelines

        return {
            "ok": True,
            "pipelines": list_pipelines(q=q, tag=tag, sort=sort, favorites_only=favorites),
            "templates": list_templates(),
            "recent": recent_pipelines(8),
        }

    @app.get("/api/automation/pipelines/templates")
    def pipelines_templates():
        from jarvis.automation.pipelines.storage import list_templates

        return {"ok": True, "templates": list_templates()}

    @app.post("/api/automation/pipelines/from-template")
    async def pipelines_from_template(request: Request):
        body = await request.json()
        from jarvis.automation.pipelines.storage import create_from_template

        try:
            wf = create_from_template(
                str(body.get("template") or body.get("template_id") or "morning_routine"),
                name=body.get("name"),
            )
        except KeyError as exc:
            return JSONResponse(status_code=404, content={"ok": False, "error": f"unknown template: {exc}"})
        return {"ok": True, "pipeline": wf, "reused": bool(wf.get("reused"))}

    @app.get("/api/automation/pipelines/{pipeline_id}")
    def pipelines_get(pipeline_id: str):
        from jarvis.automation.pipelines.engine import explain_pipeline, validate_pipeline
        from jarvis.automation.pipelines.storage import get_pipeline

        wf = get_pipeline(pipeline_id)
        if not wf:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not_found"})
        return {
            "ok": True,
            "pipeline": wf,
            "explain": explain_pipeline(pipeline_id),
            "validation": validate_pipeline(wf),
        }

    @app.post("/api/automation/pipelines")
    async def pipelines_save(request: Request):
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "error": "invalid body"})
        # Reject auto flags
        body.pop("auto_run", None)
        from jarvis.automation.pipelines.engine import validate_pipeline
        from jarvis.automation.pipelines.storage import save_pipeline

        bump = body.pop("bump_version", True)
        if body.get("id") and str(body["id"]).startswith("draft_"):
            import uuid

            body["id"] = uuid.uuid4().hex[:10]
        wf = save_pipeline(body, bump_version=bool(bump))
        return {"ok": True, "pipeline": wf, "validation": validate_pipeline(wf)}

    @app.post("/api/automation/pipelines/{pipeline_id}/rename")
    async def pipelines_rename(pipeline_id: str, request: Request):
        body = await request.json()
        from jarvis.automation.pipelines.storage import rename_pipeline

        try:
            wf = rename_pipeline(pipeline_id, str(body.get("name") or ""))
        except KeyError:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not_found"})
        return {"ok": True, "pipeline": wf}

    @app.post("/api/automation/pipelines/{pipeline_id}/duplicate")
    async def pipelines_duplicate(pipeline_id: str, request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.automation.pipelines.storage import duplicate_pipeline

        try:
            wf = duplicate_pipeline(pipeline_id, name=body.get("name"))
        except KeyError:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not_found"})
        return {"ok": True, "pipeline": wf}

    @app.delete("/api/automation/pipelines/{pipeline_id}")
    def pipelines_delete(pipeline_id: str):
        from jarvis.automation.pipelines.storage import delete_pipeline

        return delete_pipeline(pipeline_id)

    @app.post("/api/automation/pipelines/bulk-delete")
    async def pipelines_bulk_delete(request: Request):
        body = await request.json()
        from jarvis.automation.pipelines.storage import bulk_delete

        return bulk_delete(list(body.get("ids") or []))

    @app.post("/api/automation/pipelines/export")
    async def pipelines_export(request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.automation.pipelines.storage import export_pipelines

        ids = body.get("ids")
        return export_pipelines(list(ids) if ids else None)

    @app.post("/api/automation/pipelines/{pipeline_id}/favorite")
    async def pipelines_favorite(pipeline_id: str, request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.automation.pipelines.storage import set_favorite

        return set_favorite(pipeline_id, favorite=bool(body.get("favorite", True)))

    @app.post("/api/automation/pipelines/{pipeline_id}/run")
    async def pipelines_run(pipeline_id: str, request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        dry_run = bool(body.get("dry_run"))
        if not dry_run and not body.get("confirm"):
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "status": "permission_required",
                    "error": "confirm=true required for real execution (or use dry_run=true)",
                },
            )
        from jarvis.automation.pipelines.engine import run_pipeline

        result = run_pipeline(
            pipeline_id,
            variables=body.get("variables") if isinstance(body.get("variables"), dict) else {},
            dry_run=dry_run,
            approve_experimental=bool(body.get("approve_experimental")),
            from_step=body.get("from_step") or None,
            trigger=str(body.get("trigger") or "manual"),
            emit_bridges=True,
        )
        return result

    @app.get("/api/automation/pipelines/{pipeline_id}/explain")
    def pipelines_explain(pipeline_id: str):
        from jarvis.automation.pipelines.engine import explain_pipeline

        return explain_pipeline(pipeline_id)

    @app.get("/api/automation/pipelines/{pipeline_id}/canvas")
    def pipelines_canvas(pipeline_id: str):
        from jarvis.automation.pipelines.canvas import canvas_model

        return canvas_model(pipeline_id)

    @app.get("/api/automation/pipeline-runs")
    def pipeline_runs_list(limit: int = 50, pipeline_id: str = "", status: str = "", q: str = ""):
        from jarvis.automation.pipelines.runs import list_pipeline_runs

        return {
            "ok": True,
            "runs": list_pipeline_runs(
                limit=limit,
                pipeline_id=pipeline_id or None,
                status=status or None,
                q=q,
            ),
        }

    @app.get("/api/automation/pipeline-runs/{run_id}")
    def pipeline_run_get(run_id: str):
        from jarvis.automation.pipelines.runs import get_pipeline_run

        run = get_pipeline_run(run_id)
        if not run:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not_found"})
        return {"ok": True, "run": run}

    @app.get("/api/automation/pipelines/{pipeline_id}/last-run")
    def pipeline_last_run(pipeline_id: str):
        from jarvis.automation.pipelines.runs import last_run

        run = last_run(pipeline_id)
        return {"ok": True, "run": run}

    @app.get("/api/automation/pipelines/{pipeline_id}/last-failure")
    def pipeline_last_failure(pipeline_id: str):
        from jarvis.automation.pipelines.runs import last_failure

        run = last_failure(pipeline_id)
        return {"ok": True, "run": run}

    @app.post("/api/automation/pipelines/nl")
    async def pipelines_nl(request: Request):
        body = await request.json()
        from jarvis.automation.pipelines.nl import parse_nl_pipeline

        return parse_nl_pipeline(str(body.get("text") or body.get("message") or ""))

    @app.post("/api/automation/pipelines/nl/save")
    async def pipelines_nl_save(request: Request):
        body = await request.json()
        if not body.get("confirm"):
            return JSONResponse(status_code=400, content={"ok": False, "error": "confirm=true required"})
        draft = body.get("draft")
        if not isinstance(draft, dict):
            return JSONResponse(status_code=400, content={"ok": False, "error": "draft required"})
        draft.pop("auto_run", None)
        draft["auto_save"] = False
        import uuid

        if str(draft.get("id") or "").startswith("draft_"):
            draft["id"] = uuid.uuid4().hex[:10]
        from jarvis.automation.pipelines.storage import save_pipeline

        wf = save_pipeline(draft, bump_version=False)
        return {"ok": True, "pipeline": wf}

    @app.post("/api/automation/pipelines/promote-learned")
    async def pipelines_promote_learned(request: Request):
        body = await request.json()
        from jarvis.automation.pipelines.promote import learned_to_dag_draft

        draft = learned_to_dag_draft(str(body.get("slug") or ""))
        if body.get("confirm") and body.get("save") and draft.get("ok"):
            import uuid

            d = draft["draft"]
            d["id"] = uuid.uuid4().hex[:10]
            from jarvis.automation.pipelines.storage import save_pipeline

            wf = save_pipeline(d, bump_version=False)
            return {"ok": True, "pipeline": wf, "draft": d, "saved": True}
        return draft

    @app.get("/api/automation/pipeline-jobs")
    def pipeline_jobs():
        from jarvis.automation.pipelines.jobs import list_jobs

        return {"ok": True, "jobs": list_jobs(limit=20)}
