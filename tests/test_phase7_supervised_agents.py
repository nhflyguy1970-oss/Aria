"""Phase 7: disposable fake agents, real process cancellation and durable evidence."""

# ruff: noqa: F811
import json
import os
import shlex
import sys
import time
from pathlib import Path
from unittest.mock import patch
import pytest
from test_phase5_coding_agents import agents, repo, _register, _run  # noqa: F401
from jarvis.coding_agents import adapters, artifacts, contract, discovery, runs, sessions, workspace


def finished(run_id, timeout=12):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        run = runs.get_run(run_id)
        if run["status"] in contract.TERMINAL:
            return run
        time.sleep(0.05)
    pytest.fail("supervisor did not finish")


def durable_run(agents, repo, monkeypatch):
    state = agents.tmp / "private-account"
    state.mkdir()
    (state / "auth.json").write_text('{"access_token":"fake-test-token"}')
    monkeypatch.setattr(workspace, "agent_state_dirs", lambda agent: [str(state)])
    run = _run("codex", _register(repo), "inspect calc", mode=discovery.READ_ONLY)
    private = Path(run["receipt"]["private_state"][0][0])
    (private / "sessions").mkdir()
    (private / "sessions/thread.jsonl").write_text('{"fixture":"private history"}\n')
    (private / "config.toml").write_text("unapproved configuration")
    return run


def test_continuation_requires_new_approval_and_reuses_only_private_session(agents, repo, monkeypatch):
    prior = durable_run(agents, repo, monkeypatch)
    plan = runs.create_resume_plan(prior["id"], task="explain the function")
    assert plan["status"] == runs.PROPOSED and plan["resume_run"] == prior["id"]
    with pytest.raises(runs.AgentRunError, match="not approved"):
        runs.start(plan["id"], background=False)
    resumed = runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="owner fixture", background=False)
    assert resumed["status"] == contract.COMPLETED, resumed["result"]
    assert resumed["workspace"] == prior["workspace"]
    private = Path(resumed["receipt"]["private_state"][0][0])
    assert (private / "sessions/thread.jsonl").read_text() == '{"fixture":"private history"}\n'
    assert not (private / "config.toml").exists()
    assert runs.start(plan["id"], background=False)["id"] == resumed["id"]
    assert len(runs.list_runs()) == 2


@pytest.mark.parametrize("mutation", ["code", "session", "scope", "mode"])
def test_continuation_cannot_expand_or_mutate_reviewed_scope(agents, repo, monkeypatch, mutation):
    prior = durable_run(agents, repo, monkeypatch)
    plan = runs.create_resume_plan(prior["id"], task="explain")
    if mutation == "code":
        Path(prior["workspace"], "calc.py").write_text("unauthorized change\n")
    if mutation == "session":
        Path(prior["receipt"]["private_state"][0][0], "sessions/thread.jsonl").write_text("changed")
    if mutation == "scope":
        from jarvis.coding_agents import projects

        original = projects.get
        monkeypatch.setattr(projects, "get", lambda slug: {**original(slug), "test_command": "unapproved command"})
    if mutation == "mode":
        with runs._conn() as conn:
            conn.execute("UPDATE plans SET mode=? WHERE id=?", (discovery.WORKSPACE_WRITE, plan["id"]))
    with pytest.raises(runs.AgentRunError):
        runs.approve(plan["id"], token=runs.approval_token(plan["id"]), via="fixture")
    assert len(runs.list_runs()) == 1


def test_private_session_symlink_is_refused(agents, repo, monkeypatch):
    prior = durable_run(agents, repo, monkeypatch)
    Path(prior["receipt"]["private_state"][0][0], "sessions/escape").symlink_to(repo)
    with pytest.raises(runs.AgentRunError, match="redirected"):
        runs.create_resume_plan(prior["id"], task="explain")


def test_restart_reconciles_pid_reuse_without_signalling_unrelated_process(agents):
    identity = sessions.process_identity(os.getpid())
    identity["start_ticks"] = "wrong"
    with runs._conn() as conn:
        conn.execute(
            "INSERT INTO runs (id,status,owner_pid,receipt) VALUES (?,?,?,?)",
            ("reused-pid", runs.RUNNING, os.getpid(), json.dumps({"owner_identity": identity})),
        )
    with patch.object(runs.os, "kill") as kill:
        assert runs.recover_interrupted() == ["reused-pid"]
        kill.assert_not_called()
    assert runs.get_run("reused-pid")["status"] == contract.INTERRUPTED
    assert runs.recover_interrupted() == []


def test_reconciliation_preserves_live_owner_reservation(agents):
    with runs._conn() as conn:
        conn.execute(
            "INSERT INTO runs (id,status,owner_pid,receipt) VALUES (?,?,?,?)",
            ("live-owner", runs.RUNNING, os.getpid(), json.dumps({"owner_identity": sessions.process_identity(os.getpid())})),
        )
    assert runs.recover_interrupted() == []
    assert runs.get_run("live-owner")["status"] == runs.RUNNING
    runs._update("live-owner", status=contract.INTERRUPTED)


def test_pending_cancel_never_launches_agent(agents, repo, monkeypatch):
    from jarvis.missions import engine

    plan = runs.create_plan(agent="codex", project=_register(repo)["slug"], mode=discovery.READ_ONLY, task="look")
    runs.approve(plan["id"], token=runs.approval_token(plan["id"]), via="fixture")
    reserved = runs._reserve_run(plan["id"], engine)
    runs.cancel(reserved["run_id"])
    with patch.object(runs.subprocess, "Popen") as popen:
        runs.execute_step(reserved["run_id"])
        popen.assert_not_called()
    assert runs.get_run(reserved["run_id"])["status"] == contract.CANCELLED
    runs._owned.discard(reserved["run_id"])


def test_cancel_during_independent_verification_cannot_report_success(agents, repo):
    command = f"{shlex.quote(sys.executable)} -c " + shlex.quote(
        'import time; from pathlib import Path; Path("verifying.txt").write_text("ready"); time.sleep(120)'
    )
    project = _register(repo, test_command=command)
    agents.behave(edits={"calc.py": "def add(a,b): return a+b\n"})
    plan = runs.create_plan(agent="codex", project=project["slug"], mode=discovery.WORKSPACE_WRITE, task="tidy")
    run = runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="fixture")
    end = time.monotonic() + 10
    while time.monotonic() < end:
        current = runs.get_run(run["id"])
        if current.get("workspace") and Path(current["workspace"], "verifying.txt").exists():
            break
        time.sleep(0.05)
    else:
        pytest.fail("verification did not start")
    runs.cancel(run["id"])
    final = finished(run["id"])
    assert final["status"] == contract.CANCELLED and not final["result"]["success"]
    assert final["result"]["tests_run"][0]["cancelled"]
    artifacts.verify(final["receipt"]["artifacts"])


def test_verification_timeout_and_output_are_bounded(tmp_path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    result = workspace.run_tests(str(ws), "sleep 120", timeout=0.1)
    assert result["timed_out"] and not result["passed"] and result["seconds"] < 5
    result = workspace.run_tests(str(ws), f"{shlex.quote(sys.executable)} -c " + shlex.quote('print("X" * 5000000)'), timeout=10)
    assert result["output_limit_exceeded"] and not result["passed"]
    assert Path(result["output_log"]).stat().st_size <= 4_000_000


def test_verification_that_changes_code_is_not_verified(agents, repo):
    project = _register(repo, test_command="printf 'def add(a,b): return 99\n' > calc.py")
    agents.behave(edits={"calc.py": "def add(a,b): return a+b\n"})
    run = _run("codex", project, "tidy")
    assert run["status"] == contract.TESTS_FAILED
    assert "changed code" in run["result"]["tests_run"][0]["error"]


def test_full_patch_and_test_log_are_readback_verified_and_tampering_detected(agents, repo):
    project = _register(repo)
    agents.behave(edits={"calc.py": "def add(a,b): return a+b # tidy\n"})
    run = _run("codex", project, "tidy")
    assert run["status"] == contract.VERIFIED, run["result"]
    record = run["receipt"]["artifacts"]
    artifacts.verify(record)
    assert {"changes.patch", "tests.json", "stdout.log", "stderr.log", "verification.log"} <= {x["name"] for x in record["files"]}
    path = Path(record["directory"], "changes.patch")
    assert "+def add(a,b)" in path.read_text()
    path.write_text("tampered")
    with pytest.raises(RuntimeError, match="changed"):
        artifacts.verify(record)


def test_zero_exit_with_missing_codex_terminal_event_is_failure(agents, repo, monkeypatch):
    parser = adapters.parse

    def incomplete(*args, **kwargs):
        report = parser(*args, **kwargs)
        report.terminal_status = ""
        return report

    monkeypatch.setattr(adapters, "parse", incomplete)
    run = _run("codex", _register(repo), "explain", mode=discovery.READ_ONLY)
    assert run["status"] == contract.FAILED and not run["result"]["success"]


def test_failed_git_evidence_cannot_be_reported_as_no_changes(monkeypatch, tmp_path):
    from types import SimpleNamespace

    monkeypatch.setattr(workspace, "_git", lambda *a, **kw: SimpleNamespace(returncode=1, stdout=""))
    with pytest.raises(workspace.WorkspaceError, match="evidence collection failed"):
        workspace.collect_changes(str(tmp_path), "base")


def test_mission_creation_failure_keeps_consumed_approval_and_durable_failure(agents, repo, monkeypatch):
    from jarvis.missions import engine

    plan = runs.create_plan(agent="codex", project=_register(repo)["slug"], mode=discovery.READ_ONLY, task="inspect")

    def failure(*args, **kwargs):
        raise RuntimeError("simulated mission insertion failure")

    monkeypatch.setattr(engine, "create_mission", failure)
    with pytest.raises(runs.AgentRunError, match="failure is recorded"):
        runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="fixture", background=False)
    run = runs.run_for_plan(plan["id"])
    assert run["status"] == contract.FAILED
    assert runs.get_plan(plan["id"])["status"] == runs.CONSUMED
    assert runs.start(plan["id"], background=False)["id"] == run["id"]


def test_chat_continuation_is_a_reviewable_choice_and_does_not_execute(agents, repo, monkeypatch):
    from types import SimpleNamespace
    from jarvis.handlers.coding_agent_cli_handlers import coding_agent_resume

    prior = durable_run(agents, repo, monkeypatch)
    assistant = SimpleNamespace(session=SimpleNamespace(project_slug=prior["project"]))
    with patch.object(runs, "start") as start:
        result = coding_agent_resume(assistant, {"run_id": prior["id"], "task": "Explain the original function"}, "continue")
        start.assert_not_called()
    assert result["ok"] and "Continue Codex session" in result["message"]
    choice = assistant.session.pending_clarification["choice_intents"][0]
    plan = runs.get_plan(choice["params"]["plan_id"])
    assert plan["resume_run"] == prior["id"] and plan["status"] == runs.PROPOSED
    assert choice["params"]["approval_token"] == runs.approval_token(plan["id"])


def test_continuation_refuses_empty_native_thread_history(agents, repo, monkeypatch):
    prior = durable_run(agents, repo, monkeypatch)
    Path(prior["receipt"]["private_state"][0][0], "sessions/thread.jsonl").unlink()
    with pytest.raises(runs.AgentRunError, match="no saved turn history"):
        runs.create_resume_plan(prior["id"], task="continue")
    assert len(runs.list_runs()) == 1


def test_cancel_accepted_during_artifact_capture_wins_completion_race(agents, repo, monkeypatch):
    capture = artifacts.capture

    def cancel_before_commit(*args, **kwargs):
        active = next(r for r in runs.list_runs() if r["status"] == runs.RUNNING)
        runs.cancel(active["id"])
        return capture(*args, **kwargs)

    monkeypatch.setattr(artifacts, "capture", cancel_before_commit)
    run = _run("codex", _register(repo), "inspect", mode=discovery.READ_ONLY)
    assert run["status"] == contract.CANCELLED and not run["result"]["success"]
    assert not run["result"]["verified_completion"]
    assert runs.cancel(run["id"])["result"] == run["result"]


def test_refreshed_credentials_are_redacted_from_final_logs_and_artifacts(agents, repo, monkeypatch):
    state = agents.tmp / "refresh-account"
    state.mkdir()
    (state / "auth.json").write_text('{"access_token":"old-test-secret"}')
    monkeypatch.setattr(workspace, "agent_state_dirs", lambda agent: [str(state)])
    agents.behave(sleep=0.3, refresh_auth_file=str(state / "auth.json"), refreshed_token="new-test-secret", message="new-test-secret")
    run = _run("codex", _register(repo), "inspect", mode=discovery.READ_ONLY)
    assert run["status"] == contract.COMPLETED, run["result"]
    assert "old-test-secret" in (state / "auth.json").read_text()
    assert "new-test-secret" not in json.dumps(run["result"])
    for path in run["receipt"]["output_logs"].values():
        assert "new-test-secret" not in Path(path).read_text()
    for entry in run["receipt"]["artifacts"]["files"]:
        assert b"new-test-secret" not in Path(run["receipt"]["artifacts"]["directory"], entry["name"]).read_bytes()


def test_continuation_api_preserves_step_up_and_explicit_execution_approval(agents, repo, monkeypatch, chat_app):
    from types import SimpleNamespace

    prior = durable_run(agents, repo, monkeypatch)
    path = f"/api/coding-agents/runs/{prior['id']}/resume-plan"
    decisions = []

    def authorize(capability, **kwargs):
        decisions.append(capability)
        return {"ok": False, "reason": "step-up required"}

    monkeypatch.setattr("jarvis.security.owner.provider_credentials.bound_owner_service", lambda: SimpleNamespace(authorize=authorize))
    assert chat_app.post(path, json={"task": "explain"}).status_code == 403
    assert len(runs.list_runs()) == 1
    monkeypatch.setattr(
        "jarvis.security.owner.provider_credentials.bound_owner_service", lambda: SimpleNamespace(authorize=lambda *a, **k: {"ok": True})
    )
    with patch.object(runs, "start") as start:
        response = chat_app.post(path, json={"task": "explain"})
        start.assert_not_called()
    assert response.status_code == 200 and response.json()["requires_owner_approval"]
    assert response.json()["plan"]["status"] == runs.PROPOSED
    assert "nonce" not in response.json()["plan"]
    assert decisions == ["git.write"] and len(runs.list_runs()) == 1


def test_artifact_api_detects_modified_evidence(agents, repo, chat_app):
    run = _run("codex", _register(repo), "explain", mode=discovery.READ_ONLY)
    path = f"/api/coding-agents/runs/{run['id']}/artifacts"
    response = chat_app.get(path)
    assert response.status_code == 200 and response.json()["verified"]
    Path(run["receipt"]["artifacts"]["directory"], "stdout.log").write_text("tampered")
    response = chat_app.get(path)
    assert response.status_code == 409 and not response.json()["verified"]


def test_failed_launch_intent_rolls_back_approval_consumption(agents, repo):
    import sqlite3

    plan = runs.create_plan(agent="codex", project=_register(repo)["slug"], mode=discovery.READ_ONLY, task="inspect")
    runs.approve(plan["id"], token=runs.approval_token(plan["id"]), via="fixture")
    with runs._conn() as conn:
        conn.execute("CREATE TRIGGER fixture_failed_intent BEFORE INSERT ON runs BEGIN SELECT RAISE(ABORT, 'disk failure fixture'); END")
    with pytest.raises(sqlite3.IntegrityError, match="disk failure fixture"):
        runs.start(plan["id"], background=False)
    assert runs.get_plan(plan["id"])["status"] == runs.APPROVED
    assert runs.run_for_plan(plan["id"]) is None
    with runs._conn() as conn:
        conn.execute("DROP TRIGGER fixture_failed_intent")
    run = runs.start(plan["id"], background=False)
    assert run["status"] == contract.COMPLETED
    assert len(runs.list_runs()) == 1 and runs.get_plan(plan["id"])["status"] == runs.CONSUMED
