"""P1 voice routing and sessions tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_brain_routing_deep():
    from jarvis.brain_routing import needs_deep_thinking, select_chat_model

    assert needs_deep_thinking("explain why recursion overflows")
    assert not needs_deep_thinking("hello")
    m = select_chat_model("hello", {})
    assert m


def test_local_router_parse():
    from jarvis.local_router import _parse_json

    raw = '{"action":"planner_set_timer","params":{"duration":"5 minutes"},"thinking":"timer"}'
    data = _parse_json(raw)
    assert data and data["action"] == "planner_set_timer"


def test_chat_sessions(tmp_path, monkeypatch):
    db = tmp_path / "chat_sessions.db"
    monkeypatch.setattr("jarvis.chat_sessions.DB_PATH", db)
    monkeypatch.setattr("jarvis.chat_sessions._init", lambda: None)
    import jarvis.chat_sessions as cs

    with cs._conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, branch_id TEXT,
                pinned INTEGER DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            """
        )
    s = cs.create_session("Test thread")
    assert s["title"] == "Test thread"
    assert cs.pin_session(s["id"], True)


def test_router_training_export(tmp_path, monkeypatch):
    out = tmp_path / "router_training.jsonl"
    monkeypatch.setattr("jarvis.router_training.OUT", out)
    from jarvis.router_training import export_training_jsonl

    path = export_training_jsonl()
    assert path.exists()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    row = json.loads(lines[0])
    assert "messages" in row


def test_conversation_truncate():
    from jarvis.conversation import Conversation

    c = Conversation("sys")
    c.add_user("hi")
    c.add_assistant("long reply")
    assert c.truncate_last_assistant()
    assert "interrupted" in c.messages[-1]["content"]
