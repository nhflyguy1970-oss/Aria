/** Layouts — shell presentation profiles (formerly Workspace layouts). */
(function () {
  "use strict";

  const LEGACY_PRESET_ALIAS = { dashboard: "home" };
  let _catalog = null;
  let _previewChanges = [];

  function $(id) {
    return document.getElementById(id);
  }

  function prefsGet(key, fallback) {
    return window.AriaUiPrefs?.get?.(key, fallback);
  }

  function prefsSet(key, val) {
    window.AriaUiPrefs?.set?.(key, val);
  }

  function snapshot() {
    const prefs = window.AriaUiPrefs?.load?.() || {};
    const theme = document.body.classList.contains("light-theme") ? "light" : prefs.theme || "dark";
    return {
      schema_version: 1,
      view: document.querySelector(".view-tab.active")?.dataset?.view || "chat",
      favorites: [...(prefs.favorites || [])],
      sidebarCollapsed: prefs.sidebarCollapsed || null,
      sidebarWidth: prefs.sidebarWidth || 260,
      dockHidden: !!prefs.dockHidden,
      statusBarHidden: !!prefs.statusBarHidden,
      miniChatHidden: !!prefs.miniChatHidden,
      dashboardLayout: prefs.dashboardLayout || null,
      theme,
      accent: prefs.accent || "gold",
      panelCollapsed: prefs.panelCollapsed || {},
      module: window.jarvisPreferredModule || "",
      model: $("chatModelSelect")?.value || "",
      density: prefs.dashboardLayout?.density || "comfortable",
      role: prefsGet("activeLayoutRole", "default") || "default",
      split: window.AriaSplitView?.getState?.() || {
        enabled: false,
        primary: null,
        secondary: null,
        ratio: 0.55,
      },
      savedAt: Date.now(),
    };
  }

  function applySnapshot(snap, label) {
    if (!snap) return false;
    try {
      if (Array.isArray(snap.favorites)) window.AriaFavorites?.setFavorites?.(snap.favorites);
      if (snap.sidebarWidth) {
        document.documentElement.style.setProperty("--sidebar-width", `${snap.sidebarWidth}px`);
        const app = document.querySelector(".app");
        if (app) app.style.gridTemplateColumns = `${snap.sidebarWidth}px minmax(0, 1fr)`;
        prefsSet("sidebarWidth", snap.sidebarWidth);
      }
      if (snap.sidebarCollapsed && typeof snap.sidebarCollapsed === "object") {
        prefsSet("sidebarCollapsed", snap.sidebarCollapsed);
        document.querySelectorAll(".sidebar-section[data-section]").forEach((sec) => {
          const key = sec.dataset.section;
          if (!key || sec.classList.contains("sidebar-section--pinned")) return;
          const collapsed = !!snap.sidebarCollapsed[key];
          sec.classList.toggle("collapsed", collapsed);
          sec.querySelector(".sidebar-section-head")?.setAttribute("aria-expanded", collapsed ? "false" : "true");
        });
      }
      prefsSet("dockHidden", !!snap.dockHidden);
      prefsSet("statusBarHidden", !!snap.statusBarHidden);
      if (typeof snap.miniChatHidden === "boolean") prefsSet("miniChatHidden", snap.miniChatHidden);
      window.AriaQuickDock?.render?.();
      window.AriaStatusBar?.apply?.();
      if (snap.dashboardLayout) prefsSet("dashboardLayout", snap.dashboardLayout);
      if (snap.panelCollapsed && typeof snap.panelCollapsed === "object") {
        prefsSet("panelCollapsed", snap.panelCollapsed);
      }
      if (snap.theme === "light" || snap.theme === "dark") {
        prefsSet("theme", snap.theme);
        document.body.classList.toggle("light-theme", snap.theme === "light");
        const btn = $("themeToggle");
        if (btn) btn.textContent = snap.theme === "light" ? "Dark theme" : "Light theme";
      }
      if (snap.accent) window.applyAriaAccent?.(snap.accent);
      if (snap.module != null) {
        window.jarvisPreferredModule = snap.module;
        document.querySelectorAll(".module-chip").forEach((c) => {
          c.classList.toggle("active", (c.dataset.module || "all") === (snap.module || "all"));
        });
      }
      if (snap.model) {
        const sel = $("chatModelSelect");
        if (sel) {
          sel.value = snap.model;
          sel.dispatchEvent(new Event("change", { bubbles: true }));
        }
      }
      if (snap.role) prefsSet("activeLayoutRole", snap.role);
      if (snap.split?.enabled) {
        window.AriaSplitView?.enable?.(snap.split.primary, snap.split.secondary);
      } else {
        window.AriaSplitView?.disable?.();
      }
      if (snap.view) window.switchToView?.(snap.view);
      window.showAriaToast?.(label ? `Layout: ${label}` : "Layout restored", "ok", 2500);
      updateActiveIndicator(label || "");
      return true;
    } catch (err) {
      window.showAriaToast?.(err.message || "Layout apply failed", "err", 4000);
      return false;
    }
  }

  function updateActiveIndicator(label) {
    const id = prefsGet("activeWorkspace", "") || prefsGet("activeLayout", "");
    const text = label || id || "Layouts";
    document.querySelectorAll("[data-layout-active-label]").forEach((el) => {
      if (el.id === "statusSegLayoutWrap") return;
      if (el.tagName === "BUTTON" && el.id === "workspaceLayoutsBtn") {
        el.textContent = text === "Layouts" ? "Layouts" : text;
        el.title = `Layouts — ${text} (Ctrl+Shift+L)`;
        return;
      }
      el.textContent = text;
    });
    const status = $("statusSegLayout");
    if (status) status.textContent = text && text !== "Layouts" ? `Layout: ${text}` : "Layouts";
  }

  async function fetchCatalog(force) {
    if (_catalog && !force) return _catalog;
    try {
      const res = await fetch("/api/layouts/catalog", { cache: "no-store" });
      const data = await res.json();
      if (data.ok !== false) _catalog = data;
      return _catalog;
    } catch {
      return _catalog;
    }
  }

  async function applyLayout(layoutId, opts = {}) {
    const id = LEGACY_PRESET_ALIAS[layoutId] || layoutId;
    const current = snapshot();
    let preview = null;
    try {
      const res = await fetch("/api/layouts/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ layout_id: id, current }),
      });
      preview = await res.json();
    } catch (err) {
      window.showAriaToast?.(err.message || "Layout preview failed", "err", 4000);
      return false;
    }
    if (!preview?.ok) {
      window.showAriaToast?.(preview?.error || "Layout unavailable", "warn", 3500);
      return false;
    }
    if (opts.previewOnly) {
      _previewChanges = preview.changes || [];
      return preview;
    }
    if (opts.confirm !== false && (preview.change_count || 0) > 6 && !opts.quiet) {
      const summary = (preview.changes || [])
        .slice(0, 5)
        .map((c) => c.field)
        .join(", ");
      if (!window.confirm?.(`Apply “${preview.label}”? Changes: ${summary || "chrome"}`)) {
        return false;
      }
    }
    const ok = applySnapshot(preview.snapshot, preview.label);
    try {
      await fetch("/api/layouts/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ layout_id: id, current, client_ok: ok }),
      });
    } catch {
      /* local apply still done */
    }
    prefsSet("activeWorkspace", id); // compat key
    prefsSet("activeLayout", id);
    window.AriaHistory?.push?.("workflows", `layout:${id}`, 12);
    if (preview.recommended_project && !opts.quiet) {
      maybeOfferProject();
    }
    renderSwitcher();
    return ok;
  }

  async function undoLayout() {
    const current = snapshot();
    try {
      const res = await fetch("/api/layouts/undo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current }),
      });
      const data = await res.json();
      if (!data.ok) {
        window.showAriaToast?.(data.error || "Nothing to undo", "warn", 2500);
        return false;
      }
      applySnapshot(data.snapshot, data.label || "Previous");
      renderSwitcher();
      return true;
    } catch (err) {
      window.showAriaToast?.(err.message || "Undo failed", "err", 3500);
      return false;
    }
  }

  async function saveCurrent(name, { overwrite = false } = {}) {
    const label = String(name || "").trim();
    if (!label) {
      window.showAriaToast?.("Name your layout first", "warn", 2500);
      return false;
    }
    const snap = snapshot();
    try {
      const res = await fetch("/api/layouts/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: label, snapshot: snap, overwrite }),
      });
      const data = await res.json();
      if (data.needs_confirm || data.error === "exists") {
        if (window.confirm?.(`Overwrite layout “${label}”?`)) {
          return saveCurrent(label, { overwrite: true });
        }
        return false;
      }
      if (!data.ok) {
        window.showAriaToast?.(data.error || "Save failed", "err", 3500);
        return false;
      }
      // Mirror into local prefs for offline
      const layouts = prefsGet("workspaceLayouts", {}) || {};
      layouts[data.layout_id] = { label, ...snap };
      prefsSet("workspaceLayouts", layouts);
      prefsSet("activeWorkspace", data.layout_id);
      prefsSet("activeLayout", data.layout_id);
      window.showAriaToast?.(`Saved layout “${label}”`, "ok", 2500);
      $("workspaceNameInput") && ($("workspaceNameInput").value = "");
      await fetchCatalog(true);
      renderSwitcher();
      return true;
    } catch (err) {
      window.showAriaToast?.(err.message || "Save failed", "err", 3500);
      return false;
    }
  }

  async function deleteCustom(id) {
    const settings = _catalog?.settings || {};
    if (settings.confirm_delete !== false) {
      if (!window.confirm?.(`Delete layout “${id}”?`)) return;
    }
    try {
      const res = await fetch(`/api/layouts/custom/${encodeURIComponent(id)}?confirm=true`, {
        method: "DELETE",
      });
      const data = await res.json().catch(() => ({}));
      if (!data.ok) {
        window.showAriaToast?.(data.error || "Delete failed", "err", 3000);
        return;
      }
    } catch {
      /* fall through to local */
    }
    const layouts = prefsGet("workspaceLayouts", {}) || {};
    delete layouts[id];
    prefsSet("workspaceLayouts", layouts);
    if (prefsGet("activeWorkspace") === id || prefsGet("activeLayout") === id) {
      prefsSet("activeWorkspace", "");
      prefsSet("activeLayout", "");
    }
    window.showAriaToast?.("Layout deleted", "ok", 2000);
    await fetchCatalog(true);
    renderSwitcher();
  }

  function renderSwitcher(filterQ) {
    const host = $("workspaceSwitcherList");
    if (!host) return;
    host.replaceChildren();
    const q = String(filterQ ?? $("layoutsTypeahead")?.value || "")
      .trim()
      .toLowerCase();
    const active = prefsGet("activeLayout", "") || prefsGet("activeWorkspace", "");
    const builtins = (_catalog?.builtins || []).filter(
      (b) => !q || `${b.id} ${b.label} ${b.description || ""} ${(b.aliases || []).join(" ")}`.toLowerCase().includes(q)
    );
    const customs = (_catalog?.customs || []).filter(
      (c) => !q || `${c.id} ${c.label}`.toLowerCase().includes(q)
    );

    const addChip = (id, label, kind, onClick) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `ghost-btn small workspace-chip layout-chip${active === id ? " active" : ""}`;
      btn.textContent = label;
      btn.title = kind === "starter" ? `Starter layout (frozen): ${label}` : `Apply layout: ${label}`;
      btn.setAttribute("aria-pressed", active === id ? "true" : "false");
      btn.dataset.layoutId = id;
      btn.addEventListener("click", onClick);
      return btn;
    };

    if (builtins.length) {
      const head = document.createElement("p");
      head.className = "muted tiny";
      head.textContent = "Starter layouts (full frozen snapshots)";
      host.appendChild(head);
      builtins.forEach((b) => {
        host.appendChild(addChip(b.id, b.label, b.kind, () => applyLayout(b.id)));
      });
    }

    // Offline fallback presets if API cold
    if (!(_catalog?.builtins || []).length) {
      ["coding", "writing", "research", "planning", "media", "maker", "flytying", "home"]
        .filter((id) => !q || id.includes(q))
        .forEach((id) => {
          host.appendChild(addChip(id, id, "starter", () => applyLayout(id)));
        });
    }

    const localCustoms = prefsGet("workspaceLayouts", {}) || {};
    const customIds = new Set([
      ...customs.map((c) => c.id),
      ...Object.keys(localCustoms).filter(
        (id) => !q || `${id} ${localCustoms[id]?.label || ""}`.toLowerCase().includes(q)
      ),
    ]);
    if (customIds.size) {
      const head = document.createElement("p");
      head.className = "muted tiny";
      head.textContent = "Custom layouts";
      host.appendChild(head);
    }
    customIds.forEach((id) => {
      const fromApi = customs.find((c) => c.id === id);
      const label = fromApi?.label || localCustoms[id]?.label || id;
      const wrap = document.createElement("div");
      wrap.className = "workspace-custom-row";
      const btn = addChip(id, label, "custom", () => applyLayout(id));
      const del = document.createElement("button");
      del.type = "button";
      del.className = "ghost-btn tiny";
      del.textContent = "×";
      del.title = "Delete layout";
      del.setAttribute("aria-label", `Delete layout ${label}`);
      del.addEventListener("click", (e) => {
        e.stopPropagation();
        deleteCustom(id);
      });
      wrap.append(btn, del);
      host.appendChild(wrap);
    });

    updateActiveIndicator(
      builtins.find((b) => b.id === active)?.label ||
        customs.find((c) => c.id === active)?.label ||
        localCustoms[active]?.label ||
        active
    );
  }

  function openModal() {
    const modal = $("workspaceLayoutsModal");
    modal?.classList.remove("hidden");
    fetchCatalog(true).then(() => renderSwitcher());
    setTimeout(() => $("workspaceNameInput")?.focus(), 50);
  }

  async function bootRestore() {
    try {
      const res = await fetch("/api/layouts/restore");
      const plan = await res.json();
      if (plan.should_restore && plan.snapshot) {
        applySnapshot(plan.snapshot, plan.label);
        prefsSet("activeLayout", plan.layout_id);
        prefsSet("activeWorkspace", plan.layout_id);
        renderSwitcher();
      }
    } catch {
      /* ignore */
    }
  }

  async function maybeOfferProject() {
    try {
      const slug =
        document.querySelector("[data-active-project]")?.dataset?.activeProject ||
        window.AriaProjects?.activeSlug?.() ||
        "";
      const res = await fetch(`/api/layouts/suggest/project?slug=${encodeURIComponent(slug || "")}`);
      const data = await res.json();
      if (data.recommend && data.message) {
        window.showAriaToast?.(data.message + " (optional)", "info", 4500);
      }
    } catch {
      /* ignore */
    }
  }

  async function exportLayouts() {
    const res = await fetch("/api/layouts/export");
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "aria-layouts.json";
    a.click();
    URL.revokeObjectURL(a.href);
    window.showAriaToast?.("Layouts exported", "ok", 2000);
  }

  async function importLayouts(file) {
    const text = await file.text();
    const body = JSON.parse(text);
    const res = await fetch("/api/layouts/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    window.showAriaToast?.(data.ok ? `Imported ${data.imported || 0}` : data.error || "Import failed", data.ok ? "ok" : "err", 3000);
    await fetchCatalog(true);
    renderSwitcher();
  }

  function init() {
    $("workspaceLayoutsBtn")?.addEventListener("click", openModal);
    $("workspaceLayoutsCloseBtn")?.addEventListener("click", () => {
      $("workspaceLayoutsModal")?.classList.add("hidden");
    });
    $("workspaceSaveBtn")?.addEventListener("click", () => {
      saveCurrent($("workspaceNameInput")?.value);
    });
    $("workspaceNameInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        saveCurrent($("workspaceNameInput")?.value);
      }
    });
    $("layoutsUndoBtn")?.addEventListener("click", () => undoLayout());
    $("layoutsExportBtn")?.addEventListener("click", () => exportLayouts());
    $("layoutsImportBtn")?.addEventListener("click", () => $("layoutsImportFile")?.click());
    $("layoutsImportFile")?.addEventListener("change", (e) => {
      const f = e.target.files?.[0];
      if (f) importLayouts(f);
      e.target.value = "";
    });
    $("layoutsRestoreBootToggle")?.addEventListener("change", async (e) => {
      await fetch("/api/layouts/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ restore_on_boot: !!e.target.checked }),
      });
      window.showAriaToast?.(e.target.checked ? "Boot restore on" : "Boot restore off", "ok", 2000);
    });
    $("layoutsTypeahead")?.addEventListener("input", () => renderSwitcher());
    $("statusSegLayoutWrap")?.addEventListener("click", () => openModal());

    fetchCatalog(true).then((cat) => {
      renderSwitcher();
      const toggle = $("layoutsRestoreBootToggle");
      if (toggle && cat?.settings) toggle.checked = !!cat.settings.restore_on_boot;
      bootRestore();
    });
  }

  const api = {
    snapshot,
    applyLayout,
    applyPreset: (id) => applyLayout(id),
    applyCustom: (id) => applyLayout(id),
    saveCurrent,
    undoLayout,
    openModal,
    renderSwitcher,
    exportLayouts,
    importLayouts,
    fetchCatalog,
  };

  // Public names — Layouts is canonical; AriaWorkspaces kept for compatibility
  window.AriaLayouts = api;
  window.AriaWorkspaces = {
    ...api,
    PRESETS: {},
    openModal,
    applyPreset: (id) => applyLayout(id),
    applyCustom: (id) => applyLayout(id),
  };
  window.openLayouts = openModal;
  window.applyAriaLayout = applyLayout;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
