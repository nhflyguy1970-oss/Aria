"""OpenSCAD CAD runner — .scad to STL."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


def openscad_available() -> bool:
    return bool(shutil.which("openscad"))


def render_scad(scad_path: str | Path, stl_path: str | Path, *, timeout: int = 120) -> dict[str, Any]:
    scad_path = Path(scad_path)
    stl_path = Path(stl_path)
    exe = shutil.which("openscad")
    if not exe:
        return {"ok": False, "error": "OpenSCAD not installed"}
    if not scad_path.is_file():
        return {"ok": False, "error": f"SCAD missing: {scad_path}"}
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [exe, "-o", str(stl_path), str(scad_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0 or not stl_path.is_file():
            err = (proc.stderr or proc.stdout or "OpenSCAD failed").strip()
            return {"ok": False, "error": err[:500]}
        return {"ok": True, "path": str(stl_path), "scad": str(scad_path), "backend": "openscad"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "OpenSCAD timed out"}


def generate_scad_from_prompt(prompt: str, *, prior_scad: str = "") -> str:
    import jarvis.llm as llm

    system = (
        "You write OpenSCAD code only. No markdown fences. "
        "Output valid OpenSCAD that can render to STL. Use millimeters."
    )
    user = prompt.strip()
    if prior_scad:
        user = f"Edit this OpenSCAD:\n{prior_scad[:8000]}\n\nChange: {prompt}"
    raw = llm.ask_with_system(
        llm.coder_model(),
        system,
        user,
        options={"temperature": 0.2, "num_predict": 2000},
    )
    return _strip_code(raw)


def _strip_code(raw: str) -> str:
    text = (raw or "").strip()
    if "```" in text:
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def prompt_to_stl(
    prompt: str,
    scad_path: str | Path,
    stl_path: str | Path,
    *,
    prior_scad: str = "",
) -> dict[str, Any]:
    scad = generate_scad_from_prompt(prompt, prior_scad=prior_scad)
    scad_path = Path(scad_path)
    scad_path.parent.mkdir(parents=True, exist_ok=True)
    scad_path.write_text(scad, encoding="utf-8")
    result = render_scad(scad_path, stl_path)
    if result.get("ok"):
        result["scad"] = str(scad_path)
        result["scad_source"] = scad[:2000]
    return result
