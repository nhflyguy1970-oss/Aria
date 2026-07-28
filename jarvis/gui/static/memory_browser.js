/** Memory browser, cheatsheets, knowledge research, profile — extracted from app.js. */
(function () {
  "use strict";

async function loadCheatsheets(selectKey) {
  const sel = document.getElementById("cheatsheetSelect");
  if (!sel) return;
  try {
    const res = await fetch("/api/cheatsheets");
    const data = await res.json();
    const items = data.cheatsheets || [];
    sel.innerHTML = `<option value="">— choose —</option>${items.map((c) =>
      `<option value="${window.escapeHtml(c.key)}">${window.escapeHtml(c.key)} — ${window.escapeHtml(c.title)}</option>`
    ).join("")}`;
    if (selectKey) sel.value = selectKey;
  } catch (err) {
    window.showAriaToast?.(err?.message || "Could not load cheatsheets", "err", 4000);
  }
}

async function showCheatsheet(key) {
  const box = document.getElementById("cheatsheetContent");
  if (!key || !box) return;
  try {
    const res = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      window.showAriaToast?.(data.error || data.message || "Cheatsheet not found", "err", 5000);
      return;
    }
    box.textContent = data.cheatsheet?.content || "";
    box.classList.remove("hidden");
  } catch (err) {
    window.showAriaToast?.(err?.message || "Could not load cheatsheet", "err", 5000);
  }
}

let memorySettingsSaveInFlight = 0;

function applyMemorySettingsToUi(data) {
  if (!data || !data.ok) return;
  const modeEl = document.getElementById("memoryAutoMode");
  if (modeEl && data.auto_memory_mode) modeEl.value = data.auto_memory_mode;
  const brainEl = document.getElementById("memoryBrainMode");
  if (brainEl) brainEl.checked = data.brain_mode !== false;
  const journalLearnEl = document.getElementById("memoryAutoJournalLearn");
  if (journalLearnEl) {
    const bl = data.brain_learning || {};
    journalLearnEl.checked = data.auto_journal_learn === true
      || (data.auto_journal_learn == null && bl.auto_journal_learn === true);
  }
  const docLearnEl = document.getElementById("memoryAutoDocumentLearn");
  if (docLearnEl) {
    const bl = data.brain_learning || {};
    docLearnEl.checked = data.auto_document_learn === true
      || (data.auto_document_learn == null && bl.auto_document_learn === true);
  }
  const cpEl = document.getElementById("memoryAutoCheckpoint");
  if (cpEl) cpEl.checked = data.auto_checkpoint !== false;
  const nsEl = document.getElementById("memoryAutoNamespace");
  if (nsEl) nsEl.checked = data.auto_namespace !== false;
  const promptEl = document.getElementById("memoryInPrompt");
  if (promptEl) promptEl.checked = data.memory_in_system_prompt !== false;
}

async function loadMemorySettings() {
  if (memorySettingsSaveInFlight > 0) return;
  try {
    const res = await fetch("/api/memory/settings");
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      window.showAriaToast?.(data.message || data.error || `Memory settings unavailable (${res.status})`, "err", 4000);
      return;
    }
    applyMemorySettingsToUi(data);
  } catch (err) {
    window.showAriaToast?.(err?.message || "Could not load memory settings", "err", 4000);
  }
}

async function saveMemorySettings(patch) {
  memorySettingsSaveInFlight += 1;
  try {
    const res = await fetch("/api/memory/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      const err = new Error(data.message || `Could not save settings (HTTP ${res.status})`);
      err.locked = res.status === 423 || data.locked;
      throw err;
    }
    applyMemorySettingsToUi(data);
    return data;
  } finally {
    memorySettingsSaveInFlight = Math.max(0, memorySettingsSaveInFlight - 1);
  }
}

function bindMemorySettingCheckbox(id, key) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("change", async (e) => {
    const target = e.target;
    const want = target.checked;
    try {
      await saveMemorySettings({ [key]: want });
    } catch (err) {
      target.checked = !want;
      if (err.locked) window.jarvisShowLock?.();
      window.showAriaToast?.(err.message || "Could not save memory setting", "warn", 6000);
    }
  });
}

async function loadMemoryConflicts() {
  const box = document.getElementById("memoryConflicts");
  if (!box) return;
  try {
    const res = await fetch("/api/memory/conflicts");
    const data = await res.json().catch(() => ({}));
    const conflicts = data.conflicts || [];
    if (!conflicts.length) {
      box.innerHTML = `<p class="muted">No belief conflicts right now.</p>`;
      return;
    }
    box.innerHTML = conflicts.map((c, i) => {
      const a = c.a || c.keep || {};
      const b = c.b || c.drop || {};
      const aId = a.id || c.keep_id || "";
      const bId = b.id || c.drop_id || "";
      return `<div class="memory-conflict-card">
        <p class="muted">${window.escapeHtml(c.reason || "Conflicting beliefs")}</p>
        <div class="memory-conflict-pair">
          <div><strong>A</strong> ${window.escapeHtml(a.content || "")}</div>
          <div><strong>B</strong> ${window.escapeHtml(b.content || "")}</div>
        </div>
        <div class="memory-conflict-actions">
          <button type="button" class="ghost-btn small mem-keep-a" data-drop="${window.escapeHtml(bId)}">Keep A (cool B)</button>
          <button type="button" class="ghost-btn small mem-keep-b" data-drop="${window.escapeHtml(aId)}">Keep B (cool A)</button>
        </div>
      </div>`;
    }).join("");
    box.querySelectorAll(".mem-keep-a, .mem-keep-b").forEach((btn) => {
      btn.onclick = async () => {
        const drop = btn.dataset.drop;
        if (!drop) return;
        const ok = await memoryConfirm("Cool the other belief? Prefer Cool over erase.", "Resolve conflict");
        if (!ok) return;
        const res = await fetch("/api/memory/conflicts/resolve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ drop_id: drop }),
        });
        const data = await res.json().catch(() => ({}));
        window.showAriaToast?.(data.ok ? "Conflict resolved" : (data.error || "Failed"), data.ok ? "ok" : "err", 3500);
        loadMemoryBrowser();
      };
    });
    // Conflict coach
    const coach = document.getElementById("memoryConflictCoach");
    if (coach) {
      fetch("/api/memory/conflict-coach").then((r) => r.json()).then((d) => {
        const rows = d.conflicts || [];
        coach.innerHTML = rows.slice(0, 3).map((x) =>
          `<p><strong>Coach:</strong> ${window.escapeHtml(x.why || "")} — <em>${window.escapeHtml(x.recommendation || "")}</em></p>`
        ).join("");
      }).catch(() => {});
    }
  } catch (err) {
    box.innerHTML = `<p class="muted">Conflicts unavailable</p>`;
  }
}

async function loadMemoryTrustStatus() {
  const el = document.getElementById("memoryTrustStatus");
  if (!el) return;
  try {
    const res = await fetch("/api/memory/trust/status");
    const data = await res.json();
    if (!data.ok) return;
    const parts = [
      `Trust: ${data.strategies || 0} rules`,
      `${data.failures || 0} coding failures logged`,
    ];
    if (data.artifact_entries_remaining) {
      parts.push(`${data.artifact_entries_remaining} test artifact(s) — use Scrub`);
    }
    if (data.last_scrub_on_startup) {
      parts.push(`scrubbed ${data.last_scrub_on_startup} on last start`);
    }
    el.textContent = parts.join(" · ");
  } catch {
    el.textContent = "";
  }
}

async function loadEnvironmentPreferences() {
  const form = document.getElementById("envPrefsForm");
  if (!form) return;
  try {
    const res = await fetch("/api/memory/environment/preferences");
    const data = await res.json();
    const items = data.preferences || [];
    form.innerHTML = items.map((p) => `
      <div class="env-pref-field" data-key="${window.escapeHtml(p.key)}">
        <label for="envPref-${window.escapeHtml(p.key)}">${window.escapeHtml(p.label)}</label>
        <textarea id="envPref-${window.escapeHtml(p.key)}" rows="2" placeholder="${window.escapeHtml(p.hint || "")}">${window.escapeHtml(p.content || "")}</textarea>
      </div>`).join("");
  } catch (_) {
    form.innerHTML = "<p class=\"muted\">Could not load stack preferences.</p>";
  }
}

async function saveEnvironmentPreferences() {
  const form = document.getElementById("envPrefsForm");
  if (!form) return;
  const preferences = [];
  form.querySelectorAll(".env-pref-field").forEach((field) => {
    const key = field.dataset.key;
    const ta = field.querySelector("textarea");
    if (key && ta) preferences.push({ key, content: ta.value });
  });
  try {
    const res = await fetch("/api/memory/environment/preferences", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preferences }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      window.showAriaToast?.(data.error || data.message || `Save failed (${res.status})`, "err", 5000);
      return;
    }
    window.showAriaToast?.("Environment preferences saved", "ok", 2500);
    loadMemoryBrowser();
  } catch (err) {
    window.showAriaToast?.(err?.message || "Could not save preferences", "err", 5000);
  }
}

function setKnowledgeResearchStatus(text, busy = false) {
  const el = document.getElementById("knowledgeResearchStatus");
  if (!el) return;
  el.textContent = text || "";
  el.classList.toggle("busy", Boolean(busy && text));
}

function knowledgeKindLabel(kind) {
  if (kind === "intel") return "General";
  if (kind === "personal") return "Personal";
  if (kind === "profile") return "Profile";
  return "Stack";
}

function renderKnowledgeResearchBrief(b) {
  const day = b.last_day || b.updated || "";
  const label = knowledgeKindLabel(b.kind || "stack");
  return `<li><span class="knowledge-kind-badge knowledge-kind-${window.escapeHtml(b.kind || "stack")}">${window.escapeHtml(label)}</span> <button type="button" class="ghost-btn tiny knowledge-research-link" data-slug="${window.escapeHtml(b.slug)}"><strong>${window.escapeHtml(b.title || b.slug)}</strong></button> <span class="muted">${window.escapeHtml(day)}</span></li>`;
}

function renderKnowledgeResearchTopics(categories) {
  const byKind = { stack: [], intel: [], personal: [], profile: [] };
  for (const c of categories) {
    const k = c.kind || "stack";
    (byKind[k] || byKind.stack).push(c);
  }
  const parts = [];
  if (byKind.profile.length) {
    parts.push(
      `<strong>From your profile (nightly):</strong> ${byKind.profile.map((c) => window.escapeHtml(c.title)).join(" · ")}`,
    );
  }
  if (byKind.stack.length) {
    parts.push(
      `<strong>Stack (nightly):</strong> ${byKind.stack.map((c) => window.escapeHtml(c.title)).join(" · ")}`,
    );
  }
  if (byKind.intel.length) {
    parts.push(
      `<strong>General (rotating, 4/night):</strong> ${byKind.intel.map((c) => window.escapeHtml(c.title)).join(" · ")}`,
    );
  }
  if (byKind.personal.length) {
    parts.push(
      `<strong>Personal:</strong> ${byKind.personal.map((c) => window.escapeHtml(c.title)).join(" · ")}`,
    );
  }
  return parts.join("<br>");
}

async function waitForCodingJobResult(jobId, { onProgress } = {}) {
  const maxAttempts = 240;
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((r) => setTimeout(r, 1500));
    const res = await fetch(`/api/coding/job/${encodeURIComponent(jobId)}`);
    const job = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(job.message || `HTTP ${res.status}`);
    onProgress?.(job);
    if (job.done) return job;
  }
  throw new Error("Job timed out");
}

async function runKnowledgeResearchNow() {
  const runBtn = document.getElementById("knowledgeResearchRunBtn");
  const jobsBtn = document.getElementById("knowledgeResearchJobsBtn");
  if (!runBtn || runBtn.dataset.busy === "1") return;
  runBtn.dataset.busy = "1";
  runBtn.disabled = true;
  jobsBtn?.classList.add("hidden");
  setKnowledgeResearchStatus("Starting knowledge research…", true);
  try {
    window.showAriaToast?.("Running knowledge research (may take a few minutes)…", "info", 8000);
    const res = await fetch("/api/knowledge/research/daily", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force: true }),
    });
    const data = await res.json();
    if (data.pending && data.job_id) {
      jobsBtn?.classList.remove("hidden");
      setKnowledgeResearchStatus("Research queued — searching web and writing briefs…", true);
      try {
        const job = await waitForCodingJobResult(data.job_id, {
          onProgress: (j) => {
            const msg = j.message || "Running…";
            setKnowledgeResearchStatus(`Research in progress — ${msg}`, true);
          },
        });
        jobsBtn?.classList.add("hidden");
        const errText = job.error || job.result?.message || "";
        if (job.result?.ok) {
          setKnowledgeResearchStatus("Research complete.", false);
          window.showAriaToast?.(job.result.message || "Research complete", "ok", 8000);
          loadMemoryBrowser();
        } else if (String(errText).includes("knowledge_research_run")) {
          setKnowledgeResearchStatus("Handler missing — restart Jarvis server, then try again.", false);
          window.showAriaToast?.("Research handler missing — restart Jarvis server, then try again.", "err", 10000);
        } else {
          setKnowledgeResearchStatus(errText || "Research failed.", false);
          window.showAriaToast?.(errText || "Research failed", "err", 8000);
        }
      } catch (_) {
        setKnowledgeResearchStatus(
          "Still running in the background — click View job progress or Services → Background jobs.",
          false,
        );
        window.showAriaToast?.("Research still running — opening Job center…", "info", 8000);
        window.jarvisJobs?.openJobCenter?.();
      }
    } else if (data.ok) {
      setKnowledgeResearchStatus(data.message || "Research complete.", false);
      window.showAriaToast?.(data.message || "Research complete", "ok", 8000);
      loadMemoryBrowser();
    } else {
      setKnowledgeResearchStatus(data.message || "Research failed.", false);
      window.showAriaToast?.(data.message || "Research failed", "err", 8000);
    }
  } catch (e) {
    setKnowledgeResearchStatus(e.message || "Request failed.", false);
    window.showAriaToast?.(e.message || "Request failed", "err", 8000);
  } finally {
    runBtn.dataset.busy = "0";
    runBtn.disabled = false;
  }
}

async function loadKnowledgeResearchPanel() {
  let rRes;
  try {
    rRes = await fetch("/api/knowledge/research");
  } catch (e) {
    window.showAriaToast?.(e.message || "Could not load research", "err", 5000);
    return;
  }
  if (!rRes.ok) {
    window.showAriaToast?.(`Could not load research (${rRes.status})`, "err", 5000);
    return;
  }
  const rData = await rRes.json();
  const topicsEl = document.getElementById("knowledgeResearchTopics");
  if (topicsEl) {
    const cats = rData.categories || [];
    topicsEl.innerHTML = cats.length ? renderKnowledgeResearchTopics(cats) : "";
  }
  const rEl = document.getElementById("knowledgeResearchList");
  if (rEl) {
    const briefs = rData.briefs || [];
    const last = rData.last_run_day ? ` · last run ${window.escapeHtml(rData.last_run_day)}` : "";
    rEl.innerHTML = briefs.length
      ? briefs.map((b) => renderKnowledgeResearchBrief(b)).join("") + `<li class="muted">${briefs.length} brief(s)${last}</li>`
      : `<li class="muted">No nightly research yet${last}. <button type="button" class="ghost-btn tiny" id="researchEmptyRunBtn">Run research now</button> or <button type="button" class="ghost-btn tiny" id="researchEmptyChatBtn">ask Chat</button>.</li>`;
    rEl.querySelector("#researchEmptyRunBtn")?.addEventListener("click", () => {
      document.getElementById("knowledgeResearchRunBtn")?.click();
    });
    rEl.querySelector("#researchEmptyChatBtn")?.addEventListener("click", () => {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.("Run nightly knowledge research now");
    });
    rEl.querySelectorAll(".knowledge-research-link").forEach((btn) => {
      btn.onclick = async () => {
        const slug = btn.dataset.slug;
        if (!slug) return;
        try {
          const res = await fetch(`/api/knowledge/research/${encodeURIComponent(slug)}`);
          const brief = await res.json();
          if (!brief.ok) {
            window.showAriaToast?.(brief.message || "Could not load brief", "err", 5000);
            return;
          }
          const preview = (brief.markdown || "").slice(0, 8000);
          const w = window.open("", "_blank", "width=720,height=640");
          if (w) {
            w.document.write(`<pre style="font:14px/1.5 sans-serif;padding:1rem;white-space:pre-wrap">${window.escapeHtml(preview)}</pre>`);
            w.document.title = slug;
          } else {
            window.showAriaToast?.(preview.slice(0, 500), "info", 8000);
          }
        } catch (e) {
          window.showAriaToast?.(e.message || "Load failed", "err", 5000);
        }
      };
    });
  }
}

async function loadProfileInlinePanel() {
  const el = document.getElementById("profileInlineContent");
  if (!el) return;
  try {
    const [qRes, mRes] = await Promise.all([
      fetch("/api/profile/questionnaire"),
      fetch("/api/memory/all?namespace=profile"),
    ]);
    const data = await qRes.json();
    const mem = await mRes.json();
    const questions = data.questions?.length ? data.questions : [];
    const entries = (mem.entries || []).filter((e) => !(e.tags || []).includes("summary"));
    if (entries.length) {
      el.innerHTML = entries.map((e) =>
        `<div class="profile-inline-row"><span>${window.escapeHtml(e.content || "")}</span></div>`
      ).join("");
    } else if (!data.completed && questions.length) {
      el.innerHTML = `<p>Questionnaire not completed — ${questions.length} questions waiting.</p>`;
      renderProfileForm(questions);
      document.getElementById("profileModal")?.classList.remove("hidden");
    } else if (data.completed) {
      el.innerHTML = "<p>Profile completed. Click <strong>Edit answers</strong> to update your questionnaire.</p>";
    } else {
      el.innerHTML = `<p>No profile answers yet. <button type="button" class="ghost-btn tiny" id="profileEmptyEditBtn">Edit answers</button></p>`;
      el.querySelector("#profileEmptyEditBtn")?.addEventListener("click", () => {
        document.getElementById("profileInlineEditBtn")?.click()
          || document.getElementById("profileModal")?.classList.remove("hidden");
      });
    }
  } catch (e) {
    el.textContent = e.message || "Could not load profile";
  }
}

function closeMemoryDialog() {
  document.getElementById("memoryDialog")?.classList.add("hidden");
}

function openMemoryDialog(title, bodyHtml, actions) {
  const dlg = document.getElementById("memoryDialog");
  const titleEl = document.getElementById("memoryDialogTitle");
  const body = document.getElementById("memoryDialogBody");
  const acts = document.getElementById("memoryDialogActions");
  if (!dlg || !body || !acts) return Promise.resolve(null);
  if (titleEl) titleEl.textContent = title;
  body.innerHTML = bodyHtml;
  acts.innerHTML = "";
  dlg.classList.remove("hidden");
  return new Promise((resolve) => {
    (actions || []).forEach((a) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = a.primary ? "apply-btn small" : "ghost-btn small";
      btn.textContent = a.label;
      btn.onclick = () => {
        if (a.keepOpen) {
          resolve(a.value);
          return;
        }
        closeMemoryDialog();
        resolve(a.value);
      };
      acts.appendChild(btn);
    });
  });
}

function memoryConfirm(message, title = "Confirm") {
  return openMemoryDialog(
    title,
    `<p>${window.escapeHtml(message)}</p>`,
    [
      { label: "Cancel", value: false },
      { label: "Confirm", value: true, primary: true },
    ],
  );
}

function renderMemoryCard(e) {
  const conf = e.confidence != null ? Math.round(Number(e.confidence) * 100) : null;
  return `<article class="memory-cog-card" data-id="${window.escapeHtml(e.id || "")}" tabindex="0">
    <header class="memory-cog-card-head">
      <span class="memory-badge type-${window.escapeHtml(e.type || "fact")}">${window.escapeHtml(e.type || "fact")}</span>
      <span class="memory-badge ns">${window.escapeHtml(e.namespace || "default")}</span>
      ${conf != null ? `<span class="memory-conf">${conf}%</span>` : ""}
    </header>
    <h4 class="memory-cog-title">${window.escapeHtml(e.title || e.content || "")}</h4>
    <p class="memory-why muted">${window.escapeHtml(e.why || "")}</p>
    <p class="memory-prov muted">Source: ${window.escapeHtml(e.source || "memory")}
      ${e.when_learned ? ` · learned ${window.escapeHtml(String(e.when_learned).slice(0, 10))}` : ""}</p>
    <div class="memory-item-actions">
      <button type="button" class="ghost-btn tiny memory-edit-btn" data-id="${window.escapeHtml(e.id || "")}">Edit</button>
      <button type="button" class="ghost-btn tiny memory-correct-btn" data-id="${window.escapeHtml(e.id || "")}">Correct</button>
      <button type="button" class="ghost-btn tiny memory-forget-btn" data-id="${window.escapeHtml(e.id || "")}">Forget</button>
    </div>
  </article>`;
}

async function loadCognitiveHome() {
  try {
    const res = await fetch("/api/memory/home");
    const home = await res.json();
    if (!res.ok || !home.ok) return;

    const safety = document.getElementById("memorySafetyBody");
    if (safety) {
      const s = home.safety || {};
      safety.innerHTML = `<ul class="memory-health-list">
        <li><strong>Authority:</strong> ${window.escapeHtml(s.source_of_truth || "acm")} ${s.primary ? "(PRIMARY)" : ""}</li>
        <li>Fail-closed writes: ${s.fail_closed ? "yes" : "no"}</li>
        <li>Candidates are not memory until Adopt</li>
        <li>Legacy vault is forensic only</li>
      </ul>`;
    }
    const health = document.getElementById("memoryHealthBody");
    if (health) {
      const h = home.health || {};
      health.innerHTML = `<ul class="memory-health-list">
        <li>Facing memories: ${h.total_facing ?? "—"}</li>
        <li>Candidates pending: ${h.candidates_pending ?? 0}</li>
        <li>Conflicts: ${h.conflicts ?? 0}</li>
        <li class="muted">${window.escapeHtml(h.duplicates_hint || "")}</li>
      </ul>`;
    }
    const sleep = document.getElementById("memorySleepBody");
    if (sleep) {
      const sl = home.sleep || {};
      const outs = (sl.outcomes || []).map((o) => `<li>${window.escapeHtml(o.plain || "")}</li>`).join("");
      sleep.innerHTML = `<p>${window.escapeHtml(sl.message || "")}</p><ul>${outs || "<li class='muted'>No recent sleep outcomes surfaced.</li>"}</ul>`;
    }
    const candList = document.getElementById("memoryCandidateList");
    if (candList) {
      const cands = (home.recent_learning || {}).candidates || [];
      candList.innerHTML = cands.length
        ? cands.map((c) => `<li class="memory-candidate-item" data-id="${window.escapeHtml(c.id)}">
            <div><strong>${window.escapeHtml(c.source || "")}</strong> — ${window.escapeHtml(c.content || "")}</div>
            <div class="memory-item-actions">
              <button type="button" class="apply-btn tiny mem-adopt" data-id="${window.escapeHtml(c.id)}">Adopt</button>
              <button type="button" class="ghost-btn tiny mem-dismiss" data-id="${window.escapeHtml(c.id)}">Dismiss</button>
            </div>
          </li>`).join("")
        : `<li class="muted">No candidates. Journal ★ remember, Smart auto-memory, and imports stage here first.</li>`;
      candList.querySelectorAll(".mem-adopt").forEach((btn) => {
        btn.onclick = async () => {
          const ok = await memoryConfirm("Adopt this into autobiographical memory (ACM)?", "Adopt");
          if (!ok) return;
          const r = await fetch(`/api/memory/candidates/${btn.dataset.id}/adopt`, { method: "POST" });
          const d = await r.json().catch(() => ({}));
          window.showAriaToast?.(d.ok ? "Adopted into ACM" : (d.error || "Failed"), d.ok ? "ok" : "err", 3500);
          loadMemoryBrowser();
        };
      });
      candList.querySelectorAll(".mem-dismiss").forEach((btn) => {
        btn.onclick = async () => {
          await fetch(`/api/memory/candidates/${btn.dataset.id}/dismiss`, { method: "POST" });
          loadMemoryBrowser();
        };
      });
    }
    const changed = document.getElementById("memoryChangedBody");
    if (changed) {
      const recent = (home.what_changed || {}).recent || [];
      changed.innerHTML = recent.map(renderMemoryCard).join("") || `<p class="muted">Nothing recent yet.</p>`;
      bindMemoryCardActions(changed);
    }
    const beliefs = document.getElementById("memoryBeliefsBody");
    if (beliefs) {
      beliefs.innerHTML = (home.beliefs || []).map(renderMemoryCard).join("") || `<p class="muted">No beliefs projected yet.</p>`;
      bindMemoryCardActions(beliefs);
    }
  } catch (err) {
    window.showAriaToast?.(err?.message || "Memory Home unavailable", "err", 4000);
  }
}

function bindMemoryCardActions(root) {
  root.querySelectorAll(".memory-forget-btn").forEach((btn) => {
    btn.onclick = () => openForgetFlow(btn.dataset.id);
  });
  root.querySelectorAll(".memory-correct-btn").forEach((btn) => {
    btn.onclick = () => openCorrectFlowFixed(btn.dataset.id);
  });
  root.querySelectorAll(".memory-edit-btn").forEach((btn) => {
    btn.onclick = () => openEditMemoryDialog(btn.dataset.id, btn.closest(".memory-cog-card, .memory-item"));
  });
}

async function openForgetFlow(id) {
  if (!id) return;
  const prev = await fetch(`/api/memory/${id}/forget-preview`).then((r) => r.json()).catch(() => ({}));
  if (!prev.ok) {
    window.showAriaToast?.(prev.error || "Preview failed", "err", 4000);
    return;
  }
  const entry = prev.entry || {};
  const actionsHtml = (prev.actions || []).map((a) =>
    `<button type="button" class="ghost-btn small forget-act" data-act="${window.escapeHtml(a.id)}"><strong>${window.escapeHtml(a.label)}</strong><br/><span class="muted">${window.escapeHtml(a.explanation)}</span></button>`
  ).join("");
  const related = (prev.related || []).map((r) => `<li>${window.escapeHtml(r.content || "")}</li>`).join("");
  await openMemoryDialog(
    "Safe forget",
    `<p><strong>${window.escapeHtml(entry.content || "")}</strong></p>
     <p class="muted">${window.escapeHtml(prev.message || "")}</p>
     <div class="forget-actions">${actionsHtml}</div>
     ${related ? `<h4>Related</h4><ul>${related}</ul>` : ""}
     <label class="hidden" id="forgetCorrectWrap">Correction text<textarea id="forgetCorrectText" rows="3"></textarea></label>`,
    [{ label: "Cancel", value: null }],
  );
  document.querySelectorAll(".forget-act").forEach((btn) => {
    btn.onclick = async () => {
      const act = btn.dataset.act;
      let correction = "";
      if (act === "correct") {
        const wrap = document.getElementById("forgetCorrectWrap");
        wrap?.classList.remove("hidden");
        correction = document.getElementById("forgetCorrectText")?.value?.trim() || "";
        if (!correction) {
          window.showAriaToast?.("Enter correction text", "warn", 3000);
          return;
        }
      }
      const sure = await memoryConfirm(`Confirm ${act}? This changes what Aria believes.`, "Confirm forget");
      if (!sure) return;
      const res = await fetch(`/api/memory/${id}/forget`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: act, confirm: true, correction_text: correction }),
      });
      const data = await res.json().catch(() => ({}));
      closeMemoryDialog();
      window.showAriaToast?.(data.ok ? (data.message || "Done") : (data.error || "Failed"), data.ok ? "ok" : "err", 4000);
      if (data.ok) loadMemoryBrowser();
    };
  });
}

async function openEditMemoryDialog(id, itemEl) {
  const content = itemEl?.querySelector(".memory-cog-title, .memory-content")?.textContent || "";
  const dlg = document.getElementById("memoryDialog");
  const titleEl = document.getElementById("memoryDialogTitle");
  const body = document.getElementById("memoryDialogBody");
  const acts = document.getElementById("memoryDialogActions");
  if (!dlg || !body) return;
  titleEl.textContent = id ? "Edit memory" : "New memory";
  body.innerHTML = `
    <label>Content<textarea id="memEditContent" rows="5" class="memory-dialog-input">${window.escapeHtml(content)}</textarea></label>
    <label>Type
      <select id="memEditType">
        <option value="fact">fact</option>
        <option value="preference">preference</option>
        <option value="project">project</option>
        <option value="note">note</option>
      </select>
    </label>
    <label>Namespace <input id="memEditNs" type="text" value="default" /></label>
    <label>Tags <input id="memEditTags" type="text" placeholder="comma,separated" /></label>`;
  acts.innerHTML = "";
  dlg.classList.remove("hidden");
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "ghost-btn small";
  cancel.textContent = "Cancel";
  cancel.onclick = closeMemoryDialog;
  const save = document.createElement("button");
  save.type = "button";
  save.className = "apply-btn small";
  save.textContent = id ? "Save" : "Encode";
  save.onclick = async () => {
    const payload = {
      content: document.getElementById("memEditContent")?.value?.trim(),
      type: document.getElementById("memEditType")?.value || "fact",
      namespace: document.getElementById("memEditNs")?.value?.trim() || "default",
      tags: (document.getElementById("memEditTags")?.value || "").split(",").map((t) => t.trim()).filter(Boolean),
    };
    if (!payload.content) return;
    try {
      const res = await fetch(id ? `/api/memory/${id}` : "/api/memory", {
        method: id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || data.message || "Save failed");
      closeMemoryDialog();
      window.showAriaToast?.(id ? "Updated" : "Encoded into ACM", "ok", 2500);
      loadMemoryBrowser();
    } catch (err) {
      window.showAriaToast?.(err.message || "Save failed", "err", 5000);
    }
  };
  acts.append(cancel, save);
}

async function openCorrectFlowFixed(id) {
  const dlg = document.getElementById("memoryDialog");
  const body = document.getElementById("memoryDialogBody");
  const acts = document.getElementById("memoryDialogActions");
  const titleEl = document.getElementById("memoryDialogTitle");
  if (!dlg || !body) return;
  titleEl.textContent = "Correct belief";
  body.innerHTML = `<p class="muted">Revise with lineage — old belief remains in history.</p>
    <textarea id="memCorrectBody" rows="4" class="memory-dialog-input"></textarea>`;
  acts.innerHTML = "";
  dlg.classList.remove("hidden");
  const cancel = document.createElement("button");
  cancel.className = "ghost-btn small";
  cancel.textContent = "Cancel";
  cancel.onclick = closeMemoryDialog;
  const go = document.createElement("button");
  go.className = "apply-btn small";
  go.textContent = "Correct";
  go.onclick = async () => {
    const text = document.getElementById("memCorrectBody")?.value?.trim();
    if (!text) return;
    const sure = await memoryConfirm("Apply correction?", "Confirm");
    if (!sure) return;
    const res = await fetch(`/api/memory/${id}/forget`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "correct", confirm: true, correction_text: text }),
    });
    const data = await res.json().catch(() => ({}));
    closeMemoryDialog();
    window.showAriaToast?.(data.ok ? "Corrected" : (data.error || "Failed"), data.ok ? "ok" : "err", 3500);
    if (data.ok) loadMemoryBrowser();
  };
  acts.append(cancel, go);
}

async function loadMemoryListOnly() {
  const el = document.getElementById("memoryList");
  const statsEl = document.getElementById("memoryStats");
  const nsFilter = document.getElementById("memoryNsFilter");
  if (!el) return;
  el.setAttribute("aria-busy", "true");
  el.innerHTML = `<div class="memory-skeleton" aria-hidden="true"><div></div><div></div><div></div></div>`;
  const q = document.getElementById("memorySearch")?.value || "";
  const type = document.getElementById("memoryTypeFilter")?.value || "";
  const namespace = document.getElementById("memoryNsFilter")?.value || "";
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (type) params.set("type", type);
  if (namespace) params.set("namespace", namespace);
  try {
    const res = await fetch(`/api/memory/all?${params}`);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || `Load failed (${res.status})`);
    const stats = data.stats || {};
    if (statsEl) {
      const byType = Object.entries(stats.by_type || {})
        .filter(([k]) => !["strategy", "failure", "success"].includes(k))
        .map(([k, v]) => `${k}: ${v}`)
        .join(" · ");
      statsEl.textContent = `${stats.total || 0} · ${byType} · ACM PRIMARY`;
    }
    if (nsFilter && stats.namespaces) {
      const cur = nsFilter.value;
      nsFilter.innerHTML = `<option value="">All namespaces</option>${stats.namespaces
        .filter((n) => n !== "cheatsheet")
        .map((n) => `<option value="${window.escapeHtml(n)}">${window.escapeHtml(n)}</option>`)
        .join("")}`;
      nsFilter.value = cur;
    }
    const entries = (data.entries || []).filter((e) => !["strategy", "failure"].includes(e.type));
    el.innerHTML = entries.map((e) => `
      <div class="memory-item" data-id="${window.escapeHtml(e.id)}">
        <div class="memory-item-head">
          <span class="memory-badge type-${window.escapeHtml(e.type)}">${window.escapeHtml(e.type)}</span>
          <span class="memory-badge ns">${window.escapeHtml(e.namespace || "default")}</span>
        </div>
        <p class="memory-content">${window.escapeHtml(e.content)}</p>
        <div class="memory-item-actions">
          <button type="button" class="memory-edit-btn ghost-btn tiny" data-id="${window.escapeHtml(e.id)}">Edit</button>
          <button type="button" class="memory-forget-btn ghost-btn tiny" data-id="${window.escapeHtml(e.id)}">Forget</button>
        </div>
      </div>`).join("") || `<p class="memory-empty">No memories match. <button type="button" class="ghost-btn tiny" id="memoryEmptyChatBtn">Ask Chat</button></p>`;
    el.querySelector("#memoryEmptyChatBtn")?.addEventListener("click", () => {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.("Remember that ");
    });
    bindMemoryCardActions(el);
  } catch (err) {
    el.innerHTML = `<p class="memory-empty">${window.escapeHtml(err.message || "Failed")}</p>`;
  } finally {
    el.setAttribute("aria-busy", "false");
  }
}

async function loadMemoryBrowser() {
  await loadMemorySettings();
  await loadEnvironmentPreferences();
  await loadCognitiveHome();
  await loadMemoryConflicts();
  await loadMemoryTrustStatus();
  await loadProfileInlinePanel();
  await loadCheatsheets(document.getElementById("cheatsheetSelect")?.value || "");
  await loadMemoryListOnly();
}


function initMemoryBrowser() {
  document.getElementById("knowledgeResearchRunBtn")?.addEventListener("click", () => {
    runKnowledgeResearchNow();
  });
  let searchTimer = null;
  document.getElementById("memorySearch")?.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadMemoryListOnly(), 180);
  });
  document.getElementById("memoryTypeFilter")?.addEventListener("change", () => loadMemoryListOnly());
  document.getElementById("memoryNsFilter")?.addEventListener("change", () => loadMemoryListOnly());
  document.getElementById("memorySearchFocusBtn")?.addEventListener("click", () => {
    document.getElementById("memoryBrowseSection")?.setAttribute("open", "");
    document.getElementById("memorySearch")?.focus();
  });
  document.getElementById("memoryAddBtn")?.addEventListener("click", () => openEditMemoryDialog(null, null));
  document.getElementById("memoryBriefingBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/memory/briefing", { method: "POST" });
    const data = await res.json().catch(() => ({}));
    openMemoryDialog("Memory briefing", `<pre class="memory-briefing">${window.escapeHtml(data.briefing || "")}</pre>`, [
      { label: "Close", value: true, primary: true },
    ]);
  });
  document.getElementById("memoryAssistBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/memory/assist");
    const data = await res.json().catch(() => ({}));
    const sug = (data.suggestions || []).map((s) => `<li>${window.escapeHtml(s.title || "")}</li>`).join("");
    openMemoryDialog("Memory assistant", `<p class="muted">${window.escapeHtml(data.message || "")}</p><ul>${sug || "<li class='muted'>No suggestions</li>"}</ul>`, [
      { label: "Close", value: true, primary: true },
    ]);
  });
  document.getElementById("memoryShortcutsBtn")?.addEventListener("click", () => {
    const o = document.getElementById("memoryShortcutOverlay");
    if (!o) return;
    o.innerHTML = `<div class="bujo-shortcut-card"><h3>Memory shortcuts</h3>
      <ul><li><kbd>/</kbd> Search</li><li><kbd>N</kbd> New</li><li><kbd>?</kbd> Shortcuts</li><li><kbd>Esc</kbd> Close</li></ul>
      <button type="button" class="ghost-btn small" id="memCloseShortcuts">Close</button></div>`;
    o.classList.remove("hidden");
    document.getElementById("memCloseShortcuts")?.addEventListener("click", () => o.classList.add("hidden"));
  });
  document.getElementById("memoryOpenKnowledgeBtn")?.addEventListener("click", () => {
    window.switchToView?.("documents");
    window.showAriaToast?.("Knowledge Briefs live with Documents / research — not Memory, not Connections.", "info", 4000);
  });
  document.getElementById("memoryOpenKnowledgeBtn2")?.addEventListener("click", () => {
    document.getElementById("memoryOpenKnowledgeBtn")?.click();
  });
  document.getElementById("memoryOpenConnectionsBtn")?.addEventListener("click", () => {
    window.switchToView?.("connections");
    window.showAriaToast?.("Connections = relationship graph. ACM remains cognitive SoT.", "info", 3500);
  });
  document.addEventListener("keydown", (e) => {
    const view = document.getElementById("memoryView");
    if (!view || view.classList.contains("hidden")) return;
    const tag = (e.target?.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || e.target?.isContentEditable;
    if (e.key === "Escape") {
      closeMemoryDialog();
      document.getElementById("memoryShortcutOverlay")?.classList.add("hidden");
      return;
    }
    if (typing) return;
    if (e.key === "/") {
      e.preventDefault();
      document.getElementById("memoryBrowseSection")?.setAttribute("open", "");
      document.getElementById("memorySearch")?.focus();
    } else if (e.key === "n" || e.key === "N") {
      e.preventDefault();
      openEditMemoryDialog(null, null);
    } else if (e.key === "?" || (e.shiftKey && e.key === "/")) {
      e.preventDefault();
      document.getElementById("memoryShortcutsBtn")?.click();
    }
  });
  document.getElementById("memoryOpenJournalBtn")?.addEventListener("click", () => {
    window.switchToView?.("journal");
  });
  document.getElementById("memoryOpenProjectsBtn")?.addEventListener("click", () => {
    window.switchToView?.("projects");
  });
  document.getElementById("memoryOpenBrowserBtn")?.addEventListener("click", () => {
    window.switchToView?.("browser");
  });
  document.getElementById("memoryOpenDocumentsBtn")?.addEventListener("click", () => {
    window.switchToView?.("documents");
  });
  document.getElementById("memoryExportBtn")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/memory/export");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Export failed (${res.status})`);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `jarvis-memory-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
      window.showAriaToast?.("Memory exported (snapshot — ACM remains authority)", "ok", 2500);
    } catch (err) {
      window.showAriaToast?.(err.message || "Export failed", "err", 5000);
    }
  });
  const importFile = document.getElementById("memoryImportFile");
  document.getElementById("memoryImportBtn")?.addEventListener("click", () => importFile?.click());
  importFile?.addEventListener("change", async () => {
    const file = importFile.files?.[0];
    if (!file) return;
    let payload;
    try {
      payload = JSON.parse(await file.text());
    } catch {
      window.showAriaToast?.("Import failed: invalid JSON", "err", 5000);
      importFile.value = "";
      return;
    }
    const dlg = document.getElementById("memoryDialog");
    const body = document.getElementById("memoryDialogBody");
    const acts = document.getElementById("memoryDialogActions");
    const titleEl = document.getElementById("memoryDialogTitle");
    titleEl.textContent = "Import memory snapshot";
    body.innerHTML = `<p>Choose carefully. <strong>Cancel aborts</strong> — it does not replace.</p>
      <ul>
        <li><strong>Merge</strong> — add entries alongside existing beliefs</li>
        <li><strong>Replace</strong> — wipe projected store contents then import (dangerous)</li>
        <li><strong>Cancel</strong> — do nothing</li>
      </ul>`;
    acts.innerHTML = "";
    dlg.classList.remove("hidden");
    const run = async (mode) => {
      if (!mode) {
        closeMemoryDialog();
        importFile.value = "";
        return;
      }
      const sure = mode === "replace"
        ? await memoryConfirm("REPLACE all imported projection data? This is destructive.", "Confirm replace")
        : true;
      if (!sure) {
        importFile.value = "";
        return;
      }
      try {
        const res = await fetch("/api/memory/import", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...payload, mode }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) throw new Error(data.error || data.message || "Import failed");
        closeMemoryDialog();
        window.showAriaToast?.(data.message || `Imported ${data.added ?? 0}`, "ok", 3500);
        loadMemoryBrowser();
      } catch (e) {
        window.showAriaToast?.(e.message || "Import failed", "err", 5000);
      }
      importFile.value = "";
    };
    [["Cancel", null], ["Merge", "merge"], ["Replace", "replace"]].forEach(([label, mode], i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = mode === "merge" ? "apply-btn small" : "ghost-btn small";
      b.textContent = label;
      b.onclick = () => run(mode);
      acts.appendChild(b);
    });
  });
  document.getElementById("memoryPruneBtn")?.addEventListener("click", async () => {
    if (!(await memoryConfirm("Remove stale auto-extracted memories?", "Prune"))) return;
    try {
      const res = await fetch("/api/memory/prune", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        throw new Error(data.message || data.detail || `Prune failed (${res.status})`);
      }
      window.showAriaToast?.(`Pruned ${data.removed || 0} entries`, "ok", 3500);
      loadMemoryBrowser();
    } catch (err) {
      window.showAriaToast?.(err.message || "Prune failed", "err", 5000);
    }
  });
  document.getElementById("memoryScrubBtn")?.addEventListener("click", async () => {
    if (!(await memoryConfirm("Remove test artifacts from memory?", "Scrub"))) return;
    try {
      const res = await fetch("/api/memory/trust/scrub", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        throw new Error(data.message || data.detail || `Scrub failed (${res.status})`);
      }
      window.showAriaToast?.(`Scrubbed ${data.removed || 0} entries`, "ok", 3500);
      loadMemoryBrowser();
    } catch (err) {
      window.showAriaToast?.(err.message || "Scrub failed", "err", 5000);
    }
  });
  document.getElementById("memoryAutoMode")?.addEventListener("change", (e) => {
    void saveMemorySettings({ auto_memory_mode: e.target.value }).catch((err) => {
      window.showAriaToast?.(err.message || "Could not save setting", "warn", 6000);
      if (err.locked) window.jarvisShowLock?.();
    });
  });
  bindMemorySettingCheckbox("memoryBrainMode", "brain_mode");
  bindMemorySettingCheckbox("memoryAutoJournalLearn", "auto_journal_learn");
  bindMemorySettingCheckbox("memoryAutoDocumentLearn", "auto_document_learn");
  bindMemorySettingCheckbox("memoryAutoCheckpoint", "auto_checkpoint");
  bindMemorySettingCheckbox("memoryAutoNamespace", "auto_namespace");
  bindMemorySettingCheckbox("memoryInPrompt", "memory_in_system_prompt");
  document.getElementById("envPrefsSaveBtn")?.addEventListener("click", () => saveEnvironmentPreferences());
  document.getElementById("envMachineSyncBtn")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/memory/environment/sync?machine_only=true", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        throw new Error(data.message || data.detail || `Sync failed (${res.status})`);
      }
      window.showAriaToast?.(
        `Machine facts refreshed (${data.added || 0} added, ${data.updated || 0} updated)`,
        "ok",
        4000,
      );
      loadMemoryBrowser();
    } catch (err) {
      window.showAriaToast?.(err.message || "Machine sync failed", "err", 5000);
    }
  });
  document.getElementById("profileRetakeBtn")?.addEventListener("click", async () => {
    if (!(await memoryConfirm("Replace your saved profile with new answers?", "Update profile"))) return;
    try {
      const res = await fetch("/api/profile/questionnaire/reset", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        window.showAriaToast?.(data.message || "Could not reset profile", "err", 5000);
        return;
      }
      renderProfileForm(data.questions || []);
      const modal = document.getElementById("profileModal");
      if (modal) modal.dataset.retake = "1";
      modal?.classList.remove("hidden");
    } catch (err) {
      window.showAriaToast?.(err?.message || "Could not reset profile", "err", 5000);
    }
  });
  document.getElementById("profileInlineEditBtn")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/profile/questionnaire?edit=1");
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false || !(data.questions || []).length) {
        window.showAriaToast?.(data.message || "Could not load profile questions", "err", 5000);
        return;
      }
      renderProfileForm(data.questions);
      const modal = document.getElementById("profileModal");
      if (modal) modal.dataset.retake = data.completed ? "1" : "";
      modal?.classList.remove("hidden");
    } catch (err) {
      window.showAriaToast?.(err?.message || "Could not load profile questions", "err", 5000);
    }
  });
  document.getElementById("cheatsheetViewBtn")?.addEventListener("click", () => {
    const key = document.getElementById("cheatsheetSelect")?.value;
    if (!key) {
      window.showAriaToast?.("Choose a cheatsheet first", "warn", 3000);
      return;
    }
    showCheatsheet(key);
  });
  document.getElementById("cheatsheetSelect")?.addEventListener("change", (e) => {
    if (e.target.value) showCheatsheet(e.target.value);
    else document.getElementById("cheatsheetContent")?.classList.add("hidden");
  });
  document.getElementById("cheatsheetEditBtn")?.addEventListener("click", async () => {
    const key = document.getElementById("cheatsheetSelect")?.value;
    if (!key) {
      window.showAriaToast?.("Choose a cheatsheet first", "warn", 3000);
      return;
    }
    try {
      const res = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) throw new Error(data.message || data.detail || "Could not load cheatsheet");
      const dlg = document.getElementById("memoryDialog");
      const bodyEl = document.getElementById("memoryDialogBody");
      const acts = document.getElementById("memoryDialogActions");
      document.getElementById("memoryDialogTitle").textContent = `Edit ${key}`;
      bodyEl.innerHTML = `<textarea id="cheatEditArea" rows="16" class="memory-dialog-input"></textarea>`;
      document.getElementById("cheatEditArea").value = data.cheatsheet?.content || "";
      acts.innerHTML = "";
      dlg.classList.remove("hidden");
      const cancel = document.createElement("button");
      cancel.className = "ghost-btn small";
      cancel.textContent = "Cancel";
      cancel.onclick = closeMemoryDialog;
      const save = document.createElement("button");
      save.className = "apply-btn small";
      save.textContent = "Save";
      save.onclick = async () => {
        const next = document.getElementById("cheatEditArea")?.value || "";
        const put = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: next.trim() }),
        });
        const putData = await put.json().catch(() => ({}));
        if (!put.ok || putData.ok === false) {
          window.showAriaToast?.(putData.message || "Save failed", "err", 5000);
          return;
        }
        closeMemoryDialog();
        window.showAriaToast?.("Cheatsheet saved", "ok", 2500);
        showCheatsheet(key);
      };
      acts.append(cancel, save);
    } catch (err) {
      window.showAriaToast?.(err.message || "Cheatsheet save failed", "err", 5000);
    }
  });
  document.getElementById("cheatsheetResetBtn")?.addEventListener("click", async () => {
    const key = document.getElementById("cheatsheetSelect")?.value;
    if (!key) {
      window.showAriaToast?.("Choose a cheatsheet first", "warn", 3000);
      return;
    }
    if (!(await memoryConfirm(`Restore the default ${key} cheatsheet? Your edits will be lost.`, "Reset cheatsheet"))) return;
    try {
      const res = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}/reset`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        throw new Error(data.message || data.detail || `Reset failed (${res.status})`);
      }
      window.showAriaToast?.("Cheatsheet reset to default", "ok", 2500);
      loadMemoryBrowser();
      showCheatsheet(key);
    } catch (err) {
      window.showAriaToast?.(err.message || "Cheatsheet reset failed", "err", 5000);
    }
  });
}

function renderProfileForm(questions) {
  const form = document.getElementById("profileForm");
  if (!form) return;
  form.innerHTML = (questions || []).map((q) => {
    const req = q.required ? " required" : "";
    const hint = q.hint ? `<p class="hint">${window.escapeHtml(q.hint)}</p>` : "";
    if (q.type === "select") {
      const opts = (q.options || []).map((o) =>
        `<option value="${window.escapeHtml(o.value)}">${window.escapeHtml(o.label)}</option>`
      ).join("");
      return `<div class="profile-field"><label for="pf_${q.id}">${window.escapeHtml(q.label)}</label>${hint}<select id="pf_${q.id}" name="${window.escapeHtml(q.id)}"${req}>${opts}</select></div>`;
    }
    if (q.type === "textarea") {
      return `<div class="profile-field"><label for="pf_${q.id}">${window.escapeHtml(q.label)}</label>${hint}<textarea id="pf_${q.id}" name="${window.escapeHtml(q.id)}"${req}></textarea></div>`;
    }
    return `<div class="profile-field"><label for="pf_${q.id}">${window.escapeHtml(q.label)}</label>${hint}<input type="text" id="pf_${q.id}" name="${window.escapeHtml(q.id)}"${req} /></div>`;
  }).join("");
}

async function maybeShowProfileQuestionnaire() {
  const modal = document.getElementById("profileModal");
  if (!modal) return;
  const retake = modal.dataset.retake === "1";
  try {
    const res = await fetch("/api/profile/questionnaire");
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (retake) {
        window.showAriaToast?.(data.error || data.message || "Could not load profile questionnaire", "err", 4000);
      }
      return;
    }
    if (!data.ok || data.completed || !(data.questions || []).length) {
      if (retake && data.completed) {
        window.showAriaToast?.("Profile questionnaire already completed", "info", 3000);
      }
      return;
    }
    renderProfileForm(data.questions);
    modal.classList.remove("hidden");
  } catch (err) {
    if (retake) {
      window.showAriaToast?.(err?.message || "Could not load profile questionnaire", "err", 4000);
    }
  }
}

document.getElementById("profileForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const answers = {};
  new FormData(form).forEach((v, k) => { answers[k] = String(v); });
  const btn = document.getElementById("profileSaveBtn");
  if (btn) btn.disabled = true;
  try {
    const res = await fetch("/api/profile/questionnaire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers, retake: !!document.getElementById("profileModal")?.dataset.retake }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      window.showAriaToast?.(data.error || data.message || "Could not save profile", "err", 5000);
      return;
    }
    document.getElementById("profileModal")?.classList.add("hidden");
    delete document.getElementById("profileModal")?.dataset.retake;
    loadProfileInlinePanel();
    (window.addMessage || (() => {}))(
      "assistant",
      `Thanks — I saved **${data.stored || 0}** things about you to memory. I'll use this to personalize our chats.`,
      { type: "info", module: "memory" }
    );
  } catch (_) {
    window.showAriaToast?.("Save failed", "err", 5000);
  } finally {
    if (btn) btn.disabled = false;
  }
});

document.getElementById("profileSkipBtn")?.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/profile/questionnaire", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skip: true }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      window.showAriaToast?.(data.message || "Could not skip profile", "err", 5000);
      return;
    }
    document.getElementById("profileModal")?.classList.add("hidden");
    window.showAriaToast?.("Profile questionnaire skipped", "ok", 2500);
  } catch (err) {
    window.showAriaToast?.(err?.message || "Could not skip profile", "err", 5000);
  }
});


  window.loadMemoryBrowser = loadMemoryBrowser;
  window.initMemoryBrowser = initMemoryBrowser;
  window.maybeShowProfileQuestionnaire = maybeShowProfileQuestionnaire;
  window.loadProfileInlinePanel = loadProfileInlinePanel;
  window.renderProfileForm = renderProfileForm;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initMemoryBrowser());
  } else {
    initMemoryBrowser();
  }
})();
