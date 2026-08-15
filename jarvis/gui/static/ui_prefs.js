/** Shared Aria UI preferences (local, per-browser). */
(function () {
  "use strict";

  const ROOT_KEY = "aria_ui_prefs_v1";
  const DEFAULTS = {
    favorites: ["chat", "planner", "workstation", "gallery", "maker"],
    sidebarCollapsed: null,
    sidebarWidth: 260,
    recentViews: [],
    recentCommands: [],
    recentSearches: [],
    recentPrompts: [],
    recentModels: [],
    recentProviders: [],
    recentFiles: [],
    recentWorkflows: [],
    pinnedCommands: [],
    commandUsage: {},
    suggestionSeen: [],
    suggestionClicks: {},
    viewVisits: {},
    tipDismissed: [],
    tipSeenCount: {},
    whatsNewSeen: "",
    lastFilters: {},
    dockHidden: false,
    statusBarHidden: false,
    miniChatHidden: false,
    accent: "steel",
    theme: "dark",
    density: "standard",
    /** Living Interface Phase 2 */
    atmosphereEnabled: true,
    weatherAtmosphere: true,
    seasonAtmosphere: true,
    ambientSound: false,
    livingWorkspace: true,
    dashboardLayout: null,
    panelCollapsed: {},
    activeWorkspace: "",
    recordedWorkflows: {},
    splitEnabled: false,
    splitRatio: 0.55,
    splitPair: null,
    missionControl: {},
  };

  function load() {
    try {
      const raw = JSON.parse(localStorage.getItem(ROOT_KEY) || "{}");
      if (!raw || typeof raw !== "object") return { ...DEFAULTS };
      return { ...DEFAULTS, ...raw };
    } catch {
      return { ...DEFAULTS };
    }
  }

  function save(partial) {
    const next = { ...load(), ...partial };
    try {
      localStorage.setItem(ROOT_KEY, JSON.stringify(next));
    } catch {
      /* quota */
    }
    window.dispatchEvent(new CustomEvent("aria-ui-prefs", { detail: next }));
    return next;
  }

  function get(key, fallback) {
    const p = load();
    return p[key] !== undefined ? p[key] : fallback;
  }

  function set(key, value) {
    return save({ [key]: value });
  }

  function bumpUsage(mapKey, id, max = 200) {
    const prefs = load();
    const map = { ...(prefs[mapKey] || {}) };
    map[id] = (map[id] || 0) + 1;
    const keys = Object.keys(map);
    if (keys.length > max) {
      keys
        .sort((a, b) => (map[a] || 0) - (map[b] || 0))
        .slice(0, keys.length - max)
        .forEach((k) => delete map[k]);
    }
    return save({ [mapKey]: map });
  }

  function pushRecent(listKey, id, max = 12) {
    const prefs = load();
    const list = [id, ...(prefs[listKey] || []).filter((x) => x !== id)].slice(0, max);
    return save({ [listKey]: list });
  }

  window.AriaUiPrefs = {
    load,
    save,
    get,
    set,
    bumpUsage,
    pushRecent,
    ROOT_KEY,
    DEFAULTS,
  };
})();
