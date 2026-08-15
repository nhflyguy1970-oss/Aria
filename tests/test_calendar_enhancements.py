"""Calendar enhancements — time, schedule layer, ICS RRULE, NL, conflicts."""

from __future__ import annotations

from datetime import date, datetime

import pytest


@pytest.fixture
def bj(data_dir, monkeypatch):
    journal_dir = data_dir / "journal"
    journal_dir.mkdir(parents=True, exist_ok=True)
    journal_file = journal_dir / "bullet_journal.json"
    monkeypatch.setattr("jarvis.modules.journal.JOURNAL_DIR", journal_dir)
    monkeypatch.setattr("jarvis.modules.journal.JOURNAL_FILE", journal_file)
    monkeypatch.setattr("jarvis.modules.journal.JOURNAL_PHOTOS_DIR", journal_dir / "photos")
    from jarvis.modules.journal import BulletJournal

    return BulletJournal(path=journal_file)


@pytest.fixture
def planner_db(tmp_path, monkeypatch):
    db = tmp_path / "planner.db"
    monkeypatch.setattr("jarvis.planner_store.DB_PATH", db)
    monkeypatch.setenv("JARVIS_PLANNER", "1")
    import jarvis.planner_store as ps

    ps._init_db()
    return ps


def test_today_iso_local_not_utc():
    from jarvis.calendar_time import today_iso

    assert today_iso() == datetime.now().date().isoformat()


def test_validate_time_hm():
    from jarvis.calendar_time import validate_time_hm

    assert validate_time_hm("3pm") == "15:00"
    assert validate_time_hm("09:30") == "09:30"
    assert validate_time_hm("") is None
    with pytest.raises(ValueError):
        validate_time_hm("25:99")


def test_journal_daily_add_persists_explicit_time(bj):
    from jarvis.calendar_time import today_iso

    day = today_iso()
    b = bj.daily_add("Dentist", "event", day=day, time="14:30")
    assert b["time"] == "14:30"
    assert b["content"] == "Dentist"
    b2 = bj.daily_add("All-day fishing", "event", day=day, time=None)
    assert not b2.get("time")
    events = bj.day_events(day[:7]).get(day) or []
    titles = [e["content"] for e in events]
    assert "Dentist" in titles
    assert "All-day fishing" in titles
    assert any(e["content"] == "All-day fishing" and not e.get("time") for e in events)


def test_schedule_merges_planner_and_journal(bj, planner_db):
    from jarvis.calendar_schedule import schedule_for_day
    from jarvis.calendar_time import today_iso

    day = today_iso()
    bj.daily_add("Journal meetup", "event", day=day, time="10:00")
    bj.daily_add("Untimed trip", "event", day=day, time=None)
    planner_db.add_event("Planner sync", when=day, time_str="11:00")
    detail = schedule_for_day(bj, day)
    sources = {i["source"] for i in detail["items"]}
    assert "journal" in sources
    assert "planner" in sources
    titles = [i["title"] for i in detail["items"]]
    assert "Journal meetup" in titles
    assert "Untimed trip" in titles
    assert "Planner sync" in titles
    untimed = [i for i in detail["items"] if i["title"] == "Untimed trip"][0]
    assert untimed["all_day"] is True


def test_create_update_delete_commitment(bj, planner_db):
    from jarvis.calendar_schedule import (
        create_commitment,
        delete_commitment,
        schedule_for_day,
        update_commitment,
    )
    from jarvis.calendar_time import today_iso

    day = today_iso()
    created = create_commitment(bj, title="Call", day=day, time="16:00", target="journal")
    assert created["target"] == "planner"
    item_id = created["item_id"]
    update_commitment(bj, item_id, title="Call mom", time="16:30")
    detail = schedule_for_day(bj, day)
    assert any(i["title"] == "Call mom" and i["time"] == "16:30" for i in detail["items"])
    assert not bj.day_events(day[:7]).get(day)
    delete_commitment(bj, item_id)
    detail2 = schedule_for_day(bj, day)
    assert not any(i["id"] == item_id for i in detail2["items"])

    pev = create_commitment(bj, title="Ship", day=day, time="09:00", target="planner")
    assert pev["target"] == "planner"


def test_ics_rrule_and_cache(monkeypatch):
    from jarvis import calendar_ics as ics

    ics.clear_ics_cache()
    sample = """BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:Standup
DTSTART:20260727T090000
RRULE:FREQ=DAILY;COUNT=3
END:VEVENT
END:VCALENDAR"""

    monkeypatch.setenv("JARVIS_ICS_URL", "https://example.test/cal.ics")
    monkeypatch.setattr(
        ics,
        "_fetch_raw",
        lambda url, force=False: (sample, {"from_cache": False}),
    )
    result = ics.fetch_events_for_range(date(2026, 7, 27), date(2026, 7, 31))
    days = sorted((result.get("events") or {}).keys())
    assert days == ["2026-07-27", "2026-07-28", "2026-07-29"]
    assert result["events"]["2026-07-27"][0]["time"] == "09:00"


def test_nl_and_conflicts(bj, planner_db):
    from jarvis.calendar_schedule import create_commitment
    from jarvis.calendar_services import detect_conflicts, parse_natural_schedule
    from jarvis.calendar_time import today_iso

    parsed = parse_natural_schedule("Lunch tomorrow")
    assert parsed["ok"]
    assert parsed["proposal"]["time"] == "12:00"
    assert parsed["proposal"]["requires_confirmation"] is True

    day = today_iso()
    create_commitment(bj, title="A", day=day, time="10:00")
    create_commitment(bj, title="B", day=day, time="10:15")
    conflicts = detect_conflicts(bj, day)
    assert conflicts["conflicts"]


def test_week_agenda_timeline(bj, planner_db):
    from jarvis.calendar_tab import agenda_overview, timeline_overview, week_overview
    from jarvis.calendar_time import today_iso

    day = today_iso()
    bj.daily_add("X", "event", day=day, time="13:00")
    week = week_overview(bj, day)
    assert week["ok"] and len(week["dates"]) == 7
    agenda = agenda_overview(bj, days=3, start=day)
    assert agenda["ok"]
    timeline = timeline_overview(bj, day)
    assert timeline["ok"]
    assert timeline["view"] == "timeline"


def test_work_schedule_still_works(data_dir, monkeypatch):
    from jarvis.calendar_store import load_work_schedule, save_work_schedule, work_blocks_for_day

    path = data_dir / "calendar_work_schedule.json"
    monkeypatch.setattr("jarvis.calendar_store.SCHEDULE_FILE", path)
    save_work_schedule(
        {"enabled": True, "days": {"mon": [{"start": "08:00", "end": "16:00", "label": "Office"}]}}
    )
    assert load_work_schedule()["days"]["mon"][0]["label"] == "Office"
    blocks = work_blocks_for_day(date(2026, 7, 27))
    assert blocks[0]["start"] == "08:00"


def test_legacy_ics_helper():
    from jarvis.calendar_ics import _parse_ics_events

    text = "BEGIN:VEVENT\nSUMMARY:Team standup\nDTSTART:20260621T090000\nEND:VEVENT\n"
    events = _parse_ics_events(text, date(2026, 6, 21))
    assert events[0]["summary"] == "Team standup"
    assert events[0]["time"] == "09:00"


def test_ha_mode_optional(monkeypatch):
    from jarvis.calendar_services import ha_calendar_mode

    monkeypatch.setattr("jarvis.calendar_store.get_pref", lambda *a, **k: False)
    monkeypatch.setattr("jarvis.calendar_store.set_pref", lambda *a, **k: None)
    out = ha_calendar_mode("meeting")
    assert out["ok"]
    assert out["home_assistant"].get("skipped")


def test_meeting_prep_no_meeting(bj):
    from jarvis.calendar_services import meeting_prep

    out = meeting_prep(bj, assistant=None)
    assert out.get("ok") is False or "message" in out


def test_terminology_boundaries():
    from jarvis.calendar_terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY

    assert TERMINOLOGY["product"] == "Calendar"
    assert "schedule_abstraction" in BOUNDARIES["owns"]
    assert "tasks" in BOUNDARIES["does_not_own"]
    assert "notifications_delivery" in BOUNDARIES["does_not_own"]
    assert MENTAL_MODEL["ics"]


def test_bridges_dashboard_and_search(bj, planner_db):
    from jarvis.calendar_bridges import dashboard_summary, mission_status, product_status, search_hits
    from jarvis.calendar_schedule import create_commitment
    from jarvis.calendar_time import today_iso

    create_commitment(bj, title="Bridge meet", day=today_iso(), time="15:00")
    dash = dashboard_summary(bj)
    assert dash["ok"]
    assert any(i["title"] == "Bridge meet" for i in dash["items"])
    hits = search_hits("Bridge", journal=bj)
    assert any("Bridge" in (h.get("title") or "") for h in hits)
    assert mission_status()["ok"]
    assert product_status()["product"] == "Calendar"


def test_calendar_prefs_not_planner(tmp_path, monkeypatch):
    from jarvis import calendar_store as cs

    monkeypatch.setattr(cs, "PREFS_FILE", tmp_path / "calendar_prefs.json")
    cs.set_pref("ha_calendar_modes", False)
    assert cs.get_pref("ha_calendar_modes") is False
