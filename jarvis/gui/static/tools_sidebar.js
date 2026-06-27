/** P4 tools module sidebar status */
(function () {
  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderToolRows(tools) {
    if (Array.isArray(tools)) {
      return tools
        .map(
          (t) =>
            `<li class="${t.ok ? "ok" : "fail"}">${t.ok ? "✓" : "✗"} ${escapeHtml(t.name)}` +
            `<span class="muted">${t.detail ? ` — ${escapeHtml(t.detail)}` : ""}</span></li>`
        )
        .join("");
    }
    if (tools && typeof tools === "object") {
      return Object.entries(tools)
        .map(([k, v]) => {
          const val = typeof v === "object" ? JSON.stringify(v) : String(v);
          const ok =
            v === true ||
            (typeof v === "object" &&
              v &&
              (v.running || v.enabled || v.playwright || v.available));
          return `<li class="${ok ? "ok" : "fail"}">${ok ? "✓" : "✗"} ${escapeHtml(k)}` +
            `<span class="muted"> — ${escapeHtml(val)}</span></li>`;
        })
        .join("");
    }
    return "";
  }

  async function refreshToolsSidebar() {
    const list = document.getElementById("toolsStatusList");
    if (!list) return;
    try {
      const res = await fetch("/api/security/tools/status");
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || res.statusText);
      const html = renderToolRows(data.tools);
      list.innerHTML = html || "<li class='muted'>No tool status</li>";
    } catch (_) {
      list.innerHTML = "<li class='muted'>Could not load tools</li>";
    }
  }

  async function refreshBrainMode() {
    const el = document.getElementById("brainModeStrip");
    if (!el) return;
    try {
      const res = await fetch("/api/security/brain-mode");
      const d = await res.json();
      el.textContent = d.label || d.mode || "—";
      el.title = `Mode: ${d.mode} · Ollama: ${d.local ? "up" : "down"}`;
    } catch (_) {
      el.textContent = "";
    }
  }

  function initToolsSidebar() {
    refreshToolsSidebar();
    refreshBrainMode();
    setInterval(refreshToolsSidebar, 30000);
    setInterval(refreshBrainMode, 30000);
    document.getElementById("toolsRefreshBtn")?.addEventListener("click", refreshToolsSidebar);
  }

  window.initToolsSidebar = initToolsSidebar;
  window.refreshToolsSidebar = refreshToolsSidebar;
  document.addEventListener("DOMContentLoaded", initToolsSidebar);
})();
