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
      showApiKeyModal("Invalid or missing API key.");
    }
    return res;
  };
})();

function getStoredApiKey() {
  return sessionStorage.getItem("jarvis_api_key") || "";
}

function apiAuthUrl(url) {
  if (!url) return "";
  const key = getStoredApiKey();
  if (!key) return url;
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}api_key=${encodeURIComponent(key)}`;
}
window.apiAuthUrl = apiAuthUrl;

let jarvisLanIps = [];
let jarvisApiKeyRequired = false;
let jarvisLocalhostKeyExempt = true;

function isLoopbackHost(host) {
  return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
}

function isSameMachineHost() {
  const host = location.hostname;
  return isLoopbackHost(host) || jarvisLanIps.includes(host);
}

function mediaNeedsApiKey() {
  if (!jarvisApiKeyRequired) return false;
  if (jarvisLocalhostKeyExempt && isSameMachineHost()) return false;
  return true;
}

async function fetchMediaBlobUrl(url) {
  const res = await fetch(url);
  if (!res.ok) return { ok: false, status: res.status };
  const blob = await res.blob();
  const type = (blob.type || "").toLowerCase();
  if (type.includes("json") || type.includes("text")) {
    return { ok: false, status: res.status || 415 };
  }
  const videoBlob = type.startsWith("video/") ? blob : new Blob([blob], { type: "video/mp4" });
  return { ok: true, url: URL.createObjectURL(videoBlob) };
}

function resolveVideoUrl(pathOrName, { playback = true } = {}) {
  const raw = (pathOrName || "").split(/[/\\]/).pop();
  if (!raw) return "";
  let file = raw;
  if (playback && !/\.webm$/i.test(file)) {
    file = file.replace(/\.(mp4|mov|m4v|mkv|avi)$/i, ".webm");
  }
  const url = `/api/video-gallery/${encodeURIComponent(file)}`;
  if (!mediaNeedsApiKey() || isSameMachineHost()) return url;
  return apiAuthUrl(url);
}

async function resolveVideoPlaybackUrl(pathOrName) {
  const url = resolveVideoUrl(pathOrName, { playback: true });
  if (!url) return { ok: false, url: "", needsKey: false };
  if (mediaNeedsApiKey() && !isSameMachineHost() && !getStoredApiKey()) {
    return { ok: false, url, needsKey: true };
  }
  return { ok: true, url, direct: true, needsKey: false };
}
window.resolveVideoPlaybackUrl = resolveVideoPlaybackUrl;
window.mediaNeedsApiKey = mediaNeedsApiKey;
window.isSameMachineHost = isSameMachineHost;

const MEDIA_LOAD_ERROR_HINT = "Could not play this clip in the app — try Video gallery or open the file from data/generated_videos/";

function attachMediaLoadError(el, kind = "media") {
  if (!el || el.dataset.mediaErrorBound) return;
  el.dataset.mediaErrorBound = "1";
  el.addEventListener("error", () => {
    const parent = el.closest("figure") || el.parentElement;
    if (!parent || parent.querySelector(".media-load-warn")) return;
    const warn = document.createElement("p");
    warn.className = "media-load-warn warn small";
    warn.textContent = kind === "video"
      ? `Video failed to load — ${MEDIA_LOAD_ERROR_HINT}`
      : `Image failed to load — ${MEDIA_LOAD_ERROR_HINT}`;
    parent.appendChild(warn);
  });
}

function showApiKeyModal(message) {
  const modal = document.getElementById("apiKeyModal");
  const err = document.getElementById("apiKeyError");
  if (!modal) return;
  if (err) {
    err.textContent = message || "";
    err.classList.toggle("hidden", !message);
  }
  modal.classList.remove("hidden");
  document.getElementById("apiKeyInput")?.focus();
}

function hideApiKeyModal() {
  document.getElementById("apiKeyModal")?.classList.add("hidden");
}

async function verifyApiKey(key) {
  const headers = { "X-API-Key": key };
  const res = await fetch("/api/services", { headers });
  return res.ok;
}

function initApiKeyModal() {
  const modal = document.getElementById("apiKeyModal");
  const saveBtn = document.getElementById("apiKeySaveBtn");
  const cancelBtn = document.getElementById("apiKeyCancelBtn");
  const input = document.getElementById("apiKeyInput");
  const err = document.getElementById("apiKeyError");
  if (!modal || !saveBtn) return;

  saveBtn.addEventListener("click", async () => {
    const key = input?.value?.trim();
    if (!key) {
      if (err) {
        err.textContent = "Enter the API key.";
        err.classList.remove("hidden");
      }
      return;
    }
    sessionStorage.setItem("jarvis_api_key", key);
    const ok = await verifyApiKey(key);
    if (!ok) {
      sessionStorage.removeItem("jarvis_api_key");
      if (err) {
        err.textContent = "That key was rejected. Check JARVIS_API_KEY on the PC.";
        err.classList.remove("hidden");
      }
      return;
    }
    hideApiKeyModal();
    refreshLanPanel();
    location.reload();
  });
  cancelBtn?.addEventListener("click", hideApiKeyModal);
}

let lanPrimaryUrl = "";

async function refreshLanPanel() {
  const line = document.getElementById("lanStatusLine");
  const list = document.getElementById("lanUrlList");
  const copyBtn = document.getElementById("lanCopyUrlBtn");
  if (!line) return;
  try {
    const res = await fetch("/api/lan");
    const data = await res.json();
    jarvisLanIps = data.lan_ips || [];
    jarvisApiKeyRequired = Boolean(data.api_key_required);
    jarvisLocalhostKeyExempt = data.api_key_localhost_exempt !== false;
    if (!data.lan_enabled) {
      line.textContent = "Local only — run ./scripts/enable-lan.sh on the PC to allow LAN.";
      if (list) list.innerHTML = "";
      copyBtn?.classList.add("hidden");
      return;
    }
    const urls = data.connect_urls || [];
    lanPrimaryUrl = urls[0] || data.local_url || "";
    line.textContent = data.api_key_required
      ? "LAN on — API key required on other devices (not on this PC via 127.0.0.1)."
      : "LAN on — set JARVIS_API_KEY before remote use.";
    if (list) {
      list.innerHTML = urls.length
        ? urls.map((u) => `<code class="lan-url">${escapeHtml(u)}</code>`).join("")
        : `<span class="muted">No LAN IP detected — use PC IP manually.</span>`;
    }
    copyBtn?.classList.toggle("hidden", !lanPrimaryUrl);
  } catch (_) {
    line.textContent = "LAN status unavailable.";
  }
}

function initLanPanel() {
  document.getElementById("lanRefreshBtn")?.addEventListener("click", refreshLanPanel);
  document.getElementById("lanCopyUrlBtn")?.addEventListener("click", async () => {
    if (!lanPrimaryUrl) return;
    try {
      await navigator.clipboard.writeText(lanPrimaryUrl);
      statusText.textContent = "LAN URL copied";
    } catch (_) {
      prompt("Copy this URL:", lanPrimaryUrl);
    }
  });
  refreshLanPanel();
}

async function initLanAccessGate() {
  try {
    const res = await fetch("/api/live");
    const data = await res.json();
    jarvisApiKeyRequired = Boolean(data.api_key_required);
    jarvisLocalhostKeyExempt = data.api_key_localhost_exempt !== false;
    try {
      const lanRes = await fetch("/api/lan");
      if (lanRes.ok) {
        const lanData = await lanRes.json();
        jarvisLanIps = lanData.lan_ips || [];
      }
    } catch (_) {}
    const needsKey = mediaNeedsApiKey();
    if (needsKey && !getStoredApiKey()) {
      showApiKeyModal("");
    }
  } catch (_) {}
}

initApiKeyModal();
initLanPanel();
initLanAccessGate();

let haWebhookUrl = "";

function haPanelStatus(message, tone = "") {
  const el = document.getElementById("haPanelStatus");
  if (!el) return;
  el.textContent = message || "";
  el.classList.remove("warn", "ok");
  if (tone) el.classList.add(tone);
  if (message && typeof statusText !== "undefined" && statusText) {
    statusText.textContent = message;
  }
}

function haTokenFields() {
  return [
    document.getElementById("haTokenInput"),
    document.getElementById("haTokenModalInput"),
  ].filter(Boolean);
}

function syncHaTokenFields(sourceEl) {
  const val = sourceEl?.value ?? "";
  haTokenFields().forEach((el) => {
    if (el !== sourceEl) el.value = val;
  });
  updateHaTokenHint();
}

function getHaTokenValue() {
  for (const el of haTokenFields()) {
    const val = el.value?.trim();
    if (val) return val;
  }
  return "";
}

function setHaTokenValue(value) {
  for (const el of haTokenFields()) el.value = value || "";
  updateHaTokenHint();
}

function maskHaToken(token) {
  if (!token) return "";
  if (token.length <= 12) return `${token.length} characters`;
  return `${token.slice(0, 8)}…${token.slice(-6)} (${token.length} chars)`;
}

function updateHaTokenHint() {
  const token = getHaTokenValue();
  const len = token.length;
  const preview = document.getElementById("haTokenPreview");
  if (preview) {
    preview.textContent = len ? `Token ready: ${maskHaToken(token)}` : "No token pasted yet — click the box above and press Ctrl+V.";
  }
  const msg = len ? `${len} character(s) — click Test connection, then Save.` : "";
  for (const id of ["haTokenHint", "haTokenModalHint"]) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.textContent = msg;
  }
}

function haUrlValue() {
  const raw = document.getElementById("haUrlInput")?.value?.trim();
  return raw || "http://127.0.0.1:8123";
}

async function pasteHaTokenFromClipboard(targetInput) {
  try {
    const text = (await navigator.clipboard.readText())?.trim();
    if (!text) {
      haPanelStatus("Clipboard is empty.", "warn");
      return false;
    }
    if (targetInput) {
      targetInput.value = text;
      syncHaTokenFields(targetInput);
    } else {
      setHaTokenValue(text);
    }
    haPanelStatus(`Token pasted (${text.length} chars).`, "ok");
    return true;
  } catch (_) {
    haPanelStatus("Click the token box, then Ctrl+V. (Browser blocked clipboard read.)", "warn");
    return false;
  }
}

function showHaTokenModal() {
  const modal = document.getElementById("haTokenModal");
  const sidebarToken = document.getElementById("haTokenInput")?.value?.trim();
  const modalInput = document.getElementById("haTokenModalInput");
  if (modalInput && sidebarToken && !modalInput.value.trim()) modalInput.value = sidebarToken;
  document.getElementById("haTokenModalError")?.classList.add("hidden");
  updateHaTokenHint();
  modal?.classList.remove("hidden");
  modalInput?.focus();
}

function hideHaTokenModal() {
  document.getElementById("haTokenModal")?.classList.add("hidden");
}

async function saveHaConfigFromUi({ closeModal = false } = {}) {
  const body = haConfigBody();
  if (!body.token) {
    try {
      const st = await (await fetch("/api/homeassistant/status")).json();
      if (!st.token_set) {
        haPanelStatus("Paste your token first, or run ./scripts/set-ha-token.sh", "warn");
        document.getElementById("haTokenInput")?.focus();
        return null;
      }
    } catch (_) {
      haPanelStatus("Could not read Home Assistant status.", "warn");
      return null;
    }
  }
  if (!body.token) {
    haPanelStatus("Saving settings…");
    try {
      const res = await fetch("/api/homeassistant/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      const conn = data.connection || {};
      haPanelStatus(
        conn.ok
          ? `Connected${conn.version ? ` · v${conn.version}` : ""}.`
          : (conn.message || "Saved."),
        conn.ok ? "ok" : "warn",
      );
      await refreshHaPanel();
      if (typeof loadHealth === "function") loadHealth();
      return data;
    } catch (e) {
      haPanelStatus(String(e), "warn");
      return null;
    }
  }
  haPanelStatus("Testing Home Assistant…");
  try {
    const testRes = await fetch("/api/homeassistant/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: body.url, token: body.token }),
    });
    const testData = await testRes.json();
    if (!testData.ok) {
      haPanelStatus(testData.message || "Token test failed.", "warn");
      const err = document.getElementById("haTokenModalError");
      if (err) {
        err.textContent = testData.message || "Token test failed.";
        err.classList.remove("hidden");
      }
      return null;
    }
    haPanelStatus("Saving…");
    const res = await fetch("/api/homeassistant/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.connection?.ok) {
      setHaTokenValue("");
      haPanelStatus(`Connected${testData.version ? ` · v${testData.version}` : ""}. Try "house status".`, "ok");
      if (closeModal) hideHaTokenModal();
    } else {
      haPanelStatus(data.connection?.message || "Saved — check token and URL.", "warn");
    }
    await refreshHaPanel();
    if (typeof loadHealth === "function") loadHealth();
    return data;
  } catch (e) {
    haPanelStatus(String(e), "warn");
    return null;
  }
}

async function refreshHaPanel() {
  const line = document.getElementById("haStatusLine");
  const webhookLine = document.getElementById("haWebhookLine");
  const copyBtn = document.getElementById("haCopyWebhookBtn");
  const urlInput = document.getElementById("haUrlInput");
  const leaveInput = document.getElementById("haLeaveSceneInput");
  const enabledToggle = document.getElementById("haEnabledToggle");
  if (!line) return;
  try {
    const res = await fetch("/api/homeassistant/status");
    const data = await res.json();
    if (urlInput && data.url && !urlInput.value.trim()) urlInput.value = data.url;
    if (leaveInput && data.leave_scene != null && !leaveInput.dataset.userEdited) {
      leaveInput.value = data.leave_scene || "";
    }
    if (enabledToggle) {
      enabledToggle.checked = data.feature_on !== false && data.enabled !== false;
    }
    const conn = data.connection || {};
    if (data.connected || conn.ok) {
      line.textContent = `Connected${conn.version ? ` · v${conn.version}` : ""}`;
      line.classList.remove("warn");
    } else if (data.token_set) {
      line.textContent = conn.message || "Token saved — click Test connection or Save.";
      line.classList.add("warn");
    } else if (data.feature_on === false || data.enabled === false) {
      line.textContent = "Turn on Home Assistant below and click Save.";
      line.classList.add("warn");
    } else {
      line.textContent = "Paste token below (Ctrl+V) or run ./scripts/set-ha-token.sh";
      line.classList.add("warn");
    }
    haWebhookUrl = data.automation_webhook_url || "";
    if (webhookLine && haWebhookUrl) {
      webhookLine.textContent = `HA → ${ariaName()} webhook: ${haWebhookUrl}`;
      webhookLine.classList.remove("hidden");
      copyBtn?.classList.remove("hidden");
    } else {
      webhookLine?.classList.add("hidden");
      copyBtn?.classList.add("hidden");
    }
  } catch (_) {
    line.textContent = "Smart home status unavailable.";
  }
}

function haConfigBody() {
  return {
    url: haUrlValue(),
    token: getHaTokenValue(),
    leave_scene: document.getElementById("haLeaveSceneInput")?.value?.trim() || "",
    enabled: document.getElementById("haEnabledToggle")?.checked !== false,
    ensure_automation_secret: true,
  };
}

function initHaPanel() {
  const urlInput = document.getElementById("haUrlInput");
  if (urlInput && !urlInput.value.trim()) urlInput.value = "http://127.0.0.1:8123";

  document.getElementById("haRefreshBtn")?.addEventListener("click", refreshHaPanel);
  document.getElementById("haLeaveSceneInput")?.addEventListener("input", (e) => {
    e.target.dataset.userEdited = "1";
  });
  haTokenFields().forEach((el) => {
    el.addEventListener("input", () => syncHaTokenFields(el));
    el.addEventListener("paste", () => setTimeout(() => syncHaTokenFields(el), 0));
  });
  document.getElementById("haPasteTokenBtn")?.addEventListener("click", async () => {
    const input = document.getElementById("haTokenInput");
    await pasteHaTokenFromClipboard(input);
    input?.focus();
  });
  document.getElementById("haTokenModalBtn")?.addEventListener("click", showHaTokenModal);
  document.getElementById("haTokenModalPasteBtn")?.addEventListener("click", async () => {
    await pasteHaTokenFromClipboard(document.getElementById("haTokenModalInput"));
  });
  document.getElementById("haTokenModalCancelBtn")?.addEventListener("click", hideHaTokenModal);
  document.getElementById("haTokenModalSaveBtn")?.addEventListener("click", () => saveHaConfigFromUi({ closeModal: true }));
  document.getElementById("haTestBtn")?.addEventListener("click", async () => {
    const body = haConfigBody();
    if (!body.token) {
      haPanelStatus("Paste your token in the box above first (Ctrl+V).", "warn");
      document.getElementById("haTokenInput")?.focus();
      return;
    }
    haPanelStatus("Testing Home Assistant…");
    try {
      const res = await fetch("/api/homeassistant/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: body.url, token: body.token }),
      });
      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        data = {};
      }
      const msg = data.message
        || (res.status === 401 ? `${ariaName()} API key required — enter it when prompted.` : "")
        || `Request failed (HTTP ${res.status})`;
      haPanelStatus(
        data.ok
          ? `Connected${data.version ? ` · v${data.version}` : ""} — click Save to keep it.`
          : msg,
        data.ok ? "ok" : "warn",
      );
      await refreshHaPanel();
    } catch (e) {
      haPanelStatus(String(e), "warn");
    }
  });
  document.getElementById("haSaveBtn")?.addEventListener("click", () => saveHaConfigFromUi());
  document.getElementById("haCopyWebhookBtn")?.addEventListener("click", async () => {
    if (!haWebhookUrl) return;
    try {
      await navigator.clipboard.writeText(haWebhookUrl);
      statusText.textContent = "Webhook URL copied";
    } catch (_) {
      prompt("Copy webhook URL:", haWebhookUrl);
    }
  });
  document.querySelectorAll(".ha-quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const msg = btn.dataset.msg || "";
      if (msg) sendMessage(msg);
    });
  });
  refreshHaPanel();
  updateHaTokenHint();
}

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

initHaPanel();

const editorContextPill = document.getElementById("editorContextPill");
const editorPillText = document.getElementById("editorPillText");
const editorContextCard = document.getElementById("editorContextCard");
const editorContextLabel = document.getElementById("editorContextLabel");
let lastEditorFile = "";
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
let activeBranchId = "main";
let assistantDisplayName = "ARIA";

function ariaName() {
  return assistantDisplayName || "ARIA";
}

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
const debugBundleBtn = document.getElementById("debugBundleBtn");

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
const CHAT_IMAGE_THUMB_MAX = 320;

function isNativeApp() {
  return document.documentElement.classList.contains("jarvis-app");
}

function syncMediaBusyClass() {
  document.documentElement.classList.toggle("media-busy", activeMediaJobs.size > 0);
}

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
      openImageLightbox(full, img.alt || "", path, img.src);
    });
  });
}

let lightboxImagePath = "";

function openImageLightbox(url, caption = "", imagePath = "", previewUrl = "") {
  const modal = document.getElementById("imageLightbox");
  const img = document.getElementById("imageLightboxImg");
  const cap = document.getElementById("imageLightboxCaption");
  const promptEl = document.getElementById("imageLightboxPrompt");
  const statusEl = document.getElementById("imageLightboxStatus");
  if (!modal || !img || !url) return;
  lightboxImagePath = imagePath || "";
  const preview = previewUrl && previewUrl !== url ? previewUrl : "";
  img.src = preview || url;
  img.alt = caption || "Image";
  if (cap) cap.textContent = caption || "";
  if (promptEl) promptEl.value = "";
  if (statusEl) statusEl.textContent = preview ? "Loading full resolution…" : "";
  modal.classList.remove("hidden");
  promptEl?.focus();
  if (preview) {
    const fullImg = new Image();
    fullImg.onload = () => {
      if (!modal.classList.contains("hidden") && lightboxImagePath === (imagePath || "")) {
        img.src = url;
        if (statusEl) statusEl.textContent = "";
      }
    };
    fullImg.onerror = () => {
      if (statusEl) statusEl.textContent = "Could not load full image — showing preview.";
    };
    fullImg.src = url;
  }
}

function closeImageLightbox() {
  document.getElementById("imageLightbox")?.classList.add("hidden");
  lightboxImagePath = "";
}

function openVideoLightbox(url, caption = "") {
  const modal = document.getElementById("videoLightbox");
  const player = document.getElementById("videoLightboxPlayer");
  const cap = document.getElementById("videoLightboxCaption");
  if (!modal || !player || !url) return;
  player.pause();
  player.removeAttribute("src");
  player.load();
  player.src = url;
  if (cap) cap.textContent = caption || "";
  modal.classList.remove("hidden");
  player.play().catch(() => {});
}
window.openVideoLightbox = openVideoLightbox;

function closeVideoLightbox() {
  const player = document.getElementById("videoLightboxPlayer");
  if (player) {
    player.pause();
    player.removeAttribute("src");
    player.load();
  }
  document.getElementById("videoLightbox")?.classList.add("hidden");
}
window.closeVideoLightbox = closeVideoLightbox;

function bindClickableVideos(root) {
  const scope = root || document;
  scope.querySelectorAll(".gen-video video, .video-gallery-item .video-thumb").forEach((video) => {
    if (video.dataset.lightboxBound) return;
    video.dataset.lightboxBound = "1";
    const isThumb = video.classList.contains("video-thumb");
    video.classList.add("clickable-video");
    if (!video.title) video.title = isThumb ? "Click to open player" : "Double-click to open full player";
    const open = (e) => {
      const src = video.currentSrc || video.src;
      if (!src) return;
      e.preventDefault();
      e.stopPropagation();
      const host = video.closest(".gen-video, .video-gallery-item");
      const caption = host?.querySelector("figcaption, .video-item-name")?.textContent?.trim() || "";
      openVideoLightbox(src, caption);
    };
    video.addEventListener(isThumb ? "click" : "dblclick", open);
  });
}
window.bindClickableVideos = bindClickableVideos;

function initVideoLightbox() {
  document.getElementById("videoLightboxClose")?.addEventListener("click", closeVideoLightbox);
  const modal = document.getElementById("videoLightbox");
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) closeVideoLightbox();
  });
}

async function queueImageEdit(imagePath, prompt, regionKey, statusEl, onDone, denoise) {
  if (!imagePath || !prompt) {
    if (statusEl) statusEl.textContent = "Enter what you want to change.";
    return false;
  }
  const regionKeyNorm = regionKey || "full";
  const wholeImage = regionKeyNorm === "full";
  const form = new FormData();
  form.append("path", imagePath);
  form.append("prompt", prompt);
  const endpoint = wholeImage ? "/api/image/edit" : "/api/image/inpaint";
  if (!wholeImage) {
    let d = denoise;
    if (d == null || d === "") {
      const el = document.getElementById("inpaintDenoise");
      d = el?.value;
    }
    const denoiseVal = Number(d);
    form.append(
      "denoise",
      Number.isFinite(denoiseVal) ? String(Math.min(1, Math.max(0.5, denoiseVal))) : "0.82",
    );
    const region = INPAINT_REGIONS[regionKeyNorm];
    if (region) form.append("region", JSON.stringify(region));
  }
  try {
    if (statusEl) statusEl.textContent = wholeImage ? "Queuing img2img edit…" : "Queuing inpaint…";
    const res = await fetch(endpoint, { method: "POST", body: form });
    const out = await res.json().catch(() => ({}));
    if (!res.ok || !out.ok) {
      const detail = out.message || out.detail
        || (res.status === 404 ? "Edit API not loaded — use jarvis-ctl restart, then Reload UI" : null)
        || `Edit failed (${res.status})`;
      if (statusEl) statusEl.textContent = detail;
      return false;
    }
    if (out.job_id) {
      const { body } = addMessage("assistant", out.message || (wholeImage ? "Editing image…" : "Inpainting…"), {
        module: "image",
        type: "media_job",
      });
      const msg = body?.closest?.(".message");
      pollMediaJob(out.job_id, msg);
      onDone?.();
      return true;
    }
    if (out.image_path) {
      showGeneratedImage(out.image_path, out.image_name);
      onDone?.();
      return true;
    }
    if (statusEl) statusEl.textContent = "Edit queued but no job id returned.";
    return false;
  } catch (err) {
    if (statusEl) statusEl.textContent = String(err);
    return false;
  }
}

function initImageLightbox() {
  document.getElementById("imageLightboxClose")?.addEventListener("click", closeImageLightbox);
  const modal = document.getElementById("imageLightbox");
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) closeImageLightbox();
  });
  document.getElementById("imageLightboxEditBtn")?.addEventListener("click", async () => {
    const prompt = document.getElementById("imageLightboxPrompt")?.value?.trim();
    const regionKey = document.getElementById("imageLightboxRegion")?.value || "full";
    const statusEl = document.getElementById("imageLightboxStatus");
    const btn = document.getElementById("imageLightboxEditBtn");
    if (!lightboxImagePath) {
      if (statusEl) statusEl.textContent = "Image path missing — try Gallery or regenerate.";
      return;
    }
    if (btn) btn.disabled = true;
    if (statusEl) statusEl.textContent = "Queuing edit…";
    await queueImageEdit(lightboxImagePath, prompt, regionKey, statusEl, () => {
      closeImageLightbox();
      if (statusText) statusText.textContent = "Image edit running…";
    });
    if (btn) btn.disabled = false;
  });
  document.getElementById("imageLightboxPrompt")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      document.getElementById("imageLightboxEditBtn")?.click();
    }
  });
}

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

async function vramPreflight(action) {
  try {
    const res = await fetch(`/api/vram/preflight?action=${encodeURIComponent(action)}`);
    if (!res.ok) return true;
    const data = await res.json();
    if (data.blocked) {
      window.alert((data.warnings || ["Media queue full"]).join("\n\n"));
      return false;
    }
    if (data.ok || !data.warnings?.length) return true;
    const tips = (data.tips || []).slice(0, 2).join("\n");
    const adj = (data.adjustments || []).slice(0, 2).join("\n");
    const msg = data.warnings.join("\n\n")
      + (adj ? `\n\nPlan: ${adj}` : "")
      + (tips ? `\n\nTip: ${tips}` : "")
      + "\n\nContinue anyway?";
    return window.confirm(msg);
  } catch {
    return true;
  }
}

async function pollComfySettingsJob(jobId) {
  for (let i = 0; i < 120; i++) {
    await new Promise((r) => setTimeout(r, 1500));
    const res = await fetch(`/api/comfyui/settings/job/${encodeURIComponent(jobId)}`);
    const job = await res.json();
    if (!res.ok) throw new Error(job.message || `HTTP ${res.status}`);
    statusText.textContent = job.message || "Applying ComfyUI settings…";
    if (job.done) {
      if (job.ok === false) throw new Error(job.message || "ComfyUI settings failed");
      return job.result || job;
    }
  }
  throw new Error("ComfyUI settings timed out — check data/logs/comfyui.log");
}

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
    warn.querySelector(".media-key-btn")?.addEventListener("click", () => showApiKeyModal(""));
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

function formatDiff(diff, options = {}) {
  const text = typeof diff === "string" ? diff : (diff == null ? "" : String(diff));
  if (!text) return "";
  const maxLines = options.maxLines || 160;
  const lines = text.split("\n");
  const slice = lines.length > maxLines ? lines.slice(0, maxLines) : lines;
  return slice.map((line) => {
    const escaped = escapeHtml(line);
    if (line.startsWith("+") && !line.startsWith("+++")) return `<span class="add">${escaped}</span>`;
    if (line.startsWith("-") && !line.startsWith("---")) return `<span class="del">${escaped}</span>`;
    return escaped;
  }).join("\n");
}

function mountDiffBlock(pre, diff, meta) {
  if (!pre) return;
  pre.className = "diff-block";
  pre.innerHTML = formatDiff(diff);
  if (meta?.diff_truncated && meta?.proposal_id) {
    const note = document.createElement("div");
    note.className = "diff-truncated-note";
    const total = meta.diff_total_lines ? ` (${meta.diff_total_lines} lines total)` : "";
    note.textContent = `Diff preview truncated${total}.`;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ghost-btn small";
    btn.textContent = "Load full diff";
    btn.onclick = async () => {
      btn.disabled = true;
      btn.textContent = "Loading…";
      try {
        const res = await fetch(`/api/proposals/${encodeURIComponent(meta.proposal_id)}`);
        const data = await res.json();
        if (data.ok && data.diff) {
          pre.innerHTML = formatDiff(data.diff, { maxLines: 400 });
          note.remove();
        } else {
          btn.textContent = "Could not load";
        }
      } catch (_) {
        btn.textContent = "Retry load";
        btn.disabled = false;
      }
    };
    note.appendChild(btn);
    pre.insertAdjacentElement("afterend", note);
  }
}

function resolveMetaType(data) {
  // Streamed coding/image results use type=done + result_type=proposal|image_result
  if (data.type === "done" && data.result_type) return data.result_type;
  return data.type || data.result_type
    || (data.action === "generate_image" ? "image_result" : undefined)
    || (data.action === "generate_video" ? "video_result" : undefined)
    || (data.action === "generate_meme" ? "image_result" : undefined)
    || (data.type === "media_job" || data.result_type === "media_job" ? "media_job" : undefined)
    || (data.type === "coding_job" || data.result_type === "coding_job" ? "coding_job" : undefined)
    || (data.action === "capabilities" || data.action === "greeting" ? "info" : undefined)
    || (data.action === "morning_briefing" || data.type === "briefing" ? "briefing" : undefined);
}

function appendUndoButton(messageDiv) {
  if (!messageDiv || messageDiv.querySelector?.(".undo-apply-btn")) return;
  const bubble = messageDiv.querySelector?.(".bubble") || messageDiv;
  if (!bubble) return;
  const actions = document.createElement("div");
  actions.className = "proposal-actions";
  const undoBtn = document.createElement("button");
  undoBtn.className = "reject-btn undo-apply-btn";
  undoBtn.textContent = "Undo apply";
  undoBtn.onclick = () => undoLastApply(undoBtn);
  actions.appendChild(undoBtn);
  bubble.appendChild(actions);
}

function clearProposalExtras(bubble) {
  if (!bubble) return;
  bubble.querySelectorAll(
    ".diagnostics-block, .test-impact, .diff-block, .diff-truncated-note, "
    + ".proposal-actions, .agent-steps, .proposal-render-error"
  ).forEach((el) => el.remove());
}

function prepareNativeCodingResult(result) {
  if (!isNativeApp() || !result?.proposal_id) return result;
  let message = String(result.message || "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\*\*Syntax check:\*\*[\s\S]*?(?=\n\n\*\*|\n\nSay |\n\nApply|$)/i, "")
    .replace(/\*\*Pre-apply verify:\*\*[\s\S]*?(?=\n\n\*\*|\n\nSay |$)/i, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  if (message.length > 650) message = `${message.slice(0, 650)}…`;
  if (!message) message = "Code proposal ready — use **Apply** or **Dismiss** below.";
  return {
    ...result,
    message,
    diff: undefined,
    diff_omitted: true,
    agent_steps: undefined,
    diagnostics: undefined,
    test_impact: undefined,
  };
}

function attachProposalExtras(bubble, meta, messageDiv) {
  if (!bubble || !meta) return;
  try {
  const bodyText = messageDiv?.querySelector?.(".msg-body")?.dataset?.rawText
    || messageDiv?.querySelector?.(".msg-body")?.textContent
    || "";
  if (meta.agent_steps && meta.agent_steps.length && !bubble.querySelector(".agent-steps")) {
    if (!isNativeApp()) {
      const stepsEl = document.createElement("div");
      stepsEl.className = "agent-steps";
      meta.agent_steps.forEach((s) => {
        const line = document.createElement("div");
        line.className = "agent-step" + (s.ok === false ? " fail" : "");
        line.textContent = `${s.step}. ${s.action}: ${s.detail}`;
        stepsEl.appendChild(line);
      });
      bubble.appendChild(stepsEl);
    }
  }

  if (meta.diagnostics && meta.diagnostics.length && !isNativeApp() && !/syntax check/i.test(bodyText)) {
    const diagEl = document.createElement("div");
    diagEl.className = "diagnostics-block" + (meta.syntax_ok === false ? " has-errors" : "");
    const title = document.createElement("div");
    title.className = "diagnostics-title";
    if (meta.verify_ok === false) {
      title.textContent = "Pre-apply tests failed";
      diagEl.classList.add("has-errors");
    } else {
      title.textContent = meta.syntax_ok === false ? "Syntax issues found" : "Syntax check passed";
    }
    diagEl.appendChild(title);
    const pre = document.createElement("pre");
    pre.className = "diagnostics-list";
    pre.textContent = meta.diagnostics
      .slice(0, 12)
      .map((d) => `${d.path}:${d.line} [${d.severity}] (${d.source}) ${d.message}`)
      .join("\n");
    diagEl.appendChild(pre);
    bubble.appendChild(diagEl);
  }

  if (meta.test_impact && !isNativeApp() && !/tests that will run/i.test(bodyText)) {
    const ti = document.createElement("div");
    ti.className = "test-impact";
    ti.innerHTML = formatMessage(meta.test_impact);
    bubble.appendChild(ti);
  }

  if (meta.proposal_id) {
    if (meta.diff) {
      const pre = document.createElement("pre");
      mountDiffBlock(pre, meta.diff, meta);
      bubble.appendChild(pre);
    } else if (meta.diff_omitted || (isNativeApp() && !meta.diff)) {
      const note = document.createElement("div");
      note.className = "diff-truncated-note";
      note.textContent = isNativeApp()
        ? "Diff hidden in desktop app to save memory."
        : "Diff not included in this response.";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn small";
      btn.textContent = "View diff";
      btn.onclick = async () => {
        btn.disabled = true;
        btn.textContent = "Loading…";
        try {
          const res = await fetch(`/api/proposals/${encodeURIComponent(meta.proposal_id)}`);
          const data = await res.json();
          if (data.ok && data.diff) {
            const pre = document.createElement("pre");
            mountDiffBlock(pre, data.diff, { ...meta, diff_truncated: data.diff_truncated });
            note.replaceWith(pre);
          } else {
            btn.textContent = "Could not load";
            btn.disabled = false;
          }
        } catch (_) {
          btn.textContent = "Retry load";
          btn.disabled = false;
        }
      };
      note.appendChild(btn);
      bubble.appendChild(note);
    }
    const actions = document.createElement("div");
    actions.className = "proposal-actions";
    if (meta.upgrade_wizard) {
      const verifyBtn = document.createElement("button");
      verifyBtn.className = "ghost-btn";
      verifyBtn.textContent = "Verify tests";
      verifyBtn.onclick = () => runUpgradeAction("verify", meta.proposal_id, messageDiv);
      const applyBtn = document.createElement("button");
      applyBtn.className = "apply-btn";
      applyBtn.textContent = meta.verified ? "Apply upgrade" : "Apply upgrade (verify first)";
      applyBtn.onclick = () => runUpgradeAction("apply", meta.proposal_id, messageDiv);
      const rollbackBtn = document.createElement("button");
      rollbackBtn.className = "reject-btn";
      rollbackBtn.textContent = "Rollback";
      rollbackBtn.onclick = () => runUpgradeAction("rollback", "", messageDiv);
      actions.append(verifyBtn, applyBtn, rollbackBtn);
    } else {
      const applyBtn = document.createElement("button");
      applyBtn.className = "apply-btn";
      const verifyFailed = meta.verify_ok === false;
      applyBtn.textContent = verifyFailed
        ? "Apply anyway (tests failed in preview)"
        : (meta.syntax_ok === false ? "Apply anyway" : "Apply changes");
      applyBtn.onclick = () => {
        if (verifyFailed && !confirm("Pre-apply pytest failed. Apply these changes anyway?")) return;
        applyProposal(meta.proposal_id, messageDiv, meta.syntax_ok === false);
      };
      const rejectBtn = document.createElement("button");
      rejectBtn.className = "reject-btn";
      rejectBtn.textContent = "Dismiss";
      rejectBtn.onclick = () => sendMessage("don't apply that");
      actions.append(applyBtn, rejectBtn);
    }
    bubble.appendChild(actions);
  }

  if (meta.show_remember_key_points || meta.type === "knowledge_learned") {
    const actions = document.createElement("div");
    actions.className = "proposal-actions";
    const rememberBtn = document.createElement("button");
    rememberBtn.className = "apply-btn";
    rememberBtn.textContent = "Remember key points";
    rememberBtn.onclick = () => sendMessage("remember key points from that");
    actions.appendChild(rememberBtn);
    bubble.appendChild(actions);
  }

  if (meta.show_undo) {
    appendUndoButton(messageDiv);
  }
  } catch (e) {
    console.error("attachProposalExtras failed", e);
    if (messageDiv && !bubble.querySelector(".proposal-render-error")) {
      const err = document.createElement("p");
      err.className = "proposal-render-error";
      err.textContent = "Could not render proposal UI — use Apply from chat or retry.";
      bubble.appendChild(err);
    }
  }
}

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

  const mountExtras = () => attachProposalExtras(bubble, meta, div);
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

function shouldShowUndo(data) {
  if (!data || data.ok === false) return false;
  if (data.show_undo) return true;
  return data.module === "coding"
    && (data.type === "applied" || data.result_type === "applied"
      || /\b(applied changes|Done — applied)\b/i.test(data.message || ""));
}

async function applyProposal(proposalId, messageEl, force = false) {
  if (force && !confirm("This proposal has syntax errors. Apply anyway?")) return;
  const form = new FormData();
  form.append("proposal_id", proposalId);
  if (force) form.append("force", "true");
  try {
    const res = await fetch("/api/apply", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || data.ok === false) {
      addMessage("assistant", data.message || "Could not apply changes.", { module: data.module || "coding" });
      return;
    }
    addMessage("assistant", data.message || "Applied.", {
      module: data.module || "coding",
      type: "applied",
      show_undo: true,
    });
    messageEl?.querySelector?.(".proposal-actions")?.remove();
    messageEl?.querySelector?.(".diff-block")?.remove();
  } catch (e) {
    addMessage("assistant", "Failed to apply changes.");
  }
}

async function undoLastApply(triggerBtn) {
  try {
    const res = await fetch("/api/undo-apply", { method: "POST" });
    const data = await res.json();
    addMessage("assistant", data.message || (data.ok ? "Restored." : "Nothing to undo."), { module: "coding" });
    if (data.ok) {
      triggerBtn?.closest?.(".proposal-actions")?.remove();
      document.querySelectorAll(".undo-apply-btn").forEach((btn) => {
        btn.closest(".proposal-actions")?.remove();
      });
    }
  } catch (e) {
    addMessage("assistant", "Undo failed.");
  }
}

let upgradeWizardState = { proposal_id: "", verified: false, snapshot_id: "" };

async function runUpgradeAction(action, proposalId, messageEl) {
  const endpoints = {
    verify: "/api/upgrade/verify",
    apply: "/api/upgrade/apply",
    rollback: "/api/upgrade/rollback",
  };
  const url = endpoints[action];
  if (!url) return;
  const form = new FormData();
  if (proposalId) form.append("proposal_id", proposalId);
  if (action === "rollback" && upgradeWizardState.snapshot_id) {
    form.append("snapshot_id", upgradeWizardState.snapshot_id);
  }
  try {
    const res = await fetch(url, { method: "POST", body: form });
    const data = await res.json();
    addMessage("assistant", data.message || (data.ok ? "Done." : "Failed."), {
      module: "coding",
      type: data.type,
      upgrade_wizard: true,
      proposal_id: data.proposal_id || proposalId,
      verified: data.verified,
      show_undo: data.show_undo,
    });
    if (data.proposal_id) upgradeWizardState.proposal_id = data.proposal_id;
    if (data.verified) upgradeWizardState.verified = true;
    if (data.snapshot_id) upgradeWizardState.snapshot_id = data.snapshot_id;
    refreshUpgradeWizardPanel();
    messageEl?.querySelector?.(".proposal-actions")?.remove();
  } catch (_) {
    addMessage("assistant", "Upgrade action failed.");
  }
}

async function refreshUpgradeWizardPanel() {
  const stepEl = document.getElementById("upgradeWizardStep");
  const verifyBtn = document.getElementById("upgradeVerifyBtn");
  const applyBtn = document.getElementById("upgradeApplyBtn");
  const rollbackBtn = document.getElementById("upgradeRollbackBtn");
  const clearBtn = document.getElementById("upgradeClearBtn");
  if (!stepEl) return;
  try {
    const res = await fetch("/api/upgrade/status");
    const data = await res.json();
    const active = data.active || {};
    upgradeWizardState.proposal_id = active.proposal_id || upgradeWizardState.proposal_id;
    upgradeWizardState.verified = !!active.verified;
    upgradeWizardState.snapshot_id = active.snapshot_id || upgradeWizardState.snapshot_id;
    const step = active.step || "idle";
    stepEl.textContent = `Step: ${step}${active.task ? ` · ${active.task.slice(0, 60)}` : ""}`;
    if (verifyBtn) verifyBtn.disabled = !upgradeWizardState.proposal_id;
    if (applyBtn) applyBtn.disabled = !upgradeWizardState.proposal_id;
    if (rollbackBtn) rollbackBtn.disabled = !upgradeWizardState.snapshot_id && !(data.snapshots || []).length;
    const stuck = step !== "idle" || !!active.proposal_id;
    if (clearBtn) clearBtn.disabled = !stuck;
  } catch (_) {
    stepEl.textContent = "Step: offline";
  }
}

function initUpgradeWizardModal() {
  const modal = document.getElementById("upgradeWizardModal");
  const openBtn = document.getElementById("upgradeWizardBtn");
  const closeBtn = document.getElementById("upgradeWizardCloseBtn");
  const proposeBtn = document.getElementById("upgradeProposeBtn");
  const verifyBtn = document.getElementById("upgradeVerifyBtn");
  const applyBtn = document.getElementById("upgradeApplyBtn");
  const rollbackBtn = document.getElementById("upgradeRollbackBtn");
  const clearBtn = document.getElementById("upgradeClearBtn");
  const taskEl = document.getElementById("upgradeWizardTask");
  const logEl = document.getElementById("upgradeWizardLog");
  if (!modal || !openBtn) return;

  openBtn.addEventListener("click", () => {
    modal.classList.remove("hidden");
    refreshUpgradeWizardPanel();
  });
  closeBtn?.addEventListener("click", () => modal.classList.add("hidden"));

  clearBtn?.addEventListener("click", async () => {
    if (clearBtn) clearBtn.disabled = true;
    if (logEl) {
      logEl.classList.remove("hidden");
      logEl.textContent = "Clearing upgrade session…";
    }
    try {
      const res = await fetch("/api/upgrade/clear", { method: "POST" });
      const data = await res.json();
      upgradeWizardState.proposal_id = "";
      upgradeWizardState.verified = false;
      upgradeWizardState.snapshot_id = "";
      if (logEl) logEl.textContent = data.ok ? "Session cleared." : (data.message || "Clear failed.");
      window.showAriaToast?.(data.ok ? "Upgrade session cleared" : "Clear failed", data.ok ? "ok" : "err");
    } catch (e) {
      if (logEl) logEl.textContent = `Clear failed: ${e.message || e}`;
      window.showAriaToast?.(String(e.message || e), "err");
    }
    await refreshUpgradeWizardPanel();
  });

  proposeBtn?.addEventListener("click", async () => {
    const task = taskEl?.value?.trim();
    if (!task) {
      alert("Describe what to upgrade.");
      return;
    }
    if (proposeBtn) proposeBtn.disabled = true;
    if (logEl) {
      logEl.classList.remove("hidden");
      logEl.textContent = "Planning upgrade…";
    }
    try {
      const form = new FormData();
      form.append("task", task);
      const res = await fetch("/api/upgrade/propose", { method: "POST", body: form });
      const data = await res.json();
      if (logEl) logEl.textContent = data.message || (data.ok ? "Proposal ready." : "Failed.");
      addMessage("assistant", data.message || "Proposal ready.", {
        module: "coding",
        type: "upgrade_proposal",
        proposal_id: data.proposal_id,
        diff: data.diff,
        upgrade_wizard: true,
        verified: false,
        diagnostics: data.diagnostics,
        syntax_ok: data.syntax_ok,
        test_impact: data.test_impact,
      });
      if (data.proposal_id) upgradeWizardState.proposal_id = data.proposal_id;
      refreshUpgradeWizardPanel();
    } catch (_) {
      if (logEl) logEl.textContent = "Propose failed.";
    } finally {
      if (proposeBtn) proposeBtn.disabled = false;
    }
  });

  verifyBtn?.addEventListener("click", () => runUpgradeAction("verify", upgradeWizardState.proposal_id));
  applyBtn?.addEventListener("click", () => {
    if (!upgradeWizardState.verified && !confirm("Tests not verified yet. Apply anyway?")) return;
    runUpgradeAction("apply", upgradeWizardState.proposal_id);
  });
  rollbackBtn?.addEventListener("click", () => runUpgradeAction("rollback", ""));
}

initUpgradeWizardModal();

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

let chatRequestActive = false;

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
    fetch("/api/chat/cancel", { method: "POST", body: fd }).catch(() => {});
  }
  chatAbortController?.abort();
  statusText.textContent = "Stopping…";
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
  updateCompareButton();
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
    activeBranchId = data.branch_id;
    await loadBranches();
    await reloadBranchMessages();
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
    const proceed = await vramPreflight("generate_video");
    if (!proceed) {
      setChatBusy(false);
      hideProgress();
      return;
    }
  } else if (isImageRequest(text)) {
    const proceed = await vramPreflight("generate_image");
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
  if (activeBranchId) form.append("branch_id", activeBranchId);

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

const activeMediaJobs = new Set();
const MEDIA_JOBS_STORAGE_KEY = "jarvisActiveMediaJobs";
const MEDIA_SHOWN_STORAGE_KEY = "jarvisShownMediaJobs";
let mediaJobsResumeStarted = false;

function markMediaJobShown(jobId) {
  if (!jobId) return;
  try {
    const ids = JSON.parse(sessionStorage.getItem(MEDIA_SHOWN_STORAGE_KEY) || "[]");
    if (!ids.includes(jobId)) {
      ids.push(jobId);
      sessionStorage.setItem(MEDIA_SHOWN_STORAGE_KEY, JSON.stringify(ids.slice(-24)));
    }
  } catch (_) {}
}

function wasMediaJobShown(jobId) {
  if (!jobId) return false;
  try {
    return JSON.parse(sessionStorage.getItem(MEDIA_SHOWN_STORAGE_KEY) || "[]").includes(jobId);
  } catch (_) {
    return false;
  }
}

function mediaWorkActive() {
  return chatRequestActive || activeMediaJobs.size > 0;
}
window.mediaWorkActive = mediaWorkActive;

function trackMediaJob(jobId) {
  if (!jobId) return;
  try {
    const ids = JSON.parse(sessionStorage.getItem(MEDIA_JOBS_STORAGE_KEY) || "[]");
    if (!ids.includes(jobId)) {
      ids.push(jobId);
      sessionStorage.setItem(MEDIA_JOBS_STORAGE_KEY, JSON.stringify(ids.slice(-12)));
    }
  } catch (_) {}
}

function untrackMediaJob(jobId) {
  if (!jobId) return;
  try {
    const ids = JSON.parse(sessionStorage.getItem(MEDIA_JOBS_STORAGE_KEY) || "[]").filter((id) => id !== jobId);
    sessionStorage.setItem(MEDIA_JOBS_STORAGE_KEY, JSON.stringify(ids));
  } catch (_) {}
}

async function resumePendingMediaJobs() {
  if (mediaJobsResumeStarted) return;
  mediaJobsResumeStarted = true;
  const ids = new Set();
  try {
    JSON.parse(sessionStorage.getItem(MEDIA_JOBS_STORAGE_KEY) || "[]").forEach((id) => ids.add(id));
  } catch (_) {}
  try {
    const res = await fetch("/api/media/status");
    if (res.ok) {
      const data = await res.json();
      if (data.busy && data.job_id) ids.add(data.job_id);
      for (const job of data.recent || []) {
        if (job?.id && !job.done) ids.add(job.id);
      }
    }
  } catch (_) {}
  for (const jobId of ids) {
    if (!jobId || activeMediaJobs.has(jobId)) continue;
    try {
      const res = await fetch(`/api/media/job/${encodeURIComponent(jobId)}`);
      if (!res.ok) {
        untrackMediaJob(jobId);
        continue;
      }
      const data = await res.json();
      if (!data.ok) continue;
      if (data.done && data.result?.ok) {
        if (wasMediaJobShown(jobId)) {
          untrackMediaJob(jobId);
          continue;
        }
        markMediaJobShown(jobId);
        untrackMediaJob(jobId);
        const { body } = addMessage("assistant", data.result.message || "Image ready", {
          module: data.result.module || "image",
          type: "media_job",
        });
        handleDone(data.result, data.result.message || "", false, {
          targetBody: body,
          replaceQueued: true,
        });
        continue;
      }
      if (data.done) {
        untrackMediaJob(jobId);
        continue;
      }
      const { body } = addMessage("assistant", data.message || "Image job running…", {
        module: "image",
        type: "media_job",
      });
      pollMediaJob(jobId, body?.closest?.(".message"));
    } catch (_) {}
  }
}

async function pollCodingJob(jobId, messageEl) {
  if (!jobId || activeMediaJobs.has(`coding-${jobId}`)) return;
  activeMediaJobs.add(`coding-${jobId}`);

  const started = Date.now();
  const maxPollMs = 30 * 60 * 1000;
  const pollDelay = () => (isNativeApp() ? 3000 : 1500);

  const finishJob = () => {
    activeMediaJobs.delete(`coding-${jobId}`);
  };

  const tick = async () => {
    try {
      const res = await fetch(`/api/coding/job/${encodeURIComponent(jobId)}`);
      if (!res.ok) {
        if (res.status === 404 && Date.now() - started > 8000) {
          finishJob();
          const body = messageEl?.querySelector?.(".msg-body") || messageEl;
          if (body && !body.querySelector(".coding-job-lost")) {
            body.insertAdjacentHTML(
              "beforeend",
              "<p class=\"warn coding-job-lost\">Coding job was interrupted by a server restart. "
              + "Send the same request again to retry.</p>",
            );
          }
          return;
        }
        if (Date.now() - started < maxPollMs) {
          setTimeout(tick, pollDelay());
          return;
        }
        finishJob();
        return;
      }
      const data = await res.json();
      if (!data.ok) {
        if (Date.now() - started < maxPollMs) {
          setTimeout(tick, pollDelay());
          return;
        }
        finishJob();
        return;
      }
      const body = messageEl?.querySelector?.(".msg-body") || messageEl;
      if (body) {
        let note = body.querySelector(".coding-job-status");
        if (!note) {
          note = document.createElement("p");
          note.className = "coding-job-status muted";
          body.appendChild(note);
        }
        note.textContent = data.message || "Coding agent working…";
        if (data.steps?.length) {
          let stepsEl = body.querySelector(".coding-job-steps");
          if (!stepsEl) {
            stepsEl = document.createElement("ul");
            stepsEl.className = "coding-job-steps";
            body.appendChild(stepsEl);
          }
          stepsEl.innerHTML = data.steps.slice(-6).map((s) =>
            `<li>${escapeHtml(s.action)}: ${escapeHtml(s.detail || "")}</li>`,
          ).join("");
        }
        if (!body.querySelector(".coding-cancel-btn")) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "ghost-btn small coding-cancel-btn";
          btn.textContent = "Stop job";
          btn.addEventListener("click", () => {
            fetch(`/api/coding/job/${encodeURIComponent(jobId)}/cancel`, { method: "POST" });
          });
          body.appendChild(btn);
        }
      }
      if (data.done) {
        finishJob();
        if (data.result?.ok) {
          const result = prepareNativeCodingResult(data.result);
          const mountResult = () => {
            handleDone(result, result.message || "", false, {
              targetBody: body,
              replaceQueued: true,
            });
            if (isNativeApp() && window.jarvisNotify) {
              window.jarvisNotify("Coding ready", "Proposal ready — Apply or Dismiss in chat");
            }
          };
          if (isNativeApp()) {
            setTimeout(mountResult, 900);
          } else {
            mountResult();
          }
        } else if (body) {
          body.insertAdjacentHTML(
            "beforeend",
            `<p class="warn">${escapeHtml(data.error || data.result?.message || "Coding job failed")}</p>`,
          );
        }
        return;
      }
      setTimeout(tick, pollDelay());
    } catch (_) {
      if (Date.now() - started < maxPollMs) {
        setTimeout(tick, pollDelay() + 500);
      } else {
        finishJob();
      }
    }
  };
  tick();
}

window.jarvisPollCodingJob = pollCodingJob;

async function pollMediaJob(jobId, messageEl) {
  if (!jobId || activeMediaJobs.has(jobId)) return;
  activeMediaJobs.add(jobId);
  syncMediaBusyClass();
  trackMediaJob(jobId);
  const started = Date.now();
  const maxPollMs = 10 * 60 * 1000;
  const pollDelay = () => (isNativeApp() ? 5000 : 2200);

  const finishJob = () => {
    activeMediaJobs.delete(jobId);
    syncMediaBusyClass();
    untrackMediaJob(jobId);
  };

  const tick = async () => {
    try {
      const res = await fetch(`/api/media/job/${encodeURIComponent(jobId)}`);
      if (!res.ok) {
        if (res.status === 404 && Date.now() - started > 8000) {
          finishJob();
          const body = messageEl?.querySelector?.(".msg-body") || messageEl;
          if (body) {
            body.insertAdjacentHTML(
              "beforeend",
              '<p class="warn">Lost track of this job after a server restart. Check <strong>Gallery</strong> for your image.</p>',
            );
          }
          return;
        }
        if (Date.now() - started < maxPollMs) {
          setTimeout(tick, pollDelay());
          return;
        }
        finishJob();
        return;
      }
      const data = await res.json();
      if (!data.ok) {
        if (Date.now() - started < maxPollMs) {
          setTimeout(tick, pollDelay());
          return;
        }
        finishJob();
        return;
      }
      const body = messageEl?.querySelector?.(".msg-body") || messageEl;
      if (body) {
        let note = body.querySelector(".media-job-status");
        if (!note) {
          note = document.createElement("p");
          note.className = "media-job-status muted";
          body.appendChild(note);
        }
        note.textContent = data.message || "Working…";
      }
      if (data.done) {
        finishJob();
        if (data.result?.ok) {
          markMediaJobShown(jobId);
          handleDone(data.result, data.result.message || "", false, { targetBody: body, replaceQueued: true });
        } else if (body) {
          body.insertAdjacentHTML(
            "beforeend",
            `<p class="warn">${escapeHtml(data.error || data.result?.message || "Media job failed")}</p>`,
          );
        }
        return;
      }
      setTimeout(tick, pollDelay());
    } catch (_) {
      if (Date.now() - started < maxPollMs) setTimeout(tick, pollDelay());
      else finishJob();
    }
  };
  tick();
}

function handleDone(data, text, streamed = false, options = {}) {
  if (isNativeApp() && data?.proposal_id) {
    data = prepareNativeCodingResult(data);
    text = data.message || text;
  }
  const meta = {
    module: data.module,
    type: resolveMetaType(data),
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
    show_undo: shouldShowUndo(data),
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
      clearProposalExtras(bubble);
    }
    options.targetBody.innerHTML = formatMessage(text || data.message || "");
    syncMessageRawText(options.targetBody, text || data.message || "");
    ensureMessageCopyAction(messageEl, options.targetBody);
    if (bubble && (meta.proposal_id || meta.diagnostics || meta.agent_steps)) {
      const mount = () => attachProposalExtras(bubble, meta, messageEl);
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
      const mount = () => attachProposalExtras(bubble, meta, lastMsg);
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
    if (window.jarvisPollCodingJob) window.jarvisPollCodingJob(data.job_id, msg);
    else pollCodingJob(data.job_id, msg);
  } else if (
    data.job_id
    && (data.type === "media_job" || data.result_type === "media_job" || data.pending)
  ) {
    const msg = options.targetBody?.closest?.(".message")
      || document.querySelector(".message.assistant:last-child");
    pollMediaJob(data.job_id, msg);
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
    setTimeout(() => { if (galleryViewVisible()) loadGallery(); }, 800);
  }
}

window.handleDone = handleDone;

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value;
  messageInput.value = "";
  messageInput.style.height = "auto";
  resizeMessageInput();
  sendMessage(text);
});

messageInput.addEventListener("input", resizeMessageInput);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

function updateCompareButton() {
  const btn = document.getElementById("compareModeBtn");
  if (!btn) return;
  const count = (pendingFile ? 1 : 0) + (pendingFile2 ? 1 : 0);
  btn.classList.toggle("active", compareMode || Boolean(pendingFile2));
  if (pendingFile2) {
    btn.title = "Two images ready — send to compare";
  } else if (compareMode) {
    btn.title = count ? "Compare mode: add a second image" : "Compare mode: pick two images";
  } else {
    btn.title = "Compare two images (select both in one dialog)";
  }
}

function enterCompareMode() {
  compareMode = true;
  updateCompareButton();
  const fi = document.getElementById("fileInput");
  if (!fi) return;
  if (!pendingFile) {
    fi.setAttribute("multiple", "");
    fi.click();
  } else if (!pendingFile2) {
    document.getElementById("fileInput2")?.click();
  }
}

function exitCompareMode() {
  compareMode = false;
  pendingFile2 = null;
  document.getElementById("fileInput")?.removeAttribute("multiple");
  updateCompareButton();
  updateAttachmentPreview();
}

function updateAttachmentPreview() {
  if (!attachmentPreview) return;
  if (!pendingFile && !pendingFile2) {
    attachmentPreview.classList.add("hidden");
    updateCompareButton();
    return;
  }
  attachmentPreview.classList.remove("hidden");
  const parts = [];
  [pendingFile, pendingFile2].filter(Boolean).forEach((f, i) => {
    let preview = "";
    if (isVisionAttachment(f)) {
      preview = `<img src="${URL.createObjectURL(f)}" alt="" class="attach-thumb" /> `;
    }
    const label = pendingFile2 ? `Image ${i + 1}: ` : "";
    parts.push(`${preview}${label}📎 ${escapeHtml(f.name)}`);
  });
  const dataBadge = pendingFile && isDataAttachment(pendingFile) && !pendingFile2
    ? `<span class="compare-badge data-badge">Data file</span>`
    : "";
  const compareBadge = pendingFile2
    ? `<span class="compare-badge">Compare · 2 images</span>`
    : compareMode
      ? `<span class="compare-badge warn">Compare · 1/2 — add second image</span>`
      : "";
  const addSecond = compareMode && pendingFile && !pendingFile2
    ? `<button type="button" id="addSecondImgBtn" class="ghost-btn small">+ Add image 2</button>`
    : "";
  const cancelCompare = compareMode || pendingFile2
    ? `<button type="button" id="cancelCompareBtn" class="ghost-btn small">Cancel compare</button>`
    : "";
  const isVideo = pendingFile && /^video\//i.test(pendingFile.type);
  const isPdf = pendingFile && (pendingFile.type === "application/pdf" || /\.pdf$/i.test(pendingFile.name));
  const isDoc = pendingFile && (/\.docx$/i.test(pendingFile.name)
    || pendingFile.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
  const docBadge = (isPdf || isDoc) && !pendingFile2
    ? `<span class="compare-badge data-badge">Document · try “Summarize this warranty PDF”</span>`
    : "";
  const videoOpts = isVideo
    ? `<label class="attach-opt">Frame at <input type="text" id="videoSecondInput" placeholder="0:45 or 12s" value="${escapeHtml(pendingVideoSecond)}" class="attach-mini-input" /></label>`
    : "";
  const pdfOpts = isPdf
    ? `<label class="attach-opt">Page <input type="number" id="pdfPageInput" min="1" value="${escapeHtml(pendingPdfPage)}" class="attach-mini-input" title="For OCR/vision only" /></label>`
    : "";
  const cropBtn = pendingFile && isVisionAttachment(pendingFile) && !pendingFile2
    ? `<button type="button" id="cropAttachBtn" class="ghost-btn small">Crop</button>`
    : "";
  attachmentPreview.innerHTML = `${dataBadge} ${docBadge} ${compareBadge} ${parts.join(" · ")} ${videoOpts} ${pdfOpts} ${addSecond} ${cropBtn} ${cancelCompare} <button type="button" aria-label="Remove">×</button>`;
  document.getElementById("videoSecondInput")?.addEventListener("change", (e) => {
    pendingVideoSecond = e.target.value;
  });
  document.getElementById("pdfPageInput")?.addEventListener("change", (e) => {
    pendingPdfPage = e.target.value || "1";
  });
  attachmentPreview.querySelector("button[aria-label='Remove']")?.addEventListener("click", () => {
    pendingFile = null;
    pendingFile2 = null;
    pendingCrop = null;
    compareMode = false;
    if (fileInput) fileInput.value = "";
    const fi2 = document.getElementById("fileInput2");
    if (fi2) fi2.value = "";
    fileInput?.removeAttribute("multiple");
    attachmentPreview.classList.add("hidden");
    updateCompareButton();
  });
  document.getElementById("addSecondImgBtn")?.addEventListener("click", () => {
    compareMode = true;
    document.getElementById("fileInput2")?.click();
  });
  document.getElementById("cancelCompareBtn")?.addEventListener("click", () => {
    exitCompareMode();
  });
  document.getElementById("cropAttachBtn")?.addEventListener("click", openCropModal);
  updateCompareButton();
}

function assignAttachment(file, asSecond = false) {
  if (!file) return;
  if (asSecond || (compareMode && pendingFile)) {
    if (!pendingFile) pendingFile = file;
    else pendingFile2 = file;
  } else if (compareMode) {
    pendingFile = file;
  } else {
    pendingFile = file;
    pendingFile2 = null;
  }
  updateAttachmentPreview();
  if (isDataAttachment(pendingFile)) refreshDataChips();
  else refreshVisionChips();
}

function assignMultipleAttachments(files) {
  const imgs = files.filter((f) => isVisionAttachment(f) || /^image\//i.test(f.type));
  if (!imgs.length) return;
  compareMode = true;
  pendingFile = imgs[0];
  pendingFile2 = imgs.length >= 2 ? imgs[1] : null;
  updateAttachmentPreview();
  if (isDataAttachment(pendingFile)) refreshDataChips();
  else refreshVisionChips();
  if (compareMode && pendingFile && !pendingFile2) {
    setTimeout(() => document.getElementById("fileInput2")?.click(), 250);
  }
}

fileInput?.addEventListener("change", () => {
  const files = fileInput.files ? Array.from(fileInput.files) : [];
  fileInput?.removeAttribute("multiple");
  if (!files.length) return;
  if (files.length >= 2) {
    assignMultipleAttachments(files);
    fileInput.value = "";
    return;
  }
  assignAttachment(files[0], compareMode && Boolean(pendingFile));
  fileInput.value = "";
});

document.getElementById("fileInput2")?.addEventListener("change", (e) => {
  const f = e.target.files[0];
  if (f) {
    compareMode = true;
    assignAttachment(f, true);
  }
  e.target.value = "";
});

document.getElementById("compareModeBtn")?.addEventListener("click", () => {
  if (pendingFile && pendingFile2) {
    messageInput.value = "Compare these two images. Describe similarities and differences.";
    messageInput.focus();
    return;
  }
  enterCompareMode();
});

function refreshDataChips() {
  if (!suggestionsEl || !dataChips.length) return;
  if (!isDataAttachment(pendingFile)) return;
  suggestionsEl.innerHTML = "";
  dataChips.forEach((s) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "suggestion-chip data-chip";
    chip.textContent = s;
    chip.onclick = () => { messageInput.value = s; messageInput.focus(); };
    suggestionsEl.appendChild(chip);
  });
}

function refreshVisionChips() {
  if (!suggestionsEl || !visionChips.length) return;
  if (!pendingFile && !pendingFile2) return;
  suggestionsEl.innerHTML = "";
  const chips = pendingFile2
    ? ["Compare these two images. Describe similarities and differences."]
    : visionChips;
  chips.forEach((s) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "suggestion-chip vision-chip";
    chip.textContent = s;
    chip.onclick = () => { messageInput.value = s; messageInput.focus(); };
    suggestionsEl.appendChild(chip);
  });
}

async function loadVisionSettings() {
  const sel = document.getElementById("visionQualitySelect");
  const note = document.getElementById("visionStatusNote");
  try {
    const res = await fetch("/api/vision/settings");
    const data = await res.json();
    if (sel && data.quality_mode) sel.value = data.quality_mode;
    if (note) {
      note.textContent = data.low_vram
        ? `Vision: ${data.model || "?"} · ${data.vram_gb || "?"}GB VRAM (fast mode recommended)`
        : `Vision: ${data.model || "?"}`;
    }
  } catch (_) {}
}

document.getElementById("visionQualitySelect")?.addEventListener("change", async (e) => {
  const form = new FormData();
  form.append("quality_mode", e.target.value);
  await fetch("/api/vision/settings", { method: "POST", body: form });
  await loadVisionSettings();
  await loadModelSettings();
});

function openCropModal() {
  if (!pendingFile || !isVisionAttachment(pendingFile)) return;
  const modal = document.getElementById("cropModal");
  const canvas = document.getElementById("cropCanvas");
  if (!modal || !canvas) return;
  const ctx = canvas.getContext("2d");
  const img = new Image();
  img.onload = () => {
    const maxW = 640;
    const scale = Math.min(1, maxW / img.width);
    canvas.width = Math.round(img.width * scale);
    canvas.height = Math.round(img.height * scale);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    modal.classList.remove("hidden");
    let start = null;
    let rect = null;
    const redraw = () => {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      if (rect) {
        ctx.strokeStyle = "#d4a054";
        ctx.lineWidth = 2;
        ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);
      }
    };
    canvas.onmousedown = (ev) => {
      start = { x: ev.offsetX, y: ev.offsetY };
      rect = null;
    };
    canvas.onmousemove = (ev) => {
      if (!start) return;
      rect = {
        x: Math.min(start.x, ev.offsetX),
        y: Math.min(start.y, ev.offsetY),
        w: Math.abs(ev.offsetX - start.x),
        h: Math.abs(ev.offsetY - start.y),
      };
      redraw();
    };
    canvas.onmouseup = () => { start = null; };
    document.getElementById("cropApplyBtn").onclick = () => {
      if (rect && rect.w > 4 && rect.h > 4) {
        pendingCrop = {
          x: rect.x / canvas.width,
          y: rect.y / canvas.height,
          w: rect.w / canvas.width,
          h: rect.h / canvas.height,
        };
      }
      modal.classList.add("hidden");
      updateAttachmentPreview();
    };
    document.getElementById("cropCancelBtn").onclick = () => modal.classList.add("hidden");
  };
  img.src = URL.createObjectURL(pendingFile);
}

function initVisionDropPaste() {
  const chatView = document.getElementById("chatView");
  const overlay = document.getElementById("dropOverlay");
  if (!chatView) return;

  chatView.addEventListener("dragover", (e) => {
    if (![...e.dataTransfer.types].includes("Files")) return;
    e.preventDefault();
    overlay?.classList.remove("hidden");
  });
  chatView.addEventListener("dragleave", (e) => {
    if (e.target === chatView) overlay?.classList.add("hidden");
  });
  chatView.addEventListener("drop", (e) => {
    e.preventDefault();
    overlay?.classList.add("hidden");
    const imgs = [...e.dataTransfer.files].filter(
      (f) => isVisionAttachment(f) || /^image\//i.test(f.type),
    );
    if (imgs.length >= 2) {
      assignMultipleAttachments(imgs);
    } else if (imgs.length === 1) {
      assignAttachment(imgs[0], compareMode && Boolean(pendingFile));
    }
  });

  document.addEventListener("paste", (e) => {
    if (isTextEntryElement(e.target)) return;
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        const blob = item.getAsFile();
        if (blob) {
          e.preventDefault();
          assignAttachment(new File([blob], `paste-${Date.now()}.png`, { type: blob.type }));
          break;
        }
      }
    }
  });
}

initVisionDropPaste();

document.getElementById("webcamBtn")?.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
    const video = document.createElement("video");
    video.srcObject = stream;
    await video.play();
    await new Promise((r) => setTimeout(r, 400));
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    canvas.getContext("2d").drawImage(video, 0, 0);
    stream.getTracks().forEach((t) => t.stop());
    canvas.toBlob((blob) => {
      if (!blob) return;
      assignAttachment(new File([blob], `webcam-${Date.now()}.jpg`, { type: "image/jpeg" }));
    }, "image/jpeg", 0.92);
  } catch (e) {
    showError(`Webcam unavailable: ${e.message || e}`);
  }
});

clearBtn.addEventListener("click", async () => {
  const f = new FormData();
  f.append("message", "clear");
  if (activeBranchId) f.append("branch_id", activeBranchId);
  await fetch("/api/chat", { method: "POST", body: f });
  messagesEl.innerHTML = "";
  addMessage("assistant", "Fresh start. What would you like to do?");
});


readAloudBtn.addEventListener("click", async () => {
  if (!lastAssistantText) return;
  readAloudBtn.disabled = true;
  statusText.textContent = "Speaking on Sound Blaster…";
  try {
    const form = new FormData();
    form.append("text", lastAssistantText.replace(/[*`#]/g, "").slice(0, 4000));
    const res = await fetch("/api/audio/speak", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) showError(data.message || "Could not play audio.");
    else statusText.textContent = "Ready · Sound Blaster";
  } catch (e) {
    showError(`Audio playback failed: ${e.message}`);
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
  recognition.onerror = () => micBtn.classList.remove("listening");
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

    if (fresh && file !== lastEditorFile) {
      lastEditorFile = file;
      refreshEditorSuggestions(file, ctx.has_selection);
    }
    return { fresh, file, ctx };
  } catch (_) {
    return null;
  }
}

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

function sendQuickCodingMessage(msg) {
  if (!msg) return;
  const file = lastEditorFile;
  let text = msg;
  if (msg === "run tests for") {
    if (file) text = `run tests for ${file}`;
    else {
      messageInput.value = "run tests for ";
      messageInput.focus();
      return;
    }
  }
  messageInput.value = text;
  sendMessage(text);
}

editorContextPill?.addEventListener("click", () => sendQuickCodingMessage("editor context"));
editorContextCard?.addEventListener("click", () => sendQuickCodingMessage("editor context"));
document.querySelectorAll(".coding-quick-btn").forEach((btn) => {
  btn.addEventListener("click", () => sendQuickCodingMessage(btn.dataset.msg || ""));
});

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
    if (isDataAttachment(pendingFile)) refreshDataChips();
    else if (pendingFile || pendingFile2) refreshVisionChips();
    const ed = await loadEditorContext();
    if (ed?.fresh && ed.file) refreshEditorSuggestions(ed.file, ed.ctx?.has_selection);
  } catch (_) {}
}

async function freeJarvisVram(statusEl) {
  const target = statusEl || statusText;
  if (target) target.textContent = "Freeing VRAM…";
  try {
    const res = await fetch("/api/gpu/free-vram", { method: "POST" });
    const data = await res.json();
    const n = (data.unloaded_ollama || []).length;
    const msg = data.ok
      ? `VRAM freed${n ? ` (${n} Ollama model${n === 1 ? "" : "s"} unloaded)` : ""}`
      : (data.message || "Free VRAM failed");
    if (target) target.textContent = msg;
    loadGpuStatus();
    return data;
  } catch (e) {
    if (target) target.textContent = String(e);
    throw e;
  }
}

window.freeJarvisVram = freeJarvisVram;

function renderGpuStatus(gpu) {
  if (window.jarvisHealth?.renderGpuStatus) {
    window.jarvisHealth.renderGpuStatus(gpu);
    return;
  }
}

document.getElementById("freeVramBtn")?.addEventListener("click", () => freeJarvisVram(statusText));

function renderAudioStatus(audio) {
  if (!gpuStatusEl || !audio) return;
  let line = gpuStatusEl.querySelector(".audio-line");
  if (!line) {
    line = document.createElement("div");
    line.className = "audio-line gpu-status ok";
    gpuStatusEl.appendChild(line);
  }
  line.textContent = `Audio: ${(audio.name || "Sound Blaster").slice(0, 45)}`;
  line.title = `Output: ${audio.output_sink || ""}\nInput: ${audio.input_source || ""}`;
}

async function loadGpuStatus() {
  if (window.jarvisHealth?.loadGpuStatus) {
    await window.jarvisHealth.loadGpuStatus();
  }
}

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
      if (statusText && activeMediaJobs.size > 0) {
        statusText.textContent = "Server reconnecting — image job still running…";
      }
      return;
    }
    const data = await res.json();
    if (jarvisServerWasDown) {
      jarvisServerWasDown = false;
      if (statusText) {
        statusText.textContent = activeMediaJobs.size > 0
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
  if (comfySettings) syncComfySettings(comfySettings);
}

const galleryModeSelect = document.getElementById("galleryModeSelect");
const galleryCheckpointSelect = document.getElementById("galleryCheckpointSelect");
const galleryCheckpointFileSelect = document.getElementById("galleryCheckpointFileSelect");
const galleryWorkflowInput = document.getElementById("galleryWorkflowInput");
const imageEngineStatus = document.getElementById("imageEngineStatus");
const imageEngineInstallHint = document.getElementById("imageEngineInstallHint");
const imageEngineInstallNsfwBtn = document.getElementById("imageEngineInstallNsfwBtn");
const imageEngineUncensoredBanner = document.getElementById("imageEngineUncensoredBanner");
const openComfyUiLink = document.getElementById("openComfyUiLink");
let comfyModeBusy = false;
let lastComfySettings = null;

function populateCheckpointFileSelect(settings) {
  if (!galleryCheckpointFileSelect || !settings) return;
  const files = settings.all_checkpoints || [];
  const active = settings.checkpoint_file || "__preset__";
  const options = ['<option value="__preset__">Use preset above</option>'];
  for (const file of files) {
    const label = `${file.family} · ${file.name} (${file.size_mb} MB)`;
    options.push(`<option value="${escapeHtml(file.name)}">${escapeHtml(label)}</option>`);
  }
  galleryCheckpointFileSelect.innerHTML = options.join("");
  galleryCheckpointFileSelect.value = settings.checkpoint_file || "__preset__";
  if (galleryCheckpointFileSelect.value !== active && active !== "__preset__") {
    galleryCheckpointFileSelect.value = active;
  }
}

function updateImageEngineStatus(settings) {
  if (!settings) return;
  lastComfySettings = settings;
  if (openComfyUiLink && settings.comfyui_url) {
    openComfyUiLink.href = settings.comfyui_url;
  }
  populateCheckpointFileSelect(settings);
  if (galleryModeSelect && settings.mode) {
    galleryModeSelect.value = settings.mode;
  }
  if (galleryCheckpointSelect && settings.checkpoint) {
    galleryCheckpointSelect.value = settings.checkpoint;
  }
  if (galleryWorkflowInput && settings.workflow_file_active) {
    galleryWorkflowInput.value = settings.workflow_file_active;
  } else if (galleryWorkflowInput && settings.workflow_file) {
    galleryWorkflowInput.value = settings.workflow_file;
  }
  const active = settings.checkpoint_file_active || settings.checkpoint_label || settings.checkpoint;
  const statusParts = [
    settings.running ? "ComfyUI online" : "ComfyUI offline",
    `Active: ${active}`,
    settings.label || settings.effective || settings.mode,
  ];
  if (settings.prompt_model) {
    statusParts.push(`Prompt LLM: ${settings.prompt_model}`);
  }
  if (settings.workflow_file_active) {
    statusParts.push(`Workflow: ${settings.workflow_file_active.split("/").pop()}`);
  }
  if (imageEngineStatus) {
    imageEngineStatus.textContent = statusParts.filter(Boolean).join(" · ");
    imageEngineStatus.classList.toggle("muted", settings.running);
  }
  if (imageEngineUncensoredBanner) {
    if (settings.uncensored_mode) {
      const rec = settings.uncensored_recommended_label || settings.uncensored_recommended_checkpoint;
      const install = settings.install_scripts?.nsfw || "./scripts/install-nsfw-checkpoints.sh";
      let banner = `<strong>Uncensored mode</strong> — prompt expansion uses <code>${escapeHtml(settings.prompt_model || "dolphin3:latest")}</code>`;
      if (rec) {
        banner += `. Recommended checkpoint: <strong>${escapeHtml(rec)}</strong>`;
      } else {
        banner += `. Install NSFW checkpoints: <code>${escapeHtml(install)}</code>`;
      }
      imageEngineUncensoredBanner.innerHTML = banner;
      imageEngineUncensoredBanner.classList.remove("hidden");
    } else {
      imageEngineUncensoredBanner.textContent = "";
      imageEngineUncensoredBanner.classList.add("hidden");
    }
  }
  if (imageEngineInstallHint) {
    const files = settings.all_checkpoints || [];
    let hint = "";
    if (settings.uncensored_mode && !settings.uncensored_recommended_checkpoint) {
      hint = `Uncensored mode: run ${settings.install_scripts?.nsfw || "./scripts/install-nsfw-checkpoints.sh"} (~16 GB total)`;
    } else if (settings.checkpoint === "quality" && settings.installed && !settings.installed.quality) {
      hint = `SDXL 1.0 not installed. Run ${settings.install_scripts?.quality || "./scripts/install-sdxl-base.sh"}`;
    } else if (settings.checkpoint === "flux" && settings.installed && !settings.installed.flux) {
      hint = `Flux Schnell not installed. Run ${settings.install_scripts?.flux || "./scripts/install-flux-schnell.sh"}`;
    } else if (!files.length && settings.checkpoints_dir) {
      hint = `No checkpoints in ${settings.checkpoints_dir}. Install SDXL or Flux using the scripts above.`;
    }
    imageEngineInstallHint.textContent = hint;
    imageEngineInstallHint.classList.toggle("hidden", !hint);
  }
  if (imageEngineInstallNsfwBtn) {
    const showNsfw = Boolean(
      settings.uncensored_mode && !settings.uncensored_recommended_checkpoint,
    );
    imageEngineInstallNsfwBtn.classList.toggle("hidden", !showNsfw);
    imageEngineInstallNsfwBtn.disabled = imageEngineInstallNsfwBtn.dataset.running === "1";
  }
}

imageEngineInstallNsfwBtn?.addEventListener("click", async () => {
  if (!imageEngineInstallNsfwBtn || imageEngineInstallNsfwBtn.dataset.running === "1") return;
  imageEngineInstallNsfwBtn.disabled = true;
  imageEngineInstallNsfwBtn.textContent = "Starting download…";
  try {
    const res = await fetch("/api/comfyui/install-nsfw", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      statusText.textContent = data.message || "Could not start NSFW install";
      imageEngineInstallNsfwBtn.disabled = false;
      imageEngineInstallNsfwBtn.textContent = "Install NSFW checkpoints";
      return;
    }
    imageEngineInstallNsfwBtn.dataset.running = "1";
    imageEngineInstallNsfwBtn.textContent = "Downloading (~44 GB)…";
    statusText.textContent = data.message || "NSFW checkpoint download started";
    const poll = setInterval(async () => {
      try {
        const st = await (await fetch("/api/comfyui/install-nsfw/status")).json();
        if (!st.running) {
          clearInterval(poll);
          imageEngineInstallNsfwBtn.dataset.running = "0";
          imageEngineInstallNsfwBtn.textContent = "Install NSFW checkpoints";
          imageEngineInstallNsfwBtn.disabled = false;
          await loadComfyMode();
        }
      } catch (_) {}
    }, 8000);
  } catch (_) {
    imageEngineInstallNsfwBtn.disabled = false;
    imageEngineInstallNsfwBtn.textContent = "Install NSFW checkpoints";
  }
});

function syncComfySettings(settings) {
  if (comfyModeBusy || !settings) return;
  updateImageEngineStatus(settings);
}

async function loadComfyMode() {
  if (!galleryModeSelect && !galleryCheckpointSelect) return;
  try {
    const res = await fetch("/api/comfyui/settings");
    if (!res.ok) return;
    syncComfySettings(await res.json());
  } catch (_) {}
}

async function postComfySettings(fields) {
  comfyModeBusy = true;
  if (galleryModeSelect) galleryModeSelect.disabled = true;
  if (galleryCheckpointSelect) galleryCheckpointSelect.disabled = true;
  if (galleryCheckpointFileSelect) galleryCheckpointFileSelect.disabled = true;
  statusText.textContent = fields.mode ? "Restarting ComfyUI…" : "Updating image model…";
  try {
    const form = new FormData();
    if (fields.mode) form.append("mode", fields.mode);
    if (fields.checkpoint) form.append("checkpoint", fields.checkpoint);
    if (fields.checkpoint_file) form.append("checkpoint_file", fields.checkpoint_file);
    if (fields.workflow_file) form.append("workflow_file", fields.workflow_file);
    const res = await fetch("/api/comfyui/settings", { method: "POST", body: form });
    let data = await res.json();
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || `HTTP ${res.status}`);
    }
    if (data.pending && data.job_id) {
      data = await pollComfySettingsJob(data.job_id);
    }
    syncComfySettings(data);
    const svcRes = await fetch("/api/services");
    if (svcRes.ok) {
      const svcData = await svcRes.json();
      renderServices(svcData.services, svcData.comfyui_settings);
    }
    statusText.textContent = `ComfyUI · ${data.checkpoint_label || "SDXL"} · ${data.label || ""}`.trim();
    return data;
  } finally {
    if (galleryModeSelect) galleryModeSelect.disabled = false;
    if (galleryCheckpointSelect) galleryCheckpointSelect.disabled = false;
    if (galleryCheckpointFileSelect) galleryCheckpointFileSelect.disabled = false;
    comfyModeBusy = false;
  }
}

async function setComfyMode(mode) {
  if (!galleryModeSelect || comfyModeBusy) return;
  const prev = galleryModeSelect.value;
  try {
    await postComfySettings({ mode });
  } catch (e) {
    galleryModeSelect.value = prev;
    statusText.textContent = `ComfyUI switch failed — ${e.message}`;
  }
}

async function setComfyCheckpoint(checkpoint) {
  if (!galleryCheckpointSelect || comfyModeBusy) return;
  const prev = galleryCheckpointSelect.value;
  const prevFile = galleryCheckpointFileSelect?.value;
  try {
    await postComfySettings({ checkpoint });
  } catch (e) {
    galleryCheckpointSelect.value = prev;
    if (galleryCheckpointFileSelect && prevFile) galleryCheckpointFileSelect.value = prevFile;
    statusText.textContent = `Model switch failed — ${e.message}`;
  }
}

async function setComfyCheckpointFile(filename) {
  if (!galleryCheckpointFileSelect || comfyModeBusy) return;
  const prev = galleryCheckpointFileSelect.value;
  try {
    await postComfySettings({ checkpoint_file: filename });
  } catch (e) {
    galleryCheckpointFileSelect.value = prev;
    statusText.textContent = `Checkpoint switch failed — ${e.message}`;
  }
}

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
  if (view === "security" && window.initSecurity) window.initSecurity();
  if (view === "presence" && window.initPresence) window.initPresence();
  if (view === "audit" && window.initAudit) window.initAudit();
  if (view === "voice" && window.initVoiceTab) window.initVoiceTab();
  if (view === "audio" && window.initAudio) window.initAudio();
  if (view === "journal" && window.initJournal) window.initJournal();
  if (view === "memory") loadMemoryBrowser();
  if (view === "gallery") loadGallery();
  if (view === "video" && typeof loadVideoGallery === "function") loadVideoGallery();
  if (view === "meme" && typeof loadMemeGallery === "function") loadMemeGallery();
  if (view === "actions") loadActions();
  if (view === "documents" && window.loadDocumentsTab) window.loadDocumentsTab();
  document.querySelector(`.view-tab[data-view="${view}"]`)?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

function resetSidebarLayout() {
  localStorage.removeItem("jarvis_sidebar_collapsed");
  document.querySelectorAll(".sidebar-section.collapsed").forEach((sec) => {
    sec.classList.remove("collapsed");
    const head = sec.querySelector(".sidebar-section-head");
    if (head) head.setAttribute("aria-expanded", "true");
  });
  document.body.classList.remove("mobile-sidebar-open");
}

window.switchToView = switchToView;
window.resetSidebarLayout = resetSidebarLayout;

if (galleryModeSelect) {
  galleryModeSelect.addEventListener("change", () => setComfyMode(galleryModeSelect.value));
}
if (galleryCheckpointSelect) {
  galleryCheckpointSelect.addEventListener("change", () => setComfyCheckpoint(galleryCheckpointSelect.value));
}
if (galleryCheckpointFileSelect) {
  galleryCheckpointFileSelect.addEventListener("change", () => setComfyCheckpointFile(galleryCheckpointFileSelect.value));
}
galleryWorkflowInput?.addEventListener("change", async () => {
  const path = galleryWorkflowInput.value.trim();
  if (!path) return;
  try {
    await postComfySettings({ workflow_file: path });
  } catch (e) {
    statusText.textContent = `Workflow failed — ${e.message}`;
  }
});
document.getElementById("galleryGenerateBtn")?.addEventListener("click", () => {
  const prompt = document.getElementById("galleryPromptInput")?.value?.trim();
  if (!prompt) {
    window.showAriaToast?.("Enter an image description first", "warn");
    document.getElementById("galleryPromptInput")?.focus();
    return;
  }
  switchToView("chat");
  sendMessage(`generate image: ${prompt}`);
});
document.getElementById("galleryPromptInput")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    document.getElementById("galleryGenerateBtn")?.click();
  }
});
document.getElementById("openImageSettingsBtn")?.addEventListener("click", () => {
  switchToView("gallery");
  document.getElementById("imageEnginePanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
});
document.getElementById("openVideoStudioBtn")?.addEventListener("click", () => {
  switchToView("video");
  document.body.classList.remove("mobile-sidebar-open");
  refreshSidebarVideoStatus();
});
document.getElementById("openVideoGalleryBtn")?.addEventListener("click", () => {
  switchToView("video");
  document.getElementById("videoGalleryGrid")?.scrollIntoView({ behavior: "smooth", block: "start" });
  document.body.classList.remove("mobile-sidebar-open");
  refreshSidebarVideoStatus();
});
document.getElementById("sidebarVideoFreeVramBtn")?.addEventListener("click", async () => {
  if (typeof window.freeJarvisVram === "function") window.freeJarvisVram(statusText);
  await refreshSidebarVideoStatus();
});

async function refreshSidebarVideoStatus() {
  const el = document.getElementById("sidebarVideoStatus");
  if (!el) return;
  try {
    const res = await fetch("/api/resources");
    const data = await res.json().catch(() => ({}));
    const free = data.free_vram_mb ?? data.vram_free_mb;
    const total = data.vram_mb;
    const line = data.status_line || (
      free != null && total != null
        ? `${Math.round(free)} / ${Math.round(total)} MB VRAM free`
        : null
    );
    el.textContent = line
      ? `AnimateDiff · Ken Burns · ${line}`
      : "AnimateDiff · Ken Burns · chat: “make a video…”";
  } catch (_) {
    el.textContent = "AnimateDiff · Ken Burns · chat: “make a video…”";
  }
}
document.addEventListener("DOMContentLoaded", () => {
  refreshSidebarVideoStatus();
});

document.getElementById("mobileMenuBtn")?.addEventListener("click", () => {
  document.body.classList.toggle("mobile-sidebar-open");
});
document.querySelector(".sidebar-backdrop")?.addEventListener("click", () => {
  document.body.classList.remove("mobile-sidebar-open");
});

function fetchWithTimeout(url, options = {}, timeoutMs = 5000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  return fetch(url, { ...options, signal: ctrl.signal }).finally(() => clearTimeout(timer));
}

function hideStartupOverlay(message) {
  if (startupStatus && message) startupStatus.textContent = message;
  startupOverlay?.classList.add("hidden");
  window.jarvisFlashSystemsOnline?.();
}

function appendStartupLog(msg) {
  if (!startupLog || !msg) return;
  const li = document.createElement("li");
  li.textContent = msg;
  startupLog.appendChild(li);
  startupLog.scrollTop = startupLog.scrollHeight;
}

async function waitForServices(maxAttempts = 12) {
  if (!startupOverlay) return true;
  try {
    const live = await fetchWithTimeout("/api/live", {}, 2500);
    if (live.ok) {
      const data = await live.json();
      if (data.ready) {
        hideStartupOverlay(`${ariaName()} ready.`);
        return true;
      }
    }
  } catch (_) {
    /* server may be busy with ComfyUI — show overlay below */
  }
  startupOverlay.classList.remove("hidden");
  startupStatus.textContent = "Bringing services online…";
  let ensured = false;

  for (let i = 0; i < maxAttempts; i++) {
    try {
      let res = await fetchWithTimeout("/api/services", {}, 4000);
      if (!res.ok && !ensured) {
        ensured = true;
        await fetchWithTimeout("/api/services/ensure", { method: "POST" }, 8000);
        await new Promise((r) => setTimeout(r, 800));
        res = await fetchWithTimeout("/api/services", {}, 4000);
      }
      if (res.ok) {
        const data = await res.json();
        if (data.boot_log) data.boot_log.slice(-5).forEach(appendStartupLog);
        renderServices(data.services, data.comfyui_settings);
        if (data.ready) {
          try {
            const sumRes = await fetchWithTimeout("/api/workstation/startup-summary", {}, 4000);
            if (sumRes.ok) {
              const summary = await sumRes.json();
              const md = summary.summary || summary.markdown || "";
              appendStartupLog(md.split("\n").filter((l) => l.trim()).slice(0, 8).join(" · "));
              hideStartupOverlay(summary.greeting ? `${summary.greeting} — ready.` : `All set — ${ariaName()} is ready.`);
              return true;
            }
          } catch (_) {
            /* fall through */
          }
          hideStartupOverlay(`All set — ${ariaName()} is ready.`);
          return true;
        }
        const pending = (data.services || []).filter((s) => s.required && !s.running).map((s) => s.label);
        startupStatus.textContent = pending.length
          ? `Waiting for ${pending.join(", ")}…`
          : "Almost ready…";
      }
    } catch (_) {
      startupStatus.textContent = i > 2
        ? `${ariaName()} is busy (video/image gen?) — click Skip or wait…`
        : `Connecting to ${ariaName()}…`;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  hideStartupOverlay(`Some services still starting — you can use ${ariaName()} now.`);
  return false;
}

document.getElementById("startupSkipBtn")?.addEventListener("click", () => {
  hideStartupOverlay("");
});

const modelsToggle = document.getElementById("modelsToggle");
const modelsEditor = document.getElementById("modelsEditor");
const modelSelects = {
  general: document.getElementById("modelGeneral"),
  coder: document.getElementById("modelCoder"),
  review: document.getElementById("modelReview"),
  vision: document.getElementById("modelVision"),
  image: document.getElementById("modelImage"),
  embed: document.getElementById("modelEmbed"),
};

let modelSettings = null;

function fillModelSelect(select, choices, value) {
  if (!select) return;
  select.innerHTML = "";
  const seen = new Set();
  const list = [...(choices || [])].sort((a, b) => a.localeCompare(b));
  if (value && !list.includes(value)) list.unshift(value);
  if (list.length === 0 && value) list.push(value);

  list.forEach((name) => {
    if (!name || seen.has(name)) return;
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    if (name === value) opt.selected = true;
    select.appendChild(opt);
    seen.add(name);
  });

  if (list.length === 0) {
    const opt = document.createElement("option");
    opt.value = value || "";
    opt.textContent = value || "(no models — run ollama pull)";
    select.appendChild(opt);
  }
}

function renderModelSettings(settings) {
  if (!settings) return;
  modelSettings = settings;
  const mode = settings.mode || (uncensoredToggle.checked ? "uncensored" : "standard");
  const active = settings.active || settings[mode] || {};
  const choices = settings.choices || settings.installed || [];
  const imageChoices = settings.role_choices?.image || ["comfyui"];

  fillModelSelect(modelSelects.general, choices, active.general);
  fillModelSelect(modelSelects.coder, choices, active.coder);
  fillModelSelect(modelSelects.review, choices, active.review);
  fillModelSelect(modelSelects.vision, choices, active.vision);
  fillModelSelect(modelSelects.image, imageChoices, active.image || "comfyui");
  fillModelSelect(modelSelects.embed, choices, active.embed);

  const hw = settings.hardware || {};
  const hwNote = document.getElementById("hwNote");
  if (hwNote) {
    hwNote.textContent = `${hw.gpu || ""} · ${hw.ram || ""}. ${hw.note || ""}`;
  }

  const editorStatus = document.getElementById("modelsEditorStatus");
  if (editorStatus) {
    const n = settings.installed?.length || 0;
    if (n > 0) {
      editorStatus.textContent = `${n} Ollama models available`;
      editorStatus.classList.remove("warn");
    } else {
      editorStatus.textContent = "Starting Ollama — models will appear shortly";
      editorStatus.classList.add("warn");
    }
  }

  const modelsEl = document.getElementById("modelsStatus");
  if (modelsEl && active.general) {
    modelsEl.innerHTML = `<span>${active.general}</span><br><span>${active.coder}</span>`;
  }
}

async function loadModelSettings() {
  const editorStatus = document.getElementById("modelsEditorStatus");
  try {
    const res = await fetch("/api/models/settings");
    if (res.status === 404) {
      if (editorStatus) {
        editorStatus.textContent = `Old server running — restart ${ariaName()} from the desktop shortcut`;
        editorStatus.classList.add("warn");
      }
      return null;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const settings = await res.json();
    settings.mode = settings.mode || (uncensoredToggle.checked ? "uncensored" : "standard");
    renderModelSettings(settings);
    return settings;
  } catch (e) {
    if (editorStatus) {
      editorStatus.textContent = `Could not load models: ${e.message}`;
      editorStatus.classList.add("warn");
    }
    return null;
  }
}

window.loadModelSettings = loadModelSettings;

document.getElementById("saveModelsBtn")?.addEventListener("click", async () => {
  const mode = uncensoredToggle.checked ? "uncensored" : "standard";
  const form = new FormData();
  form.append("mode", mode);
  form.append("general", modelSelects.general?.value || "");
  form.append("coder", modelSelects.coder?.value || "");
  form.append("review", modelSelects.review?.value || "");
  form.append("vision", modelSelects.vision?.value || "");
  form.append("image", modelSelects.image?.value || "");
  form.append("embed", modelSelects.embed?.value || "");
  const res = await fetch("/api/models/settings", { method: "POST", body: form });
  const data = await res.json();
  if (data.settings) renderModelSettings({ ...data.settings, mode });
  const vq = document.getElementById("visionQualitySelect");
  if (vq) vq.value = "custom";
  await fetch("/api/vision/settings", { method: "POST", body: new URLSearchParams({ quality_mode: "custom" }) });
  await loadVisionSettings();
  statusText.textContent = "Models saved (vision: use selected model)";
});

document.getElementById("refreshModelsBtn")?.addEventListener("click", async () => {
  const res = await fetch("/api/models/refresh", { method: "POST" });
  const data = await res.json();
  if (data.settings) {
    renderModelSettings({ ...data.settings, mode: uncensoredToggle.checked ? "uncensored" : "standard" });
    statusText.textContent = "Models refreshed";
  }
});

document.getElementById("resetModelsBtn")?.addEventListener("click", async () => {
  const mode = uncensoredToggle.checked ? "uncensored" : "standard";
  const form = new FormData();
  form.append("mode", mode);
  const res = await fetch("/api/models/reset", { method: "POST", body: form });
  const data = await res.json();
  if (data.settings) renderModelSettings({ ...data.settings, mode });
  statusText.textContent = "Models reset to optimized defaults";
  document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
  document.getElementById("presetQualityBtn")?.classList.add("active");
});

async function applyPreset(preset) {
  const mode = uncensoredToggle.checked ? "uncensored" : "standard";
  const form = new FormData();
  form.append("preset", preset);
  form.append("mode", mode);
  const res = await fetch("/api/models/preset", { method: "POST", body: form });
  const data = await res.json();
  if (data.settings) {
    renderModelSettings({ ...data.settings, mode });
    statusText.textContent = `Applied ${preset} preset`;
  }
  document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
  document.getElementById(preset === "fast" ? "presetFastBtn" : "presetQualityBtn")?.classList.add("active");
}

document.getElementById("presetFastBtn")?.addEventListener("click", () => applyPreset("fast"));
document.getElementById("presetQualityBtn")?.addEventListener("click", () => applyPreset("quality"));

async function pullMissingModels() {
  const btn = document.getElementById("pullMissingBtn");
  const editorStatus = document.getElementById("modelsEditorStatus");
  if (btn) btn.disabled = true;
  if (pullLogEl) {
    pullLogEl.classList.remove("hidden");
    pullLogEl.textContent = "Checking missing models…\n";
  }

  try {
    const res = await fetch("/api/models/pull-missing", { method: "POST" });
    const ct = res.headers.get("content-type") || "";

    if (ct.includes("application/json")) {
      const data = await res.json();
      if (pullLogEl) pullLogEl.textContent = data.message || "All models installed.";
      if (editorStatus) editorStatus.textContent = data.message || "All models installed.";
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        let event;
        try { event = JSON.parse(line.slice(6)); } catch { continue; }

        if (event.type === "model_start" && pullLogEl) {
          pullLogEl.textContent += `\n▶ ${event.model}\n`;
        } else if (event.type === "progress" && pullLogEl) {
          pullLogEl.textContent += event.message + "\n";
          pullLogEl.scrollTop = pullLogEl.scrollHeight;
        } else if (event.type === "done" && pullLogEl) {
          pullLogEl.textContent += (event.ok ? "✓ " : "✗ ") + (event.message || "") + "\n";
        } else if (event.type === "all_done") {
          statusText.textContent = "Model pull complete";
          await loadModelSettings();
          await loadHealth();
        }
      }
    }
  } catch (e) {
    if (pullLogEl) pullLogEl.textContent += `Error: ${e.message}\n`;
  } finally {
    if (btn) btn.disabled = false;
  }
}

document.getElementById("pullMissingBtn")?.addEventListener("click", pullMissingModels);

const UNCENSORED_SESSION_KEY = "jarvisUncensoredToken";

function showUncensoredPasswordModal(needsSetup, authConfigured = false) {
  return new Promise((resolve) => {
    const modal = document.getElementById("uncensoredAuthModal");
    const title = document.getElementById("uncensoredAuthTitle");
    const intro = document.getElementById("uncensoredAuthIntro");
    const passInput = document.getElementById("uncensoredPasswordInput");
    const confirmRow = document.getElementById("uncensoredConfirmRow");
    const confirmInput = document.getElementById("uncensoredConfirmInput");
    const errEl = document.getElementById("uncensoredAuthError");
    const submitBtn = document.getElementById("uncensoredAuthSubmit");
    const resetBtn = document.getElementById("uncensoredResetBtn");
    if (!modal || !passInput) {
      resolve(null);
      return;
    }
    if (title) title.textContent = needsSetup ? "Set uncensored password" : "Uncensored mode";
    if (intro) {
      intro.textContent = needsSetup
        ? "Choose a password to protect uncensored mode. You'll need it to enable NSFW chat and image settings."
        : "Enter your password to enable uncensored mode.";
    }
    resetBtn?.classList.toggle("hidden", needsSetup || !authConfigured);
    passInput.autocomplete = needsSetup ? "new-password" : "current-password";
    if (confirmInput) confirmInput.autocomplete = "new-password";
    const sessionToken = sessionStorage.getItem(UNCENSORED_SESSION_KEY) || "";
    fetch(`/api/uncensored/auth?session_token=${encodeURIComponent(sessionToken)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((auth) => {
        if (!auth?.lockout_seconds || !intro) return;
        const mins = Math.ceil(auth.lockout_seconds / 60);
        intro.textContent = `Too many attempts — wait about ${mins} min before trying again.`;
        if (submitBtn) submitBtn.disabled = true;
        if (passInput) passInput.disabled = true;
        if (confirmInput) confirmInput.disabled = true;
      })
      .catch(() => {});
    confirmRow?.classList.toggle("hidden", !needsSetup);
    passInput.value = "";
    if (confirmInput) confirmInput.value = "";
    if (submitBtn) submitBtn.disabled = false;
    if (passInput) passInput.disabled = false;
    if (confirmInput) confirmInput.disabled = false;
    errEl?.classList.add("hidden");
    if (submitBtn) submitBtn.textContent = needsSetup ? "Set password" : "Unlock";
    modal.classList.remove("hidden");
    passInput.focus();

    const cleanup = () => {
      modal.classList.add("hidden");
      resetBtn?.removeEventListener("click", onReset);
    };
    const onCancel = () => {
      cleanup();
      resolve(null);
    };
    const onReset = async () => {
      if (!confirm("Clear the uncensored password? You can set a new one right after.")) return;
      try {
        const res = await fetch("/api/uncensored/reset", { method: "POST" });
        const data = await res.json();
        if (!res.ok || !data.ok) {
          if (errEl) {
            errEl.textContent = data.message || "Could not reset password";
            errEl.classList.remove("hidden");
          }
          return;
        }
        cleanup();
        const creds = await showUncensoredPasswordModal(true, false);
        resolve(creds);
      } catch (_) {
        if (errEl) {
          errEl.textContent = "Could not reset password";
          errEl.classList.remove("hidden");
        }
      }
    };
    const onSubmit = () => {
      const password = passInput.value.trim();
      const confirm = (confirmInput?.value || "").trim();
      if (needsSetup && password.length < 12) {
        if (errEl) {
          errEl.textContent = "Password must be at least 12 characters";
          errEl.classList.remove("hidden");
        }
        return;
      }
      if (needsSetup && password !== confirm) {
        if (errEl) {
          errEl.textContent = "Passwords do not match — re-type both fields carefully";
          errEl.classList.remove("hidden");
        }
        return;
      }
      cleanup();
      resolve({ password, confirm });
    };
    const onKey = (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        onSubmit();
      }
      if (e.key === "Escape") onCancel();
    };
    document.getElementById("uncensoredAuthCancel")?.addEventListener("click", onCancel, { once: true });
    submitBtn?.addEventListener("click", onSubmit, { once: true });
    resetBtn?.addEventListener("click", onReset, { once: true });
    passInput.addEventListener("keydown", onKey);
    confirmInput?.addEventListener("keydown", onKey);
  });
}

async function restoreUncensoredSession() {
  const token = sessionStorage.getItem(UNCENSORED_SESSION_KEY);
  if (!token) return;
  try {
    const liveRes = await fetch("/api/live");
    if (liveRes.ok) {
      const live = await liveRes.json();
      if (live.uncensored) {
        uncensoredToggle.checked = true;
        document.body.classList.add("uncensored-mode");
        modeLabel.textContent = "Uncensored · Local AI Assistant";
        return;
      }
    }
    const authRes = await fetch(`/api/uncensored/auth?session_token=${encodeURIComponent(token)}`);
    if (!authRes.ok) return;
    const auth = await authRes.json();
    if (!auth.session_valid) return;
    const form = new FormData();
    form.append("uncensored", "true");
    form.append("session_token", token);
    const res = await fetch("/api/mode", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || !data.uncensored) return;
    if (data.session_token) sessionStorage.setItem(UNCENSORED_SESSION_KEY, data.session_token);
    uncensoredToggle.checked = true;
    document.body.classList.add("uncensored-mode");
    modeLabel.textContent = "Uncensored · Local AI Assistant";
    if (data.comfyui_settings) loadComfyMode();
  } catch (_) {}
}

uncensoredToggle.addEventListener("change", async () => {
  const wantUncensored = uncensoredToggle.checked;
  if (!wantUncensored) {
    const form = new FormData();
    form.append("uncensored", "false");
    const res = await fetch("/api/mode", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) return;
    sessionStorage.removeItem(UNCENSORED_SESSION_KEY);
    document.body.classList.toggle("uncensored-mode", data.uncensored);
    modeLabel.textContent = data.uncensored ? "Uncensored · Local" : "Local AI Assistant";
    const settings = await loadModelSettings();
    if (settings) renderModelSettings({ ...settings, mode: "standard" });
    if (data.comfyui_settings) syncComfySettings(data.comfyui_settings);
    return;
  }

  uncensoredToggle.checked = false;
  let sessionToken = sessionStorage.getItem(UNCENSORED_SESSION_KEY) || "";
  let auth = { configured: false, session_valid: false };
  try {
    const authRes = await fetch(`/api/uncensored/auth?session_token=${encodeURIComponent(sessionToken)}`);
    if (authRes.ok) auth = await authRes.json();
  } catch (_) {}

  let password = "";
  let confirm = "";
  if (!auth.session_valid) {
    const creds = await showUncensoredPasswordModal(!auth.configured, auth.configured);
    if (!creds) return;
    password = creds.password;
    confirm = creds.confirm || "";
    sessionToken = "";
  }

  const form = new FormData();
  form.append("uncensored", "true");
  form.append("password", password);
  form.append("confirm_password", confirm);
  form.append("session_token", sessionToken);
  const res = await fetch("/api/mode", { method: "POST", body: form });
  const data = await res.json();
  if (!res.ok || data.ok === false) {
    statusText.textContent = data.message || "Uncensored unlock failed";
    if (data.message && (data.message.includes("match") || data.message.includes("Confirm") || data.message.includes("Wrong"))) {
      const retry = await showUncensoredPasswordModal(
        data.message.includes("match") || data.message.includes("Confirm") || !auth.configured,
        auth.configured,
      );
      if (!retry) return;
      const form2 = new FormData();
      form2.append("uncensored", "true");
      form2.append("password", retry.password);
      form2.append("confirm_password", retry.confirm || "");
      form2.append("session_token", "");
      const res2 = await fetch("/api/mode", { method: "POST", body: form2 });
      const data2 = await res2.json();
      if (!res2.ok || data2.ok === false) {
        statusText.textContent = data2.message || "Uncensored unlock failed";
        return;
      }
      Object.assign(data, data2);
    } else {
      return;
    }
  }
  if (data.session_token) {
    sessionStorage.setItem(UNCENSORED_SESSION_KEY, data.session_token);
  }
  uncensoredToggle.checked = true;
  document.body.classList.toggle("uncensored-mode", data.uncensored);
  modeLabel.textContent = data.uncensored ? "Uncensored · Local" : "Local AI Assistant";
  const settings = await loadModelSettings();
  if (settings) renderModelSettings({ ...settings, mode: data.uncensored ? "uncensored" : "standard" });
  if (data.comfyui_settings) {
    syncComfySettings(data.comfyui_settings);
  } else {
    await loadComfyMode();
  }
});

let lastWakewordEventId = sessionStorage.getItem("jarvisWwChatId") || "";

async function pollWakewordChat() {
  if (mediaWorkActive()) return;
  try {
    const res = await fetch("/api/audio/wakeword/status");
    if (!res.ok) return;
    const data = await res.json();
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
      addMessage("user", userText);
      statusText.textContent = "Wake word → chat";
      handleDone({
        ok: last.chat_ok !== false,
        message: last.chat_response,
        module: last.chat_module,
        type: last.chat_type,
      });
      return;
    }

    if (last.chat_status === "ready" && userText) {
      statusText.textContent = "Wake word → chat…";
      await sendMessage(userText);
      return;
    }

    if (last.chat_status === "error") {
      showError(last.chat_error || "Wake word chat failed.");
    }
  } catch {
    /* ignore poll errors */
  }
}

function initAriaModalChrome() {
  /** Closable overlays (Esc). Lock screen is excluded — must unlock deliberately. */
  const MODAL_IDS = [
    "commandPaletteModal",
    "imageLightbox",
    "videoLightbox",
    "inpaintModal",
    "toolConfirmModal",
    "upgradeWizardModal",
    "jobCenterModal",
    "haSetupModal",
    "haTokenModal",
    "apiKeyModal",
    "profileModal",
    "branchTrimModal",
    "uncensoredAuthModal",
    "projectPickerModal",
    "settingsModal",
    "shortcutsModal",
  ];

  function isOpen(el) {
    return !!(el && !el.classList.contains("hidden"));
  }

  function topOpenModal() {
    for (const id of MODAL_IDS) {
      const el = document.getElementById(id);
      if (isOpen(el)) return el;
    }
    return null;
  }

  function focusables(root) {
    return [...(root?.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ) || [])].filter((el) => el.offsetParent !== null || el === document.activeElement);
  }

  function closeModal(el) {
    if (!el) return;
    if (el.id === "imageLightbox") {
      closeImageLightbox();
      return;
    }
    if (el.id === "videoLightbox") {
      closeVideoLightbox();
      return;
    }
    if (el.id === "toolConfirmModal") {
      document.getElementById("toolConfirmNo")?.click();
      return;
    }
    if (el.id === "commandPaletteModal") {
      window.closeAriaCommandPalette?.();
      return;
    }
    el.classList.add("hidden");
  }

  document.addEventListener("keydown", (e) => {
    const modal = topOpenModal();
    if (!modal) return;

    if (e.key === "Escape") {
      e.preventDefault();
      closeModal(modal);
      return;
    }

    if (e.key !== "Tab") return;
    const nodes = focusables(modal);
    if (!nodes.length) return;
    const first = nodes[0];
    const last = nodes[nodes.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    } else if (!modal.contains(document.activeElement)) {
      e.preventDefault();
      first.focus();
    }
  });
}

loadSuggestions();
initImageLightbox();
initVideoLightbox();
initAriaModalChrome();
document.getElementById("reloadUiBtn")?.addEventListener("click", () => reloadJarvisUi());
document.getElementById("resetLayoutBtn")?.addEventListener("click", () => {
  resetSidebarLayout();
  if (statusText) statusText.textContent = "Sidebar expanded — all sections visible";
});
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && String(e.key).toLowerCase() === "r") {
    e.preventDefault();
    reloadJarvisUi();
  }
});
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) scheduleEditorContextPoll();
});
setInterval(() => {
  if (!mediaWorkActive()) pollWakewordChat();
}, isNativeApp() ? 5000 : 2500);
waitForServices().then(() => {
  loadHealth().then(async () => {
    await restoreUncensoredSession();
    loadModelSettings();
    loadComfyMode();
    loadGpuStatus();
    loadVisionSettings();
    loadBranches().then(() => reloadBranchMessages().then(() => resumePendingMediaJobs()));
    loadPersonality();
    loadChatModelSelect();
    maybeShowProfileQuestionnaire();
    loadCodingPanel();
    loadGitStatus();
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
      if (!mediaWorkActive()) loadCodingPanel();
    }, 90000);
    scheduleEditorContextPoll();
  });
});

function lspPathValue() {
  const el = document.getElementById("lspPath");
  return el?.value?.trim() || lastEditorFile || "";
}

function lspLineValue() {
  const el = document.getElementById("lspLine");
  const n = parseInt(el?.value || "1", 10);
  return Number.isFinite(n) && n > 0 ? n : 1;
}

function setLspOut(text) {
  const out = document.getElementById("lspOut");
  if (out) out.textContent = text || "";
}

async function runLspAction(kind) {
  const path = lspPathValue();
  const line = lspLineValue();
  if (!path) {
    setLspOut("Enter a file path or sync Cursor editor context.");
    return;
  }
  setLspOut(kind === "diagnostics" ? "Checking…" : "…");
  const q = new URLSearchParams({ path, line: String(line), column: "1" });
  // Quick diagnostics by default — deep mypy can hang the UI for a long time.
  if (kind === "diagnostics") q.set("deep", "0");
  let url = `/api/lsp/${kind}?${q}`;
  let opts = {};
  if (kind === "format") {
    url = "/api/lsp/format";
    const form = new FormData();
    form.append("path", path);
    form.append("write", "1");
    opts = { method: "POST", body: form };
  }
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), kind === "diagnostics" ? 25000 : 45000);
  opts = { ...opts, signal: ctrl.signal };
  try {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      setLspOut(data.message || data.detail || "LSP request failed");
      return;
    }
    if (kind === "diagnostics") {
      setLspOut(data.summary || "No issues");
    } else if (kind === "definition") {
      const locs = data.locations || [];
      setLspOut(locs.length ? locs.map((l) => `${l.path}:${l.line}`).join("\n") : "No definition");
    } else if (kind === "references") {
      const refs = data.references || [];
      setLspOut(refs.length ? refs.slice(0, 25).map((r) => `${r.path}:${r.line}`).join("\n") : "No references");
    } else if (kind === "hover") {
      setLspOut(data.hover || "(empty)");
    } else if (kind === "symbols") {
      const syms = data.symbols || [];
      setLspOut(syms.slice(0, 40).map((s) => `${s.name} (L${s.line})`).join("\n") || "No symbols");
    } else if (kind === "format") {
      setLspOut(data.written ? `Formatted ${path}` : "Format preview only");
    }
  } catch (e) {
    const msg = e?.name === "AbortError" ? "LSP timed out — try again or narrow the file" : String(e);
    setLspOut(msg);
  } finally {
    clearTimeout(timer);
  }
}

document.getElementById("lspDiagBtn")?.addEventListener("click", () => runLspAction("diagnostics"));
document.getElementById("lspDefBtn")?.addEventListener("click", () => runLspAction("definition"));
document.getElementById("lspRefBtn")?.addEventListener("click", () => runLspAction("references"));
document.getElementById("lspHoverBtn")?.addEventListener("click", () => runLspAction("hover"));
document.getElementById("lspSymBtn")?.addEventListener("click", () => runLspAction("symbols"));
document.getElementById("lspFmtBtn")?.addEventListener("click", () => runLspAction("format"));

async function loadCodingPanel() {
  const toolsEl = document.getElementById("codingTools");
  const tasksEl = document.getElementById("codingTasks");
  if (!toolsEl) return;
  const ed = await loadEditorContext();
  const lspPath = document.getElementById("lspPath");
  if (lspPath && ed?.file && !lspPath.value.trim()) {
    lspPath.value = ed.file;
    const lspLine = document.getElementById("lspLine");
    if (lspLine && ed.ctx?.cursor_line) lspLine.value = String(ed.ctx.cursor_line);
  }
  try {
    const [toolsRes, tasksRes, lspRes] = await Promise.all([
      fetch("/api/coding/tools"),
      fetch("/api/coding/tasks"),
      fetch("/api/lsp/status"),
    ]);
    if (toolsRes.ok) {
      const tools = await toolsRes.json();
      const active = Object.entries(tools).filter(([, v]) => v).map(([k]) => k);
      let lspNote = "";
      if (lspRes.ok) {
        const lsp = await lspRes.json();
        const servers = (lsp.servers || []).filter((s) => s.available).map((s) => s.id);
        lspNote = servers.length ? ` · LSP: ${servers.join(", ")}` : " · LSP: install servers";
      }
      toolsEl.textContent = active.length ? `Checkers: ${active.join(", ")}${lspNote}` : `No extra checkers${lspNote}`;
    }
    if (tasksEl && tasksRes.ok) {
      const data = await tasksRes.json();
      const tasks = data.tasks || [];
      if (!tasks.length) {
        tasksEl.innerHTML = "<span class='muted'>No coding tasks</span>";
      } else {
        tasksEl.innerHTML = tasks.slice(0, 5).map((t) =>
          `<div class="coding-task-row"><span>${escapeHtml(t.id)}</span> <span class="muted">${escapeHtml(t.status)}</span></div>`
        ).join("");
      }
    }
  } catch (_) {
    toolsEl.textContent = "Coding tools offline";
  }
}

document.getElementById("indexCodeBtn")?.addEventListener("click", async () => {
  statusText.textContent = "Indexing code…";
  try {
    await fetch("/api/code/reindex", { method: "POST" });
    statusText.textContent = "Code index rebuilt";
    loadCodingPanel();
  } catch (_) {
    statusText.textContent = "Index failed";
  }
});

// View switching
document.querySelectorAll(".view-tab").forEach((tab) => {
  tab.addEventListener("click", () => switchToView(tab.dataset.view));
});

async function loadCheatsheets(selectKey) {
  const sel = document.getElementById("cheatsheetSelect");
  if (!sel) return;
  try {
    const res = await fetch("/api/cheatsheets");
    const data = await res.json();
    const items = data.cheatsheets || [];
    sel.innerHTML = `<option value="">— choose —</option>${items.map((c) =>
      `<option value="${escapeHtml(c.key)}">${escapeHtml(c.key)} — ${escapeHtml(c.title)}</option>`
    ).join("")}`;
    if (selectKey) sel.value = selectKey;
  } catch (_) {}
}

async function showCheatsheet(key) {
  const box = document.getElementById("cheatsheetContent");
  if (!key || !box) return;
  const res = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`);
  const data = await res.json();
  if (!data.ok) {
    alert(data.error || "Cheatsheet not found");
    return;
  }
  box.textContent = data.cheatsheet?.content || "";
  box.classList.remove("hidden");
}

let memorySettingsSaveInFlight = 0;

function applyMemorySettingsToUi(data) {
  if (!data || !data.ok) return;
  const modeEl = document.getElementById("memoryAutoMode");
  if (modeEl && data.auto_memory_mode) modeEl.value = data.auto_memory_mode;
  const brainEl = document.getElementById("memoryBrainMode");
  if (brainEl) brainEl.checked = data.brain_mode !== false;
  const journalLearnEl = document.getElementById("memoryAutoJournalLearn");
  if (journalLearnEl) {
    const bl = data.brain_learning || {};
    journalLearnEl.checked = data.auto_journal_learn === true
      || (data.auto_journal_learn == null && bl.auto_journal_learn === true);
  }
  const docLearnEl = document.getElementById("memoryAutoDocumentLearn");
  if (docLearnEl) {
    const bl = data.brain_learning || {};
    docLearnEl.checked = data.auto_document_learn === true
      || (data.auto_document_learn == null && bl.auto_document_learn === true);
  }
  const cpEl = document.getElementById("memoryAutoCheckpoint");
  if (cpEl) cpEl.checked = data.auto_checkpoint !== false;
  const nsEl = document.getElementById("memoryAutoNamespace");
  if (nsEl) nsEl.checked = data.auto_namespace !== false;
  const promptEl = document.getElementById("memoryInPrompt");
  if (promptEl) promptEl.checked = data.memory_in_system_prompt !== false;
}

async function loadMemorySettings() {
  if (memorySettingsSaveInFlight > 0) return;
  try {
    const res = await fetch("/api/memory/settings");
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) return;
    applyMemorySettingsToUi(data);
  } catch (_) {}
}

async function saveMemorySettings(patch) {
  memorySettingsSaveInFlight += 1;
  try {
    const res = await fetch("/api/memory/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      const err = new Error(data.message || `Could not save settings (HTTP ${res.status})`);
      err.locked = res.status === 423 || data.locked;
      throw err;
    }
    applyMemorySettingsToUi(data);
    return data;
  } finally {
    memorySettingsSaveInFlight = Math.max(0, memorySettingsSaveInFlight - 1);
  }
}

function bindMemorySettingCheckbox(id, key) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("change", async (e) => {
    const target = e.target;
    const want = target.checked;
    try {
      await saveMemorySettings({ [key]: want });
    } catch (err) {
      target.checked = !want;
      if (err.locked) window.jarvisShowLock?.();
      window.showAriaToast?.(err.message || "Could not save memory setting", "warn", 6000);
    }
  });
}

async function loadMemoryConflicts() {
  const box = document.getElementById("memoryConflicts");
  if (!box) return;
  try {
    const res = await fetch("/api/memory/conflicts");
    const data = await res.json();
    const conflicts = data.conflicts || [];
    if (!conflicts.length) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    box.classList.remove("hidden");
    box.innerHTML = `<h3>Possible conflicts (${conflicts.length})</h3>` + conflicts.map((c, i) => `
      <div class="memory-conflict-item" data-keep="${escapeHtml(c.a.id)}" data-drop="${escapeHtml(c.b.id)}">
        <div class="memory-conflict-pair"><strong>${escapeHtml(c.kind)}</strong> · score ${c.score}<br/>
          A: ${escapeHtml(c.a.content)}<br/>
          B: ${escapeHtml(c.b.content)}
        </div>
        <div class="memory-conflict-actions">
          <button type="button" class="apply-btn small memory-keep-a" data-i="${i}">Keep A</button>
          <button type="button" class="apply-btn small memory-keep-b" data-i="${i}">Keep B</button>
        </div>
      </div>`).join("");
    box.querySelectorAll(".memory-keep-a").forEach((btn) => {
      btn.onclick = async () => {
        const item = btn.closest(".memory-conflict-item");
        await fetch("/api/memory/conflicts/resolve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ keep_id: item.dataset.keep, drop_id: item.dataset.drop }),
        });
        loadMemoryBrowser();
      };
    });
    box.querySelectorAll(".memory-keep-b").forEach((btn) => {
      btn.onclick = async () => {
        const item = btn.closest(".memory-conflict-item");
        await fetch("/api/memory/conflicts/resolve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ keep_id: item.dataset.drop, drop_id: item.dataset.keep }),
        });
        loadMemoryBrowser();
      };
    });
  } catch (_) {
    box.classList.add("hidden");
  }
}

async function loadMemoryTrustStatus() {
  const el = document.getElementById("memoryTrustStatus");
  if (!el) return;
  try {
    const res = await fetch("/api/memory/trust/status");
    const data = await res.json();
    if (!data.ok) return;
    const parts = [
      `Trust: ${data.strategies || 0} rules`,
      `${data.failures || 0} coding failures logged`,
    ];
    if (data.artifact_entries_remaining) {
      parts.push(`${data.artifact_entries_remaining} test artifact(s) — use Scrub`);
    }
    if (data.last_scrub_on_startup) {
      parts.push(`scrubbed ${data.last_scrub_on_startup} on last start`);
    }
    el.textContent = parts.join(" · ");
  } catch {
    el.textContent = "";
  }
}

async function loadEnvironmentPreferences() {
  const form = document.getElementById("envPrefsForm");
  if (!form) return;
  try {
    const res = await fetch("/api/memory/environment/preferences");
    const data = await res.json();
    const items = data.preferences || [];
    form.innerHTML = items.map((p) => `
      <div class="env-pref-field" data-key="${escapeHtml(p.key)}">
        <label for="envPref-${escapeHtml(p.key)}">${escapeHtml(p.label)}</label>
        <textarea id="envPref-${escapeHtml(p.key)}" rows="2" placeholder="${escapeHtml(p.hint || "")}">${escapeHtml(p.content || "")}</textarea>
      </div>`).join("");
  } catch (_) {
    form.innerHTML = "<p class=\"muted\">Could not load stack preferences.</p>";
  }
}

async function saveEnvironmentPreferences() {
  const form = document.getElementById("envPrefsForm");
  if (!form) return;
  const preferences = [];
  form.querySelectorAll(".env-pref-field").forEach((field) => {
    const key = field.dataset.key;
    const ta = field.querySelector("textarea");
    if (key && ta) preferences.push({ key, content: ta.value });
  });
  const res = await fetch("/api/memory/environment/preferences", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferences }),
  });
  const data = await res.json();
  if (!data.ok) {
    alert(data.error || "Save failed");
    return;
  }
  loadMemoryBrowser();
}

function setKnowledgeResearchStatus(text, busy = false) {
  const el = document.getElementById("knowledgeResearchStatus");
  if (!el) return;
  el.textContent = text || "";
  el.classList.toggle("busy", Boolean(busy && text));
}

function knowledgeKindLabel(kind) {
  if (kind === "intel") return "General";
  if (kind === "personal") return "Personal";
  if (kind === "profile") return "Profile";
  return "Stack";
}

function renderKnowledgeResearchBrief(b) {
  const day = b.last_day || b.updated || "";
  const label = knowledgeKindLabel(b.kind || "stack");
  return `<li><span class="knowledge-kind-badge knowledge-kind-${escapeHtml(b.kind || "stack")}">${escapeHtml(label)}</span> <button type="button" class="ghost-btn tiny knowledge-research-link" data-slug="${escapeHtml(b.slug)}"><strong>${escapeHtml(b.title || b.slug)}</strong></button> <span class="muted">${escapeHtml(day)}</span></li>`;
}

function renderKnowledgeResearchTopics(categories) {
  const byKind = { stack: [], intel: [], personal: [], profile: [] };
  for (const c of categories) {
    const k = c.kind || "stack";
    (byKind[k] || byKind.stack).push(c);
  }
  const parts = [];
  if (byKind.profile.length) {
    parts.push(
      `<strong>From your profile (nightly):</strong> ${byKind.profile.map((c) => escapeHtml(c.title)).join(" · ")}`,
    );
  }
  if (byKind.stack.length) {
    parts.push(
      `<strong>Stack (nightly):</strong> ${byKind.stack.map((c) => escapeHtml(c.title)).join(" · ")}`,
    );
  }
  if (byKind.intel.length) {
    parts.push(
      `<strong>General (rotating, 4/night):</strong> ${byKind.intel.map((c) => escapeHtml(c.title)).join(" · ")}`,
    );
  }
  if (byKind.personal.length) {
    parts.push(
      `<strong>Personal:</strong> ${byKind.personal.map((c) => escapeHtml(c.title)).join(" · ")}`,
    );
  }
  return parts.join("<br>");
}

async function waitForCodingJobResult(jobId, { onProgress } = {}) {
  const maxAttempts = 240;
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, 1500));
    const res = await fetch(`/api/coding/job/${encodeURIComponent(jobId)}`);
    const job = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(job.message || `HTTP ${res.status}`);
    onProgress?.(job);
    if (job.done) return job;
  }
  throw new Error("Job timed out");
}

async function runKnowledgeResearchNow() {
  const runBtn = document.getElementById("knowledgeResearchRunBtn");
  const jobsBtn = document.getElementById("knowledgeResearchJobsBtn");
  if (!runBtn || runBtn.dataset.busy === "1") return;
  runBtn.dataset.busy = "1";
  runBtn.disabled = true;
  jobsBtn?.classList.add("hidden");
  setKnowledgeResearchStatus("Starting knowledge research…", true);
  try {
    window.showAriaToast?.("Running knowledge research (may take a few minutes)…", "info", 8000);
    const res = await fetch("/api/knowledge/research/daily", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force: true }),
    });
    const data = await res.json();
    if (data.pending && data.job_id) {
      jobsBtn?.classList.remove("hidden");
      setKnowledgeResearchStatus("Research queued — searching web and writing briefs…", true);
      try {
        const job = await waitForCodingJobResult(data.job_id, {
          onProgress: (j) => {
            const msg = j.message || "Running…";
            setKnowledgeResearchStatus(`Research in progress — ${msg}`, true);
          },
        });
        jobsBtn?.classList.add("hidden");
        const errText = job.error || job.result?.message || "";
        if (job.result?.ok) {
          setKnowledgeResearchStatus("Research complete.", false);
          window.showAriaToast?.(job.result.message || "Research complete", "ok", 8000);
          loadMemoryBrowser();
        } else if (String(errText).includes("knowledge_research_run")) {
          setKnowledgeResearchStatus("Handler missing — restart Jarvis server, then try again.", false);
          window.showAriaToast?.("Research handler missing — restart Jarvis server, then try again.", "err", 10000);
        } else {
          setKnowledgeResearchStatus(errText || "Research failed.", false);
          window.showAriaToast?.(errText || "Research failed", "err", 8000);
        }
      } catch (_) {
        setKnowledgeResearchStatus(
          "Still running in the background — click View job progress or Services → Background jobs.",
          false,
        );
        window.showAriaToast?.("Research still running — opening Job center…", "info", 8000);
        window.jarvisJobs?.openJobCenter?.();
      }
    } else if (data.ok) {
      setKnowledgeResearchStatus(data.message || "Research complete.", false);
      window.showAriaToast?.(data.message || "Research complete", "ok", 8000);
      loadMemoryBrowser();
    } else {
      setKnowledgeResearchStatus(data.message || "Research failed.", false);
      window.showAriaToast?.(data.message || "Research failed", "err", 8000);
    }
  } catch (e) {
    setKnowledgeResearchStatus(e.message || "Request failed.", false);
    window.showAriaToast?.(e.message || "Request failed", "err", 8000);
  } finally {
    runBtn.dataset.busy = "0";
    runBtn.disabled = false;
  }
}

async function loadKnowledgeResearchPanel() {
  const rRes = await fetch("/api/knowledge/research");
  if (!rRes.ok) return;
  const rData = await rRes.json();
  const topicsEl = document.getElementById("knowledgeResearchTopics");
  if (topicsEl) {
    const cats = rData.categories || [];
    topicsEl.innerHTML = cats.length ? renderKnowledgeResearchTopics(cats) : "";
  }
  const rEl = document.getElementById("knowledgeResearchList");
  if (rEl) {
    const briefs = rData.briefs || [];
    const last = rData.last_run_day ? ` · last run ${escapeHtml(rData.last_run_day)}` : "";
    rEl.innerHTML = briefs.length
      ? briefs.map((b) => renderKnowledgeResearchBrief(b)).join("") + `<li class="muted">${briefs.length} brief(s)${last}</li>`
      : `<li class="muted">No nightly research yet${last} — click Run research now or wait for 11 PM.</li>`;
    rEl.querySelectorAll(".knowledge-research-link").forEach((btn) => {
      btn.onclick = async () => {
        const slug = btn.dataset.slug;
        if (!slug) return;
        try {
          const res = await fetch(`/api/knowledge/research/${encodeURIComponent(slug)}`);
          const brief = await res.json();
          if (!brief.ok) {
            alert(brief.message || "Could not load brief");
            return;
          }
          const preview = (brief.markdown || "").slice(0, 8000);
          const w = window.open("", "_blank", "width=720,height=640");
          if (w) {
            w.document.write(`<pre style="font:14px/1.5 sans-serif;padding:1rem;white-space:pre-wrap">${escapeHtml(preview)}</pre>`);
            w.document.title = slug;
          } else {
            alert(preview.slice(0, 2000));
          }
        } catch (e) {
          alert(e.message || "Load failed");
        }
      };
    });
  }
}

async function loadProfileInlinePanel() {
  const el = document.getElementById("profileInlineContent");
  if (!el) return;
  try {
    const [qRes, mRes] = await Promise.all([
      fetch("/api/profile/questionnaire"),
      fetch("/api/memory/all?namespace=profile"),
    ]);
    const data = await qRes.json();
    const mem = await mRes.json();
    const questions = data.questions?.length ? data.questions : [];
    const entries = (mem.entries || []).filter((e) => !(e.tags || []).includes("summary"));
    if (entries.length) {
      el.innerHTML = entries.map((e) =>
        `<div class="profile-inline-row"><span>${escapeHtml(e.content || "")}</span></div>`
      ).join("");
    } else if (!data.completed && questions.length) {
      el.innerHTML = `<p>Questionnaire not completed — ${questions.length} questions waiting.</p>`;
      renderProfileForm(questions);
      document.getElementById("profileModal")?.classList.remove("hidden");
    } else if (data.completed) {
      el.innerHTML = "<p>Profile completed. Click <strong>Edit answers</strong> to update your questionnaire.</p>";
    } else {
      el.innerHTML = "<p>No profile answers yet. Click Edit answers to fill in the questionnaire.</p>";
    }
  } catch (e) {
    el.textContent = e.message || "Could not load profile";
  }
}

async function loadMemoryBrowser() {
  await loadMemorySettings();
  await loadEnvironmentPreferences();
  await loadMemoryConflicts();
  await loadMemoryTrustStatus();
  await loadProfileInlinePanel();
  try {
    const kRes = await fetch("/api/knowledge");
    const kData = await kRes.json();
    const kEl = document.getElementById("knowledgeTopicList");
    if (kEl) {
      const topics = kData.topics || [];
      kEl.innerHTML = topics.length
        ? topics.map((t) => `<li><strong>${escapeHtml(t.title || t.slug)}</strong> <code>${escapeHtml(t.slug || "")}</code></li>`).join("")
        : "<li>No knowledge briefs yet — say <em>learn about: …</em></li>";
    }
  } catch (_) {}
  try {
    await loadKnowledgeResearchPanel();
  } catch (_) {}
  await loadCheatsheets(document.getElementById("cheatsheetSelect")?.value || "");
  const el = document.getElementById("memoryList");
  const statsEl = document.getElementById("memoryStats");
  const nsFilter = document.getElementById("memoryNsFilter");
  if (!el) return;
  const q = document.getElementById("memorySearch")?.value || "";
  const type = document.getElementById("memoryTypeFilter")?.value || "";
  const namespace = document.getElementById("memoryNsFilter")?.value || "";
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (type) params.set("type", type);
  if (namespace) params.set("namespace", namespace);
  const res = await fetch(`/api/memory/all?${params}`);
  const data = await res.json();
  const stats = data.stats || {};
  if (statsEl) {
    const byType = stats.by_type
      ? Object.entries(stats.by_type).map(([k, v]) => `${k}: ${v}`).join(" · ")
      : "";
    statsEl.textContent = `${stats.total || 0} memories${byType ? ` · ${byType}` : ""} · namespace: ${data.namespace || "default"}`;
  }
  if (nsFilter && stats.namespaces) {
    const cur = nsFilter.value;
    nsFilter.innerHTML = `<option value="">All namespaces</option>${stats.namespaces.map((n) =>
      `<option value="${escapeHtml(n)}">${escapeHtml(n)}</option>`
    ).join("")}`;
    nsFilter.value = cur;
  }
  el.innerHTML = (data.entries || []).map((e) => `
    <div class="memory-item" data-id="${escapeHtml(e.id)}">
      <div class="memory-item-head">
        <span class="memory-badge type-${escapeHtml(e.type)}">${escapeHtml(e.type)}</span>
        <span class="memory-badge ns">${escapeHtml(e.namespace || "default")}</span>
        ${(e.tags || []).map((t) => `<span class="memory-tag">${escapeHtml(t)}</span>`).join("")}
      </div>
      <p class="memory-content">${escapeHtml(e.content)}</p>
      <div class="memory-item-actions">
        <button type="button" class="memory-edit-btn" data-id="${escapeHtml(e.id)}">Edit</button>
        <button type="button" class="memory-del-btn" data-id="${escapeHtml(e.id)}">Delete</button>
      </div>
    </div>`).join("") || "<p class=\"memory-empty\">No memories stored.</p>";
  el.querySelectorAll(".memory-del-btn").forEach((btn) => {
    btn.onclick = async () => {
      const item = btn.closest(".memory-item");
      const isCheatsheet = item?.querySelector(".memory-badge.ns")?.textContent === "cheatsheet";
      const msg = isCheatsheet
        ? "Delete this cheatsheet? Use Reset default to restore bundled text instead."
        : "Delete this memory?";
      if (!confirm(msg)) return;
      await fetch(`/api/memory/${btn.dataset.id}`, { method: "DELETE" });
      loadMemoryBrowser();
    };
  });
  el.querySelectorAll(".memory-edit-btn").forEach((btn) => {
    btn.onclick = async () => {
      const item = btn.closest(".memory-item");
      const content = item?.querySelector(".memory-content")?.textContent || "";
      const next = prompt("Edit memory:", content);
      if (next == null || next.trim() === content) return;
      await fetch(`/api/memory/${btn.dataset.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: next.trim() }),
      });
      loadMemoryBrowser();
    };
  });
}

function initMemoryBrowser() {
  document.getElementById("knowledgeResearchRunBtn")?.addEventListener("click", () => {
    runKnowledgeResearchNow();
  });
  document.getElementById("memorySearch")?.addEventListener("input", () => loadMemoryBrowser());
  document.getElementById("memoryTypeFilter")?.addEventListener("change", () => loadMemoryBrowser());
  document.getElementById("memoryNsFilter")?.addEventListener("change", () => loadMemoryBrowser());
  document.getElementById("memoryAddBtn")?.addEventListener("click", async () => {
    const content = prompt("Memory to store:");
    if (!content?.trim()) return;
    await fetch("/api/memory", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: content.trim(), type: "fact" }),
    });
    loadMemoryBrowser();
  });
  document.getElementById("memoryExportBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/memory/export");
    const blob = new Blob([JSON.stringify(await res.json(), null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `jarvis-memory-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  });
  const importFile = document.getElementById("memoryImportFile");
  document.getElementById("memoryImportBtn")?.addEventListener("click", () => importFile?.click());
  importFile?.addEventListener("change", async () => {
    const file = importFile.files?.[0];
    if (!file) return;
    try {
      const payload = JSON.parse(await file.text());
      const merge = confirm("Merge with existing memories? (Cancel = replace all)");
      await fetch("/api/memory/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, merge }),
      });
      loadMemoryBrowser();
    } catch (e) {
      alert("Import failed: invalid JSON");
    }
    importFile.value = "";
  });
  document.getElementById("memoryPruneBtn")?.addEventListener("click", async () => {
    if (!confirm("Remove stale auto-extracted memories?")) return;
    const res = await fetch("/api/memory/prune", { method: "POST" });
    const data = await res.json();
    alert(`Pruned ${data.removed || 0} entries`);
    loadMemoryBrowser();
  });
  document.getElementById("memoryScrubBtn")?.addEventListener("click", async () => {
    if (!confirm("Remove test artifacts from memory (broken_calc, buy milk, stale checkpoints)?")) return;
    const res = await fetch("/api/memory/trust/scrub", { method: "POST" });
    const data = await res.json();
    alert(`Scrubbed ${data.removed || 0} entries`);
    loadMemoryBrowser();
  });
  document.getElementById("memoryAutoMode")?.addEventListener("change", (e) => {
    void saveMemorySettings({ auto_memory_mode: e.target.value }).catch((err) => {
      window.showAriaToast?.(err.message || "Could not save setting", "warn", 6000);
      if (err.locked) window.jarvisShowLock?.();
    });
  });
  bindMemorySettingCheckbox("memoryBrainMode", "brain_mode");
  bindMemorySettingCheckbox("memoryAutoJournalLearn", "auto_journal_learn");
  bindMemorySettingCheckbox("memoryAutoDocumentLearn", "auto_document_learn");
  bindMemorySettingCheckbox("memoryAutoCheckpoint", "auto_checkpoint");
  bindMemorySettingCheckbox("memoryAutoNamespace", "auto_namespace");
  bindMemorySettingCheckbox("memoryInPrompt", "memory_in_system_prompt");
  document.getElementById("envPrefsSaveBtn")?.addEventListener("click", () => saveEnvironmentPreferences());
  document.getElementById("envMachineSyncBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/memory/environment/sync?machine_only=true", { method: "POST" });
    const data = await res.json();
    if (data.ok) {
      alert(`Machine facts refreshed (${data.added || 0} added, ${data.updated || 0} updated).`);
      loadMemoryBrowser();
    }
  });
  document.getElementById("profileRetakeBtn")?.addEventListener("click", async () => {
    if (!confirm("Replace your saved profile with new answers?")) return;
    const res = await fetch("/api/profile/questionnaire/reset", { method: "POST" });
    const data = await res.json();
    if (!data.ok) {
      alert("Could not reset profile");
      return;
    }
    renderProfileForm(data.questions || []);
    const modal = document.getElementById("profileModal");
    if (modal) modal.dataset.retake = "1";
    modal?.classList.remove("hidden");
  });
  document.getElementById("profileInlineEditBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/profile/questionnaire?edit=1");
    const data = await res.json();
    if (!data.ok || !(data.questions || []).length) {
      alert("Could not load profile questions");
      return;
    }
    renderProfileForm(data.questions);
    const modal = document.getElementById("profileModal");
    if (modal) modal.dataset.retake = data.completed ? "1" : "";
    modal?.classList.remove("hidden");
  });
  document.getElementById("cheatsheetViewBtn")?.addEventListener("click", () => {
    const key = document.getElementById("cheatsheetSelect")?.value;
    if (!key) {
      alert("Choose a cheatsheet first");
      return;
    }
    showCheatsheet(key);
  });
  document.getElementById("cheatsheetSelect")?.addEventListener("change", (e) => {
    if (e.target.value) showCheatsheet(e.target.value);
    else document.getElementById("cheatsheetContent")?.classList.add("hidden");
  });
  document.getElementById("cheatsheetEditBtn")?.addEventListener("click", async () => {
    const key = document.getElementById("cheatsheetSelect")?.value;
    if (!key) {
      alert("Choose a cheatsheet first");
      return;
    }
    const res = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`);
    const data = await res.json();
    if (!data.ok) return;
    const next = prompt("Edit cheatsheet (markdown):", data.cheatsheet?.content || "");
    if (next == null || next.trim() === data.cheatsheet?.content) return;
    await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: next.trim() }),
    });
    loadMemoryBrowser();
    showCheatsheet(key);
  });
  document.getElementById("cheatsheetResetBtn")?.addEventListener("click", async () => {
    const key = document.getElementById("cheatsheetSelect")?.value;
    if (!key) {
      alert("Choose a cheatsheet first");
      return;
    }
    if (!confirm(`Restore the default ${key} cheatsheet? Your edits will be lost.`)) return;
    await fetch(`/api/cheatsheets/${encodeURIComponent(key)}/reset`, { method: "POST" });
    loadMemoryBrowser();
    showCheatsheet(key);
  });
}

window.addEventListener("beforeunload", () => {
  try {
    navigator.sendBeacon("/api/memory/auto-checkpoint", "{}");
  } catch (_) {}
});

initMemoryBrowser();

function renderProfileForm(questions) {
  const form = document.getElementById("profileForm");
  if (!form) return;
  form.innerHTML = (questions || []).map((q) => {
    const req = q.required ? " required" : "";
    const hint = q.hint ? `<p class="hint">${escapeHtml(q.hint)}</p>` : "";
    if (q.type === "select") {
      const opts = (q.options || []).map((o) =>
        `<option value="${escapeHtml(o.value)}">${escapeHtml(o.label)}</option>`
      ).join("");
      return `<div class="profile-field"><label for="pf_${q.id}">${escapeHtml(q.label)}</label>${hint}<select id="pf_${q.id}" name="${escapeHtml(q.id)}"${req}>${opts}</select></div>`;
    }
    if (q.type === "textarea") {
      return `<div class="profile-field"><label for="pf_${q.id}">${escapeHtml(q.label)}</label>${hint}<textarea id="pf_${q.id}" name="${escapeHtml(q.id)}"${req}></textarea></div>`;
    }
    return `<div class="profile-field"><label for="pf_${q.id}">${escapeHtml(q.label)}</label>${hint}<input type="text" id="pf_${q.id}" name="${escapeHtml(q.id)}"${req} /></div>`;
  }).join("");
}

async function maybeShowProfileQuestionnaire() {
  const modal = document.getElementById("profileModal");
  if (!modal) return;
  try {
    const res = await fetch("/api/profile/questionnaire");
    const data = await res.json();
    if (!data.ok || data.completed || !(data.questions || []).length) return;
    renderProfileForm(data.questions);
    modal.classList.remove("hidden");
  } catch (_) {}
}

document.getElementById("profileForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const answers = {};
  new FormData(form).forEach((v, k) => { answers[k] = String(v); });
  const btn = document.getElementById("profileSaveBtn");
  if (btn) btn.disabled = true;
  try {
    const res = await fetch("/api/profile/questionnaire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers, retake: !!document.getElementById("profileModal")?.dataset.retake }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      alert(data.error || "Could not save profile");
      return;
    }
    document.getElementById("profileModal")?.classList.add("hidden");
    delete document.getElementById("profileModal")?.dataset.retake;
    loadProfileInlinePanel();
    addMessage(
      "assistant",
      `Thanks — I saved **${data.stored || 0}** things about you to memory. I'll use this to personalize our chats.`,
      { type: "info", module: "memory" }
    );
  } catch (_) {
    alert("Save failed");
  } finally {
    if (btn) btn.disabled = false;
  }
});

document.getElementById("profileSkipBtn")?.addEventListener("click", async () => {
  await fetch("/api/profile/questionnaire", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ skip: true }),
  });
  document.getElementById("profileModal")?.classList.add("hidden");
});

const INPAINT_REGIONS = {
  full: null,
  center: { x: 0.25, y: 0.25, w: 0.5, h: 0.5 },
  "top left": { x: 0, y: 0, w: 0.5, h: 0.5 },
  "top right": { x: 0.5, y: 0, w: 0.5, h: 0.5 },
  "bottom left": { x: 0, y: 0.5, w: 0.5, h: 0.5 },
  "bottom right": { x: 0.5, y: 0.5, w: 0.5, h: 0.5 },
};

let inpaintTargetPath = "";

function openInpaintModal(imagePath) {
  inpaintTargetPath = imagePath || "";
  const modal = document.getElementById("inpaintModal");
  const promptEl = document.getElementById("inpaintPrompt");
  const statusEl = document.getElementById("inpaintStatus");
  if (!modal || !inpaintTargetPath) return;
  if (promptEl) promptEl.value = "";
  if (statusEl) statusEl.textContent = "";
  modal.classList.remove("hidden");
  promptEl?.focus();
}

function closeInpaintModal() {
  document.getElementById("inpaintModal")?.classList.add("hidden");
  inpaintTargetPath = "";
}

document.getElementById("inpaintCancelBtn")?.addEventListener("click", closeInpaintModal);
document.getElementById("inpaintModal")?.addEventListener("click", (e) => {
  if (e.target?.id === "inpaintModal") closeInpaintModal();
});
document.getElementById("inpaintRunBtn")?.addEventListener("click", async () => {
  const prompt = document.getElementById("inpaintPrompt")?.value?.trim();
  const regionKey = document.getElementById("inpaintRegion")?.value || "full";
  const denoise = document.getElementById("inpaintDenoise")?.value;
  const statusEl = document.getElementById("inpaintStatus");
  const runBtn = document.getElementById("inpaintRunBtn");
  if (!inpaintTargetPath || !prompt) {
    if (statusEl) statusEl.textContent = "Enter a prompt.";
    return;
  }
  if (runBtn) runBtn.disabled = true;
  if (statusEl) statusEl.textContent = "Queuing edit…";
  await queueImageEdit(inpaintTargetPath, prompt, regionKey, statusEl, () => {
    closeInpaintModal();
    if (statusText) statusText.textContent = "Image edit running…";
  }, denoise);
  if (runBtn) runBtn.disabled = false;
});

async function loadGallery() {
  const el = document.getElementById("galleryGrid");
  if (!el) return;
  if (document.getElementById("imageEngineUncensoredBanner")) {
    await loadComfyMode();
  }
  try {
    const res = await fetch("/api/gallery");
    if (!res.ok) throw new Error(`Gallery unavailable (${res.status})`);
    const data = await res.json();
  el.innerHTML = (data.images || []).map((img) => {
    const thumb = apiAuthUrl(`/api/gallery/${encodeURIComponent(img.name)}?max=${GALLERY_THUMB_MAX}`);
    const full = apiAuthUrl(`/api/gallery/${encodeURIComponent(img.name)}`);
    return `<div class="gallery-item">
      <button type="button" class="gallery-del" data-name="${escapeHtml(img.name)}" title="Delete" aria-label="Delete ${escapeHtml(img.name)}">×</button>
      <button type="button" class="gallery-upscale" data-path="${escapeHtml(img.path)}" title="Upscale 2×" aria-label="Upscale ${escapeHtml(img.name)} 2×">2×</button>
      <button type="button" class="gallery-inpaint" data-path="${escapeHtml(img.path)}" title="Edit image" aria-label="Edit ${escapeHtml(img.name)}">✎</button>
      <img src="${thumb}" data-full-src="${escapeHtml(full)}" alt="${escapeHtml(img.name)}" loading="lazy" decoding="async" data-image-path="${escapeHtml(img.path)}" title="Click to view and edit" />
    </div>`;
  }).join("") || "<p class=\"muted\">No generated images yet. Use the prompt above, or ask in chat: <code>generate image: …</code></p>";
  el.querySelectorAll(".gallery-inpaint").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const path = btn.dataset.path;
      if (!path) return;
      const file = path.split(/[/\\]/).pop();
      openImageLightbox(
        resolveImageUrl(path, { thumb: false }),
        file,
        path,
        resolveImageUrl(path, { thumb: true, thumbMax: GALLERY_THUMB_MAX }),
      );
    });
  });
  el.querySelectorAll(".gallery-upscale").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const path = btn.dataset.path;
      if (!path) return;
      btn.disabled = true;
      const form = new FormData();
      form.append("path", path);
      form.append("scale", "2");
      const res = await fetch("/api/image/upscale", { method: "POST", body: form });
      const out = await res.json();
      btn.disabled = false;
      if (!res.ok || !out.ok) {
        statusText.textContent = out.message || "Upscale failed";
        return;
      }
      statusText.textContent = `Upscaled → ${out.image_path?.split("/").pop() || "done"}`;
      loadGallery();
    });
  });
  el.querySelectorAll(".gallery-del").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const name = btn.dataset.name;
      if (!name || !confirm(`Delete ${name}?`)) return;
      const delRes = await fetch(`/api/gallery/${encodeURIComponent(name)}`, { method: "DELETE" });
      const delData = await delRes.json();
      if (!delRes.ok || !delData.ok) {
        statusText.textContent = delData.message || "Delete failed";
        return;
      }
      loadGallery();
    });
  });
  bindClickableImages(el);
  loadPromptHistory();
  } catch (err) {
    el.innerHTML = `<p class="warn">Could not load gallery — ${escapeHtml(String(err.message || err))}</p>`;
  }
}

async function loadPromptHistory() {
  const el = document.getElementById("promptHistoryList");
  if (!el) return;
  try {
    const res = await fetch("/api/prompts?limit=30");
    const data = await res.json();
    const items = data.prompts || [];
    el.innerHTML = items.length
      ? items.map((p) => `<div class="prompt-history-item">
          <button type="button" class="ghost-btn small prompt-reuse" data-prompt="${escapeHtml(p.prompt)}">Reuse</button>
          <button type="button" class="ghost-btn small prompt-fav" data-id="${escapeHtml(p.id)}">${p.favorite ? "★" : "☆"}</button>
          <button type="button" class="ghost-btn small prompt-del" data-id="${escapeHtml(p.id)}" title="Delete" aria-label="Delete saved prompt">×</button>
          <span class="prompt-text">${escapeHtml(p.prompt.slice(0, 120))}${p.prompt.length > 120 ? "…" : ""}</span>
        </div>`).join("")
      : "<p>No saved prompts yet — generate an image to build history.</p>";
    el.querySelectorAll(".prompt-reuse").forEach((btn) => {
      btn.addEventListener("click", () => {
        messageInput.value = btn.dataset.prompt;
        document.querySelector('.view-tab[data-view="chat"]')?.click();
        messageInput.focus();
      });
    });
    el.querySelectorAll(".prompt-fav").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await fetch(`/api/prompts/${encodeURIComponent(btn.dataset.id)}/favorite`, { method: "POST" });
        loadPromptHistory();
      });
    });
    el.querySelectorAll(".prompt-del").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this prompt from history?")) return;
        const delRes = await fetch(`/api/prompts/${encodeURIComponent(btn.dataset.id)}`, { method: "DELETE" });
        const delData = await delRes.json();
        if (!delRes.ok || !delData.ok) {
          statusText.textContent = delData.message || "Delete failed";
          return;
        }
        loadPromptHistory();
      });
    });
  } catch (_) {
    el.textContent = "Could not load prompt history.";
  }
}

async function loadActions() {
  const el = document.getElementById("actionsList");
  if (!el) return;
  try {
    const res = await fetch("/api/actions");
    const data = await res.json();
    const acts = data.actions || [];
    el.innerHTML = acts.length
      ? acts.map((a) => `<li><span class="act-time">${escapeHtml((a.time || "").slice(0, 19))}</span> `
        + `<strong>${escapeHtml(a.action || "")}</strong> `
        + `${a.module ? `<code>${escapeHtml(a.module)}</code> ` : ""}`
        + `${escapeHtml((a.detail || "").slice(0, 80))}</li>`).join("")
      : "<li class='muted'>No actions logged yet.</li>";
  } catch (_) {
    el.innerHTML = "<li>Could not load actions.</li>";
  }
}

async function loadGitStatus() {
  const el = document.getElementById("gitStatusBox");
  if (!el) return;
  try {
    const res = await fetch("/api/git/status");
    const data = await res.json();
    el.textContent = data.status || "—";
  } catch (_) {
    el.textContent = "Git: unavailable";
  }
}

async function loadGitDiff() {
  const box = document.getElementById("gitDetailBox");
  if (!box) return;
  box.classList.remove("hidden");
  box.textContent = "Loading diff…";
  try {
    const res = await fetch("/api/git/diff");
    const data = await res.json();
    box.textContent = data.diff?.trim() || "(no diff)";
  } catch (_) {
    box.textContent = "Could not load diff";
  }
}

async function loadGitLog() {
  const box = document.getElementById("gitDetailBox");
  if (!box) return;
  box.classList.remove("hidden");
  box.textContent = "Loading log…";
  try {
    const res = await fetch("/api/git/log?limit=12");
    const data = await res.json();
    const lines = (data.log || []).join("\n");
    box.textContent = lines || "(empty log)";
  } catch (_) {
    box.textContent = "Could not load log";
  }
}

async function loadChatModelSelect() {
  const sel = document.getElementById("chatModelSelect");
  if (!sel) return;
  try {
    const [modelRes, settingsRes] = await Promise.all([
      fetch("/api/chat/model"),
      fetch("/api/models/settings"),
    ]);
    const modelData = await modelRes.json();
    const settings = await settingsRes.json();
    const installed = settings.installed || [];
    const current = modelData.chat_model || "";
    const def = modelData.default || settings.models?.general || "";
    const opts = ['<option value="">Chat model: (default)</option>'];
    const seen = new Set();
    for (const m of [current, def, ...installed]) {
      if (!m || seen.has(m)) continue;
      seen.add(m);
      const label = m === def ? `${m} (default)` : m;
      opts.push(`<option value="${escapeHtml(m)}">${escapeHtml(label)}</option>`);
    }
    sel.innerHTML = opts.join("");
    sel.value = current;
  } catch (_) {}
}

document.getElementById("chatModelSelect")?.addEventListener("change", async (e) => {
  const form = new FormData();
  form.append("model", e.target.value);
  try {
    const res = await fetch("/api/chat/model", { method: "POST", body: form });
    const data = await res.json();
    statusText.textContent = data.effective ? `Chat model: ${data.effective}` : "Chat model: default";
  } catch (_) {}
});

document.getElementById("gitRefreshBtn")?.addEventListener("click", () => loadGitStatus());
document.getElementById("gitDiffBtn")?.addEventListener("click", () => loadGitDiff());
document.getElementById("gitLogBtn")?.addEventListener("click", () => loadGitLog());

document.getElementById("themeToggle")?.addEventListener("click", () => {
  document.body.classList.toggle("light-theme");
  const btn = document.getElementById("themeToggle");
  if (btn) btn.textContent = document.body.classList.contains("light-theme") ? "Dark theme" : "Light theme";
});

document.getElementById("exportChatBtn")?.addEventListener("click", () => {
  const params = new URLSearchParams();
  if (activeBranchId) params.set("branch_id", activeBranchId);
  params.set("memory", "1");
  window.open(`/api/chat/export?${params}`, "_blank");
});

document.getElementById("exportChatPdfBtn")?.addEventListener("click", () => {
  const q = activeBranchId ? `?branch_id=${encodeURIComponent(activeBranchId)}` : "";
  window.open(`/api/chat/export/pdf${q}`, "_blank");
});

document.getElementById("backupDataBtn")?.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/admin/backup", { method: "POST" });
    const data = await res.json();
    alert(data.ok ? data.message || "Backup complete" : data.message || "Backup failed");
  } catch (_) {
    alert("Backup failed");
  }
});

document.getElementById("profileSelect")?.addEventListener("change", async (e) => {
  const pid = e.target.value;
  if (!pid) return;
  try {
    const res = await fetch("/api/profiles/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile: pid }),
    });
    const data = await res.json();
    statusText.textContent = data.ok ? `Profile: ${data.label}` : data.message || "Profile switch failed";
    loadModels();
  } catch (_) {
    statusText.textContent = "Profile switch failed";
  }
});

document.getElementById("actionsClearBtn")?.addEventListener("click", async () => {
  await fetch("/api/actions/clear", { method: "POST" });
  loadActions();
});

function notifyDesktop(title, body) {
  if (!("Notification" in window)) return;
  if (Notification.permission === "granted") {
    new Notification(title, { body });
  } else if (Notification.permission !== "denied") {
    Notification.requestPermission().then((p) => {
      if (p === "granted") new Notification(title, { body });
    });
  }
}
window.jarvisNotify = notifyDesktop;

document.getElementById("personalitySelect")?.addEventListener("change", async (e) => {
  const form = new FormData();
  form.append("preset", e.target.value);
  await fetch("/api/personality", { method: "POST", body: form });
  statusText.textContent = `Personality: ${e.target.value}`;
});

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

function showGeneratedImage(path, name) {
  if (!path) return;
  addMessage("assistant", "", { type: "image_result", module: "image" });
  const msg = document.querySelector(".message.assistant:last-child .msg-body");
  setTimeout(() => appendGeneratedImage(msg, path, name), 600);
}

function showAudioPlayer(path, transcript) {
  if (!path) return;
  const url = `/api/audio/file?path=${encodeURIComponent(path)}`;
  const name = path.split("/").pop();
  let html = `<div class="chat-audio-block"><p class="chat-audio-label">${escapeHtml(name)}</p><audio controls src="${url}" class="chat-audio-player"></audio>`;
  if (transcript) {
    html += `<details class="chat-transcript-details"><summary>Transcript</summary><pre class="chat-transcript">${escapeHtml(transcript)}</pre></details>`;
  }
  html += "</div>";
  addMessage("assistant", html, { type: "info" });
}

window.jarvisSendToChat = (text) => {
  if (!text) return;
  messageInput.value = text;
  document.querySelector('.view-tab[data-view="chat"]')?.click();
  messageInput.focus();
  resizeMessageInput();
};

async function loadPersonality() {
  const sel = document.getElementById("personalitySelect");
  if (!sel) return;
  try {
    const res = await fetch("/api/personality");
    if (!res.ok) return;
    const data = await res.json();
    if (data.personality && sel.querySelector(`option[value="${data.personality}"]`)) {
      sel.value = data.personality;
    }
  } catch (_) {}
}

async function loadBranches() {
  if (!branchSelect) return;
  try {
    const res = await fetch("/api/branches");
    if (!res.ok) return;
    const data = await res.json();
    activeBranchId = data.active || "main";
    branchSelect.innerHTML = (data.branches || []).map((b) =>
      `<option value="${escapeHtml(b.id)}"${b.id === activeBranchId ? " selected" : ""}>${escapeHtml(b.name)} (${b.messages})</option>`
    ).join("");
  } catch (_) {}
}

async function maybeShowMorningBriefing() {
  if (activeBranchId && activeBranchId !== "main") return false;
  try {
    const res = await fetchWithTimeout("/api/briefing?launch=1", {}, 5000);
    if (!res.ok) return false;
    const data = await res.json();
    if (!data.show || !data.markdown) return false;
    addMessage("assistant", data.markdown, { type: "briefing", module: "journal" });
    fetch("/api/briefing/dismiss", { method: "POST" }).catch(() => {});
    return true;
  } catch (_) {
    return false;
  }
}

async function reloadBranchMessages() {
  if (!messagesEl) return;
  messagesEl.innerHTML = "";
  try {
    const res = await fetch(`/api/branches/${encodeURIComponent(activeBranchId)}/messages`);
    if (!res.ok) return;
    const data = await res.json();
    for (const m of data.messages || []) {
      addMessage(m.role === "user" ? "user" : "assistant", m.content || "");
    }
    if (!(data.messages || []).length) {
      const showed = await maybeShowMorningBriefing();
      if (!showed) {
        addMessage(
          "assistant",
          `Hello! I'm ${assistantDisplayName}. Ask **what can you do?** to see my abilities, or say **morning briefing** for today's summary.`,
          { type: "info" }
        );
      }
    }
  } catch (_) {}
}

branchSelect?.addEventListener("change", async () => {
  activeBranchId = branchSelect.value;
  const form = new FormData();
  form.append("branch_id", activeBranchId);
  await fetch("/api/branches/switch", { method: "POST", body: form });
  await reloadBranchMessages();
});

newBranchBtn?.addEventListener("click", async () => {
  const name = prompt("Branch name:", "Branch");
  if (!name) return;
  const form = new FormData();
  form.append("name", name);
  const res = await fetch("/api/branches", { method: "POST", body: form });
  const data = await res.json();
  if (data.ok) {
    activeBranchId = data.branch_id;
    await loadBranches();
    await reloadBranchMessages();
    statusText.textContent = `Branch: ${name}`;
  }
});

async function openBranchTrimModal() {
  if (!branchTrimModal || !branchTrimList) return;
  try {
    const res = await fetch("/api/branches");
    if (!res.ok) return;
    const data = await res.json();
    const branches = (data.branches || []).filter((b) => b.id !== "main");
    if (!branches.length) {
      statusText.textContent = "No extra branches to trim";
      return;
    }
    branchTrimList.innerHTML = branches.map((b) =>
      `<label class="branch-trim-item">`
      + `<input type="checkbox" name="branch_trim" value="${escapeHtml(b.id)}">`
      + `<span>${escapeHtml(b.name)} <code>${escapeHtml(b.id)}</code> (${b.messages} msgs)</span>`
      + `</label>`
    ).join("");
    branchTrimModal.classList.remove("hidden");
  } catch (_) {}
}

function closeBranchTrimModal() {
  branchTrimModal?.classList.add("hidden");
}

/* Job center — jarvis/gui/static/modules/jobs.mjs */

debugBundleBtn?.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/debug/bundle");
    const data = await res.json();
    const text = data.text || JSON.stringify(data, null, 2);
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      statusText.textContent = "Debug bundle copied to clipboard";
    } else {
      prompt("Copy debug bundle:", text.slice(0, 8000));
    }
  } catch (e) {
    showError(`Debug bundle failed: ${e.message || e}`);
  }
});

trimBranchesBtn?.addEventListener("click", () => { openBranchTrimModal(); });

clearMainBranchBtn?.addEventListener("click", async () => {
  if (!confirm("Clear all messages on the Main branch? This cannot be undone.")) return;
  try {
    const form = new FormData();
    form.append("branch_id", "main");
    let res = await fetch("/api/branches/clear", { method: "POST", body: form });
    if (res.status === 404) {
      res = await fetch("/api/branches/main/clear", { method: "POST" });
    }
    if (res.status === 404 && activeBranchId === "main") {
      const legacy = new FormData();
      legacy.append("message", "clear");
      res = await fetch("/api/chat", { method: "POST", body: legacy });
    }
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showError(
        data.message
          || (res.status === 404
            ? "Clear Main needs a server restart — run: jarvis-ctl restart"
            : "Could not clear Main branch."),
      );
      return;
    }
    await loadBranches();
    if (activeBranchId === "main") {
      await reloadBranchMessages();
    } else {
      statusText.textContent = "Main branch cleared (still on current branch)";
    }
  } catch (e) {
    showError(`Clear failed: ${e.message || e}`);
  }
});

branchTrimCancelBtn?.addEventListener("click", closeBranchTrimModal);
branchTrimModal?.addEventListener("click", (e) => {
  if (e.target === branchTrimModal) closeBranchTrimModal();
});

branchTrimConfirmBtn?.addEventListener("click", async () => {
  const checked = [...(branchTrimList?.querySelectorAll('input[name="branch_trim"]:checked') || [])]
    .map((el) => el.value);
  if (!checked.length) {
    statusText.textContent = "Select at least one branch";
    return;
  }
  if (!confirm(`Delete ${checked.length} branch(es)? This cannot be undone.`)) return;
  const form = new FormData();
  form.append("branch_ids", checked.join(","));
  const res = await fetch("/api/branches/delete", { method: "POST", body: form });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    showError(data.message || "Could not delete branches.");
    return;
  }
  closeBranchTrimModal();
  activeBranchId = data.active || "main";
  await loadBranches();
  await reloadBranchMessages();
  statusText.textContent = `Deleted ${(data.deleted || []).length} branch(es)`;
});
