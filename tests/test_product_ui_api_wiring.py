"""Regression: UI-connected product endpoints that previously 404'd."""

from __future__ import annotations


def test_disconnected_ui_routes_are_registered():
    from jarvis.gui.server import app

    paths = {getattr(route, "path", None) for route in app.routes}
    for required in (
        "/api/audio/stop",
        "/api/audio/output-sink",
        "/api/browser/install-playwright",
        "/api/journal/projects",
        "/api/journal/projects/{slug}",
        "/api/journal/projects/{slug}/log",
        "/api/journal/projects/{slug}/learn",
    ):
        assert required in paths, f"missing route {required}"


def test_pin_lock_exact_exempt_paths_exist_as_routes():
    """PIN-exempt exact paths must be live routes (no phantom exemptions)."""
    from jarvis.gui.server import app
    from jarvis.security.middleware import PinLockMiddleware

    paths = {getattr(route, "path", None) for route in app.routes}
    for exempt in PinLockMiddleware.EXEMPT_PATHS:
        assert exempt in paths, f"PIN-exempt path has no route: {exempt}"


def test_mission_control_tab_loaders_databases_and_connection():
    from jarvis.mission_control import get_tab

    dbs = get_tab("databases")
    assert dbs.get("ok") is True, dbs
    assert "databases" in (dbs.get("data") or {})

    conn = get_tab("connection")
    assert conn.get("ok") is True, conn
    assert conn.get("tab") == "connection"
    data = conn.get("data") or {}
    assert "mission_control_reachable" in data or "ok" in data


def test_browser_status_exposes_agent_ready():
    from jarvis.browser_agent import status

    st = status()
    assert "playwright" in st and "chromium" in st
    assert st.get("agent_ready") is bool(st.get("playwright") and st.get("chromium"))
    src = open("jarvis/gui/static/browser_panel.js", encoding="utf-8").read()
    assert "agent_ready" in src
    assert "st.playwright && st.chromium" in src or "playwright && st.chromium" in src


def test_dashboard_skills_and_maker_controls_are_wired():
    from pathlib import Path

    planner = Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    maker = Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    movie = Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "skillsWorkflowsRefreshBtn" in planner
    assert "loadSkillsWorkflows" in planner
    assert "cadIterateBtn" in maker and "cadClearBtn" in maker and "cadExportBtn" in maker
    assert "settingsSpeakToggle" in movie
    from jarvis.gui.server import app

    paths = {getattr(route, "path", None) for route in app.routes}
    for required in ("/api/skills", "/api/workflows", "/api/workflows/scan", "/api/upgrade/clear"):
        assert required in paths, f"missing route {required}"


def test_workflow_list_skips_index_json(data_dir, monkeypatch):
    wf = data_dir / "workflows"
    wf.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.workflow_learning.WORKFLOWS_DIR", wf)
    monkeypatch.setattr("jarvis.workflow_learning.INDEX_FILE", wf / "index.json")
    monkeypatch.setattr("jarvis.workflow_learning.WATCH_FILE", wf / "_watch_state.json")
    (wf / "index.json").write_text('{"workflows": {}}', encoding="utf-8")
    from jarvis.workflow_learning import ensure_demo_workflow, list_workflows

    ensure_demo_workflow()
    items = list_workflows()
    assert items
    assert all(i.get("slug") and i.get("name") for i in items)
    assert not any(i.get("slug") in (None, "index") for i in items)


def test_lsp_diagnostics_ui_uses_quick_mode():
    src = open("jarvis/gui/static/app.js", encoding="utf-8").read()
    assert 'q.set("deep", "0")' in src
    assert "AbortController" in src
    assert "Checking…" in src


def test_mc_dollar_accepts_hash_ids_and_audit_controls_wired():
    from pathlib import Path

    mc = Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert 'replace(/^#/, "")' in mc or "replace(/^#/, '')" in mc
    assert "mcRoutingLiveBtn" in mc
    assert "mcRepairBtn" in mc
    assert "Repair done" in mc
    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert 'id="lockFaceBtn"' in html
    assert 'id="routerWarmBtn"' in html
    assert 'id="voiceSmokeBtn"' in html
    assert 'id="routerStatusPill"' in html
    assert 'id="upgradeClearBtn"' in html
    assert 'id="galleryGenerateBtn"' in html
    assert 'id="galleryPromptInput"' in html
    voice = Path("jarvis/gui/static/voice_bar.js").read_text(encoding="utf-8")
    assert 'fetch("/api/voice/smoke")' in voice
    assert 'fetch("/api/voice/smoke", { method: "POST" })' not in voice
    app_js = Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "inpaintDenoise" in app_js
    assert "refreshSidebarVideoStatus" in app_js
    assert 'fetch("/api/upgrade/clear"' in app_js
    assert "upgradeClearBtn" in app_js
    assert "galleryGenerateBtn" in app_js
    assert "generate image:" in app_js
    maker = Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    assert "printerModelSelect" in maker


def test_stop_playback_and_clear_tts_queue_do_not_raise():
    from jarvis.audio_device import stop_playback
    from jarvis.tts_playback_queue import clear_tts_queue

    stop_playback()
    clear_tts_queue()


def test_journal_projects_backend(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.project_journal.JOURNAL_DIR", data_dir / "journal")
    monkeypatch.setattr("jarvis.project_journal.PROJECTS_DIR", data_dir / "journal" / "projects")
    monkeypatch.setattr(
        "jarvis.project_journal.INDEX_FILE", data_dir / "journal" / "projects" / "index.json"
    )
    from jarvis.project_journal import ProjectJournal, list_projects

    store = ProjectJournal("aria-test")
    store.ensure(title="Aria Test")
    store.daily_add("Ship product certification", bullet_type="task")
    projects = list_projects()
    assert any(p.get("slug") == "aria-test" for p in projects)
    page = store.daily_get()
    assert any("Ship product certification" in (b.get("content") or "") for b in page.get("bullets") or [])
