/** Image/video lightbox + inpaint — extracted from app.js. */
(function () {
  "use strict";

let lightboxImagePath = "";

function openImageLightbox(url, caption = "", imagePath = "", previewUrl = "") {
  window.openImageLightbox = openImageLightbox;
  const modal = document.getElementById("imageLightbox");
  const img = document.getElementById("imageLightboxImg");
  const cap = document.getElementById("imageLightboxCaption");
  const promptEl = document.getElementById("imageLightboxPrompt");
  const statusEl = document.getElementById("imageLightboxStatus");
  if (!modal || !img || !url) return;
  lightboxImagePath = imagePath || "";
  const preview = previewUrl && previewUrl !== url ? previewUrl : "";
  img.src = preview || url;
  img.alt = caption || "Image";
  if (cap) cap.textContent = caption || "";
  if (promptEl) promptEl.value = "";
  if (statusEl) statusEl.textContent = preview ? "Loading full resolution…" : "";
  modal.classList.remove("hidden");
  promptEl?.focus();
  if (preview) {
    const fullImg = new Image();
    fullImg.onload = () => {
      if (!modal.classList.contains("hidden") && lightboxImagePath === (imagePath || "")) {
        img.src = url;
        if (statusEl) statusEl.textContent = "";
      }
    };
    fullImg.onerror = () => {
      if (statusEl) statusEl.textContent = "Could not load full image — showing preview.";
    };
    fullImg.src = url;
  }
}

function closeImageLightbox() {
  document.getElementById("imageLightbox")?.classList.add("hidden");
  lightboxImagePath = "";
}
window.closeImageLightbox = closeImageLightbox;

function openVideoLightbox(url, caption = "") {
  const modal = document.getElementById("videoLightbox");
  const player = document.getElementById("videoLightboxPlayer");
  const cap = document.getElementById("videoLightboxCaption");
  if (!modal || !player || !url) return;
  player.pause();
  player.removeAttribute("src");
  player.load();
  player.src = url;
  if (cap) cap.textContent = caption || "";
  modal.classList.remove("hidden");
  player.play().catch(() => {});
}
window.openVideoLightbox = openVideoLightbox;

function closeVideoLightbox() {
  const player = document.getElementById("videoLightboxPlayer");
  if (player) {
    player.pause();
    player.removeAttribute("src");
    player.load();
  }
  document.getElementById("videoLightbox")?.classList.add("hidden");
}
window.closeVideoLightbox = closeVideoLightbox;

function bindClickableVideos(root) {
  const scope = root || document;
  scope.querySelectorAll(".gen-video video, .video-gallery-item .video-thumb").forEach((video) => {
    if (video.dataset.lightboxBound) return;
    video.dataset.lightboxBound = "1";
    const isThumb = video.classList.contains("video-thumb");
    video.classList.add("clickable-video");
    if (!video.title) video.title = isThumb ? "Click to open player" : "Double-click to open full player";
    const open = (e) => {
      const src = video.currentSrc || video.src;
      if (!src) return;
      e.preventDefault();
      e.stopPropagation();
      const host = video.closest(".gen-video, .video-gallery-item");
      const caption = host?.querySelector("figcaption, .video-item-name")?.textContent?.trim() || "";
      openVideoLightbox(src, caption);
    };
    video.addEventListener(isThumb ? "click" : "dblclick", open);
  });
}
window.bindClickableVideos = bindClickableVideos;

function initVideoLightbox() {
  document.getElementById("videoLightboxClose")?.addEventListener("click", closeVideoLightbox);
  const modal = document.getElementById("videoLightbox");
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) closeVideoLightbox();
  });
}

async function queueImageEdit(imagePath, prompt, regionKey, statusEl, onDone, denoise) {
  if (!imagePath || !prompt) {
    if (statusEl) statusEl.textContent = "Enter what you want to change.";
    return false;
  }
  const regionKeyNorm = regionKey || "full";
  const wholeImage = regionKeyNorm === "full";
  const form = new FormData();
  form.append("path", imagePath);
  form.append("prompt", prompt);
  const endpoint = wholeImage ? "/api/image/edit" : "/api/image/inpaint";
  if (!wholeImage) {
    let d = denoise;
    if (d == null || d === "") {
      const el = document.getElementById("inpaintDenoise");
      d = el?.value;
    }
    const denoiseVal = Number(d);
    form.append(
      "denoise",
      Number.isFinite(denoiseVal) ? String(Math.min(1, Math.max(0.5, denoiseVal))) : "0.82",
    );
    const region = INPAINT_REGIONS[regionKeyNorm];
    if (region) form.append("region", JSON.stringify(region));
  }
  try {
    if (statusEl) statusEl.textContent = wholeImage ? "Queuing img2img edit…" : "Queuing inpaint…";
    const res = await fetch(endpoint, { method: "POST", body: form });
    const out = await res.json().catch(() => ({}));
    if (!res.ok || !out.ok) {
      const detail = out.message || out.detail
        || (res.status === 404 ? "Edit API not loaded — use jarvis-ctl restart, then Reload UI" : null)
        || `Edit failed (${res.status})`;
      if (statusEl) statusEl.textContent = detail;
      window.showAriaToast?.(detail, "err", 5000);
      return false;
    }
    if (out.job_id) {
      const addMessage = window.addMessage;
      const pollMediaJob = window.pollMediaJob;
      const { body } = addMessage("assistant", out.message || (wholeImage ? "Editing image…" : "Inpainting…"), {
        module: "image",
        type: "media_job",
      });
      const msg = body?.closest?.(".message");
      pollMediaJob?.(out.job_id, msg);
      onDone?.();
      return true;
    }
    if (out.image_path) {
      window.showGeneratedImage?.(out.image_path, out.image_name);
      onDone?.();
      return true;
    }
    if (statusEl) statusEl.textContent = "Edit queued but no job id returned.";
    return false;
  } catch (err) {
    const msg = String(err?.message || err);
    if (statusEl) statusEl.textContent = msg;
    window.showAriaToast?.(msg, "err", 5000);
    return false;
  }
}

function initImageLightbox() {
  document.getElementById("imageLightboxClose")?.addEventListener("click", closeImageLightbox);
  const modal = document.getElementById("imageLightbox");
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) closeImageLightbox();
  });
  document.getElementById("imageLightboxEditBtn")?.addEventListener("click", async () => {
    const prompt = document.getElementById("imageLightboxPrompt")?.value?.trim();
    const regionKey = document.getElementById("imageLightboxRegion")?.value || "full";
    const statusEl = document.getElementById("imageLightboxStatus");
    const btn = document.getElementById("imageLightboxEditBtn");
    if (!lightboxImagePath) {
      if (statusEl) statusEl.textContent = "Image path missing — try Gallery or regenerate.";
      return;
    }
    if (btn) btn.disabled = true;
    if (statusEl) statusEl.textContent = "Queuing edit…";
    const denoise = document.getElementById("imageLightboxDenoise")?.value;
    const ok = await queueImageEdit(lightboxImagePath, prompt, regionKey, statusEl, () => {
      closeImageLightbox();
      const st = document.getElementById("statusText");
      if (st) st.textContent = "Image edit running…";
      window.showAriaToast?.("Image edit queued", "ok", 2500);
    }, denoise);
    if (!ok && statusEl && !statusEl.textContent) statusEl.textContent = "Edit failed";
    if (btn) btn.disabled = false;
  });
  document.getElementById("imageLightboxPrompt")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      document.getElementById("imageLightboxEditBtn")?.click();
    }
  });
}


const INPAINT_REGIONS = {
  full: null,
  center: { x: 0.25, y: 0.25, w: 0.5, h: 0.5 },
  "top left": { x: 0, y: 0, w: 0.5, h: 0.5 },
  "top right": { x: 0.5, y: 0, w: 0.5, h: 0.5 },
  "bottom left": { x: 0, y: 0.5, w: 0.5, h: 0.5 },
  "bottom right": { x: 0.5, y: 0.5, w: 0.5, h: 0.5 },
};

let inpaintTargetPath = "";

function openInpaintModal(imagePath) {
  inpaintTargetPath = imagePath || "";
  const modal = document.getElementById("inpaintModal");
  const promptEl = document.getElementById("inpaintPrompt");
  const statusEl = document.getElementById("inpaintStatus");
  if (!modal || !inpaintTargetPath) return;
  if (promptEl) promptEl.value = "";
  if (statusEl) statusEl.textContent = "";
  modal.classList.remove("hidden");
  promptEl?.focus();
}

function closeInpaintModal() {
  document.getElementById("inpaintModal")?.classList.add("hidden");
  inpaintTargetPath = "";
}

document.getElementById("inpaintCancelBtn")?.addEventListener("click", closeInpaintModal);
document.getElementById("inpaintModal")?.addEventListener("click", (e) => {
  if (e.target?.id === "inpaintModal") closeInpaintModal();
});
document.getElementById("inpaintRunBtn")?.addEventListener("click", async () => {
  const prompt = document.getElementById("inpaintPrompt")?.value?.trim();
  const regionKey = document.getElementById("inpaintRegion")?.value || "full";
  const denoise = document.getElementById("inpaintDenoise")?.value;
  const statusEl = document.getElementById("inpaintStatus");
  const runBtn = document.getElementById("inpaintRunBtn");
  if (!inpaintTargetPath || !prompt) {
    if (statusEl) statusEl.textContent = "Enter a prompt.";
    return;
  }
  if (runBtn) runBtn.disabled = true;
  if (statusEl) statusEl.textContent = "Queuing edit…";
  const ok = await queueImageEdit(inpaintTargetPath, prompt, regionKey, statusEl, () => {
    closeInpaintModal();
    const st = document.getElementById("statusText");
    if (st) st.textContent = "Image edit running…";
    window.showAriaToast?.("Inpaint queued", "ok", 2500);
  }, denoise);
  if (!ok && statusEl && !statusEl.textContent) statusEl.textContent = "Inpaint failed";
  if (runBtn) runBtn.disabled = false;
});


  window.openImageLightbox = openImageLightbox;
  window.closeImageLightbox = closeImageLightbox;
  window.openVideoLightbox = openVideoLightbox;
  window.closeVideoLightbox = closeVideoLightbox;
  window.bindClickableVideos = bindClickableVideos;
  window.queueImageEdit = queueImageEdit;
  window.openInpaintModal = openInpaintModal;
  window.closeInpaintModal = closeInpaintModal;

  initImageLightbox();
  initVideoLightbox();
})();
