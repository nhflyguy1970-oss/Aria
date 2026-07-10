"""Tests for routing inspector recording and classification."""

from __future__ import annotations

from jarvis.routing_inspector import (
    build_execution_flow,
    classify_route,
    record_prompt_execution,
)


def test_classify_route_families():
    assert classify_route("runtime_gpu") == "Runtime"
    assert classify_route("web_search") == "Search"
    assert classify_route("memory_search") == "Memory"
    assert classify_route("coding_fix") == "Coding"
    assert classify_route("learn_about") == "Knowledge"


def test_build_execution_flow_runtime():
    flow = build_execution_flow(
        prompt="gpu?",
        intent="runtime_gpu",
        route="Runtime",
        handler="RuntimeClient",
        backend="Mission Control",
        stage="finalize",
    )
    assert flow[0] == "User"
    assert "Runtime Priority" in flow
    assert "Mission Control" in flow


def test_record_prompt_execution_persists():
    record = record_prompt_execution(
        prompt="What GPU are you using?",
        intent={
            "action": "runtime_gpu",
            "route_trace": {
                "route": "Runtime",
                "handler": "RuntimeClient",
                "confidence": 0.99,
                "stage": "finalize",
                "reason": "runtime_keyword",
            },
        },
        conversation_id="main",
        latency_ms=17.0,
        route_latency_ms=2.0,
        result={"ok": True, "message": "GPU info"},
    )
    assert record.get("intent") == "runtime_gpu"
    assert record.get("route") == "Runtime"
    assert record.get("response_length") > 0


def test_routing_command_detection():
    from jarvis.routing_inspector import is_routing_command

    assert is_routing_command("routing") == "routing_last"
    assert is_routing_command("routing stats") == "routing_stats"


def test_runtime_keywords_still_detected():
    from jarvis.runtime_routing import is_runtime_routing_question

    assert is_runtime_routing_question("postgres status")
