/** Chat image URL/figure helpers — extracted from app.js. */
(function () {
function resolveImageUrl(imgPath, { thumb = false, thumbMax = (window.CHAT_IMAGE_THUMB_MAX||320) } = {}) {
  if (!imgPath) return "";
  const file = imgPath.split(/[/\\]/).pop();
  let url;
  if (/\/uploads[/\\]/i.test(imgPath)) {
    url = `/api/uploads/${encodeURIComponent(file)}`;
  } else if (/\/generated[/\\]memes[/\\]/i.test(imgPath)) {
    url = `/api/meme-gallery/${encodeURIComponent(file)}`;
  } else if (/\/generated[/\\]/i.test(imgPath)) {
    const base = `/api/gallery/${encodeURIComponent(file)}`;
    url = thumb ? `${base}?max=${thumbMax}` : base;
  } else {
    url = `/api/audio/file?path=${encodeURIComponent(imgPath)}`;
  }
  return window.apiAuthUrl(url);
}

function galleryViewVisible() {
  const el = document.getElementById("galleryView");
  return el && !el.classList.contains("hidden");
}
window.galleryViewVisible = galleryViewVisible;
window.resolveImageUrl = resolveImageUrl;

async function appendImageFigure(container, imgPath, imageName, caption, { thumb = true } = {}) {
  if (!container || !imgPath || !/\.(png|jpe?g|webp|gif|bmp)$/i.test(imgPath)) return;
  const file = imageName || imgPath.split(/[/\\]/).pop();
  const url = resolveImageUrl(imgPath, { thumb });
  const fullUrl = resolveImageUrl(imgPath, { thumb: false });
  const label = caption || file;
  const pathAttr = window.escapeHtml(imgPath);
  const fig = document.createElement("figure");
  fig.className = "gen-image";
  fig.dataset.imagePath = imgPath;
  const img = document.createElement("img");
  img.alt = file;
  img.loading = "lazy";
  img.decoding = "async";
  img.className = "clickable-image";
  img.dataset.imagePath = imgPath;
  img.title = "Click to view and edit";
  img.dataset.fullSrc = fullUrl;
  const cap = document.createElement("figcaption");
  cap.textContent = label;
  fig.appendChild(img);
  fig.appendChild(cap);
  container.appendChild(fig);
  window.attachMediaLoadError(img, "image");
  if (!window.mediaNeedsApiKey() || window.isNativeApp()) {
    img.src = url;
    bindClickableImages(container);
    return;
  }
  const key = window.getStoredApiKey();
  if (key) {
    try {
      const res = await fetch(fullUrl);
      if (res.ok) {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        img.dataset.fullSrc = blobUrl;
        if (thumb && url !== fullUrl) {
          const thumbRes = await fetch(url);
          img.src = thumbRes.ok ? URL.createObjectURL(await thumbRes.blob()) : blobUrl;
        } else {
          img.src = blobUrl;
        }
      } else {
        img.src = url;
      }
    } catch {
      img.src = url;
    }
  } else {
    img.src = url;
  }
  bindClickableImages(container);
}

function appendImageReveal(container, imgPath, imageName, caption) {
  if (!container || !imgPath) return;
  const file = imageName || imgPath.split(/[/\\]/).pop();
  const label = caption || file;
  const fig = document.createElement("figure");
  fig.className = "gen-image gen-image-reveal";
  fig.dataset.imagePath = imgPath;
  fig.innerHTML =
    `<button type="button" class="gen-image-reveal-btn">Show image · ${window.escapeHtml(file)}</button>`
    + `<figcaption>${window.escapeHtml(label)}</figcaption>`;
  fig.querySelector(".gen-image-reveal-btn")?.addEventListener("click", () => {
    const cap = fig.querySelector("figcaption")?.textContent || file;
    fig.remove();
    appendImageFigure(container, imgPath, file, cap);
  });
  container.appendChild(fig);
}

function bindClickableImages(container) {
  window.bindClickableImages = bindClickableImages;
  if (!container) return;
  container.querySelectorAll(".gen-image img, .gallery-item > img").forEach((img) => {
    if (img.dataset.lightboxBound) return;
    img.dataset.lightboxBound = "1";
    img.classList.add("clickable-image");
    if (!img.title) img.title = "Click to view and edit";
    img.addEventListener("click", (e) => {
      e.stopPropagation();
      const figure = img.closest(".gen-image");
      const path = img.dataset.imagePath || figure?.dataset.imagePath || "";
      const full = img.dataset.fullSrc || img.src;
      window.openImageLightbox?.(full, img.alt || "", path, img.src);
    });
  });
}

// media lightbox / queueImageEdit / inpaint → media_lightbox.js

function appendGeneratedImage(container, imgPath, imageName) {
  const cap = imageName || imgPath.split(/[/\\]/).pop();
  if (window.isNativeApp()) appendImageReveal(container, imgPath, imageName, cap);
  else appendImageFigure(container, imgPath, imageName, cap);
}

function buildVisionMessageHtml(text) {
  const format = window.formatMessage || ((t) => t);
  return format((text || "").trim() || "Image analysis complete.");
}

function buildImageMessageHtml(data, text) {
  let intro = (text || data.message || "").trim();
  const prompt = (data.enhanced_prompt || "").trim();
  let negative = "";
  const format = window.formatMessage || ((t) => t);
  const esc = window.escapeHtml || ((t) => t);

  const negMatch = intro.match(/\n\n\*\*Avoiding:\*\*\s*([\s\S]*)$/);
  if (negMatch) {
    negative = negMatch[1].trim();
    intro = intro.slice(0, negMatch.index).trim();
  }
  intro = intro.replace(/\n\n\*\*Prompt sent to[^*]+:\*\*\n[\s\S]*$/, "").trim();
  if (!intro) intro = "Here's your image.";

  let html = format(intro);
  if (prompt) {
    html += `<details class="prompt-details" open><summary>Prompt sent to model</summary><pre class="prompt-text">${esc(prompt)}</pre></details>`;
  }
  if (negative) {
    html += `<details class="prompt-details"><summary>Negative prompt</summary><pre class="prompt-text">${esc(negative)}</pre></details>`;
  }
  return html;
}

function buildDataTableHtml(preview) {
  if (!preview?.columns?.length) return "";
  const esc = window.escapeHtml || ((t) => String(t));
  const cols = preview.columns;
  const rows = preview.rows || [];
  const streamNote = preview.streaming ? " · streaming (preview)" : preview.truncated ? " · truncated" : "";
  let html = `<div class="data-preview"><p class="data-preview-meta">📊 ${esc(preview.name || "dataset")} · ${preview.row_count ?? "?"} rows${streamNote}</p><div class="data-table-wrap"><table class="data-table"><thead><tr>`;
  cols.forEach((c) => { html += `<th>${esc(String(c))}</th>`; });
  html += "</tr></thead><tbody>";
  rows.forEach((r) => {
    html += "<tr>";
    cols.forEach((c) => { html += `<td>${esc(String(r[c] ?? ""))}</td>`; });
    html += "</tr>";
  });
  html += "</tbody></table></div></div>";
  return html;
}


  Object.assign(window, {
    resolveImageUrl,
    galleryViewVisible,
    appendImageFigure,
    appendImageReveal,
    bindClickableImages,
    appendGeneratedImage,
    buildVisionMessageHtml,
    buildImageMessageHtml,
    buildDataTableHtml,
  });
})();
