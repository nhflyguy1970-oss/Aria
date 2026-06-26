/** Job center UI (Phase 3 ES module). */

import { escapeHtml, $ } from "./util.mjs";

let jobCenterPollTimer = null;

export async function cancelJobByQueue(queue, jobId) {
  const paths = {
    media: `/api/media/job/${encodeURIComponent(jobId)}/cancel`,
    coding: `/api/coding/job/${encodeURIComponent(jobId)}/cancel`,
    audio: `/api/audio/job/${encodeURIComponent(jobId)}/cancel`,
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
    if (!job.done && job.id) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn tiny";
      btn.textContent = "Cancel";
      btn.addEventListener("click", async () => {
        await cancelJobByQueue(job.queue, job.id);
        await refreshJobCenter();
      });
      li.appendChild(document.createElement("br"));
      li.appendChild(btn);
    }
    jobCenterList.appendChild(li);
  }
  if (!(data.recent || []).length) {
    jobCenterList.innerHTML = '<li class="muted">No recent jobs.</li>';
  }
}

export async function refreshJobCenter() {
  const jobCenterSummary = $("jobCenterSummary");
  try {
    const res = await fetch("/api/jobs");
    if (!res.ok) return;
    renderJobCenter(await res.json());
  } catch (_) {
    if (jobCenterSummary) jobCenterSummary.textContent = "Could not load jobs.";
  }
}

export function openJobCenter() {
  const jobCenterModal = $("jobCenterModal");
  if (!jobCenterModal) return;
  jobCenterModal.classList.remove("hidden");
  refreshJobCenter();
  if (jobCenterPollTimer) clearInterval(jobCenterPollTimer);
  jobCenterPollTimer = setInterval(refreshJobCenter, 8000);
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
  $("jobCenterBtn")?.addEventListener("click", openJobCenter);
  $("jobCenterCloseBtn")?.addEventListener("click", closeJobCenter);
  $("jobCenterRefreshBtn")?.addEventListener("click", refreshJobCenter);
  $("jobCenterModal")?.addEventListener("click", (e) => {
    if (e.target?.id === "jobCenterModal") closeJobCenter();
  });
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
  openJobCenter,
  closeJobCenter,
};
