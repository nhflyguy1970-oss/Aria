"""PIN lock middleware — require valid session for API when enabled."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from jarvis.auth import client_ip, is_exact_health_path
from jarvis.p4_flags import pin_lock_enabled
from jarvis.security.pin_lock import pin_configured, session_valid, touch_session
from jarvis.security.trusted_devices import is_trusted


class ProductionIsolationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        from jarvis.production_guard import reject_live_test_request

        msg = reject_live_test_request(request.method, dict(request.headers))
        if msg:
            return JSONResponse(status_code=403, content={"ok": False, "message": msg, "reason": "production_isolation"})
        return await call_next(request)


class PinLockMiddleware(BaseHTTPMiddleware):
    EXEMPT_PREFIXES = (
        "/static",
        "/favicon",
        "/api/live",
        "/api/ping",
        "/api/lan",
        "/api/automation/inbound",
    )
    EXEMPT_PATHS = frozenset({
        "/api/security/unlock",
        "/api/security/lock/status",
        "/api/security/session/touch",
    })

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not pin_lock_enabled() or not pin_configured():
            return await call_next(request)
        if not path.startswith("/api/"):
            return await call_next(request)
        if path in self.EXEMPT_PATHS or is_exact_health_path(path):
            return await call_next(request)
        # Memory settings mutate preferences — require unlock when PIN lock is on.
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return await call_next(request)
        token = (request.headers.get("X-Jarvis-Session") or "").strip()
        device_id = (request.headers.get("X-Jarvis-Device") or "").strip()
        if device_id and is_trusted(device_id, client_ip=client_ip(request)):
            return await call_next(request)
        if session_valid(token):
            touch_session(token)
            return await call_next(request)
        return JSONResponse(
            status_code=423,
            content={"ok": False, "message": "Locked — enter PIN or face", "locked": True},
        )
