/** Attachment preview, compare mode, and vision/data chips — extracted from app.js. */
(function () {
  function a() {
    return window.jarvisAttach || {};
  }

  function escapeHtml(text) {
    if (typeof a().escapeHtml === "function") return a().escapeHtml(text);
    const d = document.createElement("div");
    d.textContent = text == null ? "" : String(text);
    return d.innerHTML;
  }

  function updateCompareButton() {
    const btn = document.getElementById("compareModeBtn");
    if (!btn) return;
    const pendingFile = a().pendingFile;
    const pendingFile2 = a().pendingFile2;
    const compareMode = a().compareMode;
    const count = (pendingFile ? 1 : 0) + (pendingFile2 ? 1 : 0);
    btn.classList.toggle("active", compareMode || Boolean(pendingFile2));
    if (pendingFile2) {
      btn.title = "Two images ready — send to compare";
    } else if (compareMode) {
      btn.title = count ? "Compare mode: add a second image" : "Compare mode: pick two images";
    } else {
      btn.title = "Compare two images (select both in one dialog)";
    }
  }

  function enterCompareMode() {
    a().compareMode = true;
    updateCompareButton();
    const fi = document.getElementById("fileInput");
    if (!fi) return;
    if (!a().pendingFile) {
      fi.setAttribute("multiple", "");
      fi.click();
    } else if (!a().pendingFile2) {
      document.getElementById("fileInput2")?.click();
    }
  }

  function exitCompareMode() {
    a().compareMode = false;
    a().pendingFile2 = null;
    document.getElementById("fileInput")?.removeAttribute("multiple");
    updateCompareButton();
    updateAttachmentPreview();
  }

  function updateAttachmentPreview() {
    const attachmentPreview = document.getElementById("attachmentPreview");
    if (!attachmentPreview) return;
    const pendingFile = a().pendingFile;
    const pendingFile2 = a().pendingFile2;
    const compareMode = a().compareMode;
    if (!pendingFile && !pendingFile2) {
      attachmentPreview.classList.add("hidden");
      updateCompareButton();
      return;
    }
    attachmentPreview.classList.remove("hidden");
    const isVision =
      typeof a().isVisionAttachment === "function"
        ? a().isVisionAttachment
        : (f) => Boolean(f && (/^image\//i.test(f.type) || /^video\//i.test(f.type)));
    const isData =
      typeof a().isDataAttachment === "function"
        ? a().isDataAttachment
        : () => false;
    const parts = [];
    [pendingFile, pendingFile2].filter(Boolean).forEach((f, i) => {
      let preview = "";
      if (isVision(f)) {
        preview = `<img src="${URL.createObjectURL(f)}" alt="" class="attach-thumb" /> `;
      }
      const label = pendingFile2 ? `Image ${i + 1}: ` : "";
      parts.push(`${preview}${label}📎 ${escapeHtml(f.name)}`);
    });
    const dataBadge = pendingFile && isData(pendingFile) && !pendingFile2
      ? `<span class="compare-badge data-badge">Data file</span>`
      : "";
    const compareBadge = pendingFile2
      ? `<span class="compare-badge">Compare · 2 images</span>`
      : compareMode
        ? `<span class="compare-badge warn">Compare · 1/2 — add second image</span>`
        : "";
    const addSecond = compareMode && pendingFile && !pendingFile2
      ? `<button type="button" id="addSecondImgBtn" class="ghost-btn small">+ Add image 2</button>`
      : "";
    const cancelCompare = compareMode || pendingFile2
      ? `<button type="button" id="cancelCompareBtn" class="ghost-btn small">Cancel compare</button>`
      : "";
    const isVideo = pendingFile && /^video\//i.test(pendingFile.type);
    const isPdf = pendingFile && (pendingFile.type === "application/pdf" || /\.pdf$/i.test(pendingFile.name));
    const isDoc = pendingFile && (/\.docx$/i.test(pendingFile.name)
      || pendingFile.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
    const docBadge = (isPdf || isDoc) && !pendingFile2
      ? `<span class="compare-badge data-badge">Document · try “Summarize this warranty PDF”</span>`
      : "";
    const videoOpts = isVideo
      ? `<label class="attach-opt">Frame at <input type="text" id="videoSecondInput" placeholder="0:45 or 12s" value="${escapeHtml(a().pendingVideoSecond || "")}" class="attach-mini-input" /></label>`
      : "";
    const pdfOpts = isPdf
      ? `<label class="attach-opt">Page <input type="number" id="pdfPageInput" min="1" value="${escapeHtml(a().pendingPdfPage || "1")}" class="attach-mini-input" title="For OCR/vision only" /></label>`
      : "";
    const cropBtn = pendingFile && isVision(pendingFile) && !pendingFile2
      ? `<button type="button" id="cropAttachBtn" class="ghost-btn small">Crop</button>`
      : "";
    attachmentPreview.innerHTML = `${dataBadge} ${docBadge} ${compareBadge} ${parts.join(" · ")} ${videoOpts} ${pdfOpts} ${addSecond} ${cropBtn} ${cancelCompare} <button type="button" aria-label="Remove">×</button>`;
    document.getElementById("videoSecondInput")?.addEventListener("change", (e) => {
      a().pendingVideoSecond = e.target.value;
    });
    document.getElementById("pdfPageInput")?.addEventListener("change", (e) => {
      a().pendingPdfPage = e.target.value || "1";
    });
    attachmentPreview.querySelector("button[aria-label='Remove']")?.addEventListener("click", () => {
      a().pendingFile = null;
      a().pendingFile2 = null;
      a().pendingCrop = null;
      a().compareMode = false;
      const fileInput = document.getElementById("fileInput");
      if (fileInput) fileInput.value = "";
      const fi2 = document.getElementById("fileInput2");
      if (fi2) fi2.value = "";
      fileInput?.removeAttribute("multiple");
      attachmentPreview.classList.add("hidden");
      updateCompareButton();
    });
    document.getElementById("addSecondImgBtn")?.addEventListener("click", () => {
      a().compareMode = true;
      document.getElementById("fileInput2")?.click();
    });
    document.getElementById("cancelCompareBtn")?.addEventListener("click", () => {
      exitCompareMode();
    });
    document.getElementById("cropAttachBtn")?.addEventListener("click", () => {
      window.openCropModal?.();
    });
    updateCompareButton();
  }

  function assignAttachment(file, asSecond = false) {
    if (!file) return;
    const bridge = a();
    if (asSecond || (bridge.compareMode && bridge.pendingFile)) {
      if (!bridge.pendingFile) bridge.pendingFile = file;
      else bridge.pendingFile2 = file;
    } else if (bridge.compareMode) {
      bridge.pendingFile = file;
    } else {
      bridge.pendingFile = file;
      bridge.pendingFile2 = null;
    }
    updateAttachmentPreview();
    const isData = typeof bridge.isDataAttachment === "function" ? bridge.isDataAttachment : () => false;
    if (isData(bridge.pendingFile)) refreshDataChips();
    else refreshVisionChips();
  }

  function assignMultipleAttachments(files) {
    const bridge = a();
    const isVision =
      typeof bridge.isVisionAttachment === "function"
        ? bridge.isVisionAttachment
        : (f) => Boolean(f && (/^image\//i.test(f.type) || /^video\//i.test(f.type)));
    const imgs = files.filter((f) => isVision(f) || /^image\//i.test(f.type));
    if (!imgs.length) return;
    bridge.compareMode = true;
    bridge.pendingFile = imgs[0];
    bridge.pendingFile2 = imgs.length >= 2 ? imgs[1] : null;
    updateAttachmentPreview();
    const isData = typeof bridge.isDataAttachment === "function" ? bridge.isDataAttachment : () => false;
    if (isData(bridge.pendingFile)) refreshDataChips();
    else refreshVisionChips();
    if (bridge.compareMode && bridge.pendingFile && !bridge.pendingFile2) {
      setTimeout(() => document.getElementById("fileInput2")?.click(), 250);
    }
  }

  function refreshDataChips() {
    const suggestionsEl = document.getElementById("suggestions");
    const dataChips = a().dataChips || [];
    if (!suggestionsEl || !dataChips.length) return;
    const isData = typeof a().isDataAttachment === "function" ? a().isDataAttachment : () => false;
    if (!isData(a().pendingFile)) return;
    const messageInput = document.getElementById("messageInput");
    suggestionsEl.innerHTML = "";
    dataChips.forEach((s) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip data-chip";
      chip.textContent = s;
      chip.onclick = () => { if (messageInput) { messageInput.value = s; messageInput.focus(); } };
      suggestionsEl.appendChild(chip);
    });
  }

  function refreshVisionChips() {
    const suggestionsEl = document.getElementById("suggestions");
    const visionChips = a().visionChips || [];
    if (!suggestionsEl || !visionChips.length) return;
    if (!a().pendingFile && !a().pendingFile2) return;
    const messageInput = document.getElementById("messageInput");
    suggestionsEl.innerHTML = "";
    const chips = a().pendingFile2
      ? ["Compare these two images. Describe similarities and differences."]
      : visionChips;
    chips.forEach((s) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip vision-chip";
      chip.textContent = s;
      chip.onclick = () => { if (messageInput) { messageInput.value = s; messageInput.focus(); } };
      suggestionsEl.appendChild(chip);
    });
  }

  function bindAttachmentInputs() {
    const fileInput = document.getElementById("fileInput");
    fileInput?.addEventListener("change", () => {
      const files = fileInput.files ? Array.from(fileInput.files) : [];
      fileInput?.removeAttribute("multiple");
      if (!files.length) return;
      if (files.length >= 2) {
        assignMultipleAttachments(files);
        fileInput.value = "";
        return;
      }
      assignAttachment(files[0], Boolean(a().compareMode && a().pendingFile));
      fileInput.value = "";
    });

    document.getElementById("fileInput2")?.addEventListener("change", (e) => {
      const f = e.target.files[0];
      if (f) {
        a().compareMode = true;
        assignAttachment(f, true);
      }
      e.target.value = "";
    });

    document.getElementById("compareModeBtn")?.addEventListener("click", () => {
      if (a().pendingFile && a().pendingFile2) {
        const messageInput = document.getElementById("messageInput");
        if (messageInput) {
          messageInput.value = "Compare these two images. Describe similarities and differences.";
          messageInput.focus();
        }
        return;
      }
      enterCompareMode();
    });
  }

  Object.assign(window, {
    updateCompareButton,
    enterCompareMode,
    exitCompareMode,
    updateAttachmentPreview,
    assignAttachment,
    assignMultipleAttachments,
    refreshDataChips,
    refreshVisionChips,
  });

  const bridge = a();
  if (bridge && typeof bridge === "object") {
    Object.assign(bridge, {
      updateAttachmentPreview,
      assignAttachment,
      assignMultipleAttachments,
      refreshDataChips,
      refreshVisionChips,
      updateCompareButton,
      enterCompareMode,
      exitCompareMode,
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindAttachmentInputs, { once: true });
  } else {
    bindAttachmentInputs();
  }
})();
