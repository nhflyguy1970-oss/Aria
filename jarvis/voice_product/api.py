"""Voice product HTTP API — profiles, recovery, speak, utterance, Mission Control."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/voice/product")
    def voice_product_status():
        from jarvis.voice_product.engine import product_status

        return product_status()

    @app.get("/api/voice/state")
    def voice_state_get():
        from jarvis.voice_product.status_bus import get_voice_state

        return {"ok": True, **get_voice_state()}

    @app.post("/api/voice/speak")
    async def voice_speak(request: Request):
        from jarvis.voice_product.engine import speak_text

        body = await request.json()
        text = (body.get("text") or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"ok": False, "message": "text required"})
        return speak_text(
            text,
            assistant=assistant,
            force=bool(body.get("force", True)),
            source=str(body.get("source") or "api"),
            queue=body.get("queue", True) is not False,
        )

    @app.post("/api/voice/stop")
    def voice_stop():
        from jarvis.voice_product.engine import stop_speaking

        return stop_speaking()

    @app.post("/api/voice/utterance")
    async def voice_utterance(request: Request):
        from jarvis.voice_product.engine import process_utterance

        body = await request.json()
        text = (body.get("text") or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"ok": False, "message": "text required"})
        return process_utterance(
            text,
            assistant=assistant,
            source=str(body.get("source") or "api"),
            speak=body.get("speak"),
        )

    @app.get("/api/voice/settings/unified")
    def voice_unified_get():
        from jarvis.voice_product.settings import load_unified_settings

        return {"ok": True, **load_unified_settings()}

    @app.post("/api/voice/settings/unified")
    async def voice_unified_set(request: Request):
        from jarvis.voice_product.settings import save_unified_settings

        body = await request.json()
        saved = save_unified_settings(body)
        return {"ok": True, **saved}

    @app.get("/api/voice/profiles")
    def voice_profiles_list():
        from jarvis.voice_product.profiles import active_profile_id, list_profiles

        return {"ok": True, "profiles": list_profiles(), "active": active_profile_id()}

    @app.post("/api/voice/profiles")
    async def voice_profiles_create(request: Request):
        from jarvis.voice_product.profiles import create_profile

        body = await request.json()
        return {"ok": True, "profile": create_profile(body)}

    @app.post("/api/voice/profiles/{profile_id}/activate")
    def voice_profiles_activate(profile_id: str):
        from jarvis.voice_product.profiles import activate_profile

        try:
            profile = activate_profile(profile_id)
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "profile": profile}

    @app.post("/api/voice/profiles/{profile_id}/duplicate")
    def voice_profiles_dup(profile_id: str):
        from jarvis.voice_product.profiles import duplicate_profile

        profile = duplicate_profile(profile_id)
        if not profile:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "profile": profile}

    @app.delete("/api/voice/profiles/{profile_id}")
    def voice_profiles_delete(profile_id: str):
        from jarvis.voice_product.profiles import delete_profile

        ok = delete_profile(profile_id)
        if not ok:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "deleted": profile_id}

    @app.get("/api/voice/profiles/export")
    def voice_profiles_export():
        from jarvis.voice_product.profiles import export_profiles

        return {"ok": True, **export_profiles()}

    @app.post("/api/voice/profiles/import")
    async def voice_profiles_import(request: Request):
        from jarvis.voice_product.profiles import import_profiles

        body = await request.json()
        return import_profiles(body)

    @app.get("/api/voice/recovery")
    def voice_recovery():
        from jarvis.voice_product.recovery import diagnose

        return diagnose()

    @app.post("/api/voice/recovery/action")
    async def voice_recovery_action(request: Request):
        from jarvis.voice_product.recovery import apply_recovery_action

        body = await request.json()
        return apply_recovery_action(str(body.get("action") or body.get("id") or ""))

    @app.get("/api/voice/intent/preview")
    def voice_intent_preview(q: str = ""):
        from jarvis.voice_product.intent_router import route_utterance

        route = route_utterance(q)
        return {"ok": True, "route": route, "falls_to_chat": route is None}

    @app.get("/api/voice/mission")
    def voice_mission():
        from jarvis.voice_product.mission_bridge import voice_mission_panel

        return {"ok": True, **voice_mission_panel()}

    @app.get("/api/voice/experimental")
    def voice_experimental():
        from jarvis.voice_product.experimental import experimental_status

        return experimental_status()

    @app.post("/api/voice/experimental/auto-tune")
    def voice_exp_auto_tune():
        from jarvis.voice_product.experimental import maybe_auto_tune_latency

        return maybe_auto_tune_latency()
