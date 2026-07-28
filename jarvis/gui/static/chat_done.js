/** Chat response rendering (handleDone) — extracted from app.js. Load after chat_images/chat_video/chat_media/coding_proposals. */
(function () {
  function showChatWarnings(warnings) {
    if (!warnings?.length) return;
    const lastMsg = document.querySelector(".message.assistant:last-child .bubble");
    if (!lastMsg || lastMsg.querySelector(".chat-warnings")) return;
    const el = document.createElement("div");
    el.className = "chat-warnings muted";
    el.textContent = warnings.join(" ");
    lastMsg.appendChild(el);
  }

  function handleDone(data, text, streamed = false, options = {}) {
    const isNativeApp = () => window.isNativeApp?.() === true;
    const formatMessage = window.formatMessage || ((t) => t);
    const escapeHtml = window.escapeHtml || ((t) => String(t));
    const msgs = document.getElementById("messages");
    const statusText = document.getElementById("statusText");

    if (isNativeApp() && data?.proposal_id) {
      data = window.prepareNativeCodingResult?.(data) || data;
      text = data.message || text;
    }
    const meta = {
      module: data.module,
      type: window.resolveMetaType?.(data),
      proposal_id: data.proposal_id,
      diff: data.diff,
      diff_truncated: data.diff_truncated,
      diff_total_lines: data.diff_total_lines,
      choices: data.choices,
      agent_steps: data.agent_steps,
      diagnostics: data.diagnostics,
      syntax_ok: data.syntax_ok,
      verify_ok: data.verify_ok,
      test_impact: data.test_impact,
      show_undo: window.shouldShowUndo?.(data),
    };

    if (data.module) {
      document.querySelectorAll(".module-chip").forEach((chip) => {
        chip.classList.toggle("active", chip.dataset.module === data.module || chip.dataset.module === "all");
      });
    }

    // Tool-permission approvals (e.g. upgrade apply, HA control) — open the confirm modal
    if (data.confirm_required && data.confirm_id) {
      window.showToolConfirm?.(data);
    }

    const imgPath = data.image_path || data.output_path;
    const hasImage = imgPath && /\.(png|jpe?g|webp|gif|bmp)$/i.test(imgPath);
    const videoPath = data.video_path || (data.type === "video_result" ? data.output_path : "");
    const hasVideo = videoPath && /\.(mp4|webm|mov|mkv|avi|m4v)$/i.test(videoPath);
    const isVision = data.module === "vision";

    if (hasVideo) {
      let body = options.targetBody;
      if (!body) {
        if (streamed) {
          body = document.querySelector(".message.assistant:last-child .msg-body");
        } else {
          body = window.addMessage?.("assistant", "", meta, { skipScroll: true })?.body;
        }
      } else if (options.replaceQueued) {
        window.applyAssistantMeta?.(body.closest(".message"), meta);
        body.querySelector(".media-job-status")?.remove();
      }
      if (body) {
        body.innerHTML = window.buildVideoMessageHtml?.(data, text || data.message) || "";
        window.appendGeneratedVideo?.(body, videoPath, data.video_name);
        window.scrollMessageIntoView?.(body, "start");
      }
    } else if (data.compare_paths?.length >= 2 || data.diff_path) {
      let body;
      if (streamed) {
        body = document.querySelector(".message.assistant:last-child .msg-body");
      } else {
        body = window.addMessage?.("assistant", "", meta, { skipScroll: true })?.body;
      }
      if (body) {
        body.innerHTML = window.buildVisionMessageHtml?.(text || data.message) || "";
        const row = document.createElement("div");
        row.className = "compare-images-row";
        (data.compare_paths || []).forEach((p, i) => {
          window.appendImageFigure?.(row, p, null, `Image ${i + 1}`);
        });
        if (data.diff_path) {
          window.appendImageFigure?.(row, data.diff_path, null, "Visual diff (A | B | changes)");
        }
        body.appendChild(row);
        window.scrollMessageIntoView?.(body, "start");
      }
    } else if (data.module === "data") {
      let body;
      if (streamed) {
        body = document.querySelector(".message.assistant:last-child .msg-body");
      } else {
        body = window.addMessage?.("assistant", "", meta, { skipScroll: true })?.body;
      }
      if (body) {
        body.innerHTML = formatMessage(text || data.message || "");
        if (data.data_preview) body.insertAdjacentHTML("beforeend", window.buildDataTableHtml?.(data.data_preview) || "");
        if (data.chart_path) {
          const chartUrl = window.apiAuthUrl?.(`/api/audio/file?path=${encodeURIComponent(data.chart_path)}`);
          body.insertAdjacentHTML("beforeend", `<figure class="gen-image data-chart"><img src="${chartUrl}" alt="chart" /><figcaption>Chart</figcaption></figure>`);
        }
        if (data.export_path) {
          const ep = data.export_path;
          if (/\.pdf$/i.test(ep)) {
            const pdfUrl = `/api/audio/file?path=${encodeURIComponent(ep)}`;
            body.insertAdjacentHTML(
              "beforeend",
              `<p class="data-export-link">PDF report: <a href="${pdfUrl}" target="_blank" rel="noopener">Download</a> · <code>${escapeHtml(ep)}</code></p>`
            );
          } else {
            body.insertAdjacentHTML("beforeend", `<p class="data-export-link">Exported: <code>${escapeHtml(ep)}</code></p>`);
          }
        }
        window.scrollMessageIntoView?.(body, "start");
      }
    } else if (hasImage && isVision) {
      let body;
      if (streamed) {
        body = document.querySelector(".message.assistant:last-child .msg-body");
      } else {
        body = window.addMessage?.("assistant", "", meta, { skipScroll: true })?.body;
      }
      if (body) {
        body.innerHTML = window.buildVisionMessageHtml?.(text || data.message) || "";
        window.appendImageFigure?.(body, imgPath, data.image_name, "Analyzed image");
        window.scrollMessageIntoView?.(body, "start");
      }
    } else if (hasImage) {
      let body = options.targetBody;
      if (!body) {
        if (streamed) {
          body = document.querySelector(".message.assistant:last-child .msg-body");
        } else {
          body = window.addMessage?.("assistant", "", meta, { skipScroll: true })?.body;
        }
      } else if (options.replaceQueued) {
        window.applyAssistantMeta?.(body.closest(".message"), meta);
        body.querySelector(".media-job-status")?.remove();
      }
      if (body) {
        body.innerHTML = window.buildImageMessageHtml?.(data, text || data.message) || "";
        const mountImg = () => {
          window.appendGeneratedImage?.(body, imgPath, data.image_name);
          window.scrollMessageIntoView?.(body, "start");
        };
        if (options.replaceQueued) setTimeout(mountImg, isNativeApp() ? 2500 : 600);
        else mountImg();
      }
    } else if (options.targetBody && (meta.proposal_id || meta.type === "proposal")) {
      const messageEl = options.targetBody.closest(".message");
      const bubble = messageEl?.querySelector(".bubble");
      if (options.replaceQueued) {
        window.applyAssistantMeta?.(messageEl, meta);
        options.targetBody.querySelector(".coding-job-status")?.remove();
        window.clearProposalExtras?.(bubble);
      }
      options.targetBody.innerHTML = formatMessage(text || data.message || "");
      window.syncMessageRawText?.(options.targetBody, text || data.message || "");
      window.ensureMessageCopyAction?.(messageEl, options.targetBody);
      if (bubble && (meta.proposal_id || meta.diagnostics || meta.agent_steps)) {
        const mount = () => window.attachProposalExtras?.(bubble, meta, messageEl);
        if (meta.proposal_id && isNativeApp()) {
          requestAnimationFrame(() => requestAnimationFrame(mount));
        } else {
          mount();
        }
      }
      window.scrollMessageIntoView?.(options.targetBody, "start");
    } else if (options.targetBody && options.pendingMediaJob) {
      window.applyAssistantMeta?.(options.targetBody.closest(".message"), meta);
      options.targetBody.innerHTML = formatMessage(text || data.message || "Working…");
      options.targetBody.closest(".message")?.classList.remove("typing-msg");
      window.scrollMessageIntoView?.(options.targetBody, "start");
    } else if (streamed) {
      const lastMsg = document.querySelector(".message.assistant:last-child");
      const msg = lastMsg?.querySelector(".msg-body");
      const bubble = lastMsg?.querySelector(".bubble");
      const content = text || data.message || "";
      if (msg) {
        msg.innerHTML = formatMessage(content);
        window.syncMessageRawText?.(msg, content);
        window.ensureMessageCopyAction?.(lastMsg, msg);
      }
      if (bubble && (meta.proposal_id || meta.type === "proposal" || meta.show_undo
        || meta.diagnostics || meta.agent_steps)) {
        const mount = () => window.attachProposalExtras?.(bubble, meta, lastMsg);
        if (meta.proposal_id && isNativeApp()) {
          requestAnimationFrame(() => requestAnimationFrame(mount));
        } else {
          mount();
        }
        if (msgs) msgs.scrollTop = msgs.scrollHeight;
      }
    } else {
      window.addMessage?.("assistant", text || data.message || "", meta);
    }

    if (window.jarvisChat) window.jarvisChat.lastAssistantText = text || data.message || "";
    if (data.warnings?.length) showChatWarnings(data.warnings);
    if (data.audio_path) window.showAudioPlayer?.(data.audio_path, data.transcript);
    if (data.chart_path && data.module !== "data") {
      const chartUrl = window.apiAuthUrl?.(`/api/audio/file?path=${encodeURIComponent(data.chart_path)}`);
      const msg = document.querySelector(".message.assistant:last-child .msg-body");
      if (msg) {
        msg.insertAdjacentHTML("beforeend", `<img src="${chartUrl}" alt="chart" style="max-width:100%" />`);
      } else {
        window.addMessage?.("assistant", `[chart:${data.chart_path}]`, { type: "info" });
      }
    }

    if (data.job_id && (data.type === "coding_job" || data.result_type === "coding_job")) {
      const msg = document.querySelector(".message.assistant:last-child");
      window.jarvisPollCodingJob?.(data.job_id, msg);
    } else if (
      data.job_id
      && (data.type === "media_job" || data.result_type === "media_job" || data.pending)
    ) {
      const msg = options.targetBody?.closest?.(".message")
        || document.querySelector(".message.assistant:last-child");
      window.pollMediaJob?.(data.job_id, msg);
    }

    if (data.memory_citations?.length) {
      const bubble = document.querySelector(".message.assistant:last-child .bubble");
      window.jarvisRenderMemoryCitations?.(bubble, data.memory_citations);
      window.AriaChatOS?.attachReplyActions?.(
        document.querySelector(".message.assistant:last-child .bubble"),
        meta,
      );
    } else {
      window.AriaChatOS?.attachReplyActions?.(
        document.querySelector(".message.assistant:last-child .bubble"),
        meta,
      );
    }
    if (data.ok && (text || data.message) && meta.type !== "proposal" && !data.proposal_id) {
      window.jarvisMaybeSpeakReply?.(text || data.message);
    }

    const mode = data.uncensored ? "Uncensored" : "Standard";
    const mod = data.module ? ` · ${data.module}` : "";
    const timing = data.inference_ms ? ` · ${(data.inference_ms / 1000).toFixed(1)}s` : "";
    const modelTag = data.model ? ` · ${data.model.split(":")[0]}` : "";
    const tokParts = [];
    if (data.prompt_tokens) tokParts.push(`${data.prompt_tokens} in`);
    if (data.completion_tokens) tokParts.push(`${data.completion_tokens} out`);
    const tokTag = tokParts.length ? ` · ${tokParts.join(" / ")} tok` : "";
    if (statusText) {
      if (!data.ok) {
        statusText.textContent = "Error — check Ollama";
      } else {
        statusText.textContent = `Ready · ${mode}${mod}${timing}${modelTag}${tokTag}`;
      }
    }
    if (data.ok && window.jarvisNotify && !window.mediaWorkActive?.()) {
      window.__ariaActivitySuppressNotify = true;
      try {
        if (hasVideo) window.jarvisNotify("Video ready", (text || data.message || "Clip generated").slice(0, 120));
        else if (hasImage && data.module === "image" && !isNativeApp()) {
          window.jarvisNotify("Image ready", (text || data.message || "Image generated").slice(0, 120));
        } else if (data.module === "coding" && (data.proposal_id || data.agent_steps?.length)) {
          window.jarvisNotify("Coding task done", (text || data.message || "Finished").slice(0, 120));
        }
      } finally {
        window.__ariaActivitySuppressNotify = false;
      }
    }
    if (data.ok) {
      const P = window.AriaActivityProducers;
      if (hasImage && data.module === "image") P?.gallery?.complete?.(text || data.message || "Image generated");
      if (hasVideo) P?.video?.complete?.(text || data.message || "Video generated");
      if (data.module === "coding") P?.coding?.applied?.(text || data.message || "Coding finished");
      if (data.module === "vision" || data.vision) P?.vision?.complete?.(text || "Vision analysis complete");
    } else if (!data.ok) {
      const P = window.AriaActivityProducers;
      if (data.module === "image") P?.gallery?.failed?.(data.message || "Generation failed");
      if (hasVideo || data.module === "video") P?.video?.failed?.(data.message || "Video failed");
      if (data.module === "coding") P?.coding?.rejected?.(data.message || "Coding failed");
    }
    if (hasImage && data.module === "image" && window.galleryViewVisible?.() && !isNativeApp()) {
      setTimeout(() => { if (window.galleryViewVisible?.()) window.loadGallery?.(); }, 800);
    }

    // Browser Chat bridge — open Browser with shared URL/goal prefill (never fake success)
    if (data.open_view === "browser" || (data.module === "browser" && (data.prefill_url || data.prefill_goal || data.url))) {
      window.__browserPrefill = {
        url: data.prefill_url || data.url || "",
        goal: data.prefill_goal || data.goal || "",
        message: data.message || "",
      };
      try {
        window.showView?.("browser");
        window.refreshBrowserPanel?.();
        window.refreshBrowserHome?.();
      } catch (_) { /* ignore */ }
    }
  }

  Object.assign(window, { handleDone, showChatWarnings });
})();
