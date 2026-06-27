"""Gemini Live API WebSocket bridge (server-side proxy — API key never sent to browser)."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

log = logging.getLogger("jarvis.gemini_live")

GEMINI_WS_BASE = (
    "wss://generativelanguage.googleapis.com/ws/"
    "google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
)


def _api_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


def _model() -> str:
    raw = (os.getenv("JARVIS_GEMINI_LIVE_MODEL") or "gemini-2.0-flash-live-001").strip()
    return raw if raw.startswith("models/") else f"models/{raw}"


def _voice_name() -> str:
    return (os.getenv("JARVIS_GEMINI_LIVE_VOICE") or "Aoede").strip()


def _system_instruction() -> str:
    from jarvis.branding import assistant_intro, assistant_name

    custom = (os.getenv("JARVIS_GEMINI_LIVE_SYSTEM") or "").strip()
    if custom:
        return custom
    name = assistant_name()
    return (
        f"You are {name} ({assistant_intro().split('(')[-1].rstrip(')') if '(' in assistant_intro() else 'Adaptive Reasoning Intelligence Assistant'}). "
        f"You are a helpful voice assistant. Be concise and natural in speech."
    )


def build_setup_message() -> dict[str, Any]:
    return {
        "setup": {
            "model": _model(),
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": _voice_name()}}
                },
            },
            "systemInstruction": {"parts": [{"text": _system_instruction()}]},
            "inputAudioTranscription": {},
            "outputAudioTranscription": {},
        }
    }


def client_audio_to_gemini(data_b64: str) -> dict[str, Any]:
    return {
        "realtimeInput": {
            "audio": {
                "mimeType": "audio/pcm;rate=16000",
                "data": data_b64,
            }
        }
    }


def client_text_to_gemini(text: str) -> dict[str, Any]:
    return {"realtimeInput": {"text": text}}


def normalize_upstream_message(raw: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []

    out: list[dict[str, Any]] = []
    if data.get("setupComplete") is not None:
        out.append({"type": "ready"})

    sc = data.get("serverContent") or {}
    if sc.get("interrupted"):
        out.append({"type": "interrupted"})
    if sc.get("turnComplete"):
        out.append({"type": "turn_complete"})

    for key, role in (("inputTranscription", "input"), ("outputTranscription", "output")):
        block = data.get(key) or sc.get(key)
        if isinstance(block, dict):
            text = (block.get("text") or "").strip()
            if text:
                out.append({"type": "transcript", "role": role, "text": text})

    model_turn = sc.get("modelTurn") or {}
    for part in model_turn.get("parts") or []:
        if not isinstance(part, dict):
            continue
        inline = part.get("inlineData") or {}
        mime = (inline.get("mimeType") or "").lower()
        blob = inline.get("data")
        if blob and "audio" in mime:
            out.append({"type": "audio", "mimeType": inline.get("mimeType"), "data": blob})

    if data.get("toolCall"):
        out.append({"type": "tool_call", "payload": data.get("toolCall")})

    return out


def _client_to_gemini(text: str) -> str | None:
    try:
        msg = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(msg, dict):
        return None
    kind = msg.get("type")
    if kind == "audio" and msg.get("data"):
        return json.dumps(client_audio_to_gemini(str(msg["data"])))
    if kind == "text" and msg.get("text"):
        return json.dumps(client_text_to_gemini(str(msg["text"])))
    if kind == "ping":
        return None
    return None


async def run_gemini_live_bridge(client_ws: WebSocket, session_id: str) -> None:
    from jarvis.cloud_live_voice import get_live_session, mark_session_active

    session = get_live_session(session_id)
    if not session:
        await client_ws.close(code=4404, reason="session not found")
        return
    if session.get("provider") != "gemini_live":
        await client_ws.close(code=4403, reason="not a gemini session")
        return

    key = _api_key()
    if not key:
        await client_ws.send_json({"type": "error", "message": "GEMINI_API_KEY not set"})
        await client_ws.close(code=1011)
        return

    try:
        import websockets
    except ImportError:
        await client_ws.send_json(
            {"type": "error", "message": "pip install websockets (requirements-optional.txt)"}
        )
        await client_ws.close(code=1011)
        return

    url = f"{GEMINI_WS_BASE}?key={key}"
    await client_ws.accept()
    mark_session_active(session_id)

    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as upstream:
            await upstream.send(json.dumps(build_setup_message()))
            setup_ok = False
            deadline = asyncio.get_event_loop().time() + 15.0
            while not setup_ok and asyncio.get_event_loop().time() < deadline:
                raw = await asyncio.wait_for(upstream.recv(), timeout=8.0)
                for evt in normalize_upstream_message(raw):
                    if evt.get("type") == "ready":
                        setup_ok = True
                    await client_ws.send_json(evt)
                if setup_ok:
                    break

            if not setup_ok:
                await client_ws.send_json({"type": "error", "message": "Gemini setup timeout"})
                return

            async def client_loop() -> None:
                while True:
                    text = await client_ws.receive_text()
                    payload = _client_to_gemini(text)
                    if payload:
                        await upstream.send(payload)
                    elif json.loads(text).get("type") == "ping":
                        await client_ws.send_json({"type": "pong"})

            async def upstream_loop() -> None:
                async for raw in upstream:
                    for evt in normalize_upstream_message(raw):
                        await client_ws.send_json(evt)

            done, pending = await asyncio.wait(
                [asyncio.create_task(client_loop()), asyncio.create_task(upstream_loop())],
                return_when=asyncio.FIRST_EXCEPTION,
            )
            for task in pending:
                task.cancel()
            for task in done:
                exc = task.exception()
                if exc and not isinstance(exc, WebSocketDisconnect):
                    raise exc
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.warning("Gemini live bridge error: %s", exc)
        try:
            await client_ws.send_json({"type": "error", "message": str(exc)[:200]})
        except Exception:
            pass
    finally:
        from jarvis.cloud_live_voice import end_live_session

        end_live_session(session_id)
