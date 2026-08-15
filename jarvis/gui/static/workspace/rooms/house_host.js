/**
 * Aria House Host — Living Workspace room ownership.
 * Phase 5: all flagship Rooms prefer AriaRoomKit natives.
 */
(function () {
  "use strict";

  /* Abort in-flight house fetches on Room change so Chrome's 6-connection pool
     cannot wedge Integrity behind orphaned Documents/Mission/Dashboard calls. */
  (function installAriaNet() {
    if (window.AriaNet?.abortRoomTraffic) return;
    const orig = window.fetch.bind(window);
    const live = new Set();
    const ROOM_ABORT = "aria-room-leave";
    function isRoomAbort(err) {
      if (!err) return false;
      if (err.cancelled === true && (err.kind === "room-leave" || err.ownerVisible === false)) return true;
      if (err.ariaAbort === ROOM_ABORT) return true;
      if (err.name === "AbortError" || err.aborted) return true;
      // Prefer .message only — String(err) becomes "Error" when message is empty.
      const msg = String(err.message || err || "");
      const reason = String(err.reason || "");
      const combined = `${msg} ${reason}`.trim();
      if (
        /signal is aborted|request cancelled|the operation was aborted|aborterror|aria-room-leave/i.test(
          combined,
        )
      ) {
        return true;
      }
      // BUG-004: Chromium often surfaces room-leave aborts as Failed to fetch /
      // empty-message errors. Within the absorb window after abortRoomTraffic,
      // treat those as navigation aborts so loaders do not toast "X load failed".
      const ago = Date.now() - (window.AriaNet?.lastAbortAt || 0);
      if (ago >= 0 && ago < 2500) {
        if (!msg.trim()) return true;
        if (
          /failed to fetch|networkerror|err_aborted|load failed|checklist failed|connection.*(reset|closed)/i.test(
            combined,
          )
        ) {
          return true;
        }
      }
      return false;
    }
    function roomLeaveError() {
      // Empty message: naive `el.textContent = err.message` must not paint
      // "aria-room-leave" into owner-visible status lines. Classification
      // uses cancelled/kind/AbortError, not the message string.
      const err = new DOMException("", "AbortError");
      err.cancelled = true;
      err.kind = "room-leave";
      err.ownerVisible = false;
      err.ariaAbort = ROOM_ABORT;
      return err;
    }
    window.fetch = function ariaNetFetch(input, init) {
      const url = typeof input === "string" ? input : input && input.url ? String(input.url) : "";
      // Quiet caretaker + health must survive room thrash — never abort these.
      if (/\/api\/integrity\/home(?:\?|$)/.test(url) || (init && init.ariaExempt)) {
        const opts = Object.assign({}, init || {});
        delete opts.ariaExempt;
        return orig(input, opts);
      }
      const ctrl = new AbortController();
      live.add(ctrl);
      const parent = init && init.signal;
      if (parent) {
        if (parent.aborted) ctrl.abort(roomLeaveError());
        else parent.addEventListener("abort", () => ctrl.abort(roomLeaveError()), { once: true });
      }
      const opts = Object.assign({}, init || {}, { signal: ctrl.signal });
      return orig(input, opts)
        .catch((err) => {
          if (ctrl.signal.aborted || isRoomAbort(err)) {
            throw roomLeaveError();
          }
          throw err;
        })
        .finally(() => live.delete(ctrl));
    };
    let _absorbTimer = null;
    window.AriaNet = {
      ROOM_ABORT,
      isRoomAbort,
      roomLeaveError,
      /** If err is a room-leave abort, optionally retry. Returns true when handled. */
      absorbAbort(err, retryFn, delayMs) {
        if (!isRoomAbort(err)) return false;
        if (typeof retryFn === "function") {
          clearTimeout(_absorbTimer);
          _absorbTimer = setTimeout(retryFn, delayMs || 160);
        }
        return true;
      },
      lastAbortAt: 0,
      abortRoomTraffic() {
        for (const c of [...live]) {
          try {
            c.abort(roomLeaveError());
          } catch (_) {
            /* ignore */
          }
        }
        live.clear();
        window.AriaNet.lastAbortAt = Date.now();
      },
      version: "1.0.4-residency",
    };
  })();

  let _room = null;

  const ROOM_CLASS = {
    chat: "living-room",
    flytying: "house-flytying",
    health: "house-health",
    mission: "house-mission",
    documents: "house-documents",
    search: "house-search",
    gallery: "house-gallery",
    planner: "house-planner",
    calendar: "house-calendar",
    coding: "house-coding",
    projects: "house-projects",
    memory: "house-memory",
    voice: "house-voice",
    repair: "house-repair",
    integrity: "house-integrity",
    home: "house-home",
    automation: "house-automation",
    providers: "house-providers",
    home_automation: "house-home-auto",
  };

  const ALL_HOUSE = Object.values(ROOM_CLASS).filter((c) => c !== "living-room");

  const NATIVE_FALLBACK = {
    chat: () => window.AriaLivingRoom,
    flytying: () => window.AriaFlytyingRoom,
    health: () => window.AriaHealthRoom,
    mission: () => window.AriaMissionRoom,
  };

  function registryRoom(id) {
    return window.AriaWorkspaceRegistry?.room?.(id);
  }

  function nativeMod(id) {
    window.AriaRoomKit?.seedKnown?.();
    return window.AriaRoomKit?.get?.(id) || NATIVE_FALLBACK[id]?.() || null;
  }

  function clearHouseClasses() {
    const body = document.body;
    if (!body) return;
    const nativeClasses = Array.from(body.classList).filter((c) => c.startsWith("native-"));
    body.classList.remove(
      "house-room",
      "living-room",
      "furnished-room",
      ...ALL_HOUSE,
      ...nativeClasses,
    );
    delete body.dataset.furnished;
  }

  function ensureAtmosphere(panel) {
    if (!panel || panel.querySelector(".house-atmosphere") || panel.dataset.nativeRoom) return;
    const atm = document.createElement("div");
    atm.className = "house-atmosphere";
    atm.setAttribute("aria-hidden", "true");
    atm.innerHTML =
      '<div class="house-atmosphere__wash"></div>' +
      '<div class="house-atmosphere__veil"></div>' +
      '<div class="house-atmosphere__grain"></div>';
    panel.insertBefore(atm, panel.firstChild);
  }

  function ensurePresenceStrip(panel, room) {
    if (!panel || panel.dataset.nativeRoom) return;
    let strip = panel.querySelector(".house-presence");
    if (!strip) {
      strip = document.createElement("div");
      strip.className = "house-presence";
      strip.innerHTML =
        '<div class="house-presence__brand">Aria <span class="house-presence__place"></span></div>' +
        '<div class="house-presence__status">Listening quietly</div>';
      const header = panel.querySelector(
        ":scope > header, :scope > .mc-toolbar, :scope > .planner-header, :scope > .docs-shell-header, :scope > .search-header"
      );
      if (header) header.insertAdjacentElement("beforebegin", strip);
      else panel.insertBefore(strip, panel.children[1] || null);
    }
    const place = strip.querySelector(".house-presence__place");
    const meta = registryRoom(room);
    const label = meta?.place || meta?.metaphor || "";
    if (place) place.textContent = label ? `· ${label}` : "";
    if (document.body) document.body.dataset.place = label || room || "";
  }

  function viewEl(viewId) {
    return document.getElementById(`${viewId}View`);
  }

  function demolishLegacyShell() {
    const legacy = document.getElementById("ariaLegacyShell") || document.querySelector(".app");
    if (!legacy) return;
    legacy.setAttribute("inert", "");
    legacy.setAttribute("aria-hidden", "true");
    document.documentElement.classList.add("living-workspace");
    document.body?.classList.add("living-workspace");
  }

  function clearStage() {
    window.AriaRoomKit?.exitOthers?.(null);
    window.AriaLivingRoom?.exit?.({ keepStage: false });
    clearHouseClasses();
    window.AriaStage?.clear?.();
    _room = null;
    if (document.body) delete document.body.dataset.room;
  }

  function enter(roomId) {
    if (!window.AriaStage?.isWorkspace?.()) return;

    demolishLegacyShell();
    try {
      window.ariaDismissDialogs?.();
    } catch (_) {
      /* ignore */
    }

    if (roomId == null || roomId === "" || roomId === "__empty__") {
      try {
        window.AriaNet?.abortRoomTraffic?.();
      } catch (_) {
        /* ignore */
      }
      clearStage();
      window.dispatchEvent(new CustomEvent("aria-house-room", { detail: { room: null, empty: true } }));
      return;
    }

    const room = registryRoom(roomId) || { id: roomId, viewId: roomId };
    const id = room.id || roomId;
    const viewId = room.viewId || id;

    /* Abort in-flight fetches only when actually leaving a different Room.
       Re-entering the same Room used to cancel that Room's own status loads. */
    if (_room && _room !== id) {
      try {
        window.AriaNet?.abortRoomTraffic?.();
      } catch (_) {
        /* ignore */
      }
    }

    /* Chat keeps Living Room immersion */
    if (id === "chat") {
      clearHouseClasses();
      document.body.classList.add("living-room");
      document.body.dataset.room = "chat";
      delete document.body.dataset.furnished;
      _room = "chat";
      window.AriaRoomKit?.exitOthers?.("chat");
      window.AriaLivingRoom?.enter?.();
      try {
        window.AriaLivingFamiliarity?.recordVisit?.({ room: id, view: viewId });
      } catch (_) {
        /* ignore */
      }
      window.dispatchEvent(new CustomEvent("aria-house-room", { detail: { room: id, native: true } }));
      return;
    }

    /* Phase 6.4 — furnish with full original panel (not thin native shells) */
    if (window.AriaFurnish?.enter?.(id)) {
      _room = id;
      try {
        window.AriaLivingFamiliarity?.recordVisit?.({ room: id, view: viewId });
      } catch (_) {
        /* ignore */
      }
      return;
    }

    /* Fallback: thin native if no legacy panel */
    const mod = nativeMod(id);
    if (mod?.enter) {
      clearHouseClasses();
      delete document.body.dataset.furnished;
      _room = id;
      mod.enter();
      try {
        window.AriaLivingFamiliarity?.recordVisit?.({ room: id, view: viewId });
      } catch (_) {
        /* ignore */
      }
      window.dispatchEvent(new CustomEvent("aria-house-room", { detail: { room: id, native: true } }));
      return;
    }

    /* Unmigrated raw panel */
    window.AriaLivingRoom?.exit?.({ keepStage: true });
    window.AriaRoomKit?.exitOthers?.(null);
    clearHouseClasses();
    delete document.body.dataset.furnished;
    const cls = ROOM_CLASS[id] || `house-${id}`;
    document.body.classList.add("house-room", cls);
    document.body.dataset.room = id;
    _room = id;

    const panel = viewEl(viewId);
    if (panel) {
      ensureAtmosphere(panel);
      ensurePresenceStrip(panel, id);
      window.AriaStage.mount(panel, id);
    } else {
      window.AriaStage.clear();
    }

    try {
      window.AriaLivingFamiliarity?.recordVisit?.({ room: id, view: viewId });
    } catch (_) {
      /* ignore */
    }
    window.dispatchEvent(new CustomEvent("aria-house-room", { detail: { room: id, viewId, native: false } }));
  }

  function isNative(roomId) {
    const id = roomId || _room;
    if (id === "chat") return !!window.AriaLivingRoom?.enter;
    /* Furnished rooms are full original surfaces — not thin native */
    if (document.body?.dataset.furnished === "1" && _room === id) return false;
    const mod = nativeMod(id);
    return !!(mod?.enter && mod.legacyBridge === false);
  }

  function isFurnished(roomId) {
    const id = roomId || _room;
    return document.body?.dataset.furnished === "1" && (!roomId || _room === id);
  }

  function boot() {
    window.addEventListener("aria-activity-change", (e) => {
      const act = e.detail?.activity;
      if (!act) return;
      queueMicrotask(() => enter(act.primaryRoom || "chat"));
    });
    window.addEventListener("aria-workspace-ready", () => {
      demolishLegacyShell();
      const cur = window.AriaActivityEngine?.current?.();
      if (cur?.primaryRoom) enter(cur.primaryRoom);
      // Warm Integrity Truth so the Quiet caretaker never waits on a cold pool.
      try {
        fetch("/api/integrity/home", { cache: "no-store", ariaExempt: true })
          .then((r) => r.json())
          .then((d) => {
            const score = d.score || {};
            const deductions = score.deductions || d.deductions || [];
            const findings = (d.last_scan && d.last_scan.findings) || d.findings || [];
            const items = (deductions.length ? deductions : findings).map((x) => ({
              title: x.title || x.message || "Item",
            }));
            sessionStorage.setItem(
              "aria.integrity.home",
              JSON.stringify({
                overall: score.overall,
                state: d.state || score.status || "",
                items,
                at: Date.now(),
              })
            );
          })
          .catch(() => {});
      } catch (_) {
        /* ignore */
      }
    });
  }

  window.AriaHouse = {
    enter,
    clearStage,
    current: () => _room,
    isInHouse: () => document.body?.classList.contains("living-workspace") && !!_room,
    isNative,
    isFurnished,
    nativeRooms: () => window.AriaRoomKit?.allIds?.() || Object.keys(NATIVE_FALLBACK),
    rooms: () => [
      ...Object.keys(ROOM_CLASS),
      ...(window.AriaFurnish?.allRoomIds?.() || []),
    ].filter((v, i, a) => a.indexOf(v) === i),
    version: "6.4.0-furnish",
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
