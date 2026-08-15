/** Projects — Workspace Identity Layer (not a PM tool) */

function $(id) {
  return document.getElementById(id);
}

async function p2Fetch(url, opts = {}) {
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || res.statusText || "Request failed");
  return data;
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

let projectsState = { home: null, filter: "", selected: "" };
let projectsShortcutsBound = false;

function effectsChecklist(effects) {
  if (!effects) return "";
  const rows = [
    ["Coding Root", effects.coding_root],
    ["Memory Namespace", effects.memory_namespace],
    ["Knowledge Namespace", effects.knowledge_namespace],
    ["Browser Session", effects.browser_session],
    ["Current Checkpoint", effects.checkpoint],
    ["Git Repository", effects.git_repository],
    ["Active Workspace", effects.workspace],
  ];
  return `<ul class="proj-effects" aria-label="Active workspace effects">${rows
    .map(
      ([label, val]) =>
        `<li><span class="proj-effect-check" aria-hidden="true">✓</span> <strong>${esc(label)}</strong> <code>${esc(val || "—")}</code></li>`
    )
    .join("")}</ul>`;
}

function renderProjectList(home) {
  const list = $("projectsList");
  if (!list) return;
  const active = home.active || "";
  const q = (projectsState.filter || "").toLowerCase();
  let projects = home.projects || [];
  if (q) {
    projects = projects.filter((p) =>
      `${p.title || ""} ${p.slug || ""} ${p.description || ""}`.toLowerCase().includes(q)
    );
  }
  if (!projects.length) {
    list.innerHTML = `<li class="muted proj-empty">No projects yet.
      <button type="button" class="ghost-btn tiny" id="projectsEmptyCreateBtn">Create</button>
      or ask Chat: <em>create project named …</em></li>`;
    list.querySelector("#projectsEmptyCreateBtn")?.addEventListener("click", () => {
      $("projectsTitleInput")?.focus();
    });
    return;
  }
  list.innerHTML = "";
  for (const p of projects) {
    const li = document.createElement("li");
    li.className = `proj-list-item${p.slug === active ? " is-active" : ""}${p.slug === projectsState.selected ? " is-selected" : ""}`;
    li.tabIndex = 0;
    li.dataset.slug = p.slug;
    li.innerHTML = `<div class="proj-list-main">
        <strong>${esc(p.title || p.slug)}</strong>
        <span class="muted">(${esc(p.slug)})</span>
        ${p.slug === active ? '<span class="ok proj-badge">active</span>' : ""}
        ${p.archived ? '<span class="warn proj-badge">archived</span>' : ""}
      </div>
      <div class="proj-list-meta muted">${esc(p.git_path || p.description || "workspace")}</div>`;
    li.addEventListener("click", () => selectProject(p.slug));
    li.addEventListener("keydown", (e) => {
      if (e.key === "Enter") selectProject(p.slug);
    });
    list.appendChild(li);
  }
}

async function selectProject(slug) {
  projectsState.selected = slug;
  await loadProjectHome(slug);
}

async function switchTo(slug) {
  const data = await p2Fetch("/api/projects/switch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slug }),
  });
  const msg = data.message || `Project: ${slug}`;
  window.showAriaToast?.(msg.split("\n")[0].replace(/\*\*/g, ""), data.ok === false ? "warn" : "ok", 4500);
  await loadProjectHome(slug);
  return data;
}

function renderHome(home) {
  const root = $("projectsHome");
  if (!root) return;
  projectsState.home = home;

  const activeEl = $("projectsActive");
  if (activeEl) {
    activeEl.textContent = home.active
      ? `Active workspace: ${home.active}`
      : "No active project — pick one or create below.";
  }

  renderProjectList(home);

  const p = home.project;
  if (!p) {
    root.innerHTML = `<div class="proj-empty-home">
      <p class="muted">Select or create a project to enter its workspace room — coding, memory, journal, knowledge, and AI in one identity.</p>
      ${effectsChecklist(home.effects)}
    </div>`;
    return;
  }

  const id = home.identity || {};
  const today = home.today || {};
  const coding = home.coding || {};
  const ai = home.ai_context || {};
  const journal = home.journal || {};
  const memory = home.memory || {};
  const knowledge = home.knowledge || {};
  const isActive = home.is_active;

  root.innerHTML = `
    <header class="proj-home-header">
      <div>
        <h3 class="proj-home-title">${esc(p.title || p.slug)}</h3>
        <p class="muted proj-home-tagline">Workspace identity — not a task board. One slug, one room.</p>
      </div>
      <div class="proj-home-actions">
        ${
          isActive
            ? `<button type="button" class="ghost-btn small" disabled>Active</button>`
            : `<button type="button" class="apply-btn small" data-act="switch">Switch here</button>`
        }
        <button type="button" class="apply-btn small" data-act="continue">Continue Project</button>
        <button type="button" class="ghost-btn small" data-act="briefing">Briefing</button>
      </div>
    </header>

    <section class="proj-panel proj-effects-panel" aria-label="What switching does">
      <h4>Active effects</h4>
      <p class="muted tiny">Switching projects updates every subsystem below.</p>
      ${effectsChecklist(home.effects)}
    </section>

    <div class="proj-home-grid">
      <section class="proj-panel">
        <h4>Project</h4>
        <dl class="proj-dl">
          <dt>Name</dt><dd>${esc(p.title || p.slug)}</dd>
          <dt>Slug</dt><dd><code>${esc(p.slug)}</code></dd>
          <dt>Status</dt><dd>${p.archived ? "archived" : "active"}</dd>
          <dt>Description</dt><dd>${esc(p.description || "—")}</dd>
          <dt>Git</dt><dd><code>${esc(p.git_path || "—")}</code></dd>
          <dt>Workspace</dt><dd><code>${esc((p.paths && p.paths.root) || id.workspace_root || "—")}</code></dd>
          <dt>Created</dt><dd>${esc(p.created || "—")}</dd>
          <dt>Last opened</dt><dd>${esc(p.last_opened || "—")}</dd>
        </dl>
        ${(home.recent_activity || []).length ? `<p class="muted tiny">${(home.recent_activity || []).map(esc).join(" · ")}</p>` : ""}
      </section>

      <section class="proj-panel">
        <h4>Continue working</h4>
        <div class="proj-continue-grid">
          ${(home.continue_working || [])
            .map(
              (a) =>
                `<button type="button" class="ghost-btn small" data-continue="${esc(a.id)}" data-view="${esc(a.view || "")}" data-tab="${esc(a.tab || "")}">${esc(a.label)}</button>`
            )
            .join("")}
        </div>
      </section>

      <section class="proj-panel">
        <h4>Today's workspace</h4>
        <p><strong>Journal</strong> ${esc(today.journal_preview || "—")}</p>
        <p><strong>Commits</strong></p>
        <ul class="proj-mini-list">${
          (today.recent_commits || []).length
            ? (today.recent_commits || []).map((c) => `<li><code>${esc(c)}</code></li>`).join("")
            : "<li class='muted'>None today</li>"
        }</ul>
        <p><strong>Open files</strong> ${(today.open_files || []).map(esc).join(", ") || "—"}</p>
        <p><strong>Memories</strong></p>
        <ul class="proj-mini-list">${
          (today.recent_memories || []).length
            ? (today.recent_memories || []).map((m) => `<li>${esc(m)}</li>`).join("")
            : "<li class='muted'>None</li>"
        }</ul>
        ${(today.pending_candidates || []).length
          ? `<p><strong>Candidates</strong> ${today.pending_candidates.length} pending — <button type="button" class="ghost-btn tiny" data-view="memory">Review in Memory</button></p>`
          : ""}
      </section>

      <section class="proj-panel">
        <h4>Coding</h4>
        <dl class="proj-dl">
          <dt>Repository</dt><dd><code>${esc(coding.repository)}</code></dd>
          <dt>Branch</dt><dd>${esc(coding.branch)}</dd>
          <dt>Status</dt><dd><pre class="proj-pre">${esc(coding.git_status)}</pre></dd>
          <dt>Coding root</dt><dd><code>${esc(coding.coding_root)}</code></dd>
          <dt>Knowledge index</dt><dd>${esc(coding.knowledge_index)}</dd>
          <dt>Workspace session</dt><dd><code>${esc(coding.workspace_session)}</code></dd>
        </dl>
        <p class="muted tiny">Coding Workspace Identity stays on the project — Layouts only control shell presentation.</p>
      </section>

      <section class="proj-panel" id="projectsLayoutOffer">
        <h4>Layouts</h4>
        <p class="muted tiny" id="projectsLayoutOfferBody">Checking optional layout recommendation…</p>
      </section>

      <section class="proj-panel">
        <h4>AI context</h4>
        <p><strong>Checkpoint</strong></p>
        <pre class="proj-pre">${esc(ai.checkpoint)}</pre>
        <p class="muted tiny">Memory NS <code>${esc(ai.memory_namespace)}</code> · Knowledge <code>${esc(ai.knowledge_namespace)}</code></p>
        <button type="button" class="ghost-btn tiny" data-view="memory">Open Memory</button>
      </section>

      <section class="proj-panel">
        <h4>Journal</h4>
        <p>${journal.today_bullets || 0} bullet(s) today · ${journal.day_count || 0} day(s) total</p>
        <p class="muted tiny">Recent: ${(journal.recent_days || []).slice(0, 5).map(esc).join(", ") || "—"}</p>
        <button type="button" class="ghost-btn small" data-continue="journal" data-view="journal" data-tab="projects">Open project journal</button>
      </section>

      <section class="proj-panel">
        <h4>Memory</h4>
        <p>Namespace <code>${esc(memory.namespace || id.memory_namespace)}</code></p>
        <ul class="proj-mini-list">${
          (memory.recent_memories || []).length
            ? (memory.recent_memories || []).map((m) => `<li>${esc(m)}</li>`).join("")
            : "<li class='muted'>Deep-link into Memory Browser — not duplicated here.</li>"
        }</ul>
        <button type="button" class="ghost-btn small" data-view="memory">Open Memory</button>
      </section>

      <section class="proj-panel">
        <h4>Knowledge</h4>
        <p>NS <code>${esc(knowledge.namespace)}</code> · ${esc(knowledge.coverage)}</p>
        <ul class="proj-mini-list">${
          (knowledge.indexed_repositories || []).length
            ? (knowledge.indexed_repositories || [])
                .map((r) => `<li><code>${esc(r.path)}</code> ${r.dirty ? "(dirty)" : ""}</li>`)
                .join("")
            : "<li class='muted'>No indexed repo yet — import git or index from Documents.</li>"
        }</ul>
        <button type="button" class="ghost-btn small" data-view="documents">Open Documents</button>
      </section>
    </div>

    <section class="proj-panel proj-quick">
      <h4>Quick actions</h4>
      <div class="proj-continue-grid">
        ${(home.quick_actions || [])
          .map((a) => `<button type="button" class="ghost-btn small" data-quick="${esc(a.id)}">${esc(a.label)}</button>`)
          .join("")}
      </div>
    </section>

    <dialog id="projectsBriefingDialog" class="proj-dialog">
      <form method="dialog" class="proj-dialog-card">
        <h3>Project briefing</h3>
        <pre class="proj-briefing" id="projectsBriefingBody"></pre>
        <div class="proj-dialog-actions">
          <button type="submit" class="ghost-btn">Close</button>
        </div>
      </form>
    </dialog>

    <p class="muted tiny proj-shortcuts">Shortcuts: <kbd>/</kbd> search · <kbd>N</kbd> new · <kbd>?</kbd> help · <kbd>Esc</kbd> cancel</p>
  `;

  root.querySelector("[data-act=switch]")?.addEventListener("click", () => switchTo(p.slug).catch(toastErr));
  root.querySelector("[data-act=continue]")?.addEventListener("click", () => continueProject(p.slug));
  root.querySelector("[data-act=briefing]")?.addEventListener("click", () => showBriefing(p.slug));

  root.querySelectorAll("[data-continue], [data-view]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const view = btn.getAttribute("data-view");
      const tab = btn.getAttribute("data-tab");
      const cont = btn.getAttribute("data-continue");
      if (cont === "journal" || (view === "journal" && tab === "projects")) {
        window.openProjectJournal?.(p.slug);
        return;
      }
      if (view) window.switchToView?.(view);
    });
  });

  root.querySelectorAll("[data-quick]").forEach((btn) => {
    btn.addEventListener("click", () => handleQuick(btn.getAttribute("data-quick"), p));
  });

  const offerBody = root.querySelector("#projectsLayoutOfferBody");
  if (offerBody) {
    fetch(`/api/layouts/suggest/project?slug=${encodeURIComponent(p.slug || "")}`)
      .then((r) => r.json())
      .then((sug) => {
        if (!sug?.ok || !sug?.recommend) {
          offerBody.textContent =
            "No forced layout — open Layouts anytime to change shell presentation.";
          return;
        }
        const name = sug.layout_name || sug.layout_id || "a layout";
        offerBody.innerHTML = "";
        const msg = document.createElement("p");
        msg.className = "muted tiny";
        msg.textContent = sug.message || `This project recommends the ${name} layout. You choose.`;
        offerBody.appendChild(msg);
        const applyBtn = document.createElement("button");
        applyBtn.type = "button";
        applyBtn.className = "ghost-btn small";
        applyBtn.textContent = `Apply ${name}`;
        applyBtn.addEventListener("click", () => {
          window.AriaLayouts?.applyLayout?.(sug.layout_id, { source: "projects" });
        });
        const openBtn = document.createElement("button");
        openBtn.type = "button";
        openBtn.className = "ghost-btn small";
        openBtn.textContent = "Open Layouts";
        openBtn.addEventListener("click", () => window.AriaLayouts?.openModal?.());
        const row = document.createElement("div");
        row.className = "proj-continue-grid";
        row.appendChild(applyBtn);
        row.appendChild(openBtn);
        offerBody.appendChild(row);
      })
      .catch(() => {
        offerBody.textContent = "Layouts available via Ctrl+Shift+L — never forced by Projects.";
      });
  }
}

function toastErr(err) {
  window.showAriaToast?.(err.message || String(err), "err", 5000);
}

async function continueProject(slug) {
  try {
    const data = await p2Fetch("/api/projects/continue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug }),
    });
    window.showAriaToast?.(data.message?.split("\n")[0]?.replace(/\*\*/g, "") || "Continued", "ok", 4000);
    await loadProjectHome(slug);
  } catch (e) {
    toastErr(e);
  }
}

async function showBriefing(slug) {
  try {
    const data = await p2Fetch("/api/projects/briefing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug }),
    });
    const dlg = $("projectsBriefingDialog");
    const body = $("projectsBriefingBody");
    if (body) body.textContent = data.briefing || data.message || "";
    dlg?.showModal?.();
  } catch (e) {
    toastErr(e);
  }
}

async function handleQuick(id, p) {
  try {
    if (id === "archive") {
      await p2Fetch(`/api/projects/${encodeURIComponent(p.slug)}/archive`, { method: "POST" });
      window.showAriaToast?.("Archived", "ok", 2500);
      await loadProjectHome("");
    } else if (id === "restore") {
      await p2Fetch(`/api/projects/${encodeURIComponent(p.slug)}/restore`, { method: "POST" });
      window.showAriaToast?.("Restored", "ok", 2500);
      await loadProjectHome(p.slug);
    } else if (id === "rename") {
      const title = window.ariaPrompt
        ? await window.ariaPrompt("New display name (slug stays the same):", p.title || p.slug, {
            title: "Rename project",
            okLabel: "Save",
          })
        : prompt("New display name (slug stays the same):", p.title || p.slug);
      if (!title) return;
      await p2Fetch(`/api/projects/${encodeURIComponent(p.slug)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      await loadProjectHome(p.slug);
    } else if (id === "export") {
      const data = await p2Fetch(`/api/projects/${encodeURIComponent(p.slug)}/export`);
      const blob = new Blob([JSON.stringify(data.export, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${p.slug}-project-export.json`;
      a.click();
    } else if (id === "open_folder") {
      window.showAriaToast?.(p.paths?.root || p.slug, "info", 4000);
    } else if (id === "import") {
      $("projectsGitInput")?.focus();
    } else if (id === "briefing") {
      await showBriefing(p.slug);
    } else if (id === "continue") {
      await continueProject(p.slug);
    } else if (id === "create") {
      $("projectsTitleInput")?.focus();
    }
  } catch (e) {
    toastErr(e);
  }
}

function projectsViewActive() {
  return (
    document.body.classList.contains("house-projects") ||
    /^#?projects\b/i.test(location.hash || "") ||
    !!document.getElementById("projectsHome")?.closest(".is-active, [data-active-room='projects'], #ariaStage")
  );
}

async function loadProjectHome(slug) {
  const homeEl = $("projectsHome");
  if (homeEl) homeEl.innerHTML = `<div class="proj-skeleton" aria-busy="true"><div></div><div></div><div></div></div>`;
  const gen = (loadProjectHome._gen = (loadProjectHome._gen || 0) + 1);
  try {
    // Fast path: clear "Loading…" and show project list from registry before full home enrich.
    if (!slug) {
      try {
        const snap = await p2Fetch("/api/projects");
        if (gen !== loadProjectHome._gen) return;
        const activeEl = $("projectsActive");
        if (activeEl) {
          activeEl.textContent = snap.active
            ? `Active workspace: ${snap.active}`
            : "No active project — pick one or create below.";
        }
        renderProjectList({ projects: snap.projects || [], active: snap.active || "" });
      } catch (_) {
        /* full home still loads below */
      }
    }
    const q = slug ? `?slug=${encodeURIComponent(slug)}` : "";
    const home = await p2Fetch(`/api/projects/home${q}`);
    if (gen !== loadProjectHome._gen) return;
    if (!slug && home.active) projectsState.selected = home.active;
    else if (slug) projectsState.selected = slug;
    renderHome(home);
  } catch (e) {
    if (gen !== loadProjectHome._gen) return;
    if (window.AriaNet?.isRoomAbort?.(e) || e?.name === "AbortError" || /aborted/i.test(String(e?.message || ""))) {
      // Room thrash cancelled this paint — never show AbortError to Jeff.
      if (projectsViewActive() && homeEl?.querySelector(".proj-skeleton")) {
        clearTimeout(loadProjectHome._retry);
        loadProjectHome._retry = setTimeout(() => {
          if (projectsViewActive()) loadProjectHome(slug);
        }, 140);
      }
      return;
    }
    if (homeEl) homeEl.innerHTML = `<p class="muted">${esc(e.message)}</p>`;
    toastErr(e);
  }
}

async function loadProjects() {
  await loadProjectHome(projectsState.selected || "");
}

async function maybeProjectPicker() {
  if (sessionStorage.getItem("jarvisProjectPickerDone")) return;
  try {
    const data = await p2Fetch("/api/projects");
    if (data.active || !(data.projects || []).length) {
      sessionStorage.setItem("jarvisProjectPickerDone", "1");
      return;
    }
    const modal = $("projectPickerModal");
    const pickList = $("projectPickerList");
    if (!modal || !pickList) return;
    pickList.innerHTML = "";
    for (const p of data.projects) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn";
      btn.textContent = `${p.title} (${p.slug})`;
      btn.addEventListener("click", async () => {
        try {
          await switchTo(p.slug);
          modal.classList.add("hidden");
          sessionStorage.setItem("jarvisProjectPickerDone", "1");
        } catch (err) {
          toastErr(err);
        }
      });
      pickList.appendChild(btn);
    }
    modal.classList.remove("hidden");
  } catch (err) {
    toastErr(err);
  }
}

function showProjectsHelp() {
  window.showAriaToast?.(
    "Projects shortcuts: / search · N new · Enter select · Esc close · ? help. Chat: switch/list/continue/briefing project.",
    "info",
    6000
  );
}

function bindProjectsShortcuts() {
  if (projectsShortcutsBound) return;
  projectsShortcutsBound = true;
  document.addEventListener("keydown", (e) => {
    const view = $("projectsView");
    if (!view || view.classList.contains("hidden")) return;
    const tag = (e.target && e.target.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || e.target?.isContentEditable) {
      if (e.key === "Escape") {
        e.target.blur();
        $("projectsHelpDialog")?.close?.();
      }
      if (e.key === "Enter" && e.ctrlKey && e.target.id === "projectsTitleInput") {
        e.preventDefault();
        $("projectsCreateBtn")?.click();
      }
      return;
    }
    if (e.key === "/" && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
      $("projectsSearchInput")?.focus();
    } else if (e.key === "n" || e.key === "N") {
      e.preventDefault();
      $("projectsTitleInput")?.focus();
    } else if (e.key === "?") {
      e.preventDefault();
      showProjectsHelp();
    } else if (e.key === "Escape") {
      $("projectPickerModal")?.classList.add("hidden");
      $("projectsBriefingDialog")?.close?.();
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      const items = [...document.querySelectorAll("#projectsList .proj-list-item")];
      if (!items.length) return;
      e.preventDefault();
      const idx = items.findIndex((el) => el.classList.contains("is-selected"));
      const next = e.key === "ArrowDown" ? Math.min(items.length - 1, idx + 1) : Math.max(0, idx <= 0 ? 0 : idx - 1);
      const slug = items[next]?.dataset.slug;
      if (slug) selectProject(slug);
    }
  });
}

window.initProjects = function initProjects() {
  const root = $("projectsView");
  if (!root) return;
  if (root.dataset.bound === "1") {
    loadProjects();
    return;
  }
  root.dataset.bound = "1";
  bindProjectsShortcuts();

  $("projectsSearchInput")?.addEventListener("input", (e) => {
    projectsState.filter = e.target.value || "";
    if (projectsState.home) renderProjectList(projectsState.home);
  });

  $("projectsCreateBtn")?.addEventListener("click", async () => {
    const title = $("projectsTitleInput")?.value?.trim();
    if (!title) {
      window.showAriaToast?.("Enter a project title first", "warn", 3000);
      $("projectsTitleInput")?.focus();
      return;
    }
    try {
      const created = await p2Fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          description: $("projectsDescInput")?.value?.trim() || "",
        }),
      });
      $("projectsTitleInput").value = "";
      if ($("projectsDescInput")) $("projectsDescInput").value = "";
      const slug = created?.project?.slug;
      if (!slug) throw new Error("Create succeeded but no project slug returned");
      window.showAriaToast?.(`Active project: ${created?.project?.title || title}`, "ok", 3500);
      await loadProjectHome(slug);
    } catch (err) {
      toastErr(err);
    }
  });

  $("projectsImportBtn")?.addEventListener("click", async () => {
    const path = $("projectsGitInput")?.value?.trim();
    if (!path) return;
    try {
      const data = await p2Fetch("/api/projects/import-git", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });
      $("projectsGitInput").value = "";
      window.showAriaToast?.("Repository imported as workspace", "ok", 3500);
      await loadProjectHome(data.project?.slug || "");
    } catch (err) {
      toastErr(err);
    }
  });

  $("projectsHelpBtn")?.addEventListener("click", showProjectsHelp);
  $("projectPickerSkipBtn")?.addEventListener("click", () => {
    $("projectPickerModal")?.classList.add("hidden");
    sessionStorage.setItem("jarvisProjectPickerDone", "1");
  });

  loadProjects();
  maybeProjectPicker();
};

window.openProjectHome = function openProjectHome(slug) {
  window.switchToView?.("projects");
  projectsState.selected = slug || "";
  setTimeout(() => loadProjectHome(slug || ""), 50);
};
