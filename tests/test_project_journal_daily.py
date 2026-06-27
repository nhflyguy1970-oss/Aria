"""Daily auto-update for project journals."""

from datetime import datetime

import pytest

from jarvis.project_journal import ProjectJournal
from jarvis.project_journal_daily import (
    _already_ran,
    _mark_ran,
    discover_project_slugs,
    gather_daily_context,
    run_scheduled_daily,
    update_project_journal_daily,
)


@pytest.fixture
def daily_env(data_dir, monkeypatch):
    projects = data_dir / "journal" / "projects"
    projects.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.project_journal.PROJECTS_DIR", projects)
    monkeypatch.setattr("jarvis.project_journal.INDEX_FILE", projects / "index.json")
    monkeypatch.setattr("jarvis.project_journal_daily.PROJECTS_DIR", projects)
    monkeypatch.setattr("jarvis.project_journal_daily.STATE_FILE", projects / "_daily_state.json")
    monkeypatch.setenv("JARVIS_PROJECT_JOURNAL_PROJECTS", "aria")
    monkeypatch.setenv("JARVIS_PROJECT_JOURNAL_DAILY", "1")
    return projects


def test_discover_project_slugs(daily_env):
    ProjectJournal("aria").ensure(title="ARIA")
    slugs = discover_project_slugs()
    assert "aria" in slugs


def test_gather_daily_context(daily_env):
    ctx = gather_daily_context("aria", "2026-06-17")
    assert "Project: aria" in ctx
    assert "2026-06-17" in ctx


def test_update_morning_rule_based(daily_env, monkeypatch):
    monkeypatch.setattr("jarvis.project_journal_daily._llm_summary", lambda *a, **k: None)
    result = update_project_journal_daily("aria", day="2026-06-17", phase="morning", force=True)
    assert result["ok"]
    assert result["bullets"]
    journal = ProjectJournal("aria")
    page = journal.daily_get("2026-06-17")
    assert page.get("auto", {}).get("morning", {}).get("bullets")
    assert _already_ran("aria", "2026-06-17", "morning")


def test_skip_without_force(daily_env, monkeypatch):
    monkeypatch.setattr("jarvis.project_journal_daily._llm_summary", lambda *a, **k: None)
    update_project_journal_daily("aria", day="2026-06-17", phase="morning", force=True)
    again = update_project_journal_daily("aria", day="2026-06-17", phase="morning", force=False)
    assert again.get("skipped")


def test_run_scheduled_at_morning_hour(daily_env, monkeypatch):
    monkeypatch.setattr("jarvis.project_journal_daily._llm_summary", lambda *a, **k: None)
    monkeypatch.setenv("JARVIS_PROJECT_JOURNAL_MORNING_HOUR", "9")
    monkeypatch.setenv("JARVIS_PROJECT_JOURNAL_EVENING_HOUR", "22")
    now = datetime(2026, 6, 17, 9, 5)
    results = run_scheduled_daily(now)
    assert any(r.get("slug") == "aria" and r.get("phase") == "morning" for r in results)


def test_format_daily_shows_auto(daily_env, monkeypatch):
    monkeypatch.setattr("jarvis.project_journal_daily._llm_summary", lambda *a, **k: None)
    update_project_journal_daily("aria", day="2026-06-17", phase="morning", force=True)
    text = ProjectJournal("aria").format_daily("2026-06-17")
    assert "Morning" in text
