/** Search Home — federated browse UI over the one Search engine. */
(function () {
  "use strict";

  let _home = null;
  let _facet = "everything";
  let _selected = "";
  let _codeMode = "auto";
  let _busy = false;
  /** Monotonic generation — prevents stale loadHome/runQuery from overwriting a newer owner query. */
  let _gen = 0;

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  async function api(path, opts) {
    const res = await fetch(path, opts);
    return res.json();
  }

  function renderMentalModel(mm) {
    const el = $("searchMentalModel");
    if (!el || !mm) return;
    el.innerHTML = [
      ["Sidebar", mm.sidebar],
      ["Ctrl+K", mm.palette],
      ["Search Home", mm.search_home],
      ["Chat", mm.chat],
      ["Voice", mm.voice],
      ["Products", mm.products],
    ]
      .map(
        ([k, v]) =>
          `<div class="search-mm-item"><strong>${esc(k)}</strong><span class="muted small">${esc(v)}</span></div>`
      )
      .join("");
  }

  function renderFacets(facets) {
    const bar = $("searchFacetBar");
    if (!bar) return;
    const list = facets && facets.length ? facets : ["everything"];
    bar.innerHTML = list
      .map((f) => {
        const active = f === _facet ? " is-active" : "";
        return `<button type="button" class="search-facet-chip${active}" data-facet="${esc(f)}" aria-pressed="${f === _facet}">${esc(f.replace(/_/g, " "))}</button>`;
      })
      .join("");
  }

  function renderHealth(health, recovery) {
    const el = $("searchHealthStrip");
    if (!el) return;
    const web = health?.web || {};
    el.innerHTML = `
      <span>State <strong>${esc(health?.state || "idle")}</strong></span>
      <span>Corpora <strong>${esc(health?.corpora_enabled ?? "—")}</strong></span>
      <span>Web <strong>${esc(web.backend || "—")}</strong></span>
      <span>Latency <strong>${esc(health?.last_latency_ms ?? "—")} ms</strong></span>
      <span>${recovery?.ready ? "✓ Ready" : esc(recovery?.hint || "Recovery needed")}</span>
    `;
  }

  function renderHistory(items) {
    const el = $("searchHistoryList");
    if (!el) return;
    if (!items?.length) {
      el.innerHTML = `<li class="muted">No recent searches.</li>`;
      return;
    }
    el.innerHTML = items
      .slice(0, 12)
      .map(
        (h) =>
          `<li><button type="button" class="ghost-btn tiny search-hist-btn" data-q="${esc(h.query)}">${esc(h.query)}</button>
           <span class="muted tiny">${h.hit_count ?? 0} hits · ${h.latency_ms ?? 0} ms</span></li>`
      )
      .join("");
  }

  function renderSaved(items) {
    const el = $("searchSavedList");
    if (!el) return;
    if (!items?.length) {
      el.innerHTML = `<li class="muted">No saved searches.</li>`;
      return;
    }
    el.innerHTML = items
      .map(
        (s) =>
          `<li><button type="button" class="ghost-btn tiny search-saved-btn" data-q="${esc(s.query)}">${esc(s.name || s.query)}</button>
           <button type="button" class="ghost-btn tiny search-saved-del" data-id="${esc(s.id)}" aria-label="Delete saved search">✕</button></li>`
      )
      .join("");
  }

  function renderResults(results, meta) {
    const list = $("searchResultsList");
    const status = $("searchResultsStatus");
    const failures = Array.isArray(meta?.failures) ? meta.failures : [];
    const failureText = failures
      .map((f) => `${f.corpus || "corpus"}: ${f.error || "failed"}`)
      .join(" · ");
    if (status) {
      // Never leave "Searching…" on screen once results (or an empty final set) exist.
      if (_busy && !(results && results.length)) status.textContent = "Searching…";
      else if (failureText && meta?.ok === false) status.textContent = `Search failed · ${failureText}`;
      else if (!results?.length) status.textContent = meta?.query ? `No matches.${failureText ? ` Partial failure: ${failureText}` : ""}` : "Enter a query to browse federated results.";
      else {
        const searched = Array.isArray(meta?.searched) ? meta.searched.join(", ") : "";
        status.textContent = `${results.length} result(s)${meta?.latency_ms != null ? ` · ${meta.latency_ms} ms` : ""}${searched ? ` · ${searched}` : ""}${failureText ? ` · Warnings: ${failureText}` : ""}`;
      }
    }
    if (!list) return;
    if (!results?.length) {
      list.innerHTML = `<li class="search-empty muted" role="status">No results yet. Try Documents, Memory, Code, or Web facets.</li>`;
      $("searchResultDetail").innerHTML = `<p class="muted">Select a result for preview, confidence, and open-in-context.</p>`;
      return;
    }
    list.innerHTML = results
      .map((r) => {
        const sel = r.id === _selected ? " is-selected" : "";
        const conf = typeof r.confidence === "number" ? Math.round(r.confidence * 100) : "—";
        return `<li class="search-result-item${sel}" role="option" tabindex="0" data-id="${esc(r.id)}" aria-selected="${r.id === _selected}">
          <div class="search-result-row">
            <span class="search-source-chip">${esc(r.source_label || r.source)}</span>
            <strong>${esc(r.title)}</strong>
            <span class="muted tiny">${conf}%</span>
          </div>
          <div class="muted small search-result-preview">${esc((r.preview || r.summary || "").slice(0, 160))}</div>
        </li>`;
      })
      .join("");
    const sel = results.find((r) => r.id === _selected) || results[0];
    if (sel) {
      _selected = sel.id;
      renderDetail(sel, meta);
    }
  }

  function renderDetail(r, meta) {
    const el = $("searchResultDetail");
    if (!el || !r) return;
    const open = r.open || {};
    const highlights = (r.highlights || []).map((h) => `<code>${esc(h)}</code>`).join(" ");
    el.innerHTML = `
      <div class="search-detail-head">
        <span class="search-source-chip">${esc(r.source_label || r.source)}</span>
        <h3>${esc(r.title)}</h3>
      </div>
      <p class="search-detail-preview">${esc(r.preview || r.summary || "")}</p>
      <p class="muted small">Location: <code>${esc(r.location || "—")}</code></p>
      <p class="muted small">Score ${esc(r.score)} · confidence ${esc(r.confidence)} · ${esc(r.strategy || "")}</p>
      ${highlights ? `<p class="small">Highlights: ${highlights}</p>` : ""}
      <div class="search-detail-actions">
        <button type="button" class="apply-btn small" id="searchOpenResultBtn" data-id="${esc(r.id)}">Open in context</button>
        <button type="button" class="ghost-btn small" id="searchOpenWithQueryBtn" data-id="${esc(r.id)}">Open with query</button>
        ${
          r.source === "web" || open.handoff === "web_search"
            ? `<button type="button" class="ghost-btn small" id="searchWebChatBtn">Synthesize in Chat</button>`
            : ""
        }
      </div>
      ${meta?.web_handoff ? `<p class="muted small">${esc(meta.web_handoff.hint || "")}</p>` : ""}
    `;
  }

  function findResult(id) {
    const results = _home?.results || _home?.search?.results || [];
    return results.find((r) => r.id === id);
  }

  function openResult(r, withQuery) {
    if (!r) return;
    const open = r.open || {};
    const q = withQuery ? $("searchHomeInput")?.value?.trim() || open.query || "" : open.query || "";
    const hit = {
      source_type: r.source,
      title: r.title,
      excerpt: r.preview,
      location: r.location,
      query: q,
      raw: { open: { ...open, query: q }, id: open.id || r.id, confidence: r.confidence },
    };
    // Reuse palette openHit if available via command palette module internals — fallback switch
    if (typeof window.__ariaOpenSearchHit === "function") {
      window.__ariaOpenSearchHit(hit);
      return;
    }
    const view = open.view || "search";
    if (open.handoff === "web_search" || r.source === "web") {
      window.AriaActions?.askAria?.(q || r.title, { autoSend: true, switchView: true });
      return;
    }
    window.switchToView?.(view);
    setTimeout(() => {
      const selectors = [
        "documentsSearchInput",
        "memorySearch",
        "journalSearch",
        "connectionsSearchInput",
        "gallerySearchInput",
        "audioSearchInput",
        "plannerSearchInput",
        "flytyingSearchInput",
      ];
      for (const id of selectors) {
        const el = $(id);
        if (el && q) {
          el.value = q;
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.focus();
          break;
        }
      }
    }, 100);
  }

  async function runQuery() {
    const q = $("searchHomeInput")?.value?.trim() || "";
    if (!q) {
      renderResults([], {});
      return;
    }
    const gen = ++_gen;
    _busy = true;
    renderResults([], { query: q });
    try {
      const body = {
        query: q,
        facets: _facet && _facet !== "everything" ? [_facet] : null,
        code_mode: _codeMode,
        mode: $("searchModeSelect")?.value || "browse",
        limit: 24,
      };
      const data = await api("/api/search/product/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (gen !== _gen) return; // newer owner query won the race
      _home = { ...(_home || {}), results: data.results || [], search: data, query: q };
      _selected = (data.results && data.results[0]?.id) || "";
      _busy = false;
      renderResults(data.results || [], data);
      renderHistory((await api("/api/search/product/history?limit=20")).history || []);
      if (gen !== _gen) return;
      if (Array.isArray(data.failures) && data.failures.length) {
        const msg = data.failures
          .slice(0, 3)
          .map((f) => `${f.corpus || "corpus"}: ${f.error || "failed"}`)
          .join(" · ");
        window.showAriaToast?.(`Search warning: ${msg}`, data.ok === false ? "error" : "warn", 7000);
      }
      if (data.web_handoff && _facet === "web") {
        window.showAriaToast?.("Web facet ready — synthesize in Chat for an answer with sources", "info");
      }
    } catch (err) {
      if (gen !== _gen) return;
      if ($("searchResultsStatus")) $("searchResultsStatus").textContent = err?.message || "Search failed";
    } finally {
      if (gen === _gen) _busy = false;
    }
  }

  async function loadHome() {
    const q = $("searchHomeInput")?.value?.trim() || "";
    // Capture generation — do NOT bump _gen here. Bumping would cancel an in-flight
    // owner runQuery and can leave the UI stuck on "Searching…".
    const genAtStart = _gen;
    const data = await api(`/api/search/product/home?q=${encodeURIComponent(q)}&facet=${encodeURIComponent(_facet)}`);
    if (genAtStart !== _gen) {
      // Owner started a newer query; still refresh chrome chrome-only fields if safe
      return;
    }
    _home = { ...(_home || {}), ...data, results: data.results || _home?.results || [] };
    renderMentalModel(data.mental_model);
    renderFacets(data.facets);
    renderHealth(data.health, data.recovery);
    renderHistory(data.history);
    renderSaved(data.saved);
    const qNow = $("searchHomeInput")?.value?.trim() || "";
    if (_busy) {
      // Owner query in flight — never overwrite results/status
    } else if (q && qNow === q) {
      _selected = (data.results && data.results[0]?.id) || "";
      renderResults(data.results || [], data.search || { query: q });
    } else if (!qNow) {
      renderResults([], {});
    }
    const tips = $("searchTipsList");
    if (tips && data.tips) {
      tips.innerHTML = data.tips.map((t) => `<li>${esc(t)}</li>`).join("");
    }
  }

  function bind() {
    if ($("searchHomeRoot")?.dataset.bound === "1") return;
    if ($("searchHomeRoot")) $("searchHomeRoot").dataset.bound = "1";

    $("searchHomeRunBtn")?.addEventListener("click", () => runQuery());
    $("searchHomeInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        runQuery();
      }
    });
    $("searchHomeRefreshBtn")?.addEventListener("click", () => loadHome());
    $("searchDiagBtn")?.addEventListener("click", async () => {
      const d = await api("/api/search/product/diagnostics");
      window.showAriaToast?.(`Search diagnostics · ${d.health?.state || "ok"} · ${d.corpora?.length || 0} corpora`, "info");
      console.info("Search diagnostics", d);
    });
    $("searchSaveBtn")?.addEventListener("click", async () => {
      const q = $("searchHomeInput")?.value?.trim();
      if (!q) return;
      await api("/api/search/product/saved", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, facets: _facet !== "everything" ? [_facet] : [] }),
      });
      renderSaved((await api("/api/search/product/saved")).saved || []);
      window.showAriaToast?.("Search saved", "ok");
    });
    $("searchClearHistoryBtn")?.addEventListener("click", async () => {
      await api("/api/search/product/history", { method: "DELETE" });
      renderHistory([]);
    });
    $("searchCodeModeSelect")?.addEventListener("change", (e) => {
      _codeMode = e.target.value || "auto";
    });
    $("searchFacetBar")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-facet]");
      if (!btn) return;
      _facet = btn.getAttribute("data-facet") || "everything";
      renderFacets(_home?.facets || []);
      runQuery();
    });
    $("searchResultsList")?.addEventListener("click", (e) => {
      const li = e.target.closest("[data-id]");
      if (!li) return;
      _selected = li.getAttribute("data-id");
      const r = findResult(_selected);
      renderResults(_home?.results || [], _home?.search || {});
      renderDetail(r, _home?.search);
    });
    $("searchResultsList")?.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const li = e.target.closest("[data-id]");
      if (!li) return;
      e.preventDefault();
      _selected = li.getAttribute("data-id");
      openResult(findResult(_selected), true);
    });
    $("searchResultDetail")?.addEventListener("click", (e) => {
      if (e.target.id === "searchOpenResultBtn") openResult(findResult(e.target.dataset.id), false);
      if (e.target.id === "searchOpenWithQueryBtn") openResult(findResult(e.target.dataset.id), true);
      if (e.target.id === "searchWebChatBtn") {
        const q = $("searchHomeInput")?.value?.trim();
        window.AriaActions?.askAria?.(q || "web search", { autoSend: true, switchView: true });
      }
    });
    $("searchHistoryList")?.addEventListener("click", (e) => {
      const btn = e.target.closest(".search-hist-btn");
      if (!btn) return;
      if ($("searchHomeInput")) $("searchHomeInput").value = btn.getAttribute("data-q") || "";
      runQuery();
    });
    $("searchSavedList")?.addEventListener("click", async (e) => {
      const del = e.target.closest(".search-saved-del");
      if (del) {
        await api(`/api/search/product/saved/${encodeURIComponent(del.dataset.id)}`, { method: "DELETE" });
        renderSaved((await api("/api/search/product/saved")).saved || []);
        return;
      }
      const btn = e.target.closest(".search-saved-btn");
      if (!btn) return;
      if ($("searchHomeInput")) $("searchHomeInput").value = btn.getAttribute("data-q") || "";
      runQuery();
    });
    $("searchOptInGallery")?.addEventListener("change", async (e) => {
      await api("/api/search/product/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opt_in_corpora: { gallery: !!e.target.checked } }),
      });
    });
    $("searchOptInHa")?.addEventListener("change", async (e) => {
      await api("/api/search/product/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opt_in_corpora: { home_assistant: !!e.target.checked } }),
      });
    });
  }

  async function initSearchHome(force) {
    bind();
    const settings = await api("/api/search/product/settings");
    if ($("searchOptInGallery")) $("searchOptInGallery").checked = !!settings.opt_in_corpora?.gallery;
    if ($("searchOptInHa")) $("searchOptInHa").checked = !!settings.opt_in_corpora?.home_assistant;
    if ($("searchCodeModeSelect")) $("searchCodeModeSelect").value = settings.code_mode || "auto";
    _codeMode = settings.code_mode || "auto";
    await loadHome();
    if (force) $("searchHomeInput")?.focus();
  }

  window.initSearchHome = initSearchHome;
  window.runSearchHomeQuery = runQuery;
})();
