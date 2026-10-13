"""Conversation failure recovery — regressions for the 2026-10-12 Living Room failure.

"What should we work on?" failed with the generic "couldn't complete that
reply" because the gateway forced num_gpu=99 on gemma4:12b: the warm-up runner
had been fitted by Ollama (33/49 layers, ComfyUI held ~4 GB), the forced full
offload reloaded the model and hit cudaMalloc OOM, and the HTTP 500 surfaced
with no retry, no fallback and no logged cause.

All provider faults here are injected with deterministic mocks. No test makes
a network call or loads a model; live verification is reported separately.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from jarvis.inference import boundary, gateway

PRIMARY = "gemma4:12b"
FAST = "qwen3:1.7b"
CLOUD = "openai/example-model"
MSG = [{"role": "user", "content": "What should we work on?"}]

# Verbatim from the Ollama journal for the failed request.
OLLAMA_OOM = (
    "llama-server startup failed after projector CPU offload retry: llama-server process has "
    "terminated: exit status 1: cudaMalloc failed: out of memory\nalloc_tensor_range: failed "
    "to allocate CUDA0 buffer of size 268435456"
)


class ResponseError(Exception):
    """Shape of ollama.ResponseError: message + HTTP status."""

    def __init__(self, error: str, status_code: int = -1):
        super().__init__(error)
        self.status_code = status_code


ROLES = {"conversation": PRIMARY, "general": PRIMARY, "fast_chat": FAST}


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    for name in ("JARVIS_CLOUD_INFERENCE", "JARVIS_OFFLINE", "JARVIS_CLOUD_PROVIDERS",
                 "JARVIS_LOCAL_RECOVERY", "JARVIS_INFERENCE_GATEWAY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(boundary, "installed_local_models", lambda **k: {PRIMARY, FAST})
    monkeypatch.setattr("jarvis.model_store.model_for", lambda role: ROLES.get(role, PRIMARY))
    monkeypatch.setattr(
        "jarvis.inference.execution_policy.apply_policy_to_route",
        lambda *, model, role="general": {"model": model, "hardware": "nvidia", "source": "explicit"},
    )
    monkeypatch.setattr(boundary, "model_capabilities", lambda model: None)
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    monkeypatch.setattr(gateway, "LOCAL_RETRY_DELAY_S", 0.0)
    monkeypatch.setattr(gateway, "LOCAL_RECONNECT_DELAY_S", 0.0)


def _stream_of(*outcomes):
    """Fake _ollama_stream: each call consumes one outcome (an exception or a text)."""
    calls: list[str] = []
    queue = list(outcomes)

    def fake(model, messages, **kwargs):
        calls.append(model)
        outcome = queue.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        yield outcome

    return fake, calls


# ------------------------------------------------------------- root cause


def test_gpu_placement_never_forces_full_offload():
    """A forced num_gpu differs from the warm-up runner (reload) and cannot shrink to fit (OOM)."""
    from jarvis.nlu.placement import ollama_options_for_device

    for device in ("nvidia", "nvidia:0", "amd", "rocm"):
        assert "num_gpu" not in ollama_options_for_device(device)
    assert ollama_options_for_device("cpu") == {"num_gpu": 0}


def test_gateway_chat_options_match_the_warmup_runner(monkeypatch):
    """Same options as ensure_chat_model_ready's probe, so Ollama reuses the resident runner."""
    from jarvis.ollama_runtime import default_options

    seen: dict = {}

    def fake(model, messages, **kwargs):
        seen.update(kwargs.get("options") or {})
        yield "ok"

    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    assert "num_gpu" not in seen
    assert {k: v for k, v in seen.items() if k in default_options()} == {
        k: v for k, v in default_options().items() if k in seen
    }


# ------------------------------------------------------------- classification


@pytest.mark.parametrize(
    "exc, category",
    [
        (ResponseError(OLLAMA_OOM, 500), "out_of_memory"),
        (ResponseError("model 'gemma9:99b' not found, try pulling it first", 404), "model_missing"),
        (ResponseError("missing", 404), "model_missing"),
        (ConnectionError("[Errno 111] Connection refused"), "connection_refused"),
        (TimeoutError("timed out"), "timeout"),
        (ResponseError("input length exceeds the context length", 400), "context_overflow"),
        (ResponseError("Unauthorized", 401), "auth_failed"),
        (ResponseError("slow down", 429), "rate_limited"),
        (ResponseError("llama runner process has terminated", 500), "model_load_failed"),
        (ResponseError("boom", 503), "service_unavailable"),
        (ValueError("JSONDecodeError: Expecting value"), "invalid_response"),
        (RuntimeError("something odd"), "internal_error"),
        (boundary.InferenceCancelled("x"), "cancelled"),
        (boundary.CloudNotPermitted("x"), "not_permitted"),
    ],
)
def test_failures_are_classified(exc, category):
    assert boundary.classify_failure(exc) == category


def test_classification_reads_the_wrapped_cause():
    try:
        try:
            raise ResponseError(OLLAMA_OOM, 500)
        except ResponseError as inner:
            raise boundary.ProviderUnavailable("ollama model 'gemma4:12b' failed") from inner
    except boundary.ProviderUnavailable as outer:
        assert boundary.classify_failure(outer) == "out_of_memory"


def test_gpu_admission_refusal_is_its_own_category():
    from jarvis.gpu_scheduler import GpuUnavailable

    wrapped = boundary.ProviderUnavailable("failed")
    wrapped.__cause__ = GpuUnavailable("RTX 3060 is busy")
    assert boundary.classify_failure(wrapped) == "gpu_busy"


# ------------------------------------------------------------- stream recovery


def test_primary_success_is_untouched():
    fake, calls = _stream_of("hello")
    usage: dict = {}
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        assert list(gateway.stream_chat(PRIMARY, MSG, role="conversation", usage=usage)) == ["hello"]
    assert calls == [PRIMARY]
    assert usage["execution_model"] == PRIMARY
    assert usage["receipt"]["fallback_used"] is False


def test_transient_oom_is_retried_once_on_the_same_model():
    fake, calls = _stream_of(ResponseError(OLLAMA_OOM, 500), "recovered")
    usage: dict = {}
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        chunks = list(gateway.stream_chat(PRIMARY, MSG, role="conversation", usage=usage))
    assert chunks == ["recovered"]
    assert calls == [PRIMARY, PRIMARY]
    receipt = usage["receipt"]
    assert [a["status"] for a in receipt["attempts"]] == ["failed", "completed"]
    assert receipt["failure_category"] == "out_of_memory"
    assert any("retrying once" in p for p in receipt["policy"])


def test_persistent_oom_falls_back_to_the_configured_fast_chat_model():
    fake, calls = _stream_of(ResponseError(OLLAMA_OOM, 500), ResponseError(OLLAMA_OOM, 500), "small")
    usage: dict = {}
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        chunks = list(gateway.stream_chat(PRIMARY, MSG, role="conversation", usage=usage))
    assert chunks == ["small"]
    assert calls == [PRIMARY, PRIMARY, FAST]
    assert usage["execution_model"] == FAST
    assert usage["execution_locality"] == boundary.LOCAL
    assert any(f"local fallback to {FAST}" in p for p in usage["receipt"]["policy"])


def test_missing_model_skips_the_pointless_retry():
    fake, calls = _stream_of(ResponseError("model not found", 404), "small")
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        assert list(gateway.stream_chat(PRIMARY, MSG, role="conversation")) == ["small"]
    assert calls == [PRIMARY, FAST]


def test_all_local_models_unavailable_is_bounded_and_classified():
    down = ConnectionError("[Errno 111] Connection refused")
    fake, calls = _stream_of(down, down, down, down)
    usage: dict = {}
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation", usage=usage))
    # connection_refused: one retry; not substitutable (another model on the same dead service won't help)
    assert calls == [PRIMARY, PRIMARY]
    assert usage["receipt"]["status"] == "failed"
    assert usage["receipt"]["failure_category"] == "connection_refused"


def test_unclassified_local_failure_is_not_retried():
    fake, calls = _stream_of(RuntimeError("something odd"))
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    assert calls == [PRIMARY]


def test_explicitly_selected_model_is_retried_but_never_substituted():
    oom = ResponseError(OLLAMA_OOM, 500)
    fake, calls = _stream_of(oom, oom, "never")
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation", explicit_model=True))
    assert calls == [PRIMARY, PRIMARY]


def test_uncensored_mode_never_substitutes_a_censored_model(monkeypatch):
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    oom = ResponseError(OLLAMA_OOM, 500)
    fake, calls = _stream_of(oom, oom, "never")
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    assert calls == [PRIMARY, PRIMARY]


def test_local_recovery_never_reaches_a_cloud_model(monkeypatch):
    """Even with cloud enabled and a cloud id configured as fast chat, recovery stays local."""
    monkeypatch.setenv("JARVIS_CLOUD_INFERENCE", "1")
    monkeypatch.setattr("jarvis.model_store.model_for",
                        lambda role: CLOUD if role == "fast_chat" else PRIMARY)
    oom = ResponseError(OLLAMA_OOM, 500)
    fake, calls = _stream_of(oom, oom)
    with (
        patch.object(gateway, "_ollama_stream", side_effect=fake),
        patch.object(gateway, "_litellm_stream") as cloud,
    ):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    cloud.assert_not_called()
    assert calls == [PRIMARY, PRIMARY]


def test_offline_mode_recovery_stays_local(monkeypatch):
    monkeypatch.setenv("JARVIS_OFFLINE", "1")
    fake, calls = _stream_of(ResponseError("model not found", 404), "local")
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        assert list(gateway.stream_chat(PRIMARY, MSG, role="conversation")) == ["local"]
    assert calls == [PRIMARY, FAST]


def test_recovery_can_be_turned_off(monkeypatch):
    monkeypatch.setenv("JARVIS_LOCAL_RECOVERY", "0")
    fake, calls = _stream_of(ResponseError(OLLAMA_OOM, 500), "never")
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    assert calls == [PRIMARY]


def test_cancel_during_retry_backoff_stops_without_another_attempt(monkeypatch):
    monkeypatch.setattr(gateway, "LOCAL_RETRY_DELAY_S", 5.0)
    fake, calls = _stream_of(ResponseError(OLLAMA_OOM, 500), "never")
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.InferenceCancelled):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation", cancel_check=lambda: True))
    assert calls == [PRIMARY]


def test_stream_interrupted_after_output_is_never_retried():
    def partial(model, messages, **kwargs):
        yield "Half an ans"
        raise ResponseError(OLLAMA_OOM, 500)

    with patch.object(gateway, "_ollama_stream", side_effect=partial) as local:
        with pytest.raises(boundary.StreamInterrupted):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    assert local.call_count == 1


def test_invalid_provider_response_is_not_retried():
    fake, calls = _stream_of(ValueError("JSONDecodeError: Expecting value"))
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    assert calls == [PRIMARY]


def test_context_overflow_is_not_retried_or_substituted():
    fake, calls = _stream_of(ResponseError("input length exceeds the context length", 400))
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        with pytest.raises(boundary.ProviderUnavailable):
            list(gateway.stream_chat(PRIMARY, MSG, role="conversation"))
    assert calls == [PRIMARY]


def test_recovery_after_ollama_restart():
    """Ollama restarting: refused once, then answering again on the same model."""
    fake, calls = _stream_of(ConnectionError("[Errno 111] Connection refused"), "back")
    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        assert list(gateway.stream_chat(PRIMARY, MSG, role="conversation")) == ["back"]
    assert calls == [PRIMARY, PRIMARY]


# ------------------------------------------------------------- sync path


def test_sync_chat_uses_the_same_bounded_recovery():
    calls: list[str] = []
    outcomes = [ResponseError(OLLAMA_OOM, 500), ResponseError(OLLAMA_OOM, 500), ("small", {})]

    def fake(model, messages, **kwargs):
        calls.append(model)
        out = outcomes.pop(0)
        if isinstance(out, BaseException):
            raise out
        return out

    with patch.object(gateway, "_ollama_chat_with_usage", side_effect=fake):
        text, usage = gateway.chat_with_usage(PRIMARY, MSG, role="conversation")
    assert text == "small"
    assert calls == [PRIMARY, PRIMARY, FAST]
    assert usage["execution_model"] == FAST


# ------------------------------------------------------------- conversation engine


def _engine(assistant):
    from jarvis.behaviors.conversation import ConversationEngine

    return ConversationEngine(assistant)


def _run(engine, message, ask_stream, request_id="req-1"):
    with (
        patch("jarvis.llm.ask_stream", side_effect=ask_stream),
        patch("jarvis.behaviors.conversation.check_ollama", return_value={"running": True}),
        patch("jarvis.ollama_runtime.ensure_chat_model_ready", return_value={"ok": True}),
    ):
        return list(engine.execute_stream(message, {}, request_id=request_id))


def _failing(exc):
    def ask_stream(*a, **k):
        raise boundary.ProviderUnavailable("ollama model 'gemma4:12b' failed before answering") from exc
        yield  # pragma: no cover

    return ask_stream


def test_basic_conversational_request_answers(assistant):
    def ask_stream(*a, usage=None, **k):
        if usage is not None:
            usage["execution_model"] = PRIMARY
        yield "Hello! "
        yield "Good to see you."

    events = _run(_engine(assistant), "Hello, Aria.", ask_stream)
    done = events[-1]
    assert done["ok"] is True and done["message"] == "Hello! Good to see you."
    assert done["model"] == PRIMARY


def test_failure_message_is_specific_traceable_and_logged(assistant, caplog):
    before = list(assistant.conversation.messages)
    with caplog.at_level("WARNING", logger="jarvis.conversation"):
        events = _run(_engine(assistant), "What should we work on?",
                      _failing(ResponseError(OLLAMA_OOM, 500)), request_id="req-oom")
    done = events[-1]
    assert done["ok"] is False
    assert done["error_category"] == "out_of_memory"
    assert done["request_id"] == "req-oom"
    assert done["retryable"] is True
    assert "graphics card" in done["message"]
    assert "couldn't complete that reply" not in done["message"]
    # No raw backend text or stack in the owner-facing message.
    assert "cudaMalloc" not in done["message"] and "llama-server" not in done["message"]
    # The log line carries the correlation id, category and cause — not the message text.
    line = next(r.getMessage() for r in caplog.records if "chat failed" in r.getMessage())
    assert "request_id=req-oom" in line and "category=out_of_memory" in line
    assert "What should we work on" not in line
    # The failed turn was not persisted.
    assert assistant.conversation.messages == before


def test_retry_after_failure_does_not_duplicate_the_turn(assistant):
    engine = _engine(assistant)
    before = len(assistant.conversation.messages)
    _run(engine, "What should we work on?", _failing(ConnectionError("Connection refused")))
    assert len(assistant.conversation.messages) == before

    def ok_stream(*a, **k):
        yield "Let's finish the brake job."

    events = _run(engine, "What should we work on?", ok_stream)
    assert events[-1]["ok"] is True
    new = assistant.conversation.messages[before:]
    assert [m["role"] for m in new] == ["user", "assistant"]
    assert new[0]["content"].count("What should we work on?") == 1


def test_fallback_answer_reports_the_model_that_actually_answered(assistant):
    def ask_stream(*a, usage=None, **k):
        if usage is not None:
            usage["execution_model"] = FAST
            usage["receipt"] = {"fallback_used": True, "failure_category": "out_of_memory"}
        yield "Small model answer."

    done = _run(_engine(assistant), "What should we work on?", ask_stream)[-1]
    assert done["ok"] is True
    assert done["model"] == FAST
    assert done["fallback"]["to"] == FAST and done["fallback"]["reason"] == "out_of_memory"
    assert done["requested_model"] != FAST


def test_memory_service_unavailable_degrades_instead_of_failing(assistant, monkeypatch):
    from jarvis.behaviors import memory as memory_pkg

    class BrokenMemory:
        def prepare_context(self, *a, **k):
            raise RuntimeError("vector store locked")

    monkeypatch.setattr(memory_pkg, "get_memory_behavior", lambda: BrokenMemory())
    engine = _engine(assistant)
    prefix, warnings, citations = engine.build_context_prefix("Do you remember my truck?")
    assert "Long-term memory: UNAVAILABLE" in prefix
    assert "Memory was unavailable for this reply." in warnings
    assert citations == []


def test_conversation_persists_a_completed_turn(assistant):
    def ask_stream(*a, **k):
        yield "Noted."

    engine = _engine(assistant)
    before = len(assistant.conversation.messages)
    _run(engine, "Hello, Aria.", ask_stream)
    roles = [m["role"] for m in assistant.conversation.messages[before:]]
    assert roles == ["user", "assistant"]


# ------------------------------------------------------------- continuity cues


@pytest.mark.parametrize(
    "text, expected",
    [
        ("What should we work on?", True),
        ("what should we do next?", True),
        ("What were we just discussing?", True),
        ("Hello, Aria.", False),
        ("My car won't start, what should I do?", False),
        ("what should we do about the brakes", False),
    ],
)
def test_work_planning_and_recent_topic_questions_use_continuity(text, expected):
    from jarvis.continuity.retrieve import is_continuity_query

    assert is_continuity_query(text) is expected


# ------------------------------------------------------------- runtime identification


def test_model_identity_answer_uses_the_last_receipt(monkeypatch):
    from jarvis import runtime_formatters, runtime_introspection

    monkeypatch.setattr(boundary, "recent_receipts", lambda limit=20: [
        {"status": "completed", "role": "conversation", "executed_model": FAST,
         "executed_provider": "ollama", "executed_locality": "local", "requested_model": PRIMARY,
         "fallback_used": True, "id": "abc123"},
        {"status": "completed", "role": "router", "executed_model": "router-model"},
    ])
    last = runtime_introspection.last_answer_receipt()
    assert last["model"] == FAST and last["receipt_id"] == "abc123"
    text = runtime_formatters.format_inference({"last_answer": last, "current_model": PRIMARY})
    assert f"Last reply was answered by `{FAST}`" in text
    assert f"`{PRIMARY}` was requested" in text


# ------------------------------------------------------------- log volume


def test_installed_model_lookup_is_cached(monkeypatch):
    import sys
    import types

    from jarvis import platform_inference

    refreshes: list[int] = []
    validator = types.ModuleType("aiplatform.applications.inference.validator")
    validator.refresh_models = lambda: refreshes.append(1)
    registry = types.SimpleNamespace(installed=lambda: [types.SimpleNamespace(name=PRIMARY)])
    models_mod = types.ModuleType("aiplatform.models")
    models_mod.models = registry
    monkeypatch.setitem(sys.modules, "aiplatform.applications.inference.validator", validator)
    monkeypatch.setitem(sys.modules, "aiplatform.models", models_mod)
    monkeypatch.setattr(platform_inference, "is_inference_attached", lambda: True)
    monkeypatch.setattr(platform_inference, "_installed_cache", (0.0, []))
    for _ in range(25):
        assert platform_inference.installed_models() == [PRIMARY]
    assert len(refreshes) == 1


# ------------------------------------------------------------- thermal: chat thinking default


def _captured_think(monkeypatch, role, *, env=None, **extra):
    monkeypatch.setattr(boundary, "model_capabilities", lambda model: frozenset({"completion", "thinking"}))
    if env is not None:
        monkeypatch.setenv("JARVIS_CHAT_THINKING", env)
    seen: dict = {}

    def fake(model, messages, **kwargs):
        seen["think"] = kwargs.get("think", "unset")
        yield "ok"

    with patch.object(gateway, "_ollama_stream", side_effect=fake):
        list(gateway.stream_chat(PRIMARY, MSG, role=role, **extra))
    return seen["think"]


def test_everyday_chat_skips_the_thinking_pass(monkeypatch):
    assert _captured_think(monkeypatch, "conversation") is False


def test_reasoning_role_keeps_thinking(monkeypatch):
    assert _captured_think(monkeypatch, "reasoning") == "unset"


def test_owner_can_restore_chat_thinking(monkeypatch):
    assert _captured_think(monkeypatch, "conversation", env="1") == "unset"


def test_explicit_think_request_wins(monkeypatch):
    assert _captured_think(monkeypatch, "conversation", think=True) is True
