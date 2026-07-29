"""Home Assistant Docker helper tests."""

from __future__ import annotations

from unittest.mock import patch


def test_should_autostart_ha_default_off(monkeypatch):
    from jarvis.ha_docker import should_autostart_ha

    monkeypatch.delenv("JARVIS_HA_AUTOSTART", raising=False)
    with patch("jarvis.ha_docker.shutil.which", return_value="/usr/bin/docker"):
        with patch("jarvis.ha_docker.load_jarvis_env"):
            assert should_autostart_ha() is False


def test_should_autostart_ha_on_when_enabled(monkeypatch):
    from jarvis.ha_docker import should_autostart_ha

    monkeypatch.setenv("JARVIS_HA_AUTOSTART", "1")
    with patch("jarvis.ha_docker.shutil.which", return_value="/usr/bin/docker"):
        with patch("jarvis.ha_docker.load_jarvis_env"):
            assert should_autostart_ha() is True


def test_should_autostart_ha_requires_docker(monkeypatch):
    from jarvis.ha_docker import should_autostart_ha

    monkeypatch.setenv("JARVIS_HA_AUTOSTART", "1")
    with patch("jarvis.ha_docker.shutil.which", return_value=None):
        with patch("jarvis.ha_docker.load_jarvis_env"):
            assert should_autostart_ha() is False


def test_autostart_matches_service_policy(monkeypatch):
    from jarvis import ha_docker
    from jarvis import service_policy

    monkeypatch.setenv("JARVIS_HA_AUTOSTART", "0")
    with patch.object(ha_docker, "load_jarvis_env"):
        with patch.object(ha_docker.shutil, "which", return_value="/usr/bin/docker"):
            assert ha_docker.should_autostart_ha() == service_policy.autostart_ha()
