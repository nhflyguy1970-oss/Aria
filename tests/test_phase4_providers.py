"""Phase 4 — native cloud providers behind the inference gateway.

Every provider is simulated: a fake transport records each would-be request
and returns scripted OpenAI / Anthropic / Gemini responses. No test can reach a
real API (conftest also blocks outbound network), so nothing here costs money.
"""

from __future__ import annotations

import io
import json
import urllib.error
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from jarvis.inference import boundary, cloud_policy, gateway, policy, provider_routing, providers
from jarvis.inference.providers import base

KEYS = {
    "openai_api_key": "sk-test-openai-0123456789abcdef",
    "anthropic_api_key": "sk-ant-test-0123456789abcdef",
    "gemini_api_key": "AIzaTEST0123456789abcdefghij",
}
LOCAL = "qwen2.5:7b"
MSG = [{"role": "user", "content": "What is a dry fly?"}]
CLAUDE = "anthropic/claude-test-model"
GPT = "openai/gpt-test-model"
GEMINI = "google/gemini-test-model"


# ------------------------------------------------------------------ simulated providers


class FakeResponse:
    def __init__(self, body: dict | None = None, *, lines: list[str] | None = None, status: int = 200):
        self.status = status
        self.headers: dict[str, str] = {}
        self._body = json.dumps(body or {}).encode()
        self._lines = [ln.encode() + b"\n" for ln in (lines or [])]
        self.closed = False

    def read(self):
        return self._body

    def __iter__(self):
        return iter(self._lines)

    def close(self):
        self.closed = True


class FakeTransport:
    """Scripted responses, consumed in order; records every request."""

    def __init__(self):
        self.script: list = []
        self.requests: list[dict] = []

    def add(self, item):
        self.script.append(item)
        return self

    def __call__(self, method, url, headers, body, timeout):
        self.requests.append(
            {"method": method, "url": url, "headers": dict(headers), "body": json.loads(body) if body else None}
        )
        if not self.script:
            raise AssertionError(f"unexpected request: {method} {url}")
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def http_error(code: int, retry_after: str | None = None):
    hdrs = {"retry-after": retry_after} if retry_after else {}
    return urllib.error.HTTPError("https://x", code, "err", hdrs, io.BytesIO(b'{"error": "x"}'))


def sse(*events: tuple[str, dict]) -> list[str]:
    lines = []
    for name, data in events:
        if name:
            lines.append(f"event: {name}")
        lines.append("data: " + json.dumps(data))
        lines.append("")
    return lines


def openai_completed(text="A dry fly floats.", calls=None, usage=(12, 5)):
    output = [{"type": "message", "content": [{"type": "output_text", "text": text}]}] if text else []
    for c in calls or []:
        output.append({"type": "function_call", "call_id": c[0], "name": c[1], "arguments": json.dumps(c[2])})
    return {
        "id": "resp_1", "status": "completed", "model": "gpt-test-model-2026",
        "output": output, "usage": {"input_tokens": usage[0], "output_tokens": usage[1]},
    }


def anthropic_message(text="A dry fly floats.", calls=None, stop="end_turn"):
    content = [{"type": "text", "text": text}] if text else []
    for c in calls or []:
        content.append({"type": "tool_use", "id": c[0], "name": c[1], "input": c[2]})
    return {
        "id": "msg_1", "model": "claude-test-model", "stop_reason": stop, "content": content,
        "usage": {"input_tokens": 12, "output_tokens": 5},
    }


def gemini_response(text="A dry fly floats.", finish="STOP"):
    return {
        "candidates": [{"content": {"role": "model", "parts": [{"text": text}]}, "finishReason": finish}],
        "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 5},
        "modelVersion": "gemini-test-model-001",
    }


@pytest.fixture
def fake(monkeypatch, data_dir):
    t = FakeTransport()
    base.set_transport(t)
    base.reset_circuits()
    cloud_policy.reset_for_tests()
    monkeypatch.setattr(base, "_sleep", lambda s: t.requests.append({"slept": s}))

    def resolve(field):
        value = KEYS.get(field)
        return SimpleNamespace(source="vault", value=value, vault_id="x", field=field) if value else None

    monkeypatch.setattr("jarvis.security.owner.provider_credentials.resolve_provider_secret", resolve)
    for name in ("JARVIS_OFFLINE", "JARVIS_CLOUD_PROVIDERS", "JARVIS_INFERENCE_GATEWAY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("JARVIS_CLOUD_INFERENCE", "1")
    monkeypatch.setattr(boundary, "installed_local_models", lambda **k: {LOCAL})
    monkeypatch.setattr("jarvis.model_store.model_for", lambda role: LOCAL)
    monkeypatch.setattr(
        "jarvis.inference.execution_policy.apply_policy_to_route",
        lambda *, model, role="general": {"model": model, "hardware": "cpu", "source": "explicit"},
    )
    monkeypatch.setattr("jarvis.nlu.placement.ollama_options_for_device", lambda hw: {})
    monkeypatch.setattr(gateway, "litellm_available", lambda: False)
    yield t
    base.set_transport(None)


def allow(provider: str, *, classes=("current_turn",), cap=1.0, price=(1.0, 2.0), roles=("*",)):
    """Owner grants + budget for one provider (simulated, nothing is billed)."""
    budget = cloud_policy.load_budget()
    budget["monthly_total_usd"] = 10.0
    budget["per_task_max_usd"] = 1.0
    budget.setdefault("providers", {})[provider] = {"monthly_usd": 5.0}
    for model in (CLAUDE, GPT, GEMINI):
        budget.setdefault("prices", {})[model] = {"input_per_mtok": price[0], "output_per_mtok": price[1]}
    cloud_policy.BUDGET_FILE.write_text(json.dumps(budget))
    return cloud_policy.create_authorization(provider, max_cost_usd=cap, context_classes=list(classes), roles=list(roles))


def local_answer(text="local answer"):
    return patch.object(gateway, "_ollama_chat_with_usage", return_value=(text, {}))


# ====================================================================== authentication & discovery


def test_credentials_come_from_the_owner_vault_and_never_leave_in_body_or_url(fake):
    allow("google")
    fake.add(FakeResponse(gemini_response()))
    text, usage = gateway.chat_with_usage(GEMINI, MSG)
    assert text == "A dry fly floats."
    req = fake.requests[0]
    assert req["headers"]["x-goog-api-key"] == KEYS["gemini_api_key"]
    assert KEYS["gemini_api_key"] not in req["url"]
    assert KEYS["gemini_api_key"] not in json.dumps(req["body"])
    assert KEYS["gemini_api_key"] not in json.dumps(usage["receipt"])
    assert all(KEYS["gemini_api_key"] not in json.dumps(r) for r in cloud_policy.disclosure_rows())


def test_missing_or_locked_credentials_are_reported_not_guessed(fake, monkeypatch):
    monkeypatch.setattr(
        "jarvis.security.owner.provider_credentials.resolve_provider_secret",
        lambda f: SimpleNamespace(source="locked", value="", vault_id="x", field=f),
    )
    assert providers.adapter_for("openai").credential_status()["state"] == "locked"
    with pytest.raises(base.ProviderAuthError, match="locked"):
        providers.adapter_for("openai").credential()
    assert fake.requests == []


@pytest.mark.parametrize(
    "provider,listing,expected",
    [
        ("openai", {"data": [{"id": "gpt-test-model"}]}, ("gpt-test-model", None)),
        ("anthropic", {"data": [{"id": "claude-test-model", "display_name": "Claude Test",
                                  "max_input_tokens": 200000, "capabilities": {"tool_use": True, "image_input": True}}],
                       "has_more": False}, ("claude-test-model", 200000)),
        ("google", {"models": [{"name": "models/gemini-test-model", "inputTokenLimit": 1048576,
                                "outputTokenLimit": 8192, "supportedGenerationMethods": ["generateContent"]},
                               {"name": "models/embedding-x", "supportedGenerationMethods": ["embedContent"]}]},
         ("gemini-test-model", 1048576)),
    ],
)
def test_discovery_lists_this_accounts_models(fake, provider, listing, expected):
    fake.add(FakeResponse(listing))
    found = providers.discover(provider)
    assert [m["id"] for m in found["models"]] == [expected[0]]  # gemini embedding model excluded
    assert found["models"][0]["context_window"] == expected[1]
    if provider == "anthropic":
        assert providers.discovered_capabilities(f"anthropic/{expected[0]}") >= {"tools", "vision"}
    assert fake.requests[0]["method"] == "GET"


def test_discovery_obeys_cloud_disable_and_offline(fake, monkeypatch):
    monkeypatch.setenv("JARVIS_CLOUD_INFERENCE", "0")
    with pytest.raises(boundary.CloudNotPermitted):
        providers.discover("anthropic")
    monkeypatch.setenv("JARVIS_CLOUD_INFERENCE", "1")
    monkeypatch.setenv("JARVIS_OFFLINE", "1")
    with pytest.raises(boundary.CloudNotPermitted):
        providers.discover("anthropic")
    assert fake.requests == []


# ====================================================================== authorization, privacy, budget


def test_no_paid_call_without_owner_authorization(fake):
    with local_answer() as local:
        text, usage = gateway.chat_with_usage(CLAUDE, MSG)
    assert fake.requests == [], "a request left the machine without authorization"
    assert text == "local answer" and local.call_args[0][0] == LOCAL
    assert any("no active owner authorization" in p for p in usage["receipt"]["policy"])


def test_cloud_disable_and_offline_beat_an_explicit_provider_and_an_authorization(fake, monkeypatch):
    allow("anthropic")
    for env in ({"JARVIS_CLOUD_INFERENCE": "0"}, {"JARVIS_OFFLINE": "1"}):
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        with local_answer():
            _t, usage = gateway.chat_with_usage(CLAUDE, MSG)
        assert usage["receipt"]["executed_locality"] == "local"
        monkeypatch.setenv("JARVIS_CLOUD_INFERENCE", "1")
        monkeypatch.delenv("JARVIS_OFFLINE", raising=False)
    assert fake.requests == []


def test_provider_allowlist_is_enforced(fake, monkeypatch):
    allow("openai")
    monkeypatch.setenv("JARVIS_CLOUD_PROVIDERS", "anthropic")
    with local_answer():
        gateway.chat_with_usage(GPT, MSG)
    assert fake.requests == []


def test_default_disclosure_is_only_the_current_request(fake):
    allow("anthropic")
    fake.add(FakeResponse(anthropic_message()))
    messages = [
        {"role": "system", "content": "You are ARIA.\n\nPersistent cognitive context (ACM):\n- User: Jeff\n\n"
                                      "Conversation history (HITS) — Decided: SQLite.\n\nRelevant memories:\n- likes trout"},
        {"role": "user", "content": "Earlier private chat."},
        {"role": "assistant", "content": "Earlier reply."},
        {"role": "user", "content": "What is a dry fly?"},
    ]
    _t, usage = gateway.chat_with_usage(CLAUDE, messages)
    sent = json.dumps(fake.requests[0]["body"])
    assert "What is a dry fly?" in sent
    for private in ("Jeff", "SQLite", "likes trout", "Earlier private chat", "You are ARIA"):
        assert private not in sent, private
    [row] = cloud_policy.disclosure_rows()
    assert set(row["classes"]) == {"current_turn"}
    assert {"memory", "continuity", "system_prompt", "recent_conversation"} <= set(row["withheld"])
    assert row["provider"] == "anthropic" and row["receipt_id"] == usage["receipt"]["id"]


def test_granted_context_classes_are_shared_and_health_never_is(fake):
    allow("anthropic", classes=("continuity", "recent_conversation"))
    fake.add(FakeResponse(anthropic_message()))
    messages = [
        {"role": "system", "content": "Conversation history (HITS) — Decided: SQLite.\n\nRelevant memories:\n- likes trout"},
        {"role": "user", "content": "Earlier turn."},
        {"role": "user", "content": "Continue the project."},
    ]
    gateway.chat_with_usage(CLAUDE, messages)
    sent = json.dumps(fake.requests[0]["body"])
    assert "SQLite" in sent and "Earlier turn." in sent and "likes trout" not in sent

    health = [{"role": "system", "content": "Health record context (authoritative local PHR — BP 150/95"},
              {"role": "user", "content": "Summarize my health."}]
    with local_answer():
        _t, usage = gateway.chat_with_usage(CLAUDE, health)
    assert len(fake.requests) == 1, "health context reached a cloud provider"
    assert usage["receipt"]["executed_locality"] == "local"


def test_a_vault_secret_in_the_prompt_is_never_sent(fake):
    allow("openai")
    leaky = [{"role": "user", "content": f"Here is my key {KEYS['anthropic_api_key']} — what is it for?"}]
    with local_answer():
        _t, usage = gateway.chat_with_usage(GPT, leaky)
    assert fake.requests == []
    assert any("Owner Vault secret" in p for p in usage["receipt"]["policy"])
    assert KEYS["anthropic_api_key"] not in json.dumps(usage["receipt"])


def test_credential_shaped_strings_are_redacted(fake):
    allow("openai")
    fake.add(FakeResponse(openai_completed()))
    gateway.chat_with_usage(GPT, [{"role": "user", "content": "my token=abc123secretvalue please"}])
    assert "abc123secretvalue" not in json.dumps(fake.requests[0]["body"])


def test_budget_caps_and_prices_are_enforced_before_sending(fake):
    # Nothing configured: no prices, so nothing can be bounded → refused.
    cloud_policy.create_authorization("anthropic", max_cost_usd=1.0)
    with local_answer():
        _t, usage = gateway.chat_with_usage(CLAUDE, MSG)
    assert fake.requests == [] and any("no price" in p for p in usage["receipt"]["policy"])

    # Prices but zero budget caps (the default) → refused.
    cloud_policy.BUDGET_FILE.write_text(json.dumps(
        {"prices": {CLAUDE: {"input_per_mtok": 1.0, "output_per_mtok": 2.0}}}
    ))
    with local_answer():
        _t, usage = gateway.chat_with_usage(CLAUDE, MSG)
    assert fake.requests == [] and any("exceeds" in p for p in usage["receipt"]["policy"])

    # Unpriced model → refused.
    allow("anthropic")
    with local_answer():
        _t, usage = gateway.chat_with_usage("anthropic/unpriced-model", MSG)
    assert fake.requests == [] and any("no price" in p for p in usage["receipt"]["policy"])

    # Worst case above the authorization's remaining cap → refused.
    aid = allow("openai", cap=0.000001)
    with local_answer():
        gateway.chat_with_usage(GPT, MSG)
    assert fake.requests == []
    assert cloud_policy.revoke_authorization(aid)


def test_usage_is_accounted_and_counts_against_the_authorization(fake):
    aid = allow("openai", cap=1.0, price=(10.0, 20.0))
    fake.add(FakeResponse(openai_completed(usage=(100, 50))))
    _t, usage = gateway.chat_with_usage(GPT, MSG)
    [row] = cloud_policy.usage_rows()
    assert row["input_tokens"] == 100 and row["output_tokens"] == 50
    assert row["estimated_usd"] == pytest.approx(100 / 1e6 * 10 + 50 / 1e6 * 20)
    auth = next(a for a in cloud_policy.list_authorizations() if a["id"] == aid)
    assert auth["spent_usd"] == pytest.approx(row["estimated_usd"])
    assert cloud_policy.monthly_spend("openai") == pytest.approx(row["estimated_usd"])
    assert usage["receipt"]["executed_provider"] == "openai"
    assert usage["provider_model"] == "gpt-test-model-2026"


def test_expired_and_revoked_authorizations_do_not_count(fake):
    aid = allow("anthropic")
    cloud_policy.revoke_authorization(aid)
    assert cloud_policy.active_authorization("anthropic", "general") is None
    cloud_policy.create_authorization("anthropic", max_cost_usd=1.0, expires_in_s=-1)
    assert cloud_policy.active_authorization("anthropic", "general") is None
    role_bound = cloud_policy.create_authorization("anthropic", max_cost_usd=1.0, roles=["research"])
    assert cloud_policy.active_authorization("anthropic", "conversation") is None
    assert cloud_policy.active_authorization("anthropic", "research")["id"] == role_bound


def test_egress_requires_a_reservation_even_if_called_directly(fake):
    allow("openai")
    adapter = providers.adapter_for("openai")
    with pytest.raises(cloud_policy.NotAuthorized):
        adapter.chat(base.Request(model="gpt-test-model", messages=MSG))
    assert fake.requests == []


# ====================================================================== adapters: chat, stream, tools


@pytest.mark.parametrize(
    "model,response,provider",
    [(GPT, openai_completed(), "openai"), (CLAUDE, anthropic_message(), "anthropic"), (GEMINI, gemini_response(), "google")],
)
def test_each_provider_answers_with_a_receipt(fake, model, response, provider):
    allow(provider)
    fake.add(FakeResponse(response))
    text, usage = gateway.chat_with_usage(model, MSG)
    assert text == "A dry fly floats."
    receipt = usage["receipt"]
    assert receipt["status"] == "completed" and receipt["executed_locality"] == "cloud"
    assert receipt["executed_provider"] == provider
    assert receipt["attempts"][0]["prompt_tokens"] == 12
    assert any("cloud authorized by" in p for p in receipt["policy"])
    assert fake.requests[0]["url"].startswith("https://")


def test_openai_request_does_not_ask_openai_to_store_history(fake):
    allow("openai")
    fake.add(FakeResponse(openai_completed()))
    gateway.chat_with_usage(GPT, MSG)
    assert fake.requests[0]["body"]["store"] is False


@pytest.mark.parametrize(
    "model,provider,response",
    [
        (GPT, "openai", openai_completed(text="", calls=[("call_1", "route", {"action": "weather_forecast"})])),
        (CLAUDE, "anthropic", anthropic_message(text="", calls=[("tu_1", "route", {"action": "weather_forecast"})], stop="tool_use")),
        (GEMINI, "google", {"candidates": [{"content": {"parts": [{"functionCall": {"name": "route", "args": {"action": "weather_forecast"}}}]},
                                             "finishReason": "STOP"}], "usageMetadata": {}}),
    ],
)
def test_tool_calls_are_normalised_across_providers(fake, model, provider, response):
    allow(provider)
    fake.add(FakeResponse(response))
    tools = [{"type": "function", "function": {"name": "route", "parameters": {"type": "object"}}}]
    result, usage = gateway.chat_with_tools(model, MSG, tools)
    assert [(c["name"], c["arguments"]) for c in result["tool_calls"]] == [("route", {"action": "weather_forecast"})]
    body = json.dumps(fake.requests[0]["body"])
    assert "route" in body  # the tool schema was translated and sent
    assert usage["receipt"]["status"] == "completed"


def test_tool_results_round_trip_in_each_wire_format():
    convo = [
        {"role": "user", "content": "weather?"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "c1", "name": "route", "arguments": {"a": 1}}]},
        {"role": "tool", "tool_call_id": "c1", "name": "route", "content": "sunny"},
    ]
    oa = providers.adapter_for("openai")._input(convo)
    assert {"type": "function_call_output", "call_id": "c1", "output": "sunny"} in oa
    an = providers.adapter_for("anthropic")._messages(convo)
    assert an[-1]["content"][0] == {"type": "tool_result", "tool_use_id": "c1", "content": "sunny"}
    ge = providers.adapter_for("google")._contents(convo)
    assert ge[-1]["parts"][0]["functionResponse"]["name"] == "route"


def test_streaming_from_each_provider(fake):
    allow("openai")
    allow("anthropic")
    allow("google")
    fake.add(FakeResponse(lines=sse(
        ("", {"type": "response.output_text.delta", "delta": "A dry "}),
        ("", {"type": "response.output_text.delta", "delta": "fly."}),
        ("", {"type": "response.completed", "response": openai_completed()}),
    )))
    fake.add(FakeResponse(lines=sse(
        ("message_start", {"type": "message_start", "message": {"model": "claude-test-model", "usage": {"input_tokens": 9}}}),
        ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text"}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "A dry fly."}}),
        ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 4}}),
        ("message_stop", {"type": "message_stop"}),
    )))
    fake.add(FakeResponse(lines=sse(
        ("", {"candidates": [{"content": {"parts": [{"text": "A dry "}]}}]}),
        ("", {"candidates": [{"content": {"parts": [{"text": "fly."}]}, "finishReason": "STOP"}],
              "usageMetadata": {"promptTokenCount": 9, "candidatesTokenCount": 4}}),
    )))
    for model in (GPT, CLAUDE, GEMINI):
        usage: dict = {}
        assert "".join(gateway.stream_chat(model, MSG, usage=usage)) == "A dry fly."
        assert usage["receipt"]["status"] == "completed"
    assert fake.requests[2]["url"].endswith(":streamGenerateContent?alt=sse")


def test_stream_ending_without_a_terminal_event_is_an_interruption(fake):
    allow("anthropic")
    fake.add(FakeResponse(lines=sse(
        ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text"}}),
        ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Half an"}}),
    )))
    usage: dict = {}
    chunks = []
    with patch.object(gateway, "_ollama_stream") as local:
        with pytest.raises(boundary.StreamInterrupted):
            for c in gateway.stream_chat(CLAUDE, MSG, usage=usage):
                chunks.append(c)
    local.assert_not_called()
    assert chunks == ["Half an"]
    assert usage["receipt"]["status"] == "interrupted"
    [row] = cloud_policy.usage_rows()
    assert row["status"] == "interrupted"  # the partial attempt is still accounted


def test_cloud_stream_failing_before_output_falls_back_locally(fake):
    allow("openai")
    fake.add(http_error(503)).add(http_error(503)).add(http_error(503))

    def local_stream(*a, **k):
        yield "local"

    with patch.object(gateway, "_ollama_stream", side_effect=local_stream):
        usage: dict = {}
        assert list(gateway.stream_chat(GPT, MSG, usage=usage)) == ["local"]
    assert [a["locality"] for a in usage["receipt"]["attempts"]] == ["cloud", "local"]


def test_cancellation_stops_a_cloud_stream_without_fallback(fake):
    allow("openai")
    fake.add(FakeResponse(lines=sse(
        ("", {"type": "response.output_text.delta", "delta": "one "}),
        ("", {"type": "response.output_text.delta", "delta": "two "}),
        ("", {"type": "response.output_text.delta", "delta": "three"}),
        ("", {"type": "response.completed", "response": openai_completed()}),
    )))
    seen = {"n": 0}

    def cancel():
        seen["n"] += 1
        return seen["n"] > 2

    usage: dict = {}
    with patch.object(gateway, "_ollama_stream") as local:
        out = list(gateway.stream_chat(GPT, MSG, usage=usage, cancel_check=cancel))
    local.assert_not_called()
    assert out == ["one "] or out == ["one ", "two "]
    assert usage["receipt"]["status"] == "cancelled"


# ====================================================================== retries, rate limits, outages


def test_rate_limit_is_retried_with_retry_after_then_succeeds_once(fake):
    allow("anthropic")
    fake.add(http_error(429, retry_after="7")).add(FakeResponse(anthropic_message()))
    text, usage = gateway.chat_with_usage(CLAUDE, MSG)
    assert text == "A dry fly floats."
    assert {"slept": 7.0} in fake.requests
    assert len(cloud_policy.usage_rows()) == 1


def test_persistent_outage_falls_back_locally_and_opens_the_circuit(fake):
    allow("google")
    for _ in range(3):
        fake.add(http_error(503))
    with local_answer():
        text, usage = gateway.chat_with_usage(GEMINI, MSG)
    assert text == "local answer"
    assert [a["status"] for a in usage["receipt"]["attempts"]] == ["failed", "completed"]
    assert base.circuit_open("google")
    with local_answer():
        gateway.chat_with_usage(GEMINI, MSG)
    assert len([r for r in fake.requests if "url" in r]) == 3, "an open circuit still sent traffic"


def test_authentication_failure_is_not_retried(fake):
    allow("openai")
    fake.add(http_error(401))
    with local_answer():
        _t, usage = gateway.chat_with_usage(GPT, MSG)
    assert len([r for r in fake.requests if "url" in r]) == 1
    assert "authentication failed" in usage["receipt"]["attempts"][0]["error"]


def test_bad_requests_do_not_fall_back_silently(fake):
    allow("anthropic")
    fake.add(http_error(400))
    with local_answer() as local:
        with pytest.raises(base.BadRequest):
            gateway.chat_with_usage(CLAUDE, MSG)
    local.assert_not_called()


def test_no_duplicate_tool_execution_after_a_retry(fake):
    allow("openai")
    tools = [{"type": "function", "function": {"name": "add_task", "parameters": {"type": "object"}}}]
    fake.add(http_error(503)).add(
        FakeResponse(openai_completed(text="", calls=[("c1", "add_task", {"title": "buy tippet"})]))
    )
    executed: list[dict] = []
    result, usage = gateway.chat_with_tools(GPT, MSG, tools)
    for call in result["tool_calls"]:  # ARIA executes only the completed response's calls
        executed.append(call["arguments"])
    assert executed == [{"title": "buy tippet"}]
    assert len(cloud_policy.usage_rows()) == 1


# ====================================================================== continuity across providers


def test_the_same_authorized_continuity_reaches_each_provider_and_nothing_else(fake):
    for p in ("openai", "anthropic", "google"):
        allow(p, classes=("continuity",))
    fake.add(FakeResponse(openai_completed())).add(FakeResponse(anthropic_message())).add(FakeResponse(gemini_response()))
    block = "Conversation history (HITS) — Decided: SQLite for the fishing log."
    messages = [
        {"role": "system", "content": f"You are ARIA.\n\n{block}\n\nRelevant memories:\n- private preference"},
        {"role": "user", "content": "Continue the project we were discussing."},
    ]
    for model in (GPT, CLAUDE, GEMINI):
        gateway.chat_with_usage(model, messages)
    for req in fake.requests:
        sent = json.dumps(req["body"])
        assert "SQLite for the fishing log" in sent
        assert "private preference" not in sent and "You are ARIA" not in sent


# ====================================================================== routing


def test_explicit_cloud_model_routes_to_the_native_adapter_when_permitted(fake):
    route = policy.select_route(CLAUDE)
    assert route.backend == "native" and route.cloud


def test_litellm_cloud_calls_need_the_same_authorization(fake, monkeypatch):
    monkeypatch.setattr(providers, "has_credentials", lambda p: False)
    monkeypatch.setattr(gateway, "litellm_available", lambda: True)
    with patch.object(gateway, "_litellm_chat_with_usage") as cloud, local_answer():
        _t, usage = gateway.chat_with_usage(CLAUDE, MSG)
    cloud.assert_not_called()
    assert usage["receipt"]["executed_locality"] == "local"


def test_default_conversation_stays_local_and_routing_explains_itself(fake):
    allow("anthropic")
    decision = provider_routing.choose("conversation")
    assert decision.chosen.locality == "local"
    assert any("auto_escalate off" in e for e in decision.explanation)
    assert policy.select_route(LOCAL, role="conversation").backend == "ollama"


def test_auto_escalation_ranks_permitted_candidates_by_quality(fake, monkeypatch):
    allow("anthropic")
    provider_routing.ROUTING_FILE.write_text(json.dumps({
        "auto_escalate": True,
        "candidates": {"reasoning": [CLAUDE, GPT]},
        "quality": {CLAUDE: {"reasoning": 0.97}},
    }))
    provider_routing.QUALITY_FILE.write_text(json.dumps(
        {"by_model": {LOCAL: {"categories": {"reasoning": {"accuracy": 0.7, "p50_ms": 128}}}}}
    ))
    monkeypatch.setattr(boundary, "model_capabilities", lambda m: None)
    decision = provider_routing.choose("reasoning")
    assert decision.chosen.model == CLAUDE
    assert any(GPT in e and "no active owner authorization" in e for e in decision.explanation)
    # privacy still wins over measured quality
    local_only = provider_routing.choose("reasoning", privacy=boundary.LOCAL_ONLY)
    assert local_only.chosen.model == LOCAL


# ====================================================================== router role defaults


def test_utility_roles_get_bounded_output_and_no_thinking(fake, monkeypatch):
    monkeypatch.setattr(boundary, "model_capabilities", lambda m: frozenset({"completion", "thinking"}))
    seen = {}

    def capture(model, messages, **kwargs):
        seen.update(kwargs)
        return '{"action": "chat"}', {}

    with patch.object(gateway, "_ollama_chat_with_usage", side_effect=capture):
        gateway.chat_with_usage("qwen3:1.7b", MSG, role="router")
    assert seen["options"]["num_predict"] == 256 and seen["think"] is False
    with patch.object(gateway, "_ollama_chat_with_usage", side_effect=capture):
        seen.clear()
        gateway.chat_with_usage("qwen3:1.7b", MSG, role="router", options={"num_predict": 120})
    assert seen["options"]["num_predict"] == 120  # explicit options win


def test_provider_errors_never_echo_the_key_into_errors_or_logs(fake, caplog):
    import logging

    allow("openai")
    echo = urllib.error.HTTPError(
        "https://x", 400, "bad", {}, io.BytesIO(("echo: Bearer " + KEYS["openai_api_key"]).encode())
    )
    fake.add(echo)
    with caplog.at_level(logging.DEBUG):
        with local_answer():
            with pytest.raises(base.BadRequest) as info:
                gateway.chat_with_usage(GPT, MSG)
    # The provider body is truncated into the error; the key must be masked.
    assert KEYS["openai_api_key"] not in str(info.value)
    assert KEYS["openai_api_key"] not in caplog.text
    assert all(KEYS["openai_api_key"] not in json.dumps(r) for r in boundary.recent_receipts())


@pytest.mark.parametrize("status", [401, 403, 404, 429, 503])
@pytest.mark.parametrize("stream", [False, True])
def test_gemini_free_candidate_failures_fall_back_without_cloud_substitution(fake, status, stream):
    allow("google", price=(0.0, 0.0))
    for _ in range(3 if status in (429, 503) else 1):
        fake.add(http_error(status, retry_after="0" if status == 429 else None))
    if stream:
        with patch.object(gateway, "_ollama_stream", return_value=iter(["local"])):
            assert list(gateway.stream_chat(GEMINI, MSG)) == ["local"]
    else:
        with local_answer():
            assert gateway.chat_with_usage(GEMINI, MSG)[0] == "local answer"
    assert all("generativelanguage.googleapis.com" in r["url"] for r in fake.requests if "url" in r)
    assert cloud_policy.monthly_spend() == 0.0
