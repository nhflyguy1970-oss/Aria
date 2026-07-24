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

// Media URL/auth helpers → media_urls.js (window.apiAuthUrl / resolveVideo* / attachMediaLoadError)
// Do not redeclare as const/let — video_studio.js already binds resolveVideoUrl globally.

// LAN / API key modal → lan_access.js (window.showApiKeyModal, window.mediaNeedsApiKey)

// initHaPanel called after statusText is defined below
const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const stopChatBtn = document.getElementById("stopChatBtn");
const fileInput = document.getElementById("fileInput");
const attachmentPreview = document.getElementById("attachmentPreview");
const statusText = document.getElementById("statusText");

window.initHaPanel?.();

let _lastEditorFile = "";
let pendingFile = null;
let pendingFile2 = null;
let compareMode = false;
let pendingCrop = null;
let pendingVideoSecond = "";
let pendingPdfPage = "1";
let visionChips = [];
let dataChips = [];
let lastAssistantText = "";
let useStreaming = true;
let _activeBranchId = "main";

// Branding → branding.js (window.ariaName / window.applyBranding)
let chatAbortController = null;
let chatStopRequested = false;
let activeStreamText = "";
let activeChatRequestId = "";

// Branches → chat_branches.js
// Job center → modules/jobs.mjs
// Message format/copy → chat_format.js (window.escapeHtml / formatMessage / createCopyButton)

const GALLERY_THUMB_MAX = 384;
window.GALLERY_THUMB_MAX = GALLERY_THUMB_MAX;
const CHAT_IMAGE_THUMB_MAX = 320;
window.CHAT_IMAGE_THUMB_MAX = CHAT_IMAGE_THUMB_MAX;

function isNativeApp() {
  return document.documentElement.classList.contains("jarvis-app");
}

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


// Image URL/figure helpers → chat_images.js

function applyAssistantMeta(messageEl, meta) {
  const bubble = messageEl?.querySelector?.(".bubble") || messageEl?.closest?.(".message")?.querySelector?.(".bubble");
  if (!bubble) return;
  const showTag = meta.module && meta.module !== "general" && meta.type !== "info";
  let tag = bubble.querySelector(".module-tag");
  if (showTag) {
    if (!tag) {
      tag = document.createElement("div");
      bubble.appendChild(tag);
    }
    tag.className = `module-tag ${meta.module}`;
    tag.textContent = meta.module;
  } else if (tag) {
    tag.remove();
  }
}

// appendGeneratedImage → chat_images.js

// buildVision/Image/DataTable HTML → chat_images.js

function scrollMessageIntoView(node, block = "start") {
  const msg = node?.closest?.(".message") || node;
  if (!msg || !messagesEl) return;
  const msgTop = msg.offsetTop;
  const msgBottom = msgTop + msg.offsetHeight;
  const viewTop = messagesEl.scrollTop;
  const viewBottom = viewTop + messagesEl.clientHeight;
  if (block === "start") {
    if (msgTop < viewTop) messagesEl.scrollTop = msgTop;
    else if (msgBottom > viewBottom) messagesEl.scrollTop = msgBottom - messagesEl.clientHeight;
  } else {
    messagesEl.scrollTop = Math.max(0, msgBottom - messagesEl.clientHeight);
  }
}

function resizeMessageInput() {
  if (!messageInput) return;
  messageInput.style.height = "auto";
  const next = Math.min(Math.max(messageInput.scrollHeight, 24), 120);
  messageInput.style.height = `${next}px`;
}

function isImageRequest(text) {
  const t = text.trim();
  return (
    /\b(create|generate|make|draw)\b[\s\S]*\b(image|picture|photo|illustration)\b/i.test(t)
    || /\b(image|picture|photo)\b[\s\S]*\b(of|showing)\b/i.test(t)
  );
}

function isVideoRequest(text) {
  const t = text.trim();
  return /\b(create|generate|make)\b[\s\S]*\b(video|clip|animation|movie)\b/i.test(t);
}

// vramPreflight → free_vram.js (window.vramPreflight)

// pollComfySettingsJob → image_engine.js

// Chat video helpers → chat_video.js

function isVisionAttachment(file) {
  return Boolean(file && (/^image\//i.test(file.type) || /^video\//i.test(file.type)));
}

function isDataAttachment(file) {
  return Boolean(
    file && (/\.(csv|json|xlsx|xlsm|db|sqlite|sqlite3)$/i.test(file.name)
      || file.type === "text/csv" || file.type === "application/json"),
  );
}

// progressLabel / showProgress / setChatBusy / stopChat → chat_progress.js

// Coding proposals/diff/apply → coding_proposals.js

// addMessage / addTyping → chat_messages.js

// shouldShowUndo / applyProposal / undoLastApply → coding_proposals.js

// upgrade wizard → upgrade_wizard.js

// parseJsonResponse → chat_send.js

// showError / showProgress / hideProgress / setChatBusy / stopChat → chat_progress.js

function finishSendUi() {
  window.hideProgress?.();
  window.setChatBusy?.(false);
  pendingFile = null;
  pendingFile2 = null;
  pendingCrop = null;
  pendingVideoSecond = "";
  pendingPdfPage = "1";
  compareMode = false;
  if (attachmentPreview) attachmentPreview.classList.add("hidden");
  if (fileInput) fileInput.value = "";
  fileInput?.removeAttribute("multiple");
  const fileInput2 = document.getElementById("fileInput2");
  if (fileInput2) fileInput2.value = "";
  window.updateCompareButton?.();
}

// updateProgressStatus → chat_progress.js

// isStreamableAttachment → chat_send.js

// showChatWarnings / handleDone → chat_done.js

async function forkBranchFromIndex(displayIndex) {
  const name = prompt("New branch name:", "Fork");
  if (!name) return;
  const form = new FormData();
  form.append("name", name);
  form.append("display_index", String(displayIndex));
  try {
    const res = await fetch("/api/branches/fork", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      window.showError(data.message || "Could not fork branch.");
      window.showAriaToast?.(data.message || "Could not fork branch", "err", 5000);
      return;
    }
    _activeBranchId = data.branch_id;
    await window.loadBranches?.();
    await window.reloadBranchMessages?.();
    statusText.textContent = `Forked branch: ${name}`;
    window.showAriaToast?.(`Forked branch: ${name}`, "ok", 3000);
  } catch (e) {
    window.showError(String(e.message || e));
    window.showAriaToast?.(String(e.message || e), "err", 5000);
  }
}

window.forkBranchFromIndex = forkBranchFromIndex;

// sendMessage → chat_send.js


// Media job track/resume/poll → media_jobs.js (window.activeMediaJobs / pollMediaJob / resumePendingMediaJobs)

// pollCodingJob → coding_jobs.js (window.jarvisPollCodingJob)

// pollMediaJob → media_jobs.js

// handleDone → chat_done.js

window.finishSendUi = finishSendUi;
// window.addTyping → chat_messages.js

chatForm?.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value;
  messageInput.value = "";
  messageInput.style.height = "auto";
  resizeMessageInput();
  window.sendMessage?.(text);
});

messageInput?.addEventListener("input", resizeMessageInput);

messageInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

// Attachment compare / preview / chips → attachment_compare.js
// (window.updateAttachmentPreview / assignAttachment / refresh*Chips / compare mode)

// openCropModal / webcam → crop_webcam.js (window.openCropModal, window.captureWebcamAttachment)
// initVisionDropPaste → vision_drop.js

// clear / readAloud / mic → chat_controls.js (window.initChatControls)

// window.sendMessage → chat_send.js
window.isNativeApp = isNativeApp;
window.isVisionAttachment = isVisionAttachment;
window.isImageRequest = isImageRequest;
window.isVideoRequest = isVideoRequest;
window.isDataAttachment = isDataAttachment;
window.jarvisAttach = {
  get pendingFile() { return pendingFile; },
  set pendingFile(v) { pendingFile = v; },
  get pendingFile2() { return pendingFile2; },
  set pendingFile2(v) { pendingFile2 = v; },
  get compareMode() { return compareMode; },
  set compareMode(v) { compareMode = v; },
  get pendingCrop() { return pendingCrop; },
  set pendingCrop(v) { pendingCrop = v; },
  get pendingVideoSecond() { return pendingVideoSecond; },
  set pendingVideoSecond(v) { pendingVideoSecond = v; },
  get pendingPdfPage() { return pendingPdfPage; },
  set pendingPdfPage(v) { pendingPdfPage = v; },
  get visionChips() { return visionChips; },
  set visionChips(v) { visionChips = Array.isArray(v) ? v : []; },
  get dataChips() { return dataChips; },
  set dataChips(v) { dataChips = Array.isArray(v) ? v : []; },
  isVisionAttachment,
  isDataAttachment,
  isTextEntryElement: (...args) => window.isTextEntryElement?.(...args),
  escapeHtml: (...args) => window.escapeHtml?.(...args),
};
// Attachment methods filled by attachment_compare.js
// loadVisionSettings → vision_settings.js
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

// Editor context pill/card + suggestion chips → editor_context.js
// Health/live polling, GPU/audio status and service rendering → modules/health.mjs
// image engine → image_engine.js


// View routing → view_router.js (window.switchToView)

// sidebar chrome → sidebar_chrome.js (window.resetSidebarLayout)


// window.addMessage → chat_messages.js
// createCopyButton / syncMessageRawText → chat_format.js
window.scrollMessageIntoView = scrollMessageIntoView;
window.applyAssistantMeta = applyAssistantMeta;



// video sidebar → video_sidebar.js

document.addEventListener("DOMContentLoaded", () => {
  window.refreshSidebarVideoStatus?.();
});


function fetchWithTimeout(url, options = {}, timeoutMs = 5000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  return fetch(url, { ...options, signal: ctrl.signal }).finally(() => clearTimeout(timer));
}
window.fetchWithTimeout = fetchWithTimeout;

// startup overlay → startup_overlay.js (window.waitForServices)

// models editor → models_panel.js (window.loadModelSettings)

// uncensored mode → uncensored_mode.js (window.restoreUncensoredSession)

// wakeword → wakeword_chat.js (window.pollWakewordChat)

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && String(e.key).toLowerCase() === "r") {
    e.preventDefault();
    window.reloadJarvisUi?.();
  }
});
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) window.scheduleEditorContextPoll?.();
});
// Define before startup_overlay.js invokes waitForServices → ariaPostStartup
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

// coding / LSP → coding_panel.js (window.loadCodingPanel / runLspAction)

// View switching → view_router.js

// memory → memory_browser.js (window.loadMemoryBrowser / initMemoryBrowser)

window.addEventListener("beforeunload", () => {
  try {
    navigator.sendBeacon("/api/memory/auto-checkpoint", "{}");
  } catch (_) {}
});


// profile questionnaire → memory_browser.js

// inpaint modal → media_lightbox.js

// gallery → gallery_view.js (window.loadGallery)

// loadActions → movie_tiers.js (window.loadActions)

// git status/diff/log → git_panel.js (window.loadGitStatus)

// chat model select → chat_model_select.js (window.loadChatModelSelect)

// Chat export / backup → chat_export.js

// theme → theme.js

// profile / personality / actions clear / debug → profile_controls.js

// notify → notify.js (window.jarvisNotify)

document.addEventListener("keydown", (e) => {
  const inTextField = window.isTextEntryElement?.(e.target);
  if (e.ctrlKey && e.key === "Enter") {
    if (inTextField && e.target !== messageInput) return;
    e.preventDefault();
    window.sendMessage?.(messageInput.value);
  }
  if (e.ctrlKey && e.key === "l" && !inTextField) {
    e.preventDefault();
    document.getElementById("clearBtn")?.click();
  }
});

window.resizeMessageInput = resizeMessageInput;

// showGeneratedImage / showAudioPlayer / jarvisSendToChat → chat_media.js

// debug bundle → profile_controls.js

// personality/branches → chat_branches.js

