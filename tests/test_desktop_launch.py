"""Tests for desktop launch helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_api_responsive_uses_live_or_health():
    from jarvis.application.desktop_launch import api_responsive

    with patch("jarvis.services._http_ok", side_effect=[False, True]):
        assert api_responsive() is True


def test_start_aria_server_skips_when_already_healthy():
    from jarvis.application import desktop_launch as dl

    with patch.object(dl, "api_responsive", return_value=True):
        assert dl.start_aria_server() is True


def test_desktop_display_available_respects_headless():
    from jarvis.application.desktop_launch import desktop_display_available

    with patch.dict("os.environ", {"JARVIS_HEADLESS": "1", "DISPLAY": ":0"}, clear=False):
        assert desktop_display_available() is False


@patch("jarvis.application.desktop_launch.subprocess.run")
def test_open_desktop_gui_invokes_launch_script(mock_run):
    from jarvis.application.desktop_launch import open_desktop_gui

    mock_run.return_value = MagicMock(returncode=0)
    assert open_desktop_gui(blocking=True) == 0
    args = mock_run.call_args[0][0]
    assert args[0] == "bash"
    assert args[1].endswith("launch-jarvis.sh")
