/** Coding job polling — extracted from app.js. */
(function () {
  function escapeHtml(text) {
    if (typeof window.escapeHtml === "function") return window.escapeHtml(text);
    const d = document.createElement("div");
    d.textContent = text == null ? "" : String(text);
    return d.innerHTML;
  }

  // Coding jobs and background jobs (Learn topic, document summarize, …) share one worker
  // registry and one status endpoint — /api/coding/job/<id>. Only the surrounding copy
  // differs, so one poller serves both kinds.
  const JOB_KINDS = {
    coding_job: {
      prefix: "coding",
      statusClass: "coding-job-status",
      lostClass: "coding-job-lost",
      working: "Coding agent working…",
      failed: "Coding job failed",
      lost: "Coding job is no longer tracked by the server. Send the same request again to retry.",
      pollFailed: "Coding job polling failed",
      stopToast: "Coding job stop requested",
      stopError: "Could not stop coding job",
      notifyTitle: "Coding ready",
      notifyBody: "Proposal ready — Apply or Dismiss in chat",
      nativeResult: true,
    },
    background_job: {
      prefix: "background",
      statusClass: "background-job-status",
      lostClass: "background-job-lost",
      working: "Working…",
      failed: "Background job failed",
      lost: "This job is no longer tracked by the server. Check <strong>Job center</strong> for its status.",
      pollFailed: "Background job polling failed",
      stopToast: "Job stop requested",
      stopError: "Could not stop job",
      notifyTitle: "Result ready",
      notifyBody: "Your background job finished — see chat",
      nativeResult: false,
    },
  };

  async function pollCodingJob(jobId, messageEl, kind = "coding_job") {
    const cfg = JOB_KINDS[kind] || JOB_KINDS.coding_job;
    const trackKey = `${cfg.prefix}-${jobId}`;
    if (!window.activeMediaJobs) window.activeMediaJobs = new Set();
    if (!jobId || window.activeMediaJobs.has(trackKey)) return;
    window.activeMediaJobs.add(trackKey);

    const started = Date.now();
    const maxPollMs = 30 * 60 * 1000;
    const pollDelay = () => (window.isNativeApp?.() ? 3000 : 1500);

    const finishJob = () => {
      window.activeMediaJobs.delete(trackKey);
    };

    const tick = async () => {
      try {
        const res = await fetch(`/api/coding/job/${encodeURIComponent(jobId)}`);
        if (!res.ok) {
          if (res.status === 404 && Date.now() - started > 8000) {
            finishJob();
            const body = messageEl?.querySelector?.(".msg-body") || messageEl;
            if (body && !body.querySelector(`.${cfg.lostClass}`)) {
              body.insertAdjacentHTML(
                "beforeend",
                `<p class="warn ${cfg.lostClass}">${cfg.lost}</p>`,
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
          let note = body.querySelector(`.${cfg.statusClass}`);
          if (!note) {
            note = document.createElement("p");
            note.className = `${cfg.statusClass} muted`;
            body.appendChild(note);
          }
          note.textContent = data.message || cfg.working;
          if (data.steps?.length) {
            let stepsEl = body.querySelector(".coding-job-steps");
            if (!stepsEl) {
              stepsEl = document.createElement("ul");
              stepsEl.className = "coding-job-steps";
              body.appendChild(stepsEl);
            }
            stepsEl.innerHTML = data.steps.slice(-6).map((s) =>
              `<li>${escapeHtml(s.action)}: ${escapeHtml(s.detail || "")}</li>`,
            ).join("");
          }
          if (!body.querySelector(".coding-cancel-btn")) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "ghost-btn small coding-cancel-btn";
            btn.textContent = "Stop job";
            btn.addEventListener("click", () => {
              fetch(`/api/coding/job/${encodeURIComponent(jobId)}/cancel`, { method: "POST" })
                .then(async (r) => {
                  if (!r.ok) {
                    const err = await r.json().catch(() => ({}));
                    throw new Error(err.message || err.detail || `Cancel failed (${r.status})`);
                  }
                  window.showAriaToast?.(cfg.stopToast, "ok", 2500);
                })
                .catch((e) => {
                  window.showAriaToast?.(e.message || cfg.stopError, "err", 5000);
                });
            });
            body.appendChild(btn);
          }
        }
        if (data.done) {
          finishJob();
          if (data.result?.ok) {
            const prepare = (cfg.nativeResult && window.prepareNativeCodingResult) || ((r) => r);
            const result = prepare(data.result);
            const mountResult = () => {
              window.handleDone?.(result, result.message || "", false, {
                targetBody: body,
                replaceQueued: true,
              });
              if (window.isNativeApp?.() && window.jarvisNotify) {
                window.jarvisNotify(cfg.notifyTitle, cfg.notifyBody);
              }
            };
            if (cfg.nativeResult && window.isNativeApp?.()) {
              setTimeout(mountResult, 900);
            } else {
              mountResult();
            }
          } else if (body) {
            body.insertAdjacentHTML(
              "beforeend",
              `<p class="warn">${escapeHtml(data.error || data.result?.message || cfg.failed)}</p>`,
            );
          }
          return;
        }
        setTimeout(tick, pollDelay());
      } catch (err) {
        if (Date.now() - started < maxPollMs) {
          setTimeout(tick, pollDelay() + 500);
        } else {
          finishJob();
          window.showAriaToast?.(
            `${cfg.pollFailed}: ${err?.message || err}`,
            "err",
            5000,
          );
        }
      }
    };
    tick();
  }

  const pollBackgroundJob = (jobId, messageEl) => pollCodingJob(jobId, messageEl, "background_job");

  window.pollCodingJob = pollCodingJob;
  window.jarvisPollCodingJob = pollCodingJob;
  window.pollBackgroundJob = pollBackgroundJob;
  window.jarvisPollBackgroundJob = pollBackgroundJob;
})();
