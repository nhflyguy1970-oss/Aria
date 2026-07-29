/** Mission Control UX — operator console enhancements (loaded after mission_control.js). */
(function () {
  "use strict";

  const PREF_KEY = "missionControl";
  const PRIMARY_TABS = ["overview", "routing", "performance", "recovery", "connection"];
  const ADVANCED_TABS = [
    "hardware",
    "inference",
    "memory",
    "knowledge",
    "databases",
    "settings",
    "timeline",
    "release",
    "applications",
    "jobs",
    "activity",
    "intent_analytics",
  ];
  const EXPERIMENTAL_TABS = ["sessions", "diagnostics", "endurance"]; // Platform cognitive — advanced only

  const TAB_LABELS = {
    overview: "Overview",
    routing: "Routing",
    performance: "Performance",
    recovery: "Recovery",
    connection: "Connection",
    hardware: "Hardware",
    inference: "Inference",
    memory: "Memory",
    knowledge: "Knowledge",
    databases: "Databases",
    settings: "Settings",
    timeline: "Timeline",
    release: "Release",
    applications: "Applications",
    jobs: "Queue Snapshot",
    activity: "Operations Event Log",
    intent_analytics: "Intent Analytics",
    sessions: "Sessions (Platform)",
    diagnostics: "Diagnostics (Platform)",
    endurance: "Endurance (Platform)",
  };

  function prefs() {
    const all = window.AriaUiPrefs?.load?.() || {};
    return { ...(all[PREF_KEY] || {}) };
  }

  function savePrefs(partial) {
    const next = { ...prefs(), ...partial };
    window.AriaUiPrefs?.save?.({ [PREF_KEY]: next });
    return next;
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function sevClass(sev) {
    const s = String(sev || "info").toLowerCase();
    if (s === "critical" || s === "error") return "mc-sev--critical";
    if (s === "warning" || s === "warn") return "mc-sev--warn";
    if (s === "ok" || s === "success" || s === "healthy") return "mc-sev--ok";
    return "mc-sev--info";
  }

  function emptyState(title, detail, actionsHtml) {
    return `<div class="mc-empty" role="status">
      <h3>${esc(title)}</h3>
      <p class="muted">${esc(detail)}</p>
      ${actionsHtml || ""}
    </div>`;
  }

  function sparkline(points, opts = {}) {
    const pts = (points || []).map(Number).filter((n) => !Number.isNaN(n));
    if (!pts.length) return `<span class="mc-spark muted" aria-hidden="true">—</span>`;
    const w = opts.w || 96;
    const h = opts.h || 28;
    const min = Math.min(...pts);
    const max = Math.max(...pts);
    const span = max - min || 1;
    const step = w / Math.max(pts.length - 1, 1);
    const d = pts
      .map((v, i) => {
        const x = i * step;
        const y = h - ((v - min) / span) * (h - 4) - 2;
        return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
    const label = opts.label || "trend";
    return `<svg class="mc-spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${esc(label)}">
      <path d="${d}" fill="none" stroke="currentColor" stroke-width="1.5" /></svg>`;
  }

  function renderHealthBrief(brief) {
    const b = brief || {};
    const overall = b.overall || "unknown";
    const cta = b.primary_cta || {};
    const issues = (b.critical_issues || [])
      .map((i) => `<li>${esc(i)}</li>`)
      .join("");
    return `<section class="mc-health-brief ${sevClass(b.severity || overall)}" aria-label="Health brief">
      <div class="mc-health-brief__main">
        <p class="mc-health-brief__kicker">Health Brief</p>
        <h3 class="mc-health-brief__overall">${esc(String(overall).toUpperCase())}</h3>
        <p>${esc(b.headline || "")}</p>
        <dl class="mc-health-brief__meta">
          <div><dt>Severity</dt><dd>${esc(b.severity || "—")}</dd></div>
          <div><dt>Recommended</dt><dd>${esc(b.recommended_action || "—")}</dd></div>
          <div><dt>Next step</dt><dd>${esc(b.next_step || "—")}</dd></div>
          <div><dt>Impact</dt><dd>${esc(b.estimated_impact || "—")}</dd></div>
        </dl>
        ${issues ? `<ul class="mc-list mc-health-brief__issues">${issues}</ul>` : "<p class='muted'>No critical issues</p>"}
      </div>
      <div class="mc-health-brief__cta">
        <button type="button" class="apply-btn" data-mc-cta="${esc(cta.action || "mc:refresh")}" title="${esc(cta.why || "")}">${esc(cta.label || "Refresh")}</button>
        <button type="button" class="ghost-btn small" data-mc-action="voice_summary">Voice summary</button>
        <button type="button" class="ghost-btn small" data-mc-nav="activity-center">Open Activity Center</button>
        <button type="button" class="ghost-btn small" data-mc-nav="job-center">Open Job Center</button>
      </div>
    </section>`;
  }

  function renderAdvisorActions(cards) {
    if (!cards?.length) return "";
    const items = cards
      .map((c) => {
        const btns = (c.actions || [])
          .map(
            (a) =>
              `<button type="button" class="ghost-btn small" data-mc-approved="${esc(a.id)}" data-mc-confirm="${a.confirm ? "1" : "0"}">${esc(a.label)}</button>`
          )
          .join(" ");
        return `<div class="mc-advisor-item ${sevClass(c.severity)}">
          <p><strong>${esc(c.title)}</strong></p>
          ${c.reason ? `<p class="muted">${esc(c.reason)}</p>` : ""}
          ${c.impact ? `<p>Impact: ${esc(c.impact)}</p>` : ""}
          ${c.duration_estimate ? `<p class="muted">Est. ${esc(c.duration_estimate)}</p>` : ""}
          <div class="mc-advisor-actions">${btns}</div>
        </div>`;
      })
      .join("");
    return `<section class="mc-card"><h3>Approved actions</h3>
      <p class="muted tiny">Every remediating action requires confirmation. Mission Control never auto-repairs.</p>
      ${items}</section>`;
  }

  function renderPredictive(warnings) {
    if (!warnings?.length) return "";
    const items = warnings
      .map(
        (w) => `<div class="mc-predict ${sevClass(w.severity)}">
        <strong>${esc(w.title)}</strong>
        <p class="muted">${esc(w.detail || "")}</p>
        <p>Suggested: ${esc(w.suggested_fix || "Observe only")}</p>
      </div>`
      )
      .join("");
    return `<section class="mc-card"><h3>Predictive health <span class="mc-badge mc-badge--info">Experimental</span></h3>
      <p class="muted tiny">Warnings only — never auto-remediate.</p>${items}</section>`;
  }

  function renderPlatformLink(link) {
    const L = link || {};
    return `<section class="mc-card mc-platform-link">
      <h3>Platform Mission Control</h3>
      <p class="muted">${esc(L.why || "Advanced laboratory tabs live on Platform Mission Control.")}</p>
      <p>Status: ${L.available ? mcBadge?.(true, "reachable", "down") || "<span>reachable</span>" : "<span class='mc-badge mc-badge--down'>not reachable</span>"}</p>
      <a class="ghost-btn small" href="${esc(L.url || "#")}" target="_blank" rel="noopener">${esc(L.label || "Open Platform Mission Control")}</a>
    </section>`;
  }

  function enhanceOverview(d) {
    const brief = d.health_brief || {};
    const cards = d.advisor_actions || [];
    const pred = d.predictive_warnings || [];
    const series = d.perf_series || {};
    const ov = d.overview || {};
    const mini = `
      <div class="mc-mini-charts" role="group" aria-label="Performance snapshots">
        ${["cpu", "ram", "vram", "latency", "queue_depth"]
          .map((k) => {
            const s = series[k] || {};
            return `<div class="mc-mini-chart"><span class="muted">${esc(k.replace(/_/g, " "))}</span>
              ${sparkline(s.points, { label: k })}
              <strong>${esc(s.latest ?? "—")}</strong></div>`;
          })
          .join("")}
      </div>`;
    return `
      ${renderHealthBrief(brief)}
      ${mini}
      ${renderAdvisorActions(cards)}
      ${renderPredictive(pred)}
      ${typeof renderOperationalAdvisor === "function" ? "" : ""}
      <div class="mc-hero" aria-label="Platform snapshot">
        <div class="mc-hero-stat"><span class="muted">Platform</span><strong>${esc(ov.platform_status)}</strong></div>
        <div class="mc-hero-stat"><span class="muted">Phase</span><strong>${esc((ov.phase || {}).phase || "?")}</strong></div>
        <div class="mc-hero-stat"><span class="muted">Acceptance</span><strong>${ov.acceptance_overall ?? "—"}%</strong></div>
        <div class="mc-hero-stat"><span class="muted">Production</span><strong>${ov.production_readiness ?? "—"}%</strong></div>
        <div class="mc-hero-stat"><span class="muted">Model</span><strong><code>${esc(ov.current_model || "—")}</code></strong></div>
        <div class="mc-hero-stat"><span class="muted">Active work</span><strong>${ov.active_jobs ?? 0}</strong></div>
      </div>
      ${typeof mcGrid === "function"
        ? mcGrid([
            typeof mcCard === "function"
              ? mcCard(
                  "User & project",
                  `<p><strong>${esc(ov.user)}</strong></p><p>Project: ${esc(ov.project || "—")}</p><p>Branch: <code>${esc(ov.aria_branch || "?")}</code></p>`
                )
              : "",
            typeof mcCard === "function"
              ? mcCard(
                  "Providers",
                  `<p>Inference: <strong>${esc(ov.inference_provider)}</strong></p><p>Memory: <strong>${esc(ov.memory_provider)}</strong></p><p>Knowledge: <strong>${esc(ov.knowledge_provider)}</strong></p>`
                )
              : "",
            typeof mcCard === "function"
              ? mcCard(
                  "Hardware",
                  `<p>GPU: ${esc(ov.gpu || "—")}</p><p>RAM free: ${ov.ram_available_gb ?? "—"} GB</p><p>VRAM free: ${ov.free_vram_mb ?? "—"} MB</p><p>Load: ${ov.cpu_load ?? "—"}</p>`
                )
              : "",
            typeof mcCard === "function"
              ? mcCard(
                  "Attention",
                  (ov.needs_attention || []).map((n) => `<p>• ${esc(n)}</p>`).join("") ||
                    "<p class='muted'>All clear</p>"
                )
              : "",
            typeof renderRoutingOverviewCard === "function" ? renderRoutingOverviewCard(d.routing_stats) : "",
          ].filter(Boolean))
        : ""}
      ${typeof renderNotifications === "function" ? renderNotifications(d.notifications) : ""}
      ${renderPlatformLink(d.platform_link)}
    `;
  }

  function enhanceJobs(d) {
    const j = d.jobs || {};
    const recent = (j.recent || [])
      .map(
        (job) =>
          `<li>${typeof mcBadge === "function" ? mcBadge(!job.done, "active", "done") : ""} [${esc(job.queue)}] ${esc(job.label)} — ${esc(job.message)}</li>`
      )
      .join("");
    return `
      <div class="mc-product-bridge">
        <p><strong>Queue Snapshot</strong> is a read-only health view of live queues — not Job Center.</p>
        <button type="button" class="apply-btn small" data-mc-nav="job-center">Open Job Center</button>
      </div>
      ${
        typeof mcGrid === "function"
          ? mcGrid([
              mcCard(
                "Queues",
                `<p>Media busy: ${mcBadge(j.media?.busy, "yes", "no")}</p><p>Coding busy: ${mcBadge(j.coding?.busy, "yes", "no")}</p><p>Any busy: ${mcBadge(j.any_busy, "yes", "no")}</p>`
              ),
              mcCard("Recent jobs", recent ? `<ul class="mc-list">${recent}</ul>` : emptyState("No recent jobs", "Queues are idle. Open Job Center to start or inspect work.", `<button type="button" class="ghost-btn tiny" data-mc-nav="job-center">Open Job Center</button>`)),
            ])
          : ""
      }`;
  }

  async function enhanceActivity(d, filters = {}) {
    const q = filters.q || document.getElementById("mcActivityQuery")?.value?.trim() || "";
    const comp = filters.component || document.getElementById("mcActivityComponent")?.value?.trim() || "";
    const params = new URLSearchParams({ limit: "100" });
    if (q) params.set("q", q);
    if (comp) params.set("component", comp);
    const act = await (typeof mcFetch === "function"
      ? mcFetch(`/api/workstation/activity?${params}`)
      : fetch(`/api/workstation/activity?${params}`).then((r) => r.json()));
    const events = act.events || d.activity?.events || [];
    const bridge = `
      <div class="mc-product-bridge">
        <p><strong>Operations Event Log</strong> is a Mission Control operations stream — not Activity Center (durable inbox).</p>
        <button type="button" class="apply-btn small" data-mc-nav="activity-center">Open Activity Center</button>
      </div>`;
    if (!events.length) {
      return (
        bridge +
        emptyState(
          "No operations events yet",
          "Infrastructure events will appear here. Durable alerts live in Activity Center.",
          `<button type="button" class="ghost-btn tiny" data-mc-nav="activity-center">Open Activity Center</button>
           <button type="button" class="ghost-btn tiny" id="mcEmptyActivityChatBtn">Chat</button>`
        )
      );
    }
    const rows = events
      .map(
        (ev) => `<tr class="mc-activity-${esc(ev.status || "ok")}">
          <td>${esc(ev.iso)}</td><td><strong>${esc(ev.type)}</strong></td>
          <td>${esc(ev.component)}</td><td>${esc(ev.status)}</td>
          <td>${ev.duration_ms != null ? ev.duration_ms + "ms" : "—"}</td>
          <td>${esc(ev.detail)}</td>
        </tr>`
      )
      .join("");
    return `${bridge}
      <div class="mc-activity-toolbar">
        <input type="search" id="mcActivityQuery" class="audio-path-input" placeholder="Search…" value="${esc(q)}" aria-label="Filter operations log" />
        <input type="text" id="mcActivityComponent" class="audio-path-input" placeholder="Component" value="${esc(comp)}" aria-label="Component filter" />
        <button type="button" class="ghost-btn small" id="mcActivityFilterBtn">Filter</button>
        <a class="ghost-btn small" href="/api/mission-control/activity/export" download="activity.csv">Export CSV</a>
      </div>
      <table class="mc-table mc-activity-table"><thead><tr><th>Time</th><th>Event</th><th>Component</th><th>Status</th><th>Duration</th><th>Details</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  function enhanceInference(d) {
    const inf = d.inference || {};
    const loaded = (inf.loaded_models || [])
      .map((m) => `<li><code>${esc(m.name || m.model || JSON.stringify(m))}</code></li>`)
      .join("");
    const active = Object.entries(inf.active_models || {})
      .map(([k, v]) => `<li>${esc(k)}: <code>${esc(v)}</code></li>`)
      .join("");
    const model = inf.current_model || "";
    const actions = `
      <div class="mc-inference-actions" role="group" aria-label="Safe inference actions">
        <p class="muted tiny">Approved actions require confirmation and are audited. Switch updates the Models registry (conversation default). Warm/unload remain Mission Control health ops.</p>
        <button type="button" class="ghost-btn small" data-mc-inf="warm_model" data-model="${esc(model)}">Warm model</button>
        <button type="button" class="ghost-btn small" data-mc-inf="switch_model">Switch model (Models registry)</button>
        <button type="button" class="ghost-btn small" data-mc-inf="reload_provider">Reload provider</button>
        <button type="button" class="ghost-btn small" data-mc-inf="unload_model" data-model="${esc(model)}">Unload model</button>
        <button type="button" class="ghost-btn small" data-mc-inf="reconnect">Reconnect</button>
        <button type="button" class="ghost-btn small" data-mc-nav="memory">Open ACM / Memory</button>
        <button type="button" class="apply-btn small" data-models-open-home>Open Models Home</button>
      </div>`;
    return (
      actions +
      (typeof mcGrid === "function"
        ? mcGrid([
            mcCard(
              "Current",
              `<p>Provider: <strong>${esc(inf.provider)}</strong></p><p>Model: <code>${esc(model || "—")}</code></p><p>Ollama ${mcBadge(inf.ollama_running, "up", "down")}</p>`
            ),
            mcCard("Active models", active ? `<ul class="mc-list">${active}</ul>` : emptyState("No active models", "Warm or switch a model with an approved action.", "")),
            mcCard("Loaded in VRAM", loaded ? `<ul class="mc-list">${loaded}</ul>` : "<p class='muted'>—</p>"),
            mcCard("Gateway", `<pre class="mc-pre">${esc(JSON.stringify(inf.gateway || {}, null, 2))}</pre>`),
          ])
        : "")
    );
  }

  function enhancePerformance(d) {
    const perf = d?.performance || d || {};
    const series = (window._mcData && window._mcData.perf_series) || d.perf_series || {};
    const latest = perf.latest;
    const trends = perf.trends || {};
    const labels = {
      mission_control_ms: "Mission Control",
      aria_ms: "Aria",
      routing_write_ms: "Routing write",
      timeline_write_ms: "Timeline write",
    };
    const cards = Object.entries(labels).map(([key, label]) => {
      const block = latest?.metrics?.[key];
      const p50 = block?.p50_ms ?? trends[key]?.latest_p50_ms ?? "—";
      const pts = (series[key.replace(/_ms$/, "")] || series.latency || {}).points;
      return mcCard(label, `${sparkline(pts, { label })}<p><strong>${p50}</strong> ms p50</p>`);
    });
    const live = ["cpu", "ram", "vram", "latency", "queue_depth"]
      .map((k) => {
        const s = series[k] || {};
        return mcCard(k.replace(/_/g, " "), `${sparkline(s.points, { label: k })}<p><strong>${esc(s.latest ?? "—")}</strong></p>`);
      });
    return `<div class="mc-routing-toolbar">
      <button type="button" class="ghost-btn small" id="mcPerfRunBtn">Run benchmark</button>
      <a class="ghost-btn small" href="/api/mission-control/bug-report/export?format=json" download="bug-report.json">Bug report</a>
    </div>${mcGrid(live.concat(cards))}<p class="muted">Runs: ${perf.run_count ?? 0}</p>`;
  }

  function enhanceRecovery(d) {
    const r = d.recovery || {};
    const actions = (r.recommended_actions || []).map((a) => `<li>${esc(a)}</li>`).join("");
    const issues = (r.known_issues || []).map((i) => `<li>${esc(i)}</li>`).join("");
    return `
      <div class="mc-recovery-actions">
        <button type="button" class="apply-btn small" id="mcRepairBtn">Repair (confirm)</button>
        <button type="button" class="ghost-btn small" id="mcVerifyBtn">Verify after repair</button>
        <button type="button" class="ghost-btn small" id="mcAcceptanceBtn">Run acceptance</button>
        <button type="button" class="ghost-btn small" data-mc-nav="activity-center">Open Activity Center</button>
      </div>
      <p class="muted tiny">Repairs require confirmation. Auto-verification publishes to Activity — it never remediates further.</p>
      ${mcGrid([
        mcCard("Health", `<p>${mcBadge(r.health?.ok, "OK", "Issues")}</p><pre class="mc-pre">${esc(JSON.stringify(r.health || {}, null, 2).slice(0, 800))}</pre>`),
        mcCard("Backup", `<p>Latest: <code>${esc(r.latest_backup || "none")}</code></p>`),
        mcCard("Recommended", actions ? `<ul class="mc-list">${actions}</ul>` : emptyState("No recommendations", "System looks stable.", "")),
        mcCard("Known issues", issues ? `<ul class="mc-list">${issues}</ul>` : "<p class='muted'>None</p>"),
      ])}`;
  }

  function enhanceApplications(d) {
    const rows = (d.applications || [])
      .map(
        (a) => `<tr>
        <td><strong>${esc(a.label)}</strong><br><span class="muted">${esc(a.id)}</span></td>
        <td>${mcBadge(a.running, "Running", "Stopped")} ${mcBadge(a.healthy, "Healthy", "Down")}</td>
        <td>${esc(a.version || "—")}</td>
        <td>${esc(a.project || "—")}</td>
        <td><code>${esc(a.memory_namespace || "—")}</code></td>
        <td class="mc-actions">
          ${a.id === "aria" ? `<button type="button" class="ghost-btn small" data-mc-launch="aria">Launch</button>` : ""}
          ${a.id === "aria-uncensored" ? `<button type="button" class="ghost-btn small" data-mc-launch="uncensored">Launch</button>` : ""}
          <button type="button" class="ghost-btn small" data-mc-app="restart" data-app="${esc(a.id)}">Restart</button>
          <button type="button" class="ghost-btn small" data-mc-app="stop" data-app="${esc(a.id)}">Stop</button>
          <button type="button" class="ghost-btn small" data-mc-app="logs" data-app="${esc(a.id)}">Logs</button>
        </td>
      </tr>`
      )
      .join("");
    return `<table class="mc-table"><thead><tr><th>Application</th><th>Status</th><th>Version</th><th>Project</th><th>Memory NS</th><th>Lifecycle</th></tr></thead><tbody>${
      rows || `<tr><td colspan='6'>${emptyState("No applications", "No managed applications reported.", "")}</td></tr>`
    }</tbody></table>`;
  }

  function enhanceMemory(d) {
    const base = typeof renderMemory === "function" && renderMemory !== enhanceMemory ? null : null;
    const mem = d.memory || {};
    const ns = Object.entries(mem.namespaces || {})
      .map(([n, c]) => `<li>${esc(n)} (${c})</li>`)
      .join("");
    const recent = (mem.recent || [])
      .map((e) => `<li><code>${esc(e.namespace)}</code> ${esc(e.content)}</li>`)
      .join("");
    return `
      <div class="mc-product-bridge">
        <button type="button" class="ghost-btn small" data-mc-nav="memory">Open ACM / Memory</button>
      </div>
      ${mcGrid([
        mcCard(
          "Store",
          `<p>Provider: <strong>${esc(mem.provider)}</strong></p><p>Entries: ${mem.entry_count ?? "—"}</p><p>Semantic vectors: ${mem.semantic_vectors ?? "—"}</p><p>Cutover: ${esc(mem.cutover_mode || "—")}</p>`
        ),
        mcCard("Namespaces", ns ? `<ul class="mc-list">${ns}</ul>` : emptyState("No namespaces", "Memory store is empty or unavailable.", `<button type="button" class="ghost-btn tiny" data-mc-nav="memory">Open Memory</button>`)),
        mcCard("Recent", recent ? `<ul class="mc-list">${recent}</ul>` : "<p class='muted'>—</p>"),
      ])}`;
  }

  function enhanceConnection(conn) {
    const base =
      typeof window.__mcRenderConnectionOrig === "function"
        ? window.__mcRenderConnectionOrig(conn)
        : "";
    return (
      base +
      `<div class="mc-product-bridge">
        <button type="button" class="ghost-btn small" data-mc-inf="reconnect">Reconnect (confirm)</button>
        <button type="button" class="ghost-btn small" data-mc-cta="mc:recovery">Open Recovery</button>
      </div>`
    );
  }

  async function confirmAction(title, body) {
    if (window.ariaConfirm) return window.ariaConfirm(body, { title, okLabel: "Confirm" });
    return window.confirm(`${title}\n\n${body}`);
  }

  async function runApproved(id, el) {
    const needsConfirm = el?.dataset?.mcConfirm === "1";
    if (needsConfirm) {
      const ok = await confirmAction("Approved action", `Confirm: ${id.replace(/_/g, " ")}? Mission Control will not auto-remediate further.`);
      if (!ok) return;
    }
    switch (id) {
      case "warm_model":
        return runInference("warm_model", { model: window._mcData?.inference?.current_model || "" });
      case "recover_runtime":
        return document.getElementById("mcRepairBtn")?.click() || runRepair();
      case "reconnect_platform":
        return runInference("reconnect");
      case "open_inference":
        return window.switchMcTab?.("inference");
      case "open_recovery":
        return window.switchMcTab?.("recovery");
      case "open_job_center":
        return window.AriaActions?.mission?.jobs?.() || document.getElementById("jobCenterBtn")?.click();
      case "open_activity":
        return window.AriaActivity?.open?.();
      case "create_activity_alert": {
        const msg = window._mcData?.health_brief?.headline || "Mission Control alert";
        const payload = {
          category: "mission",
          type: "health",
          severity: "warning",
          title: "Mission Control alert",
          summary: msg,
          message: msg,
          deepLink: "providers",
          source: "mission_control",
          product: "mission_control",
        };
        window.AriaActivityProducers?.mission?.health?.(msg) ||
          window.AriaNotifications?.publish?.(payload) ||
          window.AriaActivity?.add?.(payload);
        window.showAriaToast?.("Notification created", "ok");
        return;
      }
      default:
        window.showAriaToast?.(`Unknown action: ${id}`, "warn");
    }
  }

  async function runInference(action, extra = {}) {
    const ok = await confirmAction("Safe inference action", `Confirm ${action.replace(/_/g, " ")}? This is audited and never runs automatically.`);
    if (!ok) return;
    let model = extra.model || "";
    if (action === "switch_model") {
      model = window.prompt?.("Model name to switch to:", window._mcData?.inference?.current_model || "") || "";
      if (!model) return;
    }
    try {
      const out = await mcFetch("/api/mission-control/inference/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, confirmed: true, model, provider: extra.provider || "" }),
      });
      window.showAriaToast?.(out.message || (out.ok ? "Done" : out.error || "Failed"), out.ok ? "ok" : "err");
      if (out.requires_verification) {
        window.AriaActivityProducers?.mission?.recovery?.(out.message || action);
      }
      window.loadMissionControl?.();
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  }

  async function runRepair() {
    const ok = await confirmAction("Repair", "Run safe recovery? This requires confirmation and will auto-verify afterward.");
    if (!ok) return;
    try {
      const data = await mcFetch("/api/workstation/recover", { method: "POST" });
      const issues = data.report?.warnings ?? data.report?.issues?.length ?? 0;
      const summary = data.ok
        ? issues
          ? `Repair done · ${issues} warning(s)`
          : "Repair done · healthy"
        : "Repair finished with issues";
      window.showAriaToast?.(summary, data.ok ? "ok" : "warn");
      window.AriaActivityProducers?.mission?.recovery?.(summary);
      await runVerify(false);
      window.loadMissionControl?.();
    } catch (err) {
      window.showAriaToast?.(err.message, "err");
    }
  }

  async function runVerify(ask = true) {
    if (ask) {
      const ok = await confirmAction("Verify", "Run post-repair verification across Recovery, Provider, Routing, Hardware, Connection?");
      if (!ok) return;
    }
    try {
      const out = await mcFetch("/api/mission-control/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ previous: window._mcData?.health_brief || {} }),
      });
      const act = out.activity || {};
      if (act.title) {
        const payload = {
          category: act.category || "mission",
          type: act.type || "verification",
          severity: act.severity || "info",
          title: act.title,
          summary: act.message || "",
          message: act.message,
          deepLink: act.fix || "mc:recovery",
          source: "mission_control",
        };
        window.AriaNotifications?.publish?.(payload) || window.AriaActivity?.add?.(payload);
      }
      window.showAriaToast?.(act.message || (out.ok ? "Verified" : "Verification issues"), out.ok ? "ok" : "warn");
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  }

  function handleCta(action) {
    const a = String(action || "");
    if (a === "mc:refresh") return window.loadMissionControl?.();
    if (a.startsWith("mc:")) return window.switchMcTab?.(a.slice(3));
    if (a === "job-center") return window.AriaActions?.mission?.jobs?.() || document.getElementById("jobCenterBtn")?.click();
    if (a === "activity-center") return window.AriaActivity?.open?.();
  }

  function voiceSummary() {
    const v = window._mcData?.voice || {};
    const b = window._mcData?.health_brief || {};
    const issues = (v.errors || v.recovery?.issues || []).slice(0, 3).map((i) => i.message || i.code).join("; ");
    const text = v.product
      ? `Voice is ${v.state || "unknown"}. Whisper ${v.whisper ? "ok" : "missing"}; Piper ${v.piper ? "ok" : "missing"}. Cloud Live ${v.cloud_live?.available ? "ready" : "off"}. ${issues || "No voice warnings."}`
      : `Mission Control health is ${b.overall || "unknown"}. Severity ${b.severity || "unknown"}. ${b.recommended_action || ""} Next: ${b.next_step || ""}`;
    window.showAriaToast?.(text, "info", 8000);
    // Prefer shared Voice engine when available
    if (typeof window.jarvisMaybeSpeakReply === "function" && window.jarvisSpeakRepliesEnabled?.()) {
      fetch("/api/voice/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, force: true, source: "mission_control" }),
      }).catch(() => {});
      return;
    }
    if (window.speechSynthesis && window.SpeechSynthesisUtterance) {
      const u = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(u);
    } else {
      window.jarvisSendToChat?.(`Voice health summary: ${text}`);
    }
  }

  function buildTabNav() {
    const nav = document.getElementById("mcTabNav");
    if (!nav) return;
    const p = prefs();
    const tab = p.tab || window._mcTab || "overview";
    const advancedOpen = p.advancedOpen !== false;
    const experimentalOpen = !!p.experimentalOpen;

    const mkBtn = (t) => {
      const selected = t === tab;
      return `<button type="button" class="mc-tab${selected ? " active" : ""}" role="tab"
        id="mc-tab-${t}" data-mc-tab="${t}"
        aria-selected="${selected ? "true" : "false"}"
        aria-controls="mcTabBody"
        tabindex="${selected ? "0" : "-1"}">${esc(TAB_LABELS[t] || t)}</button>`;
    };

    nav.setAttribute("role", "tablist");
    nav.setAttribute("aria-label", "Mission Control sections");
    nav.innerHTML = `
      <div class="mc-tab-group" data-group="primary">
        <span class="mc-tab-group__label muted">Primary</span>
        <div class="mc-tab-group__tabs" role="presentation">${PRIMARY_TABS.map(mkBtn).join("")}</div>
      </div>
      <div class="mc-tab-group" data-group="advanced">
        <button type="button" class="mc-tab-group__toggle ghost-btn tiny" data-mc-toggle-group="advanced" aria-expanded="${advancedOpen}">
          Advanced ${advancedOpen ? "▾" : "▸"}
        </button>
        <div class="mc-tab-group__tabs${advancedOpen ? "" : " hidden"}" role="presentation">${ADVANCED_TABS.map(mkBtn).join("")}</div>
      </div>
      <div class="mc-tab-group" data-group="experimental">
        <button type="button" class="mc-tab-group__toggle ghost-btn tiny" data-mc-toggle-group="experimental" aria-expanded="${experimentalOpen}" title="Platform cognitive tabs — read-only experimental">
          Experimental ${experimentalOpen ? "▾" : "▸"}
        </button>
        <div class="mc-tab-group__tabs${experimentalOpen ? "" : " hidden"}" role="presentation">
          <p class="muted tiny mc-experimental-note">Platform features · read-only · experimental. Prefer Platform Mission Control for full labs.</p>
          ${EXPERIMENTAL_TABS.map(mkBtn).join("")}
        </div>
      </div>`;

    nav.querySelectorAll(".mc-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        window.switchMcTab?.(btn.dataset.mcTab);
      });
      btn.addEventListener("keydown", (e) => {
        const tabs = [...nav.querySelectorAll(".mc-tab")].filter((t) => !t.closest(".hidden"));
        const i = tabs.indexOf(btn);
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          e.preventDefault();
          const next = tabs[(i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length];
          next?.focus();
          window.switchMcTab?.(next.dataset.mcTab);
        } else if (e.key === "Home") {
          e.preventDefault();
          tabs[0]?.focus();
          window.switchMcTab?.(tabs[0].dataset.mcTab);
        } else if (e.key === "End") {
          e.preventDefault();
          tabs[tabs.length - 1]?.focus();
          window.switchMcTab?.(tabs[tabs.length - 1].dataset.mcTab);
        }
      });
    });

    nav.querySelectorAll("[data-mc-toggle-group]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const g = btn.dataset.mcToggleGroup;
        const wrap = btn.parentElement?.querySelector(".mc-tab-group__tabs");
        const open = wrap?.classList.toggle("hidden") === false;
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        btn.textContent = `${g === "advanced" ? "Advanced" : "Experimental"} ${open ? "▾" : "▸"}`;
        if (g === "advanced") savePrefs({ advancedOpen: open });
        if (g === "experimental") savePrefs({ experimentalOpen: open });
      });
    });

    const body = document.getElementById("mcTabBody");
    if (body) {
      body.setAttribute("role", "tabpanel");
      body.setAttribute("aria-labelledby", `mc-tab-${tab}`);
      body.setAttribute("tabindex", "0");
    }
  }

  function announce(msg) {
    let live = document.getElementById("mcLiveRegion");
    if (!live) {
      live = document.createElement("div");
      live.id = "mcLiveRegion";
      live.className = "sr-only";
      live.setAttribute("aria-live", "polite");
      live.setAttribute("aria-atomic", "true");
      document.getElementById("workstationView")?.appendChild(live);
    }
    live.textContent = msg;
  }

  function promoteActivityCorrelation(events) {
    if (!events?.length) return;
    events.forEach((ev) => {
      const payload = {
        id: ev.id,
        category: "mission",
        type: ev.type || "critical_health",
        severity: ev.severity || "warning",
        title: ev.title || "Mission Control health",
        summary: ev.message || ev.title || "",
        message: ev.message,
        deepLink: ev.fix || "mc:recovery",
        source: "mission_control",
        product: "mission_control",
        metadata: {
          subsystem: ev.subsystem,
          suggested_fix: ev.suggested_fix,
          resolution: ev.resolution,
        },
      };
      window.AriaNotifications?.publish?.(payload) || window.AriaActivity?.add?.(payload);
    });
  }

  let _sse = null;
  function connectSse() {
    if (_sse || typeof EventSource === "undefined") return;
    try {
      _sse = new EventSource("/api/mission-control/stream");
      _sse.addEventListener("health", (e) => {
        try {
          const data = JSON.parse(e.data);
          const pill = document.getElementById("mcLoadStatus");
          if (pill && data.overall) {
            pill.textContent = `Live · ${data.overall}`;
            announce(`Mission Control health ${data.overall}`);
          }
        } catch (_) {
          /* ignore */
        }
      });
      _sse.onerror = () => {
        _sse?.close();
        _sse = null;
      };
    } catch (_) {
      _sse = null;
    }
  }

  // --- Patch core globals (wrap; preserve original bindings) ---
  if (typeof renderConnection === "function" && !window.__mcRenderConnectionOrig) {
    window.__mcRenderConnectionOrig = renderConnection;
  }

  window.renderOverview = function (d) {
    return enhanceOverview(d);
  };
  window.renderJobs = function (d) {
    return enhanceJobs(d);
  };
  window.renderActivity = function (d, filters) {
    return enhanceActivity(d, filters);
  };
  window.renderInference = function (d) {
    return enhanceInference(d);
  };
  window.renderPerformance = function (d) {
    return enhancePerformance(d);
  };
  window.renderRecovery = function (d) {
    return enhanceRecovery(d);
  };
  window.renderApplications = function (d) {
    return enhanceApplications(d);
  };
  window.renderMemory = function (d) {
    return enhanceMemory(d);
  };
  window.renderConnection = function (conn) {
    return enhanceConnection(conn);
  };

  const _origSwitch = window.switchMcTab;
  window.switchMcTab = function (tab) {
    const t = tab || "overview";
    savePrefs({
      tab: t,
      routingFilter: window._mcRoutingFilter,
      routingSearch: window._mcRoutingSearch,
    });
    if (EXPERIMENTAL_TABS.includes(t)) {
      window._mcTab = t;
      document.querySelectorAll(".mc-tab").forEach((el) => {
        const on = el.dataset.mcTab === t;
        el.classList.toggle("active", on);
        el.setAttribute("aria-selected", on ? "true" : "false");
        el.tabIndex = on ? 0 : -1;
      });
      const body = document.getElementById("mcTabBody");
      const link = window._mcData?.platform_link || {};
      if (body) {
        body.setAttribute("aria-labelledby", `mc-tab-${t}`);
        body.innerHTML = emptyState(
          TAB_LABELS[t] || t,
          "This is an experimental Platform cognitive surface. Aria Mission Control exposes it read-only; full labs live in Platform Mission Control.",
          `<a class="ghost-btn small" href="${esc(link.url || "#")}" target="_blank" rel="noopener">Open Platform Mission Control</a>
           <button type="button" class="ghost-btn small" data-mc-cta="mc:overview">Back to Overview</button>`
        );
      }
      announce(`${TAB_LABELS[t]} — experimental Platform tab`);
      return;
    }
    if (typeof _origSwitch === "function") _origSwitch(t);
    document.querySelectorAll(".mc-tab").forEach((el) => {
      const on = el.dataset.mcTab === t;
      el.setAttribute("aria-selected", on ? "true" : "false");
      el.tabIndex = on ? 0 : -1;
    });
    document.getElementById("mcTabBody")?.setAttribute("aria-labelledby", `mc-tab-${t}`);
    announce(`Mission Control · ${TAB_LABELS[t] || t}`);
  };

  const _origLoad = window.loadMissionControl;
  window.loadMissionControl = async function () {
    if (typeof _origLoad === "function") await _origLoad();
    promoteActivityCorrelation(window._mcData?.activity_correlation);
    connectSse();
  };

  const _origInit = window.initMissionControl || window.initWorkstation;
  window.initMissionControl = function () {
    const p = prefs();
    if (p.tab) window._mcTab = p.tab;
    // Seed original init's tab via a one-shot switch after load
    buildTabNav();
    if (typeof _origInit === "function") {
      // Prevent double-building default tabs: clear wired flag so we own nav
      const nav = document.getElementById("mcTabNav");
      if (nav) nav.dataset.wired = "1";
      _origInit();
    }
    buildTabNav();
    if (p.tab && p.tab !== "overview") {
      setTimeout(() => window.switchMcTab?.(p.tab), 100);
    }
    const openJc = document.getElementById("mcOpenJobCenterBtn");
    if (openJc && !openJc.dataset.uxWired) {
      openJc.dataset.uxWired = "1";
      openJc.addEventListener("click", () => handleCta("job-center"));
    }
    const openAc = document.getElementById("mcOpenActivityCenterBtn");
    if (openAc && !openAc.dataset.uxWired) {
      openAc.dataset.uxWired = "1";
      openAc.addEventListener("click", () => handleCta("activity-center"));
    }
  };
  window.initWorkstation = window.initMissionControl;

  // Delegate enhanced clicks (once)
  document.addEventListener(
    "click",
    async (e) => {
      const t = e.target;
      if (!(t instanceof Element)) return;
      if (!document.getElementById("workstationView") || document.getElementById("workstationView").classList.contains("hidden")) {
        // still allow toolbar outside? only MC
      }
      if (t.closest?.("[data-models-open-home]")) {
        e.preventDefault();
        window.openModelsHome?.() || window.switchToView?.("models");
        return;
      }
      const cta = t.closest?.("[data-mc-cta]");
      if (cta) {
        e.preventDefault();
        handleCta(cta.dataset.mcCta);
        return;
      }
      const nav = t.closest?.("[data-mc-nav]");
      if (nav) {
        e.preventDefault();
        handleCta(nav.dataset.mcNav);
        return;
      }
      const approved = t.closest?.("[data-mc-approved]");
      if (approved) {
        e.preventDefault();
        await runApproved(approved.dataset.mcApproved, approved);
        return;
      }
      const inf = t.closest?.("[data-mc-inf]");
      if (inf) {
        e.preventDefault();
        await runInference(inf.dataset.mcInf, { model: inf.dataset.model || "" });
        return;
      }
      const app = t.closest?.("[data-mc-app]");
      if (app) {
        e.preventDefault();
        const kind = app.dataset.mcApp;
        const id = app.dataset.app;
        if (kind === "logs") {
          window.switchToView?.("audit");
          return;
        }
        const ok = await confirmAction(`Application ${kind}`, `Confirm ${kind} for ${id}?`);
        if (!ok) return;
        try {
          const path = kind === "stop" ? "/api/workstation/down" : "/api/workstation/restart";
          await mcFetch(path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ component: id, target: id }),
          });
          window.showAriaToast?.(`${kind} · ${id}`, "ok");
          window.AriaActivityProducers?.mission?.recovery?.(`${kind} ${id}`);
          window.loadMissionControl?.();
        } catch (err) {
          window.showAriaToast?.(err.message, "err");
        }
        return;
      }
      if (t.closest?.("#mcRepairBtn")) {
        e.preventDefault();
        e.stopPropagation();
        await runRepair();
        return;
      }
      if (t.closest?.("#mcVerifyBtn")) {
        e.preventDefault();
        await runVerify(true);
        return;
      }
      if (t.closest?.("[data-mc-action='voice_summary']")) {
        e.preventDefault();
        voiceSummary();
      }
    },
    true
  );

  window.MissionControlUX = {
    TAB_LABELS,
    PRIMARY_TABS,
    ADVANCED_TABS,
    prefs,
    savePrefs,
    buildTabNav,
    voiceSummary,
  };
})();
