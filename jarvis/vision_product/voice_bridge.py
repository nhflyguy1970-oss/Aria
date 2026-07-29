"""Voice ↔ Vision bridge — uses completed Voice product; never duplicates TTS."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def latest_upload_image() -> str | None:
    from jarvis.config import DATA_DIR

    uploads = DATA_DIR / "uploads"
    if not uploads.is_dir():
        return None
    images = sorted(
        (
            p
            for p in uploads.iterdir()
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return str(images[0]) if images else None


def voice_vision_command(
    action: str,
    *,
    path: str | None = None,
    assistant=None,
    speak: bool = True,
) -> dict[str, Any]:
    """
    Run shared Vision analyze then optionally speak via Voice.
    Supported actions: describe, ocr, summarize, identify, read (alias ocr).
    """
    from jarvis.vision_product.engine import analyze

    act = (action or "describe").lower().strip()
    if act in ("read", "read_this", "speak_ocr"):
        act = "ocr"
    if act in ("whats_on_screen", "screen"):
        act = "describe"
    resolved = path or latest_upload_image()
    if not resolved or not Path(resolved).is_file():
        return {
            "ok": False,
            "error": "No recent image — attach one in Chat or open Vision Home",
            "pipeline": "vision_engine",
        }
    out = analyze(
        path=resolved,
        action=act,
        source="voice",
        assistant=assistant,
        speak=speak,
        force=True,
    )
    out["voice_bridge"] = True
    return out
