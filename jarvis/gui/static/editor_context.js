/** Cursor editor context pill/card + suggestion chips — extracted from app.js. */
(function () {
  const editorContextPill = document.getElementById("editorContextPill");
  const editorPillText = document.getElementById("editorPillText");
  const editorContextCard = document.getElementById("editorContextCard");
  const editorContextLabel = document.getElementById("editorContextLabel");
  const suggestionsEl = document.getElementById("suggestions");
  const messageInput = document.getElementById("messageInput");

  let editorContextPollTimer = null;

  function mediaWorkActive() {
    return typeof window.mediaWorkActive === "function" ? window.mediaWorkActive() : false;
  }

  function isNativeApp() {
    return typeof window.isNativeApp === "function" ? window.isNativeApp() : false;
  }

  function getLastEditorFile() {
    return window.lastEditorFile || "";
  }

  function setLastEditorFile(v) {
    window.lastEditorFile = v || "";
  }

  async function loadEditorContext() {
    if (mediaWorkActive()) return null;
    if (!editorContextPill && !editorContextCard) return null;
    try {
      const res = await fetch("/api/editor/context");
      if (!res.ok) return null;
      const data = await res.json();
      const ctx = data.context || {};
      const file = ctx.relative_file || "";
      const fresh = Boolean(data.fresh && file);
      const selLines = ctx.selection_lines || 0;
      const selNote = ctx.has_selection ? ` · ${selLines} line${selLines === 1 ? "" : "s"} selected` : "";
      const label = file ? `${file}${selNote}` : "";

      if (editorContextPill && editorPillText) {
        if (file) {
          editorContextPill.classList.remove("hidden");
          editorContextPill.classList.toggle("live", fresh);
          editorContextPill.classList.toggle("stale", !fresh);
          editorPillText.textContent = fresh
            ? `Cursor · ${file.split("/").pop()}${selNote}`
            : `Cursor (stale) · ${file.split("/").pop()}`;
          editorContextPill.title = fresh
            ? `Live from Cursor: ${label}`
            : `Stale — focus Cursor or run ARIA: Push Editor Context Now`;
        } else {
          editorContextPill.classList.remove("hidden");
          editorContextPill.classList.remove("live");
          editorContextPill.classList.add("stale");
          editorPillText.textContent = "Cursor · not synced";
          editorContextPill.title =
            "Install: ./scripts/install-cursor-extension.sh — then Reload Window in Cursor";
        }
      }

      if (editorContextCard && editorContextLabel) {
        if (file) {
          editorContextCard.classList.remove("hidden");
          editorContextCard.classList.toggle("live", fresh);
          editorContextLabel.textContent = fresh ? `Cursor · ${label}` : `Cursor (stale) · ${file}`;
          editorContextCard.title = editorContextPill?.title || label;
        } else {
          editorContextCard.classList.remove("hidden");
          editorContextCard.classList.remove("live");
          editorContextLabel.textContent = "Cursor: install extension";
          editorContextCard.title =
            "Run ./scripts/install-cursor-extension.sh then Reload Window in Cursor";
        }
      }

      if (fresh && file !== getLastEditorFile()) {
        setLastEditorFile(file);
        refreshEditorSuggestions(file, ctx.has_selection);
      }
      return { fresh, file, ctx };
    } catch (_) {
      return null;
    }
  }

  let lastEditorFresh = false;

  function scheduleEditorContextPoll() {
    if (editorContextPollTimer) clearTimeout(editorContextPollTimer);
    let delay;
    if (mediaWorkActive()) {
      delay = isNativeApp() ? 45000 : 20000;
    } else if (document.hidden) {
      delay = 30000;
    } else if (lastEditorFresh) {
      delay = 8000;
    } else {
      // No live Cursor context — do not hammer the serve process every 4s.
      delay = 20000;
    }
    editorContextPollTimer = setTimeout(async () => {
      if (!mediaWorkActive()) {
        const result = await loadEditorContext();
        lastEditorFresh = Boolean(result?.fresh);
      }
      scheduleEditorContextPoll();
    }, delay);
  }

  function refreshEditorSuggestions(file, hasSelection) {
    if (!suggestionsEl) return;
    const base = [
      "What can you do?",
      hasSelection ? "fix selection" : `fix ${file}`,
      hasSelection ? "explain selection" : `diagnose ${file}`,
      `run tests for ${file}`,
      `debug until tests pass for ${file}`,
    ];
    suggestionsEl.replaceChildren();
    base.forEach((text) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip";
      chip.textContent = text;
      chip.onclick = () => {
        if (messageInput) {
          messageInput.value = text;
          messageInput.focus();
        }
      };
      suggestionsEl.appendChild(chip);
    });
  }

  async function loadSuggestions() {
    try {
      const res = await fetch("/api/suggestions");
      const data = await res.json();
      if (window.jarvisAttach) {
        window.jarvisAttach.visionChips = data.vision_chips || [];
        window.jarvisAttach.dataChips = data.data_chips || [];
      }
      if (suggestionsEl) {
        suggestionsEl.replaceChildren();
        (data.suggestions || []).filter(Boolean).forEach((s) => {
          const chip = document.createElement("button");
          chip.type = "button";
          chip.className = "suggestion-chip";
          chip.textContent = s;
          chip.onclick = () => {
            if (messageInput) {
              messageInput.value = String(s);
              messageInput.focus();
            }
          };
          suggestionsEl.appendChild(chip);
        });
      }
      const pendingFile = window.jarvisAttach?.pendingFile;
      const pendingFile2 = window.jarvisAttach?.pendingFile2;
      if (pendingFile && window.isDataAttachment?.(pendingFile)) window.refreshDataChips?.();
      else if (pendingFile || pendingFile2) window.refreshVisionChips?.();
      const ed = await loadEditorContext();
      if (ed?.fresh && ed.file) refreshEditorSuggestions(ed.file, ed.ctx?.has_selection);
    } catch (err) {
      window.showAriaToast?.(err?.message || "Could not load suggestions", "err", 4000);
    }
  }

  window.loadEditorContext = loadEditorContext;
  window.scheduleEditorContextPoll = scheduleEditorContextPoll;
  window.refreshEditorSuggestions = refreshEditorSuggestions;
  window.loadSuggestions = loadSuggestions;
})();
