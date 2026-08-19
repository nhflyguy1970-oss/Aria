"""Bounded model health tracking and temporary avoidance.

Deliberately small: a fixed-size in-memory record per model, a threshold, and a
cooldown. One bad call must not blacklist a model, and nothing here ever
disables a model permanently — after the cooldown it is a candidate again.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

# Policy.
FAILURE_THRESHOLD = 3  # consecutive failures before temporary avoidance
COOLDOWN_S = 120.0  # how long a model is avoided
MAX_TRACKED_MODELS = 200  # bound on the state this module keeps
LATENCY_SAMPLES = 20


@dataclass
class ModelHealth:
    model_id: str
    successes: int = 0
    failures: int = 0
    timeouts: int = 0
    consecutive_failures: int = 0
    last_failure_at: float = 0.0
    last_success_at: float = 0.0
    last_error: str = ""
    last_failure_kind: str = ""
    avoided_until: float = 0.0
    latencies_ms: list[float] = field(default_factory=list)

    def average_latency_ms(self) -> float:
        return (
            round(sum(self.latencies_ms) / len(self.latencies_ms), 2) if self.latencies_ms else 0.0
        )

    def failure_rate(self) -> float:
        total = self.successes + self.failures
        return round(self.failures / total, 4) if total else 0.0

    def avoided(self, now: float | None = None) -> bool:
        return (now or time.time()) < self.avoided_until

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "successes": self.successes,
            "failures": self.failures,
            "timeouts": self.timeouts,
            "consecutive_failures": self.consecutive_failures,
            "failure_rate": self.failure_rate(),
            "average_latency_ms": self.average_latency_ms(),
            "last_error": self.last_error[:500],
            "last_failure_kind": self.last_failure_kind,
            "last_failure_at": self.last_failure_at,
            "last_success_at": self.last_success_at,
            "avoided": self.avoided(),
            "avoided_until": self.avoided_until,
        }


_lock = threading.RLock()
_health: dict[str, ModelHealth] = {}


def reset() -> None:
    with _lock:
        _health.clear()


def _entry(model_id: str) -> ModelHealth:
    entry = _health.get(model_id)
    if entry is None:
        if len(_health) >= MAX_TRACKED_MODELS:
            # Bounded state: forget the least recently active model.
            oldest = min(_health.values(), key=lambda h: max(h.last_success_at, h.last_failure_at))
            _health.pop(oldest.model_id, None)
        entry = ModelHealth(model_id=model_id)
        _health[model_id] = entry
    return entry


def record_success(model_id: str, *, latency_ms: float = 0.0) -> ModelHealth:
    with _lock:
        entry = _entry(model_id)
        entry.successes += 1
        entry.consecutive_failures = 0
        entry.avoided_until = 0.0
        entry.last_success_at = time.time()
        if latency_ms:
            entry.latencies_ms.append(latency_ms)
            del entry.latencies_ms[:-LATENCY_SAMPLES]
        return entry


def record_failure(model_id: str, *, kind: str = "", error: str = "") -> ModelHealth:
    with _lock:
        entry = _entry(model_id)
        entry.failures += 1
        entry.consecutive_failures += 1
        entry.last_failure_at = time.time()
        entry.last_error = str(error or "")
        entry.last_failure_kind = kind
        if kind == "timeout":
            entry.timeouts += 1
        if entry.consecutive_failures >= FAILURE_THRESHOLD:
            # Temporary, explainable, and self-clearing.
            entry.avoided_until = time.time() + COOLDOWN_S
        return entry


def get(model_id: str) -> ModelHealth | None:
    with _lock:
        return _health.get(model_id)


def snapshot() -> list[dict[str, Any]]:
    with _lock:
        return [h.to_dict() for h in sorted(_health.values(), key=lambda h: h.model_id)]


def is_avoided(model_id: str) -> bool:
    with _lock:
        entry = _health.get(model_id)
        return bool(entry and entry.avoided())


def avoidance_reason(model_id: str) -> str:
    with _lock:
        entry = _health.get(model_id)
        if not entry or not entry.avoided():
            return ""
        remaining = int(entry.avoided_until - time.time())
        return (
            f"temporarily avoided after {entry.consecutive_failures} consecutive failures "
            f"({entry.last_failure_kind or 'unknown'}); {max(0, remaining)}s remaining"
        )


def clear(model_id: str) -> bool:
    """Reset a model's avoidance. Health tracking must always be recoverable."""
    with _lock:
        entry = _health.get(model_id)
        if not entry:
            return False
        entry.consecutive_failures = 0
        entry.avoided_until = 0.0
        return True
