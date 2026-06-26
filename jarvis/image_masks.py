"""Mask helpers for ComfyUI inpainting."""

from __future__ import annotations

import time
from pathlib import Path

from jarvis.config import DATA_DIR

MASK_DIR = DATA_DIR / "inpaint_masks"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def mask_from_region(image_path: str | Path, region: dict | None) -> Path:
    """Build a white-on-black mask PNG matching image dimensions.

    region: {x, y, w, h} as fractions 0–1. None or empty → full-image mask.
    """
    from PIL import Image, ImageDraw

    src = Path(image_path).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Image not found: {src}")

    with Image.open(src) as opened:
        rgb = opened.convert("RGB")
        width, height = rgb.size

    mask = Image.new("L", (width, height), 0)
    if region:
        x = _clamp01(region.get("x", 0))
        y = _clamp01(region.get("y", 0))
        w = _clamp01(region.get("w", 1))
        h = _clamp01(region.get("h", 1))
        left = max(0, min(width - 1, int(x * width)))
        top = max(0, min(height - 1, int(y * height)))
        right = max(left + 1, min(width, int((x + w) * width)))
        bottom = max(top + 1, min(height, int((y + h) * height)))
        ImageDraw.Draw(mask).rectangle((left, top, right, bottom), fill=255)
    else:
        mask = Image.new("L", (width, height), 255)

    MASK_DIR.mkdir(parents=True, exist_ok=True)
    dest = MASK_DIR / f"mask_{src.stem}_{int(time.time())}.png"
    mask.save(dest, format="PNG", optimize=True)
    return dest


def validate_mask_path(mask_path: str | Path, image_path: str | Path) -> Path:
    """Ensure mask file exists and matches image size (resize mask if needed)."""
    from PIL import Image

    mask = Path(mask_path).expanduser().resolve()
    image = Path(image_path).expanduser().resolve()
    if not mask.is_file():
        raise FileNotFoundError(f"Mask not found: {mask}")
    if not image.is_file():
        raise FileNotFoundError(f"Image not found: {image}")

    with Image.open(image) as im:
        iw, ih = im.size
    with Image.open(mask) as mm:
        gray = mm.convert("L")
        if gray.size != (iw, ih):
            gray = gray.resize((iw, ih), Image.Resampling.NEAREST)
            MASK_DIR.mkdir(parents=True, exist_ok=True)
            dest = MASK_DIR / f"mask_resized_{mask.stem}_{int(time.time())}.png"
            gray.save(dest, format="PNG", optimize=True)
            return dest
    return mask
