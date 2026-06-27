/** System audit tab — 14-phase whole-system PASS / WARNING / FAIL report */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  let pollTimer = null;
  let progressTimer = null;
  let progressState = null;
  const fixStore = [];

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  async function copyText(text) {
    const value = (text || "").trim();
    if (!value) return false;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
        return true;
      }
    } catch (_) {}
    try {
      const ta = document.createElement("textarea");
      ta.value = value;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      ta.style.top = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      ta.setSelectionRange(0, value.length);
      const ok = document.execCommand("copy");
      ta.remove();
      return ok;
    } catch (_) {
      return false;
    }
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok && !data.ok && !data.running) {
      throw new Error(data.error || data.message || res.statusText || "Request failed");
    }
    return data;
  }

  function resultBadge(result) {
    const r = (result || "unknown").toLowerCase();
    if (r === "pass") return '<span class="audit-badge audit-badge-pass">PASS</span>';
    if (r === "warning") return '<span class="audit-badge audit-badge-warn">WARNING</span>';
    if (r === "fail") return '<span class="audit-badge audit-badge-fail">FAIL</span>';
    return `<span class="audit-badge">${esc(result)}</span>`;
  }

  function renderItems(items, sectionClass) {
    if (!items?.length) {
      return `<p class="audit-empty muted">None</p>`;
    }
    return `<ul class="audit-list ${sectionClass}">${
      items.map((item) => {
        let fixHtml = "";
        if (item.fix || item.install_key) {
          const idx = fixStore.length;
          if (item.fix) fixStore.push(item.fix);
          const isInstall = item.install_key || /\/scripts\/install-/.test(item.fix || "");
          const fixLabel = isInstall ? "Install:" : "Fix:";
          const runBtn = item.install_key
            ? ` <button type="button" class="ghost-btn tiny audit-run-install" data-install-key="${item.install_key}">Run install</button>`
            : "";
          fixHtml = `<div class="audit-fix"><span class="audit-fix-label">${fixLabel}</span> `
            + `<code class="audit-fix-cmd" title="Click to select">${esc(item.fix || "")}</code>`
            + (item.fix ? ` <button type="button" class="ghost-btn tiny audit-copy-fix" data-fix-idx="${idx}">Copy</button>` : "")
            + runBtn
            + `</div>`;
        }
        return `<li class="audit-item"><span class="audit-msg">${esc(item.message)}</span>${fixHtml}</li>`;
      }).join("")
    }</ul>`;
  }

  function phaseClass(phase) {
    if (phase.fail?.length) return "audit-phase-fail";
    if (phase.warn?.length) return "audit-phase-warn";
    return "audit-phase-pass";
  }

  function renderPhase(phase) {
    const p = phase.pass?.length || 0;
    const w = phase.warn?.length || 0;
    const f = phase.fail?.length || 0;
    const counts = `<span class="audit-phase-counts muted">${p}✓ ${w}⚠ ${f}✗</span>`;
    return `
      <details class="audit-phase ${phaseClass(phase)}" ${f || w ? "open" : ""}>
        <summary class="audit-phase-title">${esc(phase.title || phase.id)} ${counts}</summary>
        <div class="audit-phase-body">
          ${f ? `<div class="audit-phase-block"><h4 class="audit-block-fail">Fail</h4>${renderItems(phase.fail, "audit-list-fail")}</div>` : ""}
          ${w ? `<div class="audit-phase-block"><h4 class="audit-block-warn">Warning</h4>${renderItems(phase.warn, "audit-list-warn")}</div>` : ""}
          ${p ? `<div class="audit-phase-block"><h4 class="audit-block-pass">Pass</h4>${renderItems(phase.pass, "audit-list-pass")}</div>` : ""}
        </div>
      </details>`;
  }

  function formatTime(sec) {
    const s = Math.max(0, Math.round(Number(sec) || 0));
    if (s >= 3600) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
    if (s >= 60) return `${Math.floor(s / 60)}m ${s % 60}s`;
    return `${s}s`;
  }

  function completeStatus(data) {
    const r = (data.result || "").toLowerCase();
    const jr = (data.jarvis_result || "").toLowerCase();
    let msg = r === "fail" ? "System audit — failures found"
      : r === "warning" ? "System audit — warnings present"
        : "System audit — all system checks passed";
    if (jr && jr !== "pass") msg += ` · Jarvis stack: ${jr}`;
    return msg;
  }

  function stopProgressTick() {
    if (progressTimer) {
      clearInterval(progressTimer);
      progressTimer = null;
    }
    progressState = null;
  }

  function renderProgress(prog) {
    const body = $("auditReportBody");
    if (!body || !prog) return;

    const pct = Math.min(100, Math.max(0, Number(prog.percent) || 0));
    const phase = Number(prog.phase) || 0;
    const total = Number(prog.total) || 14;
    const title = prog.title || "Running audit…";
    const elapsed = Number(prog.elapsed_sec) || 0;
    const eta = Number(prog.eta_sec) || 0;
    const phaseLabel = phase > 0 && phase <= total ? `Phase ${phase} of ${total}` : "Preparing…";
    const etaText = eta > 0 ? `~${formatTime(eta)} remaining` : "Almost done…";

    body.innerHTML = `
      <div class="audit-progress-panel" role="status" aria-live="polite" aria-busy="true">
        <div class="audit-progress-ring-wrap">
          <div class="audit-progress-ring" style="--audit-pct: ${pct}%">
            <span class="audit-progress-ring-label">${pct}%</span>
          </div>
          <div class="audit-progress-spinner" aria-hidden="true"></div>
        </div>
        <div class="audit-progress-details">
          <p class="audit-progress-phase">${esc(title)}</p>
          <p class="audit-progress-meta muted">${esc(phaseLabel)} · elapsed ${formatTime(elapsed)} · ${esc(etaText)}</p>
          <div class="audit-progress-bar-track" aria-hidden="true">
            <div class="audit-progress-bar-fill" style="width: ${pct}%"></div>
          </div>
        </div>
      </div>`;
  }

  function tickProgressLocal() {
    if (!progressState) return;
    const startedAt = progressState.started_at;
    if (!startedAt) return;
    const elapsed = Math.max(0, Math.floor(Date.now() / 1000 - startedAt));
    const phase = Number(progressState.phase) || 1;
    const total = Number(progressState.total) || 14;
    let eta = Number(progressState.eta_sec) || 0;
    if (phase > 1 && elapsed > 0) {
      eta = Math.max(0, Math.round(elapsed / (phase - 1) * (total - phase + 1)));
    }
    renderProgress({
      ...progressState,
      elapsed_sec: elapsed,
      eta_sec: eta,
    });
  }

  function applyProgressFromApi(data) {
    const prog = data.progress;
    if (!prog) return;
    progressState = {
      ...prog,
      started_at: prog.started_at || Date.now() / 1000,
    };
    renderProgress(progressState);
  }

  function startProgressTick() {
    stopProgressTick();
    progressTimer = setInterval(tickProgressLocal, 1000);
  }

  function renderReport(data) {
    const body = $("auditReportBody");
    if (!body) return;

    fixStore.length = 0;

    if (!data?.ok && data?.error) {
      body.innerHTML = `<p class="audit-error">${esc(data.error)}</p>`;
      return;
    }

    const summary = data.summary || {};
    const cached = data.cached ? ` · cached ${data.cache_age_sec || 0}s ago — click Run audit for fresh` : " · fresh run";
    const ts = data.timestamp ? new Date(data.timestamp).toLocaleString() : "—";
    const phases = data.phases || [];
    const phaseHtml = phases.length
      ? `<div class="audit-phases">${phases.map(renderPhase).join("")}</div>`
      : `<div class="audit-sections">
          <section class="audit-section audit-section-pass"><h3>✅ Pass</h3>${renderItems(data.pass, "audit-list-pass")}</section>
          <section class="audit-section audit-section-warn"><h3>⚠️ Warning</h3>${renderItems(data.warn, "audit-list-warn")}</section>
          <section class="audit-section audit-section-fail"><h3>❌ Fail</h3>${renderItems(data.fail, "audit-list-fail")}</section>
        </div>`;

    const loc = data.locations || {};
    const locParts = [];
    if (loc.jarvis_root) locParts.push(`root <code class="audit-loc-path">${esc(loc.jarvis_root)}</code>`);
    if (loc.venv_python) locParts.push(`venv <code class="audit-loc-path">${esc(loc.venv_python)}</code>`);
    if (loc.data_dir) locParts.push(`data <code class="audit-loc-path">${esc(loc.data_dir)}</code>`);
    const locHtml = locParts.length
      ? `<div class="audit-locations muted" title="Set JARVIS_ROOT / JARVIS_VENV to override">Paths: ${locParts.join(" · ")}</div>`
      : "";

    const sys = data.summary?.system;
    const jrv = data.summary?.jarvis;
    const scopeHtml = (sys || jrv)
      ? `<div class="audit-scope-bar muted">
          <span class="audit-scope-system" title="OS, hardware, storage, network, security">System: ${resultBadge(data.result).replace(/audit-badge/g, "audit-badge audit-badge-sm")} ${sys ? `${sys.pass}✓ ${sys.warn}⚠ ${sys.fail}✗` : ""}</span>
          ${jrv ? `<span class="audit-scope-jarvis" title="Jarvis venv, PyTorch, containers, Ollama"> · Jarvis: ${resultBadge(data.jarvis_result || "pass").replace(/audit-badge/g, "audit-badge audit-badge-sm")} ${jrv.pass}✓ ${jrv.warn}⚠ ${jrv.fail}✗</span>` : ""}
        </div>`
      : "";

    body.innerHTML = `
      <div class="audit-summary-bar">
        ${resultBadge(data.result)}
        <span class="audit-summary-counts">
          <span class="audit-count-pass">${summary.pass || 0} pass</span>
          <span class="audit-count-warn">${summary.warn || 0} warn</span>
          <span class="audit-count-fail">${summary.fail || 0} fail</span>
          <span class="muted">(${summary.phases || phases.length || 0} phases · ${summary.total || 0} checks)</span>
        </span>
        <span class="audit-meta muted">${esc(data.hostname || "")} · ${esc(ts)}${cached}${data.sudo_smart ? " · SMART" : ""}</span>
      </div>
      ${scopeHtml}
      ${locHtml}
      ${phaseHtml}`;
  }

  async function onCopyClick(btn) {
    const idx = Number(btn.dataset.fixIdx);
    const cmd = fixStore[idx] || btn.closest(".audit-fix")?.querySelector(".audit-fix-cmd")?.textContent || "";
    const prev = btn.textContent;
    const ok = await copyText(cmd);
    btn.textContent = ok ? "Copied" : "Select & Ctrl+C";
    if (!ok) {
      const code = btn.closest(".audit-fix")?.querySelector(".audit-fix-cmd");
      if (code && window.getSelection) {
        const range = document.createRange();
        range.selectNodeContents(code);
        const sel = window.getSelection();
        sel?.removeAllRanges();
        sel?.addRange(range);
      }
    }
    setTimeout(() => { btn.textContent = prev; }, 1500);
  }

  async function runInstall(key, btn) {
    const prev = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Installing…";
    setStatus(`Running install: ${key}… (sudo may prompt; can take a few minutes)`, true);
    try {
      const res = await fetch("/api/audit/install", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ install_key: key }),
      });
      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        throw new Error(res.ok ? "Invalid server response" : (res.statusText || "Server error"));
      }
      if (!data.ok) {
        let err = data.error || data.message || data.stderr || "Install failed";
        if (res.status === 404) {
          err = "Install API missing — restart ARIA (tray → restart, or jarvis-ctl restart)";
        }
        setStatus(`Install failed: ${String(err).slice(0, 200)}`, false);
        btn.textContent = "Failed";
        if (data.stderr) console.warn("audit install stderr:", data.stderr);
        return;
      }
      btn.textContent = "Done";
      setStatus("Install complete — refreshing audit…", true);
      try {
        await loadAudit({ force: true });
      } catch (auditErr) {
        setStatus(`Install OK — audit refresh failed: ${auditErr.message}. Click Run audit.`, false);
      }
    } catch (e) {
      setStatus(`Install error: ${e.message}`, false);
      btn.textContent = "Error";
    } finally {
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = prev;
      }, 2500);
    }
  }

  function bindCopyDelegation() {
    $("auditReportBody")?.addEventListener("click", (e) => {
      const installBtn = e.target.closest(".audit-run-install");
      if (installBtn) {
        e.preventDefault();
        e.stopPropagation();
        runInstall(installBtn.dataset.installKey, installBtn);
        return;
      }
      const btn = e.target.closest(".audit-copy-fix");
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      onCopyClick(btn);
    });
  }

  function setStatus(text, running) {
    const line = $("auditStatusLine");
    const runBtn = $("auditRunBtn");
    if (line) line.textContent = text;
    if (runBtn) runBtn.disabled = !!running;
  }

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function stopAuditProgress() {
    stopPoll();
    stopProgressTick();
  }

  async function loadAudit({ force = false } = {}) {
    const body = $("auditReportBody");
    if (!body) return;

    setStatus(force ? "Running 14-phase system audit…" : "Loading audit…", true);
    if (force || !body.querySelector(".audit-summary-bar")) {
      renderProgress({
        percent: 0,
        phase: 0,
        total: 14,
        title: force ? "Starting audit…" : "Loading audit…",
        elapsed_sec: 0,
        eta_sec: 90,
        started_at: Date.now() / 1000,
      });
      startProgressTick();
    }

    try {
      const url = force ? "/api/audit/run" : "/api/audit";
      const data = force ? await fetchJson(url, { method: "POST" }) : await fetchJson(url);

      if (data.running) {
        setStatus("Audit in progress…", true);
        applyProgressFromApi(data);
        startProgressTick();
        stopPoll();
        pollTimer = setInterval(async () => {
          try {
            const latest = await fetchJson("/api/audit");
            if (!latest.running) {
              stopAuditProgress();
              renderReport(latest);
              setStatus(completeStatus(latest), false);
              return;
            }
            applyProgressFromApi(latest);
          } catch (_) {}
        }, 2000);
        return;
      }

      stopAuditProgress();
      renderReport(data);
      setStatus(completeStatus(data), false);
    } catch (e) {
      stopAuditProgress();
      body.innerHTML = `<p class="audit-error">Audit failed: ${esc(e.message)}</p>`;
      setStatus(`Error: ${e.message}`, false);
    }
  }

  function initAudit() {
    if (!$("auditView")) return;
    loadAudit({ force: true });
  }

  function bindAuditControls() {
    $("auditRunBtn")?.addEventListener("click", () => loadAudit({ force: true }));
  }

  window.initAudit = initAudit;
  document.addEventListener("DOMContentLoaded", () => {
    bindAuditControls();
    bindCopyDelegation();
  });
})();
