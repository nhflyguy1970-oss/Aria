/**
 * Living Room Presence (Phase 3.6).
 * Quiet companionship — not UI, not notifications, not fake life.
 * Only truthful context. Silence is allowed.
 */
(function () {
  "use strict";

  const LAST_SEEN_KEY = "aria_lr_presence_last_seen";
  const LAST_ARRIVAL_KEY = "aria_lr_presence_last_arrival_day";
  const AWARENESS_KEY = "aria_lr_presence_awareness_day";

  let _ranForSession = false;

  function hourBucket(d = new Date()) {
    const h = d.getHours();
    if (h >= 5 && h < 12) return "morning";
    if (h >= 12 && h < 17) return "afternoon";
    if (h >= 17 && h < 22) return "evening";
    return "night";
  }

  function applyTimeAtmosphere() {
    const body = document.body;
    if (!body) return;
    body.dataset.tod = hourBucket();
    // Prefer Living Interface weather if already set; never invent
    try {
      window.AriaLivingInterface?.refreshWeather?.(false);
    } catch (_) {
      /* optional */
    }
  }

  function msSinceLastSeen() {
    try {
      const raw = localStorage.getItem(LAST_SEEN_KEY);
      if (!raw) return Infinity;
      const t = Number(raw);
      if (!Number.isFinite(t)) return Infinity;
      return Date.now() - t;
    } catch (_) {
      return Infinity;
    }
  }

  function touchSeen() {
    try {
      localStorage.setItem(LAST_SEEN_KEY, String(Date.now()));
    } catch (_) {
      /* ignore */
    }
  }

  function todayKey() {
    const d = new Date();
    return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  }

  /** Sometimes presence is only being there. */
  function preferSilence(awayMs) {
    // Just stepped out briefly — no speech
    if (awayMs < 20 * 60 * 1000) return true;
    // ~1 in 5 arrivals: pure silence
    try {
      const n = (Number(localStorage.getItem("aria_lr_presence_salt") || "0") + 1) % 5;
      localStorage.setItem("aria_lr_presence_salt", String(n));
      if (n === 0 && awayMs < 12 * 60 * 60 * 1000) return true;
    } catch (_) {
      /* ignore */
    }
    return false;
  }

  function arrivalLine(awayMs, tod) {
    const firstToday = (() => {
      try {
        return localStorage.getItem(LAST_ARRIVAL_KEY) !== todayKey();
      } catch (_) {
        return true;
      }
    })();

    if (awayMs > 8 * 60 * 60 * 1000 || firstToday) {
      if (tod === "morning") return "Morning, Jeff.";
      if (tod === "afternoon") return "Good afternoon.";
      if (tod === "evening") return "Evening, Jeff.";
      return "I'm glad you're here.";
    }
    if (awayMs > 2 * 60 * 60 * 1000) {
      const opts = ["Welcome back.", "I'm glad you're back.", "I've been here."];
      return opts[Math.floor(Date.now() / 86400000) % opts.length];
    }
    if (awayMs > 20 * 60 * 1000) return "Welcome back.";
    return "";
  }

  async function fetchJson(url, ms = 4500) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), ms);
    try {
      const res = await fetch(url, { cache: "no-store", signal: ctrl.signal });
      if (!res.ok) return null;
      return await res.json();
    } catch (_) {
      return null;
    } finally {
      clearTimeout(t);
    }
  }

  /**
   * Truthful whispers only — max two, never a checklist.
   * Never invent completed work. Never brag about old history.
   */
  async function gatherAwareness() {
    const lines = [];
    const push = (line) => {
      const t = String(line || "").trim();
      if (!t || t.length > 100) return;
      lines.push(t.endsWith(".") ? t : `${t}.`);
    };

    // Familiarity — occasional, pattern-matched, never invented
    let familiar = null;
    try {
      familiar = window.AriaLivingFamiliarity?.suggestWhisper?.() || null;
      if (familiar?.line) {
        push(familiar.line);
        window.AriaLivingFamiliarity?.commitWhisper?.(familiar.id);
      }
    } catch (_) {
      familiar = null;
    }

    let home = null;
    try {
      if (window.AriaSharedFetch?.dashboardHome) {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 4000);
        try {
          home = await window.AriaSharedFetch.dashboardHome({ stale_ok: true, ttlMs: 2500, signal: ctrl.signal });
        } finally {
          clearTimeout(t);
        }
      }
    } catch (_) {
      home = null;
    }
    if (!home) home = await fetchJson("/api/dashboard/home?stale_ok=true", 4000);
    if (home?.ok !== false && home) {
      // 1) Attention that genuinely matters
      const att = home.attention;
      if (att && !att.empty && Array.isArray(att.items) && att.items[0]) {
        const item = att.items[0];
        const title = String(item.title || item.message || item.summary || "").trim();
        if (title) push(title);
      }

      // 2) Weather only when it changes the day
      const w = home.weather || {};
      const cond = String(w.condition || "").trim();
      const summary = String(w.summary || "").trim();
      const loc = String(w.location || "").trim();
      const place = loc ? ` in ${loc}` : "";
      const blob = `${cond} ${summary}`;
      if (/fog/i.test(blob)) push(`It's foggy${place}`);
      else if (/rain|storm|thunder|shower/i.test(blob)) {
        push(place ? `Rain looks likely${place}` : "It looks like rain later");
      } else if (/snow/i.test(blob)) {
        push(place ? `Snow is in the air${place}` : "Snow is in the air");
      }

      // 3) Calendar — upcoming today only (not past)
      const cal = (home.widgets || []).find((x) => x.id === "calendar_summary");
      const items = cal?.payload?.items || home.planner?.events_today || [];
      const now = new Date();
      const minsNow = now.getHours() * 60 + now.getMinutes();
      for (const ev of items) {
        if (lines.length >= 2) break;
        const title = String(ev.title || ev.name || "").trim();
        const time = String(ev.time || ev.start || "").trim();
        if (!title) continue;
        let mins = null;
        const m = time.match(/^(\d{1,2}):(\d{2})/);
        if (m) mins = Number(m[1]) * 60 + Number(m[2]);
        if (mins != null && mins + 30 < minsNow) continue; // already past
        if (time) push(`${title} at ${time}`);
        else push(title);
        break;
      }

      if (home.planner?.events_today_count > 0 && Array.isArray(home.planner.event_preview)) {
        if (lines.length < 2 && home.planner.event_preview[0]) {
          push(String(home.planner.event_preview[0]));
        }
      }

      // 4) One open task — only if we still have a slot and nothing louder
      if (lines.length < 2 && home.planner?.enabled && Number(home.planner.active_tasks) > 0) {
        const task = String((home.planner.task_preview || [])[0] || "").trim();
        if (task) push(`Still open: ${task}`);
      }
    }

    const jobs = await fetchJson("/api/jobs");
    if (jobs?.ok) {
      if (jobs.media?.busy && jobs.media.active_label) {
        if (lines.length < 2) push(`Still working on ${String(jobs.media.active_label).slice(0, 48)}`);
      } else if (jobs.coding?.busy) {
        if (lines.length < 2) push("A coding job is still running");
      } else {
        // Recently finished — only if truly recent and successful
        const recent = Array.isArray(jobs.recent) ? jobs.recent : [];
        const now = Date.now() / 1000;
        let whispered = {};
        try {
          whispered = JSON.parse(localStorage.getItem("aria_lr_presence_job_whisper") || "{}") || {};
        } catch (_) {
          whispered = {};
        }
        for (const j of recent) {
          if (lines.length >= 2) break;
          const id = String(j.id || "");
          if (!id || whispered[id]) continue;
          const started = Number(j.started || 0);
          if (!started || now - started > 6 * 3600) continue;
          const ok = j.ok === true || j.result_ok === true;
          const err = String(j.error || j.message || "");
          if (!j.done || !ok) continue;
          if (/removed|interrupted|fail/i.test(err)) continue;
          const kind = String(j.kind || j.queue || "");
          const label = String(j.label || "").toLowerCase();
          if (/image|generate_image|media/i.test(kind + label)) {
            push("The image you generated finished");
          } else if (/video/i.test(kind + label)) {
            push("Your video job finished");
          } else if (j.label) {
            push(`${String(j.label).slice(0, 40)} finished`);
          } else continue;
          whispered[id] = true;
          try {
            localStorage.setItem("aria_lr_presence_job_whisper", JSON.stringify(whispered));
          } catch (_) {
            /* ignore */
          }
          break;
        }
      }
    }

    // Dedupe & cap at two
    const seen = new Set();
    const out = [];
    for (const line of lines) {
      const k = line.toLowerCase();
      if (seen.has(k)) continue;
      seen.add(k);
      out.push(line);
      if (out.length >= 2) break;
    }
    return out;
  }

  function renderPresenceMessage(arrival, awareness) {
    const parts = [];
    if (arrival) {
      parts.push(`<p class="lr-presence-arrival">${escapeHtml(arrival)}</p>`);
    }
    for (const line of awareness || []) {
      parts.push(`<p class="lr-presence-whisper">${escapeHtml(line)}</p>`);
    }
    if (!parts.length) {
      // Pure presence — no speech
      return '<p class="lr-presence-quiet" aria-hidden="true"></p>';
    }
    return parts.join("");
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function applyToWelcome(html) {
    const msgs = document.getElementById("messages");
    if (!msgs) return;

    let welcome = msgs.querySelector(".message.welcome");
    if (!welcome) {
      // Prefer first assistant bubble if thread is only greeting / empty-ish
      const assistants = msgs.querySelectorAll(".message.assistant");
      if (assistants.length === 1 && !msgs.querySelector(".message.user")) {
        welcome = assistants[0];
        welcome.classList.add("welcome");
      }
    }
    // Only rewrite when Jeff hasn't started talking — never overwrite a real thread
    if (msgs.querySelector(".message.user")) return;

    if (!welcome) {
      // Create a quiet presence turn
      if (typeof window.addMessage === "function") {
        window.addMessage("assistant", "·", { type: "info" });
        welcome = msgs.querySelector(".message.assistant:last-child");
        welcome?.classList.add("welcome");
      }
    }
    if (!welcome) return;

    const body = welcome.querySelector(".msg-body") || welcome.querySelector(".bubble");
    if (!body) return;
    body.dataset.lrWelcome = "1";
    body.dataset.lrPresence = "1";
    body.innerHTML = html;
    const av = welcome.querySelector(".avatar");
    if (av) av.textContent = "A";

    // Strip action chrome
    welcome.querySelectorAll(".message-actions, .chat-reply-actions, .msg-timestamp").forEach((el) => el.remove());
  }

  function setStatusQuiet(text) {
    window.AriaLivingRoom?.setStatus?.(text);
  }

  async function enactArrival({ returning = false } = {}) {
    if (!window.AriaLivingRoom?.isActive?.()) return;
    applyTimeAtmosphere();

    const awayMs = msSinceLastSeen();
    const tod = hourBucket();
    const silent = preferSilence(returning ? awayMs : awayMs);

    let arrival = silent ? "" : arrivalLine(awayMs, tod);
    let awareness = [];

    // Awareness at most once per calendar day unless returning after a long absence
    let mayAware = false;
    try {
      const day = todayKey();
      const last = localStorage.getItem(AWARENESS_KEY);
      if (last !== day || awayMs > 4 * 60 * 60 * 1000) mayAware = true;
    } catch (_) {
      mayAware = true;
    }

    if (mayAware && !silent) {
      awareness = await gatherAwareness();
      try {
        localStorage.setItem(AWARENESS_KEY, todayKey());
      } catch (_) {
        /* ignore */
      }
    }

    // If silent and no awareness, leave welcome as pure quiet presence
    if (silent && !awareness.length) {
      applyToWelcome(renderPresenceMessage("", []));
      setStatusQuiet("I'm here");
      setTimeout(() => {
        if (window.AriaLivingRoom?.isActive?.()) setStatusQuiet("Listening quietly");
      }, 4500);
    } else {
      applyToWelcome(renderPresenceMessage(arrival, awareness));
      if (arrival) {
        setStatusQuiet(arrival.replace(/\.$/, ""));
        setTimeout(() => {
          if (window.AriaLivingRoom?.isActive?.()) setStatusQuiet("Listening quietly");
        }, 5000);
      } else {
        setStatusQuiet("Listening quietly");
      }
    }

    try {
      localStorage.setItem(LAST_ARRIVAL_KEY, todayKey());
    } catch (_) {
      /* ignore */
    }
    touchSeen();
    _ranForSession = true;

    // Soft invites: hide when we spoke; keep faint when silent
    const box = document.getElementById("suggestions");
    if (box) {
      if (arrival || awareness.length) {
        box.classList.remove("lr-suggestions-soft");
        box.innerHTML = "";
        box.style.opacity = "";
      } else {
        box.style.opacity = "0.35";
      }
    }

    // Atmosphere: reflect what we truthfully observed
    if (awareness.some((l) => /foggy/i.test(l))) document.body.dataset.weather = "fog";
    else if (awareness.some((l) => /rain/i.test(l))) document.body.dataset.weather = "rain";
    else if (awareness.some((l) => /snow/i.test(l))) document.body.dataset.weather = "snow";

    window.dispatchEvent(
      new CustomEvent("aria-living-presence", {
        detail: { arrival, awareness, silent, tod, awayMs, returning },
      })
    );
  }

  function onVisibility() {
    if (document.visibilityState !== "visible") {
      touchSeen();
      return;
    }
    if (!window.AriaLivingRoom?.isActive?.()) return;
    const away = msSinceLastSeen();
    if (away > 25 * 60 * 1000) {
      enactArrival({ returning: true });
    } else {
      touchSeen();
    }
  }

  function boot() {
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("aria-living-room", (e) => {
      if (e.detail?.active) {
        if (_ranForSession) return;
        // Delay so welcome/branch settle; presence owns the first turn
        setTimeout(() => enactArrival({ returning: false }), 700);
      } else {
        touchSeen();
        _ranForSession = false;
      }
    });
    // Heartbeat while present — room was occupied
    setInterval(() => {
      if (window.AriaLivingRoom?.isActive?.() && document.visibilityState === "visible") {
        touchSeen();
      }
    }, 60 * 1000);
  }

  window.AriaLivingPresence = {
    enactArrival,
    gatherAwareness,
    applyTimeAtmosphere,
    version: "3.6.0-presence",
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
