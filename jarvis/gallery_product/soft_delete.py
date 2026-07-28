"""Soft delete — trash with undo, then permanent purge."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

TRASH_DIR = DATA_DIR / "gallery_trash"
TRASH_META = TRASH_DIR / "index.json"
UNDO_WINDOW_SEC = 300  # 5 minutes soft window highlighted in UI


def _load_index() -> list[dict[str, Any]]:
    if not TRASH_META.exists():
        return []
    try:
        data = json.loads(TRASH_META.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_index(rows: list[dict[str, Any]]) -> None:
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    TRASH_META.write_text(json.dumps(rows[:500], indent=2), encoding="utf-8")


def soft_delete(path: Path, *, source: str = "generated") -> dict[str, Any]:
    from jarvis.config import DATA_DIR as _DATA

    path = Path(path)
    if not path.is_file():
        return {"ok": False, "message": "File not found"}
    trash_dir = _DATA / "gallery_trash"
    trash_dir.mkdir(parents=True, exist_ok=True)
    dest = trash_dir / f"{int(time.time())}_{path.name}"
    shutil.move(str(path), str(dest))
    row = {
        "id": dest.name,
        "original_name": path.name,
        "trash_path": str(dest),
        "source": source,
        "ts": time.time(),
    }
    # use module helpers with patched paths when tests override TRASH_*
    global TRASH_DIR, TRASH_META
    TRASH_DIR = trash_dir
    TRASH_META = trash_dir / "index.json"
    rows = _load_index()
    rows.insert(0, row)
    _save_index(rows)
    try:
        from jarvis.cache_state import invalidate_gallery

        invalidate_gallery()
    except Exception:
        pass
    return {"ok": True, "deleted": path.name, "trash_id": row["id"], "undo_sec": UNDO_WINDOW_SEC, "entry": row}


def restore(trash_id: str) -> dict[str, Any]:
    from jarvis.config import DATA_DIR as _DATA

    rows = _load_index()
    match = next((r for r in rows if r.get("id") == trash_id), None)
    if not match:
        return {"ok": False, "message": "Trash entry not found"}
    src = Path(match["trash_path"])
    if not src.is_file():
        return {"ok": False, "message": "Trash file missing"}
    dest_dir = _DATA / "generated"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / match["original_name"]
    if dest.exists():
        dest = dest_dir / f"restored_{match['original_name']}"
    shutil.move(str(src), str(dest))
    _save_index([r for r in rows if r.get("id") != trash_id])
    try:
        from jarvis.cache_state import invalidate_gallery

        invalidate_gallery()
    except Exception:
        pass
    return {"ok": True, "restored": dest.name, "path": str(dest)}


def purge(trash_id: str) -> dict[str, Any]:
    rows = _load_index()
    match = next((r for r in rows if r.get("id") == trash_id), None)
    if not match:
        return {"ok": False, "message": "Trash entry not found"}
    src = Path(match["trash_path"])
    if src.is_file():
        src.unlink()
    _save_index([r for r in rows if r.get("id") != trash_id])
    return {"ok": True, "purged": match["original_name"]}


def list_trash(*, limit: int = 50) -> dict[str, Any]:
    rows = _load_index()[:limit]
    now = time.time()
    for r in rows:
        r["undo_remaining"] = max(0, int(UNDO_WINDOW_SEC - (now - float(r.get("ts") or 0))))
    return {"ok": True, "items": rows}
