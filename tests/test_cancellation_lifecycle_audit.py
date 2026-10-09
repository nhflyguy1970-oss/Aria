"""Audit-pass repairs: non-stream cancellation, terminal cancel event, lock holders.

The first repair closed the streaming path. The audit found the non-streaming
path still bypassed cancellation entirely and that cancelled streams ended with
no terminal event — which drove the UI into a non-streaming retry of the very
request the user had stopped, restoring the original
"Another request is still finishing" chain through a different door.
"""

from __future__ import annotations

import inspect
import threading
import time

import pytest

from jarvis import chat_cancel


@pytest.fixture(autouse=True)
def _clean_cancel_state():
    for rid in chat_cancel.active_ids():
        chat_cancel.unregister_active(rid)
    yield
    for rid in chat_cancel.active_ids():
        chat_cancel.unregister_active(rid)


# --- P0 #1: non-streaming path joins the cancellation architecture ----------


def test_process_accepts_request_id() -> None:
    from jarvis.assistant import JarvisAssistant

    sig = inspect.signature(JarvisAssistant.process)
    assert "request_id" in sig.parameters, "non-stream process must take a request_id"


def test_process_binds_cancel_context_and_registers_active() -> None:
    """process() must bind_current + register_active like process_stream does."""
    from jarvis.assistant import JarvisAssistant

    src = inspect.getsource(JarvisAssistant.process)
    assert "bind_current(" in src, "non-stream turn never bound a cancel context"
    assert "register_active(" in src, "non-stream turn was invisible to cancel_active"
    assert "unregister_active(" in src
    assert "reset_current(" in src
    assert "finish(" in src


def test_process_cleanup_is_in_finally() -> None:
    """Cleanup must survive success, exception, cancellation and provider failure."""
    from jarvis.assistant import JarvisAssistant

    src = inspect.getsource(JarvisAssistant.process)
    # Everything after the last 'finally:' must contain the context reset.
    assert src.count("finally:") >= 2
    tail = src.rsplit("finally:", 1)[1]
    assert "reset_current(" in tail
    inner = src.rsplit("finally:", 2)[1]
    assert "unregister_active(" in inner and "finish(" in inner


def test_server_passes_request_id_to_non_stream_process() -> None:
    from jarvis.gui import server

    src = inspect.getsource(server.chat)
    tail = src.split("assistant.process,", 1)[1].split(")", 1)[0]
    assert "request_id" in tail, "server must hand the real request id to process()"


def test_sync_dispatch_yields_request_lock_for_all_actions() -> None:
    """Non-chat dispatch (web_search) must not hold the lock through long work."""
    from jarvis import conversation_pipeline

    src = inspect.getsource(conversation_pipeline.dispatch_action)
    head = src.split("return call_action(", 1)[0]
    assert "yield_request_lock()" in head
    # The old gate only released for chat; research kept the lock.
    assert 'if action == "chat" and hasattr(assistant, "yield_request_lock")' not in head


def test_cancel_reaches_web_search_via_sync_context() -> None:
    """A cancelled non-stream research stops before doing any searching."""
    from jarvis.behaviors.knowledge._extracted import KnowledgeOperations

    calls = {"n": 0}

    def _never(*a, **k):
        calls["n"] += 1
        return [{"title": "t", "url": "u", "snippet": "s"}]

    import jarvis.web_search as ws

    orig = ws.search
    ws.search = _never
    try:
        class _Ctx:
            session = None

        token = chat_cancel.bind_current("sync-req-1")
        try:
            chat_cancel.register_active("sync-req-1")
            chat_cancel.cancel("sync-req-1")
            out = KnowledgeOperations.web_search(_Ctx(), {"query": "x"}, "x")
        finally:
            chat_cancel.finish("sync-req-1")
            chat_cancel.unregister_active("sync-req-1")
            chat_cancel.reset_current(token)
    finally:
        ws.search = orig

    assert out.get("stopped") is True
    assert calls["n"] == 0


def test_session_interrupt_sees_a_registered_sync_request() -> None:
    """stop must report the non-stream request in stopped_requests."""
    from jarvis.handlers.meta import session_interrupt

    chat_cancel.register_active("sync-victim")
    try:
        result = session_interrupt(_StubAssistant(), {}, "stop")
        assert "sync-victim" in result["stopped_requests"]
        assert chat_cancel.is_cancelled("sync-victim") is True
    finally:
        chat_cancel.finish("sync-victim")
        chat_cancel.unregister_active("sync-victim")


class _StubSession:
    pending_clarification = None


class _StubAssistant:
    def __init__(self) -> None:
        self.session = _StubSession()


# --- P0 #2: cancelled streams emit a terminal cancellation event -----------


def test_stream_emits_terminal_cancellation_event() -> None:
    from jarvis.gui import server

    src = inspect.getsource(server.chat)
    assert "bridge.closed" in src, "server cannot tell a cancel from a normal end"
    assert '"code": "CANCELLED"' in src
    assert '"cancelled": True' in src
    assert 'reason="cancelled"' in src


def test_successful_stream_still_records_done() -> None:
    from jarvis.gui import server

    src = inspect.getsource(server.chat)
    assert 'complete_request(stream_rid, reason="done")' in src


def test_cancelled_and_done_are_mutually_exclusive() -> None:
    """Never emit both a cancellation terminal and a success terminal."""
    from jarvis.gui import server

    src = inspect.getsource(server.chat)
    assert "if not timed_out and not saw_done and bridge.closed:" in src
    assert "elif not timed_out:" in src


def test_finally_does_not_recancel_an_already_cancelled_stream() -> None:
    from jarvis.gui import server

    src = inspect.getsource(server.chat)
    assert "if not stream_completed and not stream_cancelled:" in src


def test_bridge_closed_flag_marks_external_cancellation() -> None:
    """chat_cancel.cancel() must flip bridge.closed through the registered closer."""
    from jarvis.async_util import stream_sync_iter

    bridge = stream_sync_iter(lambda: iter(()), thread_name="t-cancel-flag")
    chat_cancel.register_active("rid-flag", bridge.close)
    try:
        assert bridge.closed is False
        chat_cancel.cancel("rid-flag")
        assert bridge.closed is True
    finally:
        chat_cancel.finish("rid-flag")
        chat_cancel.unregister_active("rid-flag")


# --- P0 #3: the UI never auto-retries a deliberately stopped request -------


def _chat_send_js() -> str:
    from pathlib import Path

    return Path("jarvis/gui/static/chat_send.js").read_text()


def test_ui_recognises_server_cancellation_terminal() -> None:
    js = _chat_send_js()
    assert 'event.cancelled === true || event.code === "CANCELLED"' in js
    assert "serverCancelled = true" in js


def test_ui_does_not_retry_a_cancelled_stream() -> None:
    """The retry branch must be unreachable once the server said 'cancelled'."""
    js = _chat_send_js()
    assert "if (c.chatStopRequested || serverCancelled) {" in js
    guard = js.split("if (c.chatStopRequested || serverCancelled) {", 1)[1]
    retry_branch = guard.split("} else if (!gotDone) {", 1)
    assert len(retry_branch) == 2, "retry branch must sit behind the stopped guard"
    assert "sendMessage(text, true" in retry_branch[1], "legitimate retry must survive"


def test_ui_retry_still_exists_for_genuine_transport_failure() -> None:
    """Do not broadly disable recovery — only stopped requests are excluded."""
    js = _chat_send_js()
    assert "Stream dropped — retrying without streaming…" in js


# --- P1 #5/#6/#7: remaining long-running lock holders ---------------------


def _stream_src() -> str:
    from jarvis.assistant import JarvisAssistant

    return inspect.getsource(JarvisAssistant._process_stream_unlocked)


@pytest.mark.parametrize(
    "marker",
    ['"coding_agent_stream",', '"coding_create_stream",'],
)
def test_coding_branches_yield_lock_before_long_work(marker: str) -> None:
    src = _stream_src()
    idx = src.index(marker)
    window = src[max(0, idx - 700) : idx]
    assert "self.yield_request_lock()" in window, (
        f"long coding work at {marker} still holds the global request lock"
    )


def test_vision_branch_yields_lock_and_checks_cancel() -> None:
    src = _stream_src()
    idx = src.index("self.vision.analyze_stream(")
    before = src[max(0, idx - 900) : idx]
    after = src[idx : idx + 700]
    assert "self.yield_request_lock()" in before, "vision still holds the request lock"
    assert "current_cancelled()" in before
    assert "current_cancelled()" in after, "vision token loop needs a cancel checkpoint"


def test_briefing_branch_yields_lock_and_checks_cancel() -> None:
    src = _stream_src()
    idx = src.index("expand_headline_detail_stream(")
    before = src[max(0, idx - 1200) : idx]
    after = src[idx : idx + 500]
    assert "self.yield_request_lock()" in before, "briefing still holds the request lock"
    assert before.count("current_cancelled()") >= 2
    assert "current_cancelled()" in after


def test_safe_vision_actions_unchanged() -> None:
    """analyze_region / compare_images were already safe — keep them on dispatch."""
    src = _stream_src()
    assert 'status="Analyzing region…", prefer_queue=False' in src
    assert 'status="Comparing images…", prefer_queue=False' in src


# --- stop semantics: documented as-is (global kill switch) ----------------


def test_cancel_active_cancels_every_other_request() -> None:
    """Documents CURRENT semantics: stop is a global kill switch."""
    chat_cancel.register_active("multi-a")
    chat_cancel.register_active("multi-b")
    chat_cancel.register_active("multi-self")
    token = chat_cancel.bind_current("multi-self")
    try:
        stopped = chat_cancel.cancel_active(exclude=chat_cancel.current_request_id())
        assert set(stopped) == {"multi-a", "multi-b"}
        assert chat_cancel.is_cancelled("multi-self") is False
    finally:
        for r in ("multi-a", "multi-b", "multi-self"):
            chat_cancel.finish(r)
            chat_cancel.unregister_active(r)
        chat_cancel.reset_current(token)


def test_cancellation_is_request_specific() -> None:
    closed_a = threading.Event()
    closed_b = threading.Event()
    chat_cancel.register_active("iso-a", closed_a.set)
    chat_cancel.register_active("iso-b", closed_b.set)
    try:
        chat_cancel.cancel("iso-a")
        assert closed_a.is_set() is True
        assert closed_b.is_set() is False
        assert chat_cancel.is_cancelled("iso-b") is False
    finally:
        for r in ("iso-a", "iso-b"):
            chat_cancel.finish(r)
            chat_cancel.unregister_active(r)


def test_no_stale_registration_after_cancel_and_cleanup() -> None:
    chat_cancel.register_active("stale-1")
    chat_cancel.cancel("stale-1")
    chat_cancel.unregister_active("stale-1")
    chat_cancel.finish("stale-1")
    assert "stale-1" not in chat_cancel.active_ids()
    assert chat_cancel.is_cancelled("stale-1") is False


def test_next_request_can_acquire_immediately_after_yield() -> None:
    """The original chain: a yielded lock must be instantly reusable."""
    from jarvis.assistant import JarvisAssistant

    class _A:
        _holding_request_lock = JarvisAssistant._holding_request_lock
        yield_request_lock = JarvisAssistant.yield_request_lock

        def __init__(self) -> None:
            self._request_lock = threading.Lock()
            self._lock_state = threading.local()

    a = _A()
    assert a._request_lock.acquire(timeout=1.0)
    a._holding_request_lock = True
    a.yield_request_lock()
    t0 = time.monotonic()
    assert a._request_lock.acquire(timeout=1.0)
    assert time.monotonic() - t0 < 0.5
    a._request_lock.release()
