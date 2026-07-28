"""Screenshot capture service for Browser."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

SHOT_DIR = DATA_DIR / "browser_screenshots"


def capture(*, label: str = "shot", reason: str = "") -> dict[str, Any]:
    """Capture a fresh screenshot from the live page. Never invent success."""
    from jarvis.browser_product.session import append_step, get_page

    page = get_page()
    if page is None:
        return {
            "ok": False,
            "error": "No live page to capture",
            "recovery": "Navigate to a URL first",
            "stale": False,
        }
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SHOT_DIR / f"{label}-{int(time.time() * 1000)}.png"
    try:
        page.screenshot(path=str(path), full_page=False)
        append_step("screenshot", f"{reason or label} → {path.name}")
        return {
            "ok": True,
            "path": str(path),
            "url": "/api/browser/screenshot/image",
            "reason": reason or label,
            "stale": False,
            "captured_at": time.time(),
        }
    except Exception as exc:
        append_step("screenshot", str(exc), ok=False)
        return {
            "ok": False,
            "error": str(exc),
            "recovery": "Page may still be loading — retry Screenshot",
            "stale": False,
        }


def latest_path() -> str:
    if not SHOT_DIR.is_dir():
        return ""
    files = sorted(SHOT_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(files[0]) if files else ""
