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
    from pathlib import Path

    src = Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    coding = Path("jarvis/gui/static/coding_panel.js").read_text(encoding="utf-8")
    blob = src + coding
    assert 'q.set("deep", "0")' in blob
    assert "AbortController" in blob
    assert "Checking…" in blob


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
    media_js = Path("jarvis/gui/static/media_lightbox.js").read_text(encoding="utf-8")
    assert "inpaintDenoise" in app_js or "inpaintDenoise" in media_js
    assert "refreshSidebarVideoStatus" in app_js or "refreshSidebarVideoStatus" in Path("jarvis/gui/static/video_sidebar.js").read_text(encoding="utf-8")
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
    assert "window.loadMemoryBrowser" in app_js or "window.loadMemoryBrowser" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    media_js = Path("jarvis/gui/static/media_lightbox.js").read_text(encoding="utf-8")
    assert "window.closeImageLightbox" in app_js or "window.closeImageLightbox" in media_js
    assert "media_lightbox.js" in html
    assert "coding_panel.js" in html
    assert "models_panel.js" in html
    assert "uncensored_mode.js" in html
    assert "startup_overlay.js" in html
    assert "wakeword_chat.js" in html
    assert "chat_branches.js" in html
    assert "video_sidebar.js" in html
    assert "sidebar_chrome.js" in html
    assert "window.loadBranches" in Path("jarvis/gui/static/chat_branches.js").read_text(encoding="utf-8")
    assert "window.waitForServices" in Path("jarvis/gui/static/startup_overlay.js").read_text(encoding="utf-8")
    assert "window.ariaPostStartup" in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.restoreUncensoredSession" in Path("jarvis/gui/static/uncensored_mode.js").read_text(encoding="utf-8")
    assert "window.loadModelSettings" in Path("jarvis/gui/static/models_panel.js").read_text(encoding="utf-8")
    assert "async function loadModelSettings" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    coding_js = Path("jarvis/gui/static/coding_panel.js").read_text(encoding="utf-8")
    assert "window.loadCodingPanel" in coding_js
    assert "async function loadCodingPanel" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")

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
    assert "async: true" in Path("jarvis/gui/static/chat_export.js").read_text(encoding="utf-8")
    assert "aria_theme" in app or "aria_theme" in Path("jarvis/gui/static/theme.js").read_text(encoding="utf-8")
    assert "theme.js" in html
    assert "window.loadGallery" in app or "window.loadGallery" in Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/gallery_view.js").is_file()
    assert Path("jarvis/gui/static/memory_browser.js").is_file()
    assert Path("jarvis/gui/static/image_engine.js").is_file()
    assert Path("jarvis/gui/static/documents.js").is_file()
    assert "async function loadDocumentsTab" not in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    app_js = Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    coding_js = Path("jarvis/gui/static/coding_panel.js").read_text(encoding="utf-8")
    assert "Code index rebuilt" in app_js or "Code index rebuilt" in coding_js
    assert "Poll failed:" in Path("jarvis/gui/static/audit.js").read_text(encoding="utf-8")
    assert "async function loadCheatsheets" not in app
    assert "function syncComfySettings" not in app
    assert "window.syncComfySettings" in Path("jarvis/gui/static/image_engine.js").read_text(encoding="utf-8")
    assert "async function loadGallery" not in app
    assert "Memory exported" in app or "Memory exported" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "dataset.bound === \"1\"" in Path("jarvis/gui/static/browser_panel.js").read_text(encoding="utf-8")
    assert "Could not switch project" in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "window.syncMuteButton" in Path("jarvis/gui/static/voice_bar.js").read_text(encoding="utf-8")
    assert 'dataset.bound === "1"' in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert 'dataset.bound === "1"' in Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    assert "Reindexing…" in Path("jarvis/gui/static/documents.js").read_text(encoding="utf-8")

    assert "act:backup" in js
    assert "act:theme-toggle" in js
    assert "act:journal-rapid" in js
    assert "act:planner-task" in js
    assert "act:calendar-today" in js
    assert "act:security" in js
    assert "act:webcam" in js
    assert "act:gallery" in js
    assert "act:ics-wizard" in js
    assert "act:checklist" in js
    assert "act:meme-studio" in js
    assert "act:mute-voice" in js
    assert "act:stop-speaking" in js
    assert "act:lock-security" in js
    assert "act:pomodoro" in js
    assert "act:open-meme" not in js
    assert "journalOpenDocumentsBtn" in html
    assert "documentsOpenJournalBtn" in html
    assert "plannerOpenDocumentsBtn" in html
    assert "dashboardOpenCalendarBtn" in html
    assert "stopDashboardClock" in Path("jarvis/gui/static/view_router.js").read_text(encoding="utf-8")
    assert "audit-empty-run" in html
    assert "act:open-projects" in js
    assert "act:debug-bundle" in js
    assert "act:browser-task" in js
    assert "search:gallery-prompt" in js
    assert "presenceOpenSecurityBtn" in html
    assert "journalOpenCalendarBtn" in html
    assert "journalOpenAudioBtn" in html
    assert "memoryOpenJournalBtn" in html
    assert "memoryOpenDocumentsBtn" in html
    assert "calendarOpenDocumentsBtn" in html
    assert "memoryOpenProjectsBtn" in html
    assert "projectsOpenMemoryBtn" in html
    assert "documentsOpenMemoryBtn" in html
    assert "documentsOpenCalendarBtn" in html
    assert "documentsOpenChatBtn" in html
    assert "documentsOpenProjectsBtn" in html
    assert "auditOpenMcBtn" in html
    assert "mcOpenAuditBtn" in html
    assert "dashAiSuggestChips" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "document.hidden" in Path("jarvis/gui/static/tools_sidebar.js").read_text(encoding="utf-8")
    assert "Slice complete" in Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    assert "documentsOpenIcsBtn" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "ICS feed saved" in Path("jarvis/gui/static/calendar.js").read_text(encoding="utf-8")
    assert "calendarIcsUrl" in Path("jarvis/gui/static/command_palette.js").read_text(encoding="utf-8")
    assert "Video settings saved" in Path("jarvis/gui/static/video_studio.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/vision_settings.js").is_file()
    assert Path("jarvis/gui/static/free_vram.js").is_file()
    assert Path("jarvis/gui/static/profile_controls.js").is_file()
    assert Path("jarvis/gui/static/coding_quick.js").is_file()
    assert Path("jarvis/gui/static/chat_media.js").is_file()
    assert Path("jarvis/gui/static/crop_webcam.js").is_file()
    assert Path("jarvis/gui/static/vision_drop.js").is_file()
    assert Path("jarvis/gui/static/attachment_compare.js").is_file()
    assert Path("jarvis/gui/static/media_jobs.js").is_file()
    assert Path("jarvis/gui/static/coding_jobs.js").is_file()
    assert Path("jarvis/gui/static/media_urls.js").is_file()
    assert Path("jarvis/gui/static/coding_proposals.js").is_file()
    assert Path("jarvis/gui/static/chat_images.js").is_file()
    assert Path("jarvis/gui/static/chat_progress.js").is_file()
    assert Path("jarvis/gui/static/chat_video.js").is_file()
    assert Path("jarvis/gui/static/chat_send.js").is_file()
    assert Path("jarvis/gui/static/chat_done.js").is_file()
    assert Path("jarvis/gui/static/chat_messages.js").is_file()
    assert "coding_quick.js" in html
    assert "chat_media.js" in html
    assert "crop_webcam.js" in html
    assert "vision_drop.js" in html
    assert "attachment_compare.js" in html
    assert "media_jobs.js" in html
    assert "coding_jobs.js" in html
    assert "media_urls.js" in html
    assert "coding_proposals.js" in html
    assert "chat_images.js" in html
    assert "chat_progress.js" in html
    assert "chat_video.js" in html
    assert "chat_send.js" in html
    assert "chat_done.js" in html
    assert "chat_messages.js" in html
    assert "window.sendQuickCodingMessage" in Path("jarvis/gui/static/coding_quick.js").read_text(encoding="utf-8")
    assert "window.showGeneratedImage" in Path("jarvis/gui/static/chat_media.js").read_text(encoding="utf-8")
    assert "window.jarvisSendToChat" in Path("jarvis/gui/static/chat_media.js").read_text(encoding="utf-8")
    assert "window.jarvisSendToChat =" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "actionsEmptyChatBtn" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "plannerEmptyAddBtn" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "plannerEmptyCalBtn" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "skillsEmptyChatBtn" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "bujoEmptyGalleryBtn" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "act:compare-images" in Path("jarvis/gui/static/command_palette.js").read_text(encoding="utf-8")
    assert "Could not restore uncensored session" in Path("jarvis/gui/static/uncensored_mode.js").read_text(encoding="utf-8")
    assert "sessionStorage.removeItem(UNCENSORED_SESSION_KEY)" in Path("jarvis/gui/static/uncensored_mode.js").read_text(encoding="utf-8")
    assert "window.openCropModal" in Path("jarvis/gui/static/crop_webcam.js").read_text(encoding="utf-8")
    assert "window.captureWebcamAttachment" in Path("jarvis/gui/static/crop_webcam.js").read_text(encoding="utf-8")
    assert "window.jarvisAttach" in Path("jarvis/gui/static/chat_attach.js").read_text(encoding="utf-8")
    assert "async function openCropModal" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert 'getElementById("webcamBtn")' not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function initVisionDropPaste" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function updateAttachmentPreview" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "updateAttachmentPreview," in Path("jarvis/gui/static/attachment_compare.js").read_text(encoding="utf-8")
    assert "set pendingFile(v)" in Path("jarvis/gui/static/chat_attach.js").read_text(encoding="utf-8")
    assert "window.initVisionDropPaste" in Path("jarvis/gui/static/vision_drop.js").read_text(encoding="utf-8")
    assert "assignMultipleAttachments" in Path("jarvis/gui/static/attachment_compare.js").read_text(encoding="utf-8")
    assert "Could not resume media jobs" in Path("jarvis/gui/static/media_jobs.js").read_text(encoding="utf-8")
    assert "async function pollMediaJob" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.pollMediaJob" in Path("jarvis/gui/static/media_jobs.js").read_text(encoding="utf-8") or "pollMediaJob," in Path("jarvis/gui/static/media_jobs.js").read_text(encoding="utf-8")
    assert "projectsEmptyCreateBtn" in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "Lost contact while installing NSFW" in Path("jarvis/gui/static/image_engine.js").read_text(encoding="utf-8")
    assert "mcEmptyActivityDashBtn" in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "docsEmptyChatBtn" in Path("jarvis/gui/static/documents.js").read_text(encoding="utf-8")
    assert "securityEmptyPresenceBtn" in Path("jarvis/gui/static/security_settings.js").read_text(encoding="utf-8")
    assert "makerEmptyHelloBtn" in Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    assert "flyEmptyScanBtn" in Path("jarvis/gui/static/flytying.js").read_text(encoding="utf-8")
    assert "flyEmptyVideoBtn" in Path("jarvis/gui/static/flytying.js").read_text(encoding="utf-8")
    assert "Coding job polling failed" in Path("jarvis/gui/static/coding_jobs.js").read_text(encoding="utf-8")
    assert "async function pollCodingJob" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function resolveVideoUrl" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function attachProposalExtras" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function resolveImageUrl" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function resolveImageUrl" in Path("jarvis/gui/static/chat_images.js").read_text(encoding="utf-8")
    assert "appendGeneratedImage," in Path("jarvis/gui/static/chat_images.js").read_text(encoding="utf-8")
    assert "attachProposalExtras," in Path("jarvis/gui/static/coding_proposals.js").read_text(encoding="utf-8")
    assert "Failed to apply changes" in Path("jarvis/gui/static/coding_proposals.js").read_text(encoding="utf-8")
    assert "calEmptyAddBtn" in Path("jarvis/gui/static/calendar.js").read_text(encoding="utf-8")
    assert "Connection restored" in Path("jarvis/gui/static/modules/health.mjs").read_text(encoding="utf-8")
    assert "Forked branch:" in Path("jarvis/gui/static/chat_branches.js").read_text(encoding="utf-8")
    assert "messages.innerHTML = \"\";" in Path("jarvis/gui/static/chat_branches.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/chat_branches.js").read_text(encoding="utf-8").index("if (!res.ok) throw") < Path("jarvis/gui/static/chat_branches.js").read_text(encoding="utf-8").index("messages.innerHTML = \"\";")
    assert "audio-empty-chat" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "function resolveVideoUrl" in Path("jarvis/gui/static/media_urls.js").read_text(encoding="utf-8")
    assert "attachMediaLoadError," in Path("jarvis/gui/static/media_urls.js").read_text(encoding="utf-8")
    assert "memoryEmptyChatBtn" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "mcEmptyRecChatBtn" in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "galleryEmptyPromptBtn" in Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert "memeEmptyChatBtn" in Path("jarvis/gui/static/meme_studio.js").read_text(encoding="utf-8")
    assert "act:resume-media-jobs" in Path("jarvis/gui/static/command_palette.js").read_text(encoding="utf-8")
    assert "videoEmptyChatBtn" in Path("jarvis/gui/static/video_studio.js").read_text(encoding="utf-8")
    assert "Could not load voice settings" in Path("jarvis/gui/static/voice_bar.js").read_text(encoding="utf-8")
    assert "Media job resume failed" in Path("jarvis/gui/static/media_jobs.js").read_text(encoding="utf-8")
    assert "function showProgress" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function setChatBusy" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.jarvisChat" in Path("jarvis/gui/static/chat_state.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/api_key_fetch.js").is_file()
    assert "api_key_fetch.js" in html
    assert "initApiKeyFetch" in Path("jarvis/gui/static/api_key_fetch.js").read_text(encoding="utf-8")
    assert "initApiKeyFetch" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "chat_state.js" in html
    assert "function showProgress" in Path("jarvis/gui/static/chat_progress.js").read_text(encoding="utf-8")
    assert "setChatBusy," in Path("jarvis/gui/static/chat_progress.js").read_text(encoding="utf-8")
    assert "const resolveVideoUrl" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "researchEmptyRunBtn" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "knowledgeEmptyChatBtn" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "profileEmptyEditBtn" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "mcEmptyRoutingChatBtn" in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "act:run-research" in Path("jarvis/gui/static/command_palette.js").read_text(encoding="utf-8")
    assert "function appendAuthenticatedVideo" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "appendGeneratedVideo," in Path("jarvis/gui/static/chat_video.js").read_text(encoding="utf-8")
    assert "browserEmptyFocusUrl" in Path("jarvis/gui/static/browser_panel.js").read_text(encoding="utf-8")
    assert "function buildImageMessageHtml" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "buildImageMessageHtml," in Path("jarvis/gui/static/chat_images.js").read_text(encoding="utf-8")
    assert "buildDataTableHtml," in Path("jarvis/gui/static/chat_images.js").read_text(encoding="utf-8")
    assert "async function sendMessage" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "async function sendMessage" in Path("jarvis/gui/static/chat_send.js").read_text(encoding="utf-8")
    assert "get useStreaming" in Path("jarvis/gui/static/chat_state.js").read_text(encoding="utf-8")
    assert "window.finishSendUi" in Path("jarvis/gui/static/chat_attach.js").read_text(encoding="utf-8")
    assert "function handleDone" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function handleDone" in Path("jarvis/gui/static/chat_done.js").read_text(encoding="utf-8")
    assert "showChatWarnings," in Path("jarvis/gui/static/chat_done.js").read_text(encoding="utf-8") or "showChatWarnings }" in Path("jarvis/gui/static/chat_done.js").read_text(encoding="utf-8")
    assert "function addMessage" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function addMessage" in Path("jarvis/gui/static/chat_messages.js").read_text(encoding="utf-8")
    assert "Drop PDFs/DOCX" in Path("jarvis/gui/static/documents.js").read_text(encoding="utf-8")
    assert "audit-empty-run" in Path("jarvis/gui/static/audit.js").read_text(encoding="utf-8")
    assert "function sendQuickCodingMessage" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function showGeneratedImage" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "function showAudioPlayer" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "appendGeneratedImage," in Path("jarvis/gui/static/chat_images.js").read_text(encoding="utf-8")
    assert "aria-labelledby=\"cropModalTitle\"" in html
    assert "aria-labelledby=\"haSetupModalTitle\"" in html
    assert "cropModal" in Path("jarvis/gui/static/modal_chrome.js").read_text(encoding="utf-8")
    assert "journalOpenMemoryBtn" in html
    assert "memoryOpenBrowserBtn" in html
    assert "dashboardOpenMcBtn" in html
    assert "actionsOpenChatBtn" in html
    assert "Could not load actions" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "profile_controls.js" in html
    assert "Profile switch failed" in Path("jarvis/gui/static/profile_controls.js").read_text(encoding="utf-8")
    assert 'getElementById("profileSelect")' not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert 'getElementById("personalitySelect")' not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.freeJarvisVram" in Path("jarvis/gui/static/free_vram.js").read_text(encoding="utf-8")
    assert "window.vramPreflight" in Path("jarvis/gui/static/free_vram.js").read_text(encoding="utf-8")
    assert "async function vramPreflight" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "async function freeJarvisVram" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "renderAudioStatus" in Path("jarvis/gui/static/modules/health.mjs").read_text(encoding="utf-8")
    assert "async function loadHealth" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "async function pollLive" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "export async function loadHealth" in Path("jarvis/gui/static/modules/health.mjs").read_text(encoding="utf-8")
    assert "document.hidden || mediaWorkActive()" in Path("jarvis/gui/static/modules/health.mjs").read_text(encoding="utf-8")
    assert "Could not save fly tying model" in Path("jarvis/gui/static/flytying.js").read_text(encoding="utf-8")
    assert "Library:" in Path("jarvis/gui/static/flytying.js").read_text(encoding="utf-8")
    assert "alert(" not in Path("jarvis/gui/static/flytying.js").read_text(encoding="utf-8")
    assert "alert(" not in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "alert(" not in Path("jarvis/gui/static/smarthome.js").read_text(encoding="utf-8")
    assert "alert(" not in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "Describe what to upgrade." in Path("jarvis/gui/static/upgrade_wizard.js").read_text(encoding="utf-8")
    assert "alert(" not in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "Could not save profile" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "alert(data.error || \"Could not save profile\")" not in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "alert(" not in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "Choose a cheatsheet first" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "Profile questionnaire skipped" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "plannerOpenCalendarBtn" in html
    assert "calendarOpenPlannerBtn" in html
    assert "calendarOpenJournalBtn" in html
    assert "galleryOpenMakerBtn" in html
    assert "galleryOpenVideoBtn" in html
    assert "galleryOpenMemeBtn" in html
    assert "videoOpenGalleryBtn" in html
    assert "memeOpenGalleryBtn" in html
    assert "audioOpenVoiceBtn" in html
    assert "voiceOpenAudioBtn" in html
    assert "browserOpenMemoryBtn" in html
    assert "securityOpenPresenceBtn" in html
    assert "aria-labelledby=\"projectPickerTitle\"" in html
    assert "aria-labelledby=\"settingsModalTitle\"" in html
    assert "flytyingOpenGalleryBtn" in html
    assert "cadOpenGalleryBtn" in html
    assert "Could not load projects" in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "Security status unavailable" in Path("jarvis/gui/static/security_settings.js").read_text(encoding="utf-8")
    assert "Voice tab load failed" in Path("jarvis/gui/static/voice_tab.js").read_text(encoding="utf-8")
    assert "Browser agent unavailable" in Path("jarvis/gui/static/browser_panel.js").read_text(encoding="utf-8")
    assert "toastOnError" in Path("jarvis/gui/static/browser_panel.js").read_text(encoding="utf-8")
    assert "document.hidden" in Path("jarvis/gui/static/browser_panel.js").read_text(encoding="utf-8")
    assert "document.hidden" in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "Planner load failed" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "News briefing failed" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "Diarize failed" in Path("jarvis/gui/static/audio_advanced.js").read_text(encoding="utf-8")
    assert "window.loadVisionSettings" in Path("jarvis/gui/static/vision_settings.js").read_text(encoding="utf-8")
    assert "async function loadVisionSettings" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "Vision quality:" in Path("jarvis/gui/static/vision_settings.js").read_text(encoding="utf-8")
    assert "Normalize failed" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "window.setBujoTab" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "showAriaToast" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "Journal exported" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css
    assert "button:focus-visible" in css
    assert "toastOnError" in Path("jarvis/gui/static/maker.js").read_text(encoding="utf-8")
    mt = Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "applyModuleFilter" in mt and "MODULE_NAV" in mt
    assert 'target === "workstation"' in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "created?.project?.slug" in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "title.textContent = p.title" in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "li.innerHTML = `<strong>${p.title}" not in Path("jarvis/gui/static/projects.js").read_text(encoding="utf-8")
    assert "modelsEl.replaceChildren" in Path("jarvis/gui/static/models_panel.js").read_text(encoding="utf-8")
    assert "document.hidden || window.mediaWorkActive" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "if (document.hidden) return;" in Path("jarvis/gui/static/presence.js").read_text(encoding="utf-8")
    assert "if (document.hidden) return;" in Path("jarvis/gui/static/world_state_hud.js").read_text(encoding="utf-8")
    assert "document.hidden || window.mediaWorkActive" in Path("jarvis/gui/static/wakeword_chat.js").read_text(encoding="utf-8")
    assert "if (document.hidden) return;" in Path("jarvis/gui/static/modules/jobs.mjs").read_text(encoding="utf-8")
    assert "if (document.hidden) return;" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "if (document.hidden) return;" in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "audioEmptyRecordBtn" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/editor_context.js").is_file()
    assert "editor_context.js" in html
    assert "async function loadEditorContext" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.loadSuggestions" in Path("jarvis/gui/static/editor_context.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/view_router.js").is_file()
    assert "view_router.js" in html
    assert "function switchToView" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.switchToView" in Path("jarvis/gui/static/view_router.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/chat_export.js").is_file()
    assert "chat_export.js" in html
    assert "exportChatBtn" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "Pop-up blocked" in Path("jarvis/gui/static/chat_export.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/chat_format.js").is_file()
    assert "chat_format.js" in html
    assert "function escapeHtml" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.createCopyButton" in Path("jarvis/gui/static/chat_format.js").read_text(encoding="utf-8")
    assert "bujoEmptyGratitudeBtn" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "audioSearchEmptyChatBtn" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "chatSessionsEmptyNewBtn" in Path("jarvis/gui/static/chat_sessions.js").read_text(encoding="utf-8")
    assert "Could not start push-to-talk" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "data.message || data.error || \"Could not start push-to-talk\"" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "codingEmptyChatBtn" in Path("jarvis/gui/static/coding_panel.js").read_text(encoding="utf-8")
    assert "jobsEmptyChatBtn" in Path("jarvis/gui/static/modules/jobs.mjs").read_text(encoding="utf-8")
    assert "promptHistoryEmptyBtn" in Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert "Record failed" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "MusicGen failed" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "Batch failed" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "flytyingScanModal" in Path("jarvis/gui/static/modal_chrome.js").read_text(encoding="utf-8")
    assert "window.stopFlytyingCameraScan" in Path("jarvis/gui/static/flytying.js").read_text(encoding="utf-8")
    assert "refreshWorldStateHud" not in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "bindBarNavigation" in Path("jarvis/gui/static/world_state_hud.js").read_text(encoding="utf-8")
    assert "openFromBar" in Path("jarvis/gui/static/world_state_hud.js").read_text(encoding="utf-8")
    assert "Home Assistant offline" in Path("jarvis/gui/static/world_state_hud.js").read_text(encoding="utf-8")
    assert 'window.switchToView("chat")' in Path("jarvis/gui/static/coding_quick.js").read_text(encoding="utf-8")
    assert "dashSuggestChatBtn" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "bujoProjectEmptyChatBtn" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "Gratitude added" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "panel.focus" in Path("jarvis/gui/static/view_router.js").read_text(encoding="utf-8")
    assert "flyEmptySeasonalSearchBtn" in Path("jarvis/gui/static/flytying.js").read_text(encoding="utf-8")
    assert 'modal.dataset.retake === "1"' in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "Generation cancelled" in Path("jarvis/gui/static/chat_progress.js").read_text(encoding="utf-8")
    assert "preferred_module" in Path("jarvis/gui/static/chat_send.js").read_text(encoding="utf-8")
    assert "preferred_module" in Path("jarvis/gui/server.py").read_text(encoding="utf-8")
    assert "Knowledge search unavailable" in js
    assert "Trusted device revoked" in Path("jarvis/gui/static/security_settings.js").read_text(encoding="utf-8")
    assert "Journal stats unavailable" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "Work schedule unavailable" in cal
    assert "Memory deleted" in app or "Memory deleted" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "ensureMcDelegates" in Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert "Conversation cleared" in Path("jarvis/gui/static/chat_controls.js").read_text(encoding="utf-8")
    assert "initChatControls" in Path("jarvis/gui/static/chat_controls.js").read_text(encoding="utf-8")
    assert "chat_controls.js" in Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert "act:read-aloud" in js
    assert "act:ha-test" in js
    assert "act:image-engine" in js
    assert "ask:aria" in js
    assert "Ask Aria:" in js
    assert "dashSceneEmptyHaBtn" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "Memory settings unavailable" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert "Video trimmed" in Path("jarvis/gui/static/video_studio.js").read_text(encoding="utf-8")
    assert "bujoSearchEmptyDailyBtn" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "Collection created" in Path("jarvis/gui/static/journal.js").read_text(encoding="utf-8")
    assert "Home Assistant status unavailable" in Path("jarvis/gui/static/ha_panel.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/branding.js").is_file()
    assert "branding.js" in html
    assert "function applyBranding" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.applyBranding" in Path("jarvis/gui/static/branding.js").read_text(encoding="utf-8")
    assert "Upscale failed" in Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/chat_meta.js").is_file()
    assert "chat_meta.js" in html
    assert "function applyAssistantMeta" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "window.applyAssistantMeta" in Path("jarvis/gui/static/chat_meta.js").read_text(encoding="utf-8")
    assert "Could not leave uncensored mode" in Path("jarvis/gui/static/uncensored_mode.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/chat_attach.js").is_file()
    assert "chat_attach.js" in html
    assert "window.jarvisAttach" in Path("jarvis/gui/static/chat_attach.js").read_text(encoding="utf-8")
    assert "window.finishSendUi" in Path("jarvis/gui/static/chat_attach.js").read_text(encoding="utf-8")
    assert "window.jarvisAttach =" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/chat_input.js").is_file()
    assert "chat_input.js" in html
    assert "window.resizeMessageInput" in Path("jarvis/gui/static/chat_input.js").read_text(encoding="utf-8")
    assert "window.forkBranchFromIndex" in Path("jarvis/gui/static/chat_branches.js").read_text(encoding="utf-8")
    assert "Could not load models" in Path("jarvis/gui/static/models_panel.js").read_text(encoding="utf-8")
    assert "act:clear-chat" in js
    assert "Memory load failed" in app or "Memory load failed" in Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")

    assert not Path("jarvis/gui/static/browser.js").exists()
    assert Path("jarvis/gui/static/browser_panel.js").is_file()
    assert Path("jarvis/gui/static/ha_panel.js").is_file()
    assert "window.initHaPanel" in Path("jarvis/gui/static/ha_panel.js").read_text(encoding="utf-8")
    assert "function initHaPanel" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/upgrade_wizard.js").is_file()
    assert "function initUpgradeWizardModal" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/git_panel.js").is_file()
    assert "window.loadGitStatus" in Path("jarvis/gui/static/git_panel.js").read_text(encoding="utf-8")
    assert "async function loadGitStatus" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/chat_model_select.js").is_file()
    assert "window.loadChatModelSelect" in Path("jarvis/gui/static/chat_model_select.js").read_text(encoding="utf-8")
    assert "async function loadChatModelSelect" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert Path("jarvis/gui/static/lan_access.js").is_file()
    assert "window.showApiKeyModal" in Path("jarvis/gui/static/lan_access.js").read_text(encoding="utf-8")
    assert "function showApiKeyModal" not in Path("jarvis/gui/static/app.js").read_text(encoding="utf-8")
    assert "lan_access.js" in html
    assert "skip-link" in html
    assert 'id="mainContent"' in html
    assert ".skip-link" in css
    assert "Transcript copied" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "function audioStatus" in Path("jarvis/gui/static/audio.js").read_text(encoding="utf-8")
    assert "Task added" in Path("jarvis/gui/static/planner.js").read_text(encoding="utf-8")
    assert "Kasa unavailable" in Path("jarvis/gui/static/smarthome.js").read_text(encoding="utf-8") or "Kasa: unavailable" in Path("jarvis/gui/static/smarthome.js").read_text(encoding="utf-8")
    assert "act:integrations-keys" in js
    assert "Restarting" in Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    assert "Vision quality:" in app or "Vision quality:" in Path("jarvis/gui/static/vision_settings.js").read_text(encoding="utf-8")


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
