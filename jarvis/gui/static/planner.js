/** P0 planner, dashboard, checklist, confirm modal, system monitor */

function $(id) {
  return document.getElementById(id);
}

async function p0Fetch(url, opts = {}) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || res.statusText);
  return data;
}

function showToolConfirm(data) {
  const modal = $("toolConfirmModal");
  const msg = $("toolConfirmMessage");
  const title = $("toolConfirmTitle");
  if (!modal || !msg) return;
  const tool = data.tool || data.action || data.pending_action || "";
  if (title) title.textContent = tool ? `Confirm: ${tool}` : "Confirm action";
  msg.textContent = data.message || "Confirm this action?";
  modal.dataset.confirmId = data.confirm_id || "";
  modal.dataset.confirmTool = tool;
  modal.classList.remove("hidden");
  window.showAriaToast?.(`Approval needed: ${tool || "action"}`, "warn", 5000);
}

window.showToolConfirm = showToolConfirm;

async function resolveToolConfirm(approved) {
  const modal = $("toolConfirmModal");
  const id = modal?.dataset.confirmId;
  if (!id) {
    modal?.classList.add("hidden");
    return;
  }
  try {
    const data = await p0Fetch("/api/tool-confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, approved }),
    });
    const tool = modal?.dataset.confirmTool || "action";
    if (approved) {
      window.showAriaToast?.(`Approved: ${tool}`, "ok", 3200);
    } else {
      window.showAriaToast?.(`Denied: ${tool}`, "info", 2800);
    }
    if (data.result?.message) {
      window.addMessage?.("assistant", data.result.message, { type: data.result.type || "info" });
    } else if (data.message) {
      window.addMessage?.("assistant", data.message, { type: "info" });
    }
  } catch (e) {
    window.showAriaToast?.(`Confirm failed: ${e.message}`, "err");
    window.addMessage?.("assistant", `Confirm failed: ${e.message}`, { type: "info" });
  }
  modal.classList.add("hidden");
}

function renderPlanner(data) {
  const tasksEl = $("plannerTasks");
  const timersEl = $("plannerTimers");
  const alarmsEl = $("plannerAlarms");
  const eventsEl = $("plannerEvents");
  if (!tasksEl) return;
  const tasks = data.tasks || [];
  tasksEl.innerHTML = "";
  if (!tasks.length) {
    tasksEl.innerHTML = "<li class='muted'>No tasks yet</li>";
  }
  tasks.forEach((t) => {
    const li = document.createElement("li");
    li.textContent = t.text;
    const btn = document.createElement("button");
    btn.className = "ghost-btn small";
    btn.textContent = "Done";
    btn.onclick = async () => {
      try {
        await p0Fetch(`/api/planner/tasks/${encodeURIComponent(t.id)}/complete`, { method: "POST" });
        loadPlanner();
      } catch (e) {
        window.showAriaToast?.(`Task update failed: ${e.message}`, "err");
      }
    };
    li.appendChild(btn);
    tasksEl.appendChild(li);
  });
  const fmtTimer = (t) => {
    const rem = t.remaining_seconds || 0;
    const m = Math.floor(rem / 60);
    const s = rem % 60;
    return `${t.label || "timer"} — ${m}m ${s}s`;
  };
  timersEl.innerHTML = (data.timers || []).map((t) => `<li>${fmtTimer(t)}</li>`).join("") || "<li class='muted'>No active timers</li>";
  alarmsEl.innerHTML = (data.alarms || []).map((a) => `<li>${a.label || "alarm"} @ ${(a.fire_at || "").slice(11, 16)}</li>`).join("") || "<li class='muted'>No alarms</li>";
  eventsEl.innerHTML = (data.events_today || []).map((e) => `<li>${(e.start_time || "").slice(11, 16)} ${e.title}</li>`).join("") || "<li class='muted'>No events today</li>";
}

async function loadPlanner() {
  try {
    const data = await p0Fetch("/api/planner");
    renderPlanner(data);
  } catch (e) {
    $("plannerStatus") && ($("plannerStatus").textContent = e.message);
  }
}

let _dashClockTimer = null;

function stopDashboardClock() {
  if (_dashClockTimer) {
    clearInterval(_dashClockTimer);
    _dashClockTimer = null;
  }
}

function startDashboardClock() {
  stopDashboardClock();
  const tick = () => {
    const clock = document.getElementById("dashLiveClock");
    const dateEl = $("dashboardDate");
    const now = new Date();
    if (clock) {
      clock.textContent = now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    }
    if (dateEl) {
      dateEl.textContent = now.toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" });
    }
  };
  tick();
  _dashClockTimer = setInterval(tick, 1000);
}

function renderWeatherBubble(weather, esc) {
  if (weather.summary) {
    const hi = weather.high != null ? Math.round(Number(weather.high)) : null;
    const lo = weather.low != null ? Math.round(Number(weather.low)) : null;
    const sym = esc(weather.unit || "°");
    const tempLine =
      hi != null && lo != null ? `${hi}${sym} · L ${lo}${sym}` : esc(weather.summary);
    const loc = weather.location ? `<span class="muted">${esc(weather.location)}</span>` : "";
    return `<div class="dash-bubble dash-weather">
      <span class="dash-bubble-icon">${esc(weather.icon || "🌡️")}</span>
      <strong>${tempLine}</strong>
      <span>${esc(weather.condition || "")}</span>
      ${loc}
    </div>`;
  }
  const hint = weather.hint || weather.error || "Weather unavailable";
  return `<div class="dash-bubble dash-weather muted">
    <span class="dash-bubble-icon">🌡️</span>
    <span>${esc(hint)}</span>
  </div>`;
}

async function loadDashboard() {
  try {
    const data = await p0Fetch("/api/system-info");
    const welcome = $("dashboardWelcome");
    const greet = $("dashboardGreeting");
    const dateEl = $("dashboardDate");
    if (welcome) welcome.textContent = data.welcome || "Welcome back";
    if (greet) greet.textContent = data.greeting_short || data.greeting || "Dashboard";
    if (dateEl) dateEl.textContent = data.date_label || data.date || "";
    const body = $("dashboardBody");
    if (!body) return;

    const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
    const planner = data.planner || {};
    const tasks = planner.tasks || [];
    const activeTasks = tasks.filter((t) => !t.completed);
    const events = planner.events_today || [];
    const weather = data.weather || {};
    const kasa = data.kasa || {};
    const intel = data.intelligence || {};
    const news = data.news || {};

    const weatherHtml = renderWeatherBubble(weather, esc);
    const timeHtml = `<div class="dash-bubble dash-time"><strong id="dashLiveClock">${esc(data.time_display || data.time || "")}</strong><span class="muted">Local time</span></div>`;

    const statCards = [
      { label: "Tasks", count: activeTasks.length, view: "planner" },
      { label: "Today", count: events.length, view: "planner" },
      { label: "Kasa", count: kasa.count || 0, view: null },
      { label: "Headlines", count: (news.headlines || []).length, view: null },
    ];

    let presetsHtml = "";
    try {
      const pr = await p0Fetch("/api/scenes/presets");
      presetsHtml = (pr.presets || [])
        .slice(0, 6)
        .map(
          (p) =>
            `<button type="button" class="ghost-btn small dash-scene-btn" data-preset="${esc(p.id)}">${esc(p.label || p.id)}</button>`
        )
        .join("");
    } catch (_) {
      presetsHtml = "";
    }

    const breaking = news.breaking || (news.headlines || [])[0];
    const breakingTitle = breaking?.title || "Click Refresh briefing for headlines";

    body.innerHTML = `
      <div class="dash-header-row">${timeHtml}${weatherHtml}</div>
      <div class="dash-stat-grid">
        ${statCards
          .map(
            (c) =>
              `<button type="button" class="dash-stat-card" data-view="${esc(c.view || "")}"><span class="dash-stat-num">${c.count}</span><span class="dash-stat-label">${esc(c.label)}</span></button>`
          )
          .join("")}
      </div>
      <section class="dash-scenes">
        <h3>Home scenes</h3>
        <p class="muted">Focus, Relax, movie mode — from scene_presets.json</p>
        <div class="dash-scene-btns">${presetsHtml || '<span class="muted">No presets</span>'}</div>
      </section>
      <section class="dash-intel">
        <div class="dash-intel-head"><h3>System intelligence</h3><span class="dash-live-tag">Live</span></div>
        <div class="dash-intel-item"><strong>Daily focus</strong><p>${esc(intel.daily_focus)}</p></div>
        <div class="dash-intel-item"><strong>Intel alert</strong><p>${esc(intel.intel_alert)}</p></div>
        <div class="dash-intel-item"><strong>Smart home</strong><p>${esc(intel.smart_home)}</p></div>
        <div class="dash-priority-card"><strong>Up next</strong><p>${esc(intel.priority)}</p></div>
      </section>
      <section class="dash-briefing">
        <div class="dash-breaking"><span class="dash-breaking-tag">BREAKING</span> ${esc(breakingTitle)}</div>
        <div class="dash-news-cats" id="dashNewsCats"></div>
        <ul id="dashNewsList" class="dash-news-list"></ul>
        <button type="button" id="dashNewsRefresh" class="ghost-btn small">Refresh briefing</button>
      </section>
    `;

    body.querySelectorAll(".dash-stat-card[data-view]").forEach((btn) => {
      const v = btn.dataset.view;
      if (!v) return;
      btn.addEventListener("click", () => {
        document.querySelector(`.view-tab[data-view="${v}"]`)?.click();
      });
    });

    body.querySelectorAll(".dash-scene-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          const r = await p0Fetch(`/api/scenes/presets/${encodeURIComponent(btn.dataset.preset)}/activate`, {
            method: "POST",
          });
          window.showAriaToast?.(r.message || "Scene activated", r.ok ? "ok" : "warn");
        } catch (e) {
          window.showAriaToast?.(e.message, "err");
        } finally {
          btn.disabled = false;
        }
      });
    });

    const cats = news.categories || ["Top Stories", "Technology", "Markets", "Science", "Culture"];
    const catWrap = $("dashNewsCats");
    if (catWrap) {
      catWrap.innerHTML = cats
        .map((c, i) => `<button type="button" class="ghost-btn tiny dash-cat-btn${i === 0 ? " active" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`)
        .join("");
      const loadCat = async (cat) => {
        const list = $("dashNewsList");
        if (list) list.innerHTML = "<li class='muted'>Loading…</li>";
        const nr = await p0Fetch(`/api/curated-news?use_ai=true&category=${encodeURIComponent(cat)}`).catch(() => ({}));
        if (list) {
          list.innerHTML = (nr.headlines || [])
            .map((h) => `<li><strong>${esc(h.title)}</strong> <span class="muted">_${esc(h.category || cat)}_</span></li>`)
            .join("") || "<li class='muted'>No stories</li>";
        }
      };
      catWrap.querySelectorAll(".dash-cat-btn").forEach((b) => {
        b.addEventListener("click", () => {
          catWrap.querySelectorAll(".dash-cat-btn").forEach((x) => x.classList.remove("active"));
          b.classList.add("active");
          loadCat(b.dataset.cat);
        });
      });
      loadCat(cats[0]);
    }

    $("dashNewsRefresh")?.addEventListener("click", () => loadDashboard());
    startDashboardClock();
  } catch (e) {
    $("dashboardBody") && ($("dashboardBody").textContent = e.message);
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
    const data = await p0Fetch(url);
    const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;");
    el.innerHTML = (data.checks || []).map((c) => {
      const opt = c.optional ? " optional" : "";
      const cls = c.ok ? "ok" : c.optional ? "warn" : "fail";
      const mark = c.ok ? "✓" : c.optional ? "○" : "✗";
      return `<li class="${cls}${opt}">${mark} ${esc(c.name)}${c.detail ? ` — ${esc(c.detail)}` : ""}</li>`;
    }).join("") || "<li class='muted'>No checks returned</li>";
    const ms = data.elapsed_ms ?? Math.round(performance.now() - t0);
    if (summary) {
      const reqPass = data.passed_required ?? data.passed ?? 0;
      const reqTotal = data.total_required ?? data.total ?? 0;
      const optNote =
        data.total != null && data.total_required != null && data.total > data.total_required
          ? ` (${data.passed}/${data.total} incl. optional)`
          : "";
      summary.textContent = `${reqPass}/${reqTotal} required passed${optNote} · ${ms}ms`;
    }
  } catch (e) {
    el.innerHTML = `<li class="fail">✗ ${String(e.message || e).replace(/</g, "&lt;")}</li>`;
    if (summary) summary.textContent = "Check failed";
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = prevLabel;
    }
  }
}

window.loadChecklist = loadChecklist;

let monitorTimer = null;
function startSystemMonitor() {
  const el = $("systemMonitorStrip");
  if (!el) return;
  const tick = async () => {
    try {
      const s = await p0Fetch("/api/monitor");
      const gpu = s.gpu || {};
      const ram = s.ram || {};
      const models = (s.ollama_models || []).map((m) => m.name || m.model).filter(Boolean);
      const vramFree = gpu.free_vram_mb;
      const vramLabel = typeof vramFree === "number"
        ? `${vramFree}MB free`
        : gpu.vram_mb
          ? `${gpu.vram_mb}MB total`
          : "?";
      el.textContent = `CPU ${Math.round(s.cpu_percent || 0)}% · RAM ${Math.round(ram.percent || 0)}% · VRAM ${vramLabel}${models.length ? ` · Ollama: ${models.join(", ")}` : ""}`;
    } catch (_) {
      el.textContent = "";
    }
  };
  tick();
  if (monitorTimer) clearInterval(monitorTimer);
  monitorTimer = setInterval(tick, 5000);
}

function showListeningOverlay(show) {
  const el = $("listeningOverlay");
  if (!el) return;
  el.classList.toggle("hidden", !show);
  if (!show) {
    const partial = $("listeningPartial");
    if (partial) partial.textContent = "";
  }
  if (window.setVoiceBarState) window.setVoiceBarState(show ? "listening" : "idle");
}

window.initPlanner = function initPlanner() {
  loadPlanner();
  const root = $("plannerView");
  if (root?.dataset.bound === "1") return;
  if (root) root.dataset.bound = "1";
  $("plannerAddTaskBtn")?.addEventListener("click", async () => {
    const text = $("plannerTaskInput")?.value?.trim();
    if (!text) return;
    try {
      await p0Fetch("/api/planner/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      $("plannerTaskInput").value = "";
      loadPlanner();
    } catch (e) {
      window.showAriaToast?.(`Add task failed: ${e.message}`, "err");
    }
  });
  $("plannerTimerBtn")?.addEventListener("click", async () => {
    const duration = $("plannerTimerInput")?.value?.trim();
    if (!duration) return;
    try {
      await p0Fetch("/api/planner/timers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duration }),
      });
      loadPlanner();
    } catch (e) {
      window.showAriaToast?.(`Timer failed: ${e.message}`, "err");
    }
  });
  $("plannerPomodoroBtn")?.addEventListener("click", async () => {
    try {
      await p0Fetch("/api/planner/timers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duration: "25 minutes", label: "Pomodoro" }),
      });
      if ($("plannerTimerInput")) $("plannerTimerInput").value = "25 minutes";
      loadPlanner();
      window.showAriaToast?.("Pomodoro 25 min started", "ok");
    } catch (e) {
      window.showAriaToast?.(`Pomodoro failed: ${e.message}`, "err");
    }
  });
  $("plannerAlarmBtn")?.addEventListener("click", async () => {
    const time = $("plannerAlarmInput")?.value?.trim();
    if (!time) return;
    try {
      await p0Fetch("/api/planner/alarms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ time }),
      });
      loadPlanner();
    } catch (e) {
      window.showAriaToast?.(`Alarm failed: ${e.message}`, "err");
    }
  });
};

window.initDashboard = function initDashboard() {
  loadDashboard();
  loadChecklist();
  loadSkillsWorkflows();
};

async function loadSkillsWorkflows() {
  const skillsEl = $("skillsList");
  const workflowsEl = $("workflowsList");
  if (!skillsEl && !workflowsEl) return;
  try {
    const [skillsData, wfData] = await Promise.all([
      p0Fetch("/api/skills"),
      p0Fetch("/api/workflows"),
    ]);
    if (skillsEl) {
      const skills = skillsData.skills || [];
      skillsEl.innerHTML = skills.length
        ? skills
            .map(
              (s) =>
                `<li><strong>${s.name || s.slug}</strong> <span class="muted">${s.description || ""}</span></li>`
            )
            .join("")
        : "<li class='muted'>No skills installed</li>";
    }
    if (workflowsEl) {
      const workflows = wfData.workflows || [];
      workflowsEl.innerHTML = workflows.length
        ? workflows
            .map(
              (w) =>
                `<li><strong>${w.name || w.slug}</strong> <span class="muted">${w.count || 1}× · ${w.steps || 0} steps</span></li>`
            )
            .join("")
        : "<li class='muted'>No learned workflows yet</li>";
    }
  } catch (e) {
    if (skillsEl) skillsEl.innerHTML = `<li class='muted'>${e.message}</li>`;
    window.showAriaToast?.(`Skills/workflows: ${e.message}`, "err");
  }
}

async function scanWorkflowsFromActionLog() {
  try {
    const data = await p0Fetch("/api/workflows/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ min_repeats: 2 }),
    });
    const n = data.count ?? (data.workflows || []).length;
    window.showAriaToast?.(n ? `Found ${n} workflow pattern(s)` : "No repeated sequences yet", n ? "ok" : "info");
    await loadSkillsWorkflows();
  } catch (e) {
    window.showAriaToast?.(`Scan failed: ${e.message}`, "err");
  }
}

window.showListeningOverlay = showListeningOverlay;
window.jarvisStopSpeaking = async function () {
  try {
    await fetch("/api/audio/stop", { method: "POST" });
  } catch (_) {}
};

document.addEventListener("DOMContentLoaded", () => {
  $("toolConfirmYes")?.addEventListener("click", () => resolveToolConfirm(true));
  $("toolConfirmNo")?.addEventListener("click", () => resolveToolConfirm(false));
  $("checklistRunBtn")?.addEventListener("click", () => loadChecklist(true));
  $("skillsWorkflowsRefreshBtn")?.addEventListener("click", () => loadSkillsWorkflows());
  $("workflowsScanBtn")?.addEventListener("click", () => scanWorkflowsFromActionLog());
  $("audioStopBtn")?.addEventListener("click", () => window.jarvisStopSpeaking());
  startSystemMonitor();
  if (window.initProjects) window.initProjects();
});
