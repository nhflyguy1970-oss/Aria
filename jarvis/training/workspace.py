"""AI development training workspace — local LoRA/PEFT path."""

from __future__ import annotations

from typing import Any


def training_status() -> dict[str, Any]:
    """Report availability of local training stack."""
    checks = {
        "torch": _importable("torch"),
        "transformers": _importable("transformers"),
        "peft": _importable("peft"),
        "trl": _importable("trl"),
        "accelerate": _importable("accelerate"),
        "datasets": _importable("datasets"),
        "unsloth": _importable("unsloth"),
    }
    ready = checks["torch"] and checks["transformers"] and (checks["peft"] or checks["unsloth"])
    return {
        "ok": ready,
        "ready": ready,
        "packages": checks,
        "router_training": _importable("jarvis.router_training"),
        "note": "Use router_training for FunctionGemma fine-tune when packages installed.",
    }


def _importable(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False
