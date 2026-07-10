"""Mission Control performance samples — lightweight historical metrics."""

from __future__ import annotations

import json
import threading
import time
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

_STORE = PROJECT_ROOT / "data" / "automation" / "platform_metrics.json"
_MAX_SAMPLES = 120
_MIN_INTERVAL_S = 30.0
_LOCK = threading.Lock()
_LAST_SAMPLE = 0.0


def _load() -> list[dict[str, Any]]:
    if not _STORE.is_file():
        return []
    try:
        data = json.loads(_STORE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data[-_MAX_SAMPLES:]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save(samples: list[dict[str, Any]]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(samples[-_MAX_SAMPLES:], indent=2), encoding="utf-8")


def record_sample(metrics: dict[str, Any]) -> dict[str, Any] | None:
    """Append a metrics sample if enough time elapsed since last sample."""
    global _LAST_SAMPLE
    now = time.time()
    with _LOCK:
        if now - _LAST_SAMPLE < _MIN_INTERVAL_S:
            return None
        _LAST_SAMPLE = now
        sample = {"ts": now, "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()), **metrics}
        samples = _load()
        samples.append(sample)
        _save(samples)
        return sample


def list_samples(*, limit: int = 60) -> list[dict[str, Any]]:
    return _load()[-limit:]
