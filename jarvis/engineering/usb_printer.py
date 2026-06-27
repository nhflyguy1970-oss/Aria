"""USB/serial printer fallback for simple G-code upload."""

from __future__ import annotations

import glob
import logging
import time
from pathlib import Path
from typing import Any

from jarvis.p5_flags import usb_printer_enabled

log = logging.getLogger("jarvis.usb_printer")


def serial_available() -> bool:
    try:
        import serial  # noqa: F401

        return True
    except ImportError:
        return False


def list_serial_ports() -> list[dict[str, Any]]:
    ports: list[dict[str, Any]] = []
    if not usb_printer_enabled():
        return ports
    try:
        import serial.tools.list_ports

        for p in serial.tools.list_ports.comports():
            ports.append({"device": p.device, "description": p.description or "", "hwid": p.hwid or ""})
    except Exception:
        for path in sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")):
            ports.append({"device": path, "description": "serial", "hwid": ""})
    return ports


def send_gcode(
    device: str,
    gcode_path: str | Path,
    *,
    baud: int = 115200,
    line_delay: float = 0.02,
) -> dict[str, Any]:
    if not usb_printer_enabled():
        return {"ok": False, "error": "USB printer disabled (JARVIS_USB_PRINTER=0)"}
    if not serial_available():
        return {"ok": False, "error": "pyserial not installed (pip install pyserial)"}
    import serial

    path = Path(gcode_path)
    if not path.is_file():
        return {"ok": False, "error": f"G-code missing: {path}"}
    dev = (device or "").strip()
    if not dev:
        ports = list_serial_ports()
        if not ports:
            return {"ok": False, "error": "No serial ports found"}
        dev = ports[0]["device"]
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    sent = 0
    try:
        with serial.Serial(dev, baudrate=baud, timeout=2) as ser:
            time.sleep(1.5)
            ser.reset_input_buffer()
            for ln in lines:
                if ln.startswith(";"):
                    continue
                ser.write((ln + "\n").encode("utf-8"))
                ser.flush()
                sent += 1
                time.sleep(line_delay)
        return {"ok": True, "device": dev, "lines_sent": sent}
    except Exception as exc:
        log.warning("USB print failed: %s", exc)
        return {"ok": False, "error": str(exc)[:300], "device": dev, "lines_sent": sent}
