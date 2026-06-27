"""3D engineering lab — OpenSCAD parametric design, STL library, mesh stats."""

from __future__ import annotations

import json
import os
import re
import shutil
import struct
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from jarvis.config import DATA_DIR

ENGINEERING_DIR = DATA_DIR / "engineering"
META_FILE = ENGINEERING_DIR / "models.json"

DEFAULT_CUBE = (
    "// Jarvis parametric cube — edit dimensions\n"
    "$fn = 48;\n"
    "size = [40, 40, 20];\n"
    "cube(size, center=true);\n"
)

CAD_SYSTEM_PROMPT = (
    "You are a mechanical CAD assistant specializing in OpenSCAD for FDM 3D printing. "
    "Output ONLY valid OpenSCAD for ONE printable part. Rules: All dimensions in millimeters "
    "as parametric variables at the top. Minimum wall thickness 1.2mm (2mm for load-bearing parts). "
    "Part must sit flat on the print bed (Z=0); avoid floating geometry. Avoid unsupported overhangs "
    "beyond 45°; use chamfers or teardrop holes. Use $fn = 48 for curves (32 for large flat features). "
    "Use union, difference, hull, linear_extrude, rotate_extrude. Slip fit clearance +0.2mm; "
    "loose fit +0.4mm. No prose, no numbered options. Single ```openscad code fence only."
)

CAD_EDIT_SYSTEM_PROMPT = (
    "You are a mechanical CAD assistant editing OpenSCAD for FDM 3D printing. "
    "Return the COMPLETE updated OpenSCAD (not a diff). Keep parametric variables; preserve "
    "printability (walls ≥1.2mm, bed contact, clearances). No prose, no options. "
    "Single ```openscad fence only."
)

FLATPAK_OPENSCAD_REFS = ("org.openscad.OpenSCAD", "org.openscad.openscad-nightly")

_IMAGE_BLOCK_RE = re.compile(r"\b(image|illustration|picture|photo|drawing|painting)\b", re.I)
_EDIT_RE = re.compile(r"^edit\s+model\s+([a-z0-9]+)\s+(.+)$", re.I)


def engineering_model() -> str:
    explicit = os.getenv("JARVIS_ENGINEERING_MODEL", "").strip()
    if explicit:
        return explicit
    try:
        import jarvis.llm as llm

        return llm.coder_model()
    except Exception:
        return "qwen2.5-coder:7b"


def default_engineering_llm() -> Callable[..., str]:
    """LLM callable for design/edit (uses engineering_model + custom system prompts)."""

    def _chat(system: str, user: str, **kwargs: Any) -> str:
        import jarvis.llm as llm

        return llm.ask_with_system(
            engineering_model(),
            system,
            user,
            options={"temperature": 0.2, "num_predict": 2500, **(kwargs.get("options") or {})},
        )

    return _chat


def _ensure_dir() -> Path:
    ENGINEERING_DIR.mkdir(parents=True, exist_ok=True)
    return ENGINEERING_DIR


def _load_meta() -> dict[str, Any]:
    if not META_FILE.is_file():
        return {"models": []}
    try:
        data = json.loads(META_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("models"), list):
            return data
    except Exception:
        pass
    return {"models": []}


def _save_meta(data: dict[str, Any]) -> None:
    _ensure_dir()
    META_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _flatpak_openscad_ref() -> str | None:
    if not shutil.which("flatpak"):
        return None
    for ref in FLATPAK_OPENSCAD_REFS:
        try:
            r = subprocess.run(
                ["flatpak", "info", ref],
                capture_output=True,
                timeout=8,
                check=False,
            )
            if r.returncode == 0:
                return ref
        except Exception:
            continue
    return None


def _flatpak_export_bin(ref: str) -> str | None:
    for base in (
        Path("/var/lib/flatpak/exports/bin"),
        Path.home() / ".local/share/flatpak/exports/bin",
    ):
        for name in (ref, ref.split(".")[-1]):
            candidate = base / name
            if candidate.is_file():
                return str(candidate)
    return None


def _flatpak_filesystem_grant() -> str:
    explicit = os.getenv("JARVIS_OPENSCAD_FLATPAK_FS", "").strip()
    if explicit:
        return explicit
    try:
        return str(DATA_DIR.resolve().parent)
    except OSError:
        return str(DATA_DIR)


def _path_under_home(path: Path) -> bool:
    try:
        home = Path.home().resolve()
        resolved = path.resolve()
        if resolved == home:
            return True
        return home in resolved.parents
    except OSError:
        return False


def openscad_path() -> str | None:
    """Resolve native OpenSCAD binary (apt/snap), not Flatpak."""
    env_path = os.getenv("JARVIS_OPENSCAD_BIN", "").strip()
    if env_path and Path(env_path).is_file():
        return env_path
    found = shutil.which("openscad")
    if found:
        return found
    for candidate in ("/usr/bin/openscad", "/snap/bin/openscad"):
        if Path(candidate).is_file():
            return candidate
    return None


def openscad_status() -> dict[str, Any]:
    native = openscad_path()
    if native:
        return {"available": True, "backend": "native", "path": native}
    ref = _flatpak_openscad_ref()
    if ref:
        export = _flatpak_export_bin(ref)
        return {
            "available": True,
            "backend": "flatpak",
            "path": export or f"flatpak run {ref}",
            "flatpak_ref": ref,
        }
    return {"available": False, "backend": "none", "path": ""}


def openscad_render_cmd(scad_path: Path | str, stl_path: Path | str) -> list[str] | None:
    scad_path = Path(scad_path)
    stl_path = Path(stl_path)
    native = openscad_path()
    if native:
        return [native, "-o", str(stl_path), str(scad_path)]
    ref = _flatpak_openscad_ref()
    if not ref:
        return None
    cmd = ["flatpak", "run"]
    grant = _flatpak_filesystem_grant()
    if grant:
        cmd.extend(["--filesystem", grant])
    for p in (scad_path, stl_path, scad_path.parent, stl_path.parent):
        if _path_under_home(Path(p)):
            cmd.extend(["--filesystem", str(Path(p).resolve())])
    cmd.extend([ref, "-o", str(stl_path), str(scad_path)])
    return cmd


def _extract_scad(raw: str) -> str:
    text = (raw or "").strip()
    fence = re.search(r"```(?:openscad|scad)?\s*\n(.*?)```", text, re.I | re.S)
    if fence:
        text = fence.group(1).strip()
    elif "```" in text:
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    lines = []
    for line in text.splitlines():
        if re.match(r"^\s*(option\s+\d+|here are|choose one)\b", line, re.I):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _model_paths(model_id: str) -> dict[str, Path]:
    root = _ensure_dir()
    return {
        "scad": root / f"{model_id}.scad",
        "stl": root / f"{model_id}.stl",
    }


def _write_fallback_stl(stl_path: Path) -> None:
    """Minimal binary STL cube when OpenSCAD is unavailable."""
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    verts = [
        (-5, -5, -5),
        (5, -5, -5),
        (5, 5, -5),
        (-5, 5, -5),
        (-5, -5, 5),
        (5, -5, 5),
        (5, 5, 5),
        (-5, 5, 5),
    ]
    faces = [
        (0, 1, 2),
        (0, 2, 3),
        (4, 6, 5),
        (4, 7, 6),
        (0, 4, 5),
        (0, 5, 1),
        (2, 6, 7),
        (2, 7, 3),
        (0, 3, 7),
        (0, 7, 4),
        (1, 5, 6),
        (1, 6, 2),
    ]

    def _normal(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> tuple[float, float, float]:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        mag = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        return nx / mag, ny / mag, nz / mag

    buf = bytearray(80)
    buf.extend(struct.pack("<I", len(faces)))
    for i0, i1, i2 in faces:
        a, b, c = verts[i0], verts[i1], verts[i2]
        nx, ny, nz = _normal(a, b, c)
        buf.extend(struct.pack("<3f", nx, ny, nz))
        buf.extend(struct.pack("<3f", *a))
        buf.extend(struct.pack("<3f", *b))
        buf.extend(struct.pack("<3f", *c))
        buf.extend(struct.pack("<H", 0))
    stl_path.write_bytes(bytes(buf))


def save_model(
    *,
    name: str,
    scad: str,
    prompt: str = "",
    model_id: str | None = None,
) -> dict[str, Any]:
    mid = (model_id or "").strip() or uuid.uuid4().hex[:10]
    paths = _model_paths(mid)
    paths["scad"].write_text(scad, encoding="utf-8")
    now = time.time()
    row = {
        "id": mid,
        "name": name or mid,
        "prompt": prompt[:2000],
        "scad": scad,
        "scad_path": str(paths["scad"]),
        "stl_path": "",
        "has_stl": False,
        "created": now,
        "updated": now,
    }
    data = _load_meta()
    models = [m for m in data.get("models", []) if m.get("id") != mid]
    models.insert(0, row)
    data["models"] = models
    _save_meta(data)
    return row


def list_models(limit: int = 50) -> list[dict[str, Any]]:
    rows = list(_load_meta().get("models") or [])
    out: list[dict[str, Any]] = []
    for row in rows[:limit]:
        mid = row.get("id") or ""
        paths = _model_paths(mid) if mid else {}
        stl_path = Path(str(row.get("stl_path") or paths.get("stl") or ""))
        has_stl = bool(row.get("has_stl")) or stl_path.is_file()
        out.append(
            {
                **row,
                "has_stl": has_stl,
                "stl_path": str(stl_path) if has_stl else "",
            }
        )
    return out


def get_model(model_id: str) -> dict[str, Any] | None:
    for row in list_models(limit=500):
        if row.get("id") == model_id:
            paths = _model_paths(model_id)
            scad = row.get("scad") or ""
            if not scad and paths["scad"].is_file():
                scad = paths["scad"].read_text(encoding="utf-8")
            return {**row, "scad": scad}
    return None


def _update_model(model_id: str, **fields: Any) -> dict[str, Any] | None:
    data = _load_meta()
    for row in data.get("models") or []:
        if row.get("id") != model_id:
            continue
        row.update({k: v for k, v in fields.items() if v is not None})
        row["updated"] = time.time()
        _save_meta(data)
        return row
    return None


def render_stl(model_id: str) -> tuple[bool, str, str]:
    model = get_model(model_id)
    if not model:
        return False, "Model not found", ""
    paths = _model_paths(model_id)
    scad = model.get("scad") or DEFAULT_CUBE
    paths["scad"].write_text(scad, encoding="utf-8")
    cmd = openscad_render_cmd(paths["scad"], paths["stl"])
    if cmd:
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
            if proc.returncode == 0 and paths["stl"].is_file():
                rel = f"engineering/{model_id}.stl"
                _update_model(
                    model_id,
                    stl_path=str(paths["stl"]),
                    has_stl=True,
                )
                return True, "STL rendered", rel
            err = (proc.stderr or proc.stdout or "OpenSCAD failed").strip()
            return False, err[:500], ""
        except subprocess.TimeoutExpired:
            return False, "OpenSCAD timed out", ""
        except Exception as exc:
            return False, str(exc), ""
    _write_fallback_stl(paths["stl"])
    rel = f"engineering/{model_id}.stl"
    _update_model(model_id, stl_path=str(paths["stl"]), has_stl=True)
    return True, "Built-in STL export (OpenSCAD unavailable)", rel


def edit_and_render(
    model_id: str,
    prompt: str,
    *,
    llm_chat: Callable[..., str] | None = None,
) -> dict[str, Any]:
    model = get_model(model_id)
    if not model:
        return {"ok": False, "message": "Model not found"}
    chat = llm_chat or default_engineering_llm()
    prior = model.get("scad") or DEFAULT_CUBE
    raw = chat(CAD_EDIT_SYSTEM_PROMPT, f"Current OpenSCAD:\n{prior}\n\nChange: {prompt.strip()}")
    scad = _extract_scad(raw)
    if not scad:
        return {"ok": False, "message": "No OpenSCAD in model response"}
    paths = _model_paths(model_id)
    paths["scad"].write_text(scad, encoding="utf-8")
    _update_model(model_id, scad=scad, scad_path=str(paths["scad"]), prompt=prompt[:2000])
    ok, msg, _rel = render_stl(model_id)
    if not ok:
        return {"ok": False, "message": msg, "model_id": model_id, "edited": True}
    return {
        "ok": True,
        "model_id": model_id,
        "edited": True,
        "rendered": True,
        "message": msg,
        "stl_url": f"/api/engineering/stl/{model_id}",
    }


def design_and_render(
    prompt: str,
    *,
    engine: str = "openscad",
    llm_chat: Callable[..., str] | None = None,
) -> dict[str, Any]:
    prompt = prompt.strip()
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    if engine == "meshy":
        try:
            from jarvis.meshy_client import meshy_available, text_to_3d_preview
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        if not meshy_available():
            return {"ok": False, "message": "Meshy not configured"}
        mid = uuid.uuid4().hex[:10]
        paths = _model_paths(mid)
        try:
            data, fmt, _meta = text_to_3d_preview(prompt)
            if (fmt or "").lower() != "stl":
                return {"ok": False, "message": f"Meshy returned {fmt}, expected STL"}
            paths["stl"].write_bytes(data)
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        row = save_model(name=prompt[:80], scad="", prompt=prompt, model_id=mid)
        _update_model(mid, stl_path=str(paths["stl"]), has_stl=True, backend="meshy")
        advice = print_advice(mid)
        return {
            "ok": True,
            "model_id": mid,
            "name": row.get("name") or mid,
            "rendered": True,
            "stl_url": f"/api/engineering/stl/{mid}",
            "message": "Meshy design ready",
            "print_advice": advice,
        }
    chat = llm_chat or default_engineering_llm()
    raw = chat(CAD_SYSTEM_PROMPT, prompt)
    scad = _extract_scad(raw)
    if not scad:
        return {"ok": False, "message": "No OpenSCAD in model response"}
    row = save_model(name=prompt[:80], scad=scad, prompt=prompt)
    mid = row["id"]
    ok, msg, _rel = render_stl(mid)
    if not ok:
        return {"ok": False, "message": msg, "model_id": mid}
    advice = print_advice(mid)
    return {
        "ok": True,
        "model_id": mid,
        "name": row.get("name") or mid,
        "rendered": True,
        "stl_url": f"/api/engineering/stl/{mid}",
        "message": msg,
        "print_advice": advice,
    }


def print_advice(model_id: str) -> dict[str, Any]:
    model = get_model(model_id)
    if not model:
        return {"ok": False, "message": "Model not found"}
    tips = [
        "Use a brim for tall narrow parts.",
        "Orient the largest flat face on the bed when possible.",
        "Inspect the first layer before leaving the printer unattended.",
    ]
    return {
        "ok": True,
        "tips": tips,
        "settings": {"layer_height": "0.2mm", "infill": "20% gyroid"},
        "download_stl": f"/api/engineering/stl/{model_id}",
        "download_scad": f"/api/engineering/scad/{model_id}",
    }


def engineering_lab_status() -> dict[str, Any]:
    st = openscad_status()
    st["engineering_model"] = engineering_model()
    meshy_ok = False
    try:
        from jarvis.meshy_client import meshy_available

        meshy_ok = meshy_available()
        st["meshy_available"] = meshy_ok
    except Exception:
        st["meshy_available"] = False
    st["design_engines"] = ["openscad", "meshy"] if meshy_ok else ["openscad"]
    st["available"] = bool(st.get("available"))
    return st


def parse_engineering_message(message: str) -> dict[str, Any] | None:
    text = (message or "").strip()
    if not text:
        return None
    lower = text.lower()

    if re.search(r"\b(list|show)\b.+\bengineering models?\b", lower):
        return {"action": "engineering_list", "params": {}}

    m = _EDIT_RE.match(text)
    if m:
        return {
            "action": "engineering_edit",
            "params": {"model_id": m.group(1), "prompt": m.group(2).strip()},
        }

    if _IMAGE_BLOCK_RE.search(lower) and re.search(r"\b(create|make|design|draw)\b", lower):
        return None

    if re.search(r"\bdesign\b", lower) and not re.search(r"\b(illustration|logo|graphic)\b", lower):
        prompt = re.sub(r"^(?:please\s+)?design\s+(?:a|an)\s+", "", text, flags=re.I).strip() or text
        return {"action": "engineering_design", "params": {"prompt": prompt}}

    return None
