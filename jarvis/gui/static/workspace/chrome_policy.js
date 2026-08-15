/**
 * Workspace chrome policy — hide permanent capability furniture; keep Stage calm.
 * Does not redesign room interiors.
 */
(function () {
  "use strict";

  const POLICY = {
    focus: {
      hideViewTabs: true,
      hideVoiceEngineering: true,
      hideVisionStrip: true,
      hideWorldBar: false,
      hideSidebarHeavy: true,
      compactStatus: true,
    },
    minimal: {
      hideViewTabs: true,
      hideVoiceEngineering: true,
      hideVisionStrip: true,
      hideWorldBar: true,
      hideSidebarHeavy: true,
      compactStatus: true,
    },
    standard: {
      hideViewTabs: true,
      hideVoiceEngineering: true,
      hideVisionStrip: true,
      hideWorldBar: false,
      hideSidebarHeavy: false,
      compactStatus: true,
    },
    systems: {
      hideViewTabs: true,
      hideVoiceEngineering: true,
      hideVisionStrip: false,
      hideWorldBar: false,
      hideSidebarHeavy: false,
      compactStatus: false,
    },
  };

  function apply(policyName) {
    const p = POLICY[policyName] || POLICY.standard;
    const body = document.body;
    if (!body) return;
    body.dataset.wsChrome = policyName;
    body.classList.toggle("ws-hide-view-tabs", !!p.hideViewTabs);
    body.classList.toggle("ws-hide-voice-eng", !!p.hideVoiceEngineering);
    body.classList.toggle("ws-hide-vision-strip", !!p.hideVisionStrip);
    body.classList.toggle("ws-hide-world-bar", !!p.hideWorldBar);
    body.classList.toggle("ws-hide-sidebar-heavy", !!p.hideSidebarHeavy);
    body.classList.toggle("ws-compact-status", !!p.compactStatus);
    window.dispatchEvent(
      new CustomEvent("aria-workspace-chrome", { detail: { policy: policyName, ...p } })
    );
  }

  function clear() {
    const body = document.body;
    if (!body) return;
    delete body.dataset.wsChrome;
    body.classList.remove(
      "ws-hide-view-tabs",
      "ws-hide-voice-eng",
      "ws-hide-vision-strip",
      "ws-hide-world-bar",
      "ws-hide-sidebar-heavy",
      "ws-compact-status"
    );
  }

  window.AriaWorkspaceChrome = { apply, clear, policies: Object.keys(POLICY) };
})();
