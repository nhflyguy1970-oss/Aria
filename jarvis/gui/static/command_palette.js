/** Global command palette — Ctrl/Cmd+K (nav + actions). */
(function () {
  const RECENT_KEY = "aria_cmd_palette_recent";
  const MAX_RECENT = 8;
  const MAX_VISIBLE = 40;

  /** @type {{ id: string, label: string, group: string, keywords?: string, run: () => void, hint?: string }[]} */
  let commands = [];
  let filtered = [];
  let activeIndex = 0;
  let openerEl = null;

  function $(id) {
    return document.getElementById(id);
  }

  function loadRecent() {
    try {
      const raw = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
      return Array.isArray(raw) ? raw.filter((x) => typeof x === "string") : [];
    } catch {
      return [];
    }
  }

  function pushRecent(id) {
    const next = [id, ...loadRecent().filter((x) => x !== id)].slice(0, MAX_RECENT);
    try {
      localStorage.setItem(RECENT_KEY, JSON.stringify(next));
    } catch {
      /* ignore quota */
    }
  }

  function score(cmd, q) {
    if (!q) return 1;
    const hay = `${cmd.label} ${cmd.group} ${cmd.keywords || ""} ${cmd.id}`.toLowerCase();
    const needle = q.toLowerCase().trim();
    if (!needle) return 1;
    if (hay === needle) return 100;
    if (hay.startsWith(needle)) return 80;
    if (hay.includes(needle)) return 50;
    const parts = needle.split(/\s+/).filter(Boolean);
    if (parts.every((p) => hay.includes(p))) return 35;
    // simple fuzzy: all chars in order
    let i = 0;
    for (const ch of hay) {
      if (ch === needle[i]) i += 1;
      if (i >= needle.length) return 20;
    }
    return 0;
  }

  function goView(view) {
    window.switchToView?.(view);
  }

  function goMc(tab) {
    window.switchToView?.("workstation");
    setTimeout(() => window.switchMcTab?.(tab), 50);
  }

  function openModal(id) {
    const el = $(id);
    if (!el) return;
    el.classList.remove("hidden");
  }

  function buildCommands() {
    const views = [
      ["chat", "Chat", "conversation ai"],
      ["dashboard", "Dashboard", "home overview"],
      ["workstation", "Mission Control", "mc operator acm"],
      ["planner", "Planner", "tasks todo"],
      ["calendar", "Calendar", "schedule"],
      ["flytying", "Fly tying", "flies patterns"],
      ["projects", "Projects", "repos"],
      ["maker", "Maker lab", "cad stl print"],
      ["browser", "Browser agent", "playwright web"],
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
      ["actions", "Actions / report", "checklist"],
    ];

    const nav = views.map(([id, label, keywords]) => ({
      id: `nav:${id}`,
      label: `Go to ${label}`,
      group: "Navigate",
      keywords,
      hint: "View",
      run: () => goView(id),
    }));

    const mcTabs = [
      "overview", "routing", "timeline", "intent_analytics", "release", "connection",
      "applications", "inference", "memory", "knowledge", "databases", "hardware",
      "jobs", "activity", "performance", "settings", "recovery",
    ].map((tab) => ({
      id: `mc:${tab}`,
      label: `Mission Control · ${tab.replace(/_/g, " ")}`,
      group: "Mission Control",
      keywords: `mc ${tab}`,
      hint: "MC",
      run: () => goMc(tab),
    }));

    const actions = [
      {
        id: "act:focus-chat",
        label: "Focus chat input",
        group: "Actions",
        keywords: "message type ask",
        run: () => {
          goView("chat");
          setTimeout(() => $("messageInput")?.focus(), 60);
        },
      },
      {
        id: "act:job-center",
        label: "Open job center",
        group: "Actions",
        keywords: "background jobs media",
        run: () => {
          $("jobCenterBtn")?.click();
          if ($("jobCenterModal")?.classList.contains("hidden")) openModal("jobCenterModal");
        },
      },
      {
        id: "act:settings",
        label: "Open voice & chat settings",
        group: "Actions",
        keywords: "preferences tts",
        run: () => {
          $("settingsBtn")?.click();
          openModal("settingsModal");
        },
      },
      {
        id: "act:shortcuts",
        label: "Open keyboard shortcuts",
        group: "Actions",
        keywords: "help keys",
        run: () => {
          $("shortcutsBtn")?.click();
          openModal("shortcutsModal");
        },
      },
      {
        id: "act:upgrade",
        label: "Open upgrade wizard",
        group: "Actions",
        keywords: "update patch",
        run: () => {
          $("upgradeWizardBtn")?.click();
          openModal("upgradeWizardModal");
        },
      },
      {
        id: "act:ha-setup",
        label: "Open smart home setup",
        group: "Actions",
        keywords: "home assistant ha",
        run: () => openModal("haSetupModal"),
      },
      {
        id: "act:generate-image",
        label: "Generate image (Gallery)",
        group: "AI",
        keywords: "comfy sd flux",
        run: () => {
          goView("gallery");
          setTimeout(() => $("galleryPromptInput")?.focus(), 80);
        },
      },
      {
        id: "act:ask-status",
        label: "Ask Aria: status",
        group: "AI",
        keywords: "health services",
        run: () => {
          goView("chat");
          window.sendMessage?.("status");
        },
      },
      {
        id: "act:voice-smoke",
        label: "Run voice smoke test",
        group: "AI",
        keywords: "mic stt",
        run: () => {
          goView("voice");
          $("voiceSmokeBtn")?.click();
        },
      },
      {
        id: "act:router-warm",
        label: "Warm model router",
        group: "AI",
        keywords: "ollama models",
        run: () => $("routerWarmBtn")?.click(),
      },
      {
        id: "act:reload-ui",
        label: "Reload UI",
        group: "System",
        keywords: "refresh restart spa",
        hint: "Ctrl+Shift+R",
        run: () => window.reloadJarvisUi?.(),
      },
      {
        id: "act:reset-sidebar",
        label: "Expand all sidebar sections",
        group: "System",
        keywords: "layout",
        run: () => window.resetSidebarLayout?.(),
      },
    ];

    function focusSearch(view, inputId, clickBtnId) {
      return () => {
        goView(view);
        setTimeout(() => {
          const el = $(inputId);
          el?.focus();
          el?.select?.();
          if (clickBtnId) $(clickBtnId)?.focus?.();
        }, 80);
      };
    }

    const search = [
      {
        id: "search:journal",
        label: "Search journal",
        group: "Search",
        keywords: "bujo find filter",
        run: focusSearch("journal", "journalSearch"),
      },
      {
        id: "search:memory",
        label: "Search memory",
        group: "Search",
        keywords: "recall find filter",
        run: focusSearch("memory", "memorySearch"),
      },
      {
        id: "search:documents",
        label: "Search documents",
        group: "Search",
        keywords: "library files pdf",
        run: focusSearch("documents", "documentsSearchInput"),
      },
      {
        id: "search:flytying",
        label: "Search fly patterns",
        group: "Search",
        keywords: "tying recipes",
        run: focusSearch("flytying", "flytyingSearchInput"),
      },
      {
        id: "search:mc-routing",
        label: "Search Mission Control routing",
        group: "Search",
        keywords: "intent handler prompts",
        run: () => {
          goMc("routing");
          setTimeout(() => $("mcRoutingSearch")?.focus(), 200);
        },
      },
    ];

    commands = [...nav, ...mcTabs, ...actions, ...search];
  }

  let contentHits = [];
  let searchSeq = 0;
  let searchTimer = null;

  function hitToCommand(hit, idx) {
    const source = hit.source_type || "knowledge";
    const label = hit.title || hit.excerpt || "Result";
    const excerpt = (hit.excerpt || "").replace(/\s+/g, " ").trim().slice(0, 72);
    const id = `hit:${source}:${hit.location || hit.title || idx}`;
    return {
      id,
      label: excerpt ? `${label} — ${excerpt}` : String(label),
      group: "Results",
      hint: hit.source_label || source,
      keywords: `${hit.excerpt || ""} ${hit.location || ""}`,
      run: () => openHit(hit),
    };
  }

  function openHit(hit) {
    const type = hit.source_type || "";
    const loc = String(hit.location || "");
    if (type === "conversation" || type.includes("memory") || loc.includes("acm") || loc === "memory" || loc === "profile") {
      goView("memory");
      setTimeout(() => {
        const q = (hit.excerpt || hit.title || "").slice(0, 40);
        const el = $("memorySearch");
        if (el && q) {
          el.value = q;
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.focus();
        }
      }, 80);
      return;
    }
    if (type === "notes" || type === "journal" || loc.includes("journal")) {
      goView("journal");
      setTimeout(() => {
        const el = $("journalSearch");
        const q = (hit.title || "").replace(/\.[^.]+$/, "");
        if (el) {
          el.value = q;
          el.focus();
          $("journalSearchBtn")?.click();
        }
      }, 80);
      return;
    }
    if (type === "document_library" || type.includes("document")) {
      goView("documents");
      setTimeout(() => {
        const el = $("documentsSearchInput");
        if (el) {
          el.value = hit.title || hit.query || "";
          el.focus();
          $("documentsSearchBtn")?.click();
        }
      }, 80);
      return;
    }
    if (type === "code_index" || type === "git_repository") {
      goView("projects");
      window.showAriaToast?.(loc || hit.title || "Open in projects / coding", "info");
      return;
    }
    goView("memory");
    window.showAriaToast?.((hit.excerpt || hit.title || "").slice(0, 120), "info");
  }

  function filterCommands(q) {
    const scored = commands
      .map((c) => ({ c, s: score(c, q) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s || a.c.label.localeCompare(b.c.label));

    if (!q.trim()) {
      contentHits = [];
      const recent = loadRecent();
      const byId = new Map(commands.map((c) => [c.id, c]));
      const recentCmds = recent.map((id) => byId.get(id)).filter(Boolean);
      const rest = scored.map((x) => x.c).filter((c) => !recent.includes(c.id));
      filtered = [...recentCmds, ...rest].slice(0, MAX_VISIBLE);
      return;
    }
    const cmdHits = scored.map((x) => x.c);
    filtered = [...contentHits, ...cmdHits].slice(0, MAX_VISIBLE);
  }

  async function fetchContentHits(q) {
    const needle = q.trim();
    if (needle.length < 2) {
      contentHits = [];
      return;
    }
    const seq = ++searchSeq;
    try {
      const res = await fetch(`/api/knowledge/search?q=${encodeURIComponent(needle)}&limit=8`);
      const data = await res.json().catch(() => ({}));
      if (seq !== searchSeq) return;
      const hits = Array.isArray(data.hits) ? data.hits : [];
      contentHits = hits.slice(0, 8).map((h, i) => hitToCommand(h, i));
    } catch {
      if (seq === searchSeq) contentHits = [];
    }
  }

  function renderList() {
    const list = $("commandPaletteList");
    const empty = $("commandPaletteEmpty");
    if (!list) return;
    list.innerHTML = "";
    if (!filtered.length) {
      if (empty) empty.classList.remove("hidden");
      list.setAttribute("aria-activedescendant", "");
      return;
    }
    if (empty) empty.classList.add("hidden");
    let lastGroup = "";
    filtered.forEach((cmd, i) => {
      if (cmd.group !== lastGroup) {
        lastGroup = cmd.group;
        const head = document.createElement("li");
        head.className = "command-palette-group";
        head.setAttribute("role", "presentation");
        head.textContent = cmd.group;
        list.appendChild(head);
      }
      const li = document.createElement("li");
      li.id = `commandPaletteItem-${i}`;
      li.className = `command-palette-item${i === activeIndex ? " active" : ""}`;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === activeIndex ? "true" : "false");
      li.dataset.index = String(i);
      const recent = !($("commandPaletteInput")?.value || "").trim() && loadRecent().includes(cmd.id);
      li.innerHTML = `<span class="command-palette-label">${escapeHtml(cmd.label)}${recent ? ' <span class="command-palette-recent">Recent</span>' : ""}</span><span class="command-palette-meta">${escapeHtml(cmd.hint || cmd.group)}</span>`;
      li.addEventListener("mouseenter", () => {
        activeIndex = i;
        syncActive();
      });
      li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        runIndex(i);
      });
      list.appendChild(li);
    });
    syncActive();
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function syncActive() {
    const list = $("commandPaletteList");
    if (!list) return;
    list.querySelectorAll(".command-palette-item").forEach((el) => {
      const i = Number(el.dataset.index);
      const on = i === activeIndex;
      el.classList.toggle("active", on);
      el.setAttribute("aria-selected", on ? "true" : "false");
    });
    const active = $(`commandPaletteItem-${activeIndex}`);
    if (active) {
      list.setAttribute("aria-activedescendant", active.id);
      active.scrollIntoView({ block: "nearest" });
    }
  }

  function runIndex(i) {
    const cmd = filtered[i];
    if (!cmd) return;
    pushRecent(cmd.id);
    closePalette();
    try {
      cmd.run();
    } catch (e) {
      window.showAriaToast?.(String(e.message || e), "err");
    }
  }

  function isOpen() {
    return !$("commandPaletteModal")?.classList.contains("hidden");
  }

  function openPalette(fromEl) {
    buildCommands();
    contentHits = [];
    openerEl = fromEl || document.activeElement;
    const modal = $("commandPaletteModal");
    const input = $("commandPaletteInput");
    if (!modal || !input) return;
    modal.classList.remove("hidden");
    input.value = "";
    activeIndex = 0;
    filterCommands("");
    renderList();
    setTimeout(() => input.focus(), 0);
  }

  function closePalette() {
    const modal = $("commandPaletteModal");
    if (!modal) return;
    modal.classList.add("hidden");
    clearTimeout(searchTimer);
    searchTimer = null;
    const restore = openerEl;
    openerEl = null;
    if (restore && typeof restore.focus === "function") {
      try {
        restore.focus();
      } catch {
        /* ignore */
      }
    }
  }

  function onInput() {
    activeIndex = 0;
    const q = $("commandPaletteInput")?.value || "";
    filterCommands(q);
    renderList();
    clearTimeout(searchTimer);
    if (q.trim().length < 2) {
      contentHits = [];
      return;
    }
    searchTimer = setTimeout(async () => {
      await fetchContentHits(q);
      if (($("commandPaletteInput")?.value || "") !== q) return;
      filterCommands(q);
      renderList();
    }, 160);
  }

  function init() {
    buildCommands();
    $("commandPaletteBtn")?.addEventListener("click", (e) => openPalette(e.currentTarget));
    $("commandPaletteCloseBtn")?.addEventListener("click", closePalette);
    $("commandPaletteModal")?.addEventListener("click", (e) => {
      if (e.target?.id === "commandPaletteModal") closePalette();
    });
    $("commandPaletteInput")?.addEventListener("input", onInput);
    $("commandPaletteInput")?.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (!filtered.length) return;
        activeIndex = (activeIndex + 1) % filtered.length;
        syncActive();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (!filtered.length) return;
        activeIndex = (activeIndex - 1 + filtered.length) % filtered.length;
        syncActive();
      } else if (e.key === "Enter") {
        e.preventDefault();
        runIndex(activeIndex);
      } else if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        closePalette();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      if (String(e.key).toLowerCase() !== "k") return;
      e.preventDefault();
      if (isOpen()) closePalette();
      else openPalette(document.activeElement);
    });
  }

  window.openAriaCommandPalette = openPalette;
  window.closeAriaCommandPalette = closePalette;
  window.registerAriaCommand = (cmd) => {
    if (!cmd?.id || !cmd.label || typeof cmd.run !== "function") return;
    commands = commands.filter((c) => c.id !== cmd.id);
    commands.push(cmd);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
