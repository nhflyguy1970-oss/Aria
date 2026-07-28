/** Floating mini-chat — first-class Ask Aria surface with streaming replies. */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function hiddenPref() {
    return window.AriaUiPrefs?.get?.("miniChatHidden", false) === true;
  }

  function isOpen() {
    return !$("miniChatPanel")?.classList.contains("hidden");
  }

  function open() {
    if (hiddenPref()) {
      window.AriaUiPrefs?.set?.("miniChatHidden", false);
      updateFab();
    }
    const panel = $("miniChatPanel");
    if (!panel) return;
    panel.classList.remove("hidden");
    $("miniChatInput")?.focus();
  }

  function close() {
    $("miniChatPanel")?.classList.add("hidden");
  }

  function toggle() {
    if (isOpen()) close();
    else open();
  }

  function dockToChat() {
    close();
    window.switchToView?.("chat");
    setTimeout(() => document.getElementById("messageInput")?.focus(), 80);
  }

  function appendMini(role, text) {
    const log = $("miniChatLog");
    if (!log) return null;
    const row = document.createElement("div");
    row.className = `mini-chat-bubble mini-chat-${role === "user" ? "user" : "assist"}`;
    row.textContent = text || "";
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
    return row;
  }

  async function send() {
    const input = $("miniChatInput");
    const text = (input?.value || "").trim();
    if (!text) return;
    window.AriaHistory?.trackPrompt?.(text);
    appendMini("user", text);
    if (input) input.value = "";
    const assist = appendMini("assistant", "…");
    if (assist) assist.classList.add("muted");

    // Stream via main pipeline without forcing main view; mirror tokens into mini-chat
    const ask = window.jarvisAskAria || window.AriaChatOS?.askAria;
    if (typeof ask === "function") {
      await ask(text, {
        switchView: false,
        autoSend: true,
        returnView: "",
        onToken: (_chunk, full) => {
          if (assist) {
            assist.classList.remove("muted");
            assist.textContent = full || "";
            $("miniChatLog") && ($("miniChatLog").scrollTop = $("miniChatLog").scrollHeight);
          }
        },
        onDone: (_data, full) => {
          if (assist) {
            assist.classList.remove("muted");
            assist.textContent = full || assist.textContent || "(done)";
          }
        },
      });
      return;
    }

    // Fallback
    window.switchToView?.("chat");
    setTimeout(() => window.sendMessage?.(text), 80);
    if (assist) assist.textContent = "Sent to Chat — open Chat for the full reply.";
  }

  function quick(prompt) {
    const input = $("miniChatInput");
    if (input) input.value = prompt;
    send();
  }

  function updateFab() {
    const fab = $("miniChatFab");
    if (!fab) return;
    fab.classList.toggle("hidden", hiddenPref());
  }

  function init() {
    updateFab();
    $("miniChatFab")?.addEventListener("click", toggle);
    $("miniChatCloseBtn")?.addEventListener("click", close);
    $("miniChatDockBtn")?.addEventListener("click", dockToChat);
    $("miniChatSendBtn")?.addEventListener("click", send);
    $("miniChatInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        send();
      }
      if (e.key === "Escape") close();
    });
    document.querySelectorAll("[data-mini-prompt]").forEach((btn) => {
      btn.addEventListener("click", () => quick(btn.dataset.miniPrompt));
    });
    $("toggleMiniChatBtn")?.addEventListener("click", () => {
      window.AriaUiPrefs?.set?.("miniChatHidden", !hiddenPref());
      updateFab();
      if (hiddenPref()) close();
      const btn = $("toggleMiniChatBtn");
      if (btn) btn.textContent = hiddenPref() ? "Show mini chat" : "Hide mini chat";
    });
    const btn = $("toggleMiniChatBtn");
    if (btn) btn.textContent = hiddenPref() ? "Show mini chat" : "Hide mini chat";
  }

  window.AriaMiniChat = { open, close, toggle, send };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
