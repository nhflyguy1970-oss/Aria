/** Health Home — Personal Health Record UI. */
(function () {
  "use strict";

  let _home = null;
  let _tab = "timeline";
  let _inited = false;

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function provBadge(row) {
    const parts = [];
    if (row?.provenance) parts.push(row.provenance);
    if (row?.confidence) parts.push(row.confidence);
    if (!parts.length) return "";
    return `<span class="health-prov-badge muted tiny">${esc(parts.join(" · "))}</span>`;
  }

  async function stepUp(op, pin) {
    const res = await fetch("/api/health/auth/step-up", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ op: op || "*", pin }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || "Step-up failed");
    return data;
  }

  function status(msg) {
    if (window.AriaNet?.isRoomAbort?.({ message: msg }) || /aria-room-leave/i.test(String(msg || ""))) return;
    const el = $("healthStatus");
    if (el) el.textContent = msg || "";
  }

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.error || res.statusText || "Health request failed");
    return data;
  }

  async function apiGate(path, opts, op) {
    let res = await fetch(path, opts);
    let data = await res.json().catch(() => ({}));
    if (res.status === 423 && data.step_up_required) {
      const pin = window.ariaPrompt
        ? await window.ariaPrompt(
            "Health needs a quick Owner confirmation.\n\nEnter your Aria Master Password (or PIN if you set one). This is not a backup password.",
            "",
            {
              title: "Aria Owner confirmation",
              okLabel: "Confirm",
            },
          )
        : window.prompt("Health step-up: Aria Master Password (or PIN):");
      if (!pin?.trim()) throw new Error("Step-up cancelled.");
      await stepUp(op || data.op || "*", pin.trim());
      res = await fetch(path, opts);
      data = await res.json().catch(() => ({}));
    }
    if (!res.ok || data.ok === false) throw new Error(data.message || data.error || res.statusText || "Health request failed");
    return data;
  }

  function scoreInput(name, label, min, max, val) {
    return `<label class="health-field">${esc(label)}
      <input type="number" step="0.1" min="${min}" max="${max}" name="${esc(name)}" value="${val ?? ""}" />
    </label>`;
  }

  async function renderDashboard() {
    const d = await api("/api/health/overview");
    const goals = d.goals || [];
    const trends = d.trends || [];
    const scorecard = d.scorecard || {};
    const scores = scorecard.scores || [];
    const milestones = d.milestones || [];
    const adh = d.adherence || {};
    return `<section class="health-card">
      <h3>How am I doing?</h3>
      <div class="health-dash-grid">
        <div class="health-kpi">Check-in<strong>${d.checkin ? "On file" : "Not yet"}</strong></div>
        <div class="health-kpi">Activity<strong>${(d.today_activity || []).length} session(s)</strong></div>
        <div class="health-kpi">Workouts<strong>${(d.today_workouts || []).length}</strong></div>
        <div class="health-kpi">Streak<strong>${d.workout_streak || 0} day(s)</strong></div>
        <div class="health-kpi">Med adherence<strong>${adh.estimate_pct != null ? adh.estimate_pct + "%" : "—"}</strong></div>
        <div class="health-kpi">Habit summary<strong>${scorecard.overall != null ? scorecard.overall + "/100" : "—"}</strong></div>
      </div>
      <p class="muted tiny">Habit summary is educational only — not a medical score.</p>
    </section>
    <section class="health-card">
      <h3>Wellness scorecard</h3>
      <p class="muted tiny">${esc(scorecard.boundary || "")}</p>
      ${scores.length ? `<div class="health-scorecard-grid">${scores.map((s) => `
        <div class="health-score-item">
          <div class="health-score-label">${esc(s.label)} <strong>${s.score == null ? "—" : s.score + "/100"}</strong></div>
          <div class="health-progress"><span style="width:${s.score == null ? 0 : s.score}%"></span></div>
          <p class="muted tiny">${esc(s.explain || "")}</p>
        </div>`).join("")}</div>` : `<p class="muted">Not enough data yet.</p>`}
    </section>
    <section class="health-card">
      <h3>What changed?</h3>
      ${(d.month_changes || []).length ? `<ul>${d.month_changes.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>` : `<p class="muted">Weight ${esc(d.weight_trend || "—")} · BP ${esc(d.bp_trend || "—")} · Sugar ${esc(d.sugar_trend || "—")} · Sleep ${esc(d.sleep_trend || "—")}</p>`}
    </section>
    <section class="health-card">
      <h3>Pay attention to</h3>
      ${(d.attention || trends).length ? `<ul>${(d.attention || trends).map((t) => `<li><span class="health-status-${esc(t.status || "needs_attention")}">${esc((t.status || "note").replace("_", " "))}</span> — ${esc(t.topic)}: ${esc(t.detail)}</li>`).join("")}</ul>` : `<p class="muted">Nothing flagged from recorded trends.</p>`}
    </section>
    <section class="health-card">
      <h3>Goals</h3>
      ${goals.length ? goals.map((g) => `
        <div class="health-goal-row">
          <strong>${esc(g.title)}</strong>
          <span class="muted tiny">${g.on_track ? "On track" : g.needs_work ? "Needs work" : "Tracking"} — ${esc(g.progress_note || "")}</span>
          <div class="health-progress"><span style="width:${g.progress_pct == null ? 0 : g.progress_pct}%"></span></div>
        </div>`).join("") : `<p class="muted">No active goals.</p>`}
    </section>
    <section class="health-card">
      <h3>Milestones</h3>
      ${milestones.length ? `<ul>${milestones.map((m) => `<li><strong>${esc(m.title)}</strong>${m.detail ? " — " + esc(m.detail) : ""}</li>`).join("")}</ul>` : `<p class="muted">None yet from recorded data.</p>`}
    </section>
    <section class="health-card">
      <h3>Upcoming &amp; meds due</h3>
      <ul>
        ${(d.appointments || []).slice(0, 5).map((a) => `<li>${esc(a.day)} ${esc(a.time || "")} — ${esc(a.title)}</li>`).join("") || "<li class='muted'>No calendar appointments matched.</li>"}
        ${(d.reminders_due || []).slice(0, 5).map((r) => `<li>Reminder: ${esc(r.title)}</li>`).join("")}
        ${(d.providers_next || []).slice(0, 4).map((p) => `<li>${esc(p.specialty)} ${esc(p.name)} next ${esc(p.next_visit)}</li>`).join("")}
        ${(adh.due_today || []).slice(0, 6).map((n) => `<li>Med to log today: ${esc(n)}</li>`).join("")}
      </ul>
      <p class="muted tiny">${esc(d.disclaimer || "")}</p>
    </section>`;
  }

  function renderCheckin(home) {
    const c = home.checkin || {};
    const pending = home.pending;
    const pendingHtml = pending
      ? `<section class="health-card health-pending">
          <h3>Confirm highest-trust change</h3>
          <p>${esc(pending.summary || "A Health Record change is waiting.")}</p>
          <p class="muted tiny">Medications, conditions, allergies, blood type, physicians, and emergency contacts are never changed silently.</p>
          <div class="health-pending-actions">
            <button type="button" class="apply-btn small" id="healthConfirmYes">Confirm</button>
            <button type="button" class="ghost-btn small" id="healthConfirmNo">Cancel</button>
          </div>
        </section>`
      : "";
    return `${pendingHtml}<section class="health-card">
      <h3>Daily check-in — ${esc(home.today || "")}</h3>
      <p class="muted tiny">Under two minutes. Leave blank what you skip.</p>
      <form id="healthCheckinForm" class="health-checkin-grid">
        ${scoreInput("overall", "Overall 1–10", 1, 10, c.overall)}
        ${scoreInput("energy", "Energy 1–10", 1, 10, c.energy)}
        ${scoreInput("mood", "Mood 1–10", 1, 10, c.mood)}
        ${scoreInput("stress", "Stress 1–10", 1, 10, c.stress)}
        ${scoreInput("pain", "Pain 0–10", 0, 10, c.pain)}
        ${scoreInput("sleep_hours", "Hours slept", 0, 24, c.sleep_hours)}
        ${scoreInput("sleep_quality", "Sleep quality 1–10", 1, 10, c.sleep_quality)}
        ${scoreInput("weight", "Weight", 0, 800, c.weight)}
        ${scoreInput("bp_systolic", "BP systolic", 50, 300, c.bp_systolic)}
        ${scoreInput("bp_diastolic", "BP diastolic", 30, 200, c.bp_diastolic)}
        ${scoreInput("heart_rate", "Heart rate", 20, 250, c.heart_rate)}
        ${scoreInput("blood_sugar", "Blood sugar", 20, 800, c.blood_sugar)}
        ${scoreInput("temperature", "Temperature", 90, 110, c.temperature)}
        ${scoreInput("spo2", "Pulse ox %", 50, 100, c.spo2)}
        <label class="health-field health-span2">Exercise
          <input type="text" name="exercise" value="${esc(c.exercise || "")}" />
        </label>
        <label class="health-field">Water
          <input type="text" name="water" value="${esc(c.water || "")}" />
        </label>
        <label class="health-field">Alcohol
          <input type="text" name="alcohol" value="${esc(c.alcohol || "")}" />
        </label>
        <label class="health-field">Tobacco
          <input type="text" name="tobacco" value="${esc(c.tobacco || "")}" />
        </label>
        <label class="health-field health-span2">Meals
          <input type="text" name="meals" value="${esc(c.meals || "")}" />
        </label>
        <label class="health-field health-span2">Symptoms
          <input type="text" name="symptoms" value="${esc(c.symptoms || "")}" />
        </label>
        <label class="health-field health-span2">Notes
          <textarea name="notes" rows="2">${esc(c.notes || "")}</textarea>
        </label>
        <div class="health-span2">
          <button type="submit" class="apply-btn small">Save check-in</button>
        </div>
      </form>
    </section>
    <section class="health-card">
      <h3>Observations</h3>
      ${(home.observations || []).length
        ? `<ul>${home.observations.map((o) => `<li>${esc(o)}</li>`).join("")}</ul>`
        : `<p class="muted">No strong patterns yet.</p>`}
      <p class="muted tiny">${esc(home.disclaimer || "")}</p>
    </section>`;
  }

  function listTable(rows, cols) {
    if (!rows?.length) return `<p class="muted">None recorded.</p>`;
    return `<table class="health-table"><thead><tr>${cols.map((c) => `<th>${esc(c[1])}</th>`).join("")}</tr></thead>
      <tbody>${rows
        .map(
          (r) =>
            `<tr>${cols.map((c) => `<td>${esc(r[c[0]] ?? "")}</td>`).join("")}</tr>`
        )
        .join("")}</tbody></table>`;
  }

  async function renderMeds(home) {
    let adh = {};
    try {
      adh = await api("/api/health/adherence");
    } catch (_e) {
      adh = {};
    }
    const taken = (adh.taken_today || []).map((d) => d.name).filter(Boolean);
    const missed = (adh.missed_today || []).map((d) => d.name).filter(Boolean);
    const due = adh.due_today || [];
    return `<section class="health-card">
      <h3>Medication adherence</h3>
      <p class="muted tiny">Gentle history only — never a judgment. Log taken/missed doses to keep this honest.</p>
      <div class="health-dash-grid">
        <div class="health-kpi">Taken today<strong>${taken.length || "—"}</strong></div>
        <div class="health-kpi">Missed today<strong>${missed.length || "—"}</strong></div>
        <div class="health-kpi">Weekly<strong>${adh.weekly_pct != null ? adh.weekly_pct + "%" : "—"}</strong></div>
        <div class="health-kpi">Monthly<strong>${adh.monthly_pct != null ? adh.monthly_pct + "%" : "—"}</strong></div>
      </div>
      <p class="muted tiny">${esc(adh.explain || "")}</p>
      ${due.length ? `<p>Still to log today: ${due.map((n) => esc(n)).join(", ")}</p>` : ""}
      <form id="healthDoseForm" class="health-inline-form">
        <input name="name" placeholder="Medication name" required list="healthMedNames" />
        <select name="status"><option value="taken">Taken</option><option value="missed">Missed</option></select>
        <input name="notes" placeholder="Notes (optional)" />
        <button type="submit" class="apply-btn small">Log dose</button>
      </form>
      <datalist id="healthMedNames">${(home.medications || []).map((m) => `<option value="${esc(m.name)}"></option>`).join("")}</datalist>
    </section>
    <section class="health-card">
      <h3>Current medications</h3>
      ${listTable(home.medications || [], [
        ["name", "Name"],
        ["strength", "Strength"],
        ["dose", "Dose"],
        ["frequency", "Frequency"],
        ["purpose", "Purpose"],
        ["physician", "Physician"],
        ["status", "Status"],
      ])}
      <form id="healthMedForm" class="health-inline-form">
        <input name="name" placeholder="Medication name" required />
        <input name="strength" placeholder="Strength" />
        <input name="dose" placeholder="Dose" />
        <input name="frequency" placeholder="Frequency" />
        <input name="purpose" placeholder="Purpose" />
        <button type="submit" class="apply-btn small">Add / update</button>
      </form>
      <div id="healthSafetyBox" class="muted tiny" style="margin-top:0.7rem"></div>
      <button type="button" class="ghost-btn small" id="healthSafetyBtn">Check educational interactions</button>
    </section>`;
  }

  function renderSupps(home) {
    return `<section class="health-card">
      <h3>Current supplements</h3>
      ${listTable(home.supplements || [], [
        ["name", "Name"],
        ["dose", "Dose"],
        ["frequency", "Frequency"],
        ["purpose", "Purpose"],
        ["status", "Status"],
      ])}
      <form id="healthSuppForm" class="health-inline-form">
        <input name="name" placeholder="Supplement name" required />
        <input name="dose" placeholder="Dose" />
        <input name="frequency" placeholder="Frequency" />
        <input name="purpose" placeholder="Purpose" />
        <button type="submit" class="apply-btn small">Add / update</button>
      </form>
    </section>`;
  }

  function renderHistory(home) {
    return `<section class="health-card">
      <h3>Conditions</h3>
      ${listTable(home.conditions || [], [
        ["name", "Name"],
        ["kind", "Kind"],
        ["onset", "Onset"],
        ["status", "Status"],
        ["notes", "Notes"],
      ])}
      <form id="healthCondForm" class="health-inline-form">
        <input name="name" placeholder="Condition / surgery / illness" required />
        <select name="kind">
          <option value="condition">Condition</option>
          <option value="illness">Past illness</option>
          <option value="surgery">Surgery</option>
          <option value="hospitalization">Hospitalization</option>
          <option value="family">Family history</option>
        </select>
        <input name="onset" placeholder="Onset / date" />
        <input name="notes" placeholder="Notes" />
        <button type="submit" class="apply-btn small">Add</button>
      </form>
    </section>
    <section class="health-card">
      <h3>Allergies</h3>
      ${listTable(home.allergies || [], [
        ["kind", "Kind"],
        ["name", "Name"],
        ["reaction", "Reaction"],
      ])}
      <form id="healthAllergyForm" class="health-inline-form">
        <select name="kind">
          <option value="drug">Drug</option>
          <option value="food">Food</option>
          <option value="environmental">Environmental</option>
        </select>
        <input name="name" placeholder="Allergen" required />
        <input name="reaction" placeholder="Reaction" />
        <button type="submit" class="apply-btn small">Add</button>
      </form>
    </section>
    <section class="health-card">
      <h3>Vaccinations</h3>
      ${listTable(home.vaccinations || [], [
        ["day", "Date"],
        ["name", "Vaccine"],
        ["dose_number", "Dose"],
        ["notes", "Notes"],
      ])}
      <form id="healthVaxForm" class="health-inline-form">
        <input name="name" placeholder="Vaccine" required />
        <input name="day" type="date" />
        <input name="dose_number" placeholder="Dose #" />
        <input name="notes" placeholder="Notes" />
        <button type="submit" class="apply-btn small">Add</button>
      </form>
    </section>`;
  }

  async function renderTimeline() {
    const cat = $("healthTimelineFilter")?.value || "";
    const data = await api(`/api/health/timeline?category=${encodeURIComponent(cat)}`);
    const items = data.items || [];
    const filters = data.filters || [
      ["", "Everything"],
      ["vitals", "Vitals"],
      ["exercise", "Exercise"],
      ["workouts", "Workouts"],
      ["symptoms", "Symptoms"],
      ["medications", "Medications"],
      ["supplements", "Supplements"],
      ["labs", "Labs"],
      ["doctors", "Doctors"],
      ["documents", "Documents"],
      ["journal", "Journal"],
      ["goals", "Goals"],
      ["milestones", "Milestones"],
      ["recovery", "Recovery"],
    ];
    return `<section class="health-card">
      <h3>Lifetime Health Timeline</h3>
      <p class="muted tiny">Central chronological view of your Personal Health Record.</p>
      <label class="health-field">Filter
        <select id="healthTimelineFilter">
          ${filters.map(([v, l]) => `<option value="${esc(v)}"${cat === v ? " selected" : ""}>${esc(l)}</option>`).join("")}
        </select>
      </label>
      ${items.length ? `<ul class="health-timeline">${items.slice(0, 100).map((it) => `<li><span class="ht-day">${esc(it.day)}</span><span class="ht-src">${esc(it.source)}</span><span>${esc(it.title)}${it.detail ? " — " + esc(it.detail) : ""}</span></li>`).join("")}</ul>` : `<p class="muted">Nothing recorded yet.</p>`}
    </section>`;
  }

  async function renderQuestions(home) {
    const data = home?.doctor_questions ? { questions: home.doctor_questions } : await api("/api/health/questions?status=open");
    const rows = data.questions || home.doctor_questions || [];
    return `<section class="health-card">
      <h3>Questions for my doctor</h3>
      ${rows.length ? `<ul>${rows.map((q) => `<li>${esc(q.text)} <button type="button" class="ghost-btn small health-q-done" data-id="${esc(q.id)}">Answered</button></li>`).join("")}</ul>` : `<p class="muted">None open. Say “remind me to ask my doctor about …”</p>`}
      <form id="healthQuestionForm" class="health-inline-form">
        <input name="text" placeholder="Remind me to ask about…" required class="health-span2" />
        <button type="submit" class="apply-btn small">Save question</button>
      </form>
    </section>`;
  }

  async function renderCoach() {
    const data = await api("/api/health/coach");
    const suggestions = data.suggestions || [];
    return `<section class="health-card">
      <h3>Wellness coach</h3>
      <p class="muted tiny">${esc(data.boundary || "")}</p>
      ${suggestions.length ? `<ul>${suggestions.map((s) => `<li><strong>${esc(s.topic)}:</strong> ${esc(s.suggestion)}<br /><span class="muted tiny">Why: ${esc(s.why)}</span></li>`).join("")}</ul>` : `<p class="muted">Not enough recorded trends yet.</p>`}
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderConsult(home) {
    const rows = home.consultations || (await api("/api/health/consultations")).consultations || [];
    return `<section class="health-card">
      <h3>Optional AI consultation</h3>
      <p class="muted tiny">Health stays local. Cloud AI is a consultant only. Nothing is sent until you approve the exact payload.</p>
      <form id="healthConsultForm" class="health-inline-form">
        <input name="question" placeholder="Review my last six months of blood pressure…" required style="min-width:18rem" />
        <select name="level">
          <option value="local_only">Level 1 — local only</option>
          <option value="sanitized" selected>Level 2 — sanitized</option>
          <option value="full">Level 3 — full (explicit)</option>
        </select>
        <button type="submit" class="apply-btn small">Preview (do not send yet)</button>
      </form>
      <form id="healthSecondForm" class="health-inline-form">
        <input name="question" placeholder="Get a second opinion on…" required style="min-width:18rem" />
        <select name="level">
          <option value="sanitized" selected>Sanitized</option>
          <option value="local_only">Local only</option>
          <option value="full">Full</option>
        </select>
        <button type="submit" class="ghost-btn small">Preview second opinion</button>
      </form>
      <div id="healthConsultPreview"></div>
      <h3>Consultation history</h3>
      ${listTable(rows, [
        ["created_at", "When"],
        ["level", "Level"],
        ["provider", "Provider"],
        ["model", "Model"],
        ["question", "Question"],
        ["status", "Status"],
      ])}
    </section>`;
  }

  function renderReminders(home) {
    return `<section class="health-card">
      <h3>Reminders</h3>
      ${listTable(home.reminders || [], [
        ["kind", "Kind"],
        ["title", "Title"],
        ["schedule", "Schedule"],
        ["enabled", "On"],
      ])}
      <form id="healthReminderForm" class="health-inline-form">
        <select name="kind">
          <option value="checkin">Daily check-in</option>
          <option value="medication">Medication</option>
          <option value="supplement">Supplement</option>
          <option value="blood_pressure">Blood pressure</option>
          <option value="blood_sugar">Blood sugar</option>
          <option value="weight">Weight</option>
          <option value="appointment">Appointment</option>
          <option value="refill">Prescription refill</option>
          <option value="exercise">Exercise</option>
          <option value="hydration">Hydration</option>
        </select>
        <input name="title" placeholder="Title" required />
        <input name="schedule" placeholder="e.g. daily 08:00 or 2026-08-12 09:00" />
        <button type="submit" class="apply-btn small">Save reminder</button>
      </form>
    </section>`;
  }

  async function renderActivity() {
    const data = await api("/api/health/activities");
    const kinds = data.kinds || [];
    return `<section class="health-card">
      <h3>Activity</h3>
      ${listTable(data.activities || [], [
        ["day", "Date"],
        ["kind", "Kind"],
        ["duration_min", "Minutes"],
        ["intensity", "Intensity"],
        ["calories", "Est. cal"],
        ["distance", "Distance"],
        ["steps", "Steps"],
        ["notes", "Notes"],
      ])}
      <form id="healthActivityForm" class="health-inline-form">
        <select name="kind">${kinds.map((k) => `<option value="${esc(k)}">${esc(k.replaceAll("_", " "))}</option>`).join("")}</select>
        <input name="duration_min" type="number" step="0.1" placeholder="Minutes" required />
        <select name="intensity"><option value="light">Light</option><option value="moderate" selected>Moderate</option><option value="hard">Hard</option><option value="vigorous">Vigorous</option></select>
        <input name="distance" type="number" step="0.1" placeholder="Distance" />
        <input name="steps" type="number" placeholder="Steps" />
        <input name="heart_rate" type="number" placeholder="HR" />
        <input name="notes" placeholder="Notes" />
        <button type="submit" class="apply-btn small">Log activity</button>
      </form>
    </section>`;
  }

  async function renderWorkouts() {
    const data = await api("/api/health/workouts");
    const prog = data.progression || {};
    const pbs = prog.personal_bests || [];
    return `<section class="health-card">
      <h3>Workouts</h3>
      <p class="muted tiny">Last: ${esc((prog.last_workout || {}).title || "—")} on ${esc((prog.last_workout || {}).day || "—")} · Streak ${esc(prog.streak_days || 0)} · Volume ${esc(prog.volume_trend || "—")}</p>
      ${pbs.length ? `<p class="muted tiny">Personal bests: ${pbs.slice(0, 6).map((p) => `${esc(p.exercise)} ${esc(p.weight || "")}`).join(" · ")}</p>` : ""}
      ${listTable(data.workouts || [], [
        ["day", "Date"],
        ["title", "Title"],
        ["template", "Template"],
        ["body_part", "Body part"],
        ["duration_min", "Minutes"],
        ["difficulty", "Difficulty"],
        ["pain", "Pain"],
        ["volume", "Volume"],
      ])}
      <form id="healthWorkoutForm" class="health-inline-form">
        <select name="template">${(data.templates || []).map((t) => `<option value="${esc(t)}">${esc(t.replaceAll("_", " "))}</option>`).join("")}</select>
        <input name="title" placeholder="Workout title" />
        <input name="body_part" placeholder="Body part" />
        <input name="duration_min" type="number" placeholder="Minutes" />
        <input name="exercise" placeholder="First exercise" />
        <input name="sets" type="number" placeholder="Sets" />
        <input name="reps" type="number" placeholder="Reps" />
        <input name="weight" type="number" step="0.1" placeholder="Weight" />
        <input name="band_color" placeholder="Band color" />
        <input name="resistance" placeholder="Resistance" />
        <input name="difficulty" placeholder="Difficulty" />
        <input name="pain" type="number" step="0.1" placeholder="Pain 0–10" />
        <button type="submit" class="apply-btn small">Save workout</button>
      </form>
    </section>`;
  }

  async function renderGoals() {
    const data = await api("/api/health/goals");
    return `<section class="health-card">
      <h3>Goals &amp; coaching</h3>
      <p class="muted tiny">Progress is visual and educational — discuss targets with your physician.</p>
      ${(data.goals || []).length ? data.goals.map((g) => `
        <div class="health-goal-row">
          <strong>${esc(g.title)}</strong> <span class="muted tiny">(${esc(g.kind)}) ${g.on_track ? "· on track" : g.needs_work ? "· needs work" : ""}</span>
          <div class="health-progress"><span style="width:${g.progress_pct == null ? 0 : Math.min(100, g.progress_pct)}%"></span></div>
          <p class="muted tiny">${esc(g.progress_note || "no data yet")}${g.progress_pct != null ? " · " + Math.round(g.progress_pct) + "%" : ""}</p>
        </div>`).join("") : `<p class="muted">None yet.</p>`}
      <form id="healthGoalForm" class="health-inline-form">
        <select name="kind">
          <option value="weight">Weight</option>
          <option value="steps">Walking / steps</option>
          <option value="exercise">Exercise days/week</option>
          <option value="sleep">Sleep</option>
          <option value="blood_pressure">Blood pressure</option>
          <option value="blood_sugar">Blood sugar</option>
          <option value="water">Hydration</option>
          <option value="strength">Strength</option>
          <option value="stretch">Stretching</option>
          <option value="medication">Medication adherence</option>
          <option value="supplement">Supplement adherence</option>
          <option value="appointment">Appointment reminder</option>
          <option value="stress">Stress</option>
          <option value="custom">Custom</option>
        </select>
        <input name="title" placeholder="e.g. Lose 20 pounds" required />
        <input name="target_value" type="number" step="0.1" placeholder="Target" />
        <input name="target_unit" placeholder="Unit" />
        <input name="per_week" type="number" step="0.1" placeholder="Per week" />
        <input name="deadline" type="date" />
        <button type="submit" class="apply-btn small">Save goal</button>
      </form>
    </section>`;
  }

  async function renderTrends() {
    const data = await api("/api/health/trends");
    return `<section class="health-card">
      <h3>Trends</h3>
      <p class="muted tiny">Observations only — not diagnoses.</p>
      ${(data.trends || []).length ? `<ul>${data.trends.map((t) => `<li><span class="health-status-${esc(t.status)}">${esc(t.status.replaceAll("_", " "))}</span> — <strong>${esc(t.topic)}</strong>: ${esc(t.detail)}</li>`).join("")}</ul>` : `<p class="muted">Not enough recorded data yet.</p>`}
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderJournal() {
    const data = await api("/api/health/journal");
    return `<section class="health-card">
      <h3>Health Journal</h3>
      <p class="muted tiny">Separate from Journal. Entries appear on the Health Timeline.</p>
      ${(data.entries || []).map((e) => `<p><strong>${esc(e.day)}</strong> — ${esc(e.body)}</p>`).join("") || `<p class="muted">No entries yet.</p>`}
      <form id="healthJournalForm" class="health-inline-form">
        <input name="body" placeholder="I felt dizzy…" required style="min-width:18rem" />
        <input name="mood" placeholder="Mood (optional)" />
        <button type="submit" class="apply-btn small">Save</button>
      </form>
    </section>`;
  }

  async function renderKnowledge() {
    const data = await api("/api/health/knowledge");
    return `<section class="health-card">
      <h3>Health Knowledge</h3>
      <p class="muted tiny">Trusted notes, doctor instructions, NIH / Mayo / Cleveland / AHA / ADA clippings — searchable with Health.</p>
      ${listTable(data.items || [], [
        ["title", "Title"],
        ["source", "Source"],
        ["url", "URL"],
        ["tags", "Tags"],
      ])}
      <form id="healthKnowledgeForm" class="health-inline-form">
        <input name="title" placeholder="Title" required />
        <select name="source">
          <option value="doctor">Doctor advice</option>
          <option value="hospital">Hospital / treatment plan</option>
          <option value="nih">NIH</option>
          <option value="cdc">CDC</option>
          <option value="who">WHO</option>
          <option value="mayo">Mayo Clinic</option>
          <option value="cleveland">Cleveland Clinic</option>
          <option value="aha">AHA</option>
          <option value="ada">ADA</option>
          <option value="article">Educational article</option>
          <option value="website">Trusted website</option>
          <option value="research">Research</option>
          <option value="lifestyle">Lifestyle idea</option>
          <option value="personal">Personal note</option>
          <option value="question">Question</option>
        </select>
        <input name="url" placeholder="URL (optional)" />
        <input name="tags" placeholder="Tags" />
        <input name="body" placeholder="Notes / excerpt" style="min-width:16rem" />
        <button type="submit" class="apply-btn small">Save</button>
      </form>
    </section>`;
  }

  async function renderProviders() {
    const data = await api("/api/health/providers");
    return `<section class="health-card">
      <h3>Doctor directory</h3>
      ${listTable(data.providers || [], [
        ["specialty", "Specialty"],
        ["name", "Name"],
        ["phone", "Phone"],
        ["email", "Email"],
        ["address", "Address"],
        ["last_visit", "Last visit"],
        ["next_visit", "Next visit"],
        ["notes", "Notes"],
      ])}
      <form id="healthProviderForm" class="health-inline-form">
        <select name="specialty">
          <option value="primary">Primary physician</option>
          <option value="cardiology">Cardiologist</option>
          <option value="endocrinology">Endocrinologist</option>
          <option value="dentistry">Dentist</option>
          <option value="ophthalmology">Eye doctor</option>
          <option value="pharmacy">Pharmacy</option>
          <option value="pt">Physical therapist</option>
          <option value="other">Other specialist</option>
        </select>
        <input name="name" placeholder="Name" required />
        <input name="phone" placeholder="Phone" />
        <input name="email" placeholder="Email" />
        <input name="address" placeholder="Address" />
        <input name="last_visit" type="date" />
        <input name="next_visit" type="date" />
        <input name="notes" placeholder="Notes" />
        <button type="submit" class="apply-btn small">Save provider</button>
      </form>
    </section>
    <section class="health-card">
      <h3>Doctor appointment history</h3>
      ${listTable((await api("/api/health/visits")).visits || [], [
        ["day", "Date"],
        ["physician", "Provider"],
        ["reason", "Reason"],
        ["summary", "Summary"],
        ["instructions", "Instructions"],
        ["follow_up", "Follow-up"],
        ["next_appointment", "Next"],
      ])}
      <form id="healthVisitForm" class="health-inline-form">
        <input name="day" type="date" />
        <input name="physician" placeholder="Provider" />
        <input name="reason" placeholder="Reason" />
        <input name="summary" placeholder="Summary" style="min-width:12rem" />
        <input name="instructions" placeholder="Instructions" />
        <input name="follow_up" placeholder="Follow-up" />
        <input name="questions_asked" placeholder="Questions asked" />
        <input name="questions_answered" placeholder="Questions answered" />
        <input name="next_appointment" type="date" />
        <input name="notes" placeholder="Notes" />
        <button type="submit" class="apply-btn small">Log visit</button>
      </form>
    </section>`;
  }

  async function renderProcedures() {
    const data = await api("/api/health/procedures");
    return `<section class="health-card">
      <h3>Procedures</h3>
      ${listTable(data.procedures || [], [
        ["day", "Date"],
        ["name", "Name"],
        ["kind", "Kind"],
        ["location", "Location"],
        ["provider", "Provider"],
        ["result", "Result"],
        ["follow_up", "Follow-up"],
        ["notes", "Notes"],
      ])}
      <form id="healthProcedureForm" class="health-inline-form">
        <select name="kind">
          <option value="MRI">MRI</option>
          <option value="CT">CT</option>
          <option value="X-Ray">X-Ray</option>
          <option value="Ultrasound">Ultrasound</option>
          <option value="Colonoscopy">Colonoscopy</option>
          <option value="Stress test">Stress test</option>
          <option value="Echocardiogram">Echocardiogram</option>
          <option value="Biopsy">Biopsy</option>
          <option value="Hospital stay">Hospital stay</option>
          <option value="Other">Other</option>
        </select>
        <input name="name" placeholder="Procedure name" required />
        <input name="day" type="date" />
        <input name="location" placeholder="Location" />
        <input name="provider" placeholder="Provider" />
        <input name="result" placeholder="Result summary" />
        <input name="follow_up" placeholder="Follow-up" />
        <input name="notes" placeholder="Notes" />
        <button type="submit" class="apply-btn small">Save procedure</button>
      </form>
    </section>`;
  }

  function sparkline(series) {
    const pts = (series || []).filter((p) => p.value != null);
    if (pts.length < 2) return `<p class="muted">Not enough points to graph.</p>`;
    const w = 520;
    const h = 120;
    const vals = pts.map((p) => Number(p.value));
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const span = max - min || 1;
    const path = pts
      .map((p, i) => {
        const x = (i / (pts.length - 1)) * (w - 16) + 8;
        const y = h - 12 - ((Number(p.value) - min) / span) * (h - 24);
        return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
    return `<svg class="health-spark" viewBox="0 0 ${w} ${h}" role="img" aria-label="Trend graph">
      <path d="${path}" fill="none" stroke="currentColor" stroke-width="2" />
    </svg>
    <p class="muted tiny">${esc(pts[0].day)} → ${esc(pts[pts.length - 1].day)} · ${esc(vals[vals.length - 1])}</p>`;
  }

  async function renderVitals() {
    const kinds = [
      ["weight", "Weight"],
      ["blood_pressure", "Blood pressure"],
      ["blood_sugar", "Blood sugar"],
      ["sleep_hours", "Sleep"],
      ["heart_rate", "Heart rate"],
      ["mood", "Mood"],
      ["energy", "Energy"],
      ["pain", "Pain"],
      ["stress", "Stress"],
    ];
    const range = $("healthVitalRange")?.value || "90";
    const cards = [];
    for (const [kind, label] of kinds) {
      const data = await api(`/api/health/graph?kind=${encodeURIComponent(kind)}&days=${encodeURIComponent(range)}`);
      cards.push(`<section class="health-card"><h3>${esc(label)}</h3>${sparkline(data.series)}<p class="muted tiny">${esc((data.message || "").split("\n")[0] || "")}</p></section>`);
    }
    return `<div class="health-toolbar-inline">
      <label>Range <select id="healthVitalRange">
        <option value="7"${range === "7" ? " selected" : ""}>Week</option>
        <option value="30"${range === "30" ? " selected" : ""}>Month</option>
        <option value="90"${range === "90" ? " selected" : ""}>3 months</option>
        <option value="180"${range === "180" ? " selected" : ""}>6 months</option>
        <option value="365"${range === "365" ? " selected" : ""}>Year</option>
        <option value="3650"${range === "3650" ? " selected" : ""}>All time</option>
      </select></label>
    </div>${cards.join("")}`;
  }

  async function renderLabs() {
    const data = await api("/api/health/labs?limit=80");
    return `<section class="health-card">
      <h3>Laboratory results</h3>
      ${listTable(data.labs || [], [
        ["day", "Date"],
        ["name", "Test"],
        ["value", "Value"],
        ["units", "Units"],
        ["ref_low", "Ref low"],
        ["ref_high", "Ref high"],
        ["physician", "Physician"],
      ])}
      <form id="healthLabForm" class="health-inline-form">
        <input name="name" placeholder="Test name (A1C, LDL…)" required />
        <input name="value" type="number" step="0.01" placeholder="Value" />
        <input name="units" placeholder="Units" />
        <input name="day" type="date" />
        <input name="physician" placeholder="Ordering physician" />
        <button type="submit" class="apply-btn small">Add lab</button>
      </form>
    </section>`;
  }

  async function renderDocs() {
    const kindFilter = $("healthDocKindFilter")?.value || "";
    const q = $("healthDocSearch")?.value || "";
    const data = await api("/api/health/documents");
    let docs = data.documents || [];
    if (kindFilter) docs = docs.filter((d) => String(d.kind || "") === kindFilter);
    if (q.trim()) {
      const needle = q.trim().toLowerCase();
      docs = docs.filter((d) =>
        [d.title, d.kind, d.day, d.notes, d.extracted_preview].join(" ").toLowerCase().includes(needle)
      );
    }
    return `<section class="health-card">
      <h3>Medical documents</h3>
      <p class="muted tiny">Organized by kind. Search by doctor, date, condition, medication, or procedure via Health search or filters below.</p>
      <div class="health-toolbar-inline">
        <label>Kind <select id="healthDocKindFilter">
          ${[["", "All"], ["lab", "Labs"], ["imaging", "Imaging"], ["prescription", "Prescriptions"], ["visit", "Visit summaries"], ["insurance", "Insurance"], ["referral", "Referrals"], ["discharge", "Hospital records"], ["note", "Notes"], ["document", "Other"]].map(([v, l]) => `<option value="${esc(v)}"${kindFilter === v ? " selected" : ""}>${esc(l)}</option>`).join("")}
        </select></label>
        <input id="healthDocSearch" type="search" placeholder="Filter documents…" value="${esc(q)}" />
      </div>
      ${listTable(docs, [
        ["day", "Date"],
        ["title", "Title"],
        ["kind", "Kind"],
        ["extracted_preview", "OCR preview"],
      ])}
      <form id="healthDocForm" class="health-inline-form">
        <input type="file" name="file" required />
        <input name="title" placeholder="Title" />
        <select name="kind">
          <option value="lab">Lab report</option>
          <option value="prescription">Prescription</option>
          <option value="visit">Visit summary</option>
          <option value="discharge">Hospital record</option>
          <option value="imaging">Imaging</option>
          <option value="referral">Referral</option>
          <option value="insurance">Insurance</option>
          <option value="note">Scanned note</option>
          <option value="document">Other</option>
        </select>
        <button type="submit" class="apply-btn small">Upload + OCR</button>
      </form>
    </section>`;
  }

  async function renderRecovery() {
    const data = await api("/api/health/recovery");
    return `<section class="health-card">
      <h3>Recovery tracking</h3>
      <p class="muted tiny">Illness, injury, surgery, PT, pain, and mobility — educational history only.</p>
      ${listTable(data.events || [], [
        ["day", "Date"],
        ["kind", "Kind"],
        ["title", "Title"],
        ["body_part", "Body part"],
        ["pain", "Pain"],
        ["mobility", "Mobility"],
        ["status", "Status"],
        ["notes", "Notes"],
      ])}
      <form id="healthRecoveryForm" class="health-inline-form">
        <select name="kind">
          <option value="illness">Illness</option>
          <option value="injury">Injury</option>
          <option value="surgery">Surgery</option>
          <option value="recovery">Recovery</option>
          <option value="physical_therapy">Physical therapy</option>
          <option value="pain">Pain progression</option>
          <option value="mobility">Mobility</option>
          <option value="milestone">Healing milestone</option>
        </select>
        <input name="title" placeholder="Title" required />
        <input name="body_part" placeholder="Body part" />
        <input name="pain" type="number" step="0.1" min="0" max="10" placeholder="Pain 0–10" />
        <input name="mobility" placeholder="Mobility notes" />
        <select name="status"><option value="active">Active</option><option value="improving">Improving</option><option value="resolved">Resolved</option></select>
        <input name="notes" placeholder="Recovery notes" style="min-width:12rem" />
        <input name="day" type="date" />
        <button type="submit" class="apply-btn small">Log recovery</button>
      </form>
    </section>`;
  }

  function renderPrint() {
    const kinds = [
      ["daily", "Daily report"],
      ["week", "Weekly summary"],
      ["month", "Monthly summary"],
      ["medications", "Current medications"],
      ["medication_history", "Medication history"],
      ["supplements", "Current supplements"],
      ["supplement_history", "Supplement history"],
      ["blood_pressure", "Blood pressure log"],
      ["blood_sugar", "Blood sugar log"],
      ["weight", "Weight log"],
      ["sleep", "Sleep report"],
      ["labs", "Lab report"],
      ["vaccinations", "Vaccination report"],
      ["doctor_visit", "Doctor visit summary"],
      ["emergency", "Emergency summary"],
    ];
    return `<section class="health-card">
      <h3>Printable reports</h3>
      <p class="muted tiny">Opens a clean page you can print or save as PDF for a physician.</p>
      <div class="health-print-grid">
        ${kinds
          .map(
            ([k, label]) =>
              `<button type="button" class="ghost-btn small health-print-btn" data-report="${esc(k)}">${esc(label)}</button>`
          )
          .join("")}
        <a class="ghost-btn small" href="/api/health/export" download="aria-health-export.json">Export JSON</a>
      </div>
    </section>`;
  }

  function renderProfile(home) {
    const p = home.profile || {};
    return `<section class="health-card">
      <h3>Emergency / identity profile</h3>
      <form id="healthProfileForm" class="health-checkin-grid">
        <label class="health-field">Name <input name="name" value="${esc(p.name || "")}" /></label>
        <label class="health-field">Date of birth <input name="dob" type="date" value="${esc(p.dob || "")}" /></label>
        <label class="health-field">Blood type <input name="blood_type" value="${esc(p.blood_type || "")}" /></label>
        <label class="health-field">Height (inches) <input name="height_in" type="number" step="0.1" value="${esc(p.height_in || "")}" /></label>
        <label class="health-field health-span2">Primary physician <input name="primary_physician" value="${esc(p.primary_physician || "")}" /></label>
        <label class="health-field health-span2">Specialists <input name="specialists" value="${esc(p.specialists || "")}" /></label>
        <label class="health-field health-span2">Emergency contacts <input name="emergency_contacts" value="${esc(p.emergency_contacts || "")}" /></label>
        <label class="health-field health-span2">Insurance (optional) <input name="insurance" value="${esc(p.insurance || "")}" /></label>
        <label class="health-field health-span2">Emergency notes <textarea name="emergency_notes" rows="3">${esc(p.emergency_notes || "")}</textarea></label>
        <div class="health-span2"><button type="submit" class="apply-btn small">Save profile</button></div>
      </form>
      <p class="health-trust muted">Highest trust: medications, allergies, conditions, blood type, emergency contacts, physicians, labs, vaccinations. Chat confirms before changing those. GUI save is explicit confirmation. Privacy default is local only — Aria never silently sends Health data to the internet.</p>
    </section>`;
  }

  async function renderFamily() {
    const data = await api("/api/health/family-history");
    const rows = data.entries || [];
    const relations = [
      "mother", "father", "sister", "brother", "maternal_grandmother", "maternal_grandfather",
      "paternal_grandmother", "paternal_grandfather", "grandmother", "grandfather",
      "daughter", "son", "aunt", "uncle", "cousin", "other",
    ];
    const table = rows.length
      ? `<table class="health-table"><thead><tr>
          <th>Relation</th><th>Condition</th><th>Age at dx</th><th>Cause of death</th><th>Notes</th>
        </tr></thead><tbody>${rows.map((r) => `<tr>
          <td>${esc(r.relation)}${provBadge(r)}</td>
          <td>${esc(r.condition)}</td>
          <td>${esc(r.age_at_diagnosis ?? "")}</td>
          <td>${esc(r.cause_of_death ?? "")}</td>
          <td>${esc(r.notes ?? "")}</td>
        </tr>`).join("")}</tbody></table>`
      : `<p class="muted">None recorded.</p>`;
    return `<section class="health-card">
      <h3>Family medical history</h3>
      <p class="muted tiny">${esc(data.boundary || "")}</p>
      ${table}
      <form id="healthFamilyForm" class="health-inline-form">
        <select name="relation">${relations.map((r) => `<option value="${esc(r)}">${esc(r.replaceAll("_", " "))}</option>`).join("")}</select>
        <input name="condition" placeholder="Condition" required />
        <input name="age_at_diagnosis" placeholder="Age at diagnosis" />
        <input name="cause_of_death" placeholder="Cause of death (optional)" />
        <input name="notes" placeholder="Notes" />
        <button type="submit" class="apply-btn small">Add entry</button>
      </form>
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderPreventive() {
    const data = await api("/api/health/preventive");
    const rows = data.items || [];
    const due = data.due || [];
    const catalog = data.catalog || [];
    const table = rows.length
      ? `<table class="health-table"><thead><tr>
          <th>Name</th><th>Status</th><th>Last done</th><th>Next due</th><th>Physician</th><th></th>
        </tr></thead><tbody>${rows.map((r) => `<tr>
          <td>${esc(r.name)}${provBadge(r)}</td>
          <td><span class="health-status-${esc(r.status === "overdue" ? "needs_attention" : r.status === "due" ? "needs_attention" : "stable")}">${esc(r.status || "")}</span></td>
          <td>${esc(r.last_done ?? "")}</td>
          <td>${esc(r.next_due ?? "")}</td>
          <td>${esc(r.physician ?? "")}</td>
          <td class="health-row-actions"><button type="button" class="ghost-btn small health-prev-complete" data-id="${esc(r.id)}">Complete</button></td>
        </tr>`).join("")}</tbody></table>`
      : `<p class="muted">None recorded.</p>`;
    return `<section class="health-card">
      <h3>Preventive care</h3>
      <p class="muted tiny">${esc(data.boundary || "")}</p>
      ${due.length ? `<p><strong>Due / overdue:</strong> ${due.map((d) => esc(d.name)).join(", ")}</p>` : ""}
      ${table}
      <form id="healthPreventiveForm" class="health-inline-form">
        <input name="name" placeholder="Screening name" required list="healthPreventiveCatalog" />
        <datalist id="healthPreventiveCatalog">${catalog.map((c) => `<option value="${esc(c.name)}"></option>`).join("")}</datalist>
        <input name="last_done" type="date" placeholder="Last done" />
        <input name="next_due" type="date" placeholder="Next due" />
        <input name="physician" placeholder="Physician" />
        <input name="facility" placeholder="Facility" />
        <button type="submit" class="apply-btn small">Add / update</button>
      </form>
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderNutrition() {
    const [data, habits] = await Promise.all([
      api("/api/health/nutrition"),
      api("/api/health/nutrition/habits"),
    ]);
    const counts = habits.counts || {};
    return `<section class="health-card">
      <h3>Nutrition habits</h3>
      <p class="muted tiny">${esc(habits.boundary || "")}</p>
      <div class="health-dash-grid">
        <div class="health-kpi">Meals (14d)<strong>${counts.meals ?? 0}</strong></div>
        <div class="health-kpi">Water notes<strong>${counts.water ?? 0}</strong></div>
        <div class="health-kpi">Alcohol notes<strong>${counts.alcohol ?? 0}</strong></div>
      </div>
      <pre class="health-pre muted tiny">${esc((habits.message || "").replace(/\*\*/g, ""))}</pre>
    </section>
    <section class="health-card">
      <h3>Recent nutrition log</h3>
      ${listTable(data.entries || [], [
        ["day", "Date"],
        ["kind", "Kind"],
        ["description", "Description"],
        ["meal_slot", "Meal"],
        ["notes", "Notes"],
      ])}
      <form id="healthNutritionForm" class="health-inline-form">
        <select name="kind">
          <option value="meal">Meal</option>
          <option value="water">Water</option>
          <option value="alcohol">Alcohol</option>
          <option value="snack">Snack</option>
          <option value="other">Other</option>
        </select>
        <input name="description" placeholder="What you ate / drank…" required style="min-width:14rem" />
        <input name="notes" placeholder="Notes (optional)" />
        <button type="submit" class="apply-btn small">Log</button>
      </form>
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderInsights() {
    const data = await api("/api/health/correlations");
    const obs = data.observations || [];
    const edu = obs.filter((o) => o.educational && !o.dismissed);
    const facts = obs.filter((o) => !o.educational && !o.dismissed);
    const list = (rows) =>
      rows.length
        ? `<ul>${rows.map((o) => `<li><strong>${esc(o.topic || o.kind || "observation")}</strong>${o.strength ? ` <span class="health-prov-badge muted tiny">${esc(o.strength)}</span>` : ""}: ${esc(o.statement || o.detail || "")}${provBadge(o)}</li>`).join("")}</ul>`
        : `<p class="muted">None yet.</p>`;
    return `<section class="health-card">
      <h3>Health insights</h3>
      <p class="muted tiny">${esc(data.boundary || "")}</p>
      <h4 class="muted tiny">Educational observations</h4>
      ${list(edu)}
      ${facts.length ? `<h4 class="muted tiny">Recorded facts</h4>${list(facts)}` : ""}
      <pre class="health-pre muted tiny">${esc((data.message || "").replace(/\*\*/g, ""))}</pre>
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderVisitPrep() {
    const data = await api("/api/health/visit-prep");
    return `<section class="health-card">
      <h3>Doctor visit preparation</h3>
      <p class="muted tiny">Organizes recorded facts for your next physician visit — not a diagnosis.</p>
      <pre class="health-pre">${esc(data.message || "Nothing to prepare yet.")}</pre>
      <div class="health-print-grid">
        <a class="ghost-btn small" href="/api/health/report?kind=visit_prep" target="_blank" rel="noopener">Open printable visit prep</a>
      </div>
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderBackups() {
    const data = await api("/api/health/backups");
    const rows = data.backups || [];
    const table = rows.length
      ? `<table class="health-table"><thead><tr>
          <th>File</th><th>Kind</th><th>Verify</th><th>Size</th><th></th>
        </tr></thead><tbody>${rows.map((r) => `<tr>
          <td>${esc(r.filename || r.id)}</td>
          <td>${esc(r.kind ?? "")}</td>
          <td>${esc(r.verify_status ?? "—")}</td>
          <td>${r.size_bytes != null ? esc(String(r.size_bytes) + " B") : "—"}</td>
          <td class="health-row-actions">
            <button type="button" class="ghost-btn small health-backup-verify" data-id="${esc(r.id)}">Verify</button>
            <button type="button" class="ghost-btn small health-backup-restore" data-id="${esc(r.id)}">Restore</button>
          </td>
        </tr>`).join("")}</tbody></table>`
      : `<p class="muted">No backups yet.</p>`;
    return `<section class="health-card">
      <h3>Encrypted backups</h3>
      <p class="muted tiny">This password protects the <strong>backup file</strong> if it leaves Aria. It is not your Aria Master Password. Store it safely — Aria cannot recover it.</p>
      ${table}
      <form id="healthBackupForm" class="health-inline-form">
        <input name="password" type="password" placeholder="Portable backup password (not Aria Master Password)" required autocomplete="off" />
        <input name="notes" placeholder="Notes (optional)" />
        <button type="submit" class="apply-btn small">Create backup</button>
      </form>
      <div id="healthBackupPreview" class="muted tiny"></div>
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function renderSecurity() {
    const data = await api("/api/health/auth/status");
    const grants = data.active_grants || {};
    const grantLines = Object.keys(grants).length
      ? `<ul>${Object.entries(grants).map(([k, v]) => `<li>${esc(k)} — ${esc(String(v))}s remaining</li>`).join("")}</ul>`
      : `<p class="muted">No active step-up grants.</p>`;
    const ops = (data.ops || []).map((o) => `<option value="${esc(o)}">${esc(o.replaceAll("_", " "))}</option>`).join("");
    return `<section class="health-card">
      <h3>Health security</h3>
      <p class="muted tiny">Health uses the house-wide Owner session. Opening Health does not ask for another Aria password. Sensitive operations confirm with your Aria Master Password (PIN is optional convenience). Encrypted backups use a separate portable-file password.</p>
      <div class="health-dash-grid">
        <div class="health-kpi">Step-up enabled<strong>${data.enabled ? "Yes" : "No"}</strong></div>
        <div class="health-kpi">Grant TTL<strong>${data.ttl != null ? esc(String(data.ttl)) + "s" : "—"}</strong></div>
      </div>
      <h4 class="muted tiny">Active grants</h4>
      ${grantLines}
      <form id="healthStepUpForm" class="health-inline-form">
        <select name="op"><option value="*">All sensitive ops</option>${ops}</select>
        <input name="pin" type="password" placeholder="Aria Master Password or PIN" required autocomplete="off" />
        <button type="submit" class="apply-btn small">Confirm step-up</button>
      </form>
      <p class="muted tiny">${esc(data.disclaimer || "")}</p>
    </section>`;
  }

  async function render() {
    const body = $("healthBody");
    if (!body) return;
    if (_tab === "timeline") body.innerHTML = await renderTimeline();
    else if (_tab === "dashboard") body.innerHTML = await renderDashboard();
    else if (_tab === "checkin") body.innerHTML = renderCheckin(_home || {});
    else if (_tab === "activity") body.innerHTML = await renderActivity();
    else if (_tab === "workouts") body.innerHTML = await renderWorkouts();
    else if (_tab === "goals") body.innerHTML = await renderGoals();
    else if (_tab === "trends") body.innerHTML = await renderTrends();
    else if (_tab === "journal") body.innerHTML = await renderJournal();
    else if (_tab === "knowledge") body.innerHTML = await renderKnowledge();
    else if (_tab === "providers") body.innerHTML = await renderProviders();
    else if (_tab === "procedures") body.innerHTML = await renderProcedures();
    else if (_tab === "family") body.innerHTML = await renderFamily();
    else if (_tab === "preventive") body.innerHTML = await renderPreventive();
    else if (_tab === "nutrition") body.innerHTML = await renderNutrition();
    else if (_tab === "insights") body.innerHTML = await renderInsights();
    else if (_tab === "visitprep") body.innerHTML = await renderVisitPrep();
    else if (_tab === "backups") body.innerHTML = await renderBackups();
    else if (_tab === "security") body.innerHTML = await renderSecurity();
    else if (_tab === "meds") body.innerHTML = await renderMeds(_home || {});
    else if (_tab === "supps") body.innerHTML = renderSupps(_home || {});
    else if (_tab === "recovery") body.innerHTML = await renderRecovery();
    else if (_tab === "history") body.innerHTML = renderHistory(_home || {});
    else if (_tab === "vitals") body.innerHTML = await renderVitals();
    else if (_tab === "labs") body.innerHTML = await renderLabs();
    else if (_tab === "docs") body.innerHTML = await renderDocs();
    else if (_tab === "questions") body.innerHTML = await renderQuestions(_home || {});
    else if (_tab === "coach") body.innerHTML = await renderCoach();
    else if (_tab === "consult") body.innerHTML = await renderConsult(_home || {});
    else if (_tab === "reminders") body.innerHTML = renderReminders(_home || {});
    else if (_tab === "print") body.innerHTML = renderPrint();
    else if (_tab === "profile") body.innerHTML = renderProfile(_home || {});
    bindBody();
  }

  function formObj(form) {
    const fd = new FormData(form);
    const out = {};
    for (const [k, v] of fd.entries()) {
      if (v === "") continue;
      out[k] = v;
    }
    return out;
  }

  function bindBody() {
    $("healthCheckinForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      ["overall", "energy", "mood", "stress", "pain", "sleep_hours", "sleep_quality", "weight", "bp_systolic", "bp_diastolic", "heart_rate", "blood_sugar", "temperature", "spo2"].forEach((k) => {
        if (payload[k] != null) payload[k] = Number(payload[k]);
      });
      await api("/api/health/checkin", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      status("Check-in saved.");
      await loadHome();
    });
    $("healthMedForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/medications", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...formObj(e.target), status: "current" }) });
      status("Medication saved.");
      await loadHome();
    });
    $("healthDoseForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/doses", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Dose logged.");
      await render();
    });
    $("healthRecoveryForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      if (payload.pain != null) payload.pain = Number(payload.pain);
      await api("/api/health/recovery", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      status("Recovery event saved.");
      await render();
    });
    $("healthVisitForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/visits", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Visit saved.");
      await render();
    });
    $("healthDocKindFilter")?.addEventListener("change", () => render());
    $("healthDocSearch")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") render();
    });
    $("healthSuppForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/supplements", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...formObj(e.target), status: "current" }) });
      status("Supplement saved.");
      await loadHome();
    });
    $("healthCondForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/conditions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Condition saved.");
      await loadHome();
    });
    $("healthAllergyForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/allergies", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Allergy saved.");
      await loadHome();
    });
    $("healthVaxForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/vaccinations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Vaccination saved.");
      await loadHome();
    });
    $("healthQuestionForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/questions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Doctor question saved.");
      await loadHome();
    });
    document.querySelectorAll(".health-q-done").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await api(`/api/health/questions/${encodeURIComponent(btn.dataset.id)}/status`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: "answered" }),
        });
        status("Marked answered.");
        await loadHome();
      });
    });
    $("healthActivityForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      ["duration_min", "distance", "steps", "heart_rate"].forEach((k) => {
        if (payload[k] != null) payload[k] = Number(payload[k]);
      });
      await api("/api/health/activities", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      status("Activity saved.");
      await render();
    });
    $("healthWorkoutForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      const sets = [];
      if (payload.exercise) {
        sets.push({
          exercise: payload.exercise,
          sets: payload.sets ? Number(payload.sets) : null,
          reps: payload.reps ? Number(payload.reps) : null,
          weight: payload.weight ? Number(payload.weight) : null,
          band_color: payload.band_color || "",
          resistance: payload.resistance || "",
          difficulty: payload.difficulty || "",
          pain: payload.pain ? Number(payload.pain) : null,
        });
      }
      ["exercise", "sets", "reps", "weight", "band_color", "resistance"].forEach((k) => delete payload[k]);
      if (payload.duration_min) payload.duration_min = Number(payload.duration_min);
      if (payload.pain) payload.pain = Number(payload.pain);
      payload.title = payload.title || payload.template;
      payload.sets = sets;
      await api("/api/health/workouts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      status("Workout saved.");
      await render();
    });
    $("healthGoalForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      ["target_value", "per_week"].forEach((k) => {
        if (payload[k] != null) payload[k] = Number(payload[k]);
      });
      await api("/api/health/goals", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      status("Goal saved.");
      await loadHome();
    });
    $("healthJournalForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/journal", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Health journal saved.");
      await render();
    });
    $("healthKnowledgeForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/knowledge", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Knowledge saved.");
      await render();
    });
    $("healthProviderForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/providers", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Provider saved.");
      await render();
    });
    $("healthProcedureForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/procedures", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Procedure saved.");
      await render();
    });
    $("healthFamilyForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await apiGate("/api/health/family-history", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) }, "edit_family_history");
      status("Family history saved.");
      await render();
    });
    $("healthPreventiveForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/preventive", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Preventive care saved.");
      await render();
    });
    document.querySelectorAll(".health-prev-complete").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await api(`/api/health/preventive/${encodeURIComponent(btn.dataset.id)}/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        status("Marked complete.");
        await render();
      });
    });
    $("healthNutritionForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/nutrition", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formObj(e.target)) });
      status("Nutrition logged.");
      await render();
    });
    $("healthBackupForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      const out = await apiGate("/api/health/backups", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }, "backup_create");
      status(out.message || "Backup created.");
      await render();
    });
    document.querySelectorAll(".health-backup-verify").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const out = await api(`/api/health/backups/${encodeURIComponent(btn.dataset.id)}/verify`, { method: "POST" });
        status(out.message || "Verify complete.");
        await render();
      });
    });
    document.querySelectorAll(".health-backup-restore").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const password = window.ariaPrompt
          ? await window.ariaPrompt("Enter the portable backup password (not your Aria Master Password) to preview restore:", "", {
              title: "Restore backup file",
              okLabel: "Preview",
            })
          : window.prompt("Enter the portable backup password to preview restore:");
        if (!password?.trim()) return;
        const preview = await apiGate(
          "/api/health/backups/restore-preview",
          { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ backup_id: btn.dataset.id, password: password.trim() }) },
          "backup_restore"
        );
        const counts = preview.record_counts || {};
        const summary = Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join(", ");
        const box = $("healthBackupPreview");
        if (box) box.textContent = summary ? `Preview: ${summary}` : "";
        const restoreMsg = `Restore this backup (merge mode)?\n\n${summary || preview.message || "Review counts before confirming."}`;
        const restoreOk = window.ariaConfirm
          ? await window.ariaConfirm(restoreMsg, { title: "Restore backup", okLabel: "Restore" })
          : window.confirm(restoreMsg);
        if (!restoreOk) return;
        const out = await apiGate(
          "/api/health/backups/restore",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ backup_id: btn.dataset.id, password: password.trim(), mode: "merge", confirm: true }),
          },
          "backup_restore"
        );
        status(out.message || "Restore complete.");
        await loadHome();
      });
    });
    $("healthStepUpForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      const out = await stepUp(payload.op || "*", payload.pin);
      status(out.message || "Step-up confirmed.");
      await render();
    });
    $("healthSafetyBtn")?.addEventListener("click", async () => {
      const data = await api("/api/health/safety");
      const box = $("healthSafetyBox");
      if (box) box.textContent = data.message || "";
      status("Educational interaction scan complete.");
    });
    $("healthReminderForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await api("/api/health/reminders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...formObj(e.target), enabled: 1 }) });
      status("Reminder saved.");
      await loadHome();
    });
    $("healthSecondForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      const data = await api("/api/health/second-opinion/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const box = $("healthConsultPreview");
      if (box) box.innerHTML = `<pre class="health-pre">${esc(data.message || "")}</pre>`;
      status("Second-opinion preview ready — nothing sent.");
    });
    $("healthConsultForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      payload.include_docs = payload.level === "full";
      const data = await api("/api/health/consult/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const box = $("healthConsultPreview");
      if (box) {
        box.innerHTML = `<pre class="health-pre">${esc(data.message || "")}</pre>
          <div class="health-pending-actions">
            <button type="button" class="apply-btn small" id="healthConsultSend" data-id="${esc(data.consultation_id || "")}">Send consultation</button>
            <button type="button" class="ghost-btn small" id="healthConsultCancel" data-id="${esc(data.consultation_id || "")}">Cancel</button>
          </div>`;
        $("healthConsultSend")?.addEventListener("click", async () => {
          const out = await api(`/api/health/consult/${encodeURIComponent(data.consultation_id)}/send`, { method: "POST" });
          status(out.message || "Consultation complete.");
          await loadHome();
        });
        $("healthConsultCancel")?.addEventListener("click", async () => {
          await api(`/api/health/consult/${encodeURIComponent(data.consultation_id)}/cancel`, { method: "POST" });
          status("Consultation cancelled. Nothing was sent.");
          await loadHome();
        });
      }
    });
    $("healthConfirmYes")?.addEventListener("click", async () => {
      await api("/api/health/confirm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm: true }) });
      status("Health Record updated.");
      await loadHome();
    });
    $("healthConfirmNo")?.addEventListener("click", async () => {
      await api("/api/health/confirm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm: false }) });
      status("Cancelled. Health Record unchanged.");
      await loadHome();
    });
    $("healthTimelineFilter")?.addEventListener("change", () => render());
    $("healthLabForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      if (payload.value != null) payload.value = Number(payload.value);
      await api("/api/health/labs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      status("Lab saved.");
      await render();
    });
    $("healthDocForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const res = await fetch("/api/health/documents", { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) throw new Error(data.message || "Upload failed");
      status(data.ocr ? "Document stored and OCR indexed." : "Document stored.");
      await render();
    });
    $("healthProfileForm")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = formObj(e.target);
      if (payload.height_in != null) payload.height_in = Number(payload.height_in);
      await api("/api/health/profile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      status("Profile saved.");
      await loadHome();
    });
    $("healthVitalRange")?.addEventListener("change", () => render());
    bodyPrintBinds();
  }

  function closeHealthReportModal() {
    document.getElementById("healthReportModal")?.remove();
  }

  async function openHealthReport(kind) {
    const k = String(kind || "emergency").trim() || "emergency";
    try {
      const res = await fetch(`/api/health/report?kind=${encodeURIComponent(k)}`, {
        headers: { Accept: "text/html" },
      });
      const html = await res.text();
      if (!res.ok) throw new Error(`Report failed (${res.status})`);
      closeHealthReportModal();
      if (!document.getElementById("healthReportModalStyle")) {
        const style = document.createElement("style");
        style.id = "healthReportModalStyle";
        style.textContent = `
          .health-report-modal{position:fixed;inset:0;z-index:12000;background:rgba(8,12,18,.55);display:flex;align-items:center;justify-content:center;padding:1.5rem}
          .health-report-modal__panel{background:var(--panel,#111827);color:inherit;width:min(960px,96vw);height:min(860px,92vh);border-radius:12px;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.35)}
          .health-report-modal__head{display:flex;align-items:center;justify-content:space-between;gap:.75rem;padding:.75rem 1rem;border-bottom:1px solid rgba(255,255,255,.08)}
          .health-report-modal__actions{display:flex;gap:.5rem}
          .health-report-modal__frame{flex:1;width:100%;border:0;background:#fff}
        `;
        document.head.appendChild(style);
      }
      const modal = document.createElement("div");
      modal.id = "healthReportModal";
      modal.className = "health-report-modal";
      modal.setAttribute("role", "dialog");
      modal.setAttribute("aria-modal", "true");
      modal.setAttribute("aria-label", "Health report");
      modal.innerHTML = `
        <div class="health-report-modal__panel">
          <header class="health-report-modal__head">
            <strong>Health report</strong>
            <div class="health-report-modal__actions">
              <button type="button" class="ghost-btn small" id="healthReportPrintBtn">Print</button>
              <button type="button" class="ghost-btn small" id="healthReportCloseBtn">Close</button>
            </div>
          </header>
          <iframe id="healthReportFrame" class="health-report-modal__frame" title="Health report"></iframe>
        </div>`;
      document.body.appendChild(modal);
      const frame = modal.querySelector("#healthReportFrame");
      if (frame) {
        frame.srcdoc = html;
      }
      modal.querySelector("#healthReportCloseBtn")?.addEventListener("click", closeHealthReportModal);
      modal.querySelector("#healthReportPrintBtn")?.addEventListener("click", () => {
        try {
          frame?.contentWindow?.focus();
          frame?.contentWindow?.print();
        } catch (_) {
          /* ignore */
        }
      });
      modal.addEventListener("click", (e) => {
        if (e.target === modal) closeHealthReportModal();
      });
      status(`Opened ${k.replace(/_/g, " ")} report in Health.`);
    } catch (err) {
      status(err?.message || "Could not open report");
      window.showAriaToast?.(err?.message || "Could not open report", "err", 5000);
    }
  }

  function bodyPrintBinds() {
    document.querySelectorAll(".health-print-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        openHealthReport(btn.dataset.report || "summary");
      });
    });
    document.querySelectorAll('a[href*="/api/health/report"]').forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const href = a.getAttribute("href") || "";
        const kind = new URL(href, location.origin).searchParams.get("kind") || "summary";
        openHealthReport(kind);
      });
    });
  }

  async function loadHome() {
    _home = await api("/api/health/home");
    const disc = $("healthDisclaimer");
    if (disc) disc.textContent = _home.disclaimer || "";
    await render();
  }

  function bindChrome() {
    document.querySelectorAll(".health-tab").forEach((tab) => {
      tab.addEventListener("click", async () => {
        _tab = tab.dataset.htab || "checkin";
        document.querySelectorAll(".health-tab").forEach((t) => t.classList.toggle("active", t === tab));
        await render();
      });
    });
    $("healthRefreshBtn")?.addEventListener("click", () => loadHome().catch((err) => status(err.message)));
    $("healthUploadBtn")?.addEventListener("click", () => $("healthUploadInput")?.click());
    $("healthUploadInput")?.addEventListener("change", async (e) => {
      const file = e.target?.files?.[0];
      if (!file) return;
      try {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("title", file.name || "Upload");
        fd.append("kind", "document");
        const res = await fetch("/api/health/documents", { method: "POST", body: fd });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) throw new Error(data.message || "Upload failed");
        status(data.ocr ? "Document stored and OCR indexed." : "Document stored.");
        _tab = "docs";
        document.querySelectorAll(".health-tab").forEach((t) =>
          t.classList.toggle("active", t.dataset.htab === "docs"),
        );
        await render();
      } catch (err) {
        status(err?.message || "Upload failed");
        window.showAriaToast?.(err?.message || "Upload failed", "err", 5000);
      } finally {
        e.target.value = "";
      }
    });
    // BUG-023: keep Health reports inside the SPA (no raw /api navigation).
    $("healthDoctorBtn")?.addEventListener("click", () => openHealthReport("doctor_visit"));
    $("healthEmergencyBtn")?.addEventListener("click", () => openHealthReport("emergency"));
    $("healthSearchBtn")?.addEventListener("click", runSearch);
    $("healthSearch")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runSearch();
    });
    $("healthNlBtn")?.addEventListener("click", runNl);
    $("healthNl")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") runNl();
    });
  }

  async function runSearch() {
    const q = $("healthSearch")?.value || "";
    if (!q.trim()) return;
    const data = await api(`/api/health/search?q=${encodeURIComponent(q)}`);
    $("healthBody").innerHTML = `<section class="health-card"><h3>Search</h3><pre class="health-pre">${esc(data.message || "No matches.")}</pre></section>`;
  }

  async function runNl() {
    const text = $("healthNl")?.value || "";
    if (!text.trim()) return;
    const data = await api("/api/health/nl", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    status(data.message || "Updated.");
    $("healthNl").value = "";
    await loadHome();
  }

  async function initHealth() {
    try {
      if (!_inited) {
        bindChrome();
        _inited = true;
      }
      await loadHome();
    } catch (err) {
      if (window.AriaNet?.isRoomAbort?.(err)) return;
      status(err.message || "Health failed to load");
    }
  }

  window.initHealth = initHealth;
})();
