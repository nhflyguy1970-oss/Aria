"""Printer registry — Moonraker, Bambu handoff, USB."""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.engineering.printer_profiles import default_row_for_model, get_model

STORE = DATA_DIR / "printers.json"


def _load() -> dict[str, Any]:
    if not STORE.is_file():
        return {"printers": [], "default": ""}
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"printers": [], "default": ""}


def _save(data: dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_printers() -> list[dict[str, Any]]:
    return list(_load().get("printers") or [])


def add_printer(
    *,
    name: str,
    host: str = "",
    backend: str = "moonraker",
    port: int = 0,
    api_key: str = "",
    model: str = "",
) -> dict[str, Any]:
    model_meta = get_model(model) if model else None
    if model_meta and not backend:
        backend = model_meta["backend"]
    if model_meta and backend == model_meta["backend"] and model_meta["backend"] == "bambu_handoff":
        row = default_row_for_model(model_meta["id"], name=name or model_meta["label"])
        if host:
            row["notes"] = host
    elif backend == "usb":
        if not host:
            raise ValueError("host required (serial device path)")
        row = {
            "id": name.lower().replace(" ", "-")[:40] or "usb-printer",
            "name": name or "USB printer",
            "host": host,
            "backend": "usb",
            "serial_device": host,
            "baud": port or 115200,
            "api_key": "",
        }
    else:
        host = (host or "").strip().rstrip("/")
        if not host and model_meta and model_meta["backend"] == "moonraker":
            raise ValueError("host required (printer IP, e.g. 192.168.1.50)")
        if not host and not model_meta:
            raise ValueError("host or model required")
        if host and not host.startswith("http"):
            port = port or (model_meta or {}).get("default_port", 7125)
            host = f"http://{host}:{port}"
        row = {
            "id": name.lower().replace(" ", "-")[:40] or (model_meta or {}).get("id", "printer"),
            "name": name or (model_meta or {}).get("label", host),
            "host": host,
            "backend": (backend or (model_meta or {}).get("backend") or "moonraker").strip().lower(),
            "api_key": api_key,
        }
        if model_meta:
            row["model"] = model_meta["id"]
    data = _load()
    printers = [p for p in data.get("printers") or [] if p.get("id") != row["id"]]
    printers.append(row)
    data["printers"] = printers
    if not data.get("default"):
        data["default"] = row["id"]
    _save(data)
    return row


def add_preset_printer(model_id: str, *, host: str = "", name: str = "") -> dict[str, Any]:
    """Quick-add a known printer model (Bambu A1, A1 Mini, Creality KE)."""
    return add_printer(name=name, host=host, model=model_id)


def get_printer(printer_id: str = "") -> dict[str, Any] | None:
    data = _load()
    pid = (printer_id or data.get("default") or "").strip()
    for p in data.get("printers") or []:
        if p.get("id") == pid:
            return p
    return (data.get("printers") or [None])[0]


def discover_mdns(
    service: str = "_moonraker._tcp.local.",
    timeout: float = 3.0,
    *,
    include_creality: bool = True,
) -> list[dict[str, Any]]:
    """LAN discovery — Moonraker (Creality KE after helper script). Skips Bambu (no LAN mode)."""
    found: list[dict[str, Any]] = []
    services = [service]
    if include_creality:
        services.append("_http._tcp.local.")

    def _add(name: str, host: str, port: int, backend: str = "moonraker") -> None:
        url = f"http://{host}:{port}"
        if url not in [f.get("host") for f in found]:
            found.append({"name": name, "host": url, "backend": backend, "model": "creality_ender3_v3_ke"})

    for svc in services:
        try:
            import subprocess

            proc = subprocess.run(
                ["avahi-browse", "-rt", svc],
                capture_output=True,
                text=True,
                timeout=timeout + 2,
            )
            for line in (proc.stdout or "").splitlines():
                if "hostname" in line.lower() and "=" in line:
                    host = line.split("=", 1)[-1].strip().strip(";")
                    if host:
                        _add(host.split(".")[0], host, 7125)
        except Exception:
            pass

    try:
        from zeroconf import ServiceBrowser, Zeroconf

        class _L:
            def __init__(self):
                self.items: list[dict[str, Any]] = []

            def add_service(self, zc, type_, name):
                info = zc.get_service_info(type_, name)
                if not info:
                    return
                host = socket.inet_ntoa(info.addresses[0])
                port = info.port or 7125
                self.items.append(
                    {"name": name.split(".")[0], "host": f"http://{host}:{port}", "backend": "moonraker"}
                )

        zc = Zeroconf()
        listener = _L()
        ServiceBrowser(zc, "_moonraker._tcp.local.", listener)
        import time

        time.sleep(timeout)
        zc.close()
        found.extend(listener.items)
    except Exception:
        pass
    return found
