/**
 * Native Health Room (Phase 5) — quiet wellness place.
 * Not a 30-tab clinic panel. Backend /api/health/* unchanged.
 */
(function () {
  "use strict";

  const ROOM_ID = "healthRoom";
  let _active = false;
  let _home = null;
  let _timeline = [];

  const kit = () => window.AriaRoomKit;
  const esc = (s) => kit().esc(s);
  const api = (url, opts) => kit().fetchJson(url, opts);

  function root() {
    return document.getElementById(ROOM_ID);
  }

  function buildShell() {
    const el = kit().ensureRoot(ROOM_ID, "health-room");
    el.setAttribute("aria-label", "Health");
    if (el.dataset.shellBuilt === "1") return el;
    el.innerHTML = [
      kit().atmosphereHtml(),
      kit().presenceHtml("· Wellness", "Listening quietly"),
      '<div class="health-room__body">',
      '  <main class="health-room__stage">',
      '    <div class="health-room__hero" id="healthRoomHero"></div>',
      '    <form class="health-room__checkin" id="healthRoomCheckin" autocomplete="off">',
      "      <h2>How are you today?</h2>",
      '      <div class="health-room__fields">',
      '        <label>Energy <input name="energy" type="number" min="1" max="10" placeholder="1–10" /></label>',
      '        <label>Mood <input name="mood" type="text" placeholder="calm, tired…" /></label>',
      '        <label>Sleep (hrs) <input name="sleep_hours" type="number" min="0" max="24" step="0.5" /></label>',
      '        <label>Note <input name="note" type="text" placeholder="Anything worth remembering" /></label>',
      "      </div>",
      '      <button type="submit" class="health-room__submit">Log check-in</button>',
      "    </form>",
      '    <p class="health-room__disclaimer" id="healthRoomDisclaimer"></p>',
      "  </main>",
      '  <aside class="health-room__side" aria-label="Today">',
      '    <div id="healthRoomSide"></div>',
      "  </aside>",
      "</div>",
      '<button type="button" class="nr-overflow-btn" id="healthRoomOverflowBtn" aria-label="More">···</button>',
      '<div class="nr-overflow" id="healthRoomOverflow" hidden>',
      '  <button type="button" data-h-act="refresh">Refresh</button>',
      '  <button type="button" data-h-act="doctor">Doctor visit summary</button>',
      '  <button type="button" data-h-act="emergency">Emergency card</button>',
      "</div>",
    ].join("");
    el.dataset.shellBuilt = "1";
    if (!el.parentElement) document.body.appendChild(el);
    wire(el);
    return el;
  }

  function wire(el) {
    if (el.dataset.wired) return;
    el.dataset.wired = "1";
    el.querySelector("#healthRoomCheckin")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = {};
      fd.forEach((v, k) => {
        if (String(v).trim()) body[k] = v;
      });
      kit().setStatus(root(), "Saving…");
      try {
        await api("/api/health/checkin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        e.target.reset();
        await loadHome();
        kit().setStatus(root(), "Noted. Listening quietly");
      } catch (err) {
        kit().setStatus(root(), err.message || "Check-in failed");
      }
    });
    el.querySelector("#healthRoomOverflowBtn")?.addEventListener("click", (e) => {
      e.stopPropagation();
      const p = el.querySelector("#healthRoomOverflow");
      p.hidden = !p.hidden;
    });
    el.querySelector("#healthRoomOverflow")?.addEventListener("click", (e) => {
      const act = e.target.closest("[data-h-act]")?.dataset.hAct;
      if (!act) return;
      el.querySelector("#healthRoomOverflow").hidden = true;
      if (act === "refresh") loadHome();
      if (act === "doctor") window.open("/api/health/doctor-visit", "_blank");
      if (act === "emergency") window.open("/api/health/emergency", "_blank");
    });
  }

  function render() {
    const hero = root()?.querySelector("#healthRoomHero");
    const side = root()?.querySelector("#healthRoomSide");
    const disc = root()?.querySelector("#healthRoomDisclaimer");
    if (!hero) return;
    const h = _home || {};
    if (disc) disc.textContent = h.disclaimer || "";

    const checkin = h.checkin;
    const today = h.today || "";
    hero.innerHTML =
      `<p class="health-room__kicker">${esc(today || "Today")}</p>` +
      "<h1>How you’re doing</h1>" +
      (checkin
        ? `<p class="health-room__pulse">Last check-in is here. Energy ${esc(checkin.energy ?? "—")}, mood ${esc(checkin.mood || "—")}.</p>`
        : '<p class="health-room__pulse">No check-in yet today. The room is ready when you are.</p>');

    const meds = h.medications || [];
    const rem = h.reminders || [];
    const obs = h.observations || [];
    const timeline = h.timeline || _timeline || [];
    side.innerHTML =
      '<section class="health-room__card"><h2>Medications</h2>' +
      (meds.length
        ? `<ul>${meds.slice(0, 8).map((m) => `<li>${esc(m.name || m.medication || m.title || "Item")}</li>`).join("")}</ul>`
        : "<p class=\"muted\">None on record</p>") +
      "</section>" +
      '<section class="health-room__card"><h2>Reminders</h2>' +
      (rem.length
        ? `<ul>${rem.slice(0, 5).map((r) => `<li>${esc(r.title || r.text || r.message || "Reminder")}</li>`).join("")}</ul>`
        : "<p class=\"muted\">Nothing waiting</p>") +
      "</section>" +
      '<section class="health-room__card"><h2>Timeline</h2>' +
      (timeline.length
        ? `<ul>${timeline
            .slice(0, 8)
            .map((ev) => `<li>${esc(ev.title || ev.summary || ev.day || "Event")}${ev.detail ? ` — ${esc(String(ev.detail).slice(0, 80))}` : ""}</li>`)
            .join("")}</ul>`
        : "<p class=\"muted\">No history yet</p>") +
      "</section>" +
      (obs.length
        ? '<section class="health-room__card"><h2>Noticing</h2><ul>' +
          obs
            .slice(0, 3)
            .map((o) => `<li>${esc(o.summary || o.text || o.message || "")}</li>`)
            .join("") +
          "</ul></section>"
        : "");
  }

  async function loadHome() {
    kit().setStatus(root(), "Gathering today’s picture…");
    try {
      const [home, tl] = await Promise.all([
        api("/api/health/home"),
        api("/api/health/timeline?limit=12").catch(() => ({ items: [] })),
      ]);
      _home = home;
      _timeline = tl.items || tl.events || tl.timeline || [];
      if (_home && !_home.timeline) _home.timeline = _timeline;
      render();
      kit().setStatus(root(), "Listening quietly");
    } catch (err) {
      kit().setStatus(root(), err.message || "Health unavailable");
      const hero = root()?.querySelector("#healthRoomHero");
      if (hero) {
        hero.innerHTML = "<h1>Health</h1><p class=\"health-room__pulse\">Couldn’t load today’s picture.</p>";
      }
    }
  }

  async function enter() {
    kit().exitOthers("health");
    const el = buildShell();
    document.body.classList.add("house-room", "house-health", "native-health");
    document.body.dataset.room = "health";
    window.AriaStage.mount(el, "health");
    _active = true;
    window.AriaWorkspaceChrome?.apply?.("minimal");
    await loadHome();
    try {
      window.AriaLivingFamiliarity?.recordVisit?.({ room: "health", view: "health" });
    } catch (_) {
      /* ignore */
    }
    window.dispatchEvent(new CustomEvent("aria-native-room", { detail: { room: "health", native: true } }));
  }

  function exit() {
    if (!_active) return;
    _active = false;
    document.body.classList.remove("native-health");
  }

  window.AriaHealthRoom = {
    enter,
    exit,
    isActive: () => _active,
    version: "5.0.3-oc",
    legacyBridge: false,
  };
  window.AriaRoomKit?.register?.("health", () => window.AriaHealthRoom);
})();
