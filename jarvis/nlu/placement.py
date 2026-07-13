"""Classifier placement — adaptive benchmark results.

Hot-path rule: never block chat/routing on NLU benchmark runs.
Existing placement (or structure fallback) is returned immediately;
rebenchmark may be scheduled in the background when stale.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

from jarvis.config import DATA_DIR

_PLACEMENT_FILE = DATA_DIR / "nlu_placement.json"
_BENCHMARK_SCHEDULED = False
_LOCK = threading.Lock()
_log = logging.getLogger("jarvis.nlu.placement")


def _structure_fallback() -> dict[str, Any]:
    return {
        "model": "structure",
        "device": "cpu",
        "source": "structure_fallback",
        "selection_reason": "Structural NLU (grammar/syntax) until benchmark completes",
        "version": "1.0",
    }


def _load_placement_file() -> dict[str, Any] | None:
    if not _PLACEMENT_FILE.is_file():
        return None
    try:
        data = json.loads(_PLACEMENT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("model"):
        return data
    return None


def _schedule_background_rebenchmark() -> None:
    """Kick off ensure_benchmark off the request path (at most once per process)."""
    global _BENCHMARK_SCHEDULED
    with _LOCK:
        if _BENCHMARK_SCHEDULED:
            return
        if os.getenv("JARVIS_NLU_SKIP_BENCHMARK", "").lower() in ("1", "true", "yes"):
            _BENCHMARK_SCHEDULED = True
            return
        _BENCHMARK_SCHEDULED = True

    def _run() -> None:
        try:
            from jarvis.nlu.benchmark import ensure_benchmark, should_rebenchmark

            if should_rebenchmark():
                _log.info("Starting background NLU classifier benchmark")
                ensure_benchmark()
        except Exception:
            _log.exception("Background NLU benchmark failed")

    threading.Thread(target=_run, name="nlu-benchmark", daemon=True).start()


def placement_config() -> dict[str, Any]:
    env_model = (os.getenv("JARVIS_NLU_MODEL") or "").strip()
    env_device = (os.getenv("JARVIS_NLU_DEVICE") or "").strip()
    if env_model:
        return {
            "model": env_model,
            "device": env_device or "cpu",
            "source": "env",
            "version": "1.0",
        }

    # Never block the hot path on run_benchmark — return cached/structure first.
    cached = _load_placement_file()
    if cached:
        # Soft refresh when stale / new models appear (non-blocking).
        try:
            from jarvis.nlu.benchmark import should_rebenchmark

            if should_rebenchmark():
                _schedule_background_rebenchmark()
        except Exception:
            pass
        return cached

    _schedule_background_rebenchmark()
    return _structure_fallback()


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
