/** Discoverability — What's New, soft tips (accurate hotkeys from registry). */
(function () {
  "use strict";

  const WHATS_NEW_VERSION = "2026.07.29-global-ux";

  function chord(id, fallback) {
    return window.AriaHotkeys?.chord?.(id) || fallback;
  }

  function features() {
    return [
      {
        id: "shell-ux",
        title: "Professional shell",
        body: "Aria’s chrome is a calm desktop OS — steel accent, clear hierarchy, less glow. Products share one design system.",
      },
      {
        id: "ctx-palette",
        title: "Context-aware Commands",
        body: `${chord("palette", "Ctrl+K")} leads with actions for the page you’re on — Gallery, Planner, Mission Control, and more.`,
      },
      {
        id: "notifications",
        title: "Notifications",
        body: `Durable inbox for what still needs attention. Open from the Notifications button or ${chord("notifications", "Ctrl+Shift+A")}. Toasts are temporary; Job Center is live work.`,
      },
      {
        id: "layouts",
        title: "Layouts",
        body: `Shell presentation profiles — Coding, Writing, Research, and more. ${chord("layouts", "Ctrl+Shift+L")} (Ctrl+Shift+P still works).`,
      },
      {
        id: "split",
        title: "Split view",
        body: `Open two views side-by-side (${chord("split", "Ctrl+\\")}). Resize, swap, and exit when you’re done.`,
      },
      {
        id: "mini",
        title: "Floating mini chat",
        body: `Ask Aria from anywhere with the ✦ button or ${chord("mini_chat", "Ctrl+Shift+K")}. ${chord("mission", "Ctrl+Shift+M")} opens Mission Control.`,
      },
    ];
  }

  function tips() {
    return [
      { id: "tip-search", text: `Tip: ${chord("sidebar_search", "Ctrl+Shift+F")} searches views, settings, and tools from the sidebar.`, max: 3 },
      { id: "tip-chat", text: "Tip: In Chat, ask “what can you do?” for a guided tour of Aria’s abilities.", max: 3 },
      { id: "tip-status", text: "Tip: Mission Control shows provider health — open it when the status bar turns amber.", max: 3 },
      { id: "tip-cmdk", text: `Tip: ${chord("palette", "Ctrl+K")} shows page-specific actions first — try it on Gallery or Planner.`, max: 3 },
      { id: "tip-split", text: `Tip: ${chord("split", "Ctrl+\\")} splits the current view with another panel.`, max: 3 },
      { id: "tip-mc-hotkey", text: `Tip: ${chord("mission", "Ctrl+Shift+M")} opens Mission Control. ${chord("notifications", "Ctrl+Shift+A")} opens Notifications.`, max: 3 },
      { id: "tip-mini", text: `Tip: ${chord("mini_chat", "Ctrl+Shift+K")} toggles floating mini chat from any view.`, max: 3 },
    ];
  }

  function prefs() {
    return window.AriaUiPrefs?.load?.() || {};
  }

  function savePrefs(patch) {
    Object.entries(patch || {}).forEach(([k, v]) => window.AriaUiPrefs?.set?.(k, v));
  }

  function openWhatsNew(force) {
    const seen = prefs().whatsNewSeen || "";
    if (!force && seen === WHATS_NEW_VERSION) return;
    const list = document.getElementById("whatsNewList");
    const modal = document.getElementById("whatsNewModal");
    if (!list || !modal) return;
    list.innerHTML = features()
      .map((f) => `<li><strong>${f.title}</strong><p class="muted">${f.body}</p></li>`)
      .join("");
    modal.classList.remove("hidden");
  }

  function dismissWhatsNew() {
    document.getElementById("whatsNewModal")?.classList.add("hidden");
    savePrefs({ whatsNewSeen: WHATS_NEW_VERSION });
    maybeSoftTip();
  }

  function tipDismissedIds(raw) {
    if (Array.isArray(raw)) return raw.map(String);
    if (raw && typeof raw === "object") {
      return Object.keys(raw).filter((k) => raw[k]);
    }
    return [];
  }

  function maybeSoftTip() {
    const tip = document.getElementById("ariaSoftTip");
    if (!tip) return;
    const dismissed = new Set(tipDismissedIds(prefs().tipDismissed));
    const counts = prefs().tipSeenCount || {};
    const pool = tips().filter((t) => !dismissed.has(t.id) && (counts[t.id] || 0) < (t.max || 3));
    if (!pool.length) {
      tip.classList.add("hidden");
      return;
    }
    const pick = pool[Math.floor(Math.random() * pool.length)];
    tip.innerHTML = `<span>${pick.text}</span> <button type="button" class="ghost-btn tiny" id="ariaSoftTipDismiss" aria-label="Dismiss tip">Got it</button>`;
    tip.classList.remove("hidden");
    tip.setAttribute("role", "status");
    counts[pick.id] = (counts[pick.id] || 0) + 1;
    savePrefs({ tipSeenCount: counts });
    document.getElementById("ariaSoftTipDismiss")?.addEventListener("click", () => {
      dismissed.add(pick.id);
      savePrefs({ tipDismissed: [...dismissed] });
      tip.classList.add("hidden");
    });
  }

  function init() {
    document.getElementById("whatsNewBtn")?.addEventListener("click", () => openWhatsNew(true));
    document.getElementById("whatsNewDismissBtn")?.addEventListener("click", dismissWhatsNew);
    setTimeout(() => {
      if (document.body?.classList.contains("living-room") || document.body?.dataset.activity === "converse") {
        return; // Living Room owns first impression — no changelog wall
      }
      openWhatsNew(false);
    }, 1200);
    setTimeout(maybeSoftTip, 4000);
  }

  window.openWhatsNew = openWhatsNew;
  // Esc / modal chrome call window.dismissWhatsNew — must be exported or Esc no-ops
  // and leaves the changelog modal blocking owner clicks.
  window.dismissWhatsNew = dismissWhatsNew;
  window.AriaDiscoverability = { openWhatsNew, dismissWhatsNew, features, tips, WHATS_NEW_VERSION };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
