"""Optional API key authentication for LAN access."""

import ipaddress
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

HEALTH_EXEMPT_PATHS = frozenset({"/api/health"})


def is_exact_health_path(path: str) -> bool:
    return path in HEALTH_EXEMPT_PATHS


def api_key_enabled() -> bool:
    if os.getenv("JARVIS_API_KEY", "").strip():
        return True
    try:
        from jarvis.security.owner.provider_credentials import bound_owner_service, vault_has_entry

        return vault_has_entry(bound_owner_service(), "lan.api_key")
    except Exception:
        return False


def localhost_key_exempt() -> bool:
    """Loopback clients skip the key by default — LAN laptops still need it."""
    return os.getenv("JARVIS_API_KEY_LOCAL", "1").lower() not in ("0", "false", "no", "off")


def get_api_key() -> str:
    try:
        from jarvis.security.owner.provider_credentials import resolve_provider_secret

        got = resolve_provider_secret("lan_api_key")
        if got is not None:
            return (got.value or "").strip().strip('"').strip("'")
    except Exception:
        pass
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


def is_loopback_client(request: Request) -> bool:
    """True only for loopback addresses (127.0.0.1 / ::1)."""
    ip = client_ip(request)
    if not ip:
        return False
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def client_trust_zone(request: Request) -> str:
    """
    Auth trust zone: loopback | lan | remote.

    Architectural rule: only loopback is "local" for API-key exemption.
    Host LAN IPs are zone=lan and require a key when API auth is enabled.
    """
    ip = client_ip(request)
    if not ip:
        return "remote"
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "remote"
    if addr.is_loopback:
        return "loopback"
    if addr.is_private or addr.is_link_local:
        return "lan"
    return "remote"


def is_local_client(request: Request) -> bool:
    """
    Backward-compatible name used by middleware.

    As of auth zones (Batch A): means loopback only — NOT this host's LAN IP.
    Use client_trust_zone() for explicit zoning.
    """
    return is_loopback_client(request)


def api_key_required_for(request: Request) -> bool:
    if not api_key_enabled():
        return False
    zone = client_trust_zone(request)
    if zone == "loopback" and localhost_key_exempt():
        return False
    # lan + remote always require key when API key is configured
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
    import hmac

    key = get_api_key()
    if not key:
        # Configured but not retrievable (migrated + owner locked) → fail closed.
        # Do not treat "empty stored key" as open LAN.
        if api_key_enabled():
            return False
        return True
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        incoming = _normalize_incoming_key(auth[7:])
        try:
            if hmac.compare_digest(incoming, key):
                return True
        except (TypeError, ValueError):
            pass
    header_key = _normalize_incoming_key(request.headers.get("X-API-Key"))
    try:
        if header_key and hmac.compare_digest(header_key, key):
            return True
    except (TypeError, ValueError):
        pass
    if allow_query_api_key() or _media_gallery_file_get(request):
        q = _normalize_incoming_key(request.query_params.get("api_key"))
        try:
            return bool(q) and hmac.compare_digest(q, key)
        except (TypeError, ValueError):
            return False
    return False


class APIKeyMiddleware(BaseHTTPMiddleware):
    EXEMPT = {"/", "/favicon.ico", "/static"}

    async def dispatch(self, request: Request, call_next):
        if not api_key_enabled():
            return await call_next(request)
        path = request.url.path
        if path.startswith("/static") or path in self.EXEMPT:
            return await call_next(request)
        if path.startswith("/api/") and (
            is_exact_health_path(path)
            or path in ("/api/live", "/api/lan", "/api/automation/inbound")
        ):
            return await call_next(request)
        if path.startswith("/api/") and not api_key_required_for(request):
            return await call_next(request)
        if path.startswith("/api/") and not check_key(request):
            return JSONResponse(
                status_code=401, content={"ok": False, "message": "Invalid or missing API key"}
            )
        return await call_next(request)
