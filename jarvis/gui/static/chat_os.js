/** Aria Chat OS — Ask Aria, New Chat, context chips, reply actions (not a chatbot clone). */
(function () {
  "use strict";

  const CONTEXT_KINDS = [
    "memory", "document", "project", "connection", "planner",
    "calendar", "journal", "knowledge", "gallery",
  ];

  /** @type {{ kind: string, id: string, label: string }[]} */
  let contextChips = [];
  let lastUserPrompt = "";
  let returnView = "";

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return typeof window.escapeHtml === "function"
      ? window.escapeHtml(s)
      : String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function renderContextChips() {
    const row = $("chatContextChips");
    if (!row) return;
    if (!contextChips.length) {
      row.classList.add("hidden");
      row.innerHTML = "";
      return;
    }
    row.classList.remove("hidden");
    row.innerHTML = contextChips.map((c, i) =>
      `<button type="button" class="chat-ctx-chip" data-idx="${i}" title="${esc(c.kind)}:${esc(c.id)}">`
      + `@${esc(c.kind)} ${esc(c.label || c.id)}`
      + `<span class="chat-ctx-x" aria-label="Remove">×</span></button>`
    ).join("");
    row.querySelectorAll(".chat-ctx-chip").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = Number(btn.getAttribute("data-idx"));
        if (e.target?.classList?.contains("chat-ctx-x") || e.target === btn) {
          contextChips.splice(idx, 1);
          renderContextChips();
        }
      });
    });
  }

  function addContext(kind, id, label) {
    const k = String(kind || "").toLowerCase();
    if (!CONTEXT_KINDS.includes(k) || !id) return;
    if (contextChips.some((c) => c.kind === k && c.id === String(id))) return;
    contextChips.push({ kind: k, id: String(id), label: String(label || id) });
    renderContextChips();
  }

  function clearContext() {
    contextChips = [];
    renderContextChips();
  }

  function contextPrefix() {
    if (!contextChips.length) return "";
    const parts = contextChips.map((c) => `@${c.kind}:${c.id}`);
    return `[Context: ${parts.join(" ")}]\n`;
  }

  /**
   * Ask Aria — primary OS entry. Auto-sends by default (never mere pre-fill).
   * @param {string} text
   * @param {{
   *   autoSend?: boolean,
   *   switchView?: boolean,
   *   returnView?: string,
   *   context?: {kind:string,id:string,label?:string}[],
   *   fillOnly?: boolean,
   *   onToken?: (t:string)=>void,
   *   onDone?: (data:any)=>void,
   * }} [opts]
   */
  async function askAria(text, opts = {}) {
    const msg = String(text || "").trim();
    if (!msg && opts.fillOnly) return;
    const fillOnly = opts.fillOnly === true;
    const autoSend = opts.autoSend !== false && !fillOnly;
    const switchView = opts.switchView !== false;

    if (Array.isArray(opts.context)) {
      opts.context.forEach((c) => addContext(c.kind, c.id, c.label));
    }
    if (opts.returnView) returnView = opts.returnView;

    if (switchView) window.switchToView?.("chat");

    const composed = contextPrefix() + msg;
    lastUserPrompt = composed;

    const input = $("messageInput");
    if (input) {
      input.value = fillOnly || !autoSend ? composed : "";
      window.resizeMessageInput?.();
    }

    if (!autoSend || fillOnly) {
      setTimeout(() => input?.focus(), 40);
      return;
    }

    // Prefer sendMessage (full pipeline including attachments / streaming)
    if (typeof window.sendMessage === "function") {
      await window.sendMessage(composed, false, {
        onToken: opts.onToken,
        onDone: (event, full) => {
          try { opts.onDone?.(event, full); } catch (_) {}
          if (returnView && returnView !== "chat") {
            window.showAriaToast?.(`Reply ready — return to ${returnView} when done`, "info", 3500);
            returnView = "";
          }
        },
      });
      clearContext();
      return;
    }

    if (input) input.value = composed;
    $("chatForm")?.requestSubmit?.();
  }

  /** @deprecated Prefer askAria — kept as alias that auto-sends. */
  function jarvisSendToChat(text, opts) {
    return askAria(text, { ...(opts || {}), autoSend: opts?.autoSend !== false, fillOnly: opts?.fillOnly === true });
  }

  async function newChat(title) {
    const name = (title || "").trim() || `Chat ${new Date().toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}`;
    try {
      const res = await fetch("/api/chat/new", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: name, name }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) throw new Error(data.message || data.error || `New chat failed (${res.status})`);
      window.activeBranchId = data.branch_id;
      window.switchToView?.("chat");
      if (typeof window.loadBranches === "function") await window.loadBranches();
      else {
        const sel = $("branchSelect");
        if (sel && data.branch_id) {
          // force reload via change path
          await fetch("/api/branches/switch", {
            method: "POST",
            body: (() => { const f = new FormData(); f.append("branch_id", data.branch_id); return f; })(),
          });
        }
      }
      if (typeof window.reloadBranchMessages === "function") await window.reloadBranchMessages();
      window.loadChatSessions?.();
      clearContext();
      $("messageInput")?.focus();
      window.showAriaToast?.(data.message || "New chat started", "ok", 2500);
      return data;
    } catch (err) {
      window.showAriaToast?.(err.message || "Could not start new chat", "err", 5000);
      return null;
    }
  }

  function regenerate() {
    const prompt = lastUserPrompt || document.querySelector(".message.user:last-of-type .msg-body")?.dataset?.rawText
      || document.querySelector(".message.user:last-of-type .msg-body")?.textContent || "";
    if (!prompt.trim()) {
      window.showAriaToast?.("Nothing to regenerate", "warn");
      return;
    }
    askAria(prompt.replace(/^\[Context:[^\]]*\]\n/, ""), { switchView: true, autoSend: true });
  }

  function editLastPrompt() {
    const prompt = lastUserPrompt || document.querySelector(".message.user:last-of-type .msg-body")?.dataset?.rawText || "";
    const input = $("messageInput");
    if (!input || !prompt.trim()) return;
    input.value = prompt;
    window.resizeMessageInput?.();
    input.focus();
  }

  function parseAtMentions(text) {
    const re = /@([a-z]+):([^\s\]]+)/gi;
    let m;
    while ((m = re.exec(text || ""))) {
      addContext(m[1], m[2], m[2]);
    }
  }

  function wireComposerAtMentions() {
    const input = $("messageInput");
    if (!input || input.dataset.ctxWired) return;
    input.dataset.ctxWired = "1";
    input.addEventListener("keydown", (e) => {
      if (e.key === " " || e.key === "Enter") parseAtMentions(input.value);
    });
    // Autocomplete panel for @
    input.addEventListener("input", () => {
      const v = input.value;
      const at = v.match(/@([a-z]*)$/i);
      const box = $("chatAtSuggest");
      if (!box) return;
      if (!at) {
        box.classList.add("hidden");
        return;
      }
      const q = (at[1] || "").toLowerCase();
      const hits = CONTEXT_KINDS.filter((k) => k.startsWith(q));
      if (!hits.length) {
        box.classList.add("hidden");
        return;
      }
      box.classList.remove("hidden");
      box.innerHTML = hits.map((k) => `<button type="button" class="ghost-btn tiny" data-k="${k}">@${k}</button>`).join("");
      box.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
          input.value = v.replace(/@[a-z]*$/i, `@${btn.dataset.k}:`);
          box.classList.add("hidden");
          input.focus();
        });
      });
    });
  }

  function openCitation(cite) {
    const source = String(cite.source || cite.type || "memory").toLowerCase();
    const id = cite.id || cite.path || cite.name || "";
    if (source.includes("document") || source === "doc" || cite.path) {
      window.switchToView?.("documents");
      setTimeout(() => {
        const q = cite.path || cite.content || id;
        if ($("documentsSearchInput")) $("documentsSearchInput").value = String(q).slice(0, 80);
        $("documentsSearchBtn")?.click();
      }, 80);
      return;
    }
    if (source.includes("connection") || source === "entity" || source === "graph") {
      window.switchToView?.("connections");
      setTimeout(() => {
        if ($("connectionsSearchInput")) $("connectionsSearchInput").value = cite.name || id || cite.content || "";
        $("connectionsSearchBtn")?.click();
      }, 80);
      return;
    }
    if (source.includes("project")) {
      window.switchToView?.("projects");
      return;
    }
    if (source.includes("planner") || source.includes("task")) {
      window.switchToView?.("planner");
      return;
    }
    if (source.includes("journal")) {
      window.switchToView?.("journal");
      return;
    }
    if (source.includes("knowledge") || source.includes("brief")) {
      window.switchToView?.("documents");
      window.showAriaToast?.("Knowledge Briefs live with Documents / research", "info", 3000);
      return;
    }
    // Default: Memory
    window.switchToView?.("memory");
    setTimeout(() => {
      const search = $("memorySearch");
      if (search) {
        search.value = (cite.content || cite.title || id || "").slice(0, 80);
        search.dispatchEvent(new Event("input"));
      }
    }, 80);
  }

  function attachReplyActions(bubble, meta = {}) {
    if (!bubble || bubble.querySelector(".chat-reply-actions")) return;
    const actions = document.createElement("div");
    actions.className = "chat-reply-actions";
    const raw = bubble.querySelector(".msg-body")?.dataset?.rawText
      || bubble.querySelector(".msg-body")?.textContent
      || "";
    const btns = [
      { id: "regen", label: "Regenerate", run: () => regenerate() },
      { id: "retry", label: "Retry", run: () => regenerate() },
      { id: "edit", label: "Edit prompt", run: () => editLastPrompt() },
      { id: "task", label: "Planner task", run: () => {
        window.switchToView?.("planner");
        setTimeout(() => {
          const inp = $("plannerTaskInput");
          if (inp) { inp.value = raw.slice(0, 120); inp.focus(); }
        }, 80);
      } },
      { id: "memory", label: "Stage Memory", run: () => {
        askAria(`Stage this as a Memory candidate (do not encode yet):\n${raw.slice(0, 500)}`, { autoSend: true });
      } },
      { id: "conn", label: "Connections review", run: () => {
        window.switchToView?.("connections");
        setTimeout(() => {
          $("connectionsImportBtn")?.click();
          setTimeout(() => {
            if ($("connectionsImportText")) $("connectionsImportText").value = raw.slice(0, 2000);
          }, 100);
        }, 80);
      } },
      { id: "journal", label: "Journal", run: () => {
        window.switchToView?.("journal");
        setTimeout(() => {
          const rapid = $("rapidLogInput");
          if (rapid) { rapid.value = raw.slice(0, 200); rapid.focus(); }
        }, 80);
      } },
    ];
    // Keep ordinary chats light — show core actions always; contextual extras when module hints
    const always = ["regen", "edit"];
    const contextual = [];
    if (/task|todo|plan/i.test(raw) || meta.module === "planner") contextual.push("task");
    if (/remember|prefer|I am|my /i.test(raw) || meta.module === "memory") contextual.push("memory");
    if (/related|connect|works at|uses/i.test(raw)) contextual.push("conn");
    if (meta.module === "journal") contextual.push("journal");
    const show = new Set([...always, ...contextual, "retry"]);
    btns.filter((b) => show.has(b.id)).forEach((b) => {
      const el = document.createElement("button");
      el.type = "button";
      el.className = "ghost-btn tiny";
      el.textContent = b.label;
      el.addEventListener("click", b.run);
      actions.appendChild(el);
    });
    bubble.appendChild(actions);
  }

  function initChatOsUi() {
    $("chatNewBtn")?.addEventListener("click", () => {
      const dlg = $("chatNewDialog");
      if (dlg?.showModal) {
        if ($("chatNewTitleInput")) $("chatNewTitleInput").value = "";
        dlg.showModal();
      } else newChat();
    });
    $("chatNewConfirmBtn")?.addEventListener("click", (e) => {
      e.preventDefault();
      const title = $("chatNewTitleInput")?.value?.trim();
      $("chatNewDialog")?.close?.();
      newChat(title);
    });
    wireComposerAtMentions();
    // Sync composer model chip with sidebar select
    const side = $("chatModelSelect");
    const chip = $("chatComposerModelSelect");
    if (side && chip && !chip.dataset.wired) {
      chip.dataset.wired = "1";
      const syncOpts = () => { chip.innerHTML = side.innerHTML; chip.value = side.value; };
      syncOpts();
      const obs = new MutationObserver(syncOpts);
      obs.observe(side, { childList: true });
      chip.addEventListener("change", () => {
        if (window.jarvisChat?.chatAbortController && !window.jarvisChat?.chatStopRequested) {
          // Do not interrupt active stream — queue change after
          window.showAriaToast?.("Model will apply on the next message", "info", 2500);
        }
        side.value = chip.value;
        side.dispatchEvent(new Event("change"));
      });
      side.addEventListener("change", () => { chip.value = side.value; });
    }
    // A11y live region
    const messages = $("messages");
    if (messages && !messages.getAttribute("aria-live")) {
      messages.setAttribute("role", "log");
      messages.setAttribute("aria-live", "polite");
      messages.setAttribute("aria-relevant", "additions");
    }
    const prog = $("progressBar");
    if (prog) {
      prog.setAttribute("role", "status");
      prog.setAttribute("aria-live", "polite");
    }
  }

  window.AriaChatOS = {
    askAria,
    newChat,
    regenerate,
    editLastPrompt,
    addContext,
    clearContext,
    openCitation,
    attachReplyActions,
    getContext: () => contextChips.slice(),
    getLastPrompt: () => lastUserPrompt,
  };

  // Replace pre-fill-only helper with OS auto-send
  window.jarvisSendToChat = jarvisSendToChat;
  window.jarvisAskAria = askAria;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initChatOsUi);
  } else {
    initChatOsUi();
  }
})();
