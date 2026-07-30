"""First-token latency — cancellable streams and chat-path health checks."""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def test_iter_blocking_cancellable_stops_on_cancel() -> None:
    from jarvis import chat_cancel
    from jarvis.llm import _iter_blocking_cancellable

    key = "cancel-test-1"
    chat_cancel.begin(key)

    def forever():
        while True:
            time.sleep(10)
            yield {"message": {"content": "late"}}

    chat_cancel.cancel(key)
    t0 = time.perf_counter()
    items = list(_iter_blocking_cancellable(forever(), cancel_key=key, poll_s=0.1))
    elapsed = time.perf_counter() - t0
    assert items == []
    assert elapsed < 2.0
    chat_cancel.finish(key)


def test_conversation_stream_uses_tags_only_health(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.behaviors.conversation import ConversationEngine

    calls: list[dict] = []

    def fake_check(*, soft_probe: bool = True, force_probe: bool = False):
        calls.append({"soft_probe": soft_probe, "force_probe": force_probe})
        return {"running": True, "health_state": "healthy"}

    monkeypatch.setattr("jarvis.behaviors.conversation.check_ollama", fake_check)
    monkeypatch.setattr(
        ConversationEngine,
        "prepare_user_message",
        lambda self, message, params: message,
    )
    monkeypatch.setattr(ConversationEngine, "try_strict_instructions", lambda self, m: None)
    monkeypatch.setattr(
        ConversationEngine,
        "build_context_prefix",
        lambda self, m: ("", [], []),
    )
    monkeypatch.setattr(
        ConversationEngine,
        "messages_for_llm",
        lambda self, pending, prefix: [{"role": "user", "content": "hi"}],
    )

    def fake_stream(*a, **k):
        yield "ok"
        return
        yield  # pragma: no cover

    monkeypatch.setattr("jarvis.llm.ask_stream", fake_stream)
    monkeypatch.setattr(
        "jarvis.capability_routing.resolve_conversation_model",
        lambda *a, **k: ("test-model", "conversation"),
    )

    assistant = SimpleNamespace(
        conversation=SimpleNamespace(
            messages=[],
            add_user=lambda *a, **k: None,
            add_assistant=lambda *a, **k: None,
            pop_last_user=lambda: None,
        ),
        session=SimpleNamespace(chat_model=""),
        branches=SimpleNamespace(persist=lambda **k: None),
    )
    eng = ConversationEngine(assistant)
    events = []
    for ev in eng.execute_stream("Hello", {}, request_id="r1"):
        events.append(ev)
        if ev.get("type") == "token":
            break
    assert calls and calls[0]["soft_probe"] is False
    assert any(e.get("type") == "status" for e in events)
    assert any(e.get("type") == "token" for e in events)


def test_process_stream_lock_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.assistant import JarvisAssistant

    # Avoid full init cost — only need lock behavior.
    a = MagicMock(spec=JarvisAssistant)
    a._request_lock = __import__("threading").Lock()
    a._stream_lite_ui = False
    a._request_lock.acquire()
    monkeypatch.setenv("JARVIS_REQUEST_LOCK_TIMEOUT_S", "0.2")

    # Bind real method
    events = list(JarvisAssistant.process_stream(a, "hi"))
    assert events
    assert events[0].get("ok") is False or (events[0].get("type") == "done" and events[0].get("ok") is False)
    a._request_lock.release()
