"""Unified printer status / print dispatch by backend."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.engineering.printer_profiles import get_model


def printer_status(printer: dict[str, Any]) -> dict[str, Any]:
    backend = (printer.get("backend") or "moonraker").strip().lower()
    if backend == "bambu_handoff":
        from jarvis.engineering.bambu_handoff import printer_status as bambu_status

        return bambu_status(printer)
    if backend == "usb":
        from jarvis.engineering.usb_printer import list_serial_ports

        dev = printer.get("serial_device") or printer.get("host") or ""
        ports = {p["device"] for p in list_serial_ports()}
        return {
            "ok": dev in ports or bool(dev),
            "state": "usb" if dev in ports else "disconnected",
            "device": dev,
            "bed_c": None,
            "nozzle_c": None,
            "hint": "USB serial — use Start print after slice.",
        }
    from jarvis.engineering.moonraker_client import printer_status as moonraker_status

    host = printer.get("host") or ""
    if not host:
        model = get_model(printer.get("model") or "")
        return {
            "ok": False,
            "error": "Printer host not set — add IP (e.g. http://192.168.1.50:7125 for Creality KE + Moonraker).",
            "hint": (model or {}).get("handoff_hint", ""),
        }
    return moonraker_status(host, api_key=printer.get("api_key") or "")


def start_print_job(printer: dict[str, Any], gcode_path: str | Path) -> dict[str, Any]:
    backend = (printer.get("backend") or "moonraker").strip().lower()
    if backend == "bambu_handoff":
        from jarvis.engineering.bambu_handoff import handoff_gcode

        return handoff_gcode(printer, gcode_path)
    if backend == "usb":
        from jarvis.engineering.usb_printer import send_gcode

        return send_gcode(
            printer.get("serial_device") or printer.get("host") or "",
            str(gcode_path),
            baud=int(printer.get("baud") or 115200),
        )
    from jarvis.engineering.moonraker_client import start_print, upload_gcode

    host = printer.get("host") or ""
    key = printer.get("api_key") or ""
    up = upload_gcode(host, gcode_path, api_key=key)
    if not up.get("ok"):
        return up
    return start_print(host, up["filename"], api_key=key)
