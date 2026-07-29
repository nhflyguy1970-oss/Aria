/** Global history — recent views, commands, searches, prompts, models, files, workflows. */
(function () {
  "use strict";

  const KEYS = {
    views: "recentViews",
    commands: "recentCommands",
    searches: "recentSearches",
    prompts: "recentPrompts",
    models: "recentModels",
    providers: "recentProviders",
    files: "recentFiles",
    workflows: "recentWorkflows",
  };

  function push(kind, id, max) {
    const key = KEYS[kind];
    if (!key || !id) return;
    window.AriaUiPrefs?.pushRecent?.(key, String(id), max || 16);
  }

  function list(kind) {
    const key = KEYS[kind];
    if (!key) return [];
    const v = window.AriaUiPrefs?.get?.(key, []);
    return Array.isArray(v) ? v : [];
  }

  function trackView(view) {
    push("views", view, 12);
  }

  function trackCommand(id) {
    push("commands", id, 16);
  }

  function trackSearch(q) {
    const s = String(q || "").trim();
    if (s.length < 2) return;
    push("searches", s, 12);
  }

  function trackPrompt(text) {
    const s = String(text || "").trim();
    if (s.length < 2) return;
    push("prompts", s.slice(0, 200), 20);
  }

  function trackModel(name) {
    if (name) push("models", name, 10);
  }

  function resumeItems() {
    const labels = window.AriaFavorites?.VIEW_LABELS || {};
    const items = [];
    list("views").slice(0, 6).forEach((v) => {
      items.push({
        kind: "view",
        id: v,
        label: labels[v] || v,
        run: () => window.switchToView?.(v),
      });
    });
    list("prompts").slice(0, 4).forEach((p) => {
      items.push({
        kind: "prompt",
        id: p,
        label: p.length > 48 ? `${p.slice(0, 48)}…` : p,
        run: () => {
          window.switchToView?.("chat");
          setTimeout(() => {
            if (typeof window.jarvisSendToChat === "function") window.jarvisSendToChat(p);
            else {
              const input = document.getElementById("messageInput");
              if (input) {
                input.value = p;
                input.focus();
              }
            }
          }, 60);
        },
      });
    });
    list("searches").slice(0, 3).forEach((q) => {
      items.push({
        kind: "search",
        id: q,
        label: `Search: ${q}`,
        run: () => window.openCommandPalette?.(q),
      });
    });
    return items;
  }

  function init() {
    window.addEventListener("aria-view-change", (e) => trackView(e.detail?.view));
    document.getElementById("chatForm")?.addEventListener("submit", () => {
      const v = document.getElementById("messageInput")?.value;
      trackPrompt(v);
    });
    document.getElementById("chatModelSelect")?.addEventListener("change", (e) => {
      trackModel(e.target?.value);
    });
  }

  window.AriaHistory = {
    push,
    list,
    trackView,
    trackCommand,
    trackSearch,
    trackPrompt,
    trackModel,
    resumeItems,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
