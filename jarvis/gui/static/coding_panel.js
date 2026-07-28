/** Coding tools + LSP panel — extracted from app.js. */
(function () {
  "use strict";

function lspPathValue() {
  const el = document.getElementById("lspPath");
  return el?.value?.trim() || window.lastEditorFile || "";
}

function lspLineValue() {
  const el = document.getElementById("lspLine");
  const n = parseInt(el?.value || "1", 10);
  return Number.isFinite(n) && n > 0 ? n : 1;
}

function setLspOut(text) {
  const out = document.getElementById("lspOut");
  if (out) out.textContent = text || "";
}

async function runLspAction(kind) {
  const path = lspPathValue();
  const line = lspLineValue();
  if (!path) {
    const msg = "Enter a file path or sync Cursor editor context.";
    setLspOut(msg);
    window.showAriaToast?.(msg, "warn", 3500);
    return;
  }
  setLspOut(kind === "diagnostics" ? "Checking…" : "…");
  const q = new URLSearchParams({ path, line: String(line), column: "1" });
  // Quick diagnostics by default — deep mypy can hang the UI for a long time.
  if (kind === "diagnostics") q.set("deep", "0");
  let url = `/api/lsp/${kind}?${q}`;
  let opts = {};
  if (kind === "format") {
    url = "/api/lsp/format";
    const form = new FormData();
    form.append("path", path);
    form.append("write", "1");
    opts = { method: "POST", body: form };
  }
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), kind === "diagnostics" ? 25000 : 45000);
  opts = { ...opts, signal: ctrl.signal };
  try {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      const msg = data.message || data.detail || "LSP request failed";
      setLspOut(msg);
      window.showAriaToast?.(msg, "err", 5000);
      return;
    }
    if (kind === "diagnostics") {
      setLspOut(data.summary || "No issues");
    } else if (kind === "definition") {
      const locs = data.locations || [];
      setLspOut(locs.length ? locs.map((l) => `${l.path}:${l.line}`).join("\n") : "No definition");
    } else if (kind === "references") {
      const refs = data.references || [];
      setLspOut(refs.length ? refs.slice(0, 25).map((r) => `${r.path}:${r.line}`).join("\n") : "No references");
    } else if (kind === "hover") {
      setLspOut(data.hover || "(empty)");
    } else if (kind === "symbols") {
      const syms = data.symbols || [];
      setLspOut(syms.slice(0, 40).map((s) => `${s.name} (L${s.line})`).join("\n") || "No symbols");
    } else if (kind === "format") {
      setLspOut(data.written ? `Formatted ${path}` : "Format preview only");
    }
  } catch (e) {
    const msg = e?.name === "AbortError" ? "LSP timed out — try again or narrow the file" : String(e);
    setLspOut(msg);
    window.showAriaToast?.(msg, "err", 5000);
  } finally {
    clearTimeout(timer);
  }
}

document.getElementById("lspDiagBtn")?.addEventListener("click", () => runLspAction("diagnostics"));
document.getElementById("lspDefBtn")?.addEventListener("click", () => runLspAction("definition"));
document.getElementById("lspRefBtn")?.addEventListener("click", () => runLspAction("references"));
document.getElementById("lspHoverBtn")?.addEventListener("click", () => runLspAction("hover"));
document.getElementById("lspSymBtn")?.addEventListener("click", () => runLspAction("symbols"));
document.getElementById("lspFmtBtn")?.addEventListener("click", () => runLspAction("format"));

async function loadCodingPanel() {
  const toolsEl = document.getElementById("codingTools");
  const tasksEl = document.getElementById("codingTasks");
  if (!toolsEl) return;
  const banner = document.getElementById("codingRootBanner");
  if (banner) {
    try {
      const gRes = await fetch("/api/coding/guardrails");
      if (gRes.ok) {
        const g = await gRes.json();
        const proj = g.active_project?.title || g.active_project?.slug || "—";
        const root = g.write_target || g.coding_root || "—";
        const branch = g.repository?.branch ? ` · ${g.repository.branch}` : "";
        banner.textContent = `Project: ${proj} → ${root}${branch}`;
        banner.classList.toggle("coding-root-banner--warn", g.severity === "warn");
        banner.classList.toggle("coding-root-banner--error", g.severity === "error");
        if (g.severity === "error") {
          banner.title = (g.warnings || []).map((w) => w.message).join("\n");
        }
      }
    } catch {
      banner.textContent = "Coding root: unavailable";
    }
  }
  const ed = await window.loadEditorContext?.();
  const lspPath = document.getElementById("lspPath");
  if (lspPath && ed?.file && !lspPath.value.trim()) {
    lspPath.value = ed.file;
    const lspLine = document.getElementById("lspLine");
    if (lspLine && ed.ctx?.cursor_line) lspLine.value = String(ed.ctx.cursor_line);
  }
  try {
    const [toolsRes, tasksRes, lspRes] = await Promise.all([
      fetch("/api/coding/tools"),
      fetch("/api/coding/tasks"),
      fetch("/api/lsp/status"),
    ]);
    if (toolsRes.ok) {
      const tools = await toolsRes.json();
      const active = Object.entries(tools).filter(([, v]) => v).map(([k]) => k);
      let lspNote = "";
      if (lspRes.ok) {
        const lsp = await lspRes.json();
        const servers = (lsp.servers || []).filter((s) => s.available).map((s) => s.id);
        lspNote = servers.length ? ` · LSP: ${servers.join(", ")}` : " · LSP: install servers";
      }
      toolsEl.textContent = active.length ? `Checkers: ${active.join(", ")}${lspNote}` : `No extra checkers${lspNote}`;
    }
    if (tasksEl && tasksRes.ok) {
      const data = await tasksRes.json();
      const tasks = data.tasks || [];
      if (!tasks.length) {
        tasksEl.innerHTML = "<span class='muted'>No coding tasks. <button type='button' class='ghost-btn tiny' id='codingEmptyChatBtn'>Ask Chat</button></span>";
        tasksEl.querySelector("#codingEmptyChatBtn")?.addEventListener("click", () => {
          window.switchToView?.("chat");
          window.jarvisSendToChat?.("Create a coding task: ");
        });
      } else {
        tasksEl.innerHTML = tasks.slice(0, 5).map((t) =>
          `<div class="coding-task-row"><span>${window.escapeHtml(t.id)}</span> <span class="muted">${window.escapeHtml(t.status)}</span></div>`
        ).join("");
      }
    }
  } catch (err) {
    toolsEl.textContent = "Coding tools offline";
    window.showAriaToast?.(err?.message || "Coding panel unavailable", "err", 4000);
  }
}

document.getElementById("indexCodeBtn")?.addEventListener("click", async () => {
  const statusText = document.getElementById("statusText");
  if (statusText) statusText.textContent = "Indexing code…";
  try {
    const res = await fetch("/api/code/reindex", { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || data.detail || `Index failed (${res.status})`);
    }
    if (statusText) statusText.textContent = data.message || "Code index rebuilt";
    window.showAriaToast?.(data.message || "Code index rebuilt", "ok", 3000);
    loadCodingPanel();
  } catch (err) {
    if (statusText) statusText.textContent = err.message || "Index failed";
    window.showAriaToast?.(err.message || "Code index failed", "err", 5000);
  }
});


  window.runLspAction = runLspAction;
  window.loadCodingPanel = loadCodingPanel;
})();
