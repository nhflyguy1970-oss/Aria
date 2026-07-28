/** Command catalog — domain modules register into AriaCommandRegistry (palette is orchestrator only). */
(function () {
  "use strict";

  const A = () => window.AriaActions;
  const R = () => window.AriaCommandRegistry;

  function reg(list) {
    R()?.registerMany?.(list);
  }

  function mk(id, title, group, keywords, run, extra = {}) {
    return { id, title, label: title, group, keywords, run, source: "catalog", ...extra };
  }

  function registerNavigate() {
    const views = [
      ["chat", "Chat", "conversation ai"],
      ["dashboard", "Dashboard", "home overview"],
      ["workstation", "Mission Control", "mc operator acm health ctrl+shift+m"],
      ["mission", "Mission Control", "mc operator health infrastructure"],
      ["models", "Models", "ollama providers roles catalog routing ctrl+shift+."],
      ["coding", "Coding", "propose apply undo verify lsp git proposals ctrl+shift+c"],
      ["planner", "Planner", "tasks todo"],
      ["calendar", "Calendar", "schedule"],
      ["flytying", "Fly tying", "flies patterns"],
      ["projects", "Projects", "repos"],
      ["maker", "Maker lab", "cad stl print"],
      ["browser", "Browser", "playwright web agent ctrl+shift+b"],
      ["security", "Security", "pin auth"],
      ["presence", "Presence", "location"],
      ["audit", "System / audit", "logs repair"],
      ["voice", "Voice", "speech mic"],
      ["audio", "Audio", "sound whisper"],
      ["journal", "Bullet Journal", "bujo gratitude"],
      ["memory", "Memory", "knowledge recall"],
      ["gallery", "Gallery", "images comfy"],
      ["video", "Video", "movie render"],
      ["meme", "Meme studio", "captions"],
      ["documents", "Documents", "files pdf"],
      ["connections", "Connections", "knowledge graph relationships entities"],
      ["automation", "Automation", "rules schedules skills workflows orchestration"],
      ["actions", "Actions / report", "checklist"],
    ];
    reg(views.map(([id, label, keywords]) =>
      mk(`nav:${id}`, `Go to ${label}`, "Navigate", keywords, () => A().goView(id), {
        mode: "navigate",
        hint: "View",
        description: `Open the ${label} view`,
      })
    ));
  }

  function registerMissionControl() {
    const labels = {
      overview: "Overview",
      routing: "Routing",
      timeline: "Timeline",
      intent_analytics: "Intent Analytics",
      release: "Release",
      connection: "Connection",
      applications: "Applications",
      inference: "Inference",
      memory: "Memory",
      knowledge: "Knowledge",
      databases: "Databases",
      hardware: "Hardware",
      jobs: "Queue Snapshot",
      activity: "Operations Event Log",
      performance: "Performance",
      settings: "Settings",
      recovery: "Recovery",
    };
    const tabs = Object.keys(labels);
    reg(tabs.map((tab) =>
      mk(`mc:${tab}`, `Mission Control · ${labels[tab]}`, "Mission Control", `mc ${tab} ${labels[tab]}`, () => A().goMc(tab), {
        mode: "system",
        hint: tab === "overview" ? "Ctrl+Shift+M" : "MC",
        shortcut: tab === "overview" ? "Ctrl+Shift+M" : undefined,
      })
    ));
    reg([
      mk("mc:open", "Open Mission Control", "Mission Control", "health infrastructure console workstation mission", () => A().goMc("overview"), {
        mode: "system",
        hint: "Ctrl+Shift+M",
        shortcut: "Ctrl+Shift+M",
      }),
    ]);
  }

  function registerChatActions() {
    reg([
      mk("act:focus-chat", "Focus chat input", "Actions", "message type ask", () => A().chat.focus()),
      mk("act:clear-chat", "Clear conversation", "Actions", "reset wipe history", () => A().chat.clear()),
      mk("act:read-aloud", "Read last reply aloud", "Actions", "tts speak", () => A().chat.readAloud()),
      mk("act:stop-chat", "Stop responding", "Actions", "cancel abort", () => A().chat.stop()),
      mk("act:export-chat", "Export chat (Markdown)", "Actions", "download md transcript", () => A().chat.exportMd()),
      mk("act:export-chat-pdf", "Export chat (PDF)", "Actions", "download pdf transcript", () => A().chat.exportPdf()),
      mk("act:new-branch", "New Chat", "Actions", "branch fork session thread", () => A().newChat(), {
        description: "Start a fresh chat thread",
      }),
      mk("act:compare-images", "Compare two images", "Actions", "vision attach side-by-side diff", () => A().chat.compare()),
      mk("act:webcam", "Capture webcam attachment", "Actions", "camera vision", () => A().chat.webcam()),
      mk("act:ask-status", "Ask Aria: status", "AI", "health summary", () => A().askAria("Give me a concise status of Aria systems and what needs attention."), {
        mode: "ask",
      }),
    ]);
  }

  function registerProductivity() {
    reg([
      mk("act:planner-task", "Add planner task", "Actions", "todo focus task input", () => A().planner.focusTask()),
      mk("act:pomodoro", "Start Pomodoro", "Actions", "focus 25 timer", () => A().planner.pomodoro()),
      mk("act:calendar-today", "Open calendar today", "Actions", "schedule day", () => A().calendar.today()),
      mk("act:ics-wizard", "Focus calendar ICS import", "Actions", "subscribe ics", () => A().calendar.focusIcs()),
      mk("act:journal-rapid", "Focus journal rapid log", "Actions", "bujo quick capture bullet", () => A().journal.rapid()),
    ]);
  }

  function registerKnowledge() {
    reg([
      mk("act:memory", "Open Memory", "Actions", "recall knowledge acm", () => A().memory.open()),
      mk("act:run-research", "Run knowledge research now", "Actions", "nightly briefs", () => A().memory.research()),
      mk("act:documents-reindex", "Rebuild document search index", "System", "library pdf chunks rag", () => A().documents.rebuild()),
      mk("act:open-connections", "Open Connections", "Navigate", "knowledge graph relationships entities links", () => A().connections.open(), {
        mode: "navigate",
      }),
      mk("act:connections-search", "Search Connections", "Actions", "graph entity relationship", () => A().connections.search()),
      mk("search:journal", "Search journal", "Search", "bujo find filter", () => A().journal.search(), { mode: "search" }),
      mk("search:memory", "Search memory", "Search", "recall find filter", () => A().memory.search(), { mode: "search" }),
      mk("search:documents", "Search documents", "Search", "library files pdf", () => A().documents.search(), { mode: "search" }),
      mk("search:flytying", "Search fly patterns", "Search", "tying recipes", () => A().flytying.search(), { mode: "search" }),
      mk("search:gallery-prompt", "Focus gallery prompt", "Search", "comfy image generate", () => A().gallery.focusPrompt(), { mode: "search" }),
      mk("search:mc-routing", "Search Mission Control routing", "Search", "intent handler prompts", () => A().mission.routingSearch(), { mode: "search" }),
    ]);
  }

  function registerMediaDev() {
    reg([
      mk("act:gallery", "Open Gallery Home", "Gallery", "images comfy generate ctrl+shift+g", () => window.openGalleryHome?.() || A().gallery.open(), {
        hint: "Ctrl+Shift+G",
        shortcut: "Ctrl+Shift+G",
      }),
      mk("act:generate-image", "Generate image (Gallery)", "AI", "comfy create stay in gallery", () => {
        const prompt = document.getElementById("galleryPromptInput")?.value?.trim();
        if (!prompt) {
          A().gallery.focusPrompt();
          window.showAriaToast?.("Enter an image description first", "warn");
          return;
        }
        A().gallery.generate();
      }, { mode: "ask" }),
      mk("act:gallery-search", "Focus gallery search", "Gallery", "find caption prompt", () => {
        A().gallery.open();
        setTimeout(() => document.getElementById("gallerySearchInput")?.focus(), 80);
      }),
      mk("act:video-studio", "Open Video Studio", "Actions", "animate movie", () => A().video.studio()),
      mk("act:video-storyboard", "Focus video storyboard", "Actions", "shots", () => A().video.storyboard()),
      mk("act:audio-studio", "Open Audio studio", "Actions", "music podcast genre song whisper", () => A().audio.open()),
      mk("act:meme-studio", "Open Meme Studio", "Actions", "captions funny", () => A().meme.open()),
      mk("act:maker", "Open Maker lab", "Actions", "cad stl print", () => A().maker.open()),
      mk("act:fly-tying", "Open Fly tying", "Actions", "flies patterns", () => A().flytying.open()),
      mk("act:open-projects", "Open Projects", "Actions", "repos workspace coding", () => A().projects.open()),
      mk("act:browser-url", "Focus browser URL", "Actions", "playwright navigate web", () => A().browser.focusUrl()),
      mk("act:browser-task", "Focus browser agent task", "Actions", "playwright goal run", () => A().browser.focusTask()),
      mk("act:browser-home", "Open Browser Home", "Browser", "playwright session history bookmarks ctrl+shift+b", () => window.openBrowserHome?.() || A().goView("browser"), {
        hint: "Ctrl+Shift+B",
        shortcut: "Ctrl+Shift+B",
      }),
      mk("act:resume-media-jobs", "Resume pending media jobs", "Actions", "queue retry", () => A().system.resumeMedia()),
    ]);
  }

  function registerSystem() {
    reg([
      mk("act:free-vram", "Free VRAM", "System", "gpu memory", () => A().system.freeVram()),
      mk("act:cloud-live", "Toggle Cloud Live voice", "Actions", "openai gemini duplex", () => A().voice.cloudLive()),
      mk("act:git-status", "Refresh git status", "System", "repo", () => A().system.gitStatus()),
      mk("act:presence", "Open Presence camera", "Actions", "location face", () => A().goView("presence")),
      mk("act:audit", "Open System audit", "System", "logs repair", () => A().audit.open()),
      mk("act:mute-voice", "Toggle voice mute", "Actions", "tts silence", () => A().voice.mute()),
      mk("act:speak-replies", "Toggle speak replies", "Actions", "read aloud tts", () => A().voice.speakToggle()),
      mk("act:stop-speaking", "Stop speaking", "Actions", "tts halt", () => A().voice.stopSpeaking()),
      mk("act:uncensored", "Toggle uncensored mode", "Settings", "nsfw", () => A().system.uncensored()),
      mk("act:server-whisper", "Toggle server Whisper", "Settings", "stt", () => A().voice.serverWhisper()),
      mk("act:lan-copy", "Copy LAN URL", "System", "network share", () => A().system.lanCopy()),
      mk("act:open-actions", "Open Actions / report", "Navigate", "checklist history", () => A().goView("actions"), { mode: "navigate" }),
      mk("act:lock-security", "Lock Aria (PIN)", "System", "security pin lock screen", () => A().system.lock()),
      mk("act:security", "Open Security / PIN", "System", "lock pin auth trust", () => A().goView("security")),
      mk("act:models-editor", "Open Models Home", "Models", "ollama providers roles catalog registry", () => A().system.modelsHome?.() || A().system.modelsEditor(), {
        hint: "Ctrl+Shift+.",
        shortcut: "Ctrl+Shift+.",
      }),
      mk("act:coding-home", "Open Coding Home", "Coding", "propose apply undo verify lsp git proposals", () => window.openCodingHome?.() || A().goView("coding"), {
        hint: "Ctrl+Shift+C",
        shortcut: "Ctrl+Shift+C",
      }),
      mk("act:coding-history", "Coding proposal history", "Coding", "patches applied undo", () => window.openCodingHome?.("history") || A().goView("coding")),
      mk("act:coding-verify", "Verify last apply", "Coding", "tests syntax lint", () => window.AriaCodingVerify?.promptLast?.()),
      mk("act:pull-models", "Pull missing models", "Models", "download ollama", () => A().system.pullModels()),
      mk("act:models-recommend", "Recommend model stack", "Models", "suggest balanced fast quality", () => window.openModelsHome?.("recommend") || A().goView("models")),
      mk("act:lsp-diag", "LSP diagnostics", "System", "language server", () => A().system.lsp()),
      mk("act:reindex-code", "Reindex code", "System", "symbols search", () => A().system.reindexCode()),
      mk("act:job-center", "Open job center", "Actions", "queue media coding", () => A().mission.jobs()),
      mk("act:settings", "Open voice & chat settings", "Actions", "preferences", () => A().system.settings()),
      mk("act:shortcuts", "Open keyboard shortcuts", "Actions", "hotkeys help", () => A().system.shortcuts()),
      mk("act:upgrade", "Open upgrade wizard", "Actions", "self update", () => A().system.upgrade()),
      mk("act:ha-setup", "Open smart home setup", "Actions", "home assistant", () => A().system.haSetup()),
      mk("act:ha-test", "Test Home Assistant connection", "Actions", "ha ping smart home connection", () => A().system.haTest()),
      mk("act:image-engine", "Open image engine / Comfy settings", "Actions", "comfyui", () => A().system.imageEngine()),
      mk("act:integrations-keys", "API keys (Cloud Live & models)", "Actions", "secrets tokens", () => A().system.apiKeys()),
      mk("act:voice-smoke", "Run voice smoke test", "AI", "stt tts check", () => A().voice.smoke(), { mode: "ask" }),
      mk("act:router-warm", "Warm model router", "AI", "preload", () => A().system.warmRouter(), { mode: "ask" }),
      mk("act:reload-ui", "Reload UI", "System", "refresh soft", () => A().system.reloadUi()),
      mk("act:reset-sidebar", "Expand all sidebar sections", "System", "layout", () => A().system.resetSidebar()),
      mk("act:backup", "Backup Aria data", "System", "export archive", () => A().system.backup()),
      mk("act:theme-toggle", "Toggle light / dark theme", "System", "appearance light dark", () => A().system.theme()),
      mk("act:debug-bundle", "Copy debug bundle", "System", "diagnostics troubleshooting clipboard", () => A().system.debugBundle()),
      mk("act:checklist", "Run first-flight checklist", "Actions", "onboarding", () => A().system.checklist()),
    ]);
  }

  function registerShell() {
    reg([
      mk("act:activity", "Open Activity Center", "Actions", "notifications jobs alerts inbox events unread", () => A().shell.activity()),
      mk("act:activity-whats-wrong", "What's wrong? (Activity summary)", "Actions", "unread failures diagnose aria inbox", () => {
        if (window.AriaActivityActions?.whatsWrong) return window.AriaActivityActions.whatsWrong();
        return A().shell.activity();
      }, { mode: "ask" }),
      mk("act:activity-unread", "Activity: show unread", "Actions", "filter unread alerts", () => {
        window.AriaActivityStore?.setFilter?.("unread");
        return A().shell.activity();
      }),
      mk("act:activity-errors", "Activity: show errors", "Actions", "filter errors failures", () => {
        window.AriaActivityStore?.setFilter?.("err");
        return A().shell.activity();
      }),
      mk("act:automation-home", "Open Automation Home", "Actions", "automation rules schedules orchestration", () => A().goView("automation")),
      mk("act:automation-status", "Automation status", "Actions", "scheduled engine pause", () => {
        A().goView("automation");
        return true;
      }),
      mk("act:automation-failures", "Automation: recent failures", "Actions", "failed runs", () => {
        A().goView("automation");
        return true;
      }),
      mk("act:automation-pause", "Pause automations", "Actions", "pause travel", async () => {
        await fetch("/api/automation/pause", { method: "POST", body: JSON.stringify({ paused: true }), headers: { "Content-Type": "application/json" } });
        window.showAriaToast?.("Automations paused", "warn");
        return true;
      }),
      mk("act:automation-resume", "Resume automations", "Actions", "resume engine", async () => {
        await fetch("/api/automation/pause", { method: "POST", body: JSON.stringify({ paused: false }), headers: { "Content-Type": "application/json" } });
        await fetch("/api/automation/engine/start", { method: "POST", body: "{}" });
        window.showAriaToast?.("Automations resumed", "ok");
        return true;
      }),
      mk("act:automation-webhook", "Webhook status", "Actions", "home assistant inbound secret", () => {
        A().goView("automation");
        setTimeout(() => document.getElementById("autoWebhookBtn")?.click(), 200);
        return true;
      }),
      mk("act:automation-suggestions", "Learned automation suggestions", "Actions", "propose approve", () => {
        A().goView("automation");
        return true;
      }),
      mk("act:pipelines-list", "List pipelines (DAGs)", "Actions", "pipeline dag workflow automation", () => {
        A().goView("automation");
        return true;
      }),
      mk("act:pipelines-nl", "Draft pipeline from text", "Actions", "natural language pipeline draft", () => {
        A().goView("automation");
        setTimeout(() => document.getElementById("autoPipeNlBtn")?.click(), 250);
        return true;
      }),
      mk("act:pipelines-history", "Pipeline run history", "Actions", "pipeline runs failures history", async () => {
        A().goView("automation");
        try {
          const res = await fetch("/api/automation/pipeline-runs?limit=1");
          const data = await res.json();
          const run = (data.runs || [])[0];
          if (run) window.AriaAutomationHome?.openRunInspector?.(run);
          else window.showAriaToast?.("No pipeline runs yet", "warn");
        } catch (e) {
          window.showAriaToast?.(e.message || "Failed", "err");
        }
        return true;
      }),
      mk("act:specialists-propose", "Propose specialist team", "Actions", "specialists multi-agent team research", () => {
        window.AriaSpecialists?.openPropose?.();
        return true;
      }),
      mk("act:specialists-gallery", "Specialist gallery", "Actions", "roles coder writer vision", () => {
        window.AriaSpecialists?.openGallery?.();
        return true;
      }),
      mk("act:specialists-history", "Specialist team history", "Actions", "team runs inspect", () => {
        window.AriaSpecialists?.openHistory?.();
        return true;
      }),
      mk("act:view-paths", "Open View Paths", "Actions", "navigation shortcuts macro ui path recorder", () => A().shell.workflows()),
      mk("act:workspaces", "Workspace layouts", "Actions", "coding writing layout", () => A().shell.workspaces()),
      mk("act:split", "Toggle split view", "Actions", "dual pane", () => A().shell.split()),
      mk("act:mini-chat", "Toggle mini chat", "Actions", "floating assistant", () => A().shell.miniChat()),
      mk("act:workflows", "Open View Paths (navigation shortcuts)", "Actions", "view paths macro routine workflow recorder", () => A().shell.workflows()),
    ]);
  }

  function registerDynamicSelects() {
    const modelSelect = document.getElementById("chatModelSelect");
    if (modelSelect) {
      reg([...modelSelect.options].filter((o) => o.value).slice(0, 24).map((o) =>
        mk(`model:${o.value}`, `Use model: ${o.textContent || o.value}`, "Models", `ollama provider ${o.value}`, () => {
          A().setSelect("chatModelSelect", o.value, "Chat model");
          window.showAriaToast?.(`Model: ${o.textContent || o.value}`, "ok");
        }, { mode: "system", hint: "Chat" })
      ));
    }
    const profileSelect = document.getElementById("profileSelect");
    if (profileSelect) {
      reg([...profileSelect.options].filter((o) => o.value).slice(0, 16).map((o) =>
        mk(`profile:${o.value}`, `Config profile: ${o.textContent || o.value}`, "Settings", `profile config ${o.value}`, () => {
          A().setSelect("profileSelect", o.value, "Profile");
          window.showAriaToast?.(`Profile: ${o.textContent || o.value}`, "ok");
        }, { mode: "system", hint: "Sidebar" })
      ));
    }
    const personalitySelect = document.getElementById("personalitySelect");
    if (personalitySelect) {
      reg([...personalitySelect.options].filter((o) => o.value).slice(0, 16).map((o) =>
        mk(`personality:${o.value}`, `Personality: ${o.textContent || o.value}`, "Settings", `personality tone style ${o.value}`, () => {
          A().setSelect("personalitySelect", o.value, "Personality");
          window.showAriaToast?.(`Personality: ${o.textContent || o.value}`, "ok");
        }, { mode: "system", hint: "Sidebar" })
      ));
    }
  }

  function currentView() {
    return document.querySelector(".view-tab.active")?.dataset?.view || "chat";
  }

  function registerContextCommands() {
    // Remove prior context cmds so rebuild stays fresh
    const existing = R()?.list?.({ includeUnavailable: true }) || [];
    existing.filter((c) => c.context || String(c.id).startsWith("ctx:")).forEach((c) => R().unregister(c.id));

    const view = currentView();
    const mkCtx = (id, title, keywords, run, hint) =>
      mk(`ctx:${view}:${id}`, title, "This page", `${view} ${keywords || ""}`, run, {
        context: true,
        mode: "context",
        hint: hint || "Context",
      });

    const map = {
      gallery: [
        mkCtx("gen", "Generate an image", "create comfy", () => {
          A().gallery.open();
          A().askAria("Help me generate an image. Ask what subject, style, and aspect ratio I want.");
        }),
        mkCtx("compare", "Compare images", "diff", () => A().chat.compare()),
        mkCtx("import", "Focus gallery prompt", "prompt", () => A().gallery.focusPrompt()),
      ],
      planner: [
        mkCtx("task", "New Planner task", "todo add", () => A().planner.focusTask()),
        mkCtx("pomodoro", "Start Pomodoro", "focus 25", () => A().planner.pomodoro()),
        mkCtx("triage", "Plan My Day", "morning triage focus", () => A().planner.triage()),
        mkCtx("undo", "Undo last Planner change", "restore", () => A().planner.undo()),
        mkCtx("today", "Jump to Calendar today", "schedule", () => A().calendar.today()),
        mkCtx("journal", "Open Journal from Planner", "notes", () => A().journal.open()),
      ],
      workstation: [
        mkCtx("diag", "Mission Control diagnostics", "health inference", () => A().mission.diagnostics()),
        mkCtx("jobs", "Open Job center", "queue", () => A().mission.jobs()),
        mkCtx("activity", "Open Activity Center", "alerts", () => A().mission.activity()),
        mkCtx("logs", "Open Audit / logs", "repair", () => A().audit.open()),
      ],
      memory: [
        mkCtx("search", "Search Memory", "recall", () => A().memory.search()),
        mkCtx("recall", "Ask what Aria remembers", "profile", () => A().memory.recall()),
        mkCtx("export", "Export / browse memories", "list", () => A().memory.open()),
      ],
      browser: [
        mkCtx("url", "Focus browser agent task", "url navigate", () => A().browser.focusTask()),
        mkCtx("research", "Research with Aria", "web", () =>
          A().askAria("Help me research a topic. Ask what I want to look up and how deep to go.")),
      ],
      chat: [
        mkCtx("clear", "Clear conversation", "reset", () => A().chat.clear()),
        mkCtx("new", "New Chat", "thread", () => A().newChat()),
        mkCtx("mini", "Open mini chat", "floating", () => A().shell.miniChat()),
        mkCtx("split", "Split Chat + Planner", "dual", () => {
          if (window.AriaSplitView?.enable) window.AriaSplitView.enable("chat", "planner");
          else A().shell.split();
        }),
      ],
      journal: [
        mkCtx("today", "Journal today", "bujo", () => A().journal.today()),
        mkCtx("search", "Search journal", "find", () => A().journal.search()),
      ],
      calendar: [
        mkCtx("today", "Jump to today", "day", () => A().calendar.today()),
        mkCtx("week", "Calendar week view", "week", () => A().calendar.view("week")),
        mkCtx("timeline", "Calendar timeline", "day ops", () => A().calendar.view("timeline")),
        mkCtx("agenda", "Calendar agenda", "upcoming", () => A().calendar.view("agenda")),
        mkCtx("nl", "Natural language schedule", "add event", () => A().calendar.focusNl()),
        mkCtx("ics", "Focus ICS settings", "subscribe", () => A().calendar.focusIcs()),
        mkCtx("planner", "Open Planner", "tasks", () => A().planner.open()),
        mkCtx("journal", "Open Journal", "notes", () => A().journal.open()),
      ],
      flytying: [
        mkCtx("search", "Search fly patterns", "recipe", () => A().flytying.search()),
        mkCtx("seasonal", "Seasonal patterns", "hatch", () => A().flytying.seasonal()),
      ],
      maker: [
        mkCtx("open", "Open Maker lab", "cad stl", () => A().maker.open()),
        mkCtx("chat", "Ask Aria to design a part", "print", () =>
          A().askAria("Help me design a printable part. Ask for dimensions, material, and constraints.")),
      ],
      projects: [
        mkCtx("new", "Create project", "repo", () => A().projects.create()),
        mkCtx("coding", "Coding mode", "fix", () => A().projects.codingMode()),
      ],
      documents: [
        mkCtx("search", "Search documents", "pdf files", () => A().documents.search()),
        mkCtx("reindex", "Rebuild document search index", "index", () => A().documents.rebuild()),
        mkCtx("upload", "Upload documents", "import pdf", () => A().documents.upload()),
      ],
      connections: [
        mkCtx("search", "Search connections", "graph entity relationship", () => A().connections.search()),
        mkCtx("import", "Import connections for review", "ingest approve", () => A().connections.import()),
        mkCtx("cleanup", "Cleanup connections graph", "prune orphans", () => A().connections.cleanup()),
      ],
      video: [
        mkCtx("studio", "Open Video studio", "animate", () => A().video.studio()),
        mkCtx("gallery", "Video gallery", "clips", () => A().video.open()),
      ],
      dashboard: [
        mkCtx("customize", "Customize dashboard", "widgets", () => A().shell.customizeDash()),
        mkCtx("workspace", "Switch workspace", "layout", () => A().shell.workspaces()),
        mkCtx("welcome", "Refresh welcome card", "resume", () => window.AriaSmartWelcome?.injectIntoDashboard?.()),
      ],
      audit: [
        mkCtx("run", "Run system audit", "health", () => A().audit.run()),
        mkCtx("mc", "Open Mission Control", "ops", () => A().goView("workstation")),
      ],
    };

    const page = map[view] || [];
    const globalCtx = [
      mkCtx("activity", "Open Activity Center", "notifications jobs", () => A().shell.activity(), "Global"),
      mkCtx("workspace", "Workspace layouts", "coding writing", () => A().shell.workspaces(), "Global"),
      mkCtx("split", "Toggle split view", "dual pane", () => A().shell.split(), "Global"),
      mkCtx("mini", "Toggle mini chat", "floating assistant", () => A().shell.miniChat(), "Global"),
      mkCtx("workflow", "Automation & workflows…", "rules skills learned view paths templates", () => A().goView("automation"), "Global"),
      mkCtx("view-paths", "Open View Paths", "navigation shortcuts", () => A().shell.workflows(), "Global"),
      mkCtx("automation", "Open Automation Home", "rules schedules", () => A().goView("automation"), "Global"),
    ];
    const ids = new Set(page.map((c) => c.id));
    reg([...page, ...globalCtx.filter((c) => !ids.has(c.id))]);
  }

  function registerAll() {
    if (!R() || !A()) return;
    // Keep module-registered commands; wipe only catalog-owned prefixes on full rebuild
    const keep = (R().list({ includeUnavailable: true }) || []).filter((c) => c.source && c.source !== "catalog");
    R().clear();
    keep.forEach((c) => R().register(c));
    registerNavigate();
    registerMissionControl();
    registerChatActions();
    registerProductivity();
    registerKnowledge();
    registerMediaDev();
    registerSystem();
    registerShell();
    registerDynamicSelects();
    registerContextCommands();
  }

  window.AriaCommandCatalog = {
    registerAll,
    registerContextCommands,
    currentView,
  };

  // Mark catalog registrations
  const _reg = R()?.register;
  if (_reg && R()) {
    const orig = R().register.bind(R());
    // catalog uses registerMany which calls register — stamp source on next tick after registerAll
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      // Delay slightly so selects/DOM exist
      setTimeout(() => registerAll(), 0);
    });
  } else {
    setTimeout(() => registerAll(), 0);
  }
})();
