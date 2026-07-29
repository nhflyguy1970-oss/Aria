"""Notifications product HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/notifications/product")
    def notifications_product_status():
        from jarvis.notifications_product.engine import product_status

        return product_status()

    @app.get("/api/notifications/home")
    def notifications_home():
        from jarvis.notifications_product.engine import home_payload

        return home_payload()

    @app.post("/api/notifications/publish")
    async def notifications_publish(request: Request):
        body = await request.json()
        from jarvis.notifications_product.pipeline import publish

        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "error": "invalid_body"})
        return publish(body)

    @app.post("/api/notifications/add")
    async def notifications_add(request: Request):
        """Compatibility alias."""
        body = await request.json()
        from jarvis.notifications_product.pipeline import add

        return add(body if isinstance(body, dict) else {})

    @app.get("/api/notifications/preferences")
    def notifications_prefs_get():
        from jarvis.notifications_product.preferences import load_preferences

        return {"ok": True, **load_preferences()}

    @app.post("/api/notifications/preferences")
    async def notifications_prefs_set(request: Request):
        body = await request.json()
        from jarvis.notifications_product.preferences import save_preferences

        return {"ok": True, **save_preferences(body if isinstance(body, dict) else {})}

    @app.get("/api/notifications/history")
    def notifications_history(limit: int = 100, severity: str = ""):
        from jarvis.notifications_product.history import load_history

        items = load_history(limit=limit, severity=severity)
        return {"ok": True, "count": len(items), "history": items}

    @app.get("/api/notifications/export")
    def notifications_export():
        from jarvis.notifications_product.history import export_history

        return {"ok": True, **export_history()}

    @app.post("/api/notifications/retention")
    def notifications_retention():
        from jarvis.notifications_product.history import retention_prune

        removed = retention_prune()
        return {"ok": True, "removed": removed}

    @app.get("/api/notifications/digest")
    def notifications_digest(kind: str = "today"):
        from jarvis.notifications_product.digest import build_digest

        return build_digest(kind)

    @app.get("/api/notifications/groups")
    def notifications_groups(by: str = "source"):
        from jarvis.notifications_product.digest import group_events

        return group_events(by=by)

    @app.get("/api/notifications/correlate")
    def notifications_correlate():
        from jarvis.notifications_product.correlation import correlate

        return correlate()

    @app.post("/api/notifications/drain")
    def notifications_drain():
        from jarvis.notifications_product.outbox import drain_all

        return drain_all()

    @app.get("/api/notifications/outbox")
    def notifications_outbox():
        from jarvis.notifications_product.outbox import outbox_status

        return {"ok": True, "outboxes": outbox_status()}

    @app.get("/api/notifications/diagnostics")
    def notifications_diagnostics():
        from jarvis.notifications_product.diagnostics import health_summary

        return {"ok": True, "health": health_summary()}

    @app.get("/api/notifications/mission")
    def notifications_mission():
        from jarvis.notifications_product.mission_bridge import notifications_mission_panel

        return {"ok": True, **notifications_mission_panel()}

    @app.get("/api/notifications/dashboard")
    def notifications_dashboard():
        from jarvis.notifications_product.dashboard_bridge import dashboard_notifications_summary

        return {"ok": True, **dashboard_notifications_summary()}

    @app.get("/api/notifications/open")
    def notifications_open(target: str = "inbox"):
        return {
            "ok": True,
            "action": "open_notifications",
            "filter": "unread" if target in ("unread", "errors") else "all",
            "open_action": {"type": "open_notifications", "filter": target},
        }

    @app.get("/api/notifications/experimental/voice")
    def notifications_voice():
        from jarvis.notifications_product.diagnostics import voice_failure_script

        return voice_failure_script()

    @app.get("/api/notifications/experimental/noise")
    def notifications_noise(title: str = "", severity: str = "info"):
        from jarvis.notifications_product.diagnostics import noise_classifier_hint

        return noise_classifier_hint(title, severity)

    @app.get("/api/notifications/routing")
    def notifications_routing_preview(severity: str = "warning", source: str = "system"):
        from jarvis.notifications_product.preferences import load_preferences, route_decision

        evt = {"severity": severity, "source": source, "category": source}
        return {"ok": True, "routing": route_decision(evt, load_preferences())}

    # Compat
    @app.get("/api/activity-center/product")
    def activity_compat():
        from jarvis.notifications_product.engine import product_status

        data = product_status()
        data["deprecated"] = "Use /api/notifications/* — Notifications product"
        return data
