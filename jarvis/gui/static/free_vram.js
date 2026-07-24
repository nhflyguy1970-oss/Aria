/** Free VRAM action — extracted from app.js. */
(function () {
  "use strict";

  async function freeJarvisVram(statusEl) {
    const target = statusEl || document.getElementById("statusText");
    if (target) target.textContent = "Freeing VRAM…";
    try {
      const res = await fetch("/api/gpu/free-vram", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        throw new Error(data.message || data.detail || `Free VRAM failed (${res.status})`);
      }
      const n = (data.unloaded_ollama || []).length;
      const msg = `VRAM freed${n ? ` (${n} Ollama model${n === 1 ? "" : "s"} unloaded)` : ""}`;
      if (target) target.textContent = msg;
      window.showAriaToast?.(msg, "ok", 3000);
      if (typeof window.loadGpuStatus === "function") {
        await window.loadGpuStatus();
      } else if (window.jarvisHealth?.loadGpuStatus) {
        await window.jarvisHealth.loadGpuStatus();
      }
      return data;
    } catch (e) {
      const msg = e.message || String(e);
      if (target) target.textContent = msg;
      window.showAriaToast?.(msg, "err", 5000);
      throw e;
    }
  }

  window.freeJarvisVram = freeJarvisVram;

  async function vramPreflight(action) {
    try {
      const res = await fetch(`/api/vram/preflight?action=${encodeURIComponent(action)}`);
      if (!res.ok) return true;
      const data = await res.json();
      if (data.blocked) {
        window.showAriaToast?.((data.warnings || ["Media queue full"]).join(" · "), "warn", 6000);
        return false;
      }
      if (data.ok || !data.warnings?.length) return true;
      const tips = (data.tips || []).slice(0, 2).join("\n");
      const adj = (data.adjustments || []).slice(0, 2).join("\n");
      const msg = data.warnings.join("\n\n")
        + (adj ? `\n\nPlan: ${adj}` : "")
        + (tips ? `\n\nTip: ${tips}` : "")
        + "\n\nContinue anyway?";
      return window.confirm(msg);
    } catch {
      return true;
    }
  }

  window.vramPreflight = vramPreflight;
})();
