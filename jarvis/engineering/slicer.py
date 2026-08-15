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
# Flathub ships com.orcaslicer.OrcaSlicer; older docs used com.softfever.OrcaSlicer.
ORCA_FLATPAK_IDS = (
    "com.orcaslicer.OrcaSlicer",
    "com.softfever.OrcaSlicer",
)


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


def _flatpak_orca_commands() -> list[str]:
    """Return `flatpak run <id>` for installed OrcaSlicer apps.

    `flatpak which` is not a valid command — use `flatpak info`.
    """
    found: list[str] = []
    for app_id in ORCA_FLATPAK_IDS:
        try:
            proc = subprocess.run(
                ["flatpak", "info", app_id],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if proc.returncode == 0:
            found.append(f"flatpak run --command=orca-slicer {app_id}")
    return found


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
    paths.extend(_flatpak_orca_commands())
    return list(dict.fromkeys(paths))


def _orca_system_roots() -> list[Path]:
    roots = [
        Path.home() / ".config" / "OrcaSlicer" / "system",
        Path.home() / ".var" / "app" / "com.orcaslicer.OrcaSlicer" / "config" / "OrcaSlicer" / "system",
        Path.home() / ".var" / "app" / "com.softfever.OrcaSlicer" / "config" / "OrcaSlicer" / "system",
    ]
    custom = (os.getenv("JARVIS_ORCA_SYSTEM_DIR") or "").strip()
    if custom:
        roots.insert(0, Path(custom))
    return [r for r in roots if r.is_dir()]


def _profile_match_keys(printer_model: str) -> list[str]:
    m = get_model(printer_model)
    if not m:
        return []
    keys: list[str] = []
    for n in m.get("orca_names") or [m.get("label") or printer_model]:
        raw = str(n).lower()
        keys.append(raw)
        keys.append(raw.replace(" ", "").replace("-", ""))
    return list(dict.fromkeys(keys))


def _json_matches_printer(path: Path, keys: list[str]) -> bool:
    stem = path.stem.lower()
    compact = stem.replace(" ", "").replace("-", "")
    for k in keys:
        kc = k.replace(" ", "").replace("-", "")
        if k not in stem and kc not in compact:
            continue
        # "BBL A1" must not match "BBL A1M"
        if kc.endswith("a1") and "a1m" in compact and "a1m" not in kc:
            continue
        return True
    return False


def find_orca_profile_settings(printer_model: str) -> list[str]:
    """Return --load-settings paths (machine + process) for a known printer model.

    Orca 2.x stores `system/<Brand>/{machine,process,filament}/*.json`.
    """
    m = get_model(printer_model)
    if not m:
        return []
    keys = _profile_match_keys(printer_model)
    machine: list[str] = []
    process: list[str] = []
    for root in _orca_system_roots():
        for jf in sorted(root.rglob("*.json")):
            if not _json_matches_printer(jf, keys):
                continue
            parts = {p.lower() for p in jf.parts}
            if "machine" in parts:
                machine.append(str(jf))
            elif "process" in parts:
                process.append(str(jf))
        if machine:
            break
    machine.sort(key=lambda p: (0 if "0.4" in p.lower() else 1, len(p)))
    process.sort(
        key=lambda p: (
            0 if "0.20mm" in Path(p).name.lower() else 1,
            0 if "standard" in Path(p).name.lower() else 1,
        )
    )
    found = machine[:1] + process[:1]
    if found:
        return found
    bundled = Path(__file__).parent / "orca_profiles" / (m.get("slicer_profile") or m["id"])
    if bundled.is_dir():
        return [str(jf) for jf in sorted(bundled.glob("*.json"))[:6]]
    return []


def find_orca_filament(printer_model: str) -> list[str]:
    keys = _profile_match_keys(printer_model)
    for root in _orca_system_roots():
        cands = [
            p
            for p in sorted(root.rglob("*.json"))
            if "filament" in {x.lower() for x in p.parts}
            and "pla" in p.name.lower()
            and _json_matches_printer(p, keys)
        ]
        cands.sort(
            key=lambda p: (
                0 if "beta" not in p.name.lower() else 1,
                0 if "basic" in p.name.lower() else 1,
                0 if "generic pla" in p.name.lower() else 1,
                len(p.name),
            )
        )
        if cands:
            return [str(cands[0])]
    for root in _orca_system_roots():
        generic = [
            p
            for p in sorted(root.rglob("*.json"))
            if "filament" in {x.lower() for x in p.parts} and p.name.lower().endswith("generic pla.json")
        ]
        if generic:
            return [str(generic[0])]
    return []


def _flatpak_app_id(exe: str) -> str | None:
    for part in reversed(exe.split()):
        if part.count(".") >= 2 and not part.startswith("-"):
            return part
    return None


def _flatpak_filesystem_args(paths: list[Path]) -> list[str]:
    args: list[str] = []
    seen: set[str] = set()
    for p in paths:
        target = p if p.is_dir() else p.parent
        try:
            key = str(target.resolve())
        except OSError:
            key = str(target)
        if not key or key in seen:
            continue
        seen.add(key)
        args.append(f"--filesystem={key}")
    return args


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
    is_orca = sid.startswith("orcaslicer") or "orca" in sid or "orca" in exe.lower() or exe.startswith("flatpak")
    if is_orca and not model:
        return {
            "ok": False,
            "error": "Choose a printer model in Maker, then Slice.",
        }
    profile_settings = find_orca_profile_settings(model) if model else []
    filaments = find_orca_filament(model) if model else []
    if is_orca and not profile_settings:
        return {
            "ok": False,
            "error": f"No OrcaSlicer machine/process profile found for {model}. Pick the printer you actually use, or install its Orca presets.",
        }
    try:
        if is_orca:
            app_id = _flatpak_app_id(exe)
            if exe.startswith("flatpak") and app_id:
                binds = _flatpak_filesystem_args(
                    [stl_path, gcode_path.parent, *[Path(p) for p in profile_settings], *[Path(p) for p in filaments]]
                )
                base = ["flatpak", "run", "--command=orca-slicer", *binds, app_id]
            else:
                base = exe.split() if exe.startswith("flatpak") else [exe]
            cmd = [*base, "--slice", "0", "--outputdir", str(gcode_path.parent)]
            if profile_settings:
                cmd.extend(["--load-settings", ";".join(profile_settings)])
            if filaments:
                cmd.extend(["--load-filaments", ";".join(filaments)])
            cmd.append(str(stl_path))
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
            for alt in (
                gcode_path.parent / (stl_path.stem + ".gcode"),
                gcode_path.parent / "plate_1.gcode",
            ):
                if alt.is_file():
                    gcode_path = alt
                    break
            if not gcode_path.is_file():
                plates = sorted(gcode_path.parent.glob("plate_*.gcode"))
                if plates:
                    gcode_path = plates[0]
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
