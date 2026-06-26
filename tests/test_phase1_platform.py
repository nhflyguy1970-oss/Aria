"""Job center, debug bundle, and shared assistant tests."""

import pytest


def test_jobs_center_snapshot_empty(monkeypatch):
    monkeypatch.setattr(
        "jarvis.media_jobs.busy_state",
        lambda: {"busy": False, "pending": 0, "label": ""},
    )
    monkeypatch.setattr(
        "jarvis.media_jobs.job_stats",
        lambda: {"busy": False, "pending": 0, "completed": 0},
    )
    monkeypatch.setattr("jarvis.media_jobs.list_recent", lambda n=10: [])
    monkeypatch.setattr(
        "jarvis.coding_jobs.job_stats",
        lambda: {"busy": False, "pending": 0, "completed": 0},
    )
    monkeypatch.setattr("jarvis.coding_jobs.list_recent", lambda n=10: [])

    from jarvis.jobs_center import snapshot

    data = snapshot(recent_limit=5)
    assert data["ok"] is True
    assert isinstance(data["recent"], list)
    assert "media" in data and "coding" in data


def test_debug_bundle_collect(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_APP_VERSION", "3.1.0-test")
    monkeypatch.setenv("JARVIS_UI_VERSION", "5.13.0")
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "jarvis.log").write_text("hello jarvis log", encoding="utf-8")
    monkeypatch.setattr("jarvis.debug_bundle.LOG_DIR", log_dir)
    monkeypatch.setattr(
        "jarvis.metrics.snapshot",
        lambda: {"uptime_sec": 10, "watchdog_restarts": 0},
    )
    monkeypatch.setattr(
        "jarvis.environment.snapshot",
        lambda **kw: {"profile": "work", "disk_free_gb": 100},
    )
    monkeypatch.setattr(
        "jarvis.jobs_center.snapshot",
        lambda **kw: {"any_busy": False, "recent": []},
    )

    from jarvis.debug_bundle import collect

    bundle = collect(log_bytes=100)
    assert bundle["ok"] is True
    assert "hello jarvis" in bundle["logs"]["jarvis"]
    assert "ARIA debug bundle" in bundle["text"]


def test_shared_assistant_instance(assistant):
    from jarvis.assistant_instance import clear_assistant, get_assistant, set_assistant

    clear_assistant()
    set_assistant(assistant)
    assert get_assistant() is assistant


def test_background_job_enqueue(chat_app, monkeypatch):
    submitted = {}

    def fake_submit(assistant, action, params, message):
        submitted["action"] = action
        return "job-bg-1"

    monkeypatch.setattr("jarvis.background_jobs.submit_action", fake_submit)
    result = chat_app.assistant._enqueue_background(
        "learn_about",
        {"topic": "Python"},
        "learn about Python",
    )
    assert result["ok"] is True
    assert result["job_id"] == "job-bg-1"
    assert submitted["action"] == "learn_about"


def test_api_jobs_route(chat_app):
    res = chat_app.get("/api/jobs")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_api_debug_bundle_route(chat_app, monkeypatch, tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    monkeypatch.setattr("jarvis.debug_bundle.LOG_DIR", log_dir)
    res = chat_app.get("/api/debug/bundle")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "text" in res.json()
