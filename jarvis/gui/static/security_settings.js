/** P4 security settings — PIN, trusted devices, lock status, voice/presence */
(function () {
  const $ = (id) => document.getElementById(id);
  let initialized = false;

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || res.statusText || "Request failed");
    return data;
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  async function refreshSecurityPanel() {
    const status = $("securityStatusLine");
    const devices = $("trustedDevicesList");
    try {
      const data = await fetchJson("/api/security/lock/status");
      if (status) {
        const parts = [];
        if (data.pin_lock_enabled) parts.push("PIN lock on");
        else parts.push("PIN lock off (set JARVIS_PIN_LOCK=1)");
        if (data.pin_configured) parts.push("PIN set");
        if (data.face?.enrolled) parts.push("Face enrolled");
        status.textContent = parts.join(" · ");
      }
      const td = await fetchJson("/api/security/trusted-devices");
      const list = td.devices || [];
      if (devices) {
        devices.innerHTML = list.length
          ? list.map((d) => `<li>${esc(d.label || d.id)} `
            + `<button type="button" class="ghost-btn tiny trusted-revoke" data-id="${esc(d.id)}">Revoke</button></li>`).join("")
          : "<li class='muted'>No trusted devices</li>";
        devices.querySelectorAll(".trusted-revoke").forEach((btn) => {
          btn.addEventListener("click", async () => {
            try {
              await fetchJson(
                `/api/security/trusted-devices/${encodeURIComponent(btn.dataset.id)}/revoke`,
                { method: "POST" },
              );
              window.showAriaToast?.("Trusted device revoked", "ok", 3000);
              refreshSecurityPanel();
            } catch (err) {
              window.showAriaToast?.(err.message || "Revoke failed", "err", 5000);
            }
          });
        });
      }
    } catch (e) {
      if (status) status.textContent = `Security API: ${e.message || "unavailable"}`;
    }

    try {
      const cloud = await fetchJson("/api/voice/cloud-live/status");
      const line = $("securityCloudLiveLine");
      if (line) {
        const keyHint = cloud.gemini_key && !cloud.gemini_key_usable
          ? " — Gemini key should start with AIza (Google AI Studio)"
          : "";
        line.textContent = cloud.available
          ? `Cloud live: ready (${cloud.provider || "auto"})${keyHint}`
          : `Cloud live: ${cloud.message || "unavailable"}${keyHint}`;
      }
    } catch (_) {
      $("securityCloudLiveLine") && ($("securityCloudLiveLine").textContent = "Cloud live: status unavailable");
    }

    try {
      const g = await fetchJson("/api/security/gestures/status");
      const gLine = $("securityGesturesLine");
      if (gLine) {
        gLine.textContent = g.gestures_enabled
          ? `Gestures: ${g.mode || "off"} · floating panels ${g.floating_panels ? "on" : "off"}`
          : "Gestures: disabled — set JARVIS_GESTURES=1 to enable";
      }
    } catch (_) {
      const gLine = $("securityGesturesLine");
      if (gLine) gLine.textContent = "Gestures: status unavailable";
    }

    try {
      const b = await fetchJson("/api/security/brain-mode");
      const bLine = $("securityBrainLine");
      if (bLine) bLine.textContent = `Brain mode: ${b.label || b.mode || "local"}`;
    } catch (_) {
      const bLine = $("securityBrainLine");
      if (bLine) bLine.textContent = "Brain mode: status unavailable";
    }
  }

  function initSecuritySettings() {
    if (initialized) return;
    initialized = true;
    $("securityPinBtn")?.addEventListener("click", async () => {
      const pin = $("securityPinInput")?.value?.trim();
      const out = $("securityPinStatus");
      if (!pin) {
        if (out) out.textContent = "Enter 4–6 digits";
        return;
      }
      try {
        const res = await fetch("/api/security/pin/setup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pin }),
        });
        const data = await res.json();
        if (out) out.textContent = res.ok ? "PIN saved" : (data.message || "Failed");
        if (res.ok) $("securityPinInput").value = "";
        refreshSecurityPanel();
      } catch (e) {
        if (out) out.textContent = e.message || "Failed";
      }
    });
    $("securityLockBtn")?.addEventListener("click", async () => {
      const out = $("securityPinStatus");
      try {
        const res = await fetch("/api/security/lock", { method: "POST" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          if (out) out.textContent = data.message || "Lock failed";
          window.showAriaToast?.(data.message || "Lock failed", "err");
          return;
        }
        window.jarvisShowLock?.();
      } catch (e) {
        if (out) out.textContent = e.message || "Lock failed";
        window.showAriaToast?.(e.message || "Lock failed", "err");
      }
    });
    refreshSecurityPanel();
  }

  window.refreshSecurityPanel = refreshSecurityPanel;
  window.initSecuritySettings = initSecuritySettings;
  window.initSecurity = function initSecurity() {
    initSecuritySettings();
    refreshSecurityPanel();
  };
  document.addEventListener("DOMContentLoaded", initSecuritySettings);
})();
