"""Model / VRAM honesty for Vision runs."""

from __future__ import annotations

from typing import Any


_TASK_VRAM_HINT_MB = {
    "describe": 1500,
    "batch": 1500,
    "ocr": 3500,
    "ocr_structured": 4000,
    "compare": 4500,
    "region": 3500,
    "image_to_code": 4500,
    "pdf": 3500,
    "identify": 5000,
    "video_frame": 3500,
}


def honesty_report(*, task: str = "describe") -> dict[str, Any]:
    from jarvis import llm
    from jarvis.config import load_vision_quality
    from jarvis.vision_product.ocr import classic_ocr_available
    from jarvis.vision_product.settings import load_settings

    settings = load_settings()
    quality = settings.get("quality_mode") or load_vision_quality()
    model = llm.vision_model_for_task(task)
    light = "moondream" in (model or "").lower()
    estimated_vram = _TASK_VRAM_HINT_MB.get(task, 3000)
    if light:
        estimated_vram = min(estimated_vram, 2000)

    low_vram = False
    free_vram = None
    try:
        from jarvis.gpu import is_low_vram

        low_vram = bool(is_low_vram())
    except Exception:
        pass
    try:
        from jarvis.resource_router import snapshot

        snap = snapshot() or {}
        free_vram = snap.get("free_vram_mb") or snap.get("vram_free_mb")
    except Exception:
        pass

    warnings: list[str] = []
    if low_vram and not light:
        warnings.append("Low VRAM — prefer Fast (moondream) for this task.")
    if "llava:13b" in (model or "").lower() or "llava:13" in (model or "").lower():
        warnings.append("llava:13b is heavy on 8GB GPUs — expect slower responses.")
    if "llama3.2-vision" in (model or "").lower():
        try:
            from jarvis.ollama_health import supports_mllama

            if not supports_mllama():
                warnings.append(
                    "llama3.2-vision needs Ollama with mllama support — Fast/llava may be safer."
                )
        except Exception:
            pass

    latency = "1–3s" if light else ("5–20s" if low_vram else "3–12s")
    fallback = "moondream (Fast)" if not light else "installed vision model"

    return {
        "ok": True,
        "task": task,
        "model": model,
        "quality_mode": quality,
        "ocr_mode": settings.get("ocr_mode"),
        "classic_ocr_available": classic_ocr_available(),
        "estimated_vram_mb": estimated_vram,
        "free_vram_mb": free_vram,
        "low_vram": low_vram,
        "expected_latency": latency,
        "fallback": fallback,
        "warnings": warnings,
        "warn_before_heavy": bool(settings.get("warn_before_heavy", True)),
        "heavy": not light and task not in ("describe", "batch"),
    }
