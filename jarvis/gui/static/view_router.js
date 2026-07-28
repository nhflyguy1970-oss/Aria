/** Primary view router — extracted from app.js. */
(function () {
  const VIEW_PANELS = [
    "chatView", "dashboardView", "workstationView", "plannerView", "calendarView", "flytyingView", "projectsView",
    "makerView", "browserView", "securityView", "presenceView", "auditView", "voiceView", "audioView", "journalView",
    "memoryView", "galleryView", "videoView", "memeView", "documentsView", "connectionsView", "actionsView",
  ];

  function switchToView(view) {
    if (!view) return;
    document.querySelectorAll(".view-tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.view === view);
    });
    const targetId = `${view}View`;
    VIEW_PANELS.forEach((id) => {
      document.getElementById(id)?.classList.toggle("hidden", id !== targetId);
    });
    if (view === "dashboard" && window.initDashboard) window.initDashboard();
    else if (view !== "dashboard") window.stopDashboardClock?.();
    if (view === "workstation" && window.initWorkstation) window.initWorkstation();
    if (view === "planner" && window.initPlanner) window.initPlanner();
    if (view === "calendar" && window.initCalendar) window.initCalendar();
    if (view === "flytying" && window.initFlytying) window.initFlytying();
    if (view === "projects" && window.initProjects) window.initProjects();
    if (view === "maker" && window.initMakerLab) window.initMakerLab();
    if (view === "browser" && window.initBrowserPanel) window.initBrowserPanel();
    if (view !== "browser" && window.stopBrowserPanelPoll) window.stopBrowserPanelPoll();
    if (view === "security" && window.initSecurity) { window.initSecurity(); window.refreshToolsSidebar?.(); }
    if (view === "presence" && window.initPresence) window.initPresence();
    if (view === "audit" && window.initAudit) window.initAudit();
    if (view === "voice" && window.initVoiceTab) window.initVoiceTab();
    if (view === "audio" && window.initAudio) window.initAudio();
    if (view === "journal" && window.initJournal) window.initJournal();
    if (view === "memory") window.loadMemoryBrowser?.();
    if (view === "gallery") window.loadGallery?.();
    if (view === "video" && typeof window.loadVideoGallery === "function") window.loadVideoGallery();
    else if (view === "video" && typeof loadVideoGallery === "function") loadVideoGallery();
    if (view === "meme" && typeof window.loadMemeGallery === "function") window.loadMemeGallery();
    else if (view === "meme" && typeof loadMemeGallery === "function") loadMemeGallery();
    if (view === "actions") window.loadActions?.(document.getElementById("actionsFilter")?.value);
    if (view === "documents") { window.initDocumentsTab?.(); window.loadDocumentsTab?.(); }
    if (view === "connections" && window.initConnections) window.initConnections();

    const tab = document.querySelector(`.view-tab[data-view="${view}"]`);
    tab?.scrollIntoView({ block: "nearest", inline: "nearest" });
    const panel = document.getElementById(targetId);
    if (panel) {
      if (!panel.hasAttribute("tabindex")) panel.setAttribute("tabindex", "-1");
      try { panel.focus({ preventScroll: true }); } catch (_) { /* ignore */ }
    }
    try {
      const hash = `#${view}`;
      if (window.location.hash !== hash) {
        history.replaceState(null, "", `${window.location.pathname}${window.location.search}${hash}`);
      }
    } catch (_) { /* ignore */ }
  }

  window.switchToView = switchToView;

  document.querySelectorAll(".view-tab").forEach((tab) => {
    tab.addEventListener("click", () => switchToView(tab.dataset.view));
  });
})();
