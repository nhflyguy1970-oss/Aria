/** Quick Access Dock — one-click favorite workspaces beneath the header. Hideable, favorites-integrated. */
(function () {
  "use strict";

  function prefs() {
    return window.AriaUiPrefs?.load?.() || {};
  }

  function dockHidden() {
    return prefs().dockHidden === true;
  }

  function render() {
    const dock = document.getElementById("quickDock");
    if (!dock) return;
    const labels = window.AriaFavorites?.VIEW_LABELS || {};
    const favs = window.AriaFavorites?.getFavorites?.() || [];
    const current = document.querySelector(".view-tab.active")?.dataset?.view;

    dock.classList.toggle("hidden", dockHidden() || !favs.length);
    if (dockHidden() || !favs.length) return;

    dock.replaceChildren();
    favs.forEach((view) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `quick-dock-btn${view === current ? " active" : ""}`;
      btn.textContent = labels[view] || view;
      btn.title = `Open ${labels[view] || view}`;
      btn.dataset.view = view;
      btn.addEventListener("click", () => window.switchToView?.(view));
      btn.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        window.AriaContextMenu?.open(e, [
          { label: "Unpin from Favorites", run: () => window.AriaFavorites?.toggleFavorite?.(view) },
          { label: "Copy deep link", run: () => copyDeepLink(view) },
          { label: "Hide dock", run: () => setHidden(true) },
        ]);
      });
      dock.appendChild(btn);
    });

    const hideBtn = document.createElement("button");
    hideBtn.type = "button";
    hideBtn.className = "quick-dock-hide ghost-btn tiny";
    hideBtn.title = "Hide Quick Access Dock (re-enable in Settings)";
    hideBtn.setAttribute("aria-label", "Hide Quick Access Dock");
    hideBtn.textContent = "×";
    hideBtn.addEventListener("click", () => setHidden(true));
    dock.appendChild(hideBtn);
  }

  function copyDeepLink(view) {
    const url = `${location.origin}${location.pathname}#${view}`;
    navigator.clipboard?.writeText(url).then(
      () => window.showAriaToast?.("Deep link copied", "ok", 2000),
      () => window.showAriaToast?.("Could not copy link", "err", 3000),
    );
  }

  function setHidden(hidden) {
    window.AriaUiPrefs?.set?.("dockHidden", hidden);
    render();
    if (hidden) window.showAriaToast?.("Dock hidden — Settings → “Show dock” to restore", "info", 3500);
  }

  function init() {
    render();
    window.addEventListener("aria-ui-prefs", render);
    window.addEventListener("aria-view-change", render);
    document.getElementById("toggleDockBtn")?.addEventListener("click", () => {
      setHidden(!dockHidden());
      const btn = document.getElementById("toggleDockBtn");
      if (btn) btn.textContent = dockHidden() ? "Show dock" : "Hide dock";
    });
    const btn = document.getElementById("toggleDockBtn");
    if (btn) btn.textContent = dockHidden() ? "Show dock" : "Hide dock";
  }

  window.AriaQuickDock = { render, setHidden };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
