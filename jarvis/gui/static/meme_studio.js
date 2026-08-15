/** Meme Studio tab — classic top/bottom captions + optional AI background. */

async function pollMemeJob(jobId) {
  const res = await fetch(`/api/media/job/${encodeURIComponent(jobId)}`);
  const data = await res.json();
  if (!data.ok) throw new Error(data.message || "Job not found");
  setMemeStatus(data.message || "Working…");
  if (!data.done) {
    await new Promise((r) => setTimeout(r, 1200));
    return pollMemeJob(jobId);
  }
  if (!data.result?.ok) {
    throw new Error(data.error || data.result?.message || "Meme failed");
  }
  return data.result;
}

async function loadMemeGallery() {
  const grid = document.getElementById("memeGalleryGrid");
  if (!grid) return;
  grid.innerHTML = '<p class="muted">Loading…</p>';
  try {
    const res = await fetch("/api/meme-gallery");
    const data = await res.json();
    const memes = data.memes || [];
    if (!memes.length) {
      grid.innerHTML = '<p class="muted">No memes yet — <button type="button" class="ghost-btn tiny" id="memeEmptyChatBtn">ask Chat</button> or make one below.</p>';
      grid.querySelector("#memeEmptyChatBtn")?.addEventListener("click", () => {
        window.switchToView?.("chat");
        window.jarvisSendToChat?.("Make a meme about ");
      });
      return;
    }
    grid.innerHTML = memes.map((m) => `
      <figure class="meme-card" data-name="${escapeHtml(m.name)}">
        <img src="/api/meme-gallery/${encodeURIComponent(m.name)}" alt="${escapeHtml(m.name)}" loading="lazy" />
        <figcaption>${escapeHtml(m.name)}</figcaption>
        <button type="button" class="ghost-btn small meme-delete-btn" data-name="${escapeHtml(m.name)}">Delete</button>
      </figure>
    `).join("");
    grid.querySelectorAll(".meme-delete-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const name = btn.dataset.name;
        if (!name) return;
        const delOk = window.ariaConfirm
          ? await window.ariaConfirm(`Delete ${name}?`, { title: "Delete meme", okLabel: "Delete" })
          : window.confirm(`Delete ${name}?`);
        if (!delOk) return;
        try {
          const delRes = await fetch(`/api/meme-gallery/${encodeURIComponent(name)}`, { method: "DELETE" });
          const delData = await delRes.json().catch(() => ({}));
          if (!delRes.ok || !delData.ok) {
            window.showAriaToast?.(delData.message || `Delete failed (${delRes.status})`, "err", 5000);
            return;
          }
          window.showAriaToast?.("Meme deleted", "ok", 2500);
          loadMemeGallery();
        } catch (err) {
          window.showAriaToast?.(err?.message || "Delete failed", "err", 5000);
        }
      });
    });
  } catch (e) {
    if (window.AriaNet?.isRoomAbort?.(e)) return;
    grid.innerHTML = `<p class="muted">Failed to load memes — ${escapeHtml(String(e.message || e))}</p>`;
    window.showAriaToast?.(e.message || "Failed to load memes", "err", 5000);
  }
}

function setMemeStatus(text, isError = false) {
  const el = document.getElementById("memeEngineStatus");
  if (!el) return;
  el.textContent = text;
  el.classList.toggle("error", isError);
}

async function generateMeme(previewOnly = false) {
  const top = document.getElementById("memeTopInput")?.value?.trim() || "";
  const bottom = document.getElementById("memeBottomInput")?.value?.trim() || "";
  const idea = document.getElementById("memeIdeaInput")?.value?.trim() || "";
  const useAi = document.getElementById("memeUseAiCheckbox")?.checked !== false;

  if (!previewOnly && !useAi && !top && !bottom) {
    const msg = "Add top/bottom text or an idea.";
    setMemeStatus(msg, true);
    window.showAriaToast?.(msg, "warn", 3500);
    return;
  }
  if (previewOnly && !top && !bottom) {
    const msg = "Preview needs top or bottom text.";
    setMemeStatus(msg, true);
    window.showAriaToast?.(msg, "warn", 3500);
    return;
  }

  const btn = previewOnly
    ? document.getElementById("memePreviewBtn")
    : document.getElementById("memeGenerateBtn");
  if (btn) btn.disabled = true;
  setMemeStatus(previewOnly ? "Rendering preview…" : "Generating meme (captions + background)…");

  try {
    const res = await fetch("/api/meme/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        top,
        bottom,
        idea,
        use_ai_image: useAi,
        preview_only: previewOnly,
      }),
    });
    const data = await res.json();
    if (!data.ok) {
      const msg = data.message || "Meme failed";
      setMemeStatus(msg, true);
      window.showAriaToast?.(msg, "err", 5000);
      return;
    }
    let imageName = data.image_name;
    if (data.pending && data.job_id) {
      setMemeStatus("Queued — rendering in background…");
      const result = await pollMemeJob(data.job_id);
      imageName = result.image_name;
    }
    const okMsg = previewOnly ? "Preview ready" : "Meme saved";
    setMemeStatus(okMsg);
    window.showAriaToast?.(okMsg, "ok", 2500);
    const preview = document.getElementById("memePreview");
    if (preview && imageName) {
      preview.innerHTML = `
        <img src="/api/meme-gallery/${encodeURIComponent(imageName)}?t=${Date.now()}"
             alt="meme preview" class="meme-preview-img" />
      `;
      preview.classList.remove("hidden");
    }
    loadMemeGallery();
  } catch (e) {
    const msg = String(e.message || e);
    setMemeStatus(msg, true);
    window.showAriaToast?.(msg, "err", 5000);
  } finally {
    if (btn) btn.disabled = false;
  }
}

function initMemeStudio() {
  const root = document.getElementById("memeView");
  if (root?.dataset.bound === "1") {
    loadMemeGallery();
    return;
  }
  if (root) root.dataset.bound = "1";
  document.getElementById("memeGenerateBtn")?.addEventListener("click", () => generateMeme(false));
  document.getElementById("memePreviewBtn")?.addEventListener("click", () => generateMeme(true));
  document.getElementById("memeChatHintBtn")?.addEventListener("click", () => {
    document.querySelector('.view-tab[data-view="chat"]')?.click();
    const input = document.getElementById("messageInput");
    if (input) {
      input.value = "make a meme about ";
      input.focus();
    }
  });
  document.getElementById("memeOpenGalleryBtn")?.addEventListener("click", () => {
    window.switchToView?.("gallery");
  });
  document.getElementById("memeOpenVideoBtn")?.addEventListener("click", () => {
    window.switchToView?.("video");
  });
  loadMemeGallery();
}

document.addEventListener("DOMContentLoaded", initMemeStudio);

window.loadMemeGallery = loadMemeGallery;
