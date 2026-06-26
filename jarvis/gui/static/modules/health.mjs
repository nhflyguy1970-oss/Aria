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
  } else if (gpu.rocm_available) {
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

export async function loadGpuStatus() {
  try {
    const res = await fetch("/api/gpu");
    if (res.ok) renderGpuStatus(await res.json());
  } catch (_) {}
}

function initHealthModule() {
  $("freeVramBtn")?.addEventListener("click", () => {
    if (typeof window.freeJarvisVram === "function") {
      window.freeJarvisVram($("statusText"));
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initHealthModule);
} else {
  initHealthModule();
}

window.jarvisHealth = { renderGpuStatus, loadGpuStatus };
