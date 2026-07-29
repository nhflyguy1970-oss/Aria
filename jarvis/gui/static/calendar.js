/** Calendar — unified schedule hub (month / week / agenda / timeline). */
(function () {
  "use strict";

  const CAL_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const CAL_WEEK_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

  let calMonth = "";
  let calSelectedDay = "";
  let calWorkSchedule = null;
  let calView = "month"; // month | week | agenda | timeline
  let calFilter = "all";
  let calSearch = "";
  let timelineTimer = null;
  let lastDayItems = [];

  function calEl(id) {
    return document.getElementById(id);
  }

  function escapeHtml(t) {
    return String(t ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Local YYYY-MM-DD (never UTC midnight rollover). */
  function todayIso() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function monthKey(d = new Date()) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  function shiftMonth(mk, delta) {
    const [y, m] = mk.split("-").map(Number);
    const d = new Date(y, m - 1 + delta, 1);
    return monthKey(d);
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || data.detail || data.error || res.statusText || "Request failed");
    }
    return data;
  }

  function sourceBadge(src) {
    const label = { journal: "Journal", planner: "Planner", ics: "ICS", work: "Work", holiday: "Holiday", timer: "Timer", alarm: "Alarm", memory: "Memory" }[src] || src;
    return `<span class="cal-source cal-source-${escapeHtml(src || "other")}" title="${escapeHtml(label)}">${escapeHtml(label)}</span>`;
  }

  function matchesFilter(item) {
    if (calFilter !== "all" && item.source !== calFilter) return false;
    if (calSearch) {
      const q = calSearch.toLowerCase();
      const hay = `${item.title || item.content || ""} ${item.source || ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  }

  function renderHolidayLegend(holidays) {
    const entries = Object.entries(holidays || {}).sort(([a], [b]) => a.localeCompare(b));
    if (!entries.length) return "";
    const chips = entries
      .map(([dateStr, list]) => {
        const dayNum = parseInt(dateStr.slice(8), 10);
        const names = list.map((h) => h.name || h).join(", ");
        return `<span class="bujo-cal-holiday-chip"><strong>${dayNum}</strong> ${escapeHtml(names)}</span>`;
      })
      .join("");
    return `<div class="bujo-cal-holidays-legend">${chips}</div>`;
  }

  function renderIcsStatus(status) {
    const el = calEl("calendarIcsStatus");
    if (!el) return;
    if (!status || !status.configured) {
      el.textContent = "No external calendar — add an ICS URL below.";
      el.className = "muted";
      return;
    }
    if (status.ok) {
      const when = status.last_sync ? ` · synced ${status.last_sync}` : "";
      el.textContent = `ICS linked${when}${status.cached ? " (cached)" : ""}`;
      el.className = "muted cal-ics-ok";
    } else {
      el.textContent = `ICS error: ${status.last_error || "sync failed"} — using cache if available`;
      el.className = "audit-error";
    }
  }

  function renderMonthGrid(data, month) {
    const weeks = data.weeks || [];
    const dayMap = data.days || {};
    const notes = data.calendar_notes || {};
    const events = data.events || {};
    const holidays = data.holidays || {};
    const workDays = data.work_days || {};
    const today = data.today || todayIso();
    let grid = `<div class="bujo-cal-grid" role="rowgroup"><div class="bujo-cal-head" role="row">${CAL_WEEKDAYS.map(
      (d) => `<span role="columnheader">${d}</span>`,
    ).join("")}</div>`;
    weeks.forEach((week) => {
      grid += '<div class="bujo-cal-week" role="row">';
      week.forEach((dayNum) => {
        if (!dayNum) {
          grid += '<div class="bujo-cal-day empty" role="gridcell"></div>';
          return;
        }
        const info = dayMap[String(dayNum)] || {};
        const dateStr = info.date || `${month}-${String(dayNum).padStart(2, "0")}`;
        const isToday = dateStr === today;
        const isSelected = dateStr === calSelectedDay;
        const note = notes[String(dayNum)] || "";
        const dayEvents = (events[dateStr] || [])
          .filter((e) => matchesFilter({ source: e.source || "journal", title: e.content || e.summary }))
          .slice(0, 3)
          .map((e) => {
            const src = e.source || "journal";
            const label = e.time ? `${e.time} ` : "";
            return `<span class="bujo-cal-event cal-chip-${escapeHtml(src)}">${escapeHtml(label)}${escapeHtml(String(e.content || e.summary || "").slice(0, 18))}</span>`;
          })
          .join("");
        const dayHolidays = (holidays[dateStr] || [])
          .slice(0, 1)
          .map((h) => {
            const name = h.name || h;
            return `<span class="bujo-cal-holiday" title="${escapeHtml(name)}">★ ${escapeHtml(String(name).slice(0, 10))}</span>`;
          })
          .join("");
        const workDot = workDays[String(dayNum)] ? '<span class="cal-work-dot" title="Work schedule" aria-hidden="true"></span>' : "";
        grid += `<button type="button" role="gridcell" class="bujo-cal-day${isToday ? " today" : ""}${info.count ? " has-entries" : ""}${isSelected ? " selected" : ""}${dayHolidays ? " has-holiday" : ""}"
          data-date="${dateStr}" aria-label="${dateStr}" aria-pressed="${isSelected ? "true" : "false"}">
          <span class="bujo-cal-num">${dayNum}${workDot}</span>
          ${dayHolidays}
          ${dayEvents}
          ${note ? `<span class="bujo-cal-note">${escapeHtml(note.slice(0, 24))}</span>` : ""}
        </button>`;
      });
      grid += "</div>";
    });
    grid += "</div>";
    return grid;
  }

  function itemRow(it) {
    const time = it.time || (it.all_day ? "all day" : "");
    const editable = it.editable;
    return `<li class="cal-item cal-item-${escapeHtml(it.source || "other")} cal-kind-${escapeHtml(it.kind || "event")}" data-item-id="${escapeHtml(it.id)}" tabindex="0">
      <span class="cal-item-time">${escapeHtml(time)}</span>
      <span class="cal-item-title">${escapeHtml(it.title || it.content || "")}</span>
      ${sourceBadge(it.source)}
      ${
        editable
          ? `<span class="cal-item-actions">
        <button type="button" class="ghost-btn tiny" data-act="edit" aria-label="Edit">Edit</button>
        <button type="button" class="ghost-btn tiny" data-act="dup" aria-label="Duplicate">Dup</button>
        ${it.kind === "task" ? `<button type="button" class="ghost-btn tiny" data-act="done" aria-label="Complete">Done</button>` : ""}
        <button type="button" class="ghost-btn tiny" data-act="del" aria-label="Delete">Del</button>
      </span>`
          : it.source === "planner"
            ? `<button type="button" class="ghost-btn tiny" data-act="planner" aria-label="Open Planner">Planner</button>`
            : ""
      }
    </li>`;
  }

  function bindItemActions(root, day) {
    root.querySelectorAll("[data-item-id]").forEach((li) => {
      const id = li.dataset.itemId;
      li.addEventListener("contextmenu", (e) => {
        const item = lastDayItems.find((x) => x.id === id);
        if (!item?.editable) return;
        window.AriaContextMenu?.open(e, [
          { label: "Edit", run: () => editItem(id) },
          { label: "Duplicate", run: () => dupItem(id, day) },
          item.kind === "task" ? { label: "Complete", run: () => completeItem(id) } : null,
          { label: "Delete", run: () => deleteItem(id) },
          { label: "Ask Aria", run: () => {
            window.jarvisAskAria?.(`About my calendar item: ${item.title}`, {
              autoSend: true,
              returnView: "calendar",
              context: [{ kind: "calendar", id: String(id || item.title), label: String(item.title || "").slice(0, 40) }],
            });
          }},
        ].filter(Boolean));
      });
      li.querySelectorAll("[data-act]").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const act = btn.dataset.act;
          if (act === "edit") editItem(id);
          else if (act === "dup") dupItem(id, day);
          else if (act === "done") completeItem(id);
          else if (act === "del") deleteItem(id);
          else if (act === "planner") window.switchToView?.("planner");
        });
      });
    });
  }

  async function editItem(id) {
    const item = lastDayItems.find((x) => x.id === id);
    if (!item) return;
    const title = prompt("Title", item.title || "");
    if (title == null) return;
    const time = prompt("Time (HH:MM or blank for all-day)", item.time || "");
    if (time == null) return;
    try {
      await fetchJson(`/api/calendar/items/${encodeURIComponent(id)}/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, time: time || "" }),
      });
      window.showAriaToast?.("Updated", "ok", 2000);
      await refreshCurrent();
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  }

  async function deleteItem(id) {
    if (!confirm("Delete this item?")) return;
    try {
      await fetchJson(`/api/calendar/items/${encodeURIComponent(id)}`, { method: "DELETE" });
      window.showAriaToast?.("Deleted", "ok", 2000);
      await refreshCurrent();
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  }

  async function dupItem(id, day) {
    try {
      await fetchJson(`/api/calendar/items/${encodeURIComponent(id)}/duplicate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ day: day || calSelectedDay }),
      });
      window.showAriaToast?.("Duplicated", "ok", 2000);
      await refreshCurrent();
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  }

  async function completeItem(id) {
    try {
      await fetchJson(`/api/calendar/items/${encodeURIComponent(id)}/complete`, { method: "POST" });
      window.showAriaToast?.("Completed", "ok", 2000);
      await refreshCurrent();
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  }

  function renderDayPanel(data) {
    const el = calEl("calendarDayPanel");
    if (!el || !data?.day) return;
    const items = (data.items || []).filter(matchesFilter);
    lastDayItems = data.items || [];
    renderIcsStatus(data.ics_status);

    const list = items.map(itemRow).join("") || "";
    const hasItems = items.length > 0;

    el.innerHTML = `
      <h3 id="calDayHeading">${escapeHtml(data.title || data.day)}</h3>
      <div class="cal-day-actions">
        <button type="button" id="calOpenJournalBtn" class="ghost-btn small">Open in Journal</button>
        <button type="button" id="calOpenPlannerBtn" class="ghost-btn small">Open Planner</button>
        <button type="button" id="calConflictsBtn" class="ghost-btn small">Check conflicts</button>
        <button type="button" id="calPrepBtn" class="ghost-btn small">Meeting prep</button>
        <button type="button" id="calFocusSugBtn" class="ghost-btn small">Focus windows</button>
      </div>
      ${hasItems ? "" : `<div class="empty-state"><div class="empty-state-icon" aria-hidden="true">📅</div><p class="empty-state-title">Nothing scheduled</p><p class="muted">Calendar holds scheduled commitments. Saves to Journal by default.</p><div class="empty-state-actions"><button type="button" class="apply-btn tiny" id="calEmptyAddBtn">Add commitment</button><button type="button" class="ghost-btn tiny" id="calEmptyChatBtn">Ask Chat</button></div></div>`}
      ${list ? `<ul class="cal-day-list" aria-labelledby="calDayHeading">${list}</ul>` : ""}
      <div id="calInsightPanel" class="cal-insight-panel hidden" aria-live="polite"></div>
      <div class="cal-add-form">
        <p class="cal-section-label">Add commitment <span class="muted">(saves to Journal · scheduled)</span></p>
        <div class="cal-add-row">
          <input type="time" id="calAddTime" class="audio-path-input cal-time-input" aria-label="Event time" />
          <select id="calAddType" class="personality-select" aria-label="Entry type">
            <option value="event">Appointment / event</option>
            <option value="task">Task</option>
            <option value="note">Note</option>
          </select>
          <select id="calAddTarget" class="personality-select" aria-label="Save target" title="Where to store">
            <option value="journal">Journal (default)</option>
            <option value="planner">Planner event</option>
          </select>
        </div>
        <input type="text" id="calAddContent" class="audio-path-input" placeholder="Description… (Enter to save)" aria-label="Event description" />
        <input type="text" id="calNlInput" class="audio-path-input" placeholder="Or natural language: Lunch tomorrow 12pm" aria-label="Natural language schedule" />
        <div class="sidebar-btn-row">
          <button type="button" id="calAddBtn" class="apply-btn small">Add to day</button>
          <button type="button" id="calNlBtn" class="ghost-btn small">Parse &amp; confirm</button>
        </div>
      </div>
      <div class="cal-note-form">
        <p class="cal-section-label">Day note (monthly calendar)</p>
        <textarea id="calDayNote" rows="2" placeholder="Fly fishing, birthday, travel…">${escapeHtml(data.calendar_note || "")}</textarea>
        <button type="button" id="calNoteSaveBtn" class="ghost-btn small">Save day note</button>
      </div>`;

    calEl("calAddBtn")?.addEventListener("click", () => addCalendarEntry(data.day));
    calEl("calNlBtn")?.addEventListener("click", () => runNlSchedule());
    calEl("calNoteSaveBtn")?.addEventListener("click", () => saveCalendarNote(data.day));
    calEl("calEmptyAddBtn")?.addEventListener("click", () => calEl("calAddContent")?.focus());
    calEl("calEmptyChatBtn")?.addEventListener("click", () => {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.(`Schedule a calendar commitment on ${data.day}: `);
    });
    calEl("calOpenPlannerBtn")?.addEventListener("click", () => window.switchToView?.("planner"));
    calEl("calOpenJournalBtn")?.addEventListener("click", () => openJournalDay(data.day));
    calEl("calConflictsBtn")?.addEventListener("click", () => showConflicts(data.day));
    calEl("calPrepBtn")?.addEventListener("click", () => showPrep());
    calEl("calFocusSugBtn")?.addEventListener("click", () => showFocus(data.day));
    ["calAddContent", "calNlInput"].forEach((id) => {
      calEl(id)?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          if (id === "calNlInput") runNlSchedule();
          else addCalendarEntry(data.day);
        }
      });
    });
    bindItemActions(el, data.day);
  }

  function openJournalDay(day) {
    window.switchToView?.("journal");
    setTimeout(() => {
      const jd = document.getElementById("journalDate");
      if (jd && day) {
        jd.value = day;
        jd.dispatchEvent(new Event("change", { bubbles: true }));
      }
      window.setBujoTab?.("daily");
      document.querySelector('.bujo-tab[data-bujo="daily"]')?.click();
    }, 120);
  }

  async function showConflicts(day) {
    const panel = calEl("calInsightPanel");
    if (!panel) return;
    panel.classList.remove("hidden");
    panel.innerHTML = "<p class='muted'>Checking conflicts…</p>";
    try {
      const data = await fetchJson(`/api/calendar/conflicts?day=${encodeURIComponent(day)}`);
      const rows = (data.conflicts || []).map((c) => `<li>${escapeHtml(c.a)} ↔ ${escapeHtml(c.b)} @ ${escapeHtml(c.when || "")}</li>`).join("");
      const sug = (data.suggestions || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("");
      panel.innerHTML = `<h4>Conflicts</h4><ul>${rows || "<li class='muted'>None</li>"}</ul><h4>Suggestions</h4><ul>${sug || "<li class='muted'>None</li>"}</ul>`;
    } catch (e) {
      panel.innerHTML = `<p class="audit-error">${escapeHtml(e.message)}</p>`;
    }
  }

  async function showPrep() {
    const panel = calEl("calInsightPanel");
    if (!panel) return;
    panel.classList.remove("hidden");
    panel.innerHTML = "<p class='muted'>Preparing meeting brief…</p>";
    try {
      const data = await fetchJson("/api/calendar/prep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      panel.innerHTML = `<h4>Meeting prep</h4><p>${escapeHtml(data.message || "")}</p>
        <p class="muted">Agenda</p><ul>${(data.agenda || []).map((a) => `<li>${escapeHtml(a)}</li>`).join("")}</ul>
        ${(data.memory || []).length ? `<p class="muted">Memory</p><ul>${data.memory.map((m) => `<li>${escapeHtml(m)}</li>`).join("")}</ul>` : ""}
        ${(data.open_tasks || []).length ? `<p class="muted">Related tasks</p><ul>${data.open_tasks.map((m) => `<li>${escapeHtml(m)}</li>`).join("")}</ul>` : ""}`;
    } catch (e) {
      panel.innerHTML = `<p class="audit-error">${escapeHtml(e.message)}</p>`;
    }
  }

  async function showFocus(day) {
    const panel = calEl("calInsightPanel");
    if (!panel) return;
    panel.classList.remove("hidden");
    try {
      const data = await fetchJson(`/api/calendar/focus-suggestions?day=${encodeURIComponent(day)}`);
      const rows = (data.suggestions || [])
        .map(
          (s) =>
            `<li>${escapeHtml(s.when)} · ${escapeHtml(s.priority || "")}
              <button type="button" class="ghost-btn tiny" data-focus-when="${escapeHtml(s.when)}">Start focus</button></li>`,
        )
        .join("");
      panel.innerHTML = `<h4>Focus windows</h4><ul>${rows || "<li class='muted'>No long free blocks</li>"}</ul>`;
      panel.querySelectorAll("[data-focus-when]").forEach((btn) => {
        btn.addEventListener("click", () => {
          if (!confirm(`Start a focus session during ${btn.dataset.focusWhen}?`)) return;
          window.switchToView?.("planner");
          setTimeout(() => document.querySelector('[data-pf="focus"]')?.click(), 120);
        });
      });
    } catch (e) {
      panel.innerHTML = `<p class="audit-error">${escapeHtml(e.message)}</p>`;
    }
  }

  async function runNlSchedule() {
    const text = calEl("calNlInput")?.value?.trim();
    if (!text) {
      window.showAriaToast?.("Enter a natural language schedule", "warn");
      return;
    }
    try {
      const parsed = await fetchJson("/api/calendar/nl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!confirm((parsed.message || "Confirm?") + "\n\nRequires confirmation.")) return;
      await fetchJson("/api/calendar/nl/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmed: true, proposal: parsed.proposal }),
      });
      calEl("calNlInput").value = "";
      window.showAriaToast?.("Scheduled", "ok", 2500);
      await refreshCurrent();
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  }

  async function loadCalendarDay(day) {
    calSelectedDay = day;
    try {
      const data = await fetchJson(`/api/calendar/day?day=${encodeURIComponent(day)}`);
      renderDayPanel(data);
    } catch (e) {
      const el = calEl("calendarDayPanel");
      if (el) el.innerHTML = `<p class="muted">Could not load day: ${escapeHtml(e.message)}</p>`;
      window.showAriaToast?.(`Calendar day failed: ${e.message}`, "err");
    }
    document.querySelectorAll("#calendarGrid .bujo-cal-day[data-date]").forEach((btn) => {
      const sel = btn.dataset.date === day;
      btn.classList.toggle("selected", sel);
      btn.setAttribute("aria-pressed", sel ? "true" : "false");
    });
  }

  async function loadCalendarMonth(month) {
    calMonth = month;
    const label = calEl("calendarMonthLabel");
    if (label) label.textContent = formatMonthLabel(month);
    const grid = calEl("calendarGrid");
    const legend = calEl("calendarHolidayLegend");
    if (grid && calView === "month") {
      grid.innerHTML = '<p class="muted calendar-loading" aria-busy="true">Loading calendar…</p>';
    }
    try {
      const data = await fetchJson(`/api/calendar/month?month=${encodeURIComponent(month)}`);
      renderIcsStatus(data.ics_status);
      if (legend) legend.innerHTML = renderHolidayLegend(data.holidays);
      if (calView === "month" && grid) {
        grid.innerHTML = renderMonthGrid(data, month);
        grid.querySelectorAll(".bujo-cal-day[data-date]").forEach((btn) => {
          btn.addEventListener("click", () => loadCalendarDay(btn.dataset.date));
        });
      }
      if (!calSelectedDay || !calSelectedDay.startsWith(month)) {
        calSelectedDay = data.today?.startsWith(month) ? data.today : `${month}-01`;
      }
      if (calView === "month") await loadCalendarDay(calSelectedDay);
    } catch (err) {
      if (grid) grid.innerHTML = `<p class="audit-error">Calendar failed: ${escapeHtml(err.message || String(err))}</p>`;
      window.showAriaToast?.("Calendar load failed", "err", 5000);
    }
  }

  async function loadWeek() {
    const grid = calEl("calendarGrid");
    if (!grid) return;
    grid.innerHTML = '<p class="muted" aria-busy="true">Loading week…</p>';
    try {
      const data = await fetchJson(`/api/calendar/week?anchor=${encodeURIComponent(calSelectedDay || todayIso())}`);
      renderIcsStatus(data.ics_status);
      let html = '<div class="cal-week-grid">';
      (data.dates || []).forEach((d) => {
        const detail = (data.days || {})[d] || {};
        const items = (detail.items || []).filter(matchesFilter).slice(0, 8);
        html += `<section class="cal-week-col" data-date="${d}">
          <button type="button" class="cal-week-head ghost-btn" data-date="${d}"><strong>${escapeHtml(d.slice(5))}</strong></button>
          <ul>${items.map((it) => `<li class="cal-chip-${escapeHtml(it.source)}"><span class="muted">${escapeHtml(it.time || "·")}</span> ${escapeHtml((it.title || "").slice(0, 28))} ${sourceBadge(it.source)}</li>`).join("") || "<li class='muted'>—</li>"}</ul>
        </section>`;
      });
      html += "</div>";
      grid.innerHTML = html;
      grid.querySelectorAll("[data-date]").forEach((btn) => {
        btn.addEventListener("click", () => {
          calSelectedDay = btn.dataset.date;
          loadCalendarDay(calSelectedDay);
        });
      });
      await loadCalendarDay(calSelectedDay || todayIso());
    } catch (e) {
      grid.innerHTML = `<p class="audit-error">${escapeHtml(e.message)}</p>`;
    }
  }

  async function loadAgenda() {
    const grid = calEl("calendarGrid");
    if (!grid) return;
    grid.innerHTML = '<p class="muted" aria-busy="true">Loading agenda…</p>';
    try {
      const data = await fetchJson(`/api/calendar/agenda?days=7&start=${encodeURIComponent(calSelectedDay || todayIso())}`);
      renderIcsStatus(data.ics_status);
      const free = (data.free_windows || [])
        .map((w) => `<li class="muted">Free ${escapeHtml(w.start_hm)}–${escapeHtml(w.end_hm)} (${w.minutes}m)</li>`)
        .join("");
      let html = `<div class="cal-agenda"><p class="cal-section-label">Next 7 days</p><ul class="cal-day-list">`;
      let lastDay = "";
      (data.items || []).filter(matchesFilter).forEach((it) => {
        if (it.day !== lastDay) {
          html += `</ul><h4>${escapeHtml(it.day)}</h4><ul class="cal-day-list">`;
          lastDay = it.day;
        }
        html += itemRow(it);
      });
      html += `</ul><p class="cal-section-label">Free time (today)</p><ul>${free || "<li class='muted'>Packed</li>"}</ul></div>`;
      grid.innerHTML = html;
      lastDayItems = data.items || [];
      bindItemActions(grid, calSelectedDay);
      await loadCalendarDay(calSelectedDay || todayIso());
    } catch (e) {
      grid.innerHTML = `<p class="audit-error">${escapeHtml(e.message)}</p>`;
    }
  }

  async function loadTimeline() {
    const grid = calEl("calendarGrid");
    if (!grid) return;
    try {
      const day = calSelectedDay || todayIso();
      const data = await fetchJson(`/api/calendar/timeline?day=${encodeURIComponent(day)}`);
      renderIcsStatus(data.ics_status);
      const now = data.now_hm;
      const hours = [];
      for (let h = 7; h <= 21; h++) hours.push(h);
      let html = `<div class="cal-timeline" aria-label="Timeline for ${escapeHtml(day)}">
        <div class="cal-timeline-meta">
          <strong>Timeline</strong>
          ${data.next ? `<span class="muted">Next: ${escapeHtml(data.next.title)} @ ${escapeHtml(data.next.time || "")}${data.countdown_min != null ? ` · ${data.countdown_min}m` : ""}</span>` : "<span class='muted'>No upcoming timed commitment</span>"}
        </div>
        <div class="cal-timeline-track">`;
      hours.forEach((h) => {
        const hm = `${String(h).padStart(2, "0")}:00`;
        const slotItems = (data.items || []).filter((it) => (it.time || "").startsWith(String(h).padStart(2, "0")));
        const isNow = now && now.startsWith(String(h).padStart(2, "0"));
        html += `<div class="cal-tl-hour${isNow ? " cal-tl-now" : ""}">
          <span class="cal-tl-label">${hm}</span>
          <div class="cal-tl-slot">${slotItems.map((it) => `<div class="cal-tl-event cal-chip-${escapeHtml(it.source)}">${escapeHtml(it.title)} ${sourceBadge(it.source)}</div>`).join("") || (isNow ? '<span class="cal-now-marker" aria-label="Current time">now</span>' : "")}</div>
        </div>`;
      });
      const untimed = (data.items || []).filter((it) => !it.time);
      html += `</div>
        <p class="cal-section-label">All-day / untimed</p>
        <ul class="cal-day-list">${untimed.filter(matchesFilter).map(itemRow).join("") || "<li class='muted'>None</li>"}</ul>
        <p class="cal-section-label">Focus windows</p>
        <ul>${(data.focus_windows || []).map((w) => `<li>${escapeHtml(w.start_hm)}–${escapeHtml(w.end_hm)} (${w.minutes}m)</li>`).join("") || "<li class='muted'>None</li>"}</ul>
      </div>`;
      grid.innerHTML = html;
      lastDayItems = data.items || [];
      bindItemActions(grid, day);
      await loadCalendarDay(day);
    } catch (e) {
      grid.innerHTML = `<p class="audit-error">${escapeHtml(e.message)}</p>`;
    }
  }

  function formatMonthLabel(mk) {
    const [y, m] = mk.split("-").map(Number);
    return new Date(y, m - 1, 1).toLocaleString(undefined, { month: "long", year: "numeric" });
  }

  async function addCalendarEntry(day) {
    const content = calEl("calAddContent")?.value?.trim();
    const time = calEl("calAddTime")?.value?.trim();
    const bulletType = calEl("calAddType")?.value || "event";
    const target = calEl("calAddTarget")?.value || "journal";
    if (!content) {
      window.showAriaToast?.("Enter event text first", "warn", 2500);
      return;
    }
    try {
      if (bulletType === "event") {
        await fetchJson("/api/calendar/items", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: content, day, time: time || null, target }),
        });
      } else {
        const form = new FormData();
        form.append("content", content);
        form.append("bullet_type", bulletType);
        form.append("day", day);
        if (time) form.append("time", time);
        const res = await fetch("/api/journal/daily", { method: "POST", body: form });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) throw new Error(data.message || "Could not add entry");
      }
      calEl("calAddContent").value = "";
      window.showAriaToast?.(`Saved to ${target === "planner" ? "Planner" : "Journal"}`, "ok", 3000);
      await refreshCurrent();
    } catch (err) {
      window.showAriaToast?.(err?.message || "Could not add entry", "err", 5000);
    }
  }

  async function saveCalendarNote(day) {
    const note = calEl("calDayNote")?.value ?? "";
    const dayNum = parseInt(day.slice(8), 10);
    const form = new FormData();
    form.append("day", String(dayNum));
    form.append("note", note);
    form.append("month", calMonth || day.slice(0, 7));
    try {
      const res = await fetch("/api/journal/monthly/calendar-note", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) throw new Error(data.message || "Save failed");
      window.showAriaToast?.("Day note saved", "ok", 3000);
      await refreshCurrent();
    } catch (e) {
      window.showAriaToast?.(`Could not save day note: ${e.message}`, "err", 5000);
    }
  }

  function renderWorkScheduleEditor(sched) {
    const el = calEl("calendarWorkSchedule");
    if (!el || !sched) return;
    const enabled = sched.enabled !== false;
    let html = `<label class="memory-setting"><input type="checkbox" id="calWorkEnabled" ${enabled ? "checked" : ""} /> Show work blocks on calendar</label>`;
    html += '<div class="cal-work-grid">';
    CAL_WEEK_KEYS.forEach((key, i) => {
      const blocks = sched.days?.[key] || [];
      const rows = blocks
        .map(
          (b, idx) =>
            `<div class="cal-work-row" data-day="${key}" data-idx="${idx}">
        <input type="time" class="cal-ws-start audio-path-input" value="${escapeHtml(b.start)}" />
        <input type="time" class="cal-ws-end audio-path-input" value="${escapeHtml(b.end)}" />
        <input type="text" class="cal-ws-label audio-path-input" value="${escapeHtml(b.label || "Work")}" placeholder="Label" />
        <button type="button" class="ghost-btn tiny cal-ws-remove" title="Remove work block" aria-label="Remove work block">×</button>
      </div>`,
        )
        .join("");
      html += `<div class="cal-work-day" data-day="${key}">
      <strong>${CAL_WEEKDAYS[i]}</strong>
      <div class="cal-work-rows">${rows || '<p class="muted">No blocks</p>'}</div>
      <button type="button" class="ghost-btn tiny cal-ws-add" data-day="${key}">+ block</button>
    </div>`;
    });
    html += "</div>";
    html += '<button type="button" id="calWorkSaveBtn" class="apply-btn small">Save work schedule</button>';
    el.innerHTML = html;
    el.querySelectorAll(".cal-ws-add").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.day;
        const rows = el.querySelector(`.cal-work-day[data-day="${key}"] .cal-work-rows`);
        if (!rows) return;
        if (rows.querySelector(".muted")) rows.innerHTML = "";
        rows.insertAdjacentHTML(
          "beforeend",
          `<div class="cal-work-row" data-day="${key}">
        <input type="time" class="cal-ws-start audio-path-input" value="09:00" />
        <input type="time" class="cal-ws-end audio-path-input" value="17:00" />
        <input type="text" class="cal-ws-label audio-path-input" value="Work" />
        <button type="button" class="ghost-btn tiny cal-ws-remove" title="Remove work block" aria-label="Remove work block">×</button>
      </div>`,
        );
        bindWorkRemove(el);
      });
    });
    bindWorkRemove(el);
    calEl("calWorkSaveBtn")?.addEventListener("click", saveWorkSchedule);
  }

  function bindWorkRemove(root) {
    root.querySelectorAll(".cal-ws-remove").forEach((btn) => {
      btn.onclick = () => btn.closest(".cal-work-row")?.remove();
    });
  }

  function collectWorkSchedule() {
    const enabled = calEl("calWorkEnabled")?.checked !== false;
    const days = {};
    CAL_WEEK_KEYS.forEach((key) => {
      days[key] = [];
      calEl("calendarWorkSchedule")?.querySelectorAll(`.cal-work-row[data-day="${key}"]`).forEach((row) => {
        days[key].push({
          start: row.querySelector(".cal-ws-start")?.value || "",
          end: row.querySelector(".cal-ws-end")?.value || "",
          label: row.querySelector(".cal-ws-label")?.value || "Work",
        });
      });
    });
    return { enabled, days };
  }

  async function saveWorkSchedule() {
    try {
      const data = await fetchJson("/api/calendar/work-schedule", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectWorkSchedule()),
      });
      calWorkSchedule = data;
      window.showAriaToast?.("Work schedule saved", "ok", 3000);
      await refreshCurrent();
    } catch (err) {
      window.showAriaToast?.(err?.message || "Work schedule save failed", "err", 5000);
    }
  }

  async function loadWorkSchedule() {
    const data = await fetchJson("/api/calendar/work-schedule");
    calWorkSchedule = data;
    renderWorkScheduleEditor(data);
    renderIcsStatus(data.ics_status);
  }

  async function saveIcsUrl() {
    const status = calEl("calendarIcsStatus");
    try {
      const url = calEl("calendarIcsUrl")?.value?.trim() || "";
      const data = await fetchJson("/api/calendar/ics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const msg = data.message || (data.ok ? "ICS feed saved" : "ICS save failed");
      if (status) status.textContent = msg;
      window.showAriaToast?.(msg, data.ok ? "ok" : "err", data.ok ? 2500 : 5000);
      if (data.ok) {
        await fetchJson("/api/calendar/ics/refresh", { method: "POST" }).catch(() => {});
        await refreshCurrent();
      }
    } catch (err) {
      const msg = err?.message || "ICS save failed";
      if (status) status.textContent = msg;
      window.showAriaToast?.(msg, "err", 5000);
    }
  }

  async function testIcsUrl() {
    const status = calEl("calendarIcsStatus");
    try {
      const url = calEl("calendarIcsUrl")?.value?.trim() || "";
      if (!url) {
        window.showAriaToast?.("Enter an ICS URL to test", "warn", 3000);
        return;
      }
      const data = await fetchJson("/api/calendar/ics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, test_only: true }),
      });
      const msg = data.message || (data.ok ? "ICS feed OK" : "ICS test failed");
      if (status) status.textContent = msg;
      window.showAriaToast?.(msg, data.ok ? "ok" : "err", data.ok ? 2500 : 5000);
    } catch (err) {
      const msg = err?.message || "ICS test failed";
      if (status) status.textContent = msg;
      window.showAriaToast?.(msg, "err", 5000);
    }
  }

  async function refreshCurrent() {
    if (calView === "week") await loadWeek();
    else if (calView === "agenda") await loadAgenda();
    else if (calView === "timeline") await loadTimeline();
    else await loadCalendarMonth(calMonth || monthKey());
  }

  function setView(view) {
    calView = view;
    document.querySelectorAll("[data-cal-view]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.calView === view);
      btn.setAttribute("aria-pressed", btn.dataset.calView === view ? "true" : "false");
    });
    if (timelineTimer) {
      clearInterval(timelineTimer);
      timelineTimer = null;
    }
    if (view === "timeline") {
      timelineTimer = setInterval(() => {
        if (calView === "timeline" && !document.hidden) loadTimeline();
      }, 60000);
    }
    refreshCurrent();
  }

  function shiftSelectedDay(delta) {
    const d = new Date(`${calSelectedDay || todayIso()}T12:00:00`);
    d.setDate(d.getDate() + delta);
    const iso = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    calSelectedDay = iso;
    calMonth = iso.slice(0, 7);
    refreshCurrent();
  }

  function bindCalendarControls() {
    calEl("calendarPrevBtn")?.addEventListener("click", () => {
      if (calView === "month") loadCalendarMonth(shiftMonth(calMonth, -1));
      else shiftSelectedDay(calView === "week" ? -7 : -1);
    });
    calEl("calendarNextBtn")?.addEventListener("click", () => {
      if (calView === "month") loadCalendarMonth(shiftMonth(calMonth, 1));
      else shiftSelectedDay(calView === "week" ? 7 : 1);
    });
    calEl("calendarTodayBtn")?.addEventListener("click", () => {
      const t = todayIso();
      calSelectedDay = t;
      calMonth = t.slice(0, 7);
      refreshCurrent();
    });
    calEl("calendarOpenPlannerBtn")?.addEventListener("click", () => window.switchToView?.("planner"));
    calEl("calendarOpenJournalBtn")?.addEventListener("click", () => window.switchToView?.("journal"));
    calEl("calendarOpenDocumentsBtn")?.addEventListener("click", () => window.switchToView?.("documents"));
    calEl("calendarHintPlannerBtn")?.addEventListener("click", () => window.switchToView?.("planner"));
    calEl("calendarHintJournalBtn")?.addEventListener("click", () => window.switchToView?.("journal"));
    calEl("calendarIcsSaveBtn")?.addEventListener("click", saveIcsUrl);
    calEl("calendarIcsTestBtn")?.addEventListener("click", testIcsUrl);
    calEl("calendarIcsRefreshBtn")?.addEventListener("click", async () => {
      try {
        const data = await fetchJson("/api/calendar/ics/refresh", { method: "POST" });
        window.showAriaToast?.(data.message || "ICS refreshed", data.ok ? "ok" : "err");
        renderIcsStatus(data.status);
        await refreshCurrent();
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    });
    document.querySelectorAll("[data-cal-view]").forEach((btn) => {
      btn.addEventListener("click", () => setView(btn.dataset.calView));
    });
    calEl("calendarFilter")?.addEventListener("change", (e) => {
      calFilter = e.target.value || "all";
      refreshCurrent();
    });
    calEl("calendarSearch")?.addEventListener("input", (e) => {
      calSearch = e.target.value || "";
      refreshCurrent();
    });
    calEl("calendarVisionBtn")?.addEventListener("click", async () => {
      const path = prompt("Path to whiteboard / agenda / printed calendar image:");
      if (!path) return;
      try {
        const data = await fetchJson("/api/calendar/vision/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path }),
        });
        const n = (data.candidates || []).length;
        if (!n) {
          window.showAriaToast?.(data.message || "No events found", "warn");
          return;
        }
        if (!confirm(`Import ${n} candidate event(s)?`)) return;
        const imp = await fetchJson("/api/calendar/vision/import", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ candidates: data.candidates }),
        });
        window.showAriaToast?.(`Imported ${imp.count || 0}`, "ok");
        await refreshCurrent();
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    });
    calEl("calendarHaMeetingBtn")?.addEventListener("click", async () => {
      if (!confirm("Enable optional Home Assistant Meeting mode?")) return;
      try {
        const data = await fetchJson("/api/calendar/ha-mode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: "meeting" }),
        });
        window.showAriaToast?.(data.home_assistant?.message || `Mode: ${data.mode}`, data.ok ? "ok" : "warn");
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    });
    calEl("calendarMemoryBtn")?.addEventListener("click", async () => {
      try {
        const data = await fetchJson("/api/calendar/memory-dates");
        const lines = (data.reminders || []).map((r) => r.content).join("\n• ") || "None found";
        alert(`Memory dates / reminders:\n• ${lines}`);
      } catch (e) {
        window.showAriaToast?.(e.message, "err");
      }
    });

    document.addEventListener("keydown", (e) => {
      if (calEl("calendarView")?.classList.contains("hidden")) return;
      const tag = (e.target?.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || e.target?.isContentEditable) return;
      const k = e.key.toLowerCase();
      if (k === "arrowleft") {
        e.preventDefault();
        shiftSelectedDay(-1);
      } else if (k === "arrowright") {
        e.preventDefault();
        shiftSelectedDay(1);
      } else if (k === "t") {
        e.preventDefault();
        calEl("calendarTodayBtn")?.click();
      } else if (k === "n") {
        e.preventDefault();
        calEl("calAddContent")?.focus();
      } else if (k === "1") setView("month");
      else if (k === "2") setView("week");
      else if (k === "3") setView("agenda");
      else if (k === "4") setView("timeline");
    });
  }

  window.openCalendarDay = async function openCalendarDay(day) {
    const iso = String(day || todayIso()).slice(0, 10);
    window.switchToView?.("calendar");
    calSelectedDay = iso;
    calMonth = iso.slice(0, 7);
    await refreshCurrent();
  };

  window.initCalendar = async function initCalendar() {
    const root = calEl("calendarView");
    if (!root) return;
    if (root.dataset.bound !== "1") {
      root.dataset.bound = "1";
      bindCalendarControls();
      calMonth = monthKey();
      calSelectedDay = todayIso();
      try {
        await loadWorkSchedule();
      } catch (err) {
        console.warn("Work schedule load failed:", err);
        window.showAriaToast?.(`Work schedule unavailable: ${err?.message || "request failed"}`, "err", 5000);
      }
      const sched = calWorkSchedule || {};
      if (sched.ics_url && calEl("calendarIcsUrl")) calEl("calendarIcsUrl").value = sched.ics_url;
    }
    await refreshCurrent();
  };
})();
