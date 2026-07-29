/** Automation Home — Aria OS orchestration layer (not Job Center / Activity / HA / View Paths). */
(function () {
  "use strict";

  let home = null;
  let editingRuleId = "";
  let editingRuleParams = {};
  let lastPipeRun = null;
  let editingPipeline = null;
  let nlDraft = null;
  let pipeFilter = { q: "", sort: "name", fav: false };

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function announce(msg) {
    const live = $("autoLive");
    if (live) live.textContent = msg || "";
  }

  function ingestActivity(activity) {
    if (!activity) return;
    window.AriaActivity?.publish?.(activity);
    window.AriaActivityProducers?.automation?.[
      activity.severity === "error" ? "failed" : activity.severity === "success" ? "complete" : "complete"
    ]?.(activity.title || activity.summary);
  }

  async function api(path, opts) {
    const res = await fetch(path, {
      cache: "no-store",
      headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
      ...opts,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok && data.ok === false) throw new Error(data.error || data.message || res.statusText);
    return data;
  }

  function renderSummary(s) {
    const el = $("autoSummary");
    if (!el || !s) return;
    const sum = s.summary || {};
    const health = s.health || {};
    el.innerHTML = [
      `<div class="auto-stat"><strong>${sum.rules_enabled || 0}</strong><span>enabled</span></div>`,
      `<div class="auto-stat"><strong>${sum.rules_disabled || 0}</strong><span>disabled</span></div>`,
      `<div class="auto-stat"><strong>${sum.runs_recent || 0}</strong><span>recent runs</span></div>`,
      `<div class="auto-stat"><strong>${sum.failures_recent || 0}</strong><span>failures</span></div>`,
      `<div class="auto-stat"><strong>${health.engine || "—"}</strong><span>engine</span></div>`,
      `<div class="auto-stat"><strong>${(health.webhook || {}).configured ? "ready" : "setup"}</strong><span>webhook</span></div>`,
    ].join("");
  }

  function ruleRow(r) {
    const id = esc(r.id);
    return `<div class="auto-row" data-rule="${id}">
      <div><strong>${esc(r.name)}</strong>
        <span class="muted tiny"> · ${esc(r.kind)} · ${esc(r.expression)} · ${esc(r.action)}
        · ${r.enabled ? "on" : "off"} · ${esc(r.last_status || "never")}</span></div>
      <div class="auto-row-actions">
        <button type="button" class="ghost-btn tiny" data-act="run" data-id="${id}">Run</button>
        <button type="button" class="ghost-btn tiny" data-act="dry" data-id="${id}">Dry run</button>
        <button type="button" class="ghost-btn tiny" data-act="toggle" data-id="${id}">${r.enabled ? "Disable" : "Enable"}</button>
        <button type="button" class="ghost-btn tiny" data-act="edit" data-id="${id}">Edit</button>
        <button type="button" class="ghost-btn tiny" data-act="mute" data-id="${id}">Mute</button>
        <button type="button" class="ghost-btn tiny" data-act="del" data-id="${id}">Delete</button>
      </div></div>`;
  }

  function runRow(r) {
    return `<div class="auto-row"><div><strong>${esc(r.name)}</strong>
      <span class="muted tiny"> · ${esc(r.status)} · ${esc(r.kind)} · ${esc(r.why || "")}</span></div></div>`;
  }

  function skillRow(s) {
    const slug = esc(s.slug);
    return `<div class="auto-row" data-skill="${slug}">
      <div><strong>${esc(s.name || s.slug)}</strong><span class="muted tiny"> · ${esc(s.description || "")}</span></div>
      <div class="auto-row-actions">
        <button type="button" class="ghost-btn tiny" data-skill-act="dry" data-slug="${slug}">Dry run</button>
        <button type="button" class="apply-btn tiny" data-skill-act="run" data-slug="${slug}">Run</button>
        <button type="button" class="ghost-btn tiny" data-skill-act="schedule" data-slug="${slug}">Schedule</button>
      </div></div>`;
  }

  function learnedRow(w) {
    const slug = esc(w.slug);
    return `<div class="auto-row" data-learned="${slug}">
      <div><strong>${esc(w.name || w.slug)}</strong>
        <span class="muted tiny"> · ${w.count || 1}× · ${w.steps || 0} steps</span></div>
      <div class="auto-row-actions">
        <button type="button" class="ghost-btn tiny" data-wf-act="dry" data-slug="${slug}">Dry run</button>
        <button type="button" class="apply-btn tiny" data-wf-act="run" data-slug="${slug}">Run</button>
        <button type="button" class="ghost-btn tiny" data-wf-act="schedule" data-slug="${slug}">Schedule</button>
        <button type="button" class="ghost-btn tiny" data-wf-act="promote-dag" data-slug="${slug}">→ Pipeline</button>
        <button type="button" class="ghost-btn tiny" data-wf-act="promote" data-slug="${slug}">→ Rule</button>
      </div></div>`;
  }

  function templateRow(t) {
    const id = typeof t === "string" ? t : t.id;
    const name = typeof t === "string" ? t : t.name || t.id;
    const desc = typeof t === "string" ? "" : t.description || "";
    const tags = typeof t === "string" ? "" : (t.tags || []).join(", ");
    return `<div class="auto-row"><div><strong>Template: ${esc(name)}</strong>
      <p class="muted tiny">${esc(desc)}${tags ? " · " + esc(tags) : ""}</p></div>
      <div class="auto-row-actions">
        <button type="button" class="ghost-btn tiny" data-tpl="${esc(id)}">Create</button>
      </div></div>`;
  }

  function dagRow(d) {
    const id = esc(d.id);
    return `<div class="auto-row" data-pipe="${id}">
      <div><strong>${esc(d.name || d.id)}</strong>
        <span class="muted tiny"> · v${esc(d.version || 1)} · ${esc(d.step_count || 0)} steps
        ${d.favorite ? " · ★" : ""} · ${esc((d.tags || []).join(", "))}</span>
        <p class="muted tiny">${esc(d.description || "")}</p></div>
      <div class="auto-row-actions">
        <button type="button" class="ghost-btn tiny" data-dag-act="dry" data-id="${id}">Dry run</button>
        <button type="button" class="apply-btn tiny" data-dag-act="run" data-id="${id}">Run</button>
        <button type="button" class="ghost-btn tiny" data-dag-act="inspect" data-id="${id}">Inspect</button>
        <button type="button" class="ghost-btn tiny" data-dag-act="edit" data-id="${id}">Edit</button>
        <button type="button" class="ghost-btn tiny" data-dag-act="schedule" data-id="${id}">Schedule</button>
        <button type="button" class="ghost-btn tiny" data-dag-act="fav" data-id="${id}">★</button>
        <button type="button" class="ghost-btn tiny" data-dag-act="dup" data-id="${id}">Dup</button>
        <button type="button" class="ghost-btn tiny" data-dag-act="del" data-id="${id}">Delete</button>
      </div></div>`;
  }

  function pipeRunRow(r) {
    return `<div class="auto-row" data-pipe-run="${esc(r.id)}">
      <div><strong>${esc(r.name)}</strong>
        <span class="muted tiny"> · ${esc(r.status)} · ${esc(r.elapsed_ms || 0)}ms · ${esc(r.trigger || "")}</span></div>
      <div class="auto-row-actions">
        <button type="button" class="ghost-btn tiny" data-pipe-run-open="${esc(r.id)}">Details</button>
      </div></div>`;
  }

  function renderPipelines(data) {
    const tpls = data.templates || [];
    let dags = data.workflow_dags || [];
    const q = (pipeFilter.q || "").toLowerCase();
    if (q) {
      dags = dags.filter(
        (d) =>
          (d.name || "").toLowerCase().includes(q) ||
          (d.description || "").toLowerCase().includes(q) ||
          (d.id || "").toLowerCase().includes(q) ||
          (d.tags || []).join(" ").toLowerCase().includes(q),
      );
    }
    if (pipeFilter.fav) dags = dags.filter((d) => d.favorite);
    const sort = pipeFilter.sort || "name";
    dags = [...dags].sort((a, b) => {
      if (sort === "usage") return (b.usage_count || 0) - (a.usage_count || 0);
      if (sort === "recent") return (b.last_run_at || b.updated_at || 0) - (a.last_run_at || a.updated_at || 0);
      if (sort === "updated") return (b.updated_at || 0) - (a.updated_at || 0);
      return String(a.name || "").localeCompare(String(b.name || ""));
    });
    $("autoTemplatesList").innerHTML = [
      ...tpls.map(templateRow),
      ...dags.map(dagRow),
    ].join("") || `<p class="muted">No templates or pipelines yet.</p>`;
    const runs = data.pipeline_runs || [];
    $("autoPipeRunsList").innerHTML = runs.length
      ? `<p class="muted tiny">Recent pipeline runs</p>` + runs.map(pipeRunRow).join("")
      : `<p class="muted tiny">No pipeline runs yet.</p>`;
  }

  function sugRow(s) {
    return `<div class="auto-row" data-sug="${esc(s.id)}">
      <div><strong>${esc(s.title)}</strong><p class="muted tiny">${esc(s.explanation || "")}</p></div>
      <div class="auto-row-actions">
        <button type="button" class="ghost-btn tiny" data-sug-act="dismiss" data-id="${esc(s.id)}">Dismiss</button>
        <button type="button" class="apply-btn tiny" data-sug-act="promote" data-id="${esc(s.id)}">Approve…</button>
      </div></div>`;
  }

  function render(data) {
    home = data;
    const id = $("autoIdentityStrip");
    if (id && data.identity) {
      id.textContent = Object.entries(data.identity).map(([k, v]) => `${k}: ${v}`).join(" · ");
    }
    renderSummary(data);
    const rules = [...(data.rules?.enabled || []), ...(data.rules?.disabled || [])];
    $("autoRulesList").innerHTML = rules.length ? rules.map(ruleRow).join("") : `<p class="muted">No rules yet. Create one or draft from natural language.</p>`;
    $("autoRunsList").innerHTML = (data.recent_runs || []).length
      ? data.recent_runs.map(runRow).join("")
      : `<p class="muted">No runs yet.</p>`;
    $("autoFailList").innerHTML = (data.failures || []).length
      ? data.failures.map(runRow).join("")
      : `<p class="muted">No recent failures.</p>`;
    $("autoSuggestionsList").innerHTML = (data.suggestions || []).length
      ? data.suggestions.map(sugRow).join("")
      : `<p class="muted">No suggestions. Scan the action log from Dashboard or Automation.</p>`;
    $("autoSkillsList").innerHTML = (data.skills || []).length
      ? data.skills.map(skillRow).join("")
      : `<p class="muted">No skills installed.</p>`;
    $("autoLearnedList").innerHTML = (data.learned_workflows || []).length
      ? data.learned_workflows.map(learnedRow).join("")
      : `<p class="muted">No learned workflows.</p>`;
    renderPipelines(data);

    const wh = data.health?.webhook || {};
    $("autoWebhookPanel").innerHTML = `<p>${esc(wh.message || "")}</p>
      <p class="muted tiny">${esc(wh.url || "No URL")}</p>
      <p class="muted tiny">Engine: ${esc(data.health?.engine || "")} · Deep-link Job Center / Activity / Mission Control from row actions as needed.</p>`;

    // populate action select
    const sel = $("autoRuleAction");
    if (sel && data.actions) {
      sel.innerHTML = data.actions.map((a) => `<option value="${esc(a.id)}">${esc(a.name)}</option>`).join("");
    }
  }

  async function refresh() {
    try {
      const data = await api("/api/automation/home");
      render(data);
      announce("Automation Home refreshed");
    } catch (e) {
      window.showAriaToast?.(e.message || "Automation Home failed", "err", 4000);
    }
  }

  function openRuleEditor(rule) {
    editingRuleId = rule?.id || "";
    editingRuleParams = { ...(rule?.params || {}) };
    $("autoRuleName").value = rule?.name || "";
    $("autoRuleKind").value = rule?.kind || "interval";
    $("autoRuleExpr").value = rule?.expression || "3600";
    if (rule?.action) $("autoRuleAction").value = rule.action;
    $("autoRuleCondition").value = rule?.condition || "";
    $("autoRuleEnabled").checked = Boolean(rule?.enabled);
    previewRule();
    $("autoRuleModal")?.classList.remove("hidden");
  }

  function previewRule() {
    const p = $("autoRulePreview");
    if (!p) return;
    const paramsHint = Object.keys(editingRuleParams || {}).length
      ? ` · params=${JSON.stringify(editingRuleParams)}`
      : "";
    p.textContent = `${$("autoRuleKind").value} · ${$("autoRuleExpr").value} · ${$("autoRuleAction").value} · enabled=${$("autoRuleEnabled").checked}${paramsHint}`;
  }

  async function saveRule() {
    const body = {
      id: editingRuleId || undefined,
      name: $("autoRuleName").value || "Automation",
      kind: $("autoRuleKind").value,
      expression: $("autoRuleExpr").value,
      action: $("autoRuleAction").value,
      condition: $("autoRuleCondition").value,
      enabled: $("autoRuleEnabled").checked,
      params: { ...editingRuleParams },
    };
    const data = await api("/api/automation/rules", { method: "POST", body: JSON.stringify(body) });
    window.showAriaToast?.("Rule saved", "ok", 2000);
    $("autoRuleModal")?.classList.add("hidden");
    await refresh();
    return data;
  }

  async function runRule(id, dry) {
    const data = await api(`/api/automation/rules/${encodeURIComponent(id)}/run`, {
      method: "POST",
      body: JSON.stringify({ dry_run: !!dry }),
    });
    ingestActivity(data.result?.activity || data.activity);
    const st = data.status || data.result?.status;
    window.showAriaToast?.(
      `${dry ? "Dry run" : "Run"}: ${st}${data.result?.why ? " — " + data.result.why : ""}`,
      st === "succeeded" || st === "dry_run" ? "ok" : st === "skipped" ? "warn" : "err",
      3500,
    );
    await refresh();
  }

  async function runSkill(slug, dry) {
    const data = await api(`/api/automation/skills/${encodeURIComponent(slug)}/run`, {
      method: "POST",
      body: JSON.stringify({ dry_run: !!dry, confirm: !dry }),
    });
    ingestActivity(data.activity);
    window.showAriaToast?.(dry ? "Skill dry run done" : "Skill run finished", data.ok ? "ok" : "err", 3000);
    await refresh();
  }

  async function runLearned(slug, dry) {
    const data = await api(`/api/automation/workflows/${encodeURIComponent(slug)}/run`, {
      method: "POST",
      body: JSON.stringify({ dry_run: !!dry, confirm: !dry }),
    });
    ingestActivity(data.activity);
    window.showAriaToast?.(dry ? "Workflow dry run" : "Workflow finished", data.ok ? "ok" : "err", 3000);
    await refresh();
  }

  function openRunInspector(run) {
    lastPipeRun = run;
    if (!run) return;
    $("autoPipeRunTitle").textContent = `Pipeline run: ${run.name || run.id}`;
    $("autoPipeRunMeta").textContent = [
      `status=${run.status}`,
      `id=${run.run_id || run.id}`,
      `job=${run.job_id || "—"}`,
      `corr=${run.correlation_id || "—"}`,
      `${run.elapsed_ms || 0}ms`,
      run.dry_run ? "dry-run" : "executed",
      run.trigger || "",
    ].join(" · ");
    $("autoPipeRunSummary").innerHTML = `<p><strong>Success:</strong> ${esc(run.success_summary || "—")}</p>
      <p><strong>Failure:</strong> ${esc(run.failure_summary || "—")}</p>`;
    $("autoPipeRunVars").textContent = JSON.stringify(run.variables || {}, null, 2);
    renderRunSteps();
    $("autoPipeRunModal")?.classList.remove("hidden");
    $("autoPipeRunModal")?.focus?.();
    announce("Pipeline run details opened");
  }

  function renderRunSteps() {
    const run = lastPipeRun;
    if (!run) return;
    const q = ($("autoPipeRunFilter")?.value || "").toLowerCase();
    const st = $("autoPipeRunStatusFilter")?.value || "";
    const rows = (run.log || []).filter((r) => {
      if (q && !`${r.name} ${r.step} ${r.action} ${r.error || ""}`.toLowerCase().includes(q)) return false;
      if (st === "ok" && !(r.ok && !r.skipped)) return false;
      if (st === "fail" && r.ok) return false;
      if (st === "skip" && !r.skipped) return false;
      if (st === "retry" && !r.retry) return false;
      return true;
    });
    $("autoPipeRunSteps").innerHTML = rows
      .map((r) => {
        const cls = r.skipped ? "auto-step-skip" : r.ok ? "auto-step-ok" : "auto-step-fail";
        return `<div class="auto-row ${cls}" tabindex="0" data-expand="1">
          <div><strong>${esc(r.name || r.step)}</strong>
            <span class="muted tiny"> · ${esc(r.action || "")} · attempts=${esc(r.attempts || 1)}
            ${r.skipped ? " · skipped" : ""} ${r.retry ? " · retry" : ""} ${r.ok ? " · ok" : " · fail"}</span>
            <div class="auto-step-detail"><pre>${esc(JSON.stringify(r.result || r.error || r, null, 2))}</pre></div>
          </div></div>`;
      })
      .join("") || `<p class="muted">No matching steps.</p>`;
  }

  async function runPipeline(id, dry) {
    const data = await api(`/api/automation/pipelines/${encodeURIComponent(id)}/run`, {
      method: "POST",
      body: JSON.stringify({ dry_run: !!dry, confirm: !dry, trigger: "manual" }),
    });
    ingestActivity(data.activity);
    openRunInspector(data);
    window.showAriaToast?.(
      dry ? `Dry run: ${data.status}` : `Pipeline: ${data.status}`,
      data.ok || data.status === "dry_run" ? "ok" : "err",
      3500,
    );
    await refresh();
    return data;
  }

  async function openPipelineEditor(id) {
    const data = await api(`/api/automation/pipelines/${encodeURIComponent(id)}`);
    editingPipeline = data.pipeline;
    $("autoPipeEditName").value = editingPipeline.name || "";
    $("autoPipeEditDesc").value = editingPipeline.description || "";
    $("autoPipeEditTags").value = (editingPipeline.tags || []).join(", ");
    $("autoPipeEditEntry").value = editingPipeline.entry || "";
    $("autoPipeJson").value = JSON.stringify(editingPipeline, null, 2);
    renderFormSteps();
    $("autoPipeEditValidation").textContent = (data.validation?.errors || []).join("; ") ||
      ((data.validation?.warnings || []).length ? "Warnings: " + data.validation.warnings.join("; ") : "Valid");
    showPipeTab("form");
    $("autoPipeEditModal")?.classList.remove("hidden");
  }

  function renderFormSteps() {
    const steps = editingPipeline?.steps || [];
    $("autoPipeFormSteps").innerHTML = steps
      .map(
        (s, i) => `<div class="auto-row"><div>
        <strong>${esc(s.name || s.id)}</strong>
        <span class="muted tiny"> · ${esc(s.action)} · retries=${esc(s.retries || 0)}
        · when=${esc(s.when || "—")} · timeout=${esc(s.timeout_sec || "—")}</span>
        <label class="muted tiny">Action <input data-step-field="action" data-i="${i}" class="audio-path-input" value="${esc(s.action)}" /></label>
        <label class="muted tiny">When <input data-step-field="when" data-i="${i}" class="audio-path-input" value="${esc(s.when || "")}" /></label>
      </div></div>`,
      )
      .join("") || `<p class="muted">No steps — edit JSON.</p>`;
    $("autoPipeFormSteps")?.querySelectorAll("[data-step-field]")?.forEach((el) => {
      el.addEventListener("change", () => {
        const i = Number(el.dataset.i);
        const field = el.dataset.stepField;
        if (editingPipeline?.steps?.[i]) editingPipeline.steps[i][field] = el.value;
        $("autoPipeJson").value = JSON.stringify(editingPipeline, null, 2);
      });
    });
  }

  function showPipeTab(which) {
    const form = $("autoPipeFormSteps");
    const json = $("autoPipeJson");
    const canvas = $("autoPipeCanvas");
    form.hidden = which !== "form";
    json.hidden = which !== "json";
    canvas.hidden = which !== "canvas";
    $("autoPipeTabForm")?.setAttribute("aria-selected", which === "form" ? "true" : "false");
    $("autoPipeTabJson")?.setAttribute("aria-selected", which === "json" ? "true" : "false");
    $("autoPipeTabCanvas")?.setAttribute("aria-selected", which === "canvas" ? "true" : "false");
  }

  async function loadCanvas() {
    if (!editingPipeline?.id) return;
    const data = await api(`/api/automation/pipelines/${encodeURIComponent(editingPipeline.id)}/canvas`);
    $("autoPipeCanvas").innerHTML =
      `<p class="muted tiny">${esc(data.note || "")}</p>` +
      (data.nodes || [])
        .map(
          (n) =>
            `<span class="auto-pipe-node ${n.entry ? "is-entry" : ""}" title="${esc(n.action)}">${esc(n.label)}</span>`,
        )
        .join("") +
      `<p class="muted tiny">Edges: ${(data.edges || []).map((e) => `${e.from}→${e.to}(${e.kind})`).join(", ") || "none"}</p>`;
  }

  async function promoteLearnedToDag(slug) {
    const data = await api("/api/automation/pipelines/promote-learned", {
      method: "POST",
      body: JSON.stringify({ slug }),
    });
    if (!data.ok) {
      window.showAriaToast?.(data.error || "Promote failed", "err", 3000);
      return;
    }
    if (!window.confirm?.("Review draft and save as pipeline? Nothing runs automatically.")) return;
    const saved = await api("/api/automation/pipelines/nl/save", {
      method: "POST",
      body: JSON.stringify({ confirm: true, draft: data.draft }),
    });
    window.showAriaToast?.("Pipeline draft saved — edit and schedule in Automation", "ok", 3500);
    await refresh();
    if (saved.pipeline?.id) await openPipelineEditor(saved.pipeline.id);
  }

  function bind() {
    $("autoRefreshBtn")?.addEventListener("click", refresh);
    $("autoPauseBtn")?.addEventListener("click", async () => {
      await api("/api/automation/pause", { method: "POST", body: JSON.stringify({ paused: true }) });
      window.showAriaToast?.("Automations paused", "warn", 2500);
      refresh();
    });
    $("autoResumeBtn")?.addEventListener("click", async () => {
      await api("/api/automation/pause", { method: "POST", body: JSON.stringify({ paused: false }) });
      await api("/api/automation/engine/start", { method: "POST", body: "{}" });
      window.showAriaToast?.("Automations resumed", "ok", 2500);
      refresh();
    });
    $("autoNewRuleBtn")?.addEventListener("click", () => openRuleEditor(null));
    $("autoViewPathsBtn")?.addEventListener("click", () => window.AriaWorkflows?.openModal?.());
    $("autoWebhookBtn")?.addEventListener("click", () => {
      const wh = home?.health?.webhook || {};
      $("autoWebhookStatus").textContent = wh.message || "";
      $("autoWebhookUrl").textContent = wh.url || "";
      $("autoWebhookModal")?.classList.remove("hidden");
    });
    $("autoExportBtn")?.addEventListener("click", async () => {
      const data = await api("/api/automation/rules/export");
      await navigator.clipboard?.writeText(JSON.stringify(data, null, 2));
      window.showAriaToast?.("Rules exported to clipboard", "ok", 2500);
    });
    $("autoImportBtn")?.addEventListener("click", async () => {
      const text = prompt("Paste exported rules JSON");
      if (!text) return;
      try {
        const payload = JSON.parse(text);
        await api("/api/automation/rules/import", { method: "POST", body: JSON.stringify(payload) });
        window.showAriaToast?.("Rules imported", "ok", 2500);
        refresh();
      } catch (e) {
        window.showAriaToast?.(e.message || "Import failed", "err", 4000);
      }
    });
    $("autoNlBtn")?.addEventListener("click", async () => {
      const text = $("autoNlInput")?.value || "";
      const draft = await api("/api/automation/nl", { method: "POST", body: JSON.stringify({ text }) });
      if (!draft.ok) {
        window.showAriaToast?.(draft.error || "Could not parse", "warn", 3000);
        return;
      }
      if (draft.intent === "pause_all") {
        const ok = window.confirm?.(draft.preview || "Pause all automations?");
        if (ok) {
          await api("/api/automation/nl/confirm", {
            method: "POST",
            body: JSON.stringify({ confirm: true, intent: "pause_all" }),
          });
          refresh();
        }
        return;
      }
      if (draft.draft) {
        const enable = window.confirm?.(`${draft.preview}\n\nSave draft? (OK = save disabled; use editor to enable)`);
        if (enable) {
          await api("/api/automation/nl/confirm", {
            method: "POST",
            body: JSON.stringify({ confirm: true, draft: draft.draft, enable: false }),
          });
          refresh();
        } else {
          openRuleEditor(draft.draft);
        }
      }
    });
    $("autoSearchInput")?.addEventListener("input", async () => {
      const q = $("autoSearchInput").value || "";
      const box = $("autoSearchHits");
      if (!q.trim()) {
        box?.classList.add("hidden");
        return;
      }
      const data = await api(`/api/automation/search?q=${encodeURIComponent(q)}`);
      box.classList.remove("hidden");
      box.innerHTML = (data.hits || [])
        .map((h) => `<button type="button" class="ghost-btn tiny" data-hit-kind="${esc(h.kind)}">${esc(h.kind)}: ${esc(h.title)}</button>`)
        .join(" ") || `<span class="muted">No hits</span>`;
    });

    $("autoRulesList")?.addEventListener("click", async (ev) => {
      const btn = ev.target.closest("button[data-act]");
      if (!btn) return;
      const id = btn.dataset.id;
      const act = btn.dataset.act;
      const rule = (home?.rules?.all || []).find((r) => r.id === id);
      if (act === "run") await runRule(id, false);
      else if (act === "dry") await runRule(id, true);
      else if (act === "edit") openRuleEditor(rule);
      else if (act === "toggle" && rule) {
        await api("/api/automation/rules", {
          method: "POST",
          body: JSON.stringify({ ...rule, enabled: !rule.enabled }),
        });
        refresh();
      } else if (act === "mute") {
        await api("/api/automation/mute", { method: "POST", body: JSON.stringify({ id, muted: true }) });
        window.showAriaToast?.("Muted in Activity", "ok", 2000);
      } else if (act === "del") {
        if (window.confirm?.("Delete this rule?")) {
          await api(`/api/automation/rules/${encodeURIComponent(id)}`, { method: "DELETE" });
          refresh();
        }
      }
    });

    $("autoSkillsList")?.addEventListener("click", async (ev) => {
      const btn = ev.target.closest("button[data-skill-act]");
      if (!btn) return;
      const slug = btn.dataset.slug;
      if (btn.dataset.skillAct === "dry") await runSkill(slug, true);
      else if (btn.dataset.skillAct === "run") await runSkill(slug, false);
      else if (btn.dataset.skillAct === "schedule") {
        openRuleEditor({
          name: `Skill: ${slug}`,
          kind: "interval",
          expression: "86400",
          action: "skill_run",
          params: { slug },
          enabled: false,
        });
        $("autoRuleAction").value = "skill_run";
      }
    });

    $("autoLearnedList")?.addEventListener("click", async (ev) => {
      const btn = ev.target.closest("button[data-wf-act]");
      if (!btn) return;
      const slug = btn.dataset.slug;
      if (btn.dataset.wfAct === "dry") await runLearned(slug, true);
      else if (btn.dataset.wfAct === "run") await runLearned(slug, false);
      else if (btn.dataset.wfAct === "promote-dag") await promoteLearnedToDag(slug);
      else if (btn.dataset.wfAct === "schedule" || btn.dataset.wfAct === "promote") {
        openRuleEditor({
          name: `Learned: ${slug}`,
          kind: "interval",
          expression: "86400",
          action: "workflow_learned_run",
          params: { slug },
          enabled: false,
        });
      }
    });

    $("autoSuggestionsList")?.addEventListener("click", async (ev) => {
      const btn = ev.target.closest("button[data-sug-act]");
      if (!btn) return;
      const id = btn.dataset.id;
      if (btn.dataset.sugAct === "dismiss") {
        await api(`/api/automation/suggestions/${encodeURIComponent(id)}/dismiss`, { method: "POST", body: "{}" });
        refresh();
      } else if (btn.dataset.sugAct === "promote") {
        if (!window.confirm?.("Create a disabled rule from this suggestion? You must enable it manually.")) return;
        await api(`/api/automation/suggestions/${encodeURIComponent(id)}/promote`, {
          method: "POST",
          body: JSON.stringify({ confirm: true, enable: false }),
        });
        refresh();
      }
    });

    $("autoTemplatesList")?.addEventListener("click", async (ev) => {
      const tpl = ev.target.closest("[data-tpl]");
      if (tpl) {
        const data = await api("/api/automation/pipelines/from-template", {
          method: "POST",
          body: JSON.stringify({ template: tpl.dataset.tpl }),
        });
        window.showAriaToast?.(data.reused ? "Reused existing pipeline" : "Pipeline created from template", "ok", 2500);
        refresh();
        return;
      }
      const btn = ev.target.closest("[data-dag-act]");
      if (!btn) return;
      const id = btn.dataset.id;
      const act = btn.dataset.dagAct;
      if (act === "dry") await runPipeline(id, true);
      else if (act === "run") await runPipeline(id, false);
      else if (act === "inspect") {
        const last = await api(`/api/automation/pipelines/${encodeURIComponent(id)}/last-run`);
        if (last.run) openRunInspector(last.run);
        else {
          const expl = await api(`/api/automation/pipelines/${encodeURIComponent(id)}/explain`);
          openRunInspector({
            name: expl.name,
            status: "inspect",
            log: (expl.steps || []).map((s) => ({
              step: s.id,
              name: s.name,
              action: s.action,
              ok: true,
              result: s.action_meta,
            })),
            variables: expl.variables || {},
            success_summary: expl.summary,
          });
        }
      } else if (act === "edit") await openPipelineEditor(id);
      else if (act === "schedule") {
        openRuleEditor({
          name: `Pipeline: ${id}`,
          kind: "interval",
          expression: "86400",
          action: "workflow_dag_run",
          params: { workflow_id: id },
          enabled: false,
        });
        $("autoRuleAction").value = "workflow_dag_run";
      } else if (act === "fav") {
        await api(`/api/automation/pipelines/${encodeURIComponent(id)}/favorite`, {
          method: "POST",
          body: JSON.stringify({ favorite: true }),
        });
        refresh();
      } else if (act === "dup") {
        await api(`/api/automation/pipelines/${encodeURIComponent(id)}/duplicate`, {
          method: "POST",
          body: "{}",
        });
        refresh();
      } else if (act === "del") {
        if (!window.confirm?.("Delete this pipeline?")) return;
        await api(`/api/automation/pipelines/${encodeURIComponent(id)}`, { method: "DELETE" });
        refresh();
      }
    });

    $("autoPipeRunsList")?.addEventListener("click", async (ev) => {
      const btn = ev.target.closest("[data-pipe-run-open]");
      if (!btn) return;
      const data = await api(`/api/automation/pipeline-runs/${encodeURIComponent(btn.dataset.pipeRunOpen)}`);
      if (data.run) openRunInspector(data.run);
    });

    $("autoPipeSearch")?.addEventListener("input", () => {
      pipeFilter.q = $("autoPipeSearch").value || "";
      if (home) renderPipelines(home);
    });
    $("autoPipeSort")?.addEventListener("change", () => {
      pipeFilter.sort = $("autoPipeSort").value || "name";
      if (home) renderPipelines(home);
    });
    $("autoPipeFavOnly")?.addEventListener("change", () => {
      pipeFilter.fav = !!$("autoPipeFavOnly").checked;
      if (home) renderPipelines(home);
    });
    $("autoPipeExportBtn")?.addEventListener("click", async () => {
      const data = await api("/api/automation/pipelines/export", { method: "POST", body: "{}" });
      await navigator.clipboard?.writeText(JSON.stringify(data, null, 2));
      window.showAriaToast?.(`Exported ${data.count || 0} pipelines`, "ok", 2500);
    });
    $("autoPipeNlBtn")?.addEventListener("click", () => {
      nlDraft = null;
      $("autoPipeNlText").value = "";
      $("autoPipeNlPreview").textContent = "";
      $("autoPipeNlSaveBtn").disabled = true;
      $("autoPipeNlModal")?.classList.remove("hidden");
    });
    $("autoPipeNlDraftBtn")?.addEventListener("click", async () => {
      const data = await api("/api/automation/pipelines/nl", {
        method: "POST",
        body: JSON.stringify({ text: $("autoPipeNlText").value }),
      });
      nlDraft = data.draft;
      $("autoPipeNlPreview").textContent = data.preview || data.explanation || "";
      $("autoPipeNlSaveBtn").disabled = !data.ok;
    });
    $("autoPipeNlSaveBtn")?.addEventListener("click", async () => {
      if (!nlDraft) return;
      await api("/api/automation/pipelines/nl/save", {
        method: "POST",
        body: JSON.stringify({ confirm: true, draft: nlDraft }),
      });
      $("autoPipeNlModal")?.classList.add("hidden");
      window.showAriaToast?.("Draft saved — review in Pipelines", "ok", 3000);
      refresh();
    });
    $("autoPipeNlCloseBtn")?.addEventListener("click", () => $("autoPipeNlModal")?.classList.add("hidden"));

    $("autoPipeRunFilter")?.addEventListener("input", renderRunSteps);
    $("autoPipeRunStatusFilter")?.addEventListener("change", renderRunSteps);
    $("autoPipeRunSteps")?.addEventListener("click", (ev) => {
      const row = ev.target.closest(".auto-row[data-expand]");
      if (row) row.classList.toggle("is-open");
    });
    $("autoPipeRunCloseBtn")?.addEventListener("click", () => $("autoPipeRunModal")?.classList.add("hidden"));
    $("autoPipeRunJobsBtn")?.addEventListener("click", () => {
      $("autoPipeRunModal")?.classList.add("hidden");
      window.switchToView?.("jobs") || window.AriaActions?.goView?.("jobs");
    });
    $("autoPipeRunActivityBtn")?.addEventListener("click", () => {
      window.AriaActivity?.open?.();
    });
    $("autoPipeRunRetryBtn")?.addEventListener("click", async () => {
      const run = lastPipeRun;
      if (!run?.pipeline_id && !run?.workflow_id) return;
      const failed = (run.log || []).find((r) => !r.ok && !r.skipped);
      const pid = run.pipeline_id || run.workflow_id;
      const data = await api(`/api/automation/pipelines/${encodeURIComponent(pid)}/run`, {
        method: "POST",
        body: JSON.stringify({ confirm: true, from_step: failed?.step || null, trigger: "retry" }),
      });
      ingestActivity(data.activity);
      openRunInspector(data);
      refresh();
    });

    $("autoPipeTabForm")?.addEventListener("click", () => showPipeTab("form"));
    $("autoPipeTabJson")?.addEventListener("click", () => {
      showPipeTab("json");
    });
    $("autoPipeTabCanvas")?.addEventListener("click", async () => {
      showPipeTab("canvas");
      await loadCanvas();
    });
    $("autoPipeEditValidateBtn")?.addEventListener("click", async () => {
      try {
        editingPipeline = JSON.parse($("autoPipeJson").value);
      } catch (e) {
        $("autoPipeEditValidation").textContent = "Invalid JSON: " + e.message;
        return;
      }
      const data = await api("/api/automation/pipelines", {
        method: "POST",
        body: JSON.stringify({ ...editingPipeline, bump_version: false }),
      });
      $("autoPipeEditValidation").textContent =
        (data.validation?.errors || []).join("; ") ||
        ((data.validation?.warnings || []).length ? "Warnings: " + data.validation.warnings.join("; ") : "Valid");
    });
    $("autoPipeEditSaveBtn")?.addEventListener("click", async () => {
      try {
        const fromJson = JSON.parse($("autoPipeJson").value);
        editingPipeline = {
          ...fromJson,
          name: $("autoPipeEditName").value || fromJson.name,
          description: $("autoPipeEditDesc").value || "",
          tags: ($("autoPipeEditTags").value || "")
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean),
          entry: $("autoPipeEditEntry").value || fromJson.entry,
        };
      } catch (e) {
        window.showAriaToast?.(e.message, "err", 3000);
        return;
      }
      await api("/api/automation/pipelines", {
        method: "POST",
        body: JSON.stringify({ ...editingPipeline, bump_version: true }),
      });
      $("autoPipeEditModal")?.classList.add("hidden");
      window.showAriaToast?.("Pipeline saved", "ok", 2500);
      refresh();
    });
    $("autoPipeEditCloseBtn")?.addEventListener("click", () => $("autoPipeEditModal")?.classList.add("hidden"));

    $("autoRuleSaveBtn")?.addEventListener("click", () => saveRule().catch((e) => window.showAriaToast?.(e.message, "err")));
    $("autoRuleDryBtn")?.addEventListener("click", async () => {
      const saved = await saveRule();
      if (saved?.rule?.id) await runRule(saved.rule.id, true);
    });
    $("autoRuleCloseBtn")?.addEventListener("click", () => $("autoRuleModal")?.classList.add("hidden"));
    ["autoRuleKind", "autoRuleExpr", "autoRuleAction", "autoRuleEnabled"].forEach((id) => {
      $(id)?.addEventListener("change", previewRule);
      $(id)?.addEventListener("input", previewRule);
    });

    $("autoWebhookCloseBtn")?.addEventListener("click", () => $("autoWebhookModal")?.classList.add("hidden"));
    $("autoWebhookCopyBtn")?.addEventListener("click", async () => {
      const url = home?.health?.webhook?.url || "";
      if (url) await navigator.clipboard?.writeText(url);
      window.showAriaToast?.(url ? "Webhook URL copied" : "No URL", url ? "ok" : "warn", 2500);
    });
    $("autoWebhookTestBtn")?.addEventListener("click", async () => {
      const data = await api("/api/automation/webhook/test", { method: "POST", body: "{}" });
      window.showAriaToast?.(data.message || "Checked", data.ok ? "ok" : "warn", 4000);
    });
    $("autoWebhookHaBtn")?.addEventListener("click", () => {
      $("autoWebhookModal")?.classList.add("hidden");
      document.getElementById("haSetupWizardBtn")?.click?.();
      window.AriaActions?.system?.haSetup?.();
    });

    $("dashOpenAutomationBtn")?.addEventListener("click", () => window.switchToView?.("automation"));
  }

  function initAutomation() {
    refresh();
  }

  window.initAutomation = initAutomation;
  window.AriaAutomationHome = {
    open: () => {
      window.switchToView?.("automation");
      refresh();
    },
    refresh,
    openRuleEditor,
    openRunInspector,
    runPipeline,
    openPipelineEditor,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();
})();
