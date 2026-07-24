/** Vision quality settings — extracted from app.js. */
(function () {
  "use strict";

  async function loadVisionSettings() {
    const sel = document.getElementById("visionQualitySelect");
    const note = document.getElementById("visionStatusNote");
    try {
      const res = await fetch("/api/vision/settings");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Vision settings failed (${res.status})`);
      if (sel && data.quality_mode) sel.value = data.quality_mode;
      if (note) {
        note.textContent = data.low_vram
          ? `Vision: ${data.model || "?"} · ${data.vram_gb || "?"}GB VRAM (fast mode recommended)`
          : `Vision: ${data.model || "?"}`;
      }
    } catch (err) {
      if (note) note.textContent = "Vision settings unavailable";
      window.showAriaToast?.(err.message || "Vision settings unavailable", "err", 4000);
    }
  }

  window.loadVisionSettings = loadVisionSettings;

  document.getElementById("visionQualitySelect")?.addEventListener("change", async (e) => {
    try {
      const form = new FormData();
      form.append("quality_mode", e.target.value);
      const res = await fetch("/api/vision/settings", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Save failed (${res.status})`);
      window.showAriaToast?.(`Vision quality: ${e.target.value}`, "ok", 2500);
      await loadVisionSettings();
      await window.loadModelSettings?.();
    } catch (err) {
      window.showAriaToast?.(err.message || "Could not save vision quality", "err", 5000);
    }
  });
})();
