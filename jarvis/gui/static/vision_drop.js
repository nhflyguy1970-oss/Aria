/** Chat drag/drop + paste for vision attachments — extracted from app.js. */
(function () {
  function attach() {
    return window.jarvisAttach || {};
  }

  function initVisionDropPaste() {
    const a = attach();
    const chatView = document.getElementById("chatView");
    const overlay = document.getElementById("dropOverlay");
    if (!chatView) return;

    chatView.addEventListener("dragover", (e) => {
      if (![...e.dataTransfer.types].includes("Files")) return;
      e.preventDefault();
      overlay?.classList.remove("hidden");
    });
    chatView.addEventListener("dragleave", (e) => {
      if (e.target === chatView) overlay?.classList.add("hidden");
    });
    chatView.addEventListener("drop", (e) => {
      e.preventDefault();
      overlay?.classList.add("hidden");
      const isVision =
        typeof a.isVisionAttachment === "function"
          ? a.isVisionAttachment
          : (f) => Boolean(f && (/^image\//i.test(f.type) || /^video\//i.test(f.type)));
      const imgs = [...e.dataTransfer.files].filter(
        (f) => isVision(f) || /^image\//i.test(f.type),
      );
      if (imgs.length >= 2) {
        a.assignMultipleAttachments?.(imgs);
      } else if (imgs.length === 1) {
        a.assignAttachment?.(imgs[0], Boolean(a.compareMode && a.pendingFile));
      }
    });

    document.addEventListener("paste", (e) => {
      if (typeof a.isTextEntryElement === "function" && a.isTextEntryElement(e.target)) return;
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const blob = item.getAsFile();
          if (blob) {
            e.preventDefault();
            a.assignAttachment?.(
              new File([blob], `paste-${Date.now()}.png`, { type: blob.type }),
            );
            break;
          }
        }
      }
    });
  }

  window.initVisionDropPaste = initVisionDropPaste;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initVisionDropPaste, { once: true });
  } else {
    initVisionDropPaste();
  }
})();
