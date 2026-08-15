"""Guided Repair HTTP API — /api/repair/*"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/repair/product")
    def repair_product_status():
        from jarvis.repair_product.engine import product_status

        return product_status()

    @app.get("/api/repair/home")
    def repair_home():
        from jarvis.repair_product.engine import home_payload

        return home_payload()

    @app.get("/api/repair/modules")
    def repair_modules():
        from jarvis.repair_product.engine import product_status
        from jarvis.repair_product import reputation

        st = product_status()
        reps = {r["module_id"]: r for r in reputation.all_reputations()}
        modules = []
        for m in st.get("modules") or []:
            modules.append({**m, "reputation": reps.get(m["id"])})
        return {"ok": True, "modules": modules}

    @app.post("/api/repair/scan")
    def repair_scan():
        from jarvis.repair_product.engine import scan_issues

        return scan_issues(force=True)

    @app.get("/api/repair/issues")
    def repair_issues(active: int = 1):
        from jarvis.repair_product import store
        from jarvis.repair_product.impact import sort_by_priority

        return {"ok": True, "issues": sort_by_priority(store.list_issues(active_only=bool(active)))}

    @app.get("/api/repair/issues/{issue_id}")
    def repair_issue(issue_id: str):
        from jarvis.repair_product.engine import issue_panel

        return issue_panel(issue_id)

    @app.post("/api/repair/plan")
    async def repair_plan(request: Request):
        from jarvis.repair_product.engine import plan_from_event

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return plan_from_event(body.get("event") or body, text=str(body.get("text") or ""))

    @app.post("/api/repair/issues/{issue_id}/preview")
    def repair_preview(issue_id: str):
        from jarvis.repair_product.engine import preview_repair

        return preview_repair(issue_id)

    @app.post("/api/repair/issues/{issue_id}/approve")
    def repair_approve(issue_id: str):
        from jarvis.repair_product.engine import request_approval

        return request_approval(issue_id)

    @app.post("/api/repair/issues/{issue_id}/execute")
    async def repair_execute(issue_id: str, request: Request):
        from jarvis.repair_product.engine import execute_repair

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        approved = bool(body.get("approved") or body.get("confirm"))
        confirm_destructive = bool(body.get("confirm_destructive"))
        result = execute_repair(
            issue_id,
            approved=approved,
            confirm_destructive=confirm_destructive,
            actor=str(body.get("actor") or "jeff"),
        )
        status = 200 if result.get("ok") or result.get("approval_required") or result.get("needs_explicit_confirmation") else 400
        if result.get("approval_required") or result.get("needs_explicit_confirmation"):
            status = 409
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/repair/issues/{issue_id}/rollback")
    async def repair_rollback(issue_id: str, request: Request):
        from jarvis.repair_product.engine import rollback_issue

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return rollback_issue(issue_id, approved=bool(body.get("approved")), actor=str(body.get("actor") or "jeff"))

    @app.get("/api/repair/issues/{issue_id}/monitoring")
    def repair_monitoring(issue_id: str):
        from jarvis.repair_product.monitoring import status as mon_status

        return mon_status(issue_id)

    @app.post("/api/repair/monitoring/tick")
    def repair_monitoring_tick():
        from jarvis.repair_product.monitoring import tick

        return tick()

    @app.get("/api/repair/history")
    def repair_history(
        limit: int = 50,
        subsystem: str = "",
        result: str = "",
        q: str = "",
        successful: str = "",
        module_id: str = "",
        priority: str = "",
    ):
        from jarvis.repair_product import store

        succ: bool | None = None
        if successful in ("1", "true", "yes"):
            succ = True
        elif successful in ("0", "false", "no"):
            succ = False
        return {
            "ok": True,
            "history": store.list_history(
                limit=limit,
                subsystem=subsystem,
                result=result,
                q=q,
                successful=succ,
                module_id=module_id,
                priority=priority,
            ),
        }

    @app.get("/api/repair/learning")
    def repair_learning():
        from jarvis.repair_product import store

        return {"ok": True, "learning": store.learning_stats()}

    @app.get("/api/repair/knowledge")
    def repair_knowledge(q: str = "", subsystem: str = "", limit: int = 40):
        from jarvis.repair_product import knowledge

        return {"ok": True, "articles": knowledge.search(q, subsystem=subsystem, limit=limit)}

    @app.get("/api/repair/knowledge/article")
    def repair_knowledge_one(id: str = ""):
        from jarvis.repair_product import knowledge

        art = knowledge.get(id)
        if not art:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        return {"ok": True, "article": art}

    @app.get("/api/repair/reputation")
    def repair_reputation():
        from jarvis.repair_product import reputation

        return {"ok": True, "reputations": reputation.all_reputations()}

    @app.get("/api/repair/root-causes")
    def repair_root_causes():
        from jarvis.repair_product import root_causes

        return {"ok": True, "root_causes": root_causes.list_all()}

    @app.get("/api/repair/maintenance")
    def repair_maintenance_get():
        from jarvis.repair_product import maintenance

        return maintenance.status()

    @app.post("/api/repair/maintenance/enable")
    async def repair_maintenance_enable(request: Request):
        from jarvis.repair_product import maintenance

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return maintenance.enable(
            reason=str(body.get("reason") or "other"),
            note=str(body.get("note") or ""),
            actor=str(body.get("actor") or "jeff"),
        )

    @app.post("/api/repair/maintenance/disable")
    async def repair_maintenance_disable(request: Request):
        from jarvis.repair_product import maintenance

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return maintenance.disable(
            actor=str(body.get("actor") or "jeff"),
            run_verification=body.get("run_verification", True) is not False,
        )

    @app.post("/api/repair/export")
    async def repair_export(request: Request):
        from jarvis.repair_product.export_bundle import write_bundle

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return write_bundle(
            issue_id=str(body.get("issue_id") or ""),
            include_health=bool(body.get("include_health")),
            include_memory=bool(body.get("include_memory")),
            approved_sensitive=bool(body.get("approved_sensitive")),
        )

    @app.get("/api/repair/mission")
    def repair_mission():
        from jarvis.repair_product.mission_bridge import repair_mission_panel

        return repair_mission_panel()

    @app.get("/api/repair/auto-approve")
    def repair_auto_approve_get():
        from jarvis.repair_product import store

        return {"ok": True, "modules": store.auto_approve_list()}

    @app.post("/api/repair/auto-approve")
    async def repair_auto_approve_set(request: Request):
        from jarvis.repair_product import store

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        return {"ok": True, **store.set_auto_approve(list(body.get("modules") or []))}
