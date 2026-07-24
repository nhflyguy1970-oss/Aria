/** Sidebar video shortcuts + VRAM status — extracted from app.js. */
(function () {
  "use strict";

document.getElementById("openVideoStudioBtn")?.addEventListener("click", () => {
  window.switchToView?.("video");
  document.body.classList.remove("mobile-sidebar-open");
  refreshSidebarVideoStatus();
});
document.getElementById("openVideoGalleryBtn")?.addEventListener("click", () => {
  window.switchToView?.("video");
  document.getElementById("videoGalleryGrid")?.scrollIntoView({ behavior: "smooth", block: "start" });
  document.body.classList.remove("mobile-sidebar-open");
  refreshSidebarVideoStatus();
});
document.getElementById("sidebarVideoFreeVramBtn")?.addEventListener("click", async () => {
  if (typeof window.freeJarvisVram === "function") window.freeJarvisVram?.(document.getElementById("statusText"));
  await refreshSidebarVideoStatus();
});

async function refreshSidebarVideoStatus() {
  const el = document.getElementById("sidebarVideoStatus");
  if (!el) return;
  try {
    const res = await fetch("/api/resources");
    const data = await res.json().catch(() => ({}));
    const free = data.free_vram_mb ?? data.vram_free_mb;
    const total = data.vram_mb;
    const line = data.status_line || (
      free != null && total != null
        ? `${Math.round(free)} / ${Math.round(total)} MB VRAM free`
        : null
    );
    el.textContent = line
      ? `AnimateDiff · Ken Burns · ${line}`
      : "AnimateDiff · Ken Burns · chat: “make a video…”";
  } catch (_) {
    el.textContent = "AnimateDiff · Ken Burns · chat: “make a video…”";
  }
}

  window.refreshSidebarVideoStatus = refreshSidebarVideoStatus;
})();
