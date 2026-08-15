/**
 * Phase 6.4 — Furnish the House.
 * Reconnect full original Aria panels onto the Living Workspace stage.
 * Thin native shells are not a substitute for original capability.
 */
(function () {
  "use strict";

  /** room id → legacy view id (without View suffix) */
  const ROOM_VIEW = {
    chat: "chat",
    flytying: "flytying",
    health: "health",
    mission: "workstation",
    documents: "documents",
    coding: "coding",
    projects: "projects",
    planner: "planner",
    calendar: "calendar",
    gallery: "gallery",
    search: "search",
    memory: "memory",
    voice: "voice",
    automation: "automation",
    providers: "models",
    home: "dashboard",
    home_automation: "homeAutomation",
    presence: "presence",
    /* integrity + repair: native Rooms — never Mission Control / workstation */
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
    audit: "audit",
    security: "security",
    actions: "actions",
  };

  const ROOM_CLASS = {
    flytying: "house-flytying",
    health: "house-health",
    mission: "house-mission",
    documents: "house-documents",
    search: "house-search",
    gallery: "house-gallery",
    planner: "house-planner",
    calendar: "house-calendar",
    coding: "house-coding",
    projects: "house-projects",
    memory: "house-memory",
    voice: "house-voice",
    repair: "house-repair",
    integrity: "house-integrity",
    home: "house-home",
    automation: "house-automation",
    providers: "house-providers",
    home_automation: "house-home-auto",
    journal: "house-journal",
    video: "house-video",
    audio: "house-audio",
    browser: "house-browser",
    maker: "house-maker",
    meme: "house-meme",
    vision: "house-vision",
    connections: "house-connections",
    settings: "house-settings",
    capabilities: "house-capabilities",
    integrations: "house-integrations",
    audit: "house-audit",
    security: "house-security",
    actions: "house-actions",
  };

  function viewEl(viewId) {
    return document.getElementById(`${viewId}View`);
  }

  function clearHouseClasses() {
    const body = document.body;
    if (!body) return;
    const extras = Array.from(body.classList).filter(
      (c) =>
        c.startsWith("house-") ||
        c.startsWith("native-") ||
        c === "house-room" ||
        c === "living-room" ||
        c === "furnished-room",
    );
    body.classList.remove(...extras);
    delete body.dataset.furnished;
  }

  function ensureAtmosphere(panel) {
    if (!panel || panel.querySelector(".house-atmosphere")) return;
    const atm = document.createElement("div");
    atm.className = "house-atmosphere";
    atm.setAttribute("aria-hidden", "true");
    atm.innerHTML =
      '<div class="house-atmosphere__wash"></div>' +
      '<div class="house-atmosphere__veil"></div>' +
      '<div class="house-atmosphere__grain"></div>';
    panel.insertBefore(atm, panel.firstChild);
  }

  function ensurePresenceStrip(panel, room) {
    if (!panel) return;
    let strip = panel.querySelector(".house-presence");
    if (!strip) {
      strip = document.createElement("div");
      strip.className = "house-presence";
      strip.innerHTML =
        '<div class="house-presence__brand">Aria <span class="house-presence__place"></span></div>' +
        '<div class="house-presence__status">Listening quietly</div>';
      const header = panel.querySelector(
        ":scope > header, :scope > .mc-toolbar, :scope > .planner-header, :scope > .docs-shell-header, :scope > .search-header, :scope > .flytying-header"
      );
      if (header) header.insertAdjacentElement("beforebegin", strip);
      else panel.insertBefore(strip, panel.children[1] || null);
    }
    const place = strip.querySelector(".house-presence__place");
    const meta = window.AriaWorkspaceRegistry?.room?.(room);
    const label = meta?.place || meta?.metaphor || room;
    if (place) place.textContent = label ? `· ${label}` : "";
    if (document.body) document.body.dataset.place = label || "";
  }

  /** Run original product inits — required for full furniture. */
  function runLegacyInit(view) {
    if (!view) return;
    if (view === "dashboard" && window.initDashboard) window.initDashboard();
    else if (view !== "dashboard") window.stopDashboardClock?.();
    if (view === "automation" && window.initAutomation) window.initAutomation();
    if (view === "workstation" && window.initWorkstation) window.initWorkstation();
    if (view === "models" && window.initModelsHome) window.initModelsHome();
    if (view === "coding" && window.initCodingHome) window.initCodingHome();
    if (view === "planner" && window.initPlanner) window.initPlanner();
    if (view === "calendar" && window.initCalendar) window.initCalendar();
    if (view === "flytying" && window.initFlytying) {
      const p = window.initFlytying();
      if (p && typeof p.then === "function") {
        p.catch((err) => console.warn("[AriaFurnish] flytying init:", err));
      }
    }
    if (view === "capabilities" && window.initCapabilities) window.initCapabilities();
    if (view === "integrations" && window.initIntegrationsHome) window.initIntegrationsHome();
    if (view === "search" && window.initSearchHome) window.initSearchHome();
    if (view === "settings" && window.initSettingsHome) window.initSettingsHome();
    if (view === "projects" && window.initProjects) window.initProjects();
    if (view === "maker" && window.initMakerLab) window.initMakerLab();
    if (view === "browser" && window.initBrowserPanel) window.initBrowserPanel();
    if (view === "browser" && window.initBrowserHome) window.initBrowserHome();
    if (view !== "browser" && window.stopBrowserPanelPoll) window.stopBrowserPanelPoll();
    if (view === "security" && window.initSecurity) {
      window.initSecurity();
      window.refreshToolsSidebar?.();
    }
    if (view === "presence" && window.initPresence) window.initPresence();
    if (view === "audit" && window.initAudit) window.initAudit();
    if (view === "certification" && window.initCertification) window.initCertification();
    if (view === "voice" && window.initVoiceTab) window.initVoiceTab();
    if (view === "vision" && window.initVisionHome) window.initVisionHome();
    if (view === "audio" && window.initAudio) {
      const p = window.initAudio();
      if (p && typeof p.then === "function") {
        p.catch((err) => console.warn("[AriaFurnish] audio init:", err));
      }
    }
    if (view === "journal" && window.initJournal) window.initJournal();
    if (view === "health" && window.initHealth) window.initHealth();
    if (view === "memory") window.loadMemoryBrowser?.();
    if (view === "gallery") window.loadGallery?.();
    if (view === "video") {
      if (typeof window.loadVideoGallery === "function") window.loadVideoGallery();
      else if (typeof window.initVideoStudio === "function") window.initVideoStudio();
    }
    if (view === "meme") {
      if (typeof window.loadMemeGallery === "function") window.loadMemeGallery();
    }
    if (view === "actions") window.loadActions?.(document.getElementById("actionsFilter")?.value);
    if (view === "documents") {
      window.initDocumentsTab?.();
      window.loadDocumentsTab?.();
    }
    if (view === "connections" && window.initConnections) window.initConnections();
    if (view === "homeAutomation" || view === "home_automation") {
      window.initHaPanel?.();
      window.loadSmarthomeHome?.();
    }
  }

  function chromeFor(room) {
    const meta = window.AriaWorkspaceRegistry?.room?.(room);
    return meta?.chromePolicy || "standard";
  }

  /**
   * Mount the full original panel for a Room onto the stage.
   * @returns {boolean} true if furnished
   */
  function enter(roomId) {
    if (!window.AriaStage?.isWorkspace?.()) return false;
    if (!roomId || roomId === "chat") return false;

    const viewId = ROOM_VIEW[roomId] || roomId;
    const panel = viewEl(viewId);
    if (!panel) {
      console.warn("[AriaFurnish] missing panel", roomId, viewId);
      return false;
    }

    /* Exit thin native shells — furniture replaces them */
    try {
      window.AriaLivingRoom?.exit?.({ keepStage: true });
    } catch (_) {
      /* ignore */
    }
    try {
      window.AriaRoomKit?.exitOthers?.(null);
    } catch (_) {
      /* ignore */
    }

    clearHouseClasses();
    const prevRoom = document.body.dataset.room;
    if (prevRoom === "journal" && roomId !== "journal") {
      try {
        window.AriaJournalCancelPending?.();
      } catch (_) {
        /* ignore */
      }
    }
    const cls = ROOM_CLASS[roomId] || `house-${roomId}`;
    document.body.classList.add("house-room", cls, "furnished-room");
    document.body.dataset.room = roomId;
    document.body.dataset.furnished = "1";

    ensureAtmosphere(panel);
    ensurePresenceStrip(panel, roomId);
    window.AriaStage.mount(panel, roomId);
    window.AriaWorkspaceChrome?.apply?.(chromeFor(roomId));

    try {
      runLegacyInit(viewId);
    } catch (err) {
      console.error("[AriaFurnish] init failed", roomId, err);
    }

    window.dispatchEvent(
      new CustomEvent("aria-house-room", { detail: { room: roomId, viewId, furnished: true, native: false } })
    );
    return true;
  }

  function viewForRoom(roomId) {
    return ROOM_VIEW[roomId] || roomId;
  }

  function allFurnishedRoomIds() {
    return Object.keys(ROOM_VIEW).filter((id) => id !== "chat");
  }

  window.AriaFurnish = {
    version: "6.4.2",
    enter,
    viewForRoom,
    roomViewMap: ROOM_VIEW,
    allRoomIds: allFurnishedRoomIds,
    runLegacyInit,
  };
})();
