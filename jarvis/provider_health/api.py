"""HTTP API for Provider Health."""

from __future__ import annotations


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.get("/api/provider/health")
    def provider_health():
        from jarvis.provider_health.engine import product_status

        return product_status()

    @app.get("/api/provider/stats")
    def provider_stats():
        from jarvis.provider_health.engine import stats_payload

        return stats_payload()

    @app.get("/api/provider/diagnostics")
    def provider_diagnostics():
        from jarvis.provider_health.engine import diagnostics

        return diagnostics()

    @app.get("/api/provider/providers")
    def provider_providers():
        from jarvis.provider_health.probe import list_providers

        return {"ok": True, "providers": list_providers()}

    @app.get("/api/provider/models")
    def provider_models(provider: str = "ollama"):
        from jarvis.provider_health.probe import list_models

        return list_models(provider)

    @app.post("/api/provider/recover")
    async def provider_recover(request: Request):
        from jarvis.provider_health.recovery import recover

        try:
            body = await request.json()
        except Exception:
            body = {}
        return recover(
            code=body.get("code") or "",
            message=body.get("message") or "",
            provider=body.get("provider") or "ollama",
            model=body.get("model") or "",
            got_progress=bool(body.get("got_progress")),
            auto=body.get("auto", True),
        )

    @app.post("/api/provider/restart")
    async def provider_restart(request: Request):
        from jarvis.provider_health.history import append_event
        from jarvis.provider_health.recovery import restart_provider

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not body.get("confirmed"):
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "confirmation_required", "message": "Pass confirmed=true to restart"},
            )
        out = restart_provider(body.get("provider") or "ollama")
        append_event({"kind": "operator_restart", **out})
        return out

    @app.get("/api/provider/prefs")
    def provider_prefs_get():
        from jarvis.provider_health.prefs import load_preferences

        return {"ok": True, **load_preferences()}

    @app.post("/api/provider/prefs")
    async def provider_prefs_set(request: Request):
        from jarvis.provider_health.prefs import save_preferences

        body = await request.json()
        return {"ok": True, **save_preferences(body if isinstance(body, dict) else {})}

    @app.post("/api/provider/classify")
    async def provider_classify(request: Request):
        from jarvis.provider_health.classify import classify_failure
        from jarvis.provider_health.probe import ping_provider

        try:
            body = await request.json()
        except Exception:
            body = {}
        ping = ping_provider(body.get("provider") or "ollama", force_probe=bool(body.get("probe", True)))
        return classify_failure(
            code=body.get("code") or "",
            message=body.get("message") or "",
            provider_alive=ping.get("alive"),
            got_progress=bool(body.get("got_progress")),
            probe=ping.get("probe") if isinstance(ping.get("probe"), dict) else None,
        )

    @app.get("/api/provider/history")
    def provider_history(limit: int = 50):
        from jarvis.provider_health.history import load_history

        return {"ok": True, "events": load_history(limit=min(max(limit, 1), 200))}

    @app.get("/api/provider/mission")
    def provider_mission():
        from jarvis.provider_health.mission_bridge import mission_panel

        return mission_panel()
