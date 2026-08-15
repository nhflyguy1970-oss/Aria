/**
 * Phase 5 Priority 2 — native Rooms:
 * Documents, Coding, Projects, Planner, Gallery, Search.
 */
(function () {
  "use strict";
  const kit = () => window.AriaRoomKit;
  if (!kit()?.defineRoom) return;

  /* —— Documents — private library —— */
  kit().defineRoom({
    id: "documents",
    global: "AriaDocumentsRoom",
    rootId: "documentsRoom",
    className: "documents-room",
    houseClass: "house-documents",
    bodyNativeClass: "native-documents",
    place: "· Private library",
    label: "Documents",
    chrome: "minimal",
    overflowHtml:
      '<button type="button" data-nr-act="refresh">Refresh</button>' +
      '<button type="button" data-nr-act="chat">Ask Aria</button>',
    buildBody: () =>
      '<main class="nr-stage nr-stage--split">' +
      '<div class="nr-stage__primary">' +
      '<div class="nr-hero" data-docs-hero></div>' +
      '<label class="nr-search"><span class="visually-hidden">Search documents</span>' +
      '<input type="search" data-docs-q placeholder="Search your library…" /></label>' +
      '<ul class="nr-list" data-docs-list></ul>' +
      "</div>" +
      '<aside class="nr-stage__aside" data-docs-preview aria-live="polite">' +
      '<p class="nr-empty">Select a document to open it.</p>' +
      "</aside>" +
      "</main>",
    wire: (ctx) => {
      let t;
      ctx.root.querySelector("[data-docs-q]")?.addEventListener("input", (e) => {
        clearTimeout(t);
        t = setTimeout(() => search(ctx, e.target.value.trim()), 280);
      });
      ctx.root.querySelector("[data-docs-list]")?.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-doc-path]");
        if (!btn) return;
        openDocument(ctx, btn.dataset.docPath, btn.dataset.docTitle || "");
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Opening the library…");
      try {
        const home = await ctx.api("/api/documents/home");
        const list = await ctx.api("/api/documents?limit=40");
        const docs = list.documents || list.results || [];
        const h = home.health || {};
        ctx.root.querySelector("[data-docs-hero]").innerHTML =
          "<h1>Your library</h1>" +
          `<p class="nr-pulse">${ctx.esc(home.philosophy || "Local documents, grounded search.")}</p>` +
          `<p class="nr-meta">${ctx.esc(String(h.document_count ?? docs.length))} documents · ${ctx.esc(String(h.chunk_count ?? "—"))} chunks</p>`;
        renderDocs(ctx, docs);
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Library unavailable");
      }
    },
  });

  function renderDocs(ctx, docs) {
    const ul = ctx.root.querySelector("[data-docs-list]");
    if (!ul) return;
    if (!docs.length) {
      ul.innerHTML = '<li class="nr-empty">Nothing on the shelves yet.</li>';
      return;
    }
    ul.innerHTML = docs
      .slice(0, 40)
      .map((d) => {
        const title = d.name || d.title || d.relative || "Document";
        const sub = d.relative || d.path || d.suffix || "";
        const path = d.path || d.relative || d.location || "";
        return (
          `<li><button type="button" class="nr-row" data-doc-path="${ctx.esc(path)}" data-doc-title="${ctx.esc(title)}">` +
          `<span class="nr-row-title">${ctx.esc(title)}</span>` +
          `<span class="nr-row-meta">${ctx.esc(sub)}</span>` +
          `</button></li>`
        );
      })
      .join("");
  }

  async function openDocument(ctx, path, title) {
    if (!path) return;
    const pane = ctx.root.querySelector("[data-docs-preview]");
    if (!pane) return;
    ctx.setStatus("Opening…");
    pane.innerHTML = `<p class="nr-empty">Opening ${ctx.esc(title || path)}…</p>`;
    try {
      const data = await ctx.api(`/api/documents/preview?path=${encodeURIComponent(path)}`);
      const doc = data.document || data;
      const body = doc.preview || doc.excerpt || doc.text || "";
      const name = doc.title || title || path;
      pane.innerHTML =
        `<h2 class="nr-preview-title">${ctx.esc(name)}</h2>` +
        `<p class="nr-meta">${ctx.esc(doc.location || doc.path || path)} · ${ctx.esc(String(doc.char_count ?? body.length))} chars</p>` +
        `<pre class="nr-preview">${ctx.esc(body)}</pre>`;
      ctx.root.querySelectorAll("[data-doc-path]").forEach((btn) => {
        btn.classList.toggle("is-active", btn.dataset.docPath === path);
      });
      ctx.setStatus("Listening quietly");
    } catch (err) {
      pane.innerHTML = `<p class="nr-empty">${ctx.esc(err.message || "Could not open document")}</p>`;
      ctx.setStatus(err.message || "Open failed");
    }
  }

  async function search(ctx, q) {
    if (!q) {
      const list = await ctx.api("/api/documents?limit=40");
      renderDocs(ctx, list.documents || []);
      return;
    }
    ctx.setStatus("Searching…");
    try {
      const data = await ctx.api(`/api/documents/search?q=${encodeURIComponent(q)}&limit=20`);
      const hits = data.hits || data.results || [];
      const ul = ctx.root.querySelector("[data-docs-list]");
      ul.innerHTML = hits.length
        ? hits
            .map((h) => {
              const title = h.title || h.source || h.name || "Hit";
              const text = (h.text || h.snippet || "").slice(0, 160);
              const path = h.path || h.source || h.location || "";
              return (
                `<li><button type="button" class="nr-row" data-doc-path="${ctx.esc(path)}" data-doc-title="${ctx.esc(title)}">` +
                `<span class="nr-row-title">${ctx.esc(title)}</span>` +
                `<span class="nr-row-meta">${ctx.esc(text)}</span>` +
                `</button></li>`
              );
            })
            .join("")
        : '<li class="nr-empty">No passages found.</li>';
      ctx.setStatus(`${hits.length} passages`);
    } catch (err) {
      ctx.setStatus(err.message || "Search failed");
    }
  }

  /* —— Coding — engineering studio —— */
  kit().defineRoom({
    id: "coding",
    global: "AriaCodingRoom",
    rootId: "codingRoom",
    className: "coding-room",
    houseClass: "house-coding",
    bodyNativeClass: "native-coding",
    place: "· Engineering studio",
    label: "Coding",
    chrome: "standard",
    overflowHtml:
      '<button type="button" data-nr-act="refresh">Refresh</button>' +
      '<button type="button" data-nr-act="projects">Projects</button>' +
      '<button type="button" data-nr-act="chat">Ask Aria</button>',
    onOverflow: async (act) => {
      if (act === "projects") window.AriaActivityEngine?.start?.("projects", { confirmHighStakes: false });
    },
    buildBody: () =>
      '<main class="nr-stage">' +
      '<div class="nr-hero" data-coding-hero></div>' +
      '<div class="nr-grid" data-coding-grid></div>' +
      '<section class="nr-section" aria-label="Open proposals">' +
      "<h2>Open proposals</h2>" +
      '<ul class="nr-list" data-coding-proposals></ul>' +
      '<pre class="nr-preview" data-coding-diff hidden></pre>' +
      "</section>" +
      "</main>",
    wire: (ctx) => {
      ctx.root.querySelector("[data-coding-proposals]")?.addEventListener("click", async (e) => {
        const btn = e.target.closest("[data-coding-act]");
        if (!btn) return;
        const id = btn.dataset.proposalId;
        const act = btn.dataset.codingAct;
        if (!id || !act) return;
        if (act === "diff") {
          ctx.setStatus("Loading diff…");
          try {
            const data = await ctx.api(`/api/proposals/${encodeURIComponent(id)}`);
            const pre = ctx.root.querySelector("[data-coding-diff]");
            if (pre) {
              pre.hidden = false;
              pre.textContent = data.diff || data.message || "No diff.";
            }
            ctx.setStatus("Listening quietly");
          } catch (err) {
            ctx.setStatus(err.message || "Diff unavailable");
          }
          return;
        }
        if (act === "apply") {
          if (window.ariaConfirm) {
            if (!(await window.ariaConfirm(`Apply proposal ${id}?`, { title: "Apply proposal", okLabel: "Apply" }))) return;
          } else if (!window.confirm?.(`Apply proposal ${id}?`)) {
            return;
          }
          ctx.setStatus("Applying…");
          try {
            const form = new FormData();
            form.append("proposal_id", id);
            const res = await fetch("/api/apply", { method: "POST", body: form });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || data.ok === false) throw new Error(data.message || data.error || "Apply failed");
            window.showAriaToast?.(data.message || "Applied", "ok", 3000);
            await kit().get("coding")?.refresh?.();
            ctx.setStatus("Listening quietly");
          } catch (err) {
            ctx.setStatus(err.message || "Apply failed");
          }
        }
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Reading the bench…");
      try {
        const d = await ctx.api("/api/coding/home");
        const branch = d.repository?.branch || "—";
        const root = d.write_target || d.coding_root || "—";
        const open = d.open_proposals || d.proposals || [];
        const openN = Array.isArray(open) ? open.length : open.count || 0;
        ctx.root.querySelector("[data-coding-hero]").innerHTML =
          "<h1>Current work</h1>" +
          `<p class="nr-pulse">${ctx.esc(d.banner || d.philosophy || "Propose. Review. Apply.")}</p>`;
        ctx.root.querySelector("[data-coding-grid]").innerHTML = [
          card(ctx, "Branch", branch),
          card(ctx, "Write target", String(root).replace(/^.*\//, "")),
          card(ctx, "Open proposals", String(openN)),
          card(ctx, "Model", d.model?.name || d.model || "—"),
        ].join("");
        const ul = ctx.root.querySelector("[data-coding-proposals]");
        const list = Array.isArray(open) ? open : [];
        ul.innerHTML = list.length
          ? list
              .slice(0, 12)
              .map((p) => {
                const id = p.id || p.proposal_id || "";
                const summary = p.summary || p.explanation || p.mode || "Proposal";
                const files = Array.isArray(p.files) ? p.files.join(", ") : "";
                return (
                  `<li><div class="nr-row">` +
                  `<span class="nr-row-title">${ctx.esc(summary)}</span>` +
                  `<span class="nr-row-meta">${ctx.esc(id)} · ${ctx.esc(files)}</span>` +
                  `<span class="nr-row-actions">` +
                  `<button type="button" class="nr-mini" data-coding-act="diff" data-proposal-id="${ctx.esc(id)}">Diff</button>` +
                  `<button type="button" class="nr-mini" data-coding-act="apply" data-proposal-id="${ctx.esc(id)}">Apply</button>` +
                  `</span></div></li>`
                );
              })
              .join("")
          : '<li class="nr-empty">No open proposals. Ask Chat to fix or implement something.</li>';
        const pre = ctx.root.querySelector("[data-coding-diff]");
        if (pre) {
          pre.hidden = true;
          pre.textContent = "";
        }
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Coding unavailable");
      }
    },
  });

  function card(ctx, title, body) {
    return `<section class="nr-card"><h2>${ctx.esc(title)}</h2><p>${ctx.esc(body)}</p></section>`;
  }

  /* —— Projects — creative workshop —— */
  kit().defineRoom({
    id: "projects",
    global: "AriaProjectsRoom",
    rootId: "projectsRoom",
    className: "projects-room",
    houseClass: "house-projects",
    bodyNativeClass: "native-projects",
    place: "· Creative workshop",
    label: "Projects",
    chrome: "standard",
    buildBody: () =>
      '<main class="nr-stage">' +
      '<div class="nr-hero" data-proj-hero></div>' +
      '<form class="nr-form" data-proj-form autocomplete="off">' +
      '<input name="title" placeholder="Name a new project…" required />' +
      '<button type="submit">Create</button></form>' +
      '<ul class="nr-list" data-proj-list></ul>' +
      "</main>",
    wire: (ctx) => {
      ctx.root.querySelector("[data-proj-form]")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const title = String(new FormData(e.target).get("title") || "").trim();
        if (!title) return;
        ctx.setStatus("Creating…");
        try {
          await ctx.api("/api/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, activate: true }),
          });
          e.target.reset();
          await kit().get("projects")?.refresh?.();
          ctx.setStatus("Listening quietly");
          window.showAriaToast?.(`Project “${title}” ready`, "ok", 2500);
        } catch (err) {
          ctx.setStatus(err.message || "Create failed");
        }
      });
      ctx.root.querySelector("[data-proj-list]")?.addEventListener("click", async (e) => {
        const btn = e.target.closest("[data-proj-slug]");
        if (!btn) return;
        const slug = btn.dataset.projSlug;
        if (!slug) return;
        ctx.setStatus("Switching…");
        try {
          await ctx.api("/api/projects/switch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ slug }),
          });
          await kit().get("projects")?.refresh?.();
          ctx.setStatus("Listening quietly");
        } catch (err) {
          ctx.setStatus(err.message || "Switch failed");
        }
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Looking at the workshop…");
      try {
        const home = await ctx.api("/api/projects/home");
        const list = await ctx.api("/api/projects?limit=40");
        const projects = list.projects || home.projects || [];
        const active = home.active || list.active || "";
        ctx.root.querySelector("[data-proj-hero]").innerHTML =
          "<h1>Alive work</h1>" +
          `<p class="nr-pulse">${
            active
              ? `Active: ${ctx.esc(active)}`
              : projects.length
                ? "Choose a project when you’re ready."
                : "No projects yet — name one above when something needs a home."
          }</p>`;
        const ul = ctx.root.querySelector("[data-proj-list]");
        ul.innerHTML = projects.length
          ? projects
              .map((p) => {
                const slug = p.slug || p.id || "";
                const name = p.title || p.name || slug || "Project";
                const meta = p.path || p.root || p.description || "";
                const isActive = active && (slug === active || name === active);
                return (
                  `<li><button type="button" class="nr-row${isActive ? " is-active" : ""}" data-proj-slug="${ctx.esc(slug)}">` +
                  `<span class="nr-row-title">${ctx.esc(name)}${isActive ? " · active" : ""}</span>` +
                  `<span class="nr-row-meta">${ctx.esc(meta)}</span>` +
                  `</button></li>`
                );
              })
              .join("")
          : '<li class="nr-empty">Create a project when something needs a home.</li>';
        ctx.setStatus(projects.length ? `${projects.length} projects` : "Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Projects unavailable");
      }
    },
  });

  /* —— Planner — leather notebook —— */
  kit().defineRoom({
    id: "planner",
    global: "AriaPlannerRoom",
    rootId: "plannerRoom",
    className: "planner-room",
    houseClass: "house-planner",
    bodyNativeClass: "native-planner",
    place: "· Leather notebook",
    label: "Planner",
    chrome: "minimal",
    overflowHtml:
      '<button type="button" data-nr-act="refresh">Refresh</button>' +
      '<button type="button" data-nr-act="calendar">Calendar</button>',
    onOverflow: async (act) => {
      if (act === "calendar") window.AriaActivityEngine?.start?.("calendar", { confirmHighStakes: false });
    },
    buildBody: () =>
      '<main class="nr-stage">' +
      '<div class="nr-hero" data-plan-hero></div>' +
      '<form class="nr-form" data-plan-form autocomplete="off">' +
      '<input name="text" placeholder="Add something for today…" required />' +
      '<button type="submit">Add</button></form>' +
      '<ul class="nr-list" data-plan-list></ul>' +
      "</main>",
    wire: (ctx) => {
      ctx.root.querySelector("[data-plan-form]")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const text = String(fd.get("text") || "").trim();
        if (!text) return;
        ctx.setStatus("Noting…");
        try {
          await ctx.api("/api/planner", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
          });
          e.target.reset();
          await kit().get("planner")?.refresh?.();
        } catch (err) {
          /* try tasks endpoint variants */
          try {
            await ctx.api("/api/planner/tasks", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text }),
            });
            e.target.reset();
            await kit().get("planner")?.refresh?.();
          } catch (err2) {
            ctx.setStatus(err2.message || err.message || "Could not add");
          }
        }
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Opening today’s page…");
      try {
        const d = await ctx.api("/api/planner");
        const tasks = (d.tasks || []).filter((t) => !t.completed);
        const events = d.events_today || [];
        ctx.root.querySelector("[data-plan-hero]").innerHTML =
          "<h1>Today’s page</h1>" +
          `<p class="nr-pulse">${
            tasks.length
              ? `${tasks.length} open · ${events.length} events today`
              : "A clean page. Write what matters."
          }</p>`;
        const ul = ctx.root.querySelector("[data-plan-list]");
        ul.innerHTML = tasks.length
          ? tasks
              .map((t) => `<li><div class="nr-row"><span class="nr-row-title">${ctx.esc(t.text || t.title || "Task")}</span></div></li>`)
              .join("")
          : '<li class="nr-empty">Nothing waiting.</li>';
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Planner unavailable");
      }
    },
  });

  /* —— Gallery — museum —— */
  kit().defineRoom({
    id: "gallery",
    global: "AriaGalleryRoom",
    rootId: "galleryRoom",
    className: "gallery-room",
    houseClass: "house-gallery",
    bodyNativeClass: "native-gallery",
    place: "· Museum",
    label: "Gallery",
    chrome: "minimal",
    buildBody: () =>
      '<main class="nr-stage">' +
      '<div class="nr-hero" data-gal-hero></div>' +
      '<form class="nr-form" data-gal-form autocomplete="off">' +
      '<input name="prompt" type="text" placeholder="Describe an image to create…" required />' +
      '<button type="submit">Generate</button></form>' +
      '<p class="nr-meta" data-gal-gen-status hidden></p>' +
      '<div class="nr-gallery" data-gal-grid></div>' +
      "</main>",
    wire: (ctx) => {
      ctx.root.querySelector("[data-gal-form]")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const prompt = String(new FormData(e.target).get("prompt") || "").trim();
        if (!prompt) return;
        const status = ctx.root.querySelector("[data-gal-gen-status]");
        ctx.setStatus("Queuing generation…");
        if (status) {
          status.hidden = false;
          status.textContent = "Queuing…";
        }
        try {
          const out = await ctx.api("/api/gallery/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt }),
          });
          e.target.reset();
          if (status) {
            status.textContent = out.message
              ? String(out.message).replace(/\*\*/g, "").slice(0, 160)
              : out.job_id
                ? `Queued (${out.job_id}). It will appear when ready.`
                : "Queued.";
          }
          ctx.setStatus("Listening quietly");
          window.showAriaToast?.("Image generation queued", "ok", 3000);
        } catch (err) {
          if (status) status.textContent = err.message || "Generate failed";
          ctx.setStatus(err.message || "Generate failed");
        }
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Walking the gallery…");
      try {
        const home = await ctx.api("/api/gallery/home").catch(() => ({}));
        const data = await ctx.api("/api/gallery?limit=24");
        const images = data.images || data.items || data.results || [];
        ctx.root.querySelector("[data-gal-hero]").innerHTML =
          "<h1>Artwork</h1>" +
          `<p class="nr-pulse">${ctx.esc(home.philosophy || "Local stills — generate, browse, keep.")}</p>` +
          `<p class="nr-meta">${images.length ? `${images.length} nearby` : "The walls are quiet — generate when the mood hits."}</p>`;
        const grid = ctx.root.querySelector("[data-gal-grid]");
        if (!images.length) {
          grid.innerHTML = '<p class="nr-empty">No stills on the walls yet. Describe one above to begin.</p>';
        } else {
          grid.innerHTML = images
            .slice(0, 24)
            .map((img) => {
              const name = img.name || "";
              const src =
                img.thumb_url ||
                img.url ||
                (name ? `/api/gallery/${encodeURIComponent(name)}?max=384` : img.path || img.src || "");
              const alt = img.prompt || img.name || "Artwork";
              if (!src) return `<div class="nr-thumb nr-thumb--empty">${ctx.esc(alt).slice(0, 40)}</div>`;
              return `<figure class="nr-thumb"><img src="${ctx.esc(src)}" alt="${ctx.esc(alt)}" loading="lazy" /></figure>`;
            })
            .join("");
        }
        ctx.setStatus("Listening quietly");
      } catch (err) {
        ctx.setStatus(err.message || "Gallery unavailable");
      }
    },
  });

  /* —— Search — research study —— */
  kit().defineRoom({
    id: "search",
    global: "AriaSearchRoom",
    rootId: "searchRoom",
    className: "search-room",
    houseClass: "house-search",
    bodyNativeClass: "native-search",
    place: "· Research study",
    label: "Search",
    chrome: "focus",
    buildBody: () =>
      '<main class="nr-stage">' +
      '<div class="nr-hero" data-search-hero><h1>Discovery</h1><p class="nr-pulse">One place to look across Aria.</p></div>' +
      '<form class="nr-form nr-form--search" data-search-form>' +
      '<input name="q" type="search" placeholder="What are you looking for?" required autocomplete="off" />' +
      '<button type="submit">Search</button></form>' +
      '<ul class="nr-list" data-search-list></ul>' +
      "</main>",
    wire: (ctx) => {
      ctx.root.querySelector("[data-search-form]")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const q = String(new FormData(e.target).get("q") || "").trim();
        if (!q) return;
        await runSearch(ctx, q);
      });
    },
    load: async (ctx) => {
      ctx.setStatus("Study ready");
      try {
        const home = await ctx.api("/api/search/product/home");
        ctx.root.querySelector("[data-search-hero]").innerHTML =
          "<h1>Discovery</h1>" +
          `<p class="nr-pulse">${ctx.esc(home.mental_model?.search_home || "Browse everything Aria knows.")}</p>`;
        ctx.root.querySelector("[data-search-list]").innerHTML =
          '<li class="nr-empty">Type above — memory, journal, planner, health, and more.</li>';
      } catch (_) {
        /* ignore */
      }
    },
  });

  async function runSearch(ctx, q) {
    ctx.setStatus("Searching…");
    try {
      let data;
      try {
        data = await ctx.api(`/api/search/product/query?q=${encodeURIComponent(q)}&limit=20`);
      } catch (_) {
        data = await ctx.api("/api/search/product/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ q, limit: 20 }),
        });
      }
      const hits = data.results || data.hits || data.items || [];
      const ul = ctx.root.querySelector("[data-search-list]");
      ul.innerHTML = hits.length
        ? hits
            .slice(0, 30)
            .map((h) => {
              const title = h.title || h.source || h.corpus || h.name || "Result";
              const text = (h.snippet || h.text || h.preview || "").slice(0, 180);
              return `<li><div class="nr-row"><span class="nr-row-title">${ctx.esc(title)}</span><span class="nr-row-meta">${ctx.esc(text)}</span></div></li>`;
            })
            .join("")
        : '<li class="nr-empty">Nothing matched.</li>';
      ctx.setStatus(hits.length ? `${hits.length} results` : "No matches");
    } catch (err) {
      ctx.setStatus(err.message || "Search failed");
    }
  }
})();
