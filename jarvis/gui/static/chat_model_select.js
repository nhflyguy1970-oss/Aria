/** Chat model dropdown — extracted from app.js. */
(function () {
  "use strict";

  function esc(text) {
    return typeof window.escapeHtml === "function"
      ? window.escapeHtml(text)
      : String(text ?? "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;");
  }

  async function loadChatModelSelect() {
    const sel = document.getElementById("chatModelSelect");
    if (!sel) return;
    try {
      const [modelRes, settingsRes] = await Promise.all([
        fetch("/api/chat/model"),
        fetch("/api/models/settings"),
      ]);
      if (!modelRes.ok || !settingsRes.ok) {
        throw new Error(`Model list failed (${modelRes.status}/${settingsRes.status})`);
      }
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
        opts.push(`<option value="${esc(m)}">${esc(label)}</option>`);
      }
      sel.innerHTML = opts.join("");
      sel.value = current;
    } catch (err) {
      window.showAriaToast?.(err.message || "Could not load chat models", "err", 5000);
    }
  }

  window.loadChatModelSelect = loadChatModelSelect;

  document.getElementById("chatModelSelect")?.addEventListener("change", async (e) => {
    const form = new FormData();
    form.append("model", e.target.value);
    try {
      const res = await fetch("/api/chat/model", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Chat model update failed (${res.status})`);
      const msg = data.effective ? `Chat model: ${data.effective}` : "Chat model: default";
      const st = document.getElementById("statusText");
      if (st) st.textContent = msg;
      window.showAriaToast?.(msg, "ok", 2500);
    } catch (err) {
      window.showAriaToast?.(err.message || "Chat model update failed", "err", 5000);
    }
  });
})();
