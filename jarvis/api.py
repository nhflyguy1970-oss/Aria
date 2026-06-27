"""Voice P1 HTTP API."""

from __future__ import annotations

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/voice/settings")
    def voice_settings_get():
        from jarvis.voice_settings import load_voice_settings, stt_backend

        data = load_voice_settings()
        data["stt_backend"] = stt_backend()
        data["duplex_mode"] = data.get("duplex_mode") or "half"
        return {"ok": True, **data}

    @app.post("/api/voice/settings")
    async def voice_settings_post(request: Request):
        from jarvis.voice_settings import save_voice_settings

        body = await request.json()
        saved = save_voice_settings(body)
        return {"ok": True, **saved}

    @app.get("/api/voice/duplex")
    def voice_duplex():
        from jarvis.voice_duplex import duplex_status

        return {"ok": True, **duplex_status()}

    @app.get("/api/voice/cloud-live/status")
    def voice_cloud_live_status():
        from jarvis.cloud_live_voice import cloud_live_status

        return {"ok": True, **cloud_live_status()}

    @app.post("/api/voice/cloud-live/start")
    async def voice_cloud_live_start(request: Request):
        from jarvis.cloud_live_voice import start_live_session

        body = {}
        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = await request.json()
            except Exception:
                body = {}
        provider = str(body.get("provider") or "").strip() or None
        result = start_live_session(provider=provider)
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result

    @app.post("/api/voice/cloud-live/{session_id}/end")
    def voice_cloud_live_end(session_id: str):
        from jarvis.cloud_live_voice import end_live_session

        return end_live_session(session_id)

    @app.get("/api/voice/smoke")
    def voice_smoke_route():
        from jarvis.voice_smoke import run_voice_smoke

        return {"ok": True, **run_voice_smoke(assistant=assistant)}

    @app.get("/api/router/status")
    def router_status_route():
        from jarvis.local_router import router_status

        return {"ok": True, **router_status()}

    @app.get("/api/chat/sessions")
    def chat_sessions_list():
        from jarvis.chat_sessions import list_sessions

        return {"ok": True, "sessions": list_sessions()}

    @app.post("/api/chat/sessions")
    async def chat_sessions_create(request: Request):
        from jarvis.chat_sessions import create_session

        body = await request.json()
        sess = create_session(body.get("title") or "New chat", branch_id=body.get("branch_id"))
        return {"ok": True, "session": sess}

    @app.post("/api/chat/sessions/{session_id}/pin")
    async def chat_sessions_pin(session_id: str, request: Request):
        from jarvis.chat_sessions import pin_session

        body = await request.json()
        return {"ok": pin_session(session_id, bool(body.get("pinned", True)))}

    @app.post("/api/chat/sessions/{session_id}/rename")
    async def chat_sessions_rename(session_id: str, request: Request):
        from jarvis.chat_sessions import rename_session

        body = await request.json()
        title = (body.get("title") or "").strip()
        if not title:
            return JSONResponse(status_code=400, content={"ok": False, "message": "title required"})
        return {"ok": rename_session(session_id, title)}

    @app.post("/api/router/training/export")
    def router_training_export():
        from jarvis.router_training import export_training_jsonl

        path = export_training_jsonl()
        return {"ok": True, "path": str(path)}

    @app.websocket("/ws/events")
    async def ws_events(ws: WebSocket):
        from jarvis.ws_hub import subscribe, unsubscribe

        await ws.accept()
        subscribe(ws)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            unsubscribe(ws)
