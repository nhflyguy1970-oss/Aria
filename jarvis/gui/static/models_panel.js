/** Models editor panel — extracted from app.js. */
(function () {
  "use strict";

const pullLogEl = document.getElementById("pullLog");
const modelsToggle = document.getElementById("modelsToggle");
const modelsEditor = document.getElementById("modelsEditor");
modelsToggle?.addEventListener("click", () => {
  if (!modelsEditor) return;
  const open = modelsEditor.classList.toggle("hidden") === false;
  modelsToggle.setAttribute("aria-expanded", open ? "true" : "false");
  if (open) loadModelSettings();
});
const modelSelects = {
  general: document.getElementById("modelGeneral"),
  coder: document.getElementById("modelCoder"),
  review: document.getElementById("modelReview"),
  vision: document.getElementById("modelVision"),
  image: document.getElementById("modelImage"),
  embed: document.getElementById("modelEmbed"),
};

let modelSettings = null;

function fillModelSelect(select, choices, value) {
  if (!select) return;
  select.innerHTML = "";
  const seen = new Set();
  const list = [...(choices || [])].sort((a, b) => a.localeCompare(b));
  if (value && !list.includes(value)) list.unshift(value);
  if (list.length === 0 && value) list.push(value);

  list.forEach((name) => {
    if (!name || seen.has(name)) return;
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    if (name === value) opt.selected = true;
    select.appendChild(opt);
    seen.add(name);
  });

  if (list.length === 0) {
    const opt = document.createElement("option");
    opt.value = value || "";
    opt.textContent = value || "(no models — run ollama pull)";
    select.appendChild(opt);
  }
}

function renderModelSettings(settings) {
  if (!settings) return;
  modelSettings = settings;
  const mode = settings.mode || (document.getElementById("uncensoredToggle")?.checked ? "uncensored" : "standard");
  const active = settings.active || settings[mode] || {};
  const choices = settings.choices || settings.installed || [];
  const imageChoices = settings.role_choices?.image || ["comfyui"];

  fillModelSelect(modelSelects.general, choices, active.general);
  fillModelSelect(modelSelects.coder, choices, active.coder);
  fillModelSelect(modelSelects.review, choices, active.review);
  fillModelSelect(modelSelects.vision, choices, active.vision);
  fillModelSelect(modelSelects.image, imageChoices, active.image || "comfyui");
  fillModelSelect(modelSelects.embed, choices, active.embed);

  const hw = settings.hardware || {};
  const hwNote = document.getElementById("hwNote");
  if (hwNote) {
    hwNote.textContent = `${hw.gpu || ""} · ${hw.ram || ""}. ${hw.note || ""}`;
  }

  const editorStatus = document.getElementById("modelsEditorStatus");
  if (editorStatus) {
    const n = settings.installed?.length || 0;
    if (n > 0) {
      editorStatus.textContent = `${n} Ollama models available`;
      editorStatus.classList.remove("warn");
    } else {
      editorStatus.textContent = "Starting Ollama — models will appear shortly";
      editorStatus.classList.add("warn");
    }
  }

  const modelsEl = document.getElementById("modelsStatus");
  if (modelsEl && active.general) {
    const general = document.createElement("span");
    general.textContent = active.general;
    const coder = document.createElement("span");
    coder.textContent = active.coder || "Not configured";
    modelsEl.replaceChildren(general, document.createElement("br"), coder);
  }
}

async function loadModelSettings() {
  const editorStatus = document.getElementById("modelsEditorStatus");
  try {
    const res = await fetch("/api/models/settings");
    if (res.status === 404) {
      if (editorStatus) {
        editorStatus.textContent = `Old server running — restart ${(window.ariaName?.() || "Aria")} from the desktop shortcut`;
        editorStatus.classList.add("warn");
      }
      return null;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const settings = await res.json();
    settings.mode = settings.mode || (document.getElementById("uncensoredToggle")?.checked ? "uncensored" : "standard");
    renderModelSettings(settings);
    return settings;
  } catch (e) {
    if (editorStatus) {
      editorStatus.textContent = `Could not load models: ${e.message}`;
      editorStatus.classList.add("warn");
    }
    window.showAriaToast?.(e.message || "Could not load models", "err", 4000);
    return null;
  }
}

document.getElementById("saveModelsBtn")?.addEventListener("click", async () => {
  try {
    const mode = document.getElementById("uncensoredToggle")?.checked ? "uncensored" : "standard";
    const form = new FormData();
    form.append("mode", mode);
    form.append("general", modelSelects.general?.value || "");
    form.append("coder", modelSelects.coder?.value || "");
    form.append("review", modelSelects.review?.value || "");
    form.append("vision", modelSelects.vision?.value || "");
    form.append("image", modelSelects.image?.value || "");
    form.append("embed", modelSelects.embed?.value || "");
    const res = await fetch("/api/models/settings", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.detail || `Save failed (${res.status})`);
    if (data.settings) renderModelSettings({ ...data.settings, mode });
    const vq = document.getElementById("visionQualitySelect");
    if (vq) vq.value = "custom";
    await fetch("/api/vision/settings", { method: "POST", body: new URLSearchParams({ quality_mode: "custom" }) });
    await window.loadVisionSettings?.();
    const msg = "Models saved (vision: use selected model)";
    (document.getElementById("statusText") || {}).textContent = msg;
    window.showAriaToast?.(msg, "ok", 2500);
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not save models", "err", 5000);
  }
});

document.getElementById("refreshModelsBtn")?.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/models/refresh", { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.detail || `Refresh failed (${res.status})`);
    if (data.settings) {
      renderModelSettings({ ...data.settings, mode: document.getElementById("uncensoredToggle")?.checked ? "uncensored" : "standard" });
    }
    (document.getElementById("statusText") || {}).textContent = "Models refreshed";
    window.showAriaToast?.("Models refreshed", "ok", 2500);
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not refresh models", "err", 5000);
  }
});

document.getElementById("resetModelsBtn")?.addEventListener("click", async () => {
  try {
    const mode = document.getElementById("uncensoredToggle")?.checked ? "uncensored" : "standard";
    const form = new FormData();
    form.append("mode", mode);
    const res = await fetch("/api/models/reset", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.detail || `Reset failed (${res.status})`);
    if (data.settings) renderModelSettings({ ...data.settings, mode });
    (document.getElementById("statusText") || {}).textContent = "Models reset to optimized defaults";
    window.showAriaToast?.("Models reset to defaults", "ok", 2500);
    document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
    document.getElementById("presetQualityBtn")?.classList.add("active");
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not reset models", "err", 5000);
  }
});

async function applyPreset(preset) {
  try {
    const mode = document.getElementById("uncensoredToggle")?.checked ? "uncensored" : "standard";
    const form = new FormData();
    form.append("preset", preset);
    form.append("mode", mode);
    const res = await fetch("/api/models/preset", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.detail || `Preset failed (${res.status})`);
    if (data.settings) {
      renderModelSettings({ ...data.settings, mode });
      (document.getElementById("statusText") || {}).textContent = `Applied ${preset} preset`;
      window.showAriaToast?.(`Applied ${preset} preset`, "ok", 2500);
    }
    document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
    document.getElementById(preset === "fast" ? "presetFastBtn" : "presetQualityBtn")?.classList.add("active");
  } catch (err) {
    window.showAriaToast?.(err.message || `Could not apply ${preset} preset`, "err", 5000);
  }
}

document.getElementById("presetFastBtn")?.addEventListener("click", () => applyPreset("fast"));
document.getElementById("presetQualityBtn")?.addEventListener("click", () => applyPreset("quality"));

async function pullMissingModels() {
  const btn = document.getElementById("pullMissingBtn");
  const editorStatus = document.getElementById("modelsEditorStatus");
  if (btn) btn.disabled = true;
  if (pullLogEl) {
    pullLogEl.classList.remove("hidden");
    pullLogEl.textContent = "Checking missing models…\n";
  }

  try {
    const res = await fetch("/api/models/pull-missing", { method: "POST" });
    const ct = res.headers.get("content-type") || "";

    if (ct.includes("application/json")) {
      const data = await res.json();
      if (pullLogEl) pullLogEl.textContent = data.message || "All models installed.";
      if (editorStatus) editorStatus.textContent = data.message || "All models installed.";
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let event;
        try { event = JSON.parse(line.slice(6)); } catch { continue; }

        if (event.type === "model_start" && pullLogEl) {
          pullLogEl.textContent += `\n▶ ${event.model}\n`;
        } else if (event.type === "progress" && pullLogEl) {
          pullLogEl.textContent += event.message + "\n";
          pullLogEl.scrollTop = pullLogEl.scrollHeight;
        } else if (event.type === "done" && pullLogEl) {
          pullLogEl.textContent += (event.ok ? "✓ " : "✗ ") + (event.message || "") + "\n";
        } else if (event.type === "all_done") {
          (document.getElementById("statusText") || {}).textContent = "Model pull complete";
          await loadModelSettings();
          await window.loadHealth?.();
        }
      }
    }
  } catch (e) {
    if (pullLogEl) pullLogEl.textContent += `Error: ${e.message}\n`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

document.getElementById("pullMissingBtn")?.addEventListener("click", pullMissingModels);


  window.renderModelSettings = renderModelSettings;
  window.loadModelSettings = loadModelSettings;
  window.pullMissingModels = pullMissingModels;
})();
