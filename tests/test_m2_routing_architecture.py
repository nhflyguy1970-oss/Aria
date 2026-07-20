"""M2 routing trace, model policy, and capability health tests."""

from __future__ import annotations

import pytest


def test_routing_trace_disabled_by_default() -> None:
    from jarvis.routing_trace import begin_trace, get_current_trace, routing_trace_enabled

    assert not routing_trace_enabled()
    begin_trace("hello")
    assert get_current_trace() is None


def test_routing_trace_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.routing_trace import (
        begin_trace,
        finalize_trace,
        get_current_trace,
        record_capability,
        record_intent,
    )

    monkeypatch.setenv("JARVIS_ROUTING_TRACE", "1")
    begin_trace("What happened yesterday?")
    record_intent(intent="episodic_recall", action="memory_about_user")
    record_capability(capability="episodic_recall", role="memory")
    assert get_current_trace() is not None
    trace = finalize_trace(response_kind="memory_recall")
    assert trace
    assert trace["capability"] == "episodic_recall"
    assert trace["selected_model"] is None


def test_model_policy_non_llm_memory() -> None:
    from jarvis.model_policy import select_model_for_role

    sel = select_model_for_role("memory")
    assert sel.selected_model is None
    assert sel.execution_path == "bypass"


def test_model_policy_coding_has_model() -> None:
    from jarvis.model_policy import select_model_for_role

    sel = select_model_for_role("coding")
    assert sel.configured_model
    assert sel.selected_model


def test_capability_health_report() -> None:
    from jarvis.capability_health import capability_health_report

    rows = capability_health_report()
    caps = {r["capability"] for r in rows}
    assert "conversation" in caps
    assert "memory" in caps
    assert "coding" in caps


def test_routing_explain_always_intercepts(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.routing_explain import is_routing_explain_query, try_routing_explain

    monkeypatch.delenv("JARVIS_ROUTING_DEBUG", raising=False)
    monkeypatch.delenv("JARVIS_DEBUG", raising=False)
    assert is_routing_explain_query("Why did you choose that model?")
    hit = try_routing_explain("Why did you choose that model?")
    assert hit and hit["action"] == "chat"
    assert hit["params"].get("routing_explain")


def test_routing_explain_mission_control_go_variant() -> None:
    from jarvis.routing_explain import is_routing_explain_query, try_routing_explain

    assert is_routing_explain_query("Why did this go to Mission Control?")
    hit = try_routing_explain("Why did this go to Mission Control?")
    assert hit and hit["action"] == "chat"


def test_episodic_capability_resolution() -> None:
    from jarvis.capability_routing import capability_for_action_and_message

    assert capability_for_action_and_message("memory_about_user", "What happened yesterday?") == "episodic_recall"
    assert capability_for_action_and_message("memory_about_user", "Yesterday I bought a kayak.") == "episodic_teaching"
