(function initApiKeyFetch() {
  const params = new URLSearchParams(location.search);
  const qKey = params.get("api_key")?.trim();
  if (qKey) sessionStorage.setItem("jarvis_api_key", qKey);
  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (url, opts = {}) => {
    const key = sessionStorage.getItem("jarvis_api_key");
    const path = String(url).split("?")[0];
    if (path.startsWith("/api/")) {
      const headers = new Headers(opts.headers || {});
      if (key && !headers.has("X-API-Key")) headers.set("X-API-Key", key);
      if (typeof window.jarvisDeviceId === "function" && !headers.has("X-Jarvis-Device")) {
        headers.set("X-Jarvis-Device", window.jarvisDeviceId());
      }
      const sess = typeof window.jarvisSession === "function" ? window.jarvisSession() : "";
      if (sess && !headers.has("X-Jarvis-Session")) headers.set("X-Jarvis-Session", sess);
      opts = { ...opts, headers };
    }
    const res = await nativeFetch(url, opts);
    if (
      res.status === 401
      && path.startsWith("/api/")
      && !["/api/health", "/api/live", "/api/lan"].includes(path)
    ) {
      window.showApiKeyModal?.("Invalid or missing API key.");
    }
    return res;
  };
})();

// Media URL/auth helpers → media_urls.js
// LAN / API key modal → lan_access.js
// Branding → branding.js
// Attachment state / finishSendUi → chat_attach.js
// Composer → chat_input.js
// clear / readAloud / mic → chat_controls.js

window.initHaPanel?.();

let _lastEditorFile = "";
let lastAssistantText = "";
let useStreaming = true;
let _activeBranchId = "main";
let chatAbortController = null;
let chatStopRequested = false;
let activeStreamText = "";
let activeChatRequestId = "";

const GALLERY_THUMB_MAX = 384;
window.GALLERY_THUMB_MAX = GALLERY_THUMB_MAX;
const CHAT_IMAGE_THUMB_MAX = 320;
window.CHAT_IMAGE_THUMB_MAX = CHAT_IMAGE_THUMB_MAX;

function isNativeApp() {
  return document.documentElement.classList.contains("jarvis-app");
}
window.isNativeApp = isNativeApp;

function syncMediaBusyClass() {
  if (!window.activeMediaJobs) window.activeMediaJobs = new Set();
  document.documentElement.classList.toggle("media-busy", window.activeMediaJobs.size > 0);
}
window.syncMediaBusyClass = syncMediaBusyClass;

let chatRequestActive = false;

function mediaWorkActive() {
  return chatRequestActive || (window.activeMediaJobs?.size || 0) > 0;
}
window.mediaWorkActive = mediaWorkActive;

window.jarvisChat = {
  get chatRequestActive() { return chatRequestActive; },
  set chatRequestActive(v) { chatRequestActive = v; },
  get chatAbortController() { return chatAbortController; },
  set chatAbortController(v) { chatAbortController = v; },
  get chatStopRequested() { return chatStopRequested; },
  set chatStopRequested(v) { chatStopRequested = v; },
  get activeStreamText() { return activeStreamText; },
  set activeStreamText(v) { activeStreamText = v; },
  get activeChatRequestId() { return activeChatRequestId; },
  set activeChatRequestId(v) { activeChatRequestId = v; },
  get useStreaming() { return useStreaming; },
  set useStreaming(v) { useStreaming = v; },
  get lastAssistantText() { return lastAssistantText; },
  set lastAssistantText(v) { lastAssistantText = v; },
};

Object.defineProperty(window, "activeBranchId", {
  get() { return _activeBranchId; },
  set(v) { _activeBranchId = v; },
  configurable: true,
});
Object.defineProperty(window, "lastEditorFile", {
  get() { return _lastEditorFile; },
  set(v) { _lastEditorFile = v; },
  configurable: true,
});

document.addEventListener("DOMContentLoaded", () => {
  window.refreshSidebarVideoStatus?.();
});

function fetchWithTimeout(url, options = {}, timeoutMs = 5000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  return fetch(url, { ...options, signal: ctrl.signal }).finally(() => clearTimeout(timer));
}
window.fetchWithTimeout = fetchWithTimeout;

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && String(e.key).toLowerCase() === "r") {
    e.preventDefault();
    window.reloadJarvisUi?.();
  }
});
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) window.scheduleEditorContextPoll?.();
});

window.ariaPostStartup = function ariaPostStartup() {
  try { window.initAriaModalChrome?.(); } catch (_) {}
  window.loadSuggestions?.();
  Promise.resolve(window.loadHealth?.()).then(async () => {
    await window.restoreUncensoredSession?.();
    window.loadModelSettings?.();
    window.loadComfyMode?.();
    window.loadGpuStatus?.();
    window.loadVisionSettings?.();
    window.loadBranches?.().then(() => window.reloadBranchMessages?.().then(() => window.resumePendingMediaJobs?.()));
    window.loadPersonality?.();
    window.loadChatModelSelect?.();
    window.maybeShowProfileQuestionnaire?.();
    window.loadCodingPanel?.();
    window.loadGitStatus?.();
    const params = new URLSearchParams(window.location.search);
    const prefill = params.get("msg");
    const messageInput = document.getElementById("messageInput");
    if (prefill && messageInput) {
      messageInput.value = prefill;
      window.history.replaceState({}, "", window.location.pathname);
      setTimeout(() => window.sendMessage?.(prefill), 300);
    }
    const hashView = (window.location.hash || "").replace(/^#/, "").trim();
    if (hashView && document.querySelector(`.view-tab[data-view="${hashView}"]`)) {
      window.switchToView?.(hashView);
    }
    document.getElementById("presetQualityBtn")?.classList.add("active");
    window.startHealthMonitoring?.();
    setInterval(() => {
      if (document.hidden || mediaWorkActive()) return;
      window.loadCodingPanel?.();
    }, 90000);
    window.scheduleEditorContextPoll?.();
  });
};

window.addEventListener("beforeunload", () => {
  try {
    navigator.sendBeacon("/api/memory/auto-checkpoint", "{}");
  } catch (_) {}
});
