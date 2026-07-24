/** Bullet Journal UI — Daily, Weekly, Monthly, Habits, Future, Index, Collections */

const bujoContent = document.getElementById("bujoContent");
const journalDate = document.getElementById("journalDate");
const journalWeek = document.getElementById("journalWeek");
const journalMonth = document.getElementById("journalMonth");
const journalStats = document.getElementById("journalStats");
const journalSearch = document.getElementById("journalSearch");
const journalSearchBtn = document.getElementById("journalSearchBtn");
let currentBujo = "daily";
let monthlySelectedDay = null;
let dragBulletId = null;

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const GRATITUDE_PREFIX = "I am grateful for ";

function journalNotify(message, isError = true) {
  let el = document.getElementById("journalToast");
  if (!el) {
    el = document.createElement("div");
    el.id = "journalToast";
    el.className = "journal-toast hidden";
    document.getElementById("bujoPanel")?.appendChild(el);
  }
  el.textContent = message;
  el.classList.toggle("journal-toast-error", isError);
  el.classList.toggle("journal-toast-success", !isError);
  el.classList.remove("hidden");
  clearTimeout(journalNotify._timer);
  journalNotify._timer = setTimeout(() => el.classList.add("hidden"), 4500);
}

function showBujoLoading() {
  if (!bujoContent) return;
  bujoContent.innerHTML = '<p class="bujo-loading" aria-busy="true">Loading…</p>';
}

const nativeFetch = window.fetch.bind(window);

async function journalPost(url, init = {}) {
  const res = await nativeFetch(url, init);
  let body = {};
  try {
    // Parse a clone so callers can still read res.json() on the original response.
    body = await res.clone().json();
  } catch (_) {
    body = {};
  }
  if (!res.ok) {
    const msg = body.message || body.error || body.detail || `Request failed (${res.status})`;
    journalNotify(typeof msg === "string" ? msg : "Request failed");
    return { ok: false, res, body };
  }
  return { ok: true, res, body };
}

window.fetch = async function journalAwareFetch(url, init = {}) {
  const path = typeof url === "string" ? url : url?.url || "";
  if (path.includes("/api/journal")) {
    const out = await journalPost(path, init);
    if (out.res) return out.res;
    return new Response(JSON.stringify(out.body || {}), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
  return nativeFetch(url, init);
};

function futureMonthValue() {
  return journalMonth?.value || new Date().toISOString().slice(0, 7);
}

function formatMonthLabel(monthKey) {
  if (!monthKey || !/^\d{4}-\d{2}$/.test(monthKey)) return monthKey || "";
  const [y, m] = monthKey.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleString(undefined, { month: "long", year: "numeric" });
}

function updateRapidLogForTab() {
  const rapid = document.getElementById("rapidLogInput");
  const rapidBtn = document.getElementById("rapidLogBtn");
  if (!rapid) return;
  if (currentBujo === "future") {
    rapid.placeholder = `Rapid log → Future (${formatMonthLabel(futureMonthValue())}). One line per entry; indent 2 spaces to nest.`;
    if (rapidBtn) rapidBtn.textContent = "Add to Future";
  } else if (currentBujo === "weekly") {
    rapid.placeholder = "Rapid log — one line per entry. Indent 2 spaces to nest under the previous line.";
    if (rapidBtn) rapidBtn.textContent = "Add to Week";
  } else if (currentBujo === "monthly") {
    rapid.placeholder = "Rapid log — adds to this month's log (not a specific day). Indent 2 spaces to nest.";
    if (rapidBtn) rapidBtn.textContent = "Add to Month";
  } else {
    rapid.placeholder = "Rapid log — one line per entry. Indent 2 spaces to nest under the previous line.";
    if (rapidBtn) rapidBtn.textContent = "Add";
  }
}

function sym(b) {
  const t = b.type || "note", s = b.status || "open";
  if (t === "task") {
    if (s === "done") return "×";
    if (s === "migrated") return ">";
    if (s === "scheduled") return "<";
    if (s === "cancelled") return "~";
    return "•";
  }
  if (t === "event") return "○";
  return "—";
}

function sigPrefix(b) {
  return (b.signifiers || []).map((s) => {
    if (s === "important") return "*";
    if (s === "inspiration") return "!";
    if (s === "explore") return "👁";
    return "";
  }).join("");
}

function bulletTextClass(b) {
  const s = b.status || "open";
  if (s === "done" || s === "cancelled" || s === "migrated") return " bujo-text-done";
  return "";
}

function escapeHtml(t) {
  const d = document.createElement("div");
  d.textContent = t;
  return d.innerHTML;
}

function isoWeekValue(d = new Date()) {
  const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const dayNum = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const weekNo = Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
  return `${date.getUTCFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

function addRowHtml() {
  return `<div class="bujo-add-row">
    <select id="bujoAddType" aria-label="Bullet type">
      <option value="task">• Task</option>
      <option value="event">○ Event</option>
      <option value="note">— Note</option>
    </select>
    <input type="text" id="bujoAddContent" placeholder="Add entry…" />
    <button type="button" id="bujoAddBtn" class="apply-btn small">Add</button>
  </div>`;
}

function renderWeatherBlock(weather) {
  if (!weather?.condition && !weather?.summary) return "";
  const icon = weather.icon || "🌡️";
  const condition = weather.condition || String(weather.summary || "").split("·")[0].trim();
  const loc = weather.location ? `<span class="bujo-weather-loc">${escapeHtml(weather.location)}</span>` : "";
  const unit = weather.unit || "°";
  const hi = weather.high != null ? Math.round(Number(weather.high)) : "—";
  const lo = weather.low != null ? Math.round(Number(weather.low)) : "—";
  return `<div class="bujo-weather" aria-label="Today's weather">
    <span class="bujo-weather-icon" aria-hidden="true">${icon}</span>
    ${loc}
    <span class="bujo-weather-summary">${escapeHtml(condition)}</span>
    <span class="bujo-weather-detail">H ${hi}${escapeHtml(unit)} · L ${lo}${escapeHtml(unit)}</span>
  </div>`;
}

function renderQuoteBlock(quote) {
  if (!quote?.text) return "";
  const label = quote.tradition_label || quote.tradition || "";
  return `<blockquote class="bujo-quote">
    <p class="bujo-quote-text">${escapeHtml(quote.text)}</p>
    <footer class="bujo-quote-meta">— ${escapeHtml(quote.author || "")}${label ? ` · <span class="bujo-quote-tradition">${escapeHtml(label)}</span>` : ""}</footer>
  </blockquote>`;
}

function renderEnrichments(data, day) {
  const inner = [
    renderQuoteBlock(data.quote),
    renderWellnessBlock(day, data),
    renderPromptsBlock(day, data.prompts),
    renderPhotosBlock(day, data.photos),
  ].filter(Boolean).join("");
  if (!inner) return "";
  return `<details class="bujo-enrichments" open>
    <summary>Daily enrichments (quotes, wellness, photos, prompts)</summary>
    ${inner}
  </details>`;
}

function renderTimelineBlock(timeline) {
  const events = timeline?.events || [];
  if (!events.length) return "";
  const rows = events.map((e) =>
    `<li class="bujo-timeline-item" data-id="${escapeHtml(e.id || "")}">
      <span class="bujo-timeline-time">${escapeHtml(e.time || "")}</span>
      <span class="bujo-timeline-body">${escapeHtml(e.content || "")}</span>
    </li>`
  ).join("");
  return `<section class="bujo-timeline" aria-label="Day schedule">
    <h4>Timeline</h4>
    <ol class="bujo-timeline-list">${rows}</ol>
  </section>`;
}

function renderPromptsBlock(day, prompts) {
  if (!prompts) return "";
  return `<div class="bujo-prompts" data-day="${escapeHtml(day)}">
    <div class="bujo-prompt">
      <label>Morning · ${escapeHtml(prompts.morning_question || "")}</label>
      <textarea id="bujoMorning" rows="2" placeholder="Morning reflection…">${escapeHtml(prompts.morning || "")}</textarea>
    </div>
    <div class="bujo-prompt">
      <label>Evening · ${escapeHtml(prompts.evening_question || "")}</label>
      <textarea id="bujoEvening" rows="2" placeholder="Evening reflection…">${escapeHtml(prompts.evening || "")}</textarea>
    </div>
    <button type="button" id="bujoSavePrompts" class="ghost-btn small">Save reflections</button>
  </div>`;
}

function renderPhotosBlock(day, photos) {
  const items = (photos || []).map((p) => `
    <figure class="bujo-photo" data-id="${escapeHtml(p.id)}">
      <img src="/api/journal/photos/${encodeURIComponent(p.filename)}" alt="${escapeHtml(p.caption || "Day photo")}" loading="lazy" />
      ${p.caption ? `<figcaption>${escapeHtml(p.caption)}</figcaption>` : ""}
      <button type="button" class="bujo-act bujo-photo-del" data-id="${escapeHtml(p.id)}" title="Remove photo">✕</button>
    </figure>`).join("");
  return `<div class="bujo-photos" data-day="${escapeHtml(day)}">
    <h4>Photos</h4>
    <div class="bujo-photo-grid">${items || '<p class="bujo-empty">No photos yet.</p>'}</div>
    <div class="bujo-photo-add">
      <input type="file" id="bujoPhotoFile" accept="image/*" />
      <input type="text" id="bujoPhotoCaption" placeholder="Caption (optional)" />
      <button type="button" id="bujoPhotoBtn" class="ghost-btn small">Add photo</button>
    </div>
  </div>`;
}

function renderWellnessBlock(day, data) {
  const mood = data.mood || "";
  const gratitude = (data.gratitude || []).map((g) => `<li>${escapeHtml(g)}</li>`).join("");
  return `<div class="bujo-wellness" data-day="${escapeHtml(day)}">
    <h4>Gratitude &amp; mood</h4>
    <div class="bujo-mood-row">
      <label>Mood</label>
      ${[1, 2, 3, 4, 5].map((n) =>
        `<button type="button" class="bujo-mood-btn${mood === n ? " on" : ""}" data-mood="${n}">${n}</button>`
      ).join("")}
    </div>
    <ul class="bujo-gratitude-list">${gratitude || '<li class="bujo-empty">No gratitude lines yet.</li>'}</ul>
    <div class="bujo-gratitude-add">
      <span class="bujo-gratitude-prefix">${escapeHtml(GRATITUDE_PREFIX)}</span>
      <input type="text" id="bujoGratitudeInput" placeholder="sunshine, coffee, a good walk…" aria-label="Gratitude completion" />
      <button type="button" id="bujoGratitudeBtn" class="ghost-btn small">Add</button>
    </div>
  </div>`;
}

function renderDayPage(data, day, { showBack = false, showThread = false, timeline = null } = {}) {
  const header = showBack
    ? `<div class="bujo-day-header">
        <button type="button" id="bujoBackMonth" class="ghost-btn small">← Back to calendar</button>
        <h3>${escapeHtml(data.title || day)} ${pageNumLabel(data)}</h3>
      </div>`
    : `<h3>${escapeHtml(data.title || day)} ${pageNumLabel(data)}</h3>`;
  const weatherBlock = renderWeatherBlock(data.weather);
  return `${header}
    ${weatherBlock}
    ${renderTimelineBlock(timeline)}
    ${renderEnrichments(data, day)}
    <p class="bujo-drag-hint">Drag open tasks onto calendar days · ↳ nest · &lt; schedule · 🔗 link · ↓ thread · Rapid log: indent 2 spaces to nest</p>
    ${addRowHtml()}
    ${renderBullets(data.bullets, true, 0, showThread)}`;
}

function pageNumLabel(data) {
  return data?.page_number ? `<span class="bujo-pagenum">p.${data.page_number}</span>` : "";
}

function renderBulletMenu(b, showThread = false) {
  const sigs = b.signifiers || [];
  const openTask = b.type === "task" && b.status === "open";
  const items = [];
  if (openTask) {
    items.push(`<button type="button" class="bujo-act" data-act="schedule" data-id="${b.id}" title="Schedule to future log">&lt; schedule</button>`);
  }
  if (showThread && b.type === "task") {
    items.push(`<button type="button" class="bujo-act" data-act="thread" data-id="${b.id}" title="Migrate to daily log">↓ thread</button>`);
    items.push(`<button type="button" class="bujo-act" data-act="thread-dup" data-id="${b.id}" title="Copy to daily log">↓ copy</button>`);
  }
  if (openTask) {
    items.push(`<button type="button" class="bujo-act" data-act="cancel" data-id="${b.id}" title="Cancel">~ cancel</button>`);
  }
  if (b.type === "event") {
    items.push(`<button type="button" class="bujo-act" data-act="time" data-id="${b.id}" title="Set time">🕐 time</button>`);
  }
  items.push(`<button type="button" class="bujo-act" data-act="nest" data-id="${b.id}" title="Add sub-bullet">↳ nest</button>`);
  items.push(`<button type="button" class="bujo-act" data-act="link" data-id="${b.id}" title="Link to bullet">🔗 link</button>`);
  items.push(`<button type="button" class="bujo-act${sigs.includes("important") ? " on" : ""}" data-act="sig" data-sig="important" data-id="${b.id}" title="Important">* important</button>`);
  items.push(`<button type="button" class="bujo-act${sigs.includes("inspiration") ? " on" : ""}" data-act="sig" data-sig="inspiration" data-id="${b.id}" title="Inspiration">! inspiration</button>`);
  items.push(`<button type="button" class="bujo-act${sigs.includes("explore") ? " on" : ""}" data-act="sig" data-sig="explore" data-id="${b.id}" title="Explore">👁 explore</button>`);
  items.push(`<button type="button" class="bujo-act" data-act="remember" data-id="${b.id}" title="Save to memory">★ remember</button>`);
  items.push(`<button type="button" class="bujo-act" data-act="del" data-id="${b.id}" title="Delete">✕ delete</button>`);
  return `<details class="bujo-menu">
    <summary class="bujo-act bujo-menu-toggle" title="More actions">⋯</summary>
    <div class="bujo-menu-panel">${items.join("")}</div>
  </details>`;
}

function renderBulletItem(b, editable, showThread = false) {
  const draggable = editable && b.type === "task" && b.status === "open";
  const timeTag = b.time ? `<span class="bujo-time">${escapeHtml(b.time)}</span> ` : "";
  const links = (b.links || []).map((l) =>
    `<button type="button" class="bujo-link" data-link="${escapeHtml(l.bullet_id)}">${escapeHtml(l.label || "link")}</button>`
  ).join(" ");
  const childHtml = b.children?.length ? renderBullets(b.children, editable, 1, showThread) : "";
  const openTask = b.type === "task" && b.status === "open";
  return `
    <li class="bujo-item" data-id="${b.id}" ${draggable ? 'draggable="true"' : ""}>
      <span class="bujo-sym">${sym(b)}${sigPrefix(b)}</span>
      <span class="bujo-text${bulletTextClass(b)}" data-editable="${editable ? "1" : "0"}">${timeTag}${escapeHtml(b.content)}</span>
      ${links ? `<span class="bujo-links">${links}</span>` : ""}
      ${editable ? `<span class="bujo-actions">
        ${openTask ? `<button type="button" class="bujo-act" data-act="done" data-id="${b.id}" title="Complete">×</button>` : ""}
        ${openTask ? `<button type="button" class="bujo-act" data-act="migrate" data-id="${b.id}" title="Migrate to tomorrow">›</button>` : ""}
        ${renderBulletMenu(b, showThread)}
      </span>` : ""}
      ${childHtml}
    </li>`;
}

function renderBullets(bullets, editable = true, depth = 0, showThread = false) {
  if (!bullets?.length) {
    if (depth === 0) {
      return '<p class="bujo-empty">No entries yet. Start rapid log: type below and press <kbd>Enter</kbd>.</p>';
    }
    return "";
  }
  const items = bullets.map((b) => renderBulletItem(b, editable, showThread)).join("");
  if (depth === 0) return `<ul class="bujo-list">${items}</ul>`;
  return `<ul class="bujo-list bujo-nested">${items}</ul>`;
}

async function loadJournalStats() {
  if (!journalStats) return;
  try {
    const res = await fetch("/api/journal/stats");
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || data.detail || `Stats failed (${res.status})`);
    const s = data.stats || {};
    journalStats.textContent =
      `${s.open_tasks || 0} open tasks · ${s.daily_pages || 0} daily · ${s.weekly_pages || 0} weekly · ${s.habits || 0} habits · ${s.collections || 0} collections`;
  } catch (err) {
    journalStats.textContent = "Journal stats unavailable";
    window.showAriaToast?.(err?.message || "Journal stats unavailable", "err", 4000);
  }
}

async function postDaily(content, bulletType, day) {
  const form = new FormData();
  form.append("content", content);
  form.append("bullet_type", bulletType);
  if (day) form.append("day", day);
  return journalPost("/api/journal/daily", { method: "POST", body: form });
}

async function postWeekly(content, bulletType, week) {
  const form = new FormData();
  form.append("content", content);
  form.append("bullet_type", bulletType);
  if (week) form.append("week", week);
  await fetch("/api/journal/weekly", { method: "POST", body: form });
}

async function postMonthly(content, bulletType, month) {
  const form = new FormData();
  form.append("content", content);
  form.append("bullet_type", bulletType);
  if (month) form.append("month", month);
  await fetch("/api/journal/monthly", { method: "POST", body: form });
}

async function postFuture(content, bulletType, month) {
  const form = new FormData();
  form.append("month", month);
  form.append("content", content);
  form.append("bullet_type", bulletType);
  const out = await journalPost("/api/journal/future", { method: "POST", body: form });
  return out.body || {};
}

async function postCollection(name, content, bulletType) {
  const form = new FormData();
  form.append("content", content);
  form.append("bullet_type", bulletType);
  await fetch(`/api/journal/collections/${encodeURIComponent(name)}/add`, { method: "POST", body: form });
}

function bindWellnessExtras(day) {
  bujoContent?.querySelectorAll(".bujo-mood-btn").forEach((btn) => {
    btn.onclick = async () => {
      const form = new FormData();
      form.append("day", day);
      form.append("mood", btn.dataset.mood);
      await fetch("/api/journal/wellness", { method: "POST", body: form });
      refreshBujo();
    };
  });
  document.getElementById("bujoGratitudeBtn")?.addEventListener("click", async () => {
    const input = document.getElementById("bujoGratitudeInput");
    const suffix = input?.value.trim();
    if (!suffix) return;
    const text = GRATITUDE_PREFIX + suffix.replace(/^i am grateful for\s+/i, "");
    const form = new FormData();
    form.append("day", day);
    form.append("text", text);
    await fetch("/api/journal/gratitude", { method: "POST", body: form });
    if (input) {
      input.value = "";
      input.focus();
    }
    refreshBujo();
  });
  document.getElementById("bujoGratitudeInput")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("bujoGratitudeBtn")?.click();
  });
}

function bindLinkClicks() {
  bujoContent?.querySelectorAll(".bujo-link").forEach((btn) => {
    btn.onclick = async () => {
      const res = await fetch(`/api/journal/bullet/${btn.dataset.link}/resolve`);
      const data = await res.json();
      if (data.ok && data.bullet?.location) {
        navigateBujoPage(data.bullet.location);
      } else if (data.ok) {
        alert(data.bullet?.formatted || data.bullet?.content || "Linked bullet");
      }
    };
  });
}

function bindDayExtras(day) {
  bindWellnessExtras(day);
  document.getElementById("bujoSavePrompts")?.addEventListener("click", async () => {
    const form = new FormData();
    form.append("day", day);
    form.append("morning", document.getElementById("bujoMorning")?.value || "");
    form.append("evening", document.getElementById("bujoEvening")?.value || "");
    await fetch("/api/journal/daily/prompts", { method: "POST", body: form });
  });

  document.getElementById("bujoPhotoBtn")?.addEventListener("click", async () => {
    const fileInput = document.getElementById("bujoPhotoFile");
    const file = fileInput?.files?.[0];
    if (!file) {
      alert("Choose an image first");
      return;
    }
    const form = new FormData();
    form.append("day", day);
    form.append("caption", document.getElementById("bujoPhotoCaption")?.value || "");
    form.append("file", file);
    await fetch("/api/journal/daily/photo", { method: "POST", body: form });
    fileInput.value = "";
    refreshBujo();
  });

  bujoContent?.querySelectorAll(".bujo-photo-del").forEach((btn) => {
    btn.onclick = async () => {
      await fetch(`/api/journal/daily/${day}/photo/${btn.dataset.id}`, { method: "DELETE" });
      refreshBujo();
    };
  });

  bindBulletDrag();
  bindLinkClicks();
}

function bindBulletDrag() {
  bujoContent?.querySelectorAll(".bujo-item[draggable='true']").forEach((item) => {
    item.addEventListener("dragstart", (e) => {
      dragBulletId = item.dataset.id;
      e.dataTransfer?.setData("text/plain", dragBulletId);
      item.classList.add("dragging");
    });
    item.addEventListener("dragend", () => {
      dragBulletId = null;
      item.classList.remove("dragging");
    });
  });
}

function bindCalendarDrop(month) {
  bujoContent?.querySelectorAll(".bujo-cal-day[data-date]").forEach((cell) => {
    cell.addEventListener("dragover", (e) => {
      e.preventDefault();
      cell.classList.add("drop-target");
    });
    cell.addEventListener("dragleave", () => cell.classList.remove("drop-target"));
    cell.addEventListener("drop", async (e) => {
      e.preventDefault();
      cell.classList.remove("drop-target");
      const id = e.dataTransfer?.getData("text/plain") || dragBulletId;
      if (!id) return;
      const form = new FormData();
      form.append("target", cell.dataset.date);
      await fetch(`/api/journal/bullet/${id}/migrate`, { method: "POST", body: form });
      monthlySelectedDay = cell.dataset.date;
      refreshBujo();
    });
    cell.addEventListener("dblclick", (e) => {
      e.stopPropagation();
      editCalendarNote(month, cell.dataset.date, cell);
    });
  });
}

async function editCalendarNote(month, dateStr, cell) {
  closeCalendarNotePanel();
  const dayNum = parseInt(dateStr.split("-")[2], 10);
  const existing = cell.querySelector(".bujo-cal-note")?.textContent?.replace(/…$/, "") || "";
  const panel = document.createElement("div");
  panel.className = "bujo-cal-note-panel";
  panel.innerHTML = `
    <input type="text" class="bujo-cal-note-input" value="${escapeHtml(existing)}" placeholder="Calendar note…" />
    <button type="button" class="ghost-btn small bujo-cal-note-save">Save</button>
    <button type="button" class="ghost-btn small bujo-cal-note-cancel">Cancel</button>`;
  cell.appendChild(panel);
  const input = panel.querySelector(".bujo-cal-note-input");
  input?.focus();
  input?.select();
  panel.querySelector(".bujo-cal-note-cancel")?.addEventListener("click", (e) => {
    e.stopPropagation();
    panel.remove();
  });
  panel.querySelector(".bujo-cal-note-save")?.addEventListener("click", async (e) => {
    e.stopPropagation();
    const form = new FormData();
    form.append("day", String(dayNum));
    form.append("note", input?.value.trim() || "");
    form.append("month", month);
    await fetch("/api/journal/monthly/calendar-note", { method: "POST", body: form });
    panel.remove();
    refreshBujo();
  });
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") panel.querySelector(".bujo-cal-note-save")?.click();
    if (e.key === "Escape") panel.remove();
  });
}

function closeCalendarNotePanel() {
  bujoContent?.querySelectorAll(".bujo-cal-note-panel").forEach((p) => p.remove());
}

function bindAddRow() {
  const btn = document.getElementById("bujoAddBtn");
  if (!btn || btn.dataset.bound === "1") return;
  btn.dataset.bound = "1";
  btn.addEventListener("click", async () => {
    const content = document.getElementById("bujoAddContent")?.value.trim();
    const bulletType = document.getElementById("bujoAddType")?.value || "task";
    if (!content) return;
    if (currentBujo === "daily") {
      await postDaily(content, bulletType, journalDate?.value);
    } else if (currentBujo === "weekly") {
      await postWeekly(content, bulletType, journalWeek?.value);
    } else if (currentBujo === "monthly" && monthlySelectedDay) {
      await postDaily(content, bulletType, monthlySelectedDay);
      await openMonthlyDay(monthlySelectedDay);
      return;
    } else if (currentBujo === "monthly") {
      await postMonthly(content, bulletType, journalMonth?.value);
    } else if (currentBujo === "future") {
      const month = futureMonthValue();
      const data = await postFuture(content, bulletType, month);
      if (!data?.ok) {
        alert(data?.message || "Could not add to future log");
        return;
      }
    } else if (currentBujo === "collections") {
      const name = document.getElementById("colActive")?.value;
      if (!name) {
        alert("Select or create a collection first");
        return;
      }
      await postCollection(name, content, bulletType);
    }
    const input = document.getElementById("bujoAddContent");
    if (input) input.value = "";
    journalNotify("Entry saved", false);
    refreshBujo();
  });
}

async function loadDaily() {
  showBujoLoading();
  const day = journalDate?.value || new Date().toISOString().slice(0, 10);
  const [dayRes, timelineRes] = await Promise.all([
    fetch(`/api/journal/daily?day=${day}`),
    fetch(`/api/journal/daily/timeline?day=${day}`),
  ]);
  const data = await dayRes.json();
  const timeline = await timelineRes.json();
  bujoContent.innerHTML = `
    <div class="bujo-daily-tools">
      <button type="button" id="bujoMigrateOpen" class="ghost-btn small" title="BuJo: move open tasks to tomorrow">Migrate open → tomorrow</button>
    </div>
    ${renderDayPage(data, day, { timeline })}`;
  document.getElementById("bujoMigrateOpen")?.addEventListener("click", async () => {
    const form = new FormData();
    form.append("from_day", day);
    const res = await fetch("/api/journal/migrate-daily", { method: "POST", body: form });
    const r = await res.json();
    journalNotify(`Moved ${r.migrated || 0} open tasks to ${r.to_day}`, false);
    refreshBujo();
  });
  bindAddRow();
  bindBulletActions();
  bindDayExtras(day);
}

function renderCalendarHolidayLegend(holidays) {
  const entries = Object.entries(holidays || {}).sort(([a], [b]) => a.localeCompare(b));
  if (!entries.length) return "";
  const chips = entries.map(([dateStr, list]) => {
    const dayNum = parseInt(dateStr.slice(8), 10);
    const names = list.map((h) => h.name).join(", ");
    return `<span class="bujo-cal-holiday-chip"><strong>${dayNum}</strong> ${escapeHtml(names)}</span>`;
  }).join("");
  return `<div class="bujo-cal-holidays-legend" aria-label="Holidays this month">${chips}</div>`;
}

function renderCalendarGrid(data, month) {
  const weeks = data.weeks || [];
  const dayMap = data.days || {};
  const notes = data.calendar_notes || {};
  const events = data.events || {};
  const holidays = data.holidays || {};
  const today = data.today || new Date().toISOString().slice(0, 10);
  let grid = `<div class="bujo-cal-grid"><div class="bujo-cal-head">${WEEKDAYS.map((d) =>
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
      const isSelected = dateStr === monthlySelectedDay;
      const note = notes[String(dayNum)] || "";
      const dayEvents = (events[dateStr] || []).slice(0, 2).map((e) =>
        `<span class="bujo-cal-event">${escapeHtml(e.time || "")} ${escapeHtml(e.content.slice(0, 12))}</span>`
      ).join("");
      const dayHolidays = (holidays[dateStr] || []).slice(0, 2).map((h) =>
        `<span class="bujo-cal-holiday" title="${escapeHtml(h.name)}">★ ${escapeHtml(h.name.slice(0, 11))}${h.name.length > 11 ? "…" : ""}</span>`
      ).join("");
      const dots = info.count
        ? `<span class="bujo-cal-dots" title="${info.count} entries">${info.open_tasks ? "•" : "·"}</span>`
        : "";
      grid += `<button type="button" class="bujo-cal-day${isToday ? " today" : ""}${info.count ? " has-entries" : ""}${isSelected ? " selected" : ""}${dayHolidays ? " has-holiday" : ""}"
        data-date="${dateStr}" aria-label="Open ${dateStr}">
        <span class="bujo-cal-num">${dayNum}</span>
        ${dayHolidays}
        ${dayEvents}
        ${note ? `<span class="bujo-cal-note">${escapeHtml(note.slice(0, 28))}${note.length > 28 ? "…" : ""}</span>` : ""}
        ${dots}
      </button>`;
    });
    grid += "</div>";
  });
  grid += "</div>";
  return grid;
}

async function loadMonthlyReview(month) {
  const res = await fetch(`/api/journal/monthly/review?month=${month}`);
  const data = await res.json();
  const items = (data.checklist || []).map((item) => {
    const done = data.review?.[item.id];
    return `<label class="bujo-review-item${done ? " done" : ""}">
      <input type="checkbox" data-review-id="${escapeHtml(item.id)}" ${done ? "checked" : ""} />
      ${escapeHtml(item.label)}
    </label>`;
  }).join("");
  return `<div class="bujo-review">
    <h4>End-of-month review ${pageNumLabel({ page_number: data.page_number })}</h4>
    <div class="bujo-review-list">${items}</div>
    <textarea id="bujoReviewNotes" rows="3" placeholder="Review notes…">${escapeHtml(data.review_notes || "")}</textarea>
    <div class="bujo-review-actions">
      <button type="button" id="bujoReviewSave" class="ghost-btn small">Save review notes</button>
      <button type="button" id="bujoReviewAi" class="ghost-btn small">AI review summary</button>
    </div>
  </div>`;
}

async function loadMonthly() {
  showBujoLoading();
  const month = journalMonth?.value || new Date().toISOString().slice(0, 7);
  const res = await fetch(`/api/journal/monthly/calendar?month=${month}`);
  const data = await res.json();
  const grid = renderCalendarGrid(data, month);
  const reviewHtml = await loadMonthlyReview(month);

  let dayPanel = "";
  if (monthlySelectedDay) {
    const [dayRes, timelineRes] = await Promise.all([
      fetch(`/api/journal/daily?day=${monthlySelectedDay}`),
      fetch(`/api/journal/daily/timeline?day=${monthlySelectedDay}`),
    ]);
    const dayData = await dayRes.json();
    const timeline = await timelineRes.json();
    dayPanel = `<div class="bujo-day-panel">${renderDayPage(dayData, monthlySelectedDay, { showBack: true, showThread: false, timeline })}</div>`;
  }

  bujoContent.innerHTML = `
    <h3>${escapeHtml(data.title || month)} ${pageNumLabel(data)}</h3>
    <div class="bujo-daily-tools">
      <button type="button" id="bujoMigrateMonthIncomplete" class="ghost-btn small" title="BuJo: migrate open monthly tasks to next month">Migrate incomplete → next month</button>
    </div>
    <p class="bujo-cal-hint">Click a day · <span class="bujo-cal-holiday-inline">★ holidays</span> on cells · double-click for calendar note · drop tasks</p>
    ${grid}
    ${renderCalendarHolidayLegend(data.holidays)}
    ${reviewHtml}
    ${dayPanel || `<h4 class="bujo-month-section">Month overview</h4>${addRowHtml()}${renderBullets(data.monthly_bullets || [], true, 0, true)}`}`;

  bindAddRow();
  bindBulletActions();
  bindCalendarDrop(month);
  if (monthlySelectedDay) bindDayExtras(monthlySelectedDay);
  bindLinkClicks();

  bujoContent.querySelectorAll(".bujo-review-item input").forEach((cb) => {
    cb.onchange = async () => {
      const form = new FormData();
      form.append("item_id", cb.dataset.reviewId);
      form.append("month", month);
      await fetch("/api/journal/monthly/review/toggle", { method: "POST", body: form });
      loadMonthly();
    };
  });
  document.getElementById("bujoReviewSave")?.addEventListener("click", async () => {
    const form = new FormData();
    form.append("notes", document.getElementById("bujoReviewNotes")?.value || "");
    form.append("month", month);
    await fetch("/api/journal/monthly/review/notes", { method: "POST", body: form });
  });
  document.getElementById("bujoReviewAi")?.addEventListener("click", async () => {
    const form = new FormData();
    form.append("scope", "month");
    form.append("month", month);
    const res = await fetch("/api/journal/reflect/review", { method: "POST", body: form });
    const data = await res.json();
    alert(data.reflection || "No reflection generated.");
  });

  document.getElementById("bujoMigrateMonthIncomplete")?.addEventListener("click", async () => {
    const [y, m] = month.split("-").map(Number);
    const nm = m === 12 ? `${y + 1}-01` : `${y}-${String(m + 1).padStart(2, "0")}`;
    const dest = document.getElementById("journalMigrateDest")?.value || "monthly";
    const form = new FormData();
    form.append("from_month", month);
    form.append("to_month", nm);
    form.append("dest", dest);
    const res = await fetch("/api/journal/migrate-month", { method: "POST", body: form });
    const r = await res.json();
    journalNotify(`Migrated ${r.migrated || 0} open tasks to ${nm}`, false);
    refreshBujo();
  });

  bujoContent.querySelectorAll(".bujo-cal-day[data-date]").forEach((btn) => {
    btn.onclick = () => {
      monthlySelectedDay = btn.dataset.date;
      loadMonthly();
    };
  });
  document.getElementById("bujoBackMonth")?.addEventListener("click", () => {
    monthlySelectedDay = null;
    loadMonthly();
  });
}

async function openMonthlyDay(dateStr) {
  monthlySelectedDay = dateStr;
  await loadMonthly();
}

async function loadWeeklyReview(week) {
  const res = await fetch(`/api/journal/weekly/review?week=${encodeURIComponent(week)}`);
  const data = await res.json();
  const items = (data.checklist || []).map((item) => {
    const done = data.review?.[item.id];
    return `<label class="bujo-review-item${done ? " done" : ""}">
      <input type="checkbox" data-week-review-id="${escapeHtml(item.id)}" ${done ? "checked" : ""} />
      ${escapeHtml(item.label)}
    </label>`;
  }).join("");
  return `<div class="bujo-review">
    <h4>Weekly review ${pageNumLabel({ page_number: data.page_number })}</h4>
    <div class="bujo-review-list">${items}</div>
    <textarea id="bujoWeeklyReviewNotes" rows="3" placeholder="Weekly review notes…">${escapeHtml(data.review_notes || "")}</textarea>
    <div class="bujo-review-actions">
      <button type="button" id="bujoWeeklyReviewSave" class="ghost-btn small">Save review notes</button>
      <button type="button" id="bujoWeeklyReviewAi" class="ghost-btn small">AI review summary</button>
    </div>
  </div>`;
}

async function loadWeekly() {
  showBujoLoading();
  const week = journalWeek?.value || isoWeekValue();
  const res = await fetch(`/api/journal/weekly?week=${encodeURIComponent(week)}`);
  const data = await res.json();
  const reviewHtml = await loadWeeklyReview(week);
  bujoContent.innerHTML = `
    <h3>${escapeHtml(data.title || week)} ${pageNumLabel(data)}</h3>
    <p class="bujo-cal-hint">Weekly spread — tasks and events for this ISO week.</p>
    ${reviewHtml}
    ${addRowHtml()}
    ${renderBullets(data.bullets, true, 0, true)}`;
  bindAddRow();
  bindBulletActions();
  bindLinkClicks();

  bujoContent.querySelectorAll("[data-week-review-id]").forEach((cb) => {
    cb.onchange = async () => {
      const form = new FormData();
      form.append("item_id", cb.dataset.weekReviewId);
      form.append("week", week);
      await fetch("/api/journal/weekly/review/toggle", { method: "POST", body: form });
      loadWeekly();
    };
  });
  document.getElementById("bujoWeeklyReviewSave")?.addEventListener("click", async () => {
    const form = new FormData();
    form.append("notes", document.getElementById("bujoWeeklyReviewNotes")?.value || "");
    form.append("week", week);
    await fetch("/api/journal/weekly/review/notes", { method: "POST", body: form });
  });
  document.getElementById("bujoWeeklyReviewAi")?.addEventListener("click", async () => {
    const form = new FormData();
    form.append("scope", "week");
    form.append("week", week);
    const res = await fetch("/api/journal/reflect/review", { method: "POST", body: form });
    const data = await res.json();
    alert(data.reflection || "No reflection generated.");
  });
}

async function loadHabits() {
  showBujoLoading();
  const month = journalMonth?.value || new Date().toISOString().slice(0, 7);
  const res = await fetch(`/api/journal/habits?month=${month}`);
  const data = await res.json();
  const days = data.days || [];
  const habits = data.habits || [];

  let table = `<table class="bujo-habit-grid"><thead><tr><th>Habit</th>`;
  days.forEach((d) => {
    const num = d.split("-")[2];
    table += `<th>${parseInt(num, 10)}</th>`;
  });
  table += `<th>Done</th><th>Streak</th></tr></thead><tbody>`;
  habits.forEach((h) => {
    table += `<tr><td>${escapeHtml(h.name)}</td>`;
    days.forEach((d) => {
      const on = h.days?.[d];
      table += `<td><button type="button" class="bujo-habit-cell${on ? " on" : ""}" data-hid="${escapeHtml(h.id)}" data-day="${d}" aria-label="Toggle ${h.name} on ${d}">${on ? "●" : "○"}</button></td>`;
    });
    table += `<td class="bujo-habit-count">${h.done_count || 0}</td>`;
    table += `<td class="bujo-habit-streak" title="Consecutive days through today">${h.streak || 0}🔥</td></tr>`;
  });
  table += "</tbody></table>";

  bujoContent.innerHTML = `
    <h3>Habit tracker · ${escapeHtml(month)}</h3>
    <p class="bujo-cal-hint">Tap a cell to mark done · scroll horizontally on small screens</p>
    <div class="bujo-habit-scroll">${table}</div>
    <div class="bujo-add-index">
      <input type="text" id="habitName" placeholder="New habit name" />
      <button type="button" id="habitAddBtn" class="apply-btn small">Add habit</button>
    </div>`;

  bujoContent.querySelectorAll(".bujo-habit-cell").forEach((btn) => {
    btn.onclick = async () => {
      const form = new FormData();
      form.append("day", btn.dataset.day);
      await fetch(`/api/journal/habits/${btn.dataset.hid}/toggle`, { method: "POST", body: form });
      loadHabits();
    };
  });
  document.getElementById("habitAddBtn")?.addEventListener("click", async () => {
    const name = document.getElementById("habitName")?.value.trim();
    if (!name) return;
    const form = new FormData();
    form.append("name", name);
    await fetch("/api/journal/habits", { method: "POST", body: form });
    loadHabits();
  });
}

async function loadFuture() {
  showBujoLoading();
  const res = await fetch("/api/journal/future");
  const data = await res.json();
  const targetMonth = futureMonthValue();
  const monthLabel = formatMonthLabel(targetMonth);
  let html = `<h3>Future Log</h3>
    <div class="bujo-future-intro">
      <p><strong>Adding to ${escapeHtml(monthLabel)}</strong> — change the <em>month picker in the toolbar above</em> to schedule a different month.</p>
      <p class="bujo-cal-hint">Or schedule an open task from Daily/Monthly: ⋯ menu → <strong>&lt; schedule</strong>. Move items into the current month with <strong>Transfer open → this month</strong> below.</p>
    </div>
    <div class="bujo-add-row">
      <select id="bujoAddType"><option value="task">• Task</option><option value="event">○ Event</option><option value="note">— Note</option></select>
      <input type="text" id="bujoAddContent" placeholder="Task, event, or note for ${escapeHtml(monthLabel)}…" />
      <button type="button" id="bujoAddBtn" class="apply-btn small">Add to ${escapeHtml(monthLabel)}</button>
    </div>
    <div class="bujo-add-index">
      <label>Transfer open tasks from
        <input type="month" id="futureTransferFrom" value="${targetMonth}" />
      </label>
      <span>→</span>
      <label>into monthly log
        <input type="month" id="futureTransferTo" value="${new Date().toISOString().slice(0, 7)}" />
      </label>
      <button type="button" id="futureTransferBtn" class="ghost-btn small">Transfer open</button>
    </div>`;
  const months = Object.keys(data).filter((m) => (data[m] || []).length > 0).sort();
  if (!months.length) {
    html += `<p class="bujo-empty">Nothing scheduled yet. Use the form above or the rapid log at the bottom of this page.</p>`;
  }
  months.forEach((m) => {
    html += `<h4>${escapeHtml(formatMonthLabel(m))} <span class="bujo-month-key">${escapeHtml(m)}</span></h4>${renderBullets(data[m], true, 0, true)}`;
  });
  bujoContent.innerHTML = html;
  bindAddRow();
  bindBulletActions();
  bindLinkClicks();
  document.getElementById("futureTransferBtn")?.addEventListener("click", async () => {
    const fm = document.getElementById("futureTransferFrom")?.value;
    const mm = document.getElementById("futureTransferTo")?.value || new Date().toISOString().slice(0, 7);
    if (!fm) {
      alert("Pick the future month to transfer from");
      return;
    }
    const form = new FormData();
    form.append("future_month", fm);
    form.append("monthly_month", mm);
    const res = await fetch("/api/journal/future/transfer", { method: "POST", body: form });
    const r = await res.json();
    alert(`Transferred ${r.migrated || 0} open task(s) to ${formatMonthLabel(mm)}`);
    refreshBujo();
  });
  updateRapidLogForTab();
}

async function loadIndex() {
  showBujoLoading();
  const res = await fetch("/api/journal/index");
  const data = await res.json();
  const rows = (data.entries || []).map((e) => {
    const pages = (e.pages || []).map((p) =>
      `<button type="button" class="bujo-index-link" data-page="${escapeHtml(p)}">${escapeHtml(p)}</button>`
    ).join(", ");
    const auto = e.auto ? '<span class="bujo-index-auto">auto</span>' : "";
    return `<tr><td>${escapeHtml(e.topic)} ${auto}</td><td>${pages || "—"}</td>
     <td><button type="button" class="bujo-act" data-act="idx-del" data-id="${e.id}">✕</button></td></tr>`;
  }).join("");
  bujoContent.innerHTML = `
    <h3>Index</h3>
    <p class="bujo-cal-hint">Auto-index tracks daily/weekly/monthly pages, collections, and ★/! entries. Click a page link to jump there.</p>
    <div class="bujo-index-tools">
      <button type="button" id="indexRebuildBtn" class="ghost-btn small">Rebuild auto-index</button>
    </div>
    <table class="bujo-index"><thead><tr><th>Topic</th><th>Page</th><th></th></tr></thead><tbody>${rows || '<tr><td colspan="3" class="bujo-empty">Index empty — add topics or write entries.</td></tr>'}</tbody></table>
    <div class="bujo-add-index">
      <input type="text" id="indexTopic" placeholder="Topic (manual)" />
      <input type="text" id="indexPages" placeholder="Pages: daily:2026-06-08, collection:Books" />
      <button type="button" id="indexAddBtn" class="apply-btn small">Add manual</button>
    </div>`;
  document.getElementById("indexRebuildBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/journal/index/rebuild", { method: "POST" });
    const r = await res.json();
    const stats = r.result || {};
    alert(`Auto-index rebuilt: ${stats.auto || 0} auto, ${stats.manual || 0} manual (${stats.total || 0} total)`);
    loadIndex();
  });
  document.getElementById("indexAddBtn")?.addEventListener("click", async () => {
    const topic = document.getElementById("indexTopic")?.value.trim();
    if (!topic) {
      journalNotify("Enter a topic for the index");
      return;
    }
    const form = new FormData();
    form.append("topic", topic);
    form.append("pages", document.getElementById("indexPages")?.value || "");
    await fetch("/api/journal/index", { method: "POST", body: form });
    journalNotify("Index entry added", false);
    loadIndex();
  });
  bujoContent.querySelectorAll(".bujo-index-link").forEach((btn) => {
    btn.onclick = () => navigateBujoPage(btn.dataset.page);
  });
  bujoContent.querySelectorAll("[data-act=idx-del]").forEach((btn) => {
    btn.onclick = async () => {
      await fetch(`/api/journal/index/${btn.dataset.id}`, { method: "DELETE" });
      loadIndex();
    };
  });
}

function navigateBujoPage(pageRef) {
  fetch(`/api/journal/index/resolve?page=${encodeURIComponent(pageRef)}`)
    .then((r) => r.json())
    .then((data) => {
      if (!data.ok || !data.location) return;
      const loc = data.location;
      if (loc.type === "daily") {
        if (journalDate) journalDate.value = loc.day;
        setBujoTab("daily");
      } else if (loc.type === "monthly") {
        if (journalMonth) journalMonth.value = loc.month;
        monthlySelectedDay = null;
        setBujoTab("monthly");
      } else if (loc.type === "weekly") {
        if (journalWeek) journalWeek.value = loc.week;
        setBujoTab("weekly");
      } else if (loc.type === "collection") {
        setBujoTab("collections");
        setTimeout(() => {
          bujoContent?.querySelectorAll("h4").forEach((h) => {
            if (h.textContent.trim() === loc.name) h.scrollIntoView({ behavior: "smooth", block: "start" });
          });
        }, 250);
      } else if (loc.type === "future") {
        if (journalMonth) journalMonth.value = loc.month;
        setBujoTab("future");
      }
    });
}
window.navigateBujoPage = navigateBujoPage;

async function loadCollections() {
  showBujoLoading();
  const res = await fetch("/api/journal/collections");
  const data = await res.json();
  const names = data.names || [];
  const presets = data.presets || [];
  const opts = names.map((n) => `<option value="${escapeHtml(n)}">${escapeHtml(n)}</option>`).join("");

  const presetCards = presets.map((p) => `
    <div class="bujo-preset-card${p.active ? " active" : ""}">
      <span class="bujo-preset-name">${escapeHtml(p.name)}</span>
      <span class="bujo-preset-desc">${escapeHtml(p.description || "")}</span>
      <button type="button" class="ghost-btn small bujo-preset-add" data-id="${escapeHtml(p.id)}" ${p.active ? "disabled" : ""}>
        ${p.active ? "Added" : "Add"}
      </button>
    </div>`).join("");

  let html = `<h3>Collections</h3>
    <div class="bujo-presets">
      <h4>Starter collections</h4>
      <p>Pick templates to turn on — only the ones you add appear below. You can ignore the rest.</p>
      <div class="bujo-preset-grid">${presetCards}</div>
    </div>
    <div class="bujo-custom-col">
      <h4>Custom collection</h4>
      <div class="bujo-add-index">
        <input type="text" id="colName" placeholder="Your collection name" />
        <input type="text" id="colDesc" placeholder="Short description (optional)" />
        <button type="button" id="colCreateBtn" class="apply-btn small">Create</button>
      </div>
    </div>`;

  if (names.length) {
    html += `<div class="bujo-add-row">
      <select id="colActive">${opts}</select>
      <select id="bujoAddType"><option value="task">• Task</option><option value="event">○ Event</option><option value="note">— Note</option></select>
      <input type="text" id="bujoAddContent" placeholder="Add to collection…" />
      <button type="button" id="bujoAddBtn" class="apply-btn small">Add</button>
    </div>`;
  } else {
    html += `<p class="bujo-empty">No collections yet — add a starter above or create your own.</p>`;
  }

  names.forEach((name) => {
    const col = data.data[name];
    const desc = col?.description ? `<p class="bujo-preset-desc">${escapeHtml(col.description)}</p>` : "";
    html += `<h4>${escapeHtml(name)}</h4>${desc}${renderBullets(col?.bullets || [])}`;
  });

  bujoContent.innerHTML = html;
  bindAddRow();
  bindBulletActions();

  bujoContent.querySelectorAll(".bujo-preset-add").forEach((btn) => {
    btn.onclick = async () => {
      const form = new FormData();
      form.append("preset_id", btn.dataset.id);
      await fetch("/api/journal/collections/preset", { method: "POST", body: form });
      loadCollections();
    };
  });

  document.getElementById("colCreateBtn")?.addEventListener("click", async () => {
    const name = document.getElementById("colName")?.value.trim();
    if (!name) {
      alert("Enter a collection name");
      return;
    }
    const form = new FormData();
    form.append("name", name);
    form.append("description", document.getElementById("colDesc")?.value.trim() || "");
    await fetch("/api/journal/collections", { method: "POST", body: form });
    loadCollections();
  });
}

async function loadSearchResults(q) {
  const res = await fetch(`/api/journal/search?q=${encodeURIComponent(q)}`);
  const data = await res.json();
  const hits = data.results || [];
  if (!hits.length) {
    bujoContent.innerHTML = `<h3>Search: ${escapeHtml(q)}</h3><p class="bujo-empty">No matches.</p>`;
    return;
  }
  bujoContent.innerHTML = `<h3>Search: ${escapeHtml(q)}</h3><ul class="bujo-list bujo-search-results">${hits.map((h) =>
    `<li class="bujo-item bujo-search-hit" data-section="${escapeHtml(h.section || "")}" data-id="${escapeHtml(h.id || "")}">
      <span class="bujo-sym">${sym(h)}</span>
      <span class="bujo-text${bulletTextClass(h)}">[${escapeHtml(h.section || "")}] ${escapeHtml(h.content || h.topic || "")}</span>
    </li>`
  ).join("")}</ul>`;
  bujoContent.querySelectorAll(".bujo-search-hit").forEach((row) => {
    row.onclick = () => {
      const sec = row.dataset.section || "";
      if (sec.startsWith("daily:")) {
        if (journalDate) journalDate.value = sec.slice(6);
        setBujoTab("daily");
      } else if (sec.startsWith("monthly:")) {
        if (journalMonth) journalMonth.value = sec.slice(8);
        setBujoTab("monthly");
      } else if (sec.startsWith("weekly:")) {
        if (journalWeek) journalWeek.value = sec.slice(7);
        setBujoTab("weekly");
      } else if (sec.startsWith("collection:")) {
        navigateBujoPage(sec);
      } else if (sec.startsWith("future:")) {
        if (journalMonth) journalMonth.value = sec.slice(7);
        setBujoTab("future");
      }
    };
  });
}

function closeBulletPanels() {
  bujoContent?.querySelectorAll(".bujo-panel").forEach((p) => p.remove());
}

function showBulletPanel(id, kind) {
  closeBulletPanels();
  const item = bujoContent?.querySelector(`.bujo-item[data-id="${id}"]`);
  if (!item) return;
  const defaultMonth = journalMonth?.value || new Date().toISOString().slice(0, 7);
  let html = "";
  if (kind === "schedule") {
    html = `<div class="bujo-panel" data-panel-for="${id}">
      <label>Schedule to month</label>
      <input type="month" class="bujo-panel-month" value="${defaultMonth}" />
      <button type="button" class="ghost-btn small" data-panel-go="schedule">Schedule</button>
      <button type="button" class="ghost-btn small" data-panel-go="cancel">Cancel</button>
    </div>`;
  } else if (kind === "nest") {
    html = `<div class="bujo-panel" data-panel-for="${id}">
      <input type="text" class="bujo-panel-text" placeholder="Sub-bullet text…" />
      <button type="button" class="ghost-btn small" data-panel-go="nest">Add nested</button>
      <button type="button" class="ghost-btn small" data-panel-go="cancel">Cancel</button>
    </div>`;
  } else if (kind === "link") {
    html = `<div class="bujo-panel bujo-panel-wide" data-panel-for="${id}">
      <input type="search" class="bujo-panel-search" placeholder="Search bullets to link…" />
      <ul class="bujo-link-results"></ul>
      <button type="button" class="ghost-btn small" data-panel-go="cancel">Cancel</button>
    </div>`;
  } else if (kind === "time") {
    html = `<div class="bujo-panel" data-panel-for="${id}">
      <label>Event time</label>
      <input type="time" class="bujo-panel-time" value="09:00" />
      <button type="button" class="ghost-btn small" data-panel-go="time">Set time</button>
      <button type="button" class="ghost-btn small" data-panel-go="cancel">Cancel</button>
    </div>`;
  } else if (kind === "edit") {
    const textEl = item.querySelector(".bujo-text");
    html = `<div class="bujo-panel" data-panel-for="${id}">
      <input type="text" class="bujo-panel-text" value="${escapeHtml(textEl?.textContent?.trim() || "")}" />
      <button type="button" class="ghost-btn small" data-panel-go="edit">Save</button>
      <button type="button" class="ghost-btn small" data-panel-go="cancel">Cancel</button>
    </div>`;
  }
  item.insertAdjacentHTML("beforeend", html);
  const panel = item.querySelector(".bujo-panel");
  panel?.querySelectorAll("[data-panel-go]").forEach((btn) => {
    btn.onclick = async () => {
      const go = btn.dataset.panelGo;
      if (go === "cancel") {
        closeBulletPanels();
        return;
      }
      if (go === "schedule") {
        const month = panel.querySelector(".bujo-panel-month")?.value;
        if (!month) return;
        const form = new FormData();
        form.append("month", month);
        await fetch(`/api/journal/bullet/${id}/schedule`, { method: "POST", body: form });
      } else if (go === "nest") {
        const text = panel.querySelector(".bujo-panel-text")?.value.trim();
        if (!text) return;
        const form = new FormData();
        form.append("content", text);
        await fetch(`/api/journal/bullet/${id}/child`, { method: "POST", body: form });
      } else if (go === "time") {
        const t = panel.querySelector(".bujo-panel-time")?.value;
        if (!t) return;
        const form = new FormData();
        form.append("time", t);
        await fetch(`/api/journal/bullet/${id}/time`, { method: "POST", body: form });
      } else if (go === "edit") {
        const text = panel.querySelector(".bujo-panel-text")?.value.trim();
        if (!text) return;
        const form = new FormData();
        form.append("content", text);
        await fetch(`/api/journal/bullet/${id}`, { method: "PATCH", body: form });
      }
      closeBulletPanels();
      refreshBujo();
    };
  });
  const searchInput = panel?.querySelector(".bujo-panel-search");
  if (searchInput) {
    let searchTimer;
    searchInput.oninput = () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(async () => {
        const q = searchInput.value.trim();
        const list = panel.querySelector(".bujo-link-results");
        if (!q || !list) return;
        const res = await fetch(`/api/journal/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        list.innerHTML = (data.results || []).slice(0, 8).map((h) =>
          `<li><button type="button" class="bujo-link-pick" data-to="${escapeHtml(h.id || "")}">
            [${escapeHtml(h.section || "")}] ${escapeHtml(h.content || h.topic || "")}
          </button></li>`
        ).join("") || '<li class="bujo-empty">No matches</li>';
        list.querySelectorAll(".bujo-link-pick").forEach((pick) => {
          pick.onclick = async () => {
            const form = new FormData();
            form.append("to_id", pick.dataset.to);
            form.append("label", "see also");
            await fetch(`/api/journal/bullet/${id}/link`, { method: "POST", body: form });
            closeBulletPanels();
            refreshBujo();
          };
        });
      }, 250);
    };
    searchInput.focus();
  } else {
    panel?.querySelector(".bujo-panel-text")?.focus();
  }
}

function bindBulletActions() {
  bujoContent?.querySelectorAll(".bujo-text[data-editable='1']").forEach((el) => {
    el.onclick = () => {
      const item = el.closest(".bujo-item");
      const id = item?.dataset.id;
      if (!id) return;
      showBulletPanel(id, "edit");
    };
  });
  bujoContent?.querySelectorAll(".bujo-act").forEach((btn) => {
    btn.onclick = async (e) => {
      if (btn.classList.contains("bujo-menu-toggle")) return;
      e.stopPropagation();
      const id = btn.dataset.id, act = btn.dataset.act;
      if (act === "done") await fetch(`/api/journal/bullet/${id}/complete`, { method: "POST" });
      else if (act === "del") await fetch(`/api/journal/bullet/${id}`, { method: "DELETE" });
      else if (act === "remember") {
        const res = await fetch(`/api/journal/bullet/${id}/remember`, { method: "POST" });
        const data = await res.json();
        journalNotify(
          data.ok ? `Saved to memory (${data.namespace})` : (data.error || "Could not save"),
          !data.ok
        );
        return;
      } else if (act === "cancel") await fetch(`/api/journal/bullet/${id}/cancel`, { method: "POST" });
      else if (act === "migrate") {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const form = new FormData();
        form.append("target", tomorrow.toISOString().slice(0, 10));
        await fetch(`/api/journal/bullet/${id}/migrate`, { method: "POST", body: form });
      } else if (act === "sig") {
        const form = new FormData();
        form.append("name", btn.dataset.sig);
        await fetch(`/api/journal/bullet/${id}/signifier`, { method: "POST", body: form });
      } else if (act === "schedule") {
        showBulletPanel(id, "schedule");
        return;
      } else if (act === "thread" || act === "thread-dup") {
        const day = journalDate?.value || new Date().toISOString().slice(0, 10);
        const form = new FormData();
        form.append("day", day);
        form.append("duplicate", act === "thread-dup" ? "true" : "false");
        await fetch(`/api/journal/bullet/${id}/thread`, { method: "POST", body: form });
      } else if (act === "nest") {
        showBulletPanel(id, "nest");
        return;
      } else if (act === "link") {
        showBulletPanel(id, "link");
        return;
      } else if (act === "time") {
        showBulletPanel(id, "time");
        return;
      }
      refreshBujo();
    };
  });
  bindLinkClicks();
}

async function loadWellness() {
  showBujoLoading();
  const month = journalMonth?.value || new Date().toISOString().slice(0, 7);
  const res = await fetch(`/api/journal/wellness?month=${month}`);
  const data = await res.json();
  const moodCells = (data.days || []).map((d) =>
    `<div class="bujo-wellness-day"><span class="bujo-wellness-date">${escapeHtml(d.date.slice(8))}</span>
     <span class="bujo-mood-dot mood-${d.mood || 0}">${d.mood || "·"}</span></div>`
  ).join("");
  const gratitude = (data.gratitude_stream || []).slice().reverse().map((g) =>
    `<li><span class="bujo-grat-date">${escapeHtml(g.date)}</span> ${escapeHtml(g.text)}</li>`
  ).join("");
  bujoContent.innerHTML = `
    <h3>Wellness · ${escapeHtml(month)}</h3>
    <p class="bujo-cal-hint">Mood is set on each Daily page · gratitude stream from all days this month</p>
    <p>Average mood: <strong>${data.mood_average ?? "—"}</strong> · logged ${data.days_logged || 0} days</p>
    <div class="bujo-wellness-grid">${moodCells || '<p class="bujo-empty">No mood logged yet.</p>'}</div>
    <h4>Gratitude stream</h4>
    <ul class="bujo-gratitude-stream">${gratitude || '<li class="bujo-empty">No gratitude entries this month.</li>'}</ul>`;
  bujoContent.querySelectorAll(".bujo-wellness-day").forEach((el, i) => {
    const d = data.days[i];
    if (d) el.onclick = () => { if (journalDate) journalDate.value = d.date; setBujoTab("daily"); };
  });
}

async function loadJournalKey() {
  const el = document.getElementById("bujoKeyDynamic");
  if (!el) return;
  try {
    const res = await fetch("/api/journal/key");
    const key = await res.json();
    const symbols = key.symbols || {};
    const labels = {
      task: "task", event: "event", note: "note",
      task_done: "done", task_migrated: "migrated", task_scheduled: "scheduled",
      task_cancelled: "cancelled", important: "important", inspiration: "inspiration", explore: "explore",
    };
    const items = Object.entries(labels).map(([k, label]) => {
      const symChar = symbols[k] || "";
      if (!symChar) return "";
      return `<span class="bujo-key-item"><span class="bujo-key-sym">${escapeHtml(symChar)}</span> ${label}</span>`;
    }).filter(Boolean);
    (key.custom || []).forEach((c) => {
      if (c.symbol) items.push(`<span class="bujo-key-item"><span class="bujo-key-sym">${escapeHtml(c.symbol)}</span> ${escapeHtml(c.label || "custom")}</span>`);
    });
    el.innerHTML = items.join("") || '<span class="bujo-key-item">Set symbols on Key tab</span>';
  } catch (_) {}
}

async function loadKey() {
  showBujoLoading();
  const res = await fetch("/api/journal/key");
  const key = await res.json();
  const symbols = key.symbols || {};
  const custom = key.custom || [];
  const symRows = Object.entries(symbols).map(([k, v]) =>
    `<tr><td>${escapeHtml(k)}</td><td><input type="text" class="bujo-key-edit" data-sym="${escapeHtml(k)}" value="${escapeHtml(v)}" maxlength="4" /></td></tr>`
  ).join("");
  const customRows = custom.map((c, i) =>
    `<div class="bujo-key-custom"><input type="text" data-custom-sym="${i}" value="${escapeHtml(c.symbol || "")}" maxlength="4" />
     <input type="text" data-custom-label="${i}" value="${escapeHtml(c.label || "")}" /></div>`
  ).join("");
  bujoContent.innerHTML = `
    <h3>Symbol Key</h3>
    <p class="bujo-cal-hint">Customize your BuJo legend — saved to your journal</p>
    <table class="bujo-index">${symRows}</table>
    <label class="bujo-prompt">Legend notes</label>
    <textarea id="bujoKeyDesc" rows="2">${escapeHtml(key.description || "")}</textarea>
    <h4>Custom symbols</h4>
    <div id="bujoKeyCustom">${customRows}</div>
    <button type="button" id="bujoKeyAddCustom" class="ghost-btn small">Add custom symbol</button>
    <button type="button" id="bujoKeySave" class="apply-btn small">Save key</button>`;
  document.getElementById("bujoKeySave")?.addEventListener("click", async () => {
    const sym = {};
    bujoContent.querySelectorAll(".bujo-key-edit").forEach((inp) => { sym[inp.dataset.sym] = inp.value; });
    const customs = [];
    bujoContent.querySelectorAll(".bujo-key-custom").forEach((row) => {
      const s = row.querySelector("[data-custom-sym]")?.value?.trim();
      const l = row.querySelector("[data-custom-label]")?.value?.trim();
      if (s) customs.push({ symbol: s, label: l });
    });
    await fetch("/api/journal/key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols: sym, description: document.getElementById("bujoKeyDesc")?.value, custom: customs }),
    });
    journalNotify("Key saved", false);
    loadJournalKey();
    loadKey();
  });
  document.getElementById("bujoKeyAddCustom")?.addEventListener("click", () => {
    const div = document.createElement("div");
    div.className = "bujo-key-custom";
    div.innerHTML = '<input type="text" data-custom-sym="" maxlength="4" placeholder="sym" /> <input type="text" data-custom-label="" placeholder="meaning" />';
    document.getElementById("bujoKeyCustom")?.appendChild(div);
  });
}

function refreshBujo() {
  loadJournalStats();
  if (currentBujo === "search") {
    const q = journalSearch?.value.trim();
    if (q) loadSearchResults(q);
    return;
  }
  if (currentBujo === "daily") loadDaily();
  else if (currentBujo === "weekly") loadWeekly();
  else if (currentBujo === "monthly") loadMonthly();
  else if (currentBujo === "habits") loadHabits();
  else if (currentBujo === "wellness") loadWellness();
  else if (currentBujo === "future") loadFuture();
  else if (currentBujo === "index") loadIndex();
  else if (currentBujo === "collections") loadCollections();
  else if (currentBujo === "projects") loadProjects();
  else if (currentBujo === "key") loadKey();
}

let projectJournalSlug = null;
let projectJournalDay = null;

async function loadProjects() {
  showBujoLoading();
  const day = projectJournalDay || journalDate?.value || new Date().toISOString().slice(0, 10);
  const res = await fetch("/api/journal/projects");
  const data = await res.json();
  const projects = data.projects || [];

  const listItems = projects.map((p) =>
    `<button type="button" class="bujo-project-row${projectJournalSlug === p.slug ? " active" : ""}" data-slug="${escapeHtml(p.slug)}">
      <span class="bujo-project-title">${escapeHtml(p.title || p.slug)}</span>
      <span class="bujo-project-meta">${p.days || 0} days</span>
    </button>`
  ).join("");

  let detail = '<p class="bujo-empty">Select a project to view its daily log.</p>';
  if (projectJournalSlug) {
    const pageRes = await fetch(`/api/journal/projects/${encodeURIComponent(projectJournalSlug)}?day=${encodeURIComponent(day)}`);
    const pageData = await pageRes.json();
    const page = pageData.page || {};
    detail = `
      <div class="bujo-project-detail">
        <div class="bujo-day-header">
          <h4>${escapeHtml(pageData.project || projectJournalSlug)} · ${escapeHtml(day)}</h4>
          <input type="date" id="projectJournalDay" value="${escapeHtml(day)}" />
        </div>
        ${renderBullets(page.bullets || [], true)}
        ${page.notes ? `<p class="bujo-project-notes"><strong>Notes</strong> ${escapeHtml(page.notes)}</p>` : ""}
        <div class="bujo-add-row">
          <select id="projectLogType"><option value="note">— Note</option><option value="task">• Task</option><option value="event">○ Event</option></select>
          <input type="text" id="projectLogText" placeholder="Quick log to this project…" />
          <button type="button" id="projectLogBtn" class="apply-btn small">Add</button>
          <button type="button" id="projectLearnBtn" class="ghost-btn small" title="Send to brain">★ Learn</button>
        </div>
      </div>`;
  }

  bujoContent.innerHTML = `
    <h3>Project journals</h3>
    <p class="bujo-cal-hint">Per-project daily logs — separate from your main BuJo. Auto-updated morning/evening when enabled.</p>
    <div class="bujo-project-layout">
      <div class="bujo-project-list">${listItems || '<p class="bujo-empty">No project journals yet — log via chat: “project journal for aria”.</p>'}</div>
      <div class="bujo-project-panel">${detail}</div>
    </div>`;

  bujoContent.querySelectorAll(".bujo-project-row").forEach((btn) => {
    btn.onclick = () => {
      projectJournalSlug = btn.dataset.slug;
      loadProjects();
    };
  });

  document.getElementById("projectJournalDay")?.addEventListener("change", (e) => {
    projectJournalDay = e.target.value;
    loadProjects();
  });

  document.getElementById("projectLogBtn")?.addEventListener("click", async () => {
    const text = document.getElementById("projectLogText")?.value.trim();
    if (!text || !projectJournalSlug) return;
    await fetch(`/api/journal/projects/${encodeURIComponent(projectJournalSlug)}/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        bullet_type: document.getElementById("projectLogType")?.value || "note",
      }),
    });
    document.getElementById("projectLogText").value = "";
    journalNotify("Logged to project journal", false);
    loadProjects();
  });

  document.getElementById("projectLogText")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("projectLogBtn")?.click();
  });

  document.getElementById("projectLearnBtn")?.addEventListener("click", async () => {
    if (!projectJournalSlug) return;
    const d = document.getElementById("projectJournalDay")?.value || day;
    const res = await fetch(`/api/journal/projects/${encodeURIComponent(projectJournalSlug)}/learn`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ day: d }),
    });
    const r = await res.json();
    journalNotify(r.ok ? `Learned ${(r.facts || []).length} fact(s)` : (r.message || r.error || "Nothing to learn"), r.ok ? false : true);
  });

  if (projectJournalSlug) {
    bindBulletActions();
    bindLinkClicks();
  }
}

function setBujoTab(name) {
  currentBujo = name;
  if (name !== "monthly") monthlySelectedDay = null;
  document.querySelectorAll(".bujo-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.bujo === name);
  });
  journalDate?.classList.toggle("hidden", name !== "daily");
  journalWeek?.classList.toggle("hidden", name !== "weekly");
  journalMonth?.classList.toggle("hidden", name !== "monthly" && name !== "future" && name !== "habits" && name !== "wellness");
  if (journalMonth) {
    journalMonth.title = name === "future"
      ? "Target month for new Future log entries"
      : "Journal month";
  }
  updateRapidLogForTab();
  refreshBujo();
  if (name !== "search" && name !== "key") {
    setTimeout(() => document.getElementById("rapidLogInput")?.focus(), 120);
  }
}

document.querySelectorAll(".bujo-tab").forEach((tab) => {
  tab.addEventListener("click", () => setBujoTab(tab.dataset.bujo));
});

document.getElementById("rapidLogBtn")?.addEventListener("click", async () => {
  const text = document.getElementById("rapidLogInput")?.value.trim();
  if (!text) return;
  const form = new FormData();
  form.append("text", text);
  form.append("bullet_type", document.getElementById("rapidType")?.value || "task");
  if (currentBujo === "future") {
    const month = futureMonthValue();
    const bulletType = document.getElementById("rapidType")?.value || "task";
    for (const line of text.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      await postFuture(trimmed, bulletType, month);
    }
  } else {
    const form = new FormData();
    form.append("text", text);
    form.append("bullet_type", document.getElementById("rapidType")?.value || "task");
    if (currentBujo === "daily" && journalDate?.value) form.append("day", journalDate.value);
    const rapid = await journalPost("/api/journal/rapid", { method: "POST", body: form });
    if (!rapid.ok) return;
  }
  document.getElementById("rapidLogInput").value = "";
  journalNotify("Rapid log saved", false);
  refreshBujo();
});

document.getElementById("rapidLogInput")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.getElementById("rapidLogBtn")?.click();
  }
});

document.getElementById("journalUndoBtn")?.addEventListener("click", async () => {
  const res = await fetch("/api/journal/undo", { method: "POST" });
  const data = await res.json();
  if (data.ok) refreshBujo();
  else alert(data.error || "Nothing to undo");
});

document.getElementById("journalRedoBtn")?.addEventListener("click", async () => {
  const res = await fetch("/api/journal/redo", { method: "POST" });
  const data = await res.json();
  if (data.ok) refreshBujo();
  else alert(data.error || "Nothing to redo");
});

document.getElementById("journalReflectBtn")?.addEventListener("click", async () => {
  if (currentBujo === "monthly" || currentBujo === "weekly") {
    const form = new FormData();
    form.append("scope", currentBujo === "monthly" ? "month" : "week");
    if (currentBujo === "monthly") form.append("month", journalMonth?.value || "");
    else form.append("week", journalWeek?.value || "");
    const res = await fetch("/api/journal/reflect/review", { method: "POST", body: form });
    const data = await res.json();
    bujoContent.innerHTML = `<h3>Review reflection</h3><div class="bujo-reflect">${escapeHtml(data.reflection || "").replace(/\n/g, "<br>")}</div>`;
    return;
  }
  const scope = currentBujo === "daily" ? "today" : "week";
  const form = new FormData();
  form.append("scope", scope);
  const res = await fetch("/api/journal/reflect", { method: "POST", body: form });
  const data = await res.json();
  bujoContent.innerHTML = `<h3>Reflection</h3><div class="bujo-reflect">${escapeHtml(data.reflection || "").replace(/\n/g, "<br>")}</div>`;
});

document.getElementById("journalMigrateBtn")?.addEventListener("click", async () => {
  const now = new Date();
  const from = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  const nm = now.getMonth() === 11
    ? `${now.getFullYear() + 1}-01`
    : `${now.getFullYear()}-${String(now.getMonth() + 2).padStart(2, "0")}`;
  const dest = document.getElementById("journalMigrateDest")?.value || "monthly";
  const destLabel = dest === "future" ? "future log" : "next monthly log";
  if (!confirm(`Migrate open monthly tasks from ${from} to ${nm} (${destLabel})?`)) return;
  const form = new FormData();
  form.append("from_month", from);
  form.append("to_month", nm);
  form.append("dest", dest);
  const res = await fetch("/api/journal/migrate-month", { method: "POST", body: form });
  const data = await res.json();
  alert(`Migrated ${data.migrated || 0} tasks to ${nm} (${destLabel})`);
  refreshBujo();
});

document.getElementById("journalSearchBtn")?.addEventListener("click", () => {
  const q = journalSearch?.value.trim();
  if (!q) return;
  currentBujo = "search";
  loadSearchResults(q);
});

journalSearch?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") document.getElementById("journalSearchBtn")?.click();
});

document.getElementById("journalOpenCalendarBtn")?.addEventListener("click", () => {
  const day = journalDate?.value || new Date().toISOString().slice(0, 10);
  window.openCalendarDay?.(day);
});

document.getElementById("journalOpenPlannerBtn")?.addEventListener("click", () => {
  window.switchToView?.("planner");
});

document.getElementById("journalPrintBtn")?.addEventListener("click", () => {
  const month = journalMonth?.value || new Date().toISOString().slice(0, 7);
  window.open(`/api/journal/print?month=${month}`, "_blank");
});

document.getElementById("journalPdfBtn")?.addEventListener("click", () => {
  const month = journalMonth?.value || new Date().toISOString().slice(0, 7);
  window.location.href = `/api/journal/export/pdf?month=${month}`;
});

document.getElementById("journalExportBtn")?.addEventListener("click", async () => {
  const res = await fetch("/api/journal/export");
  const blob = new Blob([JSON.stringify(await res.json(), null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `jarvis-journal-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
});

document.getElementById("journalExportEncBtn")?.addEventListener("click", async () => {
  const password = prompt("Export password (min 4 characters):");
  if (!password || password.length < 4) {
    if (password !== null) journalNotify("Password must be at least 4 characters");
    return;
  }
  const form = new FormData();
  form.append("password", password);
  const out = await journalPost("/api/journal/export/encrypted", { method: "POST", body: form });
  if (!out.ok) return;
  const blob = new Blob([JSON.stringify(out.body.export, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `jarvis-journal-encrypted-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
});

const journalImportFile = document.getElementById("journalImportFile");
const journalImportEncFile = document.getElementById("journalImportEncFile");
document.getElementById("journalImportBtn")?.addEventListener("click", () => journalImportFile?.click());
journalImportFile?.addEventListener("change", async () => {
  const file = journalImportFile.files?.[0];
  if (!file) return;
  try {
    const payload = JSON.parse(await file.text());
    const merge = confirm("Merge with existing journal? Cancel replaces all.");
    const out = await journalPost("/api/journal/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, merge }),
    });
    if (out.ok) refreshBujo();
  } catch (_) {
    journalNotify("Invalid JSON file");
  }
  journalImportFile.value = "";
});

document.getElementById("journalImportEncBtn")?.addEventListener("click", () => journalImportEncFile?.click());
journalImportEncFile?.addEventListener("change", async () => {
  const file = journalImportEncFile.files?.[0];
  if (!file) return;
  const password = prompt("Import password:");
  if (!password) {
    journalImportEncFile.value = "";
    return;
  }
  try {
    const payload = JSON.parse(await file.text());
    const merge = confirm("Merge with existing journal? Cancel replaces all.");
    const out = await journalPost("/api/journal/import/encrypted", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ export: payload, password, merge }),
    });
    if (out.ok) refreshBujo();
  } catch (_) {
    journalNotify("Invalid encrypted journal file");
  }
  journalImportEncFile.value = "";
});

if (journalDate) journalDate.value = new Date().toISOString().slice(0, 10);
if (journalWeek) journalWeek.value = isoWeekValue();
if (journalMonth) journalMonth.value = new Date().toISOString().slice(0, 7);
journalDate?.addEventListener("change", () => { if (currentBujo === "daily") loadDaily(); });
journalWeek?.addEventListener("change", () => { if (currentBujo === "weekly") loadWeekly(); });
journalMonth?.addEventListener("change", () => {
  monthlySelectedDay = null;
  if (currentBujo === "monthly") loadMonthly();
  if (currentBujo === "habits") loadHabits();
  if (currentBujo === "wellness") loadWellness();
  if (currentBujo === "future") loadFuture();
});

window.initJournal = () => {
  loadJournalKey();
  loadJournalStats();
  refreshBujo();
};
window.refreshBujo = refreshBujo;

window.setBujoTab = setBujoTab;
