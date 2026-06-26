"""Tests for home-network request guard."""

from unittest.mock import MagicMock

import pytest

from jarvis import network_guard


def _req(ip: str, path: str = "/api/chat") -> MagicMock:
    req = MagicMock()
    req.url.path = path
    req.client.host = ip
    req.headers = {}
    return req


def test_localhost_allowed(monkeypatch):
    monkeypatch.delenv("JARVIS_ALLOW_REMOTE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("JARVIS_NETWORK_GUARD", "1")
    assert network_guard.client_allowed(_req("127.0.0.1"))
    assert network_guard.client_allowed(_req("::1"))


def test_lan_allowed(monkeypatch):
    monkeypatch.delenv("JARVIS_ALLOW_REMOTE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("JARVIS_NETWORK_GUARD", "1")
    assert network_guard.client_allowed(_req("192.168.1.42"))
    assert network_guard.client_allowed(_req("10.0.0.5"))


def test_public_blocked(monkeypatch):
    monkeypatch.delenv("JARVIS_ALLOW_REMOTE", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("JARVIS_NETWORK_GUARD", "1")
    assert not network_guard.client_allowed(_req("8.8.8.8"))
    assert not network_guard.client_allowed(_req("1.2.3.4"))


def test_allow_remote_override(monkeypatch):
    monkeypatch.setenv("JARVIS_ALLOW_REMOTE", "1")
    monkeypatch.setenv("JARVIS_NETWORK_GUARD", "1")
    assert network_guard.client_allowed(_req("8.8.8.8"))
