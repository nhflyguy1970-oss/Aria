/** Certification Dashboard — evidence-driven release readiness. */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  let pollTimer = null;
  let activeRunId = null;
  const consoleBuf = [];

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function gateBadge(gate) {
    const g = String(gate || "NO_RUN");
    if (g === "READY_TO_SHIP") return '<span class="cert-badge cert-badge-pass">READY TO SHIP</span>';
    if (g === "SMOKE_PASS") return '<span class="cert-badge cert-badge-warn">SMOKE PASS</span>';
    if (g === "DO_NOT_SHIP") return '<span class="cert-badge cert-badge-fail">DO NOT SHIP</span>';
    if (g === "PENDING" || g === "running") return '<span class="cert-badge cert-badge-warn">PENDING</span>';
    return `<span class="cert-badge">${esc(g)}</span>`;
  }

  function featBadge(st) {
    const s = String(st || "").toUpperCase();
    if (s === "PASS") return '<span class="cert-badge cert-badge-pass">PASS</span>';
    if (s === "FAIL") return '<span class="cert-badge cert-badge-fail">FAIL</span>';
    return `<span class="cert-badge cert-badge-warn">${esc(s || "—")}</span>`;
  }

  async function api(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok && data.ok === false) throw new Error(data.message || res.statusText);
    return data;
  }

  function captureConsoleHook() {
    if (window.__ariaCertConsoleHooked) return;
    window.__ariaCertConsoleHooked = true;
    const wrap = (level) => {
      const orig = console[level].bind(console);
      console[level] = (...args) => {
        try {
          consoleBuf.push({
            ts: Date.now(),
            level,
            message: args.map((a) => {
              try {
                return typeof a === "string" ? a : JSON.stringify(a);
              } catch {
                return String(a);
              }
            }).join(" "),
          });
          if (consoleBuf.length > 500) consoleBuf.shift();
        } catch (_) {}
        return orig(...args);
      };
    };
    ["log", "info", "warn", "error"].forEach(wrap);
    window.addEventListener("unhandledrejection", (ev) => {
      consoleBuf.push({ ts: Date.now(), level: "unhandledrejection", message: String(ev.reason || "") });
    });
  }

  async function uploadConsole(runId) {
    if (!runId) return;
    const text = consoleBuf.map((e) => `[${e.level}] ${e.message}`).join("\n");
    await api(`/api/certification/runs/${encodeURIComponent(runId)}/console`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    }).catch(() => {});
  }

  async function loadHome() {
    const data = await api("/api/certification/home");
    const gate = data.gate || data.release_readiness || "NO_RUN";
    if ($("certGateLine")) $("certGateLine").innerHTML = gateBadge(gate);
    if ($("certStatusLine")) {
      const c = data.counts || {};
      const failNote = Number(c.fail || 0) === 1
        ? " (1 intentional mutation FAIL)"
        : "";
      $("certStatusLine").textContent =
        `Assertions ${c.assertions || 0} · PASS ${c.pass || 0} · FAIL ${c.fail || 0}${failNote} · API ${c.api_calls || 0} · ` +
        `Coverage ${(data.coverage || {}).feature_coverage_pct ?? "—"}% · Required ${data.required_coverage_pct}%`;
    }
    const blockers = data.blockers || [];
    if ($("certBlockers")) {
      $("certBlockers").innerHTML = blockers.length
        ? `<ul>${blockers.map((b) => `<li>${esc(b)}</li>`).join("")}</ul>`
        : '<p class="muted">No blockers on latest run.</p>';
    }
    const features = (data.latest || {}).features || {};
    if ($("certFeatures")) {
      const ids = Object.keys(features);
      $("certFeatures").innerHTML = ids.length
        ? `<ul class="cert-feature-list">${ids
            .map((id) => {
              const f = features[id];
              return `<li><button type="button" class="ghost-btn tiny cert-feat" data-id="${esc(id)}">${esc(f.title || id)}</button> ${featBadge(f.status)}</li>`;
            })
            .join("")}</ul>`
        : '<p class="muted">No features in latest run — start a certification.</p>';
    }
    const hist = data.history || [];
    if ($("certHistory")) {
      $("certHistory").innerHTML = hist.length
        ? `<ul>${hist
            .map(
              (r) =>
                `<li><button type="button" class="linkish cert-run-link" data-run="${esc(r.id)}">${esc(r.id)}</button> ` +
                `${esc(r.status || "")} ${esc(r.gate || "")}</li>`
            )
            .join("")}</ul>`
        : '<p class="muted">No certification history yet.</p>';
    }
    activeRunId = (data.latest || {}).id || activeRunId;
    return data;
  }

  async function loadRun(runId) {
    activeRunId = runId;
    const data = await api(`/api/certification/runs/${encodeURIComponent(runId)}`);
    const run = data.run || {};
    if ($("certDetailTitle")) $("certDetailTitle").textContent = run.label || runId;
    if ($("certDetailMeta")) {
      $("certDetailMeta").innerHTML =
        `${gateBadge(run.gate)} · ${esc(run.status)} · assertions ${(run.counts || {}).assertions || 0}`;
    }
    const assertions = data.assertions || [];
    if ($("certAssertions")) {
      $("certAssertions").innerHTML = assertions.length
        ? `<table class="cert-table"><thead><tr><th>Result</th><th>Assertion</th><th>Expected</th><th>Observed</th></tr></thead><tbody>${assertions
            .map(
              (a) =>
                `<tr class="${a.result === "FAIL" ? "cert-row-fail" : ""}">` +
                `<td>${featBadge(a.result)}</td>` +
                `<td>${esc(a.name)}<div class="muted tiny">${esc(a.feature || "")}</div></td>` +
                `<td><code>${esc(JSON.stringify(a.expected))}</code></td>` +
                `<td><code>${esc(JSON.stringify(a.observed)).slice(0, 200)}</code></td></tr>`
            )
            .join("")}</tbody></table>`
        : '<p class="muted">No assertions.</p>';
    }
    const files = data.evidence_files || [];
    if ($("certEvidence")) {
      $("certEvidence").innerHTML = files.length
        ? `<ul>${files
            .map(
              (f) =>
                `<li><a href="/api/certification/runs/${encodeURIComponent(runId)}/file?path=${encodeURIComponent(f.path)}" target="_blank" rel="noopener">${esc(f.path)}</a> <span class="muted">(${f.bytes} B)</span></li>`
            )
            .join("")}</ul>`
        : '<p class="muted">No evidence files.</p>';
    }
    const apis = data.api_calls || [];
    if ($("certApiCalls")) {
      $("certApiCalls").innerHTML = apis.length
        ? `<ul class="cert-api-list">${apis
            .slice(-40)
            .reverse()
            .map(
              (c) =>
                `<li><code>${esc(c.method)} ${esc(c.endpoint)}</code> → ${esc(c.status)} · ${esc(c.duration_ms)}ms</li>`
            )
            .join("")}</ul>`
        : '<p class="muted">No API calls recorded.</p>';
    }
    return data;
  }

  async function startRun({ skipImage = true } = {}) {
    captureConsoleHook();
    if ($("certStatusLine")) $("certStatusLine").textContent = "Starting evidence certification…";
    const data = await api("/api/certification/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        label: "Live Certification Dashboard",
        skip_image: skipImage,
      }),
    });
    activeRunId = data.run_id;
    window.showAriaToast?.("Certification running — collecting evidence", "info", 4000);
    startPoll();
  }

  function startPoll() {
    stopPoll();
    pollTimer = setInterval(async () => {
      try {
        const latest = await api("/api/certification/runs/latest");
        const run = latest.run;
        if (!run) return;
        activeRunId = run.id;
        await loadHome();
        if (run.status === "complete" || run.status === "failed") {
          stopPoll();
          await uploadConsole(run.id);
          await loadRun(run.id);
          window.showAriaToast?.(
            run.gate === "READY_TO_SHIP" ? "READY TO SHIP — evidence recorded" : "DO NOT SHIP — see blockers",
            run.gate === "READY_TO_SHIP" ? "ok" : "err",
            6000
          );
        }
      } catch (_) {}
    }, 2000);
  }

  function stopPoll() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = null;
  }

  function bind() {
    $("certRunBtn")?.addEventListener("click", () => startRun({ skipImage: true }));
    $("certRunFullBtn")?.addEventListener("click", () => startRun({ skipImage: false }));
    $("certRefreshBtn")?.addEventListener("click", async () => {
      await loadHome();
      if (activeRunId) await loadRun(activeRunId);
    });
    $("certOpenAuditBtn")?.addEventListener("click", () => window.switchToView?.("audit"));
    document.addEventListener("click", async (ev) => {
      const runBtn = ev.target.closest?.(".cert-run-link");
      if (runBtn?.dataset.run) {
        await loadRun(runBtn.dataset.run);
        return;
      }
      const feat = ev.target.closest?.(".cert-feat");
      if (feat?.dataset.id && activeRunId) {
        const data = await loadRun(activeRunId);
        const filtered = (data.assertions || []).filter((a) => a.feature === feat.dataset.id);
        if ($("certAssertions") && filtered.length) {
          $("certAssertions").innerHTML = `<p class="muted">Filtered: ${esc(feat.dataset.id)}</p>` + $("certAssertions").innerHTML;
        }
      }
    });
    $("certAssertSearch")?.addEventListener("input", async () => {
      if (!activeRunId) return;
      const q = $("certAssertSearch").value.trim();
      const data = await api(
        `/api/certification/runs/${encodeURIComponent(activeRunId)}/assertions?q=${encodeURIComponent(q)}`
      );
      const assertions = data.assertions || [];
      if ($("certAssertions")) {
        $("certAssertions").innerHTML = assertions
          .map((a) => `<div>${featBadge(a.result)} <strong>${esc(a.name)}</strong> — expected <code>${esc(JSON.stringify(a.expected))}</code> observed <code>${esc(JSON.stringify(a.observed)).slice(0, 160)}</code></div>`)
          .join("") || '<p class="muted">No matches.</p>';
      }
    });
  }

  window.initCertification = async function initCertification() {
    captureConsoleHook();
    const root = $("certificationView");
    if (!root) return;
    if (root.dataset.bound !== "1") {
      root.dataset.bound = "1";
      bind();
    }
    await loadHome();
    if (activeRunId) await loadRun(activeRunId);
  };
})();
