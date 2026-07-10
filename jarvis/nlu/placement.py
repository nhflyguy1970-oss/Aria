"""Classifier placement — adaptive benchmark results."""

from __future__ import annotations

import json
import os
from typing import Any

from jarvis.config import DATA_DIR

_PLACEMENT_FILE = DATA_DIR / "nlu_placement.json"
_BENCHMARK_RAN = False


def placement_config() -> dict[str, Any]:
    global _BENCHMARK_RAN
    env_model = (os.getenv("JARVIS_NLU_MODEL") or "").strip()
    env_device = (os.getenv("JARVIS_NLU_DEVICE") or "").strip()
    if env_model:
        return {
            "model": env_model,
            "device": env_device or "cpu",
            "source": "env",
            "version": "1.0",
        }
    if not _BENCHMARK_RAN and os.getenv("JARVIS_NLU_SKIP_BENCHMARK", "").lower() not in (
        "1",
        "true",
        "yes",
    ):
        try:
            from jarvis.nlu.benchmark import ensure_benchmark

            ensure_benchmark()
            _BENCHMARK_RAN = True
        except Exception:
            _BENCHMARK_RAN = True
    if _PLACEMENT_FILE.is_file():
        try:
            data = json.loads(_PLACEMENT_FILE.read_text(encoding="utf-8"))
            if data.get("model"):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "model": "structure",
        "device": "cpu",
        "source": "structure_fallback",
        "selection_reason": "Structural NLU (grammar/syntax) until benchmark completes",
        "version": "1.0",
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
