"""Bambu Lab print handoff — slice locally, send via Bambu Studio / SD (no LAN mode)."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.engineering.printer_profiles import get_model

HANDOFF_ROOT = DATA_DIR / "engineering" / "handoff"


def handoff_dir(printer: dict[str, Any]) -> Path:
    pid = printer.get("id") or printer.get("model") or "bambu"
    return HANDOFF_ROOT / pid


def printer_status(printer: dict[str, Any]) -> dict[str, Any]:
    """Status without LAN — last handoff file + Studio instructions."""
    model = get_model(printer.get("model") or "") or {}
    out_dir = handoff_dir(printer)
    latest = out_dir / "latest.gcode"
    meta_path = out_dir / "handoff.json"
    last_at = ""
    if meta_path.is_file():
        try:
            import json

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            last_at = meta.get("at", "")
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "ok": True,
        "state": "handoff",
        "mode": "no_lan",
        "model": model.get("label") or printer.get("name", "Bambu"),
        "hint": model.get("handoff_hint", "Send via Bambu Studio or SD card."),
        "last_gcode": str(latest) if latest.is_file() else "",
        "handoff_dir": str(out_dir),
        "last_handoff_at": last_at,
        "bed_c": None,
        "nozzle_c": None,
        "progress": 0,
        "filename": latest.name if latest.is_file() else "",
    }


def handoff_gcode(printer: dict[str, Any], gcode_path: str | Path) -> dict[str, Any]:
    """Copy G-code to handoff folder for Bambu Studio / SD transfer."""
    src = Path(gcode_path)
    if not src.is_file():
        return {"ok": False, "error": f"G-code missing: {src}"}
    out_dir = handoff_dir(printer)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "latest.gcode"
    shutil.copy2(src, dest)
    named = out_dir / src.name
    if named != dest:
        shutil.copy2(src, named)
    readme = out_dir / "SEND.txt"
    model = get_model(printer.get("model") or "") or {}
    readme.write_text(
        f"ARIA handoff — {model.get('label', 'Bambu printer')}\n\n"
        f"G-code: {dest.name}\n\n"
        f"{model.get('handoff_hint', '')}\n\n"
        "1. Open Bambu Studio\n"
        "2. File → Import → select latest.gcode (or drag onto plate)\n"
        "3. Send to printer (cloud bind) or export to SD card\n",
        encoding="utf-8",
    )
    import json

    meta = {"at": time.time(), "source": str(src), "gcode": str(dest)}
    (out_dir / "handoff.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "handoff_dir": str(out_dir),
        "gcode_path": str(dest),
        "readme": str(readme),
        "message": (
            f"G-code ready for **{printer.get('name', 'Bambu')}** — open `{dest}` in Bambu Studio "
            "or copy to SD card."
        ),
    }
