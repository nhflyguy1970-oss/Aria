"""Product Automation API — Automation Home, rules, runs, search, webhook helpers."""

from __future__ import annotations

from typing import Any


def register_automation_product_routes(app, assistant) -> None:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    from jarvis.automation.pipeline_routes import register_pipeline_routes

    register_pipeline_routes(app, assistant)

    @app.get("/api/automation/home")
    def automation_home():
        from jarvis.automation.home import home_snapshot
        from jarvis.automation.migrate import migrate_storage

        migrate_storage()
        return home_snapshot()

    @app.post("/api/automation/migrate")
    def automation_migrate(force: bool = False):
        from jarvis.automation.migrate import migrate_storage

        return migrate_storage(force=force)

    @app.get("/api/automation/search")
    def automation_search(q: str = "", limit: int = 40):
        from jarvis.automation.home import search_automation

        return search_automation(q, limit=limit)

    @app.get("/api/automation/actions")
    def automation_actions(experimental: bool = False):
        from jarvis.automation.registry import registry_payload

        payload = registry_payload()
        if not experimental:
            payload["actions"] = [a for a in payload["actions"] if not a.get("experimental")]
        return payload

    @app.get("/api/automation/runs")
    def automation_runs(limit: int = 50, status: str = "", kind: str = "", q: str = ""):
        from jarvis.automation.history import list_runs

        return {
            "ok": True,
            "runs": list_runs(limit=limit, status=status or None, kind=kind or None, q=q),
        }

    @app.get("/api/automation/rules")
    def automation_rules_list():
        from jarvis.intelligence.automation_engine import list_rules, status

        st = status()
        return {"ok": True, "running": st.get("running"), "paused": st.get("paused"), "rules": list_rules()}

    @app.post("/api/automation/rules")
    async def automation_rules_upsert(request: Request):
        body = await request.json()
        from jarvis.intelligence.automation_engine import upsert_rule

        return {"ok": True, "rule": upsert_rule(body if isinstance(body, dict) else {})}

    @app.delete("/api/automation/rules/{rule_id}")
    def automation_rules_delete(rule_id: str):
        from jarvis.intelligence.automation_engine import delete_rule

        return delete_rule(rule_id)

    @app.post("/api/automation/rules/{rule_id}/run")
    async def automation_rules_run(rule_id: str, request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        dry_run = bool(body.get("dry_run"))
        from jarvis.intelligence.automation_engine import run_rule

        return run_rule(rule_id, dry_run=dry_run)

    @app.post("/api/automation/pause")
    async def automation_pause(request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.intelligence.automation_engine import set_paused

        return set_paused(bool(body.get("paused", True)))

    @app.post("/api/automation/engine/start")
    def automation_engine_start():
        from jarvis.intelligence.automation_engine import start_engine

        return start_engine()

    @app.get("/api/automation/rules/export")
    def automation_rules_export():
        from jarvis.intelligence.automation_engine import export_rules

        return export_rules()

    @app.post("/api/automation/rules/import")
    async def automation_rules_import(request: Request):
        body = await request.json()
        from jarvis.intelligence.automation_engine import import_rules

        return import_rules(body if isinstance(body, dict) else {}, replace=bool(body.get("replace")))

    @app.post("/api/automation/nl")
    async def automation_nl(request: Request):
        body = await request.json()
        from jarvis.automation.nl import parse_nl_automation

        return parse_nl_automation(str(body.get("text") or body.get("message") or ""))

    @app.post("/api/automation/nl/confirm")
    async def automation_nl_confirm(request: Request):
        body = await request.json()
        if not body.get("confirm"):
            return JSONResponse(status_code=400, content={"ok": False, "error": "confirm=true required"})
        draft = body.get("draft") or {}
        intent = body.get("intent")
        if intent == "pause_all":
            from jarvis.intelligence.automation_engine import list_rules, set_paused, upsert_rule

            set_paused(True)
            for r in list_rules():
                if r.get("enabled"):
                    upsert_rule({**r, "enabled": False})
            return {"ok": True, "paused": True, "message": "All automations paused / disabled"}
        if not draft:
            return JSONResponse(status_code=400, content={"ok": False, "error": "draft required"})
        draft["enabled"] = bool(body.get("enable", False))
        from jarvis.intelligence.automation_engine import upsert_rule

        rule = upsert_rule(draft)
        return {"ok": True, "rule": rule, "enabled": rule.get("enabled")}

    @app.get("/api/automation/suggestions")
    def automation_suggestions():
        from jarvis.automation.suggestions import list_suggestions

        return {"ok": True, "suggestions": list_suggestions()}

    @app.post("/api/automation/suggestions/{suggestion_id}/dismiss")
    def automation_sug_dismiss(suggestion_id: str):
        from jarvis.automation.suggestions import dismiss

        return dismiss(suggestion_id)

    @app.post("/api/automation/suggestions/{suggestion_id}/promote")
    async def automation_sug_promote(suggestion_id: str, request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.automation.suggestions import list_suggestions, mark_promoted
        from jarvis.intelligence.automation_engine import upsert_rule

        # Find suggestion
        sug = next((s for s in list_suggestions(include_dismissed=True) if s.get("id") == suggestion_id), None)
        if not sug:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not_found"})
        if not body.get("confirm"):
            return JSONResponse(status_code=400, content={"ok": False, "error": "confirm=true required"})
        wf = sug.get("workflow") or {}
        rule = upsert_rule(
            {
                "name": sug.get("title") or wf.get("name") or "Learned automation",
                "kind": "interval",
                "expression": str(body.get("interval_sec") or 86400),
                "action": "workflow_learned_run",
                "params": {"slug": wf.get("slug")},
                "enabled": bool(body.get("enable", False)),
            }
        )
        mark_promoted(suggestion_id)
        return {"ok": True, "rule": rule, "suggestion_id": suggestion_id}

    @app.post("/api/automation/mute")
    async def automation_mute(request: Request):
        body = await request.json()
        from jarvis.automation.mute import mute

        return mute(str(body.get("id") or ""), muted=bool(body.get("muted", True)))

    @app.get("/api/automation/webhook/status")
    def automation_webhook_status():
        from jarvis.automation.home import home_snapshot

        wh = (home_snapshot().get("health") or {}).get("webhook", {})
        return {"ok": True, **wh}

    @app.post("/api/automation/webhook/test")
    async def automation_webhook_test():
        """Diagnostics only — does not execute inbound actions."""
        from jarvis.home_assistant import automation_secret

        configured = bool(automation_secret())
        return {
            "ok": configured,
            "configured": configured,
            "message": (
                "Secret configured. Call POST /api/automation/inbound with X-Jarvis-Automation-Secret."
                if configured
                else "Missing JARVIS_AUTOMATION_SECRET"
            ),
            "header_required": "X-Jarvis-Automation-Secret",
            "query_secret_rejected": True,
        }

    @app.post("/api/automation/skills/{slug}/run")
    async def automation_skills_run(slug: str, request: Request):
        from jarvis.automation.activity_bridge import publish_run_event
        from jarvis.automation.execution import normalize_result
        from jarvis.skill_database import run_skill

        try:
            body = await request.json()
        except Exception:
            body = {}
        dry_run = bool(body.get("dry_run", False))
        result = run_skill(slug, dry_run=dry_run)
        norm = normalize_result(
            {"ok": result.get("ok", False), "result": result, "message": result.get("message")},
            dry_run=dry_run,
        )
        pub = publish_run_event(
            kind="skill",
            name=slug,
            status=norm["status"],
            target_id=slug,
            why=norm["why"],
            dry_run=dry_run,
            executed=norm["executed"],
            detail=result,
        )
        status = 200 if result.get("ok") or dry_run else 404
        return JSONResponse(
            status_code=status,
            content={**result, "execution": norm, "activity": pub.get("activity"), "run": pub.get("run")},
        )

    @app.post("/api/automation/workflows/{slug}/run")
    async def automation_workflows_run(slug: str, request: Request):
        from jarvis.automation.activity_bridge import publish_run_event
        from jarvis.automation.execution import normalize_result
        from jarvis.workflow_learning import run_workflow

        try:
            body = await request.json()
        except Exception:
            body = {}
        dry_run = bool(body.get("dry_run", False))
        if not dry_run and not body.get("confirm"):
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "status": "permission_required",
                    "error": "confirm=true required for real execution (or use dry_run=true)",
                },
            )
        result = run_workflow(slug, assistant=None if dry_run else assistant, dry_run=dry_run)
        norm = normalize_result(
            {"ok": result.get("ok", False), "result": result, "message": result.get("message")},
            dry_run=dry_run,
        )
        pub = publish_run_event(
            kind="learned_workflow",
            name=slug,
            status=norm["status"],
            target_id=slug,
            why=norm["why"],
            dry_run=dry_run,
            executed=norm["executed"],
            detail=result,
        )
        status_code = 200 if result.get("ok") or dry_run else 404
        return JSONResponse(
            status_code=status_code,
            content={**result, "execution": norm, "activity": pub.get("activity"), "run": pub.get("run")},
        )
