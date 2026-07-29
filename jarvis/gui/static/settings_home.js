/** Settings Home — preference catalog, search, deep links. Products own stores. */
(function () {
  "use strict";

  let _home = null;
  let _category = "all";
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

  function openDeepLink(open) {
    if (!open) return;
    if (open.action === "open_layouts" || open.type === "open_layouts") {
      window.AriaLayouts?.openModal?.() || window.AriaWorkspaces?.openModal?.();
      return;
    }
    if (open.action === "open_notifications" || open.type === "open_notifications") {
      window.openNotifications?.(open.filter) || window.AriaNotifications?.open?.(open.filter) || window.AriaActivity?.open?.();
      return;
    }
    if (open.action === "voice_chat_modal") {
      window.openVoiceChatSettings?.();
      return;
    }
    if (open.action === "uncensored") {
      document.getElementById("uncensoredToggle")?.focus();
      window.showAriaToast?.("Uncensored mode is in the Mode sidebar", "info");
      return;
    }
    const view = open.view || "settings";
    if (view === "workstation" && open.mc_tab) {
      window.switchToView?.("workstation");
      setTimeout(() => {
        const tab = document.querySelector(`.mc-tab[data-mc-tab="${open.mc_tab}"], [data-mc="${open.mc_tab}"]`);
        tab?.click();
        // Prefer runtime_config tab id after rename
        document.querySelector('[data-mc-tab="runtime_config"]')?.click();
      }, 120);
      return;
    }
    if (view === "settings" && open.section) {
      _category = open.section === "all" ? "all" : open.section;
      const sel = $("settingsCategoryFilter");
      if (sel) sel.value = _category === "all" ? "" : _category;
      renderList(_home?.preferences || []);
      if (open.pref) {
        _selected = open.pref;
        const item = (_home?.preferences || []).find((p) => p.id === open.pref);
        if (item) renderDetail(item);
      }
      return;
    }
    window.switchToView?.(view);
    if (open.focus) {
      setTimeout(() => document.getElementById(open.focus)?.focus(), 120);
    }
  }

  window.AriaSettingsOpen = openDeepLink;

  function renderCoach(warnings) {
    const el = $("settingsCoachCard");
    if (!el) return;
    if (!warnings?.length) {
      el.classList.add("hidden");
      el.innerHTML = "";
      return;
    }
    el.classList.remove("hidden");
    el.innerHTML =
      `<strong>Settings coach</strong><ul class="tiny">` +
      warnings
        .map(
          (w) =>
            `<li><button type="button" class="ghost-btn tiny settings-coach-link" data-open='${esc(JSON.stringify(w.deep_link || {}))}'>${esc(w.title)}</button> <span class="muted">${esc(w.detail || "")}</span></li>`
        )
        .join("") +
      `</ul><p class="muted tiny">Coach warns only — never auto-changes settings.</p>`;
  }

  function renderHealth(health) {
    const el = $("settingsHealthStrip");
    if (!el || !health) return;
    el.innerHTML = `
      <span>Catalog <strong>${esc(health.catalog_count)}</strong></span>
      <span>Stores <strong>${esc(health.stores_present)}/${esc(health.stores_tracked)}</strong></span>
      <span>Corrupt <strong>${esc(health.corrupt_count ?? 0)}</strong></span>
      <span>Profile <strong>${esc(health.active_profile || "default")}</strong></span>
    `;
  }

  function renderCategories(cats) {
    const sel = $("settingsCategoryFilter");
    if (!sel || sel.dataset.filled === "1") return;
    (cats || []).forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      sel.appendChild(opt);
    });
    sel.dataset.filled = "1";
  }

  function renderList(items) {
    const list = $("settingsPrefList");
    if (!list) return;
    let filtered = items || [];
    if (_category && _category !== "all") {
      filtered = filtered.filter((p) => p.category === _category);
    }
    if (!filtered.length) {
      list.innerHTML = `<li class="muted">No preferences match.</li>`;
      return;
    }
    list.innerHTML = filtered
      .map((p) => {
        const sel = p.id === _selected ? " is-selected" : "";
        return `<li class="settings-pref-item${sel}" role="option" tabindex="0" data-id="${esc(p.id)}" aria-selected="${p.id === _selected}">
          <div class="settings-pref-row">
            <span class="settings-cat-chip">${esc(p.category)}</span>
            <strong>${esc(p.title)}</strong>
            <span class="muted tiny">${esc(p.owner)}</span>
          </div>
          <div class="muted small">${esc((p.description || "").slice(0, 140))}</div>
        </li>`;
      })
      .join("");
  }

  function renderDetail(p) {
    const el = $("settingsPrefDetail");
    if (!el || !p) return;
    const open = p.deep_link || {};
    el.innerHTML = `
      <div class="settings-detail-head">
        <span class="settings-cat-chip">${esc(p.category)}</span>
        <h3>${esc(p.title)}</h3>
      </div>
      <p>${esc(p.description || "")}</p>
      <p class="muted small">Owner: <strong>${esc(p.owner)}</strong> · type ${esc(p.type)} · id <code>${esc(p.id)}</code></p>
      ${p.sensitive ? `<p class="settings-sensitive">Sensitive — confirm before changing.</p>` : ""}
      <div class="settings-detail-actions">
        <button type="button" class="apply-btn small" id="settingsOpenPrefBtn">Open</button>
        ${p.editable_in_settings ? `<span class="muted tiny">Editable in Settings</span>` : `<span class="muted tiny">Product owns store</span>`}
      </div>
    `;
    $("settingsOpenPrefBtn")?.addEventListener("click", () => openDeepLink(open));
  }

  function renderAppearance(app) {
    const theme = $("settingsThemeSelect");
    const accent = $("settingsAccentSelect");
    if (theme && app?.theme) theme.value = app.theme;
    if (accent && app?.accent) accent.value = app.accent;
    if ($("settingsDockToggle")) $("settingsDockToggle").checked = !app?.dock_hidden;
    if ($("settingsStatusToggle")) $("settingsStatusToggle").checked = !app?.status_bar_hidden;
    if ($("settingsMiniChatToggle")) $("settingsMiniChatToggle").checked = !app?.mini_chat_hidden;
  }

  function renderRecent(items) {
    const el = $("settingsRecentList");
    if (!el) return;
    if (!items?.length) {
      el.innerHTML = `<li class="muted">No recent changes.</li>`;
      return;
    }
    el.innerHTML = items
      .slice(0, 10)
      .map((h) => `<li><code>${esc(h.pref_id)}</code> <span class="muted tiny">${esc(h.detail || "")}</span></li>`)
      .join("");
  }

  function renderProfiles(profiles) {
    const el = $("settingsProfileSelect");
    if (!el) return;
    const active = profiles?.active || "default";
    const map = profiles?.profiles || {};
    el.innerHTML = Object.values(map)
      .map((p) => `<option value="${esc(p.id)}" ${p.id === active ? "selected" : ""}>${esc(p.name || p.id)}</option>`)
      .join("");
  }

  async function loadHome() {
    const q = $("settingsSearchInput")?.value?.trim() || "";
    const cat = $("settingsCategoryFilter")?.value || "";
    _category = cat || "all";
    const data = await api(
      `/api/settings/product/home?q=${encodeURIComponent(q)}&category=${encodeURIComponent(cat)}`
    );
    _home = data;
    renderCategories(data.categories);
    renderHealth(data.health);
    renderCoach(data.coach);
    renderList(data.preferences || []);
    renderAppearance(data.appearance);
    renderRecent(data.recent_changes);
    renderProfiles(data.profiles);
    const tips = $("settingsTipsList");
    if (tips && data.tips) tips.innerHTML = data.tips.map((t) => `<li>${esc(t)}</li>`).join("");
    if (!_selected && data.preferences?.length) {
      _selected = data.preferences[0].id;
      renderDetail(data.preferences[0]);
    }
  }

  function bind() {
    if ($("settingsHomeRoot")?.dataset.bound === "1") return;
    if ($("settingsHomeRoot")) $("settingsHomeRoot").dataset.bound = "1";

    $("settingsHomeRefreshBtn")?.addEventListener("click", () => loadHome());
    $("settingsSearchInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        loadHome();
      }
    });
    $("settingsSearchBtn")?.addEventListener("click", () => loadHome());
    $("settingsCategoryFilter")?.addEventListener("change", () => loadHome());
    $("settingsPrefList")?.addEventListener("click", (e) => {
      const li = e.target.closest("[data-id]");
      if (!li) return;
      _selected = li.getAttribute("data-id");
      const p = (_home?.preferences || []).find((x) => x.id === _selected);
      renderList(_home?.preferences || []);
      renderDetail(p);
    });
    $("settingsPrefList")?.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const li = e.target.closest("[data-id]");
      if (!li) return;
      e.preventDefault();
      const p = (_home?.preferences || []).find((x) => x.id === li.getAttribute("data-id"));
      if (p) openDeepLink(p.deep_link);
    });
    $("settingsCoachCard")?.addEventListener("click", (e) => {
      const btn = e.target.closest(".settings-coach-link");
      if (!btn) return;
      try {
        openDeepLink(JSON.parse(btn.getAttribute("data-open") || "{}"));
      } catch {
        /* ignore */
      }
    });
    $("settingsThemeSelect")?.addEventListener("change", async (e) => {
      const theme = e.target.value;
      await api("/api/settings/product/appearance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme }),
      });
      document.body.classList.toggle("light-theme", theme === "light");
      try {
        localStorage.setItem("aria_theme", theme);
        window.AriaUiPrefs?.set?.("theme", theme);
      } catch {
        /* ignore */
      }
      const btn = $("themeToggle");
      if (btn) btn.textContent = theme === "light" ? "Dark theme" : "Light theme";
    });
    $("settingsAccentSelect")?.addEventListener("change", async (e) => {
      const accent = e.target.value;
      await api("/api/settings/product/appearance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accent }),
      });
      window.applyAriaAccent?.(accent);
    });
    async function toggleChrome(key, checked, inverted) {
      const val = inverted ? !checked : checked;
      const patch = {};
      patch[key] = val;
      await api("/api/settings/product/appearance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
      if (key === "dock_hidden") window.AriaUiPrefs?.set?.("dockHidden", val);
      if (key === "status_bar_hidden") window.AriaUiPrefs?.set?.("statusBarHidden", val);
      if (key === "mini_chat_hidden") window.AriaUiPrefs?.set?.("miniChatHidden", val);
    }
    $("settingsDockToggle")?.addEventListener("change", (e) => toggleChrome("dock_hidden", e.target.checked, true));
    $("settingsStatusToggle")?.addEventListener("change", (e) => toggleChrome("status_bar_hidden", e.target.checked, true));
    $("settingsMiniChatToggle")?.addEventListener("change", (e) => toggleChrome("mini_chat_hidden", e.target.checked, true));
    $("settingsVoiceChatBtn")?.addEventListener("click", () => window.openVoiceChatSettings?.());
    $("settingsDiagBtn")?.addEventListener("click", async () => {
      const d = await api("/api/settings/product/diagnostics");
      console.info("Settings diagnostics", d);
      window.showAriaToast?.(`Settings diagnostics · ${d.health?.catalog_count || 0} prefs`, "info");
    });
    $("settingsResetAppearanceBtn")?.addEventListener("click", async () => {
      await api("/api/settings/product/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: "appearance" }),
      });
      loadHome();
      window.showAriaToast?.("Appearance reset", "ok");
    });
    $("settingsExportBtn")?.addEventListener("click", async () => {
      const bundle = await api("/api/settings/product/export");
      const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "aria-settings-export.json";
      a.click();
    });
    $("settingsSaveProfileBtn")?.addEventListener("click", async () => {
      const name = prompt("Profile name?", "My profile");
      if (!name) return;
      await api("/api/settings/product/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      loadHome();
    });
    $("settingsActivateProfileBtn")?.addEventListener("click", async () => {
      const id = $("settingsProfileSelect")?.value;
      if (!id) return;
      await api("/api/settings/product/profiles/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      loadHome();
      window.showAriaToast?.("Profile activated", "ok");
    });
  }

  async function initSettingsHome() {
    bind();
    // Migrate legacy aria_theme into Settings appearance
    try {
      const legacy = localStorage.getItem("aria_theme");
      if (legacy === "light" || legacy === "dark") {
        await api("/api/settings/product/appearance/migrate-theme", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ theme: legacy }),
        });
        window.AriaUiPrefs?.set?.("theme", legacy);
      }
    } catch {
      /* ignore */
    }
    await loadHome();
  }

  window.initSettingsHome = initSettingsHome;
  window.openSettingsHome = function (section) {
    window.switchToView?.("settings");
    setTimeout(() => {
      if (section) {
        const sel = $("settingsCategoryFilter");
        if (sel) {
          sel.value = section;
          loadHome();
        }
      }
      $("settingsSearchInput")?.focus();
    }, 60);
  };
})();
