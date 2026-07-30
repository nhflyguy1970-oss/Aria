/** Chat send / stream pipeline — extracted from app.js. Load after app.js + chat_progress.js. */
(function () {
  // Idle between stream chunks after first token/progress (media/coding may be slower).
  let STREAM_IDLE_MS = Number(window.JARVIS_CHAT_STREAM_IDLE_MS) || 90000;
  // Absolute wait for first meaningful progress (token / agent_step / done) — never hang on "Processing…".
  let FIRST_PROGRESS_MS = Number(window.JARVIS_CHAT_FIRST_PROGRESS_MS) || 45000;
  // Non-streaming POST overall timeout.
  const NONSTREAM_MS = Number(window.JARVIS_CHAT_NONSTREAM_MS) || 120000;

  fetch("/api/provider/prefs")
    .then((r) => (r.ok ? r.json() : null))
    .then((p) => {
      if (!p || !p.ok) return;
      if (Number(p.idle_timeout_ms) > 0) STREAM_IDLE_MS = Number(p.idle_timeout_ms);
      if (Number(p.first_progress_ms) > 0) FIRST_PROGRESS_MS = Number(p.first_progress_ms);
    })
    .catch(() => {});

  function chat() {
    return window.jarvisChat || {};
  }

  function attach() {
    return window.jarvisAttach || {};
  }

  function messagesEl() {
    return document.getElementById("messages");
  }

  function statusEl() {
    return document.getElementById("statusText");
  }

  function readStreamChunk(reader, idleMs = STREAM_IDLE_MS, code = "STREAM_IDLE_TIMEOUT") {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(providerTimeoutError(code === "FIRST_PROGRESS_TIMEOUT" ? "first" : "idle"));
      }, idleMs);
      reader.read().then(
        (result) => { clearTimeout(timer); resolve(result); },
        (err) => { clearTimeout(timer); reject(err); },
      );
    });
  }

  async function parseJsonResponse(res) {
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch {
      throw new Error(res.ok ? "Invalid server response" : `Server error (${res.status}): ${text.slice(0, 200)}`);
    }
  }

  function isStreamableAttachment(file) {
    if (!file) return false;
    if (file.size > 500000) return false;
    return /\.(txt|md|py|json|csv|log|yaml|yml|toml|xml|html|js|ts|tsx|jsx|sh|rs|go)$/i.test(file.name);
  }

  function providerTimeoutError(kind) {
    const name = typeof window.ariaName === "function" ? window.ariaName() : "ARIA";
    const err = new Error(
      kind === "first"
        ? `${name} did not receive a model response in time. `
          + "Ollama may be offline, loading a large model, or stuck accepting requests without generating."
        : `${name} stopped receiving tokens from the model provider.`,
    );
    err.code = kind === "first" ? "FIRST_PROGRESS_TIMEOUT" : "STREAM_IDLE_TIMEOUT";
    return err;
  }

  async function sendMessage(text, forceNoStream = false, options = {}) {
    const a = attach();
    const c = chat();
    let pendingFile = a.pendingFile;
    let pendingFile2 = a.pendingFile2;
    const compareMode = a.compareMode;
    const pendingCrop = a.pendingCrop;
    const pendingVideoSecond = a.pendingVideoSecond || "";
    const pendingPdfPage = a.pendingPdfPage || "1";

    if (!text.trim() && !pendingFile && !pendingFile2) return;

    if (compareMode && pendingFile && !pendingFile2) {
      window.showError?.("Compare needs **two images**. Click **+ Add image 2** in the preview, or click **Compare** and select both files at once.");
      return;
    }
    if (pendingFile2 && !pendingFile) {
      pendingFile = pendingFile2;
      pendingFile2 = null;
      a.pendingFile = pendingFile;
      a.pendingFile2 = null;
    }

    const skipUserBubble = Boolean(options.skipUserBubble);

    let displayText = text.trim();
    if (pendingFile) {
      displayText = displayText
        ? `${displayText}\n📎 ${pendingFile.name}`
        : `📎 ${pendingFile.name}`;
    }
    if (pendingFile2) {
      displayText = displayText
        ? `${displayText}\n📎 ${pendingFile2.name}`
        : `📎 ${pendingFile2.name}`;
    }
    if (!skipUserBubble) {
      window.addMessage?.("user", displayText || "(attachment)");
    }

    c.chatStopRequested = false;
    c.providerTimeout = null;
    c.activeStreamText = "";
    c.activeChatRequestId = crypto.randomUUID?.() || `req-${Date.now()}`;
    c.chatAbortController = new AbortController();
    window.setChatBusy?.(true);
    window.showProgress?.(window.progressLabel?.(text) || "Thinking…");

    if (window.isVideoRequest?.(text)) {
      const proceed = (await window.vramPreflight?.("generate_video")) !== false;
      if (!proceed) {
        window.setChatBusy?.(false);
        window.hideProgress?.();
        return;
      }
    } else if (window.isImageRequest?.(text)) {
      const proceed = (await window.vramPreflight?.("generate_image")) !== false;
      if (!proceed) {
        window.setChatBusy?.(false);
        window.hideProgress?.();
        return;
      }
    }

    // Re-read attach state after possible pendingFile swap
    pendingFile = a.pendingFile;
    pendingFile2 = a.pendingFile2;

    const form = new FormData();
    form.append("request_id", c.activeChatRequestId);
    const defaultMsg = pendingFile2
      ? "Compare these two images. Describe similarities and differences."
      : (typeof a.isDataAttachment === "function" ? a.isDataAttachment(pendingFile) : window.isDataAttachment?.(pendingFile))
        ? "Load and summarize this data."
        : "Please analyze the attached file.";
    form.append("message", text.trim() || defaultMsg);
    if (pendingFile) form.append("file", pendingFile);
    if (pendingFile2) form.append("file2", pendingFile2);
    if (pendingCrop) form.append("crop", JSON.stringify(pendingCrop));
    if (String(pendingVideoSecond).trim()) form.append("video_second", String(pendingVideoSecond).trim());
    if (String(pendingPdfPage).trim()) form.append("pdf_page", String(pendingPdfPage).trim());
    if (window.activeBranchId) form.append("branch_id", window.activeBranchId);
    if (window.jarvisPreferredModule) form.append("preferred_module", window.jarvisPreferredModule);

    const trimmed = text.trim();
    const isInstant = /^(hi|hello|hey|what can you|what (services|models|do you)|help|capabilities)/i.test(trimmed)
      || /^(undo|apply)(\s+(it|that|last|the changes?|apply))?\s*$/i.test(trimmed);
    const isCodingFix = /\b(?:fix|repair|debug|improve|refactor|clean up)\b/i.test(text) && /[^\s`'"]+\.py/.test(text);
    const isCodingCreate = /\b(with tests?|pytest)\b/i.test(text)
      && /\b(implement|create|write|make|build|add)\b/i.test(text);
    const isCodingAgent = /\b(implement|build|add feature|debug until|refactor across)\b/i.test(text)
      || isCodingFix || isCodingCreate;
    const isWebSearch = /\b(search (the )?web|web search|look up online|google)\b/i.test(trimmed);
    const isVision = typeof a.isVisionAttachment === "function"
      ? a.isVisionAttachment
      : window.isVisionAttachment;
    const hasVisionAttach = Boolean(isVision?.(pendingFile) || isVision?.(pendingFile2));
    const streamableFile = isStreamableAttachment(pendingFile);
    const wantsStream = window.isImageRequest?.(text) || window.isVideoRequest?.(text) || isCodingAgent || hasVisionAttach || (
      !forceNoStream && (!pendingFile || streamableFile) && !isInstant && text.length > 0
      && !/^(run|apply|undo|review|find|load|transcribe|generate)/i.test(trimmed)
      && (!/^search/i.test(trimmed) || isWebSearch)
    );

    const typing = window.addTyping?.();
    if (!typing) {
      window.setChatBusy?.(false);
      window.hideProgress?.();
      window.showAriaToast?.("Could not start reply UI — try again", "err", 4000);
      return;
    }
    const fetchOpts = { method: "POST", body: form, signal: c.chatAbortController.signal };
    const useStreaming = c.useStreaming !== false;
    const msgs = messagesEl();
    const statusText = statusEl();
    const escapeHtml = window.escapeHtml || ((t) => t);
    const formatMessage = window.formatMessage || ((t) => t);
    const syncMessageRawText = window.syncMessageRawText;
    const isNativeApp = () => window.isNativeApp?.() === true;
    const ariaName = () => (typeof window.ariaName === "function" ? window.ariaName() : "ARIA");

    try {
      if (useStreaming && wantsStream) {
        form.append("stream", "true");
        if (isNativeApp()) form.append("lite_ui", "true");
        const body = typing.querySelector(".msg-body");
        body.innerHTML = window.isVideoRequest?.(text)
          ? `<p class="status-hint">Starting video generation…</p>`
          : window.isImageRequest?.(text)
            ? `<p class="status-hint">Starting image generation…</p>`
            : "";
        let full = "";
        let gotDone = false;
        let gotProgress = false;
        const streamStartedAt = Date.now();
        // Heartbeats during model load reset this anchor so client FIRST_PROGRESS
        // does not fire while the server is still ensuring the chat model is ready.
        let firstProgressAnchorAt = streamStartedAt;

        const res = await fetch("/api/chat", fetchOpts);
        if (!res.ok) {
          const err = await parseJsonResponse(res);
          throw new Error(err.message || `Request failed (${res.status})`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let streamFinished = false;

        try {
          while (!streamFinished) {
            if (c.chatStopRequested) {
              streamFinished = true;
              break;
            }
            if (!gotProgress && Date.now() - firstProgressAnchorAt > FIRST_PROGRESS_MS) {
              const terr = providerTimeoutError("first");
              c.providerTimeout = terr;
              try { c.chatAbortController?.abort?.(); } catch (_) {}
              throw terr;
            }
            const idleForChunk = gotProgress ? STREAM_IDLE_MS : Math.max(5000, FIRST_PROGRESS_MS - (Date.now() - firstProgressAnchorAt));
            const idleCode = gotProgress ? "STREAM_IDLE_TIMEOUT" : "FIRST_PROGRESS_TIMEOUT";
            const { done, value } = await readStreamChunk(reader, idleForChunk, idleCode);
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();
            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              let event;
              try { event = JSON.parse(line.slice(6)); } catch { continue; }
              if (event.type === "status") {
                window.updateProgressStatus?.(event.message || "Processing…");
                if (body) {
                  body.innerHTML = `<p class="status-hint">${escapeHtml(event.message || "Processing…")}</p>`;
                  if (msgs) msgs.scrollTop = msgs.scrollHeight;
                }
                // Status alone does not count as model progress — avoids infinite "Processing…".
              } else if (event.type === "heartbeat") {
                // Server keepalive while provider is blocked (e.g. loading chat model).
                // Extends first-progress wait without counting as a token.
                firstProgressAnchorAt = Date.now();
                window.updateProgressStatus?.(event.message || "Waiting for provider…");
              } else if (event.type === "error" && (event.code === "FIRST_PROGRESS_TIMEOUT" || event.code === "STREAM_IDLE_TIMEOUT")) {
                const terr = providerTimeoutError(event.code === "STREAM_IDLE_TIMEOUT" ? "idle" : "first");
                if (event.message) terr.message = event.message;
                c.providerTimeout = terr;
                try { c.chatAbortController?.abort?.(); } catch (_) {}
                throw terr;
              } else if (event.type === "agent_step") {
                gotProgress = true;
                const label = `${event.action || "step"}: ${event.detail || ""}`;
                window.updateProgressStatus?.(label);
                if (body && !isNativeApp()) {
                  const steps = body.querySelector(".agent-steps") || document.createElement("div");
                  steps.className = "agent-steps";
                  if (!steps.parentElement) body.appendChild(steps);
                  const stepLine = document.createElement("div");
                  stepLine.className = "agent-step" + (event.ok === false ? " fail" : "");
                  stepLine.textContent = `${event.step || "•"}. ${label}`;
                  steps.appendChild(stepLine);
                  if (msgs) msgs.scrollTop = msgs.scrollHeight;
                }
              } else if (event.type === "token") {
                gotProgress = true;
                window.updateProgressStatus?.("Generating…");
                full += event.content;
                c.activeStreamText = full;
                body.innerHTML = formatMessage(full);
                syncMessageRawText?.(body, full);
                if (typeof options.onToken === "function") {
                  try { options.onToken(event.content, full); } catch (_) {}
                }
                if (msgs) msgs.scrollTop = msgs.scrollHeight;
              } else if (event.type === "done" || (event.ok && event.image_path)) {
                if (!event.ok && (event.code === "FIRST_PROGRESS_TIMEOUT" || event.code === "STREAM_IDLE_TIMEOUT")) {
                  const terr = providerTimeoutError(event.code === "STREAM_IDLE_TIMEOUT" ? "idle" : "first");
                  if (event.message) terr.message = event.message;
                  c.providerTimeout = terr;
                  throw terr;
                }
                gotProgress = true;
                gotDone = true;
                streamFinished = true;
                if (event.trace_id) c.lastLatencyTraceId = event.trace_id;
                if (event.latency) {
                  c.lastLatency = event.latency;
                  try {
                    const showDev = window.JARVIS_LATENCY_DEV === true
                      || localStorage.getItem("JARVIS_LATENCY_DEV") === "1";
                    if (showDev && Array.isArray(event.latency.overlay)) {
                      console.info("[Aria latency]\n" + event.latency.overlay.join("\n"));
                      window.showAriaToast?.(
                        `Latency ${event.latency.elapsed_ms ?? "?"}ms · FT ${event.latency.first_token_ms ?? "—"}ms`,
                        "info",
                        3500,
                      );
                    }
                  } catch (_) {}
                }
                typing.classList.remove("typing-msg");
                if (!event.ok && !full && !event.image_path) {
                  typing.remove();
                  window.showError?.(event.message || "Request failed.");
                  break;
                }
                const streamed = Boolean(full);
                const isPendingMediaJob = Boolean(
                  event.job_id
                  && (event.type === "media_job" || event.result_type === "media_job" || event.pending),
                );
                if (!streamed && !isPendingMediaJob) typing.remove();
                if (isPendingMediaJob) typing.classList.remove("typing-msg");
                c.lastAssistantText = full || event.message;
                const doneOpts = isPendingMediaJob
                  ? { targetBody: typing.querySelector(".msg-body"), pendingMediaJob: true }
                  : {};
                try {
                  window.handleDone?.(event, full || event.message, streamed, doneOpts);
                  if (typeof options.onDone === "function") {
                    try { options.onDone(event, full || event.message); } catch (_) {}
                  }
                } catch (err) {
                  console.error("handleDone failed", err);
                  window.showError?.(`Could not display response: ${err.message || err}`);
                }
                window.finishSendUi?.();
                break;
              }
            }
          }
        } finally {
          try { await reader.cancel(); } catch (_) {}
        }

        if (c.chatStopRequested) {
          typing.remove();
          if ((c.activeStreamText || "").trim()) {
            window.addMessage?.("assistant", `${c.activeStreamText.trim()}\n\n*(stopped)*`, { type: "info" });
          }
          if (statusText) statusText.textContent = "Stopped";
        } else if (!gotDone) {
          typing.remove();
          if (window.isVideoRequest?.(text)) {
            window.showError?.("Video generation did not finish — check the Video tab or try again.");
          } else if (window.isImageRequest?.(text)) {
            window.showError?.("Image generation did not finish — check the Gallery tab or try again.");
          } else if (isCodingAgent) {
            window.showError?.(
              `**${ariaName()} lost the coding stream** (the server may have restarted mid-task).\n\n`
              + "Wait a few seconds, then send the same request once — don't auto-retry in a loop."
            );
          } else {
            window.showAriaToast?.("Stream dropped — retrying without streaming…", "warn", 3500);
            if (statusText) statusText.textContent = "Retrying…";
            await sendMessage(text, true, { skipUserBubble: true });
          }
        }
      } else {
        const nonStreamAbort = new AbortController();
        const nonStreamTimer = setTimeout(() => nonStreamAbort.abort(), NONSTREAM_MS);
        const linked = () => { try { nonStreamAbort.abort(); } catch (_) {} };
        c.chatAbortController?.signal?.addEventListener?.("abort", linked, { once: true });
        let res;
        try {
          res = await fetch("/api/chat", { ...fetchOpts, signal: nonStreamAbort.signal });
        } finally {
          clearTimeout(nonStreamTimer);
        }
        const data = await parseJsonResponse(res);
        typing.remove();
        if (!res.ok || data.ok === false) {
          window.showError?.(data.message || "Something went wrong.");
          return;
        }
        window.handleDone?.(data, data.message);
      }
    } catch (e) {
      typing.remove();
      const timed = c.providerTimeout || e;
      const isProviderTimeout = timed?.code === "FIRST_PROGRESS_TIMEOUT" || timed?.code === "STREAM_IDLE_TIMEOUT"
        || /did not receive a model|stopped receiving tokens|took too long|timed out/i.test(String(timed?.message || e?.message || e));
      if (isProviderTimeout) {
        c.providerTimeout = null;
        try { c.chatAbortController?.abort?.(); } catch (_) {}
        if (statusText) statusText.textContent = "Recovering provider…";
        const gotProgress = Boolean((c.activeStreamText || "").trim());
        let recovery = null;
        try {
          const res = await fetch("/api/provider/recover", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              code: timed?.code || e.code || "PROVIDER_TIMEOUT",
              message: String(timed?.message || e?.message || e),
              got_progress: gotProgress,
              provider: "ollama",
              auto: true,
            }),
          });
          recovery = await res.json();
        } catch (_) {
          recovery = null;
        }
        if (recovery?.auto_retry_recommended && recovery?.usable && text && !options._providerRetried) {
          window.showAriaToast?.("Provider recovered — retrying…", "ok", 2500);
          if (statusText) statusText.textContent = "Retrying…";
          await sendMessage(text, false, { skipUserBubble: true, _providerRetried: true });
          return;
        }
        window.showProviderRecovery?.(String(timed.message || e.message || e), {
          retryText: text,
          reason: timed.code || e.code || "PROVIDER_TIMEOUT",
          recovery,
          gotProgress,
        });
        return;
      }
      if (c.chatStopRequested || e.name === "AbortError") {
        if ((c.activeStreamText || "").trim()) {
          window.addMessage?.("assistant", `${c.activeStreamText.trim()}\n\n*(stopped)*`, { type: "info" });
        }
        if (statusText) statusText.textContent = "Stopped";
        return;
      }
      if (!forceNoStream && useStreaming && wantsStream && !isCodingAgent
          && !/\bdebug until\b.*\btests?\s+pass\b/i.test(text)) {
        await sendMessage(text, true, { skipUserBubble: true });
        return;
      }
      const msg = String(e.message || e);
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        window.showError?.(
          `**Lost connection to ${ariaName()}** (the server may have restarted while working).\n\n`
          + "Wait a few seconds and try again. If it keeps happening, use the desktop shortcut or run:\n"
          + "`./scripts/launch-jarvis.sh`"
        );
      } else if (msg.includes("Ollama")) {
        window.showError?.(`**${msg}**\n\n${ariaName()} is starting Ollama automatically — try again in a few seconds.`);
      } else {
        window.showError?.(`**Error:** ${msg}`);
      }
    } finally {
      window.finishSendUi?.();
    }
  }

  Object.assign(window, {
    sendMessage,
    readStreamChunk,
    parseJsonResponse,
    isStreamableAttachment,
  });
})();
