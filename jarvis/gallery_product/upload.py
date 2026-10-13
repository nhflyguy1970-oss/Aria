"""Import the owner's own images into the Gallery so they can be edited (✎)."""

from __future__ import annotations

import io
import re
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

MAX_UPLOAD_BYTES = 30 * 1024 * 1024
_FORMAT_EXT = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "GIF": ".gif"}


def save_upload(filename: str, content: bytes) -> dict[str, Any]:
    """Validate an uploaded image and store it in the Gallery, marked as external.

    External images can be edited normally, but never into nude or sexual images
    (see jarvis.image_safety.edit_refusal_for)."""
    if not content:
        return {"ok": False, "message": "Empty file"}
    if len(content) > MAX_UPLOAD_BYTES:
        return {"ok": False, "message": f"Image is larger than {MAX_UPLOAD_BYTES // 1048576} MB"}
    try:
        from PIL import Image

        with Image.open(io.BytesIO(content)) as img:
            fmt = (img.format or "").upper()
            img.verify()
    except Exception:
        return {"ok": False, "message": "Not a readable image (PNG, JPEG, WebP or GIF)"}
    ext = _FORMAT_EXT.get(fmt)
    if not ext:
        return {"ok": False, "message": f"Unsupported image format: {fmt or 'unknown'}"}

    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(filename or "image").stem).strip("_")[:40] or "image"
    out_dir = DATA_DIR / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"upload_{time.strftime('%Y%m%d_%H%M%S')}_{stem}"
    dest = out_dir / f"{base}{ext}"
    n = 1
    while dest.exists():
        n += 1
        dest = out_dir / f"{base}_{n}{ext}"
    dest.write_bytes(content)

    from jarvis.image_safety import mark_external

    mark_external(dest)
    try:
        from jarvis.cache_state import invalidate_gallery

        invalidate_gallery()
    except Exception:
        pass
    return {"ok": True, "name": dest.name, "path": str(dest)}
