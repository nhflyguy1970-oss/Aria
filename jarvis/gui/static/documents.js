/** Documents library tab — extracted from movie_tiers.js. */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    if (typeof window.escapeHtml === "function") return window.escapeHtml(s);
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  async function loadDocumentsTab() {
    const list = $("documentsList");
    if (!list) return;
    try {
      const res = await fetch("/api/documents");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Library failed (${res.status})`);
      const docs = data.documents || [];
      list.innerHTML = docs.length
        ? docs.map((d) => {
          const name = d.name || d.path || "?";
          const path = d.path || name;
          return `<li class="documents-row"><strong>${escapeHtml(name)}</strong> `
            + `<span class="muted">${escapeHtml(path)}</span> `
            + `<button type="button" class="ghost-btn tiny doc-attach" data-path="${escapeHtml(path)}">Attach</button> `
            + `<button type="button" class="ghost-btn tiny doc-summarize" data-path="${escapeHtml(path)}">Summarize</button> `
            + `<button type="button" class="ghost-btn tiny doc-learn" data-path="${escapeHtml(path)}">Learn</button></li>`;
        }).join("")
        : `<li class='muted'>No documents yet. Drop PDFs/DOCX in <code>data/documents/</code> or <button type='button' class='ghost-btn tiny' id='docsEmptyChatBtn'>ask Chat</button>.</li>`;
      list.querySelector("#docsEmptyChatBtn")?.addEventListener("click", () => {
        window.switchToView?.("chat");
        window.jarvisSendToChat?.("Help me import documents into the library");
      });
      list.querySelectorAll(".doc-attach").forEach((btn) => {
        btn.addEventListener("click", () => {
          const p = btn.dataset.path || "";
          const input = $("messageInput");
          if (input) {
            input.value = `summarize document ${p}`;
            input.focus();
          }
        });
      });
      list.querySelectorAll(".doc-summarize").forEach((btn) => {
        btn.addEventListener("click", () => {
          const p = btn.dataset.path || "";
          window.switchToView?.("chat");
          if (typeof window.sendMessage === "function") {
            window.sendMessage(`summarize ${p}`);
          }
        });
      });
      list.querySelectorAll(".doc-learn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const p = btn.dataset.path || "";
          if (!p) return;
          btn.disabled = true;
          const label = btn.textContent;
          btn.textContent = "Learning…";
          try {
            const learnRes = await fetch("/api/documents/learn", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ path: p }),
            });
            const learnData = await learnRes.json().catch(() => ({}));
            if (!learnRes.ok || learnData.ok === false) {
              throw new Error(learnData.message || learnData.detail || `Learn failed (${learnRes.status})`);
            }
            const msg = learnData.message || `Learned from ${p}`;
            if (typeof window.appendAssistantMessage === "function") {
              window.appendAssistantMessage(msg);
            }
            window.showAriaToast?.(msg, "ok", 3500);
          } catch (err) {
            window.showAriaToast?.(err.message || "Document learn failed", "err", 5000);
          } finally {
            btn.disabled = false;
            btn.textContent = label;
          }
        });
      });
    } catch (err) {
      list.innerHTML = `<li class="muted">${escapeHtml(err.message || "Could not load library")}</li>`;
      window.showAriaToast?.(err.message || "Could not load documents", "err", 5000);
    }
  }

  async function searchDocumentsLibrary() {
    const q = $("documentsSearchInput")?.value?.trim();
    const out = $("documentsSearchResults");
    const list = $("documentsList");
    if (!out || !q) return;
    out.classList.remove("hidden");
    if (list) list.classList.add("hidden");
    out.innerHTML = "<li class='muted'>Searching…</li>";
    try {
      const res = await fetch(`/api/documents/search?q=${encodeURIComponent(q)}&limit=8`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.detail || `Search failed (${res.status})`);
      const hits = data.hits || [];
      out.innerHTML = hits.length
        ? hits.map((h) => `<li><strong>${escapeHtml(h.title || h.source || "?")}</strong> `
          + `<span class="muted">${escapeHtml((h.text || "").slice(0, 120))}…</span></li>`).join("")
        : `<li class='muted'>No matches. <button type='button' class='ghost-btn tiny' id='docsEmptyChatBtn'>Ask Chat</button> or <button type='button' class='ghost-btn tiny' id='docsEmptyReindexBtn'>Reindex</button></li>`;
      out.querySelector("#docsEmptyChatBtn")?.addEventListener("click", () => {
        window.switchToView?.("chat");
        window.jarvisSendToChat?.(`Search my documents for: ${q}`);
      });
      out.querySelector("#docsEmptyReindexBtn")?.addEventListener("click", () => {
        $("documentsReindexBtn")?.click();
      });
    } catch (err) {
      out.innerHTML = `<li class='muted'>${escapeHtml(err.message || "Search failed")}</li>`;
      window.showAriaToast?.(err.message || "Document search failed", "err", 5000);
    }
  }

  function initDocumentsTab() {
    const root = $("documentsView");
    if (root?.dataset.bound === "1") return;
    if (root) root.dataset.bound = "1";
    $("documentsSearchBtn")?.addEventListener("click", searchDocumentsLibrary);
    $("documentsSearchInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") searchDocumentsLibrary();
    });
    $("documentsOpenMemoryBtn")?.addEventListener("click", () => window.switchToView?.("memory"));
    $("documentsOpenJournalBtn")?.addEventListener("click", () => window.switchToView?.("journal"));
    $("documentsOpenCalendarBtn")?.addEventListener("click", () => window.switchToView?.("calendar"));
    $("documentsOpenChatBtn")?.addEventListener("click", () => window.switchToView?.("chat"));
    $("documentsOpenProjectsBtn")?.addEventListener("click", () => window.switchToView?.("projects"));
    $("documentsReindexBtn")?.addEventListener("click", async () => {
      const btn = $("documentsReindexBtn");
      const status = $("documentsIndexStatus");
      if (btn) btn.disabled = true;
      if (status) status.textContent = "Reindexing…";
      try {
        const res = await fetch("/api/documents/reindex", { method: "POST" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          throw new Error(data.message || data.detail || `Reindex failed (${res.status})`);
        }
        if (status) status.textContent = `Indexed ${data.chunks ?? 0} chunks`;
        window.showAriaToast?.(`Indexed ${data.chunks ?? 0} document chunks`, "ok", 3500);
        loadDocumentsTab();
        $("documentsList")?.classList.remove("hidden");
        $("documentsSearchResults")?.classList.add("hidden");
      } catch (err) {
        if (status) status.textContent = err.message || "Reindex failed";
        window.showAriaToast?.(err.message || "Reindex failed", "err", 5000);
      } finally {
        if (btn) btn.disabled = false;
      }
    });
  }

  window.loadDocumentsTab = loadDocumentsTab;
  window.initDocumentsTab = initDocumentsTab;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDocumentsTab);
  } else {
    initDocumentsTab();
  }
})();
