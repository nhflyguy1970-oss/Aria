"""Layouts product HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/layouts/product")
    def layouts_product_status():
        from jarvis.layouts_product.engine import product_status

        return product_status()

    @app.get("/api/layouts/home")
    def layouts_home():
        from jarvis.layouts_product.engine import home_payload

        return home_payload()

    @app.get("/api/layouts/catalog")
    def layouts_catalog(q: str = ""):
        from jarvis.layouts_product.apply import catalog_payload
        from jarvis.layouts_product.catalog import search_builtins

        cat = catalog_payload()
        if q.strip():
            cat["builtins"] = search_builtins(q)
            qlow = q.strip().lower()
            cat["customs"] = [c for c in cat.get("customs") or [] if qlow in str(c).lower()]
        return {"ok": True, **cat}

    @app.get("/api/layouts/open")
    def layouts_open(target: str = "", q: str = ""):
        from jarvis.layouts_product.apply import resolve_layout

        layout = resolve_layout(target or q)
        if not layout:
            return {"ok": False, "message": "Layout not found", "view": None}
        return {
            "ok": True,
            "layout_id": layout["id"],
            "label": layout["label"],
            "action": "apply",
            "open_action": {"type": "apply_layout", "layout_id": layout["id"]},
        }

    @app.post("/api/layouts/preview")
    async def layouts_preview(request: Request):
        body = await request.json()
        from jarvis.layouts_product.apply import preview_apply

        return preview_apply(str(body.get("layout_id") or ""), current=body.get("current"))

    @app.post("/api/layouts/apply")
    async def layouts_apply(request: Request):
        body = await request.json()
        from jarvis.layouts_product.apply import commit_apply

        return commit_apply(
            str(body.get("layout_id") or ""),
            current=body.get("current") if isinstance(body.get("current"), dict) else None,
            client_ok=bool(body.get("client_ok", True)),
            detail=str(body.get("detail") or ""),
        )

    @app.post("/api/layouts/undo")
    async def layouts_undo(request: Request):
        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.layouts_product.apply import undo_last

        return undo_last(current=body.get("current") if isinstance(body, dict) else None)

    @app.post("/api/layouts/save")
    async def layouts_save(request: Request):
        body = await request.json()
        from jarvis.layouts_product.apply import save_layout_from_client

        return save_layout_from_client(
            str(body.get("name") or ""),
            body.get("snapshot") if isinstance(body.get("snapshot"), dict) else {},
            overwrite=bool(body.get("overwrite")),
        )

    @app.delete("/api/layouts/custom/{layout_id}")
    def layouts_delete(layout_id: str, confirm: bool = False):
        from jarvis.layouts_product.store import delete_custom, load_settings, push_history

        settings = load_settings()
        if settings.get("confirm_delete", True) and not confirm:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "needs_confirm", "layout_id": layout_id},
            )
        ok = delete_custom(layout_id)
        if ok:
            push_history({"action": "delete", "layout_id": layout_id, "ok": True})
        return {"ok": ok, "layout_id": layout_id}

    @app.get("/api/layouts/settings")
    def layouts_settings_get():
        from jarvis.layouts_product.store import load_settings

        return {"ok": True, **load_settings()}

    @app.post("/api/layouts/settings")
    async def layouts_settings_set(request: Request):
        body = await request.json()
        from jarvis.layouts_product.store import save_settings

        return {"ok": True, **save_settings(body if isinstance(body, dict) else {})}

    @app.get("/api/layouts/restore")
    def layouts_restore_plan():
        from jarvis.layouts_product.restore import restore_plan

        return restore_plan()

    @app.get("/api/layouts/history")
    def layouts_history(limit: int = 40):
        from jarvis.layouts_product.store import load_history

        items = load_history(limit=limit)
        return {"ok": True, "count": len(items), "history": items}

    @app.get("/api/layouts/export")
    def layouts_export():
        from jarvis.layouts_product.apply import catalog_payload
        from jarvis.layouts_product.schema import SCHEMA_VERSION

        cat = catalog_payload()
        return {
            "ok": True,
            "format": "aria_layouts_export",
            "schema_version": SCHEMA_VERSION,
            "customs": cat.get("customs") or [],
            "settings": cat.get("settings") or {},
        }

    @app.post("/api/layouts/import")
    async def layouts_import(request: Request):
        body = await request.json()
        from jarvis.layouts_product.schema import make_snapshot, validate_snapshot
        from jarvis.layouts_product.store import load_customs, save_customs, save_settings

        if not isinstance(body, dict):
            return {"ok": False, "error": "invalid_body"}
        imported = 0
        customs = load_customs()
        for item in body.get("customs") or []:
            if not isinstance(item, dict):
                continue
            lid = str(item.get("id") or item.get("label") or "").strip().lower().replace(" ", "-")[:40]
            if not lid:
                continue
            snap = make_snapshot(item.get("snapshot") or item, label=str(item.get("label") or lid), kind="custom")
            if validate_snapshot(snap):
                continue
            customs[lid] = snap
            imported += 1
        save_customs(customs)
        if isinstance(body.get("settings"), dict):
            save_settings(body["settings"])
        return {"ok": True, "imported": imported}

    @app.get("/api/layouts/diagnostics")
    def layouts_diagnostics():
        from jarvis.layouts_product.diagnostics import health_summary
        from jarvis.layouts_product.restore import recovery_status

        return {"ok": True, "health": health_summary(), "recovery": recovery_status()}

    @app.get("/api/layouts/mission")
    def layouts_mission():
        from jarvis.layouts_product.mission_bridge import layouts_mission_panel

        return {"ok": True, **layouts_mission_panel()}

    @app.get("/api/layouts/suggest/project")
    def layouts_suggest_project(slug: str = ""):
        from jarvis.layouts_product.diagnostics import project_layout_suggestion

        return project_layout_suggestion(project_slug=slug)

    @app.get("/api/layouts/suggest/intent")
    def layouts_suggest_intent(q: str = ""):
        from jarvis.layouts_product.diagnostics import intent_coach

        return intent_coach(q)

    @app.get("/api/layouts/experimental/voice")
    def layouts_voice(layout_id: str = "coding"):
        from jarvis.layouts_product.diagnostics import voice_switch_script

        return voice_switch_script(layout_id)

    # Compat alias for older clients
    @app.get("/api/workspace-layouts/product")
    def layouts_compat_status():
        from jarvis.layouts_product.engine import product_status

        data = product_status()
        data["deprecated"] = "Use /api/layouts/* — Layouts product"
        return data
