"""Optional API key authentication for LAN access."""

import ipaddress
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


def api_key_enabled() -> bool:
    return bool(os.getenv("JARVIS_API_KEY", "").strip())


def localhost_key_exempt() -> bool:
    """Loopback clients skip the key by default — LAN laptops still need it."""
    return os.getenv("JARVIS_API_KEY_LOCAL", "1").lower() not in ("0", "false", "no", "off")


def get_api_key() -> str:
    return os.getenv("JARVIS_API_KEY", "").strip().strip('"').strip("'")


def _normalize_incoming_key(value: str | None) -> str:
    return (value or "").strip().strip('"').strip("'")


def allow_query_api_key() -> bool:
    """Query-string keys leak via logs/referrers — off by default."""
    return os.getenv("JARVIS_API_KEY_IN_QUERY", "").lower() in ("1", "true", "yes", "on")


def client_ip(request: Request) -> str:
    from jarvis.network_guard import trust_proxy

    if trust_proxy():
        forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if forwarded:
            return forwarded
    return request.client.host if request.client else ""


def is_local_client(request: Request) -> bool:
    """Loopback, or this host's own LAN IP (browser opened via http://10.x.x.x on the PC)."""
    ip = client_ip(request)
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if addr.is_loopback:
        return True
    try:
        from jarvis.lan import list_lan_ips

        if ip in list_lan_ips():
            return True
    except Exception:
        pass
    return False


def api_key_required_for(request: Request) -> bool:
    if not api_key_enabled():
        return False
    if localhost_key_exempt() and is_local_client(request):
        return False
    return True


def _media_gallery_file_get(request: Request) -> bool:
    """Read-only gallery file GETs (not list JSON endpoints)."""
    if request.method != "GET":
        return False
    path = request.url.path
    for prefix in ("/api/gallery/", "/api/video-gallery/", "/api/meme-gallery/"):
        if path.startswith(prefix) and path != prefix.rstrip("/"):
            return True
    return False


def check_key(request: Request) -> bool:
    key = get_api_key()
    if not key:
        return True
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer ") and _normalize_incoming_key(auth[7:]) == key:
        return True
    if _normalize_incoming_key(request.headers.get("X-API-Key")) == key:
        return True
    if allow_query_api_key() or _media_gallery_file_get(request):
        q = _normalize_incoming_key(request.query_params.get("api_key"))
        return q == key
    return False


class APIKeyMiddleware(BaseHTTPMiddleware):
    EXEMPT = {"/", "/favicon.ico", "/static"}

    async def dispatch(self, request: Request, call_next):
        if not api_key_enabled():
            return await call_next(request)
        path = request.url.path
        if path.startswith("/static") or path in self.EXEMPT:
            return await call_next(request)
        if path.startswith("/api/") and path in ("/api/health", "/api/live", "/api/lan", "/api/automation/inbound"):
            return await call_next(request)
        if path.startswith("/api/") and not api_key_required_for(request):
            return await call_next(request)
        if path.startswith("/api/") and not check_key(request):
            return JSONResponse(status_code=401, content={"ok": False, "message": "Invalid or missing API key"})
        return await call_next(request)
