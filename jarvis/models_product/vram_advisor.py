"""VRAM fit advisor — warn before download / assign / switch."""

from __future__ import annotations

from typing import Any

from jarvis.models_product.catalog import build_model_card


def advise_vram(model: str, *, action: str = "assign") -> dict[str, Any]:
    card = build_model_card(model)
    free = card.get("free_vram_gb")
    need = card.get("estimated_vram_gb")
    severity = "ok"
    warnings: list[str] = []
    fixes: list[dict[str, str]] = []

    if need is not None and free is not None and float(free) < float(need) * 0.9:
        severity = "warning"
        warnings.append(
            f"Estimated {need} GB VRAM needed; ~{free} GB free. Likely OOM or heavy offload."
        )
        fixes.append({"label": "Free VRAM", "action": "free_vram"})
        fixes.append({"label": "Open Mission Control", "action": "mc:inference"})
        fixes.append({"label": "Use smaller model", "action": "models:catalog?capability=low-vram"})
    if card.get("provider") == "comfyui" or "comfy" in (model or "").lower():
        warnings.append("ComfyUI competes with Ollama for GPU memory.")
        fixes.append({"label": "Free VRAM before image jobs", "action": "free_vram"})
    if action == "download" and card.get("pullable") is False:
        severity = "error"
        warnings.append("This backend is not pullable via Ollama.")

    return {
        "ok": severity != "error",
        "severity": severity,
        "model": model,
        "action": action,
        "card": card,
        "warnings": warnings,
        "fixes": fixes,
        "fits": card.get("fits_current_hardware"),
        "message": warnings[0] if warnings else "Hardware looks compatible",
    }
