/** Gallery grid + prompt history — extracted from app.js. */
(function () {
  "use strict";

  function statusLine() {
    return document.getElementById("statusText");
  }

  async function loadGallery() {
    const el = document.getElementById("galleryGrid");
    if (!el) return;
    const GALLERY_THUMB_MAX = window.GALLERY_THUMB_MAX || 384;
    const apiAuthUrl = window.apiAuthUrl || ((u) => u);
    const escapeHtml = window.escapeHtml || ((t) => String(t ?? ""));
    const resolveImageUrl = window.resolveImageUrl;
    const openImageLightbox = window.openImageLightbox;
    const bindClickableImages = window.bindClickableImages;
    if (document.getElementById("imageEngineUncensoredBanner")) {
      await window.loadComfyMode?.();
    }
    try {
      const res = await fetch("/api/gallery");
      if (!res.ok) throw new Error(`Gallery unavailable (${res.status})`);
      const data = await res.json();
      el.innerHTML = (data.images || []).map((img) => {
        const thumb = apiAuthUrl(`/api/gallery/${encodeURIComponent(img.name)}?max=${GALLERY_THUMB_MAX}`);
        const full = apiAuthUrl(`/api/gallery/${encodeURIComponent(img.name)}`);
        return `<div class="gallery-item">
      <button type="button" class="gallery-del" data-name="${escapeHtml(img.name)}" title="Delete" aria-label="Delete ${escapeHtml(img.name)}">×</button>
      <button type="button" class="gallery-upscale" data-path="${escapeHtml(img.path)}" title="Upscale 2×" aria-label="Upscale ${escapeHtml(img.name)} 2×">2×</button>
      <button type="button" class="gallery-inpaint" data-path="${escapeHtml(img.path)}" title="Edit image" aria-label="Edit ${escapeHtml(img.name)}">✎</button>
      <img src="${thumb}" data-full-src="${escapeHtml(full)}" alt="${escapeHtml(img.name)}" loading="lazy" decoding="async" data-image-path="${escapeHtml(img.path)}" title="Click to view and edit" />
    </div>`;
      }).join("") || "<p class=\"muted\">No generated images yet. Use the prompt above, or ask in chat: <code>generate image: …</code></p>";
      el.querySelectorAll(".gallery-inpaint").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const path = btn.dataset.path;
          if (!path || !openImageLightbox || !resolveImageUrl) return;
          const file = path.split(/[/\\]/).pop();
          openImageLightbox(
            resolveImageUrl(path, { thumb: false }),
            file,
            path,
            resolveImageUrl(path, { thumb: true, thumbMax: GALLERY_THUMB_MAX }),
          );
        });
      });
      el.querySelectorAll(".gallery-upscale").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.stopPropagation();
          const path = btn.dataset.path;
          if (!path) return;
          btn.disabled = true;
          const form = new FormData();
          form.append("path", path);
          form.append("scale", "2");
          const res2 = await fetch("/api/image/upscale", { method: "POST", body: form });
          const out = await res2.json().catch(() => ({}));
          btn.disabled = false;
          const st = statusLine();
          if (!res2.ok || !out.ok) {
            const msg = out.message || "Upscale failed";
            if (st) st.textContent = msg;
            window.showAriaToast?.(msg, "err", 5000);
            return;
          }
          const okMsg = `Upscaled → ${out.image_path?.split("/").pop() || "done"}`;
          if (st) st.textContent = okMsg;
          window.showAriaToast?.(okMsg, "ok", 3000);
          loadGallery();
        });
      });
      el.querySelectorAll(".gallery-del").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.stopPropagation();
          const name = btn.dataset.name;
          if (!name || !confirm(`Delete ${name}?`)) return;
          const delRes = await fetch(`/api/gallery/${encodeURIComponent(name)}`, { method: "DELETE" });
          const delData = await delRes.json().catch(() => ({}));
          const st = statusLine();
          if (!delRes.ok || !delData.ok) {
            const msg = delData.message || "Delete failed";
            if (st) st.textContent = msg;
            window.showAriaToast?.(msg, "err", 5000);
            return;
          }
          window.showAriaToast?.(`Deleted ${name}`, "ok", 2500);
          loadGallery();
        });
      });
      bindClickableImages?.(el);
      loadPromptHistory();
    } catch (err) {
      el.innerHTML = `<p class="warn">Could not load gallery — ${escapeHtml(String(err.message || err))}</p>`;
      window.showAriaToast?.(err.message || "Gallery load failed", "err", 5000);
    }
  }

  async function loadPromptHistory() {
    const el = document.getElementById("promptHistoryList");
    if (!el) return;
    const escapeHtml = window.escapeHtml || ((t) => String(t ?? ""));
    try {
      const res = await fetch("/api/prompts?limit=30");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || `Prompt history failed (${res.status})`);
      const items = data.prompts || [];
      el.innerHTML = items.length
        ? items.map((p) => `<div class="prompt-history-item">
          <button type="button" class="ghost-btn small prompt-reuse" data-prompt="${escapeHtml(p.prompt)}">Reuse</button>
          <button type="button" class="ghost-btn small prompt-fav" data-id="${escapeHtml(p.id)}">${p.favorite ? "★" : "☆"}</button>
          <button type="button" class="ghost-btn small prompt-del" data-id="${escapeHtml(p.id)}" title="Delete" aria-label="Delete saved prompt">×</button>
          <span class="prompt-text">${escapeHtml(p.prompt.slice(0, 120))}${p.prompt.length > 120 ? "…" : ""}</span>
        </div>`).join("")
        : "<p>No saved prompts yet — generate an image to build history.</p>";
      el.querySelectorAll(".prompt-reuse").forEach((btn) => {
        btn.addEventListener("click", () => {
          const messageInput = document.getElementById("messageInput");
          if (messageInput) messageInput.value = btn.dataset.prompt;
          document.querySelector('.view-tab[data-view="chat"]')?.click();
          messageInput?.focus();
        });
      });
      el.querySelectorAll(".prompt-fav").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            const res2 = await fetch(`/api/prompts/${encodeURIComponent(btn.dataset.id)}/favorite`, { method: "POST" });
            if (!res2.ok) throw new Error(`Favorite failed (${res2.status})`);
            loadPromptHistory();
          } catch (err) {
            window.showAriaToast?.(err.message || "Favorite failed", "err", 4000);
          }
        });
      });
      el.querySelectorAll(".prompt-del").forEach((btn) => {
        btn.addEventListener("click", async () => {
          if (!confirm("Delete this prompt from history?")) return;
          try {
            const delRes = await fetch(`/api/prompts/${encodeURIComponent(btn.dataset.id)}`, { method: "DELETE" });
            const delData = await delRes.json().catch(() => ({}));
            if (!delRes.ok || !delData.ok) throw new Error(delData.message || "Delete failed");
            loadPromptHistory();
          } catch (err) {
            window.showAriaToast?.(err.message || "Delete failed", "err", 4000);
          }
        });
      });
    } catch (err) {
      el.textContent = "Could not load prompt history.";
      window.showAriaToast?.(err.message || "Prompt history unavailable", "err", 4000);
    }
  }

  function initGalleryView() {
    const root = document.getElementById("galleryView");
    if (root?.dataset.galleryBound === "1") return;
    if (root) root.dataset.galleryBound = "1";
    document.getElementById("galleryGenerateBtn")?.addEventListener("click", () => {
      const prompt = document.getElementById("galleryPromptInput")?.value?.trim();
      if (!prompt) {
        window.showAriaToast?.("Enter an image description first", "warn");
        document.getElementById("galleryPromptInput")?.focus();
        return;
      }
      window.switchToView?.("chat");
      window.sendMessage?.(`generate image: ${prompt}`);
    });
    document.getElementById("galleryPromptInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        document.getElementById("galleryGenerateBtn")?.click();
      }
    });
  }

  window.loadGallery = loadGallery;
  window.loadPromptHistory = loadPromptHistory;
  window.initGalleryView = initGalleryView;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGalleryView);
  } else {
    initGalleryView();
  }
})();
