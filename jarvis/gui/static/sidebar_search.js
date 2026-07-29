/** Universal sidebar search — everyday navigation filter (Ctrl+K stays the power palette). */
(function () {
  "use strict";

  let items = [];
  let results = [];
  let activeIndex = -1;

  function $(id) {
    return document.getElementById(id);
  }

  function fuzzyScore(hay, needle) {
    hay = hay.toLowerCase();
    needle = needle.toLowerCase().trim();
    if (!needle) return 0;
    if (hay === needle) return 100;
    if (hay.startsWith(needle)) return 85;
    if (hay.includes(needle)) return 60;
    const parts = needle.split(/\s+/).filter(Boolean);
    if (parts.length > 1 && parts.every((p) => hay.includes(p))) return 45;
    let i = 0;
    for (const ch of hay) {
      if (ch === needle[i]) i += 1;
      if (i >= needle.length) return 25;
    }
    return 0;
  }

  function usageBoost(item) {
    const prefs = window.AriaUiPrefs?.load?.() || {};
    let b = 0;
    if (item.view) {
      b += Math.min(15, ((prefs.viewVisits || {})[item.view] || 0));
      if ((prefs.favorites || []).includes(item.view)) b += 20;
      if ((prefs.recentViews || []).slice(0, 4).includes(item.view)) b += 10;
    }
    if (item.commandId) {
      b += Math.min(12, ((prefs.commandUsage || {})[item.commandId] || 0) * 2);
      if ((prefs.pinnedCommands || []).includes(item.commandId)) b += 18;
    }
    return b;
  }

  function buildIndex() {
    const labels = window.AriaFavorites?.VIEW_LABELS || {};
    const sectionOf = {
      chat: "AI", search: "Workspace", settings: "Workspace", dashboard: "Home", workstation: "Mission Control", planner: "Workspace",
      calendar: "Workspace", journal: "Workspace", memory: "Workspace", projects: "Developer",
      documents: "Workspace", browser: "AI", flytying: "Maker", maker: "Maker",
      gallery: "Media", video: "Media", meme: "Media", audio: "Media", voice: "Media",
      security: "System", presence: "System", audit: "System", actions: "System",
      capabilities: "System", integrations: "System", connections: "Workspace",
      coding: "Developer", models: "System", automation: "Home", vision: "Media",
    };
    const views = Object.entries(labels).map(([view, label]) => ({
      type: "View",
      label,
      hint: sectionOf[view] || "View",
      view,
      keywords: view,
      run: () => window.switchToView?.(view),
    }));

    const settings = [
      { label: "Settings Home", el: "settingsBtn", keywords: "preferences catalog appearance ctrl+," },
      { label: "Voice & Chat", el: "voiceChatSettingsBtn", keywords: "speak whisper voice" },
      { label: "Keyboard shortcuts", el: "shortcutsBtn", keywords: "keys hotkeys" },
      { label: "What's New", el: "whatsNewBtn", keywords: "features changelog recent" },
      { label: "Job center", el: "jobCenterBtn", keywords: "background media coding jobs" },
      { label: "Debug bundle", el: "debugBundleBtn", keywords: "diagnostics support" },
      { label: "Light / dark theme", el: "themeToggle", keywords: "appearance color" },
      { label: "Restart server", el: "restartServerBtn", keywords: "reboot api" },
      { label: "Backup data", el: "backupDataBtn", keywords: "export save" },
      { label: "Image settings (SD/SDXL/Flux)", el: "openImageSettingsBtn", keywords: "checkpoint comfy gpu" },
      { label: "Coding Home", section: "coding", keywords: "propose apply undo verify lsp git proposals ctrl+shift+c" },
      { label: "Model settings", section: "models", keywords: "ollama chat coder vision embed" },
      { label: "Smart Home setup", section: "home", keywords: "home assistant ha kasa token" },
      { label: "Integrations (API keys)", section: "integrations", keywords: "gemini openai hugging face" },
      { label: "Developer tools", section: "coding", keywords: "lsp git lan coding" },
    ].map((s) => ({
      type: "Setting",
      label: s.label,
      hint: "Settings",
      keywords: s.keywords || "",
      run: () => {
        if (s.el) {
          $(s.el)?.click();
          return;
        }
        if (s.section) {
          const sec = document.querySelector(`.sidebar-section[data-section="${s.section}"]`);
          if (sec) {
            if (sec.classList.contains("collapsed")) sec.querySelector(".sidebar-section-head")?.click();
            sec.scrollIntoView({ block: "center", behavior: "smooth" });
            sec.classList.add("sidebar-section--flash");
            setTimeout(() => sec.classList.remove("sidebar-section--flash"), 1600);
          }
        }
      },
    }));

    const modelSelect = $("chatModelSelect");
    const models = modelSelect
      ? [...modelSelect.options]
          .filter((o) => o.value)
          .slice(0, 20)
          .map((o) => ({
            type: "Model",
            label: o.textContent || o.value,
            hint: "Model",
            commandId: `model:${o.value}`,
            keywords: `ollama model ${o.value}`,
            run: () => {
              modelSelect.value = o.value;
              modelSelect.dispatchEvent(new Event("change", { bubbles: true }));
              window.showAriaToast?.(`Model: ${o.textContent || o.value}`, "ok", 2200);
            },
          }))
      : [];

    const tools = [
      { label: "Command palette", keywords: "ctrl k commands power", run: () => window.openCommandPalette?.() },
      { label: "Free VRAM", el: "freeVramBtn", keywords: "gpu unload ollama" },
      { label: "Pomodoro timer", keywords: "focus 25", run: () => { window.switchToView?.("planner"); setTimeout(() => $("plannerPomodoroBtn")?.click(), 150); } },
      { label: "Clear conversation", el: "clearBtn", keywords: "chat reset" },
    ].map((t) => ({
      type: "Tool",
      label: t.label,
      hint: "Tool",
      keywords: t.keywords || "",
      run: t.run || (() => $(t.el)?.click()),
    }));

    items = [...views, ...settings, ...models, ...tools];
  }

  function searchDeepLinks(q) {
    // Views win by fuzzy; deep content search stays in Ctrl+K to keep this instant.
    return [{
      type: "More",
      label: `Open Search Home for “${q}”`,
      hint: "Browse everything",
      keywords: "federated content",
      run: () => {
        window.switchToView?.("search");
        setTimeout(() => {
          const el = document.getElementById("searchHomeInput");
          if (el) {
            el.value = q;
            window.runSearchHomeQuery?.();
          }
        }, 80);
      },
    }, {
      type: "More",
      label: `Quick search in Ctrl+K for “${q}”`,
      hint: "Ctrl+K",
      keywords: "",
      run: () => {
        window.openCommandPalette?.(q);
      },
    }];
  }

  function doSearch(q) {
    buildIndex();
    const needle = q.trim();
    if (!needle) {
      results = [];
      renderResults();
      return;
    }
    const scored = items
      .map((it) => ({ it, s: fuzzyScore(`${it.label} ${it.keywords || ""}`, needle) }))
      .filter((x) => x.s > 0)
      .map((x) => ({ it: x.it, s: x.s + usageBoost(x.it) }))
      .sort((a, b) => b.s - a.s);
    results = [...scored.slice(0, 9).map((x) => x.it), ...searchDeepLinks(needle)];
    activeIndex = results.length ? 0 : -1;
    renderResults(needle);
  }

  function highlight(label, needle) {
    if (!needle) return escapeHtml(label);
    const idx = label.toLowerCase().indexOf(needle.toLowerCase());
    if (idx < 0) return escapeHtml(label);
    return (
      escapeHtml(label.slice(0, idx)) +
      `<mark>${escapeHtml(label.slice(idx, idx + needle.length))}</mark>` +
      escapeHtml(label.slice(idx + needle.length))
    );
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function renderResults(needle) {
    const list = $("sidebarSearchResults");
    if (!list) return;
    list.replaceChildren();
    list.classList.toggle("hidden", !results.length);
    results.forEach((it, i) => {
      const li = document.createElement("li");
      li.className = `sidebar-search-item${i === activeIndex ? " active" : ""}`;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === activeIndex ? "true" : "false");
      li.innerHTML = `<span class="sidebar-search-label">${highlight(it.label, needle || "")}</span><span class="sidebar-search-hint">${escapeHtml(it.hint || it.type)}</span>`;
      li.addEventListener("mousedown", (e) => {
        e.preventDefault();
        runResult(i);
      });
      li.addEventListener("mouseenter", () => {
        activeIndex = i;
        syncActive();
      });
      list.appendChild(li);
    });
  }

  function syncActive() {
    const list = $("sidebarSearchResults");
    list?.querySelectorAll(".sidebar-search-item").forEach((el, i) => {
      el.classList.toggle("active", i === activeIndex);
      el.setAttribute("aria-selected", i === activeIndex ? "true" : "false");
    });
  }

  function runResult(i) {
    const it = results[i];
    if (!it) return;
    clearSearch();
    it.run?.();
  }

  function clearSearch() {
    const input = $("sidebarSearchInput");
    if (input) input.value = "";
    results = [];
    activeIndex = -1;
    renderResults();
  }

  function init() {
    const input = $("sidebarSearchInput");
    if (!input) return;
    let t = null;
    input.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => doSearch(input.value), 60);
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (results.length) {
          activeIndex = (activeIndex + 1) % results.length;
          syncActive();
        }
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (results.length) {
          activeIndex = (activeIndex - 1 + results.length) % results.length;
          syncActive();
        }
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (activeIndex >= 0) runResult(activeIndex);
      } else if (e.key === "Escape") {
        clearSearch();
        input.blur();
      }
    });
    input.addEventListener("blur", () => {
      setTimeout(() => {
        if (document.activeElement !== input) renderResultsHiddenOnBlur();
      }, 120);
    });
    // Ctrl+Shift+F focuses sidebar search
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "f") {
        e.preventDefault();
        input.focus();
        input.select();
      }
    });
  }

  function renderResultsHiddenOnBlur() {
    $("sidebarSearchResults")?.classList.add("hidden");
  }

  window.AriaSidebarSearch = { doSearch, clearSearch };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
