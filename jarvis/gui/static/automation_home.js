/** Automation Home — Aria OS orchestration layer (not Job Center / Activity / HA / View Paths). */
(function () {
  "use strict";

  let home = null;
  let editingRuleId = "";

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
        <button type="button" class="ghost-btn tiny" data-wf-act="promote" data-slug="${slug}">Promote</button>
      </div></div>`;
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
    const tpls = data.templates || [];
    const dags = data.workflow_dags || [];
    $("autoTemplatesList").innerHTML = [
      ...tpls.map((t) => `<div class="auto-row"><div><strong>Template: ${esc(t)}</strong></div>
        <button type="button" class="ghost-btn tiny" data-tpl="${esc(t)}">Create</button></div>`),
      ...dags.map((d) => `<div class="auto-row"><div><strong>${esc(d.name || d.id)}</strong></div>
        <button type="button" class="ghost-btn tiny" data-dag-run="${esc(d.id)}">Run</button></div>`),
    ].join("") || `<p class="muted">No templates.</p>`;

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
    p.textContent = `${$("autoRuleKind").value} · ${$("autoRuleExpr").value} · ${$("autoRuleAction").value} · enabled=${$("autoRuleEnabled").checked}`;
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
      params: {},
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
      else if (btn.dataset.wfAct === "schedule" || btn.dataset.wfAct === "promote") {
        openRuleEditor({
          name: `Learned: ${slug}`,
          kind: "interval",
          expression: "86400",
          action: "workflow_learned_run",
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
        await api("/api/intelligence/workflows/from-template", {
          method: "POST",
          body: JSON.stringify({ template: tpl.dataset.tpl }),
        });
        window.showAriaToast?.("DAG created from template", "ok", 2500);
        refresh();
      }
      const dag = ev.target.closest("[data-dag-run]");
      if (dag) {
        const data = await api(`/api/intelligence/workflows/${encodeURIComponent(dag.dataset.dagRun)}/run`, {
          method: "POST",
          body: "{}",
        });
        window.showAriaToast?.(data.ok ? "DAG finished" : "DAG failed", data.ok ? "ok" : "err", 3000);
        refresh();
      }
    });

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
      document.getElementById("haSetupBtn")?.click?.();
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
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();
})();
