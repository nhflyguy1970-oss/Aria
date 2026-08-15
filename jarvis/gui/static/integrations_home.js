/** Integrations Home — provider matrix, tests, unlocks, honest security. */
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

  async function api(path, opts) {
    const res = await fetch(path, opts);
    return res.json();
  }

  function fillCategories(categories) {
    const sel = $("integrationsCategoryFilter");
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
    const el = $("integrationsSummary");
    if (!el) return;
    const s = home.summary || {};
    el.innerHTML = [
      ["Configured", s.configured],
      ["Available", s.available],
      ["Managed elsewhere", s.managed_elsewhere],
      ["Total", s.total],
    ]
      .map(([label, n]) => `<div class="integrations-stat"><span class="muted">${esc(label)}</span><strong>${n ?? 0}</strong></div>`)
      .join("");
  }

  function renderRecovery(recovery) {
    const card = $("integrationsRecoveryCard");
    if (!card) return;
    if (recovery?.ready) {
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
    const list = $("integrationsProviderList");
    if (!list) return;
    if (!items.length) {
      list.innerHTML = `<li class="muted">No providers match.</li>`;
      return;
    }
    list.innerHTML = items
      .map((p) => {
        const sel = p.id === _selected ? " is-selected" : "";
        return `<li class="integrations-provider-item${sel}" role="option" tabindex="-1" data-id="${esc(p.id)}" aria-selected="${p.id === _selected}">
          <div class="integrations-provider-row">
            <strong>${esc(p.name)}</strong>
            <span class="integrations-status integrations-status--${esc(p.status)}">${esc(p.status)}</span>
          </div>
          <div class="muted small">${esc(p.category)} · owner ${esc(p.owner_product)} · ${p.configured ? "configured" : "not set"}</div>
        </li>`;
      })
      .join("");
    list.querySelectorAll(".integrations-provider-item").forEach((li) => {
      li.addEventListener("click", () => selectItem(li.dataset.id));
      li.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectItem(li.dataset.id);
        }
      });
    });
  }

  function fieldForProvider(p) {
    return p.secret_field || "";
  }

  function renderDetail(p) {
    const el = $("integrationsProviderDetail");
    if (!el) return;
    if (!p) {
      el.innerHTML = `<p class="muted">Select a provider to review unlocks, test connection, and manage credentials.</p>`;
      return;
    }
    const unlocks = (p.unlocks || []).map((u) => `<li>${esc(u)}</li>`).join("") || "<li class='muted'>None listed</li>";
    const field = fieldForProvider(p);
    const managed = p.managed_elsewhere
      ? `<p class="muted small">Managed in <strong>${esc(p.managed_path || p.owner_product)}</strong>. Integrations shows health only.</p>`
      : "";
    const keyForm = field && !p.managed_elsewhere
      ? `<label class="integrations-setting"><span>API key / token</span>
           <input type="password" id="integrationsDetailKey" class="audio-path-input" placeholder="Paste new value to save" autocomplete="off" aria-label="Provider secret" />
           <span class="muted small">Current: ${esc(p.secret_preview || "not set")}</span></label>
         <div class="integrations-detail-actions">
           <button type="button" class="apply-btn small" id="integrationsDetailSaveBtn">Save key</button>
           <button type="button" class="ghost-btn small" id="integrationsDetailClearBtn">Clear key</button>
           <button type="button" class="ghost-btn small" id="integrationsDetailTestBtn">Test connection</button>
           <button type="button" class="ghost-btn small" id="integrationsDetailToggleBtn">${p.enabled === false ? "Enable" : "Disable"}</button>
         </div>`
      : `<div class="integrations-detail-actions">
           <button type="button" class="ghost-btn small" id="integrationsDetailTestBtn">Test connection</button>
         </div>`;
    el.innerHTML = `
      <h3>${esc(p.name)}</h3>
      <p class="muted small">${esc(p.id)} · ${esc(p.kind)} · owner <strong>${esc(p.owner_product)}</strong></p>
      <p>${esc(p.purpose || "")}</p>
      ${managed}
      <p>Status: <strong>${esc(p.status)}</strong>${p.secret_preview ? ` · ${esc(p.secret_preview)}` : ""}</p>
      <h4 class="flytying-col-subtitle">This provider unlocks</h4>
      <ul>${unlocks}</ul>
      <p id="integrationsTestResult" class="muted small" aria-live="polite"></p>
      ${keyForm}
      ${p.docs ? `<p class="muted small">Docs: ${esc(p.docs)}</p>` : ""}`;
    $("integrationsDetailTestBtn")?.addEventListener("click", () => testProvider(p.id));
    $("integrationsDetailSaveBtn")?.addEventListener("click", () => saveKey(field));
    $("integrationsDetailClearBtn")?.addEventListener("click", () => clearKey(field));
    $("integrationsDetailToggleBtn")?.addEventListener("click", () => toggleProvider(p.id, p.enabled === false));
  }

  function selectItem(id) {
    _selected = id;
    const item = _items.find((x) => x.id === id);
    renderList(_items);
    renderDetail(item);
  }

  async function testProvider(id) {
    const out = $("integrationsTestResult");
    if (out) out.textContent = "Testing…";
    const data = await api("/api/integrations/product/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    const msg = data.message || data.error || (data.ok ? "OK" : "Failed");
    if (out) {
      out.textContent = `${data.ok ? "✓" : "✗"} ${msg}${data.latency_ms != null ? ` · ${data.latency_ms}ms` : ""}${data.recovery ? " — " + data.recovery : ""}`;
    }
    window.showAriaToast?.(msg, data.ok ? "ok" : "err");
  }

  async function saveKey(field) {
    const val = $("integrationsDetailKey")?.value?.trim();
    if (!val || !field) {
      window.showAriaToast?.("Paste a key first", "warn");
      return;
    }
    const body = {};
    body[field] = val;
    const data = await api("/api/integrations/product/secrets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    window.showAriaToast?.(data.ok ? "Saved" : data.message || "Save failed", data.ok ? "ok" : "err");
    if ($("integrationsDetailKey")) $("integrationsDetailKey").value = "";
    await loadHome();
    selectItem(_selected);
    window.loadIntegrationsPanel?.();
  }

  async function clearKey(field) {
    if (!field) return;
    if (!window.confirm?.("Clear this secret from jarvis.env?")) return;
    await api("/api/integrations/product/secrets/clear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ field }),
    });
    window.showAriaToast?.("Cleared", "ok");
    await loadHome();
    selectItem(_selected);
  }

  async function toggleProvider(id, enable) {
    await api("/api/integrations/product/enable", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, enabled: enable }),
    });
    await loadHome();
    selectItem(id);
  }

  async function loadHome() {
    const q = $("integrationsSearchInput")?.value || "";
    const category = $("integrationsCategoryFilter")?.value || "";
    const params = new URLSearchParams({ q, category });
    try {
      const home = await api(`/api/integrations/product/home?${params}`);
      fillCategories(home.categories);
      _items = home.providers || [];
      renderSummary(home);
      renderRecovery(home.recovery);
      renderList(_items);
      if (_selected) selectItem(_selected);
      else if (_items[0]) selectItem(_items[0].id);
      const banner = $("integrationsSecurityBanner");
      if (banner && home.security?.message) banner.textContent = home.security.message;
      const usage = $("integrationsUsageList");
      if (usage) {
        usage.innerHTML = (home.usage || [])
          .map((u) => `<li><span class="muted">${esc(u.iso)}</span> ${esc(u.provider_id)} ${esc(u.action)} — ${u.ok ? "ok" : "fail"} ${esc(u.message)}</li>`)
          .join("") || "<li class='muted'>No activity yet</li>";
      }
    } catch (e) {
      if (
        window.AriaNet?.isRoomAbort?.(e) ||
        e?.name === "AbortError" ||
        /aborted|aria-room-leave/i.test(String(e?.message || ""))
      ) {
        return;
      }
      window.showAriaToast?.(e.message || "Integrations load failed", "err");
    }
  }

  async function loadExperimental() {
    const el = $("integrationsExperimental");
    if (!el) return;
    try {
      const data = await api("/api/integrations/product/experimental");
      el.innerHTML = (data.items || [])
        .map((i) => `<p><strong>${esc(i.name)}</strong> · ${esc(i.status)} · ${i.available ? "available" : "unavailable"}<br/><span class="muted">${esc(i.summary)}</span></p>`)
        .join("");
    } catch (_) {
      el.textContent = "Experimental status unavailable";
    }
  }

  function bind() {
    if (bind._done) return;
    bind._done = true;
    $("integrationsHomeRefreshBtn")?.addEventListener("click", () => loadHome());
    $("integrationsTestAllBtn")?.addEventListener("click", async () => {
      const data = await api("/api/integrations/product/test-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ configured_only: true }),
      });
      window.showAriaToast?.(data.ok ? "Tests complete" : "Some tests failed", data.ok ? "ok" : "warn");
      loadHome();
    });
    $("integrationsDiagHomeBtn")?.addEventListener("click", async () => {
      const data = await api("/api/integrations/product/diagnostics");
      console.info("Integrations diagnostics", data);
      window.showAriaToast?.(`Integrations: ${data.health?.configured_count ?? "?"} configured`, "ok");
    });
    $("integrationsSearchInput")?.addEventListener("input", () => loadHome());
    $("integrationsCategoryFilter")?.addEventListener("change", () => loadHome());
    $("integrationsProviderList")?.addEventListener("keydown", (e) => {
      const items = [...($("integrationsProviderList")?.querySelectorAll(".integrations-provider-item") || [])];
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

  window.initIntegrationsHome = function initIntegrationsHome() {
    bind();
    loadHome();
    loadExperimental();
  };
})();
