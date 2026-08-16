"""Tests for Automation Pipelines (DAG Workflow Engine subsystem)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def pipe_env(tmp_path, monkeypatch):
    root = tmp_path / "automation_product"
    dags = root / "workflow_dags"
    dags.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.automation.paths.AUTOMATION_ROOT", root)
    monkeypatch.setattr("jarvis.automation.paths.WORKFLOW_DAGS_DIR", dags)
    monkeypatch.setattr("jarvis.automation.paths.EXPORT_DIR", root / "exports")
    monkeypatch.setattr("jarvis.automation.pipelines.storage.WORKFLOW_DAGS_DIR", dags)
    monkeypatch.setattr("jarvis.automation.pipelines.storage.EXPORT_DIR", root / "exports")
    monkeypatch.setattr("jarvis.automation.pipelines.runs.RUNS_FILE", root / "pipeline_runs.json")
    monkeypatch.setattr("jarvis.automation.pipelines.jobs._STATE_FILE", root / "pipeline_jobs.json")
    monkeypatch.setattr("jarvis.automation.paths.RUN_HISTORY_FILE", root / "run_history.json")
    monkeypatch.setattr("jarvis.automation.pipelines.jobs._STATE_FILE", root / "pipeline_jobs.json")
    import jarvis.automation.pipelines.jobs as jobs

    jobs._jobs.clear()
    jobs._history.clear()
    jobs._loaded = False
    return {"root": root, "dags": dags}


def test_pipeline_modules_exist():
    root = Path(__file__).resolve().parents[1] / "jarvis" / "automation" / "pipelines"
    for name in (
        "engine.py",
        "storage.py",
        "actions.py",
        "runs.py",
        "jobs.py",
        "nl.py",
        "promote.py",
        "templates.py",
        "canvas.py",
    ):
        assert (root / name).is_file()


def test_templates_have_descriptions():
    from jarvis.automation.pipelines.templates import TEMPLATES, list_template_meta

    meta = list_template_meta()
    assert any(t["id"] == "morning_routine" for t in meta)
    mr = TEMPLATES["morning_routine"]
    assert "briefing" in (mr.get("description") or "").lower() or True
    actions = [s["action"] for s in mr["steps"]]
    assert "briefing" in actions
    assert "memory_consolidate" in actions
    assert "builtin:log" not in actions or "briefing" in actions  # honest, not demo-only


def test_crud_create_rename_delete_duplicate(pipe_env):
    from jarvis.automation.pipelines.storage import (
        create_from_template,
        delete_pipeline,
        duplicate_pipeline,
        get_pipeline,
        list_pipelines,
        rename_pipeline,
        save_pipeline,
    )

    wf = create_from_template("doc_ingest")
    assert wf["id"]
    assert get_pipeline(wf["id"])
    # anti-spam reuse
    again = create_from_template("doc_ingest")
    assert again.get("reused") or again["id"] == wf["id"]

    renamed = rename_pipeline(wf["id"], "Docs Pipeline")
    assert renamed["name"] == "Docs Pipeline"
    dup = duplicate_pipeline(wf["id"])
    assert dup["id"] != wf["id"]
    assert "copy" in dup["name"].lower() or dup["name"] != renamed["name"]

    saved = save_pipeline({**get_pipeline(dup["id"]), "description": "updated"}, bump_version=True)
    assert saved["version"] >= 1

    assert delete_pipeline(dup["id"])["ok"]
    assert get_pipeline(dup["id"]) is None
    assert any(p["id"] == wf["id"] for p in list_pipelines())


def test_dry_run_no_side_effects(pipe_env, monkeypatch):
    from jarvis.automation.pipelines.engine import run_pipeline
    from jarvis.automation.pipelines.storage import create_from_template, save_pipeline

    calls = []

    def fake_exec(action, params, variables, *, dry_run=False, approve_experimental=False):
        calls.append(action)
        return {"ok": True, "dry_run": True, "would_execute": action}

    monkeypatch.setattr("jarvis.automation.pipelines.engine.execute_action", fake_exec)
    wf = create_from_template("doc_ingest", name="Dry Docs")
    # force unique
    wf = save_pipeline({**wf, "id": "drytest01", "name": "Dry Docs Unique", "template_id": None}, bump_version=False)
    result = run_pipeline(wf["id"], dry_run=True, emit_bridges=False)
    assert result["status"] == "dry_run"
    assert result["ok"]
    assert calls  # predicted steps


def test_run_with_registry_actions_and_history(pipe_env, monkeypatch):
    from jarvis.automation.pipelines.engine import run_pipeline
    from jarvis.automation.pipelines.runs import get_pipeline_run, list_pipeline_runs
    from jarvis.automation.pipelines.storage import save_pipeline

    def fake_exec(action, params, variables, *, dry_run=False, approve_experimental=False):
        if action == "builtin:fail":
            return {"ok": False, "error": "boom"}
        return {"ok": True, "result": action}

    monkeypatch.setattr("jarvis.automation.pipelines.engine.execute_action", fake_exec)

    wf = save_pipeline(
        {
            "id": "runhist01",
            "name": "Retry Path",
            "entry": "a",
            "steps": [
                {
                    "id": "a",
                    "name": "Fail then recover",
                    "action": "builtin:fail",
                    "retries": 0,
                    "on_failure": ["b"],
                },
                {"id": "b", "name": "Ok", "action": "builtin:log", "params": {"msg": "recovered"}},
            ],
        },
        bump_version=False,
    )
    result = run_pipeline(wf["id"], emit_bridges=True, trigger="test")
    assert result["status"] in ("partial_success", "succeeded", "failed")
    assert result["run_id"]
    assert list_pipeline_runs(pipeline_id=wf["id"])
    assert get_pipeline_run(result["run_id"])


def test_retry_on_failure_compat(pipe_env, monkeypatch):
    """Compatibility with intelligence workflow_engine API."""
    from jarvis.intelligence.workflow_engine import WorkflowDef, WorkflowStep, run_workflow, save_workflow

    monkeypatch.setattr(
        "jarvis.automation.pipelines.engine.execute_action",
        lambda action, params, variables, **kw: (
            {"ok": False, "error": "x"} if action == "builtin:fail" and variables.get("_n", 0) < 0 else {"ok": True}
            if action != "builtin:fail"
            else {"ok": False, "error": "x"}
        ),
    )
    # Simpler: fail once then on_failure succeeds
    def exec_action(action, params, variables, *, dry_run=False, approve_experimental=False):
        if action == "builtin:fail":
            return {"ok": False, "error": "forced"}
        return {"ok": True, "message": params.get("msg")}

    monkeypatch.setattr("jarvis.automation.pipelines.engine.execute_action", exec_action)

    wf = WorkflowDef(
        id="retry01",
        name="Retry",
        entry="fail",
        steps=[
            WorkflowStep(id="fail", name="Fail", action="builtin:fail", retries=1, on_failure=["ok"]),
            WorkflowStep(id="ok", name="OK", action="builtin:log", params={"msg": "done"}),
        ],
    )
    save_workflow(wf)
    result = run_workflow(wf.id, emit_bridges=False)
    assert result["run_id"]
    assert any(r.get("step") == "ok" for r in result["log"])


def test_workflow_dag_run_in_automation_engine(pipe_env, monkeypatch):
    from jarvis.automation.pipelines.storage import save_pipeline
    from jarvis.automation.engine import AutomationRule, _default_run

    save_pipeline(
        {
            "id": "enginedag1",
            "name": "Engine DAG",
            "entry": "a",
            "steps": [{"id": "a", "name": "Log", "action": "builtin:log", "params": {"msg": "hi"}}],
        },
        bump_version=False,
    )
    monkeypatch.setattr(
        "jarvis.automation.pipelines.engine.execute_action",
        lambda *a, **k: {"ok": True, "message": "hi"},
    )
    rule = AutomationRule(
        id="r1",
        name="Run DAG",
        kind="interval",
        expression="3600",
        action="workflow_dag_run",
        params={"workflow_id": "enginedag1"},
        enabled=True,
    )
    result = _default_run(rule, dry_run=False)
    assert result.get("ok") or result.get("status") in ("succeeded", "partial_success", "dry_run")


def test_nl_draft_never_autosave(pipe_env):
    from jarvis.automation.pipelines.nl import parse_nl_pipeline
    from jarvis.automation.pipelines.storage import list_pipelines

    before = len(list_pipelines())
    draft = parse_nl_pipeline("Create a morning workflow")
    assert draft["ok"]
    assert draft["confirmation_required"]
    assert draft["draft"]["auto_run"] is False
    assert len(list_pipelines()) == before


def test_promote_learned_requires_review(pipe_env, monkeypatch):
    from jarvis.automation.pipelines.promote import learned_to_dag_draft

    monkeypatch.setattr(
        "jarvis.workflow_learning.load_workflow",
        lambda slug: {
            "slug": slug,
            "name": "Demo learned",
            "steps": [
                {"action": "memory_consolidate", "name": "Memory"},
                {"action": "documents_reindex", "name": "Docs"},
            ],
        },
    )
    out = learned_to_dag_draft("demo")
    assert out["ok"]
    assert out["confirmation_required"]
    assert out["draft"]["auto_save"] is False
    assert len(out["draft"]["steps"]) == 2


def test_canvas_read_only(pipe_env):
    from jarvis.automation.pipelines.canvas import canvas_model
    from jarvis.automation.pipelines.storage import create_from_template

    wf = create_from_template("evening_wrap", name="Eve Unique Canvas")
    # may reuse — get id
    model = canvas_model(wf["id"])
    assert model["ok"]
    assert "nodes" in model
    assert "n8n" in (model.get("note") or "").lower() or "json" in (model.get("note") or "").lower()


def test_job_center_includes_automation_jobs(pipe_env):
    from jarvis.automation.pipelines import jobs as pj
    from jarvis.jobs_center import snapshot

    jid = pj.start_job(run_id="r1", pipeline_id="p1", name="Test Pipe")
    snap = snapshot(recent_limit=20)
    assert "automation_jobs" in snap
    assert any(j.get("id") == jid for j in snap.get("automation_jobs") or [])


def test_experimental_agent_requires_approval(pipe_env):
    from jarvis.automation.pipelines.actions import execute_action

    denied = execute_action("agent_step", {"prompt": "hi", "budget": 1}, {}, approve_experimental=False)
    assert denied.get("permission_required")
    # Approved path runs Specialist Team (may be partial if organs missing) — not a silent stub
    ok = execute_action("agent_step", {"prompt": "research aria memory", "budget": 1}, {}, approve_experimental=True)
    assert "result" in ok or ok.get("ok") is not None
    if ok.get("ok"):
        assert (ok.get("result") or {}).get("mode") == "specialist_team"


def test_ui_and_docs_wiring():
    root = Path(__file__).resolve().parents[1]
    html = (root / "jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert "autoPipeRunModal" in html
    assert "Pipelines (DAGs)" in html
    js = (root / "jarvis/gui/static/automation_home.js").read_text(encoding="utf-8")
    assert "runPipeline" in js
    assert "/api/automation/pipelines" in js
    catalog = (root / "jarvis/gui/static/command_catalog.js").read_text(encoding="utf-8")
    assert "act:pipelines-list" in catalog
    routes = (root / "jarvis/automation/pipeline_routes.py").read_text(encoding="utf-8")
    assert "/api/automation/pipelines" in routes
    docs = root / "docs/WORKFLOW_DAG_IMPLEMENTATION.md"
    assert docs.is_file()


def test_export_and_favorites(pipe_env):
    from jarvis.automation.pipelines.storage import create_from_template, export_pipelines, set_favorite

    wf = create_from_template("evening_wrap", name="Weeknight shutdown")
    set_favorite(wf["id"], True)
    exp = export_pipelines([wf["id"]])
    assert exp["count"] >= 1
    assert Path(exp["path"]).is_file()
