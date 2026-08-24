/** Media job tracking, resume, and polling — extracted from app.js. */
(function () {
  const activeMediaJobs = new Set();
  const MEDIA_JOBS_STORAGE_KEY = "jarvisActiveMediaJobs";
  const MEDIA_SHOWN_STORAGE_KEY = "jarvisShownMediaJobs";
  let mediaJobsResumeStarted = false;

  window.activeMediaJobs = activeMediaJobs;

  function escapeHtml(text) {
    if (typeof window.escapeHtml === "function") return window.escapeHtml(text);
    const d = document.createElement("div");
    d.textContent = text == null ? "" : String(text);
    return d.innerHTML;
  }

  function syncBusy() {
    if (typeof window.syncMediaBusyClass === "function") window.syncMediaBusyClass();
    else {
      document.documentElement.classList.toggle("media-busy", activeMediaJobs.size > 0);
    }
  }

  function markMediaJobShown(jobId) {
    if (!jobId) return;
    try {
      const ids = JSON.parse(sessionStorage.getItem(MEDIA_SHOWN_STORAGE_KEY) || "[]");
      if (!ids.includes(jobId)) {
        ids.push(jobId);
        sessionStorage.setItem(MEDIA_SHOWN_STORAGE_KEY, JSON.stringify(ids.slice(-24)));
      }
    } catch (_) {}
  }

  function wasMediaJobShown(jobId) {
    if (!jobId) return false;
    try {
      return JSON.parse(sessionStorage.getItem(MEDIA_SHOWN_STORAGE_KEY) || "[]").includes(jobId);
    } catch (_) {
      return false;
    }
  }

  function trackMediaJob(jobId) {
    if (!jobId) return;
    try {
      const ids = JSON.parse(sessionStorage.getItem(MEDIA_JOBS_STORAGE_KEY) || "[]");
      if (!ids.includes(jobId)) {
        ids.push(jobId);
        sessionStorage.setItem(MEDIA_JOBS_STORAGE_KEY, JSON.stringify(ids.slice(-12)));
      }
    } catch (_) {}
  }

  function untrackMediaJob(jobId) {
    if (!jobId) return;
    try {
      const ids = JSON.parse(sessionStorage.getItem(MEDIA_JOBS_STORAGE_KEY) || "[]").filter((id) => id !== jobId);
      sessionStorage.setItem(MEDIA_JOBS_STORAGE_KEY, JSON.stringify(ids));
    } catch (_) {}
  }

  async function resumePendingMediaJobs() {
    if (mediaJobsResumeStarted) return;
    mediaJobsResumeStarted = true;
    const ids = new Set();
    try {
      JSON.parse(sessionStorage.getItem(MEDIA_JOBS_STORAGE_KEY) || "[]").forEach((id) => ids.add(id));
    } catch (_) {}
    try {
      const res = await fetch("/api/media/status");
      if (res.ok) {
        const data = await res.json();
        if (data.busy && data.job_id) ids.add(data.job_id);
        for (const job of data.recent || []) {
          if (job?.id && !job.done) ids.add(job.id);
        }
      }
    } catch (e) {
      window.showAriaToast?.(
        `Could not resume media jobs: ${e?.message || e}`,
        "err",
        4000,
      );
    }
    for (const jobId of ids) {
      if (!jobId || activeMediaJobs.has(jobId)) continue;
      try {
        const res = await fetch(`/api/media/job/${encodeURIComponent(jobId)}`);
        if (!res.ok) {
          untrackMediaJob(jobId);
          continue;
        }
        const data = await res.json();
        if (!data.ok) continue;
        if (data.done && data.result?.ok) {
          if (wasMediaJobShown(jobId)) {
            untrackMediaJob(jobId);
            continue;
          }
          markMediaJobShown(jobId);
          untrackMediaJob(jobId);
          const { body } = window.addMessage?.("assistant", data.result.message || "Image ready", {
            module: data.result.module || "image",
            type: "media_job",
          }) || {};
          window.handleDone?.(data.result, data.result.message || "", false, {
            targetBody: body,
            replaceQueued: true,
          });
          continue;
        }
        if (data.done) {
          untrackMediaJob(jobId);
          continue;
        }
        const { body } = window.addMessage?.("assistant", data.message || "Image job running…", {
          module: "image",
          type: "media_job",
        }) || {};
        pollMediaJob(jobId, body?.closest?.(".message"));
      } catch (err) {
        window.showAriaToast?.(
          `Media job resume failed: ${err?.message || err}`,
          "err",
          4000,
        );
      }
    }
  }

  async function pollMediaJob(jobId, messageEl) {
    if (!jobId || activeMediaJobs.has(jobId)) return;
    activeMediaJobs.add(jobId);
    syncBusy();
    trackMediaJob(jobId);
    const started = Date.now();
    const maxPollMs = 10 * 60 * 1000;
    const pollDelay = () => (window.isNativeApp?.() ? 5000 : 2200);

    const finishJob = () => {
      activeMediaJobs.delete(jobId);
      syncBusy();
      untrackMediaJob(jobId);
    };

    const tick = async () => {
      try {
        const res = await fetch(`/api/media/job/${encodeURIComponent(jobId)}`);
        if (!res.ok) {
          if (res.status === 404 && Date.now() - started > 8000) {
            finishJob();
            // A 404 here only means this id is not in the media registry. It is not
            // evidence of a server restart, so do not claim one.
            const body = messageEl?.querySelector?.(".msg-body") || messageEl;
            if (body && !body.querySelector(".media-job-lost")) {
              body.insertAdjacentHTML(
                "beforeend",
                '<p class="warn media-job-lost">This media job is no longer tracked by the server. '
                + 'If it finished, the result will be in <strong>Gallery</strong>.</p>',
              );
            }
            return;
          }
          if (Date.now() - started < maxPollMs) {
            setTimeout(tick, pollDelay());
            return;
          }
          finishJob();
          return;
        }
        const data = await res.json();
        if (!data.ok) {
          if (Date.now() - started < maxPollMs) {
            setTimeout(tick, pollDelay());
            return;
          }
          finishJob();
          return;
        }
        const body = messageEl?.querySelector?.(".msg-body") || messageEl;
        if (body) {
          let note = body.querySelector(".media-job-status");
          if (!note) {
            note = document.createElement("p");
            note.className = "media-job-status muted";
            body.appendChild(note);
          }
          note.textContent = data.message || "Working…";
        }
        if (data.done) {
          finishJob();
          if (data.result?.ok) {
            markMediaJobShown(jobId);
            window.handleDone?.(data.result, data.result.message || "", false, {
              targetBody: body,
              replaceQueued: true,
            });
          } else if (body) {
            body.insertAdjacentHTML(
              "beforeend",
              `<p class="warn">${escapeHtml(data.error || data.result?.message || "Media job failed")}</p>`,
            );
          }
          return;
        }
        setTimeout(tick, pollDelay());
      } catch (err) {
        if (Date.now() - started < maxPollMs) setTimeout(tick, pollDelay());
        else {
          finishJob();
          window.showAriaToast?.(
            `Media job polling failed: ${err?.message || err}`,
            "err",
            5000,
          );
        }
      }
    };
    tick();
  }

  Object.assign(window, {
    markMediaJobShown,
    wasMediaJobShown,
    trackMediaJob,
    untrackMediaJob,
    resumePendingMediaJobs,
    pollMediaJob,
  });
})();
