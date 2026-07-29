/** Notifications — unified delivery product. Activity Center is the durable inbox. */
(function () {
  "use strict";

  let _prefs = null;
  let _prefsAt = 0;

  function store() {
    return window.AriaActivityStore;
  }

  async function fetchPrefs(force) {
    if (!force && _prefs && Date.now() - _prefsAt < 15000) return _prefs;
    try {
      const res = await fetch("/api/notifications/preferences", { cache: "no-store" });
      const data = await res.json();
      if (data && data.ok !== false) {
        _prefs = data;
        _prefsAt = Date.now();
      }
    } catch {
      _prefs = _prefs || {
        enabled: true,
        toast_enabled: true,
        desktop_enabled: true,
        activity_enabled: true,
        critical_only: false,
        quiet_hours_enabled: false,
        dnd: false,
      };
    }
    return _prefs;
  }

  function severityRank(s) {
    return { critical: 4, error: 3, warning: 2, info: 1, success: 0 }[String(s || "").toLowerCase()] || 0;
  }

  function inQuietHours(prefs) {
    if (prefs?.dnd) return true;
    if (!prefs?.quiet_hours_enabled) return false;
    const parse = (v) => {
      const p = String(v || "22:00").split(":");
      return Number(p[0]) * 60 + Number(p[1] || 0);
    };
    const start = parse(prefs.quiet_hours_start);
    const end = parse(prefs.quiet_hours_end);
    const now = new Date();
    const mins = now.getHours() * 60 + now.getMinutes();
    if (start === end) return false;
    if (start < end) return mins >= start && mins < end;
    return mins >= start || mins < end;
  }

  function routeLocal(evt, prefs) {
    prefs = prefs || _prefs || {};
    const sev = String(evt.severity || "info").toLowerCase();
    const critical = sev === "critical" || sev === "error";
    if (prefs.enabled === false) {
      return { deliver: false, activity: false, toast: false, desktop: false, reason: "disabled" };
    }
    const muted = prefs.muted_sources || [];
    const mutedCat = prefs.muted_categories || [];
    if (muted.includes(evt.source) || mutedCat.includes(evt.category)) {
      return { deliver: false, activity: false, toast: false, desktop: false, reason: "muted" };
    }
    if (prefs.critical_only && !critical) {
      return { deliver: false, activity: false, toast: false, desktop: false, reason: "critical_only" };
    }
    const quiet = inQuietHours(prefs);
    let activity = prefs.activity_enabled !== false;
    let toast =
      prefs.toast_enabled !== false &&
      severityRank(sev) >= severityRank(prefs.toast_min_severity || "warning");
    let desktop =
      prefs.desktop_enabled !== false &&
      severityRank(sev) >= severityRank(prefs.desktop_min_severity || "warning");
    if (quiet && !critical) {
      toast = false;
      desktop = false;
    } else if (quiet && critical) {
      desktop = prefs.desktop_enabled !== false;
      activity = true;
    }
    if (evt.toast === false) toast = false;
    if (evt.desktop === false) desktop = false;
    return { deliver: activity || toast || desktop, activity, toast, desktop, quiet, reason: "ok" };
  }

  function normalizeClient(raw) {
    const r = raw && typeof raw === "object" ? raw : { title: String(raw || "Notification") };
    const severity =
      r.severity ||
      (r.tone === "err" || r.tone === "error"
        ? "error"
        : r.tone === "warn" || r.tone === "warning"
          ? "warning"
          : r.tone === "ok" || r.tone === "success"
            ? "success"
            : "info");
    return {
      ...r,
      severity,
      title: String(r.title || r.message || "Notification").slice(0, 200),
      summary: String(r.summary || r.message || r.detail || "").slice(0, 280),
      detail: String(r.detail || r.summary || r.message || "").slice(0, 4000),
      deepLink: String(r.deepLink || r.deeplink || r.fix || ""),
      source: String(r.source || r.category || r.product || "system"),
      category: String(r.category || r.kind || r.product || "system"),
      type: String(r.type || r.kind || "event"),
    };
  }

  function ingestActivity(evt) {
    if (!store()?.publish) return null;
    return store().publish(evt);
  }

  function showToastIf(route, evt) {
    if (!route.toast || !window.showAriaToast) return;
    const tone = evt.severity === "error" || evt.severity === "critical" ? "err" : evt.severity === "warning" ? "warn" : "info";
    window.__ariaActivitySuppressToast = true;
    try {
      window.showAriaToast(evt.title || evt.summary, tone, 4200);
    } finally {
      window.__ariaActivitySuppressToast = false;
    }
  }

  function showDesktopIf(route, evt) {
    if (!route.desktop) return;
    const fn = window.__ariaDesktopNotifyRaw || window.jarvisNotify;
    if (typeof fn !== "function") return;
    window.__ariaActivitySuppressNotify = true;
    try {
      fn(evt.title || "Aria", evt.summary || evt.detail || "");
    } finally {
      window.__ariaActivitySuppressNotify = false;
    }
  }

  async function publish(raw, opts = {}) {
    const evt = normalizeClient(raw);
    const prefs = await fetchPrefs(!!opts.forcePrefs);
    const route = opts.routing || routeLocal(evt, prefs);
    let server = null;
    if (!opts.localOnly) {
      try {
        const res = await fetch("/api/notifications/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(evt),
        });
        server = await res.json();
        if (server?.routing) Object.assign(route, server.routing);
        if (server?.activity) Object.assign(evt, server.activity);
      } catch {
        /* local deliver still */
      }
    }
    if (route.activity !== false && route.deliver !== false) {
      ingestActivity(server?.activity || evt);
    }
    if (!opts.skipChannels) {
      showToastIf(route, evt);
      showDesktopIf(route, evt);
    }
    return { ok: true, event: evt, routing: route, server };
  }

  // Compatibility aliases
  function add(raw) {
    return publish(raw);
  }
  function push(raw) {
    return publish(raw);
  }

  function open(filter) {
    if (filter) store()?.setFilter?.(filter);
    window.AriaActivity?.open?.();
  }

  async function drainOutboxes() {
    try {
      const res = await fetch("/api/notifications/drain", { method: "POST" });
      const data = await res.json();
      const batch = data.activity_batch || [];
      batch.forEach((evt) => ingestActivity(evt));
      return data;
    } catch (err) {
      return { ok: false, error: String(err) };
    }
  }

  async function loadDigest(kind) {
    try {
      const res = await fetch(`/api/notifications/digest?kind=${encodeURIComponent(kind || "today")}`);
      return await res.json();
    } catch {
      return { ok: false };
    }
  }

  function wrapDesktopRaw() {
    // Preserve raw Notification helper for pipeline desktop channel
    if (typeof window.jarvisNotify === "function" && !window.__ariaDesktopNotifyRaw) {
      if (!window.jarvisNotify._ariaActivityWrapped && !window.jarvisNotify._ariaNotificationsWrapped) {
        window.__ariaDesktopNotifyRaw = window.jarvisNotify;
      }
    }
  }

  function hookDesktopThroughPipeline() {
    wrapDesktopRaw();
    const raw = window.__ariaDesktopNotifyRaw;
    if (typeof raw !== "function") return;
    if (window.jarvisNotify?._ariaNotificationsWrapped) return;
    const wrapped = function (title, body) {
      if (window.__ariaActivitySuppressNotify) {
        return raw(title, body);
      }
      publish(
        {
          title: String(title || "Notification"),
          summary: String(body || ""),
          severity: "warning",
          source: "desktop",
          category: "notification",
          type: "desktop",
          desktop: true,
          toast: false,
        },
        { skipChannels: false, localOnly: false }
      ).then((result) => {
        // Desktop channel already handled inside publish when routing allows;
        // if suppressed by prefs, do nothing.
        if (result?.routing?.desktop === false) return;
      });
    };
    wrapped._ariaNotificationsWrapped = true;
    wrapped._ariaActivityWrapped = true;
    window.jarvisNotify = wrapped;
  }

  function hookToastsThroughPipeline() {
    const orig = window.showAriaToast;
    if (typeof orig !== "function" || orig._ariaNotificationsWrapped) return;
    const wrapped = function (msg, tone, ms) {
      const t = tone || "info";
      if (!window.__ariaActivitySuppressToast && (t === "err" || t === "warn" || t === "error" || t === "warning")) {
        const text = String(msg || "Notification").slice(0, 280);
        const lower = text.toLowerCase();
        let category = "notification";
        let deepLink = "";
        if (/ollama|provider|inference|model/.test(lower)) {
          category = "providers";
          deepLink = "providers";
        } else if (/document|index|ocr/.test(lower)) {
          category = "documents";
          deepLink = "documents";
        } else if (/planner|alarm|timer|task/.test(lower)) {
          category = "planner";
          deepLink = "planner";
        } else if (/calendar|schedule/.test(lower)) {
          category = "calendar";
          deepLink = "calendar";
        } else if (/job|comfy|video|image gen|gallery/.test(lower)) {
          category = "job";
          deepLink = "jobs";
        }
        // Ingest to activity via local store; toast already showing
        const prefs = _prefs || {};
        const sev = t === "err" || t === "error" ? "error" : "warning";
        const route = routeLocal({ severity: sev, source: "toast", category }, prefs);
        if (route.activity) {
          ingestActivity({
            category,
            type: "toast",
            severity: sev,
            title: text.slice(0, 120),
            summary: text,
            source: "toast",
            deepLink,
            toast: false,
            desktop: false,
          });
        }
        // Soft tips gate
        if (prefs.soft_tips === false && sev === "info") return;
        if (prefs.enabled === false) return;
        if (prefs.toast_enabled === false) return;
        if (route.quiet && sev !== "error" && sev !== "critical") return;
      }
      return orig.apply(this, arguments);
    };
    wrapped._ariaNotificationsWrapped = true;
    wrapped._ariaActivityWrapped = true;
    window.showAriaToast = wrapped;
  }

  function init() {
    fetchPrefs(true).then(() => {
      hookToastsThroughPipeline();
      wrapDesktopRaw();
      hookDesktopThroughPipeline();
    });
    // Drain product outboxes periodically
    const drain = () => {
      if (document.hidden) return;
      drainOutboxes();
    };
    setTimeout(drain, 3500);
    setInterval(drain, 45000);
    // Re-hook after late script loads (notify.js)
    [800, 2500, 6000].forEach((ms) =>
      setTimeout(() => {
        wrapDesktopRaw();
        hookDesktopThroughPipeline();
        hookToastsThroughPipeline();
      }, ms)
    );
  }

  const api = {
    publish,
    add,
    push,
    open,
    drainOutboxes,
    loadDigest,
    fetchPrefs,
    routeLocal,
    unread: () => window.AriaActivity?.unread?.() || store()?.unreadCount?.() || 0,
    summarizeUnread: () => window.AriaActivity?.summarizeUnread?.() || store()?.summarizeUnread?.() || "",
  };

  window.AriaNotifications = api;

  // Ensure Activity Center compatibility aliases without replacing the inbox UI API
  function ensureActivityAliases() {
    const A = window.AriaActivity;
    if (!A) return;
    if (typeof A.add !== "function") {
      A.add = (e) => (typeof A.publish === "function" ? A.publish(e) : store()?.publish?.(e));
    }
    if (typeof A.push !== "function") {
      A.push = (e) => (typeof A.publish === "function" ? A.publish(e) : store()?.push?.(e));
    }
  }
  ensureActivityAliases();
  [500, 2000].forEach((ms) => setTimeout(ensureActivityAliases, ms));

  window.openNotifications = (filter) => api.open(filter);

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
