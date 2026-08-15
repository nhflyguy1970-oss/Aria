/** P4 security settings — PIN, trusted devices, lock status, voice/presence */
(function () {
  const $ = (id) => document.getElementById(id);
  let initialized = false;

  function isRoomAbort(err) {
    return !!(
      window.AriaNet?.isRoomAbort?.(err) ||
      err?.name === "AbortError" ||
      /aborted|aria-room-leave/i.test(String(err?.message || err?.reason || ""))
    );
  }

  function renderOwnerPanels(data) {
    const setup = $("ownerSetupForm");
    const recovery = $("ownerRecoveryPanel");
    const unlocked = $("ownerUnlockedPanel");
    const sessionLine = $("ownerSessionLine");
    const vault = !!data.owner_vault;
    const recovering = !recovery?.classList.contains("hidden") && !!$("ownerRecoveryKey")?.textContent;
    if (setup) setup.classList.toggle("hidden", vault || recovering);
    if (unlocked) unlocked.classList.toggle("hidden", !vault || recovering);
    if (sessionLine && vault) {
      sessionLine.textContent = data.owner_unlocked
        ? "Owner session active — Rooms share this unlock."
        : "Aria is locked. Enter your Master Password to continue.";
    }
  }

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
        if (data.owner_vault) {
          parts.push(data.owner_unlocked ? "Aria unlocked" : "Aria locked");
          parts.push("one Master Password");
        } else {
          parts.push("Master Password not set");
        }
        if (data.pin_lock_enabled) parts.push("PIN lock on");
        else parts.push("optional PIN off");
        if (data.pin_configured) parts.push("PIN set");
        if (data.face?.enrolled) parts.push("Face enrolled");
        status.textContent = parts.join(" · ");
      }
      renderOwnerPanels(data);
      const td = await fetchJson("/api/security/trusted-devices");
      const list = td.devices || [];
      if (devices) {
        devices.innerHTML = list.length
          ? list.map((d) => `<li>${esc(d.label || d.id)} `
            + `<button type="button" class="ghost-btn tiny trusted-revoke" data-id="${esc(d.id)}">Revoke</button></li>`).join("")
          : "<li class='muted'>No trusted devices yet. Unlock with PIN once, then use <button type='button' class='ghost-btn tiny' id='securityEmptyPresenceBtn'>Presence</button> / face enroll if available.</li>";
        devices.querySelector("#securityEmptyPresenceBtn")?.addEventListener("click", () => {
          window.switchToView?.("presence");
        });
        devices.querySelectorAll(".trusted-revoke").forEach((btn) => {
          btn.addEventListener("click", async () => {
            try {
              const out = await fetchJson(
                `/api/security/trusted-devices/${encodeURIComponent(btn.dataset.id)}/revoke`,
                { method: "POST" },
              );
              if (out.ok === false) {
                window.showAriaToast?.(out.message || out.error || "Revoke failed", "err", 5000);
                return;
              }
              window.showAriaToast?.("Trusted device revoked", "ok", 3000);
              refreshSecurityPanel();
            } catch (err) {
              window.showAriaToast?.(err.message || "Revoke failed", "err", 5000);
            }
          });
        });
      }
    } catch (e) {
      if (isRoomAbort(e)) {
        const still =
          document.body.classList.contains("house-security") ||
          /^#?security\b/i.test(location.hash || "");
        if (still) {
          clearTimeout(refreshSecurityPanel._retry);
          refreshSecurityPanel._retry = setTimeout(() => {
            if (
              document.body.classList.contains("house-security") ||
              /^#?security\b/i.test(location.hash || "")
            ) {
              refreshSecurityPanel();
            }
          }, 160);
        }
        return;
      }
      if (status) status.textContent = `Security API: ${e.message || "unavailable"}`;
      window.showAriaToast?.(e.message || "Security status unavailable", "err", 5000);
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
        if (!res.ok || data.ok === false) {
          const msg = data.message || "PIN setup failed — check the server is running, then try again";
          if (out) out.textContent = msg;
          window.showAriaToast?.(msg, "err", 5000);
          return;
        }
        if (out) out.textContent = "PIN saved";
        $("securityPinInput").value = "";
        window.showAriaToast?.("PIN saved", "ok", 2500);
        refreshSecurityPanel();
      } catch (e) {
        const msg = e.message || "PIN setup failed — check the server is running, then try again";
        if (out) out.textContent = msg;
        window.showAriaToast?.(msg, "err", 5000);
      }
    });
    $("securityLockBtn")?.addEventListener("click", async () => {
      const out = $("securityPinStatus");
      try {
        const data = await (window.jarvisLockHouse
          ? window.jarvisLockHouse({ hard: true })
          : Promise.resolve({ ok: false, message: "Lock is not available." }));
        if (data?.ok === false && out) out.textContent = data.message || "Lock failed";
      } catch (e) {
        if (out) out.textContent = e.message || "Lock failed";
        window.showAriaToast?.(e.message || "Lock failed", "err");
      }
    });
    $("ownerSetupBtn")?.addEventListener("click", async () => {
      const out = $("ownerSecurityStatus");
      const pw = $("ownerMasterInput")?.value || "";
      const confirm = $("ownerMasterConfirm")?.value || "";
      if (pw.length < 12) {
        if (out) out.textContent = "Master Password must be at least 12 characters";
        return;
      }
      if (pw !== confirm) {
        if (out) out.textContent = "Passwords do not match";
        return;
      }
      try {
        const res = await fetch("/api/owner-security/setup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ master_password: pw, confirm_password: confirm }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          if (out) out.textContent = data.message || "Setup failed";
          window.showAriaToast?.(data.message || "Setup failed", "err", 5000);
          return;
        }
        window.jarvisSetSession?.(data.session_token);
        $("ownerMasterInput").value = "";
        $("ownerMasterConfirm").value = "";
        $("ownerSetupForm")?.classList.add("hidden");
        $("ownerRecoveryPanel")?.classList.remove("hidden");
        $("ownerUnlockedPanel")?.classList.add("hidden");
        const keyEl = $("ownerRecoveryKey");
        if (keyEl) keyEl.textContent = data.recovery_key || "";
        if (out) out.textContent = "Store the recovery key, then continue.";
        window.showAriaToast?.("Master Password created — store the recovery key", "ok", 4000);
      } catch (e) {
        if (out) out.textContent = e.message || "Setup failed";
        window.showAriaToast?.(e.message || "Setup failed", "err", 5000);
      }
    });
    $("ownerRecoveryAckBtn")?.addEventListener("click", async () => {
      const out = $("ownerSecurityStatus");
      if (!$("ownerRecoveryAck")?.checked) {
        if (out) out.textContent = "Confirm you stored the recovery key offline.";
        return;
      }
      try {
        const res = await fetch("/api/owner-security/recovery/acknowledge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ stored: true }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          if (out) out.textContent = data.message || "Acknowledgement failed";
          return;
        }
        const keyEl = $("ownerRecoveryKey");
        if (keyEl) keyEl.textContent = "";
        $("ownerRecoveryPanel")?.classList.add("hidden");
        $("ownerUnlockedPanel")?.classList.remove("hidden");
        if (out) out.textContent = "Aria unlocked. One password from here.";
        window.showAriaToast?.("Aria unlocked", "ok", 2500);
        refreshSecurityPanel();
      } catch (e) {
        if (out) out.textContent = e.message || "Acknowledgement failed";
      }
    });
    $("ownerLockBtn")?.addEventListener("click", async () => {
      const out = $("ownerSecurityStatus");
      try {
        const data = await window.jarvisLockHouse?.({ hard: true });
        if (data?.ok === false && out) out.textContent = data.message || "Lock failed";
      } catch (e) {
        if (out) out.textContent = e.message || "Lock failed";
      }
    });
    $("securityOpenPresenceBtn")?.addEventListener("click", () => window.switchToView?.("presence"));
    $("securityOpenVoiceBtn")?.addEventListener("click", () => window.switchToView?.("voice"));
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
