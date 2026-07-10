"""Classifier hardware placement — from benchmark or env override."""

from __future__ import annotations

import json
import os
from typing import Any

from jarvis.config import DATA_DIR

_PLACEMENT_FILE = DATA_DIR / "nlu_placement.json"
_CANDIDATE_MODELS = (
    "smollm:360m",
    "qwen2.5:1.5b",
    "qwen2.5:0.5b",
    "gemma2:2b",
    "qwen3:1.7b",
)


def placement_config() -> dict[str, Any]:
    env_model = (os.getenv("JARVIS_NLU_MODEL") or "").strip()
    env_device = (os.getenv("JARVIS_NLU_DEVICE") or "").strip()
    if env_model:
        return {
            "model": env_model,
            "device": env_device or "cpu",
            "source": "env",
        }
    if _PLACEMENT_FILE.is_file():
        try:
            data = json.loads(_PLACEMENT_FILE.read_text(encoding="utf-8"))
            if data.get("model"):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "model": "qwen2.5:1.5b",
        "device": "cpu",
        "source": "default",
        "candidates": list(_CANDIDATE_MODELS),
    }


def save_placement(config: dict[str, Any]) -> None:
    _PLACEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PLACEMENT_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")


def ollama_options_for_device(device: str) -> dict[str, Any]:
    dev = (device or "cpu").lower()
    opts: dict[str, Any] = {"temperature": 0, "num_predict": 96}
    if dev == "cpu":
        opts["num_gpu"] = 0
    elif dev.startswith("nvidia"):
        opts["num_gpu"] = 99
    elif dev.startswith("amd") or dev.startswith("rocm"):
        opts["num_gpu"] = 99
    return opts
