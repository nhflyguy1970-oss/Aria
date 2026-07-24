/** Shared Esc / focus-trap chrome for Aria overlays (extracted from god-app.js). */
(function () {
  function initAriaModalChrome() {
    /** Closable overlays (Esc). Lock screen is excluded — must unlock deliberately. */
    const MODAL_IDS = [
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
    ];

    function isOpen(el) {
      return !!(el && !el.classList.contains("hidden"));
    }

    function topOpenModal() {
      for (const id of MODAL_IDS) {
        const el = document.getElementById(id);
        if (isOpen(el)) return el;
      }
      return null;
    }

    function focusables(root) {
      return [...(root?.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ) || [])].filter((el) => el.offsetParent !== null || el === document.activeElement);
    }

    function closeModal(el) {
      if (!el) return;
      if (el.id === "imageLightbox") {
        window.closeImageLightbox?.();
        return;
      }
      if (el.id === "videoLightbox") {
        window.closeVideoLightbox?.();
        return;
      }
      if (el.id === "toolConfirmModal") {
        document.getElementById("toolConfirmNo")?.click();
        return;
      }
      if (el.id === "commandPaletteModal") {
        window.closeAriaCommandPalette?.();
        return;
      }
      el.classList.add("hidden");
    }

    document.addEventListener("keydown", (e) => {
      const modal = topOpenModal();
      if (!modal) return;

      if (e.key === "Escape") {
        e.preventDefault();
        closeModal(modal);
        return;
      }

      if (e.key !== "Tab") return;
      const nodes = focusables(modal);
      if (!nodes.length) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      } else if (!modal.contains(document.activeElement)) {
        e.preventDefault();
        first.focus();
      }
    });
  }

  window.initAriaModalChrome = initAriaModalChrome;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initAriaModalChrome());
  } else {
    initAriaModalChrome();
  }
})();
