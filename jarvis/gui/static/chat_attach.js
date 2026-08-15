/** Chat attachment state bridge + finishSendUi — extracted from app.js. */
(function () {
  let pendingFile = null;
  let pendingFile2 = null;
  let compareMode = false;
  let pendingCrop = null;
  let pendingVideoSecond = "";
  let pendingPdfPage = "1";
  let visionChips = [];
  let dataChips = [];

  function isVisionAttachment(file) {
    return Boolean(file && (/^image\//i.test(file.type) || /^video\//i.test(file.type)));
  }

  function isDataAttachment(file) {
    return Boolean(
      file && (/\.(csv|json|xlsx|xlsm|db|sqlite|sqlite3)$/i.test(file.name)
        || file.type === "text/csv" || file.type === "application/json"),
    );
  }

  function isImageRequest(text) {
    const t = String(text || "").trim();
    return (
      /\b(create|generate|make|draw)\b[\s\S]*\b(image|picture|photo|illustration)\b/i.test(t)
      || /\b(image|picture|photo)\b[\s\S]*\b(of|showing)\b/i.test(t)
    );
  }

  function isVideoRequest(text) {
    const t = String(text || "").trim();
    return /\b(create|generate|make)\b[\s\S]*\b(video|clip|animation|movie)\b/i.test(t);
  }

  function finishSendUi() {
    window.hideProgress?.();
    window.setChatBusy?.(false);
    pendingFile = null;
    pendingFile2 = null;
    pendingCrop = null;
    pendingVideoSecond = "";
    pendingPdfPage = "1";
    compareMode = false;
    const attachmentPreview = document.getElementById("attachmentPreview");
    const fileInput = document.getElementById("fileInput");
    if (attachmentPreview) attachmentPreview.classList.add("hidden");
    if (fileInput) fileInput.value = "";
    fileInput?.removeAttribute("multiple");
    const fileInput2 = document.getElementById("fileInput2");
    if (fileInput2) fileInput2.value = "";
    window.updateCompareButton?.();
    try { window.loadBranches?.(); } catch (_) { /* ignore */ }
  }

  window.isVisionAttachment = isVisionAttachment;
  window.isDataAttachment = isDataAttachment;
  window.isImageRequest = isImageRequest;
  window.isVideoRequest = isVideoRequest;
  window.finishSendUi = finishSendUi;

  window.jarvisAttach = {
    get pendingFile() { return pendingFile; },
    set pendingFile(v) { pendingFile = v; },
    get pendingFile2() { return pendingFile2; },
    set pendingFile2(v) { pendingFile2 = v; },
    get compareMode() { return compareMode; },
    set compareMode(v) { compareMode = v; },
    get pendingCrop() { return pendingCrop; },
    set pendingCrop(v) { pendingCrop = v; },
    get pendingVideoSecond() { return pendingVideoSecond; },
    set pendingVideoSecond(v) { pendingVideoSecond = v; },
    get pendingPdfPage() { return pendingPdfPage; },
    set pendingPdfPage(v) { pendingPdfPage = v; },
    get visionChips() { return visionChips; },
    set visionChips(v) { visionChips = Array.isArray(v) ? v : []; },
    get dataChips() { return dataChips; },
    set dataChips(v) { dataChips = Array.isArray(v) ? v : []; },
    isVisionAttachment,
    isDataAttachment,
    isTextEntryElement: (...args) => window.isTextEntryElement?.(...args),
    escapeHtml: (...args) => window.escapeHtml?.(...args),
  };
})();
