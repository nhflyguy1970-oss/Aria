"""LAN access and API key auth tests."""

from unittest.mock import MagicMock

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from jarvis.auth import APIKeyMiddleware, api_key_enabled, api_key_required_for, check_key, is_local_client
from jarvis.lan import (
    client_base_url,
    client_host,
    is_lan_bind,
    is_wildcard_bind,
    lan_status,
    list_lan_ips,
)


async def _protected(request):
    return JSONResponse({"ok": True})


@pytest.fixture
def authed_app(monkeypatch):
    monkeypatch.setenv("JARVIS_API_KEY", "test-secret-key")
    app = Starlette(routes=[
        Route("/api/chat", _protected),
        Route("/api/live", _protected),
        Route("/api/lan", _protected),
    ])
    app.add_middleware(APIKeyMiddleware)
    return TestClient(app)


def test_api_key_enabled(monkeypatch):
    monkeypatch.delenv("JARVIS_API_KEY", raising=False)
    assert api_key_enabled() is False
    monkeypatch.setenv("JARVIS_API_KEY", "abc")
    assert api_key_enabled() is True


def test_check_key_strips_whitespace(monkeypatch):
    monkeypatch.setenv("JARVIS_API_KEY", "jarvis-home")
    req = MagicMock()
    req.headers = {"X-API-Key": "  jarvis-home  "}
    req.query_params = {}
    assert check_key(req) is True
    monkeypatch.setenv("JARVIS_API_KEY", "sekret")
    req = MagicMock()
    req.headers = {"Authorization": "Bearer sekret"}
    req.query_params = {}
    assert check_key(req) is True
    req.headers = {"X-API-Key": "sekret"}
    assert check_key(req) is True
    req.headers = {"X-API-Key": "wrong"}
    assert check_key(req) is False


def test_middleware_exempt_live_and_lan(authed_app):
    assert authed_app.get("/api/live").status_code == 200
    assert authed_app.get("/api/lan").status_code == 200


def test_localhost_skips_api_key(monkeypatch):
    monkeypatch.setenv("JARVIS_API_KEY", "sekret")
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers = {}
    assert is_local_client(req) is True
    assert api_key_required_for(req) is False


def test_lan_client_needs_api_key(monkeypatch):
    monkeypatch.setenv("JARVIS_API_KEY", "sekret")
    req = MagicMock()
    req.client.host = "192.168.1.42"
    req.headers = {}
    assert is_local_client(req) is False
    assert api_key_required_for(req) is True


def test_middleware_blocks_remote_without_key(monkeypatch, authed_app):
    monkeypatch.setenv("JARVIS_TRUST_PROXY", "1")
    res = authed_app.get("/api/chat", headers={"X-Forwarded-For": "192.168.1.50"})
    assert res.status_code == 401


def test_middleware_allows_with_header(authed_app):
    res = authed_app.get(
        "/api/chat",
        headers={"X-API-Key": "test-secret-key"},
    )
    assert res.status_code == 200


def test_client_host_wildcard():
    assert client_host("0.0.0.0") == "127.0.0.1"
    assert client_base_url("0.0.0.0", 8765) == "http://127.0.0.1:8765"


def test_is_lan_bind(monkeypatch):
    monkeypatch.setenv("JARVIS_HOST", "127.0.0.1")
    assert is_lan_bind() is False
    monkeypatch.setenv("JARVIS_HOST", "0.0.0.0")
    assert is_lan_bind() is True
    assert is_wildcard_bind("0.0.0.0") is True


def test_lan_status_shape(monkeypatch):
    monkeypatch.setenv("JARVIS_HOST", "0.0.0.0")
    monkeypatch.setenv("JARVIS_API_KEY", "key123")
    status = lan_status()
    assert status["ok"] is True
    assert status["lan_enabled"] is True
    assert status["api_key_required"] is True
    assert status["local_url"].startswith("http://127.0.0.1:")
    assert isinstance(status["connect_urls"], list)
    assert isinstance(status["hints"], list)


def test_list_lan_ips_returns_list():
    ips = list_lan_ips()
    assert isinstance(ips, list)


def test_api_lan_route(chat_app):
    res = chat_app.get("/api/lan")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "connect_urls" in data
