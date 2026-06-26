/** Advanced audio — VU meter, live record, trim preview, diarize, wakeword, stream */

let liveSessionId = "";
let vuTimer = null;
let livePartialTimer = null;

function dbToVuPct(db) {
  if (db == null || Number.isNaN(db)) return 0;
  return Math.max(0, Math.min(100, ((db + 50) / 50) * 100));
}

function drawVuMeter(db) {
  const canvas = document.getElementById("audioVuCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  const pct = dbToVuPct(db);
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#1a1d24";
  ctx.fillRect(0, 0, w, h);
  const grad = ctx.createLinearGradient(0, 0, w, 0);
  grad.addColorStop(0, "#2a8");
  grad.addColorStop(0.7, "#da2");
  grad.addColorStop(1, "#c44");
  ctx.fillStyle = grad;
  ctx.fillRect(0, h * 0.35, (w * pct) / 100, h * 0.3);
  const label = document.getElementById("audioVuLabel");
  if (label) label.textContent = db != null ? `${db.toFixed(1)} dB` : "";
}

function stopVuPolling() {
  if (vuTimer) clearInterval(vuTimer);
  vuTimer = null;
  if (livePartialTimer) clearInterval(livePartialTimer);
  livePartialTimer = null;
}

async function pollLiveSession(statusEl) {
  if (!liveSessionId) return;
  const res = await fetch(`/api/audio/record/live/level?session_id=${encodeURIComponent(liveSessionId)}`);
  const data = await res.json();
  if (data.ok) {
    drawVuMeter(data.peak_db);
    if (data.partial_text) {
      const el = document.getElementById("audioTranscript");
      if (el) {
        el.textContent = data.partial_text;
        el.classList.remove("hidden");
      }
      document.getElementById("audioTranscriptActions")?.classList.remove("hidden");
    }
    if (statusEl) statusEl.textContent = `Live ${data.elapsed || 0}s…`;
  }
}

function playTrimPreview() {
  const preview = document.getElementById("audioPreview");
  if (!preview || !waveState.duration) return;
  const start = waveState.trimStart * waveState.duration;
  const end = waveState.trimEnd * waveState.duration;
  preview.currentTime = start;
  preview.play();
  const onTime = () => {
    if (preview.currentTime >= end) {
      preview.pause();
      preview.removeEventListener("timeupdate", onTime);
    }
  };
  preview.addEventListener("timeupdate", onTime);
}

function renderAdvancedSection() {
  return `
    <section class="audio-section audio-advanced">
      <h3>Advanced</h3>
      <div class="audio-vu-wrap">
        <canvas id="audioVuCanvas" width="320" height="24" class="audio-vu-canvas"></canvas>
        <span id="audioVuLabel" class="audio-hint"></span>
      </div>
      <div class="audio-row">
        <button type="button" id="audioTrimPreviewBtn" class="ghost-btn small">Preview trim</button>
        <button type="button" id="audioDiarizeBtn" class="ghost-btn small">Diarize speakers</button>
        <button type="button" id="audioStreamTranscribeBtn" class="ghost-btn small">Stream transcribe file</button>
        <button type="button" id="audioDetectLangBtn" class="ghost-btn small">Detect language</button>
      </div>
      <div class="audio-row">
        <span class="audio-hint">AE-5 ALSA:</span>
        <button type="button" id="audioEqVoiceBtn" class="ghost-btn small">Voice</button>
        <button type="button" id="audioEqMusicBtn" class="ghost-btn small">Music</button>
        <button type="button" id="audioEqFlatBtn" class="ghost-btn small">Flat</button>
        <span id="audioEqStatus" class="audio-hint"></span>
      </div>
      <div class="audio-row audio-vst-row">
        <span class="audio-hint">VST bridge:</span>
        <select id="audioVstPlaybackSelect" class="personality-select small-select" title="EQ applied when ARIA plays audio">
          <option value="flat">Playback: bypass</option>
          <option value="voice">Playback: voice</option>
          <option value="music">Playback: music</option>
          <option value="scout">Playback: scout</option>
          <option value="gaming">Playback: gaming</option>
        </select>
        <button type="button" id="audioVstProcessBtn" class="ghost-btn small">Process file</button>
        <select id="audioVstLiveSelect" class="personality-select small-select" title="Live system EQ via PipeWire">
          <option value="off">Live: off</option>
          <option value="voice">Live: voice</option>
          <option value="music">Live: music</option>
          <option value="scout">Live: scout</option>
          <option value="gaming">Live: gaming</option>
        </select>
        <button type="button" id="audioVstInstallBtn" class="ghost-btn small" title="Install PipeWire filter configs">Install live EQ</button>
        <span id="audioVstStatus" class="audio-hint"></span>
      </div>
      <div class="audio-row">
        <button type="button" id="audioWakewordStartBtn" class="ghost-btn small">Start wake word</button>
        <button type="button" id="audioWakewordStopBtn" class="ghost-btn small">Stop wake word</button>
        <span id="audioWakewordStatus" class="audio-hint"></span>
      </div>
      <pre id="audioStreamOut" class="audio-transcript hidden"></pre>
    </section>`;
}

function bindAdvanced(statusEl) {
  document.getElementById("audioTrimPreviewBtn")?.addEventListener("click", playTrimPreview);

  async function applyEq(preset) {
    const eqStatus = document.getElementById("audioEqStatus");
    const form = new FormData();
    form.append("preset", preset);
    const res = await fetch("/api/audio/creative-eq", { method: "POST", body: form });
    const data = await res.json();
    if (eqStatus) eqStatus.textContent = data.ok ? `${preset} applied` : (data.message || "EQ failed");
  }
  document.getElementById("audioEqVoiceBtn")?.addEventListener("click", () => applyEq("voice"));
  document.getElementById("audioEqMusicBtn")?.addEventListener("click", () => applyEq("music"));
  document.getElementById("audioEqFlatBtn")?.addEventListener("click", () => applyEq("flat"));

  async function loadVstStatus() {
    const vstStatus = document.getElementById("audioVstStatus");
    const playbackSel = document.getElementById("audioVstPlaybackSelect");
    const liveSel = document.getElementById("audioVstLiveSelect");
    try {
      const res = await fetch("/api/audio/vst/status");
      const data = await res.json();
      if (playbackSel && data.playback_chain) playbackSel.value = data.playback_chain;
      if (liveSel && data.live?.selected) liveSel.value = data.live.selected;
      if (vstStatus) {
        const live = data.live?.selected && data.live.selected !== "off" ? `live=${data.live.selected}` : "live=off";
        vstStatus.textContent = `${live} · ffmpeg ${data.ffmpeg ? "ok" : "—"}${data.pedalboard ? " · VST3" : ""}`;
      }
    } catch {
      if (vstStatus) vstStatus.textContent = "";
    }
  }
  loadVstStatus();

  document.getElementById("audioVstPlaybackSelect")?.addEventListener("change", async (e) => {
    const form = new FormData();
    form.append("chain", e.target.value);
    await fetch("/api/audio/vst/playback-chain", { method: "POST", body: form });
    loadVstStatus();
  });

  document.getElementById("audioVstProcessBtn")?.addEventListener("click", async () => {
    const path = audioLastPath || document.getElementById("audioEditPath")?.value.trim();
    const chain = document.getElementById("audioVstPlaybackSelect")?.value || "voice";
    const vstStatus = document.getElementById("audioVstStatus");
    if (!path) {
      if (vstStatus) vstStatus.textContent = "No audio file selected";
      return;
    }
    setAudioBusy(true);
    const form = new FormData();
    form.append("path", path);
    form.append("chain", chain === "flat" ? "voice" : chain);
    const res = await fetch("/api/audio/vst/process", { method: "POST", body: form });
    const data = await res.json();
    setAudioBusy(false);
    if (!data.ok) {
      if (vstStatus) vstStatus.textContent = data.message || "Process failed";
      return;
    }
    showPlayback(data.audio_path, "");
    if (vstStatus) vstStatus.textContent = `Processed → ${data.audio_path?.split("/").pop() || "done"}`;
    loadVstStatus();
  });

  document.getElementById("audioVstLiveSelect")?.addEventListener("change", async (e) => {
    const vstStatus = document.getElementById("audioVstStatus");
    const form = new FormData();
    form.append("preset", e.target.value);
    const res = await fetch("/api/audio/vst/live", { method: "POST", body: form });
    const data = await res.json();
    if (vstStatus) vstStatus.textContent = data.ok ? (data.message || "Live EQ updated") : (data.message || "Live EQ failed");
    if (!data.ok) loadVstStatus();
  });

  document.getElementById("audioVstInstallBtn")?.addEventListener("click", async () => {
    const vstStatus = document.getElementById("audioVstStatus");
    const form = new FormData();
    form.append("preset", "off");
    form.append("install", "1");
    const res = await fetch("/api/audio/vst/live", { method: "POST", body: form });
    const data = await res.json();
    if (vstStatus) vstStatus.textContent = data.message || (data.ok ? "Installed" : "Install failed");
  });

  document.getElementById("audioDetectLangBtn")?.addEventListener("click", async () => {
    const path = audioLastPath || document.getElementById("audioEditPath")?.value.trim();
    if (!path) return;
    const form = new FormData();
    form.append("path", path);
    statusEl.textContent = "Detecting language…";
    const res = await fetch("/api/audio/detect-language", { method: "POST", body: form });
    const data = await res.json();
    statusEl.textContent = data.ok
      ? `Detected: ${data.language} (${Math.round((data.probability || 0) * 100)}%)`
      : (data.error || "Detection failed");
  });

  document.getElementById("audioDiarizeBtn")?.addEventListener("click", async () => {
    const path = audioLastPath || document.getElementById("audioEditPath")?.value.trim();
    if (!path) return;
    setAudioBusy(true);
    statusEl.textContent = "Diarizing…";
    const form = new FormData();
    form.append("path", path);
    const res = await fetch("/api/audio/diarize", { method: "POST", body: form });
    const data = await res.json();
    setAudioBusy(false);
    if (!data.ok) {
      statusEl.textContent = data.message || "Diarize failed";
      return;
    }
    const text = data.transcript || (data.segments || []).map((s) =>
      `${s.speaker} (${s.start}s): ${s.text || ""}`
    ).join("\n");
    showPlayback(path, text);
    statusEl.textContent = `Diarized (${data.engine})`;
  });

  document.getElementById("audioStreamTranscribeBtn")?.addEventListener("click", async () => {
    const path = audioLastPath || document.getElementById("audioEditPath")?.value.trim();
    if (!path) return;
    const out = document.getElementById("audioStreamOut");
    if (out) {
      out.textContent = "";
      out.classList.remove("hidden");
    }
    statusEl.textContent = "Streaming transcript…";
    const model = document.getElementById("audioWhisperModel")?.value || "";
    const lang = document.getElementById("audioWhisperLang")?.value || "";
    const url = `/api/audio/transcribe-stream?path=${encodeURIComponent(path)}&model=${encodeURIComponent(model)}&language=${encodeURIComponent(lang)}`;
    const res = await fetch(url);
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop() || "";
      for (const chunk of parts) {
        const line = chunk.replace(/^data:\s*/, "").trim();
        if (!line) continue;
        try {
          const ev = JSON.parse(line);
          if (ev.type === "segment" && out) out.textContent += `${ev.text} `;
          if (ev.type === "done") {
            showPlayback(path, ev.text || out?.textContent || "");
            statusEl.textContent = "Stream done";
          }
        } catch (_) { /* skip */ }
      }
    }
  });

  let wakewordPoll = null;

  async function refreshWakewordStatus() {
    const res = await fetch("/api/audio/wakeword/status");
    const data = await res.json();
    const el = document.getElementById("audioWakewordStatus");
    if (el) {
      const phrase = data.phrase || data.model || "wake word";
      let msg;
      if (data.error) {
        msg = `Error: ${data.error}`;
      } else if (data.running) {
        msg = `Listening for "${phrase}"`;
        if (data.source) msg += ` · ${data.source.split(".").pop()}`;
        if (data.input_db != null) {
          msg += data.mic_live ? ` · mic ${data.input_db} dB` : ` · mic quiet (${data.input_db} dB)`;
        }
        if (data.last_score > 0.05) msg += ` · wake ${Math.round(data.last_score * 100)}%`;
      } else {
        msg = data.available ? "Stopped" : "Install openwakeword + pw-record";
      }
      if (data.record_on_detect && data.running) msg += " · auto-record";
      if (data.active_record_session) msg += " · recording…";
      if (data.last?.action === "recording") msg = `Recording (${data.last.session_id?.slice(0, 6) || "…"})…`;
      if (data.last?.transcript) {
        msg += ` · "${data.last.transcript.slice(0, 60)}${data.last.transcript.length > 60 ? "…" : ""}"`;
        const tEl = document.getElementById("audioTranscript");
        if (tEl) {
          tEl.textContent = data.last.transcript;
          tEl.classList.remove("hidden");
          document.getElementById("audioTranscriptActions")?.classList.remove("hidden");
        }
        if (data.last.audio_path && typeof setAudioLastPath === "function") {
          setAudioLastPath(data.last.audio_path);
        }
      } else if (data.last?.model) {
        const ago = data.last.ts ? `${Math.round(Date.now() / 1000 - data.last.ts)}s ago` : "";
        msg += ` · last: ${data.last.model} ${ago}`;
      }
      el.textContent = msg;
    }
    if (data.running && !wakewordPoll) {
      wakewordPoll = setInterval(refreshWakewordStatus, 2000);
    } else if (!data.running && wakewordPoll) {
      clearInterval(wakewordPoll);
      wakewordPoll = null;
    }
  }

  document.getElementById("audioWakewordStartBtn")?.addEventListener("click", async () => {
    const res = await fetch("/api/audio/wakeword/start", { method: "POST" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || data.message?.startsWith("ERROR:")) {
      const el = document.getElementById("audioWakewordStatus");
      if (el) el.textContent = data.message || `Start failed (${res.status})`;
    }
    refreshWakewordStatus();
  });
  document.getElementById("audioWakewordStopBtn")?.addEventListener("click", async () => {
    await fetch("/api/audio/wakeword/stop", { method: "POST" });
    refreshWakewordStatus();
  });
  refreshWakewordStatus();
}

async function startLiveRecord(statusEl) {
  stopVuPolling();
  setAudioBusy(true);
  statusEl.textContent = "Live recording…";
  const form = new FormData();
  form.append("source", selectedInputSource());
  const res = await fetch("/api/audio/record/live/start", { method: "POST", body: form });
  const data = await res.json();
  if (!data.ok) {
    statusEl.textContent = data.message || "Live start failed";
    setAudioBusy(false);
    return;
  }
  liveSessionId = data.session_id;
  vuTimer = setInterval(() => pollLiveSession(statusEl), 400);
}

async function stopLiveRecord(statusEl) {
  if (!liveSessionId) return;
  stopVuPolling();
  statusEl.textContent = "Stopping…";
  const form = new FormData();
  form.append("session_id", liveSessionId);
  form.append("transcribe", "1");
  form.append("model", selectedWhisperModel());
  form.append("language", document.getElementById("audioWhisperLang")?.value || "en");
  liveSessionId = "";
  const res = await fetch("/api/audio/record/live/stop", { method: "POST", body: form });
  const data = await res.json();
  setAudioBusy(false);
  if (typeof window.finishAudioRecording === "function") {
    await window.finishAudioRecording(data, true);
  }
}
