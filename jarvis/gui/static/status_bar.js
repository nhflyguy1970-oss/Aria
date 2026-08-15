/** Bottom status bar — provider, model, GPU, jobs, health. Unobtrusive, hideable, hidden-tab aware. */
(function () {
  "use strict";

  const POLL_MS = 60000;
  let timer = null;

  function $(id) {
    return document.getElementById(id);
  }

  function hidden() {
    return window.AriaUiPrefs?.get?.("statusBarHidden", false) === true;
  }

  function setSeg(id, text, cls) {
    const el = $(id);
    if (!el) return;
    el.textContent = text || "—";
    el.className = `status-seg ${cls || ""}`.trim();
  }

  async function refresh() {
    const bar = $("ariaStatusBar");
    if (!bar || hidden() || document.hidden) return;
    try {
      const res = await fetch("/api/health", { cache: "no-store" });
      const h = await res.json().catch(() => ({}));
      const models = h.models || {};
      const gpu = h.gpu || {};
      const ollama = h.ollama_health || (h.ollama_ready ? "healthy" : "unavailable");

      setSeg("statusSegProvider", `Ollama · ${ollama}`, `status-${ollama}`);
      setSeg("statusSegModel", models.general || "no model");
      // Authoritative compute GPU (nvidia/amd), not ROCm package presence.
      const hasGpu = Boolean(
        gpu.nvidia_available || gpu.compute_vendor === "nvidia" || gpu.vendor === "nvidia" || gpu.vendor === "amd" || gpu.vram_mb
      );
      let gpuMode = "CPU";
      if (hasGpu) {
        gpuMode = gpu.ollama_using_gpu ? "GPU" : "GPU idle";
      }
      const free = gpu.free_vram_mb != null ? Math.round(Number(gpu.free_vram_mb) / 1024) : null;
      const total = gpu.vram_mb ? Math.round(Number(gpu.vram_mb) / 1024) : null;
      const vram =
        free != null && total != null ? ` ${free}/${total}GB` : total != null ? ` ${total}GB` : "";
      setSeg("statusSegGpu", `${gpuMode}${vram}`, gpu.ollama_using_gpu ? "status-healthy" : "");
      const gpuEl = $("statusSegGpu");
      if (gpuEl) {
        gpuEl.title = [
          gpu.compute_gpu || gpu.name || "",
          gpu.free_vram_mb != null ? `Free VRAM ${gpu.free_vram_mb}MB` : "",
          gpu.ollama_using_gpu ? "Ollama on GPU" : "Ollama not using GPU right now",
        ]
          .filter(Boolean)
          .join(" · ");
      }
      const el = $("statusSegModel");
      if (el) el.title = `Chat ${models.general || "—"} · Code ${models.coder || "—"} · Vision ${models.vision || "—"}`;
      if (h.version) setSeg("statusSegVersion", `v${h.version}`);
    } catch {
      setSeg("statusSegProvider", "Server unreachable", "status-unavailable");
    }
    // Jobs from existing badge (no extra request)
    const badge = $("jobCenterBadge");
    const jobsN = badge && !badge.classList.contains("hidden") ? badge.textContent.trim() : "";
    setSeg("statusSegJobs", jobsN ? `${jobsN} job${jobsN === "1" ? "" : "s"}` : "idle", jobsN ? "status-degraded" : "");
  }

  function apply() {
    const bar = $("ariaStatusBar");
    if (!bar) return;
    bar.classList.toggle("hidden", hidden());
    document.body.classList.toggle("has-status-bar", !hidden());
    const btn = $("toggleStatusBarBtn");
    if (btn) btn.textContent = hidden() ? "Show status bar" : "Hide status bar";
  }

  function startPoll() {
    if (timer) clearInterval(timer);
    timer = null;
    if (document.hidden) return;
    timer = setInterval(refresh, POLL_MS);
    refresh();
  }

  function init() {
    apply();
    startPoll();
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        if (timer) {
          clearInterval(timer);
          timer = null;
        }
        return;
      }
      startPoll();
    });
    $("toggleStatusBarBtn")?.addEventListener("click", () => {
      window.AriaUiPrefs?.set?.("statusBarHidden", !hidden());
      apply();
      if (!hidden()) refresh();
    });
    $("statusSegJobsWrap")?.addEventListener("click", () => $("jobCenterBtn")?.click());
    $("statusSegProviderWrap")?.addEventListener("click", () => {
      window.switchToView?.("workstation");
      setTimeout(() => window.switchMcTab?.("inference"), 100);
    });
    $("statusSegModelWrap")?.addEventListener("click", () => {
      window.openModelsHome?.() || window.switchToView?.("models");
    });
    $("statusSegLayoutWrap")?.addEventListener("click", () => {
      window.AriaLayouts?.openModal?.() || window.AriaWorkspaces?.openModal?.();
    });
  }

  window.AriaStatusBar = { refresh, apply };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
