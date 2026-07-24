"""Voice P1 HTTP API."""

from __future__ import annotations

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/voice/settings")
    def voice_settings_get():
        from jarvis.stt import stt_status
        from jarvis.voice_settings import load_voice_settings

        return {"ok": True, **load_voice_settings(), "stt": stt_status()}

    @app.post("/api/voice/settings")
    async def voice_settings_set(request: Request):
        from jarvis.stt import stt_status
        from jarvis.voice_settings import load_voice_settings, save_voice_settings

        body = await request.json()
        before = load_voice_settings().get("stt_backend")
        saved = save_voice_settings(body)
        note = ""
        if before != saved.get("stt_backend") and (body.get("stt_backend") or "").strip().lower() == "realtimestt":
            note = "RealTimeSTT not ready — kept Whisper"
        out = {"ok": True, **saved, "stt": stt_status()}
        if note:
            out["message"] = note
        return out

    @app.get("/api/voice/stt/status")
    def voice_stt_status_route():
        from jarvis.stt import stt_status

        return {"ok": True, **stt_status()}

    @app.get("/api/voice/smoke")
    @app.post("/api/voice/smoke")
    def voice_smoke_route():
        from jarvis.voice_smoke import run_voice_smoke

        return {"ok": True, **run_voice_smoke(assistant=assistant)}

    @app.get("/api/voice/latency")
    def voice_latency_route():
        from jarvis.voice_latency import measure_voice_round_trip, voice_latency_profile

        return {
            "ok": True,
            "profile": voice_latency_profile(),
            **measure_voice_round_trip(assistant=assistant),
        }

    @app.get("/api/voice/duplex")
    def voice_duplex_get():
        from jarvis.voice_duplex import duplex_status

        return {"ok": True, **duplex_status()}

    @app.get("/api/voice/cloud-live/status")
    def cloud_live_status_route():
        from jarvis.cloud_live_voice import cloud_live_status

        return {"ok": True, **cloud_live_status()}

    @app.post("/api/voice/cloud-live/start")
    async def cloud_live_start(request: Request):
        from jarvis.cloud_live_voice import start_live_session

        body = {}
        try:
            body = await request.json()
        except Exception:
            pass
        return start_live_session(provider=(body.get("provider") or "").strip())

    @app.post("/api/voice/cloud-live/{session_id}/end")
    def cloud_live_end(session_id: str):
        from jarvis.cloud_live_voice import end_live_session

        return end_live_session(session_id)

    @app.websocket("/ws/gemini-live/{session_id}")
    async def ws_gemini_live(ws: WebSocket, session_id: str):
        from jarvis.gemini_live_bridge import run_gemini_live_bridge

        await run_gemini_live_bridge(ws, session_id)

    @app.get("/api/voice/only")
    def voice_only_status():
        from jarvis.p1_flags import voice_only_enabled
        from jarvis.voice_only import prepare_voice_only_env

        prepare_voice_only_env()
        from jarvis import audio_wakeword

        return {
            "ok": True,
            "voice_only": voice_only_enabled(),
            "launch": "python main.py voice",
            "wakeword": audio_wakeword.status(),
        }

    @app.get("/api/router/status")
    def router_status_route():
        from jarvis.local_router import router_status
        from jarvis.stt import stt_status
        from jarvis.voice_duplex import duplex_mode as current_duplex
        from jarvis.voice_duplex import duplex_status

        return {
            "ok": True,
            **router_status(),
            "stt": stt_status(),
            "duplex_mode": current_duplex(),
            "duplex": duplex_status(),
        }

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

    @app.post("/api/router/training/export-functiongemma")
    def router_training_export_fg():
        from jarvis.router_training import export_functiongemma_jsonl

        path = export_functiongemma_jsonl()
        return {"ok": True, "path": str(path)}

    @app.post("/api/router/training/train")
    def router_training_train():
        from jarvis.router_training import train_router_model

        return train_router_model()

    @app.post("/api/router/training/train-functiongemma")
    def router_training_train_fg():
        from jarvis.router_training import train_functiongemma_router

        return train_functiongemma_router()

    @app.get("/api/router/functiongemma/status")
    def functiongemma_status_route():
        from jarvis.functiongemma_router import router_status

        return {"ok": True, **router_status()}

    @app.post("/api/router/functiongemma/warm")
    def functiongemma_warm_route():
        from jarvis.functiongemma_router import warm_model

        return warm_model()

    @app.get("/api/room-aliases")
    def room_aliases_get():
        from jarvis.room_aliases import list_aliases

        return {"ok": True, "aliases": list_aliases()}

    @app.post("/api/room-aliases")
    async def room_aliases_set(request: Request):
        import json
        from jarvis.config import DATA_DIR
        from jarvis.room_aliases import ALIASES_FILE

        body = await request.json()
        aliases = body.get("aliases") or {}
        ALIASES_FILE.parent.mkdir(parents=True, exist_ok=True)
        ALIASES_FILE.write_text(json.dumps({"aliases": aliases}, indent=2), encoding="utf-8")
        return {"ok": True, "aliases": aliases}

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
