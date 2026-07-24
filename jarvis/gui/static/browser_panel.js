/** Browser agent panel — status, screenshot, multi-step task (P2). */
(function () {
  const $ = (id) => document.getElementById(id);
  let pollTimer = null;

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  async function refreshBrowserPanel() {
    const statusEl = $("browserStatusLine");
    const urlEl = $("browserUrlLine");
    const img = $("browserScreenshot");
    const hintEl = $("browserPlaywrightHint");
    if (!statusEl) return;
    try {
      const st = await fetchJson("/api/browser/status");
      const agentReady = st.agent_ready ?? Boolean(st.playwright && st.chromium);
      const mode = agentReady
        ? "Playwright"
        : st.playwright && !st.chromium
          ? "Playwright (install Chromium)"
          : st.fallback || st.status === "external"
            ? "system browser"
            : "Playwright not installed";
      statusEl.textContent = `${st.status || "idle"} · ${mode}${st.paused ? " · paused" : ""}${st.takeover ? " · takeover" : ""}`;
      if (urlEl) urlEl.textContent = st.url || "No page loaded";
      if (hintEl) {
        const hint = st.playwright_hint || (
          !agentReady
            ? "Full agent: pip install playwright && playwright install chromium"
            : ""
        );
        hintEl.textContent = hint;
        hintEl.classList.toggle("hidden", !hint);
      }
      if (img && st.last_screenshot && agentReady) {
        img.src = `/api/browser/screenshot/image?t=${Date.now()}`;
        img.classList.remove("hidden");
      } else if (img && (st.fallback || !agentReady)) {
        img.classList.add("hidden");
      }
    } catch (_) {
      statusEl.textContent = "Browser agent unavailable";
    }
  }

  async function navigateBrowser() {
    const url = $("browserUrlInput")?.value?.trim();
    if (!url) return;
    const r = await fetchJson("/api/browser/navigate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!r.fallback && r.agent_ready !== false) {
      const shot = await fetchJson("/api/browser/screenshot", { method: "POST" });
      if (!shot.ok && !shot.skipped) {
        const out = $("browserTaskResult");
        if (out) out.textContent = shot.message || "";
      }
    }
    await refreshBrowserPanel();
  }

  async function browserAction(path) {
    await fetchJson(path, { method: "POST" });
    await refreshBrowserPanel();
  }

  async function runBrowserTask() {
    const goal = $("browserGoalInput")?.value?.trim();
    if (!goal) return;
    const out = $("browserTaskResult");
    if (out) out.textContent = "Running agent…";
    const mode = $("browserModeSelect")?.value || "auto";
    try {
      const r = await fetchJson("/api/browser/run-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, mode, max_steps: 5 }),
      });
      if (out) {
        out.textContent = r.ok
          ? (r.message || "Done")
          : (r.message || "Failed");
      }
      if (r.ok && !r.fallback) {
        const shot = await fetchJson("/api/browser/screenshot", { method: "POST" });
        if (!shot.ok && !shot.skipped && out) out.textContent = shot.message || out.textContent;
      }
      await refreshBrowserPanel();
    } catch (e) {
      if (out) out.textContent = String(e);
    }
  }

  function startPoll() {
    stopPoll();
    pollTimer = setInterval(refreshBrowserPanel, 4000);
    refreshBrowserPanel();
  }

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function initBrowserPanel() {
    $("browserRefreshBtn")?.addEventListener("click", refreshBrowserPanel);
    $("browserInstallPwBtn")?.addEventListener("click", async () => {
      const out = $("browserTaskResult");
      if (out) out.textContent = "Installing Playwright + Chromium…";
      try {
        const r = await fetchJson("/api/browser/install-playwright", { method: "POST" });
        if (out) out.textContent = r.ok ? "Playwright ready — try Open again." : (r.hint || "Install failed");
      } catch (e) {
        if (out) out.textContent = String(e);
      }
      await refreshBrowserPanel();
    });
    $("browserNavigateBtn")?.addEventListener("click", navigateBrowser);
    $("browserScreenshotBtn")?.addEventListener("click", async () => {
      await fetchJson("/api/browser/screenshot", { method: "POST" });
      await refreshBrowserPanel();
    });
    $("browserRunTaskBtn")?.addEventListener("click", runBrowserTask);
    $("browserPauseBtn")?.addEventListener("click", () => browserAction("/api/browser/pause"));
    $("browserResumeBtn")?.addEventListener("click", () => browserAction("/api/browser/resume"));
    $("browserTakeoverBtn")?.addEventListener("click", () => browserAction("/api/browser/takeover"));
    $("browserStopBtn")?.addEventListener("click", () => browserAction("/api/browser/stop"));
    startPoll();
  }

  window.initBrowserPanel = initBrowserPanel;
  window.stopBrowserPanelPoll = stopPoll;
})();
