"""Background print job queue with pre-print checklist."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.print_jobs")
STATE_FILE = DATA_DIR / "print_jobs_state.json"
_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def _load() -> None:
    global _jobs
    if not STATE_FILE.is_file():
        _jobs = {}
        return
    try:
        _jobs = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        _jobs = {}


def _save() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(_jobs, indent=2), encoding="utf-8")


_load()


def pre_print_checklist(
    *,
    bed_confirmed: bool = False,
    filament_confirmed: bool = False,
) -> dict[str, Any]:
    from jarvis.engineering.printer_store import get_printer
    from jarvis.engineering.slicer import slicer_status
    from jarvis.p3_flags import printer_enabled

    printer = get_printer()
    backend = (printer or {}).get("backend", "")
    slicers = slicer_status().get("slicers") or []
    checks: list[dict[str, Any]] = [
        {"name": "Printer enabled", "ok": printer_enabled()},
        {"name": "Slicer", "ok": bool(slicers), "detail": str(len(slicers))},
        {
            "name": "Printer configured",
            "ok": bool(printer),
            "detail": (printer or {}).get("name", ""),
        },
    ]
    if backend == "bambu_handoff":
        checks.append({"name": "Bambu handoff", "ok": True, "detail": "Studio / SD — no LAN mode"})
    else:
        checks.append({"name": "Bed clear", "ok": bed_confirmed, "detail": "confirm in GUI"})
        checks.append({"name": "Filament loaded", "ok": filament_confirmed, "detail": "confirm in GUI"})
    passed = sum(1 for c in checks if c.get("ok"))
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }


def list_jobs(limit: int = 20) -> list[dict[str, Any]]:
    rows = sorted(_jobs.values(), key=lambda j: j.get("created", 0), reverse=True)
    return rows[:limit]


def enqueue_print(
    gcode_path: str | Path,
    *,
    printer_id: str = "",
    bed_confirmed: bool = False,
    filament_confirmed: bool = False,
) -> dict[str, Any]:
    from jarvis.engineering.printer_store import get_printer

    printer = get_printer(printer_id or None)
    chk = pre_print_checklist(bed_confirmed=bed_confirmed, filament_confirmed=filament_confirmed)
    if not chk.get("ok"):
        return {"ok": False, "message": "Pre-print checklist incomplete", "checklist": chk}
    if not printer:
        return {"ok": False, "message": "No printer configured", "checklist": chk}
    jid = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[jid] = {
            "id": jid,
            "status": "queued",
            "gcode_path": str(gcode_path),
            "printer_id": printer_id,
            "created": time.time(),
            "message": "Queued (print client not started in this build)",
        }
        _save()
    return {"ok": True, "job_id": jid, "status": "queued"}
