"""Capabilities product HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    """Register /api/capabilities/product* and repair /api/registry/extensions."""

    @app.get("/api/registry/extensions")
    def registry_extensions():
        from jarvis.capabilities_product.registry import host_extensions_payload

        return host_extensions_payload()

    @app.get("/api/capabilities/product")
    def capabilities_product_status():
        from jarvis.capabilities_product.engine import product_status

        return product_status()

    @app.get("/api/capabilities/product/home")
    def capabilities_home(q: str = "", layer: str = "", category: str = "", trust: str = ""):
        from jarvis.capabilities_product.engine import home_payload

        return home_payload(q=q, layer=layer, category=category, trust=trust)

    @app.get("/api/capabilities/product/registry")
    def capabilities_registry(
        q: str = "",
        layer: str = "",
        category: str = "",
        trust: str = "",
        status: str = "",
        enabled: str = "",
    ):
        from jarvis.capabilities_product.registry import list_capabilities, registry_snapshot

        enabled_f = None
        if enabled.lower() in ("1", "true", "yes"):
            enabled_f = True
        elif enabled.lower() in ("0", "false", "no"):
            enabled_f = False
        items = list_capabilities(
            q=q, layer=layer, category=category, trust=trust, status=status, enabled=enabled_f
        )
        snap = registry_snapshot()
        return {**snap, "items": items, "filtered_count": len(items)}

    @app.get("/api/capabilities/product/capability/{cap_id:path}")
    def capabilities_get(cap_id: str):
        from jarvis.capabilities_product.registry import get_capability

        item = get_capability(cap_id)
        if not item:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not_found"})
        return {"ok": True, "capability": item}

    @app.post("/api/capabilities/product/enable")
    async def capabilities_enable(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.loader import enable_capability

        cap_id = str(body.get("id") or "")
        if not cap_id:
            return JSONResponse(status_code=400, content={"ok": False, "message": "id required"})
        return enable_capability(cap_id, load_now=bool(body.get("load_now", True)))

    @app.post("/api/capabilities/product/disable")
    async def capabilities_disable(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.loader import disable_capability

        cap_id = str(body.get("id") or "")
        if not cap_id:
            return JSONResponse(status_code=400, content={"ok": False, "message": "id required"})
        return disable_capability(cap_id)

    @app.post("/api/capabilities/product/load")
    async def capabilities_load(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.loader import load_all_enabled, load_capability

        if body.get("all"):
            return load_all_enabled()
        cap_id = str(body.get("id") or "")
        if not cap_id:
            return JSONResponse(status_code=400, content={"ok": False, "message": "id or all required"})
        return load_capability(cap_id, hot=bool(body.get("hot")))

    @app.post("/api/capabilities/product/hot-reload")
    async def capabilities_hot_reload(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.loader import hot_reload_capability

        return hot_reload_capability(str(body.get("id") or ""))

    @app.post("/api/capabilities/product/acknowledge")
    async def capabilities_ack(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.health import acknowledge

        return acknowledge(str(body.get("id") or ""), reenable=bool(body.get("reenable")))

    @app.get("/api/capabilities/product/health")
    def capabilities_health():
        from jarvis.capabilities_product.health import health_summary

        return health_summary()

    @app.get("/api/capabilities/product/diagnostics")
    def capabilities_diagnostics():
        from jarvis.capabilities_product.health import diagnostics

        return diagnostics()

    @app.get("/api/capabilities/product/recovery")
    def capabilities_recovery():
        from jarvis.capabilities_product.health import recovery_status

        return recovery_status()

    @app.get("/api/capabilities/product/mission")
    def capabilities_mission():
        from jarvis.capabilities_product.mission_bridge import capabilities_mission_panel

        return capabilities_mission_panel()

    @app.get("/api/capabilities/product/activity")
    def capabilities_activity(limit: int = 50):
        from jarvis.capabilities_product.history import list_activity

        return {"ok": True, "activity": list_activity(limit)}

    @app.get("/api/capabilities/product/settings")
    def capabilities_settings_get():
        from jarvis.capabilities_product.settings import load_settings

        return {"ok": True, **load_settings()}

    @app.post("/api/capabilities/product/settings")
    async def capabilities_settings_set(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.settings import save_settings

        return {"ok": True, **save_settings(body)}

    @app.get("/api/capabilities/product/policy")
    def capabilities_policy_get():
        from jarvis.capabilities_product import policy as cap_policy

        return {"ok": True, **cap_policy.export_policy()}

    @app.post("/api/capabilities/product/policy/import")
    async def capabilities_policy_import(request: Request):
        body = await request.json()
        from jarvis.capabilities_product import policy as cap_policy

        return {"ok": True, **cap_policy.import_policy(body, merge=bool(body.get("merge", True)))}

    @app.get("/api/capabilities/product/export")
    def capabilities_export(ids: str = ""):
        from jarvis.capabilities_product.engine import export_bundle

        id_list = [x.strip() for x in ids.split(",") if x.strip()] or None
        return export_bundle(id_list)

    @app.post("/api/capabilities/product/import")
    async def capabilities_import(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.engine import import_bundle

        return import_bundle(body, merge_policy=bool(body.get("merge", True)))

    @app.post("/api/capabilities/product/scaffold")
    async def capabilities_scaffold(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.scaffold import scaffold_capability

        try:
            return scaffold_capability(
                str(body.get("name") or ""),
                description=str(body.get("description") or ""),
                category=str(body.get("category") or "Utilities"),
                permissions=list(body.get("permissions") or []),
                under_project=bool(body.get("project")),
            )
        except Exception as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.get("/api/capabilities/product/experimental")
    def capabilities_experimental():
        from jarvis.capabilities_product.experimental import experimental_status

        return experimental_status()

    @app.get("/api/capabilities/product/experimental/mcp/export")
    def capabilities_mcp_export():
        from jarvis.capabilities_product.experimental import mcp_export_tools

        return mcp_export_tools()

    @app.post("/api/capabilities/product/experimental/mcp/import")
    async def capabilities_mcp_import(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.experimental import mcp_import_preview

        return mcp_import_preview(body.get("servers") or [])

    @app.post("/api/capabilities/product/experimental/nl-generate")
    async def capabilities_nl_generate(request: Request):
        body = await request.json()
        from jarvis.capabilities_product.experimental import nl_generate_stub

        return nl_generate_stub(str(body.get("prompt") or ""))

    @app.get("/api/capabilities/product/bridges/voice")
    def capabilities_bridge_voice():
        from jarvis.capabilities_product.bridges import voice_bridge

        return voice_bridge()

    @app.get("/api/capabilities/product/bridges/automation")
    def capabilities_bridge_automation():
        from jarvis.capabilities_product.bridges import automation_bridge

        return automation_bridge()

    @app.get("/api/capabilities/product/contributions")
    def capabilities_contributions():
        from jarvis.capabilities_product import contributions as c

        return {
            "ok": True,
            "routes": len(c.contribution_routes()),
            "tools": c.list_agent_tools(),
            "voice_intents": c.list_voice_intents(),
            "workflow_steps": c.list_workflow_steps(),
            "automation_actions": c.list_automation_actions(),
        }

    # Operator-facing alias — avoid marketing "plugins"
    @app.get("/api/capabilities/product/aliases/plugins")
    def capabilities_plugins_alias():
        from jarvis.capabilities_product.registry import list_capabilities

        return {
            "ok": True,
            "note": "Operator term is Capabilities. This alias lists SDK-layer capabilities only.",
            "capabilities": list_capabilities(layer="sdk"),
        }


def register_routes(app, assistant) -> None:
    register_product_routes(app, assistant)
