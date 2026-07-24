"""Image/video/PDF helpers for the vision module."""

from __future__ import annotations

import io
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

OCR_PROMPT = (
    "Read and transcribe ALL visible text in this image exactly as shown. "
    "Preserve layout with line breaks where helpful. "
    "If there is no text, say so."
)

OCR_STRUCTURED_PROMPT = (
    "Extract all visible content from this image as structured data.\n"
    "- Use markdown tables for tabular data.\n"
    "- Use bullet lists for forms and labeled fields.\n"
    "- Wrap JSON-like key-value pairs in a ```json code block when appropriate.\n"
    "- Preserve exact text for labels, values, and headings.\n"
    "- If there is no text, say so."
)

IMAGE_TO_CODE_PROMPT = (
    "This is a UI screenshot. Recreate it as clean, semantic HTML with embedded CSS. "
    "Match layout, colors, typography, and spacing closely. "
    "Use accessible markup. Output only a single ```html code block."
)

DESCRIBE_PROMPT = "Describe this image in detail."

IDENTIFY_PROMPT = (
    "You are an expert at visual identification. Study this image carefully.\n"
    "Answer the question with the most likely identity (species, breed, model, etc.).\n"
    "For organisms: give common name and scientific name when possible.\n"
    "Explain the key visual features that support your answer.\n"
    "If uncertain, give your best guess, plausible alternatives, and confidence.\n\n"
    "Question: {question}"
)

_IDENTIFY_PATTERNS = (
    r"\b(what|which)\s+(species|kind|type|breed|variety|sort)\b",
    r"\b(identify|identification|name (this|the|it))\b",
    r"\bwhat (animal|plant|bird|insect|spider|snake|fish|tree|flower|mushroom|bug|mammal|reptile|amphibian|fungus|lichen)\b",
    r"\b(is this (a|an)|tell me what (this|that|it) is)\b",
    r"\bwhat is (this|that|it)\b.*\?",
    r"\b(what|which)\s+(bird|tree|flower|dog|cat|snake|spider|insect|fish)\s+is\b",
    r"\b(scientific|latin)\s+name\b",
    r"\bwhat (breed|variety) (is|of)\b",
)

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
PDF_EXTENSIONS = {".pdf"}

REGION_PRESETS: dict[str, dict[str, float]] = {
    "top left": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
    "top-left": {"x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
    "top right": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 0.5},
    "top-right": {"x": 0.5, "y": 0.0, "w": 0.5, "h": 0.5},
    "bottom left": {"x": 0.0, "y": 0.5, "w": 0.5, "h": 0.5},
    "bottom-left": {"x": 0.0, "y": 0.5, "w": 0.5, "h": 0.5},
    "bottom right": {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5},
    "bottom-right": {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5},
    "center": {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5},
    "middle": {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5},
}


def vision_task_for_question(question: str) -> str:
    """Return vision task tier key: identify (heavy) or describe (light)."""
    lower = (question or "").lower().strip()
    if not lower:
        return "describe"
    for pattern in _IDENTIFY_PATTERNS:
        if re.search(pattern, lower):
            return "identify"
    return "describe"


def build_vision_prompt(question: str, task: str) -> str:
    if task == "identify":
        return IDENTIFY_PROMPT.format(question=question.strip())
    return question


def apply_crop_bytes(content: bytes, crop: dict | None) -> bytes:
    """Crop image bytes. crop: {x, y, w, h} as fractions 0–1."""
    if not crop:
        return content
    from PIL import Image

    x = float(crop.get("x", 0))
    y = float(crop.get("y", 0))
    w = float(crop.get("w", 1))
    h = float(crop.get("h", 1))
    with Image.open(io.BytesIO(content)) as opened:
        rgb = opened.convert("RGB")
        width, height = rgb.size
        left = max(0, min(width - 1, int(x * width)))
        top = max(0, min(height - 1, int(y * height)))
        right = max(left + 1, min(width, int((x + w) * width)))
        bottom = max(top + 1, min(height, int((y + h) * height)))
        cropped = rgb.crop((left, top, right, bottom))
        out = io.BytesIO()
        cropped.save(out, format="JPEG", quality=90, optimize=True)
        return out.getvalue()


def parse_video_second(message: str, explicit: float | None = None) -> float:
    if explicit is not None and explicit >= 0:
        return float(explicit)
    lower = (message or "").lower()
    if m := re.search(r"\b(?:at|@)\s*(\d{1,2}):(\d{2}):(\d{2})\b", lower):
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    if m := re.search(r"\b(?:at|@)\s*(\d{1,3}):(\d{2})\b", lower):
        return int(m.group(1)) * 60 + int(m.group(2))
    if m := re.search(r"\b(?:at|@)\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds?)\b", lower):
        return float(m.group(1))
    if m := re.search(r"\b(?:at|@)\s*(\d+(?:\.\d+)?)\b", lower):
        return float(m.group(1))
    return 0.0


def extract_video_frame(
    content: bytes,
    filename: str,
    second: float = 0.0,
) -> tuple[bytes, str]:
    """Extract one JPEG frame from video bytes (requires ffmpeg)."""
    ext = Path(filename).suffix.lower() or ".mp4"
    if ext not in VIDEO_EXTENSIONS:
        ext = ".mp4"
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / f"input{ext}"
        out = Path(td) / "frame.jpg"
        inp.write_bytes(content)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", str(max(0.0, second)),
            "-i", str(inp),
            "-vframes", "1",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
        if proc.returncode != 0 or not out.exists():
            err = (proc.stderr or b"").decode(errors="ignore").strip()
            raise ValueError(err or "Could not extract video frame — is ffmpeg installed?")
        return out.read_bytes(), f"frame_{int(second)}s.jpg"


def extract_pdf_page(content: bytes, filename: str, page: int = 1) -> tuple[bytes, str]:
    """Render a PDF page to JPEG bytes."""
    page = max(1, int(page))
    stem = Path(filename).stem or "document"
    try:
        import fitz  # pymupdf

        doc = fitz.open(stream=content, filetype="pdf")
        try:
            if page > doc.page_count:
                raise ValueError(f"PDF has {doc.page_count} page(s); page {page} not found.")
            pix = doc.load_page(page - 1).get_pixmap(matrix=fitz.Matrix(2, 2))
            return pix.tobytes("jpeg"), f"{stem}_p{page}.jpg"
        finally:
            doc.close()
    except ImportError:
        pass

    with tempfile.TemporaryDirectory() as td:
        pdf_path = Path(td) / "input.pdf"
        pdf_path.write_bytes(content)
        out_prefix = Path(td) / "page"
        cmd = [
            "pdftoppm", "-jpeg", "-f", str(page), "-l", str(page),
            "-r", "150", str(pdf_path), str(out_prefix),
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
        out_file = Path(td) / f"page-{page:02d}.jpg"
        if proc.returncode != 0 or not out_file.exists():
            candidates = list(Path(td).glob("page*.jpg"))
            if not candidates:
                err = (proc.stderr or b"").decode(errors="ignore").strip()
                raise ValueError(
                    err or "PDF render failed — install pymupdf (`pip install pymupdf`) or poppler-utils"
                )
            out_file = candidates[0]
        return out_file.read_bytes(), f"{stem}_p{page}.jpg"


def parse_region(message: str, crop: dict | None = None) -> dict | None:
    if crop:
        return crop
    lower = (message or "").lower()
    for key, region in REGION_PRESETS.items():
        if key in lower:
            return region.copy()
    if m := re.search(
        r"\b(\d{1,3})\s*[%]?\s*[,x]\s*(\d{1,3})\s*[%]?\s*[,x]\s*(\d{1,3})\s*[%]?\s*[,x]\s*(\d{1,3})\s*%?",
        lower,
    ):
        vals = [float(x) for x in m.groups()]
        if max(vals) > 1:
            vals = [v / 100.0 for v in vals]
        return {"x": vals[0], "y": vals[1], "w": vals[2], "h": vals[3]}
    return None


def build_visual_diff(path1: Path, path2: Path, out_dir: Path) -> Path | None:
    """Pixel-diff highlight image saved under out_dir (uploads)."""
    try:
        from PIL import Image, ImageChops, ImageEnhance
    except ImportError:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(path1) as raw1, Image.open(path2) as raw2:
        w = min(raw1.width, raw2.width)
        h = min(raw1.height, raw2.height)
        if w < 2 or h < 2:
            return None
        a = raw1.convert("RGB").resize((w, h))
        b = raw2.convert("RGB").resize((w, h))
        diff = ImageChops.difference(a, b)
        diff = ImageEnhance.Brightness(diff).enhance(3.0)
        gap = 6
        canvas = Image.new("RGB", (w * 3 + gap * 2, h), (24, 24, 24))
        canvas.paste(a, (0, 0))
        canvas.paste(b, (w + gap, 0))
        canvas.paste(diff, (w * 2 + gap * 2, 0))
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = out_dir / f"compare_diff_{stamp}.jpg"
        canvas.save(out, format="JPEG", quality=88, optimize=True)
        return out
