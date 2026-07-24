/** Wake-word → chat bridge — extracted from app.js. */
(function () {
  "use strict";

let lastWakewordEventId = sessionStorage.getItem("jarvisWwChatId") || "";

async function pollWakewordChat() {
  if (window.mediaWorkActive?.()) return;
  try {
    const res = await fetch("/api/audio/wakeword/status");
    if (!res.ok) return;
    const data = await res.json();
    if (!data.to_chat) return;
    const last = data.last || {};
    const eventId = last.chat_event_id || (last.action === "recorded" ? String(last.ts || "") : "");
    if (!eventId || eventId === lastWakewordEventId) return;

    if (last.chat_status === "pending") return;

    const userText = (last.chat_message || last.transcript || "").trim();
    if (!userText && last.chat_status !== "error") return;

    lastWakewordEventId = eventId;
    sessionStorage.setItem("jarvisWwChatId", eventId);
    document.querySelector('.view-tab[data-view="chat"]')?.click();

    if (last.chat_status === "done" && last.chat_response) {
      window.addMessage?.("user", userText);
      (document.getElementById("statusText")||{}).textContent = "Wake word → chat";
      window.handleDone?.({
        ok: last.chat_ok !== false,
        message: last.chat_response,
        module: last.chat_module,
        type: last.chat_type,
      });
      return;
    }

    if (last.chat_status === "ready" && userText) {
      (document.getElementById("statusText")||{}).textContent = "Wake word → chat…";
      if (typeof window.sendMessage === "function") await window.sendMessage(userText);
      return;
    }

    if (last.chat_status === "error") {
      window.showError?.(last.chat_error || "Wake word chat failed.");
    }
  } catch {
    /* ignore poll errors */
  }
}


  window.pollWakewordChat = pollWakewordChat;
  setInterval(() => {
    if (!window.mediaWorkActive?.()) pollWakewordChat();
  }, window.isNativeApp?.() ? 5000 : 2500);
})();
