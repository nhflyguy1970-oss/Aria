/** Sidebar Favorites — pin views, drag-reorder, header pin. */
(function () {
  "use strict";

  const VIEW_LABELS = {
    chat: "Chat",
    search: "Search",
    settings: "Settings",
    dashboard: "Home",
    workstation: "Mission Control",
    planner: "Planner",
    calendar: "Calendar",
    flytying: "Fly Tying",
    projects: "Projects",
    maker: "Maker",
    browser: "Browser",
    security: "Security",
    presence: "Presence",
    audit: "System",
    capabilities: "Capabilities",
    integrations: "Integrations",
    voice: "Voice",
    vision: "Vision",
    audio: "Audio",
    journal: "Journal",
    memory: "Memory",
    gallery: "Gallery",
    video: "Video",
    meme: "Meme",
    documents: "Documents",
    connections: "Connections",
    actions: "Actions",
    coding: "Coding",
    models: "Models",
    automation: "Automation",
  };

  function prefs() {
    return window.AriaUiPrefs?.load?.() || { favorites: ["chat", "planner", "workstation"] };
  }

  function getFavorites() {
    const list = prefs().favorites;
    return Array.isArray(list) ? list.filter((v) => VIEW_LABELS[v]) : [];
  }

  function setFavorites(list) {
    window.AriaUiPrefs?.set?.("favorites", list.filter((v) => VIEW_LABELS[v]));
    render();
    syncPinButton();
  }

  function isFavorite(view) {
    return getFavorites().includes(view);
  }

  function toggleFavorite(view) {
    if (!VIEW_LABELS[view]) return;
    const cur = getFavorites();
    if (cur.includes(view)) setFavorites(cur.filter((v) => v !== view));
    else setFavorites([...cur, view]);
    window.showAriaToast?.(
      isFavorite(view) ? `Pinned ${VIEW_LABELS[view]}` : `Unpinned ${VIEW_LABELS[view]}`,
      "ok",
      2000,
    );
  }

  function currentView() {
    return document.querySelector(".view-tab.active")?.dataset?.view || "chat";
  }

  function syncPinButton() {
    const btn = document.getElementById("favoriteCurrentViewBtn");
    if (!btn) return;
    const view = currentView();
    const on = isFavorite(view);
    btn.classList.toggle("is-favorite", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    btn.title = on ? `Unpin ${VIEW_LABELS[view] || view}` : `Pin ${VIEW_LABELS[view] || view} to Favorites`;
    btn.setAttribute("aria-label", btn.title);
  }

  function render() {
    const list = document.getElementById("sidebarFavoritesList");
    if (!list) return;
    const favs = getFavorites();
    list.replaceChildren();
    if (!favs.length) {
      const empty = document.createElement("p");
      empty.className = "muted small sidebar-fav-empty";
      empty.textContent = "Pin views with the ★ button";
      list.appendChild(empty);
      return;
    }
    favs.forEach((view, index) => {
      const row = document.createElement("div");
      row.className = "sidebar-fav-row";
      row.draggable = true;
      row.dataset.view = view;
      row.dataset.index = String(index);

      const go = document.createElement("button");
      go.type = "button";
      go.className = "sidebar-fav-btn";
      go.textContent = VIEW_LABELS[view] || view;
      go.title = `Open ${VIEW_LABELS[view] || view}`;
      go.addEventListener("click", () => window.switchToView?.(view));

      const unpin = document.createElement("button");
      unpin.type = "button";
      unpin.className = "sidebar-fav-unpin ghost-btn tiny";
      unpin.title = "Remove from Favorites";
      unpin.setAttribute("aria-label", `Unpin ${VIEW_LABELS[view] || view}`);
      unpin.textContent = "×";
      unpin.addEventListener("click", (e) => {
        e.stopPropagation();
        setFavorites(getFavorites().filter((v) => v !== view));
      });

      row.appendChild(go);
      row.appendChild(unpin);

      row.addEventListener("dragstart", (e) => {
        row.classList.add("dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", view);
      });
      row.addEventListener("dragend", () => row.classList.remove("dragging"));
      row.addEventListener("dragover", (e) => {
        e.preventDefault();
        row.classList.add("drag-over");
      });
      row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
      row.addEventListener("drop", (e) => {
        e.preventDefault();
        row.classList.remove("drag-over");
        const from = e.dataTransfer.getData("text/plain");
        const to = view;
        if (!from || from === to) return;
        const next = getFavorites().filter((v) => v !== from);
        const at = next.indexOf(to);
        next.splice(at < 0 ? next.length : at, 0, from);
        setFavorites(next);
      });

      list.appendChild(row);
    });
  }

  function init() {
    render();
    syncPinButton();
    document.getElementById("favoriteCurrentViewBtn")?.addEventListener("click", () => {
      toggleFavorite(currentView());
      syncPinButton();
    });
    window.addEventListener("aria-view-change", () => {
      syncPinButton();
      const view = currentView();
      window.AriaUiPrefs?.pushRecent?.("recentViews", view, 10);
      window.AriaUiPrefs?.bumpUsage?.("viewVisits", view);
    });
    window.addEventListener("aria-ui-prefs", () => {
      render();
      syncPinButton();
    });
  }

  window.AriaFavorites = {
    getFavorites,
    setFavorites,
    isFavorite,
    toggleFavorite,
    VIEW_LABELS,
    render,
    syncPinButton,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
