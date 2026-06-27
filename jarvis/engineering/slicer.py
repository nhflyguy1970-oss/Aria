"""Slicer detection and headless G-code export."""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.engineering.printer_profiles import get_model

SETTINGS_FILE = DATA_DIR / "printer_settings.json"


def _load_settings() -> dict[str, Any]:
    if not SETTINGS_FILE.is_file():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged = {**_load_settings(), **data}
    SETTINGS_FILE.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def _orca_search_paths() -> list[str]:
    paths: list[str] = []
    env = (os.getenv("JARVIS_ORCASLICER_PATH") or "").strip()
    if env:
        paths.append(env)
    for name in ("orcaslicer", "orca-slicer", "OrcaSlicer"):
        w = shutil.which(name)
        if w:
            paths.append(w)
    home = Path.home()
    for pattern in (
        str(home / "bin" / "OrcaSlicer*"),
        str(home / "Applications" / "OrcaSlicer*.AppImage"),
        str(home / ".local" / "bin" / "orcaslicer"),
        str(home / "Downloads" / "OrcaSlicer*.AppImage"),
        "/opt/OrcaSlicer/orcaslicer",
        "/usr/bin/orcaslicer",
    ):
        for hit in glob.glob(pattern):
            if Path(hit).is_file():
                paths.append(hit)
    try:
        proc = subprocess.run(
            ["flatpak", "which", "com.softfever.OrcaSlicer"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            paths.append("flatpak run com.softfever.OrcaSlicer")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return list(dict.fromkeys(paths))


def _orca_system_roots() -> list[Path]:
    roots = [
        Path.home() / ".config" / "OrcaSlicer" / "system",
        Path.home() / ".var" / "app" / "com.softfever.OrcaSlicer" / "config" / "OrcaSlicer" / "system",
    ]
    custom = (os.getenv("JARVIS_ORCA_SYSTEM_DIR") or "").strip()
    if custom:
        roots.insert(0, Path(custom))
    return [r for r in roots if r.is_dir()]


def find_orca_profile_settings(printer_model: str) -> list[str]:
    """Return --load-settings paths for a known printer model."""
    m = get_model(printer_model)
    if not m:
        return []
    names = m.get("orca_names") or []
    found: list[str] = []
    for root in _orca_system_roots():
        for brand_dir in root.iterdir():
            if not brand_dir.is_dir():
                continue
            for preset_dir in brand_dir.iterdir():
                if not preset_dir.is_dir():
                    continue
                label = preset_dir.name
                if any(n.lower() in label.lower() for n in names):
                    for jf in sorted(preset_dir.glob("*.json")):
                        found.append(str(jf))
                    if found:
                        return found[:6]
    bundled = Path(__file__).parent / "orca_profiles" / (m.get("slicer_profile") or m["id"])
    if bundled.is_dir():
        for jf in sorted(bundled.glob("*.json")):
            found.append(str(jf))
    return found


def detect_slicers() -> list[dict[str, Any]]:
    candidates = [
        ("orcaslicer", "OrcaSlicer", _orca_search_paths()),
        ("prusa-slicer", "PrusaSlicer", [shutil.which(n) or "" for n in ("prusa-slicer", "PrusaSlicer")]),
        ("cura", "Cura", [shutil.which(n) or "" for n in ("cura", "ultimaker-cura")]),
    ]
    found: list[dict[str, Any]] = []
    for sid, label, paths in candidates:
        for path in paths:
            if path:
                found.append({"id": sid, "label": label, "path": path})
                break
    return found


def slicer_status() -> dict[str, Any]:
    slicers = detect_slicers()
    settings = _load_settings()
    return {
        "slicers": slicers,
        "default_slicer": settings.get("default_slicer") or (slicers[0]["id"] if slicers else ""),
        "profile": settings.get("profile", ""),
        "printer_model": settings.get("printer_model", ""),
        "orca_system_dirs": [str(p) for p in _orca_system_roots()],
    }


def _run_slicer_cmd(cmd: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess:
    if cmd[0].startswith("flatpak run"):
        parts = cmd[0].split()
        full = parts + cmd[1:]
    else:
        full = cmd
    return subprocess.run(full, capture_output=True, text=True, timeout=timeout)


def slice_stl(
    stl_path: str | Path,
    gcode_path: str | Path | None = None,
    *,
    slicer_id: str = "",
    printer_model: str = "",
) -> dict[str, Any]:
    stl_path = Path(stl_path)
    if not stl_path.is_file():
        return {"ok": False, "error": f"STL missing: {stl_path}"}
    slicers = {s["id"]: s for s in detect_slicers()}
    if not slicers:
        return {
            "ok": False,
            "error": "No slicer found — install OrcaSlicer (recommended for Bambu A1 / Creality KE) or set JARVIS_ORCASLICER_PATH",
        }
    settings = _load_settings()
    sid = (slicer_id or settings.get("default_slicer") or next(iter(slicers))).strip()
    slicer = slicers.get(sid) or next(iter(slicers.values()))
    model = (printer_model or settings.get("printer_model") or "").strip()
    gcode_path = Path(gcode_path or stl_path.with_suffix(".gcode"))
    gcode_path.parent.mkdir(parents=True, exist_ok=True)
    exe = slicer["path"]
    profile_settings = find_orca_profile_settings(model) if model else []
    try:
        if sid.startswith("orcaslicer") or "orca" in sid or exe.startswith("flatpak"):
            if exe.startswith("flatpak"):
                base = ["flatpak", "run", "com.softfever.OrcaSlicer"]
            else:
                base = [exe]
            cmd = [*base, "--export-gcode", "--export-slice", "--outputdir", str(gcode_path.parent), str(stl_path)]
            for p in profile_settings:
                cmd.extend(["--load-settings", p])
            proc = _run_slicer_cmd(cmd)
        else:
            cmd = [exe, "--export-gcode", str(gcode_path), str(stl_path)]
            proc = _run_slicer_cmd(cmd)
        log_path = DATA_DIR / "engineering" / "slicer.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as logf:
            logf.write(
                f"\n--- slice {stl_path.name} model={model or 'default'} ---\n"
                f"cmd: {' '.join(cmd)}\n{(proc.stdout or '')[-2000:]}\n{(proc.stderr or '')[-2000:]}\n"
            )
        if not gcode_path.is_file():
            alt = gcode_path.parent / (stl_path.stem + ".gcode")
            if alt.is_file():
                gcode_path = alt
        if not gcode_path.is_file():
            return {"ok": False, "error": (proc.stderr or proc.stdout or "slice failed")[:500]}
        return {
            "ok": True,
            "gcode_path": str(gcode_path),
            "slicer": slicer["label"],
            "printer_model": model,
            "profiles_used": profile_settings,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "slicer timed out"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
