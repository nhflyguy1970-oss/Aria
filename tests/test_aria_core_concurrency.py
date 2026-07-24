"""Aria Core concurrency / thread-safety certification gates."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from aria_core.capability_bus import health, plan
from aria_core.cognitive_orchestrator import cognition_statistics
from aria_core.cognitive_orchestrator import reset_for_tests as reset_cognition
from aria_core.event_bus import get_bus, publish_name, subscribe
from aria_core.learning_manager import commit, learning_statistics, propose
from aria_core.learning_manager import reset_for_tests as reset_learning
from aria_core.reflex_engine import reflex_statistics, try_reflex
from aria_core.reflex_engine import reset_for_tests as reset_reflex


def setup_function():
    get_bus().reset_for_tests()
    reset_cognition()
    reset_learning()
    reset_reflex()


def test_event_bus_concurrent_publish_subscribe():
    seen = []
    lock = threading.Lock()

    def handler(event):
        with lock:
            seen.append(event.name)

    subscribe("ConcurrencyProbe", handler)
    n = 200

    def worker(i: int) -> None:
        publish_name("ConcurrencyProbe", source=f"t{i}", i=i)

    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(worker, range(n)))

    rates = get_bus().rates()
    assert rates["publish_count"] >= n
    assert rates["ring_size"] <= 1000
    assert rates["handler_errors"] == 0
    with lock:
        assert len(seen) == n


def test_learning_history_concurrent_commit():
    n = 100

    def worker(i: int) -> None:
        p = propose(kind="concurrency", payload={"i": i}, source="test")
        commit(p, lambda: {"ok": True, "i": i})

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(worker, range(n)))

    stats = learning_statistics()
    assert stats["accepted"] == n
    assert stats["total"] >= n


def test_reflex_concurrent_evaluate_stats():
    n = 150

    def worker(i: int) -> None:
        # Mix hits (hello) and misses
        msg = "hello" if i % 2 == 0 else f"complex planning request {i}"
        try_reflex(msg)

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(worker, range(n)))

    stats = reflex_statistics()
    assert stats["total"] == n
    assert stats["matched"] + stats["escalated"] + stats["failed"] == n
    assert stats["matched"] >= 1
    assert stats["escalated"] >= 1


def test_capability_bus_concurrent_health_and_plan():
    errors: list[BaseException] = []

    def worker(_: int) -> None:
        try:
            h = health()
            assert "ok" in h
            p = plan(action="status")
            assert p.get("ok") is True
        except BaseException as exc:  # noqa: BLE001 — collect for assertion
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(worker, i) for i in range(40)]
        for f in as_completed(futs):
            f.result()

    assert errors == []
    # Cap Bus plan/status goes through cognition orchestrator
    assert cognition_statistics()["total"] >= 1


def test_primary_remember_serializes_context_frame(monkeypatch):
    """Concurrent PRIMARY encodes must not clobber a shared ContextFrame mid-flight."""
    import time

    from aria_core import acm_bridge

    class _FakeEngine:
        def __init__(self) -> None:
            self.context = None
            self._inflight = 0
            self._lock = threading.Lock()
            self.max_inflight = 0
            self.encoded = 0

        def encode(self, content, **kwargs):  # noqa: ANN001
            with self._lock:
                self._inflight += 1
                self.max_inflight = max(self.max_inflight, self._inflight)
            # Hold briefly so concurrent callers would overlap without engine_exclusive
            time.sleep(0.01)
            with self._lock:
                self._inflight -= 1
                self.encoded += 1
            return {"encoded": True, "experience_id": f"e-{self.encoded}", "concept_id": "c1"}

    fake = _FakeEngine()
    monkeypatch.setattr(acm_bridge, "get_engine", lambda: fake)
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")

    def worker(i: int) -> None:
        out = acm_bridge.primary_remember(f"fact {i}", entry_type="fact")
        assert out.get("encoded") is True

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(worker, range(24)))

    assert fake.encoded == 24
    assert fake.max_inflight == 1
