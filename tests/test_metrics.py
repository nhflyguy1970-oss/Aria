"""Tests for metrics snapshot."""

from jarvis.metrics import note_watchdog_restart, snapshot


def test_snapshot_includes_queues():
    note_watchdog_restart()
    data = snapshot()
    assert data["ok"] is True
    assert "uptime_sec" in data
    assert data["watchdog_restarts"] >= 1
    assert "media" in data
    assert "coding" in data
