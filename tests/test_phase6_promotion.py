"""Phase 6 — reviewed promotion of agent changes into a (disposable) project."""

# ruff: noqa: F811
# Shared pytest fixtures intentionally also name test parameters.
from __future__ import annotations

import os
import subprocess
import time

import pytest
from test_phase5_coding_agents import FAKE, _register, agents, repo  # noqa: F401  (fixtures)

from jarvis.coding_agents import contract, discovery, promotion, runs

pytestmark = pytest.mark.skipif(not __import__("shutil").which("bwrap"), reason="bubblewrap required")

GOOD = "def add(a, b):\n    return a + b  # reviewed\n"


def _git(repo, *args):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=env)


def _verified_run(agents, proj, edits=None, mode=discovery.WORKSPACE_WRITE):
    agents.behave(edits=edits or {"calc.py": GOOD}, message="Done.")
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=mode, task="tidy calc")
    run = runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="test", background=False)
    return runs.get_run(run["id"]), plan


@pytest.fixture
def setup(agents, repo):  # noqa: F811
    proj = _register(repo)
    run, plan = _verified_run(agents, proj)
    assert run["status"] == contract.VERIFIED, run["result"].get("reason")
    return proj, run, plan, repo


def test_full_promotion_applies_only_after_its_own_approval(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    assert p["status"] == promotion.PROPOSED and p["checks"]["ok"]
    assert p["verification"]["applies"] and p["verification"]["tests"]["passed"]
    assert (repo / "calc.py").read_text() != GOOD  # nothing applied by proposing
    assert "no commit, no push" in promotion.summary_text(p)
    with pytest.raises(promotion.PromotionError):
        promotion.apply(p["id"])  # not approved
    out = promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    assert out["status"] == promotion.APPLIED and out["result"]["verified"]
    assert (repo / "calc.py").read_text() == GOOD
    assert _git(repo, "log", "--oneline").stdout.count("\n") == 1  # not committed
    assert "roll back promotion" in out["result"]["rollback"]


def test_plan_approval_token_cannot_approve_promotion(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    with pytest.raises(promotion.PromotionError):
        promotion.approve(p["id"], token=runs.approval_token(plan["id"]), via="test")
    assert promotion.get(p["id"])["status"] == promotion.PROPOSED


def test_approval_is_single_use_and_replay_never_reapplies(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    token = promotion.approval_token(p["id"])
    promotion.apply(p["id"], token=token, via="test")
    (repo / "calc.py").write_text(GOOD + "# owner edit after promotion\n")
    again = promotion.apply(p["id"], token=token, via="test")
    assert again["status"] == promotion.APPLIED
    assert "owner edit" in (repo / "calc.py").read_text()  # replay did nothing
    with pytest.raises(promotion.PromotionError):
        promotion.approve(p["id"], token=token, via="test")
    assert promotion.propose(run["id"])["id"] == p["id"]  # one promotion per run


def test_rejection_applies_nothing(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    promotion.reject(p["id"])
    with pytest.raises(promotion.PromotionError):
        promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    assert (repo / "calc.py").read_text() != GOOD


def test_expired_approval(setup, monkeypatch):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    promotion.approve(p["id"], token=promotion.approval_token(p["id"]), via="test")
    real = time.time
    monkeypatch.setattr(promotion.time, "time", lambda: real() + promotion.APPROVAL_TTL_S + 5)
    with pytest.raises(promotion.PromotionError, match="expired"):
        promotion.apply(p["id"])
    assert (repo / "calc.py").read_text() != GOOD


def test_uncommitted_owner_changes_in_touched_file_block_and_survive(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    (repo / "calc.py").write_text("def add(a, b):\n    return a + b\n# owner's uncommitted work\n")
    out = promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    assert out["status"] == promotion.FAILED and "uncommitted" in out["result"]["reason"]
    assert "owner's uncommitted work" in (repo / "calc.py").read_text()


def test_uncommitted_changes_elsewhere_are_preserved(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    (repo / "notes.txt").write_text("mine\n")
    out = promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    assert out["status"] == promotion.APPLIED
    assert (repo / "notes.txt").read_text() == "mine\n"


def test_destination_moved_after_review_is_refused(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    (repo / "other.py").write_text("x = 1\n")
    _git(repo, "add", "other.py")
    _git(repo, "commit", "-qm", "concurrent change")
    out = promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    assert out["status"] == promotion.FAILED and "HEAD moved" in out["result"]["reason"]
    assert (repo / "calc.py").read_text() != GOOD


def test_concurrent_promotions_into_one_project_are_serialised(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    with promotion._destination_lock(str(repo.resolve())):
        out = promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    assert out["status"] == promotion.FAILED and "in progress" in out["result"]["reason"]


def test_failed_tests_after_apply_roll_back(setup, monkeypatch):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    monkeypatch.setattr(promotion, "run_tests_in_place",
                        lambda dest, cmd, **k: {"ran": True, "passed": False, "exit_code": 1})
    out = promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    assert out["status"] == promotion.ROLLED_BACK
    assert (repo / "calc.py").read_text() == "def add(a, b):\n    return a + b\n"
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""


def test_owner_rollback_restores_and_refuses_after_later_edits(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    back = promotion.rollback(p["id"])
    assert back["status"] == promotion.REVERTED
    assert (repo / "calc.py").read_text() == "def add(a, b):\n    return a + b\n"


def test_rollback_never_overwrites_later_edits(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    (repo / "calc.py").write_text("owner rewrote it\n")
    with pytest.raises(promotion.PromotionError, match="changed after"):
        promotion.rollback(p["id"])
    assert (repo / "calc.py").read_text() == "owner rewrote it\n"


@pytest.mark.parametrize("path", [".env", "config/secrets.json", "data/materials.db", "output/x.sqlite3",
                                  "deploy/app.service", "keys/id_rsa"])
def test_protected_and_credential_paths_block(agents, repo, path):  # noqa: F811
    proj = _register(repo)
    run, _ = _verified_run(agents, proj, edits={"calc.py": GOOD, path: "x\n"})
    p = promotion.propose(run["id"])
    assert p["status"] == promotion.BLOCKED
    with pytest.raises(promotion.PromotionError):
        promotion.approve(p["id"], token=promotion.approval_token(p["id"]), via="test")


def test_project_protected_path_blocks(agents, repo):  # noqa: F811
    proj = _register(repo, protected=["fixtures_live"])
    run, _ = _verified_run(agents, proj, edits={"calc.py": GOOD, "fixtures_live/a.txt": "x\n"})
    assert promotion.propose(run["id"])["status"] == promotion.BLOCKED


def test_unverified_run_needs_explicit_acceptance(agents, repo):  # noqa: F811
    proj = _register(repo, test_command="")
    run, _ = _verified_run(agents, proj)
    assert run["status"] == contract.UNVERIFIED
    assert promotion.propose(run["id"])["status"] == promotion.BLOCKED


def test_failed_or_violating_runs_cannot_be_promoted(agents, repo):  # noqa: F811
    proj = _register(repo)
    agents.behave(edits={"calc.py": "def add(a, b):\n    return a - b\n"}, message="All tests pass.")
    plan = runs.create_plan(agent="codex", project=proj["slug"], mode=discovery.WORKSPACE_WRITE, task="x")
    run = runs.get_run(runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="t", background=False)["id"])
    assert run["status"] == contract.TESTS_FAILED
    assert promotion.propose(run["id"])["status"] == promotion.BLOCKED


def test_migration_files_are_flagged_never_run(agents, repo):  # noqa: F811
    proj = _register(repo)
    run, _ = _verified_run(agents, proj, edits={"calc.py": GOOD, "migrations/0002_add.py": "# noop\n"})
    p = promotion.propose(run["id"])
    assert any("migration" in r for r in p["checks"]["risks"])


def test_promotion_lifecycle_in_continuity_not_acm(setup):
    from jarvis.continuity import store

    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="test")
    rec = store.record_by_source(f"coding_promotion:{p['id']}:applied")
    assert rec and rec["status"] == store.DONE and rec["verified"] and rec["project"] == proj["slug"]
    assert store.pending_outbox() == []



class _Owner:
    def __init__(self, ok):
        self.ok = ok

    def authorize(self, capability, room=None, **k):
        return {"ok": self.ok, "reason": "" if self.ok else "step-up required", "capability": capability}


def test_api_promotion_requires_owner_step_up(setup, chat_app, monkeypatch):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    monkeypatch.setattr("jarvis.security.owner.provider_credentials.bound_owner_service", lambda: _Owner(False))
    for path in (f"/api/coding-agents/promotions/{p['id']}/approve", f"/api/coding-agents/runs/{run['id']}/promote",
                 f"/api/coding-agents/promotions/{p['id']}/rollback"):
        assert chat_app.post(path).status_code == 403
    assert (repo / "calc.py").read_text() != GOOD
    listed = chat_app.get("/api/coding-agents/promotions").json()
    assert listed["promotions"][0]["id"] == p["id"] and "nonce" not in listed["promotions"][0]
    monkeypatch.setattr("jarvis.security.owner.provider_credentials.bound_owner_service", lambda: _Owner(True))
    out = chat_app.post(f"/api/coding-agents/promotions/{p['id']}/approve").json()
    assert out["ok"] and (repo / "calc.py").read_text() == GOOD


def test_promotion_interrupted_mid_apply_is_restored_not_reapplied(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    promotion.approve(p["id"], token=promotion.approval_token(p["id"]), via="test")
    # Simulate ARIA dying after the recovery point and the file write, before finishing.
    full = promotion._row(p["id"])
    rdir = promotion.ROOT / "promotions" / p["id"] / "recovery"
    rdir.mkdir(parents=True, exist_ok=True)
    promotion._snapshot(promotion.get(p["id"]), rdir)
    (repo / "calc.py").write_text(GOOD)
    promotion._update(p["id"], status=promotion.APPLYING, recovery_dir=str(rdir))
    assert full["nonce"]
    recovered = promotion.recover_interrupted()
    assert p["id"] in recovered
    after = promotion.get(p["id"])
    assert after["status"] == promotion.ROLLED_BACK and after["result"]["interrupted"]
    assert (repo / "calc.py").read_text() == "def add(a, b):\n    return a + b\n"
    assert promotion.apply(p["id"])["status"] == promotion.ROLLED_BACK  # never re-applied


def test_interrupted_before_recovery_point_means_nothing_applied(setup):
    proj, run, plan, repo = setup
    p = promotion.propose(run["id"])
    promotion._update(p["id"], status=promotion.APPLYING)
    promotion.recover_interrupted()
    assert promotion.get(p["id"])["status"] == promotion.FAILED
    assert (repo / "calc.py").read_text() == "def add(a, b):\n    return a + b\n"
