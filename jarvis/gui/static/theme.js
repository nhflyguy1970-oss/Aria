/** Theme toggle + accent color persistence. */
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
    // Mirror into Settings appearance store (single source of truth)
    fetch("/api/settings/product/appearance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme: on ? "light" : "dark" }),
    }).catch(() => {});
  }

  document.getElementById("themeToggle")?.addEventListener("click", () => {
    const next = document.body.classList.contains("light-theme") ? "dark" : "light";
    setTheme(next);
    window.showAriaToast?.(next === "light" ? "Light theme" : "Dark theme", "ok", 1800);
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

  /* --- Accent colors (highlights only — not a reskin) --- */
  const ACCENTS = ["gold", "blue", "green", "purple", "orange", "red", "teal", "amber"];

  function applyAccent(name) {
    const accent = ACCENTS.includes(name) ? name : "gold";
    if (accent === "gold") document.documentElement.removeAttribute("data-accent");
    else document.documentElement.setAttribute("data-accent", accent);
    document.querySelectorAll(".accent-swatch").forEach((b) => {
      b.classList.toggle("active", b.dataset.accent === accent);
      b.setAttribute("aria-pressed", b.dataset.accent === accent ? "true" : "false");
    });
    window.AriaUiPrefs?.set?.("accent", accent);
  }

  function initAccents() {
    const saved = window.AriaUiPrefs?.get?.("accent", "gold");
    applyAccent(saved);
    document.querySelectorAll(".accent-swatch").forEach((btn) => {
      btn.addEventListener("click", () => {
        applyAccent(btn.dataset.accent);
        window.showAriaToast?.(`Accent: ${btn.dataset.accent}`, "ok", 1600);
      });
    });
  }

  window.applyAriaAccent = applyAccent;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initAccents);
  else initAccents();
})();
