"""Smart home API — Kasa, scene presets, unified devices."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/kasa/status")
    def kasa_status():
        from jarvis.kasa_devices import status

        return {"ok": True, **status()}

    @app.post("/api/kasa/discover")
    def kasa_discover_route():
        from jarvis.kasa_devices import discover

        return discover()

    @app.post("/api/kasa/control")
    async def kasa_control_route(request: Request):
        from jarvis.kasa_devices import control_device

        body = await request.json()
        target = str(body.get("target") or body.get("alias") or "").strip()
        action = str(body.get("action") or "toggle").strip().lower()
        if not target:
            return JSONResponse(status_code=400, content={"ok": False, "message": "target required"})
        ok, msg = control_device(
            target,
            action,
            brightness=body.get("brightness"),
            hue=body.get("hue"),
            saturation=body.get("saturation"),
        )
        return {"ok": ok, "message": msg}

    @app.post("/api/kasa/install")
    def kasa_install_route():
        try:
            from jarvis.kasa_install import ensure_kasa

            ensure_kasa(install=True)
            return {"ok": True, "message": "python-kasa install attempted"}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    @app.get("/api/devices")
    def unified_devices():
        from jarvis.device_router import list_unified_devices

        return {"ok": True, "devices": list_unified_devices()}

    @app.get("/api/scenes/presets")
    def scene_presets_list():
        from jarvis.scene_presets import list_presets

        return {"ok": True, "presets": list_presets()}

    @app.post("/api/scenes/presets/{preset_id}/activate")
    def scene_presets_activate(preset_id: str):
        from jarvis.scene_presets import activate_preset

        ok_flag, msg = activate_preset(preset_id)
        return {"ok": ok_flag, "message": msg}
