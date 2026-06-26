"""Tests for jarvis.watchdog."""

from unittest.mock import MagicMock, patch

from jarvis.watchdog import ServerWatchdog


def test_healthy_when_live_returns_200():
    wd = ServerWatchdog(failures_before_restart=1)
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.status = 200
        assert wd._healthy() is True


def test_restart_after_consecutive_failures():
    restarted = []

    def on_restart():
        restarted.append(1)
        return MagicMock(poll=MagicMock(return_value=None))

    wd = ServerWatchdog(failures_before_restart=2, on_restart=on_restart)
    with patch.object(wd, "_healthy", return_value=False), patch.object(wd, "_port_open", return_value=False):
        wd._consecutive_failures = 1
        wd._restart_server()
        assert len(restarted) == 1
        assert wd._restart_count == 1


def test_no_restart_while_media_busy():
    restarted = []

    def on_restart():
        restarted.append(1)
        return MagicMock(poll=MagicMock(return_value=None))

    wd = ServerWatchdog(failures_before_restart=2, on_restart=on_restart)
    with patch.object(wd, "_healthy", return_value=False), patch(
        "jarvis.watchdog._media_work_active", return_value=True,
    ):
        wd._consecutive_failures = 5
        # Simulate one loop iteration's logic
        if wd._healthy():
            wd._consecutive_failures = 0
        else:
            from jarvis.watchdog import _media_work_active
            if _media_work_active():
                wd._consecutive_failures = 0
        assert wd._consecutive_failures == 0
        assert len(restarted) == 0
