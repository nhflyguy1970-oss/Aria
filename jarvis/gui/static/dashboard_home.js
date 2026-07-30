/** Dashboard Home — first-class Home product UI. Planner no longer owns this. */
(function () {
  "use strict";

  let _clockTimer = null;
  let _refreshTimer = null;
  let _lastHome = null;
  let _generatedAt = null;

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function stopDashboardClock() {
    if (_clockTimer) {
      clearInterval(_clockTimer);
      _clockTimer = null;
    }
  }

  function startDashboardClock() {
    stopDashboardClock();
    const tick = () => {
      const el = $("dashLiveClock");
      if (!el) return;
      const now = new Date();
      el.textContent = now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    };
    tick();
    _clockTimer = setInterval(tick, 1000);
  }

  function stopBackgroundRefresh() {
    if (_refreshTimer) {
      clearInterval(_refreshTimer);
      _refreshTimer = null;
    }
  }

  function startBackgroundRefresh() {
    stopBackgroundRefresh();
    _refreshTimer = setInterval(() => {
      if (document.hidden) return;
      if (document.body?.dataset?.activeView && document.body.dataset.activeView !== "dashboard") return;
      if ($("dashboardView")?.classList.contains("hidden")) return;
      loadDashboard({ quiet: true });
    }, 120000);
  }

  function updatedLabel(iso) {
    if (!iso) return "";
    try {
      const t = Date.parse(iso);
      if (!t) return "";
      const sec = Math.max(0, Math.round((Date.now() - t) / 1000));
      if (sec < 5) return "Updated just now";
      if (sec < 60) return `Updated ${sec}s ago`;
      const m = Math.round(sec / 60);
      return `Updated ${m}m ago`;
    } catch {
      return "";
    }
  }

  function widgetById(home, id) {
    return (home.widgets || []).find((w) => w.id === id) || null;
  }

  function renderCoachOrHide(w, escFn) {
    if (!w) return "";
    if (w.render === "hide") return "";
    if (w.render === "coach" || (w.empty && w.coach)) {
      return `<section class="dash-widget dash-coach" data-widget="${escFn(w.id)}" aria-label="${escFn(w.title)}">
        <h3>${escFn(w.title)}</h3>
        <p class="muted">${escFn(w.coach || w.reason || "Unavailable")}</p>
        ${(w.deep_links || [])
          .map(
            (d) =>
              `<button type="button" class="ghost-btn tiny dash-deeplink" data-view="${escFn(d.view || "")}" data-action="${escFn(d.action || "")}">${escFn(d.label || d.view || "Open")}</button>`
          )
          .join("")}
      </section>`;
    }
    return null; // caller renders show
  }

  function bindDeepLinks(root) {
    root.querySelectorAll(".dash-deeplink").forEach((btn) => {
      btn.addEventListener("click", () => {
        const view = btn.dataset.view;
        const action = btn.dataset.action;
        if (action === "ha_setup") {
          $("haSetupWizardBtn")?.click() || $("haSetupModal")?.classList.remove("hidden");
          return;
        }
        if (action === "briefing") {
          window.switchToView?.("chat");
          return;
        }
        if (view) window.switchToView?.(view);
      });
    });
  }

  function renderAttention(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const items = w.payload?.items || [];
    const rows = items.length
      ? items
          .map(
            (it) =>
              `<button type="button" class="dash-attention-item severity-${escFn(it.severity || "info")}" data-view="${escFn((it.deep_link || {}).view || "")}">
                <strong>${escFn(it.title)}</strong>
                <span class="muted">${escFn(it.detail || it.owner || "")}</span>
              </button>`
          )
          .join("")
      : `<p class="muted">${escFn(w.payload?.message || "Nothing urgent — you're clear.")}</p>`;
    return `<section class="dash-widget dash-attention" data-widget="attention" aria-label="Attention">
      <div class="dash-intel-head"><h3>Attention</h3><span class="dash-updated" id="dashUpdatedLabel"></span></div>
      <div class="dash-attention-list" role="list">${rows}</div>
    </section>`;
  }

  function renderDailyBrief(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const p = w.payload || {};
    const sections = (p.sections || [])
      .map((s) => `<div class="dash-intel-item"><strong>${escFn(s.title)}</strong><p>${escFn(s.body)}</p></div>`)
      .join("");
    return `<section class="dash-widget dash-briefing dash-daily-brief" data-widget="daily_brief" aria-label="Daily Brief">
      <div class="dash-intel-head"><h3>Daily Brief</h3><span class="muted tiny">Morning Briefing · indexed</span></div>
      <p class="dash-brief-salutation">${escFn(p.salutation || "")}</p>
      ${p.weather_line ? `<p class="muted">${escFn(p.weather_line)}</p>` : ""}
      ${sections}
      <pre class="dash-brief-md muted">${escFn((p.markdown || "").slice(0, 900))}</pre>
      <div class="dash-detail-actions">
        ${(p.deep_links || [])
          .map(
            (d) =>
              `<button type="button" class="ghost-btn tiny dash-deeplink" data-view="${escFn(d.view || "")}" data-action="${escFn(d.action || "")}">${escFn(d.label || "Open")}</button>`
          )
          .join("")}
      </div>
    </section>`;
  }

  function renderTimeWeather(w, home, escFn) {
    const weather = (w?.payload || {}).weather || home.weather || {};
    const time = home.greeting?.time_display || w?.payload?.time_display || "";
    let weatherHtml = "";
    if (w && w.render === "show" && (weather.summary || weather.condition)) {
      const hi = weather.high != null ? Math.round(Number(weather.high)) : null;
      const lo = weather.low != null ? Math.round(Number(weather.low)) : null;
      const sym = escFn(weather.unit || "°");
      const tempLine =
        hi != null && lo != null ? `${hi}${sym} · L ${lo}${sym}` : escFn(weather.summary || weather.condition);
      weatherHtml = `<div class="dash-bubble dash-weather" aria-label="Weather">
        <strong>${tempLine}</strong>
        <span>${escFn(weather.condition || "")}</span>
        ${weather.location ? `<span class="muted">${escFn(weather.location)}</span>` : ""}
      </div>`;
    } else if (w?.coach) {
      weatherHtml = `<div class="dash-bubble dash-weather muted" aria-label="Weather unavailable"><span>${escFn(w.coach)}</span></div>`;
    }
    return `<div class="dash-header-row" data-widget="time_weather">
      <div class="dash-bubble dash-time"><strong id="dashLiveClock">${escFn(time)}</strong><span class="muted">Local time</span></div>
      ${weatherHtml}
    </div>`;
  }

  function renderGlance(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const p = w.payload || {};
    const cards = [
      { label: "Tasks", count: p.active_tasks || 0, view: "planner" },
      { label: "Events", count: p.events_today || 0, view: "planner" },
      { label: "Calendar", count: null, view: "calendar" },
      { label: "Journal", count: null, view: "journal" },
    ];
    return `<div class="dash-widget dash-stat-grid" data-widget="today_glance" role="group" aria-label="Today at a glance">
      ${cards
        .map(
          (c) =>
            `<button type="button" class="dash-stat-card" data-view="${escFn(c.view)}">
              <span class="dash-stat-num">${c.count != null ? c.count : "→"}</span>
              <span class="dash-stat-label">${escFn(c.label)}</span>
            </button>`
        )
        .join("")}
    </div>`;
  }

  function renderHealth(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const p = w.payload || {};
    const models = (p.models || p.ollama_models || []).filter(Boolean).slice(0, 4).join(", ");
    const status = p.status || "unknown";
    const score = p.health_score != null ? Math.round(p.health_score) : null;
    const recovery = p.recovery_active ? " · recovering" : "";
    const lastErr = p.last_error ? ` · last: ${escFn(String(p.last_error).slice(0, 48))}` : "";
    return `<section class="dash-widget dash-health" data-widget="provider_health" aria-label="Provider health">
      <h3>Provider health</h3>
      <p id="dashHealthLine">${escFn(status)}${score != null ? ` · score ${escFn(score)}` : ""} · ${escFn(p.provider || "provider")}${p.model ? ` · ${escFn(p.model)}` : ""}${recovery}</p>
      <p class="muted tiny">CPU ${escFn(Math.round(p.cpu_percent || 0))}% · RAM ${escFn(Math.round(p.ram_percent || 0))}%${models ? ` · ${escFn(models)}` : ""}${lastErr}</p>
      <button type="button" class="ghost-btn tiny dash-deeplink" data-view="workstation">Open Mission Control</button>
      <button type="button" class="ghost-btn tiny" id="dashProviderDiagBtn">Diagnostics</button>
      <p class="muted tiny">Summary only — Provider Health owns reliability; Mission Control is operational.</p>
    </section>`;
  }

  function renderScenes(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const presets = w.payload?.presets || [];
    const btns = presets
      .map(
        (p) =>
          `<button type="button" class="ghost-btn small dash-scene-btn" data-preset="${escFn(p.id)}">${escFn(p.label || p.id)}</button>`
      )
      .join("");
    return `<section class="dash-widget dash-scenes" data-widget="scenes" aria-label="Home scenes">
      <h3>Home scenes</h3>
      <p class="muted">Smart Home owns devices — Home only activates presets.</p>
      <div class="dash-scene-btns">${btns}</div>
    </section>`;
  }

  function renderNews(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const p = w.payload || {};
    const breaking = p.breaking?.title || (p.headlines || [])[0]?.title || "";
    const cats = p.categories || ["Top Stories", "Technology", "Markets", "Science", "Culture"];
    return `<section class="dash-widget dash-briefing" data-widget="news" aria-label="News">
      <div class="dash-breaking"><span class="dash-breaking-tag">NEWS</span> ${escFn(breaking || "Headlines")}</div>
      <div class="dash-news-cats" id="dashNewsCats" role="tablist">
        ${cats
          .map(
            (c, i) =>
              `<button type="button" class="ghost-btn tiny dash-cat-btn${i === 0 ? " active" : ""}" data-cat="${escFn(c)}" role="tab">${escFn(c)}</button>`
          )
          .join("")}
      </div>
      <ul id="dashNewsList" class="dash-news-list" aria-live="polite">
        ${(p.headlines || [])
          .map((h) => `<li><strong>${escFn(h.title)}</strong> <span class="muted">${escFn(h.category || "")}</span></li>`)
          .join("")}
      </ul>
      <button type="button" id="dashNewsRefresh" class="ghost-btn small">Refresh Home</button>
    </section>`;
  }

  function renderSuggestions(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const chips = w.payload?.suggestions || [];
    return `<section class="dash-widget dash-ai-suggest" data-widget="suggestions" id="dashAiSuggestSection" aria-label="Suggestions">
      <h3>Try asking Aria</h3>
      <div id="dashAiSuggestChips" class="dash-ai-chips">
        ${chips
          .map((s) => `<button type="button" class="ghost-btn small dash-ai-chip" data-prompt="${escFn(s)}">${escFn(s)}</button>`)
          .join("")}
      </div>
    </section>`;
  }

  function renderSimpleProduct(w, escFn) {
    const coached = renderCoachOrHide(w, escFn);
    if (coached !== null) return coached;
    const p = w.payload || {};
    const items = p.items || [];
    const list = items
      .map((it) => `<li>${escFn(it.title || it.name || it.content || "")}</li>`)
      .join("");
    return `<section class="dash-widget" data-widget="${escFn(w.id)}" aria-label="${escFn(w.title)}">
      <h3>${escFn(w.title)}</h3>
      ${p.count != null ? `<p><strong>${escFn(p.count)}</strong> <span class="muted">items</span></p>` : ""}
      ${p.morning_prompt ? `<p>${escFn(p.morning_prompt)}</p>` : ""}
      ${p.open_tasks != null ? `<p class="muted">${escFn(p.open_tasks)} open journal tasks</p>` : ""}
      ${list ? `<ul class="dash-news-list">${list}</ul>` : ""}
      ${(w.deep_links || [])
        .map(
          (d) =>
            `<button type="button" class="ghost-btn tiny dash-deeplink" data-view="${escFn(d.view || "")}">${escFn(d.label || "Open")}</button>`
        )
        .join("")}
    </section>`;
  }

  function renderQuickLaunch(escFn) {
    return `<section class="dash-widget dash-quick-rail" id="dashQuickRail" data-widget="quick_launch" aria-label="Quick launch">
      <h3>Quick launch</h3>
      <div class="dash-quick-btns" id="dashFavoritesRow"></div>
      <div class="dash-recent-row" id="dashRecentRow"></div>
    </section>`;
  }

  function renderSearchShortcuts(w, escFn) {
    return `<section class="dash-widget" data-widget="search_shortcuts" aria-label="Search">
      <h3>Search</h3>
      <p class="muted">Federated find across Aria — Search owns retrieval.</p>
      <button type="button" class="ghost-btn small dash-deeplink" data-view="search">Open Search Home</button>
    </section>`;
  }

  function renderNotificationsSummary(w, escFn) {
    const p = w?.payload || {};
    const unread = p.unread ?? 0;
    const critical = p.critical ?? 0;
    return `<section class="dash-widget" data-widget="notifications_summary" aria-label="Notifications">
      <h3>Notifications</h3>
      <p><strong>${escFn(unread)}</strong> unread · <strong>${escFn(critical)}</strong> critical</p>
      <p class="muted tiny">${escFn(p.digest_summary || p.note || "What still needs your attention.")}</p>
      <button type="button" class="ghost-btn small" id="dashOpenNotifications">Open Notifications</button>
    </section>`;
  }

  function renderDiagnostics(w, escFn) {
    const p = w.payload || {};
    const fails = (p.widget_failures || []).length;
    return `<section class="dash-widget" data-widget="diagnostics" aria-label="Home diagnostics">
      <h3>Home diagnostics</h3>
      <p>Showing <strong>${escFn(p.widgets_showing)}</strong> / ${escFn(p.widget_count)} · ${escFn(p.latency_ms)}ms · failures ${escFn(fails)}</p>
      <p class="muted tiny" id="dashDiagUpdated">${escFn(p.updated_label || "")}</p>
      <button type="button" class="ghost-btn tiny" id="dashDiagRefresh">Refresh Home</button>
      <button type="button" class="ghost-btn tiny dash-deeplink" data-view="workstation">Mission Control</button>
    </section>`;
  }

  function fillFavorites(body) {
    const favRow = body.querySelector("#dashFavoritesRow");
    const labels = window.AriaFavorites?.VIEW_LABELS || {};
    const favs = window.AriaFavorites?.getFavorites?.() || [];
    if (favRow) {
      favRow.innerHTML = favs.length
        ? favs
            .map((v) => `<button type="button" class="ghost-btn small dash-fav-btn" data-view="${esc(v)}">${esc(labels[v] || v)}</button>`)
            .join("")
        : '<span class="muted">Pin views with ★ for one-click launch</span>';
      favRow.querySelectorAll(".dash-fav-btn").forEach((btn) => {
        btn.addEventListener("click", () => window.switchToView?.(btn.dataset.view));
      });
      const layoutsBtn = document.createElement("button");
      layoutsBtn.type = "button";
      layoutsBtn.className = "ghost-btn small";
      layoutsBtn.textContent = "Layouts";
      layoutsBtn.title = "Shell presentation profiles (Ctrl+Shift+L)";
      layoutsBtn.addEventListener("click", () => window.AriaLayouts?.openModal?.());
      favRow.appendChild(layoutsBtn);
    }
    const recentRow = body.querySelector("#dashRecentRow");
    const recent = (window.AriaUiPrefs?.get?.("recentViews") || []).filter((v) => !favs.includes(v)).slice(0, 6);
    if (recentRow && recent.length) {
      recentRow.innerHTML =
        `<span class="muted small">Recent:</span> ` +
        recent
          .map((v) => `<button type="button" class="ghost-btn tiny dash-recent-btn" data-view="${esc(v)}">${esc(labels[v] || v)}</button>`)
          .join("");
      recentRow.querySelectorAll(".dash-recent-btn").forEach((btn) => {
        btn.addEventListener("click", () => window.switchToView?.(btn.dataset.view));
      });
    }
  }

  async function loadDashboard(opts = {}) {
    const quiet = !!opts.quiet;
    const category = opts.category || "";
    try {
      const url = category
        ? `/api/dashboard/home?category=${encodeURIComponent(category)}&stale_ok=true`
        : "/api/dashboard/home?stale_ok=true";
      const res = await fetch(url, { cache: "no-store" });
      const data = await res.json();
      if (!res.ok || data.ok === false) throw new Error(data.error || data.message || "Home load failed");
      _lastHome = data;
      _generatedAt = data.generated_at;

      const welcome = $("dashboardWelcome");
      const greet = $("dashboardGreeting");
      const dateEl = $("dashboardDate");
      const g = data.greeting || {};
      if (welcome) welcome.textContent = g.welcome || data.welcome || "Welcome back";
      if (greet) greet.textContent = g.greeting || data.greeting_short || "Home";
      if (dateEl) dateEl.textContent = g.date_label || data.date_label || "";

      const body = $("dashboardBody");
      if (!body) return;

      const orderHint = (data.layout?.order || []).filter(Boolean);
      const hidden = new Set(data.layout?.hidden || []);
      const byId = Object.fromEntries((data.widgets || []).map((w) => [w.id, w]));

      const defaultOrder = [
        "attention",
        "notifications_summary",
        "daily_brief",
        "time_weather",
        "quick_launch",
        "provider_health",
        "today_glance",
        "calendar_summary",
        "journal_reminder",
        "memory_highlights",
        "projects",
        "scenes",
        "suggestions",
        "search_shortcuts",
        "news",
        "diagnostics",
      ];
      const order = (orderHint.length ? orderHint : defaultOrder).filter((id) => byId[id] || id === "quick_launch");
      defaultOrder.forEach((id) => {
        if (!order.includes(id)) order.push(id);
      });

      const parts = [];
      for (const id of order) {
        if (hidden.has(id)) continue;
        const w = byId[id];
        if (id === "time_weather") {
          parts.push(renderTimeWeather(w, data, esc));
          continue;
        }
        if (id === "quick_launch" || id === "resume") {
          if (id === "quick_launch") parts.push(renderQuickLaunch(esc));
          continue;
        }
        if (!w) continue;
        if (id === "attention") parts.push(renderAttention(w, esc));
        else if (id === "daily_brief") parts.push(renderDailyBrief(w, esc));
        else if (id === "provider_health") parts.push(renderHealth(w, esc));
        else if (id === "today_glance") parts.push(renderGlance(w, esc));
        else if (id === "scenes") parts.push(renderScenes(w, esc));
        else if (id === "news") parts.push(renderNews(w, esc));
        else if (id === "suggestions") parts.push(renderSuggestions(w, esc));
        else if (id === "search_shortcuts") parts.push(renderSearchShortcuts(w, esc));
        else if (id === "notifications_summary") parts.push(renderNotificationsSummary(w, esc));
        else if (id === "diagnostics") parts.push(renderDiagnostics(w, esc));
        else if (["calendar_summary", "journal_reminder", "memory_highlights", "projects"].includes(id))
          parts.push(renderSimpleProduct(w, esc));
      }

      parts.push(`<section class="dash-whats-new-link">
        <button type="button" class="ghost-btn small" id="dashWhatsNewBtn">What's New</button>
        <button type="button" class="ghost-btn small" id="dashCustomizeBtn" title="Choose and reorder Home cards">Customize…</button>
        <button type="button" class="ghost-btn small" id="dashHomeRefreshBtn">Refresh</button>
        <span class="muted tiny" id="dashUpdatedFooter">${esc(updatedLabel(data.generated_at))}</span>
      </section>`);

      body.innerHTML = parts.join("\n");
      body.dataset.density = data.layout?.density || "comfortable";

      const upd = body.querySelector("#dashUpdatedLabel") || body.querySelector("#dashUpdatedFooter");
      if (upd) upd.textContent = updatedLabel(data.generated_at);

      fillFavorites(body);
      bindDeepLinks(body);

      body.querySelector("#dashOpenNotifications")?.addEventListener("click", () => {
        window.openNotifications?.() || window.AriaActivity?.open?.();
      });
      body.querySelector("#dashWhatsNewBtn")?.addEventListener("click", () => window.openWhatsNew?.(true));
      body.querySelector("#dashCustomizeBtn")?.addEventListener("click", () => window.AriaDashboardWidgets?.openCustomize?.());
      body.querySelector("#dashHomeRefreshBtn")?.addEventListener("click", () => loadDashboard());
      body.querySelector("#dashDiagRefresh")?.addEventListener("click", () => loadDashboard());
      body.querySelector("#dashNewsRefresh")?.addEventListener("click", () => loadDashboard());
      body.querySelector("#dashProviderDiagBtn")?.addEventListener("click", () => {
        window.open("/api/provider/diagnostics", "_blank", "noopener");
      });

      body.querySelectorAll(".dash-stat-card[data-view], .dash-attention-item[data-view]").forEach((btn) => {
        const v = btn.dataset.view;
        if (!v) return;
        btn.addEventListener("click", () => window.switchToView?.(v));
      });

      body.querySelectorAll(".dash-scene-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          btn.disabled = true;
          try {
            const r = await fetch(`/api/scenes/presets/${encodeURIComponent(btn.dataset.preset)}/activate`, {
              method: "POST",
            });
            const j = await r.json().catch(() => ({}));
            window.showAriaToast?.(j.message || "Scene activated", j.ok !== false ? "ok" : "warn");
          } catch (e) {
            window.showAriaToast?.(e.message, "err");
          } finally {
            btn.disabled = false;
          }
        });
      });

      const catWrap = body.querySelector("#dashNewsCats");
      if (catWrap) {
        const loadCat = async (cat) => {
          const list = body.querySelector("#dashNewsList");
          if (list) list.innerHTML = "<li class='muted'>Loading…</li>";
          try {
            const nr = await fetch(`/api/curated-news?use_ai=true&category=${encodeURIComponent(cat)}`).then((r) =>
              r.json()
            );
            if (list) {
              list.innerHTML =
                (nr.headlines || [])
                  .map(
                    (h) =>
                      `<li><strong>${esc(h.title)}</strong> <span class="muted">${esc(h.category || cat)}</span></li>`
                  )
                  .join("") ||
                "<li class='empty-state'><p class='empty-state-title'>No stories yet</p><p class='muted'>Ask Aria for a news briefing when providers are ready.</p></li>";
            }
          } catch (err) {
            if (list) list.innerHTML = `<li class='fail'>${esc(err.message || "News unavailable")}</li>`;
            if (!quiet) window.showAriaToast?.(err.message || "News failed", "err", 4000);
          }
        };
        catWrap.querySelectorAll(".dash-cat-btn").forEach((b) => {
          b.addEventListener("click", () => {
            catWrap.querySelectorAll(".dash-cat-btn").forEach((x) => x.classList.remove("active"));
            b.classList.add("active");
            loadCat(b.dataset.cat);
          });
        });
      }

      body.querySelectorAll(".dash-ai-chip").forEach((btn) => {
        btn.addEventListener("click", () => {
          const prompt = btn.dataset.prompt || "";
          window.switchToView?.("chat");
          setTimeout(() => {
            if (typeof window.jarvisSendToChat === "function") window.jarvisSendToChat(prompt);
            else {
              const input = $("messageInput");
              if (input) {
                input.value = prompt;
                input.focus();
              }
            }
          }, 80);
        });
      });

      window.AriaDashboardWidgets?.apply?.();
      window.AriaSmartWelcome?.injectIntoDashboard?.();
      startDashboardClock();
      startBackgroundRefresh();
      if (!quiet) {
        /* soft success only on manual refresh path via toast optional */
      }
    } catch (e) {
      const body = $("dashboardBody");
      if (body) {
        body.innerHTML = `<div class="empty-state" role="alert">
          <p class="empty-state-title">Home unavailable</p>
          <p class="muted">${esc(e.message || "Load failed")}</p>
          <button type="button" class="ghost-btn small" id="dashRetryBtn">Retry</button>
          <button type="button" class="ghost-btn small dash-deeplink" data-view="workstation">Mission Control</button>
        </div>`;
        body.querySelector("#dashRetryBtn")?.addEventListener("click", () => loadDashboard());
        bindDeepLinks(body);
      }
      if (!quiet) window.showAriaToast?.(e.message || "Home load failed", "err", 5000);
    }
  }

  async function loadChecklist(full = true) {
    const el = $("checklistResults");
    const btn = $("checklistRunBtn");
    const summary = $("checklistSummary");
    if (!el) return;
    const prevLabel = btn?.textContent || "Run checks";
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Running…";
    }
    el.innerHTML = "<li class='muted'>Running first-flight checks…</li>";
    if (summary) summary.textContent = "Running…";
    const t0 = performance.now();
    try {
      const url = full ? "/api/checklist?full=1" : "/api/checklist";
      const res = await fetch(url);
      const data = await res.json();
      el.innerHTML =
        (data.checks || [])
          .map((c) => {
            const opt = c.optional ? " optional" : "";
            const cls = c.ok ? "ok" : c.optional ? "warn" : "fail";
            const mark = c.ok ? "✓" : c.optional ? "○" : "✗";
            return `<li class="${cls}${opt}">${mark} ${esc(c.name)}${c.detail ? ` — ${esc(c.detail)}` : ""}</li>`;
          })
          .join("") ||
        "<li class='empty-state'><p class='empty-state-title'>No checks returned</p></li>";
      const ms = data.elapsed_ms ?? Math.round(performance.now() - t0);
      if (summary) {
        const reqPass = data.passed_required ?? data.passed ?? 0;
        const reqTotal = data.total_required ?? data.total ?? 0;
        summary.textContent = `${reqPass}/${reqTotal} required passed · ${ms}ms`;
      }
    } catch (e) {
      el.innerHTML = `<li class="fail">✗ ${esc(e.message || e)}</li>`;
      if (summary) summary.textContent = "Check failed";
      window.showAriaToast?.(e.message || "Checklist failed", "err", 5000);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = prevLabel;
      }
    }
  }

  async function loadSkillsWorkflows() {
    const skillsEl = $("skillsList");
    const workflowsEl = $("workflowsList");
    if (!skillsEl && !workflowsEl) return;
    try {
      const [skillsData, wfData] = await Promise.all([
        fetch("/api/skills").then((r) => r.json()),
        fetch("/api/workflows").then((r) => r.json()),
      ]);
      if (skillsEl) {
        const skills = skillsData.skills || [];
        skillsEl.innerHTML = skills.length
          ? skills
              .map(
                (s) =>
                  `<li class="auto-dash-row"><strong>${esc(s.name || s.slug)}</strong> <span class="muted">${esc(s.description || "")}</span></li>`
              )
              .join("")
          : '<li class="muted">No skills — open Automation Home.</li>';
      }
      if (workflowsEl) {
        const wfs = (wfData.workflows || []).filter((w) => w && (w.slug || w.name));
        workflowsEl.innerHTML = wfs.length
          ? wfs
              .map((w) => `<li class="auto-dash-row"><strong>${esc(w.name || w.slug)}</strong></li>`)
              .join("")
          : '<li class="muted">No learned workflows yet.</li>';
      }
    } catch (e) {
      if (skillsEl) skillsEl.innerHTML = `<li class="fail">${esc(e.message)}</li>`;
    }
  }

  function initDashboard() {
    loadDashboard();
    // Setup sections stay available but are not the daily Home focus
    const setupDone = window.AriaUiPrefs?.get?.("whatsNewSeen");
    if (!setupDone) {
      loadChecklist(false);
      loadSkillsWorkflows();
    } else {
      // Collapse visual weight: still allow manual run
      const summary = $("checklistSummary");
      if (summary && !summary.dataset.homeHint) {
        summary.dataset.homeHint = "1";
        summary.textContent = "First-flight checks available — run when validating a new install.";
      }
    }
    const root = $("dashboardView");
    if (root && root.dataset.dashCrossBound !== "1") {
      root.dataset.dashCrossBound = "1";
      $("dashboardOpenMcBtn")?.addEventListener("click", () => window.switchToView?.("workstation"));
      $("dashboardOpenPlannerBtn")?.addEventListener("click", () => window.switchToView?.("planner"));
      $("dashboardOpenJournalBtn")?.addEventListener("click", () => window.switchToView?.("journal"));
      $("dashboardOpenCalendarBtn")?.addEventListener("click", () => window.switchToView?.("calendar"));
      $("checklistRunBtn")?.addEventListener("click", () => loadChecklist(true));
      $("dashOpenAutomationBtn")?.addEventListener("click", () => window.switchToView?.("automation"));
      $("skillsWorkflowsRefreshBtn")?.addEventListener("click", () => loadSkillsWorkflows());
    }
  }

  function openHome(widget) {
    window.switchToView?.("dashboard");
    if (widget) {
      setTimeout(() => {
        const el = document.querySelector(`[data-widget="${widget}"]`);
        el?.scrollIntoView?.({ behavior: "smooth", block: "start" });
        el?.focus?.();
      }, 200);
    }
  }

  window.loadDashboard = loadDashboard;
  window.initDashboard = initDashboard;
  window.stopDashboardClock = function () {
    stopDashboardClock();
    stopBackgroundRefresh();
  };
  window.loadChecklist = loadChecklist;
  window.loadSkillsWorkflows = loadSkillsWorkflows;
  window.openDashboardHome = openHome;
  window.openHome = openHome;
  window._dashHomeOwned = true;
})();
