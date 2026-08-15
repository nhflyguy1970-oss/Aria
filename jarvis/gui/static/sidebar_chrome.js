/** Sidebar layout, collapse defaults, width, restart chrome — modernization. */
(function () {
  "use strict";

  const COLLAPSE_LEGACY = "jarvis_sidebar_collapsed";
  const COLLAPSE_V2 = "jarvis_sidebar_collapse_migrated_v2";

  function $(id) {
    return document.getElementById(id);
  }

  function loadCollapsedMap() {
    const prefs = window.AriaUiPrefs?.load?.();
    if (prefs?.sidebarCollapsed && typeof prefs.sidebarCollapsed === "object") {
      return { ...prefs.sidebarCollapsed };
    }
    try {
      return JSON.parse(localStorage.getItem(COLLAPSE_LEGACY) || "{}");
    } catch {
      return {};
    }
  }

  function saveCollapsedMap(map) {
    localStorage.setItem(COLLAPSE_LEGACY, JSON.stringify(map));
    window.AriaUiPrefs?.set?.("sidebarCollapsed", map);
  }

  function defaultCollapsedMap() {
    const map = {};
    document.querySelectorAll(".sidebar-section[data-section]").forEach((sec) => {
      const key = sec.dataset.section;
      if (!key || key === "favorites") return;
      map[key] = true; // collapsed
    });
    return map;
  }

  function applyCollapsed(map) {
    document.querySelectorAll(".sidebar-section[data-section]").forEach((sec) => {
      const key = sec.dataset.section;
      if (!key || sec.classList.contains("sidebar-section--pinned")) return;
      const head = sec.querySelector(".sidebar-section-head");
      if (!head) return;
      const collapsed = !!map[key];
      sec.classList.toggle("collapsed", collapsed);
      head.setAttribute("aria-expanded", collapsed ? "false" : "true");
    });
  }

  function initCollapsibleSections() {
    let collapsed = loadCollapsedMap();
    if (!localStorage.getItem(COLLAPSE_V2)) {
      collapsed = defaultCollapsedMap();
      // preserve any explicit expand the user already had for models only if they used v1 heavily
      saveCollapsedMap(collapsed);
      localStorage.setItem(COLLAPSE_V2, "1");
    }
    applyCollapsed(collapsed);

    document.querySelectorAll(".sidebar-section[data-section]").forEach((sec) => {
      const key = sec.dataset.section;
      const head = sec.querySelector(".sidebar-section-head");
      if (!head || sec.dataset.collapseBound === "1") return;
      if (sec.classList.contains("sidebar-section--pinned")) return;
      sec.dataset.collapseBound = "1";
      head.addEventListener("click", () => {
        sec.classList.toggle("collapsed");
        const map = loadCollapsedMap();
        map[key] = sec.classList.contains("collapsed");
        saveCollapsedMap(map);
        head.setAttribute("aria-expanded", sec.classList.contains("collapsed") ? "false" : "true");
        if (key === "models" && !sec.classList.contains("collapsed")) {
          $("modelsEditor")?.classList.remove("hidden");
          $("modelsToggle")?.setAttribute("aria-expanded", "true");
          window.loadModelSettings?.();
        }
      });
    });
  }

  function resetSidebarLayout() {
    const map = defaultCollapsedMap();
    // expand all when user asks "Expand sidebar"
    Object.keys(map).forEach((k) => {
      map[k] = false;
    });
    saveCollapsedMap(map);
    applyCollapsed(map);
    document.body.classList.remove("mobile-sidebar-open");
  }

  function collapseAllSidebar() {
    const map = defaultCollapsedMap();
    saveCollapsedMap(map);
    applyCollapsed(map);
  }

  function applySidebarWidth(px) {
    const w = Math.max(200, Math.min(420, Number(px) || 260));
    document.documentElement.style.setProperty("--sidebar-width", `${w}px`);
    const app = document.querySelector(".app");
    if (app) app.style.gridTemplateColumns = `${w}px minmax(0, 1fr)`;
    window.AriaUiPrefs?.set?.("sidebarWidth", w);
  }

  function initSidebarResize() {
    const handle = $("sidebarResizeHandle");
    if (!handle) return;
    const saved = window.AriaUiPrefs?.get?.("sidebarWidth", 260);
    applySidebarWidth(saved);
    let dragging = false;
    handle.addEventListener("pointerdown", (e) => {
      dragging = true;
      handle.setPointerCapture?.(e.pointerId);
      document.body.classList.add("resizing-sidebar");
    });
    window.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      applySidebarWidth(e.clientX);
    });
    window.addEventListener("pointerup", () => {
      if (!dragging) return;
      dragging = false;
      document.body.classList.remove("resizing-sidebar");
    });
  }

  async function waitForServerBack(maxMs = 90000) {
    const start = Date.now();
    const deadline = start + maxMs;
    await new Promise((r) => setTimeout(r, 500));
    let sawDown = false;
    const downDeadline = Math.min(deadline, Date.now() + 10000);
    while (Date.now() < downDeadline) {
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        if (!res.ok) {
          sawDown = true;
          break;
        }
      } catch {
        sawDown = true;
        break;
      }
      await new Promise((r) => setTimeout(r, 350));
    }
    if (!sawDown) await new Promise((r) => setTimeout(r, 1500));
    while (Date.now() < deadline) {
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        if (res.ok) {
          const data = await res.json().catch(() => ({}));
          if (data.version) return true;
        }
      } catch {
        /* keep waiting */
      }
      await new Promise((r) => setTimeout(r, 600));
    }
    return false;
  }

  function setRestartUi(state, message) {
    const btn = $("restartServerBtn");
    const progress = $("restartServerProgress");
    const status = $("restartServerStatus");
    if (btn) {
      btn.disabled = state === "busy";
      btn.classList.toggle("is-busy", state === "busy");
      btn.classList.toggle("is-ok", state === "ok");
      btn.classList.toggle("is-err", state === "err");
    }
    if (progress) {
      progress.classList.toggle("hidden", state !== "busy");
      progress.setAttribute("aria-hidden", state === "busy" ? "false" : "true");
    }
    if (status) {
      status.textContent = message || "";
      status.classList.toggle("hidden", !message);
    }
  }

  async function restartJarvisServer() {
    const name = typeof window.ariaName === "function" ? window.ariaName() : "ARIA";
    const msg = `Restart ${name} server now?\n\nChat will reconnect in a few seconds.`;
    if (window.ariaConfirm) {
      if (!(await window.ariaConfirm(msg, { title: "Restart Aria", okLabel: "Restart" }))) return;
    } else if (!confirm(msg)) {
      return;
    }
    setRestartUi("busy", "Restarting server…");
    const st = $("statusText");
    if (st) st.textContent = "Restarting server…";
    try {
      const res = await fetch("/api/jarvis/restart-server", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        const msg = data.message || "Restart failed.";
        setRestartUi("err", msg);
        window.showAriaToast?.(msg, "err", 5000);
        setTimeout(() => setRestartUi("idle", ""), 4000);
        return;
      }
      setRestartUi("busy", "Waiting for server…");
      const back = await waitForServerBack();
      if (back) {
        setRestartUi("ok", "Back online");
        if (st) st.textContent = "Back online — reloading…";
        if (window.mediaWorkActive?.()) {
          if (st) st.textContent = "Server back — image job still running (no reload)";
          setRestartUi("ok", "Online (job still running)");
          setTimeout(() => setRestartUi("idle", ""), 5000);
        } else {
          location.reload();
        }
      } else {
        setRestartUi("err", "Restart slow — try Ctrl+Shift+R");
        window.showAriaToast?.(`${name} may still be restarting — try Ctrl+Shift+R`, "warn", 8000);
      }
    } catch {
      const back = await waitForServerBack();
      if (back && !window.mediaWorkActive?.()) location.reload();
      else {
        setRestartUi(back ? "ok" : "err", back ? "Online" : "Restart slow — hard refresh");
        setTimeout(() => setRestartUi("idle", ""), 5000);
      }
    }
  }

  function initServerRestart() {
    $("restartServerBtn")?.addEventListener("click", restartJarvisServer);
    $("upgradeRestartBtn")?.addEventListener("click", restartJarvisServer);
  }

  function initMobile() {
    $("mobileMenuBtn")?.addEventListener("click", () => {
      document.body.classList.toggle("mobile-sidebar-open");
    });
    document.querySelector(".sidebar-backdrop")?.addEventListener("click", () => {
      document.body.classList.remove("mobile-sidebar-open");
    });
  }

  function initButtons() {
    $("resetLayoutBtn")?.addEventListener("click", () => {
      resetSidebarLayout();
      if (window.statusText) window.statusText.textContent = "Sidebar expanded — all sections visible";
      else if ($("statusText")) $("statusText").textContent = "Sidebar expanded — all sections visible";
    });
    $("collapseSidebarBtn")?.addEventListener("click", () => {
      collapseAllSidebar();
      window.showAriaToast?.("Sidebar collapsed", "ok", 2000);
    });
  }

  function initViewJumps() {
    document.querySelectorAll("[data-view-jump]").forEach((btn) => {
      if (btn.dataset.jumpBound === "1") return;
      btn.dataset.jumpBound = "1";
      btn.addEventListener("click", () => {
        const view = btn.getAttribute("data-view-jump");
        if (view) window.switchToView?.(view);
      });
    });
  }

  function init() {
    initCollapsibleSections();
    initSidebarResize();
    initServerRestart();
    initMobile();
    initButtons();
    initViewJumps();
  }

  window.resetSidebarLayout = resetSidebarLayout;
  window.collapseAllSidebar = collapseAllSidebar;
  window.restartJarvisServer = restartJarvisServer;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
