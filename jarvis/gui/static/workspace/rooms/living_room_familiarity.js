/**
 * Living Room Familiarity (Phase 3.7).
 * Quiet memory of how Jeff lives — observations only.
 * Never scripts, never launches, never invents habits.
 */
(function () {
  "use strict";

  const STORE_KEY = "aria_lr_familiarity_v1";
  const MAX_VISITS = 180;
  const MIN_HITS = 4; // days with the pattern before we may speak
  const WHISPER_COOLDOWN_DAYS = 3;

  function todBucket(d = new Date()) {
    const h = d.getHours();
    if (h >= 5 && h < 12) return "morning";
    if (h >= 12 && h < 17) return "afternoon";
    if (h >= 17 && h < 22) return "evening";
    return "night";
  }

  function dayKey(ts = Date.now()) {
    const d = new Date(ts);
    return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
  }

  function dow(ts = Date.now()) {
    return new Date(ts).getDay(); // 0 Sun
  }

  function isWeekend(ts = Date.now()) {
    const d = dow(ts);
    return d === 0 || d === 6;
  }

  function load() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return { visits: [], whispers: {} };
      const data = JSON.parse(raw);
      return {
        visits: Array.isArray(data.visits) ? data.visits : [],
        whispers: data.whispers && typeof data.whispers === "object" ? data.whispers : {},
      };
    } catch (_) {
      return { visits: [], whispers: {} };
    }
  }

  function save(data) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(data));
    } catch (_) {
      /* ignore */
    }
  }

  function normalizeRoom(room, activity, view) {
    const a = String(activity || "").toLowerCase();
    const r = String(room || view || "").toLowerCase();
    if (a === "coding" || r === "coding" || r === "projects") return "coding";
    if (a === "health" || a === "doctor_visit" || r === "health") return "health";
    if (a === "flytying" || r === "flytying") return "flytying";
    if (a === "research" || a === "reading" || r === "documents" || r === "search") return "research";
    if (a === "planning" || a === "calendar" || r === "planner" || r === "calendar") return "planning";
    if (a === "image_creation" || r === "gallery") return "gallery";
    if (a === "memory" || r === "memory") return "memory";
    if (a === "voice" || r === "voice") return "voice";
    if (a === "systems" || a === "repair" || a === "integrity" || r === "mission" || r === "repair" || r === "integrity")
      return "mission";
    if (a === "automation" || r === "automation") return "automation";
    if (a === "providers" || r === "providers" || r === "models") return "providers";
    if (a === "home_automation" || r === "home_automation" || r === "presence" || r === "home") return "home";
    if (a === "projects" || r === "projects") return "projects";
    if (a === "converse" || r === "chat") return "converse";
    if (r) return r;
    return "converse";
  }

  function recordVisit(partial = {}) {
    const data = load();
    const now = Date.now();
    const room = normalizeRoom(
      partial.room || document.body?.dataset?.room,
      partial.activity || document.body?.dataset?.activity,
      partial.view
    );
    const weather = String(partial.weather || document.body?.dataset?.weather || "").toLowerCase();
    const tod = partial.tod || todBucket();
    const day = dayKey(now);

    // One visit per room per day-bucket (keep room lived-in without spam)
    const last = data.visits[data.visits.length - 1];
    if (last && last.day === day && last.room === room && last.tod === tod) {
      last.ts = now;
      last.weather = weather || last.weather;
      save(data);
      applyLivedIn(data);
      return data;
    }

    data.visits.push({
      ts: now,
      day,
      tod,
      dow: dow(now),
      weekend: isWeekend(now),
      room,
      weather,
    });
    if (data.visits.length > MAX_VISITS) {
      data.visits = data.visits.slice(-MAX_VISITS);
    }
    save(data);
    applyLivedIn(data);
    return data;
  }

  /** Distinct days a predicate matched. Seeded prefs do not count — truth only. */
  function distinctDays(visits, pred) {
    const days = new Set();
    for (const v of visits) {
      if (v.seeded) continue;
      if (pred(v)) days.add(v.day);
    }
    return days.size;
  }

  function patterns(data) {
    const v = data.visits || [];
    const out = [];

    const codingMornings = distinctDays(v, (x) => x.room === "coding" && x.tod === "morning");
    if (codingMornings >= MIN_HITS) {
      out.push({
        id: "coding_morning",
        hits: codingMornings,
        matchesToday: () => todBucket() === "morning",
        line: "Looks like another coding morning.",
      });
    }

    const healthMorning = distinctDays(v, (x) => x.room === "health" && x.tod === "morning");
    if (healthMorning >= MIN_HITS) {
      out.push({
        id: "health_morning",
        hits: healthMorning,
        matchesToday: () => todBucket() === "morning",
        line: "Morning health check feels like part of the rhythm.",
      });
    }

    const flyRainWeekend = distinctDays(
      v,
      (x) => x.room === "flytying" && x.weekend && /rain|fog|cloud/i.test(x.weather || "")
    );
    if (flyRainWeekend >= Math.max(3, MIN_HITS - 1)) {
      out.push({
        id: "fly_rain_weekend",
        hits: flyRainWeekend,
        matchesToday: () =>
          isWeekend() && /rain|fog|cloud/i.test(document.body?.dataset?.weather || ""),
        line: "A soft day like this usually finds you at the vise.",
      });
    }

    const researchAfternoon = distinctDays(v, (x) => x.room === "research" && x.tod === "afternoon");
    if (researchAfternoon >= MIN_HITS) {
      out.push({
        id: "research_afternoon",
        hits: researchAfternoon,
        matchesToday: () => todBucket() === "afternoon",
        line: "Afternoon research again — familiar pace.",
      });
    }

    const planningMorning = distinctDays(v, (x) => x.room === "planning" && x.tod === "morning");
    if (planningMorning >= MIN_HITS) {
      out.push({
        id: "planning_morning",
        hits: planningMorning,
        matchesToday: () => todBucket() === "morning",
        line: "Planning before the day runs — same comfortable start.",
      });
    }

    const lateCoding = distinctDays(v, (x) => x.room === "coding" && (x.tod === "evening" || x.tod === "night"));
    if (lateCoding >= MIN_HITS) {
      out.push({
        id: "coding_late",
        hits: lateCoding,
        matchesToday: () => {
          const t = todBucket();
          return t === "evening" || t === "night";
        },
        line: "Late coding stretch — the room knows this hour.",
      });
    }

    const converseEvening = distinctDays(v, (x) => x.room === "converse" && x.tod === "evening");
    if (converseEvening >= MIN_HITS) {
      out.push({
        id: "converse_evening",
        hits: converseEvening,
        matchesToday: () => todBucket() === "evening",
        line: "Evening conversation — glad you're back in the chair.",
      });
    }

    // Sort by strength
    out.sort((a, b) => b.hits - a.hits);
    return out;
  }

  function daysBetween(a, b) {
    const da = new Date(a);
    const db = new Date(b);
    return Math.abs((db - da) / (24 * 3600 * 1000));
  }

  /**
   * At most one familiarity whisper, only when a real pattern matches today,
   * and only occasionally — never every day, never scripted rotation spam.
   */
  function suggestWhisper() {
    const data = load();
    const list = patterns(data).filter((p) => p.matchesToday());
    if (!list.length) return null;

    const today = dayKey();
    // Global familiarity cooldown
    const lastAny = data.whispers.__any;
    if (lastAny && daysBetween(lastAny, today) < WHISPER_COOLDOWN_DAYS) return null;

    for (const p of list) {
      const last = data.whispers[p.id];
      if (last && daysBetween(last, today) < WHISPER_COOLDOWN_DAYS + 2) continue;
      // Mark as used only when presence actually consumes — caller should commit
      return { id: p.id, line: p.line, hits: p.hits };
    }
    return null;
  }

  function commitWhisper(id) {
    if (!id) return;
    const data = load();
    const today = dayKey();
    data.whispers[id] = today;
    data.whispers.__any = today;
    save(data);
  }

  function applyLivedIn(data) {
    const body = document.body;
    if (!body) return;
    const days = new Set((data.visits || []).map((v) => v.day)).size;
    body.classList.toggle("lr-familiar", days >= 3);
    body.classList.toggle("lr-familiar-aged", days >= 14);
    body.dataset.lrFamiliarDays = String(days);
  }

  function seedFromPrefs() {
    const data = load();
    if (data.visits.length > 0) return;
    try {
      const prefs = window.AriaUiPrefs?.load?.() || {};
      const recent = prefs.recentViews || [];
      const now = Date.now();
      recent.slice(0, 12).forEach((view, i) => {
        const ts = now - (i + 1) * 36e5;
        data.visits.push({
          ts,
          day: dayKey(ts),
          tod: todBucket(new Date(ts)),
          dow: dow(ts),
          weekend: isWeekend(ts),
          room: normalizeRoom(null, null, view),
          weather: "",
          seeded: true,
        });
      });
      if (data.visits.length) save(data);
    } catch (_) {
      /* ignore */
    }
  }

  function inspect() {
    const data = load();
    return {
      visitDays: new Set(data.visits.map((v) => v.day)).size,
      visits: data.visits.length,
      patterns: patterns(data).map((p) => ({ id: p.id, hits: p.hits, today: p.matchesToday() })),
      nextWhisper: suggestWhisper(),
    };
  }

  function boot() {
    seedFromPrefs();
    applyLivedIn(load());

    // Observe life — never act on it beyond memory
    window.addEventListener("aria-activity-change", (e) => {
      const act = e.detail?.activity;
      recordVisit({
        activity: act?.id,
        room: act?.primaryRoom,
      });
    });
    window.addEventListener("aria-living-room", (e) => {
      if (e.detail?.active) recordVisit({ room: "chat", activity: "converse" });
    });
    window.addEventListener("aria-room-change", (e) => {
      recordVisit({ room: e.detail?.room, view: e.detail?.view });
    });

    // Soft wrap switchToView when available
    const wrap = () => {
      if (typeof window.switchToView !== "function" || window.switchToView.__lrFamiliar) return;
      const orig = window.switchToView;
      function wrapped(view) {
        const r = orig.apply(this, arguments);
        try {
          recordVisit({ view });
        } catch (_) {
          /* ignore */
        }
        return r;
      }
      wrapped.__lrFamiliar = true;
      window.switchToView = wrapped;
    };
    wrap();
    setTimeout(wrap, 1500);

    // Heartbeat while Living Room occupied — ages the room gently
    setInterval(() => {
      if (window.AriaLivingRoom?.isActive?.() && document.visibilityState === "visible") {
        recordVisit({ room: "chat", activity: "converse" });
      }
    }, 15 * 60 * 1000);
  }

  window.AriaLivingFamiliarity = {
    recordVisit,
    suggestWhisper,
    commitWhisper,
    inspect,
    patterns: () => patterns(load()),
    version: "3.7.0-familiarity",
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
