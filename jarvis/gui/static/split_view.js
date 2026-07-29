/** Split view — two panes side-by-side with drag-resizable divider. */
(function () {
  "use strict";

  let enabled = false;
  let primary = "chat";
  let secondary = "planner";
  let ratio = 0.55;

  function $(id) {
    return document.getElementById(id);
  }

  function panelId(view) {
    return `${view}View`;
  }

  function getState() {
    return { enabled, primary, secondary, ratio };
  }

  function label(v) {
    return window.AriaFavorites?.VIEW_LABELS?.[v] || v;
  }

  function updateChrome() {
    const btn = $("splitViewToggleBtn");
    if (btn) {
      btn.classList.toggle("active", enabled);
      btn.setAttribute("aria-pressed", enabled ? "true" : "false");
      btn.title = enabled ? "Exit split view" : "Split view with another panel";
    }
    const bar = $("splitViewBar");
    if (bar) bar.classList.toggle("hidden", !enabled);
    const lbl = $("splitViewLabel");
    if (lbl && enabled) lbl.textContent = `${label(primary)} · ${label(secondary)}`;
  }

  function restorePanelsToMain() {
    const main = $("mainContent");
    if (!main) return;
    const chat = $("chatView");
    ["splitPaneLeft", "splitPaneRight"].forEach((pid) => {
      const pane = $(pid);
      if (!pane) return;
      [...pane.querySelectorAll(".view-panel")].forEach((p) => {
        if (chat?.parentElement === main) main.insertBefore(p, chat);
        else main.appendChild(p);
        p.classList.add("hidden");
      });
    });
  }

  function applyLayout() {
    const host = $("splitViewHost");
    const left = $("splitPaneLeft");
    const right = $("splitPaneRight");
    const main = $("mainContent");
    if (!host || !left || !right || !main) return;

    if (!enabled) {
      host.classList.add("hidden");
      main.classList.remove("split-active");
      return;
    }

    host.classList.remove("hidden");
    main.classList.add("split-active");
    left.style.flex = `${ratio} 1 0`;
    right.style.flex = `${1 - ratio} 1 0`;

    // Return any stray panels to main before placing the pair
    const chat = $("chatView");
    [...left.querySelectorAll(".view-panel"), ...right.querySelectorAll(".view-panel")].forEach((p) => {
      if (p.id === panelId(primary) || p.id === panelId(secondary)) return;
      if (chat?.parentElement === main) main.insertBefore(p, chat);
      else main.appendChild(p);
      p.classList.add("hidden");
    });

    const leftPanel = $(panelId(primary));
    const rightPanel = $(panelId(secondary));
    if (leftPanel && leftPanel.parentElement !== left) left.appendChild(leftPanel);
    if (rightPanel && rightPanel.parentElement !== right) right.appendChild(rightPanel);
    leftPanel?.classList.remove("hidden");
    rightPanel?.classList.remove("hidden");
    // Ensure only the intended pair is visible inside panes
    [...left.querySelectorAll(".view-panel"), ...right.querySelectorAll(".view-panel")].forEach((p) => {
      if (p !== leftPanel && p !== rightPanel) {
        if (chat?.parentElement === main) main.insertBefore(p, chat);
        else main.appendChild(p);
        p.classList.add("hidden");
      }
    });
    document.querySelectorAll(".view-tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.view === primary || t.dataset.view === secondary);
    });
    updateChrome();
  }

  function enable(a, b) {
    primary = a || primary || "chat";
    secondary = b || secondary || "planner";
    if (primary === secondary) secondary = primary === "chat" ? "planner" : "chat";
    enabled = true;
    ratio = window.AriaUiPrefs?.get?.("splitRatio", 0.55) || 0.55;
    window.switchToView?.(primary);
    restorePanelsToMain();
    const rightPanel = $(panelId(secondary));
    rightPanel?.classList.remove("hidden");
    // init secondary if needed
    if (secondary === "planner") window.initPlanner?.();
    if (secondary === "memory") window.loadMemoryBrowser?.();
    if (secondary === "gallery") window.loadGallery?.();
    if (secondary === "calendar") window.initCalendar?.();
    if (secondary === "documents") {
      window.initDocumentsTab?.();
      window.loadDocumentsTab?.();
    }
    applyLayout();
    window.AriaUiPrefs?.set?.("splitEnabled", true);
    window.AriaUiPrefs?.set?.("splitPair", [primary, secondary]);
    window.showAriaToast?.(`Split: ${label(primary)} + ${label(secondary)}`, "ok", 2500);
  }

  function disable() {
    if (!enabled) return;
    enabled = false;
    restorePanelsToMain();
    $("splitViewHost")?.classList.add("hidden");
    $("mainContent")?.classList.remove("split-active");
    window.AriaUiPrefs?.set?.("splitEnabled", false);
    window.switchToView?.(primary);
    updateChrome();
  }

  function swap() {
    if (!enabled) return;
    const t = primary;
    primary = secondary;
    secondary = t;
    applyLayout();
    window.AriaUiPrefs?.set?.("splitPair", [primary, secondary]);
  }

  function openPicker() {
    const modal = $("splitPickerModal");
    const list = $("splitPickerList");
    if (!modal || !list) return;
    const labels = window.AriaFavorites?.VIEW_LABELS || {};
    const current = document.querySelector(".view-tab.active")?.dataset?.view || "chat";
    list.replaceChildren();
    Object.entries(labels).forEach(([view, name]) => {
      if (view === current) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn small";
      btn.textContent = name;
      btn.addEventListener("click", () => {
        modal.classList.add("hidden");
        enable(current, view);
      });
      list.appendChild(btn);
    });
    modal.classList.remove("hidden");
  }

  function toggle() {
    if (enabled) disable();
    else openPicker();
  }

  function initResize() {
    const handle = $("splitResizeHandle");
    if (!handle) return;
    let dragging = false;
    handle.addEventListener("pointerdown", (e) => {
      dragging = true;
      handle.setPointerCapture?.(e.pointerId);
      document.body.classList.add("resizing-split");
    });
    window.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const host = $("splitViewHost");
      if (!host) return;
      const rect = host.getBoundingClientRect();
      ratio = Math.min(0.75, Math.max(0.25, (e.clientX - rect.left) / rect.width));
      applyLayout();
    });
    window.addEventListener("pointerup", () => {
      if (!dragging) return;
      dragging = false;
      document.body.classList.remove("resizing-split");
      window.AriaUiPrefs?.set?.("splitRatio", ratio);
    });
  }

  function init() {
    initResize();
    $("splitViewToggleBtn")?.addEventListener("click", toggle);
    $("splitViewSwapBtn")?.addEventListener("click", swap);
    $("splitViewCloseBtn")?.addEventListener("click", disable);
    $("splitPickerCloseBtn")?.addEventListener("click", () => $("splitPickerModal")?.classList.add("hidden"));
    window.addEventListener("aria-view-change", (e) => {
      if (!enabled) return;
      const v = e.detail?.view;
      if (!v || v === secondary || v === primary) return;
      primary = v;
      applyLayout();
    });
    updateChrome();
  }

  window.AriaSplitView = { enable, disable, toggle, swap, getState, openPicker };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
