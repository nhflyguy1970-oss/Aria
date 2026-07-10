"""Tests for workstation dashboard and activity polish."""

from __future__ import annotations

from jarvis.learning_notice import learning_notice, memory_retrieval_hint
from jarvis.runtime_introspection import collect_dashboard, format_status_summary, is_status_command
from jarvis.workstation_activity import list_events, record_event


def test_status_command_maps():
    assert is_status_command("status") == "status_summary"
    assert is_status_command("/health") == "runtime_health"
    assert is_status_command("hello") is None


def test_collect_dashboard_shape():
    data = collect_dashboard()
    assert data.get("ok") is True
    assert "overview" in data
    assert "inference" in data
    assert "memory" in data
    assert "services" in data
    assert "activity" in data
    assert "applications" in data


def test_format_status_summary_has_key_lines():
    text = format_status_summary()
    assert "Mission Control" in text
    assert "Status:" in text
    assert "Mode:" in text
    assert "Acceptance:" in text


def test_activity_record_and_filter():
    record_event("test_event", component="test", detail="unit test activity")
    events = list_events(limit=5, query="unit test")
    assert any(e.get("type") == "test_event" for e in events)


def test_learning_notice_messages():
    assert "memory" in learning_notice("long_term").lower()
    hint = memory_retrieval_hint([{"type": "fact", "content": "x"}])
    assert "memory" in hint.lower()
