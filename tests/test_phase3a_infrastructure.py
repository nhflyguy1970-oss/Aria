"""Tier 3A — shared Mission Control / Focus infrastructure (disposable DATA_DIR only)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from jarvis.mission_control import (
    collect_mission_control,
    health_summary,
    invalidate_mission_control_cache,
)


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
    "applications": [],
    "inference": {"current_model": "llama3", "provider": "ollama"},
    "memory": {"provider": "platform", "entry_count": 0},
    "knowledge": {"retrieval": "platform", "documents": 0},
    "databases": [],
    "hardware": {"gpu_name": "RTX 4090"},
    "jobs": {"active_count": 0},
    "activity": {"events": []},
    "performance": {"run_count": 0},
    "recovery": {"health": {"ok": True}},
    "notifications": [],
    "settings": {"mission_control_port": "8780"},
}


@pytest.fixture(autouse=True)
def _clear_mc_cache():
    invalidate_mission_control_cache()
    yield
    invalidate_mission_control_cache()


@patch("aiplatform.mission_control.aggregator.collect_mission_control", return_value=FULL_MC, create=True)
def test_lite_enrich_skips_product_panel_fanout(mock_collect):
    with patch("jarvis.mission_control_ops.enrich._attach_product_panels") as attach:
        snap = collect_mission_control(record_metrics=False, enrich="lite", force=True)
        assert snap.get("enrich_mode") == "lite"
        assert snap.get("health_brief")
        attach.assert_not_called()
        mock_collect.assert_called_once()


@patch("aiplatform.mission_control.aggregator.collect_mission_control", return_value=FULL_MC, create=True)
def test_health_summary_reuses_lite_cache(mock_collect):
    a = health_summary(force=True)
    b = health_summary(force=False)
    assert "overall" in a and "overall" in b
    # One platform collect for both (shared raw + lite cache)
    assert mock_collect.call_count == 1


@patch("aiplatform.mission_control.aggregator.collect_mission_control", return_value=FULL_MC, create=True)
def test_automation_gate_delegates_to_health_summary(mock_collect):
    from jarvis.mission_control_ops.automation_gate import get_infrastructure_health

    h = get_infrastructure_health(force=True)
    assert h.get("source") == "mission_control"
    assert mock_collect.call_count == 1


def test_daily_focus_local_briefing_no_acm(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config
    import jarvis.planner_store as planner_store

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(planner_store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(planner_store, "DB_PATH", tmp_path / "planner.db")

    from jarvis.planner_services import daily_focus
    from jarvis.planner_store import add_task

    add_task("tier3a disposable focus task")

    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        raise AssertionError("what_am_i_working_on must not run on Focus poll")

    with patch("jarvis.workflows.daily.what_am_i_working_on", boom):
        out = daily_focus(assistant=object())
    assert out.get("ok") is True
    assert called["n"] == 0
    assert "tier3a disposable focus task" in (out.get("morning_briefing") or "")
    # Live production planner must remain untouched
    assert planner_store.DB_PATH == tmp_path / "planner.db"


def test_presence_hash_map_not_home_automation():
    """Static guard: workspace hash map must not route #presence → home_automation (SYS-F08)."""
    from pathlib import Path

    text = Path(__file__).resolve().parents[1].joinpath("jarvis/gui/static/workspace/workspace.js").read_text(
        encoding="utf-8"
    )
    assert 'presence: "home_automation"' not in text
    assert 'presence: "presence"' in text
    assert 'dashboard: "home"' in text
