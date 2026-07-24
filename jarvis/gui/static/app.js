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
const getStoredApiKey = (...a) => window.getStoredApiKey?.(...a) ?? (sessionStorage.getItem("jarvis_api_key") || "");
const apiAuthUrl = (...a) => window.apiAuthUrl?.(...a);
const isSameMachineHost = (...a) => window.isSameMachineHost?.(...a) ?? (location.hostname === "localhost" || location.hostname === "127.0.0.1");
const mediaNeedsApiKey = (...a) => window.mediaNeedsApiKey?.(...a) ?? false;
const fetchMediaBlobUrl = (...a) => window.fetchMediaBlobUrl?.(...a);
const resolveVideoUrl = (...a) => window.resolveVideoUrl?.(...a);
const resolveVideoPlaybackUrl = (...a) => window.resolveVideoPlaybackUrl?.(...a);
const attachMediaLoadError = (...a) => window.attachMediaLoadError?.(...a);

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
const uncensoredToggle = document.getElementById("uncensoredToggle");
const modeLabel = document.getElementById("modeLabel");
const appTitle = document.getElementById("appTitle");
const appTagline = document.getElementById("appTagline");
const hudEnv = document.getElementById("hudEnv");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const progressFill = progressBar?.querySelector(".progress-fill");
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
let progressTimer = null;
let progressStart = 0;
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

const JARVIS_UI_VERSION = document.querySelector('meta[name="jarvis-ui-version"]')?.content || "5.15.1";

const STREAM_IDLE_MS = 180000;

function readStreamChunk(reader, idleMs = STREAM_IDLE_MS) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`${ariaName()} took too long to respond. Try again or check that Ollama is running.`));
    }, idleMs);
    reader.read().then(
      (result) => { clearTimeout(timer); resolve(result); },
      (err) => { clearTimeout(timer); reject(err); },
    );
  });
}
const startupOverlay = document.getElementById("startupOverlay");
const startupStatus = document.getElementById("startupStatus");
const startupLog = document.getElementById("startupLog");
const servicesPanel = document.getElementById("servicesPanel");

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

function resolveImageUrl(imgPath, { thumb = false, thumbMax = CHAT_IMAGE_THUMB_MAX } = {}) {
  if (!imgPath) return "";
  const file = imgPath.split(/[/\\]/).pop();
  let url;
  if (/\/uploads[/\\]/i.test(imgPath)) {
    url = `/api/uploads/${encodeURIComponent(file)}`;
  } else if (/\/generated[/\\]memes[/\\]/i.test(imgPath)) {
    url = `/api/meme-gallery/${encodeURIComponent(file)}`;
  } else if (/\/generated[/\\]/i.test(imgPath)) {
    const base = `/api/gallery/${encodeURIComponent(file)}`;
    url = thumb ? `${base}?max=${thumbMax}` : base;
  } else {
    url = `/api/audio/file?path=${encodeURIComponent(imgPath)}`;
  }
  return apiAuthUrl(url);
}

function galleryViewVisible() {
  const el = document.getElementById("galleryView");
  return el && !el.classList.contains("hidden");
}
window.galleryViewVisible = galleryViewVisible;
window.resolveImageUrl = resolveImageUrl;

async function appendImageFigure(container, imgPath, imageName, caption, { thumb = true } = {}) {
  if (!container || !imgPath || !/\.(png|jpe?g|webp|gif|bmp)$/i.test(imgPath)) return;
  const file = imageName || imgPath.split(/[/\\]/).pop();
  const url = resolveImageUrl(imgPath, { thumb });
  const fullUrl = resolveImageUrl(imgPath, { thumb: false });
  const label = caption || file;
  const pathAttr = escapeHtml(imgPath);
  const fig = document.createElement("figure");
  fig.className = "gen-image";
  fig.dataset.imagePath = imgPath;
  const img = document.createElement("img");
  img.alt = file;
  img.loading = "lazy";
  img.decoding = "async";
  img.className = "clickable-image";
  img.dataset.imagePath = imgPath;
  img.title = "Click to view and edit";
  img.dataset.fullSrc = fullUrl;
  const cap = document.createElement("figcaption");
  cap.textContent = label;
  fig.appendChild(img);
  fig.appendChild(cap);
  container.appendChild(fig);
  attachMediaLoadError(img, "image");
  if (!mediaNeedsApiKey() || isNativeApp()) {
    img.src = url;
    bindClickableImages(container);
    return;
  }
  const key = getStoredApiKey();
  if (key) {
    try {
      const res = await fetch(fullUrl);
      if (res.ok) {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        img.dataset.fullSrc = blobUrl;
        if (thumb && url !== fullUrl) {
          const thumbRes = await fetch(url);
          img.src = thumbRes.ok ? URL.createObjectURL(await thumbRes.blob()) : blobUrl;
        } else {
          img.src = blobUrl;
        }
      } else {
        img.src = url;
      }
    } catch {
      img.src = url;
    }
  } else {
    img.src = url;
  }
  bindClickableImages(container);
}

function appendImageReveal(container, imgPath, imageName, caption) {
  if (!container || !imgPath) return;
  const file = imageName || imgPath.split(/[/\\]/).pop();
  const label = caption || file;
  const fig = document.createElement("figure");
  fig.className = "gen-image gen-image-reveal";
  fig.dataset.imagePath = imgPath;
  fig.innerHTML =
    `<button type="button" class="gen-image-reveal-btn">Show image · ${escapeHtml(file)}</button>`
    + `<figcaption>${escapeHtml(label)}</figcaption>`;
  fig.querySelector(".gen-image-reveal-btn")?.addEventListener("click", () => {
    const cap = fig.querySelector("figcaption")?.textContent || file;
    fig.remove();
    appendImageFigure(container, imgPath, file, cap);
  });
  container.appendChild(fig);
}

function bindClickableImages(container) {
  window.bindClickableImages = bindClickableImages;
  if (!container) return;
  container.querySelectorAll(".gen-image img, .gallery-item > img").forEach((img) => {
    if (img.dataset.lightboxBound) return;
    img.dataset.lightboxBound = "1";
    img.classList.add("clickable-image");
    if (!img.title) img.title = "Click to view and edit";
    img.addEventListener("click", (e) => {
      e.stopPropagation();
      const figure = img.closest(".gen-image");
      const path = img.dataset.imagePath || figure?.dataset.imagePath || "";
      const full = img.dataset.fullSrc || img.src;
      window.openImageLightbox?.(full, img.alt || "", path, img.src);
    });
  });
}

// media lightbox / queueImageEdit / inpaint → media_lightbox.js

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

function appendGeneratedImage(container, imgPath, imageName) {
  const cap = imageName || imgPath.split(/[/\\]/).pop();
  if (isNativeApp()) appendImageReveal(container, imgPath, imageName, cap);
  else appendImageFigure(container, imgPath, imageName, cap);
}

function buildVisionMessageHtml(text) {
  return formatMessage((text || "").trim() || "Image analysis complete.");
}

function buildImageMessageHtml(data, text) {
  let intro = (text || data.message || "").trim();
  const prompt = (data.enhanced_prompt || "").trim();
  let negative = "";

  const negMatch = intro.match(/\n\n\*\*Avoiding:\*\*\s*([\s\S]*)$/);
  if (negMatch) {
    negative = negMatch[1].trim();
    intro = intro.slice(0, negMatch.index).trim();
  }
  intro = intro.replace(/\n\n\*\*Prompt sent to[^*]+:\*\*\n[\s\S]*$/, "").trim();
  if (!intro) intro = "Here's your image.";

  let html = formatMessage(intro);
  if (prompt) {
    html += `<details class="prompt-details" open><summary>Prompt sent to model</summary><pre class="prompt-text">${escapeHtml(prompt)}</pre></details>`;
  }
  if (negative) {
    html += `<details class="prompt-details"><summary>Negative prompt</summary><pre class="prompt-text">${escapeHtml(negative)}</pre></details>`;
  }
  return html;
}

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

async function appendAuthenticatedVideo(container, videoPath, videoName) {
  if (!container || !videoPath) return;
  const label = videoName || videoPath.split(/[/\\]/).pop();
  const fig = document.createElement("figure");
  fig.className = "gen-video";
  const video = document.createElement("video");
  video.controls = true;
  video.preload = "metadata";
  video.className = "chat-video-player";
  attachMediaLoadError(video, "video");
  const cap = document.createElement("figcaption");
  cap.textContent = label;
  fig.appendChild(video);
  fig.appendChild(cap);
  container.appendChild(fig);

  const playback = await resolveVideoPlaybackUrl(videoPath);
  if (!playback.ok && playback.needsKey) {
    const warn = document.createElement("p");
    warn.className = "media-load-warn warn small";
    warn.innerHTML = 'Video needs your API key — <button type="button" class="ghost-btn small media-key-btn">Enter API key</button>';
    warn.querySelector(".media-key-btn")?.addEventListener("click", () => window.showApiKeyModal?.(""));
    fig.appendChild(warn);
    return;
  }
  if (playback.url) video.src = playback.url;
  bindClickableVideos(fig);
}

function appendGeneratedVideo(container, videoPath, videoName) {
  void appendAuthenticatedVideo(container, videoPath, videoName);
}

function buildVideoMessageHtml(data, text) {
  let intro = (text || data.message || "").trim();
  const prompt = (data.enhanced_prompt || "").trim();
  intro = intro.replace(/\n\n\*\*Keyframe prompt:\*\*\n[\s\S]*$/, "").trim();
  if (!intro) intro = "Here's your video.";
  let html = formatMessage(intro);
  if (prompt) {
    html += `<details class="prompt-details" open><summary>Keyframe prompt</summary><pre class="prompt-text">${escapeHtml(prompt)}</pre></details>`;
  }
  return html;
}

function isVisionAttachment(file) {
  return Boolean(file && (/^image\//i.test(file.type) || /^video\//i.test(file.type)));
}

function isDataAttachment(file) {
  return Boolean(
    file && (/\.(csv|json|xlsx|xlsm|db|sqlite|sqlite3)$/i.test(file.name)
      || file.type === "text/csv" || file.type === "application/json"),
  );
}

function buildDataTableHtml(preview) {
  if (!preview?.columns?.length) return "";
  const cols = preview.columns;
  const rows = preview.rows || [];
  const streamNote = preview.streaming ? " · streaming (preview)" : preview.truncated ? " · truncated" : "";
  let html = `<div class="data-preview"><p class="data-preview-meta">📊 ${escapeHtml(preview.name || "dataset")} · ${preview.row_count ?? "?"} rows${streamNote}</p><div class="data-table-wrap"><table class="data-table"><thead><tr>`;
  cols.forEach((c) => { html += `<th>${escapeHtml(String(c))}</th>`; });
  html += "</tr></thead><tbody>";
  rows.forEach((r) => {
    html += "<tr>";
    cols.forEach((c) => { html += `<td>${escapeHtml(String(r[c] ?? ""))}</td>`; });
    html += "</tr>";
  });
  html += "</tbody></table></div></div>";
  return html;
}

function progressLabel(text) {
  if (isVideoRequest(text)) return "Rendering keyframe & motion clip…";
  if (isImageRequest(text)) return "Understanding scene & generating…";
  if (pendingFile2) return "Comparing images…";
  if (isVisionAttachment(pendingFile)) return "Analyzing image…";
  return "Thinking…";
}

// Coding proposals/diff/apply → coding_proposals.js

function addMessage(role, content, meta = {}, options = {}) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  if (meta.type) div.dataset.msgType = meta.type;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "J";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (meta.type === "briefing") bubble.classList.add("briefing-bubble");

  const showTag = meta.module && meta.module !== "general" && meta.type !== "info";
  if (showTag && role === "assistant") {
    const tag = document.createElement("div");
    tag.className = `module-tag ${meta.module}`;
    tag.textContent = meta.module;
    bubble.appendChild(tag);
  }

  const body = document.createElement("div");
  body.className = "msg-body";
  body.innerHTML = formatMessage(content);
  if (content) body.dataset.rawText = content;
  bubble.appendChild(body);

  const mountExtras = () => window.attachProposalExtras?.(bubble, meta, div);
  if (meta.proposal_id && isNativeApp()) {
    requestAnimationFrame(() => requestAnimationFrame(mountExtras));
  } else {
    mountExtras();
  }

  if (meta.type === "clarification" && meta.choices) {
    const chips = document.createElement("div");
    chips.className = "clarification-chips";
    meta.choices.forEach((choice, i) => {
      const chip = document.createElement("button");
      chip.className = "suggestion-chip";
      chip.textContent = choice;
      chip.onclick = () => sendMessage(String(i + 1));
      chips.appendChild(chip);
    });
    bubble.appendChild(chips);
  }

  div.append(avatar, bubble);

  const msgIndex = messagesEl.querySelectorAll(".message").length;
  div.dataset.msgIndex = String(msgIndex);
  if (role === "user" || role === "assistant") {
    const actions = document.createElement("div");
    actions.className = "message-actions";
    const copyBtn = createCopyButton(body);
    actions.appendChild(copyBtn);
    const forkBtn = document.createElement("button");
    forkBtn.type = "button";
    forkBtn.className = "ghost-btn small fork-btn";
    forkBtn.title = "Fork branch from this message";
    forkBtn.textContent = "⎇ Fork";
    forkBtn.onclick = () => forkBranchFromIndex(msgIndex);
    actions.appendChild(forkBtn);
    bubble.appendChild(actions);
  }

  messagesEl.appendChild(div);
  if (!options.skipScroll) messagesEl.scrollTop = messagesEl.scrollHeight;

  if (role === "assistant") lastAssistantText = content;
  return { div, body };
}

function addTyping() {
  const div = document.createElement("div");
  div.className = "message assistant typing-msg";
  div.innerHTML = `<div class="avatar">J</div><div class="bubble"><div class="msg-body"><div class="typing"><span></span><span></span><span></span></div></div></div>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

// shouldShowUndo / applyProposal / undoLastApply → coding_proposals.js

// upgrade wizard → upgrade_wizard.js

async function parseJsonResponse(res) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(res.ok ? "Invalid server response" : `Server error (${res.status}): ${text.slice(0, 200)}`);
  }
}

function showError(msg) {
  addMessage("assistant", msg, { type: "info" });
  statusText.textContent = "Error";
}

function showProgress(label = "Thinking…") {
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
  clearInterval(progressTimer);
  progressTimer = null;
  if (progressBar) progressBar.classList.add("hidden");
  if (progressFill) progressFill.style.width = "0%";
}

function setChatBusy(busy) {
  chatRequestActive = busy;
  sendBtn.disabled = busy;
  sendBtn.classList.toggle("hidden", busy);
  stopChatBtn?.classList.toggle("hidden", !busy);
  if (!busy) {
    chatAbortController = null;
    chatStopRequested = false;
    activeStreamText = "";
  }
}

function stopChat() {
  chatStopRequested = true;
  if (activeChatRequestId) {
    const fd = new FormData();
    fd.append("request_id", activeChatRequestId);
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
  chatAbortController?.abort();
  if (statusText) statusText.textContent = "Stopping…";
}

stopChatBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  stopChat();
});

function finishSendUi() {
  hideProgress();
  setChatBusy(false);
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

function updateProgressStatus(message) {
  if (progressText) progressText.textContent = message;
  statusText.textContent = message;
}

function isStreamableAttachment(file) {
  if (!file) return false;
  if (file.size > 500000) return false;
  return /\.(txt|md|py|json|csv|log|yaml|yml|toml|xml|html|js|ts|tsx|jsx|sh|rs|go)$/i.test(file.name);
}

function showChatWarnings(warnings) {
  if (!warnings?.length) return;
  const lastMsg = document.querySelector(".message.assistant:last-child .bubble");
  if (!lastMsg || lastMsg.querySelector(".chat-warnings")) return;
  const el = document.createElement("div");
  el.className = "chat-warnings muted";
  el.textContent = warnings.join(" ");
  lastMsg.appendChild(el);
}

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
      showError(data.message || "Could not fork branch.");
      return;
    }
    _activeBranchId = data.branch_id;
    await window.loadBranches?.();
    await window.reloadBranchMessages?.();
    statusText.textContent = `Forked branch: ${name}`;
  } catch (e) {
    showError(String(e.message || e));
  }
}

async function sendMessage(text, forceNoStream = false, options = {}) {
  if (!text.trim() && !pendingFile && !pendingFile2) return;

  if (compareMode && pendingFile && !pendingFile2) {
    showError("Compare needs **two images**. Click **+ Add image 2** in the preview, or click **Compare** and select both files at once.");
    return;
  }
  if (pendingFile2 && !pendingFile) {
    pendingFile = pendingFile2;
    pendingFile2 = null;
  }

  const skipUserBubble = Boolean(options.skipUserBubble);

  let displayText = text.trim();
  if (pendingFile) {
    displayText = displayText
      ? `${displayText}\n📎 ${pendingFile.name}`
      : `📎 ${pendingFile.name}`;
  }
  if (pendingFile2) {
    displayText = displayText
      ? `${displayText}\n📎 ${pendingFile2.name}`
      : `📎 ${pendingFile2.name}`;
  }
  if (!skipUserBubble) {
    addMessage("user", displayText || "(attachment)");
  }

  chatStopRequested = false;
  activeStreamText = "";
  activeChatRequestId = crypto.randomUUID?.() || `req-${Date.now()}`;
  chatAbortController = new AbortController();
  setChatBusy(true);
  showProgress(progressLabel(text));

  if (isVideoRequest(text)) {
    const proceed = (await window.vramPreflight?.("generate_video")) !== false;
    if (!proceed) {
      setChatBusy(false);
      hideProgress();
      return;
    }
  } else if (isImageRequest(text)) {
    const proceed = (await window.vramPreflight?.("generate_image")) !== false;
    if (!proceed) {
      setChatBusy(false);
      hideProgress();
      return;
    }
  }

  const form = new FormData();
  form.append("request_id", activeChatRequestId);
  const defaultMsg = pendingFile2
    ? "Compare these two images. Describe similarities and differences."
    : isDataAttachment(pendingFile)
      ? "Load and summarize this data."
      : "Please analyze the attached file.";
  form.append("message", text.trim() || defaultMsg);
  if (pendingFile) form.append("file", pendingFile);
  if (pendingFile2) form.append("file2", pendingFile2);
  if (pendingCrop) form.append("crop", JSON.stringify(pendingCrop));
  if (pendingVideoSecond.trim()) form.append("video_second", pendingVideoSecond.trim());
  if (pendingPdfPage.trim()) form.append("pdf_page", pendingPdfPage.trim());
  if (_activeBranchId) form.append("branch_id", _activeBranchId);
  if (window.jarvisPreferredModule) form.append("preferred_module", window.jarvisPreferredModule);

  const trimmed = text.trim();
  const isInstant = /^(hi|hello|hey|what can you|what (services|models|do you)|help|capabilities)/i.test(trimmed)
    || /^(undo|apply)(\s+(it|that|last|the changes?|apply))?\s*$/i.test(trimmed);
  const isCodingFix = /\b(?:fix|repair|debug|improve|refactor|clean up)\b/i.test(text) && /[^\s`'"]+\.py/.test(text);
  const isCodingCreate = /\b(with tests?|pytest)\b/i.test(text)
    && /\b(implement|create|write|make|build|add)\b/i.test(text);
  const isCodingAgent = /\b(implement|build|add feature|debug until|refactor across)\b/i.test(text)
    || isCodingFix || isCodingCreate;
  const isWebSearch = /\b(search (the )?web|web search|look up online|google)\b/i.test(trimmed);
  const hasVisionAttach = isVisionAttachment(pendingFile) || isVisionAttachment(pendingFile2);
  const streamableFile = isStreamableAttachment(pendingFile);
  const wantsStream = isImageRequest(text) || isVideoRequest(text) || isCodingAgent || hasVisionAttach || (
    !forceNoStream && (!pendingFile || streamableFile) && !isInstant && text.length > 0
    && !/^(run|apply|undo|review|find|load|transcribe|generate)/i.test(trimmed)
    && (!/^search/i.test(trimmed) || isWebSearch)
  );
  const isLikelyChat = !forceNoStream && wantsStream && !isImageRequest(text) && !isVideoRequest(text);

  const typing = addTyping();
  const fetchOpts = { method: "POST", body: form, signal: chatAbortController.signal };

  try {
    if (useStreaming && wantsStream) {
      form.append("stream", "true");
      if (isNativeApp()) form.append("lite_ui", "true");
      const body = typing.querySelector(".msg-body");
      body.innerHTML = isVideoRequest(text)
        ? `<p class="status-hint">Starting video generation…</p>`
        : isImageRequest(text)
          ? `<p class="status-hint">Starting image generation…</p>`
          : "";
      let full = "";
      let gotDone = false;

      const res = await fetch("/api/chat", fetchOpts);
      if (!res.ok) {
        const err = await parseJsonResponse(res);
        throw new Error(err.message || `Request failed (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let streamFinished = false;

      try {
        while (!streamFinished) {
          if (chatStopRequested) {
            streamFinished = true;
            break;
          }
          const { done, value } = await readStreamChunk(reader);
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            let event;
            try { event = JSON.parse(line.slice(6)); } catch { continue; }
            if (event.type === "status") {
              updateProgressStatus(event.message || "Processing…");
              if (body) {
                body.innerHTML = `<p class="status-hint">${escapeHtml(event.message || "Processing…")}</p>`;
                messagesEl.scrollTop = messagesEl.scrollHeight;
              }
            } else if (event.type === "agent_step") {
              const label = `${event.action || "step"}: ${event.detail || ""}`;
              updateProgressStatus(label);
              if (body && !isNativeApp()) {
                const steps = body.querySelector(".agent-steps") || document.createElement("div");
                steps.className = "agent-steps";
                if (!steps.parentElement) body.appendChild(steps);
                const line = document.createElement("div");
                line.className = "agent-step" + (event.ok === false ? " fail" : "");
                line.textContent = `${event.step || "•"}. ${label}`;
                steps.appendChild(line);
                messagesEl.scrollTop = messagesEl.scrollHeight;
              }
            } else if (event.type === "token") {
              updateProgressStatus("Generating…");
              full += event.content;
              activeStreamText = full;
              body.innerHTML = formatMessage(full);
              syncMessageRawText(body, full);
              messagesEl.scrollTop = messagesEl.scrollHeight;
            } else if (event.type === "done" || (event.ok && event.image_path)) {
              gotDone = true;
              streamFinished = true;
              typing.classList.remove("typing-msg");
              if (!event.ok && !full && !event.image_path) {
                typing.remove();
                showError(event.message || "Request failed.");
                break;
              }
              const streamed = Boolean(full);
              const isPendingMediaJob = Boolean(
                event.job_id
                && (event.type === "media_job" || event.result_type === "media_job" || event.pending),
              );
              if (!streamed && !isPendingMediaJob) typing.remove();
              if (isPendingMediaJob) typing.classList.remove("typing-msg");
              lastAssistantText = full || event.message;
              const doneOpts = isPendingMediaJob
                ? { targetBody: typing.querySelector(".msg-body"), pendingMediaJob: true }
                : {};
              try {
                handleDone(event, full || event.message, streamed, doneOpts);
              } catch (err) {
                console.error("handleDone failed", err);
                showError(`Could not display response: ${err.message || err}`);
              }
              finishSendUi();
              break;
            }
          }
        }
      } finally {
        try { await reader.cancel(); } catch (_) {}
      }

      if (chatStopRequested) {
        typing.remove();
        if (activeStreamText.trim()) {
          addMessage("assistant", `${activeStreamText.trim()}\n\n*(stopped)*`, { type: "info" });
        }
        statusText.textContent = "Stopped";
      } else if (!gotDone) {
        typing.remove();
        if (isVideoRequest(text)) {
          showError("Video generation did not finish — check the Video tab or try again.");
        } else if (isImageRequest(text)) {
          showError("Image generation did not finish — check the Gallery tab or try again.");
        } else if (isCodingAgent) {
          showError(
            `**${ariaName()} lost the coding stream** (the server may have restarted mid-task).\n\n`
            + "Wait a few seconds, then send the same request once — don't auto-retry in a loop."
          );
        } else {
          await sendMessage(text, true, { skipUserBubble: true });
        }
      }
    } else {
      const res = await fetch("/api/chat", fetchOpts);
      const data = await parseJsonResponse(res);
      typing.remove();
      if (!res.ok || data.ok === false) {
        showError(data.message || "Something went wrong.");
        return;
      }
      handleDone(data, data.message);
    }
  } catch (e) {
    typing.remove();
    if (chatStopRequested || e.name === "AbortError") {
      if (activeStreamText.trim()) {
        addMessage("assistant", `${activeStreamText.trim()}\n\n*(stopped)*`, { type: "info" });
      }
      statusText.textContent = "Stopped";
      return;
    }
    if (!forceNoStream && useStreaming && wantsStream && !isCodingAgent
        && !/\bdebug until\b.*\btests?\s+pass\b/i.test(text)) {
      await sendMessage(text, true, { skipUserBubble: true });
      return;
    }
    const msg = String(e.message || e);
    if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
      showError(
        `**Lost connection to ${ariaName()}** (the server may have restarted while working).\n\n`
        + "Wait a few seconds and try again. If it keeps happening, use the desktop shortcut or run:\n"
        + "`./scripts/launch-jarvis.sh`"
      );
    } else if (msg.includes("Ollama")) {
      showError(`**${msg}**\n\n${ariaName()} is starting Ollama automatically — try again in a few seconds.`);
    } else {
      showError(`**Error:** ${msg}`);
    }
  } finally {
    finishSendUi();
  }
}

// Media job track/resume/poll → media_jobs.js (window.activeMediaJobs / pollMediaJob / resumePendingMediaJobs)

// pollCodingJob → coding_jobs.js (window.jarvisPollCodingJob)

// pollMediaJob → media_jobs.js

function handleDone(data, text, streamed = false, options = {}) {
  if (isNativeApp() && data?.proposal_id) {
    data = window.prepareNativeCodingResult?.(data);
    text = data.message || text;
  }
  const meta = {
    module: data.module,
    type: window.resolveMetaType?.(data),
    proposal_id: data.proposal_id,
    diff: data.diff,
    diff_truncated: data.diff_truncated,
    diff_total_lines: data.diff_total_lines,
    choices: data.choices,
    agent_steps: data.agent_steps,
    diagnostics: data.diagnostics,
    syntax_ok: data.syntax_ok,
    verify_ok: data.verify_ok,
    test_impact: data.test_impact,
    show_undo: window.shouldShowUndo?.(data),
  };

  if (data.module) {
    document.querySelectorAll(".module-chip").forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.module === data.module || chip.dataset.module === "all");
    });
  }

  const imgPath = data.image_path || data.output_path;
  const hasImage = imgPath && /\.(png|jpe?g|webp|gif|bmp)$/i.test(imgPath);
  const videoPath = data.video_path || (data.type === "video_result" ? data.output_path : "");
  const hasVideo = videoPath && /\.(mp4|webm|mov|mkv|avi|m4v)$/i.test(videoPath);
  const isVision = data.module === "vision";

  if (hasVideo) {
    let body = options.targetBody;
    if (!body) {
      if (streamed) {
        body = document.querySelector(".message.assistant:last-child .msg-body");
      } else {
        body = addMessage("assistant", "", meta, { skipScroll: true }).body;
      }
    } else if (options.replaceQueued) {
      applyAssistantMeta(body.closest(".message"), meta);
      body.querySelector(".media-job-status")?.remove();
    }
    if (body) {
      body.innerHTML = buildVideoMessageHtml(data, text || data.message);
      appendGeneratedVideo(body, videoPath, data.video_name);
      scrollMessageIntoView(body, "start");
    }
  } else if (data.compare_paths?.length >= 2 || data.diff_path) {
    let body;
    if (streamed) {
      body = document.querySelector(".message.assistant:last-child .msg-body");
    } else {
      body = addMessage("assistant", "", meta, { skipScroll: true }).body;
    }
    if (body) {
      body.innerHTML = buildVisionMessageHtml(text || data.message);
      const row = document.createElement("div");
      row.className = "compare-images-row";
      data.compare_paths.forEach((p, i) => {
        appendImageFigure(row, p, null, `Image ${i + 1}`);
      });
      if (data.diff_path) {
        appendImageFigure(row, data.diff_path, null, "Visual diff (A | B | changes)");
      }
      body.appendChild(row);
      scrollMessageIntoView(body, "start");
    }
  } else if (data.module === "data") {
    let body;
    if (streamed) {
      body = document.querySelector(".message.assistant:last-child .msg-body");
    } else {
      body = addMessage("assistant", "", meta, { skipScroll: true }).body;
    }
    if (body) {
      body.innerHTML = formatMessage(text || data.message || "");
      if (data.data_preview) body.insertAdjacentHTML("beforeend", buildDataTableHtml(data.data_preview));
      if (data.chart_path) {
        const chartUrl = apiAuthUrl(`/api/audio/file?path=${encodeURIComponent(data.chart_path)}`);
        body.insertAdjacentHTML("beforeend", `<figure class="gen-image data-chart"><img src="${chartUrl}" alt="chart" /><figcaption>Chart</figcaption></figure>`);
      }
      if (data.export_path) {
        const ep = data.export_path;
        if (/\.pdf$/i.test(ep)) {
          const pdfUrl = `/api/audio/file?path=${encodeURIComponent(ep)}`;
          body.insertAdjacentHTML(
            "beforeend",
            `<p class="data-export-link">PDF report: <a href="${pdfUrl}" target="_blank" rel="noopener">Download</a> · <code>${escapeHtml(ep)}</code></p>`
          );
        } else {
          body.insertAdjacentHTML("beforeend", `<p class="data-export-link">Exported: <code>${escapeHtml(ep)}</code></p>`);
        }
      }
      scrollMessageIntoView(body, "start");
    }
  } else if (hasImage && isVision) {
    let body;
    if (streamed) {
      body = document.querySelector(".message.assistant:last-child .msg-body");
    } else {
      body = addMessage("assistant", "", meta, { skipScroll: true }).body;
    }
    if (body) {
      body.innerHTML = buildVisionMessageHtml(text || data.message);
      appendImageFigure(body, imgPath, data.image_name, "Analyzed image");
      scrollMessageIntoView(body, "start");
    }
  } else if (hasImage) {
    let body = options.targetBody;
    if (!body) {
      if (streamed) {
        body = document.querySelector(".message.assistant:last-child .msg-body");
      } else {
        body = addMessage("assistant", "", meta, { skipScroll: true }).body;
      }
    } else if (options.replaceQueued) {
      applyAssistantMeta(body.closest(".message"), meta);
      body.querySelector(".media-job-status")?.remove();
    }
    if (body) {
      body.innerHTML = buildImageMessageHtml(data, text || data.message);
      // Defer decode until after ComfyUI releases GPU — avoids WebKit OOM on job finish.
      const mountImg = () => {
        appendGeneratedImage(body, imgPath, data.image_name);
        scrollMessageIntoView(body, "start");
      };
      if (options.replaceQueued) setTimeout(mountImg, isNativeApp() ? 2500 : 600);
      else mountImg();
    }
  } else if (options.targetBody && (meta.proposal_id || meta.type === "proposal")) {
    const messageEl = options.targetBody.closest(".message");
    const bubble = messageEl?.querySelector(".bubble");
    if (options.replaceQueued) {
      applyAssistantMeta(messageEl, meta);
      options.targetBody.querySelector(".coding-job-status")?.remove();
      window.clearProposalExtras?.(bubble);
    }
    options.targetBody.innerHTML = formatMessage(text || data.message || "");
    syncMessageRawText(options.targetBody, text || data.message || "");
    ensureMessageCopyAction(messageEl, options.targetBody);
    if (bubble && (meta.proposal_id || meta.diagnostics || meta.agent_steps)) {
      const mount = () => window.attachProposalExtras?.(bubble, meta, messageEl);
      if (meta.proposal_id && isNativeApp()) {
        requestAnimationFrame(() => requestAnimationFrame(mount));
      } else {
        mount();
      }
    }
    scrollMessageIntoView(options.targetBody, "start");
  } else if (options.targetBody && options.pendingMediaJob) {
    applyAssistantMeta(options.targetBody.closest(".message"), meta);
    options.targetBody.innerHTML = formatMessage(text || data.message || "Working…");
    options.targetBody.closest(".message")?.classList.remove("typing-msg");
    scrollMessageIntoView(options.targetBody, "start");
  } else if (streamed) {
    const lastMsg = document.querySelector(".message.assistant:last-child");
    const msg = lastMsg?.querySelector(".msg-body");
    const bubble = lastMsg?.querySelector(".bubble");
    const content = text || data.message || "";
    if (msg) {
      msg.innerHTML = formatMessage(content);
      syncMessageRawText(msg, content);
      ensureMessageCopyAction(lastMsg, msg);
    }
    if (bubble && (meta.proposal_id || meta.type === "proposal" || meta.show_undo
      || meta.diagnostics || meta.agent_steps)) {
      const mount = () => window.attachProposalExtras?.(bubble, meta, lastMsg);
      if (meta.proposal_id && isNativeApp()) {
        requestAnimationFrame(() => requestAnimationFrame(mount));
      } else {
        mount();
      }
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
  } else {
    addMessage("assistant", text || data.message || "", meta);
  }

  lastAssistantText = text || data.message || "";
  if (data.warnings?.length) showChatWarnings(data.warnings);
  if (data.audio_path) showAudioPlayer(data.audio_path, data.transcript);
  if (data.chart_path && data.module !== "data") {
    const chartUrl = apiAuthUrl(`/api/audio/file?path=${encodeURIComponent(data.chart_path)}`);
    const msg = document.querySelector(".message.assistant:last-child .msg-body");
    if (msg) {
      msg.insertAdjacentHTML("beforeend", `<img src="${chartUrl}" alt="chart" style="max-width:100%" />`);
    } else {
      addMessage("assistant", `[chart:${data.chart_path}]`, { type: "info" });
    }
  }

  if (data.job_id && (data.type === "coding_job" || data.result_type === "coding_job")) {
    const msg = document.querySelector(".message.assistant:last-child");
    window.jarvisPollCodingJob?.(data.job_id, msg);
  } else if (
    data.job_id
    && (data.type === "media_job" || data.result_type === "media_job" || data.pending)
  ) {
    const msg = options.targetBody?.closest?.(".message")
      || document.querySelector(".message.assistant:last-child");
    window.pollMediaJob?.(data.job_id, msg);
  }

  if (data.memory_citations?.length) {
    const bubble = document.querySelector(".message.assistant:last-child .bubble");
    window.jarvisRenderMemoryCitations?.(bubble, data.memory_citations);
  }
  if (data.ok && (text || data.message) && meta.type !== "proposal" && !data.proposal_id) {
    window.jarvisMaybeSpeakReply?.(text || data.message);
  }

  const mode = data.uncensored ? "Uncensored" : "Standard";
  const mod = data.module ? ` · ${data.module}` : "";
  const timing = data.inference_ms ? ` · ${(data.inference_ms / 1000).toFixed(1)}s` : "";
  const modelTag = data.model ? ` · ${data.model.split(":")[0]}` : "";
  const tokParts = [];
  if (data.prompt_tokens) tokParts.push(`${data.prompt_tokens} in`);
  if (data.completion_tokens) tokParts.push(`${data.completion_tokens} out`);
  const tokTag = tokParts.length ? ` · ${tokParts.join(" / ")} tok` : "";
  if (!data.ok) {
    statusText.textContent = "Error — check Ollama";
  } else {
    statusText.textContent = `Ready · ${mode}${mod}${timing}${modelTag}${tokTag}`;
  }
  if (data.ok && window.jarvisNotify && !mediaWorkActive()) {
    if (hasVideo) window.jarvisNotify("Video ready", (text || data.message || "Clip generated").slice(0, 120));
    else if (hasImage && data.module === "image" && !isNativeApp()) {
      window.jarvisNotify("Image ready", (text || data.message || "Image generated").slice(0, 120));
    } else if (data.module === "coding" && (data.proposal_id || data.agent_steps?.length)) {
      window.jarvisNotify("Coding task done", (text || data.message || "Finished").slice(0, 120));
    }
  }
  if (hasImage && data.module === "image" && galleryViewVisible() && !isNativeApp()) {
    setTimeout(() => { if (galleryViewVisible()) window.loadGallery?.(); }, 800);
  }
}

window.handleDone = handleDone;

chatForm?.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value;
  messageInput.value = "";
  messageInput.style.height = "auto";
  resizeMessageInput();
  sendMessage(text);
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
    addMessage("assistant", "Fresh start. What would you like to do?");
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
      showError(data.message || "Could not play audio.");
      window.showAriaToast?.(data.message || "Could not play audio", "err", 5000);
    } else {
      statusText.textContent = "Ready · Sound Blaster";
    }
  } catch (e) {
    showError(`Audio playback failed: ${e.message}`);
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
    sendMessage(transcript);
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

window.sendMessage = sendMessage;
window.showError = showError;
window.isNativeApp = isNativeApp;
window.loadHealth = loadHealth;
window.isVisionAttachment = isVisionAttachment;
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

// freeJarvisVram → free_vram.js (window.freeJarvisVram)

function renderGpuStatus(gpu) {
  if (window.jarvisHealth?.renderGpuStatus) {
    window.jarvisHealth.renderGpuStatus(gpu);
    return;
  }
}

// freeVramBtn click wired in modules/health.mjs

function renderAudioStatus(audio) {
  if (window.jarvisHealth?.renderAudioStatus) {
    window.jarvisHealth.renderAudioStatus(audio);
    return;
  }
}

async function loadGpuStatus() {
  if (window.jarvisHealth?.loadGpuStatus) {
    await window.jarvisHealth.loadGpuStatus();
  }
}
window.loadGpuStatus = loadGpuStatus;

let jarvisServerWasDown = false;
let jarvisKnownVersion = null;

function reloadJarvisUi(reason = "") {
  if (mediaWorkActive()) {
    const msg = "Image job running — reload deferred (finishes in chat when done)";
    if (statusText) statusText.textContent = msg;
    return;
  }
  if (reason && statusText) statusText.textContent = reason;
  setTimeout(() => location.reload(), reason ? 350 : 0);
}

window.reloadJarvisUi = reloadJarvisUi;

async function pollLive() {
  if (mediaWorkActive()) return;
  try {
    const res = await fetch("/api/live");
    if (!res.ok) {
      jarvisServerWasDown = true;
      if (statusText && (window.activeMediaJobs?.size || 0) > 0) {
        statusText.textContent = "Server reconnecting — image job still running…";
      }
      return;
    }
    const data = await res.json();
    if (jarvisServerWasDown) {
      jarvisServerWasDown = false;
      if (statusText) {
        statusText.textContent = (window.activeMediaJobs?.size || 0) > 0
          ? "Server back — finishing image job…"
          : `Ready · v${data.version || "?"}`;
      }
    }
    jarvisKnownVersion = data.version || jarvisKnownVersion;
    applyBranding(data);
    if (data.ui_version && data.ui_version !== JARVIS_UI_VERSION) {
      const envEl = document.getElementById("envStrip");
      if (envEl && !envEl.dataset.versionWarn) {
        envEl.dataset.versionWarn = "1";
        envEl.classList.add("version-warn");
        envEl.title = `UI ${JARVIS_UI_VERSION} · server expects ${data.ui_version} — Reload UI`;
      }
    }
    uncensoredToggle.checked = data.uncensored;
    document.body.classList.toggle("uncensored-mode", data.uncensored);
    modeLabel.textContent = data.uncensored ? "Uncensored · Local" : "Local AI Assistant";
    if (data.version && statusText) {
      statusText.textContent = data.ready
        ? `Ready · v${data.version}`
        : `Starting services · v${data.version}`;
    }
  } catch (_) {
    jarvisServerWasDown = true;
  }
}

async function loadHealth() {
  const modelsEl = document.getElementById("modelsStatus");
  try {
    const [healthRes, svcRes] = await Promise.all([
      fetchWithTimeout("/api/health", {}, 3000),
      fetchWithTimeout("/api/services", {}, 5000).catch(() => null),
    ]);
    if (!healthRes.ok) throw new Error("health check failed");
    const data = await healthRes.json();
    if (svcRes?.ok) {
      const svc = await svcRes.json();
      if (svc.services) renderServices(svc.services, svc.comfyui_settings);
      if (svc.ollama && data.ollama == null) data.ollama = svc.ollama;
    }
    if (data.gpu) renderGpuStatus(data.gpu);
    if (data.audio) renderAudioStatus(data.audio);
    uncensoredToggle.checked = data.uncensored;
    document.body.classList.toggle("uncensored-mode", data.uncensored);
    modeLabel.textContent = data.uncensored ? "Uncensored · Local" : "Local AI Assistant";

    if (data.services) renderServices(data.services, data.comfyui_settings);

    const visionRow = servicesPanel?.querySelector('[data-svc="vision"]');
    if (visionRow && data.vision) {
      const v = data.vision;
      visionRow.classList.toggle("online", v.installed);
      visionRow.classList.toggle("offline", !v.installed);
      const mode = v.quality_mode === "quality" ? "preset:quality"
        : v.quality_mode === "fast" ? "preset:fast" : "selected";
      visionRow.innerHTML = `<span class="svc-dot"></span> Vision · ${v.model || "?"} (${mode})`;
      if (v.note) visionRow.title = v.note;
    }

    if (data.version) {
      if (data.busy) {
        statusText.textContent = `Busy · ${data.busy_job || "media"} · v${data.version}`;
      } else {
        statusText.textContent = data.ready
          ? `Ready · v${data.version}`
          : `Starting services · v${data.version}`;
      }
    }

    if (modelsEl) {
      if (!data.ollama?.running) {
        modelsEl.innerHTML = '<span class="warn">Starting Ollama…</span>';
      } else if (data.models_missing?.length) {
        modelsEl.innerHTML = `<span class="warn">Pulling models: ${data.models_missing.join(", ")}</span>`;
      } else {
        const m = data.models || {};
        const embedNote = data.embed_ok === false && data.embed_warning
          ? `<br><span class="warn">${escapeHtml(data.embed_warning)}</span>` : "";
        modelsEl.innerHTML = `<span>${m.general || "?"}</span><br><span>${m.coder || "?"}</span>${embedNote}`;
      }
    }
    return data;
  } catch (e) {
    if (modelsEl) {
      modelsEl.innerHTML = `<span class="warn">Connecting to ${ariaName()}…</span>`;
    }
    statusText.textContent = "Connecting…";
    return null;
  }
}

function renderServices(services, comfySettings) {
  if (!servicesPanel || !services) return;
  for (const svc of services) {
    const row = servicesPanel.querySelector(`[data-svc="${svc.name}"]`);
    if (!row) continue;
    row.classList.remove("online", "offline", "starting");
    if (svc.running || svc.message === "ready") {
      row.classList.add("online");
    } else if (svc.required) {
      row.classList.add("starting");
    } else {
      row.classList.add("offline");
    }
    row.innerHTML = `<span class="svc-dot"></span> ${svc.label}${svc.detail ? ` · ${svc.detail}` : ""}`;
  }
  if (comfySettings) window.syncComfySettings?.(comfySettings);
}

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
window.renderServices = renderServices;
window.addMessage = addMessage;



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

document.getElementById("reloadUiBtn")?.addEventListener("click", () => reloadJarvisUi());
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && String(e.key).toLowerCase() === "r") {
    e.preventDefault();
    reloadJarvisUi();
  }
});
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) scheduleEditorContextPoll();
});
// Define before startup_overlay.js invokes waitForServices → ariaPostStartup
window.ariaPostStartup = function ariaPostStartup() {
  try { window.initAriaModalChrome?.(); } catch (_) {}
  loadSuggestions();
  loadHealth().then(async () => {
    await window.restoreUncensoredSession?.();
    window.loadModelSettings?.();
    window.loadComfyMode?.();
    loadGpuStatus();
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
      setTimeout(() => sendMessage(prefill), 300);
    }
    const hashView = (window.location.hash || "").replace(/^#/, "").trim();
    if (hashView && document.querySelector(`.view-tab[data-view="${hashView}"]`)) {
      switchToView(hashView);
    }
    document.getElementById("presetQualityBtn")?.classList.add("active");
    setInterval(pollLive, isNativeApp() ? 45000 : 20000);
    setInterval(() => {
      if (!mediaWorkActive()) loadHealth();
    }, 180000);
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
    sendMessage(messageInput.value);
  }
  if (e.ctrlKey && e.key === "l" && !inTextField) {
    e.preventDefault();
    clearBtn.click();
  }
});

window.appendGeneratedImage = appendGeneratedImage;
window.resizeMessageInput = resizeMessageInput;

// showGeneratedImage / showAudioPlayer / jarvisSendToChat → chat_media.js

// debug bundle → profile_controls.js

// personality/branches → chat_branches.js

