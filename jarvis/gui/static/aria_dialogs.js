/** Themed Aria prompt/confirm dialogs — replaces browser prompt()/confirm(). */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function ariaConfirm(message, opts = {}) {
    const dlg = $("ariaConfirmDialog");
    if (!dlg?.showModal) {
      return Promise.resolve(window.confirm(message));
    }
    $("ariaConfirmTitle").textContent = opts.title || "Confirm";
    $("ariaConfirmBody").textContent = message || "";
    $("ariaConfirmOk").textContent = opts.okLabel || "Confirm";
    $("ariaConfirmCancel").textContent = opts.cancelLabel || "Cancel";
    return new Promise((resolve) => {
      const onClose = () => {
        dlg.removeEventListener("close", onClose);
        resolve(dlg.returnValue === "ok");
      };
      dlg.addEventListener("close", onClose);
      $("ariaConfirmCancel").onclick = () => { dlg.returnValue = "cancel"; dlg.close(); };
      $("ariaConfirmOk").onclick = (e) => {
        e.preventDefault();
        dlg.returnValue = "ok";
        dlg.close();
      };
      dlg.returnValue = "";
      dlg.showModal();
    });
  }

  function ariaPrompt(message, defaultValue = "", opts = {}) {
    const dlg = $("ariaPromptDialog");
    if (!dlg?.showModal) {
      return Promise.resolve(window.prompt(message, defaultValue));
    }
    $("ariaPromptTitle").textContent = opts.title || "Input";
    $("ariaPromptIntro").textContent = message || "";
    const input = $("ariaPromptInput");
    if (input) input.value = defaultValue || "";
    $("ariaPromptOk").textContent = opts.okLabel || "OK";
    return new Promise((resolve) => {
      const finish = (val) => {
        dlg.removeEventListener("close", onClose);
        resolve(val);
      };
      const onClose = () => {
        if (dlg.returnValue === "ok") finish(input?.value ?? null);
        else finish(null);
      };
      dlg.addEventListener("close", onClose);
      $("ariaPromptCancel").onclick = () => { dlg.returnValue = "cancel"; dlg.close(); };
      $("ariaPromptOk").onclick = (e) => {
        e.preventDefault();
        dlg.returnValue = "ok";
        dlg.close();
      };
      dlg.returnValue = "";
      dlg.showModal();
      setTimeout(() => input?.focus(), 40);
    });
  }

  window.ariaConfirm = ariaConfirm;
  window.ariaPrompt = ariaPrompt;
})();
