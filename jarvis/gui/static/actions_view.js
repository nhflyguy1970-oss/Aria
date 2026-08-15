/** Actions log view — extracted from movie_tiers.js. */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function isRoomAbort(err) {
    return !!(
      window.AriaNet?.isRoomAbort?.(err) ||
      err?.name === "AbortError" ||
      /aborted|aria-room-leave/i.test(String(err?.message || err?.reason || ""))
    );
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    // /api/actions returns {actions} without ok — only treat explicit false as failure.
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || data.detail || `Request failed (${res.status})`);
    }
    return data;
  }

  function initActionsFilter() {
    const sel = $("actionsFilter");
    if (!sel) return;
    sel.addEventListener("change", () => {
      window.loadActions?.(sel.value);
    });
    $("actionsOpenChatBtn")?.addEventListener("click", () => window.switchToView?.("chat"));
    $("actionsOpenAuditBtn")?.addEventListener("click", () => window.switchToView?.("audit"));
    $("actionsOpenMcBtn")?.addEventListener("click", () => window.switchToView?.("workstation"));
  }

  window.loadActions = async function (moduleFilter) {
    const el = $("actionsList");
    if (!el) return;
    const gen = (window.loadActions._gen = (window.loadActions._gen || 0) + 1);
    const mod = moduleFilter ?? $("actionsFilter")?.value ?? "";
    const q = mod ? `?module=${encodeURIComponent(mod)}` : "";
    try {
      const data = await fetchJson(`/api/actions${q}`);
      if (gen !== window.loadActions._gen) return;
      const acts = data.actions || [];
      el.innerHTML = acts.length
        ? acts
            .map(
              (a) =>
                `<li><span class="act-time">${escapeHtml((a.time || "").slice(0, 19))}</span> `
                + `<strong>${escapeHtml(a.action || a.event || "")}</strong> `
                + `${a.module ? `<code>${escapeHtml(a.module)}</code> ` : ""}`
                + `${escapeHtml((a.detail || "").slice(0, 80))}</li>`
            )
            .join("")
        : "<li class='muted'>No actions logged yet. <button type='button' class='ghost-btn tiny' id='actionsEmptyChatBtn'>Open Chat</button></li>";
      el.querySelector("#actionsEmptyChatBtn")?.addEventListener("click", () => window.switchToView?.("chat"));
    } catch (err) {
      if (gen !== window.loadActions._gen) return;
      if (isRoomAbort(err)) {
        const still =
          document.body.classList.contains("house-actions") ||
          /^#?actions\b/i.test(location.hash || "");
        if (still) {
          clearTimeout(window.loadActions._retry);
          window.loadActions._retry = setTimeout(() => {
            if (
              document.body.classList.contains("house-actions") ||
              /^#?actions\b/i.test(location.hash || "")
            ) {
              window.loadActions?.(mod);
            }
          }, 160);
        }
        return;
      }
      el.innerHTML = "<li>Could not load actions.</li>";
      window.showAriaToast?.(err?.message || "Could not load actions", "err", 5000);
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    initActionsFilter();
  });
})();
