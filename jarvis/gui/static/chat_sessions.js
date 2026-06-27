/** P1 named chat sessions sidebar — linked to chat branches */
(function () {
  const $ = (id) => document.getElementById(id);

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  }

  async function switchToBranch(branchId) {
    if (!branchId) return false;
    const branchSelect = $("branchSelect");
    if (branchSelect) {
      branchSelect.value = branchId;
      branchSelect.dispatchEvent(new Event("change"));
      if (typeof window.switchToView === "function") window.switchToView("chat");
      return true;
    }
    const form = new FormData();
    form.append("branch_id", branchId);
    const res = await fetch("/api/branches/switch", { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok && !data.ok) return false;
    if (typeof window.switchToView === "function") window.switchToView("chat");
    return true;
  }

  async function loadSessions() {
    const list = $("chatSessionsList");
    if (!list) return;
    try {
      const data = await fetchJson("/api/chat/sessions");
      const sessions = data.sessions || [];
      list.innerHTML = sessions.length
        ? sessions.map((s) => {
          const pin = s.pinned ? "📌 " : "";
          const branchHint = s.branch_id ? ` <span class="muted small">→ ${esc(s.branch_id)}</span>` : "";
          return `<li data-id="${esc(s.id)}" data-branch="${esc(s.branch_id || "")}"><button type="button" class="chat-session-btn${s.pinned ? " pinned" : ""}">`
            + `${pin}${esc(s.title || s.id)}</button>${branchHint}`
            + `<button type="button" class="ghost-btn tiny chat-session-pin" title="Pin">★</button>`
            + `</li>`;
        }).join("")
        : "<li class='muted'>No saved sessions — use + Branch in chat</li>";
      list.querySelectorAll(".chat-session-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const li = btn.closest("li");
          const branchId = li?.dataset.branch;
          if (branchId) {
            const ok = await switchToBranch(branchId);
            if (ok && window.showAriaToast) window.showAriaToast(`Switched to ${li.querySelector(".chat-session-btn")?.textContent?.trim() || "session"}`, "info");
            return;
          }
          if (window.showAriaToast) window.showAriaToast("Session has no branch — create one with + Branch", "warn");
        });
      });
      list.querySelectorAll(".chat-session-pin").forEach((btn) => {
        btn.addEventListener("click", async (ev) => {
          ev.stopPropagation();
          const id = btn.closest("li")?.dataset.id;
          if (!id) return;
          await fetchJson(`/api/chat/sessions/${encodeURIComponent(id)}/pin`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pinned: true }),
          });
          loadSessions();
        });
      });
    } catch (_) {
      list.innerHTML = "<li class='muted'>Sessions unavailable</li>";
    }
  }

  async function createSession() {
    const title = $("chatSessionTitleInput")?.value?.trim() || "New chat";
    const branchId = $("branchSelect")?.value || "main";
    const created = await fetchJson("/api/chat/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, branch_id: branchId }),
    });
    if ($("chatSessionTitleInput")) $("chatSessionTitleInput").value = "";
    if (created?.session?.branch_id) await switchToBranch(created.session.branch_id);
    loadSessions();
  }

  function initChatSessions() {
    $("chatSessionNewBtn")?.addEventListener("click", createSession);
    loadSessions();
  }

  window.loadChatSessions = loadSessions;
  window.initChatSessions = initChatSessions;
  document.addEventListener("DOMContentLoaded", initChatSessions);
})();
