"""Tests for workstation dashboard and activity polish."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.learning_notice import learning_notice, memory_retrieval_hint
from jarvis.runtime_introspection import collect_dashboard, format_status_summary, is_status_command
from jarvis.workstation_activity import list_events, record_event

from test_runtime_client import SAMPLE_MC, _mock_client

FULL_MC = {
    **SAMPLE_MC,
    "memory": {"provider": "platform", "entry_count": 0},
    "knowledge": {"retrieval": "platform", "documents": 0},
    "activity": {"events": []},
    "performance": {"run_count": 0},
    "notifications": [],
    "settings": {"mission_control_port": "8780"},
}

OVERVIEW_MARKDOWN = (
    "## Mission Control\n**Status:** healthy\n**Mode:** platform-attached\n**Acceptance:** 100%"
)


def test_status_command_maps():
    assert is_status_command("status") == "status_summary"
    assert is_status_command("/health") == "runtime_health"
    assert is_status_command("hello") is None


@patch("jarvis.runtime_introspection.get_runtime_client")
def test_collect_dashboard_shape(mock_get_client):
    mock_get_client.return_value = _mock_client(FULL_MC)
    data = collect_dashboard()
    assert data.get("ok") is True
    assert "overview" in data
    assert "inference" in data
    assert "memory" in data
    assert "services" in data
    assert "activity" in data
    assert "applications" in data


@patch("jarvis.mission_control.format_overview_markdown", return_value=OVERVIEW_MARKDOWN)
def test_format_status_summary_has_key_lines(mock_md):
    text = format_status_summary()
    assert "Mission Control" in text
    assert "Status:" in text
    assert "Mode:" in text
    assert "Acceptance:" in text
    mock_md.assert_called_once()


def test_activity_record_and_filter():
    record_event("test_event", component="test", detail="unit test activity")
    events = list_events(limit=5, query="unit test")
    assert any(e.get("type") == "test_event" for e in events)


def test_learning_notice_messages():
    assert "memory" in learning_notice("long_term").lower()
    hint = memory_retrieval_hint([{"type": "fact", "content": "x"}])
    assert "memory" in hint.lower()
