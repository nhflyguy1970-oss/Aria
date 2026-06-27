"""CAD toolchain dependency status."""

from __future__ import annotations

import importlib.util
import shutil
from typing import Any


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def cad_status() -> dict[str, Any]:
    openscad_path = shutil.which("openscad") or ""
    build123d = _has_module("build123d")
    meshy = False
    cad_on = True
    printer_on = False
    meshy_cad = False
    try:
        from jarvis.p3_flags import cad_enabled, meshy_cad_enabled, printer_enabled

        cad_on = cad_enabled()
        printer_on = printer_enabled()
        meshy_cad = meshy_cad_enabled()
    except Exception:
        pass
    try:
        from jarvis.meshy_client import meshy_available

        meshy = meshy_available()
    except Exception:
        meshy = False
    try:
        from jarvis.engineering.slicer import slicer_status

        slicer = slicer_status()
    except Exception:
        slicer = {}
    return {
        "enabled": cad_on,
        "printer_enabled": printer_on,
        "meshy_cad": meshy_cad,
        "openscad": bool(openscad_path),
        "openscad_path": openscad_path,
        "build123d": build123d,
        "meshy": meshy,
        "ready": bool(openscad_path or build123d or meshy),
        "slicer": slicer,
    }
