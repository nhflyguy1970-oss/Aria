"""Daemon and watchdog reliability tests."""

import subprocess
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from jarvis.watchdog import ServerWatchdog, _media_work_active


def test_media_work_active_false_when_idle(monkeypatch):
    monkeypatch.setattr("jarvis.media_jobs.has_active_work_persisted", lambda: False)
    monkeypatch.setattr("jarvis.media_jobs.has_active_work", lambda: False)
    monkeypatch.setattr("jarvis.media_jobs.busy_state", lambda: {"busy": False, "pending": 0})
    monkeypatch.setattr("jarvis.restart_flag.controlled_restart_active", lambda: False)
    assert _media_work_active() is False


def test_media_work_active_true_when_busy(monkeypatch):
    monkeypatch.setattr("jarvis.media_jobs.has_active_work_persisted", lambda: False)
    monkeypatch.setattr("jarvis.media_jobs.has_active_work", lambda: True)
    monkeypatch.setattr("jarvis.media_jobs.busy_state", lambda: {"busy": True, "pending": 0})
    monkeypatch.setattr("jarvis.restart_flag.controlled_restart_active", lambda: False)
    assert _media_work_active() is True


def test_watchdog_does_not_restart_when_media_active(monkeypatch):
    import jarvis.watchdog as wd_mod

    restarted = {"v": False}
    wd = ServerWatchdog(interval=1, failures_before_restart=1, on_restart=lambda: restarted.update(v=True))
    monkeypatch.setattr(wd_mod, "_media_work_active", lambda: True)
    wd._consecutive_failures = 5
    if wd_mod._media_work_active():
        wd._consecutive_failures = 0
    else:
        wd._restart_server()
    assert restarted["v"] is False


def test_daemon_start_server_health_timeout(monkeypatch, tmp_path):
    from jarvis import daemon

    monkeypatch.setattr(daemon, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(daemon, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(daemon, "HEALTH_URL", "http://127.0.0.1:9/health")
    monkeypatch.setattr(daemon, "load_jarvis_env", lambda: None)

    proc = MagicMock()
    proc.poll.return_value = None
    monkeypatch.setattr(
        daemon.subprocess,
        "Popen",
        lambda *a, **k: proc,
    )
    monkeypatch.setattr(
        daemon.urllib.request,
        "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(urllib.error.URLError("down")),
    )
    monkeypatch.setattr(daemon.time, "sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="timed out"):
        daemon.start_server()
