/** Documents — personal document intelligence workspace (not Drive/Notion). */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    if (typeof window.escapeHtml === "function") return window.escapeHtml(s);
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  let docsState = { home: null, selected: "", filter: "", searching: false };
  let shortcutsBound = false;

  async function docsFetch(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) throw new Error(data.message || data.detail || res.statusText);
    return data;
  }

  function toast(msg, kind) {
    window.showAriaToast?.(String(msg || "").replace(/\*\*/g, ""), kind || "ok", 4000);
  }

  function healthLine(h) {
    if (!h) return "";
    return `${h.document_count || 0} docs · ${h.chunk_count || 0} chunks · ${h.mode || "—"} · embed ${
      h.embed_available ? "online" : "offline"
    }${h.needs_rebuild ? " · rebuild suggested" : ""}`;
  }

  function renderList(docs, targetId) {
    const list = $(targetId);
    if (!list) return;
    if (!docs.length) {
      list.innerHTML =
        `<li class="muted">No documents yet. Upload above or drop files here. <button type="button" class="ghost-btn tiny" id="docsEmptyChatBtn">Ask Chat</button></li>`;
      list.querySelector("#docsEmptyChatBtn")?.addEventListener("click", () => {
        window.switchToView?.("chat");
        window.jarvisSendToChat?.("Help me import documents into the library");
      });
      return;
    }
    list.innerHTML = "";
    docs.forEach((d) => {
      const li = document.createElement("li");
      li.className = `docs-row${d.path === docsState.selected ? " is-selected" : ""}`;
      li.tabIndex = 0;
      li.dataset.path = d.path || "";
      li.innerHTML = `<div class="docs-row-main"><strong>${escapeHtml(d.name || "?")}</strong>
        <span class="muted tiny">${escapeHtml(d.suffix || "")} · ${escapeHtml((d.relative || d.path || "").slice(-48))}</span></div>`;
      li.addEventListener("click", () => selectDoc(d.path));
      li.addEventListener("keydown", (e) => {
        if (e.key === "Enter") selectDoc(d.path);
      });
      list.appendChild(li);
    });
  }

  function hitActions(h, cite) {
    const path = h.source || h.path || "";
    const title = h.title || path || "?";
    const abs = path.startsWith("/") ? path : path;
    return `<li class="docs-hit">
      <div><strong>[${escapeHtml(cite?.id || "")}] ${escapeHtml(title)}</strong>
      <p class="muted tiny">${escapeHtml((cite?.excerpt || h.text || "").slice(0, 160))}</p>
      <p class="muted tiny">Why: ${escapeHtml(cite?.why || "match")} · <code>${escapeHtml(path)}</code></p></div>
      <div class="docs-hit-actions">
        <button type="button" class="ghost-btn tiny" data-act="preview" data-path="${escapeHtml(abs)}">Preview</button>
        <button type="button" class="ghost-btn tiny" data-act="summarize" data-path="${escapeHtml(abs)}">Summarize</button>
        <button type="button" class="ghost-btn tiny" data-act="ask" data-path="${escapeHtml(abs)}">Ask Aria</button>
        <button type="button" class="ghost-btn tiny" data-act="learn" data-path="${escapeHtml(abs)}">Learn</button>
        <button type="button" class="ghost-btn tiny" data-act="folder" data-path="${escapeHtml(abs)}">Open Folder</button>
      </div>
    </li>`;
  }

  async function selectDoc(path) {
    docsState.selected = path || "";
    await renderHome(docsState.home, path);
  }

  async function renderHome(home, previewPath) {
    const root = $("documentsHome");
    if (!root) return;
    docsState.home = home;
    const h = home.health || {};
    const status = $("documentsIndexStatus");
    if (status) status.textContent = healthLine(h);

    if (!docsState.searching) {
      renderList(home.documents || [], "documentsList");
      $("documentsList")?.classList.remove("hidden");
      $("documentsSearchResults")?.classList.add("hidden");
    }

    let previewHtml = `<p class="muted">Select a document for preview, metadata, and actions.</p>`;
    if (previewPath) {
      try {
        const prev = await docsFetch(`/api/documents/preview?path=${encodeURIComponent(previewPath)}`);
        const d = prev.document || {};
        const sug = d.suggestion || {};
        previewHtml = `
          <section class="docs-panel">
            <h4>${escapeHtml(d.title || d.path || "Document")}</h4>
            <dl class="docs-dl">
              <dt>Type</dt><dd>${escapeHtml(d.suffix || "—")}</dd>
              <dt>Modified</dt><dd>${escapeHtml(d.modified || "—")}</dd>
              <dt>Location</dt><dd><code>${escapeHtml(d.location || d.path || "")}</code></dd>
              <dt>Project</dt><dd>${escapeHtml(d.project || "—")}</dd>
              <dt>Pages</dt><dd>${escapeHtml(String(d.page_count ?? "—"))}</dd>
              <dt>Smart import</dt><dd>${escapeHtml(sug.suggested_type || "—")} — index only; Learn stages candidates</dd>
            </dl>
            <p><strong>Preview</strong></p>
            <pre class="docs-pre">${escapeHtml(d.preview || "")}</pre>
            <div class="docs-hit-actions">
              <button type="button" class="apply-btn small" data-act="summarize" data-path="${escapeHtml(d.location || previewPath)}">Summarize</button>
              <button type="button" class="ghost-btn small" data-act="ask" data-path="${escapeHtml(d.location || previewPath)}">Ask Aria</button>
              <button type="button" class="ghost-btn small" data-act="learn" data-path="${escapeHtml(d.location || previewPath)}">Learn → candidates</button>
              <button type="button" class="ghost-btn small" data-act="chat" data-path="${escapeHtml(d.location || previewPath)}">Open in Chat</button>
            </div>
          </section>`;
      } catch (e) {
        previewHtml = `<p class="muted">${escapeHtml(e.message)}</p>`;
      }
    }

    const pack = home.project_pack || {};
    const cands = home.candidates || [];
    const imports = home.recent_imports || [];
    const searches = home.recent_searches || [];

    root.innerHTML = `
      <div class="docs-home-grid">
        <section class="docs-panel">
          <h4>Library overview</h4>
          <p>${escapeHtml(home.philosophy || "")}</p>
          <dl class="docs-dl">
            <dt>Documents</dt><dd>${escapeHtml(String(h.document_count ?? home.document_count ?? 0))}</dd>
            <dt>Chunks</dt><dd>${escapeHtml(String(h.chunk_count ?? 0))}</dd>
            <dt>Embeddings</dt><dd>${escapeHtml(String(h.embedded_chunks ?? 0))} (${Math.round((h.embedding_coverage || 0) * 100)}%)</dd>
            <dt>Last indexed</dt><dd>${escapeHtml(h.last_indexed || "—")}</dd>
            <dt>Status</dt><dd>${escapeHtml(h.mode || "—")}${h.needs_rebuild ? " · rebuild suggested" : ""}</dd>
          </dl>
        </section>
        <section class="docs-panel">
          <h4>Quick actions</h4>
          <div class="docs-hit-actions">
            ${(home.quick_actions || [])
              .map((a) => `<button type="button" class="ghost-btn small" data-quick="${escapeHtml(a.id)}">${escapeHtml(a.label)}</button>`)
              .join("")}
          </div>
        </section>
        <section class="docs-panel">
          <h4>Recent searches</h4>
          <ul class="docs-mini">${
            searches.length
              ? searches.map((s) => `<li><button type="button" class="ghost-btn tiny" data-research="${escapeHtml(s.q)}">${escapeHtml(s.q)}</button></li>`).join("")
              : "<li class='muted'>None yet</li>"
          }</ul>
          <h4>Recent imports</h4>
          <ul class="docs-mini">${
            imports.length
              ? imports.map((i) => `<li>${escapeHtml(i.name)} <span class="muted">(${escapeHtml(i.suggested_type || "")})</span></li>`).join("")
              : "<li class='muted'>None yet</li>"
          }</ul>
        </section>
        <section class="docs-panel">
          <h4>Memory candidates</h4>
          <p class="muted tiny">Documents stage candidates only — adopt in Memory (ACM).</p>
          <ul class="docs-mini">${
            cands.length
              ? cands.map((c) => `<li>${escapeHtml(c.content)}</li>`).join("")
              : "<li class='muted'>None pending</li>"
          }</ul>
          <button type="button" class="ghost-btn small" data-quick="memory">Open Memory</button>
        </section>
        <section class="docs-panel">
          <h4>Project retrieval pack</h4>
          <p>${escapeHtml(pack.summary || "—")}</p>
          <p class="muted tiny">Knowledge NS <code>${escapeHtml(pack.knowledge_namespace || "—")}</code></p>
          <ul class="docs-mini">${
            (pack.git_documentation || [])
              .slice(0, 5)
              .map((g) => `<li><code>${escapeHtml(g.name)}</code></li>`)
              .join("") || "<li class='muted'>No git docs linked</li>"
          }</ul>
          <button type="button" class="ghost-btn small" data-quick="projects">Open Projects</button>
        </section>
        <section class="docs-panel docs-panel-wide">${previewHtml}</section>
      </div>
      <p class="muted tiny docs-shortcuts">Shortcuts: <kbd>/</kbd> search · <kbd>N</kbd> upload · <kbd>Esc</kbd> clear · <kbd>?</kbd> help</p>
    `;

    root.querySelectorAll("[data-quick]").forEach((btn) => {
      btn.addEventListener("click", () => handleQuick(btn.getAttribute("data-quick")));
    });
    root.querySelectorAll("[data-research]").forEach((btn) => {
      btn.addEventListener("click", () => {
        if ($("documentsSearchInput")) $("documentsSearchInput").value = btn.getAttribute("data-research") || "";
        searchDocumentsLibrary();
      });
    });
    bindDocActions(root);
  }

  function bindDocActions(scope) {
    scope.querySelectorAll("[data-act]").forEach((btn) => {
      btn.addEventListener("click", () => runDocAction(btn.getAttribute("data-act"), btn.getAttribute("data-path") || ""));
    });
  }

  async function runDocAction(act, path) {
    const full = path;
    if (act === "preview") {
      await selectDoc(full);
      return;
    }
    if (act === "summarize") {
      window.switchToView?.("chat");
      window.sendMessage?.(`summarize ${full}`);
      return;
    }
    if (act === "ask" || act === "chat") {
      window.switchToView?.("chat");
      if (act === "ask") {
        window.jarvisSendToChat?.(`Ask about document ${full}: `);
      } else {
        const input = $("messageInput");
        if (input) {
          input.value = `summarize document ${full}`;
          input.focus();
        }
      }
      return;
    }
    if (act === "learn") {
      try {
        const data = await docsFetch("/api/documents/learn", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: full }),
        });
        toast(data.message || "Candidates staged", "ok");
        await loadHome(docsState.selected);
      } catch (e) {
        toast(e.message, "err");
      }
      return;
    }
    if (act === "folder") {
      toast(full, "info");
    }
  }

  function handleQuick(id) {
    if (id === "upload") $("documentsFileInput")?.click();
    else if (id === "import_folder") $("documentsFolderInput")?.focus();
    else if (id === "ask") $("documentsAskDialog")?.showModal?.();
    else if (id === "summarize" && docsState.selected) runDocAction("summarize", docsState.selected);
    else if (id === "learn" && docsState.selected) runDocAction("learn", docsState.selected);
    else if (id === "rebuild") rebuildIndex();
    else if (id === "briefing") showBriefing();
    else if (id === "memory") window.switchToView?.("memory");
    else if (id === "projects") window.switchToView?.("projects");
  }

  async function loadHome(previewPath) {
    const root = $("documentsHome");
    if (root) root.innerHTML = `<div class="docs-skeleton" aria-busy="true"><div></div><div></div><div></div></div>`;
    try {
      const home = await docsFetch("/api/documents/home");
      await renderHome(home, previewPath || docsState.selected);
    } catch (e) {
      if (root) root.innerHTML = `<p class="muted">${escapeHtml(e.message)}</p>`;
      toast(e.message, "err");
    }
  }

  async function searchDocumentsLibrary() {
    const q = $("documentsSearchInput")?.value?.trim();
    const out = $("documentsSearchResults");
    const list = $("documentsList");
    if (!out) return;
    if (!q) {
      clearSearch();
      return;
    }
    docsState.searching = true;
    out.classList.remove("hidden");
    if (list) list.classList.add("hidden");
    out.innerHTML = "<li class='muted'>Searching…</li>";
    try {
      const data = await docsFetch(`/api/documents/search?q=${encodeURIComponent(q)}&limit=12`);
      const hits = data.hits || [];
      const cites = data.citations || [];
      out.innerHTML = hits.length
        ? hits.map((h, i) => hitActions(h, cites[i])).join("")
        : `<li class='muted'>No matches. <button type='button' class='ghost-btn tiny' id='docsAskEmpty'>Ask Chat</button></li>`;
      bindDocActions(out);
      out.querySelector("#docsAskEmpty")?.addEventListener("click", () => {
        window.switchToView?.("chat");
        window.jarvisSendToChat?.(`Search my documents for: ${q}`);
      });
    } catch (err) {
      out.innerHTML = `<li class='muted'>${escapeHtml(err.message)}</li>`;
      toast(err.message, "err");
    }
  }

  function clearSearch() {
    docsState.searching = false;
    if ($("documentsSearchInput")) $("documentsSearchInput").value = "";
    $("documentsSearchResults")?.classList.add("hidden");
    $("documentsList")?.classList.remove("hidden");
    if (docsState.home) renderList(docsState.home.documents || [], "documentsList");
  }

  async function rebuildIndex() {
    const status = $("documentsIndexStatus");
    if (status) status.textContent = "Rebuilding search index…";
    try {
      const data = await docsFetch("/api/documents/reindex", { method: "POST" });
      toast(data.message || `Indexed ${data.chunks ?? 0} chunks`, "ok");
      await loadHome();
    } catch (e) {
      if (status) status.textContent = e.message;
      toast(e.message, "err");
    }
  }

  async function showBriefing() {
    try {
      const data = await docsFetch("/api/documents/briefing");
      const body = $("documentsBriefingBody");
      if (body) body.textContent = data.briefing || data.message || "";
      $("documentsBriefingDialog")?.showModal?.();
    } catch (e) {
      toast(e.message, "err");
    }
  }

  async function uploadFiles(fileList) {
    const status = $("documentsImportStatus");
    const files = [...(fileList || [])];
    if (!files.length) return;
    if (status) status.textContent = `Importing ${files.length} file(s)…`;
    let ok = 0;
    for (const file of files) {
      const fd = new FormData();
      fd.append("file", file, file.name);
      try {
        const res = await fetch("/api/documents/upload", { method: "POST", body: fd });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) throw new Error(data.message || "Upload failed");
        ok += 1;
      } catch (e) {
        toast(e.message, "err");
      }
    }
    if (status) status.textContent = `Imported ${ok}/${files.length}`;
    toast(`Imported ${ok} file(s)`, ok ? "ok" : "warn");
    await loadHome();
  }

  function showHelp() {
    toast("Documents: / search · N upload · Esc clear · Enter open · Ask with sources · Learn stages Memory candidates only", "info");
  }

  function bindShortcuts() {
    if (shortcutsBound) return;
    shortcutsBound = true;
    document.addEventListener("keydown", (e) => {
      const view = $("documentsView");
      if (!view || view.classList.contains("hidden")) return;
      const tag = (e.target && e.target.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA" || e.target?.isContentEditable) {
        if (e.key === "Escape") {
          e.target.blur();
          clearSearch();
        }
        return;
      }
      if (e.key === "/" && !e.ctrlKey) {
        e.preventDefault();
        $("documentsSearchInput")?.focus();
      } else if (e.key === "n" || e.key === "N") {
        e.preventDefault();
        $("documentsFileInput")?.click();
      } else if (e.key === "?") {
        e.preventDefault();
        showHelp();
      } else if (e.key === "Escape") {
        clearSearch();
        $("documentsAskDialog")?.close?.();
        $("documentsBriefingDialog")?.close?.();
      } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        const items = [...document.querySelectorAll("#documentsList .docs-row, #documentsSearchResults .docs-hit")];
        if (!items.length) return;
        e.preventDefault();
        const idx = items.findIndex((el) => el.classList.contains("is-selected"));
        const next = e.key === "ArrowDown" ? Math.min(items.length - 1, Math.max(0, idx + 1)) : Math.max(0, idx <= 0 ? 0 : idx - 1);
        const path = items[next]?.dataset?.path || items[next]?.querySelector?.("[data-path]")?.getAttribute("data-path");
        if (path) selectDoc(path);
      }
    });
  }

  function initDocumentsTab() {
    const root = $("documentsView");
    if (!root) return;
    if (root.dataset.bound === "1") {
      loadHome();
      return;
    }
    root.dataset.bound = "1";
    bindShortcuts();

    $("documentsSearchBtn")?.addEventListener("click", searchDocumentsLibrary);
    $("documentsSearchInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") searchDocumentsLibrary();
    });
    $("documentsClearSearchBtn")?.addEventListener("click", clearSearch);
    $("documentsRebuildBtn")?.addEventListener("click", rebuildIndex);
    $("documentsBriefingBtn")?.addEventListener("click", showBriefing);
    $("documentsAskBtn")?.addEventListener("click", () => $("documentsAskDialog")?.showModal?.());
    $("documentsHelpBtn")?.addEventListener("click", showHelp);
    $("documentsFileInput")?.addEventListener("change", (e) => uploadFiles(e.target.files));
    $("documentsImportFolderBtn")?.addEventListener("click", async () => {
      const path = $("documentsFolderInput")?.value?.trim();
      if (!path) return;
      try {
        const data = await docsFetch("/api/documents/import-folder", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path }),
        });
        toast(data.message || `Imported ${data.count}`, "ok");
        await loadHome();
      } catch (e) {
        toast(e.message, "err");
      }
    });

    const zone = $("documentsDropzone");
    zone?.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("is-drag");
    });
    zone?.addEventListener("dragleave", () => zone.classList.remove("is-drag"));
    zone?.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("is-drag");
      uploadFiles(e.dataTransfer?.files);
    });

    $("documentsAskSubmit")?.addEventListener("click", async () => {
      const question = $("documentsAskQuestion")?.value?.trim();
      const mode = $("documentsAskMode")?.value || "library";
      if (!question) return;
      const ans = $("documentsAskAnswer");
      if (ans) {
        ans.classList.remove("hidden");
        ans.textContent = "Thinking…";
      }
      try {
        const body = { question, mode };
        if (mode === "document" && docsState.selected) body.paths = [docsState.selected];
        const data = await docsFetch("/api/documents/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (ans) ans.textContent = data.message || data.answer || "";
      } catch (e) {
        if (ans) ans.textContent = e.message;
        toast(e.message, "err");
      }
    });

    loadHome();
  }

  window.loadDocumentsTab = function loadDocumentsTab() {
    loadHome(docsState.selected);
  };
  window.initDocumentsTab = initDocumentsTab;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDocumentsTab);
  } else {
    initDocumentsTab();
  }
})();
