/** Command Palette — Aria structured OS launcher (orchestrator). Catalog lives in registry + modules. */
(function () {
  "use strict";

  const RECENT_KEY = "aria_cmd_palette_recent";
  const PIN_KEY = "aria_cmd_palette_pins";
  const USAGE_KEY = "aria_cmd_palette_usage";
  const MAX_RECENT = 10;
  const MAX_VISIBLE = 40;

  /** @type {object[]} */
  let filtered = [];
  let activeIndex = 0;
  let openerEl = null;
  let contentHits = [];
  let searchSeq = 0;
  let searchTimer = null;
  let searchStatus = "idle"; // idle | searching | ready | empty | error
  let searchError = "";
  let helpOpen = false;

  function $(id) {
    return document.getElementById(id);
  }

  function registry() {
    return window.AriaCommandRegistry;
  }

  function loadRecent() {
    const fromPrefs = window.AriaUiPrefs?.get?.("recentCommands");
    if (Array.isArray(fromPrefs) && fromPrefs.length) return fromPrefs;
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
      /* ignore */
    }
    window.AriaUiPrefs?.set?.("recentCommands", next);
    window.AriaUiPrefs?.bumpUsage?.("commandUsage", id);
    try {
      const usage = JSON.parse(localStorage.getItem(USAGE_KEY) || "{}");
      usage[id] = (usage[id] || 0) + 1;
      localStorage.setItem(USAGE_KEY, JSON.stringify(usage));
    } catch {
      /* ignore */
    }
  }

  function loadPins() {
    const fromPrefs = window.AriaUiPrefs?.get?.("pinnedCommands");
    if (Array.isArray(fromPrefs)) return fromPrefs;
    try {
      const raw = JSON.parse(localStorage.getItem(PIN_KEY) || "[]");
      return Array.isArray(raw) ? raw : [];
    } catch {
      return [];
    }
  }

  function togglePin(id) {
    const pins = loadPins();
    const next = pins.includes(id) ? pins.filter((x) => x !== id) : [id, ...pins].slice(0, 12);
    try {
      localStorage.setItem(PIN_KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
    window.AriaUiPrefs?.set?.("pinnedCommands", next);
    announce(next.includes(id) ? "Pinned" : "Unpinned");
    return next;
  }

  function loadUsage() {
    const fromPrefs = window.AriaUiPrefs?.get?.("commandUsage");
    if (fromPrefs && typeof fromPrefs === "object") return fromPrefs;
    try {
      return JSON.parse(localStorage.getItem(USAGE_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function announce(msg) {
    const live = $("commandPaletteLive");
    if (live) live.textContent = msg || "";
  }

  function setSearchStatus(status, detail) {
    searchStatus = status;
    searchError = detail || "";
    const el = $("commandPaletteStatus");
    if (!el) return;
    const map = {
      idle: "",
      searching: "Searching knowledge…",
      ready: detail || "",
      empty: "No knowledge matches",
      error: detail || "Knowledge search unavailable",
    };
    el.textContent = map[status] || "";
    el.classList.toggle("hidden", !el.textContent);
    el.classList.toggle("is-error", status === "error");
    el.classList.toggle("is-loading", status === "searching");
    const retry = $("commandPaletteRetryBtn");
    if (retry) retry.classList.toggle("hidden", status !== "error");
    if (status === "searching") announce("Searching knowledge");
    else if (status === "error") announce(el.textContent);
    else if (status === "empty") announce("No knowledge matches");
    else if (status === "ready" && detail) announce(detail);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function openHit(hit) {
    const open = hit.raw?.open || hit.open || {};
    const qPreserve = open.query || hit.query || "";
    const type = hit.source_type || open.view || "";
    const loc = String(hit.location || open.location || "");
    const rawId = hit.raw?.id || open.id || (String(hit.title || "").match(/^(exp_|mem_|acm)/) ? hit.title : "");
    const A = window.AriaActions;

    if (open.type === "open_layouts" || open.action === "open_layouts") {
      window.AriaLayouts?.openModal?.() || window.AriaWorkspaces?.openModal?.();
      return;
    }
    if (open.type === "open_notifications" || open.action === "open_notifications") {
      window.openNotifications?.(open.filter) || window.AriaNotifications?.open?.(open.filter) || window.AriaActivity?.open?.();
      return;
    }
    if (open.type === "apply_layout" || open.action === "apply_layout") {
      const lid = open.layout_id || loc;
      if (lid) window.applyAriaLayout?.(lid, { confirm: false, quiet: true });
      else window.AriaLayouts?.openModal?.();
      return;
    }

    function prefill(sel, q, btn) {
      setTimeout(() => {
        const el = typeof sel === "string" ? $(sel.replace(/^#/, "")) || document.querySelector(sel) : sel;
        if (el && q) {
          el.value = q;
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.focus();
        }
        if (btn) $(btn.replace(/^#/, ""))?.click();
      }, 80);
    }

    if (open.handoff === "web_search" || type === "web") {
      A?.askAria?.(qPreserve || hit.title || "web search", { autoSend: true, switchView: true });
      return;
    }
    if (open.view === "search") {
      window.switchToView?.("search");
      setTimeout(() => {
        const el = $("searchHomeInput");
        if (el) {
          el.value = qPreserve || hit.title || "";
          window.initSearchHome?.(true);
        }
      }, 60);
      return;
    }
    if (type === "conversation" || type === "memory" || type.includes("memory") || loc.includes("acm") || loc === "memory" || loc === "profile" || open.view === "memory") {
      A?.memory?.open?.();
      prefill("memorySearch", (qPreserve || hit.excerpt || hit.title || "").slice(0, 48));
      setTimeout(async () => {
        try {
          await window.loadMemoryBrowser?.();
        } catch {
          /* ignore */
        }
        if (rawId) {
          const item = document.querySelector(`.memory-item[data-id="${CSS.escape(String(rawId))}"]`);
          if (item) {
            item.classList.add("memory-item--flash");
            item.scrollIntoView({ block: "nearest", behavior: "smooth" });
            setTimeout(() => item.classList.remove("memory-item--flash"), 2200);
          }
        }
      }, 100);
      return;
    }
    if (type === "notes" || type === "journal" || loc.includes("journal") || open.view === "journal") {
      A?.journal?.open?.();
      prefill("journalSearch", qPreserve || (hit.title || "").replace(/\.[^.]+$/, ""), "journalSearchBtn");
      return;
    }
    if (type === "document_library" || type === "documents" || type.includes("document") || open.view === "documents") {
      A?.documents?.open?.();
      prefill("documentsSearchInput", qPreserve || hit.title || "", "documentsSearchBtn");
      return;
    }
    if (type.includes("connection") || type === "entity" || type === "graph" || type === "connections" || open.view === "connections") {
      A?.connections?.open?.();
      prefill("connectionsSearchInput", qPreserve || hit.title || hit.excerpt || "", "connectionsSearchBtn");
      return;
    }
    if (type === "code" || type === "code_index" || type === "git_repository" || open.view === "coding") {
      window.switchToView?.("coding");
      window.showAriaToast?.(loc || hit.title || "Open in Coding", "info");
      return;
    }
    if (type === "planner" || open.view === "planner") {
      window.switchToView?.("planner");
      prefill("plannerSearchInput", qPreserve || hit.title || "");
      return;
    }
    if (type === "calendar" || open.view === "calendar") {
      window.switchToView?.("calendar");
      return;
    }
    if (type === "audio" || open.view === "audio") {
      window.switchToView?.("audio");
      prefill("audioSearchInput", qPreserve || hit.title || "");
      return;
    }
    if (type === "gallery" || open.view === "gallery") {
      window.switchToView?.("gallery");
      prefill("gallerySearchInput", qPreserve || hit.title || "");
      return;
    }
    if (type === "flytying" || open.view === "flytying") {
      window.switchToView?.("flytying");
      prefill("flySearchInput", qPreserve || hit.title || "");
      return;
    }
    if (type === "automation" || open.view === "automation") {
      window.switchToView?.("automation");
      return;
    }
    if (type === "projects" || open.view === "projects") {
      A?.projects?.open?.();
      return;
    }
    // Prefer Search Home for unknown federated hits — preserve query
    window.switchToView?.("search");
    setTimeout(() => {
      const el = $("searchHomeInput");
      if (el) {
        el.value = qPreserve || hit.title || hit.excerpt || "";
        window.runSearchHomeQuery?.();
      }
    }, 60);
  }

  function hitToCommand(hit, idx) {
    const source = hit.source_type || "knowledge";
    const label = hit.title || hit.excerpt || "Result";
    const excerpt = (hit.excerpt || "").replace(/\s+/g, " ").trim().slice(0, 72);
    return {
      id: `hit:${source}:${hit.location || hit.title || idx}`,
      title: excerpt ? `${label} — ${excerpt}` : String(label),
      label: excerpt ? `${label} — ${excerpt}` : String(label),
      group: "Results",
      hint: hit.source_label || source,
      mode: "search",
      keywords: `${hit.excerpt || ""} ${hit.location || ""}`,
      description: "Knowledge result",
      run: () => openHit(hit),
    };
  }

  function buildAskCommand(trimmed) {
    return {
      id: "ask:aria",
      title: `Ask Aria: “${trimmed}”`,
      label: `Ask Aria: “${trimmed}”`,
      group: "AI",
      hint: "Chat",
      mode: "ask",
      description: "Auto-sends to Chat with streaming reply",
      run: () => {
        window.AriaActions?.askAria?.(trimmed, { autoSend: true, switchView: true });
      },
    };
  }

  function filterCommands(rawQ) {
    const reg = registry();
    const parsed = reg?.parseMode?.(rawQ) || { mode: "", query: String(rawQ || "").trim() };
    const mode = parsed.mode;
    const q = parsed.query;
    const pins = loadPins();
    const usage = loadUsage();
    const view = window.AriaCommandCatalog?.currentView?.() || "chat";
    let commands = reg?.list?.() || [];

    // Living Workspace: owner must never see certification / smoke / engineering probes.
    if (document.body?.classList?.contains("living-workspace")) {
      const blocked = /^(nav:certification|act:voice-smoke|act:router-warm|act:debug-bundle|act:checklist|act:reload-ui)$/;
      commands = commands.filter((c) => !blocked.test(String(c?.id || "")));
    }

    if (mode === "pinned") {
      const byId = new Map(commands.map((c) => [c.id, c]));
      filtered = pins.map((id) => byId.get(id)).filter(Boolean).slice(0, MAX_VISIBLE);
      return;
    }
    if (mode === "recent") {
      const byId = new Map(commands.map((c) => [c.id, c]));
      filtered = loadRecent().map((id) => byId.get(id)).filter(Boolean).slice(0, MAX_VISIBLE);
      return;
    }
    if (mode) {
      commands = commands.filter((c) => c.mode === mode || (mode === "context" && c.context));
    }

    const scored = commands
      .map((c) => ({
        c,
        s: (reg?.scoreCommand?.(c, q) || 0) + (q ? (reg?.rankBoost?.(c, { pins, usage, view }) || 0) * 0.15 : (reg?.rankBoost?.(c, { pins, usage, view }) || 0)),
      }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s || a.c.title.localeCompare(b.c.title));

    if (!q.trim() && !mode) {
      contentHits = [];
      setSearchStatus("idle");
      const byId = new Map(commands.map((c) => [c.id, c]));
      const contextCmds = commands.filter((c) => c.context || c.group === "This page");
      const pinCmds = pins.map((id) => byId.get(id)).filter(Boolean).map((c) => ({ ...c, group: "Pinned", hint: c.hint || "Pinned" }));
      const recentCmds = loadRecent()
        .map((id) => byId.get(id))
        .filter(Boolean)
        .filter((c) => !pins.includes(c.id))
        .map((c) => ({ ...c, group: "Recent" }));
      const used = new Set([...pins, ...loadRecent(), ...contextCmds.map((c) => c.id)]);
      const rest = scored.map((x) => x.c).filter((c) => !used.has(c.id));
      filtered = [...contextCmds, ...pinCmds, ...recentCmds, ...rest].slice(0, MAX_VISIBLE);
      return;
    }

    const cmdHits = scored.map((x) => x.c);
    const sentence = reg?.looksLikeSentence?.(q);
    const askCmd = q.trim() && mode !== "navigate" && mode !== "action" && mode !== "system"
      ? [buildAskCommand(q.trim())]
      : [];

    let head;
    if (sentence && askCmd.length) {
      // NL prioritizes Ask Aria
      head = [...askCmd, ...contentHits, ...cmdHits].slice(0, MAX_VISIBLE);
      filtered = head;
      return;
    }
    head = [...contentHits, ...cmdHits].slice(0, Math.max(0, MAX_VISIBLE - askCmd.length));
    filtered = [...head, ...askCmd];
  }

  async function fetchContentHits(q) {
    const needle = q.trim();
    if (needle.length < 2) {
      contentHits = [];
      setSearchStatus("idle");
      return;
    }
    const seq = ++searchSeq;
    setSearchStatus("searching");
    try {
      const res = await fetch(`/api/search/product/query?q=${encodeURIComponent(needle)}&limit=8`);
      const data = await res.json().catch(() => ({}));
      if (seq !== searchSeq) return;
      if (!res.ok) {
        throw new Error(data.message || data.error || data.detail || `Search failed (${res.status})`);
      }
      const hits = Array.isArray(data.results)
        ? data.results.map((r) => ({
            source_type: r.source,
            source_label: r.source_label || r.source,
            title: r.title,
            excerpt: r.preview || r.summary,
            location: r.location,
            strategy: r.strategy,
            score: r.score,
            raw: { open: r.open, confidence: r.confidence, id: r.id },
          }))
        : Array.isArray(data.hits)
          ? data.hits
          : [];
      contentHits = hits.slice(0, 8).map((h, i) => hitToCommand(h, i));
      window.AriaHistory?.trackSearch?.(needle);
      if (!contentHits.length) setSearchStatus("empty");
      else setSearchStatus("ready", `${contentHits.length} search result${contentHits.length === 1 ? "" : "s"}`);
    } catch (err) {
      if (seq !== searchSeq) return;
      contentHits = [];
      setSearchStatus("error", err?.message || "Knowledge search unavailable — Retry");
    }
  }

  function renderList() {
    const list = $("commandPaletteList");
    const empty = $("commandPaletteEmpty");
    if (!list) return;
    list.innerHTML = "";
    if (!filtered.length) {
      if (empty) {
        empty.classList.remove("hidden");
        empty.textContent = searchStatus === "error"
          ? (searchError || "Search failed")
          : searchStatus === "searching"
            ? "Searching…"
            : "No matching commands — try >ask or Ask Aria";
      }
      list.setAttribute("aria-activedescendant", "");
      return;
    }
    if (empty) empty.classList.add("hidden");
    let lastGroup = "";
    const pins = loadPins();
    const qEmpty = !($("commandPaletteInput")?.value || "").trim();
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
      const pinned = pins.includes(cmd.id);
      const recent = qEmpty && loadRecent().includes(cmd.id);
      const desc = cmd.description ? `<span class="command-palette-desc">${escapeHtml(cmd.description)}</span>` : "";
      const badge = cmd.mode ? `<span class="command-palette-badge">${escapeHtml(cmd.mode)}</span>` : "";
      li.innerHTML = `<button type="button" class="command-palette-pin${pinned ? " is-pinned" : ""}" data-pin-id="${escapeHtml(cmd.id)}" title="${pinned ? "Unpin" : "Pin"} (Ctrl+P)" aria-label="${pinned ? "Unpin command" : "Pin command"}">★</button>`
        + `<span class="command-palette-label">${escapeHtml(cmd.title || cmd.label)}${recent && !pinned ? ' <span class="command-palette-recent">Recent</span>' : ""}${pinned ? ' <span class="command-palette-recent">Pinned</span>' : ""}${desc}</span>`
        + `<span class="command-palette-meta">${badge}${escapeHtml(cmd.hint || cmd.group)}${cmd.shortcut ? ` · ${escapeHtml(cmd.shortcut)}` : ""}</span>`;
      li.querySelector(".command-palette-pin")?.addEventListener("mousedown", (e) => {
        e.preventDefault();
        e.stopPropagation();
        togglePin(cmd.id);
        filterCommands($("commandPaletteInput")?.value || "");
        renderList();
      });
      li.addEventListener("mouseenter", () => {
        activeIndex = i;
        syncActive();
      });
      li.addEventListener("mousedown", (e) => {
        if (e.target.closest(".command-palette-pin")) return;
        e.preventDefault();
        runIndex(i);
      });
      list.appendChild(li);
    });
    syncActive();
    const count = $("commandPaletteCount");
    if (count) count.textContent = `${filtered.length} shown`;
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

  function toggleHelp() {
    const help = $("commandPaletteHelp");
    if (!help) return;
    helpOpen = !helpOpen;
    help.classList.toggle("hidden", !helpOpen);
    announce(helpOpen ? "Command palette help open" : "Help closed");
  }

  function openPalette(fromEl, prefill) {
    window.AriaCommandCatalog?.registerAll?.();
    contentHits = [];
    setSearchStatus("idle");
    helpOpen = false;
    $("commandPaletteHelp")?.classList.add("hidden");
    openerEl = fromEl && typeof fromEl.focus === "function" ? fromEl : document.activeElement;
    const modal = $("commandPaletteModal");
    const input = $("commandPaletteInput");
    if (!modal || !input) return;
    modal.classList.remove("hidden");
    const q = typeof prefill === "string" ? prefill : "";
    input.value = q;
    activeIndex = 0;
    filterCommands(q);
    renderList();
    if (q.trim().length >= 2) {
      const parsed = registry()?.parseMode?.(q) || { query: q };
      fetchContentHits(parsed.query || q).then(() => {
        filterCommands($("commandPaletteInput")?.value || "");
        renderList();
      });
    }
    setTimeout(() => input.focus(), 0);
    announce("Command palette open");
  }

  function closePalette() {
    const modal = $("commandPaletteModal");
    if (!modal) return;
    modal.classList.add("hidden");
    clearTimeout(searchTimer);
    searchTimer = null;
    helpOpen = false;
    $("commandPaletteHelp")?.classList.add("hidden");
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
    const parsed = registry()?.parseMode?.(q) || { query: q.trim() };
    if (parsed.query.trim().length < 2 || parsed.mode === "navigate" || parsed.mode === "action") {
      contentHits = [];
      if (parsed.query.trim().length < 2) setSearchStatus("idle");
      return;
    }
    searchTimer = setTimeout(async () => {
      await fetchContentHits(parsed.query);
      if (($("commandPaletteInput")?.value || "") !== q) return;
      filterCommands(q);
      renderList();
    }, 160);
  }

  function retrySearch() {
    const q = $("commandPaletteInput")?.value || "";
    const parsed = registry()?.parseMode?.(q) || { query: q };
    fetchContentHits(parsed.query || q).then(() => {
      filterCommands(q);
      renderList();
    });
  }

  function init() {
    $("commandPaletteBtn")?.addEventListener("click", (e) => openPalette(e.currentTarget));
    $("commandPaletteCloseBtn")?.addEventListener("click", closePalette);
    $("commandPaletteModal")?.addEventListener("click", (e) => {
      if (e.target?.id === "commandPaletteModal") closePalette();
    });
    $("commandPaletteInput")?.addEventListener("input", onInput);
    $("commandPaletteRetryBtn")?.addEventListener("click", retrySearch);
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
        if (helpOpen) {
          toggleHelp();
          return;
        }
        closePalette();
      } else if (e.key === "?" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        const input = $("commandPaletteInput");
        if (input && !input.value) {
          e.preventDefault();
          toggleHelp();
        }
      } else if ((e.ctrlKey || e.metaKey) && String(e.key).toLowerCase() === "p") {
        e.preventDefault();
        const cmd = filtered[activeIndex];
        if (cmd) {
          togglePin(cmd.id);
          filterCommands(inputValue());
          renderList();
        }
      } else if (e.key === "Tab") {
        // Cycle modes lightly
        e.preventDefault();
        const modes = ["", ">navigate ", ">action ", ">search ", ">ask ", ">context ", ">system "];
        const cur = $("commandPaletteInput")?.value || "";
        const idx = Math.max(0, modes.findIndex((m) => cur.startsWith(m)));
        const next = modes[(idx + (e.shiftKey ? modes.length - 1 : 1)) % modes.length];
        const rest = cur.replace(/^\s*>(navigate|nav|action|actions|search|ask|recent|pinned|context|system|sys)\b\s*/i, "");
        if ($("commandPaletteInput")) {
          $("commandPaletteInput").value = next + rest;
          onInput();
        }
      }
    });

    document.addEventListener("keydown", (e) => {
      if (!(e.ctrlKey || e.metaKey)) return;
      if (String(e.key).toLowerCase() !== "k") return;
      /* Living Workspace: Front Door owns Ctrl+K */
      if (
        document.documentElement.classList.contains("living-workspace") ||
        document.body?.classList.contains("living-workspace")
      ) {
        return;
      }
      e.preventDefault();
      if (isOpen()) closePalette();
      else openPalette(document.activeElement);
    });
  }

  function inputValue() {
    return $("commandPaletteInput")?.value || "";
  }

  window.openAriaCommandPalette = openPalette;
  window.openCommandPalette = (prefill) => openPalette(null, typeof prefill === "string" ? prefill : undefined);
  window.closeAriaCommandPalette = closePalette;
  // Prefer registry; keep alias for modules that still call this
  window.registerAriaCommand = (cmd) => {
    if (window.AriaCommandRegistry?.register) return window.AriaCommandRegistry.register({ ...cmd, source: cmd.source || "module" });
    return false;
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
