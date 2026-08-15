/** Theme toggle + restrained accent persistence (Professional Dark / Light). */
(function () {
  "use strict";

  const THEME_BC = (() => {
    try {
      return new BroadcastChannel("aria-settings-sync");
    } catch {
      return null;
    }
  })();

  /* --- Light / dark --- */
  function applyThemeLocal(mode) {
    const on = mode === "light";
    document.body.classList.toggle("light-theme", on);
    const btn = document.getElementById("themeToggle");
    if (btn) btn.textContent = on ? "Dark theme" : "Light theme";
  }

  function setTheme(mode, { persistRemote = true, broadcast = true, successToast } = {}) {
    const on = mode === "light";
    applyThemeLocal(mode);
    try {
      localStorage.setItem("aria_theme", on ? "light" : "dark");
      window.AriaUiPrefs?.set?.("theme", on ? "light" : "dark");
    } catch {
      /* ignore */
    }
    if (broadcast) {
      try {
        THEME_BC?.postMessage({ type: "theme", theme: on ? "light" : "dark" });
      } catch {
        /* ignore */
      }
    }
    if (persistRemote) {
      void window.ariaMutate({
        request: () =>
          fetch("/api/settings/product/appearance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme: on ? "light" : "dark" }),
          }),
        successToast,
        failToast: "Theme applied locally — server persist failed",
        successTone: "ok",
      });
    }
  }

  document.getElementById("themeToggle")?.addEventListener("click", () => {
    const next = document.body.classList.contains("light-theme") ? "dark" : "light";
    setTheme(next, { successToast: next === "light" ? "Professional Light" : "Professional Dark" });
  });

  // Other tabs: storage event (localStorage) + BroadcastChannel
  window.addEventListener("storage", (ev) => {
    if (ev.key === "aria_theme" && (ev.newValue === "light" || ev.newValue === "dark")) {
      applyThemeLocal(ev.newValue);
    }
    if (ev.key === "aria_ui_prefs_v1" && ev.newValue) {
      try {
        const prefs = JSON.parse(ev.newValue);
        if (prefs.theme === "light" || prefs.theme === "dark") applyThemeLocal(prefs.theme);
        if (prefs.accent && typeof window.applyAriaAccent === "function") {
          window.applyAriaAccent(prefs.accent, { broadcast: false, fromSync: true });
        }
      } catch {
        /* ignore */
      }
    }
  });
  THEME_BC?.addEventListener("message", (ev) => {
    const data = ev?.data || {};
    if (data.type === "theme" && (data.theme === "light" || data.theme === "dark")) {
      applyThemeLocal(data.theme);
      try {
        localStorage.setItem("aria_theme", data.theme);
      } catch {
        /* ignore */
      }
    }
    if (data.type === "accent" && data.accent && typeof window.applyAriaAccent === "function") {
      window.applyAriaAccent(data.accent, { broadcast: false, fromSync: true });
    }
  });

  (function restoreAriaTheme() {
    try {
      const fromPrefs = window.AriaUiPrefs?.get?.("theme");
      const legacy = localStorage.getItem("aria_theme");
      const theme = fromPrefs === "light" || fromPrefs === "dark" ? fromPrefs : legacy;
      if (theme === "light") {
        document.body.classList.add("light-theme");
        const btn = document.getElementById("themeToggle");
        if (btn) btn.textContent = "Dark theme";
      }
      if (theme === "light" || theme === "dark") {
        window.AriaUiPrefs?.set?.("theme", theme);
      }
    } catch {
      /* ignore */
    }
  })();

  /* Restrained accents only — steel default (no RGB / neon themes) */
  const ACCENTS = ["steel", "slate", "teal", "emerald"];
  const LEGACY_MAP = {
    gold: "steel",
    blue: "steel",
    green: "emerald",
    purple: "slate",
    orange: "teal",
    red: "steel",
    amber: "steel",
  };

  function applyAccent(name, opts = {}) {
    let accent = LEGACY_MAP[name] || name;
    if (!ACCENTS.includes(accent)) accent = "steel";
    if (accent === "steel") document.documentElement.removeAttribute("data-accent");
    else document.documentElement.setAttribute("data-accent", accent);
    document.querySelectorAll(".accent-swatch").forEach((b) => {
      const key = LEGACY_MAP[b.dataset.accent] || b.dataset.accent;
      b.classList.toggle("active", key === accent);
      b.setAttribute("aria-pressed", key === accent ? "true" : "false");
    });
    if (!opts.fromSync) {
      window.AriaUiPrefs?.set?.("accent", accent);
    }
    if (opts.broadcast !== false && !opts.fromSync) {
      try {
        THEME_BC?.postMessage({ type: "accent", accent });
      } catch {
        /* ignore */
      }
    }
  }

  function initAccents() {
    const raw = window.AriaUiPrefs?.get?.("accent", "steel");
    applyAccent(raw, { broadcast: false });
    document.querySelectorAll(".accent-swatch").forEach((btn) => {
      btn.addEventListener("click", () => {
        applyAccent(btn.dataset.accent);
        window.showAriaToast?.(`Accent: ${LEGACY_MAP[btn.dataset.accent] || btn.dataset.accent}`, "ok", 1600);
      });
    });
  }

  window.applyAriaAccent = applyAccent;
  window.setAriaTheme = setTheme;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initAccents);
  else initAccents();
})();
