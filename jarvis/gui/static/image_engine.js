/** ComfyUI / image engine panel — extracted from app.js. */
(function () {
  "use strict";

async function pollComfySettingsJob(jobId) {
  for (let i = 0; i < 120; i++) {
    await new Promise((r) => setTimeout(r, 1500));
    const res = await fetch(`/api/comfyui/settings/job/${encodeURIComponent(jobId)}`);
    const job = await res.json();
    if (!res.ok) throw new Error(job.message || `HTTP ${res.status}`);
    const st = document.getElementById("statusText");
    if (st) st.textContent = job.message || "Applying ComfyUI settings…";
    if (job.done) {
      if (job.ok === false) throw new Error(job.message || "ComfyUI settings failed");
      return job.result || job;
    }
  }
  throw new Error("ComfyUI settings timed out — check data/logs/comfyui.log");
}

const galleryModeSelect = document.getElementById("galleryModeSelect");
const galleryCheckpointSelect = document.getElementById("galleryCheckpointSelect");
const galleryCheckpointFileSelect = document.getElementById("galleryCheckpointFileSelect");
const galleryWorkflowInput = document.getElementById("galleryWorkflowInput");
const imageEngineStatus = document.getElementById("imageEngineStatus");
const imageEngineInstallHint = document.getElementById("imageEngineInstallHint");
const imageEngineInstallNsfwBtn = document.getElementById("imageEngineInstallNsfwBtn");
const imageEngineUncensoredBanner = document.getElementById("imageEngineUncensoredBanner");
const openComfyUiLink = document.getElementById("openComfyUiLink");
let comfyModeBusy = false;
let comfySettingsFailToasted = false;
let lastComfySettings = null;

function populateCheckpointFileSelect(settings) {
  if (!galleryCheckpointFileSelect || !settings) return;
  const files = settings.all_checkpoints || [];
  const active = settings.checkpoint_file || "__preset__";
  const options = ['<option value="__preset__">Use preset above</option>'];
  for (const file of files) {
    const label = `${file.family} · ${file.name} (${file.size_mb} MB)`;
    options.push(`<option value="${window.escapeHtml(file.name)}">${window.escapeHtml(label)}</option>`);
  }
  galleryCheckpointFileSelect.innerHTML = options.join("");
  galleryCheckpointFileSelect.value = settings.checkpoint_file || "__preset__";
  if (galleryCheckpointFileSelect.value !== active && active !== "__preset__") {
    galleryCheckpointFileSelect.value = active;
  }
}

function updateImageEngineStatus(settings) {
  if (!settings) return;
  lastComfySettings = settings;
  if (openComfyUiLink && settings.comfyui_url) {
    openComfyUiLink.href = settings.comfyui_url;
  }
  populateCheckpointFileSelect(settings);
  if (galleryModeSelect && settings.mode) {
    galleryModeSelect.value = settings.mode;
  }
  if (galleryCheckpointSelect && settings.checkpoint) {
    galleryCheckpointSelect.value = settings.checkpoint;
  }
  if (galleryWorkflowInput && settings.workflow_file_active) {
    galleryWorkflowInput.value = settings.workflow_file_active;
  } else if (galleryWorkflowInput && settings.workflow_file) {
    galleryWorkflowInput.value = settings.workflow_file;
  }
  const active = settings.checkpoint_file_active || settings.checkpoint_label || settings.checkpoint;
  const statusParts = [
    settings.running ? "ComfyUI online" : "ComfyUI offline",
    `Active: ${active}`,
    settings.label || settings.effective || settings.mode,
  ];
  if (settings.prompt_model) {
    statusParts.push(`Prompt LLM: ${settings.prompt_model}`);
  }
  if (settings.workflow_file_active) {
    statusParts.push(`Workflow: ${settings.workflow_file_active.split("/").pop()}`);
  }
  if (imageEngineStatus) {
    imageEngineStatus.textContent = statusParts.filter(Boolean).join(" · ");
    imageEngineStatus.classList.toggle("muted", settings.running);
  }
  if (imageEngineUncensoredBanner) {
    if (settings.uncensored_mode) {
      const rec = settings.uncensored_recommended_label || settings.uncensored_recommended_checkpoint;
      const install = settings.install_scripts?.nsfw || "./scripts/install-nsfw-checkpoints.sh";
      let banner = `<strong>Uncensored mode</strong> — prompt expansion uses <code>${window.escapeHtml(settings.prompt_model || "dolphin3:latest")}</code>`;
      if (rec) {
        banner += `. Recommended checkpoint: <strong>${window.escapeHtml(rec)}</strong>`;
      } else {
        banner += `. Install NSFW checkpoints: <code>${window.escapeHtml(install)}</code>`;
      }
      imageEngineUncensoredBanner.innerHTML = banner;
      imageEngineUncensoredBanner.classList.remove("hidden");
    } else {
      imageEngineUncensoredBanner.textContent = "";
      imageEngineUncensoredBanner.classList.add("hidden");
    }
  }
  if (imageEngineInstallHint) {
    const files = settings.all_checkpoints || [];
    let hint = "";
    if (settings.uncensored_mode && !settings.uncensored_recommended_checkpoint) {
      hint = `Uncensored mode: run ${settings.install_scripts?.nsfw || "./scripts/install-nsfw-checkpoints.sh"} (~16 GB total)`;
    } else if (settings.checkpoint === "quality" && settings.installed && !settings.installed.quality) {
      hint = `SDXL 1.0 not installed. Run ${settings.install_scripts?.quality || "./scripts/install-sdxl-base.sh"}`;
    } else if (settings.checkpoint === "flux" && settings.installed && !settings.installed.flux) {
      hint = `Flux Schnell not installed. Run ${settings.install_scripts?.flux || "./scripts/install-flux-schnell.sh"}`;
    } else if (!files.length && settings.checkpoints_dir) {
      hint = `No checkpoints in ${settings.checkpoints_dir}. Install SDXL or Flux using the scripts above.`;
    }
    imageEngineInstallHint.textContent = hint;
    imageEngineInstallHint.classList.toggle("hidden", !hint);
  }
  if (imageEngineInstallNsfwBtn) {
    const showNsfw = Boolean(
      settings.uncensored_mode && !settings.uncensored_recommended_checkpoint,
    );
    imageEngineInstallNsfwBtn.classList.toggle("hidden", !showNsfw);
    imageEngineInstallNsfwBtn.disabled = imageEngineInstallNsfwBtn.dataset.running === "1";
  }
}

imageEngineInstallNsfwBtn?.addEventListener("click", async () => {
  if (!imageEngineInstallNsfwBtn || imageEngineInstallNsfwBtn.dataset.running === "1") return;
  imageEngineInstallNsfwBtn.disabled = true;
  imageEngineInstallNsfwBtn.textContent = "Starting download…";
  try {
    const res = await fetch("/api/comfyui/install-nsfw", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      { const __st = document.getElementById("statusText"); if (__st) __st.textContent = data.message || "Could not start NSFW install"; }
      window.showAriaToast?.(data.message || "Could not start NSFW install", "err", 5000);
      imageEngineInstallNsfwBtn.disabled = false;
      imageEngineInstallNsfwBtn.textContent = "Install NSFW checkpoints";
      return;
    }
    imageEngineInstallNsfwBtn.dataset.running = "1";
    imageEngineInstallNsfwBtn.textContent = "Downloading (~44 GB)…";
    { const __st = document.getElementById("statusText"); if (__st) __st.textContent = data.message || "NSFW checkpoint download started"; }
    const poll = setInterval(async () => {
      if (document.hidden) return;
      try {
        const stRes = await fetch("/api/comfyui/install-nsfw/status");
        const st = await stRes.json().catch(() => ({}));
        if (!stRes.ok) throw new Error(st.message || `Status check failed (${stRes.status})`);
        if (!st.running) {
          clearInterval(poll);
          imageEngineInstallNsfwBtn.dataset.running = "0";
          imageEngineInstallNsfwBtn.textContent = "Install NSFW checkpoints";
          imageEngineInstallNsfwBtn.disabled = false;
          await loadComfyMode();
          const failed = st.error || /error|fail/i.test(st.message || "");
          window.showAriaToast?.(
            st.message || (failed ? "NSFW checkpoint install failed" : "NSFW checkpoint install finished"),
            failed ? "err" : "ok",
            4000,
          );
        }
      } catch (err) {
        clearInterval(poll);
        imageEngineInstallNsfwBtn.dataset.running = "0";
        imageEngineInstallNsfwBtn.textContent = "Install NSFW checkpoints";
        imageEngineInstallNsfwBtn.disabled = false;
        window.showAriaToast?.(
          err?.message || "Lost contact while installing NSFW checkpoints",
          "err",
          5000,
        );
      }
    }, 8000);
  } catch (err) {
    imageEngineInstallNsfwBtn.disabled = false;
    imageEngineInstallNsfwBtn.textContent = "Install NSFW checkpoints";
    window.showAriaToast?.(err.message || "NSFW install failed to start", "err", 5000);
  }
});

function syncComfySettings(settings) {
  if (comfyModeBusy || !settings) return;
  updateImageEngineStatus(settings);
}

async function loadComfyMode() {
  if (!galleryModeSelect && !galleryCheckpointSelect) return;
  try {
    const res = await fetch("/api/comfyui/settings");
    if (!res.ok) throw new Error(`ComfyUI settings failed (${res.status})`);
    syncComfySettings(await res.json());
  } catch (err) {
    const st = document.getElementById("imageEngineStatus");
    if (st) st.textContent = err.message || "ComfyUI settings unavailable";
    if (!comfySettingsFailToasted) {
      comfySettingsFailToasted = true;
      window.showAriaToast?.(err.message || "ComfyUI settings unavailable", "err", 4000);
    }
  }
}

async function postComfySettings(fields) {
  comfyModeBusy = true;
  if (galleryModeSelect) galleryModeSelect.disabled = true;
  if (galleryCheckpointSelect) galleryCheckpointSelect.disabled = true;
  if (galleryCheckpointFileSelect) galleryCheckpointFileSelect.disabled = true;
  { const __st = document.getElementById("statusText"); if (__st) __st.textContent = fields.mode ? "Restarting ComfyUI…" : "Updating image model…"; }
  try {
    const form = new FormData();
    if (fields.mode) form.append("mode", fields.mode);
    if (fields.checkpoint) form.append("checkpoint", fields.checkpoint);
    if (fields.checkpoint_file) form.append("checkpoint_file", fields.checkpoint_file);
    if (fields.workflow_file) form.append("workflow_file", fields.workflow_file);
    const res = await fetch("/api/comfyui/settings", { method: "POST", body: form });
    let data = await res.json();
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || `HTTP ${res.status}`);
    }
    if (data.pending && data.job_id) {
      data = await pollComfySettingsJob(data.job_id);
    }
    syncComfySettings(data);
    const svcRes = await fetch("/api/services");
    if (svcRes.ok) {
      const svcData = await svcRes.json();
      window.renderServices?.(svcData.services, svcData.comfyui_settings);
    }
    const okLine = `ComfyUI · ${data.checkpoint_label || "SDXL"} · ${data.label || ""}`.trim();
    { const __st = document.getElementById("statusText"); if (__st) __st.textContent = okLine; }
    window.showAriaToast?.(okLine, "ok", 2500);
    return data;
  } finally {
    if (galleryModeSelect) galleryModeSelect.disabled = false;
    if (galleryCheckpointSelect) galleryCheckpointSelect.disabled = false;
    if (galleryCheckpointFileSelect) galleryCheckpointFileSelect.disabled = false;
    comfyModeBusy = false;
  }
}

async function setComfyMode(mode) {
  if (!galleryModeSelect || comfyModeBusy) return;
  const prev = galleryModeSelect.value;
  try {
    await postComfySettings({ mode });
  } catch (e) {
    galleryModeSelect.value = prev;
    { const __st = document.getElementById("statusText"); if (__st) __st.textContent = `ComfyUI switch failed — ${e.message}`; }
    window.showAriaToast?.(`ComfyUI switch failed — ${e.message}`, "err", 5000);
  }
}

async function setComfyCheckpoint(checkpoint) {
  if (!galleryCheckpointSelect || comfyModeBusy) return;
  const prev = galleryCheckpointSelect.value;
  const prevFile = galleryCheckpointFileSelect?.value;
  try {
    await postComfySettings({ checkpoint });
  } catch (e) {
    galleryCheckpointSelect.value = prev;
    if (galleryCheckpointFileSelect && prevFile) galleryCheckpointFileSelect.value = prevFile;
    { const __st = document.getElementById("statusText"); if (__st) __st.textContent = `Model switch failed — ${e.message}`; }
    window.showAriaToast?.(`Model switch failed — ${e.message}`, "err", 5000);
  }
}

async function setComfyCheckpointFile(filename) {
  if (!galleryCheckpointFileSelect || comfyModeBusy) return;
  const prev = galleryCheckpointFileSelect.value;
  try {
    await postComfySettings({ checkpoint_file: filename });
  } catch (e) {
    galleryCheckpointFileSelect.value = prev;
    { const __st = document.getElementById("statusText"); if (__st) __st.textContent = `Checkpoint switch failed — ${e.message}`; }
    window.showAriaToast?.(`Checkpoint switch failed — ${e.message}`, "err", 5000);
  }
}

if (galleryModeSelect) {
  galleryModeSelect.addEventListener("change", () => setComfyMode(galleryModeSelect.value));
}
if (galleryCheckpointSelect) {
  galleryCheckpointSelect.addEventListener("change", () => setComfyCheckpoint(galleryCheckpointSelect.value));
}
if (galleryCheckpointFileSelect) {
  galleryCheckpointFileSelect.addEventListener("change", () => setComfyCheckpointFile(galleryCheckpointFileSelect.value));
}
galleryWorkflowInput?.addEventListener("change", async () => {
  const path = galleryWorkflowInput.value.trim();
  if (!path) return;
  try {
    await postComfySettings({ workflow_file: path });
  } catch (e) {
    { const __st = document.getElementById("statusText"); if (__st) __st.textContent = `Workflow failed — ${e.message}`; }
  }
});
// gallery generate → gallery_view.js
document.getElementById("openImageSettingsBtn")?.addEventListener("click", () => {
  window.switchToView?.("gallery");
  document.getElementById("imageEnginePanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

function setEngineLevel(level) {
  const simple = document.getElementById("imageEngineSimpleBlock");
  const advanced = document.getElementById("imageEngineAdvancedBlock");
  const expert = document.getElementById("imageEngineExpertBlock");
  const btns = {
    simple: document.getElementById("imageEngineSimpleBtn"),
    advanced: document.getElementById("imageEngineAdvancedBtn"),
    expert: document.getElementById("imageEngineExpertBtn"),
  };
  simple?.classList.toggle("hidden", false);
  advanced?.classList.toggle("hidden", level === "simple");
  expert?.classList.toggle("hidden", level !== "expert");
  Object.entries(btns).forEach(([k, el]) => el?.setAttribute("aria-pressed", k === level ? "true" : "false"));
}
document.getElementById("imageEngineSimpleBtn")?.addEventListener("click", () => setEngineLevel("simple"));
document.getElementById("imageEngineAdvancedBtn")?.addEventListener("click", () => setEngineLevel("advanced"));
document.getElementById("imageEngineExpertBtn")?.addEventListener("click", () => setEngineLevel("expert"));

  window.pollComfySettingsJob = pollComfySettingsJob;
  window.syncComfySettings = syncComfySettings;
  window.loadComfyMode = loadComfyMode;
  window.postComfySettings = postComfySettings;
})();
