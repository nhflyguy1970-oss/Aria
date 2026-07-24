/** LAN access gate + API key modal — extracted from app.js. Load before app.js. */
(function () {
  "use strict";

  window.jarvisLanIps = window.jarvisLanIps || [];
  window.jarvisApiKeyRequired = window.jarvisApiKeyRequired ?? false;
  window.jarvisLocalhostKeyExempt = window.jarvisLocalhostKeyExempt ?? true;

  function getStoredApiKey() {
    return sessionStorage.getItem("jarvis_api_key") || "";
  }
  window.getStoredApiKey = getStoredApiKey;

  function isLoopbackHost(host) {
    return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
  }

  function isSameMachineHost() {
    const host = location.hostname;
    return isLoopbackHost(host) || (window.jarvisLanIps || []).includes(host);
  }
  window.isSameMachineHost = isSameMachineHost;

  function mediaNeedsApiKey() {
    if (!window.jarvisApiKeyRequired) return false;
    if (window.jarvisLocalhostKeyExempt && isSameMachineHost()) return false;
    return true;
  }
  window.mediaNeedsApiKey = mediaNeedsApiKey;

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
  window.showApiKeyModal = showApiKeyModal;

  function hideApiKeyModal() {
    document.getElementById("apiKeyModal")?.classList.add("hidden");
  }
  window.hideApiKeyModal = hideApiKeyModal;

  async function verifyApiKey(key) {
    const headers = { "X-API-Key": key };
    const res = await fetch("/api/services", { headers });
    return res.ok;
  }

  let lanPrimaryUrl = "";

  function esc(text) {
    return typeof window.escapeHtml === "function"
      ? window.escapeHtml(text)
      : String(text ?? "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;");
  }

  async function refreshLanPanel() {
    const line = document.getElementById("lanStatusLine");
    const list = document.getElementById("lanUrlList");
    const copyBtn = document.getElementById("lanCopyUrlBtn");
    if (!line) return;
    try {
      const res = await fetch("/api/lan");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `LAN status failed (${res.status})`);
      window.jarvisLanIps = data.lan_ips || [];
      window.jarvisApiKeyRequired = Boolean(data.api_key_required);
      window.jarvisLocalhostKeyExempt = data.api_key_localhost_exempt !== false;
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
          ? urls.map((u) => `<code class="lan-url">${esc(u)}</code>`).join("")
          : `<span class="muted">No LAN IP detected — use PC IP manually.</span>`;
      }
      copyBtn?.classList.toggle("hidden", !lanPrimaryUrl);
    } catch (err) {
      line.textContent = err.message || "LAN status unavailable.";
      window.showAriaToast?.(err.message || "LAN status unavailable", "err", 4000);
    }
  }
  window.refreshLanPanel = refreshLanPanel;

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
      window.showAriaToast?.("API key saved — reloading", "ok", 2500);
      location.reload();
    });
    cancelBtn?.addEventListener("click", hideApiKeyModal);
  }

  function initLanPanel() {
    document.getElementById("lanRefreshBtn")?.addEventListener("click", refreshLanPanel);
    document.getElementById("lanCopyUrlBtn")?.addEventListener("click", async () => {
      if (!lanPrimaryUrl) return;
      try {
        await navigator.clipboard.writeText(lanPrimaryUrl);
        const st = document.getElementById("statusText");
        if (st) st.textContent = "LAN URL copied";
        window.showAriaToast?.("LAN URL copied", "ok", 2500);
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
      window.jarvisApiKeyRequired = Boolean(data.api_key_required);
      window.jarvisLocalhostKeyExempt = data.api_key_localhost_exempt !== false;
      try {
        const lanRes = await fetch("/api/lan");
        if (lanRes.ok) {
          const lanData = await lanRes.json();
          window.jarvisLanIps = lanData.lan_ips || [];
        }
      } catch (_) { /* optional */ }
      const needsKey = mediaNeedsApiKey();
      if (needsKey && !getStoredApiKey()) {
        showApiKeyModal("");
      }
    } catch (_) { /* live endpoint optional at boot */ }
  }

  initApiKeyModal();
  initLanPanel();
  initLanAccessGate();
})();
