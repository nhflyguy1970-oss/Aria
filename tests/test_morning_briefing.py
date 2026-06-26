"""Morning briefing — weather, tasks, launch gating."""

from datetime import datetime

import pytest

from jarvis.modules.journal import BulletJournal
from jarvis.morning_briefing import (
    briefing_visible,
    build_briefing,
    mark_briefing_shown,
    profile_first_name,
    should_show_launch_briefing,
    time_greeting,
)
from jarvis.router import route
from jarvis.session import SessionContext


@pytest.fixture
def journal(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.modules.journal.JOURNAL_FILE", data_dir / "journal" / "bullet_journal.json")
    monkeypatch.setattr("jarvis.modules.journal.JOURNAL_DIR", data_dir / "journal")
    (data_dir / "journal").mkdir(parents=True, exist_ok=True)
    return BulletJournal(path=data_dir / "journal" / "bullet_journal.json")


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    from jarvis.modules.memory import MemoryStore

    return MemoryStore(path=data_dir / "memory.json")


def test_time_greeting():
    assert time_greeting(when=datetime(2026, 6, 8, 9, 0)) == "Good morning"
    assert time_greeting(when=datetime(2026, 6, 8, 14, 0)) == "Good afternoon"
    assert time_greeting(when=datetime(2026, 6, 8, 19, 0)) == "Good evening"


def test_profile_first_name(store):
    store.add("fact", "User's name is Jeff.", tags=["profile", "name"], namespace="profile")
    assert profile_first_name(store) == "Jeff"


def test_build_briefing_includes_tasks(journal, store, monkeypatch):
    monkeypatch.setattr("jarvis.modules.journal._today", lambda: "2026-06-08")
    monkeypatch.setattr("jarvis.morning_briefing.weather_for_day", lambda day: {
        "date": day,
        "condition": "Clear",
        "high": 72,
        "low": 58,
        "unit": "°F",
        "location": "Charlestown, NH",
        "icon": "☀️",
    })
    journal.daily_add("Team standup", "event", day="2026-06-08")
    journal.daily_add("finish taxes", "task", day="2026-06-08")
    briefing = build_briefing(
        journal=journal,
        memory_store=store,
        day="2026-06-08",
        reference=datetime(2026, 6, 8, 8, 30),
    )
    assert "Good morning" in briefing["salutation"]
    assert "finish taxes" in briefing["markdown"]
    assert "Team standup" in briefing["markdown"]
    assert briefing["open_task_count"] >= 1


def test_launch_briefing_once_per_day(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.morning_briefing._load_chat_settings", lambda: {})
    monkeypatch.setattr("jarvis.morning_briefing._write_chat_settings", lambda data: None)
    assert should_show_launch_briefing(day="2026-06-08") is True
    mark_briefing_shown("2026-06-08")
    monkeypatch.setattr(
        "jarvis.morning_briefing._load_chat_settings",
        lambda: {"morning_briefing": {"last_shown": "2026-06-08"}},
    )
    assert should_show_launch_briefing(day="2026-06-08") is False


def test_briefing_visible_respects_dismiss(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.morning_briefing._load_chat_settings", lambda: {})
    assert briefing_visible(day="2026-06-08") is True
    mark_briefing_shown("2026-06-08")
    monkeypatch.setattr(
        "jarvis.morning_briefing._load_chat_settings",
        lambda: {"morning_briefing": {"last_shown": "2026-06-08"}},
    )
    assert briefing_visible(day="2026-06-08") is False
    assert briefing_visible(force=True, day="2026-06-08") is True


def test_morning_briefing_route():
    intent = route("morning briefing", SessionContext())
    assert intent["action"] == "morning_briefing"


def test_good_morning_routes_to_briefing(monkeypatch):
    monkeypatch.setenv("JARVIS_BRIEFING", "1")
    intent = route("good morning", SessionContext())
    assert intent["action"] == "morning_briefing"
