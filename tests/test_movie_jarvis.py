"""Tests for Movie Jarvis completion features."""

from unittest.mock import patch


def test_good_morning_routes_to_briefing(monkeypatch):
    monkeypatch.setenv("JARVIS_BRIEFING", "1")
    from jarvis.router import route
    from jarvis.session import SessionContext

    assert route("good morning", SessionContext())["action"] == "morning_briefing"


def test_document_search_route():
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("search my documents warranty coverage", SessionContext())
    assert intent["action"] == "document_search"


def test_requires_jarvis_restart():
    from jarvis.upgrade_wizard import requires_jarvis_restart

    assert requires_jarvis_restart([{"path": "jarvis/gui/static/app.js"}]) is True
    assert requires_jarvis_restart([{"path": "tests/test_foo.py"}]) is False


def test_run_whitelisted_script_rejects_paths(data_dir, monkeypatch):
    from jarvis.remote_control import SCRIPTS_DIR, run_whitelisted_script

    monkeypatch.setattr("jarvis.remote_control.SCRIPTS_DIR", data_dir / "scripts")
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    ok, msg = run_whitelisted_script("../etc/passwd")
    assert ok is False
    assert "simple" in msg.lower() or "path" in msg.lower()


def test_environment_snapshot():
    from jarvis.environment import snapshot

    snap = snapshot(include_resources=False)
    assert "profile" in snap
    assert "disk_free_gb" in snap


def test_ics_parse_events():
    from datetime import date

    from jarvis.calendar_ics import _parse_ics_events

    ics = """BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:Team standup
DTSTART:20260608T093000
END:VEVENT
END:VCALENDAR"""
    events = _parse_ics_events(ics, date(2026, 6, 8))
    assert len(events) == 1
    assert events[0]["summary"] == "Team standup"
    assert events[0]["time"] == "09:30"


def test_enqueue_fix_tests(monkeypatch):
    monkeypatch.setenv("JARVIS_BRIEFING", "1")
    from jarvis.coding_jobs import submit_fix_tests

    class FakeAssistant:
        def _coding_fix_tests(self, params, message):
            return {"ok": True, "message": "done"}

    job_id = submit_fix_tests(FakeAssistant(), {"path": "foo.py"}, "debug until tests pass")
    assert len(job_id) == 12
