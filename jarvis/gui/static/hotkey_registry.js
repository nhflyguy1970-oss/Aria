/** Hotkey registry — single client source mirrored from /api/shell/hotkeys. */
(function () {
  "use strict";

  /** Fallback if API cold — must stay in sync with jarvis/shell/hotkeys.py */
  const FALLBACK = [
    { id: "palette", chord: "Ctrl+K", action: "command_palette", label: "Command palette" },
    { id: "sidebar_search", chord: "Ctrl+Shift+F", action: "sidebar_search", label: "Sidebar search" },
    { id: "shortcuts", chord: "Ctrl+/", action: "shortcuts_modal", label: "Keyboard shortcuts" },
    { id: "settings", chord: "Ctrl+,", action: "open_settings", label: "Settings Home" },
    { id: "home", chord: "Ctrl+Home", action: "open_home", label: "Home" },
    { id: "notifications", chord: "Ctrl+Shift+A", action: "open_notifications", label: "Notifications" },
    { id: "layouts", chord: "Ctrl+Shift+L", action: "open_layouts", label: "Layouts", aliases: ["Ctrl+Shift+P"] },
    { id: "mission", chord: "Ctrl+Shift+M", action: "open_mission_control", label: "Mission Control" },
    { id: "mini_chat", chord: "Ctrl+Shift+K", action: "toggle_mini_chat", label: "Floating mini chat" },
    { id: "split", chord: "Ctrl+\\", action: "toggle_split", label: "Split view" },
    { id: "automation", chord: "Ctrl+Shift+O", action: "open_automation", label: "Automation Home" },
    { id: "view_paths", chord: "Ctrl+Shift+V", action: "open_view_paths", label: "View Paths" },
    { id: "models", chord: "Ctrl+Shift+.", action: "open_models", label: "Models Home" },
    { id: "coding", chord: "Ctrl+Shift+C", action: "open_coding", label: "Coding Home" },
    { id: "gallery", chord: "Ctrl+Shift+G", action: "open_gallery", label: "Gallery Home" },
    { id: "browser", chord: "Ctrl+Shift+B", action: "open_browser", label: "Browser Home" },
    { id: "vision", chord: "Ctrl+Shift+I", action: "open_vision", label: "Vision Home" },
    { id: "favorites", chord: "Ctrl+1…9", action: "jump_favorite", label: "Jump Favorites" },
    { id: "cycle", chord: "Ctrl+Tab", action: "cycle_views", label: "Cycle views" },
    { id: "back", chord: "Alt+←", action: "view_back", label: "Back" },
    { id: "forward", chord: "Alt+→", action: "view_forward", label: "Forward" },
    { id: "layout_presets", chord: "Ctrl+Alt+1…8", action: "apply_layout_preset", label: "Starter layouts" },
    { id: "reload", chord: "Ctrl+Shift+R", action: "reload_ui", label: "Reload UI" },
  ];

  let _hotkeys = FALLBACK.slice();

  function chord(id) {
    const h = _hotkeys.find((x) => x.id === id || x.action === id);
    return h?.chord || "";
  }

  function label(id) {
    const h = _hotkeys.find((x) => x.id === id || x.action === id);
    return h?.label || id;
  }

  function renderShortcutsList(ul) {
    if (!ul) return;
    ul.replaceChildren();
    _hotkeys.forEach((h) => {
      const li = document.createElement("li");
      const parts = String(h.chord || "").split(/(\+|…|\.\.\.)/).filter(Boolean);
      // Simple: wrap whole chord in kbd groups
      const chordHtml = String(h.chord || "")
        .split("+")
        .map((p) => `<kbd>${p.trim()}</kbd>`)
        .join("+");
      li.innerHTML = `${chordHtml} — ${h.label}`;
      ul.appendChild(li);
    });
  }

  async function refresh() {
    try {
      const res = await fetch("/api/shell/hotkeys", { cache: "no-store" });
      const data = await res.json();
      if (data?.hotkeys?.length) _hotkeys = data.hotkeys;
      else if (data?.shortcuts?.length) {
        _hotkeys = data.shortcuts.map((s) => ({
          id: s.id,
          chord: s.chord,
          label: s.label,
          action: s.id,
        }));
      }
    } catch {
      /* keep fallback */
    }
    const ul = document.querySelector("#shortcutsModal .shortcuts-list");
    if (ul) renderShortcutsList(ul);
    document.querySelectorAll("[data-hotkey-id]").forEach((el) => {
      const c = chord(el.dataset.hotkeyId);
      if (c) el.setAttribute("title", `${el.getAttribute("data-hotkey-label") || el.textContent} (${c})`);
    });
  }

  function applyDensity() {
    const dens =
      window.AriaUiPrefs?.get?.("density") ||
      window.AriaUiPrefs?.get?.("shellDensity") ||
      "standard";
    document.documentElement.setAttribute("data-density", dens);
  }

  function progressiveDisclosure() {
    // Mark advanced sections; collapse on first run if never customized
    const advanced = ["services", "workstation", "integrations", "coding"];
    advanced.forEach((key) => {
      const sec = document.querySelector(`.sidebar-section[data-section="${key}"]`);
      if (sec) sec.classList.add("shell-advanced");
    });
    const migrated = localStorage.getItem("aria_shell_disclosure_v1");
    if (migrated) return;
    const prefs = window.AriaUiPrefs?.get?.("sidebarCollapsed");
    if (prefs && typeof prefs === "object" && Object.keys(prefs).length) {
      localStorage.setItem("aria_shell_disclosure_v1", "1");
      return;
    }
    // Default: collapse System + Mission Control + Developer for calmer first run
    const map = window.AriaUiPrefs?.get?.("sidebarCollapsed") || {};
    ["services", "workstation", "integrations", "coding", "video"].forEach((k) => {
      map[k] = true;
    });
    // Keep favorites + surfaces more open
    map.favorites = false;
    map.workspaces = false;
    window.AriaUiPrefs?.set?.("sidebarCollapsed", map);
    localStorage.setItem("aria_shell_disclosure_v1", "1");
    document.querySelectorAll(".sidebar-section.shell-advanced").forEach((sec) => {
      sec.classList.add("collapsed");
      sec.querySelector(".sidebar-section-head")?.setAttribute("aria-expanded", "false");
    });
  }

  function init() {
    applyDensity();
    progressiveDisclosure();
    refresh();
    window.addEventListener("aria-ui-prefs", applyDensity);
    window.addEventListener("aria-ui-prefs-change", applyDensity);
  }

  window.AriaHotkeys = {
    list: () => _hotkeys.slice(),
    chord,
    label,
    refresh,
    renderShortcutsList,
    FALLBACK,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
