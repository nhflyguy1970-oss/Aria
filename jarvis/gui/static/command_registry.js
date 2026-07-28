/** Aria Command Registry — modular OS launcher catalog (not Chat). */
(function () {
  "use strict";

  /** @type {Map<string, object>} */
  const byId = new Map();

  const ALIASES = {
    todo: "planner task",
    todos: "planner",
    kg: "connections",
    graph: "connections",
    rag: "documents",
    pdf: "documents",
    bujo: "journal",
    mc: "mission control",
    ha: "home assistant",
    llm: "model",
    ollama: "model",
    cmdk: "commands",
  };

  function normalizeCmd(raw) {
    if (!raw || typeof raw !== "object") return null;
    const id = String(raw.id || "").trim();
    const title = String(raw.title || raw.label || "").trim();
    if (!id || !title || typeof raw.run !== "function") return null;
    return {
      id,
      title,
      label: title,
      keywords: String(raw.keywords || ""),
      group: String(raw.group || "Actions"),
      mode: String(raw.mode || inferMode(raw.group, id)),
      icon: raw.icon || "",
      description: String(raw.description || raw.hint || ""),
      hint: String(raw.hint || raw.group || ""),
      shortcut: String(raw.shortcut || ""),
      context: Boolean(raw.context),
      available: typeof raw.available === "function" ? raw.available : () => true,
      run: raw.run,
      source: String(raw.source || "module"),
    };
  }

  function inferMode(group, id) {
    const g = String(group || "").toLowerCase();
    if (g === "navigate" || id.startsWith("nav:")) return "navigate";
    if (g === "search" || id.startsWith("search:") || id.startsWith("hit:")) return "search";
    if (g === "ai" || id.startsWith("ask:")) return "ask";
    if (g === "this page" || g === "context") return "context";
    if (g === "system" || g === "mission control" || g === "settings" || g === "models") return "system";
    if (g === "recent") return "recent";
    if (g === "pinned") return "pinned";
    return "action";
  }

  function register(raw) {
    const cmd = normalizeCmd(raw);
    if (!cmd) return false;
    byId.set(cmd.id, cmd);
    return true;
  }

  function registerMany(list) {
    let n = 0;
    (list || []).forEach((c) => {
      if (register(c)) n += 1;
    });
    return n;
  }

  function unregister(id) {
    return byId.delete(String(id || ""));
  }

  function get(id) {
    return byId.get(String(id || "")) || null;
  }

  function list({ includeUnavailable = false } = {}) {
    const out = [];
    byId.forEach((cmd) => {
      try {
        if (includeUnavailable || cmd.available()) out.push(cmd);
      } catch {
        /* skip broken availability */
      }
    });
    return out;
  }

  function expandQuery(q) {
    let s = String(q || "").toLowerCase().trim();
    Object.entries(ALIASES).forEach(([k, v]) => {
      if (s === k || s.startsWith(`${k} `)) s = s.replace(k, v);
    });
    return s;
  }

  /** Parse mode prefixes: >navigate >action >search >ask >recent >pinned >context >system */
  function parseMode(q) {
    const raw = String(q || "");
    const m = raw.match(/^\s*>(navigate|nav|action|actions|search|ask|recent|pinned|context|system|sys)\b\s*/i);
    if (!m) return { mode: "", query: raw.trim() };
    const key = m[1].toLowerCase();
    const map = {
      navigate: "navigate",
      nav: "navigate",
      action: "action",
      actions: "action",
      search: "search",
      ask: "ask",
      recent: "recent",
      pinned: "pinned",
      context: "context",
      system: "system",
      sys: "system",
    };
    return { mode: map[key] || "", query: raw.slice(m[0].length).trim() };
  }

  function looksLikeSentence(q) {
    const s = String(q || "").trim();
    if (s.length < 12) return false;
    if (/^(go to|open|toggle|start|stop|focus|search|use model|ask aria)\b/i.test(s)) return false;
    if (/\s/.test(s) && /[?.!]$/.test(s)) return true;
    if (/\s/.test(s) && s.split(/\s+/).length >= 5) return true;
    if (/^(what|why|how|when|where|who|can you|please|help me|tell me|explain)\b/i.test(s)) return true;
    return false;
  }

  function fuzzyScore(hay, needle) {
    if (!needle) return 1;
    if (hay === needle) return 100;
    if (hay.startsWith(needle)) return 85;
    if (hay.includes(needle)) return 55;
    const parts = needle.split(/\s+/).filter(Boolean);
    if (parts.length > 1 && parts.every((p) => hay.includes(p))) return 40;
    // contiguous subsequence with density bonus
    let hi = 0;
    let gaps = 0;
    let last = -1;
    for (let ni = 0; ni < needle.length; ni += 1) {
      const ch = needle[ni];
      let found = -1;
      for (let i = hi; i < hay.length; i += 1) {
        if (hay[i] === ch) {
          found = i;
          break;
        }
      }
      if (found < 0) return 0;
      if (last >= 0) gaps += found - last - 1;
      last = found;
      hi = found + 1;
    }
    const density = Math.max(0, 30 - gaps);
    return 15 + density;
  }

  function scoreCommand(cmd, query) {
    const q = expandQuery(query);
    if (!q) return 1;
    const hay = `${cmd.title} ${cmd.group} ${cmd.keywords} ${cmd.description} ${cmd.id}`.toLowerCase();
    return fuzzyScore(hay, q);
  }

  function rankBoost(cmd, { pins = [], usage = {}, view = "" } = {}) {
    let b = 0;
    if (pins.includes(cmd.id)) b += 40;
    if (cmd.context || cmd.group === "This page") b += 55;
    if (view && cmd.id.includes(`:${view}:`)) b += 10;
    b += Math.min(25, (usage[cmd.id] || 0) * 2);
    return b;
  }

  window.AriaCommandRegistry = {
    register,
    registerMany,
    unregister,
    get,
    list,
    clear: () => byId.clear(),
    size: () => byId.size,
    parseMode,
    looksLikeSentence,
    scoreCommand,
    rankBoost,
    expandQuery,
    ALIASES,
  };

  // Back-compat global used by older docs / modules
  window.registerAriaCommand = register;
})();
