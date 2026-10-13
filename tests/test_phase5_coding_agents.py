"""Phase 5 — coding-agent CLIs under supervision (simulated agents only).

The simulated agent (tests/fixtures/fake_coding_agent.py) is a real executable
installed as ``codex`` / ``claude`` / ``agy``, so these tests exercise the real
subprocess, bubblewrap sandbox, git evidence and verdict path. No live agent,
no network, no paid API.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from jarvis.coding_agents import (
    adapters,
    contract,
    discovery,
    projects,
    runs,
    supervisor,
    workspace,
)

FAKE = Path(__file__).parent / "fixtures" / "fake_coding_agent.py"
ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(not shutil.which("bwrap"), reason="bubblewrap required for agent sandbox")


@pytest.fixture
def agents(tmp_path, monkeypatch):
    """Fake CLIs on a temp bin dir; workspaces in tmp; isolated stores."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name in ("codex", "claude", "agy"):
        (bindir / name).symlink_to(FAKE)
    os.chmod(FAKE, 0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("JARVIS_AGENT_WORKSPACES", str(tmp_path / "workspaces"))
    monkeypatch.setattr(discovery, "_search_path", lambda: [str(bindir), "/usr/bin", "/bin"])
    from jarvis.coding_agents import runtime

    monkeypatch.setattr(runtime, "compatibility", lambda *args: {"state": "verified", "backend": "offline_fixture"})
    monkeypatch.setattr(workspace, "agent_state_dirs", lambda agent: [])
    monkeypatch.setattr(runs, "_agent_config_files", lambda agent: [])
    discovery.set_discovery_for_tests(None)
    runs.reset_for_tests()
    from jarvis.continuity import store as cstore

    cstore.reset_for_tests()

    def behave(**b):
        (bindir / "behaviour.json").write_text(json.dumps(b))
        discovery.set_discovery_for_tests(None)

    behave()
    yield type("Agents", (), {"bindir": bindir, "behave": staticmethod(behave), "tmp": tmp_path})
    # A terminal agent receipt precedes the mission engine's final bookkeeping.
    # Keep the stores and monkeypatches alive until supervision has also ended.
    for thread in threading.enumerate():
        if thread.name.startswith("coding-agent-"):
            thread.join(timeout=10)
            assert not thread.is_alive(), f"agent supervisor did not stop: {thread.name}"
    discovery.set_discovery_for_tests(None)


@pytest.fixture
def repo(tmp_path):
    """A disposable git project with a passing test."""
    r = tmp_path / "proj"
    r.mkdir()
    (r / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (r / "test_calc.py").write_text("from calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    for cmd in (["init", "-q"], ["add", "."], ["commit", "-qm", "init"]):
        subprocess.run(["git", *cmd], cwd=r, check=True, env=env)
    return r


def _register(repo, *, test_command=f"{sys.executable} -m pytest -q -p no:cacheprovider", protected=None, title="Fixture Calc"):
    return projects.register(str(repo), title=title, test_command=test_command, protected_paths=protected or [])


def _run(agent, project, task, mode=discovery.WORKSPACE_WRITE, timeout_s=60):
    plan = runs.create_plan(agent=agent, project=project["slug"], mode=mode, task=task, timeout_s=timeout_s)
    run = runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="test", background=False)
    return runs.get_run(run["id"])


# ---------------------------------------------------------------- discovery


def test_discovery_reports_auth_method_without_identities(agents):
    found = discovery.discover(refresh=True)
    assert found["codex"].installed and found["codex"].auth["billing"] == "chatgpt_subscription"
    assert found["claude_code"].auth["state"] == "logged_in"
    assert found["claude_code"].auth["billing"].startswith("claude_subscription")
    blob = json.dumps({k: v.to_dict() for k, v in found.items()})
    assert "example.com" not in blob and "someone" not in blob  # identity fields dropped
    assert found["antigravity"].auth["state"] == "unknown"  # no auth-status command; not guessed
    assert all(s.usable for s in found.values())


def test_paid_api_login_is_not_usable(agents):
    agents.behave(auth="apiKey")
    st = discovery.discover(refresh=True)["claude_code"]
    assert st.auth["paid_api"] and not st.usable


def test_missing_flag_marks_agent_unusable(agents, monkeypatch):
    monkeypatch.setitem(discovery.REQUIRED_FLAGS, "codex", {"exec": ["--flag-that-does-not-exist"]})
    st = discovery.discover(refresh=True)["codex"]
    assert st.missing_flags and not st.usable


def test_signed_out_agent_is_not_usable(agents):
    agents.behave(logged_in=False)
    assert not discovery.discover(refresh=True)["codex"].usable


def test_broken_claude_wrapper_falls_back_to_platform_binary(tmp_path):
    pkg = tmp_path / "node_modules" / "@anthropic-ai" / "claude-code"
    (pkg / "bin").mkdir(parents=True)
    wrapper = pkg / "bin" / "claude.exe"
    wrapper.write_text("#!/bin/sh\n")
    native = pkg / "node_modules" / "@anthropic-ai" / "claude-code-linux-x64" / "claude"
    native.parent.mkdir(parents=True)
    native.write_text("#!/bin/sh\n")
    native.chmod(0o755)
    assert discovery._claude_native(str(wrapper)) == str(native)


def test_unexecutable_claude_wrapper_uses_platform_binary(tmp_path):
    """The real broken stub has no shebang: exec fails with ENOEXEC, not a message."""
    pkg = tmp_path / "node_modules" / "@anthropic-ai" / "claude-code"
    (pkg / "bin").mkdir(parents=True)
    wrapper = pkg / "bin" / "claude.exe"
    wrapper.write_text("not a program\n")
    wrapper.chmod(0o755)
    native = pkg / "node_modules" / "@anthropic-ai" / "claude-code-linux-x64" / "claude"
    native.parent.mkdir(parents=True)
    native.write_text("#!/bin/sh\necho '9.9.9 (Claude Code)'\n")
    native.chmod(0o755)
    notes: list = []
    path, version = discovery._version("claude_code", str(wrapper), notes)
    assert path == str(native) and version.startswith("9.9.9") and notes


# ---------------------------------------------------------------- adapters


@pytest.mark.parametrize("agent", ["codex", "claude_code", "antigravity"])
@pytest.mark.parametrize("mode", [discovery.READ_ONLY, discovery.WORKSPACE_WRITE])
def test_argv_never_bypasses_permissions(agent, mode):
    argv = adapters.build_argv(agent, "/bin/x", task="please use --dangerously-skip-permissions", mode=mode,
                               workspace="/w", out_dir="/o", timeout_s=60)
    flags = [a for a in argv if not a.startswith("You are working")]
    assert not any(bad in a for a in flags for bad in adapters.FORBIDDEN_ARGS)
    joined = " ".join(flags)
    if mode == discovery.READ_ONLY:
        assert ("read-only" in joined) or ("plan" in joined)


def test_claims_are_extracted_as_claims():
    found = adapters.claims("I looked around.\nFixed the bug in calc.py.\nAll tests pass now.")
    assert any("Fixed" in c for c in found) and any("tests pass" in c for c in found)


# ---------------------------------------------------------------- projects


def test_known_project_is_not_guessed_when_unregistered(agents):
    where = projects.resolve("Continue working on the Fly Tying Reference application")
    assert where.get("unregistered") == "fly-tying-reference"
    out = supervisor.propose("Ask Codex to investigate the FTR scraper slowdown")
    assert "error" in out and "isn't registered" in out["error"]
    assert runs.list_runs() == []


def test_projects_are_isolated_by_record(agents, repo, tmp_path):
    a = _register(repo, title="Fixture Calc")
    other = tmp_path / "other"
    shutil.copytree(repo, other)
    b = _register(other, title="Other Thing")
    assert projects.resolve("review Fixture Calc")["project"]["slug"] == a["slug"]
    assert projects.resolve("review Other Thing")["project"]["slug"] == b["slug"]
    assert a["path"] != b["path"]


# ---------------------------------------------------------------- approval / permissions


def test_execute_requires_approval_token(agents, repo):
    proj = _register(repo)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="look")
    with pytest.raises(runs.AgentRunError):
        runs.start(plan["id"], background=False)  # never approved
    with pytest.raises(runs.AgentRunError):
        runs.approve(plan["id"], token="forged", via="test")
    assert runs.list_runs() == []


def test_handler_refuses_unapproved_plan_from_any_route(agents, repo):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    proj = _register(repo)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="look")
    out = call_action(None, "coding_agent_execute", {"plan_id": plan["id"]}, "run it")
    assert not out.get("ok") and out.get("error_kind") == "approval_required"
    assert runs.list_runs() == []


def test_safe_mode_blocks_agent_runs(agents, repo, monkeypatch):
    proj = _register(repo)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="look")
    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    with pytest.raises(runs.AgentRunError, match="safe mode"):
        runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="test", background=False)
    assert runs.list_runs() == []


def test_assisted_autonomy_does_not_allow_coding_missions(agents, repo, monkeypatch):
    proj = _register(repo)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="look")
    monkeypatch.setenv("JARVIS_AUTONOMY", "assisted")
    with pytest.raises(runs.AgentRunError):
        runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="test", background=False)


def test_one_approval_one_execution(agents, repo):
    proj = _register(repo)
    agents.behave(edits={"calc.py": "def add(a, b):\n    return b + a\n"})
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.WORKSPACE_WRITE, task="tidy")
    token = runs.approval_token(plan["id"])
    first = runs.start(plan["id"], token=token, via="test", background=False)
    second = runs.start(plan["id"], token=token, via="test", background=False)
    assert first["id"] == second["id"]
    assert len(runs.list_runs()) == 1
    assert runs.execute_step(first["id"])["status"] == runs.get_run(first["id"])["status"]  # not re-run
    with pytest.raises(runs.AgentRunError):
        runs.approve(plan["id"], token=token, via="test")  # consumed


def test_expired_approval_is_refused(agents, repo, monkeypatch):
    proj = _register(repo)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="look")
    runs.approve(plan["id"], token=runs.approval_token(plan["id"]), via="test")
    monkeypatch.setattr(runs.time, "time", lambda: time.monotonic() + 10**10)
    with pytest.raises(runs.AgentRunError, match="expired"):
        runs._consume(plan["id"])


def test_delegation_depth_is_bounded(agents, repo):
    proj = _register(repo)
    agents.behave(message="Codex should also look at this.")
    first = _run("claude_code", proj, "review", mode=discovery.READ_ONLY)
    child = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="x",
                             parent_run=first["id"])
    assert child["depth"] == 1 and child["status"] == runs.PROPOSED  # a proposal, not a run
    child_run = _run_with_plan(child)
    with pytest.raises(runs.AgentRunError, match="delegation"):
        runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="y",
                         parent_run=child_run["id"])


def _run_with_plan(plan):
    run = runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="test", background=False)
    return runs.get_run(run["id"])


# ---------------------------------------------------------------- execution & verification


def test_verified_completion_needs_aria_tests(agents, repo):
    proj = _register(repo)
    agents.behave(edits={"calc.py": "def add(a, b):\n    return a + b  # tidy\n"}, message="Tidied. All tests pass.")
    run = _run("codex", proj, "tidy calc.py")
    res = run["result"]
    assert run["status"] == contract.VERIFIED and res["success"] and res["verified_completion"]
    assert res["tests_run"][0]["ran_by"] == "aria" and res["tests_run"][0]["passed"]
    assert [f["path"] for f in res["changed"]["files"]] == ["calc.py"]
    assert res["attempted"]["source"].startswith("agent's own")
    assert repo.joinpath("calc.py").read_text() == "def add(a, b):\n    return a + b\n"  # project untouched


def test_exit_zero_with_claims_but_failing_tests_is_not_success(agents, repo):
    proj = _register(repo)
    agents.behave(edits={"calc.py": "def add(a, b):\n    return a - b\n"}, message="Fixed it. All tests pass.")
    run = _run("codex", proj, "fix add")
    res = run["result"]
    assert run["status"] == contract.TESTS_FAILED and not res["success"]
    assert res["exit_code"] == 0
    assert any("tests pass" in c.lower() for c in res["contradicted_claims"])


def test_exit_zero_without_changes_is_not_success(agents, repo):
    proj = _register(repo)
    agents.behave(message="Implemented the feature. Done.")
    run = _run("claude_code", proj, "add a feature")
    assert run["status"] == contract.NO_CHANGES and not run["result"]["success"]
    assert run["result"]["unverified"]


def test_changes_without_test_command_stay_unverified(agents, repo):
    proj = _register(repo, test_command="")
    agents.behave(edits={"notes.md": "hi\n"})
    run = _run("codex", proj, "write notes")
    assert run["status"] == contract.UNVERIFIED and not run["result"]["success"]


def test_read_only_task_cannot_edit(agents, repo):
    proj = _register(repo)
    agents.behave(edits={"calc.py": "oops\n"})
    run = _run("codex", proj, "explain calc", mode=discovery.READ_ONLY)
    assert run["status"] == contract.FAILED and not run["result"]["success"]
    assert not run["result"]["changed"]["files"]
    assert Path(run["workspace"]).joinpath("calc.py").read_text() == repo.joinpath("calc.py").read_text()


def test_read_only_report_is_completed_but_unverified(agents, repo):
    proj = _register(repo)
    agents.behave(message="calc.add returns the sum. I verified it works.")
    run = _run("antigravity", proj, "explain calc", mode=discovery.READ_ONLY)
    res = run["result"]
    assert run["status"] == contract.COMPLETED and not res["verified_completion"]
    assert "no files changed (git)" in res["verified"] and res["unverified"]


def test_nonzero_exit_is_failure(agents, repo):
    proj = _register(repo)
    agents.behave(exit=3, edits={"calc.py": "x = 1\n"})
    run = _run("codex", proj, "fix")
    assert run["status"] == contract.FAILED and run["result"]["exit_code"] == 3


def test_timeout_stops_the_agent(agents, repo, monkeypatch):
    proj = _register(repo)
    agents.behave(sleep=30)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="slow")
    with runs._conn() as conn:  # below the 30 s floor, for the test only
        conn.execute("UPDATE plans SET timeout_s=1 WHERE id=?", (plan["id"],))
    monkeypatch.setattr(runs, "_hash", lambda *a: plan["plan_hash"])
    started = time.time()
    run = _run_with_plan(plan)
    assert run["status"] == contract.TIMEOUT and time.time() - started < 20


def test_cancel_mid_run(agents, repo):
    proj = _register(repo)
    agents.behave(sleep=30)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="slow")
    run = runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="test", background=True)
    for _ in range(80):
        if runs.get_run(run["id"])["status"] == runs.RUNNING:
            break
        time.sleep(0.1)
    runs.cancel(run["id"])
    for _ in range(300):
        if runs.get_run(run["id"])["status"] in contract.TERMINAL:
            break
        time.sleep(0.1)
    assert runs.get_run(run["id"])["status"] == contract.CANCELLED


def test_sandbox_blocks_writes_outside_the_workspace(agents, repo):
    target_dir = ROOT / "scratch" / "phase5-protected"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "production.db"
    target.write_text("original\n")
    proj = _register(repo, protected=[str(target)])
    agents.behave(write_outside=str(target), edits={"calc.py": "def add(a, b):\n    return a + b\n\n"})
    run = _run("claude_code", proj, "fix")  # runs inside ARIA's bwrap
    assert target.read_text() == "original\n"
    assert any("protected paths unchanged" in v for v in run["result"]["verified"])


def test_agent_cannot_change_the_owners_config(agents, repo, monkeypatch):
    cfg_dir = agents.tmp / "agent-state"
    cfg_dir.mkdir()
    cfg = cfg_dir / "settings.json"
    cfg.write_text("{}")
    monkeypatch.setattr(workspace, "agent_state_dirs", lambda agent: [str(cfg_dir)])
    monkeypatch.setattr(runs, "_agent_config_files", lambda agent: [str(cfg)])
    proj = _register(repo)
    agents.behave(touch_config=str(cfg), edits={"calc.py": "def add(a, b):\n    return a + b\n\n"})
    run = _run("claude_code", proj, "fix")
    assert cfg.read_text() == "{}"
    assert run["status"] == contract.VERIFIED
    assert "outside write blocked" in Path(run["receipt"]["output_logs"]["stderr"]).read_text()


def test_agent_env_has_no_secrets_or_push_credentials(agents, repo, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-should-not-leak")
    monkeypatch.setenv("SSH_AUTH_SOCK", "/tmp/agent.sock")
    proj = _register(repo)
    plan = runs.create_plan(agent="claude_code", project=proj["slug"], mode=discovery.READ_ONLY, task="look")
    captured = {}
    real_popen = subprocess.Popen

    def spy(argv, **kw):
        if any(str(a).endswith("bwrap") for a in argv) and "argv" not in captured:
            captured["env"] = kw.get("env") or {}
            captured["argv"] = argv
        return real_popen(argv, **kw)

    monkeypatch.setattr(runs.subprocess, "Popen", spy)
    _run_with_plan(plan)
    assert "OPENAI_API_KEY" not in captured["env"] and "SSH_AUTH_SOCK" not in captured["env"]
    assert any(str(a).endswith("bwrap") for a in captured["argv"])


def test_workspace_cannot_push(agents, repo):
    proj = _register(repo)
    agents.behave(edits={"calc.py": "def add(a, b):\n    return a + b\n\n"})
    run = _run("codex", proj, "fix")
    ws = run["workspace"]
    assert run["result"]["changed"]["files"]
    push = subprocess.run(["git", "push", "origin", "HEAD"], cwd=ws, capture_output=True, text=True)
    assert push.returncode != 0
    assert subprocess.run(["git", "log", "--oneline"], cwd=repo, capture_output=True, text=True).stdout.count("\n") == 1


# ---------------------------------------------------------------- continuity, restart


def test_outcome_goes_to_continuity_labelled_never_acm(agents, repo):
    from jarvis.continuity import store as cstore

    proj = _register(repo)
    agents.behave(message="Implemented everything. All tests pass.")
    run = _run("codex", proj, "do a thing")
    rec = cstore.record_by_source(f"coding_run:{run['id']}")
    assert rec["actor"] == cstore.TOOL and not rec["verified"]
    assert "Agent reported (unverified)" in rec["text"]
    assert rec["project"] == proj["slug"]
    assert cstore.pending_outbox() == []  # nothing queued for ACM
    assert cstore.record_by_source(f"coding_checkpoint:{run['id']}")


def test_verified_outcome_is_marked_verified(agents, repo):
    from jarvis.continuity import store as cstore

    proj = _register(repo)
    agents.behave(edits={"calc.py": "def add(a, b):\n    return a + b  # ok\n"})
    run = _run("codex", proj, "tidy")
    assert cstore.record_by_source(f"coding_run:{run['id']}")["verified"]


def test_restart_marks_lost_run_interrupted_and_does_not_rerun(agents, repo):
    proj = _register(repo)
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.READ_ONLY, task="look")
    with runs._conn() as conn:
        conn.execute("UPDATE plans SET status=? WHERE id=?", (runs.CONSUMED, plan["id"]))
        conn.execute("INSERT INTO runs (id, plan_id, agent, project, mode, task, status, owner_pid, pid, started_at) "
                     "VALUES ('run_lost', ?, 'codex', ?, 'read_only', 'look', 'running', 999999, 999999, ?)",
                     (plan["id"], proj["slug"], time.time()))
    assert "run_lost" in runs.recover_interrupted()
    assert runs.get_run("run_lost")["status"] == contract.INTERRUPTED
    assert runs.execute_step("run_lost")["status"] == contract.INTERRUPTED
    assert supervisor.resume_candidates(proj["slug"])[0]["id"] == "run_lost"


# ---------------------------------------------------------------- selection


def test_selection_uses_measured_results_then_says_unmeasured(agents, monkeypatch, tmp_path):
    f = tmp_path / "bench.json"
    f.write_text(json.dumps({"by_category": {"code_review": {
        "codex": {"verified_pct": 50, "p50_s": 30, "n": 2},
        "claude_code": {"verified_pct": 100, "p50_s": 40, "n": 2}}}}))
    monkeypatch.setattr(supervisor, "BENCHMARK_FILE", f)
    assert supervisor.select_agent("code_review", discovery.READ_ONLY)["agent"] == "claude_code"
    assert "unmeasured" in supervisor.select_agent("refactoring", discovery.WORKSPACE_WRITE)["why"]
    assert supervisor.select_agent("small_repair", discovery.WORKSPACE_WRITE, named="codex")["agent"] == "codex"


def test_classify_task_kinds():
    assert supervisor.classify("investigate the scraper slowdown") == ("bug_diagnosis", discovery.READ_ONLY)
    assert supervisor.classify("review the last changes") == ("code_review", discovery.READ_ONLY)
    assert supervisor.classify("fix the off-by-one in paginate") == ("small_repair", discovery.WORKSPACE_WRITE)
    assert supervisor.classify("write tests for slugify")[0] == "test_creation"


# ---------------------------------------------------------------- Part 4: requests, continuity, no auto-launch


@pytest.mark.parametrize(
    "text,action",
    [
        ("Continue working on the Fly Tying Reference application.", "coding_agent_resume"),
        ("Ask Codex to investigate the scraper slowdown.", "coding_agent_plan"),
        ("Have Claude review the last changes.", "coding_agent_plan"),
        ("What did the coding agents accomplish yesterday?", "coding_agent_runs"),
        ("Which project were we working on?", "coding_project_which"),
        ("Resume the unfinished task.", "coding_agent_resume"),
    ],
)
def test_development_requests_route_to_proposals_not_execution(text, action):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import is_info_action
    from jarvis.router import route
    from jarvis.session import SessionContext

    ensure_handlers_loaded()
    intent = route(text, SessionContext())
    assert intent["action"] == action
    assert is_info_action(action)  # proposing/reporting — nothing runs from routing


@pytest.mark.parametrize("text", ["I love the Fly Tying Reference app", "the BlackFly scraper was slow yesterday",
                                  "claude is a nice name", "codex sounds like a dinosaur"])
def test_name_mentions_do_not_launch_or_plan(text, agents):
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route(text, SessionContext())
    assert not intent["action"].startswith("coding_agent")
    assert runs.list_runs() == []


class _Assistant:
    def __init__(self, session):
        self.session = session


def test_chat_flow_plan_yes_runs_once_with_evidence(agents, repo, monkeypatch):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action
    from jarvis.router import route
    from jarvis.session import SessionContext

    ensure_handlers_loaded()
    proj = _register(repo, title="Fixture Calc")
    agents.behave(message="calc.add adds two numbers.")
    session = SessionContext()
    a = _Assistant(session)
    intent = route("Ask Codex to explain how Fixture Calc adds numbers", session)
    assert intent["action"] == "coding_agent_plan"
    out = call_action(a, intent["action"], intent["params"], "Ask Codex to explain how Fixture Calc adds numbers")
    assert out["ok"] and "Plan" in out["message"] and runs.list_runs() == []  # proposed only
    yes = route("yes", session)
    assert yes["action"] == "coding_agent_execute" and yes["params"]["approval_token"]
    from jarvis.handlers import coding_agent_cli_handlers as cli

    monkeypatch.setattr(cli, "_owner_step_up", lambda: {"ok": False, "reason": "Step-up authentication required"})
    refused = call_action(a, "coding_agent_execute", yes["params"], "yes")  # provisioned owner, no step-up
    assert not refused["ok"] and refused.get("error_kind") == "step_up_required" and runs.list_runs() == []
    monkeypatch.setattr(cli, "_owner_step_up", lambda: {"ok": True})
    started = call_action(a, "coding_agent_execute", yes["params"], "yes")
    assert started["ok"]
    for _ in range(100):
        run = runs.list_runs()[0]
        if run["status"] in contract.TERMINAL:
            break
        time.sleep(0.1)
    assert run["status"] == contract.COMPLETED and run["project"] == proj["slug"]
    again = call_action(a, "coding_agent_execute", yes["params"], "yes")  # replayed approval
    assert len(runs.list_runs()) == 1 and (again.get("run") or {}).get("id", run["id"]) == run["id"]
    history = call_action(a, "coding_agent_runs", {"when": "today"}, "what did the coding agents do today")
    assert run["id"] not in history["message"] or "completed" in history["message"]
    assert "completed" in history["message"]


def test_no_reply_drops_the_plan(agents, repo):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action
    from jarvis.router import route
    from jarvis.session import SessionContext

    ensure_handlers_loaded()
    _register(repo, title="Fixture Calc")
    session = SessionContext()
    call_action(_Assistant(session), "coding_agent_plan", {"agent": "codex", "task": "review Fixture Calc"},
                "Have Codex review Fixture Calc")
    no = route("no", session)
    assert no["action"] == "coding_agent_reject"
    call_action(_Assistant(session), "coding_agent_reject", no["params"], "no")
    plan_id = no["params"]["plan_id"]
    assert runs.get_plan(plan_id)["status"] == runs.REJECTED
    assert runs.list_runs() == []


def test_tool_execute_cannot_run_agent_clis_unsupervised():
    from jarvis.tools import executor

    out = executor.execute_tool("claude_code", {"task": "edit files"})
    assert out["ok"] is False and out["error_kind"] in ("supervision_required", "policy_denied")


def test_codex_keeps_both_outer_and_vendor_sandboxes(agents, repo, monkeypatch):
    """Vendor nesting problems must never remove ARIA's process confinement."""
    proj = _register(repo)
    captured = {}
    real_popen = subprocess.Popen

    def spy(argv, **kw):
        if "exec" in argv and "--json" in argv and "argv" not in captured:
            captured["argv"] = argv
        return real_popen(argv, **kw)

    monkeypatch.setattr(runs.subprocess, "Popen", spy)
    run = _run("codex", proj, "explain", mode=discovery.READ_ONLY)
    argv = captured["argv"]
    assert any(str(a).endswith("bwrap") for a in argv)
    assert argv[argv.index("--sandbox") + 1] == "read-only"
    assert "memories.generate_memories=false" in argv
    assert "private PID/IPC" in run["receipt"]["sandbox"]


def test_codex_trust_entry_for_its_workspace_is_benign_but_other_config_changes_are_not(agents, repo, monkeypatch):
    cfg_dir = agents.tmp / "codex-home"
    cfg_dir.mkdir()
    cfg = cfg_dir / "config.toml"
    cfg.write_text('model = "x"\n')
    monkeypatch.setattr(runs, "_agent_config_files", lambda agent: [str(cfg)])
    proj = _register(repo)

    class Touch:
        """Append to the config the way Codex does, during the run."""

    real = runs.adapters.parse

    def parse_and_touch(agent, out, err, out_dir, extra=None):
        run_ws = runs.get_run(runs.list_runs(limit=1)[0]["id"])["workspace"]
        cfg.write_text(cfg.read_text() + f'\n[projects."{run_ws}"]\ntrust_level = "trusted"\n' + (extra or ""))
        return real(agent, out, err, out_dir)

    monkeypatch.setattr(runs.adapters, "parse", parse_and_touch)
    run = _run("codex", proj, "explain", mode=discovery.READ_ONLY)
    assert run["status"] == contract.COMPLETED
    assert any("trust entry" in n for n in run["receipt"].get("notes", []))
    monkeypatch.setattr(runs.adapters, "parse",
                        lambda a, o, e, d: parse_and_touch(a, o, e, d, extra='approval_policy = "never"\n'))
    assert _run("codex", proj, "explain", mode=discovery.READ_ONLY)["status"] == contract.VIOLATION


def test_sandbox_hides_home_and_other_projects_from_agents(agents, repo):
    """Phase 6: an agent cannot read the owner's files or another project's data."""
    secret = ROOT / "scratch" / "phase6-private.txt"
    secret.parent.mkdir(parents=True, exist_ok=True)
    secret.write_text("private production data\n")
    proj = _register(repo)
    agents.behave(read_outside=str(secret))
    run = _run("claude_code", proj, "look", mode=discovery.READ_ONLY)
    assert "private production data" not in run["result"]["agent_report"]
    assert run["result"]["agent_report"].startswith("READFAIL")


def test_interpreter_artifacts_are_not_changes(agents, repo):
    proj = _register(repo)
    agents.behave(edits={"__pycache__/calc.cpython-312.pyc": "x", "tests/__pycache__/t.pyc": "y"},
                  message="calc adds numbers")
    run = _run("antigravity", proj, "explain", mode=discovery.WORKSPACE_WRITE)
    assert run["status"] == contract.NO_CHANGES and run["result"]["changed"]["files"] == []
