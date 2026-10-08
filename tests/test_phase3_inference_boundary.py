"""Phase 3 — the inference execution boundary.

Regressions for the routing defects the October 2026 assessment reproduced,
plus offline operation, provider permissions, private context, compatible
local fallback, interrupted streams, cancellation, capability checks and
routing receipts. Cloud providers are simulated; nothing here makes a network
call to a cloud API or loads a local model.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from jarvis.inference import boundary, gateway, policy

CLOUD = "openai/example-model"
LOCAL = "qwen2.5:7b"
MSG = [{"role": "user", "content": "hi"}]


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    for name in ("JARVIS_CLOUD_INFERENCE", "JARVIS_OFFLINE", "JARVIS_CLOUD_PROVIDERS",
                 "JARVIS_CLOUD_MODEL", "JARVIS_INFERENCE_GATEWAY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(boundary, "installed_local_models", lambda **k: {LOCAL, "gemma4:12b"})
    monkeypatch.setattr("jarvis.model_store.model_for", lambda role: LOCAL)
    monkeypatch.setattr(
        "jarvis.inference.execution_policy.apply_policy_to_route",
        lambda *, model, role="general": {"model": model, "hardware": "cpu", "source": "explicit"},
    )
    monkeypatch.setattr("jarvis.nlu.placement.ollama_options_for_device", lambda hw: {})
    monkeypatch.setattr(boundary, "model_capabilities", lambda model: None)


def cloud_route() -> policy.InferenceRoute:
    return policy.InferenceRoute(backend="litellm", model=CLOUD, reason="t", local=False, cloud=True)


def enable_cloud(monkeypatch):
    """Cloud on, plus what Phase 4 requires before any paid call: an owner
    authorization, a budget and a price (all in the isolated test data)."""
    import json

    from jarvis.inference import cloud_policy

    monkeypatch.setenv("JARVIS_CLOUD_INFERENCE", "1")
    cloud_policy.reset_for_tests()
    cloud_policy.BUDGET_FILE.write_text(json.dumps({
        "monthly_total_usd": 10.0,
        "per_task_max_usd": 1.0,
        "providers": {"openai": {"monthly_usd": 5.0}, "anthropic": {"monthly_usd": 5.0}},
        "prices": {CLOUD: {"input_per_mtok": 1.0, "output_per_mtok": 2.0}},
    }))
    cloud_policy.create_authorization("openai", max_cost_usd=1.0)


# ------------------------------------------------- defect 1: cloud-disable bypass


def test_explicit_cloud_model_is_refused_when_cloud_disabled():
    with patch.object(gateway, "litellm_available", return_value=True):
        route = policy.select_route(CLOUD, lock_model=True)
    assert route.backend == "ollama" and not route.cloud and route.model == LOCAL
    assert "cloud_refused" in route.reason


def test_caller_supplied_cloud_route_is_rechecked_at_execution():
    with (
        patch.object(gateway, "_litellm_chat_with_usage") as cloud,
        patch.object(gateway, "_ollama_chat_with_usage", return_value=("local", {})) as local,
    ):
        _text, usage = gateway.chat_with_usage(CLOUD, MSG, route=cloud_route())
    cloud.assert_not_called()
    assert local.call_args[0][0] == LOCAL
    assert usage["execution_locality"] == "local"
    assert any("disabled" in p for p in usage["receipt"]["policy"])


def test_offline_mode_refuses_cloud_even_when_enabled(monkeypatch):
    enable_cloud(monkeypatch)
    monkeypatch.setenv("JARVIS_OFFLINE", "1")
    assert "offline" in boundary.cloud_refusal(CLOUD)
    with patch.object(gateway, "litellm_available", return_value=True):
        assert policy.select_route(CLOUD).backend == "ollama"


def test_provider_allowlist_is_enforced(monkeypatch):
    enable_cloud(monkeypatch)
    monkeypatch.setenv("JARVIS_CLOUD_PROVIDERS", "anthropic")
    assert "not in JARVIS_CLOUD_PROVIDERS" in boundary.cloud_refusal(CLOUD)
    assert boundary.cloud_refusal("anthropic/some-model") == ""


def test_private_health_context_never_goes_to_cloud(monkeypatch):
    enable_cloud(monkeypatch)
    messages = [{"role": "system", "content": "Health record context (authoritative local PHR — x"}]
    with (
        patch.object(gateway, "_litellm_chat_with_usage") as cloud,
        patch.object(gateway, "_ollama_chat_with_usage", return_value=("ok", {})),
    ):
        _t, usage = gateway.chat_with_usage(CLOUD, messages, route=cloud_route())
    cloud.assert_not_called()
    assert usage["receipt"]["privacy"] == boundary.LOCAL_ONLY
    with (
        patch.object(gateway, "_litellm_chat_with_usage") as cloud,
        patch.object(gateway, "_ollama_chat_with_usage", return_value=("ok", {})),
    ):
        gateway.chat_with_usage(CLOUD, MSG, route=cloud_route(), privacy="local_only")
    cloud.assert_not_called()


def test_egress_guard_blocks_direct_cloud_calls_when_disabled():
    with pytest.raises(boundary.CloudNotPermitted):
        gateway._litellm_chat_with_usage(CLOUD, MSG)
    with pytest.raises(boundary.CloudNotPermitted):
        list(gateway._litellm_stream(CLOUD, MSG))


# ------------------------------------------------- defect 2: cloud id sent to Ollama


def test_cloud_failure_falls_back_to_installed_local_model_not_cloud_id(monkeypatch):
    enable_cloud(monkeypatch)
    seen: list[str] = []
    with (
        patch.object(gateway, "_litellm_chat_with_usage", side_effect=RuntimeError("down")),
        patch.object(
            gateway, "_ollama_chat_with_usage", side_effect=lambda m, *a, **k: (seen.append(m) or "ok", {})
        ),
    ):
        _t, usage = gateway.chat_with_usage(CLOUD, MSG, route=cloud_route())
    assert seen == [LOCAL]
    receipt = usage["receipt"]
    assert [a["status"] for a in receipt["attempts"]] == ["failed", "completed"]
    assert receipt["fallback_used"] and receipt["executed_model"] == LOCAL


def test_cloud_gateway_offline_at_routing_time_uses_local(monkeypatch):
    enable_cloud(monkeypatch)
    with patch.object(gateway, "litellm_available", return_value=False):
        route = policy.select_route(CLOUD)
    assert route.model == LOCAL and route.backend == "ollama"


def test_ollama_never_receives_a_cloud_model_id():
    with pytest.raises(boundary.InferenceError, match="refusing to send cloud model"):
        gateway._ollama_chat_with_usage(CLOUD, MSG)
    with pytest.raises(boundary.InferenceError):
        list(gateway._ollama_stream("claude-whatever", MSG))


def test_no_installed_local_model_is_an_honest_failure(monkeypatch):
    monkeypatch.setattr(boundary, "installed_local_models", lambda **k: {"something-else:1b"})
    with patch.object(gateway, "_ollama_chat_with_usage") as local:
        with pytest.raises(boundary.ProviderUnavailable, match="no installed local model"):
            gateway.chat_with_usage(CLOUD, MSG, route=cloud_route())
    local.assert_not_called()


def test_local_failure_is_not_retried_on_another_model():
    with patch.object(gateway, "_ollama_chat_with_usage", side_effect=RuntimeError("oom")) as local:
        with pytest.raises(boundary.ProviderUnavailable):
            gateway.chat_with_usage(LOCAL, MSG)
    assert local.call_count == 1


# ------------------------------------------------- defect 3: mixed partial streams


def _partial_then_fail(*a, **k):
    yield "CLOUD_PARTIAL"
    raise RuntimeError("disconnect")


def _local_stream(*a, **k):
    yield "LOCAL_RESTART"


def test_interrupted_cloud_stream_is_never_continued_locally(monkeypatch):
    enable_cloud(monkeypatch)
    usage: dict = {}
    chunks: list[str] = []
    with (
        patch.object(gateway, "_litellm_stream", side_effect=_partial_then_fail),
        patch.object(gateway, "_ollama_stream", side_effect=_local_stream) as local,
    ):
        with pytest.raises(boundary.StreamInterrupted) as info:
            for chunk in gateway.stream_chat(CLOUD, MSG, route=cloud_route(), usage=usage):
                chunks.append(chunk)
    assert chunks == ["CLOUD_PARTIAL"]
    local.assert_not_called()
    assert info.value.partial_chars == len("CLOUD_PARTIAL")
    assert usage["receipt"]["status"] == "interrupted"
    assert usage["receipt"]["attempts"][0]["status"] == "interrupted"


def test_cloud_stream_failing_before_output_may_fall_back(monkeypatch):
    enable_cloud(monkeypatch)

    def dead(*a, **k):
        raise RuntimeError("connection refused")
        yield  # pragma: no cover

    usage: dict = {}
    with (
        patch.object(gateway, "_litellm_stream", side_effect=dead),
        patch.object(gateway, "_ollama_stream", side_effect=_local_stream),
    ):
        chunks = list(gateway.stream_chat(CLOUD, MSG, route=cloud_route(), usage=usage))
    assert chunks == ["LOCAL_RESTART"]
    attempts = usage["receipt"]["attempts"]
    assert [(a["locality"], a["status"]) for a in attempts] == [
        ("cloud", "failed"),
        ("local", "completed"),
    ]
    assert attempts[1]["model"] == LOCAL


def test_local_stream_interruption_is_reported_not_retried():
    with patch.object(gateway, "_ollama_stream", side_effect=_partial_then_fail) as local:
        with pytest.raises(boundary.StreamInterrupted):
            list(gateway.stream_chat(LOCAL, MSG))
    assert local.call_count == 1


def test_cancellation_stops_the_stream_without_fallback():
    state = {"n": 0}

    def long_stream(*a, **k):
        for i in range(10):
            yield f"t{i} "

    def cancelled() -> bool:
        state["n"] += 1
        return state["n"] > 2

    usage: dict = {}
    with patch.object(gateway, "_ollama_stream", side_effect=long_stream) as local:
        chunks = list(gateway.stream_chat(LOCAL, MSG, usage=usage, cancel_check=cancelled))
    assert chunks == ["t0 ", "t1 "]
    assert local.call_count == 1
    assert usage["receipt"]["status"] == "cancelled"


def test_interrupted_stream_is_not_saved_as_an_answer(assistant):
    from jarvis.behaviors.conversation import ConversationEngine

    def ask_stream(*a, **k):
        yield "Half of an ans"
        raise boundary.StreamInterrupted(
            "interrupted", provider="openai", model=CLOUD, partial_chars=14
        )

    engine = ConversationEngine(assistant)
    before = list(assistant.conversation.messages)
    with (
        patch("jarvis.llm.ask_stream", side_effect=ask_stream),
        patch("jarvis.behaviors.conversation.check_ollama", return_value={"running": True}),
    ):
        events = list(engine.execute_stream("Tell me about trout", {}))
    done = events[-1]
    assert done["type"] == "done" and done["ok"] is False and done["interrupted"] is True
    assert assistant.conversation.messages == before, "partial answer was kept"


# ------------------------------------------------- defect 4: cloud needs local Ollama


def test_cloud_target_does_not_depend_on_local_ollama_health(monkeypatch, assistant):
    from jarvis.behaviors.conversation import ConversationEngine

    engine = ConversationEngine(assistant)
    assert engine._needs_local_runtime({"model": CLOUD}) is True  # disabled → runs locally
    assert engine._needs_local_runtime({"model": LOCAL}) is True
    enable_cloud(monkeypatch)
    assert engine._needs_local_runtime({"model": CLOUD}) is False
    with (
        patch("jarvis.behaviors.conversation.check_ollama", return_value={"running": False}),
        patch("jarvis.llm.ask_with_usage", return_value=("from the cloud", {})),
    ):
        out = engine.execute({"model": CLOUD}, "Tell me about trout")
    assert out["ok"] is True, out
    assert "Ollama is still starting" not in out["message"]


# ------------------------------------------------- capabilities, receipts, discovery


def test_tool_request_on_a_model_without_tools_is_refused(monkeypatch):
    monkeypatch.setattr(boundary, "model_capabilities", lambda m: frozenset({"completion"}))
    with patch.object(gateway, "_ollama_chat_with_usage") as local:
        with pytest.raises(boundary.CapabilityMismatch, match="tools"):
            gateway.chat_with_usage(LOCAL, MSG, tools=[{"type": "function"}])
    local.assert_not_called()


def test_vision_request_needs_a_vision_model(monkeypatch):
    monkeypatch.setattr(boundary, "model_capabilities", lambda m: frozenset({"completion", "tools"}))
    with pytest.raises(boundary.CapabilityMismatch, match="vision"):
        gateway.chat_with_usage(LOCAL, [{"role": "user", "content": "x", "images": ["b64"]}])


def test_every_call_leaves_a_receipt():
    with patch.object(gateway, "_ollama_chat_with_usage", return_value=("ok", {"prompt_tokens": 3, "completion_tokens": 1})):
        _t, usage = gateway.chat_with_usage(LOCAL, MSG, role="conversation")
    receipt = usage["receipt"]
    assert receipt["status"] == "completed"
    assert receipt["executed_provider"] == "ollama" and receipt["executed_model"] == LOCAL
    assert receipt["attempts"][0]["prompt_tokens"] == 3
    assert receipt["attempts"][0]["duration_ms"] is not None
    assert boundary.recent_receipts()[-1]["id"] == receipt["id"]


def test_no_hardcoded_cloud_model_for_large_context(monkeypatch):
    enable_cloud(monkeypatch)
    big = [{"role": "user", "content": "x" * 80000}]
    with patch.object(gateway, "litellm_available", return_value=True):
        assert policy.select_route(LOCAL, messages=big).backend == "ollama"
        monkeypatch.setenv("JARVIS_CLOUD_MODEL", "anthropic/operator-chosen")
        route = policy.select_route(LOCAL, messages=big)
    assert route.backend == "litellm" and route.model == "anthropic/operator-chosen"


def test_cloud_discovery_without_a_gateway_reports_instead_of_guessing():
    with patch("urllib.request.urlopen", side_effect=OSError("no gateway")):
        found = boundary.discover_cloud_models()
    assert found and "error" in found[0]


def test_local_model_families_are_not_mistaken_for_cloud():
    assert boundary.provider_of("gpt-oss:20b") == "ollama"
    assert boundary.provider_of("ollama/qwen3:8b") == "ollama"
    assert boundary.provider_of("claude-sonnet") == "anthropic"
    assert boundary.provider_of("gemini/flash") == "google"


# ------------------------------------------------- structured tool calls


TOOLS = [{"type": "function", "function": {"name": "route", "parameters": {"type": "object"}}}]


def test_tool_turn_on_a_model_that_cannot_call_tools_is_refused_before_any_call(monkeypatch):
    # The production router role (qwen2.5-coder:1.5b-base) reports no "tools".
    monkeypatch.setattr(boundary, "model_capabilities", lambda m: frozenset({"completion", "insert"}))
    with patch.object(gateway, "_ollama_tools") as call:
        with pytest.raises(boundary.CapabilityMismatch):
            gateway.chat_with_tools("qwen2.5-coder:1.5b-base", MSG, TOOLS)
    call.assert_not_called()


def test_tool_calls_come_back_normalised_with_a_receipt(monkeypatch):
    monkeypatch.setattr(boundary, "model_capabilities", lambda m: frozenset({"completion", "tools"}))
    reply = {"content": "", "tool_calls": [{"name": "route", "arguments": {"action": "chat"}}]}
    with patch.object(gateway, "_ollama_tools", return_value=(reply, {"prompt_tokens": 5})):
        result, usage = gateway.chat_with_tools(LOCAL, MSG, TOOLS)
    assert result["tool_calls"] == [{"name": "route", "arguments": {"action": "chat"}}]
    assert usage["receipt"]["status"] == "completed"


def test_failed_cloud_tool_turn_falls_back_only_to_a_tool_capable_local_model(monkeypatch):
    enable_cloud(monkeypatch)
    monkeypatch.setattr(boundary, "model_capabilities", lambda m: frozenset({"completion", "tools"}))
    reply = {"content": "", "tool_calls": []}
    with (
        patch.object(gateway, "_litellm_tools", side_effect=RuntimeError("down")),
        patch.object(gateway, "_ollama_tools", return_value=(reply, {})) as local,
    ):
        _r, usage = gateway.chat_with_tools(CLOUD, MSG, TOOLS, route=cloud_route())
    assert local.call_args[0][0] == LOCAL
    assert [a["status"] for a in usage["receipt"]["attempts"]] == ["failed", "completed"]


def test_router_uses_the_gateway_and_degrades_gracefully(monkeypatch):
    from jarvis import llm

    monkeypatch.setattr(boundary, "model_capabilities", lambda m: frozenset({"completion"}))
    monkeypatch.setattr("jarvis.capability_routing.apply_gateway_model", lambda m, r, **k: LOCAL)
    with patch.object(gateway, "_ollama_tools") as call:
        assert llm.route_with_tools("hello", "", None) is None  # falls back to the JSON router
    call.assert_not_called()


# ------------------------------------------------- health probe vs cold loads


def test_forced_probe_on_a_cold_model_waits_for_the_load(monkeypatch):
    from jarvis import ollama_health as oh

    seen: list[float] = []
    monkeypatch.setattr(oh, "_loaded_runner_names", lambda host: set())
    monkeypatch.setattr(oh, "_soft_generate_probe",
                        lambda host, model, *, timeout: seen.append(timeout) or {"ok": True})
    oh.refresh_inference_probe(force=True)
    assert seen and seen[0] >= 120, "a 5 s probe aborts a ~40 s cold load"


def test_tests_cannot_reach_live_inference():
    import urllib.error
    import urllib.request

    with pytest.raises(urllib.error.URLError, match="blocked in tests"):
        urllib.request.urlopen("http://127.0.0.1:11434/api/generate", timeout=1)


def test_receipt_explains_when_policy_replaced_the_requested_model(monkeypatch):
    monkeypatch.setattr(
        "jarvis.inference.execution_policy.apply_policy_to_route",
        lambda *, model, role="general": {"model": LOCAL, "hardware": "cpu", "source": "user_config"},
    )
    with patch.object(gateway, "_ollama_chat_with_usage", return_value=("ok", {})):
        _t, usage = gateway.chat_with_usage(CLOUD, MSG)
    receipt = usage["receipt"]
    assert receipt["requested_model"] == CLOUD and receipt["executed_model"] == LOCAL
    assert any("user_config" in p and LOCAL in p for p in receipt["policy"])
