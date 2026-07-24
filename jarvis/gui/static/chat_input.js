/** Chat composer input / submit / shortcuts — extracted from app.js. */
(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function resizeMessageInput() {
    const messageInput = $("messageInput");
    if (!messageInput) return;
    messageInput.style.height = "auto";
    const next = Math.min(Math.max(messageInput.scrollHeight, 24), 120);
    messageInput.style.height = `${next}px`;
  }

  function bindChatInput() {
    const chatForm = $("chatForm");
    const messageInput = $("messageInput");

    chatForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = messageInput?.value || "";
      if (messageInput) {
        messageInput.value = "";
        messageInput.style.height = "auto";
      }
      resizeMessageInput();
      window.sendMessage?.(text);
    });

    messageInput?.addEventListener("input", resizeMessageInput);

    messageInput?.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatForm?.dispatchEvent(new Event("submit"));
      }
    });

    document.addEventListener("keydown", (e) => {
      const inTextField = window.isTextEntryElement?.(e.target);
      if (e.ctrlKey && e.key === "Enter") {
        if (inTextField && e.target !== messageInput) return;
        e.preventDefault();
        window.sendMessage?.(messageInput?.value || "");
      }
      if (e.ctrlKey && e.key === "l" && !inTextField) {
        e.preventDefault();
        $("clearBtn")?.click();
      }
    });
  }

  window.resizeMessageInput = resizeMessageInput;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindChatInput);
  } else {
    bindChatInput();
  }
})();
