"""Realtime voice status bus — in-process events + WebSocket fan-out."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "state": "idle",
    "detail": "",
    "partial": "",
    "ts": 0.0,
    "cloud_session": "",
    "error": "",
}


def get_voice_state() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def set_voice_state(
    state: str,
    *,
    detail: str = "",
    partial: str = "",
    cloud_session: str = "",
    error: str = "",
    publish: bool = True,
) -> dict[str, Any]:
    """Update canonical voice state and optionally push to WS clients."""
    state = (state or "idle").strip().lower()
    if state not in (
        "idle",
        "listening",
        "thinking",
        "speaking",
        "muted",
        "recording",
        "wake",
        "cloud-live",
        "error",
    ):
        state = "idle"
    with _lock:
        _state.update(
            {
                "state": state,
                "detail": detail or "",
                "partial": partial or "",
                "ts": time.time(),
                "cloud_session": cloud_session or _state.get("cloud_session") or "",
                "error": error or "",
            }
        )
        snapshot = dict(_state)

    try:
        from jarvis.events import emit

        emit(
            "voice_state",
            state=snapshot["state"],
            detail=snapshot["detail"],
            partial=snapshot["partial"],
            cloud_session=snapshot.get("cloud_session") or "",
            error=snapshot.get("error") or "",
        )
    except Exception:
        pass

    if publish:
        try:
            from jarvis.ws_hub import publish as ws_publish

            ws_publish(
                "voice_state",
                state=snapshot["state"],
                detail=snapshot["detail"],
                partial=snapshot["partial"],
                cloud_session=snapshot.get("cloud_session") or "",
                error=snapshot.get("error") or "",
            )
        except Exception:
            pass
    return snapshot


def emit_stt_partial(text: str, *, final: bool = False) -> None:
    text = (text or "").strip()
    if not text:
        return
    with _lock:
        _state["partial"] = "" if final else text
        _state["ts"] = time.time()
        if not final and _state.get("state") == "idle":
            _state["state"] = "listening"
    try:
        from jarvis.ws_hub import publish as ws_publish

        ws_publish("stt_partial", text=text, final=bool(final))
    except Exception:
        pass
    try:
        from jarvis.events import emit

        emit("stt_partial", text=text, final=bool(final))
    except Exception:
        pass
