"""Tests for Home Assistant Docker autostart."""

from unittest.mock import patch

from jarvis.ha_docker import (
    container_running,
    ensure_homeassistant,
    ha_config_dir,
    should_autostart_ha,
)


def test_should_autostart_default_on(monkeypatch):
    monkeypatch.delenv("JARVIS_HA_AUTOSTART", raising=False)
    monkeypatch.setattr("jarvis.ha_docker.shutil.which", lambda _: "/usr/bin/docker")
    assert should_autostart_ha() is True


def test_should_autostart_respects_off(monkeypatch):
    monkeypatch.setenv("JARVIS_HA_AUTOSTART", "0")
    monkeypatch.setattr("jarvis.ha_docker.shutil.which", lambda _: "/usr/bin/docker")
    assert should_autostart_ha() is False


def test_ha_config_dir_default(monkeypatch):
    monkeypatch.delenv("JARVIS_HA_CONFIG", raising=False)
    assert ha_config_dir().name == "homeassistant"


def test_ensure_skips_when_autostart_off(monkeypatch):
    monkeypatch.setenv("JARVIS_HA_AUTOSTART", "0")
    with patch("jarvis.ha_docker.ha_api_healthy", return_value=False), patch(
        "jarvis.ha_docker.container_running", return_value=False
    ), patch("jarvis.ha_docker.subprocess.run") as run:
        assert ensure_homeassistant() is False
        run.assert_not_called()


def test_ensure_starts_existing_container(monkeypatch):
    monkeypatch.setenv("JARVIS_HA_AUTOSTART", "1")
    with patch("jarvis.ha_docker.ha_api_healthy", return_value=False), patch(
        "jarvis.ha_docker.container_running", return_value=False
    ), patch("jarvis.ha_docker.container_exists", return_value=True), patch(
        "jarvis.ha_docker.subprocess.run"
    ) as run:
        assert ensure_homeassistant() is True
        run.assert_called_once()
        assert run.call_args.args[0][:2] == ["docker", "start"]
