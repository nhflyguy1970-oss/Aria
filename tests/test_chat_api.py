"""Chat API — unified New Chat endpoint and session routes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def chat_api_client(tmp_path, monkeypatch):
    db = tmp_path / "chat_sessions.db"
    monkeypatch.setattr("jarvis.chat_sessions.DB_PATH", db)
    import jarvis.chat_sessions as cs

    cs._init()

    class FakeAssistant:
        def create_branch(self, name, from_index=None):
            return f"branch_{abs(hash(name)) % 100000}"

    monkeypatch.setattr("jarvis.assistant_instance.get_assistant", lambda: FakeAssistant())
    monkeypatch.setattr("jarvis.p1_flags.chat_sessions_enabled", lambda: True)
    monkeypatch.setattr("jarvis.chat_sessions.chat_sessions_enabled", lambda: True)

    app = FastAPI()
    from jarvis.extensions.voice.api import register_routes

    register_routes(app, SimpleNamespace())
    return TestClient(app)


def test_api_chat_new(chat_api_client):
    res = chat_api_client.post("/api/chat/new", json={"title": "Morning focus"})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["branch_id"]
    assert data["session"]["title"] == "Morning focus"
    assert data["session"]["branch_id"] == data["branch_id"]


def test_api_chat_sessions_list_and_pin(chat_api_client):
    created = chat_api_client.post("/api/chat/sessions", json={"title": "Pinned", "branch_id": "main"}).json()
    sid = created["session"]["id"]
    listed = chat_api_client.get("/api/chat/sessions").json()
    assert any(s["id"] == sid for s in listed.get("sessions", []))
    pin = chat_api_client.post(f"/api/chat/sessions/{sid}/pin", json={"pinned": True})
    assert pin.status_code == 200
    assert pin.json()["ok"] is True
    unpin = chat_api_client.post(f"/api/chat/sessions/{sid}/pin", json={"pinned": False})
    assert unpin.json()["ok"] is True
