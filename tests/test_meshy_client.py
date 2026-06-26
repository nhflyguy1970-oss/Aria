"""Tests for Meshy client helpers."""

from jarvis.meshy_client import meshy_api_key, meshy_available


def test_meshy_available_without_key(monkeypatch):
    monkeypatch.delenv("JARVIS_MESHY_API_KEY", raising=False)
    monkeypatch.delenv("MESHY_API_KEY", raising=False)
    assert meshy_api_key() == ""
    assert meshy_available() is False


def test_meshy_available_with_key(monkeypatch):
    monkeypatch.setenv("JARVIS_MESHY_API_KEY", "msk-test")
    assert meshy_available() is True
