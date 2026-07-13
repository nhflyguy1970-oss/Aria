"""Conversation Trace — passive execution metadata only."""

from __future__ import annotations

from aria_core.conversation_trace import (
    build_conversation_trace,
    format_user_view,
    infer_organs,
)


def test_reflex_trace_skips_organs():
    intent = {
        "action": "greeting",
        "router": "reflex",
        "router_stage": "pre_nlu_reflex",
        "reflex_category": "social.greeting",
        "reflex_confidence": 0.98,
        "thinking": "greeting",
    }
    trace = build_conversation_trace(
        prompt="Hello Aria",
        intent=intent,
        action="greeting",
        route="Meta",
        handler="greeting",
        latency_ms=1.2,
        route_latency_ms=0.4,
        response_length=40,
        error=None,
        conversation_id="main",
    )
    assert trace["reflex"]["matched"] is True
    assert trace["nlu"]["invoked"] is False
    assert all(v.get("skipped") for v in trace["organs"].values())
    assert "chain" not in format_user_view(trace).lower()
    assert "system prompt" not in format_user_view(trace).lower()


def test_chat_trace_marks_memory_and_reasoning():
    organs = infer_organs({"router_stage": "nlu_pipeline"}, "chat")
    assert organs["memory"]["used"] is True
    assert organs["memory"]["read"] is True
    assert organs["reasoning"]["used"] is True


def test_record_prompt_execution_attaches_trace():
    from jarvis.routing_inspector import record_prompt_execution

    saved = record_prompt_execution(
        prompt="Hello Aria",
        intent={
            "action": "greeting",
            "router": "reflex",
            "router_stage": "pre_nlu_reflex",
            "reflex_category": "social.greeting",
            "route_handler": "greeting",
        },
        conversation_id="main",
        latency_ms=2.0,
        route_latency_ms=0.5,
        result={"ok": True, "message": "Hello!"},
        request_id="req-1",
    )
    assert saved.get("conversation_trace")
    assert saved["conversation_trace"]["reflex"]["matched"] is True
    assert saved.get("request_id") == "req-1"
    assert "prompt" in saved
    # Never store CoT fields
    assert "chain_of_thought" not in saved
    assert "system_prompt" not in (saved.get("conversation_trace") or {})
