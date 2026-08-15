/**
 * Aria Living Workspace orchestrator (Phase 2).
 * Environment for Activities — not a dashboard, not a page.
 */
(function () {
  "use strict";

  const ENABLED_KEY = "aria_workspace_v1";

  function prefsEnabled() {
    // Explicit escape hatch: legacy shell on demand
    const q = new URLSearchParams(location.search);
    if (q.get("workspace") === "0") return false;

    // Query / Electron / PWA markers always enable Living Workspace
    if (q.get("workspace") === "1" || q.get("shell") === "electron") return true;
    if (document.documentElement.classList.contains("jarvis-app")) return true;
    if (q.get("app") === "1") return true;

    // BUG-001: honor livingWorkspace pref on bare `/` (default true).
    // Legacy remains available via ?workspace=0 or livingWorkspace:false.
    try {
      const p = window.AriaUiPrefs?.load?.() || {};
      if (p.livingWorkspace === false) return false;
      return p.livingWorkspace !== false;
    } catch (_) {
      return true;
    }
  }

  function enable() {
    const body = document.body;
    if (!body) return;
    body.dataset.workspace = "1";
    body.classList.add("living-workspace");
    document.documentElement.classList.add("living-workspace");
    document.documentElement.dataset.workspace = "1";
    document.documentElement.dataset.runtime = "e1";
    /* House Integrity: legacy shell is inventory only — never painted */
    const legacy = document.getElementById("ariaLegacyShell") || document.querySelector(".app");
    if (legacy) {
      legacy.setAttribute("inert", "");
      legacy.setAttribute("aria-hidden", "true");
    }
    /* Phase 6.5: dialogs must escape inert shell before House Controls open them */
    window.AriaModalPortal?.ensure?.();
    window.AriaWorkspaceChrome?.apply?.("focus");
    /* wsBar lives inside demolished .app — leave hidden; Spotlight (outside) remains */
    document.getElementById("wsBar")?.classList.add("hidden");
    const hash = (location.hash || "").replace(/^#/, "").split(/[&?]/)[0];
    const view = window.AriaViewRouter?.canonicalView?.(hash) || hash;
    if (!view || view === "chat") {
      window.AriaActivityEngine?.start?.("converse", { confirmHighStakes: false });
      queueMicrotask(() => window.AriaHouse?.enter?.("chat"));
    } else {
      const roomId = window.AriaViewRouter?.viewToRoom?.(view) || view;
      if (window.AriaFrontDoorCatalog?.goRoom) {
        window.AriaFrontDoorCatalog.goRoom(roomId);
      } else if (window.AriaWorkspaceRegistry?.activity?.(roomId)) {
        window.AriaActivityEngine?.start?.(roomId, { confirmHighStakes: false });
      } else {
        window.switchToView?.(view);
      }
    }
    window.dispatchEvent(new CustomEvent("aria-workspace-ready", { detail: { runtime: "e1" } }));
  }

  function disable() {
    document.body?.classList.remove("living-workspace");
    document.documentElement.classList.remove("living-workspace");
    delete document.body?.dataset.workspace;
    delete document.documentElement?.dataset.workspace;
    window.AriaStage?.clear?.();
    const legacy = document.getElementById("ariaLegacyShell") || document.querySelector(".app");
    window.AriaModalPortal?.restore?.();
    if (legacy) {
      legacy.removeAttribute("inert");
      legacy.removeAttribute("aria-hidden");
    }
    window.AriaWorkspaceChrome?.clear?.();
    document.getElementById("wsBar")?.classList.add("hidden");
  }

  function boot() {
    if (!prefsEnabled()) {
      document.getElementById("wsBar")?.classList.add("hidden");
      return;
    }
    enable();
  }

  window.AriaWorkspace = {
    enable,
    disable,
    boot,
    isEnabled: () => document.body?.dataset.workspace === "1",
    runtime: "e1",
    version: "2.1.0-integrity",
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
