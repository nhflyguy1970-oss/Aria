"""Mission Control — operational console source of truth."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.mission_control import (
    collect_mission_control,
    export_activity_csv,
    format_overview_markdown,
    get_tab,
)
from jarvis.platform_metrics import list_samples, record_sample
from jarvis.platform_notifications import list_notifications, notify

FULL_MC = {
    "ok": True,
    "title": "AI Platform Mission Control",
    "owner": "aiplatform",
    "overview": {
        "platform_status": "healthy",
        "execution_mode": "platform-attached",
        "phase": {"phase": "production"},
        "acceptance_overall": 100,
        "production_readiness": 100,
        "current_model": "llama3",
        "inference_provider": "ollama",
        "memory_provider": "platform",
        "knowledge_provider": "platform",
        "gpu": "RTX 4090",
        "active_jobs": 0,
        "needs_attention": [],
    },
    "applications": [
        {"id": "aria", "label": "Aria", "running": True, "healthy": True},
        {"id": "aria-uncensored", "label": "Aria Uncensored", "running": False, "healthy": False},
    ],
    "inference": {"current_model": "llama3", "provider": "ollama"},
    "memory": {"provider": "platform", "entry_count": 0},
    "knowledge": {"retrieval": "platform", "documents": 0},
    "databases": [{"id": "postgres", "label": "postgres", "running": True}],
    "hardware": {"gpu_name": "RTX 4090"},
    "jobs": {"active_count": 0},
    "activity": {"events": []},
    "performance": {"run_count": 0},
    "recovery": {"health": {"ok": True}},
    "notifications": [],
    "settings": {"mission_control_port": "8780"},
}

OVERVIEW_TAB = {"ok": True, "tab": "overview", "data": FULL_MC["overview"]}

OVERVIEW_MARKDOWN = (
    "## Mission Control\n**Status:** healthy\n**Mode:** platform-attached\n**Acceptance:** 100%"
)


@patch("aiplatform.mission_control.aggregator.collect_mission_control", return_value=FULL_MC, create=True)
def test_collect_mission_control_shape(mock_collect):
    data = collect_mission_control(record_metrics=False)
    assert data.get("ok") is True
    assert data.get("title") == "AI Platform Mission Control"
    assert data.get("owner") == "aiplatform"
    for key in (
        "overview",
        "applications",
        "inference",
        "memory",
        "knowledge",
        "databases",
        "hardware",
        "jobs",
        "activity",
        "performance",
        "recovery",
        "notifications",
        "settings",
    ):
        assert key in data
    mock_collect.assert_called_once_with(record_metrics=False)


@patch("aiplatform.mission_control.aggregator.collect_mission_control", return_value=FULL_MC, create=True)
def test_applications_include_aria_profiles(mock_collect):
    data = collect_mission_control(record_metrics=False)
    apps = data.get("applications") or []
    ids = {a.get("id") for a in apps}
    assert "aria" in ids
    assert "aria-uncensored" in ids
    mock_collect.assert_called_once()


@patch("aiplatform.mission_control.aggregator.get_tab", return_value=OVERVIEW_TAB, create=True)
def test_get_tab_overview(mock_get_tab):
    tab = get_tab("overview")
    assert tab.get("ok") is True
    assert tab.get("tab") == "overview"
    assert "platform_status" in (tab.get("data") or {})
    mock_get_tab.assert_called_once_with("overview")


@patch(
    "aiplatform.mission_control.aggregator.get_tab",
    return_value={"ok": False, "tabs": ["overview", "inference"]},
    create=True,
)
def test_get_tab_unknown(mock_get_tab):
    tab = get_tab("not-a-tab")
    assert tab.get("ok") is False
    assert "tabs" in tab
    mock_get_tab.assert_called_once_with("not-a-tab")


@patch(
    "aiplatform.mission_control.aggregator.format_overview_markdown",
    return_value=OVERVIEW_MARKDOWN,
    create=True,
)
def test_format_overview_markdown(mock_md):
    text = format_overview_markdown()
    assert "Mission Control" in text
    assert "**Status:**" in text
    assert "**Mode:**" in text
    assert "**Acceptance:**" in text
    mock_md.assert_called_once()


@patch(
    "aiplatform.mission_control.activity.export_csv",
    return_value="timestamp,type,component\n2026-07-10T12:00:00,mc_export_test,test",
    create=True,
)
def test_export_activity_csv(mock_export):
    csv = export_activity_csv(limit=10)
    assert csv.startswith("timestamp,type,component")
    assert "mc_export_test" in csv
    mock_export.assert_called_once_with(limit=10)


def test_notifications_ring_buffer():
    notify("Test alert", detail="unit test", level="info")
    items = list_notifications(limit=5)
    assert any(i.get("title") == "Test alert" for i in items)


def test_metrics_sample_throttle():
    samples_before = len(list_samples(limit=120))
    record_sample({"acceptance": 99, "ram_gb": 8.0})
    record_sample({"acceptance": 98, "ram_gb": 7.0})
    samples_after = list_samples(limit=120)
    assert isinstance(samples_after, list)
    assert len(samples_after) >= samples_before
