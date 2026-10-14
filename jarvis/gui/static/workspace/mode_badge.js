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

  const MEDIA_RE = /\/api\/(gallery|video-gallery|video\/gallery)\//;

  function withView(url, on) {
    try {
      const u = new URL(url, window.location.href);
      u.searchParams.set("view", on ? "u" : "r");
      return u.pathname + u.search + u.hash;
    } catch (_) {
      return url;
    }
  }

  /** Re-request every gallery image/video on screen (chat, Gallery, lightbox) so images made in
   *  uncensored mode turn into the "Restricted" placeholder the moment Regular mode is chosen. */
  function refreshMedia(on) {
    document.querySelectorAll("img[src], video[src], source[src]").forEach((el) => {
      const src = el.getAttribute("src") || "";
      if (!MEDIA_RE.test(src)) return;
      el.setAttribute("src", withView(src, on));
      if (el.tagName === "SOURCE") el.parentElement?.load?.();
      else if (el.tagName === "VIDEO") el.load?.();
    });
    document.querySelectorAll("[data-full-src]").forEach((el) => {
      const src = el.getAttribute("data-full-src") || "";
      if (MEDIA_RE.test(src)) el.setAttribute("data-full-src", withView(src, on));
    });
    window.dispatchEvent(new CustomEvent("aria:mode-changed", { detail: { uncensored: on } }));
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
    let last = isOn();
    new MutationObserver(() => {
      render(btn);
      const on = isOn();
      if (on !== last) {
        last = on;
        refreshMedia(on);
      }
    }).observe(document.body, { attributes: true, attributeFilter: ["class"] });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
