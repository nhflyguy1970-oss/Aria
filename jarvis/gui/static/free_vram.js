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
})();
