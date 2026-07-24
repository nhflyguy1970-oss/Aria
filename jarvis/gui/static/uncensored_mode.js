/** Uncensored mode unlock — extracted from app.js. */
(function () {
  "use strict";

const uncensoredToggle = document.getElementById("uncensoredToggle");
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
        (document.getElementById("modeLabel") || {}).textContent = "Uncensored · Local AI Assistant";
        return;
      }
    }
    const authRes = await fetch(`/api/uncensored/auth?session_token=${encodeURIComponent(token)}`);
    if (!authRes.ok) {
      sessionStorage.removeItem(UNCENSORED_SESSION_KEY);
      throw new Error(`Session validation failed (${authRes.status})`);
    }
    const auth = await authRes.json();
    if (!auth.session_valid) {
      sessionStorage.removeItem(UNCENSORED_SESSION_KEY);
      window.showAriaToast?.("Uncensored session expired; sign in again to restore it", "info", 4000);
      return;
    }
    const form = new FormData();
    form.append("uncensored", "true");
    form.append("session_token", token);
    const res = await fetch("/api/mode", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || !data.uncensored) {
      throw new Error(data.message || data.detail || `Mode restore failed (${res.status})`);
    }
    if (data.session_token) sessionStorage.setItem(UNCENSORED_SESSION_KEY, data.session_token);
    uncensoredToggle.checked = true;
    document.body.classList.add("uncensored-mode");
    (document.getElementById("modeLabel") || {}).textContent = "Uncensored · Local AI Assistant";
    if (data.comfyui_settings) window.loadComfyMode?.();
  } catch (e) {
    window.showAriaToast?.(
      `Could not restore uncensored session: ${e?.message || e}`,
      "err",
      5000,
    );
  }
}

uncensoredToggle?.addEventListener("change", async () => {
  const wantUncensored = uncensoredToggle.checked;
  if (!wantUncensored) {
    try {
      const form = new FormData();
      form.append("uncensored", "false");
      const res = await fetch("/api/mode", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        window.showAriaToast?.(data.message || `Could not leave uncensored mode (${res.status})`, "err", 5000);
        uncensoredToggle.checked = true;
        return;
      }
      sessionStorage.removeItem(UNCENSORED_SESSION_KEY);
      document.body.classList.toggle("uncensored-mode", data.uncensored);
      (document.getElementById("modeLabel") || {}).textContent = data.uncensored ? "Uncensored · Local" : "Local AI Assistant";
      const settings = await window.loadModelSettings?.();
      if (settings) window.renderModelSettings?.({ ...settings, mode: "standard" });
      if (data.comfyui_settings) window.syncComfySettings?.(data.comfyui_settings);
    } catch (err) {
      uncensoredToggle.checked = true;
      window.showAriaToast?.(err?.message || "Could not leave uncensored mode", "err", 5000);
    }
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

  try {
    const form = new FormData();
    form.append("uncensored", "true");
    form.append("password", password);
    form.append("confirm_password", confirm);
    form.append("session_token", sessionToken);
    const res = await fetch("/api/mode", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      const failMsg = data.message || `Uncensored unlock failed (${res.status})`;
      if (statusText) (document.getElementById("statusText") || {}).textContent = failMsg;
      window.showAriaToast?.(failMsg, "err", 5000);
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
        const data2 = await res2.json().catch(() => ({}));
        if (!res2.ok || data2.ok === false) {
          const msg2 = data2.message || `Uncensored unlock failed (${res2.status})`;
          (document.getElementById("statusText") || {}).textContent = msg2;
          window.showAriaToast?.(msg2, "err", 5000);
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
    (document.getElementById("modeLabel") || {}).textContent = data.uncensored ? "Uncensored · Local" : "Local AI Assistant";
    window.showAriaToast?.(data.uncensored ? "Uncensored mode unlocked" : "Standard mode", "ok", 3000);
    const settings = await window.loadModelSettings?.();
    if (settings) window.renderModelSettings?.({ ...settings, mode: data.uncensored ? "uncensored" : "standard" });
    if (data.comfyui_settings) {
      window.syncComfySettings?.(data.comfyui_settings);
    } else {
      await window.loadComfyMode?.();
    }
  } catch (err) {
    window.showAriaToast?.(err?.message || "Uncensored unlock failed", "err", 5000);
  }
});

  window.restoreUncensoredSession = restoreUncensoredSession;
  window.showUncensoredPasswordModal = showUncensoredPasswordModal;
})();
