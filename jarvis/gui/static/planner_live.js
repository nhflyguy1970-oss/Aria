/** Planner live layer — tick notifications, countdown, Daily Focus, keyboard, menus. */
(function () {
  "use strict";

  const TICK_MS = 4000;
  const COUNTDOWN_MS = 1000;
  let tickTimer = null;
  let countdownTimer = null;
  let lastSnapshot = null;
  let undoAvailable = false;

  function $(id) {
    return document.getElementById(id);
  }

  function playNotifySound() {
    try {
      const prefs = window._plannerPrefs || {};
      if (prefs.notify_sound === false) return;
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      const ctx = new Ctx();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = 880;
      g.gain.value = 0.04;
      o.connect(g);
      g.connect(ctx.destination);
      o.start();
      setTimeout(() => {
        o.stop();
        ctx.close?.();
      }, 180);
    } catch (_) {
      /* ignore */
    }
  }

  let pendingNotes = [];

  function deliverNotification(note) {
    const title = note.title || (note.type === "alarm" ? "Planner alarm" : "Planner timer");
    const msg = note.message || "Reminder";
    try {
      window.__ariaActivitySuppressToast = true;
      window.__ariaActivitySuppressNotify = true;
      try {
        window.showAriaToast?.(msg, "warn", 6000);
        window.jarvisNotify?.(title, msg);
      } finally {
        window.__ariaActivitySuppressToast = false;
        window.__ariaActivitySuppressNotify = false;
      }
      window.AriaActivity?.push?.({
        kind: "planner",
        category: "planner",
        type: note.type === "alarm" ? "reminder" : "reminder",
        tone: "warn",
        title,
        detail: msg,
        source: "planner",
        deepLink: "planner",
        action: () => window.AriaActions?.planner?.open?.() || window.switchToView?.("planner"),
      });
      playNotifySound();
      return true;
    } catch (err) {
      console.warn("planner notify delivery failed", err);
      return false;
    }
  }

  function flushPendingNotes() {
    if (!pendingNotes.length) return;
    const left = [];
    pendingNotes.forEach((n) => {
      if (!deliverNotification(n)) left.push(n);
    });
    pendingNotes = left.slice(-20);
  }

  async function pollTick() {
    if (document.hidden && !window.isNativeApp?.()) {
      // Still poll lightly when hidden so alarms remain trustworthy in desktop/browser tabs
    }
    flushPendingNotes();
    try {
      const res = await fetch("/api/planner/tick", { method: "POST", cache: "no-store" });
      const data = await res.json().catch(() => ({}));
      const notes = data.notifications || [];
      notes.forEach((note) => {
        if (!deliverNotification(note)) pendingNotes.push(note);
      });
      if (notes.length) {
        window.loadPlanner?.();
        window.AriaPlannerLive?.refreshFocus?.();
      }
    } catch (err) {
      console.warn("planner tick failed", err);
      // retry next interval
    }
  }

  function fmtRemaining(sec) {
    const s = Math.max(0, Math.floor(sec));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const r = s % 60;
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
    return `${m}:${String(r).padStart(2, "0")}`;
  }

  function tickCountdowns() {
    document.querySelectorAll("[data-timer-ends]").forEach((el) => {
      if (el.dataset.paused === "1") return;
      const ends = el.dataset.timerEnds;
      if (!ends) return;
      const rem = Math.max(0, Math.floor((Date.parse(ends) - Date.now()) / 1000));
      const label = el.dataset.timerLabel || "timer";
      const clock = el.querySelector(".planner-timer-clock");
      if (clock) clock.textContent = fmtRemaining(rem);
      else {
        const base = el.querySelector(".planner-row-main");
        if (base) base.textContent = `${label} — ${fmtRemaining(rem)}`;
      }
      if (rem <= 0) el.classList.add("planner-row--done");
    });
  }

  async function api(url, opts = {}) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.error || res.statusText);
    return data;
  }

  async function refreshFocus() {
    const host = $("plannerDailyFocus");
    if (!host) return;
    try {
      const data = await api("/api/planner/focus");
      const esc = (s) =>
        String(s ?? "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/"/g, "&quot;");
      const top = (data.top_priorities || [])
        .map((t, i) => `<li><span class="planner-focus-rank">${i + 1}</span> ${esc(t.text)}</li>`)
        .join("") || "<li class='muted'>No open tasks — add one below</li>";
      const events = (data.events || [])
        .map((e) => `<li>${esc((e.start_time || "").slice(11, 16))} ${esc(e.title)}</li>`)
        .join("") || "<li class='muted'>No events today</li>";
      const timers = (data.timers || [])
        .map((t) => `<li>${esc(t.label || "timer")} · ${fmtRemaining(t.remaining_seconds || 0)}${t.paused ? " (paused)" : ""}</li>`)
        .join("") || "<li class='muted'>No running timers</li>";
      const alarms = (data.alarms || [])
        .map((a) => `<li>${esc(a.label || "alarm")} @ ${esc((a.fire_at || "").slice(11, 16))}</li>`)
        .join("") || "<li class='muted'>No upcoming alarms</li>";
      const risk = (data.tasks_at_risk || [])
        .map((t) => `<li class="planner-risk">${esc(t.text)}</li>`)
        .join("") || "<li class='muted'>Nothing at risk</li>";
      const next = data.suggested_next?.label || "Add a task or start focus";
      const health = data.health || {};
      host.innerHTML = `
        <div class="planner-focus-head">
          <div>
            <p class="planner-focus-kicker">Daily Focus</p>
            <h3>Today’s day ops</h3>
            <p class="muted">Planner = actionable work · Journal = notes · Calendar = commitments</p>
          </div>
          <div class="planner-focus-health status-${esc(health.status || "healthy")}">
            ${esc(health.status || "healthy")} · ${health.open_tasks || 0} tasks · ~${data.focus_minutes_available != null ? data.focus_minutes_available : "—"}m focus
          </div>
        </div>
        <div class="planner-focus-grid">
          <section><h4>Top 3</h4><ul>${top}</ul></section>
          <section><h4>Events</h4><ul>${events}</ul></section>
          <section><h4>Timers</h4><ul>${timers}</ul></section>
          <section><h4>Alarms</h4><ul>${alarms}</ul></section>
          <section><h4>At risk</h4><ul>${risk}</ul></section>
          <section><h4>Next</h4><p class="planner-next">${esc(next)}</p>
            ${(data.recently_completed || []).length ? `<p class="muted tiny">Done: ${(data.recently_completed || []).slice(0, 3).map((c) => esc(c.text)).join(" · ")}</p>` : ""}
            ${data.morning_briefing ? `<p class="muted tiny planner-brief-snip">${esc(String(data.morning_briefing).slice(0, 180))}</p>` : ""}
          </section>
        </div>
        <div class="planner-focus-actions" role="toolbar" aria-label="Daily Focus actions">
          <button type="button" class="apply-btn small" data-pf="triage">Plan My Day</button>
          <button type="button" class="ghost-btn small" data-pf="focus">Start Focus Session</button>
          <button type="button" class="ghost-btn small" data-pf="morning">Review Morning Plan</button>
          <button type="button" class="ghost-btn small" data-pf="repri">Reprioritize</button>
          <button type="button" class="ghost-btn small" data-pf="ask">Ask Aria</button>
          <button type="button" class="ghost-btn small" data-pf="cal">Calendar</button>
          <button type="button" class="ghost-btn small" data-pf="journal">Journal</button>
          <button type="button" class="ghost-btn small" data-pf="docs">Documents</button>
          <button type="button" class="ghost-btn small" data-pf="vision">Vision capture</button>
          <button type="button" class="ghost-btn small" data-pf="sched">Suggest schedule</button>
          <button type="button" class="ghost-btn small" data-pf="undo" title="Undo last Planner delete">Undo</button>
        </div>
        <div id="plannerTriagePanel" class="planner-triage-panel hidden" aria-live="polite"></div>
      `;
      host.querySelectorAll("[data-pf]").forEach((btn) => {
        btn.addEventListener("click", () => handleFocusAction(btn.dataset.pf));
      });
    } catch (e) {
      host.innerHTML = `<p class="muted">Daily Focus unavailable: ${e.message}</p>`;
    }
  }

  async function handleFocusAction(action) {
    try {
      if (action === "triage") {
        const panel = $("plannerTriagePanel");
        if (panel) {
          panel.classList.remove("hidden");
          panel.innerHTML = "<p class='muted'>Planning your day…</p>";
        }
        const data = await api("/api/planner/triage", { method: "POST" });
        if (panel) {
          const rec = (data.recommendations || []).map((r) => `<li>${r}</li>`).join("");
          const sched = (data.suggested_schedule || [])
            .map((s) => `<li>${s.when || "—"} · ${s.title}</li>`)
            .join("");
          panel.innerHTML = `
            <h4>Morning triage <span class="muted">confidence ${(data.confidence * 100).toFixed(0)}%</span></h4>
            <p class="muted">Recommendations (review before acting)</p>
            <ul>${rec || "<li class='muted'>None</li>"}</ul>
            <p class="muted">Suggested schedule</p>
            <ul>${sched || "<li class='muted'>None</li>"}</ul>
          `;
        }
        window.showAriaToast?.("Morning triage ready", "ok", 2500);
      } else if (action === "focus") {
        const useHa = window._plannerPrefs?.ha_focus_enabled;
        await api("/api/planner/focus/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ duration: "25 minutes", label: "Focus", use_ha: !!useHa }),
        });
        window.showAriaToast?.("Focus session started", "ok", 2500);
        window.loadPlanner?.();
        refreshFocus();
      } else if (action === "morning") {
        window.jarvisAskAria?.("morning briefing", { autoSend: true, returnView: "planner" });
      } else if (action === "repri") {
        window.jarvisAskAria?.("Help me reprioritize my planner tasks for today", {
          autoSend: true,
          returnView: "planner",
        });
      } else if (action === "ask") {
        window.jarvisAskAria?.("What should I focus on in Planner today?", {
          autoSend: true,
          returnView: "planner",
        });
      } else if (action === "cal") window.switchToView?.("calendar");
      else if (action === "journal") window.switchToView?.("journal");
      else if (action === "docs") window.switchToView?.("documents");
      else if (action === "vision") {
        const path = prompt("Path to whiteboard / screenshot / note image:");
        if (!path) return;
        const data = await api("/api/planner/vision/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path }),
        });
        const candidates = data.candidates || [];
        if (!candidates.length) {
          window.showAriaToast?.(data.message || "No tasks found", "warn", 4000);
          return;
        }
        const ok = confirm(`Import ${candidates.length} candidate task(s) into Planner?`);
        if (!ok) return;
        const imp = await api("/api/planner/vision/import", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidates }),
        });
        window.showAriaToast?.(`Imported ${imp.count || 0} task(s)`, "ok", 3000);
        window.loadPlanner?.();
        refreshFocus();
      } else if (action === "sched") {
        const data = await api("/api/planner/schedule/suggest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        const s = (data.suggestions || [])[0];
        if (!s) {
          window.showAriaToast?.("No schedule suggestions", "info", 3000);
          return;
        }
        const conf = confirm(
          `Suggest scheduling “${s.task}” at ${String(s.suggested_start || "").slice(11, 16)}?\n(Requires confirmation — will create a Planner event)`,
        );
        if (!conf) return;
        await api("/api/planner/schedule/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ suggestion: s }),
        });
        window.showAriaToast?.("Event created from suggestion", "ok", 3000);
        window.loadPlanner?.();
        refreshFocus();
      } else if (action === "undo") {
        const data = await api("/api/planner/undo", { method: "POST" });
        window.showAriaToast?.(data.ok ? "Undone" : data.message || "Nothing to undo", data.ok ? "ok" : "info", 2500);
        window.loadPlanner?.();
        refreshFocus();
      }
    } catch (e) {
      window.showAriaToast?.(e.message || "Action failed", "err", 4000);
    }
  }

  function start() {
    if (!tickTimer) tickTimer = setInterval(pollTick, TICK_MS);
    if (!countdownTimer) countdownTimer = setInterval(tickCountdowns, COUNTDOWN_MS);
    setTimeout(pollTick, 1200);
    fetch("/api/planner/prefs")
      .then((r) => r.json())
      .then((p) => {
        window._plannerPrefs = p;
      })
      .catch(() => {});
  }

  function stop() {
    if (tickTimer) clearInterval(tickTimer);
    if (countdownTimer) clearInterval(countdownTimer);
    tickTimer = null;
    countdownTimer = null;
  }

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) pollTick();
  });

  window.AriaPlannerLive = {
    start,
    stop,
    refreshFocus,
    pollTick,
    fmtRemaining,
    api,
    setSnapshot: (s) => {
      lastSnapshot = s;
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
