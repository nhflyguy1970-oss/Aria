"""P3 feature flags — CAD lab and 3D printing."""

from __future__ import annotations

import os


def _env(name: str, default: str = "1") -> bool:
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "off")


def cad_enabled() -> bool:
    return _env("JARVIS_CAD", "1")


def printer_enabled() -> bool:
    return _env("JARVIS_PRINTER", "1")


def meshy_cad_enabled() -> bool:
    return _env("JARVIS_MESHY_CAD", "1")


def p3_flags() -> dict:
    from jarvis.p2_flags import p2_flags as _p2

    base = _p2()
    base.update(
        {
            "cad": cad_enabled(),
            "printer": printer_enabled(),
            "meshy_cad": meshy_cad_enabled(),
        }
    )
    return base
