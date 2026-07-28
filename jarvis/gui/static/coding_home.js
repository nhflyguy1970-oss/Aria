/** Coding Home — propose → review → apply → undo → verify (not Projects / Job Center / Models). */
(function () {
  "use strict";

  let _data = null;
  let _tab = "overview";
  const TABS = [
    ["overview", "Overview"],
    ["proposals", "Proposals"],
    ["history", "History"],
    ["jobs", "Jobs"],
    ["tools", "LSP & Git"],
    ["prefs", "Preferences"],
    ["experimental", "Experimental"],
  ];

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  async function api(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.message || data.detail || data.error || res.statusText);
    return data;
  }

  function severityClass(sev) {
    if (sev === "error") return "coding-banner--error";
    if (sev === "warn") return "coding-banner--warn";
    return "coding-banner--ok";
  }

  function renderGuardrails() {
    const g = _data.guardrails || {};
    const repo = g.repository || {};
    const proj = g.active_project || {};
    const warns = (g.warnings || [])
      .map((w) => `<li class="coding-warn coding-warn--${esc(w.level)}">${esc(w.message)}</li>`)
      .join("");
    return `
      <section class="coding-hero" aria-label="Coding root">
        <div class="coding-banner ${severityClass(g.severity)}" role="status">
          ${esc(_data.banner || "")}
        </div>
        <dl class="coding-meta">
          <div><dt>Project</dt><dd>${esc(proj.title || proj.slug || "—")}</dd></div>
          <div><dt>Coding root</dt><dd><code>${esc(g.coding_root || "—")}</code></dd></div>
          <div><dt>Write target</dt><dd><code>${esc(g.write_target || "—")}</code></dd></div>
          <div><dt>Repository</dt><dd>${repo.is_repo ? esc(repo.branch || "(no branch)") : "Not a git repo"}</dd></div>
        </dl>
        ${warns ? `<ul class="coding-warns">${warns}</ul>` : ""}
        ${!g.coding_root ? `<p class="muted">No coding root — <button type="button" class="ghost-btn tiny" data-coding-link="projects">Open Projects</button> to set an active workspace.</p>` : ""}
      </section>`;
  }

  function renderModel() {
    const m = _data.model || {};
    return `
      <section class="coding-model-chip" aria-label="Coding model">
        <strong>Coding model</strong>
        <span><code>${esc(m.model || "—")}</code> · ${esc(m.provider || "")} · role ${esc(m.role || "coding")}</span>
        <button type="button" class="ghost-btn tiny" data-coding-link="models">Models Home</button>
      </section>`;
  }

  function renderOverview() {
    const terms = Object.entries(_data.terminology || {})
      .slice(0, 6)
      .map(([k, v]) => `<li><strong>${esc(k)}</strong> — ${esc(v)}</li>`)
      .join("");
    const open = (_data.open_proposals || [])
      .map(
        (p) =>
          `<li><code>${esc(p.id)}</code> ${esc(p.summary || p.mode || "")}
            <button type="button" class="ghost-btn tiny" data-coding-brief="${esc(p.id)}">Brief</button>
            <button type="button" class="apply-btn tiny" data-coding-apply="${esc(p.id)}">Apply</button>
          </li>`
      )
      .join("") || "<li class=\"muted\">No open proposals. Ask Chat to fix or implement something.</li>";
    const jobs = (_data.recent_jobs || [])
      .slice(0, 5)
      .map((j) => `<li><strong>${esc(j.label || j.id)}</strong> · ${esc(j.message || "")} ${j.done ? "✓" : "…"}</li>`)
      .join("") || "<li class=\"muted\">No recent coding jobs.</li>";
    const git = _data.git || {};
    const last = _data.last_coding_task;
    return `
      ${renderGuardrails()}
      ${renderModel()}
      <section class="coding-links" aria-label="Related products">
        <button type="button" class="ghost-btn small" data-coding-link="projects">Projects</button>
        <button type="button" class="ghost-btn small" data-coding-link="jobs">Job Center</button>
        <button type="button" class="ghost-btn small" data-coding-link="models">Models</button>
        <button type="button" class="ghost-btn small" data-coding-link="activity">Activity</button>
        <button type="button" class="ghost-btn small" data-coding-link="chat">Chat</button>
        <button type="button" class="ghost-btn small" data-coding-link="planner">Planner</button>
      </section>
      <div class="coding-grid">
        <section>
          <h3>Open proposals</h3>
          <ul class="coding-list">${open}</ul>
        </section>
        <section>
          <h3>Recent jobs</h3>
          <ul class="coding-list">${jobs}</ul>
          <button type="button" class="ghost-btn tiny" data-coding-link="jobs">Open Job Center</button>
        </section>
        <section>
          <h3>Repository</h3>
          <pre class="coding-pre muted">${esc(git.status_short || (git.is_repo ? "(clean)" : "Not a repository"))}</pre>
        </section>
        <section>
          <h3>Continue task</h3>
          ${
            last
              ? `<p><code>${esc(last.id)}</code> ${esc(last.title || "")} · ${esc(last.status || "")}
                   <button type="button" class="ghost-btn tiny" data-coding-continue="${esc(last.id)}">Continue in Chat</button></p>`
              : `<p class="muted">No paused coding task.</p>`
          }
        </section>
      </div>
      <section>
        <h3>Quick actions</h3>
        <div class="coding-quick-row">
          ${(_data.quick_actions || [])
            .filter((a) => !a.experimental)
            .map(
              (a) =>
                `<button type="button" class="ghost-btn small" data-coding-chat="${esc(a.chat || "")}">${esc(a.label)}</button>`
            )
            .join("")}
        </div>
      </section>
      <details class="coding-terms">
        <summary>Terminology</summary>
        <ul>${terms}</ul>
        <p class="muted tiny">${esc(_data.philosophy || "")}</p>
      </details>`;
  }

  function renderProposals() {
    const open = (_data.open_proposals || [])
      .map(
        (p) => `
      <article class="coding-card" tabindex="0">
        <header><code>${esc(p.id)}</code> · ${esc(p.mode || "")}
          ${p.syntax_ok === false ? '<span class="coding-badge coding-badge--warn">syntax</span>' : ""}
        </header>
        <p>${esc(p.summary || "")}</p>
        <p class="muted tiny">${esc((p.files || []).join(", "))}</p>
        <div>
          <button type="button" class="ghost-btn tiny" data-coding-brief="${esc(p.id)}">Quality brief</button>
          <button type="button" class="apply-btn tiny" data-coding-apply="${esc(p.id)}">Apply</button>
          <button type="button" class="ghost-btn tiny" data-coding-export="${esc(p.id)}">Export patch</button>
        </div>
        <div id="codingBrief_${esc(p.id)}" class="coding-brief hidden"></div>
      </article>`
      )
      .join("") || `<p class="muted coding-empty">No open proposals. Use Chat or Experimental workflows to create one.</p>`;
    return `<section aria-label="Open proposals">${open}</section>`;
  }

  async function loadHistory(q) {
    const params = new URLSearchParams({ limit: "40" });
    if (q) params.set("q", q);
    const status = $("codingHistoryStatus")?.value || "";
    if (status) params.set("status", status);
    const data = await api(`/api/coding/proposals/history?${params}`);
    const list = $("codingHistoryList");
    if (!list) return;
    const items = data.items || [];
    list.innerHTML = items.length
      ? items
          .map(
            (e) => `<li>
          <code>${esc(e.id)}</code>
          <span class="coding-badge">${esc(e.status)}</span>
          ${e.bookmarked ? "★" : ""}
          ${esc(e.summary || "").slice(0, 120)}
          <span class="muted tiny">${esc((e.files || []).slice(0, 3).join(", "))}</span>
          · model ${esc(e.model || "—")} · verify ${esc(e.verification_status || "—")}
          <button type="button" class="ghost-btn tiny" data-coding-restore="${esc(e.id)}">Restore</button>
          <button type="button" class="ghost-btn tiny" data-coding-export="${esc(e.id)}">Export</button>
          <button type="button" class="ghost-btn tiny" data-coding-bookmark="${esc(e.id)}" data-on="${e.bookmarked ? "0" : "1"}">${e.bookmarked ? "Unstar" : "Star"}</button>
        </li>`
          )
          .join("")
      : `<li class="muted">No proposal history yet.</li>`;
  }

  function renderHistory() {
    return `
      <section aria-label="Proposal history">
        <div class="coding-filter-row">
          <input type="search" id="codingHistorySearch" placeholder="Search proposals…" aria-label="Search proposal history" />
          <select id="codingHistoryStatus" aria-label="Filter by status">
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="applied">Applied</option>
            <option value="rejected">Rejected</option>
            <option value="undone">Undone</option>
          </select>
          <button type="button" class="ghost-btn small" id="codingHistoryRefresh">Search</button>
        </div>
        <ul id="codingHistoryList" class="coding-list"><li class="muted">Loading…</li></ul>
      </section>`;
  }

  function renderJobs() {
    const jobs = (_data.recent_jobs || [])
      .map((j) => {
        const links = j.deep_links || {};
        return `<li class="coding-job-row">
          <strong>${esc(j.label || j.id)}</strong>
          <span class="muted">${esc(j.message || "")}</span>
          ${j.proposal_id ? `<code>${esc(j.proposal_id)}</code>` : ""}
          <div class="coding-job-links">
            <button type="button" class="ghost-btn tiny" data-coding-link="jobs">Job Center</button>
            ${j.proposal_id ? `<button type="button" class="ghost-btn tiny" data-coding-brief="${esc(j.proposal_id)}">Proposal</button>` : ""}
            <button type="button" class="ghost-btn tiny" data-coding-link="chat">Chat</button>
            <button type="button" class="ghost-btn tiny" data-coding-verify-last="1">Verify</button>
            <button type="button" class="ghost-btn tiny" data-coding-undo="1">Undo</button>
            <button type="button" class="ghost-btn tiny" data-coding-link="projects">Project</button>
          </div>
        </li>`;
      })
      .join("") || `<li class="muted">No coding jobs. Long agent runs appear here and in Job Center.</li>`;
    return `<section><h3>Recent coding jobs</h3><ul class="coding-list">${jobs}</ul></section>`;
  }

  function renderTools() {
    const lsp = _data.lsp || {};
    const tools = lsp.tools || {};
    const toolBits = Object.entries(tools)
      .map(([k, v]) => `<li>${esc(k)}: ${v ? "ready" : "missing"}</li>`)
      .join("");
    return `
      <section>
        <p class="muted">LSP and Git live primarily in the Developer sidebar. Coding Home organizes; it does not replace those tools.</p>
        <h3>LSP tools</h3>
        <ul>${toolBits || "<li class=\"muted\">Status unavailable — use Developer → LSP.</li>"}</ul>
        <button type="button" class="ghost-btn small" id="codingFocusLsp">Focus Developer LSP</button>
        <h3>Git summary</h3>
        <pre class="coding-pre muted">${esc((_data.git || {}).status_short || "—")}</pre>
      </section>`;
  }

  function renderPrefs() {
    const prefs = (_data.preferences || {}).preferences || {};
    const suggestions = ((_data.preferences || {}).suggestions || [])
      .map((s) => `<li>${esc(s)}</li>`)
      .join("");
    return `
      <section aria-label="Coding preferences">
        <p class="muted">Suggestions only — never silently change coding behavior.</p>
        <label class="coding-pref-row"><input type="checkbox" id="codingPrefEnabled" ${prefs.enabled ? "checked" : ""}/> Enable preference memory</label>
        <label class="coding-pref-row">Style <input type="text" id="codingPrefStyle" value="${esc(prefs.style || "")}" placeholder="e.g. prefer small diffs"/></label>
        <label class="coding-pref-row">Formatter <input type="text" id="codingPrefFormatter" value="${esc(prefs.formatter || "")}"/></label>
        <label class="coding-pref-row">Test runner <input type="text" id="codingPrefRunner" value="${esc(prefs.test_runner || "pytest")}"/></label>
        <label class="coding-pref-row">Notes <input type="text" id="codingPrefNotes" value="${esc(prefs.notes || "")}"/></label>
        <button type="button" class="apply-btn small" id="codingPrefSave">Save suggestions</button>
        <ul>${suggestions || "<li class=\"muted\">No active suggestions.</li>"}</ul>
      </section>`;
  }

  function renderExperimental() {
    return `
      <section aria-label="Experimental coding workflows">
        <article class="coding-card">
          <h3>Vision-assisted bug fix</h3>
          <p class="muted">Screenshot → likely files → explanation → proposal. Never auto-applies.</p>
          <input type="text" id="codingVisionPath" placeholder="Path to screenshot" aria-label="Screenshot path"/>
          <input type="text" id="codingVisionHint" placeholder="Optional hint" aria-label="Vision hint"/>
          <button type="button" class="ghost-btn small" id="codingVisionGo">Analyze & propose</button>
          <pre id="codingVisionOut" class="coding-pre muted"></pre>
        </article>
        <article class="coding-card">
          <h3>Spec → code</h3>
          <p class="muted">Documents → plan → proposal → diff. Operator Apply + Verify.</p>
          <input type="text" id="codingSpecPath" placeholder="Document path (optional)" aria-label="Spec document path"/>
          <input type="text" id="codingSpecQuery" placeholder="Or search query / doc id" aria-label="Spec query"/>
          <button type="button" class="ghost-btn small" id="codingSpecGo">Plan & propose</button>
          <pre id="codingSpecOut" class="coding-pre muted"></pre>
        </article>
      </section>`;
  }

  function renderBody() {
    if (_tab === "overview") return renderOverview();
    if (_tab === "proposals") return renderProposals();
    if (_tab === "history") return renderHistory();
    if (_tab === "jobs") return renderJobs();
    if (_tab === "tools") return renderTools();
    if (_tab === "prefs") return renderPrefs();
    if (_tab === "experimental") return renderExperimental();
    return renderOverview();
  }

  function renderTabs() {
    const nav = $("codingHomeTabs");
    if (!nav) return;
    nav.innerHTML = TABS.map(
      ([id, label]) =>
        `<button type="button" class="mc-tab${_tab === id ? " active" : ""}" data-coding-tab="${id}" role="tab" aria-selected="${_tab === id}">${label}</button>`
    ).join("");
  }

  async function refresh() {
    const status = $("codingHomeStatus");
    if (status) status.textContent = "Loading…";
    try {
      _data = await api("/api/coding/home");
      renderTabs();
      const body = $("codingHomeBody");
      if (body) body.innerHTML = renderBody();
      if (_tab === "history") await loadHistory($("codingHistorySearch")?.value || "");
      bindBody();
      if (status) status.textContent = "Ready";
    } catch (err) {
      if (status) status.textContent = err.message || "Failed";
      window.showAriaToast?.(err.message || "Coding Home failed", "err", 4000);
    }
  }

  async function showBrief(pid) {
    try {
      const brief = await api(`/api/coding/proposals/${encodeURIComponent(pid)}/brief`);
      const box = $(`codingBrief_${pid}`) || document.createElement("div");
      box.className = "coding-brief";
      box.innerHTML = `
        <p><strong>Risk:</strong> ${esc(brief.estimated_risk)} · <strong>Confidence:</strong> ${esc(brief.confidence_label)} (${esc(brief.confidence)})</p>
        <p><strong>Files:</strong> ${esc((brief.files_affected || []).join(", "))}</p>
        ${brief.breaking_change_warning ? `<p class="coding-warn coding-warn--error">Breaking-change warning</p>` : ""}
        <p><strong>Verify:</strong></p>
        <ul>${(brief.suggested_verification_steps || []).map((s) => `<li>${esc(s)}</li>`).join("")}</ul>
        ${(brief.recommended_tests || []).length ? `<p><strong>Tests:</strong> ${esc(brief.recommended_tests.join("; "))}</p>` : ""}`;
      if (!$(`codingBrief_${pid}`)) {
        window.showAriaToast?.(
          `Brief ${pid}: risk ${brief.estimated_risk}, confidence ${brief.confidence_label}`,
          "ok",
          5000
        );
        const host = $("codingHomeBody");
        if (host) {
          const wrap = document.createElement("div");
          wrap.appendChild(box);
          host.prepend(wrap);
        }
      }
    } catch (err) {
      window.showAriaToast?.(err.message || "Brief failed", "err", 4000);
    }
  }

  async function applyWithBrief(pid) {
    try {
      const brief = await api(`/api/coding/proposals/${encodeURIComponent(pid)}/brief`);
      const msg =
        `Apply proposal ${pid}?\n\nRisk: ${brief.estimated_risk}\nConfidence: ${brief.confidence_label}\nFiles: ${(brief.files_affected || []).join(", ")}\n` +
        (brief.breaking_change_warning ? "\n⚠ Breaking-change warning\n" : "");
      const ok = window.ariaConfirm
        ? await window.ariaConfirm(msg, { title: "Apply proposal", okLabel: "Apply" })
        : window.confirm(msg);
      if (!ok) return;
      const form = new FormData();
      form.append("proposal_id", pid);
      const res = await fetch("/api/apply", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) throw new Error(data.message || "Apply failed");
      window.showAriaToast?.("Applied — choose Verify when ready", "ok", 4000);
      if (data.verify_offer) window.AriaCodingVerify?.show?.(data.verify_offer);
      await refresh();
    } catch (err) {
      window.showAriaToast?.(err.message || "Apply failed", "err", 4000);
    }
  }

  function bindBody() {
    const body = $("codingHomeBody");
    if (!body) return;
    body.querySelectorAll("[data-coding-tab]").forEach((btn) => {
      /* tabs bound on nav */
    });
    body.querySelectorAll("[data-coding-link]").forEach((btn) => {
      btn.addEventListener("click", () => followLink(btn.getAttribute("data-coding-link")));
    });
    body.querySelectorAll("[data-coding-brief]").forEach((btn) => {
      btn.addEventListener("click", () => showBrief(btn.getAttribute("data-coding-brief")));
    });
    body.querySelectorAll("[data-coding-apply]").forEach((btn) => {
      btn.addEventListener("click", () => applyWithBrief(btn.getAttribute("data-coding-apply")));
    });
    body.querySelectorAll("[data-coding-export]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-coding-export");
        try {
          const data = await api(`/api/coding/proposals/${encodeURIComponent(id)}/export`);
          const blob = new Blob([data.patch || ""], { type: "text/x-diff" });
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = data.filename || `aria-${id}.patch`;
          a.click();
          URL.revokeObjectURL(a.href);
        } catch (err) {
          window.showAriaToast?.(err.message || "Export failed", "err", 4000);
        }
      });
    });
    body.querySelectorAll("[data-coding-restore]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-coding-restore");
        try {
          const data = await api(`/api/coding/proposals/${encodeURIComponent(id)}/restore`, { method: "POST" });
          window.showAriaToast?.(data.message || "Restored", "ok", 3500);
          await refresh();
        } catch (err) {
          window.showAriaToast?.(err.message || "Restore failed", "err", 4000);
        }
      });
    });
    body.querySelectorAll("[data-coding-bookmark]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-coding-bookmark");
        const on = btn.getAttribute("data-on") !== "0";
        const form = new FormData();
        form.append("bookmarked", on ? "true" : "false");
        await fetch(`/api/coding/proposals/${encodeURIComponent(id)}/bookmark`, { method: "POST", body: form });
        await loadHistory($("codingHistorySearch")?.value || "");
        bindBody();
      });
    });
    body.querySelectorAll("[data-coding-chat]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const msg = btn.getAttribute("data-coding-chat") || "";
        followLink("chat");
        setTimeout(() => {
          const input = $("messageInput") || document.querySelector("#chatInput, textarea[name=message]");
          if (input && msg) {
            input.value = msg;
            input.focus();
          }
        }, 100);
      });
    });
    body.querySelectorAll("[data-coding-continue]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-coding-continue");
        followLink("chat");
        setTimeout(() => {
          const input = $("messageInput") || document.querySelector("#chatInput, textarea[name=message]");
          if (input) {
            input.value = `continue coding task ${id}`;
            input.focus();
          }
        }, 100);
      });
    });
    body.querySelectorAll("[data-coding-undo]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          const res = await fetch("/api/undo-apply", { method: "POST" });
          const data = await res.json().catch(() => ({}));
          window.showAriaToast?.(data.message || (res.ok ? "Undone" : "Undo failed"), res.ok ? "ok" : "err", 3500);
          await refresh();
        } catch (err) {
          window.showAriaToast?.(err.message || "Undo failed", "err", 4000);
        }
      });
    });
    body.querySelectorAll("[data-coding-verify-last]").forEach((btn) => {
      btn.addEventListener("click", () => window.AriaCodingVerify?.promptLast?.());
    });
    $("codingHistoryRefresh")?.addEventListener("click", async () => {
      await loadHistory($("codingHistorySearch")?.value || "");
      bindBody();
    });
    $("codingHistorySearch")?.addEventListener("keydown", async (e) => {
      if (e.key === "Enter") {
        await loadHistory(e.target.value || "");
        bindBody();
      }
    });
    $("codingPrefSave")?.addEventListener("click", async () => {
      await api("/api/coding/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          enabled: !!$("codingPrefEnabled")?.checked,
          style: $("codingPrefStyle")?.value || "",
          formatter: $("codingPrefFormatter")?.value || "",
          test_runner: $("codingPrefRunner")?.value || "pytest",
          notes: $("codingPrefNotes")?.value || "",
        }),
      });
      window.showAriaToast?.("Preferences saved (suggestions only)", "ok", 3000);
      await refresh();
    });
    $("codingVisionGo")?.addEventListener("click", async () => {
      const form = new FormData();
      form.append("path", $("codingVisionPath")?.value || "");
      form.append("hint", $("codingVisionHint")?.value || "");
      form.append("propose", "true");
      const out = $("codingVisionOut");
      if (out) out.textContent = "Working…";
      try {
        const res = await fetch("/api/coding/vision-fix", { method: "POST", body: form });
        const data = await res.json();
        if (out) out.textContent = data.message || JSON.stringify(data, null, 2);
        if (data.proposal_id) window.showAriaToast?.(`Proposal ${data.proposal_id} ready`, "ok", 4000);
      } catch (err) {
        if (out) out.textContent = err.message || "Failed";
      }
    });
    $("codingSpecGo")?.addEventListener("click", async () => {
      const form = new FormData();
      form.append("document_path", $("codingSpecPath")?.value || "");
      form.append("query", $("codingSpecQuery")?.value || "");
      const out = $("codingSpecOut");
      if (out) out.textContent = "Working…";
      try {
        const res = await fetch("/api/coding/spec-to-code", { method: "POST", body: form });
        const data = await res.json();
        if (out) out.textContent = data.message || data.plan?.plan || JSON.stringify(data, null, 2);
        if (data.proposal_id) window.showAriaToast?.(`Proposal ${data.proposal_id} ready`, "ok", 4000);
      } catch (err) {
        if (out) out.textContent = err.message || "Failed";
      }
    });
    $("codingFocusLsp")?.addEventListener("click", () => {
      const sec = document.querySelector('#codingPanel .sidebar-section-head');
      sec?.click?.();
      $("lspPath")?.focus();
    });
  }

  function followLink(target) {
    if (target === "projects") window.switchToView?.("projects") || window.AriaActions?.projects?.open?.();
    else if (target === "jobs") window.jarvisJobs?.openJobCenter?.() || window.AriaActions?.mission?.jobs?.();
    else if (target === "models") window.openModelsHome?.() || window.switchToView?.("models");
    else if (target === "activity") window.AriaActivity?.open?.() || document.getElementById("activityCenterBtn")?.click();
    else if (target === "chat") window.switchToView?.("chat");
    else if (target === "planner") window.switchToView?.("planner");
    else if (target === "coding") window.switchToView?.("coding");
  }

  function initTabs() {
    $("codingHomeTabs")?.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-coding-tab]");
      if (!btn) return;
      _tab = btn.getAttribute("data-coding-tab") || "overview";
      renderTabs();
      const body = $("codingHomeBody");
      if (body) body.innerHTML = renderBody();
      if (_tab === "history") await loadHistory();
      bindBody();
    });
    $("codingHomeRefreshBtn")?.addEventListener("click", refresh);
    $("codingOpenProjectsBtn")?.addEventListener("click", () => followLink("projects"));
    $("codingOpenJobsBtn")?.addEventListener("click", () => followLink("jobs"));
    $("codingOpenModelsBtn")?.addEventListener("click", () => followLink("models"));
  }

  window.initCodingHome = function initCodingHome() {
    if (!$("codingHomeBody")) return;
    initTabs();
    refresh();
  };

  window.openCodingHome = function openCodingHome(tab) {
    window.switchToView?.("coding");
    if (tab) _tab = tab;
    window.initCodingHome?.();
  };

  // Verify helper used after apply
  window.AriaCodingVerify = {
    async show(offer) {
      const actions = (offer?.options || []).filter((o) => o.recommended !== false).map((o) => o.id);
      const labels = (offer?.options || []).map((o) => `• ${o.label}: ${o.description}`).join("\n");
      const msg = `Run verification?\n\n${labels}\n\nRecommended: ${(actions || []).join(", ") || "syntax, summary"}`;
      const ok = window.ariaConfirm
        ? await window.ariaConfirm(msg, { title: "Verify changes", okLabel: "Run verify" })
        : window.confirm(msg);
      if (!ok) return;
      const form = new FormData();
      form.append("actions", (actions.length ? actions : ["syntax", "summary"]).join(","));
      form.append("approved", "true");
      form.append("proposal_id", offer?.proposal_id || "");
      form.append("paths", (offer?.applied_paths || []).join(","));
      const res = await fetch("/api/coding/verify", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      window.showAriaToast?.(data.message || (data.ok ? "Verified" : "Verify issues"), data.ok ? "ok" : "warn", 5000);
    },
    async promptLast() {
      try {
        const offer = await api("/api/coding/verify/offer");
        await this.show(offer);
      } catch (err) {
        window.showAriaToast?.(err.message || "No verify offer", "err", 3500);
      }
    },
  };

  document.getElementById("codingHomeOpenBtn")?.addEventListener("click", () => window.openCodingHome());
})();
