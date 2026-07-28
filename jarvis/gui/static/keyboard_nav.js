/** Keyboard-first navigation — numbered views, history back/forward, palette aliases. */
(function () {
  "use strict";

  const VIEW_ORDER = [
    "chat", "dashboard", "workstation", "planner", "calendar",
    "memory", "documents", "connections", "gallery", "projects", "maker", "journal",
  ];

  let viewStack = [];
  let stackIdx = -1;
  let navigating = false;

  function currentView() {
    return document.querySelector(".view-tab.active")?.dataset?.view || "chat";
  }

  function pushStack(view) {
    if (navigating || !view) return;
    if (viewStack[stackIdx] === view) return;
    viewStack = viewStack.slice(0, stackIdx + 1);
    viewStack.push(view);
    if (viewStack.length > 40) viewStack.shift();
    stackIdx = viewStack.length - 1;
  }

  function goBack() {
    if (stackIdx <= 0) return;
    navigating = true;
    stackIdx -= 1;
    window.switchToView?.(viewStack[stackIdx]);
    navigating = false;
  }

  function goForward() {
    if (stackIdx >= viewStack.length - 1) return;
    navigating = true;
    stackIdx += 1;
    window.switchToView?.(viewStack[stackIdx]);
    navigating = false;
  }

  function isTypingTarget(el) {
    if (!el) return false;
    const tag = el.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
    return !!el.isContentEditable;
  }

  function init() {
    pushStack(currentView());
    window.addEventListener("aria-view-change", (e) => pushStack(e.detail?.view));

    document.addEventListener("keydown", (e) => {
      const mod = e.ctrlKey || e.metaKey;
      const typing = isTypingTarget(document.activeElement);

      // Alt+Left / Alt+Right — view history
      if (e.altKey && !mod && e.key === "ArrowLeft") {
        e.preventDefault();
        goBack();
        return;
      }
      if (e.altKey && !mod && e.key === "ArrowRight") {
        e.preventDefault();
        goForward();
        return;
      }

      // Ctrl+Tab / Shift+Ctrl+Tab — cycle primary views
      if (mod && e.key === "Tab") {
        e.preventDefault();
        const cur = currentView();
        const idx = VIEW_ORDER.indexOf(cur);
        const next = e.shiftKey
          ? VIEW_ORDER[(idx - 1 + VIEW_ORDER.length) % VIEW_ORDER.length]
          : VIEW_ORDER[(idx + 1) % VIEW_ORDER.length];
        window.switchToView?.(next);
        return;
      }

      if (typing) return;

      // Ctrl+1..9 — jump favorites / ordered views
      if (mod && !e.shiftKey && e.key >= "1" && e.key <= "9") {
        e.preventDefault();
        const n = Number(e.key) - 1;
        const favs = window.AriaFavorites?.getFavorites?.() || [];
        const target = favs[n] || VIEW_ORDER[n];
        if (target) window.switchToView?.(target);
        return;
      }

      // Ctrl+, settings
      if (mod && e.key === ",") {
        e.preventDefault();
        document.getElementById("settingsBtn")?.click();
        return;
      }

      // Ctrl+/ shortcuts
      if (mod && e.key === "/") {
        e.preventDefault();
        document.getElementById("shortcutsBtn")?.click();
        return;
      }

      // Ctrl+Shift+P — workspaces (VS Code muscle memory)
      if (mod && e.shiftKey && e.key.toLowerCase() === "p") {
        e.preventDefault();
        window.AriaWorkspaces?.openModal?.();
        return;
      }

      // Ctrl+Shift+A — activity center
      if (mod && e.shiftKey && e.key.toLowerCase() === "a") {
        e.preventDefault();
        window.AriaActivity?.open?.();
        return;
      }

      // Ctrl+Shift+O — Automation Home (orchestration)
      if (mod && e.shiftKey && e.key.toLowerCase() === "o") {
        e.preventDefault();
        window.switchToView?.("automation");
        return;
      }

      // Ctrl+Shift+V — View Paths
      if (mod && e.shiftKey && e.key.toLowerCase() === "v") {
        e.preventDefault();
        window.AriaViewPaths?.openModal?.() || window.AriaWorkflows?.openModal?.();
        return;
      }

      // Ctrl+Shift+M — Mission Control
      if (mod && e.shiftKey && e.key.toLowerCase() === "m") {
        e.preventDefault();
        window.AriaActions?.goMc?.("overview") || window.switchToView?.("workstation");
        return;
      }

      // Ctrl+Shift+K — mini chat
      if (mod && e.shiftKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        window.AriaMiniChat?.toggle?.();
        return;
      }

      // Ctrl+\\ — split view
      if (mod && (e.key === "\\" || e.code === "Backslash")) {
        e.preventDefault();
        window.AriaSplitView?.toggle?.();
      }
    });
  }

  window.AriaKeyboard = { goBack, goForward, VIEW_ORDER };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
