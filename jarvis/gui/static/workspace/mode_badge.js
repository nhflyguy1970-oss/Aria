/** Always-visible Regular / Uncensored mode badge (top-right); click to switch.
 *  Turning uncensored on still goes through the master-password modal in uncensored_mode.js. */
(function () {
  "use strict";

  function isOn() {
    return document.body.classList.contains("uncensored-mode");
  }

  function render(btn) {
    const on = isOn();
    btn.classList.toggle("aria-mode-badge--uncensored", on);
    btn.innerHTML = `<span class="aria-mode-dot" aria-hidden="true"></span>${on ? "Uncensored" : "Regular"}`;
    btn.title = on ? "Uncensored mode — click to return to Regular mode"
                   : "Regular mode — click to switch to Uncensored (asks for your password)";
    btn.setAttribute("aria-label", on ? "Mode: Uncensored. Switch to Regular" : "Mode: Regular. Switch to Uncensored");
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  }

  function mount() {
    if (document.getElementById("ariaModeBadge")) return;
    const btn = document.createElement("button");
    btn.id = "ariaModeBadge";
    btn.type = "button";
    btn.className = "aria-mode-badge";
    document.body.appendChild(btn);
    render(btn);
    btn.addEventListener("click", () => {
      if (typeof window.toggleAriaUncensored === "function") window.toggleAriaUncensored();
      else window.AriaActions?.system?.uncensored?.();
    });
    // Follows every way the mode changes (badge, Ctrl+K, Settings, restore on load).
    new MutationObserver(() => render(btn)).observe(document.body, { attributes: true, attributeFilter: ["class"] });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
