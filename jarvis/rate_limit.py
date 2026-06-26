"""Simple per-IP rate limiting when Jarvis is exposed on LAN."""

from __future__ import annotations

import os
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_WINDOW = 60.0
_MAX_REQUESTS = int(os.getenv("JARVIS_RATE_LIMIT_PER_MIN", "180"))
_hits: dict[str, list[float]] = defaultdict(list)


def rate_limit_enabled() -> bool:
    if os.getenv("JARVIS_RATE_LIMIT", "").lower() in ("0", "false", "no", "off"):
        return False
    if os.getenv("JARVIS_RATE_LIMIT", "").lower() in ("1", "true", "yes", "on"):
        return True
    host = os.getenv("JARVIS_HOST", "127.0.0.1").strip()
    return host not in ("127.0.0.1", "localhost", "::1")


def _trust_proxy() -> bool:
    return os.getenv("JARVIS_TRUST_PROXY", "").lower() in ("1", "true", "yes", "on")


def _client_ip(request: Request) -> str:
    if _trust_proxy():
        forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return request.client.host if request.client else "unknown"


def _is_loopback(ip: str) -> bool:
    if not ip or ip == "unknown":
        return False
    if ip in ("127.0.0.1", "::1", "localhost"):
        return True
    if ip.startswith("127."):
        return True
    return ip == "::ffff:127.0.0.1"


def _allow(ip: str) -> bool:
    now = time.time()
    window = [t for t in _hits[ip] if now - t < _WINDOW]
    _hits[ip] = window
    if len(window) >= _MAX_REQUESTS:
        return False
    window.append(now)
    return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not rate_limit_enabled():
            return await call_next(request)
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        if path in ("/api/health", "/api/live", "/api/lan", "/api/ping", "/api/jarvis/restart-server"):
            return await call_next(request)
        ip = _client_ip(request)
        if _is_loopback(ip):
            return await call_next(request)
        if not _allow(ip):
            return JSONResponse(
                status_code=429,
                content={"ok": False, "message": "Rate limit exceeded — try again shortly"},
            )
        return await call_next(request)
