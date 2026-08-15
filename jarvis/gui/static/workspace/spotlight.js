/**
 * Legacy Activity Spotlight — superseded by Front Door in Living Workspace.
 * Kept as a thin compatibility shim.
 */
(function () {
  "use strict";

  function open(q) {
    if (window.AriaFrontDoor?.open) {
      window.AriaFrontDoor.open(typeof q === "string" ? q : undefined);
      return;
    }
    /* Pre-workspace fallback: minimal */
    const root = document.getElementById("wsSpotlight");
    if (root) {
      root.classList.remove("hidden");
      document.getElementById("wsSpotlightInput")?.focus();
    }
  }

  function close() {
    window.AriaFrontDoor?.close?.();
    document.getElementById("wsSpotlight")?.classList.add("hidden");
  }

  function isOpen() {
    return !!window.AriaFrontDoor?.isOpen?.();
  }

  window.AriaWorkspaceSpotlight = { open, close, isOpen, render: () => {} };

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("wsSpotlightBtn")?.addEventListener("click", () => open());
    document.getElementById("wsSpotlightClose")?.addEventListener("click", close);
  });
})();
