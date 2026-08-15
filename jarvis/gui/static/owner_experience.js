/** One-password owner session — house-wide unlock. Vault stays invisible. */
(function () {
  const SESSION_KEY = "jarvis_session";

  function session() {
    return (typeof window.jarvisSession === "function" ? window.jarvisSession() : sessionStorage.getItem(SESSION_KEY)) || "";
  }

  function setSession(token) {
    if (typeof window.jarvisSetSession === "function") window.jarvisSetSession(token);
    else if (token) sessionStorage.setItem(SESSION_KEY, token);
    else sessionStorage.removeItem(SESSION_KEY);
  }

  let _status = null;
  let _statusAt = 0;

  async function fetchStatus(force) {
    const now = Date.now();
    if (!force && _status && now - _statusAt < 400) return _status;
    const res = await fetch("/api/security/lock/status");
    _status = await res.json().catch(() => ({}));
    _statusAt = now;
    window.jarvisLockCapable = !!_status.lock_capable;
    return _status;
  }

  function isHouseLocked(st) {
    if (!st) return false;
    if (st.owner_vault) return !!st.locked;
    return !!st.locked;
  }

  async function authorize(capability, room) {
    const res = await fetch("/api/owner-security/authorize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capability, room: room || "" }),
    });
    return res.json().catch(() => ({ ok: false, message: "Authorize failed" }));
  }

  async function requireUnlocked() {
    const st = await fetchStatus(true);
    if (isHouseLocked(st)) {
      window.jarvisShowLock?.();
      return false;
    }
    return true;
  }

  window.AriaOwner = {
    status: fetchStatus,
    authorize,
    requireUnlocked,
    isHouseLocked,
    session,
    setSession,
    notifyUnlocked() {
      try {
        window.dispatchEvent(new CustomEvent("aria-owner-unlocked"));
      } catch (_) { /* ignore */ }
    },
    notifyLocked() {
      try {
        window.dispatchEvent(new CustomEvent("aria-owner-locked"));
      } catch (_) { /* ignore */ }
    },
  };
})();
