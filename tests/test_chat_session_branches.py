"""Chat OS — unified New Chat, sessions, and branch association."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture
def sessions_db(tmp_path, monkeypatch):
    db = tmp_path / "chat_sessions.db"
    monkeypatch.setattr("jarvis.chat_sessions.DB_PATH", db)
    import jarvis.chat_sessions as cs

    # Re-init against temp DB
    cs._init()
    return cs


def test_create_session_and_pin_toggle(sessions_db):
    cs = sessions_db
    s = cs.create_session("Work thread", branch_id="main")
    assert s["title"] == "Work thread"
    assert s["branch_id"] == "main"
    assert cs.pin_session(s["id"], True) is True
    assert cs.get_session(s["id"])["pinned"] in (1, True)
    assert cs.pin_session(s["id"], False) is True
    assert not cs.get_session(s["id"])["pinned"]


def test_create_new_chat_unified(sessions_db, monkeypatch):
    cs = sessions_db
    created = {"name": None, "kwargs": None}

    class FakeBranches:
        active_id = "main"

        def create_branch(self, name, from_branch=None, from_index=None, **kwargs):
            created["name"] = name
            created["kwargs"] = kwargs
            return f"br_{name.replace(' ', '_').lower()}"

    class FakeAssistant:
        branches = FakeBranches()

        def create_branch(self, name, from_index=None, **kwargs):
            created["kwargs"] = kwargs
            return self.branches.create_branch(name, **kwargs)

    monkeypatch.setattr("jarvis.assistant_instance.get_assistant", lambda: FakeAssistant())
    monkeypatch.setattr("jarvis.chat_sessions.chat_sessions_enabled", lambda: True)

    result = cs.create_new_chat(title="Weekend project")
    assert result["ok"] is True
    assert result["branch_id"].startswith("br_")
    assert result["session"]["title"] == "Weekend project"
    assert result["session"]["branch_id"] == result["branch_id"]
    assert created["name"] == "Weekend project"
    assert created["kwargs"].get("copy_messages") is False
    assert created["kwargs"].get("copy_session") is False


def test_create_new_chat_default_title(sessions_db, monkeypatch):
    cs = sessions_db

    class FakeAssistant:
        def create_branch(self, name, from_index=None, **kwargs):
            return "br_new"

    monkeypatch.setattr("jarvis.assistant_instance.get_assistant", lambda: FakeAssistant())
    result = cs.create_new_chat()
    assert result["ok"]
    assert result["branch_id"] == "br_new"
    assert result["session"]["branch_id"] == "br_new"


def test_branch_manager_new_chat_starts_empty(tmp_path, monkeypatch):
    import jarvis.branches as br

    path = tmp_path / "branches.json"
    monkeypatch.setattr(br, "BRANCHES_FILE", path)
    mgr = br.BranchManager()
    mgr._data["branches"]["main"]["messages"] = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    mgr._save()
    fork_id = mgr.create_branch("Forked")
    assert len(mgr._data["branches"][fork_id]["messages"]) == 2
    empty_id = mgr.create_branch("Fresh", copy_messages=False, copy_session=False)
    assert mgr._data["branches"][empty_id]["messages"] == []
    assert mgr._data["branches"][empty_id]["forked_from"] is None
    assert mgr.active_id == empty_id
