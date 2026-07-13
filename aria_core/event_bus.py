"""Aria Core Event Bus (Phase 4).

In-process publish/subscribe only. Publish never changes caller behavior:
handler and bus failures are swallowed/logged.
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from aria_core.event_contracts import get_contract, list_contracts, validate_contracts
from aria_core.event_types import ALL_EVENT_TYPES, EVENT_VERSION
from aria_core.ownership import module_ownership

OWNER = module_ownership("events")
logger = logging.getLogger("aria_core.event_bus")

Handler = Callable[["CoreEvent"], None]
WILDCARD = "*"

_DEFAULT_RING = 1000


@dataclass
class CoreEvent:
    """Immutable-ish event envelope (payload may be mutated by careless handlers)."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: float = field(default_factory=time.time)
    version: str = EVENT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "payload": dict(self.payload),
            "source": self.source,
            "ts": self.ts,
            "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.ts)),
            "version": self.version,
        }


class InProcessEventBus:
    """Deterministic in-process bus with observability ring."""

    def __init__(self, *, ring_size: int | None = None) -> None:
        self._lock = threading.RLock()
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)
        self._publishers: dict[str, int] = defaultdict(int)
        self._handler_errors = 0
        self._publish_count = 0
        self._latency_ms: deque[float] = deque(maxlen=200)
        size = ring_size or self._env_ring()
        self._ring: deque[dict[str, Any]] = deque(maxlen=size)
        self._started = time.time()

    @staticmethod
    def _env_ring() -> int:
        try:
            return max(100, int(os.getenv("ARIA_CORE_EVENT_RING", str(_DEFAULT_RING))))
        except ValueError:
            return _DEFAULT_RING

    def subscribe(self, event_name: str, handler: Handler) -> None:
        with self._lock:
            handlers = self._subscribers[event_name]
            if handler not in handlers:
                handlers.append(handler)

    def unsubscribe(self, event_name: str, handler: Handler) -> None:
        with self._lock:
            handlers = self._subscribers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)

    def listeners(self, event_name: str | None = None) -> dict[str, int] | list[str]:
        with self._lock:
            if event_name is None:
                return {k: len(v) for k, v in sorted(self._subscribers.items()) if v}
            return [getattr(h, "__name__", str(h)) for h in self._subscribers.get(event_name, [])]

    def publish(self, event: CoreEvent) -> None:
        t0 = time.perf_counter()
        with self._lock:
            self._publish_count += 1
            self._publishers[event.source or "unknown"] += 1
            named = list(self._subscribers.get(event.name, []))
            wild = list(self._subscribers.get(WILDCARD, []))
            self._ring.appendleft(event.to_dict())
        for handler in named + wild:
            try:
                handler(event)
            except Exception as exc:
                with self._lock:
                    self._handler_errors += 1
                logger.warning(
                    "Event handler failed for %s: %s",
                    event.name,
                    exc,
                )
        elapsed = (time.perf_counter() - t0) * 1000.0
        with self._lock:
            self._latency_ms.append(elapsed)

    def publish_name(self, name: str, *, source: str = "", **payload: Any) -> CoreEvent:
        event = CoreEvent(name=name, payload=dict(payload), source=source)
        self.publish(event)
        return event

    def recent(self, *, limit: int = 100, name: str = "", query: str = "") -> list[dict[str, Any]]:
        q = (query or "").strip().lower()
        n = (name or "").strip()
        with self._lock:
            items = list(self._ring)
        out: list[dict[str, Any]] = []
        for item in items:
            if n and item.get("name") != n:
                continue
            if q:
                blob = f"{item.get('name')} {item.get('source')} {item.get('payload')}".lower()
                if q not in blob:
                    continue
            out.append(item)
            if len(out) >= limit:
                break
        return out

    def rates(self) -> dict[str, Any]:
        with self._lock:
            elapsed = max(0.001, time.time() - self._started)
            count = self._publish_count
            lat = list(self._latency_ms)
            by_name: dict[str, int] = defaultdict(int)
            for item in self._ring:
                by_name[str(item.get("name"))] += 1
            pubs = dict(self._publishers)
            errors = self._handler_errors
        lat_sorted = sorted(lat)
        p50 = lat_sorted[len(lat_sorted) // 2] if lat_sorted else 0.0
        return {
            "publish_count": count,
            "publishes_per_sec": round(count / elapsed, 3),
            "handler_errors": errors,
            "latency_p50_ms": round(p50, 3),
            "latency_max_ms": round(max(lat_sorted), 3) if lat_sorted else 0.0,
            "by_name_in_ring": dict(sorted(by_name.items())),
            "by_publisher": pubs,
            "ring_size": len(self._ring) if hasattr(self, "_ring") else 0,
            "uptime_s": round(elapsed, 1),
        }

    def clear_ring(self) -> None:
        with self._lock:
            self._ring.clear()

    def reset_for_tests(self) -> None:
        with self._lock:
            self._subscribers.clear()
            self._publishers.clear()
            self._handler_errors = 0
            self._publish_count = 0
            self._latency_ms.clear()
            self._ring.clear()
            self._started = time.time()


_BUS = InProcessEventBus()


def get_bus() -> InProcessEventBus:
    return _BUS


def subscribe(event_name: str, handler: Handler) -> None:
    _BUS.subscribe(event_name, handler)


def unsubscribe(event_name: str, handler: Handler) -> None:
    _BUS.unsubscribe(event_name, handler)


def publish(event: CoreEvent) -> None:
    _BUS.publish(event)


def publish_name(name: str, *, source: str = "", **payload: Any) -> CoreEvent | None:
    """Publish; never raise into callers."""
    try:
        return _BUS.publish_name(name, source=source, **payload)
    except Exception as exc:
        logger.warning("Event publish failed for %s: %s", name, exc)
        return None


def safe_publish(name: str, *, source: str = "", **payload: Any) -> None:
    publish_name(name, source=source, **payload)


def recent_events(*, limit: int = 100, name: str = "", query: str = "") -> list[dict[str, Any]]:
    return _BUS.recent(limit=limit, name=name, query=query)


def replay_ring(*, limit: int = 100, name: str = "") -> list[dict[str, Any]]:
    """Phase 4 replay = re-read ring buffer (not durable re-delivery)."""
    return recent_events(limit=limit, name=name)


def mission_control_panel(
    *,
    limit: int = 100,
    name: str = "",
    query: str = "",
) -> dict[str, Any]:
    rates = _BUS.rates()
    listeners = _BUS.listeners()
    return {
        "ok": True,
        "title": "Aria Core Event Bus",
        "version": EVENT_VERSION,
        "owner": OWNER["owner"],
        "event_types": list(ALL_EVENT_TYPES),
        "subscribers": listeners,
        "publishers": rates.get("by_publisher") or {},
        "rates": rates,
        "latency": {
            "p50_ms": rates.get("latency_p50_ms"),
            "max_ms": rates.get("latency_max_ms"),
        },
        "errors": {"handler_errors": rates.get("handler_errors", 0)},
        "live_events": recent_events(limit=limit, name=name, query=query),
        "replay": replay_ring(limit=min(limit, 50), name=name),
        "contracts_ok": not validate_contracts(),
        "contract_count": len(list_contracts()),
        "note": "In-process only. Visibility; organs unchanged.",
    }


def describe_event_type(name: str) -> dict[str, Any] | None:
    return get_contract(name)
