/** Git status / diff / log sidebar — extracted from app.js. */
(function () {
  "use strict";

  async function loadGitStatus() {
    const el = document.getElementById("gitStatusBox");
    if (!el) return;
    try {
      const res = await fetch("/api/git/status");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Git status failed (${res.status})`);
      el.textContent = data.status || "—";
    } catch (err) {
      el.textContent = "Git: unavailable";
      window.showAriaToast?.(err.message || "Git status unavailable", "err", 4000);
    }
  }

  async function loadGitDiff() {
    const box = document.getElementById("gitDetailBox");
    if (!box) return;
    box.classList.remove("hidden");
    box.textContent = "Loading diff…";
    try {
      const res = await fetch("/api/git/diff");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Git diff failed (${res.status})`);
      box.textContent = data.diff?.trim() || "(no diff)";
    } catch (err) {
      box.textContent = "Could not load diff";
      window.showAriaToast?.(err.message || "Could not load diff", "err", 4000);
    }
  }

  async function loadGitLog() {
    const box = document.getElementById("gitDetailBox");
    if (!box) return;
    box.classList.remove("hidden");
    box.textContent = "Loading log…";
    try {
      const res = await fetch("/api/git/log?limit=12");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Git log failed (${res.status})`);
      const lines = (data.log || []).join("\n");
      box.textContent = lines || "(empty log)";
    } catch (err) {
      box.textContent = "Could not load log";
      window.showAriaToast?.(err.message || "Could not load log", "err", 4000);
    }
  }

  window.loadGitStatus = loadGitStatus;
  window.loadGitDiff = loadGitDiff;
  window.loadGitLog = loadGitLog;

  document.getElementById("gitRefreshBtn")?.addEventListener("click", () => loadGitStatus());
  document.getElementById("gitDiffBtn")?.addEventListener("click", () => loadGitDiff());
  document.getElementById("gitLogBtn")?.addEventListener("click", () => loadGitLog());
})();
