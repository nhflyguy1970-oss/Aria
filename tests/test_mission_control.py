"""Mission Control — operational console source of truth."""

from __future__ import annotations

from jarvis.mission_control import (
    collect_mission_control,
    export_activity_csv,
    format_overview_markdown,
    get_tab,
)
from jarvis.platform_metrics import list_samples, record_sample
from jarvis.platform_notifications import list_notifications, notify
from jarvis.workstation_activity import record_event


def test_collect_mission_control_shape():
    data = collect_mission_control(record_metrics=False)
    assert data.get("ok") is True
    assert data.get("title") == "AI Platform Mission Control"
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


def test_applications_include_aria_profiles():
    data = collect_mission_control(record_metrics=False)
    apps = data.get("applications") or []
    ids = {a.get("id") for a in apps}
    assert "aria" in ids
    assert "aria-uncensored" in ids


def test_get_tab_overview():
    tab = get_tab("overview")
    assert tab.get("ok") is True
    assert tab.get("tab") == "overview"
    assert "platform_status" in (tab.get("data") or {})


def test_get_tab_unknown():
    tab = get_tab("not-a-tab")
    assert tab.get("ok") is False
    assert "tabs" in tab


def test_format_overview_markdown():
    text = format_overview_markdown()
    assert "Mission Control" in text
    assert "**Status:**" in text
    assert "**Mode:**" in text
    assert "**Acceptance:**" in text


def test_export_activity_csv():
    record_event("mc_export_test", component="test", detail="csv row")
    csv = export_activity_csv(limit=10)
    assert csv.startswith("timestamp,type,component")
    assert "mc_export_test" in csv


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
