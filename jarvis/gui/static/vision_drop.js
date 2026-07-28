/** Chat drag/drop + paste for multimodal attachments (vision, docs, audio, data). */
(function () {
  function attach() {
    return window.jarvisAttach || {};
  }

  function isAttachable(file) {
    if (!file) return false;
    const a = attach();
    if (a.isVisionAttachment?.(file)) return true;
    if (a.isDataAttachment?.(file)) return true;
    if (/^audio\//i.test(file.type)) return true;
    if (/^image\//i.test(file.type) || /^video\//i.test(file.type)) return true;
    if (/\.(pdf|docx|txt|md|csv|json|xlsx|xlsm|db|sqlite|sqlite3|py|js|ts|html|yml|yaml)$/i.test(file.name)) {
      return true;
    }
    return Boolean(file.type);
  }

  function initVisionDropPaste() {
    const a = attach();
    const chatView = document.getElementById("chatView");
    const overlay = document.getElementById("dropOverlay");
    if (!chatView) return;

    chatView.addEventListener("dragover", (e) => {
      if (![...e.dataTransfer.types].includes("Files")) return;
      e.preventDefault();
      if (overlay) {
        overlay.textContent = "Drop to attach (image, document, audio, or data)";
        overlay.classList.remove("hidden");
      }
    });
    chatView.addEventListener("dragleave", (e) => {
      if (e.target === chatView) overlay?.classList.add("hidden");
    });
    chatView.addEventListener("drop", (e) => {
      e.preventDefault();
      overlay?.classList.add("hidden");
      const files = [...(e.dataTransfer.files || [])].filter(isAttachable);
      if (!files.length) {
        window.showAriaToast?.("Nothing attachable in that drop", "warn");
        return;
      }
      const isVision =
        typeof a.isVisionAttachment === "function"
          ? a.isVisionAttachment
          : (f) => Boolean(f && (/^image\//i.test(f.type) || /^video\//i.test(f.type)));
      const imgs = files.filter((f) => isVision(f));
      if (imgs.length >= 2) {
        a.assignMultipleAttachments?.(imgs);
      } else if (files.length >= 1) {
        a.assignAttachment?.(files[0], Boolean(a.compareMode && a.pendingFile));
        if (files.length > 1) {
          window.showAriaToast?.(`Attached ${files[0].name} (${files.length - 1} more ignored — attach one at a time or use Compare for two images)`, "info", 4000);
        }
      }
    });

    document.addEventListener("paste", (e) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      // Allow paste into the chat composer (and other Aria text fields that expect attachments)
      const target = e.target;
      const inComposer = target && (target.id === "messageInput" || target.closest?.("#chatForm"));
      const blockTextPaste = typeof a.isTextEntryElement === "function"
        && a.isTextEntryElement(target)
        && !inComposer;
      if (blockTextPaste) return;

      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const blob = item.getAsFile();
          if (blob) {
            e.preventDefault();
            a.assignAttachment?.(
              new File([blob], `paste-${Date.now()}.png`, { type: blob.type }),
            );
            window.showAriaToast?.("Image pasted — ready to send", "ok", 2000);
            break;
          }
        }
        // File paste (some browsers)
        if (item.kind === "file") {
          const f = item.getAsFile();
          if (f && isAttachable(f) && !item.type.startsWith("image/")) {
            e.preventDefault();
            a.assignAttachment?.(f);
            window.showAriaToast?.(`Attached ${f.name}`, "ok", 2000);
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
