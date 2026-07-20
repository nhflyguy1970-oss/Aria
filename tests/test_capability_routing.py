"""Capability-based model routing — registry and brain routing integration."""

from __future__ import annotations

import pytest


def test_capability_memory_is_non_llm() -> None:
    from jarvis.capability_routing import resolve_model_for_capability

    assert resolve_model_for_capability("memory") is None
    assert resolve_model_for_capability("mission_control") is None


def test_capability_roles_resolve_models() -> None:
    from jarvis.capability_routing import configured_model_for_role, resolve_model_for_capability

    assert resolve_model_for_capability("coding") == configured_model_for_role("coding") or resolve_model_for_capability("coding")
    assert resolve_model_for_capability("vision")
    assert configured_model_for_role("web_research")


def test_brain_routing_deep_uses_reasoning_role(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.brain_routing import needs_deep_thinking, select_chat_model
    from jarvis.model_store import model_for

    monkeypatch.setenv("JARVIS_BRAIN_ROUTING", "1")
    assert needs_deep_thinking("explain why recursion overflows", action="chat")
    assert not needs_deep_thinking("hello", action="chat")
    deep = select_chat_model(
        "explain step by step",
        {},
        action="chat",
        voice=False,
        session_chat_model="",
    )
    assert deep == model_for("reasoning")


def test_conversation_engine_uses_capability_routing() -> None:
    from jarvis.capability_routing import resolve_conversation_model

    model, role = resolve_conversation_model("hello there", {}, action="chat")
    assert model
    assert role in ("conversation", "fast_chat", "reasoning")


def test_legacy_general_alias() -> None:
    from jarvis.llm import conversation_model, general_model

    assert general_model() == conversation_model()


def test_routing_matrix_complete() -> None:
    from jarvis.capability_routing import routing_matrix

    rows = routing_matrix()
    caps = {r["capability"] for r in rows}
    assert "memory" in caps
    assert "coding" in caps
    assert "conversation" in caps
