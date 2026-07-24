/** Chat scroll + assistant meta tags — extracted from app.js. */
(function () {
  function applyAssistantMeta(messageEl, meta) {
    const bubble = messageEl?.querySelector?.(".bubble") || messageEl?.closest?.(".message")?.querySelector?.(".bubble");
    if (!bubble) return;
    const showTag = meta.module && meta.module !== "general" && meta.type !== "info";
    let tag = bubble.querySelector(".module-tag");
    if (showTag) {
      if (!tag) {
        tag = document.createElement("div");
        bubble.appendChild(tag);
      }
      tag.className = `module-tag ${meta.module}`;
      tag.textContent = meta.module;
    } else if (tag) {
      tag.remove();
    }
  }

  function scrollMessageIntoView(node, block = "start") {
    const messagesEl = document.getElementById("messages");
    const msg = node?.closest?.(".message") || node;
    if (!msg || !messagesEl) return;
    const msgTop = msg.offsetTop;
    const msgBottom = msgTop + msg.offsetHeight;
    const viewTop = messagesEl.scrollTop;
    const viewBottom = viewTop + messagesEl.clientHeight;
    if (block === "start") {
      if (msgTop < viewTop) messagesEl.scrollTop = msgTop;
      else if (msgBottom > viewBottom) messagesEl.scrollTop = msgBottom - messagesEl.clientHeight;
    } else {
      messagesEl.scrollTop = Math.max(0, msgBottom - messagesEl.clientHeight);
    }
  }

  window.applyAssistantMeta = applyAssistantMeta;
  window.scrollMessageIntoView = scrollMessageIntoView;
})();
