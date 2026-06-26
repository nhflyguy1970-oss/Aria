"""Block requests from outside the home LAN unless explicitly allowed."""

from __future__ import annotations

import ipaddress
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


def allow_remote() -> bool:
    return os.getenv("JARVIS_ALLOW_REMOTE", "").lower() in ("1", "true", "yes", "on")


def trust_proxy() -> bool:
    return os.getenv("JARVIS_TRUST_PROXY", "").lower() in ("1", "true", "yes", "on")


def guard_enabled() -> bool:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    if os.getenv("JARVIS_NETWORK_GUARD", "").lower() in ("0", "false", "no", "off"):
        return False
    return True


def _client_ip(request: Request) -> str:
    if trust_proxy():
        forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return request.client.host if request.client else ""


def _is_private_or_local(ip: str) -> bool:
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if addr.is_loopback or addr.is_private or addr.is_link_local:
        return True
    # Docker / pod bridges often use 172.16–31; covered by is_private.
    return False


def client_allowed(request: Request) -> bool:
    if not guard_enabled():
        return True
    if allow_remote():
        return True
    return _is_private_or_local(_client_ip(request))


class NetworkGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not client_allowed(request):
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=403,
                    content={
                        "ok": False,
                        "message": "Forbidden — Jarvis only accepts home-network clients. "
                        "Set JARVIS_ALLOW_REMOTE=1 only if you intend public exposure.",
                    },
                )
            return JSONResponse(status_code=403, content="Forbidden")
        return await call_next(request)
