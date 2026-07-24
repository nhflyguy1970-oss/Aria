/** Personality + chat branches — extracted from app.js. */
(function () {
  "use strict";

const branchSelect = document.getElementById("branchSelect");
const newBranchBtn = document.getElementById("newBranchBtn");
const trimBranchesBtn = document.getElementById("trimBranchesBtn");
const clearMainBranchBtn = document.getElementById("clearMainBranchBtn");
const branchTrimModal = document.getElementById("branchTrimModal");
const branchTrimList = document.getElementById("branchTrimList");
const branchTrimCancelBtn = document.getElementById("branchTrimCancelBtn");
const branchTrimConfirmBtn = document.getElementById("branchTrimConfirmBtn");
const fetchWithTimeout = (...args) => window.fetchWithTimeout(...args);

async function loadPersonality() {
  const sel = document.getElementById("personalitySelect");
  if (!sel) return;
  try {
    const res = await fetch("/api/personality");
    if (!res.ok) throw new Error(`Personality load failed (${res.status})`);
    const data = await res.json();
    if (data.personality && sel.querySelector(`option[value="${data.personality}"]`)) {
      sel.value = data.personality;
    }
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not load personality", "err", 4000);
  }
}

async function loadBranches() {
  if (!branchSelect) return;
  try {
    const res = await fetch("/api/branches");
    if (!res.ok) throw new Error(`Branches load failed (${res.status})`);
    const data = await res.json();
    window.activeBranchId = data.active || "main";
    branchSelect.innerHTML = (data.branches || []).map((b) =>
      `<option value="${window.escapeHtml(b.id)}"${b.id === window.activeBranchId ? " selected" : ""}>${window.escapeHtml(b.name)} (${b.messages})</option>`
    ).join("");
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not load branches", "err", 4000);
  }
}

async function maybeShowMorningBriefing() {
  if (window.activeBranchId && window.activeBranchId !== "main") return false;
  try {
    const res = await fetchWithTimeout("/api/briefing?launch=1", {}, 5000);
    if (!res.ok) return false;
    const data = await res.json();
    if (!data.show || !data.markdown) return false;
    window.addMessage?.("assistant", data.markdown, { type: "briefing", module: "journal" });
    fetch("/api/briefing/dismiss", { method: "POST" }).catch(() => {});
    return true;
  } catch (_) {
    return false;
  }
}

async function reloadBranchMessages() {
  const messages = document.getElementById("messages");
  if (!messages) return;
  try {
    const res = await fetch(`/api/branches/${encodeURIComponent(window.activeBranchId)}/messages`);
    if (!res.ok) throw new Error(`Messages load failed (${res.status})`);
    const data = await res.json();
    messages.innerHTML = "";
    for (const m of data.messages || []) {
      window.addMessage?.(m.role === "user" ? "user" : "assistant", m.content || "");
    }
    if (!(data.messages || []).length) {
      const showed = await maybeShowMorningBriefing();
      if (!showed) {
        window.addMessage?.(
          "assistant",
          `Hello! I'm ${(window.ariaName?.() || "ARIA")}. Ask **what can you do?** to see my abilities, or say **morning briefing** for today's summary.`,
          { type: "info" }
        );
      }
    }
    return true;
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not load branch messages", "err", 5000);
    return false;
  }
}

branchSelect?.addEventListener("change", async () => {
  const previousBranchId = window.activeBranchId;
  let serverSwitched = false;
  window.activeBranchId = branchSelect.value;
  const form = new FormData();
  form.append("branch_id", window.activeBranchId);
  try {
    const res = await fetch("/api/branches/switch", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.detail || `Switch failed (${res.status})`);
    serverSwitched = true;
    const loaded = await reloadBranchMessages();
    if (!loaded) throw new Error("Branch switched, but its messages could not be loaded");
    window.showAriaToast?.(`Switched to ${branchSelect.selectedOptions?.[0]?.textContent || window.activeBranchId}`, "ok", 2500);
  } catch (err) {
    if (!serverSwitched) {
      window.activeBranchId = previousBranchId;
      branchSelect.value = previousBranchId;
    } else {
      const status = document.getElementById("statusText");
      if (status) status.textContent = "Branch switched · messages unavailable";
    }
    window.showAriaToast?.(err.message || "Could not switch branch", "err", 5000);
  }
});

newBranchBtn?.addEventListener("click", async () => {
  const name = prompt("Branch name:", "Branch");
  if (!name) return;
  const form = new FormData();
  form.append("name", name);
  try {
    const res = await fetch("/api/branches", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.message || data.detail || `Create failed (${res.status})`);
    window.activeBranchId = data.branch_id;
    await loadBranches();
    await reloadBranchMessages();
    (document.getElementById("statusText") || {}).textContent = `Branch: ${name}`;
    window.showAriaToast?.(`Branch created: ${name}`, "ok", 3000);
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not create branch", "err", 5000);
  }
});

async function openBranchTrimModal() {
  if (!branchTrimModal || !branchTrimList) return;
  try {
    const res = await fetch("/api/branches");
    if (!res.ok) throw new Error(`Branches load failed (${res.status})`);
    const data = await res.json();
    const branches = (data.branches || []).filter((b) => b.id !== "main");
    if (!branches.length) {
      (document.getElementById("statusText") || {}).textContent = "No extra branches to trim";
      return;
    }
    branchTrimList.innerHTML = branches.map((b) =>
      `<label class="branch-trim-item">`
      + `<input type="checkbox" name="branch_trim" value="${window.escapeHtml(b.id)}">`
      + `<span>${window.escapeHtml(b.name)} <code>${window.escapeHtml(b.id)}</code> (${b.messages} msgs)</span>`
      + `</label>`
    ).join("");
    branchTrimModal.classList.remove("hidden");
  } catch (err) {
    window.showAriaToast?.(err.message || "Could not load branches to trim", "err", 5000);
  }
}

function closeBranchTrimModal() {
  branchTrimModal?.classList.add("hidden");
}

/* Job center — jarvis/gui/static/modules/jobs.mjs */

trimBranchesBtn?.addEventListener("click", () => { openBranchTrimModal(); });

clearMainBranchBtn?.addEventListener("click", async () => {
  if (!confirm("Clear all messages on the Main branch? This cannot be undone.")) return;
  try {
    const form = new FormData();
    form.append("branch_id", "main");
    let res = await fetch("/api/branches/clear", { method: "POST", body: form });
    if (res.status === 404) {
      res = await fetch("/api/branches/main/clear", { method: "POST" });
    }
    if (res.status === 404 && window.activeBranchId === "main") {
      const legacy = new FormData();
      legacy.append("message", "clear");
      res = await fetch("/api/chat", { method: "POST", body: legacy });
    }
    const data = await res.json();
    if (!res.ok || !data.ok) {
      window.showError?.(
        data.message
          || (res.status === 404
            ? "Clear Main needs a server restart — run: jarvis-ctl restart"
            : "Could not clear Main branch."),
      );
      return;
    }
    await loadBranches();
    if (window.activeBranchId === "main") {
      await reloadBranchMessages();
    } else {
      (document.getElementById("statusText") || {}).textContent = "Main branch cleared (still on current branch)";
    }
  } catch (e) {
    window.showError?.(`Clear failed: ${e.message || e}`);
  }
});

branchTrimCancelBtn?.addEventListener("click", closeBranchTrimModal);
branchTrimModal?.addEventListener("click", (e) => {
  if (e.target === branchTrimModal) closeBranchTrimModal();
});

branchTrimConfirmBtn?.addEventListener("click", async () => {
  const checked = [...(branchTrimList?.querySelectorAll('input[name="branch_trim"]:checked') || [])]
    .map((el) => el.value);
  if (!checked.length) {
    (document.getElementById("statusText") || {}).textContent = "Select at least one branch";
    window.showAriaToast?.("Select at least one branch", "warn", 3000);
    return;
  }
  if (!confirm(`Delete ${checked.length} branch(es)? This cannot be undone.`)) return;
  const form = new FormData();
  form.append("branch_ids", checked.join(","));
  try {
    const res = await fetch("/api/branches/delete", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      throw new Error(data.message || "Could not delete branches.");
    }
    closeBranchTrimModal();
    window.activeBranchId = data.active || "main";
    await loadBranches();
    await reloadBranchMessages();
    const msg = `Deleted ${(data.deleted || []).length} branch(es)`;
    (document.getElementById("statusText") || {}).textContent = msg;
    window.showAriaToast?.(msg, "ok", 3000);
  } catch (err) {
    window.showError?.(err.message || "Could not delete branches.");
    window.showAriaToast?.(err.message || "Could not delete branches", "err", 5000);
  }
});

  window.loadPersonality = loadPersonality;
  window.loadBranches = loadBranches;
  window.reloadBranchMessages = reloadBranchMessages;
  window.maybeShowMorningBriefing = maybeShowMorningBriefing;

  async function forkBranchFromIndex(displayIndex) {
    const name = prompt("New branch name:", "Fork");
    if (!name) return;
    const form = new FormData();
    form.append("name", name);
    form.append("display_index", String(displayIndex));
    try {
      const res = await fetch("/api/branches/fork", { method: "POST", body: form });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        const msg = data.message || data.detail || `Could not fork branch (${res.status})`;
        window.showError?.(msg);
        window.showAriaToast?.(msg, "err", 5000);
        return;
      }
      window.activeBranchId = data.branch_id;
      await loadBranches();
      await reloadBranchMessages();
      const status = document.getElementById("statusText");
      if (status) status.textContent = `Forked branch: ${name}`;
      window.showAriaToast?.(`Forked branch: ${name}`, "ok", 3000);
    } catch (e) {
      window.showError?.(String(e.message || e));
      window.showAriaToast?.(String(e.message || e), "err", 5000);
    }
  }
  window.forkBranchFromIndex = forkBranchFromIndex;
})();
