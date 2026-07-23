"""Outbound URL safety — block SSRF to loopback/private/metadata."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    """Raised when a URL is not safe for server-side fetch."""


_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata",
    }
)


def _host_is_blocked(host: str) -> bool:
    h = (host or "").strip().lower().rstrip(".")
    if not h or h in _BLOCKED_HOSTNAMES:
        return True
    if h.endswith(".localhost") or h.endswith(".local"):
        return True
    # Literal IPs
    try:
        ip = ipaddress.ip_address(h)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        pass
    # Resolve DNS and re-check (mitigate DNS rebinding to private IPs)
    try:
        infos = socket.getaddrinfo(h, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return True
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return True
    return False


def assert_safe_fetch_url(url: str, *, allow_http: bool = True) -> str:
    """Validate URL for server-side fetch. Returns normalized URL or raises UnsafeURLError."""
    text = (url or "").strip()
    if not text:
        raise UnsafeURLError("URL required")
    parsed = urlparse(text)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise UnsafeURLError("Only http(s) URLs are allowed")
    if scheme == "http" and not allow_http:
        raise UnsafeURLError("HTTPS required")
    host = parsed.hostname or ""
    if not host:
        raise UnsafeURLError("URL host required")
    if parsed.username or parsed.password:
        raise UnsafeURLError("URLs with credentials are not allowed")
    if _host_is_blocked(host):
        raise UnsafeURLError("URL host is not allowed (private/loopback/metadata)")
    return text


def is_safe_fetch_url(url: str, *, allow_http: bool = True) -> tuple[bool, str]:
    try:
        assert_safe_fetch_url(url, allow_http=allow_http)
        return True, ""
    except UnsafeURLError as exc:
        return False, str(exc)
