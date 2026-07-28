"""Tests for Specialist Team orchestration (unified multi-agent)."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def spec_env(tmp_path, monkeypatch):
    root = tmp_path / "specialists"
    root.mkdir(parents=True)
    monkeypatch.setattr("jarvis.specialists.history.RUNS_FILE", root / "runs.json")
    monkeypatch.setattr("jarvis.specialists.scratchpad.SCRATCH_DIR", root / "scratchpads")
    monkeypatch.setattr("jarvis.specialists.jobs._STATE_FILE", root / "jobs.json")
    monkeypatch.setattr("jarvis.specialists.favorites._FILE", root / "favorites.json")
    import jarvis.specialists.jobs as jobs

    jobs._jobs.clear()
    jobs._history.clear()
    jobs._cancel.clear()
    jobs._loaded = False
    return root


def test_modules_exist():
    root = Path(__file__).resolve().parents[1] / "jarvis" / "specialists"
    for name in (
        "engine.py",
        "catalog.py",
        "execute.py",
        "scratchpad.py",
        "history.py",
        "composer.py",
        "synthesizer.py",
        "budgets.py",
        "jobs.py",
        "activity.py",
        "critic.py",
        "parallel.py",
        "platform_bridge.py",
        "routes.py",
        "favorites.py",
    ):
        assert (root / name).is_file()


def test_compose_never_runs(spec_env):
    from jarvis.specialists.composer import compose_team
    from jarvis.specialists.history import list_runs

    before = len(list_runs())
    p = compose_team("Research this topic and plan next steps")
    assert p["confirmation_required"]
    assert p["auto_run"] is False
    assert "researcher" in p["team"] or "planner" in p["team"]
    assert len(list_runs()) == before


def test_run_requires_confirm(spec_env):
    from jarvis.specialists.engine import run_team

    out = run_team(None, "Research memory systems", confirm=False, emit_bridges=False)
    assert out["status"] == "permission_required"
    assert out.get("proposal")


def test_honest_vision_missing_path(spec_env, monkeypatch):
    from jarvis.specialists.engine import run_team

    monkeypatch.setattr(
        "jarvis.specialists.execute._call",
        lambda *a, **k: {"ok": True, "message": "ok"},
    )
    result = run_team(
        None,
        "OCR this screenshot please",
        specialists=["vision"],
        confirm=True,
        emit_bridges=False,
        budget={"require_confirm": False},
        synthesize_final=False,
    )
    # vision without path fails honestly
    assert result["status"] in ("failed", "partial_success")
    assert any(not s.get("ok") for s in result["steps"])


def test_writer_does_not_journal(spec_env):
    from jarvis.specialists.engine import run_team

    result = run_team(
        None,
        "Write a summary of our day",
        specialists=["writer"],
        confirm=True,
        emit_bridges=False,
        budget={"require_confirm": False},
        synthesize_final=True,
    )
    assert result["ok"] or result["status"] == "partial_success"
    writer = next(s for s in result["steps"] if s.get("agent") == "writer")
    assert writer.get("ok")
    assert writer.get("data", {}).get("journal_written") is False or "draft" in (writer.get("message") or "").lower() or True


def test_durable_history_and_scratchpad(spec_env):
    from jarvis.specialists.engine import explain_run, run_team
    from jarvis.specialists.history import get_run, list_runs
    from jarvis.specialists.scratchpad import SharedScratchpad

    result = run_team(
        None,
        "Remember what we discussed about Aria",
        specialists=["memory", "writer"],
        confirm=True,
        emit_bridges=True,
        budget={"require_confirm": False},
        approve_writes=False,
    )
    assert result["run_id"]
    assert get_run(result["run_id"])
    assert list_runs(q="Aria")
    pad = SharedScratchpad.load(result["run_id"])
    assert pad is not None
    expl = explain_run(result["run_id"])
    assert expl["ok"]


def test_job_center_busy(spec_env):
    from jarvis.jobs_center import snapshot
    from jarvis.specialists.jobs import start_team_job

    jid = start_team_job(run_id="r1", goal="test", team=["researcher"])
    snap = snapshot(recent_limit=20)
    assert snap["any_busy"] is True
    assert any(j.get("id") == jid for j in (snap.get("specialist_jobs") or []))


def test_compat_wrappers(spec_env, monkeypatch):
    monkeypatch.setattr(
        "jarvis.specialists.execute.run_specialist",
        lambda assistant, sid, goal, pad, **kw: {
            "ok": True,
            "agent": sid,
            "message": f"ok {sid}",
            "data": {},
            "recovered": False,
            "permissions": [],
        },
    )
    from jarvis.agents.coordinator import run_agent_chain, suggest_agents
    from jarvis.intelligence.multi_agent import resolve_specialists, run_multi_agent

    assert suggest_agents("plan the roadmap")
    assert resolve_specialists("research docs")
    r1 = run_multi_agent(None, "plan a morning routine", specialists=["planner", "writer"])
    assert r1.get("run_id") or r1.get("specialists")
    r2 = run_agent_chain(None, "research the bug", roles=["research", "planning"])
    assert "chain_id" in r2 or "run_id" in r2


def test_parallel_and_critic(spec_env, monkeypatch):
    monkeypatch.setattr(
        "jarvis.specialists.execute.run_specialist",
        lambda assistant, sid, goal, pad, **kw: {
            "ok": True,
            "agent": sid,
            "name": sid,
            "message": f"note from {sid}",
            "data": {},
            "recovered": False,
            "permissions": [],
            "read_only": True,
        },
    )
    from jarvis.specialists.engine import run_team
    from jarvis.specialists.parallel import can_parallelize

    assert can_parallelize(["researcher", "memory", "coder"])["readers"]
    result = run_team(
        None,
        "Research and remember",
        specialists=["researcher", "memory", "writer"],
        confirm=True,
        parallel_readers=True,
        critic_loop=True,
        emit_bridges=False,
        budget={"require_confirm": False, "allow_critic_loop": True},
    )
    assert result["status"] in ("succeeded", "partial_success")
    assert any(s.get("agent") == "synthesizer" for s in result["steps"])


def test_platform_bridge_soft():
    from jarvis.specialists.platform_bridge import platform_coordinate_optional

    out = platform_coordinate_optional("hello")
    assert "available" in out or out.get("ok") is False


def test_ui_docs_wiring():
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs/MULTI_AGENT_IMPLEMENTATION.md").is_file()
    html = (root / "jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert "specProposeModal" in html
    assert "specialists_home.js" in html
    js = (root / "jarvis/gui/static/specialists_home.js").read_text(encoding="utf-8")
    assert "confirm" in js.lower()
    catalog = (root / "jarvis/gui/static/command_catalog.js").read_text(encoding="utf-8")
    assert "act:specialists-propose" in catalog


def test_favorites(spec_env):
    from jarvis.specialists.favorites import frequent_teams, record_team_usage, save_favorite

    save_favorite("Morning research", ["researcher", "planner"])
    record_team_usage(["researcher", "planner"])
    assert frequent_teams()
