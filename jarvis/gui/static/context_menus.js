/** Universal context menus — right-click actions for views, lists, media, tasks, and more. */
(function () {
  "use strict";

  let menuEl = null;

  function close() {
    menuEl?.remove();
    menuEl = null;
    document.removeEventListener("mousedown", onDocDown, true);
    document.removeEventListener("keydown", onKey, true);
  }

  function onDocDown(e) {
    if (menuEl && !menuEl.contains(e.target)) close();
  }

  function onKey(e) {
    if (e.key === "Escape") close();
  }

  function open(event, actions) {
    close();
    const list = (actions || []).filter(Boolean);
    if (!list.length) return;
    event.preventDefault();
    event.stopPropagation();
    menuEl = document.createElement("div");
    menuEl.className = "aria-context-menu";
    menuEl.setAttribute("role", "menu");
    list.forEach((a) => {
      if (a.separator) {
        const hr = document.createElement("div");
        hr.className = "aria-context-sep";
        menuEl.appendChild(hr);
        return;
      }
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "aria-context-item";
      btn.setAttribute("role", "menuitem");
      btn.textContent = a.label;
      if (a.disabled) btn.disabled = true;
      btn.addEventListener("click", () => {
        close();
        try {
          a.run?.();
        } catch (err) {
          window.showAriaToast?.(err?.message || "Action failed — try again", "err", 4000);
        }
      });
      menuEl.appendChild(btn);
    });
    document.body.appendChild(menuEl);
    const { innerWidth: w, innerHeight: h } = window;
    const rect = menuEl.getBoundingClientRect();
    let x = event.clientX;
    let y = event.clientY;
    if (x + rect.width > w - 8) x = w - rect.width - 8;
    if (y + rect.height > h - 8) y = h - rect.height - 8;
    menuEl.style.left = `${Math.max(8, x)}px`;
    menuEl.style.top = `${Math.max(8, y)}px`;
    menuEl.querySelector(".aria-context-item:not(:disabled)")?.focus();
    document.addEventListener("mousedown", onDocDown, true);
    document.addEventListener("keydown", onKey, true);
  }

  function copyText(text, okMsg) {
    navigator.clipboard?.writeText(String(text || "")).then(
      () => window.showAriaToast?.(okMsg || "Copied", "ok", 1800),
      () => window.showAriaToast?.("Could not copy", "err", 3000),
    );
  }

  function copyDeepLink(view) {
    copyText(`${location.origin}${location.pathname}#${view}`, "Deep link copied");
  }

  function viewActions(view) {
    const labels = window.AriaFavorites?.VIEW_LABELS || {};
    const isFav = window.AriaFavorites?.isFavorite?.(view);
    return [
      { label: `Open ${labels[view] || view}`, run: () => window.switchToView?.(view) },
      {
        label: "Open in new window",
        run: () => window.open(`${location.origin}${location.pathname}?app=1#${view}`, "_blank", "noopener"),
      },
      {
        label: "Split with Chat",
        run: () => window.AriaSplitView?.enable?.(view === "chat" ? "planner" : "chat", view === "chat" ? view : view),
      },
      { separator: true },
      {
        label: isFav ? "Unpin from Favorites" : "Pin to Favorites",
        run: () => window.AriaFavorites?.toggleFavorite?.(view),
      },
      { label: "Copy deep link", run: () => copyDeepLink(view) },
    ];
  }

  function genericItemActions(opts) {
    const { label, open, copy, pinView, extra } = opts;
    const acts = [];
    if (open) acts.push({ label: `Open${label ? `: ${label}` : ""}`, run: open });
    if (copy) acts.push({ label: "Copy", run: () => copyText(copy) });
    if (pinView) {
      acts.push({
        label: window.AriaFavorites?.isFavorite?.(pinView) ? "Unpin view" : "Favorite this view",
        run: () => window.AriaFavorites?.toggleFavorite?.(pinView),
      });
    }
    if (extra?.length) {
      acts.push({ separator: true });
      acts.push(...extra);
    }
    return acts;
  }

  function resolveTarget(e) {
    const t = e.target;
    if (!(t instanceof Element)) return null;

    const viewTab = t.closest?.(".view-tab[data-view]");
    if (viewTab) return { type: "view", view: viewTab.dataset.view };

    const fav = t.closest?.(".sidebar-fav-row[data-view]");
    if (fav) return { type: "view", view: fav.dataset.view };

    const dock = t.closest?.(".quick-dock-btn[data-view]");
    if (dock) return { type: "view", view: dock.dataset.view };

    const plannerTask = t.closest?.("#plannerTasks li, .planner-list li");
    if (plannerTask && document.getElementById("plannerView")?.contains(plannerTask)) {
      const text = plannerTask.textContent?.trim() || "Task";
      return {
        type: "task",
        actions: genericItemActions({
          label: text.slice(0, 40),
          copy: text,
          pinView: "planner",
          open: () => window.switchToView?.("planner"),
          extra: [
            { label: "New task", run: () => { window.switchToView?.("planner"); setTimeout(() => document.getElementById("plannerTaskInput")?.focus(), 80); } },
            { label: "Ask Aria about this", run: () => { window.switchToView?.("chat"); setTimeout(() => window.jarvisSendToChat?.(`Help me with this task: ${text}`), 80); } },
          ],
        }),
      };
    }

    const memoryItem = t.closest?.(".memory-item, #memoryList li, .memory-list li");
    if (memoryItem) {
      const text = memoryItem.textContent?.trim() || "";
      const id = memoryItem.dataset?.id || "";
      return {
        type: "memory",
        actions: genericItemActions({
          label: "memory",
          copy: text.slice(0, 500),
          pinView: "memory",
          open: () => window.switchToView?.("memory"),
          extra: [
            { label: "Search Memory", run: () => { window.switchToView?.("memory"); setTimeout(() => document.getElementById("memorySearch")?.focus(), 80); } },
            { label: "Ask Aria to recall", run: () => { window.switchToView?.("chat"); setTimeout(() => window.jarvisSendToChat?.(`What do you remember about: ${text.slice(0, 80)}`), 80); } },
            id ? { label: "Copy ID", run: () => copyText(id) } : null,
          ].filter(Boolean),
        }),
      };
    }

    const gallery = t.closest?.(".gallery-card, .gallery-item, #galleryGrid img, .gallery-thumb");
    if (gallery || (t.tagName === "IMG" && t.closest?.("#galleryView"))) {
      const img = gallery?.querySelector?.("img") || (t.tagName === "IMG" ? t : null);
      const src = img?.src || img?.dataset?.src || "";
      return {
        type: "image",
        actions: genericItemActions({
          label: "image",
          copy: src,
          pinView: "gallery",
          open: () => window.switchToView?.("gallery"),
          extra: [
            { label: "Open Gallery", run: () => window.switchToView?.("gallery") },
            { label: "Generate another", run: () => {
              window.openGalleryHome?.() || window.switchToView?.("gallery");
              setTimeout(() => {
                if (typeof window.galleryGenerateAnother === "function") window.galleryGenerateAnother();
                else document.getElementById("galleryPromptInput")?.focus();
              }, 80);
            } },
            { label: "Compare images", run: () => document.getElementById("compareModeBtn")?.click() },
            src ? { label: "Copy image URL", run: () => copyText(src) } : null,
          ].filter(Boolean),
        }),
      };
    }

    const fly = t.closest?.("#flytyingRecipeList li, .flytying-recipe-list li, .flytying-queue-list li");
    if (fly) {
      const text = fly.textContent?.trim() || "Pattern";
      return {
        type: "fly",
        actions: genericItemActions({
          label: text.slice(0, 40),
          copy: text,
          pinView: "flytying",
          open: () => window.switchToView?.("flytying"),
          extra: [
            { label: "Ask Aria about pattern", run: () => { window.switchToView?.("chat"); setTimeout(() => window.jarvisSendToChat?.(`Explain the fly pattern: ${text}`), 80); } },
          ],
        }),
      };
    }

    const project = t.closest?.("#projectsList li, .projects-list li");
    if (project) {
      const text = project.textContent?.trim() || "Project";
      return {
        type: "project",
        actions: genericItemActions({
          label: text.slice(0, 40),
          copy: text,
          pinView: "projects",
          open: () => window.switchToView?.("projects"),
          extra: [
            { label: "Open in Chat / Coding", run: () => { window.switchToView?.("chat"); document.querySelector('.module-chip[data-module="coding"]')?.click(); } },
          ],
        }),
      };
    }

    const doc = t.closest?.("#documentsList li, .documents-list li, .documents-row");
    if (doc) {
      const text = doc.textContent?.trim() || "Document";
      return {
        type: "document",
        actions: genericItemActions({
          label: text.slice(0, 40),
          copy: text,
          pinView: "documents",
          open: () => window.switchToView?.("documents"),
          extra: [
            { label: "Ask Aria about this file", run: () => { window.switchToView?.("chat"); setTimeout(() => window.jarvisSendToChat?.(`Summarize document: ${text.slice(0, 80)}`), 80); } },
          ],
        }),
      };
    }

    const journal = t.closest?.("#journalEntries li, .journal-list li, .bujo-item");
    if (journal) {
      const text = journal.textContent?.trim() || "Entry";
      return {
        type: "journal",
        actions: genericItemActions({
          label: text.slice(0, 40),
          copy: text,
          pinView: "journal",
          open: () => window.switchToView?.("journal"),
        }),
      };
    }

    const modelRow = t.closest?.(".model-row, #modelsEditor select, #chatModelSelect");
    if (modelRow || t.id === "chatModelSelect") {
      const sel = t.closest?.("select") || document.getElementById("chatModelSelect");
      const val = sel?.value || "";
      return {
        type: "model",
        actions: [
          { label: "Open model settings", run: () => {
            const sec = document.querySelector('.sidebar-section[data-section="models"]');
            if (sec?.classList.contains("collapsed")) sec.querySelector(".sidebar-section-head")?.click();
            sec?.scrollIntoView({ block: "center", behavior: "smooth" });
          } },
          val ? { label: `Copy model: ${val}`, run: () => copyText(val) } : null,
          { label: "Refresh models", run: () => document.getElementById("refreshModelsBtn")?.click() },
        ].filter(Boolean),
      };
    }

    const service = t.closest?.(".service-row[data-svc]");
    if (service) {
      const svc = service.dataset.svc;
      return {
        type: "service",
        actions: [
          { label: `Restart ${svc}`, run: () => service.querySelector(".svc-restart")?.click() },
          { label: "Open Mission Control", run: () => window.switchToView?.("workstation") },
          { label: "Copy service name", run: () => copyText(svc) },
        ],
      };
    }

    return null;
  }

  function init() {
    document.querySelectorAll(".view-tab[data-view]").forEach((tab) => {
      tab.addEventListener("contextmenu", (e) => open(e, viewActions(tab.dataset.view)));
    });
    document.getElementById("sidebarFavoritesList")?.addEventListener("contextmenu", (e) => {
      const row = e.target.closest?.(".sidebar-fav-row");
      if (!row?.dataset?.view) return;
      open(e, viewActions(row.dataset.view));
    });

    document.addEventListener(
      "contextmenu",
      (e) => {
        if (e.defaultPrevented) return;
        if (e.target.closest?.(".aria-context-menu")) return;
        if (e.target.closest?.("input, textarea, select, .command-palette-modal")) return;
        const hit = resolveTarget(e);
        if (!hit) return;
        if (hit.type === "view") open(e, viewActions(hit.view));
        else if (hit.actions) open(e, hit.actions);
      },
      true,
    );
  }

  window.AriaContextMenu = { open, close, viewActions, copyText };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
