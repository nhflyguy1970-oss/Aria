"""LAN access helpers — bind detection, client URLs, discovery."""

from __future__ import annotations

import ipaddress
import os
import secrets
import socket


def bind_host(default: str = "127.0.0.1") -> str:
    return (os.getenv("JARVIS_HOST", default) or default).strip()


def bind_port(default: int = 8765) -> int:
    return int(os.getenv("JARVIS_PORT", str(default)))


def is_wildcard_bind(host: str | None = None) -> bool:
    h = (host or bind_host()).lower()
    return h in ("0.0.0.0", "::", "::0")


def is_lan_bind(host: str | None = None) -> bool:
    h = (host or bind_host()).lower()
    if is_wildcard_bind(h):
        return True
    return h not in ("127.0.0.1", "localhost", "::1")


def client_host(host: str | None = None) -> str:
    """Host for local browser/health checks (never 0.0.0.0)."""
    h = (host or bind_host()).strip()
    if is_wildcard_bind(h):
        return "127.0.0.1"
    return h or "127.0.0.1"


def client_base_url(host: str | None = None, port: int | None = None) -> str:
    return f"http://{client_host(host)}:{bind_port() if port is None else int(port)}"


def _is_private_ipv4(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return addr.is_private and not addr.is_loopback


def list_lan_ips() -> list[str]:
    """Best-effort list of this machine's LAN IPv4 addresses."""
    found: set[str] = set()
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.settimeout(0.2)
        probe.connect(("8.8.8.8", 80))
        ip = probe.getsockname()[0]
        probe.close()
        if _is_private_ipv4(ip):
            found.add(ip)
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if _is_private_ipv4(ip):
                found.add(ip)
    except OSError:
        pass

    return sorted(found)


def generate_api_key(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)


def lan_status() -> dict:
    from jarvis.auth import api_key_enabled
    from jarvis.network_guard import allow_remote, guard_enabled
    from jarvis.rate_limit import rate_limit_enabled

    host = bind_host()
    port = bind_port()
    ips = list_lan_ips()
    local = client_base_url(host, port)
    connect_urls = [f"http://{ip}:{port}" for ip in ips]

    hints: list[str] = []
    from jarvis.branding import assistant_name

    name = assistant_name()
    if is_lan_bind(host):
        hints.append(f"{name} listens on all interfaces — use a LAN IP from another device.")
        if api_key_enabled():
            hints.append("Set the API key once in the browser; it stays in session storage.")
        else:
            hints.append(f"Set JARVIS_API_KEY before exposing {name} on your LAN.")
        hints.append("Keep Ollama on localhost (127.0.0.1:11434) — do not port-forward it.")
    else:
        hints.append("LAN access is off — set JARVIS_HOST=0.0.0.0 and JARVIS_API_KEY to enable.")

    from jarvis.auth import localhost_key_exempt

    return {
        "ok": True,
        "bind_host": host,
        "port": port,
        "local_url": local,
        "lan_ips": ips,
        "connect_urls": connect_urls,
        "lan_enabled": is_lan_bind(host),
        "api_key_required": api_key_enabled(),
        "api_key_localhost_exempt": localhost_key_exempt(),
        "network_guard": guard_enabled(),
        "allow_remote": allow_remote(),
        "rate_limit": rate_limit_enabled(),
        "ollama_localhost": True,
        "hints": hints,
    }


def require_api_key_for_lan_bind(host: str | None = None) -> None:
    """Refuse non-loopback binds without JARVIS_API_KEY unless explicitly overridden."""
    if not is_lan_bind(host):
        return
    if os.getenv("JARVIS_API_KEY", "").strip():
        return
    allow = os.getenv("JARVIS_ALLOW_INSECURE_LAN", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if allow:
        return
    raise SystemExit(
        "Refusing LAN bind without JARVIS_API_KEY. "
        "Set a key in data/jarvis.env, or set JARVIS_ALLOW_INSECURE_LAN=1 "
        "to override (not recommended)."
    )
