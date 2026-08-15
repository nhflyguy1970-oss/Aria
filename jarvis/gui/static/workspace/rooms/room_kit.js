/**
 * Shared kit for native Living Workspace Rooms (Phase 5).
 * Atmosphere, presence, fetch, registry — not a content bridge.
 */
(function () {
  "use strict";

  /** @type {Record<string, () => {enter?:Function, exit?:Function}>} */
  const _registry = Object.create(null);

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  /**
   * JSON fetch with optional AbortSignal + hard timeout.
   * Room switches abort in-flight loads so Chrome's connection pool cannot
   * wedge Integrity / Automation behind orphaned room requests.
   * Timeout aborts are distinct from navigation aborts — callers must surface them.
   */
  async function fetchJson(url, opts = {}) {
    const timeoutMs = opts.timeoutMs != null ? Number(opts.timeoutMs) : 12000;
    const parentSignal = opts.signal;
    const fetchOpts = { ...opts };
    delete fetchOpts.timeoutMs;
    delete fetchOpts.signal;

    const ctrl = new AbortController();
    let timedOut = false;
    const onParentAbort = () => ctrl.abort();
    if (parentSignal) {
      if (parentSignal.aborted) ctrl.abort();
      else parentSignal.addEventListener("abort", onParentAbort, { once: true });
    }
    const timer = setTimeout(() => {
      timedOut = true;
      ctrl.abort();
    }, Math.max(1000, timeoutMs));
    try {
      const res = await fetch(url, { ...fetchOpts, signal: ctrl.signal });
      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        /* ignore */
      }
      if (!res.ok) {
        const msg = data.message || data.detail || res.statusText || `HTTP ${res.status}`;
        const err = new Error(typeof msg === "string" ? msg : "Request failed");
        err.status = res.status;
        err.data = data;
        throw err;
      }
      return data;
    } catch (e) {
      if (e && (e.name === "AbortError" || ctrl.signal.aborted)) {
        const err = new Error(timedOut ? "That check took too long" : "Request cancelled");
        err.aborted = !timedOut;
        err.timedOut = timedOut;
        err.name = timedOut ? "TimeoutError" : "AbortError";
        throw err;
      }
      throw e;
    } finally {
      clearTimeout(timer);
      if (parentSignal) parentSignal.removeEventListener("abort", onParentAbort);
    }
  }

  function atmosphereHtml() {
    return (
      '<div class="nr-atmosphere" aria-hidden="true">' +
      '<div class="nr-atmosphere__wash"></div>' +
      '<div class="nr-atmosphere__veil"></div>' +
      '<div class="nr-atmosphere__grain"></div>' +
      "</div>"
    );
  }

  function presenceHtml(place, status) {
    return (
      '<header class="nr-presence">' +
      `<div class="nr-presence__brand">Aria <span class="nr-presence__place">${esc(place || "")}</span></div>` +
      `<div class="nr-presence__status" data-nr-status>${esc(status || "Listening quietly")}</div>` +
      "</header>"
    );
  }

  function setStatus(root, text) {
    const el = root?.querySelector?.("[data-nr-status]");
    if (el) el.textContent = text || "Listening quietly";
  }

  function ensureRoot(id, className) {
    let el = document.getElementById(id);
    if (el) return el;
    el = document.createElement("section");
    el.id = id;
    el.className = `native-room ${className || ""}`.trim();
    el.setAttribute("role", "region");
    el.dataset.nativeRoom = "1";
    return el;
  }

  function register(id, getter) {
    if (id) _registry[id] = getter;
  }

  function get(id) {
    return _registry[id]?.() || null;
  }

  function allIds() {
    return Object.keys(_registry);
  }

  function exitOthers(keepId) {
    const chat = window.AriaLivingRoom;
    if (keepId !== "chat" && chat?.exit) {
      try {
        chat.exit({ keepStage: true });
      } catch (_) {
        /* ignore */
      }
    }
    Object.keys(_registry).forEach((id) => {
      if (id === keepId) return;
      try {
        _registry[id]?.()?.exit?.();
      } catch (_) {
        /* ignore */
      }
    });
  }

  /**
   * Define a native Room module quickly.
   * spec: { id, rootId, className, bodyNativeClass, houseClass, place, chrome,
   *         overflowHtml?, buildBody(html helpers)->innerHTML, load(ctx), wire?(ctx) }
   */
  function defineRoom(spec) {
    const ROOM_ID = spec.rootId;
    let _active = false;
    let _loadGen = 0;
    /** @type {AbortController|null} */
    let _abort = null;

    function root() {
      return document.getElementById(ROOM_ID);
    }

    function buildShell() {
      const el = ensureRoot(ROOM_ID, spec.className);
      el.setAttribute("aria-label", spec.label || spec.id);
      if (el.dataset.shellBuilt === "1") return el;
      const overflow =
        spec.overflowHtml ||
        '<button type="button" data-nr-act="refresh">Refresh</button>';
      el.innerHTML = [
        atmosphereHtml(),
        presenceHtml(spec.place || "", "Listening quietly"),
        `<div class="nr-body" data-nr-body>${bodyHtml()}</div>`,
        `<button type="button" class="nr-overflow-btn" data-nr-overflow-btn aria-label="More">···</button>`,
        `<div class="nr-overflow" data-nr-overflow hidden>${overflow}</div>`,
      ].join("");
      el.dataset.shellBuilt = "1";
      if (!el.parentElement) document.body.appendChild(el);
      if (!el.dataset.wired) {
        el.dataset.wired = "1";
        el.querySelector("[data-nr-overflow-btn]")?.addEventListener("click", (e) => {
          e.stopPropagation();
          const p = el.querySelector("[data-nr-overflow]");
          if (p) p.hidden = !p.hidden;
        });
        el.querySelector("[data-nr-overflow]")?.addEventListener("click", async (e) => {
          const act = e.target.closest("[data-nr-act]")?.dataset.nrAct;
          if (!act) return;
          el.querySelector("[data-nr-overflow]").hidden = true;
          if (act === "refresh") await refresh();
          else if (act === "chat") window.AriaActivityEngine?.start?.("converse", { confirmHighStakes: false });
          else if (typeof spec.onOverflow === "function") await spec.onOverflow(act, ctx());
        });
        if (typeof spec.wire === "function") spec.wire(ctx());
      }
      return el;
    }

    function ctx() {
      const gen = _loadGen;
      return {
        root: root(),
        esc,
        signal: _abort?.signal,
        api: (url, opts) => fetchJson(url, { ...(opts || {}), signal: _abort?.signal }),
        setStatus: (t) => {
          if (!_active || gen !== _loadGen) return;
          setStatus(root(), t);
        },
        body: () => root()?.querySelector("[data-nr-body]"),
        active: () => _active && gen === _loadGen,
      };
    }

    async function refresh() {
      if (typeof spec.load !== "function") return;
      _abort?.abort();
      _abort = new AbortController();
      const gen = ++_loadGen;
      const c = ctx();
      try {
        await spec.load(c);
      } catch (err) {
        // Navigation abort: ignore. Timeout / real errors: surface while still current.
        if (gen !== _loadGen) return;
        if (err?.aborted && !err?.timedOut) return;
        try {
          c.setStatus(err?.message || "Unavailable");
        } catch (_) {
          /* ignore */
        }
      }
    }

    function bodyHtml() {
      if (typeof spec.buildBody === "function") return spec.buildBody({ esc }) || "";
      return spec.buildBody || "";
    }

    async function enter() {
      exitOthers(spec.id);
      const el = buildShell();
      el.hidden = false;
      el.removeAttribute("aria-hidden");
      el.removeAttribute("inert");
      /* Rebuild structural slots if exit cleared the painted body (BUG-009). */
      const painted = el.querySelector("[data-nr-body]");
      if (painted && !painted.innerHTML.trim()) {
        painted.innerHTML = bodyHtml();
      }
      const body = document.body;
      body.classList.add("house-room", spec.houseClass || `house-${spec.id}`, spec.bodyNativeClass || `native-${spec.id}`);
      body.dataset.room = spec.id;
      window.AriaStage.mount(el, spec.id);
      _active = true;
      window.AriaWorkspaceChrome?.apply?.(spec.chrome || "minimal");
      await refresh();
      try {
        window.AriaLivingFamiliarity?.recordVisit?.({ room: spec.id, view: spec.viewId || spec.id });
      } catch (_) {
        /* ignore */
      }
      window.dispatchEvent(new CustomEvent("aria-native-room", { detail: { room: spec.id, native: true } }));
    }

    function exit() {
      if (!_active) return;
      _active = false;
      _abort?.abort();
      _loadGen += 1;
      document.body.classList.remove(spec.bodyNativeClass || `native-${spec.id}`);
      const el = root();
      if (el) {
        /* Parked native rooms must not stay live in a11y/DOM probes (BUG-009). */
        el.hidden = true;
        el.setAttribute("aria-hidden", "true");
        el.setAttribute("inert", "");
        const painted = el.querySelector("[data-nr-body]");
        if (painted) painted.innerHTML = "";
      }
    }

    const mod = {
      enter,
      exit,
      isActive: () => _active,
      refresh,
      version: spec.version || "5.1.1-native",
      legacyBridge: false,
    };
    if (spec.global) window[spec.global] = mod;
    register(spec.id, () => mod);
    return mod;
  }

  /* Seed Priority-1 modules into registry when present */
  function seedKnown() {
    if (window.AriaFlytyingRoom) register("flytying", () => window.AriaFlytyingRoom);
    if (window.AriaHealthRoom) register("health", () => window.AriaHealthRoom);
    if (window.AriaMissionRoom) register("mission", () => window.AriaMissionRoom);
  }
  seedKnown();

  window.AriaRoomKit = {
    esc,
    fetchJson,
    atmosphereHtml,
    presenceHtml,
    setStatus,
    ensureRoot,
    register,
    get,
    allIds,
    exitOthers,
    defineRoom,
    seedKnown,
    version: "5.1.2-timeout",
  };
})();
