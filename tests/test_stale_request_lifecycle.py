"""Bug 1 — stale active-request lifecycle.

A web_search that outlived its consumer kept the global request lock, so every
later turn was refused with "Another request is still finishing", and "stop" was
cosmetic. These cover the lock, the bridge, cancellation and ownership.
"""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

from jarvis import chat_cancel
from jarvis.async_util import stream_sync_iter


@pytest.fixture(autouse=True)
def _clean_cancel_state():
    for rid in chat_cancel.active_ids():
        chat_cancel.unregister_active(rid)
    yield
    for rid in chat_cancel.active_ids():
        chat_cancel.unregister_active(rid)


class _FakeAssistant:
    """Minimal stand-in exercising the real lock/ownership code paths."""

    def __init__(self) -> None:
        self._request_lock = threading.Lock()
        self._lock_state = threading.local()

    # Bind the real property so ownership semantics are the ones under test.
    from jarvis.assistant import JarvisAssistant as _JA

    _holding_request_lock = _JA._holding_request_lock
    yield_request_lock = _JA.yield_request_lock
    del _JA


# --- 1/3/4: the bridge releases the producer and the lock on abandonment -----


def test_bridge_close_stops_producer_and_runs_generator_finally() -> None:
    """Consumer abandons mid-iteration -> generator finally runs, lock released."""
    lock = threading.Lock()
    lock.acquire()
    released = threading.Event()

    def gen():
        try:
            for i in range(10_000):
                yield {"type": "token", "content": str(i)}
                time.sleep(0.001)
        finally:
            lock.release()
            released.set()

    async def drive() -> None:
        bridge = stream_sync_iter(gen, thread_name="test-abandon")
        ait = bridge.__aiter__()
        first = await ait.__anext__()
        assert first["type"] == "token"
        # Abandon mid-iteration, exactly like the first-progress timeout did.
        assert await bridge.aclose(timeout=10.0) is True

    asyncio.run(drive())
    assert released.wait(5.0), "generator finally never ran — lock would stay held"
    assert lock.acquire(timeout=1.0), "request lock was not released"
    lock.release()


def test_bridge_close_is_idempotent_and_safe_before_start() -> None:
    bridge = stream_sync_iter(lambda: iter(()), thread_name="test-idem")
    bridge.close()
    bridge.close()
    assert bridge.closed is True
    assert bridge.wait_closed(1.0) is True


def test_bridge_leaves_no_live_producer_thread_after_close() -> None:
    """FIRST_PROGRESS_TIMEOUT must not leave the producer thread running."""
    name = "test-no-live-thread"

    def gen():
        for i in range(10_000):
            yield {"type": "status", "message": str(i)}
            time.sleep(0.001)

    async def drive() -> None:
        bridge = stream_sync_iter(gen, thread_name=name)
        ait = bridge.__aiter__()
        await ait.__anext__()
        assert await bridge.aclose(timeout=10.0) is True

    asyncio.run(drive())
    time.sleep(0.2)
    alive = [t for t in threading.enumerate() if t.name == name and t.is_alive()]
    assert not alive, f"producer thread still alive: {alive}"


# --- 2: dispatched (non-chat) actions must not hold the lock ----------------


def test_dispatched_action_releases_request_lock() -> None:
    """_dispatched_events yields the lock before long research runs."""
    a = _FakeAssistant()
    assert a._request_lock.acquire(timeout=1.0)
    a._holding_request_lock = True

    a.yield_request_lock()

    assert a._holding_request_lock is False
    other = threading.Lock()

    def competitor() -> None:
        if a._request_lock.acquire(timeout=1.0):
            other.acquire()
            a._request_lock.release()

    t = threading.Thread(target=competitor)
    t.start()
    t.join(timeout=3.0)
    assert other.locked(), "second request could not acquire after yield"


def test_dispatched_events_yields_lock_before_dispatch() -> None:
    """The generic dispatch closure releases the request lock first."""
    import inspect

    from jarvis.assistant import JarvisAssistant

    src = inspect.getsource(JarvisAssistant._process_stream_unlocked)
    assert "def _dispatched_events(" in src
    body = src.split("def _dispatched_events(", 1)[1]
    head = body.split("if status:", 1)[0]
    assert "self.yield_request_lock()" in head, (
        "_dispatched_events must release the request lock before dispatching"
    )


def test_web_search_stream_branch_yields_lock_and_checks_cancel() -> None:
    """web_search has its own streaming branch — the one that actually ran.

    Live verification caught this: patching only _dispatched_events left the real
    research path holding the lock, so "stop" was still refused.
    """
    import inspect

    from jarvis.assistant import JarvisAssistant

    src = inspect.getsource(JarvisAssistant._process_stream_unlocked)
    assert 'if action == "web_search":' in src
    branch = src.split('if action == "web_search":', 1)[1]
    branch = branch.split('if action in (', 1)[0]

    before_search = branch.split('"Searching the web', 1)[0]
    assert "self.yield_request_lock()" in before_search, (
        "web_search must release the request lock before the research I/O"
    )
    # A cancel checkpoint between every long phase.
    assert branch.count("current_cancelled()") >= 4, (
        "web_search stream branch needs cancel checkpoints between research phases"
    )


# --- 5: cancellation reaches the web_search dispatch path -------------------


def test_current_cancelled_tracks_bound_request() -> None:
    token = chat_cancel.bind_current("req-a")
    try:
        chat_cancel.register_active("req-a")
        assert chat_cancel.current_cancelled() is False
        chat_cancel.cancel("req-a")
        assert chat_cancel.current_cancelled() is True
    finally:
        chat_cancel.finish("req-a")
        chat_cancel.unregister_active("req-a")
        chat_cancel.reset_current(token)


def test_web_search_stops_when_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cancelled research request returns immediately instead of searching."""
    from jarvis.behaviors.knowledge._extracted import KnowledgeOperations

    called = {"search": 0}

    def _never(*a, **k):
        called["search"] += 1
        return [{"title": "t", "url": "u", "snippet": "s"}]

    monkeypatch.setattr("jarvis.web_search.search", _never)
    monkeypatch.setattr("jarvis.profiles.web_search_disabled", lambda: False)

    class _Ctx:
        session = None

    token = chat_cancel.bind_current("req-cancelled")
    try:
        chat_cancel.register_active("req-cancelled")
        chat_cancel.cancel("req-cancelled")
        out = KnowledgeOperations.web_search(_Ctx(), {"query": "molybdenum"}, "molybdenum")
    finally:
        chat_cancel.finish("req-cancelled")
        chat_cancel.unregister_active("req-cancelled")
        chat_cancel.reset_current(token)

    assert out.get("stopped") is True, out
    assert called["search"] == 0, "cancelled research still ran the web search"


def test_synthesis_passes_cancel_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Research synthesis threads the active request id into ask_stream."""
    import inspect

    from jarvis import web_search

    src = inspect.getsource(web_search.synthesize_answer)
    assert "cancel_key=current_request_id()" in src


# --- 6/7: session_interrupt really cancels ----------------------------------


def test_session_interrupt_cancels_active_request_and_closes_stream() -> None:
    from jarvis.handlers.meta import session_interrupt

    closed = threading.Event()
    chat_cancel.register_active("req-victim", closed.set)

    token = chat_cancel.bind_current("req-stop")
    try:
        chat_cancel.register_active("req-stop")
        result = session_interrupt(_StubAssistant(), {}, "stop")
    finally:
        chat_cancel.unregister_active("req-stop")
        chat_cancel.reset_current(token)

    assert result["ok"] is True
    assert "req-victim" in result["stopped_requests"]
    assert chat_cancel.is_cancelled("req-victim") is True
    assert closed.is_set(), "stop did not close the active stream"

    chat_cancel.finish("req-victim")
    chat_cancel.unregister_active("req-victim")


def test_session_interrupt_never_cancels_itself() -> None:
    from jarvis.handlers.meta import session_interrupt

    token = chat_cancel.bind_current("req-self")
    try:
        chat_cancel.register_active("req-self")
        result = session_interrupt(_StubAssistant(), {}, "stop")
    finally:
        chat_cancel.unregister_active("req-self")
        chat_cancel.reset_current(token)

    assert "req-self" not in result["stopped_requests"]
    assert chat_cancel.is_cancelled("req-self") is False


def test_session_interrupt_preserves_pending_clarification_clear() -> None:
    from jarvis.handlers.meta import session_interrupt

    stub = _StubAssistant()
    stub.session.pending_clarification = {"type": "nlu_intent"}
    session_interrupt(stub, {}, "stop")
    assert stub.session.pending_clarification is None


class _StubSession:
    pending_clarification = None


class _StubAssistant:
    def __init__(self) -> None:
        self.session = _StubSession()


# --- 8/9: cleanup lets the next request run; a live request stays guarded ---


def test_next_request_runs_immediately_after_cleanup() -> None:
    a = _FakeAssistant()
    assert a._request_lock.acquire(timeout=1.0)
    a._holding_request_lock = True
    a.yield_request_lock()
    # A brand-new turn must acquire without waiting out the guard timeout.
    t0 = time.monotonic()
    assert a._request_lock.acquire(timeout=1.0)
    assert time.monotonic() - t0 < 0.5
    a._request_lock.release()


def test_active_request_still_blocks_a_concurrent_one() -> None:
    """Concurrency protection is preserved — the guard must still fire."""
    a = _FakeAssistant()
    assert a._request_lock.acquire(timeout=1.0)
    a._holding_request_lock = True
    try:
        assert a._request_lock.acquire(timeout=0.2) is False
    finally:
        a._holding_request_lock = False
        a._request_lock.release()


# --- 10: ownership — one thread's cleanup cannot release another's lock -----


def test_lock_ownership_is_per_thread() -> None:
    a = _FakeAssistant()
    assert a._request_lock.acquire(timeout=1.0)
    a._holding_request_lock = True  # owned by this thread

    seen: dict[str, bool] = {}

    def other_thread() -> None:
        # Thread B never acquired it, so its cleanup must be a no-op.
        seen["holding"] = a._holding_request_lock
        a.yield_request_lock()

    t = threading.Thread(target=other_thread)
    t.start()
    t.join(timeout=3.0)

    assert seen["holding"] is False, "ownership flag leaked across threads"
    assert a._holding_request_lock is True, "owner lost its own ownership flag"
    assert a._request_lock.locked(), "another thread released a lock it did not own"
    a._holding_request_lock = False
    a._request_lock.release()


# --- 11: no first-progress budget for non-token-streaming actions ----------


def test_first_progress_budget_only_for_token_streaming_actions() -> None:
    """web_search must not be charged an LLM first-token budget."""
    import inspect

    from jarvis.gui import server

    src = inspect.getsource(server.chat)
    assert 'expects_token_stream = pre_action in ("chat", "")' in src

    # The timeout branch itself must be gated, not merely the flag defined.
    branch = src.split("waited_ms = (_time.monotonic() - ", 1)[1]
    condition = branch.split("first_progress_ms", 1)[0]
    assert "expects_token_stream" in condition, (
        "first-progress timeout is not gated by expects_token_stream"
    )

    # A research action must not be charged the budget.
    for action, expected in (("chat", True), ("", True), ("web_search", False)):
        assert (action in ("chat", "")) is expected


def test_stream_closes_bridge_in_finally() -> None:
    import inspect

    from jarvis.gui import server

    src = inspect.getsource(server.chat)
    assert "await bridge.aclose(" in src, "bridge is never closed"
    tail = src.split("except Exception as e:", 1)[1]
    assert "finally:" in tail and "bridge.aclose(" in tail, (
        "bridge close must run from a finally, not only on the happy path"
    )
