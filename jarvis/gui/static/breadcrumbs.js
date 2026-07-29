/** Breadcrumbs — section > page for every Product Home. */
(function () {
  "use strict";

  const MAP = {
    chat: { section: "AI", sectionKey: "capabilities", label: "Chat" },
    dashboard: { section: "Home", sectionKey: null, label: "Home" },
    search: { section: "Surfaces", sectionKey: "workspaces", label: "Search" },
    settings: { section: "Surfaces", sectionKey: "workspaces", label: "Settings" },
    workstation: { section: "Mission Control", sectionKey: "workstation", label: "Mission Control" },
    mission: { section: "Mission Control", sectionKey: "workstation", label: "Mission Control" },
    planner: { section: "Surfaces", sectionKey: "workspaces", label: "Planner" },
    calendar: { section: "Surfaces", sectionKey: "workspaces", label: "Calendar" },
    journal: { section: "Surfaces", sectionKey: "workspaces", label: "Bullet Journal" },
    memory: { section: "Surfaces", sectionKey: "workspaces", label: "Memory" },
    documents: { section: "Surfaces", sectionKey: "workspaces", label: "Documents" },
    connections: { section: "Surfaces", sectionKey: "workspaces", label: "Connections" },
    projects: { section: "Developer", sectionKey: "coding", label: "Projects" },
    coding: { section: "Developer", sectionKey: "coding", label: "Coding" },
    models: { section: "Developer", sectionKey: "coding", label: "Models" },
    browser: { section: "AI", sectionKey: "capabilities", label: "Browser" },
    automation: { section: "System", sectionKey: "services", label: "Automation" },
    flytying: { section: "Maker", sectionKey: "maker", label: "Fly Tying" },
    maker: { section: "Maker", sectionKey: "maker", label: "Maker Lab" },
    gallery: { section: "Media", sectionKey: "video", label: "Gallery" },
    video: { section: "Media", sectionKey: "video", label: "Video" },
    meme: { section: "Media", sectionKey: "video", label: "Meme Studio" },
    audio: { section: "Media", sectionKey: "video", label: "Audio" },
    voice: { section: "Media", sectionKey: "video", label: "Voice" },
    vision: { section: "Media", sectionKey: "video", label: "Vision" },
    capabilities: { section: "System", sectionKey: "services", label: "Capabilities" },
    integrations: { section: "System", sectionKey: "integrations", label: "Integrations" },
    security: { section: "System", sectionKey: "services", label: "Security" },
    presence: { section: "System", sectionKey: "services", label: "Presence" },
    audit: { section: "System", sectionKey: "services", label: "Audit & Repair" },
    actions: { section: "System", sectionKey: "services", label: "Actions Report" },
    // Modal surfaces — shown when view is related or last product view
    notifications: { section: "Shell", sectionKey: null, label: "Notifications" },
    layouts: { section: "Shell", sectionKey: null, label: "Layouts" },
    jobs: { section: "System", sectionKey: "services", label: "Job Center" },
  };

  function openSection(sectionKey) {
    if (!sectionKey) {
      window.switchToView?.("dashboard");
      return;
    }
    const sec = document.querySelector(`.sidebar-section[data-section="${sectionKey}"]`);
    if (!sec) return;
    const head = sec.querySelector(".sidebar-section-head");
    if (sec.classList.contains("collapsed") && head) head.click();
    sec.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
  }

  function render(view) {
    const host = document.getElementById("ariaBreadcrumbs");
    if (!host) return;
    const meta = MAP[view] || { section: "Aria", sectionKey: null, label: view || "View" };
    host.replaceChildren();
    const secBtn = document.createElement("button");
    secBtn.type = "button";
    secBtn.className = "ghost-btn tiny";
    secBtn.textContent = meta.section;
    secBtn.addEventListener("click", () => openSection(meta.sectionKey));
    const sep = document.createElement("span");
    sep.className = "muted";
    sep.textContent = " / ";
    const page = document.createElement("span");
    page.textContent = meta.label;
    page.setAttribute("aria-current", "page");
    host.append(secBtn, sep, page);
  }

  function init() {
    window.addEventListener("aria-view-change", (e) => render(e.detail?.view || ""));
    render(document.querySelector(".view-tab.active")?.dataset?.view || "chat");
  }

  window.AriaBreadcrumbs = { render, MAP };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
