/** Calendar tab — holidays, events, appointments, work schedule. */

const CAL_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const CAL_WEEK_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

let calMonth = "";
let calSelectedDay = "";
let calWorkSchedule = null;

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

function monthKey(d = new Date()) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function shiftMonth(mk, delta) {
  const [y, m] = mk.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return monthKey(d);
}

async function fetchJson(url, opts) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || data.detail || res.statusText || "Request failed");
  }
  return data;
}

function renderHolidayLegend(holidays) {
  const entries = Object.entries(holidays || {}).sort(([a], [b]) => a.localeCompare(b));
  if (!entries.length) return "";
  const chips = entries.map(([dateStr, list]) => {
    const dayNum = parseInt(dateStr.slice(8), 10);
    const names = list.map((h) => h.name).join(", ");
    return `<span class="bujo-cal-holiday-chip"><strong>${dayNum}</strong> ${escapeHtml(names)}</span>`;
  }).join("");
  return `<div class="bujo-cal-holidays-legend">${chips}</div>`;
}

function renderMonthGrid(data, month) {
  const weeks = data.weeks || [];
  const dayMap = data.days || {};
  const notes = data.calendar_notes || {};
  const events = data.events || {};
  const holidays = data.holidays || {};
  const today = data.today || todayIso();
  let grid = `<div class="bujo-cal-grid"><div class="bujo-cal-head">${CAL_WEEKDAYS.map((d) =>
    `<span>${d}</span>`
  ).join("")}</div>`;
  weeks.forEach((week) => {
    grid += '<div class="bujo-cal-week">';
    week.forEach((dayNum) => {
      if (!dayNum) {
        grid += '<div class="bujo-cal-day empty"></div>';
        return;
      }
      const info = dayMap[String(dayNum)] || {};
      const dateStr = info.date || `${month}-${String(dayNum).padStart(2, "0")}`;
      const isToday = dateStr === today;
      const isSelected = dateStr === calSelectedDay;
      const note = notes[String(dayNum)] || "";
      const dayEvents = (events[dateStr] || []).slice(0, 2).map((e) =>
        `<span class="bujo-cal-event">${escapeHtml(e.time || "")} ${escapeHtml((e.content || e.summary || "").slice(0, 12))}</span>`
      ).join("");
      const dayHolidays = (holidays[dateStr] || []).slice(0, 1).map((h) =>
        `<span class="bujo-cal-holiday" title="${escapeHtml(h.name)}">★ ${escapeHtml(h.name.slice(0, 10))}</span>`
      ).join("");
      grid += `<button type="button" class="bujo-cal-day${isToday ? " today" : ""}${info.count ? " has-entries" : ""}${isSelected ? " selected" : ""}${dayHolidays ? " has-holiday" : ""}"
        data-date="${dateStr}">
        <span class="bujo-cal-num">${dayNum}</span>
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

function renderDayPanel(data) {
  const el = calEl("calendarDayPanel");
  if (!el || !data?.day) return;
  const holidays = (data.holidays || []).map((h) =>
    `<li class="cal-item cal-item-holiday">★ ${escapeHtml(h.name)}</li>`
  ).join("");
  const work = (data.work_blocks || []).map((b) =>
    `<li class="cal-item cal-item-work">${escapeHtml(b.start)}–${escapeHtml(b.end)} ${escapeHtml(b.label)}</li>`
  ).join("");
  const ics = (data.ics_events || []).map((e) =>
    `<li class="cal-item cal-item-ics">${escapeHtml(e.time || "all day")} ${escapeHtml(e.summary || "")}</li>`
  ).join("");
  const events = (data.journal_events || []).map((e) =>
    `<li class="cal-item cal-item-event">${escapeHtml(e.time || "")} ${escapeHtml(e.content || "")}</li>`
  ).join("");
  const tasks = (data.tasks || []).filter((t) => t.status !== "done").map((t) =>
    `<li class="cal-item cal-item-task">☐ ${escapeHtml(t.content || "")}</li>`
  ).join("");
  const hasItems = Boolean(holidays || work || ics || events || tasks);

  el.innerHTML = `
    <h3>${escapeHtml(data.title || data.day)}</h3>
    ${hasItems ? "" : `<p class="muted">Nothing scheduled for this day.</p>`}
    ${holidays ? `<ul class="cal-day-list">${holidays}</ul>` : ""}
    ${work ? `<p class="cal-section-label">Work schedule</p><ul class="cal-day-list">${work}</ul>` : ""}
    ${ics ? `<p class="cal-section-label">External calendar</p><ul class="cal-day-list">${ics}</ul>` : ""}
    ${events ? `<p class="cal-section-label">Appointments &amp; events</p><ul class="cal-day-list">${events}</ul>` : ""}
    ${tasks ? `<p class="cal-section-label">Tasks</p><ul class="cal-day-list">${tasks}</ul>` : ""}
    <div class="cal-add-form">
      <p class="cal-section-label">Add entry</p>
      <div class="cal-add-row">
        <input type="time" id="calAddTime" class="audio-path-input cal-time-input" />
        <select id="calAddType" class="personality-select">
          <option value="event">Appointment / event</option>
          <option value="task">Task</option>
          <option value="note">Note</option>
        </select>
      </div>
      <input type="text" id="calAddContent" class="audio-path-input" placeholder="Description…" />
      <button type="button" id="calAddBtn" class="apply-btn small">Add to day</button>
    </div>
    <div class="cal-note-form">
      <p class="cal-section-label">Day note (monthly calendar)</p>
      <textarea id="calDayNote" rows="2" placeholder="Fly fishing, birthday, travel…">${escapeHtml(data.calendar_note || "")}</textarea>
      <button type="button" id="calNoteSaveBtn" class="ghost-btn small">Save day note</button>
    </div>`;

  calEl("calAddBtn")?.addEventListener("click", () => addCalendarEntry(data.day));
  calEl("calNoteSaveBtn")?.addEventListener("click", () => saveCalendarNote(data.day));
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
    btn.classList.toggle("selected", btn.dataset.date === day);
  });
}

async function loadCalendarMonth(month) {
  calMonth = month;
  const label = calEl("calendarMonthLabel");
  if (label) label.textContent = formatMonthLabel(month);
  const grid = calEl("calendarGrid");
  const legend = calEl("calendarHolidayLegend");
  if (grid && !grid.querySelector(".bujo-cal-grid")) {
    grid.innerHTML = '<p class="muted">Loading calendar…</p>';
  }
  try {
    const data = await fetchJson(`/api/calendar/month?month=${encodeURIComponent(month)}`);
    if (data.ok === false) {
      throw new Error(data.message || "Calendar load failed");
    }
    if (legend) legend.innerHTML = renderHolidayLegend(data.holidays);
    if (grid) {
      grid.innerHTML = renderMonthGrid(data, month);
      grid.querySelectorAll(".bujo-cal-day[data-date]").forEach((btn) => {
        btn.addEventListener("click", () => loadCalendarDay(btn.dataset.date));
      });
    }
    const icsEl = calEl("calendarIcsStatus");
    if (icsEl) {
      icsEl.textContent = data.ics_url
        ? "External calendar linked (ICS)."
        : "No external calendar — add an ICS URL below.";
    }
    if (!calSelectedDay || !calSelectedDay.startsWith(month)) {
      calSelectedDay = data.today?.startsWith(month) ? data.today : `${month}-01`;
    }
    await loadCalendarDay(calSelectedDay);
  } catch (err) {
    if (grid) {
      grid.innerHTML = `<p class="audit-error">Calendar failed: ${escapeHtml(err.message || String(err))}</p>`;
    }
    window.showAriaToast?.("Calendar load failed", "err", 5000);
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
  if (!content) return;
  const form = new FormData();
  form.append("content", content);
  form.append("bullet_type", bulletType);
  form.append("day", day);
  if (time && bulletType === "event") form.append("time", time);
  const res = await fetch("/api/journal/daily", { method: "POST", body: form });
  const data = await res.json();
  if (!data.ok) {
    window.showAriaToast?.("Could not add entry", "err", 5000);
    return;
  }
  calEl("calAddContent").value = "";
  window.showAriaToast?.("Added to calendar", "ok", 4000);
  await loadCalendarMonth(calMonth);
}

async function saveCalendarNote(day) {
  const note = calEl("calDayNote")?.value ?? "";
  const dayNum = parseInt(day.slice(8), 10);
  const form = new FormData();
  form.append("day", String(dayNum));
  form.append("note", note);
  form.append("month", calMonth);
  try {
    const res = await fetch("/api/journal/monthly/calendar-note", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || res.statusText || "Save failed");
    }
    window.showAriaToast?.("Day note saved", "ok", 4000);
    await loadCalendarMonth(calMonth);
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
    const rows = blocks.map((b, idx) =>
      `<div class="cal-work-row" data-day="${key}" data-idx="${idx}">
        <input type="time" class="cal-ws-start audio-path-input" value="${escapeHtml(b.start)}" />
        <input type="time" class="cal-ws-end audio-path-input" value="${escapeHtml(b.end)}" />
        <input type="text" class="cal-ws-label audio-path-input" value="${escapeHtml(b.label || "Work")}" placeholder="Label" />
        <button type="button" class="ghost-btn tiny cal-ws-remove">×</button>
      </div>`
    ).join("");
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
      rows.insertAdjacentHTML("beforeend", `<div class="cal-work-row" data-day="${key}">
        <input type="time" class="cal-ws-start audio-path-input" value="09:00" />
        <input type="time" class="cal-ws-end audio-path-input" value="17:00" />
        <input type="text" class="cal-ws-label audio-path-input" value="Work" />
        <button type="button" class="ghost-btn tiny cal-ws-remove">×</button>
      </div>`);
      bindWorkRemove(el);
    });
  });
  bindWorkRemove(el);
  calEl("calWorkSaveBtn")?.addEventListener("click", saveWorkSchedule);
}

function bindWorkRemove(root) {
  root.querySelectorAll(".cal-ws-remove").forEach((btn) => {
    btn.onclick = () => {
      btn.closest(".cal-work-row")?.remove();
    };
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
  const body = collectWorkSchedule();
  const data = await fetchJson("/api/calendar/work-schedule", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!data.ok) {
    window.showAriaToast?.("Save failed", "err", 5000);
    return;
  }
  calWorkSchedule = data;
  window.showAriaToast?.("Work schedule saved", "ok", 4000);
  if (calSelectedDay) await loadCalendarDay(calSelectedDay);
}

async function loadWorkSchedule() {
  const data = await fetchJson("/api/calendar/work-schedule");
  calWorkSchedule = data;
  renderWorkScheduleEditor(data);
}

async function saveIcsUrl() {
  const url = calEl("calendarIcsUrl")?.value?.trim() || "";
  const data = await fetchJson("/api/calendar/ics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  calEl("calendarIcsStatus").textContent = data.message || (data.ok ? "Saved" : "Failed");
  if (data.ok) await loadCalendarMonth(calMonth);
}

async function testIcsUrl() {
  const url = calEl("calendarIcsUrl")?.value?.trim() || "";
  const data = await fetchJson("/api/calendar/ics", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, test_only: true }),
  });
  calEl("calendarIcsStatus").textContent = data.message || (data.ok ? "OK" : "Failed");
}

function bindCalendarControls() {
  calEl("calendarPrevBtn")?.addEventListener("click", () => {
    loadCalendarMonth(shiftMonth(calMonth, -1));
  });
  calEl("calendarNextBtn")?.addEventListener("click", () => {
    loadCalendarMonth(shiftMonth(calMonth, 1));
  });
  calEl("calendarTodayBtn")?.addEventListener("click", () => {
    const t = todayIso();
    loadCalendarMonth(t.slice(0, 7)).then(() => loadCalendarDay(t));
  });
  calEl("calendarIcsSaveBtn")?.addEventListener("click", saveIcsUrl);
  calEl("calendarIcsTestBtn")?.addEventListener("click", testIcsUrl);
}

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
    }
    const sched = calWorkSchedule || {};
    if (sched.ics_url && calEl("calendarIcsUrl")) {
      calEl("calendarIcsUrl").value = sched.ics_url;
    }
  }
  await loadCalendarMonth(calMonth || monthKey());
};
