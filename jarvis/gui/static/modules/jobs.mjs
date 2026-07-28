/** Job center UI (Phase 3 ES module). */

import { escapeHtml, $ } from "./util.mjs";

let jobCenterPollTimer = null;

export function updateJobCenterBadge(data) {
  const badge = $("jobCenterBadge");
  const svcBtn = $("jobCenterServicesBtn");
  const dot = $("jobCenterSvcDot");
  if (!badge || !svcBtn) return;
  const busy = Boolean(data?.any_busy);
  svcBtn.classList.toggle("busy", busy);
  if (dot) dot.classList.toggle("online", busy);
  if (busy) {
    badge.textContent = "running";
    badge.classList.remove("hidden");
  } else {
    badge.textContent = "";
    badge.classList.add("hidden");
  }
}

export async function refreshJobCenterBadge() {
  try {
    const res = await fetch("/api/jobs");
    if (!res.ok) return;
    updateJobCenterBadge(await res.json());
  } catch {
    /* ignore */
  }
}

export async function cancelJobByQueue(queue, jobId) {
  const paths = {
    media: `/api/media/job/${encodeURIComponent(jobId)}/cancel`,
    coding: `/api/coding/job/${encodeURIComponent(jobId)}/cancel`,
    audio: `/api/audio/job/${encodeURIComponent(jobId)}/cancel`,
    specialists: `/api/specialists/jobs/${encodeURIComponent(jobId)}/cancel`,
    agent: `/api/specialists/jobs/${encodeURIComponent(jobId)}/cancel`,
  };
  const url = paths[queue];
  if (!url) return false;
  const res = await fetch(url, { method: "POST" });
  return res.ok;
}

export function renderJobCenter(data) {
  const jobCenterSummary = $("jobCenterSummary");
  const jobCenterList = $("jobCenterList");
  if (!jobCenterSummary || !jobCenterList) return;
  const media = data.media || {};
  const coding = data.coding || {};
  const audio = data.audio || {};
  const parts = [];
  if (media.busy || media.pending) {
    parts.push(`Media: ${media.label || media.active_label || "busy"} (${media.pending || 0} queued)`);
  }
  if (coding.busy || coding.pending) {
    parts.push(`Coding: ${coding.pending || 0} queued`);
  }
  if (audio.busy || audio.active_count) {
    parts.push(`Audio: ${audio.active_count || 0} active`);
  }
  const specialists = data.specialist_jobs || [];
  const agents = data.agent_jobs || [];
  const teamBusy = specialists.some((j) => !j.done) || agents.some((j) => !j.done);
  if (teamBusy) {
    parts.push(`Specialists: running`);
  }
  jobCenterSummary.textContent = parts.length
    ? parts.join(" · ")
    : (data.any_busy ? "Working…" : "No background jobs running.");
  jobCenterList.innerHTML = "";
  for (const job of data.recent || []) {
    const li = document.createElement("li");
    li.className = "job-center-item";
    if (!job.done) li.classList.add("running");
    else if (job.error) li.classList.add("done-err");
    else li.classList.add("done-ok");
    const pct = job.done ? 100 : (job.pct || 0);
    li.innerHTML = `<strong>[${escapeHtml(job.queue)}]</strong> ${escapeHtml(job.label || job.id)}<br>`
      + `<span class="muted">${escapeHtml(job.message || "")}</span> · ${pct}%`;
    if (job.queue === "coding") {
      const links = document.createElement("div");
      links.className = "job-coding-links";
      const add = (label, fn) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "ghost-btn tiny";
        b.textContent = label;
        b.addEventListener("click", fn);
        links.appendChild(b);
      };
      add("Coding Home", () => {
        closeJobCenter();
        window.openCodingHome?.("jobs");
      });
      if (job.proposal_id) {
        add("Proposal", () => {
          closeJobCenter();
          window.openCodingHome?.("proposals");
          setTimeout(() => window.showAriaToast?.(`Proposal ${job.proposal_id}`, "ok", 3000), 200);
        });
      }
      add("Chat", () => {
        closeJobCenter();
        window.switchToView?.("chat");
      });
      add("Verify", () => {
        closeJobCenter();
        window.AriaCodingVerify?.promptLast?.();
      });
      add("Undo", async () => {
        try {
          const res = await fetch("/api/undo-apply", { method: "POST" });
          const data = await res.json().catch(() => ({}));
          window.showAriaToast?.(data.message || (res.ok ? "Undone" : "Undo failed"), res.ok ? "ok" : "err", 3500);
        } catch (err) {
          window.showAriaToast?.(err?.message || "Undo failed", "err", 4000);
        }
      });
      add("Project", () => {
        closeJobCenter();
        window.switchToView?.("projects");
      });
      li.appendChild(links);
    }
    if (!job.done && job.id) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn tiny";
      btn.textContent = "Cancel";
      btn.addEventListener("click", async () => {
        try {
          const ok = await cancelJobByQueue(job.queue, job.id);
          if (ok === false) window.showAriaToast?.("Cancel failed — job may have finished", "err", 4000);
          else window.showAriaToast?.("Cancel requested", "ok", 2500);
        } catch (err) {
          window.showAriaToast?.(err?.message || "Cancel failed", "err", 4000);
        }
        await refreshJobCenter();
      });
      li.appendChild(document.createElement("br"));
      li.appendChild(btn);
    }
    jobCenterList.appendChild(li);
  }
  if (!(data.recent || []).length) {
    jobCenterList.innerHTML = '<li class="muted">No recent jobs. <button type="button" class="ghost-btn tiny" id="jobsEmptyChatBtn">Ask Chat</button></li>';
    jobCenterList.querySelector("#jobsEmptyChatBtn")?.addEventListener("click", () => {
      closeJobCenter();
      window.switchToView?.("chat");
    });
  }
  updateJobCenterBadge(data);
}

export async function refreshJobCenter() {
  const jobCenterSummary = $("jobCenterSummary");
  try {
    const res = await fetch("/api/jobs");
    if (!res.ok) {
      if (jobCenterSummary) jobCenterSummary.textContent = `Could not load jobs (${res.status}).`;
      window.showAriaToast?.(`Job center unavailable (${res.status})`, "err", 4000);
      return;
    }
    renderJobCenter(await res.json());
  } catch (err) {
    if (jobCenterSummary) jobCenterSummary.textContent = "Could not load jobs.";
    window.showAriaToast?.(err?.message || "Could not load jobs", "err", 4000);
  }
}

export function openJobCenter() {
  const jobCenterModal = $("jobCenterModal");
  if (!jobCenterModal) return;
  jobCenterModal.classList.remove("hidden");
  refreshJobCenter();
  if (jobCenterPollTimer) clearInterval(jobCenterPollTimer);
  jobCenterPollTimer = setInterval(() => {
    if (document.hidden) return;
    refreshJobCenter();
  }, 8000);
}

export function closeJobCenter() {
  const jobCenterModal = $("jobCenterModal");
  jobCenterModal?.classList.add("hidden");
  if (jobCenterPollTimer) {
    clearInterval(jobCenterPollTimer);
    jobCenterPollTimer = null;
  }
}

function initJobCenter() {
  const open = () => openJobCenter();
  $("jobCenterBtn")?.addEventListener("click", open);
  $("jobCenterServicesBtn")?.addEventListener("click", open);
  $("knowledgeResearchJobsBtn")?.addEventListener("click", open);
  $("jobCenterCloseBtn")?.addEventListener("click", closeJobCenter);
  $("jobCenterRefreshBtn")?.addEventListener("click", refreshJobCenter);
  $("jobCenterModal")?.addEventListener("click", (e) => {
    if (e.target?.id === "jobCenterModal") closeJobCenter();
  });
  refreshJobCenterBadge();
  setInterval(() => {
    if (document.hidden) return;
    refreshJobCenterBadge();
  }, 15000);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initJobCenter);
} else {
  initJobCenter();
}

window.jarvisJobs = {
  cancelJobByQueue,
  renderJobCenter,
  refreshJobCenter,
  refreshJobCenterBadge,
  updateJobCenterBadge,
  openJobCenter,
  closeJobCenter,
};
