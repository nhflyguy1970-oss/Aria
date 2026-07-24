/** Coding job polling — extracted from app.js. */
(function () {
  function escapeHtml(text) {
    if (typeof window.escapeHtml === "function") return window.escapeHtml(text);
    const d = document.createElement("div");
    d.textContent = text == null ? "" : String(text);
    return d.innerHTML;
  }

  async function pollCodingJob(jobId, messageEl) {
    if (!window.activeMediaJobs) window.activeMediaJobs = new Set();
    if (!jobId || window.activeMediaJobs.has(`coding-${jobId}`)) return;
    window.activeMediaJobs.add(`coding-${jobId}`);

    const started = Date.now();
    const maxPollMs = 30 * 60 * 1000;
    const pollDelay = () => (window.isNativeApp?.() ? 3000 : 1500);

    const finishJob = () => {
      window.activeMediaJobs.delete(`coding-${jobId}`);
    };

    const tick = async () => {
      try {
        const res = await fetch(`/api/coding/job/${encodeURIComponent(jobId)}`);
        if (!res.ok) {
          if (res.status === 404 && Date.now() - started > 8000) {
            finishJob();
            const body = messageEl?.querySelector?.(".msg-body") || messageEl;
            if (body && !body.querySelector(".coding-job-lost")) {
              body.insertAdjacentHTML(
                "beforeend",
                "<p class=\"warn coding-job-lost\">Coding job was interrupted by a server restart. "
                + "Send the same request again to retry.</p>",
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
          let note = body.querySelector(".coding-job-status");
          if (!note) {
            note = document.createElement("p");
            note.className = "coding-job-status muted";
            body.appendChild(note);
          }
          note.textContent = data.message || "Coding agent working…";
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
                  window.showAriaToast?.("Coding job stop requested", "ok", 2500);
                })
                .catch((e) => {
                  window.showAriaToast?.(e.message || "Could not stop coding job", "err", 5000);
                });
            });
            body.appendChild(btn);
          }
        }
        if (data.done) {
          finishJob();
          if (data.result?.ok) {
            const prepare = window.prepareNativeCodingResult || ((r) => r);
            const result = prepare(data.result);
            const mountResult = () => {
              window.handleDone?.(result, result.message || "", false, {
                targetBody: body,
                replaceQueued: true,
              });
              if (window.isNativeApp?.() && window.jarvisNotify) {
                window.jarvisNotify("Coding ready", "Proposal ready — Apply or Dismiss in chat");
              }
            };
            if (window.isNativeApp?.()) {
              setTimeout(mountResult, 900);
            } else {
              mountResult();
            }
          } else if (body) {
            body.insertAdjacentHTML(
              "beforeend",
              `<p class="warn">${escapeHtml(data.error || data.result?.message || "Coding job failed")}</p>`,
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
            `Coding job polling failed: ${err?.message || err}`,
            "err",
            5000,
          );
        }
      }
    };
    tick();
  }

  window.pollCodingJob = pollCodingJob;
  window.jarvisPollCodingJob = pollCodingJob;
})();
