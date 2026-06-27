/** Video studio — keyframe checkpoints, gallery, upload, trim, frame analysis. */

function resolveVideoUrl(pathOrName, { playback = true } = {}) {
  if (typeof window.resolveVideoPlaybackUrl === "function" && playback) {
    const raw = (pathOrName || "").split(/[/\\]/).pop();
    if (!raw) return "";
    let file = raw.replace(/\.(mp4|mov|m4v|mkv|avi)$/i, ".webm");
    const base = `/api/video-gallery/${encodeURIComponent(file)}`;
    if (typeof window.mediaNeedsApiKey === "function"
      && typeof window.isSameMachineHost === "function"
      && (window.mediaNeedsApiKey() && !window.isSameMachineHost())) {
      return typeof window.apiAuthUrl === "function" ? window.apiAuthUrl(base) : base;
    }
    return base;
  }
  const file = (pathOrName || "").split(/[/\\]/).pop();
  if (!file) return "";
  const base = `/api/video-gallery/${encodeURIComponent(file)}`;
  return typeof window.apiAuthUrl === "function" ? window.apiAuthUrl(base) : base;
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
  videoEl.src = resolveVideoUrl(fileName);
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
  } catch (_) {
    if (status) status.textContent = "Could not load video settings";
  }
}

async function postVideoSettings(form) {
  videoSettingsBusy = true;
  await loadVideoSettings();
  try {
    const res = await fetch("/api/video/settings", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) {
      alert(data.message || "Settings update failed");
    }
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
  if (dur) form.append("duration_sec", dur);
  if (fps) form.append("fps", fps);
  if (engine) form.append("engine", engine);
  if (adFrames) form.append("animatediff_frames", adFrames);
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
      grid.innerHTML = "<p class=\"muted\">No videos yet. Chat: “generate a video of …” or upload below.</p>";
      return;
    }
    grid.innerHTML = videos.map((v) => {
      return `<div class="video-gallery-item" data-path="${escapeHtml(v.path)}" data-video-name="${escapeHtml(v.name)}">
        <button type="button" class="gallery-del video-del" data-name="${escapeHtml(v.name)}" title="Delete">×</button>
        <video preload="metadata" class="video-thumb clickable-video" title="Click to open player"></video>
        <p class="video-item-name">${escapeHtml(v.name)}</p>
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
            else alert(msg);
            return;
          }
          btn.closest(".video-gallery-item")?.remove();
          if (window.showAriaToast) window.showAriaToast(`Deleted ${name}`, "info");
          if (!grid.querySelector(".video-gallery-item")) {
            grid.innerHTML = "<p class=\"muted\">No videos yet. Chat: “generate a video of …” or upload below.</p>";
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
  } catch (_) {
    grid.innerHTML = "<p class=\"muted\">Failed to load videos</p>";
  }
}

async function analyzeVideoFrame(path) {
  const sec = prompt("Analyze at second (e.g. 0 or 12.5):", "0");
  if (sec === null) return;
  const question = prompt("Question about this frame:", "Describe this video frame.") || "Describe this video frame.";
  const form = new FormData();
  form.append("path", path);
  form.append("second", sec);
  form.append("question", question);
  const res = await fetch("/api/video/analyze-frame", { method: "POST", body: form });
  const data = await res.json();
  if (!data.ok) {
    alert(data.message || "Analysis failed");
    return;
  }
  if (typeof window.jarvisSendToChat === "function") {
    window.jarvisSendToChat(`Frame analysis:\n\n${data.message}`);
  } else {
    alert(data.message);
  }
}

async function trimVideoPrompt(path) {
  const start = prompt("Trim start (seconds):", "0");
  if (start === null) return;
  const duration = prompt("Duration (seconds):", "5");
  if (duration === null) return;
  const form = new FormData();
  form.append("path", path);
  form.append("start", start);
  form.append("duration", duration);
  const res = await fetch("/api/video/trim", { method: "POST", body: form });
  const data = await res.json();
  if (!data.ok) {
    alert(data.message || "Trim failed");
    return;
  }
  loadVideoGallery();
}

document.getElementById("videoUploadInput")?.addEventListener("change", async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/video/upload", { method: "POST", body: form });
  const data = await res.json();
  e.target.value = "";
  if (!data.ok) {
    alert(data.message || "Upload failed");
    return;
  }
  loadVideoGallery();
});

document.getElementById("videoFreeVramBtn")?.addEventListener("click", async () => {
  const status = document.getElementById("videoEngineStatus");
  try {
    if (typeof window.freeJarvisVram === "function") {
      await window.freeJarvisVram(status);
    } else {
      const res = await fetch("/api/gpu/free-vram", { method: "POST" });
      const data = await res.json();
      if (status) {
        status.textContent = data.ok ? "VRAM freed — ready for video gen" : (data.message || "Free VRAM failed");
      }
    }
  } catch (_) {}
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
      alert(data.message || "Install failed");
      btn.disabled = false;
      btn.textContent = "Install AnimateDiff (~2 GB)";
      return;
    }
    btn.dataset.running = "1";
    btn.textContent = "Installing (~2 GB)…";
    const poll = setInterval(async () => {
      const st = await fetch("/api/comfyui/install-animatediff/status");
      const info = await st.json();
      if (!info.running) {
        clearInterval(poll);
        btn.dataset.running = "0";
        btn.textContent = "Install AnimateDiff (~2 GB)";
        btn.disabled = false;
        loadVideoSettings();
        if (info.readiness?.ready) {
          alert("AnimateDiff ready — restart ComfyUI if it was already running.");
        }
      }
    }, 5000);
  } catch (_) {
    btn.disabled = false;
    btn.textContent = "Install AnimateDiff (~2 GB)";
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
      alert(data.message || "Install failed");
      btn.disabled = false;
      btn.textContent = "Install NSFW checkpoints";
      return;
    }
    btn.dataset.running = "1";
    btn.textContent = "Downloading (~44 GB)…";
    const poll = setInterval(async () => {
      const st = await fetch("/api/comfyui/install-nsfw/status");
      const info = await st.json();
      if (!info.running) {
        clearInterval(poll);
        btn.dataset.running = "0";
        btn.textContent = "Install NSFW checkpoints";
        btn.disabled = false;
        loadVideoSettings();
      }
    }, 8000);
  } catch (_) {
    btn.disabled = false;
    btn.textContent = "Install NSFW checkpoints";
  }
});

document.getElementById("videoGenHintBtn")?.addEventListener("click", () => {
  if (typeof window.jarvisSendToChat === "function") {
    window.jarvisSendToChat("generate a video of ");
  }
});

async function pollStoryboardJob(jobId, statusEl) {
  if (!jobId) return;
  const tick = async () => {
    try {
      const res = await fetch(`/api/coding/job/${encodeURIComponent(jobId)}`);
      const data = await res.json();
      if (!data.ok) {
        if (statusEl) statusEl.textContent = data.message || "Storyboard job not found";
        return;
      }
      if (statusEl) statusEl.textContent = data.message || "Building storyboard…";
      if (data.done) {
        const result = data.result || {};
        if (result.ok && result.video_path) {
          const url = resolveVideoUrl(result.video_path);
          if (statusEl) {
            statusEl.innerHTML = `Ready: <a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(result.video_path.split(/[/\\]/).pop())}</a>`;
          }
          loadVideoGallery();
        } else if (statusEl) {
          statusEl.textContent = data.error || result.message || "Storyboard failed";
        }
        return;
      }
      setTimeout(tick, 1500);
    } catch (e) {
      if (statusEl) statusEl.textContent = String(e.message || e);
    }
  };
  tick();
}

document.getElementById("storyboardBuildBtn")?.addEventListener("click", async () => {
  const paths = document.getElementById("storyboardPathsInput")?.value?.trim();
  const statusEl = document.getElementById("storyboardStatus");
  const btn = document.getElementById("storyboardBuildBtn");
  if (!paths) {
    if (statusEl) statusEl.textContent = "Enter comma-separated image paths";
    return;
  }
  if (btn) btn.disabled = true;
  if (statusEl) statusEl.textContent = "Queueing storyboard…";
  try {
    const form = new FormData();
    form.append("paths", paths);
    form.append("sec_per_slide", "3.5");
    const res = await fetch("/api/video/storyboard", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      if (statusEl) statusEl.textContent = data.message || "Could not queue storyboard";
      return;
    }
    if (statusEl) statusEl.textContent = data.message || "Storyboard queued…";
    pollStoryboardJob(data.job_id, statusEl);
  } catch (e) {
    if (statusEl) statusEl.textContent = String(e.message || e);
  } finally {
    if (btn) btn.disabled = false;
  }
});

window.loadVideoGallery = loadVideoGallery;
