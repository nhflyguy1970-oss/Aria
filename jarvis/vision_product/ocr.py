"""OCR manager — classic / VLM / hybrid through one Vision pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


def classic_ocr_available() -> bool:
    return bool(shutil.which("tesseract"))


def run_classic_ocr(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "error": f"not found: {p}", "engine": "classic"}
    if not classic_ocr_available():
        return {"ok": False, "error": "tesseract not installed", "engine": "classic"}
    try:
        import subprocess

        proc = subprocess.run(
            ["tesseract", str(p), "stdout", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        text = (proc.stdout or "").strip()
        if proc.returncode != 0 and not text:
            err = (proc.stderr or "").strip() or "tesseract failed"
            return {"ok": False, "error": err, "engine": "classic"}
        conf = 0.7 if len(text) > 20 else 0.45
        return {"ok": True, "text": text, "engine": "classic", "confidence": conf}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "engine": "classic"}


def run_vlm_ocr(path: str | Path, *, structured: bool = False, assistant=None) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "error": f"not found: {p}", "engine": "vlm"}
    try:
        if assistant is None:
            from jarvis.assistant_instance import get_assistant

            assistant = get_assistant()
        vision = assistant.vision
        if structured:
            text = vision.ocr_structured(str(p))
        else:
            text = vision.ocr(str(p))
        if str(text).startswith("ERROR:"):
            return {"ok": False, "error": str(text), "engine": "vlm"}
        conf = 0.65 if len(str(text)) > 40 else 0.5
        return {
            "ok": True,
            "text": str(text),
            "engine": "vlm",
            "confidence": conf,
            "structured": structured,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "engine": "vlm"}


def run_ocr(
    path: str | Path,
    *,
    mode: str | None = None,
    structured: bool = False,
    assistant=None,
) -> dict[str, Any]:
    """Shared OCR entry — classic, VLM, hybrid, or auto."""
    from jarvis.vision_product.settings import load_settings

    settings = load_settings()
    mode = (mode or settings.get("ocr_mode") or "auto").lower()
    threshold = float(settings.get("confidence_threshold") or 0.55)

    if structured:
        # Structured needs VLM understanding
        return run_vlm_ocr(path, structured=True, assistant=assistant)

    if mode == "classic":
        return run_classic_ocr(path)
    if mode == "vlm":
        return run_vlm_ocr(path, structured=False, assistant=assistant)

    # auto / hybrid: prefer classic when available for dense text, else VLM; hybrid merges
    classic = run_classic_ocr(path) if classic_ocr_available() else {"ok": False}
    if mode == "auto" and classic.get("ok") and float(classic.get("confidence") or 0) >= threshold:
        classic["mode"] = "auto"
        return classic

    vlm = run_vlm_ocr(path, structured=False, assistant=assistant)
    if mode == "auto":
        if vlm.get("ok"):
            vlm["mode"] = "auto"
            return vlm
        if classic.get("ok"):
            classic["mode"] = "auto"
            return classic
        return vlm if vlm.get("error") else classic

    # hybrid
    if classic.get("ok") and vlm.get("ok"):
        c_text = str(classic.get("text") or "").strip()
        v_text = str(vlm.get("text") or "").strip()
        # Prefer longer classic for dense docs; append VLM notes if different
        if len(c_text) >= len(v_text) * 0.8:
            text = c_text
            conf = max(float(classic.get("confidence") or 0), float(vlm.get("confidence") or 0))
        else:
            text = v_text
            conf = float(vlm.get("confidence") or 0.55)
        return {
            "ok": True,
            "text": text,
            "engine": "hybrid",
            "mode": "hybrid",
            "confidence": conf,
            "classic_len": len(c_text),
            "vlm_len": len(v_text),
        }
    if classic.get("ok"):
        classic["mode"] = "hybrid"
        classic["engine"] = "hybrid-classic"
        return classic
    if vlm.get("ok"):
        vlm["mode"] = "hybrid"
        return vlm
    return {"ok": False, "error": vlm.get("error") or classic.get("error") or "OCR failed", "engine": "hybrid"}
