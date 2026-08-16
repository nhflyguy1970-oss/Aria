"""Automation product — storage, honest execution, home, registry, wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "jarvis" / "gui" / "static"


def test_automation_modules_exist():
    base = ROOT / "jarvis" / "automation"
    for name in (
        "paths.py",
        "execution.py",
        "registry.py",
        "history.py",
        "migrate.py",
        "home.py",
        "nl.py",
        "suggestions.py",
        "mute.py",
        "activity_bridge.py",
        "product_routes.py",
    ):
        assert (base / name).is_file(), name


def test_docs_and_ui_exist():
    assert (ROOT / "docs" / "AUTOMATION_IMPLEMENTATION.md").is_file()
    assert (STATIC / "automation_home.js").is_file()
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'data-view="automation"' in html
    assert 'id="automationView"' in html
    assert "View Paths" in html
    assert "automation_home.js" in html
    assert "Workflow recorder" not in html or "View Paths" in html


def test_view_paths_not_called_workflows_in_recorder():
    js = (STATIC / "workflow_recorder.js").read_text(encoding="utf-8")
    assert "View Path" in js
    assert "NOT Automation" in js or "navigation shortcuts" in js.lower()


def test_chat_suggestion_points_to_automation():
    sug = (STATIC / "chat_suggestions.js").read_text(encoding="utf-8")
    assert 'view: "automation"' in sug
    assert "Run an install or repair skill from Dashboard" not in sug


def test_palette_automation_commands():
    catalog = (STATIC / "command_catalog.js").read_text(encoding="utf-8")
    assert "act:automation-home" in catalog
    assert "act:view-paths" in catalog
    assert "Open View Paths" in catalog


def test_execution_skipped_not_success():
    from jarvis.automation.execution import SKIPPED, normalize_result

    n = normalize_result({"ok": True, "skipped": True, "reason": "no handler"})
    assert n["status"] == SKIPPED
    assert n["ok"] is False
    assert n["executed"] is False
    assert n["skipped"] is True


def test_execution_dry_run():
    from jarvis.automation.execution import DRY_RUN, normalize_result

    n = normalize_result({"ok": True}, dry_run=True)
    assert n["status"] == DRY_RUN
    assert n["executed"] is False
    assert n["dry_run"] is True


def test_registry_lists_actions(data_dir=None):
    from jarvis.automation.registry import get_action, list_actions, validate_action

    acts = list_actions(include_experimental=False)
    assert any(a["id"] == "maintenance" for a in acts)
    assert get_action("memory_consolidate")
    bad = validate_action("nope_action")
    assert bad["ok"] is False


def test_migrate_isolates_namespaces(tmp_path, monkeypatch):
    from jarvis.automation import migrate as mig
    from jarvis.automation import paths as p

    monkeypatch.setattr(p, "AUTOMATION_ROOT", tmp_path / "automation_product")
    monkeypatch.setattr(p, "RULES_FILE", tmp_path / "automation_product" / "rules.json")
    monkeypatch.setattr(p, "WORKFLOW_DAGS_DIR", tmp_path / "automation_product" / "workflow_dags")
    monkeypatch.setattr(p, "LEARNED_WORKFLOWS_DIR", tmp_path / "automation_product" / "learned_workflows")
    monkeypatch.setattr(p, "LEARNED_INDEX_FILE", tmp_path / "automation_product" / "learned_workflows" / "index.json")
    monkeypatch.setattr(p, "LEARNED_WATCH_FILE", tmp_path / "automation_product" / "learned_workflows" / "_watch_state.json")
    monkeypatch.setattr(p, "LEGACY_RULES_FILE", tmp_path / "user_automations.json")
    monkeypatch.setattr(p, "LEGACY_WORKFLOWS_DIR", tmp_path / "workflows")
    monkeypatch.setattr(mig, "RULES_FILE", p.RULES_FILE)
    monkeypatch.setattr(mig, "WORKFLOW_DAGS_DIR", p.WORKFLOW_DAGS_DIR)
    monkeypatch.setattr(mig, "LEARNED_WORKFLOWS_DIR", p.LEARNED_WORKFLOWS_DIR)
    monkeypatch.setattr(mig, "LEARNED_INDEX_FILE", p.LEARNED_INDEX_FILE)
    monkeypatch.setattr(mig, "LEARNED_WATCH_FILE", p.LEARNED_WATCH_FILE)
    monkeypatch.setattr(mig, "LEGACY_RULES_FILE", p.LEGACY_RULES_FILE)
    monkeypatch.setattr(mig, "LEGACY_WORKFLOWS_DIR", p.LEGACY_WORKFLOWS_DIR)

    p.ensure_dirs()
    p.LEGACY_RULES_FILE.write_text(json.dumps({"rules": [{"id": "r1", "name": "T", "kind": "interval", "expression": "60", "action": "briefing"}]}), encoding="utf-8")
    legacy = p.LEGACY_WORKFLOWS_DIR
    legacy.mkdir(parents=True)
    (legacy / "dag1.json").write_text(
        json.dumps({"id": "dag1", "name": "DAG", "entry": "a", "steps": [{"id": "a", "action": "builtin:log"}]}),
        encoding="utf-8",
    )
    (legacy / "learned1.json").write_text(
        json.dumps({"slug": "learned1", "name": "L", "count": 3, "steps": [{"action": "x"}, {"action": "y"}]}),
        encoding="utf-8",
    )

    report = mig.migrate_storage(force=True)
    assert report["ok"]
    assert p.RULES_FILE.is_file()
    assert (p.WORKFLOW_DAGS_DIR / "dag1.json").is_file()
    assert (p.LEARNED_WORKFLOWS_DIR / "learned1.json").is_file()
    # legacy preserved
    assert (legacy / "dag1.json").is_file()


def test_home_snapshot(data_dir, monkeypatch):
    from jarvis.automation.home import home_snapshot
    from jarvis.automation.migrate import migrate_storage

    migrate_storage()
    snap = home_snapshot()
    assert snap["ok"] is True
    assert "identity" in snap
    assert "summary" in snap
    assert "rules" in snap
    assert snap["identity"]["view_paths"].lower().find("navigation") >= 0


def test_nl_never_auto_enables():
    from jarvis.automation.nl import parse_nl_automation

    d = parse_nl_automation("Every weekday at 7am run Briefing")
    assert d["ok"]
    assert d["confirmation_required"] is True
    if d.get("draft"):
        assert d["draft"]["enabled"] is False


def test_suggestions_not_auto_enabled(data_dir, monkeypatch):
    from jarvis.automation import suggestions as sug
    from jarvis.automation import paths as p

    monkeypatch.setattr(p, "SUGGESTIONS_FILE", Path(data_dir) / "suggestions.json")
    monkeypatch.setattr(sug, "SUGGESTIONS_FILE", p.SUGGESTIONS_FILE)
    created = sug.propose_from_scan([{"slug": "demo", "name": "Demo", "count": 4, "steps": [1, 2]}])
    assert created
    assert created[0]["enabled"] is False
    assert created[0]["status"] == "suggested"


def test_engine_unknown_action_is_skipped(data_dir, monkeypatch):
    from jarvis.automation import engine as eng

    eng._rules = []
    rule = eng.upsert_rule(
        {
            "name": "Unknown",
            "kind": "interval",
            "expression": "99999",
            "action": "definitely_missing_action_xyz",
            "enabled": False,
        }
    )
    out = eng.run_rule(rule["id"], dry_run=False)
    assert out.get("status") == "skipped" or out.get("result", {}).get("status") == "skipped"
    assert out.get("ok") is False


def test_engine_writes_single_rules_file(data_dir):
    from jarvis.automation import engine as eng
    from jarvis.automation import paths as p

    legacy = p.LEGACY_RULES_FILE
    if legacy.exists():
        legacy.unlink()
    eng._rules = []
    eng.upsert_rule(
        {
            "name": "Single file",
            "kind": "interval",
            "expression": "99999",
            "action": "briefing",
            "enabled": False,
        }
    )
    assert eng._rules_path().is_file()
    assert not legacy.exists()


def test_api_routes_documented_in_product_routes():
    src = (ROOT / "jarvis" / "automation" / "product_routes.py").read_text(encoding="utf-8")
    for path in (
        "/api/automation/home",
        "/api/automation/rules",
        "/api/automation/nl",
        "/api/automation/webhook/test",
        "/api/automation/search",
        "/api/automation/actions",
    ):
        assert path in src, path


def test_automation_request_annotation_resolves():
    """Regression: local Request import + future annotations made FastAPI treat
    `request` as a required query param, breaking rule/pipeline dry-run and run."""
    import inspect

    from fastapi import FastAPI, Request
    from jarvis.automation.product_routes import register_automation_product_routes

    app = FastAPI()
    register_automation_product_routes(app, None)
    for path in (
        "/api/automation/rules",
        "/api/automation/rules/{rule_id}/run",
        "/api/automation/pipelines/{pipeline_id}/run",
    ):
        route = next(
            r
            for r in app.routes
            if getattr(r, "path", None) == path and "POST" in (getattr(r, "methods", None) or set())
        )
        hints = inspect.get_annotations(route.endpoint, eval_str=True)
        assert hints.get("request") is Request, path
        assert not route.dependant.query_params, path


def test_webhook_docs_header_only():
    docs = (ROOT / "docs" / "automation-webhook.md").read_text(encoding="utf-8")
    assert "X-Jarvis-Automation-Secret" in docs
    assert "rejected" in docs.lower()
