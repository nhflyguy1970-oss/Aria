"""Regional hatch packs — bundled + operator-imported calendars."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

BUNDLED_DIR = Path(__file__).resolve().parent.parent / "flytying" / "data"
USER_DIR = DATA_DIR / "flytying_product" / "hatch_packs"

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$", re.I)


def _ensure_user_dir() -> Path:
    USER_DIR.mkdir(parents=True, exist_ok=True)
    return USER_DIR


def _read_pack(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        data = dict(data)
        data.setdefault("id", path.stem.replace("hatch_", ""))
        data["_path"] = str(path)
        data["_bundled"] = str(path.parent.resolve()) == str(BUNDLED_DIR.resolve())
        return data
    except (OSError, json.JSONDecodeError):
        return None


def list_packs() -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root, bundled in ((BUNDLED_DIR, True), (_ensure_user_dir(), False)):
        if not root.is_dir():
            continue
        for path in sorted(root.glob("hatch_*.json")):
            pack = _read_pack(path)
            if not pack:
                continue
            pid = str(pack.get("id") or path.stem)
            if pid in seen and not bundled:
                # user pack overrides bundled id
                packs = [p for p in packs if p.get("id") != pid]
            elif pid in seen:
                continue
            seen.add(pid)
            packs.append(
                {
                    "id": pid,
                    "region": pack.get("region") or pid,
                    "bundled": bundled and not (USER_DIR / path.name).is_file(),
                    "months": len(pack.get("months") or {}),
                    "path": pack.get("_path"),
                }
            )
    return packs


def load_pack(pack_id: str) -> dict[str, Any] | None:
    pid = (pack_id or "").strip()
    if not pid:
        return None
    # Prefer user override
    for candidate in (
        _ensure_user_dir() / f"hatch_{pid}.json",
        _ensure_user_dir() / f"{pid}.json" if not pid.startswith("hatch_") else _ensure_user_dir() / f"{pid}.json",
        BUNDLED_DIR / f"hatch_{pid}.json",
        BUNDLED_DIR / f"{pid}.json",
    ):
        pack = _read_pack(candidate)
        if pack:
            pack.pop("_path", None)
            return pack
    # Fuzzy: match id field
    for info in list_packs():
        if info.get("id") == pid:
            return _read_pack(Path(str(info.get("path"))))
    return None


def import_pack(payload: dict[str, Any] | None = None, *, path: str = "") -> dict[str, Any]:
    data: dict[str, Any] | None = None
    if path:
        data = _read_pack(Path(path))
    elif isinstance(payload, dict):
        data = dict(payload)
    if not data:
        return {"ok": False, "message": "pack payload or path required"}
    pid = str(data.get("id") or "").strip()
    if not pid:
        region = str(data.get("region") or "custom").lower()
        slug = re.sub(r"[^a-z0-9]+", "_", region).strip("_") or uuid.uuid4().hex[:8]
        pid = slug
    if not _SAFE_ID.match(pid):
        pid = re.sub(r"[^a-z0-9_\-]", "_", pid.lower())[:64] or uuid.uuid4().hex[:8]
    data["id"] = pid
    if "months" not in data or not isinstance(data.get("months"), dict):
        return {"ok": False, "message": "pack requires months object"}
    dest = _ensure_user_dir() / f"hatch_{pid}.json"
    clean = {k: v for k, v in data.items() if not str(k).startswith("_")}
    dest.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    return {"ok": True, "id": pid, "path": str(dest)}


def export_pack(pack_id: str) -> dict[str, Any]:
    pack = load_pack(pack_id)
    if not pack:
        return {"ok": False, "message": "pack_not_found"}
    clean = {k: v for k, v in pack.items() if not str(k).startswith("_")}
    return {"ok": True, "pack": clean}


def copy_bundled_to_user(pack_id: str) -> dict[str, Any]:
    """Duplicate a bundled pack into user dir for editing."""
    src = BUNDLED_DIR / f"hatch_{pack_id}.json"
    if not src.is_file():
        return {"ok": False, "message": "bundled_pack_not_found"}
    dest = _ensure_user_dir() / src.name
    shutil.copy2(src, dest)
    return {"ok": True, "id": pack_id, "path": str(dest)}


def activate_pack(pack_id: str) -> dict[str, Any]:
    """Activate a hatch pack as the operator calendar (shared by hatch.py)."""
    pack = load_pack(pack_id)
    if not pack:
        return {"ok": False, "message": "pack_not_found"}
    dest = BUNDLED_DIR / "hatch_operator_active.json"
    clean = {k: v for k, v in pack.items() if not str(k).startswith("_")}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    try:
        from jarvis.flytying import hatch as hatch_mod

        hatch_mod._calendar.cache_clear()
    except Exception:
        pass
    return {"ok": True, "id": clean.get("id") or pack_id, "region": clean.get("region"), "path": str(dest)}
