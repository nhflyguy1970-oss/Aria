"""Download safety for Browser."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jarvis.config import DATA_DIR

DOWNLOAD_DIR = DATA_DIR / "browser_downloads"

_RISKY_EXT = {
    ".exe",
    ".msi",
    ".bat",
    ".cmd",
    ".ps1",
    ".scr",
    ".js",
    ".vbs",
    ".jar",
    ".dmg",
    ".pkg",
    ".sh",
    ".apk",
}
_ALLOWED_EXT = {
    ".pdf",
    ".txt",
    ".csv",
    ".json",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".zip",
    ".gz",
    ".tar",
    ".docx",
    ".xlsx",
    ".pptx",
}


def _check_download_safe(url: str, *, filename: str = "") -> tuple[bool, str, dict[str, Any]]:
    """Validate download URL / extension. Returns (ok, reason, meta)."""
    parsed = urlparse(url or "")
    name = filename or Path(parsed.path or "").name or "download"
    ext = Path(name).suffix.lower()
    meta = {"filename": name, "extension": ext, "url": url}
    if not url:
        return False, "Download URL missing", meta
    if parsed.scheme and parsed.scheme.lower() not in ("http", "https"):
        return False, f"Blocked download scheme: {parsed.scheme}", meta
    if ext in _RISKY_EXT:
        return False, f"Risky executable/script type blocked: {ext}", {**meta, "risk": "high"}
    if ext and ext not in _ALLOWED_EXT:
        return False, f"Unlisted file type requires confirmation: {ext}", {**meta, "needs_confirm": True, "risk": "medium"}
    return True, "", {**meta, "risk": "low"}


def check_download_safe(url: str, *, filename: str = "", allow_risky: bool = False) -> dict[str, Any]:
    ok, reason, meta = _check_download_safe(url, filename=filename)
    if ok:
        return {"ok": True, **meta}
    if meta.get("needs_confirm") and allow_risky:
        return {"ok": True, "confirmed": True, **meta}
    return {"ok": False, "message": reason, "needs_confirm": bool(meta.get("needs_confirm")), **meta}


def prepare_download_dir() -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return DOWNLOAD_DIR


def list_downloads(*, limit: int = 40) -> dict[str, Any]:
    """List files already in the Browser download directory (metadata only)."""
    d = prepare_download_dir()
    items = []
    try:
        files = sorted(d.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:
        files = []
    for p in files[:limit]:
        if not p.is_file():
            continue
        try:
            st = p.stat()
            items.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "size": st.st_size,
                    "mtime": st.st_mtime,
                    "extension": p.suffix.lower(),
                }
            )
        except Exception:
            continue
    return {"ok": True, "items": items, "dir": str(d)}
