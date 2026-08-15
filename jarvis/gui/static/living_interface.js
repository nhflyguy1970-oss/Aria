/** Aria Living Interface — Phase 2 atmosphere (time, weather, season, soft sound). */
(function () {
  const VIEW_TO_ROOM = {
    chat: "chat",
    dashboard: "home",
    home: "home",
    workstation: "mission",
    mission: "mission",
    health: "health",
    flytying: "flytying",
    coding: "coding",
    documents: "documents",
    search: "search",
    gallery: "gallery",
    /* Keep Room identity — do not collapse distinct Rooms into atmosphere aliases */
    video: "video",
    meme: "meme",
    planner: "planner",
    calendar: "calendar",
    journal: "journal",
    voice: "voice",
    audio: "audio",
    browser: "browser",
    presence: "presence",
    homeAutomation: "home_automation",
    home_automation: "home_automation",
    repair: "repair",
    integrity: "integrity",
    automation: "automation",
    /* certification view is engineering-only — never map into Living Workspace Rooms */
    audit: "audit",
    security: "security",
    settings: "settings",
    models: "providers",
    projects: "projects",
    maker: "maker",
    capabilities: "capabilities",
    integrations: "integrations",
    connections: "connections",
    memory: "memory",
    vision: "vision",
    actions: "actions",
  };

  const ROOM_VOICE = {
    chat: "welcoming",
    home: "comfortable",
    mission: "precise",
    health: "reassuring",
    flytying: "adventurous",
    coding: "confident",
    documents: "thoughtful",
    search: "invisible",
    gallery: "artistic",
    video: "artistic",
    meme: "artistic",
    planner: "encouraging",
    calendar: "relaxing",
    journal: "reflective",
    voice: "warm",
    audio: "warm",
    browser: "curious",
    maker: "confident",
    vision: "thoughtful",
    repair: "calm",
    integrity: "quiet",
    home_automation: "aware",
    automation: "precise",
    settings: "comfortable",
    memory: "thoughtful",
    providers: "precise",
    projects: "confident",
    capabilities: "comfortable",
    integrations: "aware",
    connections: "thoughtful",
    audit: "calm",
    security: "calm",
    actions: "comfortable",
  };

  let _weatherAt = 0;
  let _audioCtx = null;

  function prefs() {
    return window.AriaUiPrefs?.load?.() || {};
  }

  function atmosphereOn() {
    const p = prefs();
    if (p.atmosphere === false || p.atmosphereEnabled === false) return false;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches && p.atmosphereForce !== true) {
      /* still allow static time/season tints; JS marks reduced */
    }
    return true;
  }

  function roomForView(view) {
    if (!view) return "chat";
    if (window.AriaViewRouter?.viewToRoom) return window.AriaViewRouter.viewToRoom(view);
    if (view === "mission") view = "workstation";
    if (view === "home") view = "dashboard";
    if (view === "home_automation") view = "homeAutomation";
    if (VIEW_TO_ROOM[view]) return VIEW_TO_ROOM[view];
    const rooms = window.AriaWorkspaceRegistry?.rooms;
    if (Array.isArray(rooms)) {
      const hit = rooms.find((r) => r.viewId === view || r.id === view);
      if (hit?.id) return hit.id;
    }
    return view;
  }

  function timeOfDay(d = new Date()) {
    const h = d.getHours();
    if (h >= 5 && h < 11) return "morning";
    if (h >= 11 && h < 17) return "afternoon";
    if (h >= 17 && h < 21) return "evening";
    return "night";
  }

  function seasonOf(d = new Date()) {
    const m = d.getMonth(); // 0-11
    if (m >= 2 && m <= 4) return "spring";
    if (m >= 5 && m <= 7) return "summer";
    if (m >= 8 && m <= 10) return "autumn";
    return "winter";
  }

  function classifyWeather(text) {
    const t = String(text || "").toLowerCase();
    if (!t) return "";
    if (/\b(snow|sleet|blizzard|flurries)\b/.test(t)) return "snow";
    if (/\b(rain|drizzle|shower|thunder|storm|precip)\b/.test(t)) return "rain";
    if (/\b(cloud|overcast|fog|mist|haze)\b/.test(t)) return "cloudy";
    if (/\b(sun|clear|fair|bright)\b/.test(t)) return "sunny";
    return "clear";
  }

  function applyAtmosphereFlags() {
    const body = document.body;
    if (!body) return;
    const on = atmosphereOn();
    body.dataset.atmosphere = on ? "on" : "off";
    body.dataset.tod = timeOfDay();
    const p = prefs();
    if (p.seasonAtmosphere !== false) body.dataset.season = seasonOf();
    else delete body.dataset.season;
  }

  async function refreshWeather(force) {
    const p = prefs();
    if (p.weatherAtmosphere === false) {
      delete document.body?.dataset.weather;
      return;
    }
    const now = Date.now();
    if (!force && now - _weatherAt < 50 * 60 * 1000) return;
    _weatherAt = now;
    try {
      const data =
        (await window.AriaSharedFetch?.dashboardHome?.({ ttlMs: 2500 })) ||
        (await (async () => {
          const res = await fetch("/api/dashboard/home?stale_ok=true", { cache: "no-store" });
          if (!res.ok) return null;
          return res.json();
        })());
      if (!data) return;
      const w = data.weather || (data.widgets || []).find((x) => x.id === "time_weather")?.payload?.weather || {};
      const blob = [w.condition, w.summary, w.weather_line, w.hint].filter(Boolean).join(" ");
      const kind = classifyWeather(blob);
      if (kind) document.body.dataset.weather = kind;
      else delete document.body.dataset.weather;
    } catch {
      /* optional — never block UI */
    }
  }

  function setRoom(view) {
    const room = roomForView(view);
    const body = document.body;
    if (!body) return room;
    const prev = body.dataset.room;
    const meta = window.AriaWorkspaceRegistry?.room?.(room);
    body.dataset.place = meta?.place || meta?.metaphor || room;
    if (prev !== room) {
      body.dataset.room = room;
      body.dataset.roomVoice = ROOM_VOICE[room] || "calm";
      body.setAttribute("data-living", "1");
      try {
        window.dispatchEvent(
          new CustomEvent("aria-room-change", {
            detail: { room, view, voice: body.dataset.roomVoice, previous: prev || null },
          })
        );
      } catch (_) {
        /* ignore */
      }
    }
    applyAtmosphereFlags();
    return room;
  }

  function syncFromHash() {
    if (window.AriaViewRouter?.applyingHash?.()) return;
    const view = (location.hash || "#chat").replace(/^#/, "") || "chat";
    setRoom(view);
  }

  /** Soft UI sounds — muted by default. Frequencies are gentle and short. */
  function playCue(kind) {
    const p = prefs();
    if (!p.ambientSound && !p.livingSound) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      if (!_audioCtx) _audioCtx = new AC();
      if (_audioCtx.state === "suspended") _audioCtx.resume();
      const o = _audioCtx.createOscillator();
      const g = _audioCtx.createGain();
      o.type = "sine";
      const map = {
        confirm: 520,
        notify: 440,
        paper: 380,
        soft: 300,
      };
      o.frequency.value = map[kind] || map.soft;
      g.gain.value = 0.0001;
      o.connect(g);
      g.connect(_audioCtx.destination);
      const t = _audioCtx.currentTime;
      g.gain.exponentialRampToValueAtTime(0.025, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.14);
      o.start(t);
      o.stop(t + 0.16);
    } catch {
      /* ignore */
    }
  }

  function tick() {
    applyAtmosphereFlags();
    refreshWeather(false);
  }

  window.AriaLivingInterface = {
    roomForView,
    setRoom,
    timeOfDay,
    seasonOf,
    classifyWeather,
    refreshWeather,
    playCue,
    applyAtmosphereFlags,
    rooms: Object.keys(ROOM_VOICE),
    map: VIEW_TO_ROOM,
  };

  document.addEventListener("DOMContentLoaded", () => {
    syncFromHash();
    applyAtmosphereFlags();
    refreshWeather(true);
  });
  window.addEventListener("aria-view-change", (ev) => setRoom(ev.detail?.view));
  window.addEventListener("hashchange", syncFromHash);
  window.addEventListener("aria-ui-prefs", () => {
    applyAtmosphereFlags();
    refreshWeather(true);
  });

  // Quiet periodic refresh — cheap attribute updates only
  setInterval(tick, 15 * 60 * 1000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) tick();
  });

  // Soft confirm on primary actions when sound is opted in
  document.addEventListener(
    "click",
    (ev) => {
      const t = ev.target?.closest?.(".apply-btn, .primary-btn, [data-living-confirm]");
      if (!t || t.disabled) return;
      playCue("confirm");
    },
    true
  );

  syncFromHash();
  applyAtmosphereFlags();
})();
