/** Dynamic rotating chat suggestions — contextual, non-repetitive. */
(function () {
  "use strict";

  const ROTATE_MS = 45000;
  const SHOW_COUNT = 5;

  const POOL = [
    { id: "cmd-k", cat: "shortcut", text: "Press Ctrl+K to open Commands.", action: "palette", run: () => window.openCommandPalette?.() },
    { id: "summarize-day", cat: "workflow", text: "Summarize today's work.", action: "prompt" },
    { id: "review-code", cat: "workflow", text: "Review my latest code.", action: "prompt" },
    { id: "search-memory", cat: "workflow", text: "Search your Memory.", action: "view", view: "memory" },
    { id: "continue-project", cat: "workflow", text: "Continue yesterday's project.", action: "prompt" },
    { id: "gen-image", cat: "media", text: "Generate an image.", action: "prompt", prompt: "Generate an image of " },
    { id: "resume-media", cat: "media", text: "Resume your media job.", action: "view", view: "gallery" },
    { id: "check-ha", cat: "home", text: "Check Home Assistant.", action: "prompt", prompt: "home status" },
    { id: "organize-notes", cat: "workflow", text: "Ask Aria to organize your notes.", action: "prompt" },
    { id: "morning", cat: "time", text: "Morning briefing", action: "prompt", when: (h) => h < 11 },
    { id: "afternoon", cat: "time", text: "What should I focus on this afternoon?", action: "prompt", when: (h) => h >= 12 && h < 17 },
    { id: "evening", cat: "time", text: "Reflect on my day.", action: "prompt", when: (h) => h >= 17 },
    { id: "planner-today", cat: "workflow", text: "What are my open tasks?", action: "prompt" },
    { id: "journal-today", cat: "workflow", text: "Journal today", action: "prompt" },
    { id: "calendar-today", cat: "workflow", text: "What's on my calendar today?", action: "prompt" },
    { id: "free-vram", cat: "tip", text: "Free VRAM before image or video generation.", action: "palette" },
    { id: "favorites", cat: "tip", text: "Pin frequent views to Favorites in the sidebar.", action: "hint" },
    { id: "whats-new", cat: "feature", text: "See What's New in Aria.", action: "whatsnew" },
    { id: "pomodoro", cat: "workflow", text: "Start a Pomodoro focus timer.", action: "view", view: "planner" },
    { id: "fly-pattern", cat: "inspiration", text: "Suggest a fly pattern for this season.", action: "prompt" },
    { id: "maker-idea", cat: "inspiration", text: "Help me design a printable part.", action: "view", view: "maker" },
    { id: "docs-search", cat: "workflow", text: "Search my documents.", action: "view", view: "documents" },
    { id: "provider-health", cat: "tip", text: "Check whether Ollama is healthy or degraded.", action: "view", view: "workstation" },
    { id: "shortcuts", cat: "shortcut", text: "Open keyboard shortcuts.", action: "modal", modal: "shortcutsModal" },
    { id: "mute", cat: "shortcut", text: "Toggle speak-replies from the voice strip.", action: "hint" },
    { id: "deep-link", cat: "tip", text: "Jump from Planner → Calendar → Journal in one click.", action: "view", view: "planner" },
    { id: "skills", cat: "feature", text: "Open Automation Home to run a skill (Dry run first).", action: "view", view: "automation" },
    { id: "automation", cat: "feature", text: "What automations are scheduled?", action: "view", view: "automation" },
    { id: "security", cat: "tip", text: "Set an optional PIN lock in Security.", action: "view", view: "security" },
    { id: "browser", cat: "workflow", text: "Browse the web with the Browser agent.", action: "view", view: "browser" },
    { id: "meme", cat: "inspiration", text: "Make a meme from this idea.", action: "view", view: "meme" },
    { id: "remember", cat: "workflow", text: "What do you remember about me?", action: "prompt" },
    { id: "where-left", cat: "workflow", text: "Where did I leave off?", action: "prompt" },
    { id: "heading-out", cat: "home", text: "I'm heading out", action: "prompt" },
    { id: "debug-bundle", cat: "tip", text: "Copy a debug bundle when something looks wrong.", action: "click", el: "debugBundleBtn" },
  ];

  const CONTEXT = {
    chat: [
      { id: "ctx-chat-1", text: "Help me think through this problem.", action: "prompt" },
      { id: "ctx-chat-2", text: "Make this answer shorter.", action: "prompt" },
      { id: "ctx-chat-split", text: "Split Chat with Planner", action: "split", primary: "chat", secondary: "planner" },
    ],
    planner: [
      { id: "ctx-pl", text: "Prioritize my tasks for today.", action: "prompt" },
      { id: "ctx-pl-journal", text: "Open Journal to log progress.", action: "view", view: "journal" },
    ],
    memory: [
      { id: "ctx-mem", text: "Search my memory for preferences.", action: "prompt" },
      { id: "ctx-mem-docs", text: "Search related Documents.", action: "view", view: "documents" },
    ],
    gallery: [
      { id: "ctx-gal", text: "Generate an image.", action: "prompt", prompt: "Generate an image of " },
      { id: "ctx-gal-fly", text: "Browse Fly Tying patterns for inspiration.", action: "view", view: "flytying" },
    ],
    maker: [
      { id: "ctx-mk", text: "Iterate on my CAD design.", action: "prompt" },
      { id: "ctx-mk-proj", text: "Open Projects for related work.", action: "view", view: "projects" },
    ],
    flytying: [
      { id: "ctx-fly", text: "Recommend a pattern for today's hatch.", action: "prompt" },
      { id: "ctx-fly-gal", text: "Open Gallery for pattern photos.", action: "view", view: "gallery" },
    ],
    workstation: [
      { id: "ctx-mc", text: "Show me anything unhealthy in Mission Control.", action: "prompt" },
      { id: "ctx-mc-act", text: "Open Notifications for alerts.", action: "activity" },
    ],
    projects: [
      { id: "ctx-proj", text: "Review my latest code.", action: "prompt" },
      { id: "ctx-proj-chat", text: "Switch to Coding mode.", action: "coding" },
    ],
    browser: [
      { id: "ctx-br", text: "Research this topic for me.", action: "prompt", prompt: "Research: " },
      { id: "ctx-br-docs", text: "Save findings to Documents.", action: "view", view: "documents" },
    ],
    audit: [
      { id: "ctx-audit", text: "Run a full system audit.", action: "click", el: "auditRunBtn" },
      { id: "ctx-audit-mc", text: "Open Mission Control diagnostics.", action: "view", view: "workstation" },
    ],
    dashboard: [
      { id: "ctx-dash-resume", text: "Resume yesterday's work.", action: "prompt" },
      { id: "ctx-dash-ws", text: "Switch Layouts.", action: "workspace" },
    ],
  };

  let rotateTimer = null;

  function hourOk(item) {
    if (typeof item.when !== "function") return true;
    return item.when(new Date().getHours());
  }

  function currentView() {
    return document.querySelector(".view-tab.active")?.dataset?.view || "chat";
  }

  function pickSuggestions() {
    const prefs = window.AriaUiPrefs?.load?.() || {};
    const seen = new Set(prefs.suggestionSeen || []);
    const clicks = prefs.suggestionClicks || {};
    const visits = prefs.viewVisits || {};
    const view = currentView();
    const hour = new Date().getHours();

    const contextual = (CONTEXT[view] || []).map((c) => ({ ...c, cat: "context", boost: 30 }));
    const pool = [...POOL.filter(hourOk), ...contextual];

    const scored = pool.map((item) => {
      let score = 10 + Math.random() * 20;
      if (seen.has(item.id)) score -= 40;
      score += Math.min(12, (clicks[item.id] || 0) * 2);
      if (item.cat === "context") score += 25;
      if (item.cat === "time") score += 15;
      if (item.view && (visits[item.view] || 0) > 2) score += 8;
      if (item.cat === "feature" && !(prefs.whatsNewSeen)) score += 20;
      // Prefer categories not recently shown
      const recentCats = (prefs.suggestionSeen || []).slice(-8);
      const catHits = recentCats.filter((id) => pool.find((p) => p.id === id)?.cat === item.cat).length;
      score -= catHits * 5;
      return { item, score };
    });

    scored.sort((a, b) => b.score - a.score);
    const picked = [];
    const usedCats = new Set();
    for (const { item } of scored) {
      if (picked.length >= SHOW_COUNT) break;
      if (usedCats.has(item.cat) && picked.length < SHOW_COUNT - 1) {
        // allow second of same cat only late
        if (picked.filter((p) => p.cat === item.cat).length >= 1) continue;
      }
      picked.push(item);
      usedCats.add(item.cat);
    }

    const nextSeen = [...picked.map((p) => p.id), ...(prefs.suggestionSeen || [])].slice(0, 40);
    window.AriaUiPrefs?.set?.("suggestionSeen", nextSeen);
    return picked;
  }

  function runSuggestion(item) {
    window.AriaUiPrefs?.bumpUsage?.("suggestionClicks", item.id);
    const prompt = item.prompt || item.text;
    if (item.action === "palette") {
      window.openCommandPalette?.();
      return;
    }
    if (item.action === "whatsnew") {
      window.openWhatsNew?.();
      return;
    }
    if (item.action === "activity") {
      window.AriaActivity?.open?.();
      return;
    }
    if (item.action === "workspace") {
      window.AriaLayouts?.openModal?.() || window.AriaWorkspaces?.openModal?.();
      return;
    }
    if (item.action === "split") {
      window.AriaSplitView?.enable?.(item.primary || "chat", item.secondary || "planner");
      return;
    }
    if (item.action === "coding") {
      window.switchToView?.("chat");
      document.querySelector('.module-chip[data-module="coding"]')?.click();
      return;
    }
    if (item.action === "modal" && item.modal) {
      document.getElementById(item.modal)?.classList.remove("hidden");
      return;
    }
    if (item.action === "click" && item.el) {
      document.getElementById(item.el)?.click();
      return;
    }
    if (item.action === "view" && item.view) {
      window.switchToView?.(item.view);
      return;
    }
    if (item.action === "hint") {
      window.showAriaToast?.(item.text, "info", 4000);
      return;
    }
    // prompt / default — populate and optionally send for clear commands
    window.switchToView?.("chat");
    setTimeout(() => {
      const input = document.getElementById("messageInput");
      if (!input) return;
      input.value = prompt;
      input.focus();
      if (item.action === "prompt" && !String(prompt).endsWith(" ")) {
        // leave for edit unless it's a complete short command
        const autoSend = /^(Morning briefing|home status|I'm heading out|Journal today|What do you remember about me\?|Where did I leave off\?)$/i.test(prompt);
        if (autoSend && typeof window.jarvisSendToChat === "function") {
          window.jarvisSendToChat(prompt);
        }
      }
    }, 60);
  }

  function render() {
    const el = document.getElementById("suggestions");
    if (!el) return;
    // Living Room owns the hearth chips — no feature-marketing wall
    if (window.AriaLivingRoom?.isActive?.()) {
      window.AriaLivingRoom?.refreshSuggestions?.();
      return;
    }
    // Preserve attachment-driven chips
    const keep = [...el.querySelectorAll(".data-chip, .vision-chip")];
    el.replaceChildren();
    keep.forEach((n) => el.appendChild(n));
    pickSuggestions().forEach((item) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = `suggestion-chip suggestion-chip--${item.cat || "general"}`;
      chip.textContent = item.text;
      chip.title = item.cat ? `${item.cat} · click to use` : "Click to use";
      chip.dataset.suggestionId = item.id;
      chip.addEventListener("click", () => runSuggestion(item));
      el.appendChild(chip);
    });
  }

  async function loadSuggestions() {
    try {
      const res = await fetch("/api/suggestions");
      const data = await res.json().catch(() => ({}));
      if (window.jarvisAttach) {
        window.jarvisAttach.visionChips = data.vision_chips || [];
        window.jarvisAttach.dataChips = data.data_chips || [];
      }
      render();
      const pendingFile = window.jarvisAttach?.pendingFile;
      const pendingFile2 = window.jarvisAttach?.pendingFile2;
      if (pendingFile && window.isDataAttachment?.(pendingFile)) window.refreshDataChips?.();
      else if (pendingFile || pendingFile2) window.refreshVisionChips?.();
      const ed = await window.loadEditorContext?.();
      if (ed?.fresh && ed.file) window.refreshEditorSuggestions?.(ed.file, ed.ctx?.has_selection);
    } catch (err) {
      render();
      window.showAriaToast?.(err?.message || "Could not load suggestions", "err", 4000);
    }
  }

  function startRotate() {
    if (rotateTimer) clearInterval(rotateTimer);
    rotateTimer = setInterval(() => {
      if (document.hidden) return;
      if (document.querySelector(".view-tab.active")?.dataset?.view !== "chat") return;
      render();
    }, ROTATE_MS);
  }

  window.loadSuggestions = loadSuggestions;
  window.refreshDynamicSuggestions = render;

  window.addEventListener("aria-view-change", () => {
    if (document.querySelector(".view-tab.active")?.dataset?.view === "chat") render();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      startRotate();
    });
  } else {
    startRotate();
  }
})();
