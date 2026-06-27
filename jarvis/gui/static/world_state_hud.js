/** Global world-state HUD — visible on all web views; polls /api/world-state */
(function () {
  const POLL_MS = 12000;
  let timer = null;

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

  async function refreshWorldHud() {
    const el = hudEl();
    if (!el) return;
    try {
      const res = await fetch("/api/world-state");
      if (res.status === 401) {
        el.textContent = "World state — API key required";
        setBarState("warn");
        return;
      }
      const data = await res.json();
      if (!data.ok) {
        el.textContent = data.message || "World state disabled";
        setBarState("warn");
        return;
      }
      if (!data.state) {
        el.textContent = "World state unavailable";
        setBarState("warn");
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
      if (bar) {
        bar.title = [
          data.summary || "",
          proj.name ? `Project: ${proj.name}` : "",
          st.editor && st.editor.file ? `File: ${st.editor.file}` : "",
          st.services && !st.services.ready ? "Services warming" : "",
        ].filter(Boolean).join("\n") || "ARIA world state";
      } else {
        el.title = bar?.title || "World state";
      }
      const warn = (st.services && !st.services.ready) || (ha.enabled && !ha.connected);
      setBarState(warn ? "warn" : "ok");
    } catch (_) {
      el.textContent = "World state — offline";
      setBarState("error");
    }
  }

  function start() {
    refreshWorldHud();
    if (timer) clearInterval(timer);
    timer = setInterval(refreshWorldHud, POLL_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
