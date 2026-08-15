/**
 * Contextual Tools host — sheets / HUD entry; never permanent capability walls.
 */
(function () {
  "use strict";

  function open(toolId) {
    const tool = window.AriaWorkspaceRegistry?.tool?.(toolId);
    if (!tool) {
      window.showAriaToast?.(`Unknown tool: ${toolId}`, "warn");
      return;
    }

    const inLivingRoom = !!window.AriaLivingRoom?.isActive?.();

    // Voice stays in the Living Room — never eject into a Voice page
    if (tool.invoke === "voice" || toolId === "voice") {
      if (inLivingRoom) {
        window.AriaLivingRoom?.setStatus?.("Speak when ready");
        document.getElementById("micBtnComposer")?.focus?.();
        // Briefly surface Voice as a contextual chip, then fade
        const tray = document.getElementById("wsToolTray");
        if (tray) {
          tray.classList.remove("hidden");
          tray.innerHTML =
            '<button type="button" class="ws-tool-chip" data-tool="voice">Voice</button>';
          clearTimeout(open._voiceHide);
          open._voiceHide = setTimeout(() => {
            if (window.AriaLivingRoom?.isActive?.()) {
              tray.innerHTML = "";
              tray.classList.add("hidden");
              window.AriaLivingRoom?.setStatus?.("Listening quietly");
            }
          }, 8000);
        }
        return;
      }
      try {
        window.switchToView?.("voice");
      } catch (_) {
        /* ignore */
      }
      return;
    }

    // Prefer existing panels as temporary adapters (no room redesign).
    // goRoom / switchToView keep hash + AriaHouse synchronized —
    // AriaHouse.enter alone left Jeff on a new Room under a stale hash.
    if (tool.viewId) {
      const roomId =
        tool.viewId === "workstation"
          ? "mission"
          : tool.viewId === "repair"
            ? "repair"
            : tool.viewId === "models"
              ? "providers"
              : tool.viewId === "dashboard"
                ? "home"
                : tool.viewId === "homeAutomation" || tool.viewId === "presence"
                  ? tool.viewId === "presence"
                    ? "presence"
                    : "home_automation"
                  : tool.viewId;
      try {
        if (typeof window.AriaFrontDoorCatalog?.goRoom === "function") {
          window.AriaFrontDoorCatalog.goRoom(roomId);
        } else {
          window.switchToView?.(tool.viewId);
        }
      } catch (_) {
        try {
          window.switchToView?.(tool.viewId);
        } catch (__) {
          /* ignore */
        }
      }
      if (!inLivingRoom) window.showAriaToast?.(`Tool · ${tool.label}`, "info", 1600);
      return;
    }

    if (tool.invoke === "notifications") {
      window.AriaActivity?.open?.() || window.AriaNotificationsInbox?.open?.();
      return;
    }
    if (tool.invoke === "jobs") {
      window.jarvisJobs?.openJobCenter?.() ||
        window.AriaActions?.mission?.jobs?.() ||
        document.getElementById("jobCenterBtn")?.click();
      return;
    }
    if (tool.invoke === "clipboard") {
      navigator.clipboard?.readText?.().then(
        (t) => window.showAriaToast?.(t ? `Clipboard · ${t.slice(0, 80)}` : "Clipboard empty", "info"),
        () => window.showAriaToast?.("Clipboard unavailable", "warn")
      );
      return;
    }
    if (tool.invoke === "docker" || toolId === "docker") {
      try {
        window.switchToView?.("workstation");
        window.showAriaToast?.("Tool · Docker — open Mission for containers", "info", 2200);
      } catch (_) {
        window.showAriaToast?.("Docker — open Mission Control", "info", 2200);
      }
      return;
    }

    window.showAriaToast?.(`${tool.label} — available as a Tool (sheet pending)`, "info");
  }

  function bind() {
    document.getElementById("wsToolTray")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-tool]");
      if (!btn) return;
      open(btn.getAttribute("data-tool"));
    });
  }

  window.AriaWorkspaceTools = { open };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();
})();
