/** Primary view router — extracted from app.js.
 * Living Workspace: AriaHouse owns Rooms. Legacy inits skipped when native Rooms exist.
 */
(function () {
  const VIEW_PANELS = [
    "chatView", "dashboardView", "automationView", "workstationView", "modelsView", "codingView", "plannerView", "calendarView", "flytyingView", "projectsView",
    "makerView", "browserView", "securityView", "presenceView", "homeAutomationView", "auditView", "certificationView", "capabilitiesView", "integrationsView", "searchView", "settingsView", "voiceView", "visionView", "audioView", "journalView",
    "memoryView", "healthView", "galleryView", "videoView", "memeView", "documentsView", "connectionsView", "actionsView",
  ];

  function isLivingWorkspace() {
    return (
      document.documentElement.classList.contains("living-workspace") ||
      document.body?.classList.contains("living-workspace") ||
      document.body?.dataset.workspace === "1"
    );
  }

  /** Views with thin native Rooms that SKIP legacy init — Chat only after Phase 6.4 furnish. */
  function hasNativeRoom(view) {
    if (!isLivingWorkspace()) return false;
    const room = viewToRoom(view);
    /* Repair and Integrity are their own native Rooms — never workstation / Mission Control. */
    if (room === "repair" || room === "integrity") {
      return !!(
        window.AriaRoomKit?.get?.(room)?.enter ||
        (room === "repair" ? window.AriaRepairRoom : window.AriaIntegrityRoom)
      );
    }
    /* Phase 6.4: AriaFurnish reconnects full panels + inits for every Room except Chat */
    if (window.AriaFurnish?.enter) {
      return room === "chat" && !!window.AriaLivingRoom;
    }
    if (room === "chat") return !!window.AriaLivingRoom;
    return !!(window.AriaRoomKit?.get?.(room)?.enter || window.AriaHouse?.isNative?.(room));
  }

  let _lastRouterInit = { view: null, at: 0 };



  function runInits(view) {
    // The room shell also initialises this panel on the same transition, so a
    // repeat of the same view within a moment is that overlap, not navigation:
    // it fetched every panel twice. A genuine re-entry later still re-runs.
    const _now = Date.now();
    if (view === _lastRouterInit.view && _now - _lastRouterInit.at < 1200) return;
    _lastRouterInit = { view, at: _now };
    if (hasNativeRoom(view)) return;

    if (view === "dashboard" && window.initDashboard) window.initDashboard();
    else if (view !== "dashboard") window.stopDashboardClock?.();
    if (view === "automation" && window.initAutomation) window.initAutomation();
    if (view === "workstation" && window.initWorkstation) window.initWorkstation();
    if (view === "models" && window.initModelsHome) window.initModelsHome();
    if (view === "coding" && window.initCodingHome) window.initCodingHome();
    if (view === "planner" && window.initPlanner) window.initPlanner();
    if (view === "calendar" && window.initCalendar) window.initCalendar();
    if (view === "flytying" && window.initFlytying) window.initFlytying();
    if (view === "capabilities" && window.initCapabilities) window.initCapabilities();
    if (view === "integrations" && window.initIntegrationsHome) window.initIntegrationsHome();
    if (view === "search" && window.initSearchHome) window.initSearchHome();
    if (view === "settings" && window.initSettingsHome) window.initSettingsHome();
    if (view === "projects" && window.initProjects) window.initProjects();
    if (view === "maker" && window.initMakerLab) window.initMakerLab();
    if (view === "browser" && window.initBrowserPanel) window.initBrowserPanel();
    if (view === "browser" && window.initBrowserHome) window.initBrowserHome();
    if (view !== "browser" && window.stopBrowserPanelPoll) window.stopBrowserPanelPoll();
    if (view === "security" && window.initSecurity) { window.initSecurity(); window.refreshToolsSidebar?.(); }
    if (view === "presence" && window.initPresence) window.initPresence();
    if ((view === "homeAutomation" || view === "home_automation") && window.initHaPanel) {
      window.initHaPanel();
      window.loadSmarthomeHome?.();
    }
    if (view === "audit" && window.initAudit) window.initAudit();
    if (view === "certification" && window.initCertification) window.initCertification();
    if (view === "voice" && window.initVoiceTab) window.initVoiceTab();
    if (view === "vision" && window.initVisionHome) window.initVisionHome();
    if (view === "audio" && window.initAudio) window.initAudio();
    if (view === "journal" && window.initJournal) window.initJournal();
    if (view === "health" && window.initHealth) window.initHealth();
    if (view === "memory") window.loadMemoryBrowser?.();
    if (view === "gallery") window.loadGallery?.();
    if (view === "video" && typeof window.loadVideoGallery === "function") window.loadVideoGallery();
    else if (view === "video" && typeof loadVideoGallery === "function") loadVideoGallery();
    if (view === "meme" && typeof window.loadMemeGallery === "function") window.loadMemeGallery();
    else if (view === "meme" && typeof loadMemeGallery === "function") loadMemeGallery();
    if (view === "actions") window.loadActions?.(document.getElementById("actionsFilter")?.value);
    if (view === "documents") { window.initDocumentsTab?.(); window.loadDocumentsTab?.(); }
    if (view === "connections" && window.initConnections) window.initConnections();
  }

  function canonicalView(input) {
    if (!input) return "chat";
    let v = String(input).replace(/^#/, "").split(/[&?/]/)[0].trim();
    if (!v) return "chat";
    if (v === "mission" || v === "missionRoom" || v === "mission-control") v = "workstation";
    if (v === "home") v = "dashboard";
    if (v === "home_automation" || v === "smarthome") v = "homeAutomation";
    return v;
  }

  function viewToRoom(view) {
    view = canonicalView(view);
    const map = {
      chat: "chat",
      workstation: "mission",
      repair: "repair",
      integrity: "integrity",
      dashboard: "home",
      models: "providers",
      audit: "audit",
      certification: "integrity",
      presence: "presence",
      homeAutomation: "home_automation",
      home_automation: "home_automation",
      journal: "journal",
      video: "video",
      audio: "audio",
      browser: "browser",
      maker: "maker",
      meme: "meme",
      vision: "vision",
      connections: "connections",
      settings: "settings",
      capabilities: "capabilities",
      integrations: "integrations",
      security: "security",
      actions: "actions",
      voice: "voice",
      calendar: "calendar",
      planner: "planner",
      coding: "coding",
      automation: "automation",
    };
    if (map[view]) return map[view];
    const rooms = window.AriaWorkspaceRegistry?.rooms;
    if (Array.isArray(rooms)) {
      const hit = rooms.find((r) => r.viewId === view || r.id === view);
      if (hit?.id) return hit.id;
    }
    return view;
  }

  let _currentView = null;
  let _switching = false;
  let _applyingHash = false;

  function syncHash(view, { push = false } = {}) {
    const canon = canonicalView(view);
    const hash = `#${canon}`;
    const url = `${window.location.pathname}${window.location.search}${hash}`;
    const state = { ariaView: canon, ariaRoom: viewToRoom(canon) };
    if (_applyingHash) return;
    _applyingHash = true;
    try {
      const same =
        window.location.hash === hash &&
        window.history.state &&
        window.history.state.ariaView === canon;
      if (push && !same) {
        window.history.pushState(state, "", url);
      } else if (!same) {
        window.history.replaceState(state, "", url);
      }
      /* Some embedded webviews ignore replaceState hash-only updates.
         Assigning location.hash is the reliable address-bar sync. */
      if (window.location.hash !== hash) {
        window.location.hash = canon;
      }
    } catch (_) {
      try {
        if (window.location.hash !== hash) window.location.hash = canon;
      } catch (__) {
        /* ignore */
      }
    } finally {
      _applyingHash = false;
    }
  }

  function switchToView(view, opts) {
    if (!view) return;
    const fromHistory = !!(opts && opts.fromHistory);
    const lockEl = document.getElementById("lockScreen");
    if (lockEl && !lockEl.classList.contains("hidden")) {
      return;
    }
    view = canonicalView(view);
    if (_switching) return;
    _switching = true;
    try {
    const splitOn = !!window.AriaSplitView?.getState?.()?.enabled;
    const targetId = `${view}View`;

    document.querySelectorAll(".view-tab").forEach((t) => {
      if (splitOn) {
        const st = window.AriaSplitView.getState();
        t.classList.toggle("active", t.dataset.view === st.primary || t.dataset.view === st.secondary || t.dataset.view === view);
      } else {
        t.classList.toggle("active", t.dataset.view === view);
      }
    });

    if (isLivingWorkspace() && !splitOn) {
      runInits(view);
      try {
        window.AriaHouse?.enter?.(viewToRoom(view));
      } catch (_) {
        /* ignore */
      }
    } else {
      if (!splitOn) {
        VIEW_PANELS.forEach((id) => {
          document.getElementById(id)?.classList.toggle("hidden", id !== targetId);
        });
      }
      runInits(view);
      const panel = document.getElementById(targetId);
      if (panel && !splitOn) {
        if (!panel.hasAttribute("tabindex")) panel.setAttribute("tabindex", "-1");
        try { panel.focus({ preventScroll: true }); } catch (_) { /* ignore */ }
      }
    }

    const tab = document.querySelector(`.view-tab[data-view="${view}"]`);
    tab?.scrollIntoView({ block: "nearest", inline: "nearest" });
    const prev = _currentView;
    _currentView = view;
    try {
      if (!fromHistory) syncHash(view, { push: !!(prev && prev !== view) });
    } catch (_) { /* ignore */ }
    try {
      window.AriaLivingInterface?.setRoom?.(view);
    } catch (_) { /* ignore */ }
    try {
      window.dispatchEvent(new CustomEvent("aria-view-change", { detail: { view, room: viewToRoom(view) } }));
    } catch (_) { /* ignore */ }
    } finally {
      _switching = false;
    }
  }

  window.switchToView = switchToView;
  window.AriaViewRouter = {
    switchToView,
    canonicalView,
    viewToRoom,
    syncHash,
    currentView: () => _currentView,
    applyingHash: () => _applyingHash,
  };

  window.addEventListener("popstate", (ev) => {
    if (_applyingHash || _switching) return;
    const view = (ev.state && ev.state.ariaView) || canonicalView(window.location.hash);
    if (view && view !== _currentView) switchToView(view, { fromHistory: true });
  });

  window.addEventListener("hashchange", () => {
    if (_applyingHash || _switching) return;
    const raw = String(window.location.hash || "").replace(/^#/, "").split(/[&?/]/)[0].trim();
    const view = canonicalView(raw);
    if (view && view !== _currentView) switchToView(view, { fromHistory: true });
    if (view && raw && raw !== view) syncHash(view);
  });

  document.querySelectorAll(".view-tab").forEach((tab) => {
    tab.addEventListener("click", () => switchToView(tab.dataset.view));
  });
})();
