"""Self-upgrade pipeline tests."""

from pathlib import Path

import pytest

from jarvis.self_upgrade import (
    branch_name_for_task,
    is_merge_command,
    is_self_upgrade_task,
    merge_pipeline,
    parse_self_upgrade_task,
    run_pipeline,
)


def test_parse_self_upgrade_task():
    assert "ping" in parse_self_upgrade_task("self upgrade: add /api/ping").lower()
    assert is_self_upgrade_task("run self upgrade: fix router")


def test_branch_name():
    name = branch_name_for_task("add health route")
    assert name.startswith("aria/upgrade-")


def test_run_pipeline_no_git(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.self_upgrade.is_repo", lambda: False)
    result = run_pipeline(assistant, "add ping")
    assert not result["ok"]
    assert "git" in result["message"].lower()


def test_run_pipeline_dirty_tree(assistant, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("jarvis.self_upgrade.is_repo", lambda: True)
    monkeypatch.setattr("jarvis.self_upgrade.has_local_changes", lambda: True)
    result = run_pipeline(assistant, "add ping")
    assert not result["ok"]
    assert "uncommitted" in result["message"].lower()


def test_run_pipeline_success(assistant, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("jarvis.self_upgrade.is_repo", lambda: True)
    monkeypatch.setattr("jarvis.self_upgrade.has_local_changes", lambda: False)
    monkeypatch.setattr("jarvis.self_upgrade.create_branch", lambda name: f"Created `{name}`")
    monkeypatch.setattr(
        "jarvis.self_upgrade.commit",
        lambda msg, files=None: "[main abc123] upgrade",
    )
    monkeypatch.setattr("jarvis.self_upgrade.verify_proposal", lambda p, base=None: (True, "pytest ok"))
    monkeypatch.setattr("jarvis.self_upgrade._abort_branch", lambda *a: [])

    assistant._upgrade_wizard = lambda params, msg: {
        "ok": True,
        "proposal_id": "p1",
        "message": "proposed",
    }
    assistant._upgrade_verify = lambda params, msg: {"ok": True, "message": "verified"}
    assistant._upgrade_apply = lambda params, msg: {
        "ok": True,
        "message": "applied",
        "snapshot_id": "snap1",
    }
    assistant._upgrade_proposal = lambda pid=None: {
        "files": [{"path": "jarvis/ping.py", "code": "def ping(): return 1\n"}],
        "verified": True,
    }
    assistant.session.last_proposal_id = "p1"
    assistant.pending_proposals = {
        "p1": {"files": [{"path": "jarvis/ping.py", "code": "def ping(): return 1\n"}]},
    }

    result = run_pipeline(assistant, "add ping route")
    assert result["ok"]
    assert result.get("awaiting_merge")
    assert "aria/upgrade" in result.get("branch", "")


def test_merge_requires_session(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.self_upgrade.get_session", lambda: None)
    result = merge_pipeline(assistant)
    assert not result["ok"]


def test_router_self_upgrade():
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("self upgrade: add health endpoint", SessionContext())
    assert intent["action"] == "self_upgrade_run"
    assert "health" in intent["params"]["task"].lower()

    intent2 = route("merge upgrade", SessionContext())
    assert intent2["action"] == "self_upgrade_merge"

    assert is_merge_command("approve merge")
