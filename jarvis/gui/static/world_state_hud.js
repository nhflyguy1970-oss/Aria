/** Global world-state HUD — visible on all web views; polls /api/world-state */
(function () {
  const POLL_MS = 12000;
  let timer = null;
  let lastNav = { target: "workstation", reason: "" };

  function $(id) {
    return document.getElementById(id);
  }

  function hudEl() {
    return $("globalWorldStateHud") || $("worldStateHud");
  }

  function barEl() {
    return $("globalWorldStateBar");
  }

  function fmtNext(nxt) {
    if (!nxt || !nxt.title) return "";
    const mins = nxt.minutes_until;
    const when = mins != null && mins <= 120 ? ` · ${mins}m` : "";
    return ` · ${nxt.title}${when}`;
  }

  function setBarState(kind) {
    const bar = barEl();
    if (!bar) return;
    bar.classList.remove("is-warn", "is-error");
    if (kind === "warn") bar.classList.add("is-warn");
    if (kind === "error") bar.classList.add("is-error");
  }

  function setNavHint(target, label, reason) {
    lastNav = { target, reason: reason || "" };
    const bar = barEl();
    if (!bar) return;
    bar.setAttribute("aria-label", label);
  }

  async function refreshWorldHud() {
    const el = hudEl();
    if (!el) return;
    try {
      const res = await fetch("/api/world-state");
      if (res.status === 401) {
        el.textContent = "World state — API key required";
        setBarState("warn");
        setNavHint("api-key", "Open API key dialog", "API key required");
        return;
      }
      const data = await res.json();
      if (!data.ok) {
        el.textContent = data.message || "World state disabled";
        setBarState("warn");
        setNavHint("workstation", "Open Mission Control", "World state disabled");
        return;
      }
      if (!data.state) {
        el.textContent = "World state unavailable";
        setBarState("warn");
        setNavHint("workstation", "Open Mission Control", "World state unavailable");
        return;
      }
      const st = data.state;
      const proj = st.project || {};
      const slug = proj.slug || "default";
      const ha = st.home_assistant || {};
      let haOk = "—";
      if (ha.enabled) {
        haOk = ha.connected ? "HA ok" : "HA off";
      }
      const jobs = (st.jobs || {}).running_count || 0;
      const jobsTxt = jobs ? `${jobs} job${jobs === 1 ? "" : "s"}` : "idle";
      const mode = st.scene_mode ? ` · ${st.scene_mode}` : "";
      const next = fmtNext(st.planner_next);
      el.textContent = `World · ${slug} · ${haOk} · ${jobsTxt}${mode}${next}`;
      const bar = barEl();
      const titleBits = [
        data.summary || "",
        proj.name ? `Project: ${proj.name}` : "",
        st.editor && st.editor.file ? `File: ${st.editor.file}` : "",
        st.services && !st.services.ready ? "Services warming" : "",
      ].filter(Boolean);
      const haWarn = ha.enabled && !ha.connected;
      if (haWarn) titleBits.push("Click: fix Home Assistant");
      else titleBits.push("Click: Mission Control");
      if (bar) bar.title = titleBits.join("\n") || "ARIA world state";
      else el.title = titleBits.join("\n") || "World state";
      const warn = (st.services && !st.services.ready) || haWarn;
      setBarState(warn ? "warn" : "ok");
      if (haWarn) {
        setNavHint("ha", "Open Home Assistant setup", "Home Assistant offline — open setup");
      } else {
        setNavHint("workstation", "Open Mission Control", "Open Mission Control");
      }
    } catch (_) {
      el.textContent = "World state — offline";
      setBarState("error");
      setNavHint("workstation", "Open Mission Control", "World state offline");
    }
  }

  function openFromBar() {
    if (lastNav.target === "ha") {
      const sec = $("haPanel")?.closest?.(".sidebar-section");
      if (sec?.classList.contains("collapsed")) {
        sec.querySelector(".sidebar-section-head")?.click();
      }
      document.getElementById("haSetupModal")?.classList.remove("hidden");
      $("haPanel")?.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
      document.getElementById("haTestBtn")?.focus();
      window.showAriaToast?.(lastNav.reason || "Check Home Assistant connection", "warn", 3500);
      return;
    }
    if (lastNav.target === "api-key") {
      window.showApiKeyModal?.("API key required for world state.");
      return;
    }
    window.switchToView?.("workstation");
  }

  function bindBarNavigation() {
    const bar = barEl();
    if (!bar || bar.dataset.navBound === "1") return;
    bar.dataset.navBound = "1";
    bar.classList.add("is-clickable");
    bar.setAttribute("role", "button");
    bar.setAttribute("tabindex", "0");
    bar.setAttribute("aria-label", "Open Mission Control");
    bar.addEventListener("click", openFromBar);
    bar.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openFromBar();
      }
    });
  }

  function start() {
    bindBarNavigation();
    refreshWorldHud();
    if (timer) clearInterval(timer);
    timer = setInterval(() => {
      if (document.hidden) return;
      refreshWorldHud();
    }, POLL_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
