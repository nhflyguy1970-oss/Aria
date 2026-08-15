/**
 * Native Fly Tying Room (Phase 5) — streamside cabin.
 * Designed for the Living Workspace. Not a relocated panel.
 * Backend: /api/flytying/* unchanged.
 */
(function () {
  "use strict";

  const ROOM_ID = "flytyingRoom";
  let _active = false;
  let _recipes = [];
  let _selected = null;
  let _stepIdx = 0;
  let _user = { favorites: [], inventory: [], queue: [] };
  let _q = "";
  let _loading = false;

  const kit = () => window.AriaRoomKit;
  const esc = (s) => kit().esc(s);
  const api = (url, opts) => kit().fetchJson(url, opts);

  function root() {
    return document.getElementById(ROOM_ID);
  }

  function buildShell() {
    const el = kit().ensureRoot(ROOM_ID, "fly-room");
    el.setAttribute("aria-label", "Fly Tying");
    if (el.dataset.shellBuilt === "1") return el;
    el.innerHTML = [
      kit().atmosphereHtml(),
      kit().presenceHtml("· Streamside cabin", "The bench is quiet"),
      '<div class="fly-room__body">',
      '  <aside class="fly-room__rail" aria-label="Patterns">',
      '    <label class="fly-room__search"><span class="visually-hidden">Search patterns</span>',
      '      <input type="search" id="flyRoomSearch" placeholder="Find a pattern…" autocomplete="off" />',
      "    </label>",
      '    <ul class="fly-room__list" id="flyRoomList" role="listbox" aria-label="Patterns"></ul>',
      "  </aside>",
      '  <main class="fly-room__stage">',
      '    <div class="fly-room__hero" id="flyRoomHero"></div>',
      '    <div class="fly-room__bench" id="flyRoomBench" hidden></div>',
      "  </main>",
      '  <aside class="fly-room__hearth" aria-label="Materials">',
      '    <div class="fly-room__hearth-title">On the bench</div>',
      '    <p class="fly-room__inv" id="flyRoomInv">Materials…</p>',
      '    <button type="button" class="fly-room__suggest" id="flyRoomSuggest">Suggest from what I have</button>',
      '    <p class="fly-room__whisper" id="flyRoomWhisper" hidden></p>',
      "  </aside>",
      "</div>",
      '<button type="button" class="nr-overflow-btn" id="flyRoomOverflowBtn" aria-label="More" aria-expanded="false">···</button>',
      '<div class="nr-overflow" id="flyRoomOverflow" hidden role="menu">',
      '  <button type="button" data-fly-act="favorites">Favorites only</button>',
      '  <button type="button" data-fly-act="seasonal">Seasonal picks</button>',
      '  <button type="button" data-fly-act="refresh">Refresh library</button>',
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
    const search = el.querySelector("#flyRoomSearch");
    let t;
    search?.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => {
        _q = search.value.trim();
        loadRecipes();
      }, 280);
    });
    el.querySelector("#flyRoomList")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-recipe-id]");
      if (!btn) return;
      selectRecipe(btn.dataset.recipeId);
    });
    el.querySelector("#flyRoomSuggest")?.addEventListener("click", suggestFromMaterials);
    el.querySelector("#flyRoomOverflowBtn")?.addEventListener("click", (e) => {
      e.stopPropagation();
      const panel = el.querySelector("#flyRoomOverflow");
      const open = panel.hidden;
      panel.hidden = !open;
      e.currentTarget.setAttribute("aria-expanded", open ? "true" : "false");
    });
    el.querySelector("#flyRoomOverflow")?.addEventListener("click", async (e) => {
      const act = e.target.closest("[data-fly-act]")?.dataset.flyAct;
      if (!act) return;
      el.querySelector("#flyRoomOverflow").hidden = true;
      if (act === "refresh") await refreshAll();
      if (act === "seasonal") await loadSeasonal();
      if (act === "favorites") {
        _q = "";
        el.querySelector("#flyRoomSearch").value = "";
        await loadRecipes({ favoritesOnly: true });
      }
    });
    el.querySelector("#flyRoomBench")?.addEventListener("click", (e) => {
      const act = e.target.closest("[data-fly-bench]")?.dataset.flyBench;
      if (act === "prev") {
        _stepIdx = Math.max(0, _stepIdx - 1);
        renderBench();
      }
      if (act === "next") {
        const steps = _selected?.steps || [];
        _stepIdx = Math.min(steps.length - 1, _stepIdx + 1);
        renderBench();
      }
      if (act === "fav") toggleFavorite();
    });
    document.addEventListener("click", (e) => {
      if (!_active) return;
      const panel = el.querySelector("#flyRoomOverflow");
      if (panel && !panel.hidden && !e.target.closest("#flyRoomOverflow") && !e.target.closest("#flyRoomOverflowBtn")) {
        panel.hidden = true;
      }
    });
  }

  function renderList() {
    const list = root()?.querySelector("#flyRoomList");
    if (!list) return;
    if (_loading && !_recipes.length) {
      list.innerHTML = '<li class="fly-room__empty">Gathering patterns…</li>';
      return;
    }
    if (!_recipes.length) {
      list.innerHTML = '<li class="fly-room__empty">No patterns match.</li>';
      return;
    }
    list.innerHTML = _recipes
      .map((r) => {
        const id = r.recipe_id || r.id || "";
        const active = _selected && (id === (_selected.recipe_id || _selected.id));
        return (
          `<li><button type="button" class="fly-room__pattern${active ? " is-active" : ""}" data-recipe-id="${esc(id)}" role="option" aria-selected="${active}">` +
          `<span class="fly-room__pname">${esc(r.name || "Untitled")}</span>` +
          `<span class="fly-room__ptype">${esc(r.type || "")}</span>` +
          `</button></li>`
        );
      })
      .join("");
  }

  function renderHero() {
    const hero = root()?.querySelector("#flyRoomHero");
    const bench = root()?.querySelector("#flyRoomBench");
    if (!hero) return;
    if (!_selected) {
      hero.innerHTML =
        '<div class="fly-room__welcome">' +
        "<h1>Come to the bench</h1>" +
        "<p>Pick a pattern. Tie what the water asks for.</p>" +
        "</div>";
      if (bench) bench.hidden = true;
      return;
    }
    const r = _selected;
    const fav = (_user.favorites || []).includes(r.recipe_id || r.id);
    hero.innerHTML =
      `<p class="fly-room__kicker">${esc(r.type || "pattern")}</p>` +
      `<h1>${esc(r.name || "Pattern")}</h1>` +
      `<p class="fly-room__hook">${esc(r.hook || r.hook_size || "")}</p>` +
      `<div class="fly-room__hero-actions">` +
      `<button type="button" data-fly-bench="fav" class="fly-room__ghost">${fav ? "★ Favorited" : "☆ Favorite"}</button>` +
      `</div>`;
    if (bench) {
      bench.hidden = false;
      renderBench();
    }
  }

  function renderBench() {
    const bench = root()?.querySelector("#flyRoomBench");
    if (!bench || !_selected) return;
    const steps = Array.isArray(_selected.steps)
      ? _selected.steps
      : typeof _selected.steps === "string"
        ? _selected.steps.split(/\n+/).filter(Boolean)
        : [];
    const mats = _selected.materials || _selected.material_list || [];
    const matHtml = Array.isArray(mats)
      ? mats
          .map((m) => {
            if (typeof m === "string") return `<li>${esc(m)}</li>`;
            return `<li>${esc(m.name || m.what || m.item || JSON.stringify(m))}</li>`;
          })
          .join("")
      : `<li>${esc(String(mats))}</li>`;
    const step = steps[_stepIdx];
    const stepText =
      typeof step === "string" ? step : step?.text || step?.instruction || step?.step || "";
    bench.innerHTML =
      '<div class="fly-room__materials"><h2>Materials</h2><ul>' +
      (matHtml || "<li class=\"muted\">None listed</li>") +
      "</ul></div>" +
      '<div class="fly-room__steps">' +
      `<h2>Steps <span class="fly-room__step-count">${steps.length ? _stepIdx + 1 + " / " + steps.length : ""}</span></h2>` +
      (steps.length
        ? `<p class="fly-room__step">${esc(stepText)}</p>` +
          `<div class="fly-room__step-nav">` +
          `<button type="button" data-fly-bench="prev" ${ _stepIdx <= 0 ? "disabled" : "" }>Previous</button>` +
          `<button type="button" data-fly-bench="next" ${ _stepIdx >= steps.length - 1 ? "disabled" : "" }>Next</button>` +
          `</div>`
        : "<p class=\"muted\">No steps for this pattern.</p>") +
      "</div>";
  }

  function renderInv() {
    const el = root()?.querySelector("#flyRoomInv");
    if (!el) return;
    const items = _user.inventory || _user.materials || [];
    const n = Array.isArray(items) ? items.length : 0;
    el.textContent = n ? `${n} material${n === 1 ? "" : "s"} on hand` : "No materials logged yet";
  }

  async function loadRecipes(opts) {
    _loading = true;
    renderList();
    kit().setStatus(root(), "Looking through the library…");
    try {
      const params = new URLSearchParams();
      if (_q) params.set("q", _q);
      params.set("limit", "48");
      params.set("offset", "0");
      if (opts?.favoritesOnly) params.set("favorites_only", "true");
      const data = await api(`/api/flytying/recipes?${params}`);
      _recipes = data.results || data.recipes || [];
      kit().setStatus(root(), data.total != null ? `${data.total} patterns nearby` : "Bench ready");
    } catch (err) {
      _recipes = [];
      kit().setStatus(root(), err.message || "Library unavailable");
    }
    _loading = false;
    renderList();
  }

  async function loadSeasonal() {
    try {
      const data = await api("/api/flytying/seasonal?limit=40");
      _recipes = data.results || data.recipes || [];
      kit().setStatus(root(), "Seasonal picks");
      renderList();
      if (_recipes[0]) selectRecipe(_recipes[0].recipe_id || _recipes[0].id);
    } catch (err) {
      kit().setStatus(root(), err.message || "Seasonal unavailable");
    }
  }

  async function selectRecipe(id) {
    if (!id) return;
    kit().setStatus(root(), "Opening pattern…");
    try {
      const data = await api(`/api/flytying/recipes/${encodeURIComponent(id)}`);
      /* API returns flat recipe fields on the payload */
      _selected = data.recipe || data.result || data;
      if (_selected && _selected.ok != null && !_selected.name && data.name) _selected = data;
      _stepIdx = 0;
      window._flytyingSelectedId = _selected.recipe_id || _selected.id || id;
      window._flytyingSelectedName = _selected.name || "";
      renderHero();
      renderList();
      kit().setStatus(root(), "Listening quietly");
    } catch (err) {
      kit().setStatus(root(), err.message || "Could not open pattern");
    }
  }

  async function toggleFavorite() {
    if (!_selected) return;
    const id = _selected.recipe_id || _selected.id;
    try {
      await api("/api/flytying/favorites/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_id: id }),
      });
      await loadUser();
      renderHero();
    } catch (err) {
      kit().setStatus(root(), err.message || "Favorite failed");
    }
  }

  async function loadUser() {
    try {
      const data = await api("/api/flytying/user");
      const inv = data.inventory;
      _user = {
        favorites: data.favorites || [],
        queue: data.queue || [],
        inventory: Array.isArray(inv) ? inv : inv?.items || data.items || [],
      };
      renderInv();
    } catch (_) {
      renderInv();
    }
  }

  async function suggestFromMaterials() {
    const whisper = root()?.querySelector("#flyRoomWhisper");
    kit().setStatus(root(), "Reading the materials…");
    try {
      const data = await api("/api/flytying/from-materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const top = data.results?.[0] || data.suggestions?.[0] || data.recipe;
      if (whisper) {
        whisper.hidden = false;
        whisper.textContent = top
          ? `Try ${top.name || "this pattern"} — from what you have.`
          : data.message || "Nothing clear from materials yet.";
      }
      if (top?.recipe_id || top?.id) selectRecipe(top.recipe_id || top.id);
      else kit().setStatus(root(), "Listening quietly");
    } catch (err) {
      if (whisper) {
        whisper.hidden = false;
        whisper.textContent = err.message || "Suggestion unavailable";
      }
      kit().setStatus(root(), "Listening quietly");
    }
  }

  async function refreshAll() {
    await Promise.all([loadUser(), loadRecipes()]);
  }

  async function enter() {
    kit().exitOthers("flytying");
    const el = buildShell();
    document.body.classList.add("house-room", "house-flytying", "native-flytying");
    document.body.dataset.room = "flytying";
    window.AriaStage.mount(el, "flytying");
    _active = true;
    window.AriaWorkspaceChrome?.apply?.("minimal");
    await refreshAll();
    if (!_selected) renderHero();
    else {
      renderHero();
      renderList();
    }
    try {
      window.AriaLivingFamiliarity?.recordVisit?.({ room: "flytying", view: "flytying" });
    } catch (_) {
      /* ignore */
    }
    window.dispatchEvent(new CustomEvent("aria-native-room", { detail: { room: "flytying", native: true } }));
  }

  function exit() {
    if (!_active) return;
    _active = false;
    document.body.classList.remove("native-flytying");
    const el = root();
    if (el?.getAttribute("data-aria-stage-mounted") && window.AriaStage?.mountedId?.() === ROOM_ID) {
      /* house will mount next; leave stage clear to house */
    }
  }

  function isActive() {
    return _active;
  }

  window.AriaFlytyingRoom = {
    enter,
    exit,
    isActive,
    selectRecipe,
    version: "5.0.0-native",
    legacyBridge: false,
  };
  window.AriaRoomKit?.register?.("flytying", () => window.AriaFlytyingRoom);
})();
