/** Video studio — keyframe checkpoints, gallery, upload, trim, frame analysis. */

function escapeHtml(s) {
  if (typeof window.escapeHtml === "function") return window.escapeHtml(s);
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function videoStudioResolveUrl(pathOrName, { playback = true } = {}) {
  const file = (pathOrName || "").split(/[/\\]/).pop();
  if (!file) return "";
  let name = file;
  if (playback && !/\.webm$/i.test(name)) {
    name = name.replace(/\.(mp4|mov|m4v|mkv|avi)$/i, ".webm");
  }
  const base = `/api/video-gallery/${encodeURIComponent(name)}`;
  if (typeof window.mediaNeedsApiKey === "function"
      && typeof window.isSameMachineHost === "function"
      && window.mediaNeedsApiKey() && !window.isSameMachineHost()) {
    return typeof window.apiAuthUrl === "function" ? window.apiAuthUrl(base) : base;
  }
  return typeof window.apiAuthUrl === "function" ? window.apiAuthUrl(base) : base;
}

function resolveVideoUrlForStudio(pathOrName, opts) {
  // Prefer shared media_urls helper when present (loaded after this file).
  if (typeof window.resolveVideoUrl === "function") {
    return window.resolveVideoUrl(pathOrName, opts);
  }
  return videoStudioResolveUrl(pathOrName, opts);
}

function attachVideoLoadError(video) {
  if (!video || video.dataset.mediaErrorBound) return;
  video.dataset.mediaErrorBound = "1";
  video.addEventListener("error", () => {
    const parent = video.closest(".video-gallery-item") || video.parentElement;
    if (!parent || parent.querySelector(".media-load-warn")) return;
    const warn = document.createElement("p");
    warn.className = "media-load-warn warn small";
    warn.textContent = "Video failed to load — if using LAN, ensure API key is set";
    parent.appendChild(warn);
  });
}

async function appendGalleryVideo(videoEl, fileName) {
  attachVideoLoadError(videoEl);
  if (typeof window.resolveVideoPlaybackUrl === "function") {
    const playback = await window.resolveVideoPlaybackUrl(fileName);
    if (playback.ok && playback.url) {
      videoEl.src = playback.url;
      return;
    }
    if (playback.needsKey) {
      const parent = videoEl.closest(".video-gallery-item") || videoEl.parentElement;
      if (parent && !parent.querySelector(".media-load-warn")) {
        const warn = document.createElement("p");
        warn.className = "media-load-warn warn small";
        warn.innerHTML = 'Video needs API key — <button type="button" class="ghost-btn small media-key-btn">Enter key</button>';
        warn.querySelector(".media-key-btn")?.addEventListener("click", () => {
          if (typeof showApiKeyModal === "function") showApiKeyModal("");
        });
        parent.appendChild(warn);
      }
      return;
    }
  }
  videoEl.src = resolveVideoUrlForStudio(fileName);
}

let videoSettingsBusy = false;

function populateVideoCheckpointFiles(settings) {
  const sel = document.getElementById("videoCheckpointFileSelect");
  if (!sel || !settings) return;
  const active = settings.keyframe_checkpoint_active || "";
  const files = settings.all_checkpoints || [];
  const options = ['<option value="__preset__">Use preset above</option>'];
  files.forEach((f) => {
    const nsfw = (settings.uncensored_checkpoints || []).includes(f.name) ? " · NSFW" : "";
    options.push(
      `<option value="${escapeHtml(f.name)}">${escapeHtml(f.name)} (${f.family}${nsfw})</option>`,
    );
  });
  sel.innerHTML = options.join("");
  sel.value = settings.keyframe_checkpoint || "__preset__";
  if (sel.value !== settings.keyframe_checkpoint && settings.keyframe_checkpoint) {
    sel.value = settings.keyframe_checkpoint;
  }
  if (active && ![...sel.options].some((o) => o.value === active)) {
    const opt = document.createElement("option");
    opt.value = active;
    opt.textContent = active;
    sel.appendChild(opt);
    sel.value = active;
  }
}

async function loadVideoSettings() {
  const status = document.getElementById("videoEngineStatus");
  const banner = document.getElementById("videoEngineUncensoredBanner");
  const hint = document.getElementById("videoEngineInstallHint");
  const nsfwBtn = document.getElementById("videoEngineInstallNsfwBtn");
  const adBtn = document.getElementById("videoEngineInstallAdBtn");
  const presetSel = document.getElementById("videoCheckpointSelect");
  const fileSel = document.getElementById("videoCheckpointFileSelect");
  const engineSel = document.getElementById("videoEngineSelect");
  const adFrames = document.getElementById("videoAdFramesInput");
  try {
    const res = await fetch("/api/video/settings");
    const s = await res.json();
    const dur = document.getElementById("videoDurationInput");
    const fps = document.getElementById("videoFpsInput");
    if (dur) dur.value = s.duration_sec ?? 4;
    if (fps) fps.value = s.fps ?? 8;
    const wEl = document.getElementById("videoWidthInput");
    const hEl = document.getElementById("videoHeightInput");
    if (wEl && s.width) wEl.value = s.width;
    if (hEl && s.height) hEl.value = s.height;
    if (engineSel && s.engine) engineSel.value = s.engine;
    if (adFrames) adFrames.value = s.animatediff_frames ?? 16;
    if (presetSel && s.keyframe_preset) presetSel.value = s.keyframe_preset;
    populateVideoCheckpointFiles(s);
    if (status) {
      const plan = s.clip_plan || {};
      let line = s.note || `Engine: ${s.engine || "auto"}`;
      if (plan.frames && plan.fps) {
        line += ` · AnimateDiff plan: ${plan.frames} frames @ ${plan.fps} fps (~${plan.actual_duration_sec}s`;
        if (plan.truncated && plan.target_duration_sec) {
          line += `, requested ${plan.target_duration_sec}s`;
        }
        line += ")";
      }
      status.textContent = line;
    }
    if (hint) {
      const ad = s.animatediff || {};
      if (!ad.ready && (s.engine === "auto" || s.engine === "animatediff")) {
        hint.classList.remove("hidden");
        hint.textContent = (ad.missing && ad.missing.length)
          ? `AnimateDiff: ${ad.missing.join("; ")}`
          : "AnimateDiff not ready — Ken Burns used as fallback in Auto mode.";
      } else if (s.uncensored_mode && !s.uncensored_recommended_checkpoint) {
        hint.classList.remove("hidden");
        hint.textContent = "No NSFW checkpoints found — same install as Image gallery (~44 GB).";
      } else {
        hint.classList.add("hidden");
      }
    }
    if (adBtn) {
      const ad = s.animatediff || {};
      const show = !ad.ready && (s.engine === "auto" || s.engine === "animatediff");
      adBtn.classList.toggle("hidden", !show);
      adBtn.disabled = adBtn.dataset.running === "1";
      if (!adBtn.dataset.running) adBtn.textContent = "Install AnimateDiff (~2 GB)";
    }
    if (banner) {
      if (s.uncensored_mode) {
        banner.classList.remove("hidden");
        const rec = s.uncensored_recommended_label || s.uncensored_recommended_checkpoint;
        const active = s.keyframe_checkpoint_label || s.keyframe_checkpoint_active;
        banner.textContent = rec
          ? `Uncensored — Ken Burns keyframes use NSFW checkpoints (active: ${active || rec}). AnimateDiff uses SD 1.5.`
          : `Uncensored — install NSFW checkpoints for unrestricted Ken Burns keyframes.`;
      } else {
        banner.classList.add("hidden");
      }
    }
    if (nsfwBtn) {
      const show = Boolean(s.uncensored_mode && !s.uncensored_recommended_checkpoint);
      nsfwBtn.classList.toggle("hidden", !show);
      nsfwBtn.disabled = nsfwBtn.dataset.running === "1";
    }
    if (presetSel) presetSel.disabled = videoSettingsBusy;
    if (fileSel) fileSel.disabled = videoSettingsBusy;
    if (engineSel) engineSel.disabled = videoSettingsBusy;
    if (adFrames) adFrames.disabled = videoSettingsBusy;
  } catch (err) {
    if (status) status.textContent = "Could not load video settings";
    window.showAriaToast?.(err?.message || "Could not load video settings", "err", 4000);
  }
}

async function postVideoSettings(form) {
  videoSettingsBusy = true;
  await loadVideoSettings();
  try {
    const res = await fetch("/api/video/settings", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      const msg = data.message || data.detail || "Settings update failed";
      window.showAriaToast?.(msg, "err", 5000);
      return;
    }
    window.showAriaToast?.("Video settings saved", "ok", 2000);
  } catch (err) {
    window.showAriaToast?.(err?.message || "Settings update failed", "err", 5000);
  } finally {
    videoSettingsBusy = false;
    loadVideoSettings();
  }
}

async function saveVideoSettings() {
  const form = new FormData();
  const dur = document.getElementById("videoDurationInput")?.value;
  const fps = document.getElementById("videoFpsInput")?.value;
  const engine = document.getElementById("videoEngineSelect")?.value;
  const adFrames = document.getElementById("videoAdFramesInput")?.value;
  const width = document.getElementById("videoWidthInput")?.value;
  const height = document.getElementById("videoHeightInput")?.value;
  if (dur) form.append("duration_sec", dur);
  if (fps) form.append("fps", fps);
  if (engine) form.append("engine", engine);
  if (adFrames) form.append("animatediff_frames", adFrames);
  if (width) form.append("width", width);
  if (height) form.append("height", height);
  await postVideoSettings(form);
}

async function setVideoEngine(engine) {
  const form = new FormData();
  form.append("engine", engine);
  await postVideoSettings(form);
}

async function setVideoKeyframePreset(preset) {
  const form = new FormData();
  form.append("keyframe_preset", preset);
  await postVideoSettings(form);
}

async function setVideoKeyframeFile(file) {
  const form = new FormData();
  form.append("keyframe_checkpoint", file);
  await postVideoSettings(form);
}

async function loadVideoGallery() {
  const grid = document.getElementById("videoGalleryGrid");
  if (!grid) return;
  grid.innerHTML = "<p class=\"muted\">Loading…</p>";
  await loadVideoSettings();
  try {
    const res = await fetch("/api/video-gallery", { cache: "no-store" });
    const data = await res.json();
    const videos = data.videos || [];
    if (!videos.length) {
      grid.innerHTML = `<p class="muted">No videos yet. <button type="button" class="ghost-btn tiny" id="videoEmptyPromptBtn">Focus prompt</button> — generate stays in Video Studio.</p>`;
      grid.querySelector("#videoEmptyPromptBtn")?.addEventListener("click", () => document.getElementById("videoPromptInput")?.focus());
      return;
    }
    grid.innerHTML = videos.map((v) => {
      if (v.restricted || v.thumb_blocked) {
        return `<div class="video-gallery-item restricted" data-video-name="${escapeHtml(v.name)}">
          <p class="video-item-name">Restricted</p>
          <p class="muted tiny">${escapeHtml(v.preview_message || "Created in uncensored mode")}</p>
        </div>`;
      }
      const metaBits = [v.method, v.engine, v.seed != null ? `seed ${v.seed}` : "", v.duration != null ? `${v.duration}s` : ""]
        .filter(Boolean).join(" · ");
      return `<div class="video-gallery-item" data-path="${escapeHtml(v.path)}" data-video-name="${escapeHtml(v.name)}">
        <button type="button" class="gallery-del video-del" data-name="${escapeHtml(v.name)}" title="Delete video" aria-label="Delete video">×</button>
        <video preload="metadata" class="video-thumb clickable-video" title="Click to open player"></video>
        <p class="video-item-name">${escapeHtml(v.name)}</p>
        ${metaBits ? `<p class="muted tiny">${escapeHtml(metaBits)}</p>` : ""}
        <button type="button" class="ghost-btn small video-analyze-btn" data-path="${escapeHtml(v.path)}">Analyze frame</button>
        <button type="button" class="ghost-btn small video-trim-btn" data-path="${escapeHtml(v.path)}">Trim</button>
      </div>`;
    }).join("");

    grid.querySelectorAll(".video-gallery-item").forEach((item) => {
      const video = item.querySelector("video");
      const name = item.dataset.videoName;
      if (video && name) {
        void appendGalleryVideo(video, name).then(() => {
          if (typeof window.bindClickableVideos === "function") window.bindClickableVideos(item);
        });
      }
    });

    grid.querySelectorAll(".video-del").forEach((btn) => {
      btn.addEventListener("click", async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const name = btn.dataset.name;
        if (!name || !confirm("Delete this video?")) return;
        btn.disabled = true;
        try {
          const res = await fetch(`/api/video-gallery/${encodeURIComponent(name)}`, { method: "DELETE" });
          const data = await res.json().catch(() => ({}));
          if (!res.ok || data.ok === false) {
            const msg = data.message || data.detail || res.statusText || "Delete failed";
            btn.disabled = false;
            if (window.showAriaToast) window.showAriaToast(msg, "error");
            else window.showAriaToast?.(msg, "err", 5000);
            return;
          }
          btn.closest(".video-gallery-item")?.remove();
          if (window.showAriaToast) window.showAriaToast(`Deleted ${name}`, "info");
          if (!grid.querySelector(".video-gallery-item")) {
            grid.innerHTML = `<p class="muted">No videos yet. <button type="button" class="ghost-btn tiny" id="videoEmptyPromptBtn">Focus prompt</button></p>`;
            grid.querySelector("#videoEmptyPromptBtn")?.addEventListener("click", () => document.getElementById("videoPromptInput")?.focus());
          }
        } catch (e) {
          btn.disabled = false;
          if (window.showAriaToast) window.showAriaToast(e.message || "Delete failed", "error");
        }
      });
    });
    grid.querySelectorAll(".video-analyze-btn").forEach((btn) => {
      btn.addEventListener("click", () => analyzeVideoFrame(btn.dataset.path));
    });
    grid.querySelectorAll(".video-trim-btn").forEach((btn) => {
      btn.addEventListener("click", () => trimVideoPrompt(btn.dataset.path));
    });
  } catch (err) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon" aria-hidden="true">▶</div><p class="empty-state-title">Couldn’t load videos</p><p class="muted">${String(err?.message || "Network or server error").slice(0, 160)}</p><div class="empty-state-actions"><button type="button" class="apply-btn small" id="videoGalleryRetryBtn">Retry</button><button type="button" class="ghost-btn small" id="videoGalleryChatBtn">Ask Aria</button></div></div>`;
    document.getElementById("videoGalleryRetryBtn")?.addEventListener("click", () => loadVideoGallery());
    document.getElementById("videoGalleryChatBtn")?.addEventListener("click", () => {
      window.switchToView?.("chat");
      setTimeout(() => window.jarvisSendToChat?.("Help me troubleshoot the video gallery"), 80);
    });
    window.showAriaToast?.(err?.message || "Failed to load videos — Retry from the gallery", "err", 5000);
  }
}

async function analyzeVideoFrame(path) {
  const sec = prompt("Analyze at second (e.g. 0 or 12.5):", "0");
  if (sec === null) return;
  const question = prompt("Question about this frame:", "Describe this video frame.") || "Describe this video frame.";
  try {
    const form = new FormData();
    form.append("path", path);
    form.append("second", sec);
    form.append("question", question);
    const res = await fetch("/api/video/analyze-frame", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      const msg = data.message || `Analysis failed (${res.status})`;
      window.showAriaToast?.(msg, "err", 5000);
      return;
    }
    window.showAriaToast?.("Frame analysis ready", "ok", 2500);
    if (typeof window.jarvisSendToChat === "function") {
      window.jarvisSendToChat(`Frame analysis:\n\n${data.message}`);
    } else {
      window.showAriaToast?.(data.message || "Analysis ready", "info", 6000);
    }
  } catch (err) {
    window.showAriaToast?.(err?.message || "Frame analysis failed", "err", 5000);
  }
}

async function trimVideoPrompt(path) {
  const start = prompt("Trim start (seconds):", "0");
  if (start === null) return;
  const duration = prompt("Duration (seconds):", "5");
  if (duration === null) return;
  try {
    const form = new FormData();
    form.append("path", path);
    form.append("start", start);
    form.append("duration", duration);
    const res = await fetch("/api/video/trim", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      window.showAriaToast?.(data.message || `Trim failed (${res.status})`, "err", 5000);
      return;
    }
    window.showAriaToast?.("Video trimmed", "ok", 2500);
    loadVideoGallery();
  } catch (err) {
    window.showAriaToast?.(err?.message || "Trim failed", "err", 5000);
  }
}

document.getElementById("videoUploadInput")?.addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  try {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/video/upload", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    e.target.value = "";
    if (!res.ok || data.ok === false) {
      window.showAriaToast?.(data.message || `Upload failed (${res.status})`, "err", 5000);
      return;
    }
    window.showAriaToast?.("Video uploaded", "ok", 2500);
    loadVideoGallery();
  } catch (err) {
    e.target.value = "";
    window.showAriaToast?.(err?.message || "Upload failed", "err", 5000);
  }
});

document.getElementById("videoFreeVramBtn")?.addEventListener("click", async () => {
  const status = document.getElementById("videoEngineStatus");
  try {
    if (typeof window.freeJarvisVram === "function") {
      await window.freeJarvisVram(status);
    } else {
      const res = await fetch("/api/gpu/free-vram", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        throw new Error(data.message || data.detail || `Free VRAM failed (${res.status})`);
      }
      if (status) status.textContent = "VRAM freed — ready for video gen";
      window.showAriaToast?.("VRAM freed", "ok", 3000);
    }
  } catch (err) {
    if (status) status.textContent = err.message || "Free VRAM failed";
    window.showAriaToast?.(err.message || "Free VRAM failed", "err", 5000);
  }
});

document.getElementById("videoSettingsSaveBtn")?.addEventListener("click", () => saveVideoSettings());

document.getElementById("videoCheckpointSelect")?.addEventListener("change", (e) => {
  if (videoSettingsBusy) return;
  setVideoKeyframePreset(e.target.value);
});

document.getElementById("videoCheckpointFileSelect")?.addEventListener("change", (e) => {
  if (videoSettingsBusy) return;
  setVideoKeyframeFile(e.target.value);
});

document.getElementById("videoEngineSelect")?.addEventListener("change", (e) => {
  if (videoSettingsBusy) return;
  setVideoEngine(e.target.value);
});

document.getElementById("videoEngineInstallAdBtn")?.addEventListener("click", async () => {
  const btn = document.getElementById("videoEngineInstallAdBtn");
  if (!btn || btn.dataset.running === "1") return;
  btn.disabled = true;
  btn.textContent = "Starting install…";
  try {
    const res = await fetch("/api/comfyui/install-animatediff", { method: "POST" });
    const data = await res.json();
    if (!data.ok) {
      window.showAriaToast?.(data.message || "Install failed", "err", 5000);
      btn.disabled = false;
      btn.textContent = "Install AnimateDiff (~2 GB)";
      return;
    }
    btn.dataset.running = "1";
    btn.textContent = "Installing (~2 GB)…";
    const poll = setInterval(async () => {
      if (document.hidden) return;
      const st = await fetch("/api/comfyui/install-animatediff/status").catch(() => null);
      const info = st ? await st.json().catch(() => ({})) : {};
      if (!st) return;
      if (!info.running) {
        clearInterval(poll);
        btn.dataset.running = "0";
        btn.textContent = "Install AnimateDiff (~2 GB)";
        btn.disabled = false;
        loadVideoSettings();
        if (info.readiness?.ready) {
          window.showAriaToast?.("AnimateDiff ready — restart ComfyUI if it was already running.", "ok", 6000);
        } else {
          window.showAriaToast?.(info.message || "AnimateDiff install finished but not ready — check logs", "err", 6000);
        }
      }
    }, 5000);
  } catch (err) {
    btn.disabled = false;
    btn.textContent = "Install AnimateDiff (~2 GB)";
    window.showAriaToast?.(err?.message || "AnimateDiff install failed to start", "err", 5000);
  }
});

document.getElementById("videoEngineInstallNsfwBtn")?.addEventListener("click", async () => {
  const btn = document.getElementById("videoEngineInstallNsfwBtn");
  if (!btn || btn.dataset.running === "1") return;
  btn.disabled = true;
  btn.textContent = "Starting download…";
  try {
    const res = await fetch("/api/comfyui/install-nsfw", { method: "POST" });
    const data = await res.json();
    if (!data.ok) {
      const msg = data.message || "Install failed";
      window.showAriaToast?.(msg, "err", 5000);
      btn.disabled = false;
      btn.textContent = "Install NSFW checkpoints";
      return;
    }
    btn.dataset.running = "1";
    btn.textContent = "Downloading (~44 GB)…";
    const poll = setInterval(async () => {
      if (document.hidden) return;
      const st = await fetch("/api/comfyui/install-nsfw/status").catch(() => null);
      const info = st ? await st.json().catch(() => ({})) : {};
      if (!st) return;
      if (!info.running) {
        clearInterval(poll);
        btn.dataset.running = "0";
        btn.textContent = "Install NSFW checkpoints";
        btn.disabled = false;
        loadVideoSettings();
        const failed = info.error || /error|fail/i.test(info.message || "");
        window.showAriaToast?.(
          info.message || (failed ? "NSFW checkpoint install failed" : "NSFW checkpoint install finished"),
          failed ? "err" : "ok",
          4000,
        );
      }
    }, 8000);
  } catch (err) {
    btn.disabled = false;
    btn.textContent = "Install NSFW checkpoints";
    window.showAriaToast?.(err?.message || "NSFW install failed to start", "err", 5000);
  }
});

document.getElementById("videoOpenGalleryBtn")?.addEventListener("click", () => {
  window.switchToView?.("gallery");
});
document.getElementById("videoOpenMemeBtn")?.addEventListener("click", () => {
  window.switchToView?.("meme");
});
document.getElementById("videoOpenMcBtn")?.addEventListener("click", () => {
  window.switchToView?.("mission") || window.switchToView?.("mission-control");
});

let videoActiveJobId = null;
let videoLastParams = null;

function setVideoJobStatus(msg, tone) {
  const el = document.getElementById("videoJobStatus");
  if (el) {
    el.textContent = msg || "";
    el.classList.toggle("warn", tone === "err");
  }
  if (msg && tone) window.showAriaToast?.(msg, tone === "err" ? "err" : tone === "ok" ? "ok" : "info", 3500);
}

async function pollVideoMediaJob(jobId) {
  videoActiveJobId = jobId;
  document.getElementById("videoCancelGenBtn")?.classList.remove("hidden");
  document.getElementById("storyboardCancelBtn")?.classList.remove("hidden");
  const res = await fetch(`/api/media/job/${encodeURIComponent(jobId)}`);
  const data = await res.json();
  if (!data.ok) throw new Error(data.message || "Job not found");
  const label = data.message || (data.done ? "Done" : "Working…");
  const pct = data.pct != null ? ` (${data.pct}%)` : "";
  setVideoJobStatus(`${label}${pct}`);
  const sb = document.getElementById("storyboardStatus");
  if (sb && document.activeElement?.id?.includes("storyboard")) sb.textContent = `${label}${pct}`;
  if (!data.done) {
    await new Promise((r) => setTimeout(r, 1500));
    return pollVideoMediaJob(jobId);
  }
  videoActiveJobId = null;
  document.getElementById("videoCancelGenBtn")?.classList.add("hidden");
  document.getElementById("storyboardCancelBtn")?.classList.add("hidden");
  if (data.cancelled) throw new Error("Cancelled");
  if (!data.result?.ok) throw new Error(data.error || data.result?.message || "Job failed");
  return data.result;
}

function collectVideoParams() {
  const prompt = document.getElementById("videoPromptInput")?.value?.trim() || "";
  const params = {
    prompt,
    enhance: !!document.getElementById("videoEnhanceToggle")?.checked,
    style_preset: document.getElementById("videoStylePreset")?.value || "",
    duration: document.getElementById("videoDurationInput")?.value || "",
    fps: document.getElementById("videoFpsInput")?.value || "",
    width: document.getElementById("videoWidthInput")?.value || "",
    height: document.getElementById("videoHeightInput")?.value || "",
    engine: document.getElementById("videoEngineSelect")?.value || "auto",
    negative: document.getElementById("videoNegativeInput")?.value?.trim() || "",
    enhanced_prompt: document.getElementById("videoEnhancedInput")?.value?.trim() || "",
    frames: document.getElementById("videoAdFramesInput")?.value || "",
    motion_strength: document.getElementById("videoMotionStrength")?.value || "",
    keyframe_preset: document.getElementById("videoCheckpointSelect")?.value || "",
  };
  const fileCkpt = document.getElementById("videoCheckpointFileSelect")?.value;
  if (fileCkpt && fileCkpt !== "__preset__") params.checkpoint = fileCkpt;
  if (document.getElementById("videoRandomSeed")?.checked) params.random_seed = true;
  else if (document.getElementById("videoSeedInput")?.value) params.seed = document.getElementById("videoSeedInput").value;
  return params;
}

async function loadVideoPresets() {
  const sel = document.getElementById("videoStylePreset");
  if (!sel) return;
  try {
    const res = await fetch("/api/video-generation/presets");
    const data = await res.json();
    if (!data.ok) return;
    const cur = sel.value;
    sel.innerHTML = `<option value="">— none —</option>`;
    for (const p of data.items || []) {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.title || p.id;
      sel.appendChild(opt);
    }
    if (cur) sel.value = cur;
  } catch { /* ignore */ }
}

async function previewVideoEnhance() {
  const prompt = document.getElementById("videoPromptInput")?.value?.trim();
  if (!prompt) {
    window.showAriaToast?.("Enter a prompt first", "warn");
    return;
  }
  const box = document.getElementById("videoEnhancePreview");
  try {
    const res = await fetch("/api/video-generation/enhance-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        enhance: !!document.getElementById("videoEnhanceToggle")?.checked,
        negative: document.getElementById("videoNegativeInput")?.value || "",
      }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.message || "Preview failed");
    if (box) {
      box.classList.remove("hidden");
      box.innerHTML = `<strong>Original:</strong> ${escapeHtml(data.original)}<br/><strong>Enhanced:</strong> ${escapeHtml(data.enhanced)}`
        + (data.negative ? `<br/><strong>Negative:</strong> ${escapeHtml(data.negative)}` : "");
    }
    const enh = document.getElementById("videoEnhancedInput");
    if (enh && data.enhanced) enh.value = data.enhanced;
    document.getElementById("videoAdvancedParams")?.classList.remove("hidden");
  } catch (e) {
    window.showAriaToast?.(e.message || "Enhance preview failed", "err");
  }
}

async function showVideoRecovery(error) {
  try {
    const res = await fetch("/api/video-generation/recovery", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ error }),
    });
    const data = await res.json();
    const el = document.getElementById("videoJobStatus");
    if (!el || !data.actions?.length) return;
    const wrap = document.createElement("span");
    wrap.className = "gallery-recovery-actions";
    for (const a of data.actions.slice(0, 5)) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "ghost-btn tiny";
      b.textContent = a.label;
      b.addEventListener("click", async () => {
        if (a.view) {
          window.switchToView?.(a.view === "mission-control" ? "mission" : a.view);
          return;
        }
        if (a.action === "free_vram") {
          await window.freeJarvisVram?.();
          return;
        }
        if (a.action === "retry") {
          const params = { ...(videoLastParams || {}) };
          if (a.engine) params.engine = a.engine;
          if (a.frames) params.frames = a.frames;
          if (a.duration) params.duration = a.duration;
          videoGenerateInStudio({ params });
        }
      });
      wrap.appendChild(b);
      wrap.appendChild(document.createTextNode(" "));
    }
    el.appendChild(document.createTextNode(" "));
    el.appendChild(wrap);
  } catch { /* ignore */ }
}

async function videoGenerateInStudio(opts = {}) {
  const params = opts.params || collectVideoParams();
  if (!params.prompt) {
    window.showAriaToast?.("Enter a video description first", "warn");
    document.getElementById("videoPromptInput")?.focus();
    return;
  }
  const proceed = (await window.vramPreflight?.("generate_video")) !== false;
  if (!proceed) return;
  const btn = document.getElementById("videoGenerateBtn");
  if (btn) btn.disabled = true;
  setVideoJobStatus("Queuing video…");
  videoLastParams = { ...params };
  try {
    const res = await fetch("/api/video-generation/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...params, source: "studio" }),
    });
    const data = await res.json();
    if (!res.ok || data.ok === false) throw new Error(data.message || "Queue failed");
    const result = data.pending && data.job_id ? await pollVideoMediaJob(data.job_id) : data;
    const name = result.video_name || result.video_path?.split(/[/\\]/).pop() || "video";
    const method = result.generation_method ? ` · ${result.generation_method}` : "";
    setVideoJobStatus(`Generated ${name}${method}`, "ok");
    if (result.seed != null && document.getElementById("videoSeedInput")) {
      document.getElementById("videoSeedInput").value = String(result.seed);
    }
    window.jarvisNotify?.("Video ready", name);
    loadVideoGallery();
  } catch (err) {
    setVideoJobStatus(err.message || "Generation failed", "err");
    showVideoRecovery(err.message || "");
  } finally {
    if (btn) btn.disabled = false;
    videoActiveJobId = null;
    document.getElementById("videoCancelGenBtn")?.classList.add("hidden");
  }
}

async function videoGenerateAnother() {
  let params = videoLastParams;
  if (!params) {
    try {
      const res = await fetch("/api/video-generation/last-settings");
      const data = await res.json();
      if (data.prompt) {
        params = { prompt: data.prompt, negative: data.negative || "", enhanced_prompt: data.enhanced || "", random_seed: true };
        if (document.getElementById("videoPromptInput")) document.getElementById("videoPromptInput").value = data.prompt;
      }
    } catch { /* ignore */ }
  }
  if (!params?.prompt) {
    window.showAriaToast?.("Nothing to regenerate yet", "warn");
    return;
  }
  return videoGenerateInStudio({ params: { ...params, random_seed: true } });
}

async function cancelVideoJob() {
  const id = videoActiveJobId;
  if (!id) return;
  await fetch(`/api/media/job/${encodeURIComponent(id)}/cancel`, { method: "POST" }).catch(() => {});
  setVideoJobStatus("Cancelling…", "err");
}

function setVideoUiLevel(level) {
  const adv = document.getElementById("videoAdvancedParams");
  const exp = document.getElementById("videoExpertParams");
  adv?.classList.toggle("hidden", level === "simple");
  exp?.classList.toggle("hidden", level !== "expert");
  adv?.setAttribute("aria-hidden", level === "simple" ? "true" : "false");
  exp?.setAttribute("aria-hidden", level === "expert" ? "false" : "true");
  document.getElementById("videoSimpleBtn")?.setAttribute("aria-pressed", level === "simple" ? "true" : "false");
  document.getElementById("videoExpertBtn")?.setAttribute("aria-pressed", level === "expert" ? "true" : "false");
  document.getElementById("videoAdvancedToggle")?.setAttribute("aria-expanded", level !== "simple" ? "true" : "false");
}

document.getElementById("videoGenerateBtn")?.addEventListener("click", () => videoGenerateInStudio());
document.getElementById("videoCancelGenBtn")?.addEventListener("click", cancelVideoJob);
document.getElementById("storyboardCancelBtn")?.addEventListener("click", cancelVideoJob);
document.getElementById("videoEnhancePreviewBtn")?.addEventListener("click", previewVideoEnhance);
document.getElementById("videoGenAnotherBtn")?.addEventListener("click", videoGenerateAnother);
document.getElementById("videoAdvancedToggle")?.addEventListener("click", () => {
  const open = document.getElementById("videoAdvancedParams")?.classList.toggle("hidden") === false;
  setVideoUiLevel(open ? "advanced" : "simple");
});
document.getElementById("videoSimpleBtn")?.addEventListener("click", () => setVideoUiLevel("simple"));
document.getElementById("videoExpertBtn")?.addEventListener("click", () => setVideoUiLevel("expert"));
document.getElementById("videoPromptInput")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    videoGenerateInStudio();
  }
});
loadVideoPresets();

async function pollStoryboardJob(jobId, statusEl) {
  if (!jobId) return;
  try {
    const result = await pollVideoMediaJob(jobId);
    const name = result.video_name || result.video_path?.split(/[/\\]/).pop() || "storyboard";
    if (statusEl) statusEl.textContent = `Ready: ${name}`;
    window.showAriaToast?.(`Storyboard ready: ${name}`, "ok");
    loadVideoGallery();
  } catch (e) {
    const msg = String(e.message || e);
    if (statusEl) statusEl.textContent = msg;
    window.showAriaToast?.(msg, "err", 5000);
  }
}

document.getElementById("storyboardBuildBtn")?.addEventListener("click", async () => {
  const paths = document.getElementById("storyboardPathsInput")?.value?.trim();
  const statusEl = document.getElementById("storyboardStatus");
  const btn = document.getElementById("storyboardBuildBtn");
  if (!paths) {
    const msg = "Enter comma-separated image paths";
    if (statusEl) statusEl.textContent = msg;
    window.showAriaToast?.(msg, "warn", 3500);
    return;
  }
  if (btn) btn.disabled = true;
  if (statusEl) statusEl.textContent = "Queueing storyboard…";
  try {
    const sec = document.getElementById("storyboardSecInput")?.value || "3.5";
    const res = await fetch("/api/video/storyboard", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paths, sec_per_slide: Number(sec) || 3.5 }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      const msg = data.message || "Could not queue storyboard";
      if (statusEl) statusEl.textContent = msg;
      window.showAriaToast?.(msg, "err", 5000);
      return;
    }
    const queued = data.message || "Storyboard queued…";
    if (statusEl) statusEl.textContent = queued;
    window.showAriaToast?.(queued, "ok", 2500);
    await pollStoryboardJob(data.job_id, statusEl);
  } catch (e) {
    const msg = String(e.message || e);
    if (statusEl) statusEl.textContent = msg;
    window.showAriaToast?.(msg, "err", 5000);
  } finally {
    if (btn) btn.disabled = false;
  }
});

window.loadVideoGallery = loadVideoGallery;
window.videoGenerateInStudio = videoGenerateInStudio;
window.videoGenerateAnother = videoGenerateAnother;
window.openVideoStudio = function () {
  window.switchToView?.("video");
  loadVideoGallery();
};
