/** Coding quick-actions — extracted from app.js. */
(function () {
  function sendQuickCodingMessage(msg) {
    if (!msg) return;
    const input = document.getElementById("messageInput");
    if (!input) return;
    const file = window.lastEditorFile || "";
    let text = msg;
    if (msg === "run tests for") {
      if (file) text = `run tests for ${file}`;
      else {
        input.value = "run tests for ";
        if (typeof window.switchToView === "function") window.switchToView("chat");
        input.focus();
        return;
      }
    }
    input.value = text;
    if (typeof window.switchToView === "function") window.switchToView("chat");
    if (typeof window.sendMessage === "function") {
      window.sendMessage(text);
    }
  }

  function bindCodingQuick() {
    document.getElementById("editorContextPill")?.addEventListener("click", () => {
      sendQuickCodingMessage("editor context");
    });
    document.getElementById("editorContextCard")?.addEventListener("click", () => {
      sendQuickCodingMessage("editor context");
    });
    document.querySelectorAll(".coding-quick-btn").forEach((btn) => {
      if (btn.dataset.codingQuickBound === "1") return;
      btn.dataset.codingQuickBound = "1";
      btn.addEventListener("click", () => sendQuickCodingMessage(btn.dataset.msg || ""));
    });
  }

  window.sendQuickCodingMessage = sendQuickCodingMessage;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindCodingQuick);
  } else {
    bindCodingQuick();
  }
})();
