/** Chat progress / busy / stop / error UI — extracted from app.js. */
(function () {
  let progressTimer = null;
  let progressStart = 0;

  function els() {
    const progressBar = document.getElementById("progressBar");
    return {
      progressBar,
      progressText: document.getElementById("progressText"),
      progressFill: progressBar?.querySelector(".progress-fill"),
      statusText: document.getElementById("statusText"),
      sendBtn: document.getElementById("sendBtn"),
      stopChatBtn: document.getElementById("stopChatBtn"),
    };
  }

  function chat() {
    return window.jarvisChat || {};
  }

  function progressLabel(text) {
    if (window.isVideoRequest?.(text)) return "Rendering keyframe & motion clip…";
    if (window.isImageRequest?.(text)) return "Understanding scene & generating…";
    const a = window.jarvisAttach || {};
    if (a.pendingFile2) return "Comparing images…";
    if (typeof a.isVisionAttachment === "function" && a.isVisionAttachment(a.pendingFile)) {
      return "Analyzing image…";
    }
    if (window.isVisionAttachment?.(a.pendingFile)) return "Analyzing image…";
    return "Thinking…";
  }

  function showError(msg) {
    window.addMessage?.("assistant", msg, { type: "info" });
    const { statusText } = els();
    if (statusText) statusText.textContent = "Error";
  }

  function showProgress(label = "Thinking…") {
    const { progressBar, progressFill, progressText } = els();
    if (!progressBar) return;
    progressBar.classList.remove("hidden");
    if (progressFill) progressFill.style.width = "30%";
    if (progressText) progressText.textContent = label;
    progressStart = Date.now();
    clearInterval(progressTimer);
    progressTimer = setInterval(() => {
      const sec = Math.floor((Date.now() - progressStart) / 1000);
      if (progressText) {
        progressText.textContent = sec > 0 ? `${label} (${sec}s)` : label;
      }
      if (progressFill) {
        const w = Math.min(90, 30 + sec * 3);
        progressFill.style.width = `${w}%`;
      }
    }, 500);
  }

  function hideProgress() {
    const { progressBar, progressFill } = els();
    clearInterval(progressTimer);
    progressTimer = null;
    if (progressBar) progressBar.classList.add("hidden");
    if (progressFill) progressFill.style.width = "0%";
  }

  function setChatBusy(busy) {
    const c = chat();
    c.chatRequestActive = busy;
    const { sendBtn, stopChatBtn } = els();
    if (sendBtn) {
      sendBtn.disabled = busy;
      sendBtn.classList.toggle("hidden", busy);
    }
    stopChatBtn?.classList.toggle("hidden", !busy);
    if (!busy) {
      c.chatAbortController = null;
      c.chatStopRequested = false;
      c.activeStreamText = "";
    }
  }

  function stopChat() {
    const c = chat();
    c.chatStopRequested = true;
    const sid = c.activeChatRequestId;
    if (sid) {
      const fd = new FormData();
      fd.append("request_id", sid);
      fetch("/api/chat/cancel", { method: "POST", body: fd })
        .then(async (res) => {
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.message || err.detail || `Cancel failed (${res.status})`);
          }
          window.showAriaToast?.("Generation cancelled", "ok", 2500);
        })
        .catch((err) => {
          window.showAriaToast?.(
            err?.message || "Could not reach cancel API — stream aborted locally",
            "err",
            5000,
          );
        });
    }
    c.chatAbortController?.abort?.();
    const { statusText } = els();
    if (statusText) statusText.textContent = "Stopping…";
  }

  function updateProgressStatus(message) {
    const { progressText, statusText } = els();
    if (progressText) progressText.textContent = message;
    if (statusText) statusText.textContent = message;
  }

  function bindStopButton() {
    const btn = document.getElementById("stopChatBtn");
    if (!btn || btn.dataset.progressBound === "1") return;
    btn.dataset.progressBound = "1";
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      stopChat();
    });
  }

  Object.assign(window, {
    progressLabel,
    showError,
    showProgress,
    hideProgress,
    setChatBusy,
    stopChat,
    updateProgressStatus,
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindStopButton, { once: true });
  } else {
    bindStopButton();
  }
})();
