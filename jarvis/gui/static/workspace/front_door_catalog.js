/**
 * Front Door catalog — Rooms, Tools, House Controls, Advanced.
 * Jeff-facing names + synonyms. Not architecture vocabulary.
 */
(function () {
  "use strict";

  /** @typedef {{ id: string, kind: 'room'|'tool'|'control'|'advanced', title: string, blurb: string, synonyms?: string[], icon?: string, run: Function }} DoorItem */

  function rooms() {
    const reg = window.AriaWorkspaceRegistry?.rooms || [];
    const blurbs = {
      chat: "Sit down. Talk.",
      health: "How you’re doing today",
      flytying: "The bench by the water",
      mission: "How the house is breathing",
      coding: "Work in progress",
      projects: "Things you’re building",
      documents: "Your private library",
      gallery: "What you’ve made",
      planner: "Today’s page",
      calendar: "The week ahead",
      search: "Look across everything",
      memory: "What we’ve learned together",
      voice: "When you’d rather speak",
      home: "Orientation",
      home_automation: "Lights and the room around you",
      repair: "When something needs care",
      integrity: "Whether things are true",
      automation: "Work that runs itself",
      providers: "Which minds are available",
      journal: "Daily pages and reflections",
      video: "Motion and clips",
      audio: "Sound, speech, and music",
      browser: "The open web",
      maker: "CAD, slice, and print",
      meme: "Quick meme generation",
      vision: "See and describe",
      connections: "How things relate",
      settings: "How the house feels",
      capabilities: "What Aria can load",
      integrations: "Keys and outside services",
      audit: "System audit trail",
      security: "Lock, PIN, and trust",
      actions: "What just happened",
    };
    return reg.map((r) => ({
      id: `room:${r.id}`,
      kind: "room",
      roomId: r.id,
      title: titleForRoom(r),
      blurb: blurbs[r.id] || r.metaphor || r.hero || "",
      synonyms: synonymsForRoom(r),
      icon: iconForRoom(r.id),
      run: () => goRoom(r.id),
    }));
  }

  function titleForRoom(r) {
    const map = {
      chat: "Chat",
      flytying: "Fly Tying",
      health: "Health",
      mission: "Mission Control",
      coding: "Coding",
      projects: "Projects",
      documents: "Documents",
      gallery: "Gallery",
      planner: "Planner",
      calendar: "Calendar",
      search: "Search",
      memory: "Memory",
      voice: "Voice",
      home: "Home",
      home_automation: "Home Automation",
      repair: "Repair",
      integrity: "Integrity",
      automation: "Automation",
      providers: "AI Providers",
      journal: "Journal",
      video: "Video Studio",
      audio: "Audio",
      browser: "Browser",
      maker: "Maker Lab",
      meme: "Meme Studio",
      vision: "Vision",
      connections: "Connections",
      settings: "Settings",
      capabilities: "Capabilities",
      integrations: "Integrations",
      audit: "System Audit",
      security: "Security",
      actions: "Action History",
    };
    return map[r.id] || r.id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function synonymsForRoom(r) {
    const extra = {
      chat: ["talk", "converse", "living room", "conversation", "ask aria"],
      flytying: ["flies", "fly tying", "patterns", "hatch", "tying", "streamside"],
      health: ["doctor", "meds", "vitals", "wellness", "blood pressure", "checkin", "check-in"],
      mission: ["mission control", "systems", "ops", "workstation", "server health", "system health"],
      coding: ["code", "git", "propose", "python", "fix", "engineering"],
      projects: ["project", "workspace", "repo"],
      documents: ["docs", "files", "library", "pdf", "notes"],
      gallery: ["images", "pictures", "artwork", "generate image", "stills"],
      planner: ["tasks", "todo", "today", "plan"],
      calendar: ["schedule", "week", "events", "appointment"],
      search: ["find", "lookup", "federated", "discover"],
      memory: ["remember", "about me", "beliefs", "history"],
      voice: ["speak", "microphone", "tts", "stt", "listen"],
      home: ["dashboard", "foyer", "welcome", "briefing"],
      home_automation: ["ha", "lights", "scenes", "smarthome", "home assistant", "smart home"],
      presence: ["presence", "webcam", "gestures", "face enroll", "camera"],
      repair: ["fix", "restore", "broken", "guided repair"],
      integrity: ["truth", "readiness", "score"],
      automation: ["skills", "workflows", "schedules", "rules"],
      providers: ["models", "ollama", "llm", "cloud", "local model", "model selection"],
      journal: ["bullet journal", "daily", "habits", "reflect", "bujo"],
      video: ["video studio", "clip", "storyboard", "animatediff"],
      audio: ["microphone", "whisper", "transcribe", "podcast", "music"],
      browser: ["web", "playwright", "browse", "research"],
      maker: ["cad", "stl", "print", "3d", "slicer"],
      meme: ["memes", "caption"],
      vision: ["ocr", "describe", "see", "screenshot"],
      connections: ["graph", "relationships", "knowledge graph"],
      settings: ["preferences", "appearance", "theme", "atmosphere"],
      capabilities: ["extensions", "plugins", "modules"],
      integrations: ["api keys", "openai", "gemini", "anthropic"],
      audit: ["system audit", "install check"],
      security: ["pin", "lock", "trusted devices"],
      actions: ["history", "undo", "what happened"],
    };
    return [r.id, r.metaphor, r.hero, r.viewId, ...(extra[r.id] || [])].filter(Boolean);
  }

  function iconForRoom(id) {
    const map = {
      chat: "◇",
      health: "♡",
      flytying: "∿",
      mission: "◎",
      coding: "</>",
      projects: "▣",
      documents: "☰",
      gallery: "▣",
      planner: "▤",
      calendar: "▦",
      search: "⌕",
      memory: "◎",
      voice: "♩",
      home: "⌂",
      home_automation: "⌂",
      repair: "⚒",
      integrity: "✓",
      automation: "↻",
      providers: "⬡",
      journal: "▤",
      video: "▶",
      audio: "♪",
      browser: "🌐",
      maker: "⚙",
      meme: "▣",
      vision: "◉",
      connections: "⚭",
      settings: "⚙",
      capabilities: "◇",
      integrations: "⬡",
      audit: "☰",
      security: "🔒",
      actions: "↺",
    };
    return map[id] || "·";
  }

  function goRoom(roomId) {
    const acts = (window.AriaWorkspaceRegistry?.activities || []).filter((a) => a.primaryRoom === roomId);
    const preferred = acts.find((a) => a.id === roomId) || acts[0];
    if (preferred?.id) {
      window.AriaActivityEngine?.start?.(preferred.id, { confirmHighStakes: false });
    } else {
      /* Rooms without an Activity recipe (Journal, Settings, Browser, …) still need
         view + hash sync. AriaHouse.enter alone left the previous Room’s hash
         (e.g. Journal showing under #search) and stale activity chrome. */
      const room = window.AriaWorkspaceRegistry?.room?.(roomId);
      const viewId = room?.viewId || roomId;
      window.switchToView?.(viewId);
      document.body.dataset.activity = roomId;
      const label = document.getElementById("wsActivityLabel");
      if (label) label.textContent = titleForRoom(room || { id: roomId });
      const recipe = document.getElementById("wsActivityRecipe");
      if (recipe) {
        const blurb = room?.metaphor || room?.hero || "";
        recipe.textContent = blurb;
        recipe.title = blurb;
      }
    }
    try {
      window.AriaFrontDoor?.recordVisit?.(roomId);
    } catch (_) {
      /* ignore */
    }
  }

  function tools() {
    const list = window.AriaWorkspaceRegistry?.tools || [];
    const extra = [
      {
        id: "tool:image_gen",
        kind: "tool",
        title: "Image Generator",
        blurb: "Create stills",
        synonyms: ["comfy", "generate image", "draw", "picture"],
        icon: "▣",
        run: () => {
          goRoom("gallery");
        },
      },
      {
        id: "tool:jobs",
        kind: "tool",
        title: "Job Center",
        blurb: "Running work",
        synonyms: ["jobs", "queue", "builds", "job center"],
        icon: "☰",
        run: () => {
          window.jarvisJobs?.openJobCenter?.() ||
            window.AriaActions?.mission?.jobs?.() ||
            document.getElementById("jobCenterBtn")?.click();
        },
      },
    ];
    const fromReg = list.map((t) => ({
      id: `tool:${t.id}`,
      kind: "tool",
      title: t.label || t.id,
      blurb: `Tool · ${t.surface || "when needed"}`,
      synonyms: [t.id, t.label, t.invoke, t.viewId].filter(Boolean),
      icon: "·",
      run: () => window.AriaWorkspaceTools?.open?.(t.id),
    }));
    return [...fromReg, ...extra];
  }

  function clickId(id) {
    const el = document.getElementById(id);
    if (el) {
      el.click();
      return true;
    }
    return false;
  }

  function controls() {
    /** @type {DoorItem[]} */
    return [
      {
        id: "ctrl:restart",
        kind: "control",
        title: "Restart Server",
        blurb: "Bring Aria’s server back up",
        synonyms: ["reboot", "restart aria", "restart jarvis", "restart server"],
        icon: "↻",
        run: () => {
          if (typeof window.restartJarvisServer === "function") {
            Promise.resolve(window.restartJarvisServer()).catch(() => {});
            return;
          }
          if (!clickId("restartServerBtn")) {
            fetch("/api/jarvis/restart-server", { method: "POST" }).catch(() => {});
          }
        },
      },
      {
        id: "ctrl:providers",
        kind: "control",
        title: "AI Providers",
        blurb: "Models and routing",
        synonyms: ["providers", "ollama", "openai", "models", "llm"],
        icon: "⬡",
        run: () => goRoom("providers"),
      },
      {
        id: "ctrl:model",
        kind: "control",
        title: "Model Selection",
        blurb: "Choose the active model",
        synonyms: ["model", "switch model", "local model", "cloud model"],
        icon: "⬡",
        run: () => {
          goRoom("providers");
          setTimeout(() => document.getElementById("chatComposerModelSelect")?.focus?.(), 200);
        },
      },
      {
        id: "ctrl:uncensored",
        kind: "control",
        title: "Uncensored Mode",
        blurb: "Toggle local uncensored",
        synonyms: ["nsfw", "uncensored", "safe mode", "censorship"],
        icon: "◌",
        run: () => {
          window.AriaActions?.system?.uncensored?.() || clickId("uncensoredToggle");
        },
      },
      {
        id: "ctrl:theme",
        kind: "control",
        title: "Appearance / Theme",
        blurb: "Look and feel",
        synonyms: ["theme", "dark", "light", "appearance", "colors"],
        icon: "☀",
        run: () => window.AriaActions?.system?.theme?.() || clickId("themeToggle"),
      },
      {
        id: "ctrl:voice",
        kind: "control",
        title: "Voice Settings",
        blurb: "Speaking and listening",
        synonyms: ["voice settings", "tts", "stt", "microphone"],
        icon: "♩",
        run: () => goRoom("voice"),
      },
      {
        id: "ctrl:audio",
        kind: "control",
        title: "Audio",
        blurb: "Audio studio",
        synonyms: ["sound", "audio studio", "speakers"],
        icon: "♪",
        run: () => window.switchToView?.("audio"),
      },
      {
        id: "ctrl:settings",
        kind: "control",
        title: "Settings",
        blurb: "House preferences",
        synonyms: ["preferences", "settings", "config"],
        icon: "⚙",
        run: () => window.switchToView?.("settings") || window.initSettingsHome?.(),
      },
      {
        id: "ctrl:notifications",
        kind: "control",
        title: "Notifications",
        blurb: "Alerts and inbox",
        synonyms: ["alerts", "inbox", "notify"],
        icon: "⚑",
        run: () => window.AriaActivity?.open?.() || window.AriaNotificationsInbox?.open?.(),
      },
      {
        id: "ctrl:security",
        kind: "control",
        title: "Security",
        blurb: "PIN and trust",
        synonyms: ["pin", "lock", "security", "privacy"],
        icon: "⌖",
        run: () => window.switchToView?.("security"),
      },
      {
        id: "ctrl:repair",
        kind: "control",
        title: "Repair",
        blurb: "Guided restoration",
        synonyms: ["repair", "fix aria"],
        icon: "⚒",
        run: () => goRoom("repair"),
      },
      {
        id: "ctrl:integrity",
        kind: "control",
        title: "Production Integrity",
        blurb: "Truth score",
        synonyms: ["integrity", "readiness", "truth score"],
        icon: "✓",
        run: () => goRoom("integrity"),
      },
      {
        id: "ctrl:gpu",
        kind: "control",
        title: "GPU / Free VRAM",
        blurb: "Graphics memory",
        synonyms: ["gpu", "vram", "nvidia", "free vram"],
        icon: "▣",
        run: () => window.AriaActions?.system?.freeVram?.() || clickId("freeVramBtn"),
      },
      {
        id: "ctrl:memory",
        kind: "control",
        title: "Memory Controls",
        blurb: "What Aria knows",
        synonyms: ["memory settings", "forget", "about me"],
        icon: "◎",
        run: () => goRoom("memory"),
      },
      {
        id: "ctrl:layouts",
        kind: "control",
        title: "Workspace Layouts",
        blurb: "Saved arrangements",
        synonyms: ["layout", "layouts", "workspace layout", "panels"],
        icon: "▦",
        run: () => {
          clickId("workspaceLayoutsBtn") ||
            window.AriaWorkspaceLayouts?.open?.() ||
            window.openWorkspaceLayouts?.() ||
            goRoom("settings");
        },
      },
      {
        id: "ctrl:performance",
        kind: "control",
        title: "Performance",
        blurb: "Runtime health",
        synonyms: ["performance", "latency", "slow", "throughput"],
        icon: "◎",
        run: () => {
          goRoom("mission");
          setTimeout(() => window.switchMcTab?.("performance"), 200);
        },
      },
      {
        id: "ctrl:databases",
        kind: "control",
        title: "Database tools",
        blurb: "Stores and indexes",
        synonyms: ["database", "databases", "sqlite", "index"],
        icon: "☰",
        run: () => {
          goRoom("mission");
          setTimeout(() => window.switchMcTab?.("databases"), 200);
        },
      },
      {
        id: "ctrl:diagnostics",
        kind: "control",
        title: "Diagnostics",
        blurb: "Deep system checks",
        synonyms: ["diagnostics", "diagnose", "health check"],
        icon: "✓",
        run: () => {
          goRoom("mission");
          setTimeout(() => window.switchMcTab?.("diagnostics"), 200);
        },
      },
    ];
  }

  function advanced() {
    return [
      {
        id: "adv:audit",
        kind: "advanced",
        title: "System / Logs",
        blurb: "Audit trail",
        synonyms: ["logs", "audit", "diagnostics", "debug"],
        icon: "☰",
        run: () => window.switchToView?.("audit"),
      },
      {
        id: "adv:capabilities",
        kind: "advanced",
        title: "Capabilities",
        blurb: "What Aria can do",
        synonyms: ["capabilities", "features"],
        icon: "◇",
        run: () => window.switchToView?.("capabilities"),
      },
      {
        id: "adv:integrations",
        kind: "advanced",
        title: "Integrations",
        blurb: "Connected services",
        synonyms: ["integrations", "connections", "apis"],
        icon: "⬡",
        run: () => window.switchToView?.("integrations") || window.switchToView?.("connections"),
      },
      {
        id: "adv:mission-deep",
        kind: "advanced",
        title: "Mission Control (deep)",
        blurb: "Ops presence",
        synonyms: ["diagnostics", "performance", "latency"],
        icon: "◎",
        run: () => goRoom("mission"),
      },
      {
        id: "adv:palette",
        kind: "advanced",
        title: "Legacy Command Palette",
        blurb: "Power user commands",
        synonyms: ["commands", "palette", "actions"],
        icon: "⌘",
        run: () => window.openCommandPalette?.(),
      },
      {
        id: "adv:browser",
        kind: "advanced",
        title: "Browser",
        blurb: "Agent browser",
        synonyms: ["playwright", "web", "browse"],
        icon: "◌",
        run: () => window.switchToView?.("browser"),
      },
      {
        id: "adv:maker",
        kind: "advanced",
        title: "Maker Lab",
        blurb: "CAD and making",
        synonyms: ["maker", "stl", "print", "cad"],
        icon: "⚒",
        run: () => window.switchToView?.("maker"),
      },
    ];
  }

  function all() {
    return [...rooms(), ...tools(), ...controls(), ...advanced()];
  }

  function normalize(s) {
    return String(s || "")
      .toLowerCase()
      .replace(/[^a-z0-9\s/+<>]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function scoreItem(item, q) {
    if (!q) return 0;
    const nq = normalize(q);
    const hay = normalize([item.title, item.blurb, ...(item.synonyms || [])].join(" "));
    if (hay === nq || normalize(item.title) === nq) return 100;
    if (hay.startsWith(nq) || normalize(item.title).startsWith(nq)) return 90;
    if (hay.includes(` ${nq} `) || hay.includes(nq)) return 70;
    const parts = nq.split(" ").filter(Boolean);
    let hit = 0;
    parts.forEach((p) => {
      if (hay.includes(p)) hit += 1;
    });
    if (hit && hit === parts.length) return 60;
    if (hit) return 20 + hit * 10;
    return 0;
  }

  function match(query) {
    const q = String(query || "").trim();
    const items = all();
    if (!q) return { rooms: rooms(), tools: tools().slice(0, 12), controls: controls(), advanced: advanced(), results: [] };

    /* Natural language intents */
    const nl = normalize(q);
    const intentRoutes = [
      { re: /\b(tie flies|fly tying|tying)\b/, id: "room:flytying" },
      { re: /\b(my health|health|doctor|blood pressure)\b/, id: "room:health" },
      { re: /\b(mission control|system health|check server)\b/, id: "room:mission" },
      { re: /\b(restart (aria|jarvis|server)|reboot)\b/, id: "ctrl:restart" },
      { re: /\b(uncensored|nsfw)\b/, id: "ctrl:uncensored" },
      { re: /\b(local model|switch.*model|change model)\b/, id: "ctrl:model" },
      { re: /\b(providers|ai providers)\b/, id: "ctrl:providers" },
      { re: /\b(documents|my documents|library)\b/, id: "room:documents" },
      { re: /\b(gallery|images|pictures)\b/, id: "room:gallery" },
      { re: /\b(let'?s code|coding|write code)\b/, id: "room:coding" },
      { re: /\b(repair|fix aria)\b/, id: "ctrl:repair" },
      { re: /\b(job center|jobs? queue|running (jobs|work))\b/, id: "tool:jobs" },
      { re: /\b(layout|layouts|workspace layout)\b/, id: "ctrl:layouts" },
      { re: /\b(database|databases|sqlite)\b/, id: "ctrl:databases" },
      { re: /\b(performance|latency)\b/, id: "ctrl:performance" },
      { re: /\b(diagnostics?)\b/, id: "ctrl:diagnostics" },
      { re: /\b(planner|today'?s? (tasks|page))\b/, id: "room:planner" },
      { re: /\b(memory|what do you know)\b/, id: "room:memory" },
      { re: /\b(search|find)\b/, id: "room:search" },
    ];
    for (const route of intentRoutes) {
      if (route.re.test(nl)) {
        const hit = items.find((i) => i.id === route.id);
        if (hit) return { rooms: [], tools: [], controls: [], advanced: [], results: [{ ...hit, _score: 120, _intent: true }] };
      }
    }

    const scored = items
      .map((i) => ({ ...i, _score: scoreItem(i, q) }))
      .filter((i) => i._score > 0)
      .sort((a, b) => b._score - a._score || a.title.localeCompare(b.title));
    return { rooms: [], tools: [], controls: [], advanced: [], results: scored.slice(0, 40) };
  }

  window.AriaFrontDoorCatalog = {
    rooms,
    tools,
    controls,
    advanced,
    all,
    match,
    goRoom,
    version: "6.1.0",
  };
})();
