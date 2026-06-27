"""CAD model registry — global + per-project versioned history."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

ENGINEERING_DIR = DATA_DIR / "engineering"
INDEX_FILE = ENGINEERING_DIR / "models.json"
LAST_SCRIPT_FILE = ENGINEERING_DIR / "last_script.json"


def _cad_root() -> Path:
    try:
        from jarvis.active_project import get_active_slug
        from jarvis.project_registry import project_dir

        slug = get_active_slug()
        if slug:
            root = project_dir(slug) / "cad"
            root.mkdir(parents=True, exist_ok=True)
            return root
    except Exception:
        pass
    ENGINEERING_DIR.mkdir(parents=True, exist_ok=True)
    return ENGINEERING_DIR


def _load_index() -> dict[str, Any]:
    path = _cad_root() / "models.json"
    if path.is_file() and INDEX_FILE.is_file() and path != INDEX_FILE:
        pass
    if not path.is_file() and INDEX_FILE.is_file():
        path = INDEX_FILE
    if not path.is_file():
        return {"models": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"models": []}


def _save_index(data: dict[str, Any]) -> None:
    path = _cad_root() / "models.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if path != INDEX_FILE:
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def new_model_id() -> str:
    return uuid.uuid4().hex[:10]


def register_model(
    *,
    prompt: str,
    name: str = "",
    backend: str,
    stl_path: str | Path | None = None,
    scad_path: str | Path | None = None,
    script_path: str | Path | None = None,
    notes: str = "",
    verify: dict[str, Any] | None = None,
    model_id: str | None = None,
) -> dict[str, Any]:
    data = _load_index()
    mid = (model_id or "").strip() or new_model_id()
    now = time.time()
    stl_str = str(stl_path) if stl_path else ""
    scad_str = str(scad_path) if scad_path else ""
    script_str = str(script_path) if script_path else ""
    row = {
        "id": mid,
        "name": (name or prompt[:120]),
        "prompt": prompt[:2000],
        "tags": ["aria"],
        "backend": backend,
        "created": now,
        "updated": now,
        "stl_rendered": bool(stl_str),
        "stl_path": stl_str,
        "scad_path": scad_str,
        "script_path": script_str,
        "notes": (notes or "")[:500],
        "verify": verify or {},
        "version": 1,
    }
    data.setdefault("models", []).append(row)
    _save_index(data)
    return row


def list_models(limit: int = 50) -> list[dict[str, Any]]:
    rows = list(_load_index().get("models") or [])
    rows.sort(key=lambda r: float(r.get("updated") or 0), reverse=True)
    return rows[:limit]


def get_model(model_id: str) -> dict[str, Any] | None:
    for row in list_models(limit=500):
        if row.get("id") == model_id:
            return row
    return None


def update_model(model_id: str, **fields: Any) -> dict[str, Any] | None:
    data = _load_index()
    models = data.get("models") or []
    for row in models:
        if row.get("id") != model_id:
            continue
        row.update({k: v for k, v in fields.items() if v is not None})
        row["updated"] = time.time()
        _save_index(data)
        return row
    return None


def paths_for_model(model_id: str) -> dict[str, Path]:
    root = _cad_root()
    return {
        "stl": root / f"{model_id}.stl",
        "scad": root / f"{model_id}.scad",
        "script": root / f"{model_id}.py",
        "gcode": root / f"{model_id}.gcode",
    }


def save_last_script(*, backend: str, content: str, model_id: str = "", prompt: str = "") -> None:
    ENGINEERING_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "backend": backend,
        "content": content[:20000],
        "model_id": model_id,
        "prompt": prompt[:2000],
        "updated": time.time(),
    }
    LAST_SCRIPT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_last_script() -> dict[str, Any]:
    if not LAST_SCRIPT_FILE.is_file():
        return {}
    try:
        return json.loads(LAST_SCRIPT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def clear_gallery(*, delete_files: bool = False) -> dict[str, Any]:
    removed_ids: list[str] = []
    deleted_files: list[str] = []
    data = _load_index()
    for row in list(data.get("models") or []):
        mid = (row.get("id") or "").strip()
        if mid:
            removed_ids.append(mid)
        if not delete_files:
            continue
        for key in ("stl_path", "scad_path", "script_path"):
            p = (row.get(key) or "").strip()
            if not p:
                continue
            path = Path(p)
            if path.is_file():
                path.unlink()
                deleted_files.append(str(path))
        if mid:
            for path in paths_for_model(mid).values():
                if path.is_file():
                    path.unlink()
                    if str(path) not in deleted_files:
                        deleted_files.append(str(path))
    empty = {"models": []}
    _save_index(empty)
    if INDEX_FILE != _cad_root() / "models.json":
        INDEX_FILE.write_text(json.dumps(empty, indent=2), encoding="utf-8")
    if delete_files and LAST_SCRIPT_FILE.is_file():
        LAST_SCRIPT_FILE.unlink()
        deleted_files.append(str(LAST_SCRIPT_FILE))
    return {
        "ok": True,
        "removed": len(removed_ids),
        "ids": removed_ids,
        "deleted_files": len(deleted_files),
    }
