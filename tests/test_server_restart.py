"""Server restart must work without the desktop tray."""

from __future__ import annotations

from unittest.mock import patch


def test_request_restart_self_mode_without_tray(monkeypatch, tmp_path):
    monkeypatch.delenv("JARVIS_LAUNCH_OWNER", raising=False)
    monkeypatch.delenv("JARVIS_SERVICES_MANAGED", raising=False)
    monkeypatch.setattr("jarvis.server_restart.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.server_restart.PROJECT_ROOT", tmp_path)

    with (
        patch("jarvis.server_restart._spawn_successor_serve", return_value=True) as spawn,
        patch("jarvis.server_restart._schedule_self_exit") as exit_fn,
        patch("jarvis.restart_audit.log_restart_event"),
    ):
        from jarvis.server_restart import request_restart

        result = request_restart(source="test", detail="no-tray")

    assert result["ok"] is True
    assert result.get("mode") == "self"
    spawn.assert_called_once()
    exit_fn.assert_called_once()


def test_request_restart_tray_mode_signals_parent(monkeypatch, tmp_path):
    monkeypatch.delenv("JARVIS_LAUNCH_OWNER", raising=False)
    monkeypatch.setenv("JARVIS_SERVICES_MANAGED", "1")
    monkeypatch.setattr("jarvis.server_restart.DATA_DIR", tmp_path)

    with (
        patch("jarvis.server_restart._signal_tray_restart", return_value=True) as sig,
        patch("jarvis.restart_audit.log_restart_event"),
    ):
        from jarvis.server_restart import request_restart

        result = request_restart(source="test", detail="tray")

    assert result["ok"] is True
    assert result.get("mode") == "tray"
    sig.assert_called_once()


def test_request_restart_systemd_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_LAUNCH_OWNER", "systemd")
    monkeypatch.delenv("JARVIS_SERVICES_MANAGED", raising=False)
    monkeypatch.setattr("jarvis.server_restart.DATA_DIR", tmp_path)

    with (
        patch("jarvis.server_restart._schedule_systemd_restart") as sysd,
        patch("jarvis.server_restart._spawn_successor_serve") as spawn,
        patch("jarvis.restart_audit.log_restart_event"),
    ):
        from jarvis.server_restart import request_restart

        result = request_restart(source="test", detail="systemd")

    assert result["ok"] is True
    assert result.get("mode") == "systemd"
    sysd.assert_called_once()
    spawn.assert_not_called()


def test_request_restart_no_longer_requires_tray_message(monkeypatch, tmp_path):
    """Regression: previously returned tray-launcher error when unmanaged."""
    monkeypatch.delenv("JARVIS_SERVICES_MANAGED", raising=False)
    monkeypatch.setattr("jarvis.server_restart.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.server_restart.PROJECT_ROOT", tmp_path)

    with (
        patch("jarvis.server_restart._spawn_successor_serve", return_value=True),
        patch("jarvis.server_restart._schedule_self_exit"),
        patch("jarvis.restart_audit.log_restart_event"),
    ):
        from jarvis.server_restart import request_restart

        result = request_restart()

    assert result["ok"] is True
    assert "tray launcher" not in str(result.get("message", "")).lower()
