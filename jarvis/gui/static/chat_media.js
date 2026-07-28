/** Chat media helpers — showGeneratedImage / showAudioPlayer (extracted from app.js). */
(function () {
  function showGeneratedImage(path, name) {
    if (!path || typeof window.addMessage !== "function") return;
    window.addMessage("assistant", "", { type: "image_result", module: "image" });
    const msg = document.querySelector(".message.assistant:last-child .msg-body");
    setTimeout(() => {
      if (typeof window.appendGeneratedImage === "function") {
        window.appendGeneratedImage(msg, path, name);
      }
    }, 600);
  }

  function showAudioPlayer(path, transcript) {
    if (!path || typeof window.addMessage !== "function") return;
    const esc = window.escapeHtml || ((s) => String(s));
    const url = `/api/audio/file?path=${encodeURIComponent(path)}`;
    const name = path.split("/").pop();
    let html = `<div class="chat-audio-block"><p class="chat-audio-label">${esc(name)}</p><audio controls src="${url}" class="chat-audio-player"></audio>`;
    if (transcript) {
      html += `<details class="chat-transcript-details"><summary>Transcript</summary><pre class="chat-transcript">${esc(transcript)}</pre></details>`;
    }
    html += "</div>";
    window.addMessage("assistant", html, { type: "info" });
  }

  window.showGeneratedImage = showGeneratedImage;
  window.showAudioPlayer = showAudioPlayer;

  // Back-compat: jarvisSendToChat is owned by chat_os.js (auto-send). Soft fallback only.
  if (typeof window.jarvisSendToChat !== "function") {
    window.jarvisSendToChat = (text) => {
      if (typeof window.jarvisAskAria === "function") return window.jarvisAskAria(text);
      const input = document.getElementById("messageInput");
      if (input) input.value = text || "";
      window.switchToView?.("chat");
      setTimeout(() => window.sendMessage?.(text), 60);
    };
  }
})();
