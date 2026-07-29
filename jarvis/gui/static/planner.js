/** P0 planner, confirm modal, system monitor — Home lives in dashboard_home.js */

function $(id) {
  return document.getElementById(id);
}

async function p0Fetch(url, opts = {}) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) throw new Error(data.message || data.error || res.statusText || "Request failed");
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
    tasksEl.innerHTML =
      "<li class='muted'>No tasks yet. <button type='button' class='ghost-btn tiny' id='plannerEmptyAddBtn'>Add task</button> or ask in <button type='button' class='ghost-btn tiny' id='plannerEmptyChatBtn'>Chat</button></li>";
    tasksEl.querySelector("#plannerEmptyAddBtn")?.addEventListener("click", () => {
      $("plannerTaskInput")?.focus();
    });
    tasksEl.querySelector("#plannerEmptyChatBtn")?.addEventListener("click", () => {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.("Add a planner task: ");
    });
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
  timersEl.innerHTML = (data.timers || []).map((t) => `<li>${fmtTimer(t)}</li>`).join("")
    || "<li class='muted'>No active timers. <button type='button' class='ghost-btn tiny' id='plannerEmptyPomoBtn'>Start Pomodoro</button></li>";
  timersEl.querySelector("#plannerEmptyPomoBtn")?.addEventListener("click", () => $("plannerPomodoroBtn")?.click());
  alarmsEl.innerHTML = (data.alarms || []).map((a) => `<li>${a.label || "alarm"} @ ${(a.fire_at || "").slice(11, 16)}</li>`).join("")
    || "<li class='muted'>No alarms. <button type='button' class='ghost-btn tiny' id='plannerEmptyAlarmBtn'>Add alarm</button></li>";
  alarmsEl.querySelector("#plannerEmptyAlarmBtn")?.addEventListener("click", () => {
    $("plannerAlarmInput")?.focus();
    window.showAriaToast?.("Set a time and click Add alarm", "info", 3000);
  });
  const events = data.events_today || [];
  if (!events.length) {
    eventsEl.innerHTML =
      "<li class='muted'>No events today. <button type='button' class='ghost-btn tiny' id='plannerEmptyCalBtn'>Open Calendar</button></li>";
    eventsEl.querySelector("#plannerEmptyCalBtn")?.addEventListener("click", () => {
      window.switchToView?.("calendar");
    });
  } else {
    eventsEl.innerHTML = events
      .map((e) => `<li>${(e.start_time || "").slice(11, 16)} ${e.title}</li>`)
      .join("");
  }
}

async function loadPlanner() {
  try {
    const data = await p0Fetch("/api/planner");
    renderPlanner(data);
  } catch (e) {
    if ($("plannerStatus")) $("plannerStatus").textContent = e.message;
    window.showAriaToast?.(e.message || "Planner load failed", "err", 5000);
  }
}


/* —— Home / Dashboard extracted to dashboard_home.js (Dashboard product) —— */

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
  monitorTimer = setInterval(() => {
    if (document.hidden) return;
    tick();
  }, 5000);
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
  $("plannerOpenCalendarBtn")?.addEventListener("click", () => window.switchToView?.("calendar"));
  $("plannerOpenJournalBtn")?.addEventListener("click", () => window.switchToView?.("journal"));
  $("plannerOpenDocumentsBtn")?.addEventListener("click", () => window.switchToView?.("documents"));
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
      window.showAriaToast?.(`Timer: ${duration}`, "ok", 2500);
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
      window.showAriaToast?.(`Alarm set: ${time}`, "ok", 2500);
    } catch (e) {
      window.showAriaToast?.(`Alarm failed: ${e.message}`, "err");
    }
  });
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
      window.showAriaToast?.("Task added", "ok", 2000);
    } catch (e) {
      window.showAriaToast?.(`Add task failed: ${e.message}`, "err");
    }
  });
};


async function scanWorkflowsFromActionLog() {
  try {
    const data = await p0Fetch("/api/workflows/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ min_repeats: 2 }),
    });
    const n = data.count ?? (data.workflows || []).length;
    window.showAriaToast?.(n ? `Found ${n} workflow pattern(s)` : "No repeated sequences yet", n ? "ok" : "info");
    await window.loadSkillsWorkflows?.();
  } catch (e) {
    window.showAriaToast?.(`Scan failed: ${e.message}`, "err");
  }
}

window.showListeningOverlay = showListeningOverlay;
window.jarvisStopSpeaking = async function () {
  try {
    const res = await fetch("/api/audio/stop", { method: "POST" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      window.showAriaToast?.(data.message || `Stop failed (${res.status})`, "err", 4000);
    }
  } catch (e) {
    window.showAriaToast?.(e?.message || "Could not stop audio", "err", 4000);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  $("toolConfirmYes")?.addEventListener("click", () => resolveToolConfirm(true));
  $("toolConfirmNo")?.addEventListener("click", () => resolveToolConfirm(false));
  $("checklistRunBtn")?.addEventListener("click", () => window.loadChecklist?.(true));
  $("skillsWorkflowsRefreshBtn")?.addEventListener("click", () => window.loadSkillsWorkflows?.());
  $("workflowsScanBtn")?.addEventListener("click", () => scanWorkflowsFromActionLog());
  $("dashOpenAutomationBtn")?.addEventListener("click", () => window.switchToView?.("automation"));
  $("audioStopBtn")?.addEventListener("click", () => window.jarvisStopSpeaking());
  startSystemMonitor();
  if (window.initProjects) window.initProjects();
});
