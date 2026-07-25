/** Coding proposal diff UI + apply/undo — extracted from app.js. */
(function () {
function formatDiff(diff, options = {}) {
  const text = typeof diff === "string" ? diff : (diff == null ? "" : String(diff));
  if (!text) return "";
  const maxLines = options.maxLines || 160;
  const lines = text.split("\n");
  const slice = lines.length > maxLines ? lines.slice(0, maxLines) : lines;
  return slice.map((line) => {
    const escaped = window.escapeHtml(line);
    if (line.startsWith("+") && !line.startsWith("+++")) return `<span class="add">${escaped}</span>`;
    if (line.startsWith("-") && !line.startsWith("---")) return `<span class="del">${escaped}</span>`;
    return escaped;
  }).join("\n");
}

function mountDiffBlock(pre, diff, meta) {
  if (!pre) return;
  pre.className = "diff-block";
  pre.innerHTML = formatDiff(diff);
  if (meta?.diff_truncated && meta?.proposal_id) {
    const note = document.createElement("div");
    note.className = "diff-truncated-note";
    const total = meta.diff_total_lines ? ` (${meta.diff_total_lines} lines total)` : "";
    note.textContent = `Diff preview truncated${total}.`;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ghost-btn small";
    btn.textContent = "Load full diff";
    btn.onclick = async () => {
      btn.disabled = true;
      btn.textContent = "Loading…";
      try {
        const res = await fetch(`/api/proposals/${encodeURIComponent(meta.proposal_id)}`);
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false || !data.diff) {
          const msg = data.message || data.detail || `Could not load full diff (${res.status || "?"})`;
          btn.textContent = "Retry load";
          btn.disabled = false;
          window.showAriaToast?.(msg, "err", 4000);
          return;
        }
        pre.innerHTML = formatDiff(data.diff, { maxLines: 400 });
        note.remove();
      } catch (err) {
        btn.textContent = "Retry load";
        btn.disabled = false;
        window.showAriaToast?.(err?.message || "Could not load full diff", "err", 4000);
      }
    };
    note.appendChild(btn);
    pre.insertAdjacentElement("afterend", note);
  }
}

function resolveMetaType(data) {
  // Streamed coding/image results use type=done + result_type=proposal|image_result
  if (data.type === "done" && data.result_type) return data.result_type;
  return data.type || data.result_type
    || (data.action === "generate_image" ? "image_result" : undefined)
    || (data.action === "generate_video" ? "video_result" : undefined)
    || (data.action === "generate_meme" ? "image_result" : undefined)
    || (data.type === "media_job" || data.result_type === "media_job" ? "media_job" : undefined)
    || (data.type === "coding_job" || data.result_type === "coding_job" ? "coding_job" : undefined)
    || (data.action === "capabilities" || data.action === "greeting" ? "info" : undefined)
    || (data.action === "morning_briefing" || data.type === "briefing" ? "briefing" : undefined);
}

function appendUndoButton(messageDiv) {
  if (!messageDiv || messageDiv.querySelector?.(".undo-apply-btn")) return;
  const bubble = messageDiv.querySelector?.(".bubble") || messageDiv;
  if (!bubble) return;
  const actions = document.createElement("div");
  actions.className = "proposal-actions";
  const undoBtn = document.createElement("button");
  undoBtn.className = "reject-btn undo-apply-btn";
  undoBtn.textContent = "Undo apply";
  undoBtn.onclick = () => undoLastApply(undoBtn);
  actions.appendChild(undoBtn);
  bubble.appendChild(actions);
}

function clearProposalExtras(bubble) {
  if (!bubble) return;
  bubble.querySelectorAll(
    ".diagnostics-block, .test-impact, .diff-block, .diff-truncated-note, "
    + ".proposal-actions, .agent-steps, .proposal-render-error"
  ).forEach((el) => el.remove());
}

function prepareNativeCodingResult(result) {
  if (!window.isNativeApp?.() || !result?.proposal_id) return result;
  let message = String(result.message || "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\*\*Syntax check:\*\*[\s\S]*?(?=\n\n\*\*|\n\nSay |\n\nApply|$)/i, "")
    .replace(/\*\*Pre-apply verify:\*\*[\s\S]*?(?=\n\n\*\*|\n\nSay |$)/i, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  if (message.length > 650) message = `${message.slice(0, 650)}…`;
  if (!message) message = "Code proposal ready — use **Apply** or **Dismiss** below.";
  return {
    ...result,
    message,
    diff: undefined,
    diff_omitted: true,
    agent_steps: undefined,
    diagnostics: undefined,
    test_impact: undefined,
  };
}

function attachProposalExtras(bubble, meta, messageDiv) {
  if (!bubble || !meta) return;
  try {
  const bodyText = messageDiv?.querySelector?.(".msg-body")?.dataset?.rawText
    || messageDiv?.querySelector?.(".msg-body")?.textContent
    || "";
  if (meta.agent_steps && meta.agent_steps.length && !bubble.querySelector(".agent-steps")) {
    if (!window.isNativeApp?.()) {
      const stepsEl = document.createElement("div");
      stepsEl.className = "agent-steps";
      meta.agent_steps.forEach((s) => {
        const line = document.createElement("div");
        line.className = "agent-step" + (s.ok === false ? " fail" : "");
        line.textContent = `${s.step}. ${s.action}: ${s.detail}`;
        stepsEl.appendChild(line);
      });
      bubble.appendChild(stepsEl);
    }
  }

  if (meta.diagnostics && meta.diagnostics.length && !window.isNativeApp?.() && !/syntax check/i.test(bodyText)) {
    const diagEl = document.createElement("div");
    diagEl.className = "diagnostics-block" + (meta.syntax_ok === false ? " has-errors" : "");
    const title = document.createElement("div");
    title.className = "diagnostics-title";
    if (meta.verify_ok === false) {
      title.textContent = "Pre-apply tests failed";
      diagEl.classList.add("has-errors");
    } else {
      title.textContent = meta.syntax_ok === false ? "Syntax issues found" : "Syntax check passed";
    }
    diagEl.appendChild(title);
    const pre = document.createElement("pre");
    pre.className = "diagnostics-list";
    pre.textContent = meta.diagnostics
      .slice(0, 12)
      .map((d) => `${d.path}:${d.line} [${d.severity}] (${d.source}) ${d.message}`)
      .join("\n");
    diagEl.appendChild(pre);
    bubble.appendChild(diagEl);
  }

  if (meta.test_impact && !window.isNativeApp?.() && !/tests that will run/i.test(bodyText)) {
    const ti = document.createElement("div");
    ti.className = "test-impact";
    ti.innerHTML = window.formatMessage(meta.test_impact);
    bubble.appendChild(ti);
  }

  if (meta.proposal_id) {
    if (meta.diff) {
      const pre = document.createElement("pre");
      mountDiffBlock(pre, meta.diff, meta);
      bubble.appendChild(pre);
    } else if (meta.diff_omitted || (window.isNativeApp?.() && !meta.diff)) {
      const note = document.createElement("div");
      note.className = "diff-truncated-note";
      note.textContent = window.isNativeApp?.()
        ? "Diff hidden in desktop app to save memory."
        : "Diff not included in this response.";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn small";
      btn.textContent = "View diff";
      btn.onclick = async () => {
        btn.disabled = true;
        btn.textContent = "Loading…";
        try {
          const res = await fetch(`/api/proposals/${encodeURIComponent(meta.proposal_id)}`);
          const data = await res.json().catch(() => ({}));
          if (!res.ok || data.ok === false || !data.diff) {
            const msg = data.message || data.detail || `Could not load diff (${res.status || "?"})`;
            btn.textContent = "Retry load";
            btn.disabled = false;
            window.showAriaToast?.(msg, "err", 4000);
            return;
          }
          const pre = document.createElement("pre");
          mountDiffBlock(pre, data.diff, { ...meta, diff_truncated: data.diff_truncated });
          note.replaceWith(pre);
        } catch (err) {
          btn.textContent = "Retry load";
          btn.disabled = false;
          window.showAriaToast?.(err?.message || "Could not load diff", "err", 4000);
        }
      };
      note.appendChild(btn);
      bubble.appendChild(note);
    }
    const actions = document.createElement("div");
    actions.className = "proposal-actions";
    if (meta.upgrade_wizard) {
      const verifyBtn = document.createElement("button");
      verifyBtn.className = "ghost-btn";
      verifyBtn.textContent = "Verify tests";
      verifyBtn.onclick = () => window.runUpgradeAction?.("verify", meta.proposal_id, messageDiv);
      const applyBtn = document.createElement("button");
      applyBtn.className = "apply-btn";
      applyBtn.textContent = meta.verified ? "Apply upgrade" : "Apply upgrade (verify first)";
      applyBtn.onclick = () => window.runUpgradeAction?.("apply", meta.proposal_id, messageDiv);
      const rollbackBtn = document.createElement("button");
      rollbackBtn.className = "reject-btn";
      rollbackBtn.textContent = "Rollback";
      rollbackBtn.onclick = () => window.runUpgradeAction?.("rollback", "", messageDiv);
      actions.append(verifyBtn, applyBtn, rollbackBtn);
    } else {
      const applyBtn = document.createElement("button");
      applyBtn.className = "apply-btn";
      const verifyFailed = meta.verify_ok === false;
      applyBtn.textContent = verifyFailed
        ? "Apply anyway (tests failed in preview)"
        : (meta.syntax_ok === false ? "Apply anyway" : "Apply changes");
      applyBtn.onclick = () => {
        if (verifyFailed && !confirm("Pre-apply pytest failed. Apply these changes anyway?")) return;
        applyProposal(meta.proposal_id, messageDiv, meta.syntax_ok === false);
      };
      const rejectBtn = document.createElement("button");
      rejectBtn.className = "reject-btn";
      rejectBtn.textContent = "Dismiss";
      rejectBtn.onclick = () => window.sendMessage?.("don't apply that");
      actions.append(applyBtn, rejectBtn);
    }
    bubble.appendChild(actions);
  }

  if (meta.show_remember_key_points || meta.type === "knowledge_learned") {
    const actions = document.createElement("div");
    actions.className = "proposal-actions";
    const rememberBtn = document.createElement("button");
    rememberBtn.className = "apply-btn";
    rememberBtn.textContent = "Remember key points";
    rememberBtn.onclick = () => window.sendMessage?.("remember key points from that");
    actions.appendChild(rememberBtn);
    bubble.appendChild(actions);
  }

  if (meta.show_undo) {
    appendUndoButton(messageDiv);
  }
  } catch (e) {
    console.error("attachProposalExtras failed", e);
    if (messageDiv && !bubble.querySelector(".proposal-render-error")) {
      const err = document.createElement("p");
      err.className = "proposal-render-error";
      err.textContent = "Could not render proposal UI — use Apply from chat or retry.";
      bubble.appendChild(err);
    }
  }
}


function shouldShowUndo(data) {
  if (!data || data.ok === false) return false;
  if (data.show_undo) return true;
  return data.module === "coding"
    && (data.type === "applied" || data.result_type === "applied"
      || /\b(applied changes|Done — applied)\b/i.test(data.message || ""));
}

async function applyProposal(proposalId, messageEl, force = false) {
  if (force && !confirm("This proposal has syntax errors. Apply anyway?")) return;
  const form = new FormData();
  form.append("proposal_id", proposalId);
  if (force) form.append("force", "true");
  try {
    const res = await fetch("/api/apply", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || data.ok === false) {
      const msg = data.message || "Could not apply changes.";
      window.addMessage?.("assistant", msg, { module: data.module || "coding" });
      window.showAriaToast?.(msg, "err", 5000);
      return;
    }
    window.addMessage?.("assistant", data.message || "Applied.", {
      module: data.module || "coding",
      type: "applied",
      show_undo: true,
    });
    messageEl?.querySelector?.(".proposal-actions")?.remove();
    messageEl?.querySelector?.(".diff-block")?.remove();
  } catch (e) {
    window.addMessage?.("assistant", `Failed to apply changes: ${e?.message || e}`);
    window.showAriaToast?.(e?.message || "Failed to apply changes", "err", 5000);
  }
}

async function undoLastApply(triggerBtn) {
  try {
    const res = await fetch("/api/undo-apply", { method: "POST" });
    const data = await res.json();
    const msg = data.message || (data.ok ? "Restored." : "Nothing to undo.");
    window.addMessage?.("assistant", msg, { module: "coding" });
    window.showAriaToast?.(msg, data.ok ? "ok" : "info", 3000);
    if (data.ok) {
      triggerBtn?.closest?.(".proposal-actions")?.remove();
      document.querySelectorAll(".undo-apply-btn").forEach((btn) => {
        btn.closest(".proposal-actions")?.remove();
      });
    }
  } catch (e) {
    window.addMessage?.("assistant", `Undo failed: ${e?.message || e}`);
    window.showAriaToast?.(e?.message || "Undo failed", "err", 5000);
  }
}


  Object.assign(window, {
    formatDiff,
    mountDiffBlock,
    resolveMetaType,
    appendUndoButton,
    clearProposalExtras,
    prepareNativeCodingResult,
    attachProposalExtras,
    shouldShowUndo,
    applyProposal,
    undoLastApply,
  });
})();
