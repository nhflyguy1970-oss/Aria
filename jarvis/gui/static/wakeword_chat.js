/** Wake-word → chat bridge — extracted from app.js. */
(function () {
  "use strict";

  let lastWakewordEventId = sessionStorage.getItem("jarvisWwChatId") || "";
  let wakewordLikelyRunning = false;
  let pollTimer = null;

  function nextDelayMs() {
    if (window.isNativeApp?.()) return wakewordLikelyRunning ? 5000 : 20000;
    return wakewordLikelyRunning ? 2500 : 15000;
  }

  function schedulePoll() {
    if (pollTimer) clearTimeout(pollTimer);
    pollTimer = setTimeout(async () => {
      if (!document.hidden && !window.mediaWorkActive?.()) {
        await pollWakewordChat();
      }
      schedulePoll();
    }, nextDelayMs());
  }

  async function pollWakewordChat() {
    if (window.mediaWorkActive?.()) return;
    try {
      const res = await fetch("/api/audio/wakeword/status");
      if (!res.ok) return;
      const data = await res.json();
      wakewordLikelyRunning = Boolean(data.running || data.to_chat);
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
        (document.getElementById("statusText") || {}).textContent = "Wake word → chat";
        window.handleDone?.({
          ok: last.chat_ok !== false,
          message: last.chat_response,
          module: last.chat_module,
          type: last.chat_type,
        });
        return;
      }

      if (last.chat_status === "ready" && userText) {
        (document.getElementById("statusText") || {}).textContent = "Wake word → chat…";
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
  schedulePoll();
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) pollWakewordChat();
  });
})();
