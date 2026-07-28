/** Connections — Knowledge Graph explorer (not Memory, not Documents, not Knowledge Briefs). */
(function () {
  const $ = (id) => document.getElementById(id);
  let selectedName = "";
  let selectedNamespace = "default";
  let lastUndo = "";

  async function api(path, opts) {
    const res = await fetch(path, opts);
    return res.json();
  }

  function toast(msg, kind) {
    window.showAriaToast?.(msg, kind || "info", 3500);
  }

  function esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function provenanceLine(item) {
    const p = item.provenance || item;
    return `source=${esc(p.source || item.source || "?")} · conf=${esc(p.confidence ?? item.confidence ?? "?")} · mem=${esc(p.memory_id || item.memory_id || "—")} · doc=${esc(p.document || item.document || "—")}`;
  }

  async function loadHome() {
    const home = $("connectionsHome");
    if (!home) return;
    home.innerHTML = `<div class="conn-skeleton" aria-busy="true"><div></div><div></div><div></div></div>`;
    try {
      const data = await api("/api/connections/home");
      if (!data.ok) throw new Error(data.error || "Failed");
      const o = data.overview || {};
      const h = data.health || {};
      const pending = (data.pending_ingest || []).filter((p) => p.status === "pending");
      home.innerHTML = `
        <div class="conn-home-grid">
          <section class="conn-panel">
            <h4>Overview</h4>
            <dl class="conn-dl">
              <dt>Nodes</dt><dd>${esc(o.nodes)}</dd>
              <dt>Relationships</dt><dd>${esc(o.relationships)}</dd>
              <dt>Orphans</dt><dd>${esc(o.orphans)}</dd>
              <dt>Missing provenance</dt><dd>${esc(o.missing_provenance)}</dd>
              <dt>Backend</dt><dd>${esc(h.backend)}</dd>
            </dl>
            <p class="muted tiny">${esc(data.philosophy)}</p>
          </section>
          <section class="conn-panel">
            <h4>Identity</h4>
            <ul class="conn-mini">
              <li><strong>Documents</strong> — Document Intelligence</li>
              <li><strong>Knowledge</strong> — Knowledge Briefs</li>
              <li><strong>Connections</strong> — Knowledge Graph (this view)</li>
              <li><strong>Memory</strong> — Autobiographical cognition (ACM)</li>
            </ul>
          </section>
          <section class="conn-panel">
            <h4>Namespaces</h4>
            <ul class="conn-mini">${(o.namespaces || []).slice(0, 8).map((n) =>
              `<li><button type="button" class="ghost-btn tiny conn-ns" data-ns="${esc(n.namespace)}">${esc(n.namespace)}</button> · ${esc(n.nodes)} nodes</li>`
            ).join("") || "<li class='muted'>None yet</li>"}</ul>
          </section>
          <section class="conn-panel conn-panel-wide">
            <h4>Recent activity</h4>
            <ul class="conn-mini">${(data.recent_activity || []).slice(0, 8).map((a) => {
              const it = a.item || {};
              const label = a.kind === "relationship"
                ? `${it.subject} —${it.predicate}→ ${it.object}`
                : it.name;
              return `<li>${esc(a.kind)}: ${esc(label)}</li>`;
            }).join("") || "<li class='muted'>No activity yet. Create an entity or import with review.</li>"}</ul>
          </section>
          <section class="conn-panel conn-panel-wide">
            <h4>Pending import reviews</h4>
            <ul class="conn-mini" id="connPendingList">${pending.length ? pending.map((p) =>
              `<li>
                <strong>${esc(p.id)}</strong> · ${esc(p.source)} · ${(p.entities || []).length} entities · ${(p.relationships || []).length} rels
                <button type="button" class="ghost-btn tiny conn-approve" data-id="${esc(p.id)}">Approve all</button>
                <button type="button" class="ghost-btn tiny conn-dismiss" data-id="${esc(p.id)}">Dismiss</button>
              </li>`
            ).join("") : "<li class='muted'>No pending imports</li>"}</ul>
          </section>
          <section class="conn-panel" id="connectionsEntityPanel">
            <h4>Entity</h4>
            <p class="muted tiny">Select a search result or browse to inspect.</p>
          </section>
        </div>`;
      home.querySelectorAll(".conn-ns").forEach((btn) => {
        btn.addEventListener("click", () => {
          if ($("connectionsSearchInput")) $("connectionsSearchInput").value = "";
          search(btn.getAttribute("data-ns") || "", "namespace");
        });
      });
      home.querySelectorAll(".conn-approve").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-id");
          const r = await api("/api/connections/approve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pending_id: id }),
          });
          toast(r.ok ? `Approved ${r.nodes || 0} entities, ${r.relationships || 0} relationships` : (r.error || "Failed"), r.ok ? "success" : "error");
          loadHome();
        });
      });
      home.querySelectorAll(".conn-dismiss").forEach((btn) => {
        btn.addEventListener("click", async () => {
          await api("/api/connections/dismiss", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pending_id: btn.getAttribute("data-id") }),
          });
          loadHome();
        });
      });
    } catch (err) {
      home.innerHTML = `<p class="muted">Could not load Connections: ${esc(err.message || err)}</p>`;
      toast(String(err.message || err), "error");
    }
  }

  async function search(q, mode) {
    const out = $("connectionsSearchResults");
    const list = $("connectionsList");
    if (!out) return;
    const query = (q ?? $("connectionsSearchInput")?.value ?? "").trim();
    const m = mode || $("connectionsSearchMode")?.value || "all";
    out.classList.remove("hidden");
    if (list) list.classList.add("hidden");
    out.innerHTML = `<li class="muted">Searching…</li>`;
    const ns = m === "namespace" ? query : "";
    const data = await api(`/api/connections/search?q=${encodeURIComponent(m === "namespace" ? "" : query)}&mode=${encodeURIComponent(m)}&namespace=${encodeURIComponent(ns)}&limit=24`);
    const nodes = data.nodes || [];
    const rels = data.relationships || [];
    if (!nodes.length && !rels.length) {
      out.innerHTML = `<li class="muted">No connections. Try New entity (N) or Import text for review.</li>`;
      return;
    }
    out.innerHTML = [
      ...nodes.map((n) => `<li class="conn-row" role="option" tabindex="0" data-name="${esc(n.name)}" data-ns="${esc(n.namespace)}">
        <strong>${esc(n.name)}</strong> <span class="muted tiny">${esc(n.kind)} · ${esc(n.namespace)}</span>
        <div class="muted tiny">${provenanceLine(n)}</div>
      </li>`),
      ...rels.map((r) => `<li class="conn-hit">
        <strong>${esc(r.subject)}</strong> —${esc(r.predicate)}→ <strong>${esc(r.object)}</strong>
        <div class="muted tiny">${provenanceLine(r)}</div>
        <div class="conn-hit-actions">
          <button type="button" class="ghost-btn tiny conn-open-subj" data-name="${esc(r.subject)}" data-ns="${esc(r.namespace)}">Open</button>
          <button type="button" class="ghost-btn tiny conn-explain" data-s="${esc(r.subject)}" data-o="${esc(r.object)}">Explain</button>
          ${r.id ? `<button type="button" class="ghost-btn tiny conn-del-rel" data-id="${esc(r.id)}">Delete</button>` : ""}
        </div>
      </li>`),
    ].join("");
    out.querySelectorAll(".conn-row").forEach((row) => {
      row.addEventListener("click", () => openEntity(row.getAttribute("data-name"), row.getAttribute("data-ns")));
      row.addEventListener("keydown", (e) => {
        if (e.key === "Enter") openEntity(row.getAttribute("data-name"), row.getAttribute("data-ns"));
      });
    });
    out.querySelectorAll(".conn-open-subj").forEach((b) => b.addEventListener("click", () => openEntity(b.getAttribute("data-name"), b.getAttribute("data-ns"))));
    out.querySelectorAll(".conn-explain").forEach((b) => b.addEventListener("click", () => explain(b.getAttribute("data-s"), b.getAttribute("data-o"))));
    out.querySelectorAll(".conn-del-rel").forEach((b) => b.addEventListener("click", () => deleteRel(b.getAttribute("data-id"))));
  }

  async function browse() {
    const list = $("connectionsList");
    const out = $("connectionsSearchResults");
    out?.classList.add("hidden");
    list?.classList.remove("hidden");
    if (!list) return;
    list.innerHTML = `<li class="muted">Loading…</li>`;
    const data = await api("/api/connections/search?mode=entities&limit=40&q=");
    const collected = data.nodes || [];
    if (!collected.length) {
      list.innerHTML = `<li class="muted">No entities yet. Press <kbd>N</kbd> to create one, or Import text for review.</li>`;
      return;
    }
    list.innerHTML = collected.map((n) => `<li class="conn-row" role="option" tabindex="0" aria-selected="false" data-name="${esc(n.name)}" data-ns="${esc(n.namespace)}">
      <strong>${esc(n.name)}</strong> <span class="muted tiny">${esc(n.kind)} · ${esc(n.namespace)}</span>
    </li>`).join("");
    list.querySelectorAll(".conn-row").forEach((row) => {
      const open = () => {
        list.querySelectorAll(".conn-row").forEach((el) => {
          el.classList.remove("is-selected");
          el.setAttribute("aria-selected", "false");
        });
        row.classList.add("is-selected");
        row.setAttribute("aria-selected", "true");
        openEntity(row.getAttribute("data-name"), row.getAttribute("data-ns"));
      };
      row.addEventListener("click", open);
      row.addEventListener("keydown", (e) => {
        if (e.key === "Enter") open();
      });
    });
  }

  async function openEntity(name, ns) {
    selectedName = name || "";
    selectedNamespace = ns || "default";
    const panel = $("connectionsEntityPanel");
    if (!panel) return;
    panel.innerHTML = `<h4>Entity</h4><p class="muted">Loading…</p>`;
    const data = await api(`/api/connections/entity?name=${encodeURIComponent(name)}&namespace=${encodeURIComponent(ns || "")}`);
    if (!data.ok) {
      panel.innerHTML = `<h4>Entity</h4><p class="muted">${esc(data.error || "Not found")}</p>`;
      return;
    }
    const e = data.entity;
    const rels = data.relationships || [];
    panel.innerHTML = `
      <h4>${esc(e.name)}</h4>
      <dl class="conn-dl">
        <dt>Type</dt><dd>${esc(e.kind)}</dd>
        <dt>Namespace</dt><dd>${esc(e.namespace)}</dd>
        <dt>Description</dt><dd>${esc(e.description || "—")}</dd>
        <dt>Confidence</dt><dd>${esc(e.confidence)}</dd>
        <dt>Created</dt><dd>${esc(e.created_at || "—")}</dd>
        <dt>Updated</dt><dd>${esc(e.updated_at || "—")}</dd>
        <dt>Source</dt><dd>${esc(e.source)}</dd>
        <dt>Memory</dt><dd>${esc(e.memory_id || "—")}</dd>
      </dl>
      <p class="muted tiny">${provenanceLine(e)}</p>
      <h5>Relationships</h5>
      <ul class="conn-mini">${rels.map((r) => `<li>
        ${esc(r.subject)} —${esc(r.predicate)}→ ${esc(r.object)}
        <div class="muted tiny">${provenanceLine(r)}</div>
      </li>`).join("") || "<li class='muted'>None</li>"}</ul>
      <div class="conn-hit-actions">
        <button type="button" class="ghost-btn tiny" id="connOpenMemory">Open Memory</button>
        <button type="button" class="ghost-btn tiny" id="connOpenProjects">Open Projects</button>
        <button type="button" class="ghost-btn tiny" id="connOpenDocs">Open Documents</button>
        <button type="button" class="ghost-btn tiny" id="connOpenKnowledge">Knowledge Briefs</button>
        <button type="button" class="ghost-btn tiny" id="connDeleteEntity">Delete</button>
      </div>`;
    $("connOpenMemory")?.addEventListener("click", () => window.switchToView?.("memory"));
    $("connOpenProjects")?.addEventListener("click", () => window.switchToView?.("projects"));
    $("connOpenDocs")?.addEventListener("click", () => window.switchToView?.("documents"));
    $("connOpenKnowledge")?.addEventListener("click", () => {
      window.switchToView?.("documents");
      toast("Knowledge Briefs live with Documents / research — separate from Connections.", "info");
    });
    $("connDeleteEntity")?.addEventListener("click", () => deleteEntity(e.name, e.namespace));
  }

  async function deleteEntity(name, ns) {
    if (!name) {
      toast("Select an entity first", "error");
      return;
    }
    const r = await fetch(`/api/connections/entity?name=${encodeURIComponent(name)}&namespace=${encodeURIComponent(ns || "default")}`, { method: "DELETE" }).then((x) => x.json());
    if (r.ok) {
      lastUndo = r.undo_id || "";
      toast("Entity deleted — Undo available", "success");
      loadHome();
      browse();
    } else toast(r.error || "Delete failed", "error");
  }

  async function deleteRel(id) {
    const r = await fetch(`/api/connections/relationship?id=${encodeURIComponent(id)}`, { method: "DELETE" }).then((x) => x.json());
    if (r.ok) {
      lastUndo = r.undo_id || "";
      toast("Relationship deleted", "success");
      search();
      loadHome();
    } else toast(r.error || "Delete failed", "error");
  }

  async function explain(subject, object) {
    const r = await api(`/api/connections/explain?subject=${encodeURIComponent(subject)}&object=${encodeURIComponent(object)}`);
    const why = (r.explanations || []).map((e) => e.why).join("\n") || r.error || "No explanation";
    toast(why.slice(0, 280), r.ok ? "info" : "error");
    const dlg = $("connectionsExplainDialog");
    const body = $("connectionsExplainBody");
    if (dlg && body) {
      body.textContent = (r.explanations || []).map((e) => e.why).join("\n\n") || r.error || "";
      dlg.showModal?.();
    }
  }

  async function createEntityDialog() {
    const name = prompt("Entity name");
    if (!name) return;
    const kind = prompt("Type (person/place/organization/concept/project/entity)", "entity") || "entity";
    const r = await api("/api/connections/entity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, kind, source: "manual", confidence: 1, namespace: "default" }),
    });
    toast(r.ok ? `Created ${name}` : (r.error || "Failed"), r.ok ? "success" : "error");
    if (r.ok) {
      loadHome();
      openEntity(name, "default");
    }
  }

  async function importText() {
    const text = $("connectionsImportText")?.value?.trim();
    if (!text) {
      toast("Paste text to extract, then approve", "error");
      return;
    }
    const ns = $("connectionsImportNs")?.value?.trim() || "default";
    const r = await api("/api/connections/propose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, namespace: ns, source: "ai_suggestion" }),
    });
    toast(r.ok ? "Staged for review — approve on Home" : (r.error || "Failed"), r.ok ? "success" : "error");
    $("connectionsImportDialog")?.close?.();
    loadHome();
  }

  async function cleanup() {
    const prune = await api("/api/connections/prune", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    if (prune.ok) lastUndo = prune.undo_id || lastUndo;
    const q = await api("/api/connections/cleanup-queries", { method: "POST" });
    if (q.ok) lastUndo = q.undo_id || lastUndo;
    toast(`Pruned ${prune.pruned || 0}; cleaned queries namespace`, "success");
    loadHome();
  }

  async function runAssistant() {
    const r = await api("/api/connections/assistant");
    const box = $("connectionsAssistantBody");
    const dlg = $("connectionsAssistantDialog");
    if (!box || !dlg) return;
    const suggestions = r.suggestions || [];
    box.innerHTML = suggestions.length
      ? suggestions.map((s) => `<li><strong>${esc(s.type)}</strong> — ${esc(s.message)}</li>`).join("")
      : "<li class='muted'>No suggestions — graph looks clean.</li>";
    dlg.showModal?.();
  }

  async function undo() {
    const r = await api("/api/connections/undo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ undo_id: lastUndo || "" }),
    });
    toast(r.ok ? `Restored ${r.restored}` : (r.error || "Nothing to undo"), r.ok ? "success" : "error");
    loadHome();
    browse();
  }

  function showHelp() {
    toast("/ search · N new · Delete delete · Esc clear · ? help · arrows navigate", "info");
  }

  function initConnections() {
    if ($("connectionsView")?.dataset.ready) {
      loadHome();
      return;
    }
    if ($("connectionsView")) $("connectionsView").dataset.ready = "1";
    $("connectionsSearchBtn")?.addEventListener("click", () => search());
    $("connectionsSearchInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") search();
    });
    $("connectionsBrowseBtn")?.addEventListener("click", browse);
    $("connectionsImportBtn")?.addEventListener("click", () => $("connectionsImportDialog")?.showModal?.());
    $("connectionsImportSubmit")?.addEventListener("click", (e) => {
      e.preventDefault();
      importText();
    });
    $("connectionsCleanupBtn")?.addEventListener("click", cleanup);
    $("connectionsAssistantBtn")?.addEventListener("click", runAssistant);
    $("connectionsUndoBtn")?.addEventListener("click", undo);
    $("connectionsHelpBtn")?.addEventListener("click", showHelp);
    $("connectionsNewBtn")?.addEventListener("click", createEntityDialog);
    $("connectionsClearBtn")?.addEventListener("click", () => {
      if ($("connectionsSearchInput")) $("connectionsSearchInput").value = "";
      $("connectionsSearchResults")?.classList.add("hidden");
      $("connectionsList")?.classList.remove("hidden");
      browse();
    });
    document.addEventListener("keydown", (e) => {
      const view = $("connectionsView");
      if (!view || view.classList.contains("hidden")) return;
      const tag = (e.target?.tagName || "").toLowerCase();
      const typing = tag === "input" || tag === "textarea" || e.target?.isContentEditable;
      if (e.key === "Escape") {
        $("connectionsImportDialog")?.close?.();
        $("connectionsAssistantDialog")?.close?.();
        $("connectionsExplainDialog")?.close?.();
        if (!typing) $("connectionsClearBtn")?.click();
        return;
      }
      if (typing) return;
      if (e.key === "/") {
        e.preventDefault();
        $("connectionsSearchInput")?.focus();
      } else if (e.key === "n" || e.key === "N") {
        e.preventDefault();
        createEntityDialog();
      } else if (e.key === "Delete" || e.key === "Backspace") {
        if (selectedName) {
          e.preventDefault();
          deleteEntity(selectedName, selectedNamespace);
        }
      } else if (e.key === "?" || (e.shiftKey && e.key === "/")) {
        e.preventDefault();
        showHelp();
      } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        const items = [...document.querySelectorAll("#connectionsList .conn-row, #connectionsSearchResults .conn-row")];
        if (!items.length) return;
        e.preventDefault();
        const idx = items.findIndex((el) => el.classList.contains("is-selected"));
        const next = e.key === "ArrowDown" ? Math.min(items.length - 1, idx + 1) : Math.max(0, idx < 0 ? 0 : idx - 1);
        items.forEach((el) => el.classList.remove("is-selected"));
        items[next]?.classList.add("is-selected");
        items[next]?.focus();
      }
    });
    loadHome();
    browse();
  }

  window.initConnections = initConnections;
})();
