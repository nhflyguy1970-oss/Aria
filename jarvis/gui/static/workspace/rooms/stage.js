/**
 * Aria Stage — exclusive Living Workspace mount point.
 * House Integrity + Phase 5 native Rooms.
 */
(function () {
  "use strict";

  const _homes = new Map();
  let _mountedId = null;

  function stageEl() {
    return document.getElementById("ariaStage");
  }

  function isWorkspace() {
    return (
      document.documentElement.classList.contains("living-workspace") ||
      document.body?.classList.contains("living-workspace")
    );
  }

  function isNativeRoom(ch) {
    return !!(ch && (ch.dataset?.nativeRoom === "1" || ch.classList?.contains("native-room")));
  }

  function isLegacyPanel(ch) {
    if (!ch || isNativeRoom(ch)) return false;
    return ch.classList?.contains("view-panel") || !!ch.id?.endsWith("View");
  }

  function holdEl() {
    let h = document.getElementById("ariaNativeHold");
    if (!h) {
      h = document.createElement("div");
      h.id = "ariaNativeHold";
      h.hidden = true;
      h.setAttribute("aria-hidden", "true");
      document.body.appendChild(h);
    }
    return h;
  }

  function rememberHome(panel) {
    if (!panel || !panel.id || _homes.has(panel.id) || isNativeRoom(panel)) return;
    _homes.set(panel.id, {
      parent: panel.parentElement,
      next: panel.nextSibling,
    });
  }

  function restore(panel) {
    if (!panel || !panel.id) return;
    if (isNativeRoom(panel)) {
      holdEl().appendChild(panel);
      panel.hidden = true;
      panel.setAttribute("aria-hidden", "true");
      panel.setAttribute("inert", "");
      panel.removeAttribute("data-aria-stage-mounted");
      return;
    }
    const home = _homes.get(panel.id);
    if (!home?.parent) {
      holdEl().appendChild(panel);
      panel.classList.add("hidden");
      panel.removeAttribute("data-aria-stage-mounted");
      return;
    }
    try {
      if (home.next && home.next.parentNode === home.parent) {
        home.parent.insertBefore(panel, home.next);
      } else {
        home.parent.appendChild(panel);
      }
    } catch (_) {
      home.parent.appendChild(panel);
    }
    panel.classList.add("hidden");
    panel.removeAttribute("data-aria-stage-mounted");
  }

  function clear() {
    const stage = stageEl();
    if (!stage) return;
    Array.from(stage.children).forEach((ch) => {
      if (isLegacyPanel(ch) || isNativeRoom(ch)) restore(ch);
      else ch.remove();
    });
    _mountedId = null;
    stage.setAttribute("data-room", "");
  }

  function mount(panel, roomId) {
    if (!isWorkspace()) return false;
    const stage = stageEl();
    if (!stage || !panel) return false;

    if (_mountedId && _mountedId !== panel.id) {
      const prev = document.getElementById(_mountedId);
      if (prev) restore(prev);
    } else if (_mountedId === panel.id && panel.parentElement === stage) {
      panel.classList.remove("hidden");
      stage.setAttribute("data-room", roomId || "");
      return true;
    }

    Array.from(stage.children).forEach((ch) => {
      if (ch !== panel && (isLegacyPanel(ch) || isNativeRoom(ch))) restore(ch);
    });

    rememberHome(panel);
    stage.appendChild(panel);
    panel.classList.remove("hidden");
    panel.hidden = false;
    panel.removeAttribute("aria-hidden");
    panel.removeAttribute("inert");
    panel.setAttribute("data-aria-stage-mounted", "1");
    panel.setAttribute("tabindex", "-1");
    _mountedId = panel.id;
    stage.setAttribute("data-room", roomId || "");

    const legacy = document.getElementById("ariaLegacyShell") || document.querySelector(".app");
    if (legacy) {
      legacy.setAttribute("inert", "");
      legacy.setAttribute("aria-hidden", "true");
    }
    return true;
  }

  function mounted() {
    return _mountedId ? document.getElementById(_mountedId) : null;
  }

  function mountedId() {
    return _mountedId;
  }

  function proof() {
    const stage = stageEl();
    const legacy = document.querySelector(".app");
    const legacyStyle = legacy ? getComputedStyle(legacy) : null;
    const node = _mountedId ? document.getElementById(_mountedId) : null;
    return {
      stageChildren: stage ? stage.children.length : 0,
      mountedId: _mountedId,
      nativeRoom: isNativeRoom(node),
      legacyDisplay: legacyStyle?.display || null,
      legacyVisibility: legacyStyle?.visibility || null,
      legacyInert: legacy?.hasAttribute("inert") || false,
      workspace: isWorkspace(),
      livingRoomVisibleUnderStage: false,
    };
  }

  window.AriaStage = {
    mount,
    clear,
    mounted,
    mountedId,
    proof,
    isWorkspace,
    version: "1.1.0-native",
  };
})();
