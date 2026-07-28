/** Chat clear / read-aloud / mic — extracted from app.js. */
(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function bindClear() {
    $("clearBtn")?.addEventListener("click", async () => {
      try {
        const f = new FormData();
        f.append("message", "clear");
        if (window.activeBranchId) f.append("branch_id", window.activeBranchId);
        const res = await fetch("/api/chat", { method: "POST", body: f });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.message || data.detail || `Clear failed (${res.status})`);
        const messagesEl = $("messages");
        if (messagesEl) messagesEl.innerHTML = "";
        window.addMessage?.("assistant", "Fresh start. What would you like to do?");
        window.showAriaToast?.("Conversation cleared", "ok", 2500);
      } catch (err) {
        window.showAriaToast?.(err.message || "Could not clear conversation", "err", 5000);
      }
    });
  }

  function bindReadAloud() {
    const readAloudBtn = $("readAloudBtn");
    if (!readAloudBtn) return;
    readAloudBtn.addEventListener("click", async () => {
      const text = window.jarvisChat?.lastAssistantText || "";
      if (!text) {
        window.showAriaToast?.("Nothing to read yet — wait for an assistant reply", "info", 3000);
        return;
      }
      readAloudBtn.disabled = true;
      const statusText = $("statusText");
      if (statusText) statusText.textContent = "Speaking on Sound Blaster…";
      try {
        const form = new FormData();
        form.append("text", String(text).replace(/[*`#]/g, "").slice(0, 4000));
        const res = await fetch("/api/audio/speak", { method: "POST", body: form });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          const msg = data.message || `Could not play audio (${res.status})`;
          window.showError?.(msg);
          window.showAriaToast?.(msg, "err", 5000);
        } else if (statusText) {
          statusText.textContent = "Ready · Sound Blaster";
        }
      } catch (e) {
        window.showError?.(`Audio playback failed: ${e.message}`);
        window.showAriaToast?.(`Audio playback failed: ${e.message}`, "err", 5000);
      } finally {
        readAloudBtn.disabled = false;
      }
    });
  }

  function bindMic() {
    const micBtn = $("micBtn");
    if (!micBtn) return;
    const hasBrowserStt = "webkitSpeechRecognition" in window || "SpeechRecognition" in window;
    const useBrowserMicStt = () =>
      (typeof window.jarvisUseServerWhisper === "function"
        ? !window.jarvisUseServerWhisper()
        : localStorage.getItem("jarvis_chat_server_whisper") === "0");

    // Never disable mic when server Whisper can run — PTT is bound in movie_tiers.js
    micBtn.disabled = false;
    if (!hasBrowserStt) {
      micBtn.title = "Hold for server Whisper (browser STT unavailable)";
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      const messageInput = $("messageInput");
      if (messageInput) messageInput.value = transcript;
      micBtn.classList.remove("listening");
      window.sendMessage?.(transcript);
    };
    recognition.onerror = (ev) => {
      micBtn.classList.remove("listening");
      const err = ev?.error || "mic error";
      if (err !== "aborted" && err !== "no-speech") {
        window.showAriaToast?.(`Mic: ${err}`, "err", 4000);
      }
    };
    recognition.onend = () => micBtn.classList.remove("listening");

    if (useBrowserMicStt()) {
      micBtn.addEventListener("click", () => {
        if (micBtn.classList.contains("listening")) {
          recognition.stop();
        } else {
          micBtn.classList.add("listening");
          recognition.start();
        }
      });
      micBtn.title = "Click for browser speech recognition";
    } else {
      micBtn.title = "Hold for server Whisper (see Settings)";
    }
  }

  function initChatControls() {
    bindClear();
    bindReadAloud();
    bindMic();
  }

  window.initChatControls = initChatControls;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initChatControls);
  } else {
    initChatControls();
  }
})();
