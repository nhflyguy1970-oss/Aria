/** Vision Home — product dashboard, history, profiles, honesty, batch. */
(function () {
  function $(id) {
    return document.getElementById(id);
  }

  async function loadVisionHome() {
    const status = $("visionHomeStatus");
    const honestyEl = $("visionHonesty");
    const historyEl = $("visionHistoryList");
    const profileSel = $("visionProfileSelect");
    const batchEl = $("visionBatchList");
    if (!status) return;
    const gen = (loadVisionHome._gen = (loadVisionHome._gen || 0) + 1);
    try {
      const [product, honesty, history, profiles, actions, batch, settings, experimental] = await Promise.all([
        fetch("/api/vision/product").then((r) => r.json()),
        fetch("/api/vision/honesty").then((r) => r.json()),
        fetch("/api/vision/history?limit=20").then((r) => r.json()),
        fetch("/api/vision/profiles").then((r) => r.json()),
        fetch("/api/vision/actions").then((r) => r.json()),
        fetch("/api/vision/batch").then((r) => r.json()).catch(() => ({ jobs: [] })),
        fetch("/api/vision/settings/unified").then((r) => r.json()).catch(() => ({})),
        fetch("/api/vision/experimental").then((r) => r.json()).catch(() => ({})),
      ]);
      if (gen !== loadVisionHome._gen) return;
      const st = product.state || {};
      status.textContent = `State: ${st.state || "idle"} · Model: ${honesty.model || "?"} · Mode: ${honesty.quality_mode || "?"}`;
      if (honestyEl) {
        const warns = (honesty.warnings || []).map((w) => `<li>${escape(w)}</li>`).join("") || "<li class='muted'>No warnings</li>";
        honestyEl.innerHTML = `
          <p><strong>${escape(honesty.model || "?")}</strong> · ${escape(honesty.expected_latency || "")}</p>
          <p>Est. VRAM ~${honesty.estimated_vram_mb ?? "?"}MB · Free ${honesty.free_vram_mb ?? "—"}MB · OCR: ${escape(honesty.ocr_mode || "")}${honesty.classic_ocr_available ? " (tesseract ok)" : ""}</p>
          <p>Fallback: ${escape(honesty.fallback || "")}</p>
          <ul class="tiny">${warns}</ul>`;
      }
      const ocrMode = $("visionHomeOcrMode");
      if (ocrMode && settings.ocr_mode) ocrMode.value = settings.ocr_mode;
      const speak = $("visionHomeSpeak");
      if (speak) speak.checked = Boolean(settings.speak_results);
      if (profileSel) {
        const active = profiles.active || "";
        profileSel.innerHTML = '<option value="">— none —</option>';
        (profiles.profiles || []).forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p.id;
          opt.textContent = p.name + (p.builtin ? "" : " *");
          if (p.id === active) opt.selected = true;
          profileSel.appendChild(opt);
        });
      }
      if (historyEl) {
        const rows = history.history || [];
        historyEl.innerHTML = rows.length
          ? rows
              .map(
                (h) => `<article class="vision-history-item" data-id="${escape(h.id)}">
            <strong>${escape(h.task || "analyze")}</strong>
            <span class="muted tiny">${escape((h.path || "").split("/").pop())} · ${h.latency_ms || 0}ms · ${escape(h.model || "")}${h.confidence != null ? " · conf " + h.confidence : ""}</span>
            <p>${escape((h.redacted ? h.analysis : h.analysis || h.ocr || "").slice(0, 180))}</p>
          </article>`,
              )
              .join("")
          : "<p class='muted'>No vision history yet — attach an image in Chat or analyze here.</p>";
      }
      if (batchEl) {
        const jobs = batch.jobs || [];
        batchEl.innerHTML = jobs.length
          ? jobs
              .map((j) => {
                const id = escape(j.id || "");
                return `<article class="vision-history-item">
              <strong>${escape(j.action || "batch")}</strong>
              <span class="muted tiny">${escape(j.status || "")} · ${j.done || 0}/${j.total || 0}</span>
              <div class="sidebar-btn-row">
                <button type="button" class="ghost-btn tiny" data-vision-cancel="${id}">Cancel</button>
                <button type="button" class="ghost-btn tiny" data-vision-retry="${id}">Retry</button>
              </div>
            </article>`;
              })
              .join("")
          : "<p class='muted'>No batch jobs.</p>";
      }
      const exp = $("visionExperimentalStatus");
      if (exp) {
        const enabled = (experimental.enabled || []).join(", ") || "none enabled";
        exp.textContent = `Flags: ${enabled}\nSet JARVIS_VISION_EXP_* =1 to opt in. Same Vision engine.`;
      }
      const rail = $("visionHomeActions");
      if (rail && !(rail.dataset.bound === "1")) {
        rail.dataset.bound = "1";
        (actions.actions || []).forEach((a) => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "ghost-btn small";
          btn.textContent = a.label;
          btn.title = a.id;
          btn.addEventListener("click", () => runHomeAction(a.id));
          rail.appendChild(btn);
        });
      }
      window.refreshVisionStrip?.(product, honesty);
    } catch (err) {
      if (gen !== loadVisionHome._gen) return;
      if (
        window.AriaNet?.absorbAbort?.(err, () => {
          if (
            document.body.classList.contains("house-vision") ||
            /^#?vision\b/i.test(location.hash || "")
          ) {
            loadVisionHome();
          }
        })
      ) {
        return;
      }
      if (status) status.textContent = err.message || "Vision Home failed to load";
    }
  }

  function escape(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  async function runHomeAction(action) {
    const path = $("visionHomePath")?.value?.trim();
    if (!path && action !== "compare") {
      window.showAriaToast?.("Enter an image path or attach via Chat", "warn");
      return;
    }
    try {
      const honesty = await fetch(`/api/vision/honesty?task=${encodeURIComponent(action === "tables" ? "ocr_structured" : action)}`).then((r) => r.json());
      if ((honesty.warnings || []).length) {
        window.showAriaToast?.(honesty.warnings[0], "warn", 5000);
      }
      const body = {
        path,
        path2: $("visionHomePath2")?.value?.trim() || undefined,
        action: action === "import" ? "import" : action,
        import_target: $("visionHomeImportTarget")?.value || "preview",
        question: $("visionHomeQuestion")?.value || "",
        source: "vision_home",
        speak: Boolean($("visionHomeSpeak")?.checked),
        force: true,
      };
      const res = await fetch("/api/vision/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || data.message || "Analyze failed");
      let text = data.message || data.analysis || JSON.stringify(data, null, 2);
      if (data.diff_path) text += `\n\nVisual diff: ${data.diff_path}`;
      if (data.confidence != null) text += `\n\nConfidence: ${data.confidence}`;
      $("visionHomeResult").textContent = text;
      window.showAriaToast?.(`Vision: ${action}`, "ok");
      loadVisionHome();
    } catch (err) {
      window.showAriaToast?.(err.message || "Vision action failed", "err", 5000);
    }
  }

  window.initVisionHome = function initVisionHome() {
    const root = $("visionView");
    if (!root) return;
    if (root.dataset.bound === "1") {
      loadVisionHome();
      return;
    }
    root.dataset.bound = "1";
    loadVisionHome();
    $("visionHomeRefreshBtn")?.addEventListener("click", loadVisionHome);
    $("visionHomeBatchBtn")?.addEventListener("click", loadVisionHome);
    $("visionHomeActivateProfileBtn")?.addEventListener("click", async () => {
      const id = $("visionProfileSelect")?.value;
      if (!id) return;
      await fetch(`/api/vision/profiles/${encodeURIComponent(id)}/activate`, { method: "POST" });
      window.showAriaToast?.("Vision profile applied", "ok");
      loadVisionHome();
    });
    $("visionHomeOcrMode")?.addEventListener("change", async (e) => {
      await fetch("/api/vision/settings/unified", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ocr_mode: e.target.value }),
      });
      window.showAriaToast?.(`OCR mode: ${e.target.value}`, "ok", 2000);
      loadVisionHome();
    });
    $("visionHomeSpeak")?.addEventListener("change", async (e) => {
      await fetch("/api/vision/settings/unified", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speak_results: e.target.checked }),
      });
    });
    $("visionHomeSpeakOcrBtn")?.addEventListener("click", () => runHomeAction("ocr"));
    $("visionOpenChatBtn")?.addEventListener("click", () => {
      window.jarvisPreferredModule = "vision";
      window.switchToView?.("chat");
    });
    $("visionOpenGalleryBtn")?.addEventListener("click", () => window.switchToView?.("gallery"));
    $("visionBatchList")?.addEventListener("click", async (e) => {
      const cancel = e.target.closest("[data-vision-cancel]");
      const retry = e.target.closest("[data-vision-retry]");
      if (cancel) {
        await fetch(`/api/vision/batch/${cancel.dataset.visionCancel}/cancel`, { method: "POST" });
        loadVisionHome();
      }
      if (retry) {
        await fetch(`/api/vision/batch/${retry.dataset.visionRetry}/retry`, { method: "POST" });
        loadVisionHome();
      }
    });
  };

  window.refreshVisionStrip = function refreshVisionStrip(product, honesty) {
    const strip = $("ariaVisionStrip");
    const label = strip?.querySelector(".vision-strip-label");
    if (!strip || !label) return;
    const st = product?.state?.state || "idle";
    const model = honesty?.model || product?.honesty?.model || "";
    strip.dataset.state = st;
    label.textContent = st === "idle" ? `Vision · ${model || "ready"}` : `Vision ${st}${model ? " · " + model : ""}`;
    strip.classList.toggle("vision-strip-active", st !== "idle");
  };

  window.addEventListener("jarvis-ws", (ev) => {
    const data = ev.detail || {};
    if (data.event === "vision_state") {
      const strip = $("ariaVisionStrip");
      const label = strip?.querySelector(".vision-strip-label");
      if (label) label.textContent = `Vision ${data.state || "idle"}`;
      strip?.classList.toggle("vision-strip-active", data.state && data.state !== "idle");
      const homeStatus = $("visionHomeStatus");
      if (homeStatus && !document.getElementById("visionView")?.classList.contains("hidden")) {
        homeStatus.textContent = `State: ${data.state || "idle"} · ${data.detail || ""}`;
      }
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.shiftKey && (e.key === "I" || e.key === "i")) {
      e.preventDefault();
      window.switchToView?.("vision");
    }
  });
})();
