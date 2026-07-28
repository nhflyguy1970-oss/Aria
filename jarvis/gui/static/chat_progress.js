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
    const text = String(msg || "Something went wrong").trim();
    const hint = /ollama|provider|timeout|connect|refus/i.test(text)
      ? " — Retry, switch model, or open Mission Control diagnostics"
      : " — Retry or check Activity Center for details";
    window.addMessage?.("assistant", text, { type: "info" });
    const { statusText } = els();
    if (statusText) {
      const short = text.length > 72 ? `${text.slice(0, 69)}…` : text;
      statusText.textContent = short.includes("—") ? short : `${short}${hint}`;
    }
    window.showAriaToast?.(text.slice(0, 160), "err", 5000);
  }

  function showProviderRecovery(message, opts = {}) {
    const retryText = opts.retryText || "";
    const reason = opts.reason || "PROVIDER_TIMEOUT";
    const wrap = document.createElement("div");
    wrap.className = "chat-recovery";
    wrap.setAttribute("role", "alert");
    const title = document.createElement("p");
    title.className = "chat-recovery-title";
    title.textContent = "Model provider timed out";
    const body = document.createElement("p");
    body.className = "chat-recovery-body";
    body.textContent = message || "The provider accepted the request but did not produce a response in time.";
    const actions = document.createElement("div");
    actions.className = "chat-recovery-actions";
    const mkBtn = (label, onClick, primary) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = primary ? "ghost-btn small chat-recovery-primary" : "ghost-btn small";
      b.textContent = label;
      b.addEventListener("click", onClick);
      return b;
    };
    actions.appendChild(mkBtn("Retry", () => {
      if (retryText) window.sendMessage?.(retryText);
      else document.getElementById("messageInput")?.focus();
    }, true));
    actions.appendChild(mkBtn("Stop", () => window.stopChat?.()));
    actions.appendChild(mkBtn("Switch Model", () => {
      window.switchToView?.("chat");
      document.getElementById("modelsToggle")?.click?.();
      window.openCommandPalette?.("model");
      window.showAriaToast?.("Open Models or use the command palette to switch models", "info", 4000);
    }));
    actions.appendChild(mkBtn("Switch Provider", () => {
      window.openCommandPalette?.("provider");
      window.switchToView?.("audit");
      window.showAriaToast?.("Check provider status under System / Mission Control", "info", 4000);
    }));
    actions.appendChild(mkBtn("View Diagnostics", () => {
      window.switchToView?.("workstation");
      setTimeout(() => {
        document.querySelector('[data-mc-tab="diagnostics"], [data-tab="diagnostics"]')?.click?.();
      }, 200);
    }));
    wrap.appendChild(title);
    wrap.appendChild(body);
    const meta = document.createElement("p");
    meta.className = "chat-recovery-meta muted";
    meta.textContent = `Reason: ${reason}`;
    wrap.appendChild(meta);
    wrap.appendChild(actions);
    const msgs = document.getElementById("messages");
    if (msgs) {
      const row = document.createElement("div");
      row.className = "message assistant";
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.appendChild(wrap);
      row.appendChild(bubble);
      msgs.appendChild(row);
      msgs.scrollTop = msgs.scrollHeight;
    } else {
      showError(`${title.textContent}: ${body.textContent}`);
    }
    const { statusText } = els();
    if (statusText) statusText.textContent = "Provider timeout — choose a recovery action";
    window.showAriaToast?.("Model provider timed out — use Retry or Diagnostics", "err", 5000);
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
      if (document.hidden) return;
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
    showProviderRecovery,
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
