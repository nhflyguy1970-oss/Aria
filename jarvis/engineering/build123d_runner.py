"""build123d parametric CAD runner."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HELLO_CUBE_SCRIPT = """
from build123d import BuildPart, Box, export_stl
with BuildPart() as p:
    Box(10, 10, 10)
export_stl(p.part, r"__OUT__")
"""


def build123d_available() -> bool:
    try:
        import build123d  # noqa: F401

        return True
    except ImportError:
        return False


def hello_cube(dest) -> dict[str, Any]:
    if not build123d_available():
        return {"ok": False, "error": "build123d not installed (pip install build123d)"}
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    script = HELLO_CUBE_SCRIPT.replace("__OUT__", str(dest_path).replace("\\", "\\\\"))
    return _run_script_text(script, dest_path)


def run_script_file(script_path, stl_out) -> dict[str, Any]:
    if not build123d_available():
        return {"ok": False, "error": "build123d not installed"}
    script_path = Path(script_path)
    stl_out = Path(stl_out)
    stl_out.parent.mkdir(parents=True, exist_ok=True)
    patched = script_path.read_text(encoding="utf-8")
    if "export_stl" not in patched:
        patched += f'\nfrom build123d import export_stl\nexport_stl(part, r"{stl_out}")\n'
    return _run_script_text(patched, stl_out)


def _run_script_text(script: str, stl_out: Path) -> dict[str, Any]:
    tmp = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
    tmp_path = tmp.name
    try:
        tmp.write(script)
        tmp.close()
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "build123d failed").strip()
            return {"ok": False, "error": err[:500]}
        if not stl_out.is_file():
            return {"ok": False, "error": "STL not produced"}
        return {"ok": True, "path": str(stl_out)}
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
