/** Workstation operational dashboard — live runtime visibility (not chat). */

function ws$(id) {
  return document.getElementById(id);
}

async function wsFetch(url, opts = {}) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || data.detail || res.statusText);
  return data;
}

function wsEsc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/"/g, "&quot;");
}

function wsBadge(ok, labelUp, labelDown) {
  const cls = ok ? "ws-badge ws-badge--ok" : "ws-badge ws-badge--down";
  return `<span class="${cls}">${wsEsc(ok ? labelUp : labelDown)}</span>`;
}

function wsCard(title, body) {
  return `<section class="ws-card"><h3>${wsEsc(title)}</h3>${body}</section>`;
}

function renderWorkstationDashboard(data) {
  const root = ws$("workstationDashboardBody");
  if (!root) return;
  const rt = data.runtime || {};
  const inf = data.inference || {};
  const mem = data.memory || {};
  const know = data.knowledge || {};
  const hw = data.hardware || {};
  const gpu = hw.gpu || {};
  const res = hw.resources || {};
  const health = data.health || {};
  const acc = health.acceptance || {};
  const git = data.git || {};
  const jobs = (data.infrastructure || {}).jobs || {};

  const apps = (data.applications || [])
    .map(
      (a) =>
        `<li>${wsEsc(a.label || a.id)} ${wsBadge(a.healthy, "healthy", "down")} ${a.attached ? wsBadge(true, "attached", "") : ""}</li>`
    )
    .join("");

  const services = (data.services || [])
    .map((s) => `<li>${wsEsc(s.label || s.id)} ${wsBadge(s.running, "up", "down")}</li>`)
    .join("");

  const dbs = (data.databases || [])
    .map((d) => `<li>${wsEsc(d.label || d.id)} ${wsBadge(d.running, "up", "down")}</li>`)
    .join("");

  const providers = Object.entries(data.providers || {})
    .filter(([, v]) => v && typeof v === "object")
    .map(([name, info]) => {
      const src = info.source || (info.platform_attached ? "platform" : "local");
      return `<li><strong>${wsEsc(name)}</strong> — ${wsEsc(src)}</li>`;
    })
    .join("");

  const ns = Object.entries(mem.namespaces || {})
    .map(([n, c]) => `${wsEsc(n)} (${c})`)
    .join(", ");

  root.innerHTML = `
    <div class="ws-summary-bar">
      <span><strong>${wsEsc(rt.mode || "?")}</strong></span>
      <span>Phase: ${wsEsc((rt.phase || {}).phase || "?")}</span>
      <span>Acceptance: ${acc.overall != null ? acc.overall + "%" : "—"}</span>
      <span>Services: ${wsBadge(data.services_ready, "Healthy", "Degraded")}</span>
    </div>
    <div class="ws-grid">
      ${wsCard(
        "Runtime",
        `<p><strong>Mode</strong> ${wsEsc(rt.mode)} · <strong>Phase</strong> ${wsEsc((rt.phase || {}).phase || "?")}</p>
         <p class="muted">${wsEsc((rt.phase || {}).detail || "")}</p>
         <p>Platform: ${wsBadge((rt.host || {}).attached, "Attached", "Standalone")}</p>`
      )}
      ${wsCard(
        "Inference",
        `<p><strong>General</strong> <code>${wsEsc(inf.general || "—")}</code></p>
         <p><strong>Coder</strong> <code>${wsEsc(inf.coder || "—")}</code></p>
         <p>Ollama ${wsBadge(inf.ollama_running, "running", "stopped")}</p>`
      )}
      ${wsCard(
        "Memory",
        `<p>Provider: <strong>${wsEsc(mem.provider || "local")}</strong></p>
         <p>Entries: ${mem.entry_count ?? "—"} · Semantic: ${mem.semantic_vectors ?? "—"}</p>
         <p class="muted">${ns || "No namespaces"}</p>`
      )}
      ${wsCard(
        "Knowledge",
        `<p>Retrieval: <strong>${wsEsc(know.retrieval || "local")}</strong></p>
         <p>Documents: ${know.documents ?? "—"}</p>`
      )}
      ${wsCard("Applications", `<ul class="ws-list">${apps || "<li class='muted'>None</li>"}</ul>`)}
      ${wsCard("Services", `<ul class="ws-list">${services || "<li class='muted'>—</li>"}</ul>`)}
      ${wsCard("Databases", `<ul class="ws-list">${dbs || "<li class='muted'>—</li>"}</ul>`)}
      ${wsCard("Providers", `<ul class="ws-list">${providers || "<li class='muted'>—</li>"}</ul>`)}
      ${wsCard(
        "Hardware",
        `<p><strong>GPU</strong> ${wsEsc(gpu.name || "—")} · ${wsEsc(gpu.vram_gb != null ? gpu.vram_gb + " GB VRAM" : "")}</p>
         <p>RAM free: ${wsEsc(res.ram_free_gb != null ? res.ram_free_gb + " GB" : "—")}</p>`
      )}
      ${wsCard(
        "Health",
        `<p>Acceptance: <strong>${acc.overall != null ? acc.overall + "%" : "—"}</strong></p>
         <p>Production readiness: ${acc.production_readiness != null ? acc.production_readiness + "%" : "—"}</p>
         <p>Services ${wsBadge(data.services_ready, "ready", "degraded")}</p>`
      )}
      ${wsCard(
        "Git",
        `<p>Aria: <code>${wsEsc(git.aria_branch || "?")}</code>${git.aria_dirty ? " (dirty)" : ""}</p>
         <p>Project: ${wsEsc(git.current_project || "—")}</p>`
      )}
      ${wsCard(
        "Background jobs",
        `<p>Active: ${jobs.active_count ?? jobs.busy_count ?? 0}</p>`
      )}
    </div>
  `;
}

function renderActivityEvents(events) {
  const el = ws$("workstationActivityList");
  if (!el) return;
  if (!events.length) {
    el.innerHTML = "<li class='muted'>No recent activity</li>";
    return;
  }
  el.innerHTML = events
    .map((ev) => {
      const dur = ev.duration_ms != null ? ` · ${ev.duration_ms}ms` : "";
      return `<li class="ws-activity-item ws-activity--${wsEsc(ev.status || "ok")}">
        <span class="ws-activity-ts">${wsEsc(ev.iso || "")}</span>
        <strong>${wsEsc(ev.type)}</strong>
        <span class="muted">${wsEsc(ev.component)}</span>
        <span>${wsEsc(ev.detail)}${dur}</span>
      </li>`;
    })
    .join("");
}

async function loadWorkstationActivity() {
  const q = ws$("workstationActivityQuery")?.value?.trim() || "";
  const comp = ws$("workstationActivityComponent")?.value?.trim() || "";
  const params = new URLSearchParams({ limit: "60" });
  if (q) params.set("q", q);
  if (comp) params.set("component", comp);
  try {
    const data = await wsFetch(`/api/workstation/activity?${params}`);
    renderActivityEvents(data.events || []);
  } catch (e) {
    const el = ws$("workstationActivityList");
    if (el) el.innerHTML = `<li class="muted">${wsEsc(e.message)}</li>`;
  }
}

async function loadWorkstationDashboard() {
  const status = ws$("workstationLoadStatus");
  if (status) status.textContent = "Refreshing…";
  try {
    const data = await wsFetch("/api/workstation/dashboard");
    renderWorkstationDashboard(data);
    if (status) status.textContent = `Updated ${new Date().toLocaleTimeString()}`;
    await loadWorkstationActivity();
  } catch (e) {
    if (status) status.textContent = e.message;
  }
}

function initWorkstationDashboard() {
  loadWorkstationDashboard();
  ws$("workstationRefreshBtn")?.addEventListener("click", loadWorkstationDashboard);
  ws$("workstationActivityFilterBtn")?.addEventListener("click", loadWorkstationActivity);
  ws$("workstationRepairBtn")?.addEventListener("click", async () => {
    try {
      await wsFetch("/api/workstation/recover", { method: "POST" });
      window.showAriaToast?.("Repair started", "ok");
      loadWorkstationDashboard();
    } catch (e) {
      window.showAriaToast?.(e.message, "err");
    }
  });
}

window.initWorkstation = initWorkstationDashboard;
window.loadWorkstationDashboard = loadWorkstationDashboard;

// Sidebar workstation menu shortcuts
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-ws-nav]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.wsNav;
      if (target === "chat-status") {
        window.switchToView?.("chat");
        if (typeof window.sendMessage === "function") window.sendMessage("status");
        return;
      }
      window.switchToView?.("workstation");
      if (target && target !== "workstation") {
        setTimeout(() => {
          const el = ws$(target);
          el?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 200);
      }
    });
  });
});
