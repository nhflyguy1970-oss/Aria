/** Activity Center event store — versioned schema, unread/pin/mute/snooze, dedupe (local-first). */
(function () {
  "use strict";

  const STORE_KEY = "aria_activity_log_v2";
  const CACHE_META_KEY = "aria_activity_cache_meta_v1";
  const PREFS_KEY = "aria_activity_prefs_v1";
  const SCHEMA_VERSION = 2;
  const MAX_EVENTS = 200;
  const DEDUPE_WINDOW_MS = 5 * 60 * 1000;
  /** Server is source of truth; localStorage is cache only (Batch C). */
  const SERVER_AUTHORITATIVE = true;

  /** @type {object[]} */
  let events = [];
  /** @type {{ filter: string, query: string, mutedSources: string[], scrollTop: number }} */
  let prefs = { filter: "all", query: "", mutedSources: [], scrollTop: 0 };
  /** @type {{ type: string, events: object[] } | null} */
  let lastUndo = null;

  const SEVERITY = {
    critical: 4,
    error: 3,
    warning: 2,
    info: 1,
    success: 0,
  };

  function now() {
    return Date.now();
  }

  function uid() {
    return `act_${now()}_${Math.random().toString(36).slice(2, 8)}`;
  }

  function loadPrefs() {
    try {
      const raw = JSON.parse(localStorage.getItem(PREFS_KEY) || "{}");
      prefs = {
        filter: raw.filter || "all",
        query: raw.query || "",
        mutedSources: Array.isArray(raw.mutedSources) ? raw.mutedSources : [],
        scrollTop: Number(raw.scrollTop || 0) || 0,
      };
    } catch {
      prefs = { filter: "all", query: "", mutedSources: [], scrollTop: 0 };
    }
  }

  function savePrefs() {
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
    } catch {
      /* quota */
    }
  }

  function normalize(raw) {
    if (!raw || typeof raw !== "object") return null;
    const severity = String(raw.severity || mapTone(raw.tone) || "info").toLowerCase();
    const category = String(raw.category || raw.kind || "system").toLowerCase();
    const type = String(raw.type || raw.kind || "event").toLowerCase();
    const source = String(raw.source || category || "system");
    return {
      id: String(raw.id || uid()),
      version: SCHEMA_VERSION,
      timestamp: Number(raw.timestamp || raw.ts || now()),
      severity,
      priority: Number(raw.priority != null ? raw.priority : SEVERITY[severity] ?? 1),
      category,
      source,
      type,
      title: String(raw.title || "Event").slice(0, 200),
      summary: String(raw.summary || raw.detail || "").slice(0, 280),
      detail: String(raw.detail || raw.summary || "").slice(0, 4000),
      context: raw.context && typeof raw.context === "object" ? raw.context : {},
      deepLink: String(raw.deepLink || raw.deeplink || ""),
      actions: Array.isArray(raw.actions) ? raw.actions : defaultActions(category, raw),
      read: Boolean(raw.read),
      pinned: Boolean(raw.pinned),
      muted: Boolean(raw.muted),
      dismissed: Boolean(raw.dismissed),
      snoozedUntil: Number(raw.snoozedUntil || 0) || 0,
      groupId: String(raw.groupId || ""),
      metadata: raw.metadata && typeof raw.metadata === "object" ? raw.metadata : {},
      // legacy compat
      kind: category,
      tone: severity === "error" || severity === "critical" ? "err"
        : severity === "warning" ? "warn"
          : severity === "success" ? "ok" : "info",
      ts: Number(raw.timestamp || raw.ts || now()),
    };
  }

  function mapTone(tone) {
    const t = String(tone || "").toLowerCase();
    if (t === "err" || t === "error") return "error";
    if (t === "warn" || t === "warning") return "warning";
    if (t === "ok" || t === "success") return "success";
    return "info";
  }

  function defaultActions(category, raw) {
    const acts = ["mark_read", "ask_aria", "dismiss"];
    if (raw.deepLink || raw.source) acts.unshift("open");
    if (category === "job" || /fail|error/i.test(String(raw.title || ""))) acts.splice(1, 0, "retry");
    return [...new Set(acts)];
  }

  function migrateV1(list) {
    return (list || []).map((e) => normalize({
      ...e,
      category: e.kind || e.category || "notification",
      type: e.kind || "notification",
      severity: mapTone(e.tone),
      summary: e.detail,
      deepLink: e.source && String(e.source).startsWith("view:")
        ? `view:${e.source.slice(5)}`
        : e.source === "jobs" ? "jobs" : (e.source || ""),
      timestamp: e.ts || e.timestamp,
    })).filter(Boolean);
  }

  function load() {
    loadPrefs();
    try {
      const v2 = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
      if (Array.isArray(v2)) {
        events = v2.map(normalize).filter(Boolean);
      } else {
        const v1 = JSON.parse(localStorage.getItem("aria_activity_log_v1") || "[]");
        events = migrateV1(Array.isArray(v1) ? v1 : []);
        persist();
      }
    } catch {
      events = [];
    }
    if (SERVER_AUTHORITATIVE) {
      syncFromServer();
    }
  }

  function serverItemToLocal(row) {
    const meta = row.meta || {};
    return normalize({
      id: row.id,
      timestamp: (row.ts || 0) * (row.ts > 1e12 ? 1 : 1000),
      ts: row.ts,
      title: row.title,
      summary: row.body,
      detail: row.body,
      source: row.source,
      category: meta.category || row.kind || "system",
      type: meta.type || row.kind || "event",
      severity: meta.severity || (mapTone(row.kind) === "info" && row.kind === "error" ? "error" : mapTone(row.kind)),
      kind: row.kind,
      dismissed: Boolean(row.dismissed),
      read: Boolean(row.read),
      metadata: meta,
    });
  }

  async function syncFromServer() {
    try {
      const res = await fetch("/api/activity/inbox?limit=200");
      if (!res.ok) return;
      const data = await res.json().catch(() => ({}));
      if (!data.ok || !Array.isArray(data.items)) return;
      const mapped = data.items.map(serverItemToLocal).filter(Boolean);
      // Server wins for shared fields; keep local-only pins/snooze if same id
      const byId = new Map(events.map((e) => [e.id, e]));
      events = mapped.map((s) => {
        const local = byId.get(s.id);
        if (!local) return s;
        return {
          ...s,
          pinned: local.pinned,
          snoozedUntil: local.snoozedUntil,
          muted: local.muted,
        };
      });
      persist();
    } catch {
      /* offline — cache remains */
    }
  }

  async function publishToServer(item) {
    if (!SERVER_AUTHORITATIVE || !item) return;
    try {
      await fetch("/api/activity/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: item.id,
          kind: item.severity || item.kind || "info",
          title: item.title,
          body: item.detail || item.summary || "",
          source: item.source || "client",
          meta: item.metadata || {},
        }),
      });
    } catch {
      /* queue offline later — cache already has item */
    }
  }

  function persist() {
    try {
      const serializable = events.slice(0, MAX_EVENTS).map((e) => {
        const { action, ...rest } = e;
        return rest;
      });
      localStorage.setItem(STORE_KEY, JSON.stringify(serializable));
      localStorage.setItem(CACHE_META_KEY, JSON.stringify({
        sourceOfTruth: "server:/api/activity/inbox",
        cacheOnly: true,
        updatedAt: new Date().toISOString(),
      }));
    } catch {
      /* quota */
    }
    window.dispatchEvent(new CustomEvent("aria-activity-change", { detail: { unread: unreadCount() } }));
  }

  function snapshotForUndo(label) {
    lastUndo = { type: label, events: events.map((e) => ({ ...e })) };
  }

  function undo() {
    if (!lastUndo) return false;
    events = lastUndo.events;
    lastUndo = null;
    persist();
    return true;
  }

  function isMutedSource(source) {
    return prefs.mutedSources.includes(String(source || ""));
  }

  function isOwnerChannel(item) {
    const ch = String(item?.channel || "owner").toLowerCase();
    return ch === "owner" || ch === "";
  }

  function classifyChannel(raw) {
    const title = String(raw?.title || "");
    const detail = String(raw?.detail || raw?.summary || raw?.body || "");
    const blob = `${title} ${detail}`.toLowerCase();
    if (window.AriaNet?.isRoomAbort?.(raw) || window.AriaNet?.isRoomAbort?.({ message: blob })) return "cancelled";
    if (/aria-room-leave|signal is aborted|the operation was aborted|aborterror|stream aborted|cancel api/.test(blob)) return "cancelled";
    if (
      /could not load |failed to load |load failed|checklist failed|settings unavailable|status unavailable|home unavailable|work schedule unavailable|mission control.*health|activity center is listening|save failed|toggle failed|settings update failed|model switch failed|another request is still finishing|enter a |enter event text|need top text|preview needs|nothing to redo|empty request|^not found$/.test(
        blob,
      )
    ) {
      return "engineering";
    }
    return String(raw?.channel || "owner").toLowerCase() || "owner";
  }

  function publish(raw) {
    const item = normalize(raw);
    if (!item) return null;
    item.channel = classifyChannel(raw);
    if (item.channel === "cancelled") return null;
    if (item.channel !== "owner") {
      item.read = true;
      return null;
    }
    if (item.muted || isMutedSource(item.source) || prefs.mutedSources.includes(item.category)) {
      return null;
    }
    // Dedupe / rollup identical alerts in window
    const twin = events.find((e) =>
      !e.dismissed
      && e.title === item.title
      && e.source === item.source
      && e.severity === item.severity
      && (now() - e.timestamp) < DEDUPE_WINDOW_MS
    );
    if (twin) {
      twin.metadata = { ...(twin.metadata || {}), count: (twin.metadata.count || 1) + 1 };
      twin.summary = `${item.summary || item.detail}`.slice(0, 280);
      twin.detail = item.detail || twin.detail;
      twin.timestamp = now();
      twin.ts = twin.timestamp;
      // Rollup must not re-open already-read noise as unread.
      if (item.severity === "error" || item.severity === "critical") {
        twin.read = false;
      }
      if (!twin.groupId) twin.groupId = `grp_${twin.id}`;
      item.groupId = twin.groupId;
      // move twin to front
      events = [twin, ...events.filter((e) => e.id !== twin.id)].slice(0, MAX_EVENTS);
      persist();
      publishToServer(twin);
      return twin;
    }
    events = [item, ...events].slice(0, MAX_EVENTS);
    persist();
    publishToServer(item);
    return item;
  }

  /** Back-compat push({kind,tone,title,detail,source,action}) */
  function push(evt) {
    const deepLink = evt.deepLink
      || (evt.source && String(evt.source).startsWith("view:") ? evt.source
        : evt.source === "jobs" || evt.source === "job" ? "jobs"
          : evt.source || "");
    const item = publish({
      category: evt.kind || evt.category || "notification",
      type: evt.type || evt.kind || "notification",
      severity: mapTone(evt.tone) || evt.severity || "info",
      title: evt.title,
      summary: evt.detail,
      detail: evt.detail,
      source: evt.source || "toast",
      deepLink,
      context: evt.context,
      metadata: evt.metadata,
      groupId: evt.groupId,
      actions: evt.actions,
    });
    if (item && typeof evt.action === "function") {
      item._actionFn = evt.action;
    }
    return item;
  }

  function get(id) {
    return events.find((e) => e.id === id) || null;
  }

  function update(id, patch) {
    const e = get(id);
    if (!e) return null;
    Object.assign(e, patch);
    if (patch.timestamp) e.ts = patch.timestamp;
    persist();
    return e;
  }

  function markRead(id, read = true) {
    const out = update(id, { read: Boolean(read) });
    if (SERVER_AUTHORITATIVE && read && id) {
      void window.ariaMutate?.({
        request: () =>
          fetch("/api/activity/read", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id }),
          }),
        failToast: "Could not mark activity read",
      });
    }
    return out;
  }

  function markAllRead() {
    snapshotForUndo("markAllRead");
    events.forEach((e) => {
      if (!e.dismissed && !isSnoozed(e)) e.read = true;
    });
    persist();
    if (SERVER_AUTHORITATIVE) {
      void window.ariaMutate?.({
        request: () => fetch("/api/activity/read-all", { method: "POST" }),
        failToast: "Could not mark all activity read",
      })?.then?.((result) => {
        if (result?.ok) void syncFromServer();
      });
    }
  }

  function markUnread(id) {
    return markRead(id, false);
  }

  function togglePin(id) {
    const e = get(id);
    if (!e) return null;
    return update(id, { pinned: !e.pinned });
  }

  function snooze(id, ms = 60 * 60 * 1000) {
    return update(id, { snoozedUntil: now() + ms, read: true });
  }

  function dismiss(id) {
    snapshotForUndo("dismiss");
    const out = update(id, { dismissed: true, read: true });
    if (SERVER_AUTHORITATIVE && id) {
      void window.ariaMutate?.({
        request: () =>
          fetch("/api/activity/dismiss", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id }),
          }),
        failToast: "Could not dismiss activity",
      });
    }
    return out;
  }

  function clearRead() {
    snapshotForUndo("clearRead");
    events = events.filter((e) => !e.read || e.pinned);
    persist();
    if (SERVER_AUTHORITATIVE) {
      void window.ariaMutate?.({
        request: () => fetch("/api/activity/clear-read", { method: "POST" }),
        failToast: "Could not clear read activity",
      })?.then?.((result) => {
        if (result?.ok) void syncFromServer();
      });
    }
  }

  function clearAll() {
    snapshotForUndo("clearAll");
    events = events.filter((e) => e.pinned);
    persist();
    if (SERVER_AUTHORITATIVE) {
      void window.ariaMutate?.({
        request: () => fetch("/api/activity/clear-all", { method: "POST" }),
        failToast: "Could not clear activity",
      })?.then?.((result) => {
        if (result?.ok) void syncFromServer();
      });
    }
  }

  function muteSource(source, muted = true) {
    const s = String(source || "");
    if (!s) return;
    if (muted) {
      if (!prefs.mutedSources.includes(s)) prefs.mutedSources.push(s);
    } else {
      prefs.mutedSources = prefs.mutedSources.filter((x) => x !== s);
    }
    savePrefs();
  }

  function isSnoozed(e) {
    return e.snoozedUntil && e.snoozedUntil > now();
  }

  function visibleEvents() {
    return events.filter((e) => !e.dismissed && !isSnoozed(e) && isOwnerChannel(e));
  }

  function unreadCount() {
    return visibleEvents().filter((e) => !e.read).length;
  }

  function setFilter(filter) {
    prefs.filter = filter || "all";
    savePrefs();
  }

  function setQuery(q) {
    prefs.query = q || "";
    savePrefs();
  }

  function setScrollTop(n) {
    prefs.scrollTop = Math.max(0, Number(n) || 0);
    savePrefs();
  }

  /** Lightweight NL-ish query tokens → structured constraints (future-ready). */
  function parseSearchQuery(raw) {
    let q = String(raw || "").trim().toLowerCase();
    const constraints = { unread: false, pinned: false, muted: false, dismissed: false, recent: false, severity: "", category: "", date: "" };
    if (!q) return { q: "", constraints };
    if (/\bunread\b/.test(q)) { constraints.unread = true; q = q.replace(/\bunread\b/g, " ").trim(); }
    if (/\bpinned?\b/.test(q)) { constraints.pinned = true; q = q.replace(/\bpinned?\b/g, " ").trim(); }
    if (/\bmuted?\b/.test(q)) { constraints.muted = true; q = q.replace(/\bmuted?\b/g, " ").trim(); }
    if (/\bdismissed\b/.test(q)) { constraints.dismissed = true; q = q.replace(/\bdismissed\b/g, " ").trim(); }
    if (/\brecent\b/.test(q)) { constraints.recent = true; q = q.replace(/\brecent\b/g, " ").trim(); }
    const sev = q.match(/\b(critical|error|errors|failure|failures|warning|warnings|success|info)\b/);
    if (sev) {
      const s = sev[1];
      constraints.severity = /error|fail/.test(s) ? "error" : /warn/.test(s) ? "warning" : s === "success" ? "success" : s === "critical" ? "critical" : "info";
      q = q.replace(sev[0], " ").trim();
    }
    const cat = q.match(/\b(chat|job|jobs|memory|document|documents|planner|calendar|journal|provider|providers|gallery|voice|vision|coding|home|ha|system|mission)\b/);
    if (cat) {
      const c = cat[1];
      constraints.category = c === "jobs" ? "job" : c === "document" ? "documents" : c === "ha" ? "home" : c === "providers" ? "providers" : c;
      q = q.replace(cat[0], " ").trim();
    }
    const dm = q.match(/\b(today|yesterday)\b/);
    if (dm) {
      constraints.date = dm[1];
      q = q.replace(dm[0], " ").trim();
    }
    return { q: q.replace(/\s+/g, " ").trim(), constraints };
  }

  function matchesDate(ts, token) {
    if (!token) return true;
    const d = new Date(ts);
    const today = new Date();
    const sameDay = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
    if (token === "today") return sameDay(d, today);
    if (token === "yesterday") {
      const y = new Date(Date.now() - 86400_000);
      return sameDay(d, y);
    }
    return true;
  }

  function queryEvents({ includeDismissed = false } = {}) {
    const parsed = parseSearchQuery(prefs.query || "");
    const q = parsed.q;
    const c = parsed.constraints;
    const filter = prefs.filter || "all";
    let list = (includeDismissed || c.dismissed) ? events.slice() : visibleEvents();
    if (c.dismissed) list = events.filter((e) => e.dismissed);
    // pinned first, then unread, then time
    list.sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      if (a.read !== b.read) return a.read ? 1 : -1;
      return b.timestamp - a.timestamp;
    });
    return list.filter((e) => {
      if (filter === "unread" && e.read) return false;
      if (filter === "pinned" && !e.pinned) return false;
      if (filter === "muted" && !e.muted && !isMutedSource(e.source)) return false;
      if (filter === "job" && e.category !== "job" && e.type !== "job") return false;
      if (filter === "err" || filter === "error") {
        if (e.severity !== "error" && e.severity !== "critical" && e.tone !== "err") return false;
      }
      if (filter === "warn" || filter === "warning") {
        if (e.severity !== "warning" && e.tone !== "warn") return false;
      }
      if (filter === "success" && e.severity !== "success" && e.tone !== "ok") return false;
      if (c.unread && e.read) return false;
      if (c.pinned && !e.pinned) return false;
      if (c.muted && !e.muted && !isMutedSource(e.source)) return false;
      if (c.recent && (now() - e.timestamp) > 24 * 3600_000) return false;
      if (c.severity === "error" && e.severity !== "error" && e.severity !== "critical") return false;
      if (c.severity && c.severity !== "error" && e.severity !== c.severity) return false;
      if (c.category) {
        const hayCat = `${e.category} ${e.source} ${e.type}`.toLowerCase();
        if (!hayCat.includes(c.category) && e.category !== c.category) return false;
      }
      if (!matchesDate(e.timestamp, c.date)) return false;
      if (!q) return true;
      const hay = `${e.title} ${e.summary} ${e.detail} ${e.source} ${e.category} ${e.type} ${e.severity} ${new Date(e.timestamp).toISOString()}`.toLowerCase();
      return q.split(/\s+/).every((tok) => hay.includes(tok));
    });
  }

  function exportLog() {
    return JSON.stringify({ version: SCHEMA_VERSION, exportedAt: new Date().toISOString(), events }, null, 2);
  }

  function correlate() {
    /** Group related failures into incident summaries (local heuristic). */
    const recent = visibleEvents().filter((e) => (now() - e.timestamp) < 30 * 60 * 1000);
    const fails = recent.filter((e) => e.severity === "error" || e.severity === "critical" || e.severity === "warning");
    const buckets = {};
    fails.forEach((e) => {
      const key = /ollama|provider|model|inference/i.test(`${e.title} ${e.detail}`)
        ? "inference"
        : /job|media|comfy|video|image/i.test(`${e.title} ${e.detail}${e.category}`)
          ? "jobs"
          : /ha |home assistant|device/i.test(`${e.title} ${e.detail}`)
            ? "home"
            : e.category || "other";
      (buckets[key] = buckets[key] || []).push(e);
    });
    return Object.entries(buckets)
      .filter(([, arr]) => arr.length >= 2)
      .map(([key, arr]) => ({
        id: `corr_${key}`,
        key,
        count: arr.length,
        title: key === "inference" ? "Inference / provider issues"
          : key === "jobs" ? "Background job issues"
            : key === "home" ? "Home Assistant issues"
              : `Related ${key} events`,
        events: arr,
        summary: arr.slice(0, 4).map((e) => e.title).join(" · "),
      }));
  }

  function summarizeUnread() {
    const unread = visibleEvents().filter((e) => !e.read);
    if (!unread.length) return "No unread activity. Aria is quiet.";
    const errs = unread.filter((e) => e.severity === "error" || e.severity === "critical");
    const warns = unread.filter((e) => e.severity === "warning");
    const jobs = unread.filter((e) => e.category === "job");
    const parts = [`${unread.length} unread event${unread.length === 1 ? "" : "s"}`];
    if (errs.length) parts.push(`${errs.length} failure${errs.length === 1 ? "" : "s"}`);
    if (warns.length) parts.push(`${warns.length} warning${warns.length === 1 ? "" : "s"}`);
    if (jobs.length) parts.push(`${jobs.length} job update${jobs.length === 1 ? "" : "s"}`);
    const top = unread.slice(0, 5).map((e) => e.title).join("; ");
    const corr = correlate();
    let text = `${parts.join(", ")}. Top: ${top}.`;
    if (corr.length) {
      text += ` Correlated: ${corr.map((c) => `${c.title} (${c.count})`).join("; ")}.`;
    }
    return text;
  }

  // init
  load();

  window.AriaActivityStore = {
    SCHEMA_VERSION,
    load,
    persist,
    syncFromServer,
    publish,
    push,
    get,
    update,
    markRead,
    markUnread,
    markAllRead,
    togglePin,
    snooze,
    dismiss,
    clearRead,
    clearAll,
    muteSource,
    isMutedSource,
    unreadCount,
    queryEvents,
    visibleEvents,
    all: () => events.slice(),
    getPrefs: () => ({ ...prefs, mutedSources: prefs.mutedSources.slice() }),
    setFilter,
    setQuery,
    setScrollTop,
    exportLog,
    correlate,
    summarizeUnread,
    parseSearchQuery,
    undo,
    canUndo: () => Boolean(lastUndo),
  };
})();
