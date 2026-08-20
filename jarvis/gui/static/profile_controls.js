/** Profile / personality / actions clear / debug bundle — extracted from app.js. */
(function () {
  function statusEl() {
    return document.getElementById("statusText");
  }

  document.getElementById("profileSelect")?.addEventListener("change", async (e) => {
    const pid = e.target.value;
    if (!pid) return;
    try {
      const res = await fetch("/api/profiles/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: pid }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        const msg = data.message || data.detail || "Profile switch failed";
        const st = statusEl();
        if (st) st.textContent = msg;
        window.showAriaToast?.(msg, "err", 5000);
        return;
      }
      const msg = `Profile: ${data.label || pid}`;
      const st = statusEl();
      if (st) st.textContent = msg;
      window.showAriaToast?.(msg, "ok", 2500);
      window.loadModels?.();
    } catch (_) {
      const st = statusEl();
      if (st) st.textContent = "Profile switch failed";
      window.showAriaToast?.("Profile switch failed", "err", 5000);
    }
  });

  document.getElementById("actionsClearBtn")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/actions/clear", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        throw new Error(data.message || data.detail || `Clear failed (${res.status})`);
      }
      window.showAriaToast?.("Action log cleared", "ok", 2500);
      window.loadActions?.(document.getElementById("actionsFilter")?.value);
    } catch (err) {
      window.showAriaToast?.(err.message || "Clear failed", "err", 5000);
    }
  });

  document.getElementById("personalitySelect")?.addEventListener("change", async (e) => {
    const form = new FormData();
    form.append("preset", e.target.value);
    try {
      const res = await fetch("/api/personality", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) throw new Error(data.message || data.detail || `Personality update failed (${res.status})`);
      const msg = `Personality: ${e.target.value}`;
      const st = statusEl();
      if (st) st.textContent = msg;
      window.showAriaToast?.(msg, "ok", 2500);
    } catch (err) {
      window.showAriaToast?.(err.message || "Personality update failed", "err", 5000);
    }
  });

  document.getElementById("debugBundleBtn")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/debug/bundle");
      const data = await res.json();
      const text = data.text || JSON.stringify(data, null, 2);
      if (navigator.clipboard?.writeText) {
        await window.ariaCopy(text);
        const st = statusEl();
        if (st) st.textContent = "Debug bundle copied to clipboard";
        window.showAriaToast?.("Debug bundle copied", "ok", 2500);
      } else {
        if (window.ariaPrompt) {
          await window.ariaPrompt("Copy debug bundle:", text.slice(0, 8000), {
            title: "Debug bundle",
            okLabel: "Close",
          });
        } else {
          prompt("Copy debug bundle:", text.slice(0, 8000));
        }
      }
    } catch (e) {
      window.showError?.(`Debug bundle failed: ${e.message || e}`);
      window.showAriaToast?.(`Debug bundle failed: ${e.message || e}`, "err", 5000);
    }
  });
})();
