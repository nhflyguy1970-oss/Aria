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
    monkeypatch.setattr(
        "jarvis.ollama_runtime.ensure_chat_model_ready",
        lambda model=None, **k: {"ok": True, "action": "already_ready", "model": model},
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


def test_embed_available_is_tags_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """embed_available must not call live embed() — that thrashs VRAM vs chat."""
    import jarvis.llm as llm_mod

    llm_mod._EMBED_AVAIL_CACHE.clear()
    called = {"embed": False}

    def boom(*a, **k):
        called["embed"] = True
        raise AssertionError("live embed must not run")

    monkeypatch.setattr(llm_mod, "embed_text", boom)
    monkeypatch.setattr(llm_mod, "model_for", lambda role: "nomic-embed-text:latest")
    monkeypatch.setattr(
        "jarvis.ollama_health.check_ollama",
        lambda **k: {"running": True, "models": ["nomic-embed-text:latest", "qwen2.5:7b"]},
    )
    assert llm_mod.embed_available() is True
    assert called["embed"] is False


def test_ask_stream_applies_default_num_ctx(monkeypatch: pytest.MonkeyPatch) -> None:
    import jarvis.llm as llm_mod

    seen: dict = {}

    def fake_chat(**kwargs):
        seen.update(kwargs)
        yield {"message": {"content": "hi"}}

    monkeypatch.setattr(
        "jarvis.inference.policy.select_route",
        lambda model, role="general", messages=None: SimpleNamespace(
            backend="ollama", model=model
        ),
    )
    monkeypatch.setattr(llm_mod, "chat", fake_chat)
    monkeypatch.setenv("JARVIS_OLLAMA_NUM_CTX", "4096")
    tokens = list(llm_mod.ask_stream("qwen2.5:7b", [{"role": "user", "content": "hi"}]))
    assert tokens == ["hi"]
    opts = (seen.get("options") or {})
    assert opts.get("num_ctx") == 4096


def test_embed_text_skips_during_chat_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    import jarvis.llm as llm_mod
    from jarvis.ollama_runtime import chat_priority_section

    called = {"embed": False}

    def boom(*a, **k):
        called["embed"] = True
        raise AssertionError("embed must not run under chat priority")

    monkeypatch.setattr(llm_mod, "embed", boom)
    monkeypatch.setattr(llm_mod, "model_for", lambda role: "nomic-embed-text:latest")
    with chat_priority_section():
        assert llm_mod.embed_text("ping") == []
    assert called["embed"] is False


def test_chat_priority_grace_blocks_embeds_after_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inter-request grace must keep embeds deferred after the stream ends."""
    import jarvis.llm as llm_mod
    import jarvis.ollama_runtime as rt

    monkeypatch.setenv("JARVIS_CHAT_PRIORITY_GRACE_S", "30")
    # Reset module state between tests.
    with rt._chat_priority_lock:
        rt._chat_priority = 0
        rt._chat_priority_grace_until = 0.0

    called = {"embed": False}

    def boom(*a, **k):
        called["embed"] = True
        raise AssertionError("embed must not run during chat priority grace")

    monkeypatch.setattr(llm_mod, "embed", boom)
    monkeypatch.setattr(llm_mod, "model_for", lambda role: "nomic-embed-text:latest")

    rt.begin_chat_priority()
    rt.end_chat_priority()
    assert rt.chat_priority_active() is True
    assert llm_mod.embed_text("ping") == []
    assert called["embed"] is False

    # Expire grace immediately for cleanup.
    with rt._chat_priority_lock:
        rt._chat_priority_grace_until = 0.0
    try:
        rt._chat_priority_flag_path().unlink(missing_ok=True)
    except Exception:
        pass


def test_ensure_skips_reload_inside_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    import jarvis.ollama_runtime as rt

    monkeypatch.setattr(
        rt,
        "free_slot_for_chat_model",
        lambda model: {"ok": True, "action": "noop", "loaded": []},
    )
    monkeypatch.setattr(rt, "runner_info", lambda model: {"name": model, "size_vram": 0})

    def boom(*a, **k):
        raise AssertionError("warmup must not run with allow_reload=False")

    monkeypatch.setattr(rt, "warmup_chat_model", boom)
    monkeypatch.setattr(rt, "unload_model", boom)
    out = rt.ensure_chat_model_ready("qwen2.5:7b", allow_reload=False)
    assert out["ok"] is False
    assert out["action"] == "stream_skip_reload"


def test_ensure_chat_model_ready_already_resident(monkeypatch: pytest.MonkeyPatch) -> None:
    import jarvis.ollama_runtime as rt

    monkeypatch.setattr(
        rt,
        "free_slot_for_chat_model",
        lambda model: {"ok": True, "action": "already_loaded", "loaded": [model]},
    )
    monkeypatch.setattr(
        rt,
        "runner_info",
        lambda model: {
            "name": model,
            "size_vram": 5_000_000_000,
            "context_length": 8192,
        },
    )

    def boom(*a, **k):
        raise AssertionError("warmup must not run when already resident")

    monkeypatch.setattr(rt, "warmup_chat_model", boom)
    out = rt.ensure_chat_model_ready("qwen2.5:7b")
    assert out["ok"] is True
    assert out["action"] == "already_ready"


def test_ensure_reloads_oversized_host_default_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """Daemon OLLAMA_CONTEXT_LENGTH=32768 residents must not count as chat-ready."""
    import jarvis.ollama_runtime as rt

    monkeypatch.setenv("JARVIS_OLLAMA_NUM_CTX", "8192")
    monkeypatch.setenv("OLLAMA_NUM_PARALLEL", "2")
    monkeypatch.setattr(rt.time, "sleep", lambda s: None)
    calls = {"unload": 0, "warm": 0}
    state = {"n": 0}

    monkeypatch.setattr(
        rt,
        "free_slot_for_chat_model",
        lambda model: {"ok": True, "action": "noop", "loaded": []},
    )

    def info(model):
        state["n"] += 1
        # First checks see oversized host-default context; after unload+warm, match chat.
        if calls["warm"] == 0:
            return {"name": model, "size_vram": 5_000_000_000, "context_length": 32768}
        return {"name": model, "size_vram": 5_000_000_000, "context_length": 8192}

    monkeypatch.setattr(rt, "runner_info", info)

    def unload(model, **k):
        calls["unload"] += 1
        return True

    def warm(model=None):
        calls["warm"] += 1
        return {"ok": True, "load_ms": 1, "total_s": 0.1}

    monkeypatch.setattr(rt, "unload_model", unload)
    monkeypatch.setattr(rt, "warmup_chat_model", warm)

    out = rt.ensure_chat_model_ready("qwen2.5:7b", timeout=30)
    assert out["ok"] is True
    assert calls["unload"] >= 1
    assert calls["warm"] >= 1
    assert out["action"] == "warmed"
