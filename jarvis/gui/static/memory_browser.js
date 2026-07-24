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
  const res = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`);
  const data = await res.json();
  if (!data.ok) {
    window.showAriaToast?.(data.error || "Cheatsheet not found", "err", 5000);
    return;
  }
  box.textContent = data.cheatsheet?.content || "";
  box.classList.remove("hidden");
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
    const data = await res.json();
    const conflicts = data.conflicts || [];
    if (!conflicts.length) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    box.classList.remove("hidden");
    box.innerHTML = `<h3>Possible conflicts (${conflicts.length})</h3>` + conflicts.map((c, i) => `
      <div class="memory-conflict-item" data-keep="${window.escapeHtml(c.a.id)}" data-drop="${window.escapeHtml(c.b.id)}">
        <div class="memory-conflict-pair"><strong>${window.escapeHtml(c.kind)}</strong> · score ${c.score}<br/>
          A: ${window.escapeHtml(c.a.content)}<br/>
          B: ${window.escapeHtml(c.b.content)}
        </div>
        <div class="memory-conflict-actions">
          <button type="button" class="apply-btn small memory-keep-a" data-i="${i}">Keep A</button>
          <button type="button" class="apply-btn small memory-keep-b" data-i="${i}">Keep B</button>
        </div>
      </div>`).join("");
    box.querySelectorAll(".memory-keep-a").forEach((btn) => {
      btn.onclick = async () => {
        const item = btn.closest(".memory-conflict-item");
        try {
          const res = await fetch("/api/memory/conflicts/resolve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keep_id: item.dataset.keep, drop_id: item.dataset.drop }),
          });
          const data = await res.json().catch(() => ({}));
          if (!res.ok || data.ok === false) {
            throw new Error(data.message || data.detail || `Resolve failed (${res.status})`);
          }
          window.showAriaToast?.("Kept memory A", "ok", 2500);
          loadMemoryBrowser();
        } catch (err) {
          window.showAriaToast?.(err.message || "Resolve failed", "err", 5000);
        }
      };
    });
    box.querySelectorAll(".memory-keep-b").forEach((btn) => {
      btn.onclick = async () => {
        const item = btn.closest(".memory-conflict-item");
        try {
          const res = await fetch("/api/memory/conflicts/resolve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keep_id: item.dataset.drop, drop_id: item.dataset.keep }),
          });
          const data = await res.json().catch(() => ({}));
          if (!res.ok || data.ok === false) {
            throw new Error(data.message || data.detail || `Resolve failed (${res.status})`);
          }
          window.showAriaToast?.("Kept memory B", "ok", 2500);
          loadMemoryBrowser();
        } catch (err) {
          window.showAriaToast?.(err.message || "Resolve failed", "err", 5000);
        }
      };
    });
  } catch (_) {
    box.classList.add("hidden");
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
  const res = await fetch("/api/memory/environment/preferences", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferences }),
  });
  const data = await res.json();
  if (!data.ok) {
    window.showAriaToast?.(data.error || "Save failed", "err", 5000);
    return;
  }
  loadMemoryBrowser();
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
        document.getElementById("profileEditBtn")?.click()
          || document.getElementById("profileModal")?.classList.remove("hidden");
      });
    }
  } catch (e) {
    el.textContent = e.message || "Could not load profile";
  }
}

async function loadMemoryBrowser() {
  await loadMemorySettings();
  await loadEnvironmentPreferences();
  await loadMemoryConflicts();
  await loadMemoryTrustStatus();
  await loadProfileInlinePanel();
  try {
    const kRes = await fetch("/api/knowledge");
    const kData = await kRes.json();
    const kEl = document.getElementById("knowledgeTopicList");
    if (kEl) {
      const topics = kData.topics || [];
      kEl.innerHTML = topics.length
        ? topics.map((t) => `<li><strong>${window.escapeHtml(t.title || t.slug)}</strong> <code>${window.escapeHtml(t.slug || "")}</code></li>`).join("")
        : `<li>No knowledge briefs yet. <button type="button" class="ghost-btn tiny" id="knowledgeEmptyChatBtn">Ask Chat</button> — say <em>learn about: …</em></li>`;
      kEl.querySelector("#knowledgeEmptyChatBtn")?.addEventListener("click", () => {
        window.switchToView?.("chat");
        window.jarvisSendToChat?.("learn about: ");
      });
    }
  } catch (err) {
    window.showAriaToast?.(err?.message || "Knowledge topics unavailable", "err", 4000);
  }
  try {
    await loadKnowledgeResearchPanel();
  } catch (err) {
    window.showAriaToast?.(err?.message || "Research panel unavailable", "err", 4000);
  }
  await loadCheatsheets(document.getElementById("cheatsheetSelect")?.value || "");
  const el = document.getElementById("memoryList");
  const statsEl = document.getElementById("memoryStats");
  const nsFilter = document.getElementById("memoryNsFilter");
  if (!el) return;
  const q = document.getElementById("memorySearch")?.value || "";
  const type = document.getElementById("memoryTypeFilter")?.value || "";
  const namespace = document.getElementById("memoryNsFilter")?.value || "";
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (type) params.set("type", type);
  if (namespace) params.set("namespace", namespace);
  let data = {};
  try {
    const res = await fetch(`/api/memory/all?${params}`);
    data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || data.detail || `Memory load failed (${res.status})`);
  } catch (err) {
    el.innerHTML = `<p class="memory-empty">${window.escapeHtml(err.message || "Memory load failed")}</p>`;
    window.showAriaToast?.(err.message || "Memory load failed", "err", 5000);
    return;
  }
  const stats = data.stats || {};
  if (statsEl) {
    const byType = stats.by_type
      ? Object.entries(stats.by_type).map(([k, v]) => `${k}: ${v}`).join(" · ")
      : "";
    statsEl.textContent = `${stats.total || 0} memories${byType ? ` · ${byType}` : ""} · namespace: ${data.namespace || "default"}`;
  }
  if (nsFilter && stats.namespaces) {
    const cur = nsFilter.value;
    nsFilter.innerHTML = `<option value="">All namespaces</option>${stats.namespaces.map((n) =>
      `<option value="${window.escapeHtml(n)}">${window.escapeHtml(n)}</option>`
    ).join("")}`;
    nsFilter.value = cur;
  }
  el.innerHTML = (data.entries || []).map((e) => `
    <div class="memory-item" data-id="${window.escapeHtml(e.id)}">
      <div class="memory-item-head">
        <span class="memory-badge type-${window.escapeHtml(e.type)}">${window.escapeHtml(e.type)}</span>
        <span class="memory-badge ns">${window.escapeHtml(e.namespace || "default")}</span>
        ${(e.tags || []).map((t) => `<span class="memory-tag">${window.escapeHtml(t)}</span>`).join("")}
      </div>
      <p class="memory-content">${window.escapeHtml(e.content)}</p>
      <div class="memory-item-actions">
        <button type="button" class="memory-edit-btn" data-id="${window.escapeHtml(e.id)}">Edit</button>
        <button type="button" class="memory-del-btn" data-id="${window.escapeHtml(e.id)}">Delete</button>
      </div>
    </div>`).join("") || `<p class="memory-empty">No memories stored. <button type="button" class="ghost-btn tiny" id="memoryEmptyChatBtn">Ask Chat</button> or import from the toolbar.</p>`;
    el.querySelector("#memoryEmptyChatBtn")?.addEventListener("click", () => {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.("Remember that ");
    });
  el.querySelectorAll(".memory-del-btn").forEach((btn) => {
    btn.onclick = async () => {
      const item = btn.closest(".memory-item");
      const isCheatsheet = item?.querySelector(".memory-badge.ns")?.textContent === "cheatsheet";
      const msg = isCheatsheet
        ? "Delete this cheatsheet? Use Reset default to restore bundled text instead."
        : "Delete this memory?";
      if (!confirm(msg)) return;
      try {
        const res = await fetch(`/api/memory/${btn.dataset.id}`, { method: "DELETE" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.message || data.detail || `Delete failed (${res.status})`);
        window.showAriaToast?.("Memory deleted", "ok", 2500);
        loadMemoryBrowser();
      } catch (err) {
        window.showAriaToast?.(err.message || "Delete failed", "err", 5000);
      }
    };
  });
  el.querySelectorAll(".memory-edit-btn").forEach((btn) => {
    btn.onclick = async () => {
      const item = btn.closest(".memory-item");
      const content = item?.querySelector(".memory-content")?.textContent || "";
      const next = prompt("Edit memory:", content);
      if (next == null || next.trim() === content) return;
      try {
        const res = await fetch(`/api/memory/${btn.dataset.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: next.trim() }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.message || data.detail || `Update failed (${res.status})`);
        window.showAriaToast?.("Memory updated", "ok", 2500);
        loadMemoryBrowser();
      } catch (err) {
        window.showAriaToast?.(err.message || "Update failed", "err", 5000);
      }
    };
  });
}


function initMemoryBrowser() {
  document.getElementById("knowledgeResearchRunBtn")?.addEventListener("click", () => {
    runKnowledgeResearchNow();
  });
  document.getElementById("memorySearch")?.addEventListener("input", () => loadMemoryBrowser());
  document.getElementById("memoryTypeFilter")?.addEventListener("change", () => loadMemoryBrowser());
  document.getElementById("memoryNsFilter")?.addEventListener("change", () => loadMemoryBrowser());
  document.getElementById("memoryAddBtn")?.addEventListener("click", async () => {
    const content = prompt("Memory to store:");
    if (!content?.trim()) return;
    try {
      const res = await fetch("/api/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: content.trim(), type: "fact" }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Save failed (${res.status})`);
      window.showAriaToast?.("Memory saved", "ok", 2500);
      loadMemoryBrowser();
    } catch (err) {
      window.showAriaToast?.(err.message || "Save failed", "err", 5000);
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
      window.showAriaToast?.("Memory exported", "ok", 2500);
    } catch (err) {
      window.showAriaToast?.(err.message || "Export failed", "err", 5000);
    }
  });
  const importFile = document.getElementById("memoryImportFile");
  document.getElementById("memoryImportBtn")?.addEventListener("click", () => importFile?.click());
  importFile?.addEventListener("change", async () => {
    const file = importFile.files?.[0];
    if (!file) return;
    try {
      const payload = JSON.parse(await file.text());
      const merge = confirm("Merge with existing memories? (Cancel = replace all)");
      const res = await fetch("/api/memory/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, merge }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        throw new Error(data.error || data.message || data.detail || `Import failed (${res.status})`);
      }
      window.showAriaToast?.(`Imported ${data.added ?? 0} memories`, "ok", 3500);
      loadMemoryBrowser();
    } catch (e) {
      window.showAriaToast?.(
        e instanceof SyntaxError ? "Import failed: invalid JSON" : (e.message || "Import failed"),
        "err",
        5000,
      );
    }
    importFile.value = "";
  });
  document.getElementById("memoryPruneBtn")?.addEventListener("click", async () => {
    if (!confirm("Remove stale auto-extracted memories?")) return;
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
    if (!confirm("Remove test artifacts from memory (broken_calc, buy milk, stale checkpoints)?")) return;
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
    if (!confirm("Replace your saved profile with new answers?")) return;
    const res = await fetch("/api/profile/questionnaire/reset", { method: "POST" });
    const data = await res.json();
    if (!data.ok) {
      window.showAriaToast?.("Could not reset profile", "err", 5000);
      return;
    }
    renderProfileForm(data.questions || []);
    const modal = document.getElementById("profileModal");
    if (modal) modal.dataset.retake = "1";
    modal?.classList.remove("hidden");
  });
  document.getElementById("profileInlineEditBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/profile/questionnaire?edit=1");
    const data = await res.json();
    if (!data.ok || !(data.questions || []).length) {
      window.showAriaToast?.("Could not load profile questions", "err", 5000);
      return;
    }
    renderProfileForm(data.questions);
    const modal = document.getElementById("profileModal");
    if (modal) modal.dataset.retake = data.completed ? "1" : "";
    modal?.classList.remove("hidden");
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
      const next = prompt("Edit cheatsheet (markdown):", data.cheatsheet?.content || "");
      if (next == null || next.trim() === data.cheatsheet?.content) return;
      const put = await fetch(`/api/cheatsheets/${encodeURIComponent(key)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: next.trim() }),
      });
      const putData = await put.json().catch(() => ({}));
      if (!put.ok || putData.ok === false) {
        throw new Error(putData.message || putData.detail || `Save failed (${put.status})`);
      }
      window.showAriaToast?.("Cheatsheet saved", "ok", 2500);
      loadMemoryBrowser();
      showCheatsheet(key);
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
    if (!confirm(`Restore the default ${key} cheatsheet? Your edits will be lost.`)) return;
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
