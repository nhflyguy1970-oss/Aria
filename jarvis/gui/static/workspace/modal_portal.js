/**
 * Phase 6.5 — Portal legacy dialogs out of #ariaLegacyShell[inert].
 * Living Workspace demolishes the shell; modals must live under document.body
 * or they open invisibly / non-interactively under inert.
 */
(function () {
  "use strict";

  const MODAL_IDS = [
    "memoryDialog",
    "memoryShortcutOverlay",
    "commandPaletteModal",
    "imageLightbox",
    "videoLightbox",
    "inpaintModal",
    "toolConfirmModal",
    "upgradeWizardModal",
    "jobCenterModal",
    "haSetupModal",
    "haTokenModal",
    "apiKeyModal",
    "profileModal",
    "branchTrimModal",
    "uncensoredAuthModal",
    "projectPickerModal",
    "settingsModal",
    "shortcutsModal",
    "cropModal",
    "flytyingScanModal",
    "flytyingNameBarcodeModal",
    "whatsNewModal",
    "dashCustomizeModal",
    "activityCenterModal",
    "workspaceLayoutsModal",
    "workflowModal",
    "autoRuleModal",
    "autoWebhookModal",
    "splitPickerModal",
    "guidedRepairModal",
    "guidedRepairOverlay",
  ];

  /** @type {Map<string, { parent: Node, next: ChildNode | null }>} */
  const homes = new Map();
  let portaled = false;

  function isLivingWorkspace() {
    return (
      document.documentElement.classList.contains("living-workspace") ||
      document.body?.classList.contains("living-workspace") ||
      document.body?.dataset.workspace === "1"
    );
  }

  function ensure() {
    if (!isLivingWorkspace()) return false;
    if (portaled) return true;
    const shell = document.getElementById("ariaLegacyShell") || document.querySelector(".app");
    MODAL_IDS.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (!shell || !shell.contains(el)) return;
      if (!homes.has(id)) {
        homes.set(id, { parent: el.parentNode, next: el.nextSibling });
      }
      el.dataset.ariaModalPortal = "1";
      document.body.appendChild(el);
    });
    portaled = true;
    return true;
  }

  function restore() {
    if (!portaled) return;
    homes.forEach((home, id) => {
      const el = document.getElementById(id);
      if (!el || !home?.parent) return;
      try {
        if (home.next && home.next.parentNode === home.parent) {
          home.parent.insertBefore(el, home.next);
        } else {
          home.parent.appendChild(el);
        }
        delete el.dataset.ariaModalPortal;
      } catch (_) {
        /* ignore */
      }
    });
    homes.clear();
    portaled = false;
  }

  function open(id) {
    ensure();
    const el = document.getElementById(id);
    if (!el) return false;
    el.classList.remove("hidden");
    return true;
  }

  window.AriaModalPortal = { ensure, restore, open, MODAL_IDS };

  window.addEventListener("aria-workspace-ready", () => ensure());
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      if (isLivingWorkspace()) ensure();
    });
  } else if (isLivingWorkspace()) {
    ensure();
  }
})();
