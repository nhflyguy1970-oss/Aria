/** Dashboard customization — hide/show + reorder Home widgets; layout remembered. */
(function () {
  "use strict";

  const WIDGETS = [
    { id: "attention", label: "Attention" },
    { id: "daily_brief", label: "Daily Brief" },
    { id: "time_weather", label: "Time & weather" },
    { id: "quick_launch", label: "Quick launch" },
    { id: "provider_health", label: "Provider health" },
    { id: "today_glance", label: "Today at a glance" },
    { id: "calendar_summary", label: "Calendar" },
    { id: "journal_reminder", label: "Journal" },
    { id: "memory_highlights", label: "Memory" },
    { id: "projects", label: "Projects" },
    { id: "scenes", label: "Home scenes" },
    { id: "suggestions", label: "Try asking Aria" },
    { id: "search_shortcuts", label: "Search" },
    { id: "news", label: "News" },
    { id: "diagnostics", label: "Home diagnostics" },
  ];

  function layout() {
    const saved = window.AriaUiPrefs?.get?.("dashboardLayout");
    if (saved && Array.isArray(saved.order)) return saved;
    return { order: WIDGETS.map((w) => w.id), hidden: ["news"] };
  }

  function saveLayout(next) {
    window.AriaUiPrefs?.set?.("dashboardLayout", next);
    // Mirror to Dashboard product layout API (non-blocking)
    fetch("/api/dashboard/layout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(next),
    }).catch(() => {});
  }

  function apply() {
    const body = document.getElementById("dashboardBody");
    if (!body) return;
    const lay = layout();
    const hiddenSet = new Set(lay.hidden || []);
    const headerRow = body.querySelector(".dash-header-row");
    lay.order.forEach((id) => {
      const el = body.querySelector(`[data-widget="${id}"]`);
      if (el) body.appendChild(el);
    });
    if (headerRow) body.prepend(headerRow);
    WIDGETS.forEach((w) => {
      const el = body.querySelector(`[data-widget="${w.id}"]`);
      if (el) el.classList.toggle("hidden", hiddenSet.has(w.id));
    });
    const wn = body.querySelector(".dash-whats-new-link");
    if (wn) body.appendChild(wn);
  }

  function openCustomize() {
    const modal = document.getElementById("dashCustomizeModal");
    const list = document.getElementById("dashCustomizeList");
    if (!modal || !list) return;
    const lay = layout();
    const hiddenSet = new Set(lay.hidden || []);
    const order = lay.order.filter((id) => WIDGETS.some((w) => w.id === id));
    WIDGETS.forEach((w) => {
      if (!order.includes(w.id)) order.push(w.id);
    });

    const renderRows = () => {
      list.replaceChildren();
      order.forEach((id, i) => {
        const w = WIDGETS.find((x) => x.id === id);
        if (!w) return;
        const row = document.createElement("div");
        row.className = "dash-customize-row";
        const label = document.createElement("label");
        label.className = "dash-customize-label";
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.checked = !hiddenSet.has(id);
        cb.addEventListener("change", () => {
          if (cb.checked) hiddenSet.delete(id);
          else hiddenSet.add(id);
        });
        label.append(cb, document.createTextNode(` ${w.label}`));
        const up = document.createElement("button");
        up.type = "button";
        up.className = "ghost-btn tiny";
        up.textContent = "↑";
        up.title = "Move up";
        up.setAttribute("aria-label", `Move ${w.label} up`);
        up.disabled = i === 0;
        up.addEventListener("click", () => {
          [order[i - 1], order[i]] = [order[i], order[i - 1]];
          renderRows();
        });
        const down = document.createElement("button");
        down.type = "button";
        down.className = "ghost-btn tiny";
        down.textContent = "↓";
        down.title = "Move down";
        down.setAttribute("aria-label", `Move ${w.label} down`);
        down.disabled = i === order.length - 1;
        down.addEventListener("click", () => {
          [order[i], order[i + 1]] = [order[i + 1], order[i]];
          renderRows();
        });
        row.append(label, up, down);
        list.appendChild(row);
      });
    };
    renderRows();
    modal.classList.remove("hidden");
    const saveBtn = document.getElementById("dashCustomizeSaveBtn");
    const resetBtn = document.getElementById("dashCustomizeResetBtn");
    const closeBtn = document.getElementById("dashCustomizeCloseBtn");
    const onSave = () => {
      saveLayout({ order: [...order], hidden: [...hiddenSet] });
      modal.classList.add("hidden");
      window.loadDashboard?.();
      saveBtn?.removeEventListener("click", onSave);
    };
    saveBtn?.addEventListener("click", onSave);
    closeBtn?.addEventListener("click", () => modal.classList.add("hidden"));
    resetBtn?.addEventListener("click", () => {
      order.splice(0, order.length, ...WIDGETS.map((w) => w.id));
      hiddenSet.clear();
      hiddenSet.add("news");
      renderRows();
    });
  }

  document.getElementById("dashCustomizeBtn")?.addEventListener("click", openCustomize);

  window.AriaDashboardWidgets = {
    WIDGETS,
    layout,
    saveLayout,
    apply,
    openCustomize,
  };
})();
