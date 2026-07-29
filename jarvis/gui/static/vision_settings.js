/** Vision quality settings + honesty strip. */
(function () {
  "use strict";

  async function loadVisionSettings() {
    const sel = document.getElementById("visionQualitySelect");
    const note = document.getElementById("visionStatusNote");
    const stripHonesty = document.getElementById("visionStripHonesty");
    try {
      const [data, honesty] = await Promise.all([
        fetch("/api/vision/settings").then((r) => r.json()),
        fetch("/api/vision/honesty").then((r) => r.json()).catch(() => ({})),
      ]);
      if (sel && data.quality_mode) sel.value = data.quality_mode;
      const model = honesty.model || data.model || "?";
      if (note) {
        const warn = (honesty.warnings || [])[0] || "";
        note.textContent = data.low_vram || honesty.low_vram
          ? `Vision: ${model} · Fast recommended · ${honesty.expected_latency || ""}${warn ? " · " + warn : ""}`
          : `Vision: ${model} · ${data.quality_mode || honesty.quality_mode || ""} · ~${honesty.estimated_vram_mb || "?"}MB`;
      }
      if (stripHonesty) {
        stripHonesty.textContent = `${model} · ${honesty.quality_mode || data.quality_mode || ""}`;
      }
      window.refreshVisionStrip?.({ state: { state: "idle" }, honesty }, honesty);
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
      await fetch("/api/vision/settings/unified", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quality_mode: e.target.value }),
      }).catch(() => {});
      window.showAriaToast?.(`Vision quality: ${e.target.value}`, "ok", 2500);
      await loadVisionSettings();
      await window.loadModelSettings?.();
    } catch (err) {
      window.showAriaToast?.(err.message || "Could not save vision quality", "err", 5000);
    }
  });

  document.getElementById("visionStripHomeBtn")?.addEventListener("click", () => {
    window.switchToView?.("vision");
  });
  document.getElementById("ariaVisionStrip")?.addEventListener("click", (e) => {
    if (e.target.closest("button")) return;
    window.switchToView?.("vision");
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => loadVisionSettings(), { once: true });
  } else {
    loadVisionSettings();
  }
})();
