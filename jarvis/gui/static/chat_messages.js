/** Chat message DOM helpers — addMessage / addTyping. Load after app.js (needs formatMessage, createCopyButton). */
(function () {
  function messagesEl() {
    return document.getElementById("messages");
  }

  function addMessage(role, content, meta = {}, options = {}) {
    const msgs = messagesEl();
    if (!msgs) return { div: null, body: null };

    const div = document.createElement("div");
    div.className = `message ${role}`;
    if (meta.type) div.dataset.msgType = meta.type;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "You" : "J";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    if (meta.type === "briefing") bubble.classList.add("briefing-bubble");

    const showTag = meta.module && meta.module !== "general" && meta.type !== "info";
    if (showTag && role === "assistant") {
      const tag = document.createElement("div");
      tag.className = `module-tag ${meta.module}`;
      tag.textContent = meta.module;
      bubble.appendChild(tag);
    }

    const body = document.createElement("div");
    body.className = "msg-body";
    const formatMessage = window.formatMessage || ((t) => t);
    body.innerHTML = formatMessage(content);
    if (content) body.dataset.rawText = content;
    bubble.appendChild(body);

    const mountExtras = () => window.attachProposalExtras?.(bubble, meta, div);
    if (meta.proposal_id && window.isNativeApp?.()) {
      requestAnimationFrame(() => requestAnimationFrame(mountExtras));
    } else {
      mountExtras();
    }

    if (meta.type === "clarification" && meta.choices) {
      const chips = document.createElement("div");
      chips.className = "clarification-chips";
      meta.choices.forEach((choice, i) => {
        const chip = document.createElement("button");
        chip.className = "suggestion-chip";
        chip.textContent = choice;
        chip.onclick = () => window.sendMessage?.(String(i + 1));
        chips.appendChild(chip);
      });
      bubble.appendChild(chips);
    }

    div.append(avatar, bubble);

    const msgIndex = msgs.querySelectorAll(".message").length;
    div.dataset.msgIndex = String(msgIndex);
    if (role === "user" || role === "assistant") {
      const actions = document.createElement("div");
      actions.className = "message-actions";
      const copyBtn = window.createCopyButton?.(body);
      if (copyBtn) actions.appendChild(copyBtn);
      const forkBtn = document.createElement("button");
      forkBtn.type = "button";
      forkBtn.className = "ghost-btn small fork-btn";
      forkBtn.title = "Fork branch from this message";
      forkBtn.textContent = "⎇ Fork";
      forkBtn.onclick = () => window.forkBranchFromIndex?.(msgIndex);
      actions.appendChild(forkBtn);
      bubble.appendChild(actions);
    }

    msgs.appendChild(div);
    if (!options.skipScroll) msgs.scrollTop = msgs.scrollHeight;

    if (role === "assistant" && window.jarvisChat) {
      window.jarvisChat.lastAssistantText = content;
    }
    return { div, body };
  }

  function addTyping() {
    const msgs = messagesEl();
    if (!msgs) return null;
    const div = document.createElement("div");
    div.className = "message assistant typing-msg";
    div.innerHTML = `<div class="avatar">J</div><div class="bubble"><div class="msg-body"><div class="typing"><span></span><span></span><span></span></div></div></div>`;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  Object.assign(window, { addMessage, addTyping });
})();
