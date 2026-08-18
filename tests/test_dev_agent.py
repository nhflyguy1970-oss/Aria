"""Coding Agent — workspace safety, command policy, development loop, recovery."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from jarvis import missions
from jarvis import specialized_agents as agents
from jarvis.dev_agent import commands, engine, store, workspace
from jarvis.dev_agent.editors import static_editor
from jarvis.missions import store as mstore
from jarvis.specialized_agents import definitions, registry

REPO_ROOT = Path(__file__).resolve().parents[1]

PASSING_TEST = "def test_ok():\n    assert True\n"
FAILING_TEST = "def test_broken():\n    assert False\n"
TARGET_SRC = "def add(a, b):\n    return a + b\n"
TARGET_TEST = "from mod import add\n\ndef test_add():\n    assert add(2, 2) == 4\n"


@pytest.fixture(autouse=True)
def _clean():
    registry.reset()
    yield
    registry.reset()


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=30)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """A small deterministic git repository — never ARIA's own tree."""
    repo = tmp_path / "fixture_repo"
    repo.mkdir()
    (repo / "mod.py").write_text("def add(a, b):\n    return 0\n", encoding="utf-8")
    (repo / "test_mod.py").write_text(TARGET_TEST, encoding="utf-8")
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@example.com"], repo)
    _git(["config", "user.name", "T"], repo)
    _git(["add", "."], repo)
    _git(["commit", "-qm", "initial"], repo)
    return repo


def _ws(repo: Path) -> workspace.Workspace:
    return workspace.open_workspace(repo)


# ------------------------------------------------------------- workspace


def test_workspace_opens_and_snapshots_state(data_dir: Path, fixture_repo: Path):
    ws = _ws(fixture_repo)
    state = workspace.repo_state(ws)
    assert state["is_repo"] is True
    assert state["head"]
    assert state["dirty"] == []


def test_path_escape_denied(data_dir: Path, fixture_repo: Path):
    ws = _ws(fixture_repo)
    for bad in ("../outside.py", "../../etc/passwd", "/etc/passwd"):
        with pytest.raises(workspace.PathEscape):
            ws.resolve(bad)


def test_symlink_escape_denied(data_dir: Path, fixture_repo: Path, tmp_path: Path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    (fixture_repo / "link.txt").symlink_to(outside)
    ws = _ws(fixture_repo)
    with pytest.raises(workspace.PathEscape):
        ws.resolve("link.txt")


def test_write_and_read_inside_workspace(data_dir: Path, fixture_repo: Path):
    ws = _ws(fixture_repo)
    info = ws.write("new/file.py", "x = 1\n")
    assert info["created"] is True
    assert ws.read("new/file.py") == "x = 1\n"


def test_write_outside_workspace_denied(data_dir: Path, fixture_repo: Path):
    ws = _ws(fixture_repo)
    with pytest.raises(workspace.PathEscape):
        ws.write("../escaped.py", "bad")


def test_delete_refuses_user_modified_file(data_dir: Path, fixture_repo: Path):
    (fixture_repo / "mod.py").write_text("user edit\n", encoding="utf-8")
    ws = _ws(fixture_repo)
    assert "mod.py" in ws.baseline_dirty
    with pytest.raises(workspace.WorkspaceError, match="user had modified"):
        ws.delete("mod.py")


def test_unrelated_changes_preserved_detection(data_dir: Path, fixture_repo: Path):
    (fixture_repo / "mod.py").write_text("user edit\n", encoding="utf-8")
    ws = _ws(fixture_repo)
    assert workspace.unrelated_changes_preserved(ws)["preserved"] is True
    _git(["checkout", "--", "mod.py"], fixture_repo)
    result = workspace.unrelated_changes_preserved(ws)
    assert result["preserved"] is False
    assert "mod.py" in result["lost"]


# --------------------------------------------------------- command policy


@pytest.mark.parametrize("argv", [["git", "status"], ["git", "diff"], ["ls"], ["cat", "x"]])
def test_read_only_commands(data_dir: Path, argv):
    assert commands.classify(argv) == commands.READ_ONLY


@pytest.mark.parametrize(
    "argv", [["pytest", "-q"], ["ruff", "check"], ["git", "commit", "-m", "x"]]
)
def test_development_commands(data_dir: Path, argv):
    assert commands.classify(argv) == commands.DEVELOPMENT


@pytest.mark.parametrize(
    "argv",
    [
        ["rm", "-rf", "/"],
        ["sudo", "ls"],
        ["systemctl", "restart", "x"],
        ["curl", "http://x"],
        ["bash", "-c", "rm -rf /"],
        ["pip", "install", "x"],
        ["docker", "ps"],
        ["chmod", "777", "/"],
    ],
)
def test_forbidden_binaries_denied(data_dir: Path, argv):
    with pytest.raises(commands.CommandDenied):
        commands.classify(argv)


@pytest.mark.parametrize(
    "argv",
    [
        ["git", "push"],
        ["git", "reset", "--hard"],
        ["git", "clean", "-fd"],
        ["git", "rebase", "main"],
        ["git", "gc"],
        ["git", "remote", "add", "x", "y"],
    ],
)
def test_high_impact_git_denied(data_dir: Path, argv):
    with pytest.raises(commands.CommandDenied):
        commands.classify(argv)


def test_forced_git_flags_denied(data_dir: Path):
    with pytest.raises(commands.CommandDenied, match="Forced"):
        commands.classify(["git", "checkout", "--force", "main"])


def test_unknown_binary_denied(data_dir: Path):
    with pytest.raises(commands.CommandDenied, match="allowlist"):
        commands.classify(["mysteriousbinary"])


def test_command_runs_inside_workspace(data_dir: Path, fixture_repo: Path):
    ws = _ws(fixture_repo)
    out = commands.run(["git", "status", "--porcelain"], ws)
    assert out["ok"] is True and out["impact"] == commands.READ_ONLY


def test_command_timeout_bounded(data_dir: Path, fixture_repo: Path):
    ws = _ws(fixture_repo)
    out = commands.run(["python3", "-c", "import time; time.sleep(5)"], ws, timeout_s=1)
    assert out["ok"] is False and out["error_kind"] == "timeout"


def test_command_cancellation(data_dir: Path, fixture_repo: Path):
    ws = _ws(fixture_repo)
    out = commands.run(["pytest", "-q"], ws, cancel_check=lambda: True)
    assert out["ok"] is False and out["error_kind"] == "cancelled"


def test_test_output_parsing(data_dir: Path):
    s = commands.parse_test_output("FAILED tests/test_a.py::test_x\n1 failed, 3 passed in 1s")
    assert s == {
        "passed": 3,
        "failed": 1,
        "errors": 0,
        "failing_tests": ["tests/test_a.py::test_x"],
        "green": False,
    }
    assert commands.parse_test_output("5 passed in 1s")["green"] is True


# ---------------------------------------------------------- task lifecycle


def test_task_creation_persists(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("make tests pass", str(fixture_repo))
    assert task["phase"] == store.PENDING
    assert store.get(task["id"])["objective"] == "make tests pass"
    assert store.DB_PATH.is_file()


def test_task_store_isolated(data_dir: Path):
    assert data_dir in store.DB_PATH.resolve().parents


def test_empty_objective_rejected(data_dir: Path, fixture_repo: Path):
    with pytest.raises(engine.CodingAgentError):
        engine.create_task("  ", str(fixture_repo))


def test_missing_workspace_rejected(data_dir: Path, tmp_path: Path):
    with pytest.raises(workspace.WorkspaceError):
        engine.create_task("x", str(tmp_path / "nope"))


def test_illegal_phase_transition_rejected(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("x", str(fixture_repo))
    store.set_phase(task["id"], store.PLANNING)
    with pytest.raises(store.CodingTaskError, match="Illegal"):
        store.set_phase(task["id"], store.COMPLETED)


def test_workspace_lock_prevents_second_task(data_dir: Path, fixture_repo: Path):
    engine.create_task("first", str(fixture_repo))
    with pytest.raises(engine.CodingAgentError, match="active coding task"):
        engine.create_task("second", str(fixture_repo))


def test_lock_released_on_cancel(data_dir: Path, fixture_repo: Path):
    t1 = engine.create_task("first", str(fixture_repo))
    engine.cancel(t1["id"])
    t2 = engine.create_task("second", str(fixture_repo))
    assert t2["id"] != t1["id"]


def test_independent_repos_do_not_conflict(data_dir: Path, fixture_repo: Path, tmp_path: Path):
    other = tmp_path / "other_repo"
    other.mkdir()
    _git(["init", "-q"], other)
    a = engine.create_task("a", str(fixture_repo))
    b = engine.create_task("b", str(other))
    assert a["workspace"] != b["workspace"]
    assert store.lock_holder(a["workspace"]) == a["id"]
    assert store.lock_holder(b["workspace"]) == b["id"]


# ------------------------------------------------------------ the loop


def test_scenario_a_simple_task_succeeds(data_dir: Path, fixture_repo: Path):
    """A: fix the fixture so its tests pass."""
    task = engine.create_task("make add() correct", str(fixture_repo))
    editor = static_editor([{"path": "mod.py", "content": TARGET_SRC}], "fix add")
    out = engine.run_loop(task["id"], editor, ["pytest", "-q"])
    final = out["task"]
    assert final["phase"] == store.COMPLETED, final
    assert final["last_test"]["green"] is True
    assert "mod.py" in final["files_changed"]


def test_scenario_b_failure_then_fix(data_dir: Path, fixture_repo: Path):
    """B: first attempt fails, second fixes it."""
    task = engine.create_task("iterative fix", str(fixture_repo))
    attempts = {"n": 0}

    def editor(t, ws, ctx):
        attempts["n"] += 1
        content = TARGET_SRC if attempts["n"] >= 2 else "def add(a, b):\n    return a - b\n"
        return {
            "files": [{"path": "mod.py", "content": content}],
            "summary": f"try {attempts['n']}",
        }

    out = engine.run_loop(task["id"], editor, ["pytest", "-q"])
    assert out["task"]["phase"] == store.COMPLETED
    assert attempts["n"] >= 2, "agent did not iterate after a failure"
    assert out["task"]["test_runs"] >= 2


def test_scenario_c_pre_existing_failure_not_blamed(data_dir: Path, fixture_repo: Path):
    """C: a failure that existed before must not be reported as caused by the task."""
    (fixture_repo / "test_broken.py").write_text(FAILING_TEST, encoding="utf-8")
    _git(["add", "."], fixture_repo)
    _git(["commit", "-qm", "add broken test"], fixture_repo)

    task = engine.create_task("fix add only", str(fixture_repo))
    engine.phase_plan(task["id"])
    engine.phase_inspect(task["id"], test_cmd=["pytest", "-q"])
    baseline = store.get(task["id"])["baseline_failures"]
    assert any("test_broken" in f for f in baseline), baseline

    engine.phase_implement(task["id"], static_editor([{"path": "mod.py", "content": TARGET_SRC}]))
    engine.phase_test(task["id"], ["pytest", "-q"])
    diagnosis = engine.phase_diagnose(task["id"])
    assert diagnosis["verdict"] == "pre_existing"
    assert diagnosis["caused_by_task"] == []


def test_scenario_d_unrelated_work_preserved(data_dir: Path, fixture_repo: Path):
    """D: the user's own edits survive the coding task."""
    (fixture_repo / "user_notes.txt").write_text("user work\n", encoding="utf-8")
    task = engine.create_task("fix add", str(fixture_repo))
    engine.run_loop(
        task["id"], static_editor([{"path": "mod.py", "content": TARGET_SRC}]), ["pytest", "-q"]
    )
    assert (fixture_repo / "user_notes.txt").read_text() == "user work\n"
    ws = workspace.open_workspace(fixture_repo)
    assert "user_notes.txt" in "\n".join(workspace.dirty_files(ws.root))


def test_scenario_e_editor_cannot_escape_workspace(data_dir: Path, fixture_repo: Path):
    """E: a model proposing an outside path is refused."""
    task = engine.create_task("escape attempt", str(fixture_repo))
    editor = static_editor([{"path": "../../escaped.py", "content": "bad"}])
    with pytest.raises(workspace.PathEscape):
        engine.phase_implement(task["id"], editor)


def test_completion_refused_without_passing_tests(data_dir: Path, fixture_repo: Path):
    """The central rule: no green tests, no completion."""
    task = engine.create_task("never fixed", str(fixture_repo))
    engine.phase_plan(task["id"])
    engine.phase_inspect(task["id"], test_cmd=["pytest", "-q"])
    engine.phase_implement(
        task["id"], static_editor([{"path": "mod.py", "content": "def add(a,b):\n    return 0\n"}])
    )
    engine.phase_test(task["id"], ["pytest", "-q"])
    review = engine.phase_review(task["id"])
    final = engine.complete(task["id"], review)
    assert final["phase"] == store.FAILED
    assert "did not pass" in (final["error"] or "")


def test_bounded_iterations(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("never converges", str(fixture_repo))
    editor = static_editor([{"path": "mod.py", "content": "def add(a,b):\n    return 0\n"}])
    out = engine.run_loop(task["id"], editor, ["pytest", "-q"], max_iterations=2)
    assert out["task"]["phase"] == store.BOUNDED
    assert "max_iterations" in out["task"]["stop_reason"]


def test_scenario_g_cancellation_preserves_state(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("cancel me", str(fixture_repo))
    engine.phase_plan(task["id"])
    engine.phase_inspect(task["id"])
    final = engine.cancel(task["id"])
    assert final["phase"] == store.CANCELLED
    assert final["plan"], "plan lost on cancel"
    assert store.lock_holder(final["workspace"]) == ""


def test_loop_cancellation_midway(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("cancel loop", str(fixture_repo))
    out = engine.run_loop(
        task["id"],
        static_editor([{"path": "mod.py", "content": TARGET_SRC}]),
        ["pytest", "-q"],
        cancel_check=lambda: True,
    )
    assert out["cancelled"] is True
    assert out["task"]["phase"] == store.CANCELLED


def test_scenario_j_commit_only_task_files(data_dir: Path, fixture_repo: Path):
    """J: the commit contains the task's file and not the user's unrelated edit."""
    (fixture_repo / "user_notes.txt").write_text("user work\n", encoding="utf-8")
    task = engine.create_task("fix add", str(fixture_repo))
    engine.run_loop(
        task["id"], static_editor([{"path": "mod.py", "content": TARGET_SRC}]), ["pytest", "-q"]
    )
    result = engine.commit_task(task["id"], "fix add")
    assert result["ok"] is True and result["commit"]
    show = _git(["show", "--name-only", "--format=", "HEAD"], fixture_repo).stdout
    assert "mod.py" in show
    assert "user_notes.txt" not in show, "commit swept up unrelated user work"
    assert (fixture_repo / "user_notes.txt").exists()


# ---------------------------------------------------------- permissions


def test_scenario_k_permissions(data_dir: Path):
    assert agents.get("coding_specialist").permits("dev_task_run") is True
    assert agents.get("coding_specialist").permits("dev_command") is True
    assert agents.get("coding_specialist").permits("dev_deploy") is False
    for aid in ("research_specialist", "analysis_specialist", "general_specialist"):
        assert agents.get(aid).permits("dev_task_run") is False, aid
        assert agents.get(aid).permits("dev_command") is False, aid


def test_unauthorized_specialist_denied_via_invoke(data_dir: Path, fixture_repo: Path):
    out = agents.invoke("general_specialist", "run coding", action="dev_task_run")
    assert out["ok"] is False and out["error_kind"] == "permission_denied"


def test_coding_specialist_has_no_browser_authority(data_dir: Path):
    """Coding authority must not quietly become browsing authority (M8 rule)."""
    coder = agents.get("coding_specialist")
    assert coder.permits("browser_use_high_impact") is False
    assert coder.permits("browser_use_interact") is False
    assert coder.permits("browser_use_read") is False


# ------------------------------------------------------ mission integration


def _runner():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    return lambda step, ctx: call_action(None, step["action"], step["params"], "")


def test_mission_backed_coding_task(data_dir: Path, fixture_repo: Path, monkeypatch):
    from jarvis.dev_agent import editors

    monkeypatch.setattr(
        editors,
        "model_editor",
        lambda assistant=None: static_editor([{"path": "mod.py", "content": TARGET_SRC}], "fix"),
    )
    task = engine.create_task("mission coding", str(fixture_repo), create_mission=True)
    mid = store.get(task["id"])["mission_id"]
    assert mid
    missions.run(mid, _runner())
    assert missions.get(mid)["state"] == mstore.COMPLETED
    assert len(mstore.checkpoints(mid)) == 5
    assert store.get(task["id"])["phase"] == store.COMPLETED


def test_mission_coding_task_cancellation(data_dir: Path, fixture_repo: Path, monkeypatch):
    from jarvis.dev_agent import editors

    monkeypatch.setattr(
        editors,
        "model_editor",
        lambda assistant=None: static_editor([{"path": "mod.py", "content": TARGET_SRC}]),
    )
    task = engine.create_task("cancel mission coding", str(fixture_repo), create_mission=True)
    mid = store.get(task["id"])["mission_id"]
    missions.cancel(mid)
    assert missions.get(mid)["state"] == mstore.CANCELLED
    engine.cancel(task["id"])
    assert store.get(task["id"])["phase"] == store.CANCELLED


def test_recovery_moves_interrupted_task_to_paused(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("interrupted", str(fixture_repo))
    store.set_phase(task["id"], store.PLANNING)
    store.set_phase(task["id"], store.IMPLEMENTING)
    assert task["id"] in engine.recover()
    recovered = store.get(task["id"])
    assert recovered["phase"] == store.PAUSED
    assert "interrupt" in (recovered["stop_reason"] or "")


# ------------------------------------------------------------ observability


def test_status_snapshot(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("observe", str(fixture_repo))
    engine.run_loop(
        task["id"], static_editor([{"path": "mod.py", "content": TARGET_SRC}]), ["pytest", "-q"]
    )
    snap = engine.status(task["id"])
    for key in (
        "task_id",
        "objective",
        "workspace",
        "branch",
        "phase",
        "plan",
        "iterations",
        "test_runs",
        "files_changed",
        "last_test",
        "bounds",
        "elapsed_s",
        "model",
    ):
        assert key in snap, key
    assert snap["phase"] == store.COMPLETED


def test_events_recorded(data_dir: Path, fixture_repo: Path):
    task = engine.create_task("events", str(fixture_repo))
    engine.run_loop(
        task["id"], static_editor([{"path": "mod.py", "content": TARGET_SRC}]), ["pytest", "-q"]
    )
    kinds = [e["kind"] for e in store.events(task["id"])]
    for expected in ("created", "plan", "inspect", "implement", "test", "review"):
        assert expected in kinds, expected


def test_results_survive_module_reload(data_dir: Path, fixture_repo: Path):
    import importlib

    task = engine.create_task("durable", str(fixture_repo))
    engine.run_loop(
        task["id"], static_editor([{"path": "mod.py", "content": TARGET_SRC}]), ["pytest", "-q"]
    )
    importlib.reload(store)
    importlib.reload(importlib.import_module("jarvis.dev_agent"))
    reloaded = store.get(task["id"])
    assert reloaded["phase"] == store.COMPLETED
    assert reloaded["result"]["completed"] is True


# --------------------------------------------------------------- handlers


def test_dev_actions_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {s["action"] for s in all_actions()}
    for action in (
        "dev_task_create",
        "dev_task_status",
        "dev_task_list",
        "dev_task_run",
        "dev_task_commit",
        "dev_task_cancel",
        "dev_task_recover",
        "dev_command",
        "dev_step",
    ):
        assert action in names, action


def test_handler_round_trip(data_dir: Path, fixture_repo: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    created = call_action(
        None, "dev_task_create", {"objective": "handler task", "workspace": str(fixture_repo)}, ""
    )
    assert created["ok"] is True
    tid = created["task_id"]

    status = call_action(None, "dev_task_status", {"task_id": tid}, "")
    assert status["ok"] is True and status["task"]["objective"] == "handler task"

    listed = call_action(None, "dev_task_list", {}, "")
    assert any(t["id"] == tid for t in listed["tasks"])

    cmd = call_action(None, "dev_command", {"task_id": tid, "argv": ["git", "status"]}, "")
    assert cmd["ok"] is True

    denied = call_action(None, "dev_command", {"task_id": tid, "argv": ["rm", "-rf", "/"]}, "")
    assert denied["ok"] is False and denied["error_kind"] == "command_denied"

    cancelled = call_action(None, "dev_task_cancel", {"task_id": tid}, "")
    assert cancelled["ok"] is True


def test_scenario_f_dangerous_command_denied_via_handler(data_dir: Path, fixture_repo: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    created = call_action(
        None, "dev_task_create", {"objective": "danger", "workspace": str(fixture_repo)}, ""
    )
    for argv in (["git", "push"], ["git", "reset", "--hard"], ["sudo", "rm", "-rf", "/"]):
        out = call_action(None, "dev_command", {"task_id": created["task_id"], "argv": argv}, "")
        assert out["ok"] is False, argv
        assert out["error_kind"] == "command_denied"


# ------------------------------------------------- research/evidence/browser


def test_scenario_l_research_evidence_provenance(data_dir: Path, fixture_repo: Path):
    """L: a coding task uses the existing evidence layer and keeps provenance."""
    from jarvis import evidence as ev

    task = engine.create_task("research-backed change", str(fixture_repo))
    ctx = task["id"]
    claim = ev.add_claim("the API returns a list", context_id=ctx)
    src = ev.add_source("https://nasa.gov/api-docs", context_id=ctx)
    ev.mark_source_inspected(src)
    eid = ev.add_evidence(
        src, "the endpoint returns a list", context_id=ctx, evidence_type=ev.FULL_TEXT
    )
    ev.link(claim, eid, ev.SUPPORTS)
    prov = ev.provenance(claim)
    assert prov["chain"][0]["source"]["access_state"] == ev.INSPECTED
    assert prov["claim"]["context_id"] == task["id"]


def test_scenario_m_browser_uses_isolated_state(data_dir: Path, fixture_repo: Path):
    """M: coding-side browser work stays in the isolated test root."""
    from jarvis import computer_use as cu

    task = engine.create_task("browser-assisted", str(fixture_repo))
    session = cu.open_session(owner="coding_specialist", task_id=task["id"])
    assert session["owner"] == "coding_specialist"
    # Coding authority is not browsing authority: even a read-only navigate is
    # refused, so a coding task cannot reach the network through the browser.
    assert cu.agent_may("coding_specialist", "navigate") is False
    assert cu.agent_may("coding_specialist", "click") is False
    from jarvis.computer_use import retention

    assert data_dir in retention.screenshot_dir().resolve().parents


# ----------------------------------------------------------- crash recovery

_CRASH = """
import os, sys
sys.path.insert(0, {repo!r})
os.environ["JARVIS_DATA_DIR"] = {data_dir!r}
from unittest.mock import MagicMock
sys.modules.setdefault("ollama", MagicMock())

from jarvis.dev_agent import engine, store
from jarvis.dev_agent.editors import static_editor

tid = {tid!r}
engine.phase_plan(tid)
engine.phase_inspect(tid, test_cmd=["pytest", "-q"])
engine.phase_implement(tid, static_editor([{{"path": "mod.py", "content": {src!r}}}], "crash fix"))
assert store.get(tid)["files_changed"] == ["mod.py"]
# Durable progress written. Die before testing/review.
os._exit(9)
"""


def test_scenario_h_crash_recovery(data_dir: Path, fixture_repo: Path, tmp_path: Path):
    task = engine.create_task("crash task", str(fixture_repo))
    script = tmp_path / "crash_dev.py"
    script.write_text(
        textwrap.dedent(_CRASH).format(
            repo=str(REPO_ROOT), data_dir=str(data_dir), tid=task["id"], src=TARGET_SRC
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["JARVIS_DATA_DIR"] = str(data_dir)
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=180, env=env
    )
    assert proc.returncode == 9, f"child did not crash: {proc.stderr[-1500:]}"

    # Durable state survived, and the task did not claim success.
    survived = store.get(task["id"])
    assert survived["plan"], "plan lost in crash"
    assert survived["files_changed"] == ["mod.py"]
    assert survived["phase"] == store.IMPLEMENTING
    assert survived["result"] is None
    assert (fixture_repo / "mod.py").read_text() == TARGET_SRC

    # Recovery parks it safely, then it resumes without redoing the edit.
    assert task["id"] in engine.recover()
    assert store.get(task["id"])["phase"] == store.PAUSED
    store.set_phase(task["id"], store.TESTING)
    engine.phase_test(task["id"], ["pytest", "-q"])
    review = engine.phase_review(task["id"])
    final = engine.complete(task["id"], review)
    assert final["phase"] == store.COMPLETED
    assert final["files_changed"] == ["mod.py"], "recovery duplicated work"


# --------------------------------------------- live-only defects (regression)


def _fake_llm(monkeypatch, items, explanation="fixed"):
    from jarvis import llm

    calls = {}

    def fake(task, *, path, content, context="", errors=None):
        calls.update(task=task, path=path, content=content, errors=errors)
        return explanation, items

    monkeypatch.setattr(llm, "generate_patched_edit", fake)
    return calls


def test_model_editor_applies_the_models_change(data_dir: Path, fixture_repo: Path, monkeypatch):
    """Regression: the production editor silently produced nothing.

    It drove CodingAgent.diagnose(""), where the empty path resolves to the
    workspace directory (Errno 21) and diagnose() never returns files by
    design, then read each proposal under "content" while the edit primitive
    returns it under "code".
    """
    from jarvis.dev_agent import editors

    calls = _fake_llm(monkeypatch, [{"path": "mod.py", "code": TARGET_SRC}])
    task = engine.create_task("fix add", str(fixture_repo))
    engine.phase_plan(task["id"])
    engine.phase_inspect(task["id"], test_cmd=["pytest", "-q"])
    out = engine.phase_implement(task["id"], editors.model_editor())

    assert out["files_written"], "model edit was silently dropped"
    assert "editor_error" not in out
    assert (fixture_repo / "mod.py").read_text() == TARGET_SRC
    # Aimed at the module under test, and grounded in the real failure.
    assert calls["path"] == "mod.py"
    assert "test_add" in calls["task"]


def test_model_editor_refuses_to_edit_the_failing_test(
    data_dir: Path, fixture_repo: Path, monkeypatch
):
    """A red test must not be 'fixed' by rewriting the test."""
    from jarvis.dev_agent import editors

    _fake_llm(monkeypatch, [{"path": "test_mod.py", "code": "def test_add():\n    pass\n"}])
    task = engine.create_task("make add correct", str(fixture_repo))
    before = (fixture_repo / "test_mod.py").read_text()
    out = engine.phase_implement(task["id"], editors.model_editor())

    assert out["files_written"] == []
    assert (fixture_repo / "test_mod.py").read_text() == before
    assert "refused" in out["summary"]


def test_editor_failure_is_reported_not_swallowed(data_dir: Path, fixture_repo: Path, monkeypatch):
    """Regression: an editor exception was reported as a successful phase."""
    from jarvis import llm
    from jarvis.dev_agent import editors

    def boom(*a, **k):
        raise OSError(21, "Is a directory")

    monkeypatch.setattr(llm, "generate_patched_edit", boom)
    task = engine.create_task("fix add", str(fixture_repo))
    out = engine.phase_implement(task["id"], editors.model_editor())
    assert out["editor_error"], "editor failure was swallowed"
    assert "Is a directory" in out["editor_error"]

    # And the loop must stop on it instead of burning every iteration.
    engine.cancel(task["id"])  # release the workspace lock first
    task2 = engine.create_task("fix add again", str(fixture_repo))
    looped = engine.run_loop(task2["id"], editors.model_editor(), ["pytest", "-q"])
    assert looped["task"]["phase"] == store.BOUNDED
    assert "produced no changes" in looped["stop_reason"]


def test_model_editor_end_to_end_reaches_green(data_dir: Path, fixture_repo: Path, monkeypatch):
    """The whole point: the production editor can actually complete a task."""
    from jarvis.dev_agent import editors

    _fake_llm(monkeypatch, [{"path": "mod.py", "code": TARGET_SRC}])
    task = engine.create_task("fix add", str(fixture_repo))
    out = engine.run_loop(task["id"], editors.model_editor(), ["pytest", "-q"])
    assert out["task"]["phase"] == store.COMPLETED
    assert out["task"]["last_test"]["green"] is True


def test_pick_target_prefers_module_over_test(data_dir: Path, fixture_repo: Path):
    from jarvis.dev_agent import editors

    ws = workspace.open_workspace(fixture_repo)
    task = {"objective": "fix add", "baseline_failures": ["test_mod.py::test_add"]}
    assert editors.pick_target(task, ws, {}) == "mod.py"
    assert editors.is_test_file("test_mod.py") is True
    assert editors.is_test_file("mod.py") is False


def test_every_registered_dev_action_is_reachable_by_the_coding_specialist(data_dir: Path):
    """Regression: dev_task_recover was registered but denied to every agent.

    An action the coding specialist cannot invoke is dead code in production,
    which is only visible once the real service is driven over HTTP.
    """
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    dev_actions = {
        a["action"] for a in all_actions() if str(a.get("action", "")).startswith("dev_")
    }
    assert dev_actions, "no dev_* actions registered"
    coder = agents.get("coding_specialist")
    high_impact = set(definitions.CODING_HIGH_IMPACT)
    unreachable = {a for a in dev_actions - high_impact if not coder.permits(a)}
    assert not unreachable, f"registered but unreachable: {sorted(unreachable)}"


def test_edit_that_breaks_collection_is_diagnosed_and_rolled_back(
    data_dir: Path, fixture_repo: Path, monkeypatch
):
    """Regression, seen live: the model wrote test content into the module.

    Collection then fails, so pytest reports an error and no FAILED lines at
    all. Without this the tree looked "clean" while nothing could run, and the
    corrupted file was fed straight back to the model on the next iteration.
    """
    from jarvis.dev_agent import editors

    corrupt = "from mod import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    _fake_llm(monkeypatch, [{"path": "mod.py", "code": corrupt}])

    task = engine.create_task("fix add", str(fixture_repo))
    engine.phase_plan(task["id"])
    engine.phase_inspect(task["id"], test_cmd=["pytest", "-q"])
    assert store.get(task["id"])["baseline_runnable"] == 1

    before = (fixture_repo / "mod.py").read_text()
    implemented = engine.phase_implement(task["id"], editors.model_editor())
    assert (fixture_repo / "mod.py").read_text() == corrupt

    tested = engine.phase_test(task["id"], ["pytest", "-q"])
    assert tested["summary"]["green"] is False
    assert tested["summary"]["errors"] >= 1
    assert tested["summary"]["failing_tests"] == []

    diagnosis = engine.phase_diagnose(task["id"])
    assert diagnosis["verdict"] == "broke_the_suite", diagnosis
    assert diagnosis["broke_the_suite"] is True

    undone = engine._rollback(task["id"], implemented["restore"])
    assert undone == ["mod.py"]
    assert (fixture_repo / "mod.py").read_text() == before


def test_loop_rolls_back_a_suite_breaking_edit(data_dir: Path, fixture_repo: Path, monkeypatch):
    """The loop must not leave the workspace unrunnable."""
    from jarvis.dev_agent import editors

    corrupt = "from mod import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    _fake_llm(monkeypatch, [{"path": "mod.py", "code": corrupt}])
    before = (fixture_repo / "mod.py").read_text()

    task = engine.create_task("fix add", str(fixture_repo))
    out = engine.run_loop(task["id"], editors.model_editor(), ["pytest", "-q"], max_iterations=2)

    assert out["task"]["phase"] == store.BOUNDED
    assert (fixture_repo / "mod.py").read_text() == before, "corrupted file left behind"
    events = [e["kind"] for e in store.events(task["id"])]
    assert "rollback" in events
