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
    gallery_js = Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    upgrade_js = Path("jarvis/gui/static/upgrade_wizard.js").read_text(encoding="utf-8")
    assert "inpaintDenoise" in app_js
    assert "refreshSidebarVideoStatus" in app_js
    assert 'fetch("/api/upgrade/clear"' in upgrade_js or 'fetch("/api/upgrade/clear"' in app_js
    assert "upgradeClearBtn" in upgrade_js or "upgradeClearBtn" in app_js
    assert "galleryGenerateBtn" in gallery_js or "galleryGenerateBtn" in app_js
    assert "generate image:" in gallery_js or "generate image:" in app_js
    maker = Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    assert "printerModelSelect" in maker


def test_a11y_modal_esc_and_ux_debt_regressions():
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    css = Path("jarvis/gui/static/style.css").read_text(encoding="utf-8")
    app_js = Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    modal = Path("jarvis/gui/static/modal_chrome.js").read_text(encoding="utf-8")
    voice = Path("jarvis/gui/static/voice_bar.js").read_text(encoding="utf-8")
    mc = Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")

    assert 'id="toolConfirmTitle"' in html
    assert 'aria-labelledby="toolConfirmTitle"' in html
    assert 'data-ws-nav="workstationInference"' in html
    assert html.count('data-ws-nav="workstation"') == 1
    assert 'aria-label="Detach smart home panel"' in html
    assert 'aria-label="Close image preview"' in html
    assert 'aria-label="PIN"' in html
    assert "modal_chrome.js" in html

    assert "--muted: var(--text-muted)" in css
    assert "#memeEngineStatus.error" in css
    assert "memory-item--flash" in css

    assert "initAriaModalChrome" in modal
    assert "window.initAriaModalChrome" in modal
    assert "window.initAriaModalChrome?.()" in app_js
    assert "function initAriaModalChrome" not in app_js
    assert "galleryGenerateBtn" in app_js or "galleryGenerateBtn" in Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert 'aria-label="Delete' in app_js or 'aria-label="Delete' in Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert "window.loadMemoryBrowser" in app_js
    assert "window.closeImageLightbox" in app_js

    assert voice.count('data.event === "voice_state"') == 1
    assert 'data.detail === "cloud-live"' in voice
    assert 'switchMcTab("inference")' in mc


def test_orphan_jarvis_api_py_removed():
    from pathlib import Path

    assert not Path("jarvis/api.py").exists(), "stale duplicate voice API must stay removed"
    voice_ext = Path("jarvis/extensions/voice/api.py")
    assert voice_ext.is_file()
    assert "/api/voice/settings" in voice_ext.read_text(encoding="utf-8")


def test_command_palette_is_wired():
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    js = Path("jarvis/gui/static/command_palette.js").read_text(encoding="utf-8")
    css = Path("jarvis/gui/static/style.css").read_text(encoding="utf-8")
    mc = Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")

    assert 'id="commandPaletteModal"' in html
    assert 'id="commandPaletteBtn"' in html
    assert 'id="commandPaletteInput"' in html
    assert "command_palette.js" in html
    assert "Ctrl</kbd>+<kbd>K" in html or "Ctrl+K" in html
    assert "openAriaCommandPalette" in js
    assert 'toLowerCase() !== "k"' in js or 'toLowerCase() === "k"' in js
    assert 'id: "search:memory"' in js
    assert "/api/knowledge/search" in js
    assert "fetchContentHits" in js
    assert "memory-item--flash" in js
    assert "Use model:" in js
    assert "command-palette-modal" in css
    assert "window.switchMcTab = switchMcTab" in mc
    assert Path("docs/ARIA_COMPETITIVE_ANALYSIS_V2.md").is_file()
    assert Path("docs/ARIA_GUI_INVENTORY_V2.md").is_file()
    assert "Ctrl</kbd>+<kbd>L" in html or "Ctrl+L" in html
    cal = Path("jarvis/gui/static/calendar.js").read_text(encoding="utf-8")
    app = Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "planner_tasks" in cal
    assert "cal-open-planner" in cal
    assert "calOpenJournalBtn" in cal
    assert "window.openCalendarDay" in cal
    assert "planner_tasks" in Path("jarvis/calendar_tab.py").read_text(encoding="utf-8")
    assert "async: true" in app
    assert "aria_theme" in app
    assert "window.loadGallery" in app or "window.loadGallery" in Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/gallery_view.js").is_file()
    assert "async function loadGallery" not in app
    assert "Memory exported" in app
    assert "dataset.bound === \"1\"" in Path("jarvis/gui/static/browser_panel.js").read_text(encoding="utf-8")
    assert "Could not switch project" in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "window.syncMuteButton" in Path("jarvis/gui/static/voice_bar.js").read_text(encoding="utf-8")
    assert 'dataset.bound === "1"' in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert 'dataset.bound === "1"' in Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    assert "Reindexing…" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")

    assert "act:backup" in js
    assert "act:theme-toggle" in js
    assert "journalOpenCalendarBtn" in html
    assert "window.setBujoTab" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css
    mt = Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "applyModuleFilter" in mt and "MODULE_NAV" in mt
    assert 'target === "workstation"' in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "created?.project?.slug" in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "Generation cancelled" in app
    assert "preferred_module" in app
    assert "preferred_module" in Path("jarvis/gui/server.py").read_text(encoding="utf-8")
    assert "Knowledge search unavailable" in js
    assert "Trusted device revoked" in Path("jarvis/gui/static/security_settings.js").read_text(encoding="utf-8")
    assert "Journal stats unavailable" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "Work schedule unavailable" in cal
    assert "Memory deleted" in app
    assert "ensureMcDelegates" in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "Conversation cleared" in app
    assert "act:clear-chat" in js
    assert "Memory load failed" in app

    assert not Path("jarvis/gui/static/browser.js").exists()
    assert Path("jarvis/gui/static/browser_panel.js").is_file()
    assert Path("jarvis/gui/static/ha_panel.js").is_file()
    assert "window.initHaPanel" in Path("jarvis/gui/static/ha_panel.js").read_text(encoding="utf-8")
    assert "function initHaPanel" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/upgrade_wizard.js").is_file()
    assert "function initUpgradeWizardModal" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "act:integrations-keys" in js
    assert "Restarting" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "Vision quality:" in app or "Vision quality:" in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")


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
