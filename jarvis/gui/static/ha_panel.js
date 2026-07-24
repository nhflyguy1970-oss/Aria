/** Home Assistant sidebar panel — extracted from app.js for maintainability. */
(function () {
  "use strict";

  let haWebhookUrl = "";


function haPanelStatus(message, tone = "") {
  const el = document.getElementById("haPanelStatus");
  if (!el) return;
  el.textContent = message || "";
  el.classList.remove("warn", "ok");
  if (tone) el.classList.add(tone);
  if (message) {
    const st = document.getElementById("statusText");
    if (st) st.textContent = message;
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
      window.loadHealth?.();
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
    window.loadHealth?.();
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
      webhookLine.textContent = `HA → ${(window.ariaName?.() || "Aria")} webhook: ${haWebhookUrl}`;
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
        || (res.status === 401 ? `${(window.ariaName?.() || "Aria")} API key required — enter it when prompted.` : "")
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
      const st = document.getElementById("statusText"); if (st) st.textContent = "Webhook URL copied";
    } catch (_) {
      prompt("Copy webhook URL:", haWebhookUrl);
    }
  });
  document.querySelectorAll(".ha-quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const msg = btn.dataset.msg || "";
      if (msg) window.sendMessage?.(msg);
    });
  });
  refreshHaPanel();
  updateHaTokenHint();
}


  window.refreshHaPanel = refreshHaPanel;
  window.initHaPanel = initHaPanel;
  window.saveHaConfigFromUi = saveHaConfigFromUi;
})();
