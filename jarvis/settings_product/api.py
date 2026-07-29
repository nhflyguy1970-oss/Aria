"""Settings product HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/settings/product")
    def settings_product_status():
        from jarvis.settings_product.engine import product_status

        return product_status()

    @app.get("/api/settings/product/home")
    def settings_home(q: str = "", category: str = ""):
        from jarvis.settings_product.engine import home_payload

        return home_payload(q=q, category=category)

    @app.get("/api/settings/product/catalog")
    def settings_catalog(category: str = "", q: str = "", limit: int = 100):
        from jarvis.settings_product.catalog import catalog_by_category, search_catalog

        if q.strip():
            items = search_catalog(q.strip(), limit=min(limit, 100))
        else:
            items = catalog_by_category(category)[:limit]
        return {"ok": True, "count": len(items), "preferences": items}

    @app.get("/api/settings/product/search")
    def settings_search(q: str = "", limit: int = 24):
        from jarvis.settings_product.catalog import search_catalog

        items = search_catalog(q, limit=limit)
        return {"ok": True, "query": q, "count": len(items), "preferences": items}

    @app.get("/api/settings/product/open")
    def settings_open(pref: str = "", q: str = ""):
        from jarvis.settings_product.router import resolve_deep_link

        return resolve_deep_link(pref, query=q)

    @app.get("/api/settings/product/appearance")
    def settings_appearance_get():
        from jarvis.settings_product.appearance import load_appearance

        return {"ok": True, **load_appearance()}

    @app.post("/api/settings/product/appearance")
    async def settings_appearance_set(request: Request):
        body = await request.json()
        from jarvis.settings_product.appearance import save_appearance
        from jarvis.settings_product.history import record_change

        data = save_appearance(body if isinstance(body, dict) else {})
        record_change("appearance", detail=str(list((body or {}).keys())), category="appearance")
        return {"ok": True, **data}

    @app.post("/api/settings/product/appearance/migrate-theme")
    async def settings_migrate_theme(request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.settings_product.appearance import migrate_theme_hint

        return {"ok": True, **migrate_theme_hint(str(body.get("theme") or ""))}

    @app.get("/api/settings/product/global")
    def settings_global_get():
        from jarvis.settings_product.appearance import load_global

        return {"ok": True, **load_global()}

    @app.post("/api/settings/product/global")
    async def settings_global_set(request: Request):
        body = await request.json()
        from jarvis.settings_product.appearance import save_global
        from jarvis.settings_product.history import record_change

        data = save_global(body if isinstance(body, dict) else {})
        record_change("global", detail=str(list((body or {}).keys())), category="global")
        # Notifications owns delivery — mirror enable/soft_tips into prefs
        try:
            from jarvis.notifications_product.preferences import save_preferences

            patch = {}
            if isinstance(body, dict):
                if "notifications_enabled" in body:
                    patch["enabled"] = bool(body.get("notifications_enabled"))
                if "soft_tips" in body:
                    patch["soft_tips"] = bool(body.get("soft_tips"))
            if patch:
                save_preferences(patch)
        except Exception:
            pass
        return {"ok": True, **data}

    @app.get("/api/settings/product/profiles")
    def settings_profiles():
        from jarvis.settings_product.profiles import list_profiles

        return {"ok": True, **list_profiles()}

    @app.post("/api/settings/product/profiles")
    async def settings_profiles_save(request: Request):
        body = await request.json()
        from jarvis.settings_product.profiles import save_profile

        return save_profile(str(body.get("name") or "Profile"), profile_id=str(body.get("id") or ""))

    @app.post("/api/settings/product/profiles/activate")
    async def settings_profiles_activate(request: Request):
        body = await request.json()
        from jarvis.settings_product.profiles import activate_profile

        return activate_profile(str(body.get("id") or ""))

    @app.delete("/api/settings/product/profiles/{profile_id}")
    def settings_profiles_delete(profile_id: str):
        from jarvis.settings_product.profiles import delete_profile

        return delete_profile(profile_id)

    @app.get("/api/settings/product/export")
    def settings_export():
        from jarvis.settings_product.profiles import export_bundle

        return export_bundle()

    @app.post("/api/settings/product/import")
    async def settings_import(request: Request):
        body = await request.json()
        from jarvis.settings_product.profiles import import_bundle

        return import_bundle(body if isinstance(body, dict) else {})

    @app.post("/api/settings/product/reset")
    async def settings_reset(request: Request):
        body = await request.json()
        category = str(body.get("category") or "")
        from jarvis.settings_product.appearance import APPEARANCE_DEFAULTS, GLOBAL_DEFAULTS, save_appearance, save_global
        from jarvis.settings_product.history import record_change

        if category in ("appearance", "all"):
            save_appearance(dict(APPEARANCE_DEFAULTS))
            record_change("appearance.reset", detail="reset", category="appearance")
        if category in ("global", "all"):
            save_global(dict(GLOBAL_DEFAULTS))
            record_change("global.reset", detail="reset", category="global")
        if category not in ("appearance", "global", "all"):
            return JSONResponse(status_code=400, content={"ok": False, "error": "category must be appearance|global|all"})
        return {"ok": True, "reset": category}

    @app.get("/api/settings/product/history")
    def settings_history(limit: int = 30):
        from jarvis.settings_product.history import list_changes

        return {"ok": True, "history": list_changes(limit)}

    @app.get("/api/settings/product/coach")
    def settings_coach():
        from jarvis.settings_product.coach import coach_warnings

        return {"ok": True, "warnings": coach_warnings()}

    @app.get("/api/settings/product/health")
    def settings_health():
        from jarvis.settings_product.diagnostics import health_summary

        return health_summary()

    @app.get("/api/settings/product/diagnostics")
    def settings_diagnostics():
        from jarvis.settings_product.diagnostics import diagnostics

        return diagnostics()

    @app.get("/api/settings/product/recovery")
    def settings_recovery():
        from jarvis.settings_product.diagnostics import recovery_status

        return recovery_status()

    @app.get("/api/settings/product/mission")
    def settings_mission():
        from jarvis.settings_product.mission_bridge import settings_mission_panel

        return settings_mission_panel()

    @app.get("/api/settings/product/experimental")
    def settings_experimental():
        from jarvis.settings_product.experimental import experimental_status

        return experimental_status()

    @app.post("/api/settings/product/experimental/nl")
    async def settings_nl(request: Request):
        body = await request.json()
        from jarvis.settings_product.experimental import nl_configure_suggest

        return nl_configure_suggest(str(body.get("prompt") or ""))

    @app.post("/api/settings/product/experimental/hardware-defaults")
    def settings_hw_defaults():
        from jarvis.settings_product.experimental import hardware_aware_defaults

        return hardware_aware_defaults()


def register_routes(app, assistant) -> None:
    register_product_routes(app, assistant)
