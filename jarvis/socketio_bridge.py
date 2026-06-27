"""Optional Socket.IO bridge alongside WebSocket hub."""

from __future__ import annotations

import logging

log = logging.getLogger("jarvis.socketio")


def socketio_available() -> bool:
    try:
        import socketio  # noqa: F401

        return True
    except ImportError:
        return False


def wrap_asgi_app(app):
    """Wrap FastAPI with Socket.IO when JARVIS_SOCKETIO=1."""
    from jarvis.p4_flags import socketio_enabled

    if not socketio_enabled() or not socketio_available():
        return app
    try:
        import socketio

        sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

        @sio.event
        async def connect(sid, environ):
            await sio.emit("hello", {"ok": True}, to=sid)

        @sio.event
        async def ping(sid, data):
            await sio.emit("pong", data or {}, to=sid)

        wrapped = socketio.ASGIApp(sio, other_asgi_app=app)
        log.info("Socket.IO wrapped at /socket.io")
        return wrapped
    except Exception as exc:
        log.warning("Socket.IO wrap failed: %s", exc)
        return app


def mount_socketio(app) -> bool:
    """Deprecated — use wrap_asgi_app at uvicorn startup."""
    return wrap_asgi_app(app) is not app
