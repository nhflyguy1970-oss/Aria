/** Browser agent panel — status, screenshot, multi-step task (P2). */
(function () {
  const $ = (id) => document.getElementById(id);
  let pollTimer = null;

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.message || data.detail || data.hint || `Request failed (${res.status})`);
    }
    return data;
  }

  function setTaskResult(msg, tone) {
    const out = $("browserTaskResult");
    if (out) out.textContent = msg || "";
    if (msg) window.showAriaToast?.(msg, tone || (tone === "ok" ? "ok" : "err"), 4500);
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
    } catch (err) {
      statusEl.textContent = "Browser agent unavailable";
    }
  }

  async function navigateBrowser() {
    const url = $("browserUrlInput")?.value?.trim();
    if (!url) return;
    const out = $("browserTaskResult");
    if (out) out.textContent = `Opening ${url}…`;
    try {
      const r = await fetchJson("/api/browser/navigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (r.ok === false) {
        throw new Error(r.message || r.hint || "Navigate failed");
      }
      if (!r.fallback && r.agent_ready !== false) {
        const shot = await fetchJson("/api/browser/screenshot", { method: "POST" }).catch((e) => ({
          ok: false,
          message: e.message,
        }));
        if (!shot.ok && !shot.skipped) {
          if (out) out.textContent = shot.message || "Navigate ok — screenshot failed";
        } else if (out) {
          out.textContent = r.message || `Opened ${url}`;
        }
      } else if (out) {
        out.textContent = r.message || (r.fallback ? "Opened in system browser" : `Opened ${url}`);
      }
      window.showAriaToast?.(r.message || `Opened ${url}`, "ok", 3000);
      await refreshBrowserPanel();
    } catch (e) {
      const msg = String(e.message || e);
      if (out) out.textContent = msg;
      window.showAriaToast?.(msg, "err", 5000);
    }
  }

  async function browserAction(path, label) {
    try {
      const r = await fetchJson(path, { method: "POST" });
      if (r.ok === false) throw new Error(r.message || `${label || "Action"} failed`);
      window.showAriaToast?.(r.message || (label ? `${label} ok` : "OK"), "ok", 2500);
      await refreshBrowserPanel();
    } catch (e) {
      window.showAriaToast?.(e.message || String(e), "err", 5000);
      const out = $("browserTaskResult");
      if (out) out.textContent = String(e.message || e);
    }
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
      if (!r.ok) window.showAriaToast?.(r.message || "Browser task failed", "err", 5000);
      if (r.ok && !r.fallback) {
        const shot = await fetchJson("/api/browser/screenshot", { method: "POST" }).catch(() => ({}));
        if (!shot.ok && !shot.skipped && out) out.textContent = shot.message || out.textContent;
      }
      await refreshBrowserPanel();
    } catch (e) {
      if (out) out.textContent = String(e.message || e);
      window.showAriaToast?.(String(e.message || e), "err", 5000);
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
    const root = $("browserView");
    if (root?.dataset.bound === "1") {
      startPoll();
      return;
    }
    if (root) root.dataset.bound = "1";

    $("browserRefreshBtn")?.addEventListener("click", refreshBrowserPanel);
    $("browserInstallPwBtn")?.addEventListener("click", async () => {
      const out = $("browserTaskResult");
      if (out) out.textContent = "Installing Playwright + Chromium…";
      try {
        const r = await fetchJson("/api/browser/install-playwright", { method: "POST" });
        if (out) out.textContent = r.ok ? "Playwright ready — try Open again." : (r.hint || "Install failed");
        window.showAriaToast?.(
          r.ok ? "Playwright ready" : (r.hint || "Install failed"),
          r.ok ? "ok" : "err",
          5000,
        );
      } catch (e) {
        if (out) out.textContent = String(e.message || e);
        window.showAriaToast?.(String(e.message || e), "err", 5000);
      }
      await refreshBrowserPanel();
    });
    $("browserNavigateBtn")?.addEventListener("click", navigateBrowser);
    $("browserUrlInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        navigateBrowser();
      }
    });
    $("browserScreenshotBtn")?.addEventListener("click", async () => {
      try {
        const shot = await fetchJson("/api/browser/screenshot", { method: "POST" });
        if (!shot.ok && !shot.skipped) throw new Error(shot.message || "Screenshot failed");
        window.showAriaToast?.("Screenshot captured", "ok", 2500);
        await refreshBrowserPanel();
      } catch (e) {
        window.showAriaToast?.(e.message || String(e), "err", 5000);
        const out = $("browserTaskResult");
        if (out) out.textContent = String(e.message || e);
      }
    });
    $("browserRunTaskBtn")?.addEventListener("click", runBrowserTask);
    $("browserPauseBtn")?.addEventListener("click", () => browserAction("/api/browser/pause", "Pause"));
    $("browserResumeBtn")?.addEventListener("click", () => browserAction("/api/browser/resume", "Resume"));
    $("browserTakeoverBtn")?.addEventListener("click", () => browserAction("/api/browser/takeover", "Takeover"));
    $("browserStopBtn")?.addEventListener("click", () => browserAction("/api/browser/stop", "Stop"));
    startPoll();
  }

  window.initBrowserPanel = initBrowserPanel;
  window.stopBrowserPanelPoll = stopPoll;
})();
