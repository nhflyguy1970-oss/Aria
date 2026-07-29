"""Integrations product HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    """Register /api/integrations/product* and enhance /api/integrations/secrets."""

    @app.get("/api/integrations/product")
    def integrations_product_status():
        from jarvis.integrations_product.engine import product_status

        return product_status()

    @app.get("/api/integrations/product/home")
    def integrations_home(q: str = "", category: str = ""):
        from jarvis.integrations_product.engine import home_payload

        return home_payload(q=q, category=category)

    @app.get("/api/integrations/product/providers")
    def integrations_providers(q: str = "", category: str = "", configured: str = ""):
        from jarvis.integrations_product.providers import provider_matrix

        configured_only = configured.lower() in ("1", "true", "yes")
        return {"ok": True, "providers": provider_matrix(q=q, category=category, configured_only=configured_only)}

    @app.post("/api/integrations/product/test")
    async def integrations_test(request: Request):
        body = await request.json()
        from jarvis.integrations_product.providers import test_connection
        from jarvis.integrations_product.status_bus import set_integrations_state

        pid = str(body.get("id") or body.get("provider_id") or "")
        if not pid:
            return JSONResponse(status_code=400, content={"ok": False, "message": "id required"})
        set_integrations_state("testing", detail=pid)
        result = test_connection(pid)
        set_integrations_state("idle" if result.get("ok") else "error", detail=pid, error=str(result.get("error") or ""))
        return result

    @app.post("/api/integrations/product/test-all")
    async def integrations_test_all(request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.integrations_product.health import run_all_tests

        return run_all_tests(configured_only=bool(body.get("configured_only", True)))

    @app.get("/api/integrations/product/secrets")
    def integrations_secrets_product():
        from jarvis.integrations_product.secrets_bus import secrets_status

        return {"ok": True, **secrets_status(last4=True)}

    @app.post("/api/integrations/product/secrets")
    async def integrations_secrets_product_save(request: Request):
        body = await request.json()
        from jarvis.integrations_product.secrets_bus import save_secrets

        return save_secrets(body if isinstance(body, dict) else {})

    @app.post("/api/integrations/product/secrets/clear")
    async def integrations_secrets_clear(request: Request):
        body = await request.json()
        from jarvis.integrations_product.secrets_bus import clear_secret

        return clear_secret(str(body.get("field") or ""))

    @app.post("/api/integrations/product/secrets/rotate")
    async def integrations_secrets_rotate(request: Request):
        body = await request.json()
        from jarvis.integrations_product.secrets_bus import rotate_secret

        return rotate_secret(str(body.get("field") or ""), str(body.get("value") or ""))

    @app.get("/api/integrations/product/hygiene")
    def integrations_hygiene():
        from jarvis.integrations_product.secrets_bus import hygiene_report

        return hygiene_report()

    @app.get("/api/integrations/product/audit")
    def integrations_audit(limit: int = 50):
        from jarvis.integrations_product.secrets_bus import list_audit

        return {"ok": True, "audit": list_audit(limit)}

    @app.get("/api/integrations/product/usage")
    def integrations_usage(limit: int = 50, provider_id: str = ""):
        from jarvis.integrations_product.usage import list_usage

        return {"ok": True, "usage": list_usage(limit, provider_id=provider_id)}

    @app.get("/api/integrations/product/health")
    def integrations_health():
        from jarvis.integrations_product.health import health_summary

        return health_summary()

    @app.get("/api/integrations/product/diagnostics")
    def integrations_diagnostics():
        from jarvis.integrations_product.health import diagnostics

        return diagnostics()

    @app.get("/api/integrations/product/recovery")
    def integrations_recovery():
        from jarvis.integrations_product.health import recovery_status

        return recovery_status()

    @app.get("/api/integrations/product/mission")
    def integrations_mission():
        from jarvis.integrations_product.mission_bridge import integrations_mission_panel

        return integrations_mission_panel()

    @app.get("/api/integrations/product/settings")
    def integrations_settings_get():
        from jarvis.integrations_product.settings import load_settings

        return {"ok": True, **load_settings()}

    @app.post("/api/integrations/product/settings")
    async def integrations_settings_set(request: Request):
        body = await request.json()
        from jarvis.integrations_product.settings import save_settings

        return {"ok": True, **save_settings(body)}

    @app.post("/api/integrations/product/enable")
    async def integrations_enable(request: Request):
        body = await request.json()
        from jarvis.integrations_product.secrets_bus import set_provider_enabled

        return set_provider_enabled(str(body.get("id") or ""), bool(body.get("enabled", True)))

    @app.get("/api/integrations/product/export")
    def integrations_export(values: str = "0"):
        from jarvis.integrations_product.secrets_bus import export_bundle

        return export_bundle(include_values=values in ("1", "true", "yes"))

    @app.post("/api/integrations/product/import")
    async def integrations_import(request: Request):
        body = await request.json()
        from jarvis.integrations_product.secrets_bus import import_bundle

        return import_bundle(body, write_values=bool(body.get("write_values")))

    @app.get("/api/integrations/product/experimental")
    def integrations_experimental():
        from jarvis.integrations_product.experimental import experimental_status

        return experimental_status()

    @app.post("/api/integrations/product/experimental/nl-setup")
    async def integrations_nl_setup(request: Request):
        body = await request.json()
        from jarvis.integrations_product.experimental import nl_setup_suggest

        return nl_setup_suggest(str(body.get("prompt") or ""))

    @app.get("/api/integrations/product/bridges/voice")
    def integrations_bridge_voice():
        from jarvis.integrations_product.bridges import voice_bridge

        return voice_bridge()

    @app.get("/api/integrations/product/bridges/models")
    def integrations_bridge_models():
        from jarvis.integrations_product.bridges import models_bridge

        return models_bridge()

    @app.get("/api/integrations/product/bridges/engineering")
    def integrations_bridge_engineering():
        from jarvis.integrations_product.bridges import engineering_bridge

        return engineering_bridge()

    @app.get("/api/integrations/product/connectors")
    def integrations_connectors():
        from jarvis.intelligence.connectors import list_connectors

        return {
            "ok": True,
            "note": "Connector runtime is the External APIs architecture layer used by Integrations.",
            "connectors": list_connectors(),
        }

    # Backward-compatible secrets endpoints (enhanced)
    @app.get("/api/integrations/secrets")
    def integrations_secrets_get():
        from jarvis.integrations_product.secrets_bus import secrets_status

        return {"ok": True, **secrets_status(last4=True)}

    @app.post("/api/integrations/secrets")
    async def integrations_secrets_post(request: Request):
        from jarvis.integrations_product.secrets_bus import save_secrets

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "message": "JSON body required"})
        return save_secrets(body)


def register_routes(app, assistant) -> None:
    register_product_routes(app, assistant)
