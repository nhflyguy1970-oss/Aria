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
const suggestionsEl = document.getElementById("suggestions");
const statusText = document.getElementById("statusText");

window.initHaPanel?.();

const editorContextPill = document.getElementById("editorContextPill");
const editorPillText = document.getElementById("editorPillText");
const editorContextCard = document.getElementById("editorContextCard");
const editorContextLabel = document.getElementById("editorContextLabel");
let _lastEditorFile = "";
const clearBtn = document.getElementById("clearBtn");
const micBtn = document.getElementById("micBtn");
const readAloudBtn = document.getElementById("readAloudBtn");
const appTitle = document.getElementById("appTitle");
const appTagline = document.getElementById("appTagline");
const hudEnv = document.getElementById("hudEnv");
const gpuStatusEl = document.getElementById("gpuStatus");
const pullLogEl = document.getElementById("pullLog");

let pendingFile = null;
let pendingFile2 = null;
let compareMode = false;
let pendingCrop = null;
let pendingVideoSecond = "";
let pendingPdfPage = "1";
let visionChips = [];
let dataChips = [];
let lastAssistantText = "";
let recognition = null;
let useStreaming = true;
let _activeBranchId = "main";
let assistantDisplayName = "ARIA";

function ariaName() {
  return assistantDisplayName || "ARIA";
}
window.ariaName = ariaName;

function applyBranding(data = {}) {
  assistantDisplayName = data.assistant_name || "ARIA";
  const name = assistantDisplayName;
  const full = data.assistant_full_name || "Adaptive Reasoning Intelligence Assistant";
  document.title = name;
  if (appTitle) appTitle.textContent = name;
  if (appTagline) appTagline.textContent = full;
  if (hudEnv) hudEnv.textContent = name;
  const svcName = document.getElementById("serviceAssistantName");
  if (svcName) svcName.textContent = name;
  const welcomeName = document.getElementById("welcomeAssistantName");
  if (welcomeName) welcomeName.textContent = name;
  const startupTitle = document.getElementById("startupOverlayTitle");
  if (startupTitle) startupTitle.textContent = `Starting ${name}…`;
  const upgradeBtn = document.getElementById("upgradeWizardBtn");
  if (upgradeBtn) upgradeBtn.textContent = `Upgrade ${name}`;
  const upgradeTitle = document.getElementById("upgradeWizardTitle");
  if (upgradeTitle) upgradeTitle.textContent = `Upgrade ${name}`;
  const upgradeRestart = document.getElementById("upgradeRestartBtn");
  if (upgradeRestart) upgradeRestart.textContent = `Restart ${name}`;
  const apiKeyTitle = document.getElementById("apiKeyModalTitle");
  if (apiKeyTitle) apiKeyTitle.textContent = `${name} API key`;
  const profileTitle = document.getElementById("profileModalTitle");
  if (profileTitle) profileTitle.textContent = `Help ${name} learn about you`;
}
window.applyBranding = applyBranding;
let chatAbortController = null;
let chatStopRequested = false;
let activeStreamText = "";
let activeChatRequestId = "";

const branchSelect = document.getElementById("branchSelect");
const newBranchBtn = document.getElementById("newBranchBtn");
const trimBranchesBtn = document.getElementById("trimBranchesBtn");
const clearMainBranchBtn = document.getElementById("clearMainBranchBtn");
const branchTrimModal = document.getElementById("branchTrimModal");
const branchTrimList = document.getElementById("branchTrimList");
const branchTrimConfirmBtn = document.getElementById("branchTrimConfirmBtn");
const branchTrimCancelBtn = document.getElementById("branchTrimCancelBtn");

const jobCenterBtn = document.getElementById("jobCenterBtn");
const jobCenterModal = document.getElementById("jobCenterModal");
const jobCenterList = document.getElementById("jobCenterList");
const jobCenterSummary = document.getElementById("jobCenterSummary");
const jobCenterRefreshBtn = document.getElementById("jobCenterRefreshBtn");
const jobCenterCloseBtn = document.getElementById("jobCenterCloseBtn");

// readStreamChunk / STREAM_IDLE_MS → chat_send.js
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
window.escapeHtml = escapeHtml;
window.formatMessage = formatMessage;

function formatMessage(text) {
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
  html = html.replace(/\n/g, "<br>");
  return html;
}

function messagePlainText(bodyEl) {
  if (!bodyEl) return "";
  return (bodyEl.innerText || bodyEl.textContent || "").trim();
}

async function copyTextToClipboard(text) {
  const value = (text || "").trim();
  if (!value) return false;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (_) {}
  try {
    const ta = document.createElement("textarea");
    ta.value = value;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  } catch (_) {
    return false;
  }
}

function isTextEntryElement(el) {
  if (!el) return false;
  const tag = el.tagName;
  if (tag === "TEXTAREA" || tag === "INPUT") return true;
  return Boolean(el.isContentEditable);
}

function syncMessageRawText(body, text) {
  if (!body) return;
  const t = (text || "").trim();
  if (t) body.dataset.rawText = t;
}

function createCopyButton(body) {
  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "ghost-btn small copy-btn";
  copyBtn.title = "Copy message";
  copyBtn.textContent = "Copy";
  copyBtn.onclick = async () => {
    const text = body.dataset.rawText || messagePlainText(body);
    const ok = await copyTextToClipboard(text);
    if (ok) {
      copyBtn.classList.add("copied");
      copyBtn.textContent = "Copied";
      if (statusText) statusText.textContent = "Message copied";
      setTimeout(() => {
        copyBtn.classList.remove("copied");
        copyBtn.textContent = "Copy";
      }, 1600);
    } else if (statusText) {
      statusText.textContent = "Select text and press Ctrl+C";
    }
  };
  return copyBtn;
}

function ensureMessageCopyAction(messageDiv, body) {
  if (!messageDiv || !body) return;
  const bubble = messageDiv.querySelector?.(".bubble") || messageDiv;
  if (!bubble || bubble.querySelector(".copy-btn")) return;
  let actions = bubble.querySelector(".message-actions");
  if (!actions) {
    actions = document.createElement("div");
    actions.className = "message-actions";
    bubble.appendChild(actions);
  }
  actions.prepend(createCopyButton(body));
}

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

clearBtn?.addEventListener("click", async () => {
  try {
    const f = new FormData();
    f.append("message", "clear");
    if (_activeBranchId) f.append("branch_id", _activeBranchId);
    const res = await fetch("/api/chat", { method: "POST", body: f });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || data.detail || `Clear failed (${res.status})`);
    messagesEl.innerHTML = "";
    window.addMessage?.("assistant", "Fresh start. What would you like to do?");
    window.showAriaToast?.("Conversation cleared", "ok", 2500);
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not clear conversation", "err", 5000);
  }
});


readAloudBtn?.addEventListener("click", async () => {
  if (!lastAssistantText) {
    window.showAriaToast?.("Nothing to read yet — wait for an assistant reply", "info", 3000);
    return;
  }
  readAloudBtn.disabled = true;
  statusText.textContent = "Speaking on Sound Blaster…";
  try {
    const form = new FormData();
    form.append("text", lastAssistantText.replace(/[*`#]/g, "").slice(0, 4000));
    const res = await fetch("/api/audio/speak", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      window.showError(data.message || "Could not play audio.");
      window.showAriaToast?.(data.message || "Could not play audio", "err", 5000);
    } else {
      statusText.textContent = "Ready · Sound Blaster";
    }
  } catch (e) {
    window.showError(`Audio playback failed: ${e.message}`);
    window.showAriaToast?.(`Audio playback failed: ${e.message}`, "err", 5000);
  } finally {
    readAloudBtn.disabled = false;
  }
});

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const useBrowserMicStt = () => localStorage.getItem("jarvis_chat_server_whisper") === "0";
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    messageInput.value = transcript;
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
  } else {
    micBtn.title = micBtn.title || "Hold for server Whisper (see Settings)";
  }
} else {
  micBtn.title = "Voice not supported in this browser";
  micBtn.disabled = true;
}

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
  get dataChips() { return dataChips; },
  isVisionAttachment,
  isDataAttachment,
  isTextEntryElement,
  escapeHtml,
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


async function loadEditorContext() {
  if (mediaWorkActive()) return null;
  if (!editorContextPill && !editorContextCard) return null;
  try {
    const res = await fetch("/api/editor/context");
    if (!res.ok) return null;
    const data = await res.json();
    const ctx = data.context || {};
    const file = ctx.relative_file || "";
    const fresh = Boolean(data.fresh && file);
    const selLines = ctx.selection_lines || 0;
    const selNote = ctx.has_selection ? ` · ${selLines} line${selLines === 1 ? "" : "s"} selected` : "";
    const label = file ? `${file}${selNote}` : "";

    if (editorContextPill && editorPillText) {
      if (file) {
        editorContextPill.classList.remove("hidden");
        editorContextPill.classList.toggle("live", fresh);
        editorContextPill.classList.toggle("stale", !fresh);
        editorPillText.textContent = fresh ? `Cursor · ${file.split("/").pop()}${selNote}` : `Cursor (stale) · ${file.split("/").pop()}`;
        editorContextPill.title = fresh
          ? `Live from Cursor: ${label}`
          : `Stale — focus Cursor or run ARIA: Push Editor Context Now`;
      } else {
        editorContextPill.classList.remove("hidden");
        editorContextPill.classList.remove("live");
        editorContextPill.classList.add("stale");
        editorPillText.textContent = "Cursor · not synced";
        editorContextPill.title =
          "Install: ./scripts/install-cursor-extension.sh — then Reload Window in Cursor";
      }
    }

    if (editorContextCard && editorContextLabel) {
      if (file) {
        editorContextCard.classList.remove("hidden");
        editorContextCard.classList.toggle("live", fresh);
        editorContextLabel.textContent = fresh ? `Cursor · ${label}` : `Cursor (stale) · ${file}`;
        editorContextCard.title = editorContextPill?.title || label;
      } else {
        editorContextCard.classList.remove("hidden");
        editorContextCard.classList.remove("live");
        editorContextLabel.textContent = "Cursor: install extension";
        editorContextCard.title =
          "Run ./scripts/install-cursor-extension.sh then Reload Window in Cursor";
      }
    }

    if (fresh && file !== _lastEditorFile) {
      _lastEditorFile = file;
      refreshEditorSuggestions(file, ctx.has_selection);
    }
    return { fresh, file, ctx };
  } catch (_) {
    return null;
  }
}

window.loadEditorContext = loadEditorContext;

let editorContextPollTimer = null;
function scheduleEditorContextPoll() {
  if (editorContextPollTimer) clearTimeout(editorContextPollTimer);
  const delay = mediaWorkActive()
    ? (isNativeApp() ? 45000 : 20000)
    : (document.hidden ? 12000 : 4000);
  editorContextPollTimer = setTimeout(async () => {
    if (!mediaWorkActive()) await loadEditorContext();
    scheduleEditorContextPoll();
  }, delay);
}

function refreshEditorSuggestions(file, hasSelection) {
  if (!suggestionsEl) return;
  const base = [
    "What can you do?",
    hasSelection ? "fix selection" : `fix ${file}`,
    hasSelection ? "explain selection" : `diagnose ${file}`,
    `run tests for ${file}`,
    `debug until tests pass for ${file}`,
  ];
  suggestionsEl.innerHTML = "";
  base.forEach((text) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "suggestion-chip";
    chip.textContent = text;
    chip.onclick = () => {
      messageInput.value = text;
      messageInput.focus();
    };
    suggestionsEl.appendChild(chip);
  });
}

// coding quick buttons → coding_quick.js (window.sendQuickCodingMessage)

async function loadSuggestions() {
  try {
    const res = await fetch("/api/suggestions");
    const data = await res.json();
    visionChips = data.vision_chips || [];
    dataChips = data.data_chips || [];
    suggestionsEl.innerHTML = "";
    data.suggestions.filter(Boolean).forEach((s) => {
      const chip = document.createElement("button");
      chip.className = "suggestion-chip";
      chip.textContent = s;
      chip.onclick = () => { messageInput.value = String(s); messageInput.focus(); };
      suggestionsEl.appendChild(chip);
    });
    if (isDataAttachment(pendingFile)) window.refreshDataChips?.();
    else if (pendingFile || pendingFile2) window.refreshVisionChips?.();
    const ed = await loadEditorContext();
    if (ed?.fresh && ed.file) refreshEditorSuggestions(ed.file, ed.ctx?.has_selection);
  } catch (err) {
    window.showAriaToast?.(err?.message || "Could not load suggestions", "err", 4000);
  }
}

// Health/live polling, GPU/audio status and service rendering → modules/health.mjs

// image engine → image_engine.js


function switchToView(view) {
  const VIEW_PANELS = [
    "chatView", "dashboardView", "workstationView", "plannerView", "calendarView", "flytyingView", "projectsView",
    "makerView", "browserView", "securityView", "presenceView", "auditView", "voiceView", "audioView", "journalView",
    "memoryView", "galleryView", "videoView", "memeView", "documentsView", "actionsView",
  ];
  document.querySelectorAll(".view-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.view === view);
  });
  const targetId = `${view}View`;
  VIEW_PANELS.forEach((id) => {
    document.getElementById(id)?.classList.toggle("hidden", id !== targetId);
  });
  if (view === "dashboard" && window.initDashboard) window.initDashboard();
  if (view === "workstation" && window.initWorkstation) window.initWorkstation();
  if (view === "planner" && window.initPlanner) window.initPlanner();
  if (view === "calendar" && window.initCalendar) window.initCalendar();
  if (view === "flytying" && window.initFlytying) window.initFlytying();
  if (view === "projects" && window.initProjects) window.initProjects();
  if (view === "maker" && window.initMakerLab) window.initMakerLab();
  if (view === "browser" && window.initBrowserPanel) window.initBrowserPanel();
  if (view !== "browser" && window.stopBrowserPanelPoll) window.stopBrowserPanelPoll();
  if (view === "security" && window.initSecurity) { window.initSecurity(); window.refreshToolsSidebar?.(); }
  if (view === "presence" && window.initPresence) window.initPresence();
  if (view === "audit" && window.initAudit) window.initAudit();
  if (view === "voice" && window.initVoiceTab) window.initVoiceTab();
  if (view === "audio" && window.initAudio) window.initAudio();
  if (view === "journal" && window.initJournal) window.initJournal();
  if (view === "memory") window.loadMemoryBrowser?.();
  if (view === "gallery") window.loadGallery?.();
  if (view === "video" && typeof loadVideoGallery === "function") loadVideoGallery();
  if (view === "meme" && typeof loadMemeGallery === "function") loadMemeGallery();
  if (view === "actions") window.loadActions?.(document.getElementById("actionsFilter")?.value);
  if (view === "documents") { window.initDocumentsTab?.(); window.loadDocumentsTab?.(); }
  document.querySelector(`.view-tab[data-view="${view}"]`)?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

// sidebar chrome → sidebar_chrome.js (window.resetSidebarLayout)


window.switchToView = switchToView;
// window.addMessage → chat_messages.js
window.createCopyButton = createCopyButton;
window.ensureMessageCopyAction = ensureMessageCopyAction;
window.scrollMessageIntoView = scrollMessageIntoView;
window.applyAssistantMeta = applyAssistantMeta;
window.syncMessageRawText = syncMessageRawText;



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
  if (!document.hidden) scheduleEditorContextPoll();
});
// Define before startup_overlay.js invokes waitForServices → ariaPostStartup
window.ariaPostStartup = function ariaPostStartup() {
  try { window.initAriaModalChrome?.(); } catch (_) {}
  loadSuggestions();
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
      switchToView(hashView);
    }
    document.getElementById("presetQualityBtn")?.classList.add("active");
    window.startHealthMonitoring?.();
    setInterval(() => {
      if (!mediaWorkActive()) window.loadCodingPanel?.();
    }, 90000);
    scheduleEditorContextPoll();
  });
};

// coding / LSP → coding_panel.js (window.loadCodingPanel / runLspAction)

// View switching
document.querySelectorAll(".view-tab").forEach((tab) => {
  tab.addEventListener("click", () => switchToView(tab.dataset.view));
});

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

document.getElementById("exportChatBtn")?.addEventListener("click", () => {
  const params = new URLSearchParams();
  if (_activeBranchId) params.set("branch_id", _activeBranchId);
  params.set("memory", "1");
  window.open(`/api/chat/export?${params}`, "_blank");
});

document.getElementById("exportChatPdfBtn")?.addEventListener("click", () => {
  const q = _activeBranchId ? `?branch_id=${encodeURIComponent(_activeBranchId)}` : "";
  window.open(`/api/chat/export/pdf${q}`, "_blank");
});

document.getElementById("backupDataBtn")?.addEventListener("click", async () => {
  const btn = document.getElementById("backupDataBtn");
  if (btn) btn.disabled = true;
  window.showAriaToast?.("Backup starting…", "info");
  try {
    const res = await fetch("/api/admin/backup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ async: true }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      window.showAriaToast?.(data.message || "Backup failed", "err");
      return;
    }
    if (data.pending && data.job_id) {
      window.showAriaToast?.(`Backup queued (${data.job_id.slice(0, 8)}…)`, "ok");
      window.jarvisJobs?.refreshJobCenter?.();
      document.getElementById("jobCenterBtn")?.classList.add("pulse");
    } else {
      window.showAriaToast?.(data.message || "Backup complete", "ok");
    }
  } catch (e) {
    window.showAriaToast?.(String(e.message || e || "Backup failed"), "err");
  } finally {
    if (btn) btn.disabled = false;
  }
});

// theme → theme.js

// profile / personality / actions clear / debug → profile_controls.js

// notify → notify.js (window.jarvisNotify)

document.addEventListener("keydown", (e) => {
  const inTextField = isTextEntryElement(e.target);
  if (e.ctrlKey && e.key === "Enter") {
    if (inTextField && e.target !== messageInput) return;
    e.preventDefault();
    window.sendMessage?.(messageInput.value);
  }
  if (e.ctrlKey && e.key === "l" && !inTextField) {
    e.preventDefault();
    clearBtn.click();
  }
});

window.resizeMessageInput = resizeMessageInput;

// showGeneratedImage / showAudioPlayer / jarvisSendToChat → chat_media.js

// debug bundle → profile_controls.js

// personality/branches → chat_branches.js

