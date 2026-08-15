/** Capabilities Home — unified registry for everything that extends Aria. */
(function () {
  let _items = [];
  let _selected = "";

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function trustClass(trust) {
    return `cap-trust cap-trust--${esc(trust || "unknown")}`;
  }

  async function api(path, opts) {
    const res = await fetch(path, opts);
    return res.json();
  }

  function fillCategories(categories) {
    const sel = $("capabilitiesCategoryFilter");
    if (!sel || sel.dataset.filled === "1") return;
    (categories || []).forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      sel.appendChild(opt);
    });
    sel.dataset.filled = "1";
  }

  function renderSummary(home) {
    const el = $("capabilitiesSummary");
    if (!el) return;
    const s = home.summary || {};
    el.innerHTML = [
      ["Installed", s.installed],
      ["Built-in", s.built_in],
      ["Enabled", s.enabled],
      ["Disabled", s.disabled],
      ["Failed", s.failed],
      ["Experimental", s.experimental],
      ["Updates", s.updates],
    ]
      .map(([label, n]) => `<div class="capabilities-stat"><span class="muted">${esc(label)}</span><strong>${n ?? 0}</strong></div>`)
      .join("");
  }

  function renderRecovery(recovery) {
    const card = $("capabilitiesRecoveryCard");
    if (!card) return;
    if (recovery && recovery.ready) {
      card.classList.add("hidden");
      card.innerHTML = "";
      return;
    }
    card.classList.remove("hidden");
    const steps = (recovery?.steps || [])
      .map((s) => `<li>${s.done ? "✓" : "○"} ${esc(s.label)} — <span class="muted">${esc(s.detail)}</span></li>`)
      .join("");
    card.innerHTML = `<strong>Recovery</strong><p class="muted small">${esc(recovery?.hint || "")}</p><ol class="tiny">${steps}</ol>`;
  }

  function renderList(items) {
    const list = $("capabilitiesList");
    if (!list) return;
    if (!items.length) {
      list.innerHTML = `<li class="muted" role="option">No capabilities match.</li>`;
      return;
    }
    list.innerHTML = items
      .map((item) => {
        const selected = item.id === _selected ? " aria-selected=\"true\" class=\"capabilities-item is-selected\"" : " aria-selected=\"false\" class=\"capabilities-item\"";
        return `<li role="option" tabindex="-1" data-id="${esc(item.id)}"${selected}>
          <div class="capabilities-item-row">
            <strong>${esc(item.name)}</strong>
            <span class="${trustClass(item.trust)}">${esc(item.trust_label || item.trust)}</span>
          </div>
          <div class="muted small">${esc(item.layer)} · ${esc(item.category)} · ${esc(item.status)} · ${item.enabled ? "on" : "off"}</div>
        </li>`;
      })
      .join("");
    list.querySelectorAll(".capabilities-item").forEach((li) => {
      li.addEventListener("click", () => selectItem(li.dataset.id));
      li.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectItem(li.dataset.id);
        }
      });
    });
  }

  function renderDetail(item) {
    const el = $("capabilitiesDetail");
    if (!el) return;
    if (!item) {
      el.innerHTML = `<p class="muted">Select a capability to review permissions, trust, and health.</p>`;
      return;
    }
    const perms = (item.permission_labels || item.permissions || []).map((p) => `<li>${esc(p)}</li>`).join("") || "<li class='muted'>None declared</li>";
    const schema = item.metadata?.settings_schema || {};
    let settingsForm = "";
    if (schema && schema.properties) {
      settingsForm = Object.keys(schema.properties)
        .map((key) => {
          const prop = schema.properties[key] || {};
          return `<label class="capabilities-setting"><span>${esc(prop.title || key)}</span>
            <input type="text" data-setting-key="${esc(key)}" class="audio-path-input" value="${esc(prop.default || "")}" aria-label="${esc(prop.title || key)}" /></label>`;
        })
        .join("");
      if (settingsForm) settingsForm = `<div class="capabilities-settings"><h4 class="flytying-col-subtitle">Settings</h4>${settingsForm}</div>`;
    }
    el.innerHTML = `
      <h3>${esc(item.name)}</h3>
      <p class="muted small">${esc(item.id)} · v${esc(item.version)} · ${esc(item.author || "—")}</p>
      <p>${esc(item.description || "")}</p>
      <p><span class="${trustClass(item.trust)}">${esc(item.trust_label || item.trust)}</span>
         · health <strong>${esc(item.health)}</strong> · status <strong>${esc(item.status)}</strong></p>
      <p class="capabilities-risk">${esc(item.risk_summary || "")}</p>
      <p class="muted small">${esc(item.isolation_note || "")}</p>
      <h4 class="flytying-col-subtitle">Permissions</h4>
      <ul class="capabilities-perm-list">${perms}</ul>
      ${item.error ? `<p class="err">${esc(item.error)}</p>` : ""}
      ${settingsForm}
      <div class="capabilities-detail-actions">
        ${item.enabled
          ? `<button type="button" class="ghost-btn small" id="capDisableBtn">Disable</button>`
          : `<button type="button" class="apply-btn small" id="capEnableBtn">Enable</button>`}
        <button type="button" class="ghost-btn small" id="capLoadBtn">Load</button>
        <button type="button" class="ghost-btn small" id="capHotReloadBtn">Hot reload</button>
        ${item.trust === "quarantined" || item.status === "quarantined"
          ? `<button type="button" class="ghost-btn small" id="capAckBtn">Acknowledge quarantine</button>`
          : ""}
      </div>`;
    $("capEnableBtn")?.addEventListener("click", () => enableItem(item.id));
    $("capDisableBtn")?.addEventListener("click", () => disableItem(item.id));
    $("capLoadBtn")?.addEventListener("click", () => loadItem(item.id));
    $("capHotReloadBtn")?.addEventListener("click", () => hotReload(item.id));
    $("capAckBtn")?.addEventListener("click", () => acknowledge(item.id));
  }

  function selectItem(id) {
    _selected = id;
    const item = _items.find((x) => x.id === id);
    renderList(_items);
    renderDetail(item);
  }

  async function enableItem(id) {
    const data = await api("/api/capabilities/product/enable", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, load_now: true }),
    });
    window.showAriaToast?.(data.message || (data.ok ? "Enabled" : "Enable failed"), data.ok ? "ok" : "err");
    await loadHome();
    selectItem(id);
  }

  async function disableItem(id) {
    const data = await api("/api/capabilities/product/disable", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    window.showAriaToast?.(data.message || (data.ok ? "Disabled" : "Disable failed"), data.ok ? "ok" : "err");
    await loadHome();
    selectItem(id);
  }

  async function loadItem(id) {
    const data = await api("/api/capabilities/product/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    window.showAriaToast?.(data.ok ? "Load complete" : data.failed?.[0]?.error || "Load failed", data.ok ? "ok" : "err");
    await loadHome();
  }

  async function hotReload(id) {
    const data = await api("/api/capabilities/product/hot-reload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    window.showAriaToast?.(data.message || (data.ok ? "Hot reloaded" : "Hot reload failed"), data.ok ? "ok" : "err");
    await loadHome();
  }

  async function acknowledge(id) {
    await api("/api/capabilities/product/acknowledge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, reenable: false }),
    });
    window.showAriaToast?.("Quarantine acknowledged", "ok");
    await loadHome();
  }

  async function loadHome() {
    const q = $("capabilitiesSearchInput")?.value || "";
    const layer = $("capabilitiesLayerFilter")?.value || "";
    const category = $("capabilitiesCategoryFilter")?.value || "";
    const trust = $("capabilitiesTrustFilter")?.value || "";
    const params = new URLSearchParams({ q, layer, category, trust });
    try {
      const home = await api(`/api/capabilities/product/home?${params}`);
      fillCategories(home.categories);
      _items = home.items || [];
      renderSummary(home);
      renderRecovery(home.recovery);
      renderList(_items);
      if (_selected) selectItem(_selected);
      else if (_items[0]) selectItem(_items[0].id);
      const act = $("capabilitiesActivity");
      if (act) {
        act.innerHTML = (home.activity || [])
          .map((a) => `<li><span class="muted">${esc(a.iso)}</span> ${esc(a.kind)} ${esc(a.capability_id)} — ${esc(a.message)}</li>`)
          .join("") || "<li class='muted'>No activity yet</li>";
      }
      const banner = $("capabilitiesSecurityBanner");
      if (banner && home.security?.message) banner.textContent = home.security.message;
    } catch (e) {
      if (
        window.AriaNet?.isRoomAbort?.(e) ||
        e?.name === "AbortError" ||
        /aborted|aria-room-leave/i.test(String(e?.message || ""))
      ) {
        return;
      }
      window.showAriaToast?.(e.message || "Capabilities load failed", "err");
    }
  }

  async function loadExperimental() {
    const el = $("capabilitiesExperimental");
    if (!el) return;
    try {
      const data = await api("/api/capabilities/product/experimental");
      el.innerHTML = (data.items || [])
        .map(
          (i) =>
            `<p><strong>${esc(i.name)}</strong> · ${esc(i.status)} · ${i.available ? "available" : "unavailable"}<br/><span class="muted">${esc(i.summary)}</span></p>`
        )
        .join("");
    } catch (_) {
      el.textContent = "Experimental status unavailable";
    }
  }

  function bind() {
    $("capabilitiesRefreshBtn")?.addEventListener("click", () => loadHome());
    $("capabilitiesLoadAllBtn")?.addEventListener("click", async () => {
      const data = await api("/api/capabilities/product/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ all: true }),
      });
      window.showAriaToast?.(data.ok ? "Enabled capabilities loaded" : "Load finished with errors", data.ok ? "ok" : "warn");
      loadHome();
    });
    $("capabilitiesScaffoldBtn")?.addEventListener("click", async () => {
      const name = window.prompt?.("New capability name");
      if (!name) return;
      const data = await api("/api/capabilities/product/scaffold", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      window.showAriaToast?.(data.message || (data.ok ? "Scaffolded (disabled)" : "Scaffold failed"), data.ok ? "ok" : "err");
      loadHome();
    });
    $("capabilitiesDiagBtn")?.addEventListener("click", async () => {
      const data = await api("/api/capabilities/product/diagnostics");
      window.showAriaToast?.(`Diagnostics: ${data.registry?.count ?? "?"} capabilities`, "ok");
      console.info("Capabilities diagnostics", data);
    });
    ["capabilitiesSearchInput", "capabilitiesLayerFilter", "capabilitiesCategoryFilter", "capabilitiesTrustFilter"].forEach((id) => {
      $(id)?.addEventListener("change", () => loadHome());
      $(id)?.addEventListener("input", () => {
        if (id === "capabilitiesSearchInput") loadHome();
      });
    });
    $("capabilitiesList")?.addEventListener("keydown", (e) => {
      const items = [...($("capabilitiesList")?.querySelectorAll(".capabilities-item") || [])];
      const idx = items.findIndex((el) => el.dataset.id === _selected);
      if (e.key === "ArrowDown" && items[idx + 1]) {
        e.preventDefault();
        selectItem(items[idx + 1].dataset.id);
        items[idx + 1].focus();
      } else if (e.key === "ArrowUp" && items[idx - 1]) {
        e.preventDefault();
        selectItem(items[idx - 1].dataset.id);
        items[idx - 1].focus();
      }
    });
  }

  window.initCapabilities = function initCapabilities() {
    bind();
    loadHome();
    loadExperimental();
  };
})();
