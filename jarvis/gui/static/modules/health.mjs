/** GPU / health strip helpers (Phase 3 ES module). */

import { $ } from "./util.mjs";

export function renderGpuStatus(gpu) {
  const gpuStatusEl = $("gpuStatus");
  if (!gpuStatusEl || !gpu) return;
  const shortName = (gpu.name || "GPU").replace(/^.*\[AMD\/ATI\]\s*/, "").replace(/\s*\(rev.*$/, "");
  const vram = gpu.vram_mb ? ` · ${Math.round(gpu.vram_mb / 1024)}GB` : "";
  let status = `GPU: ${shortName}${vram}`;
  let cls = "gpu-status";
  if (gpu.ollama_using_gpu) {
    status += " · active";
    cls += " ok";
  } else if (gpu.nvidia_available || gpu.compute_vendor === "nvidia" || gpu.vendor === "nvidia") {
    const free = gpu.free_vram_mb != null ? `${Math.round(Number(gpu.free_vram_mb))}MB free` : "idle";
    status += ` · ${free}`;
    cls += " ok";
  } else if (gpu.rocm_available && gpu.vendor === "amd") {
    status += " · ROCm ready";
    cls += " ok";
  } else if (gpu.vendor === "amd") {
    status += " · ROCm not detected";
    cls += " warn";
  }
  const resLine = gpu.resource_status_line || gpu.resources?.media_queue;
  if (typeof resLine === "string" && resLine.includes("busy")) {
    status += ` · ${resLine.split(" · ").slice(1).join(" · ") || "queue busy"}`;
    cls += " warn";
  } else if (gpu.resources?.media_queue?.pending) {
    status += ` · queue ${gpu.resources.media_queue.pending}`;
  }
  let gpuLine = gpuStatusEl.querySelector(".gpu-line");
  if (!gpuLine) {
    gpuStatusEl.innerHTML = "";
    gpuLine = document.createElement("div");
    gpuLine.className = "gpu-line";
    gpuStatusEl.appendChild(gpuLine);
  }
  gpuLine.textContent = status;
  gpuLine.className = cls;
  const tips = gpu.tips || gpu.vram_guard?.recommendations || [];
  gpuLine.title = [gpu.recommendation, ...tips].filter(Boolean).join("\n");
}

export function renderAudioStatus(audio) {
  const gpuStatusEl = $("gpuStatus");
  if (!gpuStatusEl || !audio) return;
  let line = gpuStatusEl.querySelector(".audio-line");
  if (!line) {
    line = document.createElement("div");
    line.className = "audio-line gpu-status ok";
    gpuStatusEl.appendChild(line);
  }
  line.textContent = `Audio: ${(audio.name || "Sound Blaster").slice(0, 45)}`;
  line.title = `Output: ${audio.output_sink || ""}\nInput: ${audio.input_source || ""}`;
}

export async function loadGpuStatus() {
  try {
    const res = await fetch("/api/gpu");
    if (res.ok) renderGpuStatus(await res.json());
  } catch (_) {}
}

const UI_VERSION = document.querySelector('meta[name="jarvis-ui-version"]')?.content || "unknown";
let serverWasDown = false;
let knownVersion = null;
let liveTimer = null;
let healthTimer = null;
let liveFailStreak = 0;
let liveDownSince = 0;

function mediaWorkActive() {
  return window.mediaWorkActive?.() === true;
}

function setLocalMode(uncensored) {
  const toggle = $("uncensoredToggle");
  const label = $("modeLabel");
  if (toggle) toggle.checked = Boolean(uncensored);
  document.body.classList.toggle("uncensored-mode", Boolean(uncensored));
  if (label) label.textContent = uncensored ? "Uncensored · Local" : "Local AI Assistant";
}

function fetchWithTimeout(url, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, { signal: controller.signal }).finally(() => clearTimeout(timer));
}

/** Live poll: allow brief server stalls (chat/media) without false "down" toasts. */
const LIVE_TIMEOUT_MS = 12000;
const LIVE_FAIL_TOAST_AFTER = 2;
const LIVE_RESTORE_TOAST_AFTER_MS = 15000;

export function renderServices(services, comfySettings) {
  const panel = $("servicesPanel");
  if (!panel || !Array.isArray(services)) return;
  for (const service of services) {
    const row = panel.querySelector(`[data-svc="${CSS.escape(String(service.name || ""))}"]`);
    if (!row) continue;
    row.classList.remove("online", "offline", "starting");
    if (service.running || service.message === "ready") row.classList.add("online");
    else if (service.required) row.classList.add("starting");
    else row.classList.add("offline");
    row.replaceChildren();
    const dot = document.createElement("span");
    dot.className = "svc-dot";
    row.append(dot, document.createTextNode(
      ` ${service.label || service.name || "Service"}${service.detail ? ` · ${service.detail}` : ""}`,
    ));
  }
  if (comfySettings) window.syncComfySettings?.(comfySettings);
}

export function reloadUi(reason = "") {
  const status = $("statusText");
  if (mediaWorkActive()) {
    if (status) status.textContent = "Media job running — reload deferred until it finishes";
    window.showAriaToast?.("Reload deferred while media work is active", "info", 3000);
    return false;
  }
  if (reason && status) status.textContent = reason;
  setTimeout(() => location.reload(), reason ? 350 : 0);
  return true;
}

export async function pollLive() {
  if (document.hidden || mediaWorkActive()) return null;
  const status = $("statusText");
  try {
    const res = await fetchWithTimeout("/api/live", LIVE_TIMEOUT_MS);
    if (!res.ok) throw new Error(`Live check failed (${res.status})`);
    const data = await res.json();
    const wasDownLong =
      serverWasDown && liveDownSince && (Date.now() - liveDownSince) >= LIVE_RESTORE_TOAST_AFTER_MS;
    liveFailStreak = 0;
    liveDownSince = 0;
    if (serverWasDown) {
      serverWasDown = false;
      window.__ariaLiveFailToast = false;
      if (status) {
        status.textContent = (window.activeMediaJobs?.size || 0) > 0
          ? "Server back — finishing media job…"
          : `Ready · v${data.version || "?"}`;
      }
      // Only announce restore after a sustained outage — not brief poll stalls.
      if (wasDownLong) window.showAriaToast?.("Connection restored", "ok", 2500);
    }
    knownVersion = data.version || knownVersion;
    window.applyBranding?.(data);
    const env = $("envStrip");
    if (data.ui_version && data.ui_version !== UI_VERSION && env && !env.dataset.versionWarn) {
      env.dataset.versionWarn = "1";
      env.classList.add("version-warn");
      env.title = `UI ${UI_VERSION} · server expects ${data.ui_version} — Reload UI`;
    }
    setLocalMode(data.uncensored);
    if (data.version && status) {
      status.textContent = data.ready
        ? `Ready · v${data.version}`
        : `Starting services · v${data.version}`;
    }
    return data;
  } catch (error) {
    liveFailStreak += 1;
    if (!liveDownSince) liveDownSince = Date.now();
    serverWasDown = true;
    // Require consecutive failures so a single slow /api/live does not spam.
    if (liveFailStreak >= LIVE_FAIL_TOAST_AFTER && !window.__ariaLiveFailToast) {
      window.__ariaLiveFailToast = true;
      window.showAriaToast?.(
        error?.name === "AbortError" ? "Aria health check timed out — retrying…" : (error?.message || "Lost connection to Aria — retrying…"),
        "err",
        4000,
      );
    }
    return null;
  }
}

export async function loadHealth() {
  const models = $("modelsStatus");
  const status = $("statusText");
  try {
    const [healthRes, servicesRes] = await Promise.all([
      fetchWithTimeout("/api/health", 3000),
      fetchWithTimeout("/api/services", 5000).catch(() => null),
    ]);
    if (!healthRes.ok) throw new Error(`Health check failed (${healthRes.status})`);
    const data = await healthRes.json();
    if (servicesRes?.ok) {
      const serviceData = await servicesRes.json();
      renderServices(serviceData.services, serviceData.comfyui_settings);
      if (serviceData.ollama && data.ollama == null) data.ollama = serviceData.ollama;
    }
    if (data.gpu) renderGpuStatus(data.gpu);
    if (data.audio) renderAudioStatus(data.audio);
    setLocalMode(data.uncensored);
    if (data.services) renderServices(data.services, data.comfyui_settings);

    const visionRow = $("servicesPanel")?.querySelector('[data-svc="vision"]');
    if (visionRow && data.vision) {
      const vision = data.vision;
      visionRow.classList.toggle("online", Boolean(vision.installed));
      visionRow.classList.toggle("offline", !vision.installed);
      const mode = vision.quality_mode === "quality" ? "preset:quality"
        : vision.quality_mode === "fast" ? "preset:fast" : "selected";
      visionRow.replaceChildren();
      const dot = document.createElement("span");
      dot.className = "svc-dot";
      visionRow.append(dot, document.createTextNode(` Vision · ${vision.model || "?"} (${mode})`));
      visionRow.title = vision.note || "";
    }
    if (data.version && status) {
      status.textContent = data.busy
        ? `Busy · ${data.busy_job || "media"} · v${data.version}`
        : data.ready ? `Ready · v${data.version}` : `Starting services · v${data.version}`;
    }
    if (models) {
      if (!data.ollama?.running) {
        models.textContent = "Starting Ollama…";
        models.className = "warn";
      } else if (data.models_missing?.length) {
        models.textContent = `Pulling models: ${data.models_missing.join(", ")}`;
        models.className = "warn";
      } else {
        const configured = data.models || {};
        models.replaceChildren(
          document.createTextNode(configured.general || "?"),
          document.createElement("br"),
          document.createTextNode(configured.coder || "?"),
        );
        if (data.embed_ok === false && data.embed_warning) {
          models.append(document.createElement("br"));
          const warning = document.createElement("span");
          warning.className = "warn";
          warning.textContent = data.embed_warning;
          models.append(warning);
        }
      }
    }
    return data;
  } catch (error) {
    if (models) {
      models.textContent = `Connecting to ${window.ariaName?.() || "ARIA"}…`;
      models.className = "warn";
    }
    if (status) status.textContent = "Connecting…";
    return null;
  }
}

export function startHealthMonitoring() {
  if (liveTimer || healthTimer) return;
  liveTimer = setInterval(pollLive, window.isNativeApp?.() ? 45000 : 20000);
  healthTimer = setInterval(() => {
    if (!document.hidden && !mediaWorkActive()) loadHealth();
  }, 180000);
}

function initHealthModule() {
  $("freeVramBtn")?.addEventListener("click", () => {
    if (typeof window.freeJarvisVram === "function") {
      window.freeJarvisVram($("statusText"));
    }
  });
  $("reloadUiBtn")?.addEventListener("click", () => reloadUi());
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initHealthModule);
} else {
  initHealthModule();
}

window.jarvisHealth = {
  renderGpuStatus,
  renderAudioStatus,
  loadGpuStatus,
  renderServices,
  reloadUi,
  pollLive,
  loadHealth,
  startHealthMonitoring,
  get knownVersion() { return knownVersion; },
};
Object.assign(window, {
  loadGpuStatus,
  renderServices,
  reloadJarvisUi: reloadUi,
  pollLive,
  loadHealth,
  startHealthMonitoring,
});
