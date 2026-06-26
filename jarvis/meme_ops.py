"""Classic meme compositor: Impact-style captions on an image."""

from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from jarvis.config import DATA_DIR

MEME_DIR = DATA_DIR / "generated" / "memes"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
    "/usr/share/fonts/truetype/microsoft-fonts/Impact.ttf",
    str(Path.home() / ".fonts/Impact.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _wrap_lines(text: str, max_chars: int) -> list[str]:
    text = " ".join(text.strip().upper().split())
    if not text:
        return []
    return textwrap.wrap(text, width=max_chars) or [text]


def _fit_font(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    max_width: int,
    max_height: int,
    start_size: int,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, list[str]]:
    size = start_size
    while size >= 16:
        font = _load_font(size)
        wrapped: list[str] = []
        for line in lines:
            wrapped.extend(_wrap_lines(line, max(8, max_width // max(size // 2, 1))))
        if not wrapped:
            return font, []
        widths = [draw.textbbox((0, 0), ln, font=font)[2] for ln in wrapped]
        heights = sum(draw.textbbox((0, 0), ln, font=font)[3] for ln in wrapped)
        line_gap = max(4, size // 8)
        total_h = heights + line_gap * max(0, len(wrapped) - 1)
        if max(widths) <= max_width and total_h <= max_height:
            return font, wrapped
        size -= 2
    font = _load_font(16)
    flat = []
    for line in lines:
        flat.extend(_wrap_lines(line, 24))
    return font, flat[:4]


def _draw_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    img_w: int,
    y_start: int,
) -> None:
    if not lines:
        return
    line_gap = max(4, getattr(font, "size", 32) // 8)
    heights = [draw.textbbox((0, 0), ln, font=font)[3] for ln in lines]
    total_h = sum(heights) + line_gap * max(0, len(lines) - 1)
    y = y_start
    if y_start > img_w:
        y = y_start - total_h
    stroke = max(2, getattr(font, "size", 32) // 14)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (img_w - tw) // 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill="white",
            stroke_width=stroke,
            stroke_fill="black",
        )
        y += heights[i] + line_gap


def overlay_meme_text(
    image: Image.Image,
    top: str = "",
    bottom: str = "",
) -> Image.Image:
    """Return a copy of *image* with classic top/bottom meme captions."""
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    margin = max(8, w // 40)
    max_w = w - margin * 2
    max_h = h // 3

    top_lines = _wrap_lines(top, 28) if top.strip() else []
    bottom_lines = _wrap_lines(bottom, 28) if bottom.strip() else []

    if top_lines:
        font, wrapped = _fit_font(draw, top_lines, max_w, max_h, max(24, w // 10))
        _draw_block(draw, wrapped, font, w, margin)

    if bottom_lines:
        font, wrapped = _fit_font(draw, bottom_lines, max_w, max_h, max(24, w // 10))
        _draw_block(draw, wrapped, font, w, h - margin)

    return img.convert("RGB")


def solid_background(width: int = 800, height: int = 600, color: tuple[int, int, int] = (32, 32, 32)) -> Image.Image:
    return Image.new("RGB", (width, height), color)


def compose_meme(
    background_path: str | Path,
    top: str = "",
    bottom: str = "",
    output: str | Path | None = None,
) -> str:
    """Add captions to *background_path* and save under MEME_DIR."""
    MEME_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(background_path)
    if not src.is_file():
        raise FileNotFoundError(f"Background not found: {background_path}")

    with Image.open(src) as raw:
        result = overlay_meme_text(raw, top=top, bottom=bottom)

    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = MEME_DIR / f"meme_{stamp}.png"

    result.save(out, format="PNG", optimize=True)
    return str(out.resolve())


def list_memes(limit: int = 50) -> list[dict]:
    MEME_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(MEME_DIR.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict] = []
    for f in files:
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
            out.append({"name": f.name, "path": str(f)})
        if len(out) >= limit:
            break
    return out
