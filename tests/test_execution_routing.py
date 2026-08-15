"""Regression: benchmark-driven execution routing (no hardcoded AMD/NVIDIA)."""

from __future__ import annotations

from pathlib import Path

from jarvis.inference.execution_benchmark import (
    _has_size_token,
    discover_models_for_workload,
)
from jarvis.inference.execution_policy import (
    apply_policy_to_route,
    resolve_execution,
    routing_matrix,
)


def test_size_token_does_not_match_larger_sizes():
    assert _has_size_token("gemma3:4b", "4b")
    assert not _has_size_token("qwen2.5:14b", "4b")
    assert not _has_size_token("llava:13b", "3b")
    assert _has_size_token("qwen2.5:3b", "3b")
    assert _has_size_token("qwen3:1.7b", "1.7b")


def test_lightweight_discovery_excludes_14b_false_positives(monkeypatch):
    monkeypatch.setattr(
        "jarvis.inference.execution_benchmark._list_ollama_models",
        lambda: [
            ("qwen2.5:14b", 9.0),
            ("llava:13b", 8.0),
            ("deepseek-r1:14b", 9.0),
            ("qwen3:1.7b", 1.4),
            ("gemma3:4b", 3.3),
            ("qwen2.5:3b", 1.9),
            ("phi3:mini", 2.2),
        ],
    )
    models = discover_models_for_workload("lightweight", max_models=4)
    assert "qwen2.5:14b" not in models
    assert "llava:13b" not in models
    assert "deepseek-r1:14b" not in models
    assert any("1.7b" in m or "3b" in m or "4b" in m or "mini" in m for m in models)


def test_resolve_execution_non_llm_reference():
    plan = resolve_execution("reference")
    assert plan.provider == "local_docs"
    assert plan.model is None
    assert plan.hardware == "cpu"
    assert plan.source == "non_llm"


def test_apply_policy_uses_benchmark_when_present(tmp_path, monkeypatch):
    policy = {
        "version": "1.0",
        "benchmark_date": "2026-07-14T00:00:00",
        "workloads": {
            "lightweight": {
                "model": "gemma3:4b",
                "hardware": "nvidia",
                "provider": "ollama",
                "selection_reason": "measured",
                "warm_latency_ms": 100.0,
                "fallback_model": "qwen2.5:3b",
                "fallback_hardware": "cpu",
            }
        },
    }
    path = tmp_path / "execution_routing_policy.json"
    path.write_text(__import__("json").dumps(policy), encoding="utf-8")
    monkeypatch.setattr("jarvis.inference.execution_policy._POLICY_FILE", path)
    monkeypatch.delenv("JARVIS_EXECUTION_MODEL", raising=False)
    monkeypatch.setattr(
        "jarvis.model_store.explicit_saved_model",
        lambda role: None,
    )
    overlay = apply_policy_to_route(model="qwen2.5-coder:1.5b-base", role="router")
    assert overlay["model"] == "gemma3:4b"
    assert overlay["hardware"] == "nvidia"
    assert overlay["source"] == "benchmark"


def test_apply_policy_user_config_beats_benchmark(tmp_path, monkeypatch):
    policy = {
        "version": "1.0",
        "benchmark_date": "2026-07-14T00:00:00",
        "workloads": {
            "coding": {
                "model": "deepseek-coder:latest",
                "hardware": "nvidia",
                "provider": "ollama",
                "selection_reason": "measured",
                "warm_latency_ms": 200.0,
                "fallback_model": "qwen2.5-coder:1.5b-base",
                "fallback_hardware": "cpu",
            }
        },
    }
    path = tmp_path / "execution_routing_policy.json"
    path.write_text(__import__("json").dumps(policy), encoding="utf-8")
    monkeypatch.setattr("jarvis.inference.execution_policy._POLICY_FILE", path)
    monkeypatch.delenv("JARVIS_EXECUTION_MODEL", raising=False)
    monkeypatch.setattr(
        "jarvis.model_store.explicit_saved_model",
        lambda role: "qwen2.5-coder:7b",
    )
    overlay = apply_policy_to_route(model="deepseek-coder:latest", role="coding")
    assert overlay["model"] == "qwen2.5-coder:7b"
    assert overlay["hardware"] == "nvidia"
    assert overlay["source"] == "user_config"


def test_gateway_merges_device_options(monkeypatch):
    from jarvis.inference import gateway

    monkeypatch.setattr(
        "jarvis.inference.execution_policy.apply_policy_to_route",
        lambda **kwargs: {
            "model": "gemma3:4b",
            "hardware": "cpu",
            "source": "benchmark",
            "reason": "test",
            "workload": "lightweight",
        },
    )
    captured: dict = {}

    def fake_ollama(model, messages, **kwargs):
        captured["model"] = model
        captured["options"] = kwargs.get("options")
        return "ok", {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(gateway, "_ollama_chat_with_usage", fake_ollama)
    monkeypatch.setattr(
        gateway,
        "select_route",
        lambda model, role="general", messages=None, lock_model=False: type(
            "R",
            (),
            {"backend": "ollama", "model": model, "reason": "test"},
        )(),
    )
    text, usage = gateway.chat_with_usage("ignored:7b", [{"role": "user", "content": "hi"}], role="general")
    assert text == "ok"
    assert captured["model"] == "gemma3:4b"
    assert captured["options"]["num_gpu"] == 0
    assert usage["execution_hardware"] == "cpu"
    assert usage["execution_source"] == "benchmark"


def test_gateway_stream_records_trace_and_usage(monkeypatch):
    from types import SimpleNamespace

    from jarvis.inference import gateway

    decisions = []
    monkeypatch.setattr(
        "jarvis.inference.execution_policy.apply_policy_to_route",
        lambda **kwargs: {
            "model": "gemma3:4b",
            "hardware": "cpu",
            "source": "benchmark",
            "reason": "measured",
            "workload": "conversation",
        },
    )
    monkeypatch.setattr(
        gateway,
        "select_route",
        lambda model, role="general", messages=None, lock_model=False: SimpleNamespace(
            backend="ollama",
            model=model,
            reason="selected",
            cloud=False,
        ),
    )
    monkeypatch.setattr("jarvis.routing_trace.record_gateway", lambda *, decision: decisions.append(decision))
    monkeypatch.setattr(gateway, "_ollama_stream", lambda model, messages, **kwargs: iter(["hi"]))

    usage = {}
    tokens = list(gateway.stream_chat("ignored:7b", [{"role": "user", "content": "hi"}], role="conversation", usage=usage))

    assert tokens == ["hi"]
    assert decisions
    assert decisions[-1]["stream"] is True
    assert decisions[-1]["model"] == "gemma3:4b"
    assert usage["execution_model"] == "gemma3:4b"
    assert usage["execution_source"] == "benchmark"


def test_routing_matrix_rows_cover_request_classes():
    rows = routing_matrix()
    classes = {r["request_class"] for r in rows}
    for required in ("greeting", "reference", "runtime", "coding", "reasoning", "vision", "voice"):
        assert required in classes


def test_conversation_trace_includes_execution():
    from aria_core.conversation_trace import build_conversation_trace

    ct = build_conversation_trace(
        prompt="Show me the Docker Compose documentation.",
        intent={"action": "search_reference", "execution": {"request_class": "reference"}},
        action="search_reference",
        route="Local",
        handler="reference",
        latency_ms=12.0,
        route_latency_ms=1.0,
        response_length=100,
        error=None,
        conversation_id="t1",
    )
    assert "execution" in ct
    assert ct["execution"]["provider"] == "local_docs"
    assert ct["execution"]["hardware"] == "cpu"


def test_docs_writers_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "jarvis" / "inference" / "execution_benchmark.py").is_file()
    assert (root / "scripts" / "run_execution_benchmark.py").is_file()
