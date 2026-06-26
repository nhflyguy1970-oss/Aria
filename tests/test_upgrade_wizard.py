"""Upgrade Jarvis wizard — guardrails, snapshot, rollback, routing."""

from pathlib import Path

import pytest

from jarvis.upgrade_wizard import (
    SESSION_FILE,
    SNAPSHOT_DIR,
    create_snapshot,
    is_upgrade_task,
    parse_upgrade_task,
    rollback_snapshot,
    save_session,
    validate_proposal_paths,
    verify_proposal,
    wizard_status,
)


def test_is_upgrade_task():
    assert is_upgrade_task("upgrade jarvis: add health endpoint")
    assert is_upgrade_task("upgrade: wire rollback button")
    assert is_upgrade_task("improve jarvis routing for documents")
    assert not is_upgrade_task("how hard would it be to upgrade yourself")
    assert not is_upgrade_task("what can you do")


def test_parse_upgrade_task():
    assert parse_upgrade_task("upgrade jarvis: add tests") == "add tests"
    assert parse_upgrade_task("upgrade: fix router") == "fix router"


def test_validate_proposal_paths_allows_jarvis_and_tests():
    ok, errs = validate_proposal_paths([
        {"path": "jarvis/foo.py", "code": "x = 1"},
        {"path": "tests/test_foo.py", "code": "def test_x(): pass"},
    ])
    assert ok is True
    assert errs == []


def test_validate_proposal_paths_blocks_live_data():
    ok, errs = validate_proposal_paths([
        {"path": "data/journal/daily.json", "code": "{}"},
    ])
    assert ok is False
    assert any("Blocked" in e or "journal" in e.lower() for e in errs)


def test_validate_proposal_paths_blocks_outside_tree():
    ok, errs = validate_proposal_paths([
        {"path": "scripts/foo.sh", "code": "#!/bin/sh"},
    ])
    assert ok is False
    assert any("jarvis/" in e for e in errs)


def test_snapshot_and_rollback(data_dir, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("jarvis.upgrade_wizard.SESSION_FILE", data_dir / "upgrade_wizard.json")
    monkeypatch.setattr("jarvis.upgrade_wizard.SNAPSHOT_DIR", data_dir / "upgrade_snapshots")
    monkeypatch.setattr("jarvis.upgrade_wizard.PROJECT_ROOT", tmp_path)

    target = tmp_path / "jarvis" / "sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")

    files = [{"path": "jarvis/sample.py", "code": "after\n"}]
    snap = create_snapshot(files, task="test snap", proposal_id="abc123")
    assert snap["id"]

    target.write_text("after\n", encoding="utf-8")
    save_session({"snapshot_id": snap["id"], "step": "applied"})

    ok, msg, restored = rollback_snapshot(snap["id"])
    assert ok is True
    assert "jarvis/sample.py" in restored
    assert target.read_text(encoding="utf-8") == "before\n"
    assert "Rolled back" in msg


def test_wizard_status(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.upgrade_wizard.SESSION_FILE", data_dir / "upgrade_wizard.json")
    monkeypatch.setattr("jarvis.upgrade_wizard.SNAPSHOT_DIR", data_dir / "upgrade_snapshots")
    save_session({"step": "proposed", "task": "add health", "proposal_id": "p1"})
    status = wizard_status()
    assert status["active"]["proposal_id"] == "p1"
    assert "jarvis/" in str(status["guardrails"]["allowed"])


def test_verify_proposal_syntax_only(data_dir, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("jarvis.upgrade_wizard.PROJECT_ROOT", tmp_path)
    pkg = tmp_path / "jarvis"
    pkg.mkdir()
    (pkg / "ok.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    files = [{"path": "jarvis/ok.py", "code": "def ok():\n    return 2\n"}]
    monkeypatch.setattr(
        "jarvis.upgrade_wizard._pytest_for_changes",
        lambda paths: (True, "pytest passed (mocked)"),
    )
    ok, detail = verify_proposal({"files": files}, base=tmp_path)
    assert ok is True
    assert "mocked" in detail


def test_router_upgrade_wizard():
    from jarvis.router import route
    from jarvis.session import SessionContext

    session = SessionContext()
    intent = route("upgrade jarvis: add /api/ping", session)
    assert intent["action"] == "upgrade_wizard"
    assert "ping" in intent["params"]["task"].lower()

    intent2 = route("verify upgrade", session)
    assert intent2["action"] == "upgrade_verify"

    intent3 = route("rollback upgrade", session)
    assert intent3["action"] == "upgrade_rollback"


def test_apply_blocks_unverified_upgrade(assistant, monkeypatch):
    pid, payload = assistant._store_agent_proposal(
        [{"path": "jarvis/ping.py", "code": "def ping(): return 'pong'\n"}],
        mode="upgrade_wizard",
        explanation="test",
    )
    payload["verified"] = False
    assistant.pending_proposals[pid] = payload
    assistant.session.last_proposal_id = pid

    result = assistant.apply_proposal(pid)
    assert result["ok"] is False
    assert "verify" in result["message"].lower()
    assert pid in assistant.pending_proposals


def test_apply_blocks_journal_paths(assistant):
    pid, payload = assistant._store_agent_proposal(
        [{"path": "data/memory.json", "code": "{}"}],
        mode="upgrade_wizard",
        explanation="bad",
    )
    payload["verified"] = True
    assistant.pending_proposals[pid] = payload
    assistant.session.last_proposal_id = pid

    result = assistant.apply_proposal(pid)
    assert result["ok"] is False
    assert "blocked" in result["message"].lower() or "not allowed" in result["message"].lower()
