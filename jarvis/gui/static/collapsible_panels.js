/** Generic collapsible sections for large views — click h3 headers; state remembered. */
(function () {
  "use strict";

  // Containers whose direct `section` children (with an h3) become collapsible.
  const TARGETS = [
    { root: "#dashboardView", selector: ".checklist-section", keyPrefix: "dash" },
    { root: "#plannerView", selector: ".planner-grid > section", keyPrefix: "planner" },
  ];

  function stateMap() {
    return window.AriaUiPrefs?.get?.("panelCollapsed", {}) || {};
  }

  function saveState(map) {
    window.AriaUiPrefs?.set?.("panelCollapsed", map);
  }

  function keyFor(prefix, section, idx) {
    const h = section.querySelector("h3")?.textContent?.trim().toLowerCase().replace(/\W+/g, "-") || `s${idx}`;
    return `${prefix}:${h}`;
  }

  function enhance() {
    const map = stateMap();
    TARGETS.forEach(({ root, selector, keyPrefix }) => {
      const rootEl = document.querySelector(root);
      if (!rootEl) return;
      rootEl.querySelectorAll(selector).forEach((section, idx) => {
        const head = section.querySelector("h3");
        if (!head || head.dataset.collapsibleBound === "1") return;
        head.dataset.collapsibleBound = "1";
        const key = keyFor(keyPrefix, section, idx);
        head.classList.add("panel-collapse-head");
        head.setAttribute("role", "button");
        head.setAttribute("tabindex", "0");
        const chevron = document.createElement("span");
        chevron.className = "panel-collapse-chevron";
        chevron.setAttribute("aria-hidden", "true");
        chevron.textContent = "▾";
        head.appendChild(chevron);

        const setCollapsed = (collapsed, persist) => {
          section.classList.toggle("panel-collapsed", collapsed);
          head.setAttribute("aria-expanded", collapsed ? "false" : "true");
          if (persist) {
            const m = stateMap();
            m[key] = collapsed;
            saveState(m);
          }
        };
        setCollapsed(!!map[key], false);
        const toggle = () => setCollapsed(!section.classList.contains("panel-collapsed"), true);
        head.addEventListener("click", toggle);
        head.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggle();
          }
        });
      });
    });
  }

  function init() {
    enhance();
    // Views render lazily — re-enhance on view switches.
    window.addEventListener("aria-view-change", () => setTimeout(enhance, 250));
  }

  /** Expand a collapsible section by heading text (e.g. "Tasks") so new items are visible. */
  function expand(rootSelector, headingMatch) {
    const rootEl = document.querySelector(rootSelector);
    if (!rootEl) return false;
    const needle = String(headingMatch || "").trim().toLowerCase();
    if (!needle) return false;
    let prefix = "panel";
    if (rootSelector.includes("planner")) prefix = "planner";
    else if (rootSelector.includes("dashboard")) prefix = "dash";
    for (const section of rootEl.querySelectorAll("section")) {
      const head = section.querySelector("h3");
      if (!head) continue;
      const label = (head.textContent || "").replace(/[▾▲▼▸◀▶]/g, "").trim().toLowerCase();
      if (label !== needle && !label.startsWith(needle)) continue;
      section.classList.remove("panel-collapsed");
      head.setAttribute("aria-expanded", "true");
      const m = stateMap();
      m[keyFor(prefix, section, 0)] = false;
      saveState(m);
      return true;
    }
    return false;
  }

  window.AriaCollapsiblePanels = { enhance, expand };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
