/** House lock screen — one Aria Master Password (PIN only as optional convenience). */
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
  /** True when a house lock can actually be unlocked (vault or PIN). */
  window.jarvisLockCapable = false;

  const $ = (id) => document.getElementById(id);
  let idleTimer = null;
  let lastStatus = null;
  let lockEpoch = 0;
  let idleEnabled = false;

  function idleSecondsFromStatus(d) {
    const n = Number(d?.idle_seconds);
    if (!Number.isFinite(n) || n <= 0) return 0;
    return n;
  }

  window.jarvisLockHouse = async (opts = {}) => {
    const hard = opts.hard !== false;
    try {
      const st = await (window.AriaOwner?.status?.(true) || fetch("/api/security/lock/status").then((r) => r.json()));
      if (!st?.lock_capable) {
        window.showAriaToast?.(
          st?.owner_vault
            ? "Owner lock is not available"
            : "Set a Master Password before locking Aria",
          "warn",
          4000,
        );
        return { ok: false, message: "lock_not_capable" };
      }
      const res = await fetch("/api/security/lock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hard }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        window.showAriaToast?.(data.message || "Lock failed", "err", 4000);
        return data;
      }
      setSession("");
      await window.jarvisShowLock?.();
      return data;
    } catch (e) {
      const msg = String(e.message || e);
      window.showAriaToast?.(msg, "err", 5000);
      return { ok: false, message: msg };
    }
  };

  function showLock(show) {
    $("lockScreen")?.classList.toggle("hidden", !show);
    if (show) {
      // Focus whichever field is actually on screen. Status may not have
      // arrived at first paint, and focusing the hidden PIN field left the
      // first screen a user ever sees with nothing focused at all.
      const master = $("lockMasterInput");
      const pin = $("lockPinInput");
      const visible = (el) => el && el.offsetParent !== null;
      const target =
        lastStatus?.unlock_with === "master_password"
          ? master
          : visible(pin)
            ? pin
            : master;
      (visible(target) ? target : visible(master) ? master : pin)?.focus();
    }
  }

  function applyLockMode(data) {
    lastStatus = data;
    const masterMode = data.owner_vault === true;
    const pinSoft = !!data.pin_soft_unlock_available;
    $("lockScreen")?.classList.toggle("lock-mode-master", masterMode);
    $("lockScreen")?.classList.toggle("lock-mode-pin", !masterMode);
    const title = $("lockScreenTitle");
    const hint = $("lockScreenHint");
    if (title) title.textContent = "ARIA locked";
    if (hint) {
      hint.textContent = masterMode
        ? "Aria is locked. Enter your Aria Master Password to unlock the house."
        : "Enter PIN, face unlock, or use a trusted device";
    }
    const masterWrap = $("lockMasterBlock");
    const pinWrap = $("lockPinBlock");
    const faceBtn = $("lockFaceBtn");
    const trust = $("lockTrustRow");
    if (masterWrap) masterWrap.classList.toggle("hidden", !masterMode);
    if (pinWrap) pinWrap.classList.toggle("hidden", masterMode && !pinSoft);
    if (faceBtn) faceBtn.classList.toggle("hidden", masterMode);
    if (trust) trust.classList.toggle("hidden", masterMode);
    const pinInput = $("lockPinInput");
    if (pinInput) {
      pinInput.placeholder = pinSoft ? "Optional PIN" : "PIN";
    }
  }

  window.jarvisShowLock = async () => {
    try {
      const data = await (window.AriaOwner?.status?.(true) || fetch("/api/security/lock/status").then((r) => r.json()));
      applyLockMode(data);
      if (!data.lock_capable) {
        showLock(false);
        window.showAriaToast?.(
          data.owner_vault
            ? "Owner lock is not available"
            : (!data.pin_lock_enabled
              ? "PIN lock is off — enable JARVIS_PIN_LOCK=1 and set a PIN first"
              : "Set a PIN before locking Aria"),
          "warn",
          4500,
        );
        return;
      }
    } catch (_) {
      showLock(false);
      return;
    }
    setSession("");
    showLock(true);
    window.AriaOwner?.notifyLocked?.();
  };

  async function checkLock() {
    const epoch = ++lockEpoch;
    try {
      const data = await (window.AriaOwner?.status?.(true) || fetch("/api/security/lock/status").then((r) => r.json()));
      if (epoch !== lockEpoch) return;
      applyLockMode(data);
      window.jarvisLockCapable = !!data.lock_capable;
      idleEnabled = idleSecondsFromStatus(data) > 0;
      if (!data.lock_capable) {
        showLock(false);
        return;
      }
      if (data.owner_vault) {
        try { sessionStorage.setItem("aria_owner_vault", "1"); } catch (_) { /* ignore */ }
        if (data.locked) {
          setSession("");
          showLock(true);
        } else {
          showLock(false);
          resetIdle();
        }
        return;
      }
      if (data.locked) {
        showLock(true);
        return;
      }
      showLock(false);
      resetIdle();
    } catch (_) {
      if (epoch !== lockEpoch) return;
      try {
        if (sessionStorage.getItem("aria_owner_vault") === "1") {
          showLock(true);
          return;
        }
      } catch (_) { /* ignore */ }
      showLock(false);
    }
  }

  async function unlockHouse() {
    const err = $("lockError");
    const master = $("lockMasterInput")?.value || "";
    const pin = $("lockPinInput")?.value?.trim() || "";
    const trust = $("lockTrustDevice")?.checked;
    const body = { device_id: deviceId(), trust_device: trust, label: navigator.platform };
    if (lastStatus?.owner_vault) {
      if (master) body.master_password = master;
      else if (pin) body.pin = pin;
      else {
        // A message identical to the standing prompt reads as the button doing
        // nothing at all, so say what is missing instead.
        if (err) err.textContent = "Enter your Aria Master Password first.";
        $("lockMasterInput")?.focus();
        return;
      }
    } else {
      body.pin = pin;
    }
    try {
      const res = await fetch("/api/security/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok || data.ok === false) {
        const msg = data.message || "Unlock failed";
        if (err) err.textContent = msg;
        window.showAriaToast?.(msg, "err", 4000);
        return;
      }
      setSession(data.session || data.session_token);
      lockEpoch += 1;
      if ($("lockMasterInput")) $("lockMasterInput").value = "";
      if ($("lockPinInput")) $("lockPinInput").value = "";
      showLock(false);
      if (err) err.textContent = "";
      resetIdle();
      notifyUnlocked();
      window.showAriaToast?.("Aria unlocked", "ok", 2000);
    } catch (e) {
      const msg = String(e.message || e);
      if (err) err.textContent = msg;
      window.showAriaToast?.(msg, "err", 5000);
    }
  }

  function notifyUnlocked() {
    window.AriaOwner?.notifyUnlocked?.();
  }

  function resetIdle() {
    if (idleTimer) {
      clearTimeout(idleTimer);
      idleTimer = null;
    }
    if (!idleEnabled) return;
    fetch("/api/security/lock/status")
      .then((r) => r.json())
      .then((d) => {
        const sec = idleSecondsFromStatus(d);
        idleEnabled = sec > 0;
        if (sec <= 0) return;
        idleTimer = setTimeout(() => {
          setSession("");
          if (d.owner_vault) {
            fetch("/api/security/lock", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ hard: true }),
            }).finally(() => checkLock());
          } else {
            checkLock();
          }
        }, sec * 1000);
      })
      .catch(() => {});
  }

  ["click", "keydown", "touchstart"].forEach((ev) => {
    document.addEventListener(ev, () => {
      if (!idleEnabled) return;
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
        const msg = data.message || "Face unlock failed";
        if (err) err.textContent = msg;
        window.showAriaToast?.(msg, "err", 4000);
        return;
      }
      setSession(data.session || data.session_token);
      showLock(false);
      if (err) err.textContent = "";
      resetIdle();
      notifyUnlocked();
      window.showAriaToast?.("Unlocked with face", "ok", 2000);
    } catch (e) {
      const msg = String(e.message || e);
      if (err) err.textContent = msg;
      window.showAriaToast?.(msg, "err", 5000);
    }
  }

  function initLockScreen() {
    $("lockUnlockBtn")?.addEventListener("click", unlockHouse);
    $("lockFaceBtn")?.addEventListener("click", unlockWithFace);
    $("lockPinInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") unlockHouse();
    });
    $("lockMasterInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") unlockHouse();
    });
    $("pinSetupBtn")?.addEventListener("click", async () => {
      const pin = $("pinSetupInput")?.value?.trim();
      const status = $("pinSetupStatus");
      if (!pin) {
        if (status) status.textContent = "Enter 4–6 digits";
        window.showAriaToast?.("Enter 4–6 digits", "warn", 3000);
        return;
      }
      try {
        const res = await fetch("/api/security/pin/setup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pin }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          const msg = data.message || "Setup failed";
          if (status) status.textContent = msg;
          window.showAriaToast?.(msg, "err", 5000);
          return;
        }
        if (status) status.textContent = "PIN saved";
        $("pinSetupInput").value = "";
        window.showAriaToast?.("PIN saved", "ok", 2500);
      } catch (e) {
        const msg = String(e.message || e);
        if (status) status.textContent = msg;
        window.showAriaToast?.(msg, "err", 5000);
      }
    });
    checkLock();
  }

  window.initLockScreen = initLockScreen;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLockScreen);
  } else {
    initLockScreen();
  }
  window.addEventListener("pageshow", () => {
    if (typeof checkLock === "function") checkLock();
  });
})();
