"""Regression: UI-connected product endpoints that previously 404'd."""

from __future__ import annotations


def test_disconnected_ui_routes_are_registered():
    from jarvis.gui.server import app

    paths = {getattr(route, "path", None) for route in app.routes}
    for required in (
        "/api/audio/stop",
        "/api/audio/output-sink",
        "/api/browser/install-playwright",
        "/api/journal/projects",
        "/api/journal/projects/{slug}",
        "/api/journal/projects/{slug}/log",
        "/api/journal/projects/{slug}/learn",
    ):
        assert required in paths, f"missing route {required}"


def test_stop_playback_and_clear_tts_queue_do_not_raise():
    from jarvis.audio_device import stop_playback
    from jarvis.tts_playback_queue import clear_tts_queue

    stop_playback()
    clear_tts_queue()


def test_journal_projects_backend(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.project_journal.JOURNAL_DIR", data_dir / "journal")
    monkeypatch.setattr("jarvis.project_journal.PROJECTS_DIR", data_dir / "journal" / "projects")
    monkeypatch.setattr(
        "jarvis.project_journal.INDEX_FILE", data_dir / "journal" / "projects" / "index.json"
    )
    from jarvis.project_journal import ProjectJournal, list_projects

    store = ProjectJournal("aria-test")
    store.ensure(title="Aria Test")
    store.daily_add("Ship product certification", bullet_type="task")
    projects = list_projects()
    assert any(p.get("slug") == "aria-test" for p in projects)
    page = store.daily_get()
    assert any("Ship product certification" in (b.get("content") or "") for b in page.get("bullets") or [])
