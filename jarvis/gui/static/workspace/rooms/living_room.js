/**
 * Aria Living Room — Chat Room (Phase 3).
 * Inhabits Workspace. Conversation is the place.
 * Bridges to existing #messages / #messageInput / send pipeline — never redesigns Workspace.
 */
(function () {
  "use strict";

  let _active = false;
  let _observer = null;
  let _statusTimer = null;

  const WELCOME_HTML =
    '<p>Come in. Sit down.<br><strong>I\'m here</strong> whenever you are.</p>';

  function ensureDom() {
    const chat = document.getElementById("chatView");
    if (!chat) return null;

    if (!document.getElementById("livingRoomAtmosphere")) {
      const atm = document.createElement("div");
      atm.id = "livingRoomAtmosphere";
      atm.className = "lr-atmosphere";
      atm.setAttribute("aria-hidden", "true");
      atm.innerHTML =
        '<div class="lr-atmosphere__wash"></div>' +
        '<div class="lr-atmosphere__veil"></div>' +
        '<div class="lr-atmosphere__grain"></div>';
      chat.insertBefore(atm, chat.firstChild);
    }

    if (!document.getElementById("livingRoomTop")) {
      const top = document.createElement("div");
      top.id = "livingRoomTop";
      top.className = "lr-top";
      top.innerHTML = [
        '<div class="lr-presence house-presence">',
        '  <div class="lr-brand house-presence__brand" id="livingRoomBrand">Aria <span class="house-presence__place">· Living room</span></div>',
        '  <div class="lr-status house-presence__status" id="livingRoomStatus">Listening quietly</div>',
        "</div>",
        '<button type="button" class="lr-overflow-btn" id="livingRoomOverflowBtn" aria-label="More" aria-expanded="false" title="More">',
        '  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/></svg>',
        "</button>",
        '<div class="lr-overflow" id="livingRoomOverflow" role="menu" aria-hidden="true">',
        "  <h3>Nearby</h3>",
        '  <button type="button" data-lr-action="new-chat">New conversation <span class="meta">fresh</span></button>',
        '  <button type="button" data-lr-action="attach">Place something here <span class="meta">attach</span></button>',
        '  <div class="divider"></div>',
        '  <div class="lr-overflow-row"><span>Model</span><select id="lrModelSelect" aria-label="Model"></select></div>',
        '  <button type="button" data-lr-action="speak-toggle">Read aloud <span class="meta" id="lrSpeakMeta">off</span></button>',
        '  <button type="button" data-lr-action="voice-tool">Voice <span class="meta">when speaking</span></button>',
        '  <div class="divider"></div>',
        '  <button type="button" data-lr-action="spotlight">Open the front door <span class="meta">Ctrl+K</span></button>',
        '  <button type="button" data-lr-action="fork">Fork thread <span class="meta">branch</span></button>',
        "</div>",
      ].join("");
      const header = chat.querySelector(".chat-header");
      if (header) header.insertAdjacentElement("afterend", top);
      else chat.insertBefore(top, chat.querySelector("#messages") || null);
    }

    return chat;
  }

  function syncModelSelect() {
    const src = document.getElementById("chatComposerModelSelect");
    const dst = document.getElementById("lrModelSelect");
    if (!src || !dst) return;
    dst.innerHTML = src.innerHTML;
    dst.value = src.value;
    if (!dst.dataset.bound) {
      dst.dataset.bound = "1";
      dst.addEventListener("change", () => {
        src.value = dst.value;
        src.dispatchEvent(new Event("change", { bubbles: true }));
      });
    }
  }

  function setOverflow(open) {
    const panel = document.getElementById("livingRoomOverflow");
    const btn = document.getElementById("livingRoomOverflowBtn");
    if (!panel || !btn) return;
    panel.classList.toggle("is-open", open);
    panel.setAttribute("aria-hidden", open ? "false" : "true");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function wireOverflow() {
    const btn = document.getElementById("livingRoomOverflowBtn");
    const panel = document.getElementById("livingRoomOverflow");
    if (!btn || !panel || btn.dataset.bound) return;
    btn.dataset.bound = "1";

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      setOverflow(!panel.classList.contains("is-open"));
      if (panel.classList.contains("is-open")) syncModelSelect();
    });

    document.addEventListener("click", (e) => {
      if (!_active) return;
      if (panel.contains(e.target) || btn.contains(e.target)) return;
      setOverflow(false);
    });

    panel.addEventListener("click", (e) => {
      const action = e.target.closest("[data-lr-action]")?.dataset?.lrAction;
      if (!action) return;
      e.preventDefault();
      if (action === "new-chat") document.getElementById("chatNewBtn")?.click();
      else if (action === "attach") document.getElementById("fileInput")?.click();
      else if (action === "speak-toggle") {
        const t = document.getElementById("speakRepliesToggle");
        if (t) {
          t.checked = !t.checked;
          t.dispatchEvent(new Event("change", { bubbles: true }));
          const meta = document.getElementById("lrSpeakMeta");
          if (meta) meta.textContent = t.checked ? "on" : "off";
        }
      } else if (action === "voice-tool") {
        window.AriaWorkspaceTools?.open?.("voice");
        setStatus("Voice nearby");
        scheduleQuietStatus();
      } else if (action === "spotlight") {
        window.AriaFrontDoor?.open?.() || document.getElementById("wsSpotlightBtn")?.click();
      } else if (action === "fork") {
        document.getElementById("newBranchBtn")?.click();
      }
      if (action !== "speak-toggle") setOverflow(false);
    });
  }

  function wireHearthMic() {
    const composerMic = document.getElementById("micBtnComposer");
    const mic = document.getElementById("micBtn");
    const row = document.querySelector("#chatForm .input-row");
    if (!composerMic || !row) return;

    // Seat the mic in the hearth next to send
    if (composerMic.parentElement !== row) {
      const send = document.getElementById("sendBtn");
      if (send) row.insertBefore(composerMic, send);
      else row.appendChild(composerMic);
    }
    composerMic.removeAttribute("hidden");
    if (!composerMic.querySelector("svg")) {
      composerMic.innerHTML =
        '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>';
    }

    if (!mic || composerMic.dataset.lrBound) return;
    composerMic.dataset.lrBound = "1";
    const forward = (type, ev) => {
      try {
        mic.dispatchEvent(
          new PointerEvent(type, {
            bubbles: true,
            cancelable: true,
            pointerId: ev.pointerId || 1,
            pointerType: ev.pointerType || "mouse",
            isPrimary: true,
            button: ev.button,
            buttons: ev.buttons,
            clientX: ev.clientX,
            clientY: ev.clientY,
          })
        );
      } catch (_) {
        mic.dispatchEvent(new Event(type, { bubbles: true }));
      }
    };
    ["pointerdown", "pointerup", "pointercancel"].forEach((type) => {
      composerMic.addEventListener(type, (ev) => forward(type, ev));
    });
    composerMic.addEventListener("click", (ev) => {
      ev.preventDefault();
      mic.click();
    });
  }

  function softenWelcome() {
    // Presence owns the first turn — do not overwrite
    if (document.querySelector("#messages [data-lr-presence='1']")) return;
    const welcome = document.querySelector("#messages .message.welcome .bubble");
    if (welcome) {
      const body = welcome.querySelector(".msg-body") || welcome;
      if (!body.dataset.lrWelcome) {
        body.dataset.lrWelcome = "1";
        body.innerHTML = WELCOME_HTML;
      }
    }
    // Branch bootstrap / empty-thread greeting
    document.querySelectorAll("#messages .message.assistant").forEach((msg, idx) => {
      if (idx > 0) return;
      const body = msg.querySelector(".msg-body") || msg.querySelector(".bubble");
      if (!body || body.dataset.lrWelcome || body.dataset.lrPresence) return;
      const text = (body.textContent || "").toLowerCase();
      if (
        text.includes("how can i help") ||
        text.includes("what can you do") ||
        text.includes("hello! i'm") ||
        text.includes("come in. sit down")
      ) {
        body.dataset.lrWelcome = "1";
        body.innerHTML = WELCOME_HTML;
        msg.classList.add("welcome");
      }
    });
    document.querySelectorAll("#messages .message.assistant .avatar, #messages .message.welcome .avatar").forEach((av) => {
      if (av && (av.textContent === "J" || av.textContent === "A" || !av.textContent.trim())) av.textContent = "A";
    });
  }

  function softSuggestions() {
    const box = document.getElementById("suggestions");
    if (!box) return;
    // Presence already spoke — do not re-invite with chips
    if (document.querySelector("#messages [data-lr-presence='1']")) {
      box.classList.remove("lr-suggestions-soft");
      box.replaceChildren();
      return;
    }
    const keep = [...box.querySelectorAll(".data-chip, .vision-chip")];
    const msgs = document.querySelectorAll("#messages .message.user").length;
    if (msgs > 0) {
      box.classList.remove("lr-suggestions-soft");
      box.replaceChildren();
      keep.forEach((n) => box.appendChild(n));
      return;
    }
    box.classList.add("lr-suggestions-soft");
    box.replaceChildren();
    keep.forEach((n) => box.appendChild(n));
    [
      "Good morning",
      "What should we work on?",
      "Just listen for a bit",
    ].forEach((label) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip";
      chip.dataset.lrSoft = "1";
      chip.textContent = label;
      box.appendChild(chip);
    });
    if (!box.dataset.lrSoftBound) {
      box.dataset.lrSoftBound = "1";
      box.addEventListener("click", (e) => {
        const chip = e.target.closest("[data-lr-soft]");
        if (!chip || !window.AriaLivingRoom?.isActive?.()) return;
        const t = chip.textContent.trim();
        const input = document.getElementById("messageInput");
        if (input) {
          input.value = t === "Just listen for a bit" ? "" : t;
          input.focus();
        }
        if (t !== "Just listen for a bit") {
          document.getElementById("chatForm")?.requestSubmit?.();
        }
      });
    }
  }

  function stripSoftwareChrome() {
    document.querySelectorAll("#messages .message-actions, #messages .chat-reply-actions, #messages .msg-timestamp").forEach((el) => {
      el.remove();
    });
    const side = document.querySelector(".sidebar");
    if (side) {
      side.setAttribute("aria-hidden", "true");
      side.setAttribute("inert", "");
    }
    document.getElementById("ariaStatusBar")?.setAttribute("aria-hidden", "true");
    document.getElementById("wsBar")?.setAttribute("aria-hidden", "true");
  }

  function restoreSoftwareChrome() {
    const side = document.querySelector(".sidebar");
    if (side) {
      side.removeAttribute("aria-hidden");
      side.removeAttribute("inert");
    }
    document.getElementById("ariaStatusBar")?.removeAttribute("aria-hidden");
    document.getElementById("wsBar")?.removeAttribute("aria-hidden");
  }

  function muteToasts() {
    if (window.__lrToastWrapped) return;
    window.__lrToastWrapped = true;
    const orig = window.showAriaToast;
    window.__lrShowAriaToast = typeof orig === "function" ? orig.bind(window) : null;
    window.showAriaToast = function (msg, kind, ms) {
      const text = String(msg || "");
      if (/signal is aborted|request cancelled|the operation was aborted|aborterror/i.test(text)) {
        return;
      }
      if (window.AriaLivingRoom?.isActive?.()) {
        // Presence whispers for anything Jeff must know — never toast walls
        if (kind === "err" || kind === "error" || kind === "warn") {
          setStatus(text.slice(0, 80) || "Something went quiet");
          scheduleQuietStatus();
        }
        return;
      }
      return window.__lrShowAriaToast?.(msg, kind, ms);
    };
  }

  function fadeInvites() {
    clearTimeout(fadeInvites._t);
    fadeInvites._t = setTimeout(() => {
      if (!_active) return;
      const box = document.getElementById("suggestions");
      if (!box?.classList.contains("lr-suggestions-soft")) return;
      box.style.transition = "opacity 1.2s ease";
      box.style.opacity = "0";
      setTimeout(() => {
        if (!_active) return;
        if (document.querySelectorAll("#messages .message.user").length === 0) {
          box.style.opacity = "0.35";
        } else {
          softSuggestions();
        }
      }, 1200);
    }, 14000);
  }

  function dismissSoftwareInterruptions() {
    document.getElementById("whatsNewModal")?.classList.add("hidden");
    document.getElementById("ariaSoftTip")?.classList.add("hidden");
    document.getElementById("startupOverlay")?.classList.add("hidden");
  }

  function enhanceAvatars(root) {
    (root || document).querySelectorAll?.("#messages .message")?.forEach?.((msg) => {
      const av = msg.querySelector(".avatar");
      if (!av) return;
      if (msg.classList.contains("user")) {
        if (av.textContent === "You" || av.textContent === "J" || av.textContent.length <= 3) {
          av.textContent = "You";
        }
      } else if (av.textContent === "J" || av.textContent === "A" || !av.textContent.trim()) {
        av.textContent = "A";
      }
    });
  }

  function observeMessages() {
    const msgs = document.getElementById("messages");
    if (!msgs || _observer) return;
    _observer = new MutationObserver((muts) => {
      if (!_active) return;
      for (const m of muts) {
        m.addedNodes.forEach((n) => {
          if (n.nodeType === 1) enhanceAvatars(n.parentElement || msgs);
        });
      }
      stripSoftwareChrome();
      softenWelcome();
      softSuggestions();
    });
    _observer.observe(msgs, { childList: true });
  }

  function setStatus(text) {
    const el = document.getElementById("livingRoomStatus");
    if (el) el.textContent = text;
  }

  function scheduleQuietStatus() {
    clearTimeout(_statusTimer);
    _statusTimer = setTimeout(() => {
      if (_active) setStatus("Listening quietly");
    }, 4200);
  }

  function wirePresenceFromChat() {
    if (document.body.dataset.lrPresenceBound) return;
    document.body.dataset.lrPresenceBound = "1";
    window.addEventListener("aria-chat-thinking", () => {
      if (!_active) return;
      setStatus("Thinking with you");
      scheduleQuietStatus();
    });
    window.addEventListener("aria-chat-streaming", () => {
      if (!_active) return;
      setStatus("Speaking");
    });
    window.addEventListener("aria-chat-idle", () => {
      if (!_active) return;
      setStatus("Listening quietly");
    });
    // Heuristic: progress bar visibility
    const progress = document.getElementById("progressBar");
    if (progress) {
      const mo = new MutationObserver(() => {
        if (!_active) return;
        if (!progress.classList.contains("hidden")) setStatus("Thinking with you");
        else scheduleQuietStatus();
      });
      mo.observe(progress, { attributes: true, attributeFilter: ["class"] });
    }
  }

  function setPlaceholder() {
    const input = document.getElementById("messageInput");
    if (!input) return;
    if (!input.dataset.lrPlaceholder) {
      input.dataset.lrPlaceholder = input.placeholder || "";
    }
    input.placeholder = "Say anything…";
  }

  function restorePlaceholder() {
    const input = document.getElementById("messageInput");
    if (!input || input.dataset.lrPlaceholder == null) return;
    input.placeholder = input.dataset.lrPlaceholder;
  }

  function stageHasLivingRoom(chat) {
    const stage = document.getElementById("ariaStage");
    return !!(
      chat &&
      stage &&
      chat.parentElement === stage &&
      window.AriaStage?.mountedId?.() === "chatView"
    );
  }

  function enter() {
    /* Heal blank stage: _active can stay true after an external AriaStage.clear(). */
    if (_active) {
      const existing = document.getElementById("chatView");
      if (stageHasLivingRoom(existing)) return;
      _active = false;
    }
    /* Phase 6.5: never displace a furnished Room (Mission, Fly, Health, …) */
    if (
      document.body?.dataset?.furnished === "1" &&
      document.body.dataset.room &&
      document.body.dataset.room !== "chat"
    ) {
      return;
    }
    if (
      document.body?.classList.contains("furnished-room") &&
      document.body.dataset.room &&
      document.body.dataset.room !== "chat"
    ) {
      return;
    }
    const chat = ensureDom();
    if (!chat) return;
    try {
      window.AriaJournalCancelPending?.();
    } catch (_) {
      /* ignore */
    }
    /* House Integrity: Room owns the stage — never sit on top of legacy shell */
    window.AriaStage?.mount?.(chat, "chat");
    wireOverflow();
    wireHearthMic();
    wirePresenceFromChat();
    observeMessages();
    document.body.classList.add("living-room");
    document.body.dataset.room = "chat";
    const chatMeta = window.AriaWorkspaceRegistry?.room?.("chat");
    document.body.dataset.place = chatMeta?.place || chatMeta?.metaphor || "Living room";
    _active = true;
    muteToasts();
    dismissSoftwareInterruptions();
    stripSoftwareChrome();
    softenWelcome();
    enhanceAvatars(document.getElementById("messages"));
    setPlaceholder();
    setStatus("Listening quietly");
    syncModelSelect();
    window.AriaWorkspaceChrome?.apply?.("minimal");
    const tray = document.getElementById("wsToolTray");
    if (tray) {
      tray.innerHTML = "";
      tray.classList.add("hidden");
    }
    window.dispatchEvent(new CustomEvent("aria-living-room", { detail: { active: true } }));
    setTimeout(() => {
      if (!_active) return;
      dismissSoftwareInterruptions();
      stripSoftwareChrome();
      softenWelcome();
      if (!document.querySelector("#messages [data-lr-presence='1']")) softSuggestions();
      fadeInvites();
    }, 2200);
  }

  function exit(opts) {
    if (!_active) return;
    _active = false;
    document.body.classList.remove("living-room");
    if (document.body.dataset.room === "chat") delete document.body.dataset.room;
    setOverflow(false);
    restorePlaceholder();
    restoreSoftwareChrome();
    clearTimeout(_statusTimer);
    clearTimeout(fadeInvites._t);
    const box = document.getElementById("suggestions");
    if (box) box.style.opacity = "";
    /* keepStage: true when another Room is about to mount (house_host) */
    if (!opts?.keepStage) {
      const chat = document.getElementById("chatView");
      if (chat?.getAttribute("data-aria-stage-mounted") && window.AriaStage?.mountedId?.() === "chatView") {
        window.AriaStage.clear();
      }
    }
    window.dispatchEvent(new CustomEvent("aria-living-room", { detail: { active: false } }));
  }

  function shouldBeInLivingRoom() {
    if (!document.body?.classList.contains("living-workspace")) return false;
    /* Phase 6.5: a furnished non-chat Room owns the stage — do not steal it back to Chat */
    const furnishedRoom = document.body.dataset.furnished === "1" ? document.body.dataset.room : "";
    if (furnishedRoom && furnishedRoom !== "chat") return false;
    if (
      document.body.classList.contains("furnished-room") &&
      document.body.dataset.room &&
      document.body.dataset.room !== "chat"
    ) {
      return false;
    }
    const cur = window.AriaActivityEngine?.current?.();
    if (cur?.id === "converse" || cur?.primaryRoom === "chat") return true;
    if (document.body.dataset.activity === "converse") return true;
    const hash = (location.hash || "").replace(/^#/, "").split(/[&?]/)[0];
    if ((!hash || hash === "chat") && document.body.dataset.workspace === "1") {
      // Default Stage destination is conversation
      if (!document.body.dataset.activity || document.body.dataset.activity === "converse") return true;
    }
    return false;
  }

  function syncFromActivity(detail) {
    const act = detail?.activity;
    if (!act) {
      // Activity stopped — leave room only if we left conversation entirely
      if (document.body.dataset.activity && document.body.dataset.activity !== "converse") exit();
      return;
    }
    const id = act.id || act;
    const room = act.primaryRoom;
    if (id === "converse" || room === "chat") {
      if (
        document.body?.dataset?.furnished === "1" &&
        document.body.dataset.room &&
        document.body.dataset.room !== "chat"
      ) {
        return;
      }
      enter();
    } else exit();
  }

  function boot() {
    ensureDom();
    window.addEventListener("aria-activity-change", (e) => syncFromActivity(e.detail || {}));
    window.addEventListener("aria-workspace-ready", () => {
      if (shouldBeInLivingRoom()) enter();
    });
    const tryEnter = () => {
      if (shouldBeInLivingRoom()) enter();
    };
    tryEnter();
    // Workspace may boot in the same tick after us — catch late start
    requestAnimationFrame(() => {
      tryEnter();
      setTimeout(tryEnter, 0);
      setTimeout(tryEnter, 50);
      setTimeout(tryEnter, 250);
    });
  }

  window.AriaLivingRoom = {
    enter,
    exit,
    isActive: () => _active,
    setStatus,
    refreshSuggestions: softSuggestions,
    version: "3.8.0-integrity",
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
