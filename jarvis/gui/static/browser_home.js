/** Browser Home — overview / history / bookmarks / security (not Chat or Documents). */
(function () {
  "use strict";

  let _data = null;
  let _tab = "overview";
  const TABS = [
    ["overview", "Overview"],
    ["session", "Session"],
    ["history", "History"],
    ["bookmarks", "Bookmarks"],
    ["downloads", "Downloads"],
    ["notes", "Notes"],
    ["research", "Research"],
    ["security", "Security"],
  ];

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  async function api(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || data.detail || data.error || res.statusText);
    }
    return data;
  }

  function renderTabs() {
    const nav = $("browserHomeTabs");
    if (!nav) return;
    nav.innerHTML = TABS.map(
      ([id, label]) =>
        `<button type="button" class="mc-tab${_tab === id ? " active" : ""}" data-browser-tab="${id}" role="tab" aria-selected="${_tab === id}">${label}</button>`
    ).join("");
  }

  function renderOverview() {
    const st = _data.status || {};
    const modes = _data.modes || {};
    const hist = (_data.history || [])
      .slice(0, 5)
      .map((h) => `<li><button type="button" class="ghost-btn tiny" data-browser-open-url="${esc(h.url)}">${esc(h.title || h.url)}</button></li>`)
      .join("") || "<li class=\"muted\">No history yet.</li>";
    return `
      <section class="coding-hero" aria-label="Browser status">
        <p class="coding-banner ${st.agent_ready ? "coding-banner--ok" : "coding-banner--warn"}">
          ${st.agent_ready ? "Playwright ready" : esc(st.playwright_hint || "Playwright not ready")}
          · status <strong>${esc(st.status || "idle")}</strong>
          ${st.session_active ? " · session live" : ""}
        </p>
        <dl class="coding-meta">
          <div><dt>Profile</dt><dd>${esc(st.profile || "_default")}</dd></div>
          <div><dt>URL</dt><dd><code>${esc(st.url || "—")}</code></dd></div>
          <div><dt>DOM</dt><dd>${modes.dom ? "available" : "unavailable"}</dd></div>
          <div><dt>VLM</dt><dd>${modes.vlm ? "available" : "unavailable"}</dd></div>
        </dl>
        <p class="muted tiny">${esc(_data.philosophy || "")}</p>
      </section>
      <section>
        <h3>Recent history</h3>
        <ul class="coding-list">${hist}</ul>
      </section>`;
  }

  function renderSession() {
    return `<p class="muted">Live controls are below in the session panel. Use Open / Run / Pause / Takeover there.</p>
      <pre class="coding-pre muted">${esc(JSON.stringify(_data.session || {}, null, 2))}</pre>`;
  }

  function renderHistory() {
    const items = (_data.history || [])
      .map(
        (h) =>
          `<li><code>${esc(h.url)}</code> ${esc(h.title || "")}
            <button type="button" class="ghost-btn tiny" data-browser-open-url="${esc(h.url)}">Open</button></li>`
      )
      .join("") || "<li class=\"muted\">No visits recorded.</li>";
    return `<ul class="coding-list">${items}</ul>`;
  }

  function renderBookmarks() {
    const items = (_data.bookmarks || [])
      .map(
        (b) =>
          `<li><strong>${esc(b.title)}</strong> <code>${esc(b.url)}</code>
            <button type="button" class="ghost-btn tiny" data-browser-open-url="${esc(b.url)}">Open</button>
            <button type="button" class="ghost-btn tiny" data-browser-unbook="${esc(b.url)}">Remove</button></li>`
      )
      .join("") || "<li class=\"muted\">No bookmarks.</li>";
    return `<ul class="coding-list">${items}</ul>`;
  }

  function renderDownloads() {
    const items = (_data.downloads || [])
      .map((d) => `<li><code>${esc(d.name)}</code> <span class="muted">${esc(String(d.size || 0))} B</span></li>`)
      .join("") || "<li class=\"muted\">No downloads in Browser download dir yet.</li>";
    const dir = (_data.security || {}).download_dir || "";
    return `<p class="muted tiny">Dir: <code>${esc(dir)}</code> — downloads are gated; never silent.</p>
      <ul class="coding-list">${items}</ul>`;
  }

  function renderNotes() {
    const items = (_data.notes || [])
      .map((n) => `<li>${esc(n.text)} <span class="muted tiny">${esc(n.url || "")}</span></li>`)
      .join("") || "<li class=\"muted\">No operator notes yet.</li>";
    return `
      <label class="muted tiny" for="browserNoteInput">Operator note</label>
      <textarea id="browserNoteInput" rows="3" aria-label="Operator note"></textarea>
      <button type="button" class="ghost-btn small" id="browserNoteSaveBtn">Save note</button>
      <ul class="coding-list">${items}</ul>`;
  }

  function renderResearch() {
    return `
      <p class="muted">Multi-tab research is operator-controlled — never an autonomous fleet.</p>
      <input type="text" id="browserResearchGoal" placeholder="Research goal" aria-label="Research goal" />
      <input type="text" id="browserResearchUrls" placeholder="URLs comma-separated" aria-label="Research URLs" />
      <button type="button" class="ghost-btn small" id="browserResearchPlanBtn">Plan tabs</button>
      <button type="button" class="ghost-btn small" id="browserResearchMergeBtn">Merge findings</button>
      <pre id="browserResearchOut" class="coding-pre muted"></pre>`;
  }

  function renderSecurity() {
    const sec = _data.security || {};
    return `<ul class="coding-list">
      <li>SSRF / private network guard: ${sec.ssrf_guard ? "on" : "off"}</li>
      <li>Checkout/payment heuristics: ${sec.checkout_heuristics ? "on" : "off"}</li>
      <li>Downloads gated: ${sec.downloads_gated ? "on" : "off"}</li>
    </ul>
    <p class="muted tiny">Risky URLs require allow_risky confirmation. Voice cannot buy or pay.</p>`;
  }

  function renderBody() {
    if (_tab === "overview") return renderOverview();
    if (_tab === "session") return renderSession();
    if (_tab === "history") return renderHistory();
    if (_tab === "bookmarks") return renderBookmarks();
    if (_tab === "downloads") return renderDownloads();
    if (_tab === "notes") return renderNotes();
    if (_tab === "research") return renderResearch();
    if (_tab === "security") return renderSecurity();
    return renderOverview();
  }

  function bindBody() {
    const body = $("browserHomeBody");
    if (!body) return;
    body.querySelectorAll("[data-browser-open-url]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const url = btn.getAttribute("data-browser-open-url");
        if ($("browserUrlInput")) $("browserUrlInput").value = url;
        window.browserNavigate?.(url);
      });
    });
    body.querySelectorAll("[data-browser-unbook]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await fetch("/api/browser/bookmarks/remove", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: btn.getAttribute("data-browser-unbook") }),
        });
        await refresh();
      });
    });
    $("browserResearchPlanBtn")?.addEventListener("click", async () => {
      const goal = $("browserResearchGoal")?.value || "";
      const urls = ($("browserResearchUrls")?.value || "").split(",").map((s) => s.trim()).filter(Boolean);
      const out = await api("/api/browser/research/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal, urls }),
      });
      if ($("browserResearchOut")) $("browserResearchOut").textContent = JSON.stringify(out, null, 2);
    });
    $("browserResearchMergeBtn")?.addEventListener("click", async () => {
      const out = await api("/api/browser/research/merge");
      if ($("browserResearchOut")) $("browserResearchOut").textContent = out.merged || "";
    });
    $("browserNoteSaveBtn")?.addEventListener("click", async () => {
      const text = $("browserNoteInput")?.value || "";
      if (!text.trim()) return;
      await api("/api/browser/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, url: $("browserUrlInput")?.value || "" }),
      });
      await refresh();
    });
  }

  async function refresh() {
    const status = $("browserHomeStatus");
    if (status) status.textContent = "Loading…";
    try {
      _data = await api("/api/browser/home");
      renderTabs();
      const body = $("browserHomeBody");
      if (body) body.innerHTML = renderBody();
      bindBody();
      if (status) status.textContent = "Ready";
    } catch (err) {
      if (status) status.textContent = err.message || "Failed";
    }
  }

  function initTabs() {
    $("browserHomeTabs")?.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-browser-tab]");
      if (!btn) return;
      _tab = btn.getAttribute("data-browser-tab") || "overview";
      renderTabs();
      const body = $("browserHomeBody");
      if (body) body.innerHTML = renderBody();
      bindBody();
    });
    $("browserHomeRefreshBtn")?.addEventListener("click", refresh);
    $("browserOpenProjectsBtn")?.addEventListener("click", () => window.switchToView?.("projects"));
    $("browserOpenJobsBtn")?.addEventListener("click", () => window.jarvisJobs?.openJobCenter?.());
    $("browserOpenCodingBtn")?.addEventListener("click", () => window.openCodingHome?.() || window.switchToView?.("coding"));
  }

  window.initBrowserHome = function () {
    if (!$("browserHomeBody")) return;
    initTabs();
    refresh();
  };

  window.refreshBrowserHome = refresh;

  window.openBrowserHome = function (tab) {
    window.switchToView?.("browser");
    if (tab) _tab = tab;
    window.initBrowserHome?.();
    window.initBrowserPanel?.();
  };
})();
