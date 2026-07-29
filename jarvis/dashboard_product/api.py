"""Dashboard product HTTP API."""

from __future__ import annotations

from fastapi import Request


def register_product_routes(app, assistant) -> None:
    @app.get("/api/dashboard/product")
    def dashboard_product_status():
        from jarvis.dashboard_product.engine import product_status

        return product_status(assistant=assistant)

    @app.get("/api/dashboard/home")
    def dashboard_home(category: str = "", stale_ok: bool = True):
        from jarvis.dashboard_product.engine import home_payload

        return home_payload(assistant=assistant, news_category=category, stale_ok=stale_ok)

    @app.get("/api/dashboard/widgets")
    def dashboard_widgets(q: str = "", limit: int = 50):
        from jarvis.dashboard_product.widgets import list_widget_defs, search_widgets

        items = search_widgets(q, limit=limit) if q.strip() else list_widget_defs()
        return {"ok": True, "count": len(items), "widgets": items}

    @app.get("/api/dashboard/open")
    def dashboard_open(target: str = "", q: str = ""):
        from jarvis.dashboard_product.router import resolve_deep_link

        return resolve_deep_link(target, query=q)

    @app.get("/api/dashboard/attention")
    def dashboard_attention():
        from jarvis.dashboard_product.attention import build_attention

        return {"ok": True, **build_attention(assistant=assistant)}

    @app.get("/api/dashboard/brief")
    def dashboard_brief():
        from jarvis.dashboard_product.brief import build_daily_brief

        return {"ok": True, **build_daily_brief(assistant=assistant)}

    @app.get("/api/dashboard/layout")
    def dashboard_layout_get():
        from jarvis.dashboard_product.cache import load_layout

        return {"ok": True, **load_layout()}

    @app.post("/api/dashboard/layout")
    async def dashboard_layout_set(request: Request):
        body = await request.json()
        from jarvis.dashboard_product.cache import save_layout
        from jarvis.dashboard_product.experimental import policy_layouts

        patch = body if isinstance(body, dict) else {}
        role = patch.get("role")
        if role and not patch.get("order"):
            roles = (policy_layouts().get("roles") or {}).get(role)
            if roles:
                patch = {**patch, "order": list(roles)}
        return {"ok": True, **save_layout(patch)}

    @app.get("/api/dashboard/diagnostics")
    def dashboard_diagnostics():
        from jarvis.dashboard_product.diagnostics import health_summary, recovery_status

        return {
            "ok": True,
            "health": health_summary(assistant=assistant),
            "recovery": recovery_status(),
        }

    @app.get("/api/dashboard/mission")
    def dashboard_mission():
        from jarvis.dashboard_product.mission_bridge import dashboard_mission_panel

        return {"ok": True, **dashboard_mission_panel(assistant=assistant)}

    @app.get("/api/dashboard/cache")
    def dashboard_cache():
        from jarvis.dashboard_product.cache import load_last_good

        cached = load_last_good()
        return {"ok": True, "present": cached is not None, "cache": cached}

    @app.get("/api/dashboard/experimental/voice-brief")
    def dashboard_voice_brief():
        from jarvis.dashboard_product.engine import home_payload
        from jarvis.dashboard_product.experimental import voice_home_brief_script

        home = home_payload(assistant=assistant, stale_ok=True)
        return voice_home_brief_script(home)

    @app.get("/api/dashboard/experimental/kiosk")
    def dashboard_kiosk():
        from jarvis.dashboard_product.experimental import kiosk_hints

        return {"ok": True, **kiosk_hints()}

    @app.get("/api/dashboard/experimental/policies")
    def dashboard_policies():
        from jarvis.dashboard_product.experimental import policy_layouts

        return {"ok": True, **policy_layouts()}
