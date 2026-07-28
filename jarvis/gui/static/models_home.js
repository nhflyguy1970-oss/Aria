/** Models Home — AI Model Configuration and Routing Center (not Mission Control). */
(function () {
  "use strict";

  let _data = null;
  let _tab = "overview";
  let _advancedOpen = false;
  const TABS = [
    ["overview", "Overview"],
    ["roles", "Roles"],
    ["catalog", "Catalog"],
    ["providers", "Providers"],
    ["recommend", "Recommend"],
    ["pull", "Downloads"],
    ["packs", "Packs"],
    ["first_run", "Setup"],
  ];

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  async function api(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || data.detail || data.error || res.statusText);
    return data;
  }

  function confirmAct(title, body) {
    if (window.ariaConfirm) return window.ariaConfirm(body, { title, okLabel: "Confirm" });
    return Promise.resolve(window.confirm(`${title}\n\n${body}`));
  }

  function cardHtml(c) {
    if (!c) return "";
    const fits =
      c.fits_current_hardware === true
        ? '<span class="models-badge models-badge--ok">Fits hardware</span>'
        : c.fits_current_hardware === false
          ? '<span class="models-badge models-badge--warn">VRAM risk</span>'
          : "";
    const caps = (c.capabilities || []).map((x) => `<span class="models-chip">${esc(x)}</span>`).join("");
    const uses = (c.recommended_uses || []).map((u) => `<li>${esc(u)}</li>`).join("");
    const conflicts = (c.potential_conflicts || []).map((u) => `<li class="warn">${esc(u)}</li>`).join("");
    return `<article class="models-card" data-tag="${esc(c.tag)}" tabindex="0" role="listitem" aria-label="${esc(c.friendly_name)}">
      <header>
        <h4>${esc(c.friendly_name)}</h4>
        <code>${esc(c.tag)}</code>
      </header>
      <p class="muted tiny">${esc(c.provider)} · conf ${esc(c.confidence)}
        ${c.installed ? '<span class="models-badge models-badge--ok">Installed</span>' : '<span class="models-badge">Available</span>'}
        ${c.running ? '<span class="models-badge models-badge--ok">Running</span>' : ""}
        ${fits}
      </p>
      <div class="models-chips">${caps}</div>
      <dl class="models-meta">
        <div><dt>VRAM</dt><dd>${c.estimated_vram_gb != null ? esc(c.estimated_vram_gb) + " GB" : "—"}</dd></div>
        <div><dt>RAM</dt><dd>${c.recommended_ram_gb != null ? esc(c.recommended_ram_gb) + " GB" : "—"}</dd></div>
        <div><dt>Context</dt><dd>${c.context_window != null ? esc(c.context_window) : "—"}</dd></div>
        <div><dt>License</dt><dd>${esc(c.license || "—")}</dd></div>
      </dl>
      ${uses ? `<ul class="models-uses">${uses}</ul>` : ""}
      ${conflicts ? `<ul class="models-uses">${conflicts}</ul>` : ""}
      <div class="models-card-actions">
        <button type="button" class="ghost-btn tiny" data-models-assign="${esc(c.tag)}">Assign to Chat</button>
        ${c.pullable && !c.installed ? `<button type="button" class="ghost-btn tiny" data-models-pull="${esc(c.tag)}">Pull</button>` : ""}
        <button type="button" class="ghost-btn tiny" data-models-vram="${esc(c.tag)}">VRAM check</button>
      </div>
    </article>`;
  }

  function roleSelect(role, current, choices) {
    const opts = (choices || [])
      .map((t) => `<option value="${esc(t)}"${t === current ? " selected" : ""}>${esc(t)}</option>`)
      .join("");
    return `<label class="models-role-row">
      <span class="models-role-label">${esc(role.label || role.id)}</span>
      <select data-role-id="${esc(role.id)}" aria-label="${esc(role.label || role.id)} model">${opts}</select>
    </label>`;
  }

  function renderOverview() {
    const h = _data.health || {};
    const t = _data.terminology || {};
    const terms = Object.entries(t)
      .map(([k, v]) => `<li><strong>${esc(k)}</strong> — ${esc(v)}</li>`)
      .join("");
    const loaded = (_data.loaded_models || [])
      .map((m) => `<li><code>${esc(m.name || m.model || JSON.stringify(m))}</code></li>`)
      .join("");
    return `
      <section class="models-hero">
        <div>
          <p class="muted tiny">Models configures · Mission Control monitors</p>
          <h3>Models Home</h3>
          <p>Role assignments, catalog, providers, presets, and recommendations.</p>
        </div>
        <div class="models-hero-actions">
          <button type="button" class="apply-btn small" data-models-goto="roles">Edit roles</button>
          <button type="button" class="ghost-btn small" data-models-goto="catalog">Browse catalog</button>
          <button type="button" class="ghost-btn small" data-models-mc="inference">Open Mission Control · Inference</button>
          <button type="button" class="ghost-btn small" data-models-integrations>Open Integrations</button>
          <button type="button" class="ghost-btn small" id="modelsFreeVramBtn">Free VRAM</button>
        </div>
      </section>
      <div class="models-grid">
        <section class="models-panel-card">
          <h4>Health summary</h4>
          <p>Ollama: <strong>${h.ollama?.ok ? "reachable" : "check connection"}</strong></p>
          <p>Loaded: <strong>${h.loaded_count ?? 0}</strong> · Free VRAM: <strong>${h.free_vram_gb ?? "—"} GB</strong></p>
          <p class="muted tiny">${esc(h.provider_summary || "")}</p>
          ${(h.missing || []).length ? `<p class="warn">Missing: ${(h.missing || []).map(esc).join(", ")}</p>` : "<p class='muted'>No missing active models</p>"}
        </section>
        <section class="models-panel-card">
          <h4>Runtime (loaded)</h4>
          <ul class="models-list">${loaded || "<li class='muted'>None loaded</li>"}</ul>
          <p class="muted tiny">Warm / unload live in Mission Control — Models owns configuration only.</p>
        </section>
        <section class="models-panel-card">
          <h4>Terminology</h4>
          <ul class="models-list">${terms}</ul>
        </section>
      </div>`;
  }

  function renderRoles() {
    const roles = _data.roles || {};
    const choices = (_data.settings || {}).choices || (_data.settings || {}).installed || [];
    const primary = (roles.primary || [])
      .map((r) => roleSelect(r, r.model, r.id === "image" ? ["comfyui", ...choices] : choices))
      .join("");
    const advanced = (roles.advanced || [])
      .map((r) => roleSelect(r, r.model, choices))
      .join("");
    return `
      <div class="models-toolbar">
        <button type="button" class="apply-btn small" id="modelsSaveRolesBtn">Save role assignments</button>
        <button type="button" class="ghost-btn small" data-models-preset="fast">Preset · Fast</button>
        <button type="button" class="ghost-btn small" data-models-preset="quality">Preset · Quality</button>
        <button type="button" class="ghost-btn small" id="modelsResetBtn">Reset optimized</button>
        <button type="button" class="ghost-btn small" id="modelsExportBtn">Export</button>
        <button type="button" class="ghost-btn small" id="modelsImportBtn">Import</button>
      </div>
      <section class="models-panel-card">
        <h4>Primary roles</h4>
        <div class="models-role-grid">${primary}</div>
      </section>
      <section class="models-panel-card">
        <button type="button" class="ghost-btn tiny" id="modelsAdvancedToggle" aria-expanded="${_advancedOpen}">
          Advanced roles ${_advancedOpen ? "▾" : "▸"}
        </button>
        <div id="modelsAdvancedRoles" class="${_advancedOpen ? "" : "hidden"}">
          <p class="muted tiny">Router, summarization, planning, reasoning, documents, and more.</p>
          <div class="models-role-grid">${advanced}</div>
        </div>
      </section>
      <div class="models-grid">${Object.values(roles.cards || {})
        .slice(0, 6)
        .map(cardHtml)
        .join("")}</div>`;
  }

  function renderCatalog() {
    const cards = ((_data.catalog || {}).cards || []).map(cardHtml).join("");
    return `
      <div class="models-toolbar" role="search">
        <input type="search" id="modelsCatalogQ" class="audio-path-input" placeholder="Search models, capabilities…" aria-label="Search catalog" />
        <select id="modelsCatalogCap" aria-label="Capability filter">
          <option value="">All capabilities</option>
          <option value="coding">Coding</option>
          <option value="vision">Vision</option>
          <option value="embedding">Embedding</option>
          <option value="reasoning">Reasoning</option>
          <option value="chat">Chat</option>
          <option value="image">Image</option>
        </select>
        <select id="modelsCatalogSort" aria-label="Sort">
          <option value="installed">Installed first</option>
          <option value="name">Name</option>
          <option value="vram">VRAM</option>
        </select>
        <label class="muted tiny"><input type="checkbox" id="modelsCatalogInstalled" /> Installed only</label>
        <button type="button" class="ghost-btn small" id="modelsCatalogRefresh">Refresh</button>
      </div>
      <div class="models-card-grid" role="list">${cards || "<p class='muted'>No models match.</p>"}</div>`;
  }

  function renderProviders() {
    const results = (_data.providers || {}).results || {};
    const rows = Object.entries(results)
      .map(([id, r]) => {
        const ok = r.ok ? "models-badge--ok" : "models-badge--warn";
        return `<tr>
          <td><strong>${esc(id)}</strong></td>
          <td><span class="models-badge ${ok}">${r.ok ? "OK" : "Needs setup"}</span></td>
          <td>${esc(r.message || r.error || "")}</td>
          <td><button type="button" class="ghost-btn tiny" data-models-validate="${esc(id)}">Validate</button></td>
        </tr>`;
      })
      .join("");
    return `
      <section class="models-panel-card">
        <h4>Provider wizard</h4>
        <p class="muted">Validate connectivity and keys. Cloud keys live in Integrations. Warm/unload stay in Mission Control.</p>
        <table class="mc-table"><thead><tr><th>Provider</th><th>Status</th><th>Detail</th><th></th></tr></thead><tbody>${rows}</tbody></table>
        <button type="button" class="ghost-btn small" data-models-integrations>Open Integrations</button>
      </section>`;
  }

  function renderRecommend() {
    const stacks = ((_data.recommendations || {}).stacks || [])
      .map((s) => {
        const roles = Object.entries(s.roles || {})
          .map(([k, v]) => `<li>${esc(k)} → <code>${esc(v)}</code></li>`)
          .join("");
        return `<article class="models-panel-card">
          <h4>${esc(s.label)}</h4>
          <p>${esc(s.summary)}</p>
          <p class="muted">${esc(s.why)}</p>
          <ul class="models-list">${roles}</ul>
          <button type="button" class="apply-btn small" data-models-stack="${esc(s.id)}">Apply (confirm)</button>
        </article>`;
      })
      .join("");
    return `<p class="muted">Recommendations never auto-apply.</p><div class="models-grid">${stacks}</div>`;
  }

  function renderPull() {
    const pull = _data.pull || {};
    const active = pull.active
      ? `<p><strong>${esc(pull.active.model)}</strong> — ${esc(pull.active.message)} (${esc(pull.active.progress)}%)</p>`
      : "<p class='muted'>No active download</p>";
    const hist = (pull.history || [])
      .map((h) => `<li>${h.ok ? "✓" : "✗"} <code>${esc(h.model)}</code> — ${esc(h.message)}</li>`)
      .join("");
    return `
      <section class="models-panel-card">
        <h4>Download manager</h4>
        ${active}
        <button type="button" class="ghost-btn small" id="modelsPullMissingBtn">Pull missing active models</button>
        <h5>History</h5>
        <ul class="models-list">${hist || "<li class='muted'>—</li>"}</ul>
        <pre id="modelsPullLog" class="pull-log"></pre>
      </section>`;
  }

  function renderPacks() {
    const packs = ((_data.packs || {}).packs || [])
      .map(
        (p) => `<article class="models-panel-card">
        <h4>${esc(p.name || p.id)}</h4>
        <p class="muted tiny">${esc(p.id)}</p>
        <button type="button" class="apply-btn small" data-models-pack="${esc(p.id)}">Apply pack</button>
      </article>`
      )
      .join("");
    return `
      <section class="models-panel-card">
        <h4>Project / workspace packs</h4>
        <p class="muted">Save the current role map as a reusable pack.</p>
        <input id="modelsPackName" class="audio-path-input" placeholder="Pack name" aria-label="Pack name" />
        <button type="button" class="ghost-btn small" id="modelsPackSaveBtn">Save current as pack</button>
      </section>
      <div class="models-grid">${packs || "<p class='muted'>No packs yet</p>"}</div>`;
  }

  function renderFirstRun() {
    const fr = _data.first_run || {};
    const rec = ((_data.recommendations || {}).stacks || []).find((s) => s.id === "balanced") || {};
    return `
      <section class="models-panel-card">
        <h4>Guided setup</h4>
        <ol>
          ${(fr.steps || []).map((s) => `<li>${esc(s)}</li>`).join("")}
        </ol>
        <p>${fr.needed ? "No installed Ollama models detected yet." : "Models are installed — you can still re-run setup."}</p>
        <p class="muted">${esc(rec.why || "")}</p>
        <button type="button" class="apply-btn small" data-models-stack="balanced">Apply balanced stack (confirm)</button>
        <button type="button" class="ghost-btn small" id="modelsPullMissingBtn2">Pull missing</button>
        <button type="button" class="ghost-btn small" data-models-goto="providers">Validate providers</button>
      </section>`;
  }

  function renderBody() {
    const body = $("modelsHomeBody");
    if (!body) return;
    const map = {
      overview: renderOverview,
      roles: renderRoles,
      catalog: renderCatalog,
      providers: renderProviders,
      recommend: renderRecommend,
      pull: renderPull,
      packs: renderPacks,
      first_run: renderFirstRun,
    };
    body.innerHTML = (map[_tab] || renderOverview)();
    body.setAttribute("aria-labelledby", `models-tab-${_tab}`);
  }

  function buildTabs() {
    const nav = $("modelsHomeTabs");
    if (!nav) return;
    nav.setAttribute("role", "tablist");
    nav.innerHTML = TABS.map(
      ([id, label]) =>
        `<button type="button" class="mc-tab${id === _tab ? " active" : ""}" role="tab" id="models-tab-${id}"
          data-models-tab="${id}" aria-selected="${id === _tab}" aria-controls="modelsHomeBody">${esc(label)}</button>`
    ).join("");
    nav.querySelectorAll("[data-models-tab]").forEach((btn) => {
      btn.addEventListener("click", () => {
        _tab = btn.dataset.modelsTab;
        buildTabs();
        renderBody();
      });
      btn.addEventListener("keydown", (e) => {
        const tabs = [...nav.querySelectorAll("[data-models-tab]")];
        const i = tabs.indexOf(btn);
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          e.preventDefault();
          const n = tabs[(i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length];
          n.focus();
          n.click();
        }
      });
    });
  }

  async function refresh() {
    const st = $("modelsHomeStatus");
    if (st) st.textContent = "Loading…";
    try {
      _data = await api("/api/models/home");
      // Drain activity outbox into Activity Center
      try {
        const box = await api("/api/models/activity/outbox");
        (box.events || []).forEach((ev) => {
          window.AriaActivity?.add?.({
            category: "models",
            type: ev.type,
            severity: ev.severity,
            title: ev.title,
            message: ev.message,
            fix: ev.fix,
          });
        });
      } catch (_) {
        /* */
      }
      if (st) st.textContent = `Updated ${new Date().toLocaleTimeString()}`;
      buildTabs();
      renderBody();
    } catch (e) {
      if (st) st.textContent = e.message;
    }
  }

  async function saveRoles() {
    const roles = {};
    document.querySelectorAll("#modelsHomeBody [data-role-id]").forEach((sel) => {
      roles[sel.dataset.roleId] = sel.value;
    });
    const ok = await confirmAct("Save roles", "Update persistent role→model registry?");
    if (!ok) return;
    // advise first role
    try {
      const adv = await api(`/api/models/vram-advise?model=${encodeURIComponent(roles.conversation || "")}&action=assign`);
      if (adv.severity === "warning") {
        const cont = await confirmAct("VRAM warning", adv.message + "\n\nContinue anyway?");
        if (!cont) return;
      }
    } catch (_) {
      /* */
    }
    const out = await api("/api/models/settings/json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ roles }),
    });
    window.showAriaToast?.(out.switch?.message || "Roles saved", out.ok ? "ok" : "err");
    await refresh();
    window.loadChatModelSelect?.();
  }

  async function pullModel(tag) {
    const ok = await confirmAct("Pull model", `Pull ${tag}? This may take time and disk space.`);
    if (!ok) return;
    const log = $("modelsPullLog") || $("pullLog");
    if (log) {
      log.classList.remove("hidden");
      log.textContent = `Pulling ${tag}…\n`;
    }
    const form = new FormData();
    form.append("model", tag);
    const res = await fetch("/api/models/pull", { method: "POST", body: form });
    if (!res.ok || !res.body) {
      window.showAriaToast?.("Pull failed", "err");
      return;
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop() || "";
      for (const part of parts) {
        const line = part.replace(/^data:\s*/, "");
        try {
          const ev = JSON.parse(line);
          if (log) log.textContent += `${ev.status || ev.type || JSON.stringify(ev)}\n`;
        } catch (_) {
          if (log) log.textContent += line + "\n";
        }
      }
    }
    window.showAriaToast?.(`Pull finished: ${tag}`, "ok");
    await refresh();
  }

  function wireBody() {
    const body = $("modelsHomeBody");
    if (!body || body.dataset.wired) return;
    body.dataset.wired = "1";
    body.addEventListener("click", async (e) => {
      const t = e.target;
      if (!(t instanceof Element)) return;
      const goto = t.closest?.("[data-models-goto]");
      if (goto) {
        _tab = goto.dataset.modelsGoto;
        buildTabs();
        renderBody();
        return;
      }
      if (t.closest?.("[data-models-mc]")) {
        window.AriaActions?.goMc?.(t.closest("[data-models-mc]").dataset.modelsMc || "inference");
        return;
      }
      if (t.closest?.("[data-models-integrations]")) {
        window.switchToView?.("chat");
        document.getElementById("integrationsPanel")?.scrollIntoView?.({ behavior: "smooth" });
        document.querySelector('.sidebar-section[data-section="integrations"] .sidebar-section-head')?.click();
        return;
      }
      if (t.closest?.("#modelsFreeVramBtn") || t.id === "modelsFreeVramBtn") {
        document.getElementById("freeVramBtn")?.click();
        return;
      }
      if (t.closest?.("#modelsSaveRolesBtn")) {
        await saveRoles();
        return;
      }
      if (t.closest?.("#modelsAdvancedToggle")) {
        _advancedOpen = !_advancedOpen;
        renderBody();
        return;
      }
      const preset = t.closest?.("[data-models-preset]");
      if (preset) {
        const ok = await confirmAct("Apply preset", `Apply ${preset.dataset.modelsPreset} preset?`);
        if (!ok) return;
        const form = new FormData();
        form.append("preset", preset.dataset.modelsPreset);
        await fetch("/api/models/preset", { method: "POST", body: form });
        window.showAriaToast?.("Preset applied", "ok");
        await refresh();
        return;
      }
      if (t.closest?.("#modelsResetBtn")) {
        const ok = await confirmAct("Reset", "Reset to optimized defaults?");
        if (!ok) return;
        await fetch("/api/models/reset", { method: "POST", body: new FormData() });
        await refresh();
        return;
      }
      if (t.closest?.("#modelsExportBtn")) {
        const data = await api("/api/models/export");
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "aria-models-config.json";
        a.click();
        return;
      }
      if (t.closest?.("#modelsImportBtn")) {
        const raw = window.prompt?.("Paste exported Models JSON");
        if (!raw) return;
        const ok = await confirmAct("Import", "Import will overwrite role assignments.");
        if (!ok) return;
        try {
          const config = JSON.parse(raw);
          await api("/api/models/import", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ confirmed: true, config }),
          });
          window.showAriaToast?.("Imported", "ok");
          await refresh();
        } catch (err) {
          window.showAriaToast?.(err.message, "err");
        }
        return;
      }
      const assign = t.closest?.("[data-models-assign]");
      if (assign) {
        const tag = assign.dataset.modelsAssign;
        const ok = await confirmAct("Assign", `Set Chat (conversation) default to ${tag}?`);
        if (!ok) return;
        await api("/api/models/switch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scope: "role_default", role: "conversation", model: tag }),
        });
        window.showAriaToast?.(`Chat default → ${tag}`, "ok");
        await refresh();
        window.loadChatModelSelect?.();
        return;
      }
      const pull = t.closest?.("[data-models-pull]");
      if (pull) {
        await pullModel(pull.dataset.modelsPull);
        return;
      }
      const vram = t.closest?.("[data-models-vram]");
      if (vram) {
        const adv = await api(`/api/models/vram-advise?model=${encodeURIComponent(vram.dataset.modelsVram)}`);
        window.showAriaToast?.(adv.message, adv.severity === "ok" ? "ok" : "warn", 6000);
        return;
      }
      const stack = t.closest?.("[data-models-stack]");
      if (stack) {
        const ok = await confirmAct("Apply stack", `Apply recommended stack ${stack.dataset.modelsStack}? Never auto-applied.`);
        if (!ok) return;
        const out = await api("/api/models/recommend/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ stack_id: stack.dataset.modelsStack, confirmed: true }),
        });
        window.showAriaToast?.(out.message || out.switch?.message || "Stack applied", out.ok ? "ok" : "err");
        await refresh();
        return;
      }
      const val = t.closest?.("[data-models-validate]");
      if (val) {
        const out = await api("/api/models/providers/validate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider: val.dataset.modelsValidate }),
        });
        window.showAriaToast?.(out.message || (out.ok ? "OK" : out.error), out.ok ? "ok" : "warn");
        return;
      }
      if (t.closest?.("#modelsPullMissingBtn") || t.closest?.("#modelsPullMissingBtn2") || t.closest?.("#pullMissingBtn")) {
        document.getElementById("pullMissingBtn")?.click();
        _tab = "pull";
        buildTabs();
        await refresh();
        return;
      }
      if (t.closest?.("#modelsCatalogRefresh")) {
        const q = $("modelsCatalogQ")?.value || "";
        const capability = $("modelsCatalogCap")?.value || "";
        const sort = $("modelsCatalogSort")?.value || "name";
        const installed_only = !!$("modelsCatalogInstalled")?.checked;
        const params = new URLSearchParams({ q, capability, sort, installed_only: installed_only ? "1" : "0" });
        _data.catalog = await api(`/api/models/catalog?${params}`);
        renderBody();
        return;
      }
      if (t.closest?.("#modelsPackSaveBtn")) {
        const name = $("modelsPackName")?.value?.trim() || `pack-${Date.now()}`;
        const roles = {};
        ((_data.roles || {}).primary || []).concat((_data.roles || {}).advanced || []).forEach((r) => {
          if (r.model) roles[r.id] = r.model;
        });
        await api("/api/models/packs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: name, name, roles }),
        });
        window.showAriaToast?.("Pack saved", "ok");
        await refresh();
        return;
      }
      const pack = t.closest?.("[data-models-pack]");
      if (pack) {
        const ok = await confirmAct("Apply pack", `Apply pack ${pack.dataset.modelsPack}?`);
        if (!ok) return;
        await api(`/api/models/packs/${encodeURIComponent(pack.dataset.modelsPack)}/apply`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        await refresh();
      }
    });
  }

  function initModelsHome() {
    wireBody();
    $("modelsHomeRefreshBtn")?.addEventListener("click", refresh);
    $("modelsOpenMcBtn")?.addEventListener("click", () => window.AriaActions?.goMc?.("inference"));
    refresh();
  }

  window.initModelsHome = initModelsHome;
  window.openModelsHome = function (tab) {
    window.switchToView?.("models");
    if (tab) {
      _tab = tab;
      setTimeout(() => {
        buildTabs();
        renderBody();
      }, 80);
    }
  };
})();
