/** Theme toggle + restrained accent persistence (Professional Dark / Light). */
(function () {
  "use strict";

  /* --- Light / dark --- */
  function setTheme(mode) {
    const on = mode === "light";
    document.body.classList.toggle("light-theme", on);
    try {
      localStorage.setItem("aria_theme", on ? "light" : "dark");
      window.AriaUiPrefs?.set?.("theme", on ? "light" : "dark");
    } catch {
      /* ignore */
    }
    const btn = document.getElementById("themeToggle");
    if (btn) btn.textContent = on ? "Dark theme" : "Light theme";
    fetch("/api/settings/product/appearance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme: on ? "light" : "dark" }),
    }).catch(() => {});
  }

  document.getElementById("themeToggle")?.addEventListener("click", () => {
    const next = document.body.classList.contains("light-theme") ? "dark" : "light";
    setTheme(next);
    window.showAriaToast?.(next === "light" ? "Professional Light" : "Professional Dark", "ok", 1800);
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

  function applyAccent(name) {
    let accent = LEGACY_MAP[name] || name;
    if (!ACCENTS.includes(accent)) accent = "steel";
    if (accent === "steel") document.documentElement.removeAttribute("data-accent");
    else document.documentElement.setAttribute("data-accent", accent);
    document.querySelectorAll(".accent-swatch").forEach((b) => {
      const key = LEGACY_MAP[b.dataset.accent] || b.dataset.accent;
      b.classList.toggle("active", key === accent);
      b.setAttribute("aria-pressed", key === accent ? "true" : "false");
    });
    window.AriaUiPrefs?.set?.("accent", accent);
  }

  function initAccents() {
    const raw = window.AriaUiPrefs?.get?.("accent", "steel");
    applyAccent(raw);
    document.querySelectorAll(".accent-swatch").forEach((btn) => {
      btn.addEventListener("click", () => {
        applyAccent(btn.dataset.accent);
        window.showAriaToast?.(`Accent: ${LEGACY_MAP[btn.dataset.accent] || btn.dataset.accent}`, "ok", 1600);
      });
    });
  }

  window.applyAriaAccent = applyAccent;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initAccents);
  else initAccents();
})();
