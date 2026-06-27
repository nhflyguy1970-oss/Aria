"""Moonraker / Klipper HTTP client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _request(url: str, method: str = "GET", data: bytes | None = None, headers: dict | None = None) -> Any:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw.strip() else {}


def printer_status(host: str, *, api_key: str = "") -> dict[str, Any]:
    base = host.rstrip("/")
    headers = {}
    if api_key:
        headers["X-Api-Key"] = api_key
    try:
        data = _request(f"{base}/printer/objects/query?print_stats&heater_bed&extruder", headers=headers)
        result = data.get("result", {}).get("status", {})
        ps = result.get("print_stats", {})
        bed = result.get("heater_bed", {})
        ext = result.get("extruder", {})
        return {
            "ok": True,
            "state": ps.get("state", "unknown"),
            "filename": ps.get("filename", ""),
            "progress": ps.get("progress", 0),
            "bed_c": bed.get("temperature"),
            "nozzle_c": ext.get("temperature"),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def upload_gcode(host: str, gcode_path: str | Path, *, api_key: str = "") -> dict[str, Any]:
    path = Path(gcode_path)
    if not path.is_file():
        return {"ok": False, "error": f"G-code missing: {path}"}
    base = host.rstrip("/")
    boundary = "----aria-boundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if api_key:
        headers["X-Api-Key"] = api_key
    try:
        _request(f"{base}/server/files/upload", method="POST", data=body, headers=headers)
        return {"ok": True, "filename": path.name}
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": err[:300]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def start_print(host: str, filename: str, *, api_key: str = "") -> dict[str, Any]:
    base = host.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    payload = json.dumps({"filename": filename}).encode()
    try:
        _request(f"{base}/printer/print/start", method="POST", data=payload, headers=headers)
        return {"ok": True, "filename": filename}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
