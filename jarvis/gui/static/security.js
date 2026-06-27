/** Security tab — PIN, lock, tools, brain mode, gestures */

function $(id) {
  return document.getElementById(id);
}

function sessionHeaders() {
  const token = sessionStorage.getItem("jarvis_session") || "";
  const headers = { "Content-Type": "application/json" };
  if (token) headers["X-Jarvis-Session"] = token;
  return headers;
}

async function secFetch(url, opts = {}) {
  const headers = { ...sessionHeaders(), ...(opts.headers || {}) };
  const res = await fetch(url, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || res.statusText);
  return data;
}

function renderTools(tools) {
  const el = $("securityTools");
  if (!el) return;
  const rows = tools?.tools ?? tools;
  if (Array.isArray(rows)) {
    el.innerHTML = rows
      .map((t) => {
        const detail = t.detail ? ` — ${t.detail}` : "";
        return `<li class="security-tool-row${t.ok ? " ok" : ""}"><strong>${t.name}</strong><span>${detail || (t.ok ? "ok" : "off")}</span></li>`;
      })
      .join("") || "<li class='muted'>No tool status</li>";
    return;
  }
  if (rows && typeof rows === "object") {
    el.innerHTML = Object.entries(rows)
      .map(([k, v]) => {
        const val = typeof v === "object" ? JSON.stringify(v) : String(v);
        const ok = v === true || (typeof v === "object" && v?.running);
        return `<li class="security-tool-row${ok ? " ok" : ""}"><strong>${k}</strong><span>${val}</span></li>`;
      })
      .join("") || "<li class='muted'>No tool status</li>";
    return;
  }
  el.innerHTML = "<li class='muted'>No tool status</li>";
}

async function loadSecurity() {
  const status = $("securityStatus");
  const brain = $("securityBrainMode");
  const gestures = $("securityGestures");
  const devices = $("securityDevices");
  if (!status) return;
  try {
    const lock = await secFetch("/api/security/lock/status").catch(() => ({}));
    const locked = lock.locked || (lock.pin_lock_enabled && lock.pin_configured && !lock.session_valid);
    status.textContent = locked
      ? "Screen locked — enter PIN to unlock"
      : lock.pin_configured
        ? "Unlocked"
        : "PIN not configured";
    status.classList.toggle("locked", Boolean(locked));

    const toolData = await secFetch("/api/security/tools/status").catch(() => ({}));
    renderTools(toolData);

    const brainData = await secFetch("/api/security/brain-mode").catch(() => ({}));
    if (brain) {
      brain.textContent = brainData.label || brainData.mode || "—";
      brain.title = (brainData.cloud_providers || []).join(", ");
    }

    const gestureData = await secFetch("/api/security/gestures/status").catch(() => ({}));
    if (gestures) {
      gestures.textContent = gestureData.gestures_enabled
        ? `Gestures: ${gestureData.mode || "off"} · sensitivity ${gestureData.sensitivity ?? "?"}`
        : "Gestures disabled";
      gestures.title = gestureData.help || "";
    }

    const trusted = await secFetch("/api/security/trusted-devices").catch(() => ({}));
    if (devices) {
      const list = trusted.devices || [];
      devices.innerHTML = list.length
        ? list.map((d) =>
            `<li>${d.label || d.id} <span class="muted">${d.ip || ""}</span>
             <button type="button" class="ghost-btn tiny security-revoke-btn" data-id="${d.id}">Revoke</button></li>`
          ).join("")
        : "<li class='muted'>No trusted devices</li>";
      devices.querySelectorAll(".security-revoke-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          await secFetch(`/api/security/trusted-devices/${encodeURIComponent(btn.dataset.id)}/revoke`, { method: "POST" });
          loadSecurity();
        });
      });
    }
  } catch (e) {
    status.textContent = e.message;
  }
}

async function setupPin() {
  const pin = $("securityPinInput")?.value?.trim();
  const confirm = $("securityPinConfirm")?.value?.trim();
  const msg = $("securityPinMsg");
  if (!pin || pin !== confirm) {
    if (msg) msg.textContent = "PINs must match (4–6 digits)";
    return;
  }
  try {
    await secFetch("/api/security/pin/setup", { method: "POST", body: JSON.stringify({ pin }) });
    if (msg) msg.textContent = "PIN saved";
    $("securityPinInput").value = "";
    $("securityPinConfirm").value = "";
    loadSecurity();
  } catch (e) {
    if (msg) msg.textContent = e.message;
  }
}

async function unlockScreen() {
  const pin = $("securityUnlockPin")?.value?.trim();
  const msg = $("securityUnlockMsg");
  if (!pin) return;
  try {
    const data = await secFetch("/api/security/unlock", { method: "POST", body: JSON.stringify({ pin }) });
    if (data.session_token) sessionStorage.setItem("jarvis_session", data.session_token);
    if (msg) msg.textContent = "Unlocked";
    $("securityUnlockPin").value = "";
    loadSecurity();
  } catch (e) {
    if (msg) msg.textContent = e.message;
  }
}

window.initSecurity = function initSecurity() {
  const root = $("securityView");
  if (!root || root.dataset.bound === "1") return;
  root.dataset.bound = "1";
  loadSecurity();
  $("securityLockBtn")?.addEventListener("click", async () => {
    await secFetch("/api/security/lock", { method: "POST" });
    sessionStorage.removeItem("jarvis_session");
    loadSecurity();
  });
  $("securityPinSetupBtn")?.addEventListener("click", setupPin);
  $("securityUnlockBtn")?.addEventListener("click", unlockScreen);
  $("securityRefreshBtn")?.addEventListener("click", loadSecurity);
};
