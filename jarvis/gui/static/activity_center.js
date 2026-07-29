/** Activity Center UI — Aria durable OS event inbox (not Job Center / not Mission Control). */
(function () {
  "use strict";

  let activeIndex = 0;
  let helpOpen = false;
  /** @type {object[]} */
  let rows = [];

  function $(id) {
    return document.getElementById(id);
  }

  function store() {
    return window.AriaActivityStore;
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function announce(msg) {
    const live = $("activityCenterLive");
    if (live) live.textContent = msg || "";
  }

  function relativeTime(ts) {
    const d = Date.now() - ts;
    if (d < 60_000) return "just now";
    if (d < 3600_000) return `${Math.floor(d / 60_000)}m ago`;
    if (d < 86400_000) return `${Math.floor(d / 3600_000)}h ago`;
    return new Date(ts).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  function dayKey(ts) {
    const d = new Date(ts);
    return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
  }

  function dayLabel(ts) {
    const d = new Date(ts);
    const today = new Date();
    const yday = new Date(Date.now() - 86400_000);
    if (dayKey(ts) === dayKey(today.getTime())) return "Today";
    if (dayKey(ts) === dayKey(yday.getTime())) return "Yesterday";
    return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  }

  function severityIcon(sev) {
    const s = String(sev || "").toLowerCase();
    if (s === "critical" || s === "error") return "!";
    if (s === "warning") return "▲";
    if (s === "success") return "✓";
    return "·";
  }

  function bumpBadge() {
    const n = store()?.unreadCount?.() || 0;
    const badge = $("activityCenterBadge");
    const status = $("statusSegActivity");
    if (badge) {
      badge.textContent = n > 0 ? String(n) : "";
      badge.classList.toggle("hidden", n === 0);
      badge.setAttribute("aria-label", n > 0 ? `${n} unread` : "No unread");
    }
    if (status) {
      status.textContent = n > 0 ? `${n} alert${n === 1 ? "" : "s"}` : "quiet";
      status.className = `status-seg ${n > 0 ? "status-degraded" : ""}`.trim();
    }
    const corr = $("activityCorrelation");
    if (corr) {
      const groups = store()?.correlate?.() || [];
      if (!groups.length) {
        corr.classList.add("hidden");
        corr.textContent = "";
      } else {
        corr.classList.remove("hidden");
        corr.innerHTML = groups.map((g) =>
          `<button type="button" class="ghost-btn tiny" data-corr="${escapeHtml(g.key)}">${escapeHtml(g.title)} · ${g.count}</button>`
        ).join(" ");
        corr.querySelectorAll("[data-corr]").forEach((btn) => {
          btn.addEventListener("click", () => {
            store()?.setFilter?.("unread");
            syncFilterUi();
            render();
            announce(btn.textContent || "Correlation");
          });
        });
      }
    }
    const summary = $("activityUnreadSummary");
    if (summary) {
      const text = store()?.summarizeUnread?.() || "";
      summary.textContent = text;
    }
  }

  function syncFilterUi() {
    const filter = store()?.getPrefs?.().filter || "all";
    document.querySelectorAll("[data-activity-filter]").forEach((b) => {
      b.classList.toggle("active", (b.dataset.activityFilter || "all") === filter);
    });
    const q = store()?.getPrefs?.().query || "";
    if ($("activitySearchInput") && $("activitySearchInput").value !== q) {
      $("activitySearchInput").value = q;
    }
  }

  function render() {
    const list = $("activityCenterList");
    if (!list || !store()) return;
    rows = store().queryEvents();
    list.replaceChildren();
    activeIndex = Math.min(activeIndex, Math.max(0, rows.length - 1));

    if (!rows.length) {
      list.innerHTML = `<li class="empty-state" role="presentation"><div class="empty-state-icon" aria-hidden="true">◎</div>`
        + `<p class="empty-state-title">Inbox is clear</p>`
        + `<p class="muted">Notifications uses this Activity Center inbox for durable attention — not Job Center (live work) and not Mission Control (health). Items stay until you mark them read or dismiss them.</p>`
        + `<div class="empty-state-actions">`
        + `<button type="button" class="apply-btn small" id="activityEmptyJobsBtn">Open Job center</button>`
        + `<button type="button" class="ghost-btn small" id="activityEmptyMcBtn">Mission Control</button>`
        + `<button type="button" class="ghost-btn small" id="activityEmptyChatBtn">Ask what’s wrong</button>`
        + `</div></li>`;
      $("activityEmptyJobsBtn")?.addEventListener("click", () => {
        close();
        window.AriaActions?.mission?.jobs?.();
      });
      $("activityEmptyMcBtn")?.addEventListener("click", () => {
        close();
        window.AriaActions?.goView?.("workstation");
      });
      $("activityEmptyChatBtn")?.addEventListener("click", () => {
        close();
        window.AriaActivityActions?.whatsWrong?.();
      });
      bumpBadge();
      return;
    }

    let lastDay = "";
    rows.forEach((e, i) => {
      const dk = dayKey(e.timestamp);
      if (dk !== lastDay) {
        lastDay = dk;
        const sep = document.createElement("li");
        sep.className = "activity-day-sep";
        sep.setAttribute("role", "presentation");
        sep.textContent = dayLabel(e.timestamp);
        list.appendChild(sep);
      }
      const li = document.createElement("li");
      li.className = `activity-item activity-${e.tone || "info"}${e.read ? "" : " unread"}${e.pinned ? " pinned" : ""}`;
      li.id = `activityItem-${i}`;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === activeIndex ? "true" : "false");
      li.tabIndex = -1;
      li.dataset.index = String(i);
      li.dataset.id = e.id;
      const count = e.metadata?.count > 1 ? ` ×${e.metadata.count}` : "";
      const abs = new Date(e.timestamp).toLocaleString();
      li.innerHTML = `<span class="activity-sev" aria-hidden="true">${severityIcon(e.severity)}</span>`
        + `<div class="activity-item-main">`
        + `<strong>${escapeHtml(e.title)}${escapeHtml(count)}</strong>`
        + `<span class="muted activity-meta">${escapeHtml(e.severity)} · ${escapeHtml(e.category)} · ${escapeHtml(relativeTime(e.timestamp))}`
        + `${e.source ? ` · ${escapeHtml(e.source)}` : ""}`
        + `${e.pinned ? " · pinned" : ""}`
        + ` · <time datetime="${new Date(e.timestamp).toISOString()}" title="${escapeHtml(abs)}">${escapeHtml(abs)}</time>`
        + `</span>`
        + `${e.summary || e.detail ? `<p class="muted">${escapeHtml((e.summary || e.detail).slice(0, 220))}</p>` : ""}`
        + `</div>`;
      const actions = document.createElement("div");
      actions.className = "activity-item-actions";
      const mkBtn = (label, fn, title) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "ghost-btn tiny";
        b.textContent = label;
        if (title) b.title = title;
        b.addEventListener("click", (ev) => {
          ev.stopPropagation();
          fn();
        });
        return b;
      };
      actions.appendChild(mkBtn("Open", () => {
        window.AriaActivityActions?.openDeepLink?.(e.deepLink || e.source, e);
        close();
      }, "Open destination"));
      actions.appendChild(mkBtn(e.read ? "Unread" : "Read", () => {
        if (e.read) store().markUnread(e.id);
        else store().markRead(e.id, true);
        render();
        announce(e.read ? "Marked unread" : "Marked read");
      }, "M mark read · U unread"));
      actions.appendChild(mkBtn(e.pinned ? "Unpin" : "Pin", () => {
        store().togglePin(e.id);
        render();
      }, "P pin"));
      actions.appendChild(mkBtn("Ask Aria", () => {
        close();
        window.AriaActivityActions?.askAbout?.(e);
      }));
      actions.appendChild(mkBtn("Fix", () => {
        close();
        window.AriaActivityActions?.suggestFix?.(e);
      }, "Suggested fix"));
      actions.appendChild(mkBtn("Retry", () => {
        window.AriaActivityActions?.retry?.(e);
      }));
      actions.appendChild(mkBtn("Snooze", () => {
        store().snooze(e.id, 60 * 60 * 1000);
        render();
        announce("Snoozed 1 hour");
      }));
      actions.appendChild(mkBtn("Mute", () => {
        store().muteSource(e.source || e.category, true);
        window.showAriaToast?.(`Muted ${e.source || e.category}`, "ok", 2500);
        render();
      }, "Mute this source"));
      actions.appendChild(mkBtn("Dismiss", () => {
        store().dismiss(e.id);
        render();
      }));
      actions.appendChild(mkBtn("Copy", () => {
        navigator.clipboard?.writeText(`${e.title}\n${e.detail || e.summary || ""}`).then(
          () => window.showAriaToast?.("Copied", "ok", 1500),
          () => window.showAriaToast?.("Copy failed", "err", 2500),
        );
      }));
      li.appendChild(actions);
      li.addEventListener("click", (ev) => {
        if (ev.target.closest("button")) return;
        activeIndex = i;
        syncActive();
      });
      li.addEventListener("dblclick", () => {
        window.AriaActivityActions?.openDeepLink?.(e.deepLink || e.source, e);
        close();
      });
      list.appendChild(li);
    });
    // IMPORTANT: do NOT mark read on render
    syncActive();
    bumpBadge();
    const countEl = $("activityResultCount");
    if (countEl) countEl.textContent = `${rows.length} shown · ${store().unreadCount()} unread`;
  }

  function syncActive() {
    const list = $("activityCenterList");
    if (!list) return;
    list.querySelectorAll(".activity-item").forEach((el) => {
      const i = Number(el.dataset.index);
      const on = i === activeIndex;
      el.classList.toggle("active", on);
      el.setAttribute("aria-selected", on ? "true" : "false");
    });
    const active = $(`activityItem-${activeIndex}`);
    if (active) {
      list.setAttribute("aria-activedescendant", active.id);
      active.scrollIntoView({ block: "nearest" });
    }
  }

  function open() {
    const modal = $("activityCenterModal");
    if (!modal) return;
    modal.classList.remove("hidden");
    syncFilterUi();
    render();
    bumpBadge();
    const list = $("activityCenterList");
    const saved = store()?.getPrefs?.().scrollTop || 0;
    if (list && saved > 0) list.scrollTop = saved;
    $("activitySearchInput")?.focus();
    announce(`Activity Center open. ${store()?.unreadCount?.() || 0} unread.`);
  }

  function close() {
    $("activityCenterModal")?.classList.add("hidden");
    $("activityHelp")?.classList.add("hidden");
    helpOpen = false;
  }

  function isOpen() {
    return !$("activityCenterModal")?.classList.contains("hidden");
  }

  async function syncJobs() {
    const status = $("activitySyncStatus");
    if (status) {
      status.textContent = "Checking jobs…";
      status.classList.remove("hidden");
    }
    try {
      const res = await fetch("/api/jobs?limit=12", { cache: "no-store" });
      if (!res.ok) {
        if (status) {
          status.textContent = "Job sync unavailable";
          setTimeout(() => status.classList.add("hidden"), 2500);
        }
        return;
      }
      const data = await res.json().catch(() => ({}));
      const jobs = data.jobs || data.items || [];
      jobs.slice(0, 8).forEach((j) => {
        const id = j.id || j.job_id || j.name;
        const jobStatus = (j.status || j.state || "").toLowerCase();
        if (!id || !jobStatus) return;
        const exists = store().all().some((e) =>
          e.metadata?.jobId === id && String(e.metadata?.jobStatus || "").includes(jobStatus)
        );
        if (exists) return;
        if (jobStatus.includes("fail") || jobStatus.includes("error")) {
          store().publish({
            category: "job",
            type: "job_failed",
            severity: "error",
            title: `Job failed: ${j.name || id}`,
            summary: j.message || j.error || jobStatus,
            detail: j.message || j.error || jobStatus,
            source: "jobs",
            deepLink: `job:${id}`,
            metadata: { jobId: id, jobStatus },
          });
        } else if (/done|complete|success/.test(jobStatus)) {
          store().publish({
            category: "job",
            type: "job_finished",
            severity: "success",
            title: `Job finished: ${j.name || id}`,
            summary: jobStatus,
            source: "jobs",
            deepLink: `job:${id}`,
            metadata: { jobId: id, jobStatus },
            // successes start read to reduce noise, unless user wants them
            read: true,
          });
        }
      });
      if (status) {
        status.textContent = "Jobs synced";
        setTimeout(() => status.classList.add("hidden"), 1500);
      }
      if (isOpen()) render();
      else bumpBadge();
    } catch {
      if (status) {
        status.textContent = "Job sync offline";
        setTimeout(() => status.classList.add("hidden"), 2500);
      }
    }
  }

  function hookToasts() {
    const orig = window.showAriaToast;
    if (typeof orig !== "function" || orig._ariaActivityWrapped) return;
    const wrapped = function (msg, tone, ms) {
      const t = tone || "info";
      if (!window.__ariaActivitySuppressToast && (t === "err" || t === "warn" || t === "error" || t === "warning")) {
        const text = String(msg || "Notification").slice(0, 280);
        const lower = text.toLowerCase();
        let category = "notification";
        let deepLink = "";
        if (/ollama|provider|inference|model/.test(lower)) { category = "providers"; deepLink = "providers"; }
        else if (/document|index|ocr/.test(lower)) { category = "documents"; deepLink = "documents"; }
        else if (/planner|alarm|timer|task/.test(lower)) { category = "planner"; deepLink = "planner"; }
        else if (/calendar|schedule/.test(lower)) { category = "calendar"; deepLink = "calendar"; }
        else if (/journal/.test(lower)) { category = "journal"; deepLink = "journal"; }
        else if (/connection|memgraph|kg /.test(lower)) { category = "connections"; deepLink = "connections"; }
        else if (/home assistant|ha |device/.test(lower)) { category = "home"; deepLink = "ha"; }
        else if (/job|comfy|video|image gen|gallery/.test(lower)) { category = "job"; deepLink = "jobs"; }
        else if (/voice|whisper|wake/.test(lower)) { category = "voice"; deepLink = "voice"; }
        else if (/chat|stream|reply/.test(lower)) { category = "chat"; deepLink = "chat"; }
        store()?.publish?.({
          category,
          type: "toast",
          severity: t === "err" || t === "error" ? "error" : "warning",
          title: text.slice(0, 120),
          summary: text,
          source: "toast",
          deepLink,
        });
      }
      return orig.apply(this, arguments);
    };
    wrapped._ariaActivityWrapped = true;
    window.showAriaToast = wrapped;
  }

  function hookDesktopNotify() {
    const orig = window.jarvisNotify;
    if (typeof orig !== "function" || orig._ariaActivityWrapped) return;
    window.jarvisNotify = function (title, body) {
      let item = null;
      if (!window.__ariaActivitySuppressNotify) {
        item = store()?.publish?.({
          category: "notification",
          type: "desktop",
          severity: "warning",
          title: String(title || "Notification"),
          summary: String(body || ""),
          source: "desktop",
        });
      }
      if (!("Notification" in window)) return;
      const show = () => {
        const n = new Notification(title, { body, tag: item?.id || undefined });
        n.onclick = () => {
          window.focus?.();
          open();
          if (item?.id) {
            const idx = rows.findIndex((r) => r.id === item.id);
            if (idx >= 0) activeIndex = idx;
            render();
          }
        };
      };
      if (Notification.permission === "granted") show();
      else if (Notification.permission !== "denied") {
        Notification.requestPermission().then((p) => { if (p === "granted") show(); });
      }
    };
    window.jarvisNotify._ariaActivityWrapped = true;
  }

  function confirmClear(kind) {
    const msg = kind === "read"
      ? "Clear all read events? Pinned items are kept."
      : "Clear all events? Pinned items are kept. This cannot be undone unless you use Undo.";
    const run = () => {
      if (kind === "read") store().clearRead();
      else store().clearAll();
      render();
      announce("Cleared");
    };
    if (window.ariaConfirm) {
      window.ariaConfirm(msg, { title: "Clear Activity", okLabel: "Clear" }).then((ok) => { if (ok) run(); });
      return;
    }
    if (window.confirm(msg)) run();
  }

  function onListKey(e) {
    if (!isOpen()) return;
    if (e.target && (e.target.id === "activitySearchInput" || e.target.tagName === "INPUT")) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        $("activityCenterList")?.focus?.();
        syncActive();
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!rows.length) return;
      activeIndex = (activeIndex + 1) % rows.length;
      syncActive();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!rows.length) return;
      activeIndex = (activeIndex - 1 + rows.length) % rows.length;
      syncActive();
    } else if (e.key === "Enter") {
      e.preventDefault();
      const row = rows[activeIndex];
      if (row) {
        window.AriaActivityActions?.openDeepLink?.(row.deepLink || row.source, row);
        close();
      }
    } else if (e.key === "Delete" || e.key === "Backspace") {
      if (e.target?.tagName === "INPUT") return;
      e.preventDefault();
      const row = rows[activeIndex];
      if (row) {
        store().dismiss(row.id);
        render();
      }
    } else if (e.key === "m" || e.key === "M") {
      if (e.target?.tagName === "INPUT") return;
      e.preventDefault();
      const row = rows[activeIndex];
      if (row) {
        store().markRead(row.id, true);
        render();
      }
    } else if (e.key === "u" || e.key === "U") {
      if (e.target?.tagName === "INPUT") return;
      e.preventDefault();
      const row = rows[activeIndex];
      if (row) {
        store().markUnread(row.id);
        render();
      }
    } else if (e.key === "p" || e.key === "P") {
      if (e.target?.tagName === "INPUT") return;
      e.preventDefault();
      const row = rows[activeIndex];
      if (row) {
        store().togglePin(row.id);
        render();
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      close();
    } else if (e.key === "?" && !e.ctrlKey) {
      if (e.target?.tagName === "INPUT" && $("activitySearchInput")?.value) return;
      e.preventDefault();
      helpOpen = !helpOpen;
      $("activityHelp")?.classList.toggle("hidden", !helpOpen);
    } else if (e.key === "/" && e.target?.tagName !== "INPUT") {
      e.preventDefault();
      $("activitySearchInput")?.focus();
    } else if (e.key === "z" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (store().undo()) {
        render();
        announce("Undo");
      }
    }
  }

  function seedWelcome() {
    const flagged = localStorage.getItem("aria_activity_welcome_v1");
    if (flagged) return;
    store()?.publish?.({
      category: "system",
      type: "welcome",
      severity: "info",
      title: "Notifications is your alert inbox",
      summary: "Activity Center keeps durable events until you resolve them. Toasts are temporary. Job Center tracks live work; Mission Control tracks health.",
      source: "system",
      deepLink: "",
      read: true,
    });
    try {
      localStorage.setItem("aria_activity_welcome_v1", "1");
    } catch {
      /* ignore */
    }
  }

  function init() {
    hookToasts();
    hookDesktopNotify();
    seedWelcome();
    bumpBadge();

    $("activityCenterBtn")?.addEventListener("click", open);
    $("statusSegActivityWrap")?.addEventListener("click", open);
    $("activityCenterCloseBtn")?.addEventListener("click", close);
    $("activityMarkReadBtn")?.addEventListener("click", () => {
      store().markAllRead();
      render();
      announce("All marked read");
    });
    $("activityClearReadBtn")?.addEventListener("click", () => confirmClear("read"));
    $("activityClearBtn")?.addEventListener("click", () => confirmClear("all"));
    $("activityUndoBtn")?.addEventListener("click", () => {
      if (store().undo()) render();
      else window.showAriaToast?.("Nothing to undo", "warn", 2000);
    });
    $("activityExportBtn")?.addEventListener("click", async () => {
      const text = store().exportLog();
      try {
        await navigator.clipboard.writeText(text);
        window.showAriaToast?.("Activity log copied", "ok", 2500);
      } catch {
        window.showAriaToast?.("Could not copy export", "err", 3000);
      }
    });
    $("activitySummarizeBtn")?.addEventListener("click", () => {
      close();
      window.AriaActivityActions?.whatsWrong?.();
    });
    $("activitySearchInput")?.addEventListener("input", () => {
      store().setQuery($("activitySearchInput").value || "");
      render();
    });
    $("activityCenterList")?.addEventListener("scroll", () => {
      store()?.setScrollTop?.($("activityCenterList").scrollTop || 0);
    }, { passive: true });
    document.querySelectorAll("[data-activity-filter]").forEach((btn) => {
      btn.addEventListener("click", () => {
        store().setFilter(btn.dataset.activityFilter || "all");
        syncFilterUi();
        render();
      });
    });
    $("activityCenterModal")?.addEventListener("keydown", onListKey);
    $("activityCenterList")?.setAttribute("tabindex", "0");
    $("activityCenterList")?.setAttribute("role", "listbox");
    $("activityCenterList")?.setAttribute("aria-label", "Activity events");

    window.addEventListener("aria-activity-change", () => {
      bumpBadge();
      if (isOpen()) render();
      else {
        const n = store()?.unreadCount?.() || 0;
        if (n > 0) announce(`${n} unread in Activity Center`);
      }
    });

    setInterval(() => {
      if (document.hidden) return;
      syncJobs();
    }, 90000);
    setTimeout(syncJobs, 4000);
  }

  // Public API — store handles data; this module owns UI
  window.AriaActivity = {
    push: (e) => {
      if (window.AriaNotifications?.publish) {
        return window.AriaNotifications.publish(e, { localOnly: true, skipChannels: true });
      }
      return store()?.push?.(e);
    },
    publish: (e) => {
      if (window.AriaNotifications?.publish) {
        return window.AriaNotifications.publish(e, { localOnly: true, skipChannels: true });
      }
      return store()?.publish?.(e);
    },
    // Compatibility alias — never leave .add undefined
    add: (e) => window.AriaActivity.publish(e),
    open,
    close,
    syncJobs,
    hookToasts,
    hookDesktopNotify,
    unread: () => store()?.unreadCount?.() || 0,
    summarizeUnread: () => store()?.summarizeUnread?.() || "",
    whatsWrong: () => window.AriaActivityActions?.whatsWrong?.(),
  };

  // Notifications product alias for the inbox
  window.AriaNotificationsInbox = { open, close };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
