/** Breadcrumbs — section > page context on every major view. Parent click opens the matching sidebar group. */
(function () {
  "use strict";

  const MAP = {
    chat: { section: "AI", sectionKey: "capabilities", label: "Chat" },
    dashboard: { section: "Home", sectionKey: null, label: "Home" },
    // Sidebar nav group formerly labeled Workspaces — now Surfaces
    workstation: { section: "Mission Control", sectionKey: "workstation", label: "Mission Control" },
    mission: { section: "Mission Control", sectionKey: "workstation", label: "Mission Control" },
    planner: { section: "Surfaces", sectionKey: "workspaces", label: "Planner" },
    calendar: { section: "Surfaces", sectionKey: "workspaces", label: "Calendar" },
    journal: { section: "Surfaces", sectionKey: "workspaces", label: "Bullet Journal" },
    memory: { section: "Surfaces", sectionKey: "workspaces", label: "Memory" },
    documents: { section: "Surfaces", sectionKey: "workspaces", label: "Documents" },
    projects: { section: "Developer", sectionKey: "coding", label: "Projects" },
    browser: { section: "AI", sectionKey: "capabilities", label: "Browser Agent" },
    flytying: { section: "Maker", sectionKey: "maker", label: "Fly Tying" },
    capabilities: { section: "System", sectionKey: "services", label: "Capabilities" },
    integrations: { section: "System", sectionKey: "integrations", label: "Integrations" },
    maker: { section: "Maker", sectionKey: "maker", label: "CAD Lab" },
    gallery: { section: "Media", sectionKey: "video", label: "Gallery" },
    video: { section: "Media", sectionKey: "video", label: "Video" },
    meme: { section: "Media", sectionKey: "video", label: "Meme Studio" },
    audio: { section: "Media", sectionKey: "video", label: "Audio" },
    voice: { section: "Media", sectionKey: "video", label: "Voice" },
    vision: { section: "Media", sectionKey: "video", label: "Vision" },
    security: { section: "System", sectionKey: "services", label: "Security" },
    presence: { section: "System", sectionKey: "services", label: "Presence" },
    audit: { section: "System", sectionKey: "services", label: "Audit & Repair" },
    actions: { section: "System", sectionKey: "services", label: "Actions Report" },
  };

  function openSection(sectionKey) {
    if (!sectionKey) {
      window.switchToView?.("dashboard");
      return;
    }
    const sec = document.querySelector(`.sidebar-section[data-section="${sectionKey}"]`);
    if (!sec) return;
    if (sec.classList.contains("collapsed")) sec.querySelector(".sidebar-section-head")?.click();
    sec.scrollIntoView({ block: "center", behavior: "smooth" });
    sec.classList.add("sidebar-section--flash");
    setTimeout(() => sec.classList.remove("sidebar-section--flash"), 1600);
  }

  function render(view) {
    const bar = document.getElementById("breadcrumbBar");
    if (!bar) return;
    const entry = MAP[view];
    if (!entry) {
      bar.classList.add("hidden");
      return;
    }
    bar.classList.remove("hidden");
    bar.replaceChildren();

    const parent = document.createElement("button");
    parent.type = "button";
    parent.className = "breadcrumb-parent";
    parent.textContent = entry.section;
    parent.title = `Open ${entry.section} in sidebar`;
    parent.addEventListener("click", () => openSection(entry.sectionKey));

    const sep = document.createElement("span");
    sep.className = "breadcrumb-sep";
    sep.setAttribute("aria-hidden", "true");
    sep.textContent = "›";

    const leaf = document.createElement("span");
    leaf.className = "breadcrumb-leaf";
    leaf.textContent = entry.label;
    leaf.setAttribute("aria-current", "page");

    bar.append(parent, sep, leaf);
  }

  function init() {
    render(document.querySelector(".view-tab.active")?.dataset?.view || "chat");
    window.addEventListener("aria-view-change", (e) => render(e.detail?.view));
  }

  window.AriaBreadcrumbs = { render };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
