/** Gallery Home — stay-in-Gallery generation, library, honest jobs, keyboard a11y. Chat command hint: generate image: */
(function () {
  "use strict";

  const state = {
    offset: 0,
    limit: 48,
    total: 0,
    query: "",
    sort: "newest",
    includeArtifacts: false,
    favoritesOnly: false,
    selected: new Set(),
    focusIdx: -1,
    items: [],
    jobStatus: "",
    tab: "library",
    activeJobId: null,
    lastParams: null,
  };

  function $(id) {
    return document.getElementById(id);
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function statusLine() {
    return $("statusText");
  }

  function setGenStatus(msg, tone) {
    const el = $("galleryJobStatus");
    if (el) {
      el.textContent = msg || "";
      el.classList.toggle("warn", tone === "err");
    }
    state.jobStatus = msg || "";
    if (msg && tone) window.showAriaToast?.(msg, tone === "err" ? "err" : tone === "ok" ? "ok" : "info", 3500);
  }

  async function pollGalleryJob(jobId) {
    state.activeJobId = jobId;
    $("galleryCancelGenBtn")?.classList.remove("hidden");
    const res = await fetch(`/api/media/job/${encodeURIComponent(jobId)}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.message || "Job not found");
    const label = data.message || (data.done ? "Done" : "Working…");
    const pct = data.pct != null ? ` (${data.pct}%)` : "";
    const eta = data.eta_sec != null ? ` · ~${data.eta_sec}s` : "";
    const q = data.queue_position != null ? ` · queue #${data.queue_position}` : "";
    setGenStatus(`${label}${pct}${eta}${q}`);
    if (!data.done) {
      await new Promise((r) => setTimeout(r, 1200));
      return pollGalleryJob(jobId);
    }
    state.activeJobId = null;
    $("galleryCancelGenBtn")?.classList.add("hidden");
    if (data.cancelled) throw new Error("Cancelled");
    if (!data.result?.ok) {
      const msg = data.error || data.result?.message || "Job failed";
      const actions = data.result?.actions || data.result?.hint;
      if (actions) setGenStatus(`${msg} — ${typeof actions === "string" ? actions : "See recovery options"}`, "err");
      throw new Error(msg);
    }
    return data.result;
  }

  async function runQueued(url, bodyOrForm, { formData = false } = {}) {
    const opts = formData
      ? { method: "POST", body: bodyOrForm }
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(bodyOrForm || {}),
        };
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.ok === false) {
      throw new Error(data.message || `Request failed (${res.status})`);
    }
    if (data.pending && data.job_id) {
      setGenStatus(data.message || "Queued…");
      return pollGalleryJob(data.job_id);
    }
    // Never treat pending-less incomplete as success if expected async
    return data;
  }

  function thumbUrl(img) {
    const apiAuthUrl = window.apiAuthUrl || ((u) => u);
    if (img.restricted || img.thumb_blocked) {
      return apiAuthUrl("/api/gallery/placeholder");
    }
    return apiAuthUrl(`/api/gallery/${encodeURIComponent(img.name)}?max=${window.GALLERY_THUMB_MAX || 384}`);
  }

  function renderGrid() {
    const el = $("galleryGrid");
    if (!el) return;
    const items = state.items;
    if (!items.length) {
      el.innerHTML = `<p class="muted">No images yet.
        <button type="button" class="ghost-btn tiny" id="galleryEmptyPromptBtn">Focus prompt</button>
        — generate stays in Gallery.</p>`;
      $("galleryEmptyPromptBtn")?.addEventListener("click", () => $("galleryPromptInput")?.focus());
      return;
    }
    el.innerHTML = items
      .map((img, idx) => {
        const selected = state.selected.has(img.name);
        const focused = idx === state.focusIdx;
        const restricted = img.restricted;
        const alt = restricted
          ? "Restricted image"
          : esc(img.caption || img.prompt || img.name);
        return `<div class="gallery-item${selected ? " selected" : ""}${focused ? " focused" : ""}${restricted ? " gallery-item--restricted" : ""}"
          data-name="${esc(img.name)}" data-path="${esc(img.path || "")}" data-idx="${idx}" tabindex="0" role="option" aria-selected="${selected}">
          ${restricted ? "" : `<button type="button" class="gallery-del" data-name="${esc(img.name)}" title="Move to trash" aria-label="Trash ${esc(img.name)}">×</button>
          <button type="button" class="gallery-upscale" data-path="${esc(img.path)}" data-name="${esc(img.name)}" title="Upscale 2×" aria-label="Upscale ${esc(img.name)}">2×</button>
          <button type="button" class="gallery-inpaint" data-path="${esc(img.path)}" data-name="${esc(img.name)}" title="Edit image" aria-label="Edit ${esc(img.name)}">✎</button>
          <button type="button" class="gallery-fav" data-name="${esc(img.name)}" title="Favorite" aria-label="Favorite ${esc(img.name)}">${img.favorite ? "★" : "☆"}</button>`}
          <img src="${thumbUrl(img)}" alt="${alt}" loading="lazy" decoding="async"
            data-image-path="${restricted ? "" : esc(img.path)}"
            data-full-src="${restricted ? "" : esc((window.apiAuthUrl || ((u) => u))(`/api/gallery/${encodeURIComponent(img.name)}`))}"
            title="${restricted ? esc(img.preview_message || "Restricted") : "Click to view"}" />
          ${restricted ? `<span class="gallery-restricted-badge">Restricted</span>` : ""}
        </div>`;
      })
      .join("");
    bindGrid(el);
  }

  function bindGrid(el) {
    el.querySelectorAll(".gallery-item").forEach((node) => {
      node.addEventListener("click", (e) => {
        if (e.target.closest("button")) return;
        const name = node.dataset.name;
        const idx = Number(node.dataset.idx);
        if (e.shiftKey && state.focusIdx >= 0) {
          const a = Math.min(state.focusIdx, idx);
          const b = Math.max(state.focusIdx, idx);
          for (let i = a; i <= b; i++) state.selected.add(state.items[i]?.name);
        } else if (e.metaKey || e.ctrlKey) {
          if (state.selected.has(name)) state.selected.delete(name);
          else state.selected.add(name);
        } else {
          state.selected.clear();
          state.selected.add(name);
          openItem(state.items[idx]);
        }
        state.focusIdx = idx;
        renderGrid();
      });
      node.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openItem(state.items[Number(node.dataset.idx)]);
        }
      });
    });
    el.querySelectorAll(".gallery-del").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await trashImage(btn.dataset.name);
      });
    });
    el.querySelectorAll(".gallery-upscale").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await upscaleImage(btn.dataset.path);
      });
    });
    el.querySelectorAll(".gallery-inpaint").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const path = btn.dataset.path;
        if (window.openInpaintModal) window.openInpaintModal(path);
        else openItem(state.items.find((i) => i.path === path));
      });
    });
    el.querySelectorAll(".gallery-fav").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await fetch("/api/gallery/favorites/toggle", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: btn.dataset.name }),
        });
        loadGallery();
      });
    });
  }

  function openItem(img) {
    if (!img || img.restricted) {
      window.showAriaToast?.(img?.preview_message || "Restricted in censored mode", "warn", 4000);
      return;
    }
    const resolveImageUrl = window.resolveImageUrl;
    const openImageLightbox = window.openImageLightbox;
    if (!openImageLightbox) return;
    const GALLERY_THUMB_MAX = window.GALLERY_THUMB_MAX || 384;
    openImageLightbox(
      resolveImageUrl ? resolveImageUrl(img.path, { thumb: false }) : `/api/gallery/${encodeURIComponent(img.name)}`,
      img.name,
      img.path,
      resolveImageUrl
        ? resolveImageUrl(img.path, { thumb: true, thumbMax: GALLERY_THUMB_MAX })
        : `/api/gallery/${encodeURIComponent(img.name)}?max=${GALLERY_THUMB_MAX}`,
    );
  }

  async function trashImage(name) {
    try {
      const result = await window.ariaMutate({
        request: () => fetch(`/api/gallery/${encodeURIComponent(name)}`, { method: "DELETE" }),
        verify: async () => {
          const listRes = await fetch("/api/gallery?limit=80");
          if (!listRes.ok) return false;
          const listData = await listRes.json().catch(() => ({}));
          const names = (listData.images || []).map((i) => i.name);
          return !names.includes(name);
        },
        successToast: `Moved ${name} to trash`,
        failToast: "Trash failed",
      });
      if (!result.ok) return;
      const trashId = result.data?.trash_id;
      await loadGallery();
      // Inline undo like prompt history
      const bar = $("galleryUndoBar");
      if (bar && trashId) {
        bar.innerHTML = `Trashed ${esc(name)}. <button type="button" class="ghost-btn tiny" id="galleryUndoBtn">Undo</button>`;
        bar.classList.remove("hidden");
        $("galleryUndoBtn")?.addEventListener("click", async () => {
          const restored = { name };
          const restore = await window.ariaMutate({
            request: () =>
              fetch("/api/gallery/restore", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ trash_id: trashId }),
              }),
            verify: async (data) => {
              restored.name = data.restored || data.name || name;
              const check = await fetch(`/api/gallery/${encodeURIComponent(restored.name)}?max=64`);
              return check.ok;
            },
            successToast: "Restored",
            failToast: "Restore failed",
          });
          if (!restore.ok) return;
          bar.classList.add("hidden");
          await loadGallery();
        });
        setTimeout(() => bar.classList.add("hidden"), 300 * 1000);
      }
    } catch (err) {
      window.showAriaToast?.(err.message || "Trash failed", "err", 5000);
    }
  }

  async function upscaleImage(path) {
    if (!path) return;
    setGenStatus("Upscale queued…");
    try {
      const form = new FormData();
      form.append("path", path);
      form.append("scale", "2");
      const result = await runQueued("/api/image/upscale", form, { formData: true });
      const name = result.image_path?.split("/").pop() || result.image_name || "done";
      setGenStatus(`Upscaled → ${name}`, "ok");
      loadGallery({ reset: true });
    } catch (err) {
      setGenStatus(err.message || "Upscale failed", "err");
    }
  }

  async function loadGallery({ reset = false, append = false } = {}) {
    const el = $("galleryGrid");
    if (!el) return;
    if (reset) state.offset = 0;
    if (!append) {
      el.innerHTML = `<p class="muted gallery-skeleton" aria-busy="true">Loading library…</p>`;
    }
    if (document.getElementById("imageEngineUncensoredBanner")) {
      await window.loadComfyMode?.();
    }
    try {
      const params = new URLSearchParams({
        offset: String(state.offset),
        limit: String(state.limit),
        sort: state.sort,
        include_artifacts: state.includeArtifacts ? "true" : "false",
        favorites: state.favoritesOnly ? "true" : "false",
      });
      if (state.query) params.set("q", state.query);
      const res = await fetch(`/api/gallery?${params}`);
      if (!res.ok) throw new Error(`Gallery unavailable (${res.status})`);
      const data = await res.json();
      const images = data.images || [];
      state.total = data.total ?? images.length;
      state.items = append ? state.items.concat(images) : images;
      const meta = $("galleryLibraryMeta");
      if (meta) {
        meta.textContent = `${state.total} image${state.total === 1 ? "" : "s"} · showing ${state.items.length}`;
      }
      renderGrid();
      const more = $("galleryLoadMoreBtn");
      if (more) more.classList.toggle("hidden", !data.has_more);
      loadPromptHistory();
    } catch (err) {
      if (
        window.AriaNet?.isRoomAbort?.(err) ||
        err?.name === "AbortError" ||
        /aborted/i.test(String(err?.message || ""))
      ) {
        if (
          document.body.classList.contains("house-gallery") ||
          /^#?gallery\b/i.test(location.hash || "")
        ) {
          clearTimeout(loadGallery._retry);
          loadGallery._retry = setTimeout(() => loadGallery({ reset: true }), 140);
        }
        return;
      }
      el.innerHTML = `<p class="warn">Could not load gallery — ${esc(String(err.message || err))}
        <button type="button" class="ghost-btn tiny" id="galleryRetryBtn">Retry</button></p>`;
      $("galleryRetryBtn")?.addEventListener("click", () => loadGallery({ reset: true }));
      window.showAriaToast?.(err.message || "Gallery load failed", "err", 5000);
    }
  }

  async function loadPromptHistory() {
    const el = $("promptHistoryList");
    if (!el) return;
    try {
      const res = await fetch("/api/prompts?limit=30");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || `Prompt history failed (${res.status})`);
      const items = data.prompts || [];
      el.innerHTML = items.length
        ? items
            .map(
              (p) => `<div class="prompt-history-item">
          <button type="button" class="ghost-btn small prompt-reuse" data-prompt="${esc(p.prompt)}">Reuse</button>
          <button type="button" class="ghost-btn small prompt-fav" data-id="${esc(p.id)}" aria-label="${p.favorite ? "Unfavorite" : "Favorite"} prompt">${p.favorite ? "★" : "☆"}</button>
          <button type="button" class="ghost-btn small prompt-del" data-id="${esc(p.id)}" aria-label="Delete saved prompt">×</button>
          <span class="prompt-text">${esc(p.prompt.slice(0, 120))}${p.prompt.length > 120 ? "…" : ""}</span>
        </div>`,
            )
            .join("")
        : `<p>No saved prompts yet. <button type="button" class="ghost-btn tiny" id="promptHistoryEmptyBtn">Focus gallery prompt</button></p>`;
      el.querySelector("#promptHistoryEmptyBtn")?.addEventListener("click", () => $("galleryPromptInput")?.focus());
      el.querySelectorAll(".prompt-reuse").forEach((btn) => {
        btn.addEventListener("click", () => {
          if ($("galleryPromptInput")) $("galleryPromptInput").value = btn.dataset.prompt || "";
          $("galleryPromptInput")?.focus();
          window.showAriaToast?.("Prompt loaded in Gallery", "ok", 2500);
        });
      });
      el.querySelectorAll(".prompt-fav").forEach((btn) => {
        btn.addEventListener("click", async () => {
          await fetch(`/api/prompts/${encodeURIComponent(btn.dataset.id)}/favorite`, { method: "POST" });
          loadPromptHistory();
        });
      });
      el.querySelectorAll(".prompt-del").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const item = btn.closest(".prompt-history-item");
          const delRes = await fetch(`/api/prompts/${encodeURIComponent(btn.dataset.id)}`, { method: "DELETE" });
          const delData = await delRes.json().catch(() => ({}));
          if (!delRes.ok || !delData.ok) return;
          const undoRow = document.createElement("div");
          undoRow.className = "muted small prompt-undo-row";
          undoRow.innerHTML = `Prompt deleted. <button type="button" class="ghost-btn tiny">Undo</button>`;
          undoRow.querySelector("button")?.addEventListener("click", async () => {
            await fetch("/api/prompts/restore", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ entry: delData.entry }),
            });
            loadPromptHistory();
          });
          if (item) item.replaceChildren(undoRow);
          setTimeout(() => {
            if (undoRow.isConnected) loadPromptHistory();
          }, 8000);
        });
      });
    } catch (err) {
      el.textContent = "Could not load prompt history.";
    }
  }

  function collectGenParams() {
    const prompt = $("galleryPromptInput")?.value?.trim() || "";
    const params = {
      prompt,
      enhance: !!$("galleryEnhanceToggle")?.checked,
      aspect_ratio: $("galleryAspectSelect")?.value || "square",
      style_preset: $("galleryStylePreset")?.value || "",
      negative: $("galleryNegativeInput")?.value?.trim() || "",
      enhanced_prompt: $("galleryEnhancedInput")?.value?.trim() || "",
      steps: $("galleryStepsInput")?.value || "",
      cfg: $("galleryCfgInput")?.value || "",
      sampler: $("gallerySamplerSelect")?.value || "",
      scheduler: $("gallerySchedulerSelect")?.value || "",
      variations: $("galleryVariationsInput")?.value || "1",
      width: $("galleryWidthInput")?.value || "",
      height: $("galleryHeightInput")?.value || "",
    };
    if ($("galleryRandomSeed")?.checked) {
      params.random_seed = true;
    } else if ($("gallerySeedInput")?.value) {
      params.seed = $("gallerySeedInput").value;
    }
    return params;
  }

  async function loadPresets() {
    const sel = $("galleryStylePreset");
    if (!sel) return;
    try {
      const res = await fetch("/api/image-generation/presets");
      const data = await res.json();
      if (!data.ok) return;
      const cur = sel.value;
      sel.innerHTML = `<option value="">— none —</option>`;
      for (const p of data.items || []) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.title || p.id;
        sel.appendChild(opt);
      }
      if (cur) sel.value = cur;
    } catch {
      /* ignore */
    }
  }

  async function previewEnhance() {
    const prompt = $("galleryPromptInput")?.value?.trim();
    if (!prompt) {
      window.showAriaToast?.("Enter a prompt first", "warn");
      return;
    }
    const box = $("galleryEnhancePreview");
    try {
      const res = await fetch("/api/image-generation/enhance-preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          enhance: !!$("galleryEnhanceToggle")?.checked,
          negative: $("galleryNegativeInput")?.value || "",
        }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.message || "Preview failed");
      if (box) {
        box.classList.remove("hidden");
        box.innerHTML = `<strong>Original:</strong> ${esc(data.original)}<br/><strong>Enhanced:</strong> ${esc(data.enhanced)}`
          + (data.negative ? `<br/><strong>Negative:</strong> ${esc(data.negative)}` : "");
      }
      if ($("galleryEnhancedInput") && data.enhanced) $("galleryEnhancedInput").value = data.enhanced;
      if ($("galleryNegativeInput") && data.negative && !$("galleryNegativeInput").value) {
        $("galleryNegativeInput").value = data.negative;
      }
      $("galleryAdvancedParams")?.classList.remove("hidden");
    } catch (e) {
      window.showAriaToast?.(e.message || "Enhance preview failed", "err");
    }
  }

  async function cancelActiveJob() {
    const id = state.activeJobId;
    if (!id) return;
    try {
      await fetch(`/api/media/job/${encodeURIComponent(id)}/cancel`, { method: "POST" });
      setGenStatus("Cancelling…", "err");
    } catch (e) {
      setGenStatus(e.message || "Cancel failed", "err");
    }
  }

  async function generateInGallery(opts = {}) {
    const params = opts.params || collectGenParams();
    if (!params.prompt) {
      window.showAriaToast?.("Enter an image description first", "warn");
      $("galleryPromptInput")?.focus();
      return;
    }
    const proceed = (await window.vramPreflight?.("generate_image")) !== false;
    if (!proceed) return;
    const btn = $("galleryGenerateBtn");
    if (btn) btn.disabled = true;
    setGenStatus("Queuing generation…");
    state.lastParams = { ...params };
    try {
      const result = await runQueued("/api/gallery/generate", params);
      const name = result.image_name || result.image_path?.split("/").pop() || "";
      if (!name) throw new Error("Generation finished but no image name was returned");
      // Outcome check — never toast success from job ok alone
      const probe = await fetch(`/api/gallery/${encodeURIComponent(name)}?max=64`);
      if (!probe.ok) {
        throw new Error(`Image missing from Gallery after generate (${name}, HTTP ${probe.status})`);
      }
      const seedMsg = result.seed != null ? ` · seed ${result.seed}` : "";
      setGenStatus(`Generated ${name}${seedMsg}`, "ok");
      if (result.seed != null && $("gallerySeedInput")) $("gallerySeedInput").value = String(result.seed);
      window.jarvisNotify?.("Image ready", name);
      await loadGallery({ reset: true });
      const listed = (state.items || []).some((img) => img && img.name === name);
      if (!listed) {
        setGenStatus(`Generated file exists but Gallery list did not show ${name}`, "err");
        throw new Error(`Gallery list missing ${name} after generate`);
      }
    } catch (err) {
      setGenStatus(err.message || "Generation failed", "err");
      showRecovery(err.message || "");
    } finally {
      if (btn) btn.disabled = false;
      state.activeJobId = null;
      $("galleryCancelGenBtn")?.classList.add("hidden");
    }
  }

  async function showRecovery(error) {
    try {
      const res = await fetch("/api/image-generation/recovery", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error }),
      });
      const data = await res.json();
      if (!data.actions?.length) return;
      const el = $("galleryJobStatus");
      if (!el) return;
      const wrap = document.createElement("span");
      wrap.className = "gallery-recovery-actions";
      for (const a of data.actions.slice(0, 4)) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "ghost-btn tiny";
        b.textContent = a.label;
        b.addEventListener("click", async () => {
          if (a.view) {
            window.switchToView?.(a.view === "mission-control" ? "mission" : a.view);
            return;
          }
          if (a.action === "retry" && a.device) {
            try {
              if (window.postComfySettings) {
                await window.postComfySettings({ mode: a.device === "cpu" ? "cpu" : "gpu" });
              } else {
                const form = new FormData();
                form.append("mode", a.device === "cpu" ? "cpu" : "gpu");
                await fetch("/api/comfyui/settings", { method: "POST", body: form });
              }
            } catch { /* ignore */ }
            generateInGallery({ params: state.lastParams });
          } else if (a.action === "restart_comfyui") {
            try {
              if (window.postComfySettings) await window.postComfySettings({ mode: "auto" });
            } catch { /* ignore */ }
          }
        });
        wrap.appendChild(b);
        wrap.appendChild(document.createTextNode(" "));
      }
      el.appendChild(document.createTextNode(" "));
      el.appendChild(wrap);
    } catch { /* ignore */ }
  }

  async function generateAnother() {
    let params = state.lastParams;
    if (!params) {
      try {
        const res = await fetch("/api/image-generation/last-settings");
        const data = await res.json();
        if (data.prompt) {
          params = {
            prompt: data.prompt,
            negative: data.negative || "",
            enhanced_prompt: data.enhanced || "",
            enhance: data.enhance,
            steps: data.steps,
            cfg: data.cfg,
            random_seed: true,
          };
          if ($("galleryPromptInput")) $("galleryPromptInput").value = data.prompt;
        }
      } catch { /* ignore */ }
    }
    if (!params?.prompt) {
      window.showAriaToast?.("Nothing to regenerate yet", "warn");
      return;
    }
    params = { ...params, random_seed: true, seed: undefined };
    return generateInGallery({ params });
  }

  function moveFocus(delta) {
    if (!state.items.length) return;
    state.focusIdx = Math.max(0, Math.min(state.items.length - 1, (state.focusIdx < 0 ? 0 : state.focusIdx) + delta));
    renderGrid();
    const node = document.querySelector(`.gallery-item[data-idx="${state.focusIdx}"]`);
    node?.focus();
  }

  function onGalleryKeydown(e) {
    const view = $("galleryView");
    if (!view || view.classList.contains("hidden")) return;
    if (e.target?.matches?.("input, textarea, select")) return;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      moveFocus(1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      moveFocus(-1);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      moveFocus(4);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      moveFocus(-4);
    } else if (e.key === "Delete" || e.key === "Backspace") {
      const name = [...state.selected][0] || state.items[state.focusIdx]?.name;
      if (name) {
        e.preventDefault();
        trashImage(name);
      }
    } else if (e.key === "Escape") {
      state.selected.clear();
      renderGrid();
    } else if (e.key === "Enter" && state.focusIdx >= 0) {
      openItem(state.items[state.focusIdx]);
    }
  }

  function initGalleryView() {
    const root = $("galleryView");
    if (root?.dataset.galleryBound === "1") return;
    if (root) root.dataset.galleryBound = "1";

    $("galleryGenerateBtn")?.addEventListener("click", () => generateInGallery());
    $("galleryCancelGenBtn")?.addEventListener("click", cancelActiveJob);
    $("galleryEnhancePreviewBtn")?.addEventListener("click", previewEnhance);
    $("galleryGenAnotherBtn")?.addEventListener("click", generateAnother);
    $("galleryAdvancedToggle")?.addEventListener("click", () => {
      const adv = $("galleryAdvancedParams");
      if (!adv) return;
      const open = adv.classList.toggle("hidden") === false;
      $("galleryAdvancedToggle")?.setAttribute("aria-expanded", open ? "true" : "false");
      adv.setAttribute("aria-hidden", open ? "false" : "true");
    });
    $("galleryOpenMcBtn")?.addEventListener("click", () => window.switchToView?.("mission") || window.switchToView?.("mission-control"));
    $("galleryOpenJobsBtn")?.addEventListener("click", () => window.jarvisJobs?.openJobCenter?.() || window.switchToView?.("jobs"));
    loadPresets();
    $("galleryPromptInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        generateInGallery();
      }
    });
    $("gallerySearchInput")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        state.query = $("gallerySearchInput").value.trim();
        loadGallery({ reset: true });
      }
    });
    $("gallerySearchBtn")?.addEventListener("click", () => {
      state.query = $("gallerySearchInput")?.value?.trim() || "";
      loadGallery({ reset: true });
    });
    $("gallerySortSelect")?.addEventListener("change", (e) => {
      state.sort = e.target.value || "newest";
      loadGallery({ reset: true });
    });
    $("galleryArtifactsToggle")?.addEventListener("change", (e) => {
      state.includeArtifacts = !!e.target.checked;
      loadGallery({ reset: true });
    });
    $("galleryFavoritesToggle")?.addEventListener("change", (e) => {
      state.favoritesOnly = !!e.target.checked;
      loadGallery({ reset: true });
    });
    $("galleryLoadMoreBtn")?.addEventListener("click", () => {
      state.offset = state.items.length;
      loadGallery({ append: true });
    });
    $("galleryRefreshBtn")?.addEventListener("click", () => loadGallery({ reset: true }));
    $("galleryOpenMakerBtn")?.addEventListener("click", () => window.switchToView?.("maker"));
    $("galleryOpenFlytyingBtn")?.addEventListener("click", () => window.switchToView?.("flytying"));
    $("galleryOpenVideoBtn")?.addEventListener("click", () => window.switchToView?.("video"));
    $("galleryOpenMemeBtn")?.addEventListener("click", () => window.switchToView?.("meme"));
    $("galleryOpenJobsBtn")?.addEventListener("click", () => window.jarvisJobs?.openJobCenter?.());
    $("galleryOpenModelsBtn")?.addEventListener("click", () => window.openModelsHome?.() || window.switchToView?.("models"));
    $("galleryStoryboardBtn")?.addEventListener("click", async () => {
      const names = [...state.selected];
      if (!names.length) {
        window.showAriaToast?.("Select images first", "warn");
        return;
      }
      const out = await (
        await fetch("/api/gallery/storyboard-suggest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ names }),
        })
      ).json();
      window.switchToView?.("video");
      const input = $("storyboardPathsInput");
      if (input) input.value = out.paths_csv || names.join(",");
      window.showAriaToast?.("Storyboard paths suggested — create in Video Studio", "ok", 4000);
    });
    $("galleryVisionMetaBtn")?.addEventListener("click", async () => {
      const name = [...state.selected][0] || state.items[state.focusIdx]?.name;
      if (!name) return window.showAriaToast?.("Select an image", "warn");
      setGenStatus("Generating Vision metadata (opt-in)…");
      const res = await fetch(`/api/gallery/meta/${encodeURIComponent(name)}/vision`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      setGenStatus(data.ok ? "Metadata saved" : data.message || "Failed", data.ok ? "ok" : "err");
      loadGallery({ reset: true });
    });
    $("galleryDescribeBtn")?.addEventListener("click", () => $("galleryVisionMetaBtn")?.click());
    $("gallerySaveDocsBtn")?.addEventListener("click", async () => {
      const name = [...state.selected][0];
      if (!name) return window.showAriaToast?.("Select an image", "warn");
      const res = await fetch("/api/gallery/save-documents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json().catch(() => ({}));
      window.showAriaToast?.(data.message || (data.ok ? "Saved" : "Failed"), data.ok ? "ok" : "err");
    });
    $("galleryVisionCodingBtn")?.addEventListener("click", async () => {
      const img = state.items.find((i) => state.selected.has(i.name)) || state.items[state.focusIdx];
      if (!img?.path) return window.showAriaToast?.("Select an image", "warn");
      const res = await fetch("/api/gallery/vision-coding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: img.path }),
      });
      const data = await res.json().catch(() => ({}));
      window.showAriaToast?.(data.message || data.error || "Done", data.ok ? "ok" : "err");
      if (data.open_view === "coding") window.openCodingHome?.("proposals");
    });
    $("galleryClusterBtn")?.addEventListener("click", async () => {
      const res = await fetch("/api/gallery/clusters", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      const out = $("galleryClusterOut");
      if (out) out.textContent = JSON.stringify(data.clusters || [], null, 2);
    });
    $("galleryCollectionBtn")?.addEventListener("click", async () => {
      const names = [...state.selected];
      if (!names.length) return window.showAriaToast?.("Select images", "warn");
      const colRes = await fetch("/api/gallery/collections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: `Collection ${new Date().toLocaleString()}`, names }),
      });
      const colData = await colRes.json().catch(() => ({}));
      if (!colRes.ok || colData.ok === false) {
        window.showAriaToast?.(colData.message || `Collection failed (${colRes.status})`, "err", 5000);
        return;
      }
      window.showAriaToast?.("Collection created", "ok");
    });
    document.addEventListener("keydown", onGalleryKeydown);
  }

  window.loadGallery = () => loadGallery({ reset: true });
  window.loadPromptHistory = loadPromptHistory;
  window.initGalleryView = initGalleryView;
  window.pollGalleryJob = pollGalleryJob;
  window.galleryGenerateInGallery = generateInGallery;
  window.galleryGenerateAnother = generateAnother;
  window.galleryFocusPrompt = () => $("galleryPromptInput")?.focus();
  window.openGalleryHome = function () {
    window.switchToView?.("gallery");
    initGalleryView();
    loadGallery({ reset: true });
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initGalleryView);
  else initGalleryView();
})();
