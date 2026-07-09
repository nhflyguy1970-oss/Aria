"""Tests for integration probes and startup."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.workstation.integration_probes import probe_redis, run_probe
from jarvis.workstation.local_config import detect_local_services
from jarvis.workstation.startup import _autostart_ids


def test_autostart_ids_from_env(monkeypatch):
    monkeypatch.setenv("JARVIS_AUTOSTART_SERVICES", "postgres,redis,aria")
    assert _autostart_ids() == ["postgres", "redis", "aria"]


def test_detect_local_services_has_ai_root():
    detected = detect_local_services()
    assert "JARVIS_AUTOSTART_SERVICES" in detected


def test_probe_redis_uses_cli_fallback(monkeypatch):
    monkeypatch.delitem(__import__("sys").modules, "redis", raising=False)
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")
    with patch("shutil.which", return_value="/usr/bin/redis-cli"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "PONG"})()
            result = probe_redis()
    assert result["ok"] is True


@patch(
    "jarvis.workstation.integration_probes.PROBE_MAP",
    {"redis": lambda: {"ok": True, "detail": "ok"}},
)
def test_run_probe_unknown_skips():
    result = run_probe("missing")
    assert result["ok"] is False
