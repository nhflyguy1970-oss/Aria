/** Song Studio — genre transform, full songs, voice→song */

function updateAudioJobProgress(pct, message, statusEl, progressWrap, progressFill) {
  const safePct = Math.max(0, Math.min(100, Number(pct) || 0));
  if (statusEl) statusEl.textContent = `${safePct}% — ${message || "Working…"}`;
  if (progressWrap) progressWrap.classList.remove("hidden");
  if (progressFill) progressFill.style.width = `${safePct}%`;
}

function resetAudioJobProgress(statusEl, progressWrap, progressFill) {
  if (progressWrap) progressWrap.classList.add("hidden");
  if (progressFill) progressFill.style.width = "0%";
  if (statusEl) statusEl.textContent = "";
}

let activeAudioJobId = null;

async function cancelAudioJob() {
  if (!activeAudioJobId) return;
  try {
    await fetch(`/api/audio/job/${encodeURIComponent(activeAudioJobId)}/cancel`, { method: "POST" });
  } catch (_) {}
}

async function pollAudioJob(jobId, statusEl, onDone, progressWrap, progressFill) {
  const maxWait = 600000;
  const start = Date.now();
  activeAudioJobId = jobId;
  const cancelBtn = document.getElementById("audioJobCancelBtn");
  cancelBtn?.classList.remove("hidden");
  while (Date.now() - start < maxWait) {
    const res = await fetch(`/api/audio/job/${encodeURIComponent(jobId)}`);
    const data = await res.json();
    if (!data.ok) break;
    updateAudioJobProgress(data.pct, data.message, statusEl, progressWrap, progressFill);
    if (data.done) {
      activeAudioJobId = null;
      cancelBtn?.classList.add("hidden");
      if (data.error) {
        if (statusEl) statusEl.textContent = data.error;
        if (progressFill) progressFill.style.width = "100%";
        return null;
      }
      updateAudioJobProgress(100, data.message || "Complete", statusEl, progressWrap, progressFill);
      if (onDone) onDone(data.result || {});
      if (window.jarvisNotify) {
        const title = data.result?.title || `${typeof ariaName === "function" ? ariaName() : "ARIA"} audio`;
        window.jarvisNotify("Audio job complete", title);
      }
      return data.result || {};
    }
    await new Promise((r) => setTimeout(r, 1200));
  }
  if (statusEl) statusEl.textContent = "Job timed out";
  activeAudioJobId = null;
  cancelBtn?.classList.add("hidden");
  return null;
}

function setAudioBusy(busy) {
  const root = document.getElementById("audioContent");
  if (!root) return;
  root.querySelectorAll("button, input, textarea, select").forEach((el) => {
    el.disabled = busy;
  });
}

function songStudioJobUi() {
  return {
    statusEl: document.getElementById("audioSongStatus"),
    progressWrap: document.getElementById("audioJobProgressWrap"),
    progressFill: document.getElementById("audioJobProgressFill"),
  };
}

function bindSongStudio(statusEl) {
  document.getElementById("audioJobCancelBtn")?.addEventListener("click", async () => {
    await cancelAudioJob();
    const ui = songStudioJobUi();
    if (ui.statusEl) ui.statusEl.textContent = "Cancelling…";
    setAudioBusy(false);
  });

  const genreBtn = document.getElementById("audioGenreBtn");
  const songBtn = document.getElementById("audioFullSongBtn");
  const voiceSongBtn = document.getElementById("audioVoiceSongBtn");
  const jobUi = songStudioJobUi();

  genreBtn?.addEventListener("click", async () => {
    const path = document.getElementById("audioGenrePath")?.value.trim()
      || audioLastPath
      || document.getElementById("audioEditPath")?.value.trim();
    const genre = document.getElementById("audioGenrePrompt")?.value.trim();
    if (!path || !genre) {
      jobUi.statusEl.textContent = "Pick a song file and enter a target genre";
      return;
    }
    setAudioBusy(true);
    resetAudioJobProgress(jobUi.statusEl, jobUi.progressWrap, jobUi.progressFill);
    updateAudioJobProgress(0, "Starting genre transform…", jobUi.statusEl, jobUi.progressWrap, jobUi.progressFill);
    const form = new FormData();
    form.append("path", path);
    form.append("genre", genre);
    form.append("duration", document.getElementById("audioGenreDur")?.value || "30");
    form.append("async_job", "1");
    const res = await fetch("/api/audio/song/genre", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      jobUi.statusEl.textContent = data.message || "Failed";
      setAudioBusy(false);
      return;
    }
    await pollAudioJob(
      data.job_id,
      jobUi.statusEl,
      (result) => {
        if (result.audio_path) {
          loadAudioIntoPlayer(result.audio_path, null);
          refreshRecentLists();
        }
        setAudioBusy(false);
      },
      jobUi.progressWrap,
      jobUi.progressFill,
    );
    setAudioBusy(false);
  });

  songBtn?.addEventListener("click", async () => {
    const topic = document.getElementById("audioSongTopic")?.value.trim();
    if (!topic) return;
    setAudioBusy(true);
    resetAudioJobProgress(jobUi.statusEl, jobUi.progressWrap, jobUi.progressFill);
    updateAudioJobProgress(0, "Starting full song…", jobUi.statusEl, jobUi.progressWrap, jobUi.progressFill);
    const form = new FormData();
    form.append("topic", topic);
    form.append("genre", document.getElementById("audioSongGenre")?.value || "pop");
    form.append("mood", document.getElementById("audioSongMood")?.value || "uplifting");
    form.append("duration", document.getElementById("audioSongDur")?.value || "30");
    form.append("async_job", "1");
    const res = await fetch("/api/audio/song/full", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      jobUi.statusEl.textContent = data.message || "Failed";
      setAudioBusy(false);
      return;
    }
    await pollAudioJob(
      data.job_id,
      jobUi.statusEl,
      (result) => {
        if (result.audio_path) {
          loadAudioIntoPlayer(result.audio_path, result.lyrics || null);
          const summaryEl = document.getElementById("audioSummary");
          if (summaryEl && result.lyrics) {
            summaryEl.textContent = result.lyrics;
            summaryEl.classList.remove("hidden");
          }
          refreshRecentLists();
        }
        setAudioBusy(false);
      },
      jobUi.progressWrap,
      jobUi.progressFill,
    );
    setAudioBusy(false);
  });

  voiceSongBtn?.addEventListener("click", async () => {
    const path = audioLastPath || document.getElementById("audioEditPath")?.value.trim();
    if (!path) {
      jobUi.statusEl.textContent = "Record your voice first";
      return;
    }
    setAudioBusy(true);
    resetAudioJobProgress(jobUi.statusEl, jobUi.progressWrap, jobUi.progressFill);
    updateAudioJobProgress(0, "Starting voice→song…", jobUi.statusEl, jobUi.progressWrap, jobUi.progressFill);
    const form = new FormData();
    form.append("path", path);
    form.append("lyrics", document.getElementById("audioVoiceLyrics")?.value.trim() || "");
    form.append("title", document.getElementById("audioVoiceTitle")?.value.trim() || "");
    form.append("style", document.getElementById("audioVoiceStyle")?.value.trim() || "pop ballad");
    form.append("genre", document.getElementById("audioVoiceGenre")?.value || "pop");
    form.append("duration", document.getElementById("audioVoiceDur")?.value || "30");
    form.append("async_job", "1");
    const res = await fetch("/api/audio/song/voice", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      jobUi.statusEl.textContent = data.message || "Failed";
      setAudioBusy(false);
      return;
    }
    await pollAudioJob(
      data.job_id,
      jobUi.statusEl,
      (result) => {
        if (result.audio_path) {
          loadAudioIntoPlayer(result.audio_path, result.lyrics || null);
          refreshRecentLists();
        }
        setAudioBusy(false);
      },
      jobUi.progressWrap,
      jobUi.progressFill,
    );
    setAudioBusy(false);
  });

  document.getElementById("audioPodcastMixBtn")?.addEventListener("click", async () => {
    const backing = document.getElementById("audioPodcastBacking")?.value.trim();
    const vocal = document.getElementById("audioPodcastVocal")?.value.trim();
    const status = document.getElementById("audioPodcastStatus");
    if (!backing) {
      if (status) status.textContent = "Enter a backing track path";
      return;
    }
    if (status) status.textContent = "Mixing…";
    const form = new FormData();
    form.append("backing_path", backing);
    if (vocal) form.append("vocal_path", vocal);
    form.append("vocal_gain_db", document.getElementById("audioPodcastGain")?.value || "2");
    form.append("title", "podcast_mix");
    const res = await fetch("/api/audio/podcast/mix", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      if (status) status.textContent = data.message || "Mix failed";
      return;
    }
    if (status) status.textContent = data.message || "Mix complete";
    if (data.audio_path) {
      loadAudioIntoPlayer(data.audio_path, null);
      refreshRecentLists();
      if (window.jarvisNotify) window.jarvisNotify("Podcast mix ready", data.audio_path.split("/").pop());
    }
  });

  document.getElementById("audioGenreUploadBtn")?.addEventListener("click", () => {
    document.getElementById("audioGenreUpload")?.click();
  });
  document.getElementById("audioGenreUpload")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    statusEl.textContent = "Uploading…";
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/api/audio/transcribe-upload", { method: "POST", body: form });
    const data = await res.json();
    if (data.ok && data.path) {
      document.getElementById("audioGenrePath").value = data.path;
      setAudioLastPath(data.path);
      statusEl.textContent = `Loaded: ${file.name}`;
    }
  });

  function applySongLimits(data) {
    const el = document.getElementById("audioSongSafeHint");
    const badge = document.getElementById("audioSongModeBadge");
    if (!el || !data.ok) return;
    const mode = (data.mode || "auto").toLowerCase();
    if (badge) {
      badge.textContent = mode.toUpperCase();
      badge.className = `audio-mode-badge audio-mode-${mode}`;
      badge.hidden = false;
      badge.title = data.warning || `Song Studio mode: ${mode}`;
    }
    if (data.warning) {
      el.textContent = data.warning;
      el.classList.add("audio-routing-warn");
    } else {
      el.textContent = `${data.duration}s max · vocals ${data.allow_vocals ? data.vocal_device : "off"} · music ${data.music_device || "cuda"}`;
      el.classList.remove("audio-routing-warn");
    }
    const durInputs = ["audioSongDur", "audioGenreDur"];
    durInputs.forEach((id) => {
      const input = document.getElementById(id);
      if (input && data.duration) input.max = String(data.duration);
    });
  }

  fetch("/api/audio/song/limits?duration=30")
    .then((r) => r.json())
    .then(applySongLimits)
    .catch(() => {});

  document.getElementById("audioSongDur")?.addEventListener("change", () => {
    const dur = document.getElementById("audioSongDur")?.value || "30";
    fetch(`/api/audio/song/limits?duration=${encodeURIComponent(dur)}`)
      .then((r) => r.json())
      .then(applySongLimits)
      .catch(() => {});
  });
}

function renderSongStudioSection(melodyOk) {
  return `
    <section class="audio-section audio-studio">
      <h3>Song Studio</h3>
      <p class="audio-hint">Genre remix needs MusicGen-Melody${melodyOk ? " ✓" : " (install transformers + librosa)"}.</p>

      <div id="audioJobProgressWrap" class="audio-job-progress hidden">
        <div class="audio-job-progress-track" aria-hidden="true">
          <div id="audioJobProgressFill" class="audio-job-progress-fill"></div>
        </div>
        <p id="audioSongStatus" class="audio-msg" aria-live="polite"></p>
        <button type="button" id="audioJobCancelBtn" class="ghost-btn small hidden audio-job-cancel">Cancel job</button>
      </div>

      <h4>Genre transform</h4>
      <p class="audio-hint">Load a song → describe the target genre (e.g. "heavy metal with distorted guitars").</p>
      <div class="audio-row">
        <input type="text" id="audioGenrePath" placeholder="Song path or use recent / upload" class="audio-path-input" />
        <input type="file" id="audioGenreUpload" accept="audio/*" hidden />
        <button type="button" id="audioGenreUploadBtn" class="ghost-btn small">Upload</button>
      </div>
      <div class="audio-row">
        <input type="text" id="audioGenrePrompt" placeholder="Target genre / style" class="audio-path-input" />
        <label>Duration <input type="number" id="audioGenreDur" min="5" max="30" value="30" /></label>
        <button type="button" id="audioGenreBtn" class="apply-btn small">Transform genre</button>
      </div>

      <h4>AI full song (lyrics + music) <span id="audioSongModeBadge" class="audio-mode-badge" hidden></span></h4>
      <p id="audioSongSafeHint" class="audio-hint audio-routing-warn">Loading GPU limits…</p>
      <div class="audio-row">
        <input type="text" id="audioSongTopic" placeholder="Song topic e.g. summer road trip" class="audio-path-input" />
        <input type="text" id="audioSongGenre" placeholder="Genre" value="pop" />
        <input type="text" id="audioSongMood" placeholder="Mood" value="uplifting" />
        <label>Dur <input type="number" id="audioSongDur" min="5" max="30" value="30" /></label>
        <button type="button" id="audioFullSongBtn" class="apply-btn small">Generate song</button>
      </div>

      <h4>Podcast / multi-track mix</h4>
      <p class="audio-hint">Combine a backing track (intro music, bed) with a voice recording via ffmpeg amix.</p>
      <div class="audio-row">
        <input type="text" id="audioPodcastBacking" placeholder="Backing track path (music bed)" class="audio-path-input" />
        <input type="text" id="audioPodcastVocal" placeholder="Vocal path (or use last recording)" class="audio-path-input" />
        <label>Voice gain (dB) <input type="number" id="audioPodcastGain" value="2" step="0.5" /></label>
        <button type="button" id="audioPodcastMixBtn" class="apply-btn small">Mix tracks</button>
      </div>
      <p id="audioPodcastStatus" class="audio-msg muted"></p>

      <h4>Voice → singing</h4>
      <p class="audio-hint">Record your voice (hum or speak lyrics), then generate a sung mix with AI backing.</p>
      <div class="audio-row">
        <input type="text" id="audioVoiceTitle" placeholder="Song title (optional)" class="audio-path-input" />
        <input type="text" id="audioVoiceStyle" placeholder="Style" value="pop ballad" />
        <input type="text" id="audioVoiceGenre" placeholder="Genre" value="pop" />
        <label>Dur <input type="number" id="audioVoiceDur" min="5" max="30" value="30" /></label>
      </div>
      <textarea id="audioVoiceLyrics" rows="2" placeholder="Lyrics (optional — auto-transcribed from recording)"></textarea>
      <div class="audio-row">
        <button type="button" id="audioVoiceSongBtn" class="apply-btn small">Make my voice a song</button>
      </div>
    </section>`;
}
