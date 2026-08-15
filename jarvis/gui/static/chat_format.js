/** Message formatting and copy helpers — extracted from app.js. */
(function () {
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function formatMessage(text) {
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
    // Render only trusted local media markdown as real images (reload must show the asset).
    // External ![…](https://…) is a known LLM lie — never embed; surface as a failure.
    html = html.replace(
      /!\[([^\]]*)\]\(([^)\s]+)\)/g,
      (_m, alt, url) => {
        const u = String(url || "").trim();
        const local =
          /^\/api\/(gallery|meme-gallery|uploads|video-gallery|audio\/file)\b/i.test(u) ||
          /^\/media\//i.test(u);
        if (!local) {
          return (
            `<p class="chat-fake-media warn" role="status">` +
            `Image link was not a real Aria asset (blocked external URL). ` +
            `Generation did not produce a Gallery file.</p>`
          );
        }
        const name = (u.split("/").pop() || "image").split("?")[0];
        const src = typeof window.apiAuthUrl === "function" ? window.apiAuthUrl(u) : u;
        const altEsc = escapeHtml(alt || name);
        // Path shape must include /generated/ so resolveImageUrl maps to Gallery.
        const pathGuess = `data/generated/${decodeURIComponent(name)}`;
        return (
          `<figure class="gen-image" data-image-path="${escapeHtml(pathGuess)}">` +
          `<img class="clickable-image" src="${escapeHtml(src)}" alt="${altEsc}" ` +
          `loading="lazy" decoding="async" data-full-src="${escapeHtml(src)}" ` +
          `data-image-path="${escapeHtml(pathGuess)}" title="Click to view and edit" />` +
          `<figcaption>${escapeHtml(name)}</figcaption></figure>`
        );
      }
    );
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  function messagePlainText(bodyEl) {
    if (!bodyEl) return "";
    return (bodyEl.innerText || bodyEl.textContent || "").trim();
  }

  async function copyTextToClipboard(text) {
    const value = (text || "").trim();
    if (!value) return false;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value);
        return true;
      }
    } catch (_) { /* fall through */ }
    try {
      const ta = document.createElement("textarea");
      ta.value = value;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      return ok;
    } catch (_) {
      return false;
    }
  }

  function isTextEntryElement(el) {
    if (!el) return false;
    const tag = el.tagName;
    if (tag === "TEXTAREA" || tag === "INPUT") return true;
    return Boolean(el.isContentEditable);
  }

  function syncMessageRawText(body, text) {
    if (!body) return;
    const t = (text || "").trim();
    if (t) body.dataset.rawText = t;
  }

  function createCopyButton(body) {
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "ghost-btn small copy-btn";
    copyBtn.title = "Copy message";
    copyBtn.textContent = "Copy";
    copyBtn.onclick = async () => {
      const text = body.dataset.rawText || messagePlainText(body);
      const ok = await copyTextToClipboard(text);
      const statusText = document.getElementById("statusText");
      if (ok) {
        copyBtn.classList.add("copied");
        copyBtn.textContent = "Copied";
        if (statusText) statusText.textContent = "Message copied";
        window.showAriaToast?.("Message copied", "ok", 2000);
        setTimeout(() => {
          copyBtn.classList.remove("copied");
          copyBtn.textContent = "Copy";
        }, 1600);
      } else {
        if (statusText) statusText.textContent = "Select text and press Ctrl+C";
        window.showAriaToast?.("Copy failed — select text and press Ctrl+C", "warn", 4000);
      }
    };
    return copyBtn;
  }

  function ensureMessageCopyAction(messageDiv, body) {
    if (!messageDiv || !body) return;
    const bubble = messageDiv.querySelector?.(".bubble") || messageDiv;
    if (!bubble || bubble.querySelector(".copy-btn")) return;
    let actions = bubble.querySelector(".message-actions");
    if (!actions) {
      actions = document.createElement("div");
      actions.className = "message-actions";
      bubble.appendChild(actions);
    }
    actions.prepend(createCopyButton(body));
  }

  window.escapeHtml = escapeHtml;
  window.formatMessage = formatMessage;
  window.messagePlainText = messagePlainText;
  window.copyTextToClipboard = copyTextToClipboard;
  window.isTextEntryElement = isTextEntryElement;
  window.syncMessageRawText = syncMessageRawText;
  window.createCopyButton = createCopyButton;
  window.ensureMessageCopyAction = ensureMessageCopyAction;
})();
