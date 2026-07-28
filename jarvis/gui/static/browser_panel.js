/** Browser live session panel — truthful status, steps, screenshots. */
(function () {
  const $ = (id) => document.getElementById(id);
  let pollTimer = null;

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.message || data.detail || data.hint || data.recovery || `Request failed (${res.status})`);
    }
    return data;
  }

  function setTaskResult(msg, tone) {
    const out = $("browserTaskResult");
    if (out) out.textContent = msg || "";
    if (msg && tone) window.showAriaToast?.(msg, tone, 4500);
  }

  function renderSteps(steps) {
    const el = $("browserStepLog");
    if (!el) return;
    const items = steps || [];
    if (!items.length) {
      el.innerHTML = "<li class='muted'>No steps yet.</li>";
      return;
    }
    el.innerHTML = items
      .slice()
      .reverse()
      .slice(0, 25)
      .map((s) => {
        const ok = s.ok !== false;
        return `<li class="${ok ? "" : "coding-warn--error"}"><strong>${escapeHtml(s.action || "")}</strong> ${escapeHtml(s.detail || s.message || "")}</li>`;
      })
      .join("");
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function applyModeAvailability(modes) {
    const sel = $("browserModeSelect");
    const runBtn = $("browserRunTaskBtn");
    const queueBtn = $("browserQueueTaskBtn");
    if (!sel) return;
    const ready = Boolean(modes?.dom || modes?.vlm);
    [...sel.options].forEach((opt) => {
      if (opt.value === "vlm") opt.disabled = !modes?.vlm;
      if (opt.value === "dom" || opt.value === "auto") opt.disabled = !modes?.dom;
    });
    if (runBtn) runBtn.disabled = !ready;
    if (queueBtn) queueBtn.disabled = !ready;
    const label = $("browserTaskLabel");
    if (label && !ready) {
      label.textContent = "Agent task (unavailable — install Playwright)";
    } else if (label) {
      label.textContent = "Agent task";
    }
  }

  async function refreshBrowserPanel({ toastOnError = false } = {}) {
    const statusEl = $("browserStatusLine");
    const urlEl = $("browserUrlLine");
    const img = $("browserScreenshot");
    const hintEl = $("browserPlaywrightHint");
    const profileEl = $("browserProfileLine");
    if (!statusEl) return;
    try {
      const st = await fetchJson("/api/browser/status");
      const agentReady = st.agent_ready ?? Boolean(st.playwright && st.chromium);
      const mode = agentReady
        ? "Playwright"
        : st.playwright && !st.chromium
          ? "Playwright (install Chromium)"
          : st.fallback || st.status === "external"
            ? "system browser (no agent)"
            : "Playwright not installed";
      statusEl.textContent = `${st.status || "idle"} · ${mode}${st.paused ? " · paused" : ""}${st.takeover ? " · takeover" : ""}${st.last_error ? " · error" : ""}`;
      if (profileEl) {
        profileEl.textContent = `Profile: ${st.profile || "_default"}${st.profile_dir ? ` → ${st.profile_dir}` : ""}`;
      }
      applyModeAvailability(st.modes_available || { dom: agentReady, vlm: agentReady });
      renderSteps(st.steps || []);
      if (urlEl) {
        if (st.url) {
          urlEl.textContent = st.url;
        } else {
          urlEl.innerHTML = `No page loaded. <button type="button" class="ghost-btn tiny" id="browserEmptyFocusUrl">Enter URL</button> or <button type="button" class="ghost-btn tiny" id="browserEmptyChatBtn">ask Chat</button>`;
          urlEl.querySelector("#browserEmptyFocusUrl")?.addEventListener("click", () => {
            $("browserUrlInput")?.focus();
          });
          urlEl.querySelector("#browserEmptyChatBtn")?.addEventListener("click", () => {
            window.switchToView?.("chat");
            window.jarvisSendToChat?.("Browse to ");
          });
        }
      }
      if (hintEl) {
        const hint = st.playwright_hint || (!agentReady ? "Install Playwright to enable live navigation and agent tasks" : "");
        hintEl.textContent = hint;
        hintEl.classList.toggle("hidden", !hint);
      }
      const meta = $("browserShotMeta");
      if (img && st.last_screenshot && (agentReady || st.session_active)) {
        img.src = `/api/browser/screenshot/image?t=${Date.now()}`;
        img.classList.remove("hidden");
        if (meta) {
          meta.classList.toggle("hidden", !st.screenshot_stale);
          meta.textContent = st.screenshot_stale ? "Screenshot may be stale" : "";
        }
      } else if (img && (st.fallback || !agentReady)) {
        img.classList.add("hidden");
        if (meta) meta.classList.add("hidden");
      }
    } catch (err) {
      statusEl.textContent = "Browser agent unavailable";
      if (toastOnError) {
        window.showAriaToast?.(err?.message || "Browser agent unavailable", "err", 5000);
      }
    }
  }

  async function navigateBrowser(explicitUrl) {
    const url = (explicitUrl || $("browserUrlInput")?.value || "").trim();
    if (!url) return;
    const out = $("browserTaskResult");
    if (out) out.textContent = `Navigating ${url}…`;
    try {
      const r = await fetchJson("/api/browser/navigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (r.ok === false) {
        const msg = [r.message, r.recovery].filter(Boolean).join(" — ");
        throw new Error(msg || "Navigate failed — page was not loaded");
      }
      if (out) out.textContent = r.message || `Navigated to ${r.url || url}`;
      window.showAriaToast?.(r.message || "Navigated", r.fallback ? "warn" : "ok", 3500);
      if (r.screenshot_warning) {
        window.showAriaToast?.(r.screenshot_warning, "warn", 4000);
      }
      await refreshBrowserPanel();
      window.initBrowserHome?.();
    } catch (e) {
      const msg = String(e.message || e);
      if (out) out.textContent = msg;
      window.showAriaToast?.(msg, "err", 5500);
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
      setTaskResult(String(e.message || e));
    }
  }

  async function runBrowserTask({ queue = false } = {}) {
    const goal = $("browserGoalInput")?.value?.trim();
    if (!goal) return;
    const out = $("browserTaskResult");
    if (out) out.textContent = queue ? "Queuing agent…" : "Running agent…";
    const mode = $("browserModeSelect")?.value || "auto";
    const url = $("browserUrlInput")?.value?.trim() || "";
    try {
      const r = await fetchJson("/api/browser/run-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, mode, max_steps: 8, url: url || undefined, async: queue }),
      });
      if (!r.ok) {
        const msg = [r.message, r.recovery].filter(Boolean).join(" — ");
        if (out) out.textContent = msg || "Browser task failed";
        window.showAriaToast?.(msg || "Browser task failed", "err", 5500);
      } else {
        if (out) out.textContent = r.message || (queue ? "Queued in Job Center" : "Done");
        window.showAriaToast?.(r.message || "Done", "ok", 3500);
        if (queue && r.job_id) window.jarvisJobs?.openJobCenter?.();
      }
      await refreshBrowserPanel();
    } catch (e) {
      if (out) out.textContent = String(e.message || e);
      window.showAriaToast?.(String(e.message || e), "err", 5000);
    }
  }

  function startPoll() {
    stopPoll();
    const tick = () => {
      if (document.hidden) return;
      const view = $("browserView");
      if (view?.classList.contains("hidden")) return;
      refreshBrowserPanel();
    };
    pollTimer = setInterval(tick, 4000);
    tick();
  }

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function applyPrefillFromChat() {
    try {
      const pre = window.__browserPrefill;
      if (!pre) return;
      if (pre.url && $("browserUrlInput")) $("browserUrlInput").value = pre.url;
      if (pre.goal && $("browserGoalInput")) $("browserGoalInput").value = pre.goal;
      window.__browserPrefill = null;
    } catch {
      /* ignore */
    }
  }

  function initBrowserPanel() {
    const root = $("browserView");
    window.initBrowserHome?.();
    applyPrefillFromChat();
    if (root?.dataset.bound === "1") {
      startPoll();
      return;
    }
    if (root) root.dataset.bound = "1";

    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && !$("browserView")?.classList.contains("hidden")) {
        refreshBrowserPanel();
      }
    });

    $("browserRefreshBtn")?.addEventListener("click", () => refreshBrowserPanel({ toastOnError: true }));
    $("browserInstallPwBtn")?.addEventListener("click", async () => {
      const out = $("browserTaskResult");
      if (out) out.textContent = "Installing Playwright + Chromium…";
      try {
        const r = await fetchJson("/api/browser/install-playwright", { method: "POST" });
        const msg = r.ok ? "Playwright ready — try Open again." : (r.hint || r.recovery || "Install failed");
        if (out) out.textContent = msg;
        window.showAriaToast?.(msg, r.ok ? "ok" : "err", 5000);
      } catch (e) {
        if (out) out.textContent = String(e.message || e);
        window.showAriaToast?.(String(e.message || e), "err", 5000);
      }
      await refreshBrowserPanel();
    });
    $("browserNavigateBtn")?.addEventListener("click", () => navigateBrowser());
    $("browserUrlInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        navigateBrowser();
      }
    });
    $("browserScreenshotBtn")?.addEventListener("click", async () => {
      try {
        const shot = await fetchJson("/api/browser/screenshot", { method: "POST" });
        if (!shot.ok && !shot.skipped) throw new Error(shot.message || shot.recovery || "Screenshot failed");
        if (shot.skipped) window.showAriaToast?.(shot.message || "Screenshot skipped", "warn", 3500);
        else window.showAriaToast?.("Screenshot captured", "ok", 2500);
        await refreshBrowserPanel();
      } catch (e) {
        window.showAriaToast?.(e.message || String(e), "err", 5000);
        setTaskResult(String(e.message || e));
      }
    });
    $("browserRunTaskBtn")?.addEventListener("click", () => runBrowserTask({ queue: false }));
    $("browserQueueTaskBtn")?.addEventListener("click", () => runBrowserTask({ queue: true }));
    $("browserPauseBtn")?.addEventListener("click", () => browserAction("/api/browser/pause", "Pause"));
    $("browserResumeBtn")?.addEventListener("click", () => browserAction("/api/browser/resume", "Resume"));
    $("browserTakeoverBtn")?.addEventListener("click", () => browserAction("/api/browser/takeover", "Takeover"));
    $("browserStopBtn")?.addEventListener("click", () => browserAction("/api/browser/stop", "Stop"));
    $("browserOpenMemoryBtn")?.addEventListener("click", () => window.switchToView?.("memory"));
    $("browserOpenDocumentsBtn")?.addEventListener("click", () => window.switchToView?.("documents"));
    $("browserOpenChatBtn")?.addEventListener("click", () => window.switchToView?.("chat"));
    $("browserBookmarkBtn")?.addEventListener("click", async () => {
      const url = $("browserUrlInput")?.value?.trim() || $("browserUrlLine")?.textContent?.trim();
      if (!url || url.startsWith("No page")) return;
      await fetch("/api/browser/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, title: url }),
      });
      window.showAriaToast?.("Bookmarked", "ok", 2500);
      window.initBrowserHome?.();
    });
    $("browserSaveDocsBtn")?.addEventListener("click", async () => {
      try {
        const r = await fetchJson("/api/browser/save-documents", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        setTaskResult(r.message || "Saved", r.ok === false ? "err" : "ok");
      } catch (e) {
        setTaskResult(String(e.message || e), "err");
      }
    });
    $("browserVisionCodingBtn")?.addEventListener("click", async () => {
      try {
        const r = await fetchJson("/api/browser/vision-coding", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ hint: $("browserGoalInput")?.value || "" }),
        });
        setTaskResult(r.message || (r.proposal_id ? `Proposal ${r.proposal_id}` : "Done"), r.ok === false ? "err" : "ok");
        if (r.proposal_id) window.openCodingHome?.("proposals");
      } catch (e) {
        setTaskResult(String(e.message || e), "err");
      }
    });
    startPoll();
  }

  window.initBrowserPanel = initBrowserPanel;
  window.stopBrowserPanelPoll = stopPoll;
  window.browserNavigate = navigateBrowser;
  window.refreshBrowserPanel = refreshBrowserPanel;
})();
