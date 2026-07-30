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
  "runtime_config",
  "recovery",
];

/** Shared with mission_control_ux.js via window (let bindings are not cross-script). */
window._mcData = window._mcData || null;
window._mcTab = window._mcTab || "overview";
window._mcPoll = window._mcPoll || null;
window._mcRoutingLive = false;
window._mcRoutingPoll = null;
window._mcRoutingFilter = "";
window._mcRoutingSearch = "";
/** Monotonic token so slow async tab loads cannot overwrite a newer tab. */
let _mcRenderGen = 0;
// Compat aliases used throughout this file
var _mcData = window._mcData;
var _mcTab = window._mcTab;
var _mcPoll = window._mcPoll;
var _mcRoutingLive = window._mcRoutingLive;
var _mcRoutingPoll = window._mcRoutingPoll;
var _mcRoutingFilter = window._mcRoutingFilter;
var _mcRoutingSearch = window._mcRoutingSearch;

function mcSyncGlobals() {
  window._mcData = _mcData;
  window._mcTab = _mcTab;
  window._mcPoll = _mcPoll;
  window._mcRoutingLive = _mcRoutingLive;
  window._mcRoutingPoll = _mcRoutingPoll;
  window._mcRoutingFilter = _mcRoutingFilter;
  window._mcRoutingSearch = _mcRoutingSearch;
}

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
    `<p class="mc-advisor-headline ${healthy}"><strong>${mcEsc(adv.headline || "—")}</strong></p>${items || "<p class='muted'>No recommendations. <button type='button' class='ghost-btn tiny' id='mcEmptyRecChatBtn'>Ask Chat</button></p>"}`
  );
}

function renderOverview(d) {
  const ov = d.overview || {};
  const phase = (ov.phase || {}).phase || "?";
  const advisor = ov.operational_advisor || d.operational_advisor || {};
      const voice = d.voice || {};
  const vision = d.vision || {};
  const flytying = d.flytying || {};
  const smarthome = d.smarthome || {};
  const capabilities = d.capabilities || {};
  const integrations = d.integrations || {};
  const searchProduct = d.search || {};
  const settingsProduct = d.settings_product || {};
  const dashboardProduct = d.dashboard || {};
  const voiceCard = voice.product
    ? mcCard(
        "Voice",
        `<p>State: <strong>${mcEsc(voice.state || "idle")}</strong></p>
         <p>Whisper ${mcBadge(!!voice.whisper, "ok", "missing")} · Piper ${mcBadge(!!voice.piper, "ok", "missing")}</p>
         <p>Cloud Live: ${mcEsc(voice.cloud_live?.provider || (voice.cloud_live?.available ? "ready" : "off"))} · sessions ${voice.cloud_live?.active_sessions ?? 0}</p>
         <p>Duplex: ${mcEsc(voice.duplex || "—")} · queue ${voice.queue?.pending ?? 0}</p>
         <p class="mc-actions">
           <button type="button" class="ghost-btn small" data-mc-action="voice_summary">Voice summary</button>
           <a class="ghost-btn small" href="#voice" data-mc-nav="voice">Open Voice</a>
           <a class="ghost-btn small" href="/api/voice/recovery" target="_blank">Recovery</a>
         </p>`
      )
    : "";
  const visionCard = vision.product
    ? mcCard(
        "Vision",
        `<p>State: <strong>${mcEsc(vision.state || "idle")}</strong></p>
         <p>Model: <code>${mcEsc(vision.model || "—")}</code> · ${mcEsc(vision.quality_mode || "")}</p>
         <p>VRAM est. ${vision.estimated_vram_mb ?? "—"}MB · free ${vision.free_vram_mb ?? "—"}MB</p>
         <p>Batch jobs: ${vision.queue?.batch_jobs ?? 0} · active ${vision.queue?.active ?? 0}</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#vision" data-mc-nav="vision">Open Vision</a>
           <a class="ghost-btn small" href="/api/vision/honesty" target="_blank">Honesty</a>
         </p>`
      )
    : "";
  const flytyingCard = flytying.product
    ? mcCard(
        "Fly Tying",
        `<p>State: <strong>${mcEsc(flytying.state || "idle")}</strong> · corpus ${mcBadge(!!flytying.corpus_loaded, "ok", "offline")}</p>
         <p>Patterns: ${flytying.record_count ?? "—"} · RAG ${mcBadge(!!flytying.rag, "ok", "keyword")}</p>
         <p>Inventory: ${flytying.inventory?.count ?? 0} · low ${flytying.inventory?.low_stock ?? 0} · queue ${flytying.queue?.pending ?? 0}</p>
         <p>Session: ${flytying.session?.active ? mcEsc(flytying.session?.recipe_name || flytying.session?.id || "active") : "none"}</p>
         <p>Recovery: ${flytying.recovery?.ready ? "ready" : mcEsc(flytying.recovery?.hint || "setup needed")} (${flytying.recovery?.steps_done ?? 0}/${flytying.recovery?.steps_total ?? 0})</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#flytying" data-mc-nav="flytying">Open Fly Tying</a>
           <a class="ghost-btn small" href="/api/flytying/product/recovery" target="_blank">Recovery</a>
           <a class="ghost-btn small" href="/api/flytying/product/mission" target="_blank">Mission</a>
         </p>`
      )
    : "";
  const smarthomeCard = smarthome.product
    ? mcCard(
        "Smart Home",
        `<p>State: <strong>${mcEsc(smarthome.state || "idle")}</strong> · ${mcBadge(!!smarthome.connected, "ok", "offline")}</p>
         <p>Entities: ${smarthome.entity_count ?? "—"} · rooms ${smarthome.rooms?.count ?? 0} · favorites ${smarthome.favorites?.count ?? 0}</p>
         <p>Webhook ${mcBadge(!!smarthome.webhook?.set, "ok", "unset")} · HA ${mcEsc(smarthome.version || "—")}</p>
         <p>Recovery: ${smarthome.recovery?.ready ? "ready" : mcEsc(smarthome.recovery?.hint || "setup needed")} (${smarthome.recovery?.steps_done ?? 0}/${smarthome.recovery?.steps_total ?? 0})</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#smarthome" data-mc-nav="home">Open Smart Home</a>
           <a class="ghost-btn small" href="/api/smarthome/product/recovery" target="_blank">Recovery</a>
           <a class="ghost-btn small" href="/api/smarthome/product/mission" target="_blank">Mission</a>
         </p>`
      )
    : "";
  const capabilitiesCard = capabilities.product
    ? mcCard(
        "Capabilities",
        `<p>State: <strong>${mcEsc(capabilities.state || "idle")}</strong> · ${capabilities.count ?? 0} total</p>
         <p>Enabled ${capabilities.enabled ?? 0} · disabled ${capabilities.disabled ?? 0} · failed ${capabilities.failed ?? 0}</p>
         <p>Isolation: <strong>none</strong> (honest — in-process)</p>
         <p>Recovery: ${capabilities.recovery?.ready ? "ready" : mcEsc(capabilities.recovery?.hint || "review needed")} (${capabilities.recovery?.steps_done ?? 0}/${capabilities.recovery?.steps_total ?? 0})</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#capabilities" data-mc-nav="capabilities">Open Capabilities</a>
           <a class="ghost-btn small" href="/api/capabilities/product/diagnostics" target="_blank">Diagnostics</a>
           <a class="ghost-btn small" href="/api/capabilities/product/recovery" target="_blank">Recovery</a>
         </p>`
      )
    : "";
  const integrationsCard = integrations.product
    ? mcCard(
        "Integrations",
        `<p>State: <strong>${mcEsc(integrations.state || "idle")}</strong> · configured ${integrations.configured ?? 0}/${integrations.total ?? 0}</p>
         <p>Health ${mcBadge(!!integrations.healthy, "ready", "attention")} · failures ${integrations.failed ?? 0}</p>
         <p>Secrets: ${integrations.storage?.encrypted ? "encrypted" : "plaintext jarvis.env"}${integrations.storage?.world_readable ? " · ⚠ world-readable" : ""}</p>
         <p>Recovery: ${integrations.recovery?.ready ? "ready" : mcEsc(integrations.recovery?.hint || "review needed")} (${integrations.recovery?.steps_done ?? 0}/${integrations.recovery?.steps_total ?? 0})</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#integrations" data-mc-nav="integrations">Open Integrations</a>
           <a class="ghost-btn small" href="/api/integrations/product/diagnostics" target="_blank">Diagnostics</a>
           <a class="ghost-btn small" href="/api/integrations/product/recovery" target="_blank">Recovery</a>
         </p>`
      )
    : "";
  const searchCard = searchProduct.product
    ? mcCard(
        "Search",
        `<p>State: <strong>${mcEsc(searchProduct.state || "idle")}</strong> · corpora ${searchProduct.corpora_enabled ?? 0} · ${searchProduct.latency_ms ?? 0} ms</p>
         <p>Web: ${mcEsc(searchProduct.web_backend || "—")} ${mcBadge(!!searchProduct.web_ok, "ok", "down")} · index ${searchProduct.retrieval_available ?? 0}/${searchProduct.registry_sources ?? 0}</p>
         <p>Recovery: ${searchProduct.recovery?.ready ? "ready" : mcEsc(searchProduct.recovery?.hint || "review")} (${searchProduct.recovery?.steps_done ?? 0}/${searchProduct.recovery?.steps_total ?? 0})</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#search" data-mc-nav="search">Search Home</a>
           <a class="ghost-btn small" href="/api/search/product/diagnostics" target="_blank">Diagnostics</a>
           <a class="ghost-btn small" href="/api/search/product/recovery" target="_blank">Recovery</a>
         </p>`
      )
    : "";
  const settingsPrefsCard = settingsProduct.product
    ? mcCard(
        "Settings",
        `<p>Catalog <strong>${settingsProduct.catalog_count ?? 0}</strong> · stores ${settingsProduct.stores_present ?? 0}/${settingsProduct.stores_tracked ?? 0}</p>
         <p>Corrupt ${settingsProduct.corrupt_count ?? 0} · profile ${mcEsc(settingsProduct.active_profile || "default")}</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#settings" data-mc-nav="settings">Settings Home</a>
           <a class="ghost-btn small" href="/api/settings/product/diagnostics" target="_blank">Diagnostics</a>
         </p>`
      )
    : "";
  const homeCard = dashboardProduct.product
    ? mcCard(
        "Home",
        `<p>Widgets showing <strong>${dashboardProduct.widgets_showing ?? 0}</strong> / defs ${dashboardProduct.widget_defs ?? 0} · ${dashboardProduct.latency_ms ?? "—"} ms</p>
         <p>State ${mcEsc(dashboardProduct.state || "—")} · failures ${dashboardProduct.failures ?? 0}</p>
         <p class="muted tiny">${mcEsc(dashboardProduct.note || "Summary only — open Home for the glance surface.")}</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#dashboard" data-mc-nav="dashboard">Open Home</a>
           <a class="ghost-btn small" href="/api/dashboard/diagnostics" target="_blank">Diagnostics</a>
         </p>`
      )
    : "";
  const layoutsProduct = d.layouts || {};
  const layoutsCard = layoutsProduct.product
    ? mcCard(
        "Layouts",
        `<p>${mcEsc(layoutsProduct.detail || "")}</p>
         <p>Active ${mcEsc(layoutsProduct.active_layout || "—")} · restore ${layoutsProduct.restore_on_boot ? "on" : "off"} · failures ${layoutsProduct.failures ?? 0}</p>
         <p class="muted tiny">${mcEsc(layoutsProduct.note || "")}</p>
         <p class="mc-actions">
           <button type="button" class="ghost-btn small" id="mcOpenLayoutsBtn" onclick="window.AriaLayouts&amp;&amp;window.AriaLayouts.openModal()">Open Layouts</button>
           <a class="ghost-btn small" href="/api/layouts/diagnostics" target="_blank">Diagnostics</a>
         </p>`
      )
    : "";
  const notificationsProduct = d.notifications || {};
  const notificationsCard = notificationsProduct.product
    ? mcCard(
        "Notifications",
        `<p>${mcEsc(notificationsProduct.detail || "")}</p>
         <p>Unread proxy ${notificationsProduct.unread_proxy ?? "—"} · critical ${notificationsProduct.critical_proxy ?? 0} · ${notificationsProduct.enabled === false ? "disabled" : "enabled"}</p>
         <p class="muted tiny">${mcEsc(notificationsProduct.note || "")}</p>
         <p class="mc-actions">
           <button type="button" class="ghost-btn small" onclick="window.openNotifications&amp;&amp;window.openNotifications()">Open Notifications</button>
           <a class="ghost-btn small" href="/api/notifications/diagnostics" target="_blank">Diagnostics</a>
         </p>`
      )
    : "";
  const providerHealth = d.provider_health || {};
  const providerHealthCard = providerHealth.product
    ? mcCard(
        "Provider Health",
        `<p>State: <strong>${mcEsc(providerHealth.state || "unknown")}</strong> · score ${providerHealth.health_score ?? "—"}</p>
         <p>Provider: <strong>${mcEsc(providerHealth.provider || "—")}</strong> · model <code>${mcEsc(providerHealth.model || "—")}</code></p>
         <p>Connection ${mcEsc(providerHealth.connection || "—")} · GPU ${mcEsc(typeof providerHealth.gpu === "object" ? (providerHealth.gpu?.name || providerHealth.gpu?.model || "—") : (providerHealth.gpu || "—"))}</p>
         <p>Failure rate ${(providerHealth.failure_rate ?? 0) * 100}% · recoveries ${providerHealth.recovery_attempts ?? 0}</p>
         <p class="muted tiny">${mcEsc(providerHealth.last_error || providerHealth.note || "")}</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="/api/provider/diagnostics" target="_blank">Diagnostics</a>
           <a class="ghost-btn small" href="/api/provider/health" target="_blank">Health</a>
           <button type="button" class="ghost-btn small" data-mc-action="provider_recover">Recover</button>
         </p>`
      )
    : "";
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
      voiceCard,
      visionCard,
      flytyingCard,
      smarthomeCard,
      capabilitiesCard,
      integrationsCard,
      searchCard,
      settingsPrefsCard,
      homeCard,
      layoutsCard,
      notificationsCard,
      providerHealthCard,
    ].filter(Boolean))}
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
    mcCard("Retrieval / Knowledge Briefs", `<p>Provider: <strong>${mcEsc(k.retrieval)}</strong></p><p>Documents: ${k.documents ?? "—"}</p><p>Last sync: ${mcEsc(k.last_sync || "—")}</p><p class="muted tiny">This is Knowledge Briefs / retrieval — not Connections (graph).</p>`),
    mcCard("Sources", mcList([sources])),
  ]);
}

function renderDatabases(d) {
  const dbs = (d.databases || []).map((db) => `<li>${mcEsc(db.label || db.id)} ${mcBadge(db.running, "up", "down")} <span class="muted">${mcEsc(db.detail || "")}</span></li>`).join("");
  const svc = (d.services || []).map((s) => `<li>${mcEsc(s.label || s.id)} ${mcBadge(s.running, "up", "down")}</li>`).join("");
  const conn = d.connections || {};
  const connCard = mcCard(
    "Connections (Knowledge Graph)",
    `<p>Backend: <strong>${mcEsc(conn.backend || "—")}</strong> · ${mcEsc(conn.health || conn.status || "—")}</p>
     <p>Nodes: ${conn.node_count ?? "—"} · Relationships: ${conn.relationship_count ?? "—"}</p>
     <p>Namespaces: ${Array.isArray(conn.namespaces) ? conn.namespaces.length : (conn.namespaces ?? "—")}</p>
     <p>Last ingest: ${mcEsc((conn.last_ingest && (conn.last_ingest.at || conn.last_ingest.kind)) || "—")}</p>
     <p>Last cleanup: ${mcEsc((conn.last_cleanup && conn.last_cleanup.at) || "—")}</p>
     <p class="muted tiny">Storage: ${mcEsc(conn.storage || "—")}</p>
     <p class="muted tiny">Not Memory · Not Documents · ACM remains SoT</p>`
  );
  return mcGrid([mcCard("Databases", mcList([dbs])), mcCard("All services", mcList([svc])), connCard]);
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
    if (!events.length) {
      return `<p class='muted'>No activity recorded yet. <button type='button' class='ghost-btn tiny' id='mcEmptyActivityDashBtn'>Open Dashboard</button> or <button type='button' class='ghost-btn tiny' id='mcEmptyActivityChatBtn'>Chat</button> to generate events.</p>`;
    }    const rows = events
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
  const prefs = d.settings_product || {};
  const registry = s.intent_registry?.intents || [];
  const regRows = registry
    .map(
      (i) =>
        `<tr><td>${mcEsc(i.intent)}</td><td>${mcEsc(i.handler)}</td>` +
        `<td>${i.uses ?? 0}</td><td>${i.avg_confidence ?? "—"}</td>` +
        `<td>${i.success_rate ?? "—"}%</td></tr>`
    )
    .join("");
  const prefsCard = prefs.product
    ? mcCard(
        "Operator Settings (preferences)",
        `<p>Catalog <strong>${prefs.catalog_count ?? 0}</strong> · stores ${prefs.stores_present ?? 0}/${prefs.stores_tracked ?? 0} · corrupt ${prefs.corrupt_count ?? 0}</p>
         <p class="muted tiny">${mcEsc(prefs.runtime_config_note || "")}</p>
         <p class="mc-actions">
           <a class="ghost-btn small" href="#settings" data-mc-nav="settings">Settings Home</a>
           <a class="ghost-btn small" href="/api/settings/product/diagnostics" target="_blank">Diagnostics</a>
         </p>`
      )
    : "";
  return `
    <p class="muted">This tab is <strong>Runtime configuration</strong> (ops snapshot) — not the Settings preference editor. Use Settings Home for preferences.</p>
    ${prefsCard}
    ${mcGrid([
    mcCard("Platform runtime", `<pre class="mc-pre">${mcEsc(JSON.stringify(s, null, 2).slice(0, 1200))}</pre>`),
    mcCard(
      "Intent Registry",
      regRows
        ? `<table class="mc-table"><thead><tr><th>Intent</th><th>Handler</th><th>Uses</th><th>Confidence</th><th>Success</th></tr></thead><tbody>${regRows}</tbody></table>`
        : "<p class='muted'>No intent statistics yet. <button type='button' class='ghost-btn tiny' id='mcEmptyIntentChatBtn'>Ask Chat</button></p>"
    ),
  ])}`;
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
    return mcCard("Routing", "<p class='muted'>No routing records yet. <button type='button' class='ghost-btn tiny' id='mcEmptyRoutingChatBtn'>Ask Chat</button></p>");
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
        : "<p class='muted'>No analytics yet. <button type='button' class='ghost-btn tiny' id='mcEmptyAnalyticsChatBtn'>Ask Chat</button></p>"
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
      html = (window.renderConnection || renderConnection)(conn);
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
      html = (window.renderOverview || renderOverview)(_mcData);
      break;
    case "applications":
      html = (window.renderApplications || renderApplications)(_mcData);
      break;
    case "inference":
      html = (window.renderInference || renderInference)(_mcData);
      break;
    case "memory":
      html = (window.renderMemory || renderMemory)(_mcData);
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
      html = (window.renderJobs || renderJobs)(_mcData);
      break;
    case "activity":
      html = await (window.renderActivity || renderActivity)(_mcData);
      break;
    case "performance":
      html = (window.renderPerformance || renderPerformance)(_mcData);
      break;
    case "runtime_config":
    case "settings":
      html = renderSettings(_mcData);
      break;
    case "recovery":
      html = (window.renderRecovery || renderRecovery)(_mcData);
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
          if (document.hidden) return;
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
    if (e.target.closest?.("#mcEmptyActivityDashBtn")) {
      window.switchToView?.("dashboard");
      return;
    }
    if (e.target.closest?.("#mcEmptyActivityChatBtn")) {
      window.switchToView?.("chat");
      return;
    }
    if (e.target.closest?.("#mcEmptyIntentChatBtn")
        || e.target.closest?.("#mcEmptyRoutingChatBtn")
        || e.target.closest?.("#mcEmptyAnalyticsChatBtn")) {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.("Summarize Mission Control routing and intent health");
      return;
    }
    if (e.target.closest?.("#mcEmptyRecChatBtn")) {
      window.switchToView?.("chat");
      window.jarvisSendToChat?.("What should I focus on in Mission Control right now?");
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
        const out = await mcFetch("/api/mission-control/performance-lab/run", { method: "POST" });
        if (out.ok === false) throw new Error(out.error || out.message || "Benchmark failed");
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
  mcSyncGlobals();
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
    try {
      const conn = await mcFetch("/api/connections/health");
      _mcData.connections = conn;
    } catch (_) {
      _mcData.connections = { backend: "unavailable", health: "error", node_count: 0, relationship_count: 0 };
    }
    if (window._mcTab && window._mcTab !== _mcTab) _mcTab = window._mcTab;
    mcSyncGlobals();
    if (status) status.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    switchMcTab(_mcTab);
  } catch (e) {
    if (status) status.textContent = e.message;
  }
}

function initMissionControl() {
  if (window._mcTab) _mcTab = window._mcTab;
  const nav = mc$("mcTabNav");
  if (nav && !nav.dataset.wired) {
    nav.dataset.wired = "1";
    nav.innerHTML = MC_TABS.map((t) => {
      const label =
        t === "runtime_config"
          ? "Runtime config"
          : t === "intent_analytics"
            ? "Intent analytics"
            : t.charAt(0).toUpperCase() + t.slice(1).replace(/_/g, " ");
      return `<button type="button" class="mc-tab${t === _mcTab ? " active" : ""}" data-mc-tab="${t}">${label}</button>`;
    }).join("");
    nav.querySelectorAll(".mc-tab").forEach((btn) => {
      btn.addEventListener("click", () => switchMcTab(btn.dataset.mcTab));
    });
  }
  if (mc$("mcRefreshBtn") && !mc$("mcRefreshBtn").dataset.wired) {
    mc$("mcRefreshBtn").dataset.wired = "1";
    mc$("mcRefreshBtn").addEventListener("click", loadMissionControl);
  }
  if (mc$("mcOpenChatBtn") && !mc$("mcOpenChatBtn").dataset.wired) {
    mc$("mcOpenChatBtn").dataset.wired = "1";
    mc$("mcOpenChatBtn").addEventListener("click", () => window.switchToView?.("chat"));
  }
  if (mc$("mcOpenAuditBtn") && !mc$("mcOpenAuditBtn").dataset.wired) {
    mc$("mcOpenAuditBtn").dataset.wired = "1";
    mc$("mcOpenAuditBtn").addEventListener("click", () => window.switchToView?.("audit"));
  }
  if (mc$("mcOpenDashboardBtn") && !mc$("mcOpenDashboardBtn").dataset.wired) {
    mc$("mcOpenDashboardBtn").dataset.wired = "1";
    mc$("mcOpenDashboardBtn").addEventListener("click", () => window.switchToView?.("dashboard"));
  }
  loadMissionControl();
  if (_mcPoll) clearInterval(_mcPoll);
  _mcPoll = setInterval(() => {
    if (document.hidden) return;
    if (document.getElementById("workstationView")?.classList.contains("hidden")) return;
    loadMissionControl();
  }, 30000);
}

window.initWorkstation = initMissionControl;
window.initMissionControl = initMissionControl;
window.switchMcTab = switchMcTab;
window.loadMissionControl = loadMissionControl;
window.renderOverview = renderOverview;
window.renderJobs = renderJobs;
window.renderActivity = renderActivity;
window.renderInference = renderInference;
window.renderPerformance = renderPerformance;
window.renderRecovery = renderRecovery;
window.renderApplications = renderApplications;
window.renderMemory = renderMemory;
window.renderConnection = renderConnection;
window.renderMcTab = renderMcTab;
window.mcFetch = mcFetch;
window.mcCard = mcCard;
window.mcGrid = mcGrid;
window.mcBadge = mcBadge;
window.mcEsc = mcEsc;
window.renderRoutingOverviewCard = renderRoutingOverviewCard;
window.renderNotifications = renderNotifications;
window.renderOperationalAdvisor = renderOperationalAdvisor;

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
