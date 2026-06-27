"""Calendar store and tab tests."""

from datetime import date

import pytest

from jarvis.calendar_store import load_work_schedule, save_work_schedule, work_blocks_for_day


def test_work_schedule_roundtrip(data_dir, monkeypatch):
    path = data_dir / "calendar_work_schedule.json"
    monkeypatch.setattr("jarvis.calendar_store.SCHEDULE_FILE", path)
    saved = save_work_schedule({
        "enabled": True,
        "days": {
            "mon": [{"start": "08:00", "end": "16:00", "label": "Office"}],
            "sat": [],
        },
    })
    assert saved["days"]["mon"][0]["label"] == "Office"
    loaded = load_work_schedule()
    assert loaded["days"]["mon"][0]["start"] == "08:00"


def test_work_blocks_for_day(data_dir, monkeypatch):
    path = data_dir / "calendar_work_schedule.json"
    monkeypatch.setattr("jarvis.calendar_store.SCHEDULE_FILE", path)
    save_work_schedule({
        "enabled": True,
        "days": {"fri": [{"start": "09:00", "end": "17:00", "label": "Work"}]},
    })
    blocks = work_blocks_for_day(date(2026, 6, 19))
    assert len(blocks) == 1
    assert blocks[0]["label"] == "Work"


def test_fetch_events_for_month_parses():
    from jarvis.calendar_ics import _parse_ics_event_block

    chunk = "SUMMARY:Team standup\nDTSTART:20260621T090000\n"
    d, summary, time_str = _parse_ics_event_block(chunk)
    assert d == date(2026, 6, 21)
    assert summary == "Team standup"
    assert time_str == "09:00"
