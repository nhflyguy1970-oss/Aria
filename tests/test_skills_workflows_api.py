"""API route tests for skills, workflows, and admin backup (§22 S22-09)."""

from __future__ import annotations

from unittest.mock import patch


def test_api_skills_list(chat_app, data_dir, monkeypatch):
    skills = data_dir / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.skill_database.SKILLS_DIR", skills)
    monkeypatch.setattr("jarvis.skill_database.INDEX_FILE", skills / "index.json")

    res = chat_app.get("/api/skills")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert isinstance(body["skills"], list)
    assert body["skills"]


def test_api_skills_run_dry_run(chat_app, data_dir, monkeypatch):
    skills = data_dir / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.skill_database.SKILLS_DIR", skills)
    monkeypatch.setattr("jarvis.skill_database.INDEX_FILE", skills / "index.json")

    from jarvis.skill_database import ensure_default_skills

    ensure_default_skills()
    slug = chat_app.get("/api/skills").json()["skills"][0]["slug"]
    res = chat_app.post(f"/api/skills/{slug}/run", json={"dry_run": True})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body.get("dry_run") is True


def test_api_workflows_scan_and_run(chat_app, data_dir, monkeypatch):
    wf = data_dir / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.workflow_learning.WORKFLOWS_DIR", wf)
    monkeypatch.setattr("jarvis.workflow_learning.INDEX_FILE", wf / "index.json")
    monkeypatch.setattr("jarvis.workflow_learning.WATCH_FILE", wf / "_watch_state.json")

    from jarvis.workflow_learning import ensure_demo_workflow

    demo = ensure_demo_workflow()
    assert demo

    list_res = chat_app.get("/api/workflows")
    assert list_res.status_code == 200
    workflows = list_res.json()["workflows"]
    assert workflows

    run_res = chat_app.post(f"/api/workflows/{demo['slug']}/run", json={})
    assert run_res.status_code == 200
    run_body = run_res.json()
    assert run_body["ok"] is True
    assert run_body.get("dry_run") is True

    scan_res = chat_app.post("/api/workflows/scan", json={"min_repeats": 2})
    assert scan_res.status_code == 200
    assert scan_res.json()["ok"] is True


def test_api_admin_backup_async(chat_app, monkeypatch):
    def fake_submit(label, fn):
        result = fn()
        chat_app._backup_result = result
        return "backup-job-1"

    monkeypatch.setattr("jarvis.coding_jobs.submit", fake_submit)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = type("P", (), {"returncode": 0, "stdout": "Backup saved: /tmp/x.tar.gz", "stderr": ""})()
        res = chat_app.post("/api/admin/backup", json={"async": True})

    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["pending"] is True
    assert body["job_id"] == "backup-job-1"
    assert chat_app._backup_result["ok"] is True


def test_api_upgrade_clear(chat_app, data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.upgrade_wizard.SESSION_FILE", data_dir / "upgrade_wizard.json")
    from jarvis.upgrade_wizard import save_session

    save_session({"step": "proposed", "proposal_id": "p1", "test": True})
    res = chat_app.post("/api/upgrade/clear")
    assert res.status_code == 200
    status = chat_app.get("/api/upgrade/status").json()
    assert status.get("active") is None
