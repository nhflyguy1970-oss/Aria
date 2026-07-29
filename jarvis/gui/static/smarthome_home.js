/** Smart Home Home — control-first overview, search, favorites, scenes, recovery. */
(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  async function control(entityId, action) {
    try {
      const res = await fetch("/api/smarthome/product/control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: entityId, action, confirmed: true }),
      });
      const data = await res.json();
      if (data.confirm_required) {
        window.showAriaToast?.(data.message || "Confirm required", "warn");
        return;
      }
      if (!data.ok) throw new Error(data.message || "Control failed");
      window.showAriaToast?.(data.message || action, "ok", 2500);
      loadHome();
    } catch (e) {
      window.showAriaToast?.(e.message || "Control failed", "err");
    }
  }

  async function activateScene(name) {
    try {
      const res = await fetch("/api/smarthome/product/scene", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scene: name, confirmed: true }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.message || "Scene failed");
      window.showAriaToast?.(data.message || name, "ok", 2500);
      loadHome();
    } catch (e) {
      window.showAriaToast?.(e.message || "Scene failed", "err");
    }
  }

  async function loadHome() {
    const panel = $("smarthomeHomePanel");
    if (!panel) return;
    try {
      const [home, profiles] = await Promise.all([
        fetch("/api/smarthome/product/home").then((r) => r.json()),
        fetch("/api/smarthome/product/profiles").then((r) => r.json()).catch(() => ({ profiles: [] })),
      ]);
      const recovery = home.recovery || {};
      const card = $("smarthomeRecoveryCard");
      const setup = $("smarthomeSetupDetails");
      if (card) {
        if (!recovery.ready) {
          card.classList.remove("hidden");
          if (setup) setup.open = true;
          const steps = (recovery.steps || [])
            .map((s) => `<li>${s.done ? "✓" : "○"} ${esc(s.label)} — <span class="muted">${esc(s.detail)}</span></li>`)
            .join("");
          card.innerHTML = `<strong>Connect Home Assistant</strong><p class="muted small">${esc(recovery.hint || "")}</p><ol class="tiny">${steps}</ol>`;
        } else {
          card.classList.add("hidden");
          if (setup) setup.open = false;
        }
      }
      const health = home.health || {};
      if ($("smarthomeHomeHealth")) {
        $("smarthomeHomeHealth").textContent = health.connected
          ? `Connected${health.url ? " · " + health.url : ""}`
          : health.hint || "Not connected";
      }
      const fav = $("smarthomeFavoritesList");
      if (fav) {
        const ents = (home.favorites && home.favorites.entities) || [];
        fav.innerHTML = ents.length
          ? ents
              .map(
                (e) =>
                  `<li><button type="button" class="ghost-btn tiny smarthome-fav-toggle" data-id="${esc(e.entity_id)}" aria-label="Toggle ${esc(e.friendly_name || e.entity_id)}">${esc(e.friendly_name || e.entity_id)} · ${esc(e.state || "?")}</button></li>`
              )
              .join("")
          : "<li class='muted'>Pin devices from search</li>";
        fav.querySelectorAll(".smarthome-fav-toggle").forEach((btn) =>
          btn.addEventListener("click", () => control(btn.dataset.id, "toggle"))
        );
      }
      const chips = $("smarthomeSceneChips");
      if (chips) {
        const scenes = home.scenes || [];
        chips.innerHTML = scenes.length
          ? scenes
              .slice(0, 8)
              .map(
                (s) =>
                  `<button type="button" class="ghost-btn small smarthome-scene-chip" data-id="${esc(s.id || s.label)}">${esc(s.label || s.id)}</button>`
              )
              .join("")
          : '<span class="muted small">No presets</span>';
        chips.querySelectorAll(".smarthome-scene-chip").forEach((btn) =>
          btn.addEventListener("click", () => activateScene(btn.dataset.id))
        );
      }
      const rooms = $("smarthomeRoomsList");
      if (rooms) {
        const rows = home.rooms || [];
        rooms.innerHTML = rows.length
          ? rows
              .slice(0, 8)
              .map((r) => `<li>${esc(r.name || r.id)} · ${(r.entity_ids || []).length} devices</li>`)
              .join("")
          : "<li class='muted'>No rooms yet</li>";
      }
      if ($("smarthomeSuggestions")) {
        $("smarthomeSuggestions").textContent = (home.suggestions || []).slice(0, 2).join(" · ");
      }
      const sel = $("smarthomeProfileSelect");
      if (sel && sel.dataset.bound !== "1") {
        sel.dataset.bound = "1";
        (profiles.profiles || []).forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.textContent = p.name + (p.builtin ? "" : " *");
          if (p.id === profiles.active) opt.selected = true;
          sel.appendChild(opt);
        });
      }
    } catch (err) {
      if ($("smarthomeHomeHealth")) $("smarthomeHomeHealth").textContent = err.message || "Home failed";
    }
  }

  async function runSearch() {
    const q = ($("smarthomeSearchInput")?.value || "").trim();
    const list = $("smarthomeSearchResults");
    if (!list) return;
    list.innerHTML = "<li class='muted'>Searching…</li>";
    try {
      const data = await fetch(
        `/api/smarthome/product/entities/search?q=${encodeURIComponent(q)}&limit=20`
      ).then((r) => r.json());
      const rows = data.results || data.entities || data.items || [];
      if (!rows.length) {
        list.innerHTML = "<li class='muted'>No matches</li>";
        return;
      }
      list.innerHTML = rows
        .map((e) => {
          const id = e.entity_id || e.id;
          const name = e.friendly_name || id;
          return `<li>
            <button type="button" class="ghost-btn tiny" data-act="toggle" data-id="${esc(id)}">${esc(name)} · ${esc(e.state || "?")}</button>
            <button type="button" class="ghost-btn tiny" data-act="pin" data-id="${esc(id)}" aria-label="Pin ${esc(name)}">Pin</button>
          </li>`;
        })
        .join("");
      list.querySelectorAll("button[data-act=toggle]").forEach((btn) =>
        btn.addEventListener("click", () => control(btn.dataset.id, "toggle"))
      );
      list.querySelectorAll("button[data-act=pin]").forEach((btn) =>
        btn.addEventListener("click", async () => {
          await fetch("/api/smarthome/product/favorites/pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ entity_id: btn.dataset.id }),
          });
          window.showAriaToast?.("Pinned", "ok", 2000);
          loadHome();
        })
      );
    } catch (e) {
      list.innerHTML = `<li class="muted">${esc(e.message || "Search failed")}</li>`;
    }
  }

  function bind() {
    const root = $("haPanel");
    if (!root || root.dataset.homeBound === "1") return;
    root.dataset.homeBound = "1";
    $("smarthomeSearchBtn")?.addEventListener("click", runSearch);
    $("smarthomeSearchInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        runSearch();
      }
    });
    $("smarthomeHouseStatusBtn")?.addEventListener("click", async () => {
      try {
        const data = await fetch("/api/smarthome/product/house-status").then((r) => r.json());
        window.showAriaToast?.(data.message || "Status", data.ok ? "ok" : "warn", 5000);
      } catch (e) {
        window.showAriaToast?.(e.message || "Status failed", "err");
      }
    });
    $("smarthomeOpenHaBtn")?.addEventListener("click", async () => {
      try {
        const st = await fetch("/api/homeassistant/status").then((r) => r.json());
        const url = st.url || $("haUrlInput")?.value;
        if (url) window.open(url, "_blank", "noopener");
        else window.showAriaToast?.("Set Home Assistant URL first", "warn");
      } catch {
        const url = $("haUrlInput")?.value;
        if (url) window.open(url, "_blank", "noopener");
      }
    });
    $("smarthomeProfileActivateBtn")?.addEventListener("click", async () => {
      const id = $("smarthomeProfileSelect")?.value;
      if (!id) return;
      await fetch(`/api/smarthome/product/profiles/${encodeURIComponent(id)}/activate`, { method: "POST" });
      window.showAriaToast?.("Smart Home profile applied", "ok");
      loadHome();
    });
    document.addEventListener("keydown", (e) => {
      if (e.target && /input|textarea|select/i.test(e.target.tagName)) return;
      const section = document.querySelector('[data-section="home"]');
      if (!section || section.classList.contains("collapsed")) return;
      if (e.key === "/" && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        $("smarthomeSearchInput")?.focus();
      }
    });
  }

  const prev = window.initHaPanel;
  window.initHaPanel = function initHaPanelWrapped() {
    if (typeof prev === "function") prev();
    bind();
    loadHome();
  };
  const prevExtras = window.initHaExtras;
  window.initHaExtras = function initHaExtrasWrapped() {
    if (typeof prevExtras === "function") prevExtras();
    bind();
    loadHome();
  };
  window.loadSmarthomeHome = loadHome;
  if (document.readyState !== "loading") {
    bind();
    loadHome();
  }
})();
