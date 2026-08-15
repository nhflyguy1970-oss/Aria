/** Guided Repair Engine UI — diagnose → plan → approve → repair → verify. */
(function () {
  "use strict";

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function toast(msg, kind = "info") {
    window.showAriaToast?.(msg, kind, 4000);
  }

  async function api(path, opts) {
    const res = await fetch(path, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
      ...opts,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok && !data.approval_required && !data.needs_explicit_confirmation) {
      throw new Error(data.message || data.error || res.statusText || "Repair API error");
    }
    return data;
  }

  function renderPanel(panel, issue) {
    if (!panel) return `<p class="muted">No repair panel.</p>`;
    const steps = (panel.plan_steps || []).map((s) => `<li>✓ ${esc(s)}</li>`).join("");
    const evidence = (panel.evidence || []).map((e) => `<li>${esc(e)}</li>`).join("");
    const reasons = (panel.confidence_reasons || []).map((e) => `<li>${esc(e)}</li>`).join("");
    const diag = panel.diagnosis || {};
    const impact = panel.impact || {};
    const dep = panel.dependency || {};
    const rollback = panel.rollback || {};
    const rep = panel.reputation || {};
    const destructive = panel.destructive || panel.approval_class === "manual";
    const affected = (impact.affected || []).map(esc).join(", ") || "—";
    const notAff = (impact.not_affected || []).slice(0, 8).map(esc).join(", ") || "—";
    const workflow = (panel.workflow || [])
      .map((w) => `<li><code>${esc(w.phase || "")}</code> ${esc(w.title || "")}</li>`)
      .join("");
    return `
      <article class="gr-panel" data-issue-id="${esc(panel.issue_id || issue?.id || "")}">
        <header class="gr-panel__head">
          <h3>Issue Detected</h3>
          <p class="gr-title">${esc(panel.title || issue?.title || "Issue")}</p>
          <p class="muted tiny">Priority: <strong>${esc(panel.priority || "medium")}</strong> · State: <code>${esc(panel.state || issue?.state || "")}</code>
            ${rep.reliability_stars ? ` · ${esc(rep.reliability_stars)}` : ""}</p>
        </header>
        <section><h4>Confidence</h4><p>${esc(panel.confidence_label || "")}</p>
          ${reasons ? `<p class="muted tiny">Reason</p><ul class="gr-list">${reasons}</ul>` : ""}</section>
        <section><h4>Diagnosis</h4><p>${esc(diag.root_cause || diag.explanation || "—")}</p>
          ${diag.why ? `<p class="muted tiny">${esc(diag.why)}</p>` : ""}</section>
        <section><h4>Evidence</h4>${evidence ? `<ul class="gr-list">${evidence}</ul>` : "<p class='muted'>None yet</p>"}</section>
        ${dep.display ? `<section><h4>Dependency Chain</h4><p>${esc(dep.display)}</p><p class="muted tiny">Repair lowest dependency first.</p></section>` : ""}
        <section><h4>Impact</h4>
          <p><strong>Affected</strong> ${affected}</p>
          <p><strong>Not affected</strong> ${notAff}</p>
          <p>Downtime ${esc(impact.expected_downtime_label || "—")} · Restart ${impact.restart_required ? "yes" : "no"}</p>
          <p class="muted tiny">Data risk: ${esc(impact.data_risk || "—")} · Config risk: ${esc(impact.configuration_risk || "—")} · Interruption: ${esc(impact.user_interruption || "—")}</p>
        </section>
        <section><h4>Repair Plan</h4>${steps ? `<ul class="gr-list">${steps}</ul>` : "<p class='muted'>—</p>"}</section>
        ${workflow ? `<section><h4>Workflow</h4><ul class="gr-list">${workflow}</ul></section>` : ""}
        <section class="gr-meta">
          <div><strong>Risk</strong><br>${esc(panel.risk || "—")}<br><span class="muted tiny">${esc(panel.risk_why || "")}</span></div>
          <div><strong>Estimated Time</strong><br>${esc(panel.estimated_time_label || "—")}</div>
          <div><strong>Rollback</strong><br>${esc(rollback.label || (panel.rollback_available ? "Available" : "Unavailable"))}<br><span class="muted tiny">${esc(rollback.why || panel.rollback_description || "")}</span></div>
        </section>
        <section><h4>Expected Result</h4><p>${esc(panel.expected_result || "—")}</p></section>
        <footer class="gr-actions">
          <button type="button" class="ghost-btn small" data-gr-preview="1">Preview Repair</button>
          ${
            destructive
              ? `<button type="button" class="apply-btn small" data-gr-exec="1" data-gr-destructive="1">Confirm destructive repair</button>`
              : `<button type="button" class="apply-btn small" data-gr-exec="1">Repair</button>`
          }
          <button type="button" class="ghost-btn small" data-gr-rollback="1">Rollback</button>
          <button type="button" class="ghost-btn small" data-gr-export="1">Export diagnostic</button>
          <button type="button" class="ghost-btn small" data-gr-close="1">Dismiss</button>
        </footer>
        <p class="muted tiny gr-disclaimer">${esc(panel.disclaimer || "")}</p>
        <div class="gr-progress muted tiny" hidden></div>
      </article>`;
  }

  let _openGen = 0;

  function repairSurfaceActive() {
    const room = document.body?.dataset?.room;
    return room === "mission" || room === "repair";
  }

  function onOverlayKeydown(e) {
    if (e.key !== "Escape") return;
    const root = document.getElementById("guidedRepairOverlay");
    if (!root?.classList.contains("is-open")) return;
    /* Nested confirms (Preview) keep Esc for themselves while open. */
    const confirm = document.getElementById("ariaConfirmDialog");
    if (confirm?.open) return;
    e.preventDefault();
    e.stopPropagation();
    closeOverlay();
  }

  function openOverlay(html) {
    /* Don't cover another Room if Open plan / Scan finished after Jeff left Mission. */
    if (!repairSurfaceActive()) return;
    let root = document.getElementById("guidedRepairOverlay");
    if (!root) {
      root = document.createElement("div");
      root.id = "guidedRepairOverlay";
      root.className = "gr-overlay";
      root.innerHTML = `<div class="gr-overlay__backdrop" data-gr-close="1"></div><div class="gr-overlay__card" role="dialog" aria-label="Guided Repair"></div>`;
      document.body.appendChild(root);
      root.addEventListener("click", onOverlayClick);
    }
    const card = root.querySelector(".gr-overlay__card");
    card.innerHTML = html;
    root.hidden = false;
    root.classList.add("is-open");
    document.addEventListener("keydown", onOverlayKeydown, true);
  }

  function closeOverlay() {
    const root = document.getElementById("guidedRepairOverlay");
    if (!root) return;
    root.classList.remove("is-open");
    root.hidden = true;
    document.removeEventListener("keydown", onOverlayKeydown, true);
  }

  async function onOverlayClick(e) {
    const t = e.target;
    if (t.closest?.("[data-gr-close]")) {
      closeOverlay();
      return;
    }
    const panel = t.closest?.(".gr-panel");
    const issueId = panel?.dataset?.issueId;
    if (!issueId) return;

    if (t.closest?.("[data-gr-preview]")) {
      try {
        const out = await api(`/api/repair/issues/${encodeURIComponent(issueId)}/preview`, { method: "POST", body: "{}" });
        const cmds = (out.commands || []).map((c) => `• ${c}`).join("\n");
        const body = [
          "PREVIEW ONLY — nothing will change.",
          "",
          `Duration: ${out.estimated_duration || "—"}`,
          `Outcome: ${out.expected_outcome || "—"}`,
          `Rollback: ${(out.rollback && out.rollback.label) || "—"}`,
          `Affected: ${(out.subsystems_affected || []).join(", ") || "—"}`,
          "",
          "Commands / steps:",
          cmds || "—",
        ].join("\n");
        if (window.ariaConfirm) await window.ariaConfirm(body, { title: "Preview Repair", okLabel: "Close" });
        else window.alert(body);
      } catch (err) {
        toast(err.message, "err");
      }
      return;
    }

    if (t.closest?.("[data-gr-export]")) {
      try {
        const out = await api("/api/repair/export", {
          method: "POST",
          body: JSON.stringify({ issue_id: issueId, approved_sensitive: false }),
        });
        toast(out.path ? `Diagnostic saved: ${out.path}` : out.message || "Exported", "ok");
      } catch (err) {
        toast(err.message, "err");
      }
      return;
    }

    if (t.closest?.("[data-gr-exec]")) {
      const destructive = !!t.closest("[data-gr-destructive]");
      const label = destructive
        ? "This is a DESTRUCTIVE repair. Type confirmation is required by policy. Proceed only if you understand the risk."
        : "Execute this repair plan? Aria will verify afterward and will not claim success without proof.";
      const ok = window.ariaConfirm
        ? await window.ariaConfirm(label, { title: "Approve repair", okLabel: "Repair" })
        : window.confirm(label);
      if (!ok) return;
      const prog = panel.querySelector(".gr-progress");
      if (prog) {
        prog.hidden = false;
        prog.textContent = "Repairing… UI stays responsive. Verification will follow.";
      }
      try {
        const out = await api(`/api/repair/issues/${encodeURIComponent(issueId)}/execute`, {
          method: "POST",
          body: JSON.stringify({
            approved: true,
            confirm_destructive: destructive,
            actor: "jeff",
          }),
        });
        if (out.approval_required || out.needs_explicit_confirmation) {
          toast(out.message || "Further confirmation required", "warn");
          return;
        }
        const verified = !!out.verified;
        toast(
          verified ? "Repair verified successful" : out.message || "Repair did not verify — not claiming fixed",
          verified ? "ok" : "warn",
        );
        window.AriaActivityProducers?.mission?.recovery?.(
          verified ? `Verified repair: ${out.issue?.title || issueId}` : `Unverified repair: ${out.issue?.title || issueId}`,
        );
        if (prog) {
          prog.textContent = out.message || (verified ? "Verified." : "Not verified.");
        }
        // Refresh panel with final state
        if (out.panel) {
          panel.outerHTML = renderPanel(out.panel, out.issue);
        }
        window.loadMissionControl?.();
      } catch (err) {
        toast(err.message || "Repair failed", "err");
        if (prog) prog.textContent = err.message || "Failed";
      }
      return;
    }

    if (t.closest?.("[data-gr-rollback]")) {
      const ok = window.ariaConfirm
        ? await window.ariaConfirm("Roll back this repair?", { title: "Rollback", okLabel: "Rollback" })
        : window.confirm("Roll back this repair?");
      if (!ok) return;
      try {
        const out = await api(`/api/repair/issues/${encodeURIComponent(issueId)}/rollback`, {
          method: "POST",
          body: JSON.stringify({ approved: true }),
        });
        toast(out.message || (out.ok ? "Rollback done" : "Rollback unavailable"), out.ok ? "ok" : "warn");
      } catch (err) {
        toast(err.message, "err");
      }
    }
  }

  async function planFromEvent(event) {
    toast("Diagnosing…", "info");
    const data = await api("/api/repair/plan", {
      method: "POST",
      body: JSON.stringify({ event: event || {}, text: `${event?.title || ""} ${event?.detail || ""}` }),
    });
    if (data.panel) {
      openOverlay(renderPanel(data.panel, data.issue));
      return true;
    }
    toast(data.message || "No repair plan available", "warn");
    return false;
  }

  async function scanAndShow() {
    toast("Scanning for repairable issues…", "info");
    const gen = ++_openGen;
    const scan = await api("/api/repair/scan", { method: "POST", body: "{}" });
    if (gen !== _openGen || !repairSurfaceActive()) return { ok: false, cancelled: true, issues: scan.issues || [] };
    const issues = scan.issues || [];
    if (!issues.length) {
      toast("No repairable issues detected", "ok");
      return { ok: true, issues: [] };
    }
    // Show highest severity / first repair-ready
    const ranked = [...issues].sort((a, b) => {
      const sev = { critical: 0, warning: 1, info: 2 };
      return (sev[a.severity] ?? 9) - (sev[b.severity] ?? 9);
    });
    const first = ranked[0];
    const detail = await api(`/api/repair/issues/${encodeURIComponent(first.id)}`);
    if (gen !== _openGen || !repairSurfaceActive()) return { ok: false, cancelled: true, issues };
    openOverlay(renderPanel(detail.panel || {}, detail.issue || first));
    return scan;
  }

  function renderRecoverySection(d) {
    const gr = d.guided_repair || {};
    const issues = gr.repair_queue || gr.issues || [];
    const hist = gr.history || [];
    const maint = gr.maintenance || {};
    const reps = gr.reputations || [];
    const issueRows = issues
      .map(
        (i) => {
          const conf = i.confidence != null ? Math.round(Number(i.confidence) * 100) + "%" : "—";
          const meta = [conf, i.risk || null].filter(Boolean).join(" · ");
          return `<tr>
          <td>${esc(i.priority || "")}</td>
          <td>
            <div>${esc(i.title)}</div>
            <button type="button" class="ghost-btn tiny" data-gr-open="${esc(i.id)}">Open plan</button>
            ${meta ? `<div class="muted tiny">${esc(meta)}</div>` : ""}
          </td>
          <td><code>${esc(i.state)}</code></td>
        </tr>`;
        },
      )
      .join("");
    const histRows = hist
      .map(
        (h) => `<li>${esc(h.iso || "")} — ${esc(h.title || h.module_id)} — <strong>${esc(h.result || "")}</strong>
          ${h.verified_ok ? "✓ verified" : "✗ not verified"}</li>`,
      )
      .join("");
    const repRows = reps
      .slice(0, 6)
      .map(
        (r) =>
          `<li>${esc(r.reliability_stars || "")} <strong>${esc(r.module_id)}</strong> — ${r.succeeded || 0}/${r.executed || 0} · avg ${r.average_repair_time ?? "—"}s · ${esc(r.trend || "")}</li>`,
      )
      .join("");
    return `
      <div class="gr-mc">
        <div class="mc-recovery-actions">
          <button type="button" class="apply-btn small" id="mcGuidedRepairScan">Scan &amp; diagnose</button>
          <button type="button" class="ghost-btn small" id="mcMaintToggle">${maint.enabled ? "End maintenance" : "Maintenance mode"}</button>
          <button type="button" class="ghost-btn small" id="mcRepairBtn">Legacy safe recover…</button>
          <button type="button" class="ghost-btn small" id="mcVerifyBtn">Verify</button>
          <button type="button" class="ghost-btn small" id="mcAcceptanceBtn">Run acceptance</button>
        </div>
        <p class="muted tiny">Guided Repair explains, waits for approval, verifies, then monitors. Confidence is justified — never certainty. Maintenance: <strong>${maint.enabled ? "ON (" + esc(maint.reason || "") + ")" : "off"}</strong></p>
        <div class="mc-grid">
          <div class="mc-card">
            <h3>Guided Repair</h3>
            <p>${esc(gr.detail || "—")}</p>
            <p class="muted tiny">${esc(gr.note || "")}</p>
          </div>
          <div class="mc-card">
            <h3>Repair queue (priority)</h3>
            ${
              issueRows
                ? `<table class="mc-table"><thead><tr><th>Pri</th><th>Issue</th><th>State</th></tr></thead><tbody>${issueRows}</tbody></table>`
                : "<p class='muted'>None active — run Scan &amp; diagnose</p>"
            }
          </div>
          <div class="mc-card">
            <h3>Repair reputation</h3>
            ${repRows ? `<ul class="mc-list">${repRows}</ul>` : "<p class='muted'>No reputation yet</p>"}
          </div>
          <div class="mc-card">
            <h3>Repair history</h3>
            ${histRows ? `<ul class="mc-list">${histRows}</ul>` : "<p class='muted'>No repairs recorded yet</p>"}
          </div>
        </div>
      </div>`;
  }

  function ensureMcHooks() {
    document.addEventListener(
      "click",
      async (e) => {
        if (e.target.closest?.("#mcGuidedRepairScan")) {
          e.preventDefault();
          try {
            await scanAndShow();
            window.loadMissionControl?.();
          } catch (err) {
            toast(err.message, "err");
          }
          return;
        }
        if (e.target.closest?.("#mcMaintToggle")) {
          e.preventDefault();
          try {
            const st = await api("/api/repair/maintenance");
            if (st.enabled) {
              await api("/api/repair/maintenance/disable", { method: "POST", body: JSON.stringify({ run_verification: true }) });
              toast("Maintenance ended — full verification ran", "ok");
            } else {
              await api("/api/repair/maintenance/enable", {
                method: "POST",
                body: JSON.stringify({ reason: "other", note: "Enabled from Mission Control" }),
              });
              toast("Maintenance mode on — expected alerts suppressed", "info");
            }
            window.loadMissionControl?.();
          } catch (err) {
            toast(err.message, "err");
          }
          return;
        }
        const open = e.target.closest?.("[data-gr-open]");
        if (open) {
          e.preventDefault();
          const gen = ++_openGen;
          try {
            const id = open.getAttribute("data-gr-open");
            const detail = await api(`/api/repair/issues/${encodeURIComponent(id)}`);
            if (gen !== _openGen || !repairSurfaceActive()) return;
            openOverlay(renderPanel(detail.panel || {}, detail.issue));
          } catch (err) {
            if (gen === _openGen && repairSurfaceActive()) toast(err.message, "err");
          }
        }
      },
      true,
    );
  }

  window.AriaGuidedRepair = {
    planFromEvent,
    scanAndShow,
    openOverlay,
    closeOverlay,
    renderPanel,
    renderRecoverySection,
    api,
  };

  ensureMcHooks();

  /* Leaving Mission/Repair must not leave Guided Repair covering the next Room. */
  window.addEventListener("aria-house-room", (e) => {
    const room = e.detail?.room;
    if (room === "mission" || room === "repair") return;
    _openGen += 1;
    closeOverlay();
  });
})();