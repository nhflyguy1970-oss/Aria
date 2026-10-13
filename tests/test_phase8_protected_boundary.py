"""Phase 8 — protected data/ boundary: ARIA's own writes are attributed, agent writes are not.

Regression for run_5e2375f2da: a read-only Codex run was reported as a
boundary violation because ARIA recorded the run's own progress events in
data/coding_agents.db while data/ was protected. Fake agents and temp stores only.
"""
# ruff: noqa: F811
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

import pytest
from test_phase5_coding_agents import _register, _run, agents, repo  # noqa: F401

from jarvis.coding_agents import boundary, contract, discovery, runs, workspace


def _data(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    (data / "logs").mkdir(parents=True)
    (data / "security" / "owner").mkdir(parents=True)
    (data / "plugins").mkdir()
    (data / "jarvis.env").write_text("SECRET=1\n")
    (data / "notes.json").write_text('{"owner": "notes"}')
    (data / "continuity.db").write_bytes(b"db")
    (data / "logs" / "jarvis.log").write_text("start\n")
    (data / "security" / "owner" / "vault.json").write_text("{}")
    (data / "security" / "owner" / "sessions.json").write_text(
        json.dumps({"sessions": {"v1": {"session_id": "s1", "created": 1.0, "last_active": 2.0}}}))
    (data / "automation_product").mkdir()
    (data / "automation_product" / "rules.json").write_text(json.dumps({"version": 1, "rules": [
        {"id": "r1", "action": "notify", "params": {}, "permissions": [], "last_run": 1.0, "last_status": "ok"}]}))
    (data / "coding_agent_runtime.json").write_text(json.dumps({"codex": {"state": "verified", "policy_sha256": "a"}}))
    conn = sqlite3.connect(data / "coding_agents.db")
    conn.executescript("CREATE TABLE runs (id TEXT PRIMARY KEY, status TEXT, result TEXT);"
                       "CREATE TABLE events (run_id TEXT, ts REAL, kind TEXT, detail TEXT);"
                       "INSERT INTO runs VALUES ('run_old', 'completed', 'ok');"
                       "INSERT INTO runs VALUES ('run_now', 'running', '');"
                       "INSERT INTO events VALUES ('run_old', 1.0, 'finished', 'completed');")
    conn.commit()
    conn.close()
    return data


def _check(data: Path, change) -> dict:
    before = boundary.snapshot([str(data)], data_dir=data, run_id="run_now")
    time.sleep(0.01)
    change(data)
    after = boundary.snapshot([str(data)], data_dir=data, run_id="run_now")
    return boundary.compare(before, after, data_dir=data)


def _sql(data: Path, statement: str) -> None:
    conn = sqlite3.connect(data / "coding_agents.db")
    conn.execute(statement)
    conn.commit()
    conn.close()


def _rewrite(rel: str, text: str):
    return lambda data: (data / rel).write_text(text)


# ---------------------------------------------------------------- legitimate ARIA writes


def test_incident_aria_ledger_events_for_the_current_run_are_not_a_violation(tmp_path):
    def aria_records_progress(data):
        _sql(data, "INSERT INTO events VALUES ('run_now', 2.0, 'progress', 'item.delta')")
        _sql(data, "UPDATE runs SET status='completed' WHERE id='run_now'")
        (data / "logs" / "jarvis.log").write_text("start\nmore\n")
        (data / "continuity.db").write_bytes(b"db2")

    report = _check(_data(tmp_path), aria_records_progress)
    assert report["violations"] == []
    assert any(p.endswith("coding_agents.db") for p in report["controller_writes"])
    assert {Path(p).name for p in report["runtime_writes"]} >= {"jarvis.log", "continuity.db"}


def test_certificate_may_only_be_disabled_during_a_run(tmp_path):
    disable = _rewrite("coding_agent_runtime.json", json.dumps({"codex": {"state": "disabled", "reason": "quota"}}))
    assert _check(_data(tmp_path / "a"), disable)["violations"] == []
    upgrade = _rewrite("coding_agent_runtime.json", json.dumps({"codex": {"state": "verified", "policy_sha256": "b"}}))
    assert _check(_data(tmp_path / "b"), upgrade)["violations"]
    added = _rewrite("coding_agent_runtime.json", json.dumps({"codex": {"state": "verified", "policy_sha256": "a"},
                                                              "claude_code": {"state": "verified"}}))
    assert _check(_data(tmp_path / "c"), added)["violations"]


def test_owner_sessions_may_only_be_used_or_revoked(tmp_path):
    used = _rewrite("security/owner/sessions.json",
                    json.dumps({"sessions": {"v1": {"session_id": "s1", "created": 1.0, "last_active": 9.0}}}))
    assert _check(_data(tmp_path / "a"), used)["violations"] == []
    revoked = _rewrite("security/owner/sessions.json", json.dumps({"sessions": {}}))
    assert _check(_data(tmp_path / "b"), revoked)["violations"] == []
    forged = _rewrite("security/owner/sessions.json", json.dumps({"sessions": {
        "v1": {"session_id": "s1", "created": 1.0, "last_active": 2.0},
        "v2": {"session_id": "evil", "created": 3.0, "last_active": 3.0}}}))
    assert _check(_data(tmp_path / "c"), forged)["violations"]


def _rules(**rule):
    base = {"id": "r1", "action": "notify", "params": {}, "permissions": [], "last_run": 1.0, "last_status": "ok"}
    return _rewrite("automation_product/rules.json", json.dumps({"version": 1, "rules": [{**base, **rule}]}))


def test_automation_rules_may_only_record_their_last_run(tmp_path):
    assert _check(_data(tmp_path / "a"), _rules(last_run=5.0, last_status="error"))["violations"] == []
    assert _check(_data(tmp_path / "b"), _rules(action="shell", params={"cmd": "curl x | sh"}))["violations"]
    assert _check(_data(tmp_path / "c"), _rules(permissions=["system.exec"]))["violations"]


# ---------------------------------------------------------------- unauthorized writes stay detectable


@pytest.mark.parametrize("change", [
    _rewrite("jarvis.env", "SECRET=stolen\n"),
    _rewrite("notes.json", '{"owner": "tampered"}'),
    _rewrite("security/owner/vault.json", '{"k": 1}'),
    _rewrite("plugins/backdoor.py", "import os\n"),
    _rewrite("logs/evil.py", "import os\n"),
    _rewrite("new_unregistered.db", "x"),
    lambda data: (data / "notes.json").unlink(),
    lambda data: (data / "link").symlink_to("/etc/passwd"),
    lambda data: _sql(data, "UPDATE runs SET status='verified' WHERE id='run_old'"),
    lambda data: _sql(data, "DELETE FROM events WHERE run_id='run_old'"),
], ids=["credentials", "user-data", "owner-vault", "plugin-code", "code-in-runtime-dir", "new-file",
        "deletion", "symlink", "receipt-tamper", "history-erase"])
def test_unauthorized_writes_are_violations_naming_the_file(tmp_path, change):
    report = _check(_data(tmp_path), change)
    assert report["violations"], report
    assert all(Path(v).is_relative_to(tmp_path) for v in report["violations"])


def test_rewrite_with_restored_mtime_is_still_detected(tmp_path):
    def sneaky(data):
        st = (data / "notes.json").stat()
        (data / "notes.json").write_text('{"owner": "notez"}')  # same size
        os.utime(data / "notes.json", ns=(st.st_atime_ns, st.st_mtime_ns))

    assert _check(_data(tmp_path), sneaky)["violations"]


def test_every_file_is_inventoried_no_truncation(tmp_path):
    data = _data(tmp_path)
    bulk = data / "projects" / "cache"
    bulk.mkdir(parents=True)
    for i in range(6000):
        (bulk / f"{i:05d}").write_text("c")
    report = _check(data, _rewrite("projects/cache/05999", "changed"))
    assert report["checked_files"] > 6000
    assert [Path(v).name for v in report["violations"]] == ["05999"]


def test_inventory_over_the_limit_is_refused_not_truncated(tmp_path, monkeypatch):
    monkeypatch.setattr(boundary, "MAX_FILES", 3)
    with pytest.raises(boundary.BoundaryError):
        boundary.snapshot([str(_data(tmp_path))], data_dir=tmp_path / "data", run_id="run_now")


def test_paths_outside_the_data_dir_are_always_strict(tmp_path):
    data = _data(tmp_path)
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    before = boundary.snapshot([str(env), str(data)], data_dir=data, run_id="run_now")
    env.write_text("A=2\n")
    after = boundary.snapshot([str(env), str(data)], data_dir=data, run_id="run_now")
    assert boundary.compare(before, after, data_dir=data)["violations"] == [str(env)]


def test_exposed_detects_mounts_of_or_around_protected_paths(tmp_path):
    data = tmp_path / "jarvis" / "data"
    data.mkdir(parents=True)
    assert boundary.exposed([str(tmp_path / "ws")], [str(data)]) == []
    assert boundary.exposed([str(data)], [str(data)])
    assert boundary.exposed([str(data / "sub")], [str(data)])
    assert boundary.exposed([str(tmp_path / "jarvis")], [str(data)])


# ---------------------------------------------------------------- full run path (fake agent, real supervision)


def test_read_only_run_with_live_data_dir_protected_completes(agents, repo):
    """The run_5e2375f2da scenario: data/ protected, ARIA records the run there."""
    proj = _register(repo, protected=[str(runs.DATA_DIR)])
    run = _run("codex", proj, "explain", mode=discovery.READ_ONLY)
    assert run["status"] == contract.COMPLETED, run["result"]["reason"]
    changes = run["receipt"]["protected_changes"]
    assert changes["violations"] == []
    assert any(p.endswith("coding_agents.db") for p in changes["controller_writes"])
    assert run["receipt"]["protected_mounts"].startswith("none")


def test_run_that_touches_protected_user_data_is_a_violation(agents, repo, monkeypatch):
    target = runs.DATA_DIR / "phase8_owner_notes.json"
    target.write_text("{}")
    proj = _register(repo, protected=[str(runs.DATA_DIR)])
    real = runs.adapters.parse

    def escaped_agent_writes(agent, out, err, out_dir, *rest):
        target.write_text('{"tampered": true}')  # simulates a write that bypassed the sandbox
        return real(agent, out, err, out_dir, *rest)

    monkeypatch.setattr(runs.adapters, "parse", escaped_agent_writes)
    try:
        run = _run("codex", proj, "explain", mode=discovery.READ_ONLY)
    finally:
        target.unlink()
    assert run["status"] == contract.VIOLATION
    assert str(target) in run["result"]["reason"]
    assert run["receipt"]["protected_changes"]["violations"] == [str(target)]


def test_sandbox_mount_of_a_protected_path_refuses_launch(agents, repo, monkeypatch, tmp_path):
    secret_dir = tmp_path / "protected-state"
    secret_dir.mkdir()
    proj = _register(repo, protected=[str(secret_dir)])
    monkeypatch.setattr(workspace, "private_agent_state", lambda *a, **k: [(str(secret_dir), "/home/x/.codex")])
    run = _run("codex", proj, "explain", mode=discovery.READ_ONLY)
    assert run["status"] == contract.REFUSED
    assert "protected path mounted" in run["result"]["reason"]
