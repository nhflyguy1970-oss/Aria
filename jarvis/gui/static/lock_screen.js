/** P4 PIN lock + idle re-lock */
(function () {
  const DEVICE_KEY = "jarvis_device_id";
  const SESSION_KEY = "jarvis_session";

  function deviceId() {
    let id = localStorage.getItem(DEVICE_KEY);
    if (!id) {
      id = "dev-" + Math.random().toString(36).slice(2, 12);
      localStorage.setItem(DEVICE_KEY, id);
    }
    return id;
  }

  function session() {
    return sessionStorage.getItem(SESSION_KEY) || "";
  }

  function setSession(token) {
    if (token) sessionStorage.setItem(SESSION_KEY, token);
    else sessionStorage.removeItem(SESSION_KEY);
  }

  window.jarvisDeviceId = deviceId;
  window.jarvisSession = session;
  window.jarvisSetSession = setSession;
  /** True only when PIN lock is enabled and configured — UI gates use this, not session alone. */
  window.jarvisLockCapable = false;

  const $ = (id) => document.getElementById(id);
  let idleTimer = null;

  function showLock(show) {
    $("lockScreen")?.classList.toggle("hidden", !show);
  }

  window.jarvisShowLock = () => {
    setSession("");
    showLock(true);
  };

  async function checkLock() {
    try {
      const res = await fetch("/api/security/lock/status");
      const data = await res.json();
      if (!data.pin_lock_enabled || !data.pin_configured) {
        showLock(false);
        return;
      }
      const unlockRes = await fetch("/api/security/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Jarvis-Device": deviceId() },
        body: JSON.stringify({ device_id: deviceId() }),
      });
      if (unlockRes.ok) {
        const u = await unlockRes.json();
        if (u.session) setSession(u.session);
        showLock(false);
        resetIdle();
        return;
      }
      showLock(true);
    } catch (_) {
      showLock(false);
    }
  }

  async function unlockWithPin() {
    const pin = $("lockPinInput")?.value?.trim();
    const trust = $("lockTrustDevice")?.checked;
    const err = $("lockError");
    try {
      const res = await fetch("/api/security/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin, device_id: deviceId(), trust_device: trust, label: navigator.platform }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (err) err.textContent = data.message || "Unlock failed";
        return;
      }
      setSession(data.session);
      showLock(false);
      if (err) err.textContent = "";
      resetIdle();
      notifyUnlocked();
    } catch (e) {
      if (err) err.textContent = String(e.message || e);
    }
  }

  function resetIdle() {
    if (idleTimer) clearTimeout(idleTimer);
    fetch("/api/security/lock/status")
      .then((r) => r.json())
      .then((d) => {
        const sec = d.idle_seconds || 900;
        idleTimer = setTimeout(() => {
          setSession("");
          checkLock();
        }, sec * 1000);
      })
      .catch(() => {});
  }

  ["click", "keydown", "touchstart"].forEach((ev) => {
    document.addEventListener(ev, () => {
      if (!$("lockScreen")?.classList.contains("hidden")) return;
      resetIdle();
    }, { passive: true });
  });

  async function unlockWithFace() {
    const err = $("lockError");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      const video = document.createElement("video");
      video.srcObject = stream;
      await video.play();
      await new Promise((r) => setTimeout(r, 400));
      const c = document.createElement("canvas");
      c.width = video.videoWidth || 320;
      c.height = video.videoHeight || 240;
      c.getContext("2d").drawImage(video, 0, 0);
      stream.getTracks().forEach((t) => t.stop());
      const image = c.toDataURL("image/jpeg", 0.85);
      const res = await fetch("/api/security/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Jarvis-Device": deviceId() },
        body: JSON.stringify({ image, device_id: deviceId() }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (err) err.textContent = data.message || "Face unlock failed";
        return;
      }
      setSession(data.session);
      showLock(false);
      if (err) err.textContent = "";
      resetIdle();
      notifyUnlocked();
    } catch (e) {
      if (err) err.textContent = String(e.message || e);
    }
  }

  function initLockScreen() {
    $("lockUnlockBtn")?.addEventListener("click", unlockWithPin);
    $("lockFaceBtn")?.addEventListener("click", unlockWithFace);
    $("lockPinInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") unlockWithPin();
    });
    $("pinSetupBtn")?.addEventListener("click", async () => {
      const pin = $("pinSetupInput")?.value?.trim();
      const status = $("pinSetupStatus");
      if (!pin) {
        if (status) status.textContent = "Enter 4–6 digits";
        return;
      }
      try {
        const res = await fetch("/api/security/pin/setup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pin }),
        });
        const data = await res.json();
        if (status) status.textContent = res.ok ? "PIN saved" : (data.message || "Setup failed");
        if (res.ok) $("pinSetupInput").value = "";
      } catch (e) {
        if (status) status.textContent = String(e.message || e);
      }
    });
    checkLock();
  }

  window.initLockScreen = initLockScreen;
  document.addEventListener("DOMContentLoaded", initLockScreen);
})();
