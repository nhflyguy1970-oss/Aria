/** Theme toggle + persistence — extracted from app.js. */
(function () {
  "use strict";

document.getElementById("themeToggle")?.addEventListener("click", () => {
  document.body.classList.toggle("light-theme");
  const on = document.body.classList.contains("light-theme");
  try {
    localStorage.setItem("aria_theme", on ? "light" : "dark");
  } catch {
    /* ignore */
  }
  const btn = document.getElementById("themeToggle");
  if (btn) btn.textContent = on ? "Dark theme" : "Light theme";
  window.showAriaToast?.(on ? "Light theme" : "Dark theme", "ok", 1800);
});

(function restoreAriaTheme() {
  try {
    if (localStorage.getItem("aria_theme") === "light") {
      document.body.classList.add("light-theme");
      const btn = document.getElementById("themeToggle");
      if (btn) btn.textContent = "Dark theme";
    }
  } catch {
    /* ignore */
  }
})();
})();
