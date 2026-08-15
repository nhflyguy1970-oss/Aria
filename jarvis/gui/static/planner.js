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
  window.AriaPlannerLive?.setSnapshot?.(data);

  const esc = (s) =>
    String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");

  const tasks = data.tasks || [];
  tasksEl.innerHTML = "";
  if (!tasks.length) {
    tasksEl.innerHTML = `<li class="empty-state"><div class="empty-state-icon" aria-hidden="true">✓</div><p class="empty-state-title">No tasks yet</p><p class="muted">Planner is for today’s actionable work.</p><div class="empty-state-actions"><button type="button" class="apply-btn tiny" id="plannerEmptyAddBtn">Add task</button><button type="button" class="ghost-btn tiny" id="plannerEmptyChatBtn">Ask Chat</button><button type="button" class="ghost-btn tiny" id="plannerEmptyJournalBtn">Open Journal</button></div></li>`;
    tasksEl.querySelector("#plannerEmptyAddBtn")?.addEventListener("click", () => $("plannerTaskInput")?.focus());
    tasksEl.querySelector("#plannerEmptyChatBtn")?.addEventListener("click", () => {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.("Add a planner task: ");
    });
    tasksEl.querySelector("#plannerEmptyJournalBtn")?.addEventListener("click", () => window.switchToView?.("journal"));
  }
  tasks.forEach((t) => {
    const li = document.createElement("li");
    li.className = "planner-row";
    li.dataset.taskId = t.id;
    const due = t.due_date ? `<span class="muted planner-due">due ${(t.due_date || "").slice(0, 10)}</span>` : "";
    li.innerHTML = `<span class="planner-row-main">${esc(t.text)}</span>${due}`;
    const actions = document.createElement("div");
    actions.className = "planner-row-actions";
    const done = document.createElement("button");
    done.type = "button";
    done.className = "ghost-btn tiny";
    done.textContent = "Done";
    done.setAttribute("aria-label", `Complete ${t.text}`);
    done.onclick = async () => {
      try {
        const result = await window.ariaMutate({
          request: () => fetch(`/api/planner/tasks/${encodeURIComponent(t.id)}/complete`, { method: "POST" }),
          failToast: "Task update failed",
        });
        if (!result.ok) return;
        loadPlanner();
        window.AriaPlannerLive?.refreshFocus?.();
      } catch (e) {
        window.showAriaToast?.(`Task update failed: ${e.message}`, "err");
      }
    };
    const del = document.createElement("button");
    del.type = "button";
    del.className = "ghost-btn tiny";
    del.textContent = "Delete";
    del.setAttribute("aria-label", `Delete ${t.text}`);
    del.onclick = async () => {
      try {
        await p0Fetch(`/api/planner/tasks/${encodeURIComponent(t.id)}`, { method: "DELETE" });
        window.showAriaToast?.("Task deleted — Undo available", "info", 3500);
        loadPlanner();
        window.AriaPlannerLive?.refreshFocus?.();
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    };
    actions.append(done, del);
    li.appendChild(actions);
    li.addEventListener("contextmenu", (e) => {
      window.AriaContextMenu?.open(e, [
        { label: "Complete", run: () => done.click() },
        { label: "Delete", run: () => del.click() },
        { label: "Ask Aria about this", run: () => {
          window.jarvisAskAria?.(`Help me with planner task: ${t.text}`, {
            autoSend: true,
            returnView: "planner",
            context: [{ kind: "planner", id: String(t.id || t.text), label: String(t.text || "").slice(0, 40) }],
          });
        }},
      ]);
    });
    tasksEl.appendChild(li);
  });

  const fmtTimer = (t) => window.AriaPlannerLive?.fmtRemaining?.(t.remaining_seconds || 0) || `${t.remaining_seconds || 0}s`;
  timersEl.innerHTML = "";
  if (!(data.timers || []).length) {
    timersEl.innerHTML = `<li class="empty-state"><div class="empty-state-icon" aria-hidden="true">⏱</div><p class="empty-state-title">No active timers</p><div class="empty-state-actions"><button type="button" class="apply-btn tiny" id="plannerEmptyPomoBtn">Start Focus 25m</button></div></li>`;
    timersEl.querySelector("#plannerEmptyPomoBtn")?.addEventListener("click", () => $("plannerPomodoroBtn")?.click());
  }
  (data.timers || []).forEach((t) => {
    const li = document.createElement("li");
    li.className = "planner-row";
    li.dataset.timerEnds = t.ends_at || "";
    li.dataset.timerLabel = t.label || "timer";
    li.dataset.paused = t.paused ? "1" : "0";
    li.innerHTML = `<span class="planner-row-main">${esc(t.label || "timer")} — <span class="planner-timer-clock">${fmtTimer(t)}</span>${t.paused ? " (paused)" : ""}</span>`;
    const actions = document.createElement("div");
    actions.className = "planner-row-actions";
    const mk = (label, aria, fn) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "ghost-btn tiny";
      b.textContent = label;
      b.setAttribute("aria-label", aria);
      b.onclick = fn;
      return b;
    };
    actions.append(
      mk(t.paused ? "Resume" : "Pause", t.paused ? "Resume timer" : "Pause timer", async () => {
        try {
          await p0Fetch(`/api/planner/timers/${encodeURIComponent(t.id)}/${t.paused ? "resume" : "pause"}`, { method: "POST" });
          loadPlanner();
        } catch (e) {
          window.showAriaToast?.(e.message, "err");
        }
      }),
      mk("Dup", "Duplicate timer", async () => {
        try {
          await p0Fetch(`/api/planner/timers/${encodeURIComponent(t.id)}/duplicate`, { method: "POST" });
          loadPlanner();
        } catch (e) {
          window.showAriaToast?.(e.message, "err");
        }
      }),
      mk("Cancel", "Cancel timer", async () => {
        try {
          await p0Fetch(`/api/planner/timers/${encodeURIComponent(t.id)}/cancel`, { method: "POST" });
          window.showAriaToast?.("Timer cancelled — Undo available", "info", 3000);
          loadPlanner();
          window.AriaPlannerLive?.refreshFocus?.();
        } catch (e) {
          window.showAriaToast?.(e.message, "err");
        }
      }),
    );
    li.appendChild(actions);
    timersEl.appendChild(li);
  });

  alarmsEl.innerHTML = "";
  if (!(data.alarms || []).length) {
    alarmsEl.innerHTML = `<li class="empty-state"><div class="empty-state-icon" aria-hidden="true">⏰</div><p class="empty-state-title">No alarms</p><div class="empty-state-actions"><button type="button" class="ghost-btn tiny" id="plannerEmptyAlarmBtn">Add alarm</button></div></li>`;
    alarmsEl.querySelector("#plannerEmptyAlarmBtn")?.addEventListener("click", () => {
      $("plannerAlarmInput")?.focus();
      window.showAriaToast?.("Enter a time like 7am, then press Enter", "info", 3000);
    });
  }
  (data.alarms || []).forEach((a) => {
    const li = document.createElement("li");
    li.className = "planner-row";
    li.innerHTML = `<span class="planner-row-main">${esc(a.label || "alarm")} @ ${esc((a.fire_at || "").slice(11, 16))}</span>`;
    const actions = document.createElement("div");
    actions.className = "planner-row-actions";
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "ghost-btn tiny";
    edit.textContent = "Edit";
    edit.onclick = async () => {
      const time = window.ariaPrompt
        ? await window.ariaPrompt("New alarm time (e.g. 7:30am)", (a.fire_at || "").slice(11, 16), {
            title: "Edit alarm",
            okLabel: "Save",
          })
        : prompt("New alarm time (e.g. 7:30am)", (a.fire_at || "").slice(11, 16));
      if (!time) return;
      try {
        await p0Fetch(`/api/planner/alarms/${encodeURIComponent(a.id)}/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ time }),
        });
        loadPlanner();
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    };
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.className = "ghost-btn tiny";
    cancel.textContent = "Cancel";
    cancel.onclick = async () => {
      try {
        await p0Fetch(`/api/planner/alarms/${encodeURIComponent(a.id)}/cancel`, { method: "POST" });
        window.showAriaToast?.("Alarm cancelled — Undo available", "info", 3000);
        loadPlanner();
        window.AriaPlannerLive?.refreshFocus?.();
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    };
    actions.append(edit, cancel);
    li.appendChild(actions);
    alarmsEl.appendChild(li);
  });

  const events = data.events_today || [];
  eventsEl.innerHTML = "";
  if (!events.length) {
    eventsEl.innerHTML = `<li class="empty-state"><div class="empty-state-icon" aria-hidden="true">📅</div><p class="empty-state-title">No events today</p><p class="muted">Add a light event here, or open Calendar for commitments.</p><div class="empty-state-actions"><button type="button" class="apply-btn tiny" id="plannerEmptyEventBtn">Add event</button><button type="button" class="ghost-btn tiny" id="plannerEmptyCalBtn">Open Calendar</button></div></li>`;
    eventsEl.querySelector("#plannerEmptyEventBtn")?.addEventListener("click", () => $("plannerEventTitle")?.focus());
    eventsEl.querySelector("#plannerEmptyCalBtn")?.addEventListener("click", () => window.switchToView?.("calendar"));
  }
  events.forEach((e) => {
    const li = document.createElement("li");
    li.className = "planner-row";
    li.innerHTML = `<span class="planner-row-main">${esc((e.start_time || "").slice(11, 16))} ${esc(e.title)}</span>`;
    const actions = document.createElement("div");
    actions.className = "planner-row-actions";
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "ghost-btn tiny";
    edit.textContent = "Edit";
    edit.onclick = async () => {
      const title = window.ariaPrompt
        ? await window.ariaPrompt("Event title", e.title, { title: "Edit event", okLabel: "Save" })
        : prompt("Event title", e.title);
      if (title == null) return;
      const time = window.ariaPrompt
        ? await window.ariaPrompt("Time (e.g. 3pm)", (e.start_time || "").slice(11, 16), {
            title: "Edit event time",
            okLabel: "Save",
          })
        : prompt("Time (e.g. 3pm)", (e.start_time || "").slice(11, 16));
      try {
        await p0Fetch(`/api/planner/events/${encodeURIComponent(e.id)}/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, time: time || undefined }),
        });
        loadPlanner();
        window.AriaPlannerLive?.refreshFocus?.();
      } catch (err) {
        window.showAriaToast?.(err.message, "err");
      }
    };
    const del = document.createElement("button");
    del.type = "button";
    del.className = "ghost-btn tiny";
    del.textContent = "Delete";
    del.onclick = async () => {
      try {
        await p0Fetch(`/api/planner/events/${encodeURIComponent(e.id)}`, { method: "DELETE" });
        window.showAriaToast?.("Event deleted — Undo available", "info", 3000);
        loadPlanner();
        window.AriaPlannerLive?.refreshFocus?.();
      } catch (err) {
        window.showAriaToast?.(err.message, "err");
      }
    };
    const cal = document.createElement("button");
    cal.type = "button";
    cal.className = "ghost-btn tiny";
    cal.textContent = "Calendar";
    cal.onclick = () => window.switchToView?.("calendar");
    actions.append(edit, del, cal);
    li.appendChild(actions);
    eventsEl.appendChild(li);
  });

  window.AriaPlannerLive?.refreshFocus?.();
}

async function loadPlanner() {
  const status = $("plannerStatus");
  if (status) status.textContent = "Loading…";
  try {
    const data = await p0Fetch("/api/planner");
    renderPlanner(data);
    if (status) status.textContent = "";
    // Keep Calendar in agreement when Planner mutates (same commitments).
    try {
      window.refreshCalendar?.();
    } catch (_) { /* calendar may be unloaded */ }
  } catch (e) {
    if (window.AriaNet?.isRoomAbort?.(e) || e?.name === "AbortError" || /aborted|aria-room-leave/i.test(String(e?.message || ""))) {
      if (status) status.textContent = "";
      return;
    }
    if (status) status.textContent = e.message;
    window.showAriaToast?.(e.message || "Planner load failed — retry from the view", "err", 5000);
  }
}


/* —— Home / Dashboard extracted to dashboard_home.js (Dashboard product) —— */
/* Checklist + skills loaders live on window from dashboard_home.js. */

let monitorTimer = null;
function startSystemMonitor() {
  const el = $("systemMonitorStrip");
  if (!el) return;
  const tick = async () => {
    try {
      const s = await p0Fetch("/api/monitor");
      const gpu = s.gpu || {};
      const ram = s.ram || {};
      const sys = s.system || {};
      const sysRam = sys.ram || {};
      const models = (s.ollama_models || []).map((m) => m.name || m.model).filter(Boolean);
      const vramFree = gpu.free_vram_mb;
      const vramLabel = typeof vramFree === "number"
        ? `${vramFree}MB free`
        : gpu.vram_mb
          ? `${gpu.vram_mb}MB total`
          : "?";
      const ariaRss = ram.rss_mb || ram.used_mb;
      const ariaRam = typeof ariaRss === "number" ? `${ariaRss >= 1024 ? (ariaRss / 1024).toFixed(1) + "GB" : ariaRss + "MB"}` : "?";
      const sysCpu = sys.cpu_percent != null ? Math.round(sys.cpu_percent) : null;
      const sysRamPct = sysRam.percent != null ? Math.round(sysRam.percent) : null;
      const sysBit =
        sysCpu != null || sysRamPct != null
          ? ` · Host ${sysCpu != null ? sysCpu + "% CPU" : ""}${sysCpu != null && sysRamPct != null ? "/" : ""}${sysRamPct != null ? sysRamPct + "% RAM" : ""}`
          : "";
      el.textContent = `Aria ${Math.round(s.cpu_percent || 0)}% CPU · ${ariaRam}${sysBit} · VRAM ${vramLabel}${models.length ? ` · Ollama: ${models.join(", ")}` : ""}`;
      el.title = "Aria = this process. Host = whole machine.";
    } catch (_) {
      el.textContent = "";
    }
  };
  tick();
  if (monitorTimer) clearInterval(monitorTimer);
  monitorTimer = setInterval(() => {
    if (document.hidden) return;
    tick();
  }, 15000);
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

  const bindEnter = (inputId, btnId) => {
    $(inputId)?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        $(btnId)?.click();
      }
    });
  };

  $("plannerOpenCalendarBtn")?.addEventListener("click", () => window.switchToView?.("calendar"));
  $("plannerOpenJournalBtn")?.addEventListener("click", () => window.switchToView?.("journal"));
  $("plannerOpenDocumentsBtn")?.addEventListener("click", () => window.switchToView?.("documents"));
  $("plannerPromoteFromJournalBtn")?.addEventListener("click", () => {
    window.switchToView?.("chat");
    setTimeout(
      () =>
        window.jarvisSendToChat?.(
          "Promote an actionable Journal note into a Planner task for today. Ask me which note if unclear.",
        ),
      80,
    );
  });

  const haPref = $("plannerHaFocusPref");
  if (haPref) {
    fetch("/api/planner/prefs")
      .then((r) => r.json())
      .then((p) => {
        window._plannerPrefs = p;
        haPref.checked = !!p.ha_focus_enabled;
      })
      .catch(() => {});
    haPref.addEventListener("change", async () => {
      try {
        await p0Fetch("/api/planner/prefs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ha_focus_enabled: !!haPref.checked }),
        });
        window._plannerPrefs = { ...(window._plannerPrefs || {}), ha_focus_enabled: !!haPref.checked };
        window.showAriaToast?.(haPref.checked ? "HA Focus mode on" : "HA Focus mode off", "ok", 2000);
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    });
  }

  $("plannerTimerBtn")?.addEventListener("click", async () => {
    const duration = $("plannerTimerInput")?.value?.trim();
    if (!duration) {
      window.showAriaToast?.("Enter a duration like “10 minutes”", "warn", 2800);
      $("plannerTimerInput")?.focus();
      return;
    }
    try {
      await p0Fetch("/api/planner/timers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duration }),
      });
      $("plannerTimerInput").value = "";
      loadPlanner();
      window.AriaCollapsiblePanels?.expand?.("#plannerView", "Timers");
      window.showAriaToast?.(`Timer: ${duration}`, "ok", 2500);
    } catch (e) {
      window.showAriaToast?.(`Timer failed: ${e.message}`, "err");
    }
  });
  $("plannerPomodoroBtn")?.addEventListener("click", async () => {
    try {
      const useHa = !!$("plannerHaFocusPref")?.checked;
      const data = await p0Fetch("/api/planner/focus/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duration: "25 minutes", label: "Pomodoro", use_ha: useHa }),
      });
      if ($("plannerTimerInput")) $("plannerTimerInput").value = "25 minutes";
      loadPlanner();
      window.AriaPlannerLive?.refreshFocus?.();
      window.AriaCollapsiblePanels?.expand?.("#plannerView", "Timers");
      if (useHa && data.ha_ok === false) {
        const why = data.home_assistant?.message || (data.warnings || [])[0] || "HA Focus failed";
        window.showAriaToast?.(`Focus timer started — scene not activated: ${why}`, "warn", 6000);
      } else {
        window.showAriaToast?.("Focus 25m started", "ok");
      }
    } catch (e) {
      window.showAriaToast?.(`Focus failed: ${e.message}`, "err");
    }
  });
  $("plannerAlarmBtn")?.addEventListener("click", async () => {
    const time = $("plannerAlarmInput")?.value?.trim();
    if (!time) {
      window.showAriaToast?.("Enter a time like 7am", "warn", 2800);
      $("plannerAlarmInput")?.focus();
      return;
    }
    try {
      await p0Fetch("/api/planner/alarms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ time }),
      });
      $("plannerAlarmInput").value = "";
      loadPlanner();
      window.AriaCollapsiblePanels?.expand?.("#plannerView", "Alarms");
      window.showAriaToast?.(`Alarm set: ${time}`, "ok", 2500);
    } catch (e) {
      window.showAriaToast?.(`Alarm failed: ${e.message}`, "err");
    }
  });
  $("plannerAddTaskBtn")?.addEventListener("click", async () => {
    const input = $("plannerTaskInput");
    const text = input?.value?.trim();
    if (!text) {
      window.showAriaToast?.("Task text required", "warn", 2500);
      input?.focus();
      return;
    }
    const taskInSnapshot = (snap, created) => {
      const tasks = snap?.tasks || [];
      const id = created?.task?.id || created?.id;
      if (id && tasks.some((t) => t.id === id)) return true;
      return tasks.some((t) => String(t.text || "") === text);
    };
    let created = {};
    try {
      created = await p0Fetch("/api/planner/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
    } catch (e) {
      created = { error: e };
    }
    let snap = null;
    try {
      snap = await p0Fetch("/api/planner");
    } catch (e) {
      if (!window.AriaNet?.isRoomAbort?.(e)) {
        window.showAriaToast?.(created?.error?.message || "Add task failed", "err");
        return;
      }
    }
    if (!taskInSnapshot(snap, created)) {
      const msg =
        (created && created.error && created.error.message) ||
        (created && created.message) ||
        "Add task failed";
      window.showAriaToast?.(String(msg), "err");
      return;
    }
    if (input) input.value = "";
    loadPlanner();
    window.AriaPlannerLive?.refreshFocus?.();
    window.AriaCollapsiblePanels?.expand?.("#plannerView", "Tasks");
    window.showAriaToast?.("Task added", "ok", 3000);
  });
  $("plannerAddEventBtn")?.addEventListener("click", async () => {
    const title = $("plannerEventTitle")?.value?.trim();
    const time = $("plannerEventTime")?.value?.trim();
    if (!title) {
      window.showAriaToast?.("Event title required", "warn", 2500);
      $("plannerEventTitle")?.focus();
      return;
    }
    try {
      await p0Fetch("/api/planner/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, time: time || undefined, when: "today" }),
      });
      $("plannerEventTitle").value = "";
      if ($("plannerEventTime")) $("plannerEventTime").value = "";
      loadPlanner();
      window.AriaPlannerLive?.refreshFocus?.();
      window.AriaCollapsiblePanels?.expand?.("#plannerView", "Today");
      window.showAriaToast?.("Event added", "ok", 2000);
    } catch (e) {
      window.showAriaToast?.(`Add event failed: ${e.message}`, "err");
    }
  });

  bindEnter("plannerTaskInput", "plannerAddTaskBtn");
  bindEnter("plannerTimerInput", "plannerTimerBtn");
  bindEnter("plannerAlarmInput", "plannerAlarmBtn");
  bindEnter("plannerEventTitle", "plannerAddEventBtn");
  bindEnter("plannerEventTime", "plannerAddEventBtn");

  document.addEventListener("keydown", (e) => {
    if (document.body?.dataset?.activeView !== "planner" && !$("plannerView")?.classList.contains("active")) {
      // fallback: only when planner visible
      if ($("plannerView")?.classList.contains("hidden")) return;
    }
    const tag = (e.target?.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || e.target?.isContentEditable) return;
    if (!$("plannerView") || $("plannerView").classList.contains("hidden")) return;
    const k = e.key.toLowerCase();
    if (k === "n") {
      e.preventDefault();
      $("plannerTaskInput")?.focus();
    } else if (k === "p") {
      e.preventDefault();
      $("plannerPomodoroBtn")?.click();
    } else if (k === "f") {
      e.preventDefault();
      document.querySelector('[data-pf="focus"]')?.click();
    } else if (k === "t") {
      e.preventDefault();
      document.querySelector('[data-pf="triage"]')?.click();
    } else if (k === "u") {
      e.preventDefault();
      document.querySelector('[data-pf="undo"]')?.click();
    } else if (k === "?" || (e.shiftKey && k === "/")) {
      e.preventDefault();
      $("shortcutsBtn")?.click();
    }
  });
};

window.loadPlanner = loadPlanner;

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
