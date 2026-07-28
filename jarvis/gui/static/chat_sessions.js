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
            + `<button type="button" class="ghost-btn tiny chat-session-pin" title="Pin session" aria-label="Pin session">★</button>`
            + `</li>`;
        }).join("")
        : "<li class='muted'>No saved threads. <button type='button' class='ghost-btn tiny' id='chatSessionsEmptyNewBtn'>New Chat</button></li>";
      list.querySelector("#chatSessionsEmptyNewBtn")?.addEventListener("click", () => {
        window.AriaChatOS?.newChat?.() || $("chatNewBtn")?.click();
      });
      list.querySelectorAll(".chat-session-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const li = btn.closest("li");
          const branchId = li?.dataset.branch;
          if (branchId) {
            const ok = await switchToBranch(branchId);
            if (ok && window.showAriaToast) window.showAriaToast(`Switched to ${li.querySelector(".chat-session-btn")?.textContent?.trim() || "session"}`, "info");
            else if (!ok) window.showAriaToast?.("Could not switch session branch", "err", 4000);
            return;
          }
          if (window.showAriaToast) window.showAriaToast("Session has no branch — use New Chat", "warn");
        });
      });
      list.querySelectorAll(".chat-session-pin").forEach((btn) => {
        btn.addEventListener("click", async (ev) => {
          ev.stopPropagation();
          const li = btn.closest("li");
          const id = li?.dataset.id;
          if (!id) return;
          const currentlyPinned = btn.closest("li")?.querySelector(".chat-session-btn")?.classList.contains("pinned");
          try {
            const data = await fetchJson(`/api/chat/sessions/${encodeURIComponent(id)}/pin`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ pinned: !currentlyPinned }),
            });
            if (data?.ok === false) {
              window.showAriaToast?.(data.message || data.error || "Could not update pin", "err", 4000);
              return;
            }
            window.showAriaToast?.(currentlyPinned ? "Unpinned" : "Pinned", "ok", 2000);
            loadSessions();
          } catch (err) {
            window.showAriaToast?.(err?.message || "Could not update pin", "err", 4000);
          }
        });
      });
    } catch (err) {
      list.innerHTML = "<li class='muted'>Sessions unavailable</li>";
      window.showAriaToast?.(err?.message || "Could not load chat sessions", "err", 4000);
    }
  }

  async function createSession() {
    // Bookmark current thread (session metadata only — does not create a new branch)
    const title = $("chatSessionTitleInput")?.value?.trim() || "Bookmarked chat";
    const branchId = $("branchSelect")?.value || window.activeBranchId || "main";
    try {
      const created = await fetchJson("/api/chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, branch_id: branchId }),
      });
      if (created?.ok === false || (!created?.session && created?.error)) {
        window.showAriaToast?.(created.message || created.error || "Could not bookmark thread", "err", 5000);
        return;
      }
      if ($("chatSessionTitleInput")) $("chatSessionTitleInput").value = "";
      window.showAriaToast?.(created?.session?.title ? `Bookmarked “${created.session.title}”` : "Thread bookmarked", "ok", 2500);
      loadSessions();
    } catch (err) {
      window.showAriaToast?.(err?.message || "Could not bookmark thread", "err", 5000);
    }
  }

  function initChatSessions() {
    $("chatSessionNewBtn")?.addEventListener("click", createSession);
    $("chatSessionNewChatBtn")?.addEventListener("click", () => {
      window.AriaChatOS?.newChat?.() || $("chatNewBtn")?.click();
    });
    loadSessions();
  }

  window.loadChatSessions = loadSessions;
  window.initChatSessions = initChatSessions;
  document.addEventListener("DOMContentLoaded", initChatSessions);
})();
