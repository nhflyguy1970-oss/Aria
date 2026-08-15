/** Aria app shell — post-startup, session globals, thin orchestration. */
// Media URL/auth helpers → media_urls.js
// LAN / API key modal → lan_access.js
// API key fetch wrapper → api_key_fetch.js
// Branding → branding.js
// Chat state → chat_state.js
// Attachment state / finishSendUi → chat_attach.js
// Composer → chat_input.js
// clear / readAloud / mic → chat_controls.js

window.initHaPanel?.();

let _lastEditorFile = "";
let _activeBranchId = "main";

const GALLERY_THUMB_MAX = 384;
window.GALLERY_THUMB_MAX = GALLERY_THUMB_MAX;
const CHAT_IMAGE_THUMB_MAX = 320;
window.CHAT_IMAGE_THUMB_MAX = CHAT_IMAGE_THUMB_MAX;

function isNativeApp() {
  return document.documentElement.classList.contains("jarvis-app");
}
window.isNativeApp = isNativeApp;

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
    const hashView = window.AriaViewRouter?.canonicalView?.(window.location.hash)
      || (window.location.hash || "").replace(/^#/, "").trim();
    if (hashView && document.querySelector(`.view-tab[data-view="${hashView}"]`)) {
      window.switchToView?.(hashView);
    }
    document.getElementById("presetQualityBtn")?.classList.add("active");
    window.startHealthMonitoring?.();
    setInterval(() => {
      if (document.hidden || window.mediaWorkActive?.()) return;
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
