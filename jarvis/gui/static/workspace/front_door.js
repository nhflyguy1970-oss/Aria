/**
 * Aria Front Door — foyer arrival (Phase 6.1.1).
 * Same catalog. Different experience: doors, not a launcher.
 */
(function () {
  "use strict";

  const RECENT_KEY = "aria_front_door_recent_v1";
  const PIN_KEY = "aria_front_door_pins_v1";
  const MAX_RECENT = 8;

  let _bound = false;
  let _activeIdx = 0;
  let _mode = "foyer"; /* foyer | search */
  let _closeTimer = null;

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function root() {
    return document.getElementById("ariaFrontDoor");
  }

  function isWorkspace() {
    return (
      document.documentElement.classList.contains("living-workspace") ||
      document.body?.classList.contains("living-workspace")
    );
  }

  function loadList(key) {
    try {
      const raw = JSON.parse(localStorage.getItem(key) || "[]");
      return Array.isArray(raw) ? raw.filter((x) => typeof x === "string") : [];
    } catch {
      return [];
    }
  }

  function saveList(key, arr) {
    try {
      localStorage.setItem(key, JSON.stringify(arr));
    } catch {
      /* ignore */
    }
  }

  function recordVisit(roomId) {
    if (!roomId) return;
    const next = [roomId, ...loadList(RECENT_KEY).filter((x) => x !== roomId)].slice(0, MAX_RECENT);
    saveList(RECENT_KEY, next);
  }

  function pins() {
    return loadList(PIN_KEY);
  }

  function togglePin(roomId) {
    const cur = pins();
    const next = cur.includes(roomId) ? cur.filter((x) => x !== roomId) : [roomId, ...cur].slice(0, 10);
    saveList(PIN_KEY, next);
    return next;
  }

  function esc(s) {
    return (
      window.AriaRoomKit?.esc?.(s) ||
      String(s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]))
    );
  }

  const HOUSE_SVG =
    '<svg class="fd-house-glyph" viewBox="0 0 32 32" aria-hidden="true"><path fill="currentColor" d="M16 3.2 3 14.2h3.2V28h8.2V19h5.2v9h8.2V14.2H29L16 3.2zm0 3.4 9.2 7.7V25h-4.8v-9H11.6v9H6.8V14.3L16 6.6z"/></svg>';

  function ensureHouseBtn() {
    let btn = document.getElementById("ariaHouseBtn");
    if (btn) return btn;
    btn = document.createElement("button");
    btn.id = "ariaHouseBtn";
    btn.type = "button";
    btn.className = "aria-house-btn";
    btn.setAttribute("aria-label", "Open the Front Door");
    btn.title = "Home · Front Door (Ctrl+K)";
    btn.innerHTML = HOUSE_SVG;
    document.body.appendChild(btn);
    btn.addEventListener("click", () => toggle());
    return btn;
  }

  function ensureDom() {
    let el = root();
    if (el) return el;
    el = document.createElement("div");
    el.id = "ariaFrontDoor";
    el.className = "fd-root hidden";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.setAttribute("aria-hidden", "true");
    el.setAttribute("aria-label", "Front Door");
    el.innerHTML = [
      '<div class="fd-veil" aria-hidden="true"></div>',
      '<div class="fd-foyer" role="document">',
      '  <header class="fd-header">',
      '    <div class="fd-header-mark">' + HOUSE_SVG + "</div>",
      '    <p class="fd-brand">Aria</p>',
      '    <h1 class="fd-title">Where would you like to go?</h1>',
      '    <p class="fd-welcome" id="fdWelcome"></p>',
      "  </header>",
      '  <div class="fd-table" id="fdTable" aria-label="Left on the table"></div>',
      '  <div class="fd-body" id="fdBody"></div>',
      '  <div class="fd-find" id="fdFind">',
      '    <button type="button" class="fd-find-toggle" id="fdFindToggle">Looking for something specific?</button>',
      '    <label class="fd-search-wrap hidden" id="fdSearchWrap"><span class="visually-hidden">Search the house</span>',
      '      <input type="search" id="fdSearch" class="fd-search" placeholder="Type a place, tool, or need…" autocomplete="off" />',
      "    </label>",
      "  </div>",
      '  <footer class="fd-footer">',
      '    <button type="button" id="fdClose" class="fd-close">Return</button>',
      '    <button type="button" id="fdLockAria" class="fd-lock hidden" hidden>Lock Aria</button>',
      '    <span class="fd-foot-meta">Esc · Ctrl+K</span>',
      "  </footer>",
      "</div>",
    ].join("");
    document.body.appendChild(el);
    return el;
  }

  function doorCard(item, opts) {
    const pin = opts?.showPin && item.roomId;
    const pinned = pin && pins().includes(item.roomId);
    const tone = item.roomId ? ` fd-door--${esc(item.roomId)}` : "";
    return (
      `<button type="button" class="fd-door${tone} fd-item" data-fd-id="${esc(item.id)}" data-kind="${esc(item.kind)}" role="option">` +
      `<span class="fd-door-glow" aria-hidden="true"></span>` +
      `<span class="fd-door-icon" aria-hidden="true">${esc(item.icon || "·")}</span>` +
      `<span class="fd-door-copy"><strong>${esc(item.title)}</strong><span class="fd-door-blurb">${esc(item.blurb || "")}</span></span>` +
      (pin
        ? `<span class="fd-pin${pinned ? " is-on" : ""}" data-fd-pin="${esc(item.roomId)}" title="Keep near">${pinned ? "●" : "○"}</span>`
        : "") +
      `</button>`
    );
  }

  function quietRow(item) {
    return (
      `<button type="button" class="fd-quiet fd-item" data-fd-id="${esc(item.id)}" data-kind="${esc(item.kind)}" role="option">` +
      `<span class="fd-quiet-icon" aria-hidden="true">${esc(item.icon || "·")}</span>` +
      `<span class="fd-quiet-copy"><strong>${esc(item.title)}</strong><span>${esc(item.blurb || "")}</span></span>` +
      `</button>`
    );
  }

  function chip(item) {
    return (
      `<button type="button" class="fd-chip fd-item" data-fd-id="${esc(item.id)}" data-kind="${esc(item.kind)}">` +
      `<span aria-hidden="true">${esc(item.icon || "·")}</span> ${esc(item.title)}` +
      `</button>`
    );
  }

  function renderFoyer() {
    _mode = "foyer";
    const cat = window.AriaFrontDoorCatalog;
    if (!cat) return;
    const body = $("#fdBody");
    const table = $("#fdTable");
    const welcome = $("#fdWelcome");
    const wrap = $("#fdSearchWrap");
    const toggle = $("#fdFindToggle");
    if (!body) return;

    if (wrap) wrap.classList.add("hidden");
    if (toggle) toggle.classList.remove("hidden");

    const roomMap = Object.fromEntries(cat.rooms().map((r) => [r.roomId, r]));
    const recentItems = loadList(RECENT_KEY)
      .map((id) => roomMap[id])
      .filter(Boolean);
    const pinItems = pins()
      .map((id) => roomMap[id])
      .filter(Boolean);

    const act = window.AriaActivityEngine?.current?.();
    const room = window.AriaHouse?.current?.() || document.body?.dataset?.room || "";
    if (welcome) {
      if (act) welcome.textContent = `You’re in the middle of ${act.title || act.id}. The rest of the house is through these doors.`;
      else if (room) welcome.textContent = `Stepped out from ${room}. Choose another door — or return.`;
      else welcome.textContent = "Come in. The rooms are waiting.";
    }

    if (table) {
      const bits = [];
      if (pinItems.length) {
        bits.push(`<div class="fd-table-row"><span class="fd-table-label">Kept near</span><div class="fd-chips">${pinItems.map(chip).join("")}</div></div>`);
      }
      if (recentItems.length) {
        bits.push(`<div class="fd-table-row"><span class="fd-table-label">Just visited</span><div class="fd-chips">${recentItems.map(chip).join("")}</div></div>`);
      }
      table.innerHTML = bits.join("");
      table.hidden = !bits.length;
    }

    const rooms = cat.rooms().filter((r) => r.roomId !== "home"); /* home is the foyer metaphor */
    body.innerHTML = [
      `<section class="fd-wing fd-wing--rooms"><h2 class="fd-wing-title">Rooms</h2><div class="fd-doors">${rooms.map((r) => doorCard(r, { showPin: true })).join("")}</div></section>`,
      `<details class="fd-wing fd-wing--hall"><summary>House Controls</summary><div class="fd-quiet-grid">${cat.controls().map(quietRow).join("")}</div></details>`,
      `<details class="fd-wing fd-wing--tools"><summary>Tools</summary><div class="fd-quiet-grid">${cat.tools().slice(0, 14).map(quietRow).join("")}</div></details>`,
      `<details class="fd-wing fd-wing--adv"><summary>Advanced</summary><div class="fd-quiet-grid">${cat.advanced().map(quietRow).join("")}</div></details>`,
    ].join("");
    _activeIdx = 0;
    highlightActive();
    syncLockButton();
  }

  function renderSearch(q) {
    _mode = "search";
    const cat = window.AriaFrontDoorCatalog;
    const body = $("#fdBody");
    const table = $("#fdTable");
    if (!body || !cat) return;
    if (table) table.hidden = true;
    const { results } = cat.match(q);
    if (!results.length) {
      body.innerHTML = '<p class="fd-empty">Nothing behind that name — try a Room, or something you need done.</p>';
      return;
    }
    const groups = { room: [], tool: [], control: [], advanced: [] };
    results.forEach((r) => {
      (groups[r.kind] || groups.advanced).push(r);
    });
    body.innerHTML = [
      groups.room.length ? `<section class="fd-wing"><h2 class="fd-wing-title">Rooms</h2><div class="fd-doors">${groups.room.map((r) => doorCard(r, { showPin: true })).join("")}</div></section>` : "",
      groups.control.length ? `<section class="fd-wing"><h2 class="fd-wing-title">House Controls</h2><div class="fd-quiet-grid">${groups.control.map(quietRow).join("")}</div></section>` : "",
      groups.tool.length ? `<section class="fd-wing"><h2 class="fd-wing-title">Tools</h2><div class="fd-quiet-grid">${groups.tool.map(quietRow).join("")}</div></section>` : "",
      groups.advanced.length ? `<section class="fd-wing"><h2 class="fd-wing-title">Advanced</h2><div class="fd-quiet-grid">${groups.advanced.map(quietRow).join("")}</div></section>` : "",
    ].join("");
    _activeIdx = 0;
    highlightActive();
    syncLockButton();
  }

  function visibleItems() {
    return Array.from(root()?.querySelectorAll("#fdBody .fd-item, #fdTable .fd-item") || []);
  }

  function highlightActive() {
    const items = visibleItems();
    items.forEach((el, i) => el.classList.toggle("is-active", i === _activeIdx));
    items[_activeIdx]?.scrollIntoView?.({ block: "nearest" });
  }

  function invoke(el) {
    if (!el) return;
    const id = el.getAttribute("data-fd-id");
    const item = window.AriaFrontDoorCatalog?.all?.()?.find((x) => x.id === id);
    close();
    if (item?.run) {
      try {
        item.run();
      } catch (err) {
        console.warn("[FrontDoor]", err);
      }
    }
  }

  function showSearch() {
    const wrap = $("#fdSearchWrap");
    const toggle = $("#fdFindToggle");
    wrap?.classList.remove("hidden");
    toggle?.classList.add("hidden");
    setTimeout(() => $("#fdSearch")?.focus(), 30);
  }

  function open(prefill) {
    if (!isWorkspace()) {
      window.openCommandPalette?.(prefill);
      return;
    }
    ensureHouseBtn();
    const el = ensureDom();
    /* Cancel a pending leave so Ctrl+K / House during close always reopens. */
    if (_closeTimer) {
      clearTimeout(_closeTimer);
      _closeTimer = null;
    }
    el.classList.remove("hidden");
    el.classList.remove("fd-root--leaving");
    el.classList.add("fd-root--enter");
    el.setAttribute("aria-hidden", "false");
    document.body.classList.add("front-door-open");
    const input = $("#fdSearch");
    if (typeof prefill === "string" && prefill) {
      showSearch();
      if (input) {
        input.value = prefill;
        renderSearch(prefill);
      }
    } else {
      if (input) input.value = "";
      renderFoyer();
      /* Arrival: do not steal focus into search */
      setTimeout(() => {
        const first = root()?.querySelector(".fd-door");
        first?.focus?.();
      }, 80);
    }
  }

  function close() {
    const el = root();
    if (!el || el.classList.contains("hidden")) return;
    if (el.classList.contains("fd-root--leaving")) return;
    el.classList.add("fd-root--leaving");
    el.classList.remove("fd-root--enter");
    if (_closeTimer) clearTimeout(_closeTimer);
    _closeTimer = setTimeout(() => {
      _closeTimer = null;
      /* Re-opened during leave — do not hide. */
      if (!el.classList.contains("fd-root--leaving")) return;
      el.classList.add("hidden");
      el.classList.remove("fd-root--leaving");
      el.setAttribute("aria-hidden", "true");
      document.body.classList.remove("front-door-open");
    }, 280);
  }

  function isOpen() {
    const el = root();
    return !!el && !el.classList.contains("hidden") && !el.classList.contains("fd-root--leaving");
  }

  async function syncLockButton() {
    const btn = $("#fdLockAria");
    if (!btn) return;
    let show = false;
    try {
      const st = await (window.AriaOwner?.status?.(true) || fetch("/api/security/lock/status").then((r) => r.json()));
      show = !!(st && st.lock_capable && st.locked === false);
    } catch (_) {
      show = false;
    }
    btn.hidden = !show;
    btn.classList.toggle("hidden", !show);
    btn.setAttribute("aria-hidden", show ? "false" : "true");
  }

  async function lockAriaFromDoor(e) {
    e?.preventDefault?.();
    e?.stopPropagation?.();
    const lock = window.jarvisLockHouse;
    const out = lock
      ? await lock({ hard: true })
      : await fetch("/api/security/lock", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ hard: true }),
        }).then((r) => r.json()).catch(() => ({ ok: false }));
    if (out && out.ok === false) return;
    close();
  }

  function toggle(prefill) {
    if (isOpen()) close();
    else open(prefill);
  }

  function bind() {
    if (_bound) return;
    _bound = true;
    ensureHouseBtn();
    ensureDom();
    const el = root();

    /* House button only in workspace */
    const syncBtn = () => {
      const btn = ensureHouseBtn();
      btn.classList.toggle("hidden", !isWorkspace());
    };
    syncBtn();
    window.addEventListener("aria-workspace-ready", syncBtn);

    $("#fdClose", el)?.addEventListener("click", close);
    $("#fdLockAria", el)?.addEventListener("click", (e) => {
      void lockAriaFromDoor(e);
    });
    window.addEventListener("aria-owner-unlocked", () => syncLockButton());
    window.addEventListener("aria-owner-locked", () => syncLockButton());
    el.addEventListener("click", (e) => {
      if (e.target === el || e.target.classList?.contains("fd-veil")) close();
    });

    $("#fdFindToggle", el)?.addEventListener("click", showSearch);

    $("#fdSearch", el)?.addEventListener("input", (e) => {
      const q = e.target.value.trim();
      if (!q) renderFoyer();
      else renderSearch(q);
    });

    el.addEventListener("click", (e) => {
      const pin = e.target.closest("[data-fd-pin]");
      if (pin) {
        e.preventDefault();
        e.stopPropagation();
        togglePin(pin.getAttribute("data-fd-pin"));
        const q = $("#fdSearch")?.value?.trim();
        if (q) renderSearch(q);
        else renderFoyer();
        return;
      }
      const item = e.target.closest(".fd-item");
      if (item) invoke(item);
    });

    el.addEventListener("keydown", (e) => {
      if (e.key === "/" && _mode === "foyer" && e.target?.id !== "fdSearch") {
        e.preventDefault();
        showSearch();
        return;
      }
      const items = visibleItems();
      if (e.key === "ArrowDown" || e.key === "ArrowRight") {
        e.preventDefault();
        _activeIdx = Math.min(items.length - 1, _activeIdx + 1);
        highlightActive();
        items[_activeIdx]?.focus?.();
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
        e.preventDefault();
        _activeIdx = Math.max(0, _activeIdx - 1);
        highlightActive();
        items[_activeIdx]?.focus?.();
      } else if (e.key === "Enter" && e.target?.closest?.(".fd-item")) {
        e.preventDefault();
        invoke(e.target.closest(".fd-item"));
      } else if (e.key === "Enter" && e.target?.id === "fdSearch") {
        e.preventDefault();
        invoke(items[_activeIdx] || items[0]);
      } else if (e.key === "Escape") {
        e.preventDefault();
        if (_mode === "search" && $("#fdSearch")?.value) {
          $("#fdSearch").value = "";
          renderFoyer();
        } else close();
      }
    });

    document.addEventListener(
      "keydown",
      (e) => {
        const mod = e.ctrlKey || e.metaKey;
        if (mod && String(e.key).toLowerCase() === "k") {
          if (!isWorkspace()) return;
          e.preventDefault();
          e.stopImmediatePropagation();
          toggle();
          return;
        }
        if (e.key === "Escape" && isOpen()) {
          e.preventDefault();
          close();
        }
      },
      true
    );

    document.getElementById("wsSpotlightBtn")?.addEventListener(
      "click",
      (e) => {
        if (!isWorkspace()) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        open();
      },
      true
    );

    window.addEventListener("aria-house-room", (e) => {
      const id = e.detail?.room;
      if (id) recordVisit(id);
    });
  }

  window.AriaFrontDoor = {
    open,
    close,
    toggle,
    isOpen,
    recordVisit,
    version: "6.1.3-owner-lock",
  };

  window.AriaWorkspaceSpotlight = {
    open: (q) => open(q),
    close,
    isOpen,
    render: () => {},
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();
})();
