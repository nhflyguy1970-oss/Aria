/** Upgrade wizard modal — extracted from app.js. */
(function () {
  "use strict";

let upgradeWizardState = { proposal_id: "", verified: false, snapshot_id: "" };

async function runUpgradeAction(action, proposalId, messageEl) {
  const endpoints = {
    verify: "/api/upgrade/verify",
    apply: "/api/upgrade/apply",
    rollback: "/api/upgrade/rollback",
  };
  const url = endpoints[action];
  if (!url) return;
  const form = new FormData();
  if (proposalId) form.append("proposal_id", proposalId);
  if (action === "rollback" && upgradeWizardState.snapshot_id) {
    form.append("snapshot_id", upgradeWizardState.snapshot_id);
  }
  try {
    const res = await fetch(url, { method: "POST", body: form });
    const data = await res.json();
    const msg = data.message || (data.ok ? "Done." : "Failed.");
    (window.addMessage || (() => {}))("assistant", msg, {
      module: "coding",
      type: data.type,
      upgrade_wizard: true,
      proposal_id: data.proposal_id || proposalId,
      verified: data.verified,
      show_undo: data.show_undo,
    });
    window.showAriaToast?.(msg, data.ok ? "ok" : "err", data.ok ? 3000 : 5000);
    if (data.proposal_id) upgradeWizardState.proposal_id = data.proposal_id;
    if (data.verified) upgradeWizardState.verified = true;
    if (data.snapshot_id) upgradeWizardState.snapshot_id = data.snapshot_id;
    refreshUpgradeWizardPanel();
    messageEl?.querySelector?.(".proposal-actions")?.remove();
  } catch (err) {
    (window.addMessage || (() => {}))("assistant", "Upgrade action failed.");
    window.showAriaToast?.(err?.message || "Upgrade action failed", "err", 5000);
  }
}

async function refreshUpgradeWizardPanel() {
  const stepEl = document.getElementById("upgradeWizardStep");
  const verifyBtn = document.getElementById("upgradeVerifyBtn");
  const applyBtn = document.getElementById("upgradeApplyBtn");
  const rollbackBtn = document.getElementById("upgradeRollbackBtn");
  const clearBtn = document.getElementById("upgradeClearBtn");
  if (!stepEl) return;
  try {
    const res = await fetch("/api/upgrade/status");
    const data = await res.json();
    const active = data.active || {};
    upgradeWizardState.proposal_id = active.proposal_id || upgradeWizardState.proposal_id;
    upgradeWizardState.verified = !!active.verified;
    upgradeWizardState.snapshot_id = active.snapshot_id || upgradeWizardState.snapshot_id;
    const step = active.step || "idle";
    stepEl.textContent = `Step: ${step}${active.task ? ` · ${active.task.slice(0, 60)}` : ""}`;
    if (verifyBtn) verifyBtn.disabled = !upgradeWizardState.proposal_id;
    if (applyBtn) applyBtn.disabled = !upgradeWizardState.proposal_id;
    if (rollbackBtn) rollbackBtn.disabled = !upgradeWizardState.snapshot_id && !(data.snapshots || []).length;
    const stuck = step !== "idle" || !!active.proposal_id;
    if (clearBtn) clearBtn.disabled = !stuck;
  } catch (_) {
    stepEl.textContent = "Step: offline";
  }
}

function initUpgradeWizardModal() {
  const modal = document.getElementById("upgradeWizardModal");
  const openBtn = document.getElementById("upgradeWizardBtn");
  const closeBtn = document.getElementById("upgradeWizardCloseBtn");
  const proposeBtn = document.getElementById("upgradeProposeBtn");
  const verifyBtn = document.getElementById("upgradeVerifyBtn");
  const applyBtn = document.getElementById("upgradeApplyBtn");
  const rollbackBtn = document.getElementById("upgradeRollbackBtn");
  const clearBtn = document.getElementById("upgradeClearBtn");
  const taskEl = document.getElementById("upgradeWizardTask");
  const logEl = document.getElementById("upgradeWizardLog");
  if (!modal || !openBtn) return;

  openBtn.addEventListener("click", () => {
    modal.classList.remove("hidden");
    refreshUpgradeWizardPanel();
  });
  closeBtn?.addEventListener("click", () => modal.classList.add("hidden"));

  clearBtn?.addEventListener("click", async () => {
    if (clearBtn) clearBtn.disabled = true;
    if (logEl) {
      logEl.classList.remove("hidden");
      logEl.textContent = "Clearing upgrade session…";
    }
    try {
      const res = await fetch("/api/upgrade/clear", { method: "POST" });
      const data = await res.json();
      upgradeWizardState.proposal_id = "";
      upgradeWizardState.verified = false;
      upgradeWizardState.snapshot_id = "";
      if (logEl) logEl.textContent = data.ok ? "Session cleared." : (data.message || "Clear failed.");
      window.showAriaToast?.(data.ok ? "Upgrade session cleared" : "Clear failed", data.ok ? "ok" : "err");
    } catch (e) {
      if (logEl) logEl.textContent = `Clear failed: ${e.message || e}`;
      window.showAriaToast?.(String(e.message || e), "err");
    }
    await refreshUpgradeWizardPanel();
  });

  proposeBtn?.addEventListener("click", async () => {
    const task = taskEl?.value?.trim();
    if (!task) {
      window.showAriaToast?.("Describe what to upgrade.", "warn", 3000);
      return;
    }
    if (proposeBtn) proposeBtn.disabled = true;
    if (logEl) {
      logEl.classList.remove("hidden");
      logEl.textContent = "Planning upgrade…";
    }
    try {
      const form = new FormData();
      form.append("task", task);
      const res = await fetch("/api/upgrade/propose", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        const msg = data.message || data.error || `Propose failed (${res.status})`;
        if (logEl) logEl.textContent = msg;
        window.showAriaToast?.(msg, "err", 5000);
        return;
      }
      if (logEl) logEl.textContent = data.message || "Proposal ready.";
      (window.addMessage || (() => {}))("assistant", data.message || "Proposal ready.", {
        module: "coding",
        type: "upgrade_proposal",
        proposal_id: data.proposal_id,
        diff: data.diff,
        upgrade_wizard: true,
        verified: false,
        diagnostics: data.diagnostics,
        syntax_ok: data.syntax_ok,
        test_impact: data.test_impact,
      });
      if (data.proposal_id) upgradeWizardState.proposal_id = data.proposal_id;
      refreshUpgradeWizardPanel();
    } catch (err) {
      if (logEl) logEl.textContent = "Propose failed.";
      window.showAriaToast?.(err?.message || "Propose failed", "err", 5000);
    } finally {
      if (proposeBtn) proposeBtn.disabled = false;
    }
  });

  verifyBtn?.addEventListener("click", () => runUpgradeAction("verify", upgradeWizardState.proposal_id));
  applyBtn?.addEventListener("click", () => {
    if (!upgradeWizardState.verified && !confirm("Tests not verified yet. Apply anyway?")) return;
    runUpgradeAction("apply", upgradeWizardState.proposal_id);
  });
  rollbackBtn?.addEventListener("click", () => runUpgradeAction("rollback", ""));
}


  window.runUpgradeAction = runUpgradeAction;
  window.refreshUpgradeWizardPanel = refreshUpgradeWizardPanel;
  window.initUpgradeWizardModal = initUpgradeWizardModal;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initUpgradeWizardModal());
  } else {
    initUpgradeWizardModal();
  }
})();
