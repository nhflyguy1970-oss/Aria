/** Specialist Team UI — propose → confirm → inspect (not CrewAI). */
(function () {
  "use strict";

  let lastProposal = null;
  let lastRun = null;

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

  function announce(msg) {
    const live = $("specLive");
    if (live) live.textContent = msg || "";
  }

  function ingestActivity(activity) {
    if (!activity) return;
    window.AriaActivity?.publish?.(activity);
  }

  function openPropose() {
    $("specProposeModal")?.classList.remove("hidden");
    $("specGoal")?.focus();
    announce("Propose specialist team");
  }

  async function openGallery() {
    const data = await api("/api/specialists/gallery");
    $("specGalleryList").innerHTML = (data.gallery || [])
      .map(
        (g) => `<div class="auto-row"><div><strong>${esc(g.name)}</strong>
        <span class="muted tiny"> · ${esc(g.id)} · ${g.read_only ? "read-only" : "write"}</span>
        <p class="muted tiny">${esc(g.description || "")}</p>
        <p class="muted tiny">Permissions: ${esc((g.permissions || []).join(", "))}</p></div></div>`,
      )
      .join("");
    $("specGalleryModal")?.classList.remove("hidden");
  }

  async function openHistory() {
    const data = await api("/api/specialists/runs?limit=20");
    $("specHistoryList").innerHTML = (data.runs || []).length
      ? data.runs
          .map(
            (r) => `<div class="auto-row"><div><strong>${esc((r.goal || "").slice(0, 80))}</strong>
        <span class="muted tiny"> · ${esc(r.status)} · ${esc(r.id)}</span></div>
        <button type="button" class="ghost-btn tiny" data-run="${esc(r.id)}">Inspect</button></div>`,
          )
          .join("")
      : `<p class="muted">No runs yet.</p>`;
    $("specHistoryModal")?.classList.remove("hidden");
  }

  function openRunInspector(run) {
    lastRun = run?.run || run;
    if (!lastRun) return;
    const r = lastRun;
    $("specRunTitle").textContent = `Specialist run: ${(r.goal || "").slice(0, 60)}`;
    $("specRunMeta").textContent = [
      `status=${r.status}`,
      `id=${r.id || r.run_id}`,
      `job=${r.job_id || "—"}`,
      `${r.elapsed_ms || 0}ms`,
      `team=${(r.team || []).join(",")}`,
    ].join(" · ");
    $("specRunSynthesis").textContent = r.synthesis || r.summary || "";
    $("specRunScratch").textContent = JSON.stringify(r.scratchpad || {}, null, 2);
    renderSteps();
    $("specRunModal")?.classList.remove("hidden");
    announce("Specialist run details opened");
  }

  function renderSteps() {
    const r = lastRun;
    if (!r) return;
    const q = ($("specRunFilter")?.value || "").toLowerCase();
    const rows = (r.steps || []).filter((s) => {
      if (!q) return true;
      return `${s.agent} ${s.message || ""} ${s.error || ""}`.toLowerCase().includes(q);
    });
    $("specRunSteps").innerHTML = rows
      .map((s) => {
        const cls = s.ok ? "auto-step-ok" : "auto-step-fail";
        return `<div class="auto-row ${cls}" tabindex="0" data-expand="1">
          <div><strong>${esc(s.name || s.agent)}</strong>
          <span class="muted tiny"> · ${esc(s.action || s.organ || "")} · ${s.ok ? "ok" : "fail"}
          ${s.recovered ? " · recovered" : ""} · ${esc(s.elapsed_ms || 0)}ms</span>
          <div class="auto-step-detail"><pre>${esc(s.message || s.error || JSON.stringify(s.data || {}, null, 2))}</pre></div>
          </div></div>`;
      })
      .join("") || `<p class="muted">No steps.</p>`;
  }

  async function doPropose() {
    const goal = $("specGoal")?.value || "";
    const data = await api("/api/specialists/propose", {
      method: "POST",
      body: JSON.stringify({ goal, use_llm: !!$("specUseLlm")?.checked }),
    });
    lastProposal = data;
    $("specProposalPreview").textContent =
      `Team: ${(data.team || []).join(", ")}\n${data.reasoning || ""}\n${data.expected_output || ""}`;
    $("specConfirmBtn").disabled = !data.ok;
    announce("Team proposed — confirm to run");
  }

  async function doConfirmRun() {
    if (!lastProposal) return;
    if (!window.confirm?.("Run this specialist team? Write specialists need approval if enabled.")) return;
    const goal = $("specGoal")?.value || lastProposal.goal;
    const data = await api("/api/specialists/run", {
      method: "POST",
      body: JSON.stringify({
        goal,
        specialists: lastProposal.team,
        confirm: true,
        approve_writes: !!$("specApproveWrites")?.checked,
        parallel_readers: !!$("specParallel")?.checked,
        critic_loop: !!$("specCritic")?.checked,
      }),
    });
    ingestActivity(data.activity);
    $("specProposeModal")?.classList.add("hidden");
    openRunInspector(data);
    window.showAriaToast?.(`Specialists: ${data.status}`, data.ok ? "ok" : "err", 3500);
  }

  function bind() {
    $("specProposeBtn")?.addEventListener("click", openPropose);
    $("specCardProposeBtn")?.addEventListener("click", openPropose);
    $("specGalleryBtn")?.addEventListener("click", () => openGallery().catch((e) => window.showAriaToast?.(e.message, "err")));
    $("specCardGalleryBtn")?.addEventListener("click", () => openGallery().catch((e) => window.showAriaToast?.(e.message, "err")));
    $("specHistoryBtn")?.addEventListener("click", () => openHistory().catch((e) => window.showAriaToast?.(e.message, "err")));
    $("specCardHistoryBtn")?.addEventListener("click", () => openHistory().catch((e) => window.showAriaToast?.(e.message, "err")));
    $("specDraftBtn")?.addEventListener("click", () => doPropose().catch((e) => window.showAriaToast?.(e.message, "err")));
    $("specConfirmBtn")?.addEventListener("click", () => doConfirmRun().catch((e) => window.showAriaToast?.(e.message, "err")));
    $("specProposeCloseBtn")?.addEventListener("click", () => $("specProposeModal")?.classList.add("hidden"));
    $("specGalleryCloseBtn")?.addEventListener("click", () => $("specGalleryModal")?.classList.add("hidden"));
    $("specHistoryCloseBtn")?.addEventListener("click", () => $("specHistoryModal")?.classList.add("hidden"));
    $("specRunCloseBtn")?.addEventListener("click", () => $("specRunModal")?.classList.add("hidden"));
    $("specRunFilter")?.addEventListener("input", renderSteps);
    $("specRunSteps")?.addEventListener("click", (ev) => {
      const row = ev.target.closest(".auto-row[data-expand]");
      if (row) row.classList.toggle("is-open");
    });
    $("specHistoryList")?.addEventListener("click", async (ev) => {
      const btn = ev.target.closest("[data-run]");
      if (!btn) return;
      const data = await api(`/api/specialists/runs/${encodeURIComponent(btn.dataset.run)}`);
      openRunInspector(data.run || data);
    });
    $("specRunJobsBtn")?.addEventListener("click", () => {
      $("specRunModal")?.classList.add("hidden");
      window.switchToView?.("jobs");
    });
    $("specRunActivityBtn")?.addEventListener("click", () => window.AriaActivity?.open?.());
    $("specRunExportBtn")?.addEventListener("click", async () => {
      if (!lastRun) return;
      await window.ariaCopy(JSON.stringify(lastRun, null, 2), 'run');
      window.showAriaToast?.("Run exported to clipboard", "ok", 2000);
    });
  }

  window.AriaSpecialists = {
    openPropose,
    openGallery,
    openHistory,
    openRunInspector,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();
})();
