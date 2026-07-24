/** AI Platform Mission Control — operational console (not chat). */

const MC_TABS = [
  "overview",
  "routing",
  "timeline",
  "intent_analytics",
  "release",
  "connection",
  "applications",
  "inference",
  "memory",
  "knowledge",
  "databases",
  "hardware",
  "jobs",
  "activity",
  "performance",
  "settings",
  "recovery",
];

let _mcData = null;
let _mcTab = "overview";
let _mcPoll = null;
let _mcRoutingLive = false;
let _mcRoutingPoll = null;
let _mcRoutingFilter = "";
let _mcRoutingSearch = "";
/** Monotonic token so slow async tab loads cannot overwrite a newer tab. */
let _mcRenderGen = 0;

function mc$(id) {
  // Accept both "id" and "#id" — many call sites use CSS-selector style.
  const key = String(id || "").replace(/^#/, "");
  return key ? document.getElementById(key) : null;
}

async function mcFetch(url, opts = {}) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || data.detail || res.statusText);
  return data;
}

function mcEsc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function mcBadge(ok, up, down) {
  const cls = ok ? "mc-badge mc-badge--ok" : "mc-badge mc-badge--down";
  return `<span class="${cls}">${mcEsc(ok ? up : down)}</span>`;
}

function mcCard(title, body) {
  return `<section class="mc-card"><h3>${mcEsc(title)}</h3>${body}</section>`;
}

function mcGrid(cards) {
  return `<div class="mc-grid">${cards.join("")}</div>`;
}

function mcList(items) {
  if (!items?.length) return "<ul class='mc-list'><li class='muted'>—</li></ul>";
  return `<ul class="mc-list">${items.join("")}</ul>`;
}

function renderOperationalAdvisor(advisor) {
  const adv = advisor || {};
  const recs = adv.recommendations || [];
  if (!adv.headline && !recs.length) return "";
  const severityClass = (s) => {
    if (s === "warning") return "mc-advisor--warn";
    if (s === "info") return "mc-advisor--info";
    return "mc-advisor--ok";
  };
  const items = recs.map((r) => `
    <div class="mc-advisor-item ${severityClass(r.severity)}">
      <p><strong>${mcEsc(r.title)}</strong></p>
      ${r.reason ? `<p class="muted">${mcEsc(r.reason)}</p>` : ""}
      ${r.impact ? `<p>Impact: ${mcEsc(r.impact)}</p>` : ""}
      ${r.action ? `<p>Action: ${mcEsc(r.action)}</p>` : ""}
      ${r.duration_estimate ? `<p class="muted">Est. ${mcEsc(r.duration_estimate)}</p>` : ""}
    </div>`).join("");
  const healthy = adv.healthy ? "mc-advisor--ok" : recs.length ? "mc-advisor--warn" : "mc-advisor--ok";
  return mcCard(
    "Operational advisor",
    `<p class="mc-advisor-headline ${healthy}"><strong>${mcEsc(adv.headline || "—")}</strong></p>${items || "<p class='muted'>No recommendations</p>"}`
  );
}

function renderOverview(d) {
  const ov = d.overview || {};
  const phase = (ov.phase || {}).phase || "?";
  const advisor = ov.operational_advisor || d.operational_advisor || {};
  return `
    <div class="mc-hero">
      <div class="mc-hero-stat"><span class="muted">Platform</span><strong>${mcEsc(ov.platform_status)}</strong></div>
      <div class="mc-hero-stat"><span class="muted">Phase</span><strong>${mcEsc(phase)}</strong></div>
      <div class="mc-hero-stat"><span class="muted">Acceptance</span><strong>${ov.acceptance_overall ?? "—"}%</strong></div>
      <div class="mc-hero-stat"><span class="muted">Production</span><strong>${ov.production_readiness ?? "—"}%</strong></div>
      <div class="mc-hero-stat"><span class="muted">Model</span><strong><code>${mcEsc(ov.current_model || "—")}</code></strong></div>
      <div class="mc-hero-stat"><span class="muted">Jobs</span><strong>${ov.active_jobs ?? 0}</strong></div>
    </div>
    ${renderOperationalAdvisor(advisor)}
    ${mcGrid([
      mcCard("User & project", `<p><strong>${mcEsc(ov.user)}</strong></p><p>Project: ${mcEsc(ov.project || "—")}</p><p>Branch: <code>${mcEsc(ov.aria_branch || "?")}</code></p>`),
      mcCard("Providers", `<p>Inference: <strong>${mcEsc(ov.inference_provider)}</strong></p><p>Memory: <strong>${mcEsc(ov.memory_provider)}</strong></p><p>Knowledge: <strong>${mcEsc(ov.knowledge_provider)}</strong></p>`),
      mcCard("Hardware", `<p>GPU: ${mcEsc(ov.gpu || "—")}</p><p>RAM free: ${ov.ram_available_gb ?? "—"} GB</p><p>VRAM free: ${ov.free_vram_mb ?? "—"} MB</p><p>Load: ${ov.cpu_load ?? "—"}</p>`),
      mcCard("Attention", (ov.needs_attention || []).map((n) => `<p>• ${mcEsc(n)}</p>`).join("") || "<p class='muted'>All clear</p>"),
      renderRoutingOverviewCard(d.routing_stats),
    ])}
    ${renderNotifications(d.notifications)}
  `;
}

function renderNotifications(notifs) {
  if (!notifs?.length) return "";
  const items = notifs.slice(0, 8).map((n) => `<li><span class="muted">${mcEsc(n.iso)}</span> <strong>${mcEsc(n.title)}</strong> ${mcEsc(n.detail)}</li>`);
  return mcCard("Recent notifications", mcList(items));
}

function renderApplications(d) {
  const rows = (d.applications || [])
    .map(
      (a) => `<tr>
        <td><strong>${mcEsc(a.label)}</strong><br><span class="muted">${mcEsc(a.id)}</span></td>
        <td>${mcBadge(a.running, "Running", "Stopped")} ${mcBadge(a.healthy, "Healthy", "Down")}</td>
        <td>${mcEsc(a.version || "—")}</td>
        <td>${mcEsc(a.project || "—")}</td>
        <td><code>${mcEsc(a.memory_namespace || "—")}</code></td>
        <td class="mc-actions">
          ${a.id === "aria" ? `<button type="button" class="ghost-btn small" data-mc-launch="aria">Launch</button>` : ""}
          ${a.id === "aria-uncensored" ? `<button type="button" class="ghost-btn small" data-mc-launch="uncensored">Launch</button>` : ""}
        </td>
      </tr>`
    )
    .join("");
  return `<table class="mc-table"><thead><tr><th>Application</th><th>Status</th><th>Version</th><th>Project</th><th>Memory NS</th><th></th></tr></thead><tbody>${rows || "<tr><td colspan='6' class='muted'>No applications</td></tr>"}</tbody></table>`;
}

function renderInference(d) {
  const inf = d.inference || {};
  const loaded = (inf.loaded_models || []).map((m) => `<li><code>${mcEsc(m.name || m.model || JSON.stringify(m))}</code></li>`).join("");
  const active = Object.entries(inf.active_models || {}).map(([k, v]) => `<li>${mcEsc(k)}: <code>${mcEsc(v)}</code></li>`).join("");
  return mcGrid([
    mcCard("Current", `<p>Provider: <strong>${mcEsc(inf.provider)}</strong></p><p>Model: <code>${mcEsc(inf.current_model || "—")}</code></p><p>Ollama ${mcBadge(inf.ollama_running, "up", "down")}</p>`),
    mcCard("Active models", mcList([active])),
    mcCard("Loaded in VRAM", mcList([loaded])),
    mcCard("Gateway", `<pre class="mc-pre">${mcEsc(JSON.stringify(inf.gateway || {}, null, 2))}</pre>`),
  ]);
}

function renderMemory(d) {
  const mem = d.memory || {};
  const ns = Object.entries(mem.namespaces || {}).map(([n, c]) => `<li>${mcEsc(n)} (${c})</li>`).join("");
  const recent = (mem.recent || []).map((e) => `<li><code>${mcEsc(e.namespace)}</code> ${mcEsc(e.content)}</li>`).join("");
  return mcGrid([
    mcCard("Store", `<p>Provider: <strong>${mcEsc(mem.provider)}</strong></p><p>Entries: ${mem.entry_count ?? "—"}</p><p>Semantic vectors: ${mem.semantic_vectors ?? "—"}</p><p>Cutover: ${mcEsc(mem.cutover_mode || "—")}</p>`),
    mcCard("Namespaces", mcList([ns])),
    mcCard("Recent", mcList([recent])),
  ]);
}

function renderKnowledge(d) {
  const k = d.knowledge || {};
  const sources = (k.sources || []).map((s) => `<li>${mcEsc(typeof s === "string" ? s : s.name || JSON.stringify(s))}</li>`).join("");
  return mcGrid([
    mcCard("Retrieval", `<p>Provider: <strong>${mcEsc(k.retrieval)}</strong></p><p>Documents: ${k.documents ?? "—"}</p><p>Last sync: ${mcEsc(k.last_sync || "—")}</p>`),
    mcCard("Sources", mcList([sources])),
  ]);
}

function renderDatabases(d) {
  const dbs = (d.databases || []).map((db) => `<li>${mcEsc(db.label || db.id)} ${mcBadge(db.running, "up", "down")} <span class="muted">${mcEsc(db.detail || "")}</span></li>`).join("");
  const svc = (d.services || []).map((s) => `<li>${mcEsc(s.label || s.id)} ${mcBadge(s.running, "up", "down")}</li>`).join("");
  return mcGrid([mcCard("Databases", mcList([dbs])), mcCard("All services", mcList([svc]))]);
}

function renderHardware(d) {
  const h = d.hardware || {};
  return mcGrid([
    mcCard("CPU / RAM", `<p>Load (1m): ${h.cpu_load ?? "—"}</p><p>RAM available: ${h.ram_available_gb ?? "—"} / ${h.ram_total_gb ?? "—"} GB</p><p>Swap used: ${h.swap_used_gb ?? "—"} GB</p>`),
    mcCard("GPU", `<p>${mcEsc(h.gpu_name || "—")}</p><p>VRAM: ${h.free_vram_mb ?? "—"} / ${h.vram_mb ?? "—"} MB free</p><p>Models loaded: ${h.ollama_models_loaded ?? 0}</p>`),
    mcCard("Disk", `<p>Free: ${h.disk_free_gb ?? "—"} GB</p>`),
  ]);
}

function renderJobs(d) {
  const j = d.jobs || {};
  const recent = (j.recent || []).map((job) => `<li>${mcBadge(!job.done, "active", "done")} [${mcEsc(job.queue)}] ${mcEsc(job.label)} — ${mcEsc(job.message)}</li>`).join("");
  return mcGrid([
    mcCard("Queues", `<p>Media busy: ${mcBadge(j.media?.busy, "yes", "no")}</p><p>Coding busy: ${mcBadge(j.coding?.busy, "yes", "no")}</p><p>Any busy: ${mcBadge(j.any_busy, "yes", "no")}</p>`),
    mcCard("Recent jobs", mcList([recent])),
  ]);
}

function renderActivity(d, filters = {}) {
  const q = filters.q || mc$("mcActivityQuery")?.value?.trim() || "";
  const comp = filters.component || mc$("mcActivityComponent")?.value?.trim() || "";
  const params = new URLSearchParams({ limit: "100" });
  if (q) params.set("q", q);
  if (comp) params.set("component", comp);
  return mcFetch(`/api/workstation/activity?${params}`).then((act) => {
    const events = act.events || d.activity?.events || [];
    if (!events.length) return "<p class='muted'>No activity recorded yet.</p>";
    const rows = events
      .map(
        (ev) => `<tr class="mc-activity-${mcEsc(ev.status || "ok")}">
          <td>${mcEsc(ev.iso)}</td><td><strong>${mcEsc(ev.type)}</strong></td>
          <td>${mcEsc(ev.component)}</td><td>${mcEsc(ev.status)}</td>
          <td>${ev.duration_ms != null ? ev.duration_ms + "ms" : "—"}</td>
          <td>${mcEsc(ev.detail)}</td>
        </tr>`
      )
      .join("");
    return `
      <div class="mc-activity-toolbar">
        <input type="search" id="mcActivityQuery" class="audio-path-input" placeholder="Search…" value="${mcEsc(q)}" />
        <input type="text" id="mcActivityComponent" class="audio-path-input" placeholder="Component" value="${mcEsc(comp)}" />
        <button type="button" class="ghost-btn small" id="mcActivityFilterBtn">Filter</button>
        <a class="ghost-btn small" href="/api/mission-control/activity/export" download="activity.csv">Export CSV</a>
      </div>
      <table class="mc-table mc-activity-table"><thead><tr><th>Time</th><th>Event</th><th>Component</th><th>Status</th><th>Duration</th><th>Details</th></tr></thead><tbody>${rows}</tbody></table>`;
  });
}

function renderPerformance(d) {
  const perf = d?.performance || d || {};
  const latest = perf.latest;
  const trends = perf.trends || {};
  const labels = { mission_control_ms: "Mission Control", aria_ms: "Aria", routing_write_ms: "Routing write", timeline_write_ms: "Timeline write" };
  const cards = Object.entries(labels).map(([key, label]) => {
    const block = latest?.metrics?.[key];
    const p50 = block?.p50_ms ?? trends[key]?.latest_p50_ms ?? "—";
    return mcCard(label, `<p><strong>${p50}</strong> ms p50</p>`);
  });
  return `<div class="mc-routing-toolbar">
    <button type="button" class="ghost-btn small" id="mcPerfRunBtn">Run benchmark</button>
    <a class="ghost-btn small" href="/api/mission-control/bug-report/export?format=json" download="bug-report.json">Bug report</a>
  </div>${mcGrid(cards)}<p class="muted">Runs: ${perf.run_count ?? 0}</p>`;
}

function renderReleaseDashboard(r) {
  const warnings = (r.warnings || []).map((w) => `<li>${mcEsc(w)}</li>`).join("") || "<li class='muted'>None</li>";
  return `${mcGrid([
    mcCard("Readiness", `<p>Production: <strong>${r.production_readiness ?? "—"}%</strong></p><p>Acceptance: <strong>${r.acceptance_overall ?? "—"}%</strong></p>`),
    mcCard("Warnings", mcList([warnings])),
    mcCard("Export", `<a class="ghost-btn small" href="/api/mission-control/bug-report/export?format=markdown" download="bug-report.md">Download bug report</a>`),
  ])}`;
}

function renderSettings(d) {
  const s = d.settings || {};
  const registry = s.intent_registry?.intents || [];
  const regRows = registry
    .map(
      (i) =>
        `<tr><td>${mcEsc(i.intent)}</td><td>${mcEsc(i.handler)}</td>` +
        `<td>${i.uses ?? 0}</td><td>${i.avg_confidence ?? "—"}</td>` +
        `<td>${i.success_rate ?? "—"}%</td></tr>`
    )
    .join("");
  return mcGrid([
    mcCard("Platform", `<pre class="mc-pre">${mcEsc(JSON.stringify(s, null, 2).slice(0, 1200))}</pre>`),
    mcCard(
      "Intent Registry",
      regRows
        ? `<table class="mc-table"><thead><tr><th>Intent</th><th>Handler</th><th>Uses</th><th>Confidence</th><th>Success</th></tr></thead><tbody>${regRows}</tbody></table>`
        : "<p class='muted'>No intent statistics yet.</p>"
    ),
  ]);
}

function timelineSeverityClass(ev) {
  const sev = (ev.severity || "info").toLowerCase();
  if (sev === "error" || sev === "critical") return "mc-route-error";
  if (sev === "warning") return "mc-route-fallback";
  return "mc-route-ok";
}

function renderTimelineInspector(events, stats) {
  const rows = (events || [])
    .map((ev) => {
      const cls = timelineSeverityClass(ev);
      return `<tr class="${cls}"><td>${mcEsc(ev.iso)}</td><td>${mcEsc(ev.type)}</td>` +
        `<td>${mcEsc(ev.application)}/${mcEsc(ev.component)}</td>` +
        `<td>${mcEsc(ev.severity)}</td><td>${mcEsc(ev.detail || "")}</td></tr>`;
    })
    .join("");
  const exportBtns = `
    <a class="ghost-btn small" href="/api/mission-control/timeline/export?format=json" target="_blank">JSON</a>
    <a class="ghost-btn small" href="/api/mission-control/timeline/export?format=csv" target="_blank">CSV</a>
    <a class="ghost-btn small" href="/api/mission-control/timeline/export?format=markdown" target="_blank">Markdown</a>
    <a class="ghost-btn small" href="/api/mission-control/timeline/export?format=html" target="_blank">HTML</a>`;
  return `
    <div class="mc-routing-toolbar">
      <input type="search" id="mcTimelineSearch" placeholder="Search timeline…" value="">
      <select id="mcTimelineSeverity"><option value="">All severities</option>
        <option value="info">Info</option><option value="warning">Warning</option>
        <option value="error">Error</option></select>
      ${exportBtns}
    </div>
    <p class="muted">Events: ${stats?.count ?? events?.length ?? 0}</p>
    <table class="mc-table"><thead><tr><th>Time</th><th>Type</th><th>App/Component</th><th>Severity</th><th>Detail</th></tr></thead>
    <tbody>${rows || "<tr><td colspan='5' class='muted'>No events</td></tr>"}</tbody></table>`;
}

async function loadTimelineInspector() {
  const params = new URLSearchParams({ limit: "200" });
  const q = mc$("mcTimelineSearch")?.value?.trim();
  const sev = mc$("mcTimelineSeverity")?.value;
  if (q) params.set("q", q);
  if (sev) params.set("severity", sev);
  const [eventsResp, stats] = await Promise.all([
    mcFetch(`/api/mission-control/timeline?${params}`),
    mcFetch("/api/mission-control/timeline/stats"),
  ]);
  return { events: eventsResp.events || [], stats };
}

async function reloadTimelineInspector() {
  const body = mc$("mcTabBody");
  if (!body || _mcTab !== "timeline") return;
  try {
    const { events, stats } = await loadTimelineInspector();
    body.innerHTML = renderTimelineInspector(events, stats);
  } catch (e) {
    body.innerHTML = `<p class="muted">${mcEsc(e.message)}</p>`;
  }
}

function wireTimelineInspector() {
  /* Delegated via ensureMcDelegates — kept for call-site compatibility. */
  ensureMcDelegates();
}

function renderRecovery(d) {
  const r = d.recovery || {};
  const actions = (r.recommended_actions || []).map((a) => `<li>${mcEsc(a)}</li>`).join("");
  const issues = (r.known_issues || []).map((i) => `<li>${mcEsc(i)}</li>`).join("");
  return `
    <div class="mc-recovery-actions">
      <button type="button" class="ghost-btn small" id="mcRepairBtn">Repair</button>
      <button type="button" class="ghost-btn small" id="mcAcceptanceBtn">Run acceptance</button>
    </div>
    ${mcGrid([
      mcCard("Health", `<p>${mcBadge(r.health?.ok, "OK", "Issues")}</p><pre class="mc-pre">${mcEsc(JSON.stringify(r.health || {}, null, 2).slice(0, 800))}</pre>`),
      mcCard("Backup", `<p>Latest: <code>${mcEsc(r.latest_backup || "none")}</code></p>`),
      mcCard("Recommended", mcList([actions])),
      mcCard("Known issues", mcList([issues])),
    ])}`;
}

function renderRoutingOverviewCard(stats) {
  const s = stats || {};
  if (!s.count) {
    return mcCard("Routing", "<p class='muted'>No routing records yet.</p>");
  }
  const last = s.last_route || {};
  return mcCard(
    "Routing",
    `<p><strong>Last route:</strong> ${mcEsc(last.intent || "—")} → ${mcEsc(last.route || "—")}</p>
     <p>Avg latency: <strong>${s.average_latency_ms ?? "—"}</strong> ms</p>
     <p>Runtime ${s.runtime_pct ?? 0}% · Search ${s.search_pct ?? 0}% · Knowledge ${s.knowledge_pct ?? 0}% · Tools ${s.tool_pct ?? 0}%</p>
     <p>Fallback ${s.fallback_pct ?? 0}% · Errors ${s.error_pct ?? 0}%</p>`
  );
}

function routingStatusClass(rec) {
  if (rec.error) return "mc-route-error";
  if (rec.fallback_used) return "mc-route-fallback";
  const lat = Number(rec.latency_ms || 0);
  if (lat >= 2000) return "mc-route-slow";
  return "mc-route-ok";
}

function renderRoutingInspector(records, stats) {
  const filters = [
    "Runtime",
    "Search",
    "Knowledge",
    "Memory",
    "Inference",
    "Tools",
    "Coding",
    "Vision",
    "Voice",
    "Automation",
    "Jobs",
    "Errors",
    "Fallbacks",
  ];
  const filterBtns = filters
    .map(
      (f) =>
        `<button type="button" class="ghost-btn small mc-route-filter${_mcRoutingFilter === f ? " active" : ""}" data-route-filter="${mcEsc(f)}">${mcEsc(f)}</button>`
    )
    .join(" ");
  const rows = (records || [])
    .map((r) => {
      const cls = routingStatusClass(r);
      const flow = (r.flow || []).join("\n");
      return `<tr class="${cls}" data-route-id="${mcEsc(r.id)}">
        <td>${mcEsc(r.iso)}</td>
        <td title="${mcEsc(r.prompt)}">${mcEsc((r.prompt || "").slice(0, 80))}</td>
        <td><code>${mcEsc(r.intent)}</code></td>
        <td>${mcEsc(r.route)}</td>
        <td>${mcEsc(r.handler)}</td>
        <td>${r.latency_ms ?? "—"}</td>
        <td>${r.confidence ?? "—"}</td>
        <td>${r.fallback_used ? mcEsc(r.fallback || "yes") : "None"}</td>
        <td><pre class="mc-flow">${mcEsc(flow)}</pre></td>
      </tr>`;
    })
    .join("");
  const exportBtns = `
    <a class="ghost-btn small" href="/api/mission-control/routing/export?format=json" target="_blank">Export JSON</a>
    <a class="ghost-btn small" href="/api/mission-control/routing/export?format=csv" target="_blank">Export CSV</a>
    <a class="ghost-btn small" href="/api/mission-control/routing/export?format=markdown" target="_blank">Export Markdown</a>`;
  return `
    <div class="mc-routing-toolbar">
      <input id="mcRoutingSearch" type="search" placeholder="Search prompt, intent, handler…" value="${mcEsc(_mcRoutingSearch)}" />
      <button type="button" class="ghost-btn small" id="mcRoutingLiveBtn">${_mcRoutingLive ? "Live Routing: ON" : "Live Routing: OFF"}</button>
      ${exportBtns}
    </div>
    <div class="mc-routing-filters">${filterBtns}</div>
    ${renderRoutingOverviewCard(stats)}
    <table class="mc-table mc-routing-table"><thead><tr>
      <th>Time</th><th>Prompt</th><th>Intent</th><th>Route</th><th>Handler</th><th>Latency</th><th>Conf</th><th>Fallback</th><th>Flow</th>
    </tr></thead><tbody>${rows || "<tr><td colspan='9' class='muted'>No records</td></tr>"}</tbody></table>
    <div id="mcRoutingDetail" class="mc-routing-detail hidden"></div>`;
}

async function loadRoutingInspector() {
  const params = new URLSearchParams({ limit: "100" });
  if (_mcRoutingSearch) params.set("q", _mcRoutingSearch);
  if (_mcRoutingFilter === "Errors") params.set("errors", "1");
  else if (_mcRoutingFilter === "Fallbacks") params.set("fallbacks", "1");
  else if (_mcRoutingFilter) params.set("category", _mcRoutingFilter);
  const [recordsResp, statsResp] = await Promise.all([
    mcFetch(`/api/mission-control/routing?${params}`),
    mcFetch("/api/mission-control/routing/stats"),
  ]);
  return { records: recordsResp.records || [], stats: statsResp };
}

function wireRoutingInspector() {
  /* Delegated via ensureMcDelegates — kept for call-site compatibility. */
  ensureMcDelegates();
}

function renderIntentAnalytics(data) {
  const week = data?.week || data || {};
  const dist = week.distribution || [];
  const rows = dist
    .map(
      (d) =>
        `<tr><td>${mcEsc(d.intent)}</td><td>${d.count}</td><td>${d.pct}%</td>` +
        `<td>${d.avg_confidence ?? "—"}</td><td>${d.avg_route_latency_ms ?? "—"}</td></tr>`
    )
    .join("");
  return mcGrid([
    mcCard(
      "Summary (week)",
      `<p>Records: <strong>${week.count ?? 0}</strong></p>
       <p>Clarification rate: ${week.clarification_rate ?? 0}% · Fallback: ${week.fallback_rate ?? 0}%</p>
       <p>Success: ${week.success_rate ?? 0}% · Errors: ${week.error_rate ?? 0}%</p>`
    ),
    mcCard(
      "Intent distribution",
      rows
        ? `<table class="mc-table"><thead><tr><th>Intent</th><th>Count</th><th>%</th><th>Conf</th><th>Route ms</th></tr></thead><tbody>${rows}</tbody></table>`
        : "<p class='muted'>No analytics yet.</p>"
    ),
    mcCard("Classifier", renderClassifierCard()),
  ]);
}

function renderClassifierCard() {
  const c = _mcData?.classifier_health || _mcData?.settings?.classifier || {};
  return `<p><strong>Model:</strong> <code>${mcEsc(c.model || "—")}</code></p>
    <p><strong>Device:</strong> ${mcEsc(c.device || "—")} · <strong>Status:</strong> ${mcEsc(c.benchmark_status || "—")}</p>
    <p><strong>Latency:</strong> ${c.average_latency_ms ?? "—"} ms · <strong>Healthy:</strong> ${c.healthy ? "yes" : "no"}</p>
    <p class="muted">${mcEsc(c.selection_reason || "")}</p>`;
}

async function loadIntentAnalytics() {
  return mcFetch("/api/mission-control/intent-analytics?window=week");
}

function renderConnection(conn) {
  const checks = conn.checks || {};
  const row = (label, ok) =>
    `<tr><td>${mcEsc(label)}</td><td>${mcBadge(ok, "Yes", "No")}</td></tr>`;
  const issues = (conn.issues || []).map((i) => `<li>${mcEsc(i)}</li>`).join("");
  return mcGrid([
    mcCard(
      "Runtime connection",
      `<table class="mc-table">
        ${row("Platform discovered", conn.platform_discovered)}
        ${row("Mission Control reachable", conn.mission_control_reachable)}
        ${row("ApplicationHost connected", conn.application_host_connected)}
        ${row("Application registered", conn.application_registered)}
        ${row("Runtime synced", conn.runtime_synced)}
      </table>
      <p class="muted">Mode: <code>${mcEsc(conn.connection_mode || "none")}</code></p>
      <p class="muted">URL: <code>${mcEsc(conn.mission_control_url || "—")}</code></p>`
    ),
    mcCard(
      "Heartbeat & API",
      `<p>Heartbeat age: <strong>${conn.heartbeat_age_seconds ?? "—"}</strong>s</p>
       <p>Last API: <strong>${mcEsc(conn.last_api_call || "—")}</strong></p>
       <p>Path: <code>${mcEsc(conn.last_api_path || "—")}</code></p>
       <p>Latency: <strong>${conn.connection_latency_ms ?? "—"}</strong> ms</p>
       <p>Last error: ${mcEsc(conn.last_error || "—")}</p>`
    ),
    mcCard(
      "Self-test checks",
      `<table class="mc-table">${Object.entries(checks)
        .map(([k, v]) => row(k.replace(/_/g, " "), v))
        .join("")}</table>`
    ),
    mcCard("Issues", issues ? `<ul class="mc-list">${issues}</ul>` : "<p class='muted'>None</p>"),
  ]);
}

async function renderMcTab(tab) {
  const body = mc$("mcTabBody");
  if (!body) return;
  const gen = ++_mcRenderGen;
  const stillCurrent = () => gen === _mcRenderGen && _mcTab === tab;
  if (tab === "connection") {
    body.innerHTML = "<p class='muted'>Loading…</p>";
    let html = "";
    try {
      const conn = await mcFetch("/api/runtime/connection");
      html = renderConnection(conn);
    } catch (e) {
      html = `<p class="muted">${mcEsc(e.message)}</p>`;
    }
    if (!stillCurrent()) return;
    body.innerHTML = html;
    return;
  }
  if (tab === "routing") {
    body.innerHTML = "<p class='muted'>Loading routing inspector…</p>";
    try {
      const { records, stats } = await loadRoutingInspector();
      if (!stillCurrent()) return;
      body.innerHTML = renderRoutingInspector(records, stats);
      wireRoutingInspector();
      if (_mcRoutingLive) body.scrollTop = body.scrollHeight;
    } catch (e) {
      if (!stillCurrent()) return;
      body.innerHTML = `<p class="muted">${mcEsc(e.message)}</p>`;
    }
    return;
  }
  if (tab === "intent_analytics") {
    body.innerHTML = "<p class='muted'>Loading intent analytics…</p>";
    try {
      const data = await mcFetch("/api/mission-control/intent-analytics?window=week");
      if (!stillCurrent()) return;
      body.innerHTML = renderIntentAnalytics(data);
    } catch (e) {
      if (!stillCurrent()) return;
      body.innerHTML = `<p class="muted">${mcEsc(e.message)}</p>`;
    }
    return;
  }
  if (tab === "release") {
    body.innerHTML = "<p class='muted'>Loading release readiness…</p>";
    try {
      const data = await mcFetch("/api/mission-control/release");
      if (!stillCurrent()) return;
      body.innerHTML = renderReleaseDashboard(data);
      wireMcTabActions();
    } catch (e) {
      if (!stillCurrent()) return;
      body.innerHTML = `<p class="muted">${mcEsc(e.message)}</p>`;
    }
    return;
  }
  if (tab === "timeline") {
    body.innerHTML = "<p class='muted'>Loading event timeline…</p>";
    try {
      const { events, stats } = await loadTimelineInspector();
      if (!stillCurrent()) return;
      body.innerHTML = renderTimelineInspector(events, stats);
      wireTimelineInspector();
    } catch (e) {
      if (!stillCurrent()) return;
      body.innerHTML = `<p class="muted">${mcEsc(e.message)}</p>`;
    }
    return;
  }
  if (!_mcData) return;
  body.innerHTML = "<p class='muted'>Loading…</p>";
  let html = "";
  switch (tab) {
    case "overview":
      html = renderOverview(_mcData);
      break;
    case "applications":
      html = renderApplications(_mcData);
      break;
    case "inference":
      html = renderInference(_mcData);
      break;
    case "memory":
      html = renderMemory(_mcData);
      break;
    case "knowledge":
      html = renderKnowledge(_mcData);
      break;
    case "databases":
      html = renderDatabases(_mcData);
      break;
    case "hardware":
      html = renderHardware(_mcData);
      break;
    case "jobs":
      html = renderJobs(_mcData);
      break;
    case "activity":
      html = await renderActivity(_mcData);
      break;
    case "performance":
      html = renderPerformance(_mcData);
      break;
    case "settings":
      html = renderSettings(_mcData);
      break;
    case "recovery":
      html = renderRecovery(_mcData);
      break;
    default:
      html = "<p class='muted'>Unknown tab</p>";
  }
  if (!stillCurrent()) return;
  body.innerHTML = html;
  ensureMcDelegates();
}

function ensureMcDelegates() {
  const body = mc$("mcTabBody");
  if (!body || body.dataset.mcDelegates === "1") return;
  body.dataset.mcDelegates = "1";
  let timelineTimer = null;

  body.addEventListener("input", (e) => {
    if (e.target?.id !== "mcTimelineSearch" || _mcTab !== "timeline") return;
    clearTimeout(timelineTimer);
    timelineTimer = setTimeout(() => reloadTimelineInspector(), 250);
  });
  body.addEventListener("change", (e) => {
    if (e.target?.id !== "mcTimelineSeverity" || _mcTab !== "timeline") return;
    reloadTimelineInspector();
  });
  body.addEventListener("keydown", (e) => {
    if (e.target?.id === "mcRoutingSearch" && e.key === "Enter") {
      _mcRoutingSearch = e.target.value || "";
      renderMcTab("routing");
    }
  });
  body.addEventListener("click", async (e) => {
    const filter = e.target.closest?.(".mc-route-filter");
    if (filter) {
      const f = filter.dataset.routeFilter || "";
      _mcRoutingFilter = _mcRoutingFilter === f ? "" : f;
      renderMcTab("routing");
      return;
    }
    if (e.target.closest?.("#mcRoutingLiveBtn")) {
      _mcRoutingLive = !_mcRoutingLive;
      if (_mcRoutingLive) {
        if (_mcRoutingPoll) clearInterval(_mcRoutingPoll);
        _mcRoutingPoll = setInterval(() => {
          if (_mcTab === "routing") renderMcTab("routing");
        }, 2000);
      } else if (_mcRoutingPoll) {
        clearInterval(_mcRoutingPoll);
        _mcRoutingPoll = null;
      }
      renderMcTab("routing");
      return;
    }
    const row = e.target.closest?.(".mc-routing-table tbody tr[data-route-id]");
    if (row) {
      const id = row.dataset.routeId;
      const detail = mc$("mcRoutingDetail");
      if (!detail || !id) return;
      try {
        const data = await mcFetch(`/api/mission-control/routing/${encodeURIComponent(id)}`);
        const rec = data.record || {};
        const sem = rec.semantic_report || {};
        detail.classList.remove("hidden");
        detail.innerHTML = `<h4>Semantic Report</h4>
          <p><strong>Prompt:</strong> ${mcEsc(rec.prompt)}</p>
          <p><strong>Intent:</strong> <code>${mcEsc(rec.intent)}</code> · <strong>Confidence:</strong> ${rec.confidence ?? "—"}</p>
          <p><strong>Route:</strong> ${mcEsc(rec.route)} · <strong>Handler:</strong> ${mcEsc(rec.handler)}</p>
          <p><strong>Latency:</strong> ${rec.latency_ms} ms · <strong>Band:</strong> ${mcEsc(rec.confidence_band || "—")}</p>
          <h5>Classifier output</h5>
          <pre class="mc-pre">${mcEsc(JSON.stringify(sem.semantic || sem, null, 2))}</pre>
          <h5>Grammar / Morphology / Syntax</h5>
          <pre class="mc-pre">${mcEsc(JSON.stringify({grammar: sem.grammar, morphology: sem.morphology, syntax: sem.syntax}, null, 2))}</pre>
          <p><strong>Rule matched:</strong> ${mcEsc(rec.rule_matched || "—")} · <strong>Stage:</strong> ${mcEsc(rec.router_stage || "—")}</p>`;
      } catch (err) {
        detail.textContent = err.message;
      }
      return;
    }
    if (e.target.closest?.("#mcActivityFilterBtn")) {
      renderMcTab("activity");
      return;
    }
    if (e.target.closest?.("#mcRepairBtn")) {
      try {
        const data = await mcFetch("/api/workstation/recover", { method: "POST" });
        const issues = data.report?.warnings ?? data.report?.issues?.length ?? 0;
        const summary = data.ok
          ? (issues ? `Repair done · ${issues} warning(s)` : "Repair done · healthy")
          : "Repair finished with issues";
        window.showAriaToast?.(summary, data.ok ? "ok" : "warn");
        loadMissionControl();
      } catch (err) {
        window.showAriaToast?.(err.message, "err");
      }
      return;
    }
    if (e.target.closest?.("#mcAcceptanceBtn")) {
      window.switchToView?.("chat");
      window.sendMessage?.("workstation acceptance");
      return;
    }
    if (e.target.closest?.("#mcPerfRunBtn")) {
      try {
        await mcFetch("/api/mission-control/performance-lab/run", { method: "POST" });
        window.showAriaToast?.("Benchmark complete", "ok");
        loadMissionControl();
      } catch (err) {
        window.showAriaToast?.(err.message, "err");
      }
      return;
    }
    const launch = e.target.closest?.("[data-mc-launch]");
    if (launch) {
      const kind = launch.dataset.mcLaunch;
      window.switchToView?.("chat");
      if (kind === "uncensored") window.sendMessage?.("switch to uncensored");
    }
  });
}

function wireMcTabActions() {
  ensureMcDelegates();
}

function switchMcTab(tab) {
  _mcTab = tab;
  document.querySelectorAll(".mc-tab").forEach((el) => {
    el.classList.toggle("active", el.dataset.mcTab === tab);
  });
  renderMcTab(tab);
}

async function loadMissionControl() {
  const status = mc$("mcLoadStatus");
  if (status) status.textContent = "Refreshing…";
  try {
    _mcData = await mcFetch("/api/mission-control");
    if (status) status.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    switchMcTab(_mcTab);
  } catch (e) {
    if (status) status.textContent = e.message;
  }
}

function initMissionControl() {
  const nav = mc$("mcTabNav");
  if (nav && !nav.dataset.wired) {
    nav.dataset.wired = "1";
    nav.innerHTML = MC_TABS.map(
      (t) => `<button type="button" class="mc-tab${t === _mcTab ? " active" : ""}" data-mc-tab="${t}">${t.charAt(0).toUpperCase() + t.slice(1)}</button>`
    ).join("");
    nav.querySelectorAll(".mc-tab").forEach((btn) => {
      btn.addEventListener("click", () => switchMcTab(btn.dataset.mcTab));
    });
  }
  if (mc$("mcRefreshBtn") && !mc$("mcRefreshBtn").dataset.wired) {
    mc$("mcRefreshBtn").dataset.wired = "1";
    mc$("mcRefreshBtn").addEventListener("click", loadMissionControl);
  }
  loadMissionControl();
  if (_mcPoll) clearInterval(_mcPoll);
  _mcPoll = setInterval(() => {
    if (document.getElementById("workstationView")?.classList.contains("hidden")) return;
    loadMissionControl();
  }, 30000);
}

window.initWorkstation = initMissionControl;
window.initMissionControl = initMissionControl;
window.loadMissionControl = loadMissionControl;
window.switchMcTab = switchMcTab;

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-ws-nav]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.wsNav;
      if (target === "chat-status") {
        window.switchToView?.("chat");
        window.sendMessage?.("status");
        return;
      }
      window.switchToView?.("workstation");
      if (target === "workstation" || target === "overview") switchMcTab("overview");
      else if (target === "workstationActivityList") switchMcTab("activity");
      else if (target === "workstationConnection") switchMcTab("connection");
      else if (target === "workstationInference") switchMcTab("inference");
      else if (target) switchMcTab("overview");
    });
  });
});
