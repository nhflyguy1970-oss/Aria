/** Themed Aria prompt/confirm dialogs — replaces browser prompt()/confirm(). */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  let _confirmSeq = 0;
  let _promptSeq = 0;

  /** Living Workspace hides #ariaLegacyShell — dialogs must live on <body>. */
  function ensureBodyHost(dlg) {
    if (!dlg || !document.body) return dlg;
    if (dlg.parentElement !== document.body) {
      document.body.appendChild(dlg);
    }
    return dlg;
  }

  function dismissDialog(dlg, value) {
    if (!dlg) return;
    try {
      if (dlg.open) {
        dlg.returnValue = value || "cancel";
        dlg.close();
      }
    } catch (_) {
      /* ignore */
    }
  }

  function ariaDismissDialogs() {
    dismissDialog($("ariaConfirmDialog"), "cancel");
    dismissDialog($("ariaPromptDialog"), "cancel");
  }

  function ariaConfirm(message, opts = {}) {
    const dlg = ensureBodyHost($("ariaConfirmDialog"));
    if (!dlg?.showModal) {
      return Promise.resolve(window.confirm(message));
    }
    // Never let a prior Restart/Apply confirm linger and steal the next answer.
    dismissDialog(dlg, "cancel");
    const seq = ++_confirmSeq;
    $("ariaConfirmTitle").textContent = opts.title || "Confirm";
    $("ariaConfirmBody").textContent = message || "";
    $("ariaConfirmOk").textContent = opts.okLabel || "Confirm";
    $("ariaConfirmCancel").textContent = opts.cancelLabel || "Cancel";
    return new Promise((resolve) => {
      const onClose = () => {
        dlg.removeEventListener("close", onClose);
        if (seq !== _confirmSeq) {
          resolve(false);
          return;
        }
        resolve(dlg.returnValue === "ok");
      };
      dlg.addEventListener("close", onClose);
      $("ariaConfirmCancel").onclick = () => {
        dlg.returnValue = "cancel";
        dlg.close();
      };
      $("ariaConfirmOk").onclick = (e) => {
        e.preventDefault();
        dlg.returnValue = "ok";
        dlg.close();
      };
      dlg.returnValue = "";
      try {
        dlg.showModal();
      } catch (_) {
        // Already open in some browsers — force close then reopen.
        dismissDialog(dlg, "cancel");
        try {
          dlg.showModal();
        } catch (err2) {
          resolve(window.confirm(message));
        }
      }
    });
  }

  function ariaPrompt(message, defaultValue = "", opts = {}) {
    const dlg = ensureBodyHost($("ariaPromptDialog"));
    if (!dlg?.showModal) {
      return Promise.resolve(window.prompt(message, defaultValue));
    }
    dismissDialog(dlg, "cancel");
    const seq = ++_promptSeq;
    $("ariaPromptTitle").textContent = opts.title || "Input";
    $("ariaPromptIntro").textContent = message || "";
    const input = $("ariaPromptInput");
    if (input) {
      input.value = defaultValue || "";
      if (opts.password || opts.type === "password") input.type = "password";
      else input.type = "text";
    }
    $("ariaPromptOk").textContent = opts.okLabel || "OK";
    return new Promise((resolve) => {
      const finish = (val) => {
        dlg.removeEventListener("close", onClose);
        if (seq !== _promptSeq) {
          resolve(null);
          return;
        }
        resolve(val);
      };
      const onClose = () => {
        if (dlg.returnValue === "ok") finish(input?.value ?? null);
        else finish(null);
      };
      dlg.addEventListener("close", onClose);
      $("ariaPromptCancel").onclick = () => {
        dlg.returnValue = "cancel";
        dlg.close();
      };
      $("ariaPromptOk").onclick = (e) => {
        e.preventDefault();
        dlg.returnValue = "ok";
        dlg.close();
      };
      dlg.returnValue = "";
      try {
        dlg.showModal();
      } catch (_) {
        dismissDialog(dlg, "cancel");
        try {
          dlg.showModal();
        } catch (err2) {
          resolve(window.prompt(message, defaultValue));
          return;
        }
      }
      setTimeout(() => input?.focus(), 40);
    });
  }

  // Re-host on boot so Living Workspace never inherits a hidden-shell parent.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      ensureBodyHost($("ariaPromptDialog"));
      ensureBodyHost($("ariaConfirmDialog"));
      ensureBodyHost($("chatNewDialog"));
    });
  } else {
    ensureBodyHost($("ariaPromptDialog"));
    ensureBodyHost($("ariaConfirmDialog"));
    ensureBodyHost($("chatNewDialog"));
  }

  window.ariaConfirm = ariaConfirm;
  window.ariaPrompt = ariaPrompt;
  window.ariaDismissDialogs = ariaDismissDialogs;
})();
