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
      grid.innerHTML = '<p class="muted">No memes yet — make one below or say “make a meme about …” in chat.</p>';
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
        if (!name || !confirm(`Delete ${name}?`)) return;
        const delRes = await fetch(`/api/meme-gallery/${encodeURIComponent(name)}`, { method: "DELETE" });
        const delData = await delRes.json();
        if (delData.ok) loadMemeGallery();
        else alert(delData.message || "Delete failed");
      });
    });
  } catch (e) {
    grid.innerHTML = `<p class="muted">Failed to load memes — ${escapeHtml(String(e.message || e))}</p>`;
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
    setMemeStatus("Add top/bottom text or an idea.", true);
    return;
  }
  if (previewOnly && !top && !bottom) {
    setMemeStatus("Preview needs top or bottom text.", true);
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
      setMemeStatus(data.message || "Meme failed", true);
      return;
    }
    let imageName = data.image_name;
    if (data.pending && data.job_id) {
      setMemeStatus("Queued — rendering in background…");
      const result = await pollMemeJob(data.job_id);
      imageName = result.image_name;
    }
    setMemeStatus(previewOnly ? "Preview ready" : "Meme saved");
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
    setMemeStatus(String(e.message || e), true);
  } finally {
    if (btn) btn.disabled = false;
  }
}

function initMemeStudio() {
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
  loadMemeGallery();
}

document.addEventListener("DOMContentLoaded", initMemeStudio);

window.loadMemeGallery = loadMemeGallery;
