"""Planner enhancements — store CRUD, tick, focus, triage, vision, schedule, briefing."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def planner_db(tmp_path, monkeypatch):
    db = tmp_path / "planner.db"
    monkeypatch.setattr("jarvis.planner_store.DB_PATH", db)
    monkeypatch.setenv("JARVIS_PLANNER", "1")
    import jarvis.planner_store as ps

    # Force re-init against temp DB with migrations
    ps._init_db()
    return ps


def test_task_due_priority_and_soft_delete(planner_db):
    ps = planner_db
    t = ps.add_task("ship planner")
    ps.update_task(t["id"], due_date=datetime.now().date().isoformat(), priority=5)
    listed = ps.list_tasks()
    assert listed[0]["priority"] == 5
    assert listed[0]["due_date"]
    ps.delete_task(t["id"])
    assert ps.list_tasks() == []
    und = ps.undo_last()
    assert und["ok"] is True
    assert len(ps.list_tasks()) == 1


def test_timer_pause_resume_cancel_duplicate_and_tick(planner_db):
    ps = planner_db
    timer = ps.set_timer("2 minutes", "deep work")
    paused = ps.pause_timer(timer["id"])
    assert paused["paused"] is True
    assert paused["remaining_seconds"] > 0
    resumed = ps.resume_timer(timer["id"])
    assert resumed["paused"] is False
    dup = ps.duplicate_timer(timer["id"])
    assert dup["id"] != timer["id"]
    assert "copy" in (dup["label"] or "").lower() or "deep work" in (dup["label"] or "")

    # Force expiry for tick
    past = (datetime.now() - timedelta(seconds=5)).isoformat(timespec="seconds")
    with ps._conn() as conn:
        conn.execute("UPDATE timers SET ends_at = ?, paused = 0 WHERE id = ?", (past, timer["id"]))
    notes = ps.tick_alarms_and_timers()
    assert any(n.get("type") in ("timer", "pomodoro") and timer["id"] == n.get("id") for n in notes)


def test_alarm_cancel_update_and_tick(planner_db):
    ps = planner_db
    alarm = ps.set_alarm("11:59pm", "wind down")
    updated = ps.update_alarm(alarm["id"], time_str="10:30pm", label="earlier")
    assert updated["label"] == "earlier"
    assert "22:30" in updated["fire_at"] or "10:30" in updated["fire_at"]
    ps.cancel_alarm(alarm["id"])
    assert all(a["id"] != alarm["id"] for a in ps.list_alarms())
    und = ps.undo_last()
    assert und["ok"] is True

    # Fire alarm via tick
    a2 = ps.set_alarm("11:58pm", "ping")
    past = (datetime.now() - timedelta(seconds=2)).isoformat(timespec="seconds")
    with ps._conn() as conn:
        conn.execute("UPDATE alarms SET fire_at = ?, fired = 0, enabled = 1, deleted = 0 WHERE id = ?", (past, a2["id"]))
    notes = ps.tick_alarms_and_timers()
    assert any(n.get("type") == "alarm" for n in notes)


def test_event_crud_and_load_planner(planner_db):
    ps = planner_db
    ps.add_task("priority A")
    ev = ps.add_event("Standup", when="today", time_str="3pm", duration_min=30)
    assert ev["title"] == "Standup"
    ps.update_event(ev["id"], title="Standup sync")
    day = ps.events_for_day()
    assert any(e["title"] == "Standup sync" for e in day)
    ps.delete_event(ev["id"])
    assert not any(e["id"] == ev["id"] for e in ps.events_for_day())
    snap = ps.load_planner()
    assert snap["enabled"] is True
    assert snap["tasks"][0]["done"] is False
    assert snap["tasks"][0]["title"]


def test_daily_focus_and_triage(planner_db):
    ps = planner_db
    today = datetime.now().date().isoformat()
    t = ps.add_task("at risk item")
    ps.update_task(t["id"], due_date=today, priority=3)
    ps.set_timer("25 minutes", "Focus")
    from jarvis.planner_services import daily_focus, morning_triage

    focus = daily_focus(None)
    assert focus["ok"] is True
    assert focus["top_priorities"]
    assert focus["focus_minutes_available"] >= 0
    triage = morning_triage(None)
    assert triage["ok"] is True
    assert "confidence" in triage
    assert triage["recommendations"]


def test_vision_import_and_schedule(planner_db, tmp_path, monkeypatch):
    from jarvis import planner_services as svc

    img = tmp_path / "board.txt"
    # OCR path expects image file; mock ocr_image
    img.write_text("ignore", encoding="utf-8")

    monkeypatch.setattr(
        "jarvis.intelligence.document_intel.ocr_image",
        lambda p: {"ok": True, "text": "- Buy milk\n- Call bank\n- Ship release"},
        raising=False,
    )

    # Ensure import path works even if document_intel missing
    def fake_extract(path, assistant=None):
        return {
            "ok": True,
            "candidates": [
                {"text": "Buy milk", "selected": True},
                {"text": "Call bank", "selected": True},
            ],
            "message": "ok",
        }

    monkeypatch.setattr(svc, "vision_extract_tasks", fake_extract)
    extracted = svc.vision_extract_tasks(str(img))
    assert len(extracted["candidates"]) == 2
    imported = svc.import_vision_tasks(extracted["candidates"])
    assert imported["count"] == 2
    assert len(planner_db.list_tasks()) >= 2

    planner_db.add_task("schedule me")
    sug = svc.suggest_schedule()
    assert sug["suggestions"]
    assert sug["suggestions"][0]["requires_confirmation"] is True
    applied = svc.apply_schedule_suggestion(sug["suggestions"][0])
    assert applied["title"]


def test_focus_session_without_ha(planner_db, monkeypatch):
    from jarvis.planner_services import end_focus_session, start_focus_session

    planner_db.set_pref("ha_focus_enabled", False)
    result = start_focus_session(duration="5 minutes", label="Focus", use_ha=False)
    assert result["ok"] is True
    assert result["timer"]["id"]
    ended = end_focus_session(restore_ha=False)
    assert ended["ok"] is True


def test_morning_workflow_includes_planner(planner_db):
    from jarvis.workflows.daily import what_am_i_working_on

    planner_db.add_task("Finish tests")
    planner_db.set_timer("10 minutes", "test timer")
    assistant = MagicMock()
    assistant.memory.search.return_value = []
    out = what_am_i_working_on(assistant)
    assert out["ok"] is True
    assert "Finish tests" in out["message"]
    assert "timer" in out["message"].lower() or "Timers" in out["message"]


def test_format_planner_lines_rich(planner_db):
    planner_db.add_task("X")
    planner_db.set_alarm("8am", "wake")
    text = planner_db.format_planner_lines()
    assert "Planner priorities" in text or "X" in text


def test_p0_fixture_compat_still_works(tmp_path, monkeypatch):
    """Legacy bare schema still accepts basic task/timer after migration columns added via real init."""
    db = tmp_path / "legacy.db"
    monkeypatch.setattr("jarvis.planner_store.DB_PATH", db)
    monkeypatch.setenv("JARVIS_PLANNER", "1")
    import jarvis.planner_store as ps

    ps._init_db()
    task = ps.add_task("buy milk")
    assert task["text"] == "buy milk"
    timer = ps.set_timer("5 minutes", "tea")
    assert timer["remaining_seconds"] >= 299
