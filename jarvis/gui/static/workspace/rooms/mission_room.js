/**
 * Native Mission Room (Phase 5) — quiet ops presence.
 * Not an 18-tab workstation panel. Backend /api/mission-control unchanged.
 */
(function () {
  "use strict";

  const ROOM_ID = "missionRoom";
  let _active = false;
  let _data = null;
  let _poll = null;

  const kit = () => window.AriaRoomKit;
  const esc = (s) => kit().esc(s);
  const api = (url, opts) => kit().fetchJson(url, opts);

  function root() {
    return document.getElementById(ROOM_ID);
  }

  function buildShell() {
    const el = kit().ensureRoot(ROOM_ID, "mission-room");
    el.setAttribute("aria-label", "Mission");
    if (el.dataset.shellBuilt === "1") return el;
    el.innerHTML = [
      kit().atmosphereHtml(),
      kit().presenceHtml("· Ops", "Listening quietly"),
      '<div class="mission-room__body">',
      '  <main class="mission-room__stage">',
      '    <div class="mission-room__hero" id="missionRoomHero"></div>',
      '    <div class="mission-room__grid" id="missionRoomGrid"></div>',
      "  </main>",
      "</div>",
      '<button type="button" class="nr-overflow-btn" id="missionRoomOverflowBtn" aria-label="More">···</button>',
      '<div class="nr-overflow" id="missionRoomOverflow" hidden>',
      '  <button type="button" data-m-act="refresh">Refresh</button>',
      '  <button type="button" data-m-act="recover">Recover provider</button>',
      '  <button type="button" data-m-act="restart">Restart Aria</button>',
      '  <button type="button" data-m-act="repair">Guided repair</button>',
      '  <button type="button" data-m-act="integrity">Integrity</button>',
      '  <button type="button" data-m-act="chat">Ask Aria</button>',
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
    el.querySelector("#missionRoomOverflowBtn")?.addEventListener("click", (e) => {
      e.stopPropagation();
      const p = el.querySelector("#missionRoomOverflow");
      p.hidden = !p.hidden;
    });
    el.querySelector("#missionRoomOverflow")?.addEventListener("click", async (e) => {
      const act = e.target.closest("[data-m-act]")?.dataset.mAct;
      if (!act) return;
      el.querySelector("#missionRoomOverflow").hidden = true;
      if (act === "refresh") load();
      if (act === "recover") recoverProvider();
      if (act === "restart") restartAria();
      if (act === "repair") window.AriaActivityEngine?.start?.("repair", { confirmHighStakes: false });
      if (act === "integrity") window.AriaActivityEngine?.start?.("integrity", { confirmHighStakes: false });
      if (act === "chat") window.AriaActivityEngine?.start?.("converse", { confirmHighStakes: false });
    });
  }

  async function recoverProvider() {
    kit().setStatus(root(), "Recovering provider…");
    try {
      const out = await api("/api/provider/recover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: "OPERATOR_RECOVER", auto: true }),
      });
      kit().setStatus(root(), out.usable ? "Provider usable" : "Provider still down");
      window.showAriaToast?.(
        out.usable ? "Provider recovered" : out.operator_message || "Recovery incomplete",
        out.usable ? "ok" : "warn",
        3500,
      );
      await load();
    } catch (err) {
      kit().setStatus(root(), err.message || "Recover failed");
    }
  }

  async function restartAria() {
    const msg = "Restart Aria server now? Open work will reconnect after a few seconds.";
    if (window.ariaConfirm) {
      if (!(await window.ariaConfirm(msg, { title: "Restart Aria", okLabel: "Restart" }))) return;
    } else if (!window.confirm?.(msg)) {
      return;
    }
    kit().setStatus(root(), "Restarting…");
    try {
      await fetch("/api/jarvis/restart-server", { method: "POST" });
      window.showAriaToast?.("Aria is restarting…", "info", 4000);
    } catch (err) {
      kit().setStatus(root(), err.message || "Restart failed");
    }
  }

  function render() {
    const hero = root()?.querySelector("#missionRoomHero");
    const grid = root()?.querySelector("#missionRoomGrid");
    if (!hero || !grid) return;
    const o = _data?.overview || {};
    const status = o.platform_status || o.status || "unknown";
    const attn = Array.isArray(o.needs_attention) ? o.needs_attention : [];
    const clear = attn.length === 1 && /all clear/i.test(attn[0]);
    const ph = _data?.inference || _data?.providers || {};
    const provider =
      o.inference_provider ||
      ph.provider ||
      ph.current_provider ||
      "ollama";
    const model = o.current_model || ph.current_model || ph.model || "";

    hero.innerHTML =
      `<p class="mission-room__kicker">${esc(status)}</p>` +
      "<h1>System presence</h1>" +
      `<p class="mission-room__pulse">${
        clear || !attn.length
          ? "Everything quiet. Nothing needs you right now."
          : esc(attn.slice(0, 3).join(" · "))
      }</p>`;

    const jobs = o.active_jobs ?? _data?.jobs?.active ?? 0;
    const gpu = o.gpu || "";
    const vram = o.free_vram_mb != null ? `${o.free_vram_mb} MB free VRAM` : "";
    const ready = o.production_readiness != null ? `${o.production_readiness}% ready` : "";
    const phase = o.phase?.phase || o.phase || "";

    grid.innerHTML = [
      card("Attention", clear || !attn.length ? "All clear" : attn.slice(0, 5).join("\n")),
      card("Jobs", String(jobs)),
      card("Providers", [provider, model].filter(Boolean).join(" · ") || "—"),
      card("Hardware", [gpu, vram].filter(Boolean).join(" · ") || "—"),
      card("Readiness", [ready, phase].filter(Boolean).join(" · ") || "—"),
    ].join("");
  }

  function card(title, body) {
    return (
      `<section class="mission-room__card"><h2>${esc(title)}</h2>` +
      `<p>${esc(body).replace(/\n/g, "<br>")}</p></section>`
    );
  }

  async function load() {
    kit().setStatus(root(), "Reading the system…");
    try {
      _data = await api("/api/mission-control");
      render();
      const o = _data?.overview || {};
      const attn = o.needs_attention || [];
      const clear = attn.length === 1 && /all clear/i.test(attn[0]);
      kit().setStatus(root(), clear ? "All clear" : "Listening quietly");
    } catch (err) {
      kit().setStatus(root(), err.message || "Mission unavailable");
    }
  }

  function startPoll() {
    stopPoll();
    _poll = setInterval(() => {
      if (!_active || document.hidden) return;
      if (window.AriaHouse?.current?.() !== "mission") return;
      load();
    }, 30000);
  }

  function stopPoll() {
    if (_poll) clearInterval(_poll);
    _poll = null;
  }

  async function enter() {
    kit().exitOthers("mission");
    const el = buildShell();
    document.body.classList.add("house-room", "house-mission", "native-mission");
    document.body.dataset.room = "mission";
    window.AriaStage.mount(el, "mission");
    _active = true;
    window.AriaWorkspaceChrome?.apply?.("systems");
    await load();
    startPoll();
    try {
      window.AriaLivingFamiliarity?.recordVisit?.({ room: "mission", view: "workstation" });
    } catch (_) {
      /* ignore */
    }
    window.dispatchEvent(new CustomEvent("aria-native-room", { detail: { room: "mission", native: true } }));
  }

  function exit() {
    if (!_active) return;
    _active = false;
    stopPoll();
    document.body.classList.remove("native-mission");
  }

  window.AriaMissionRoom = {
    enter,
    exit,
    isActive: () => _active,
    version: "5.0.2-oc",
    legacyBridge: false,
  };
  window.AriaRoomKit?.register?.("mission", () => window.AriaMissionRoom);
})();
