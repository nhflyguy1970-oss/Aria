/** Jarvis Audio panel — record, transcribe, TTS, edit, waveform, MusicGen */

const audioContent = document.getElementById("audioContent");
const audioStatusBar = document.getElementById("audioStatusBar");

let waveState = { path: "", duration: 0, peaks: [], trimStart: 0, trimEnd: 1 };
let pttSessionId = "";
let pttActive = false;
let audioLastPath = "";
let audioPanelMounted = false;

function audioFileUrl(path) {
  return `/api/audio/file?path=${encodeURIComponent(path)}&t=${Date.now()}`;
}

function escapeHtml(t) {
  const d = document.createElement("div");
  d.textContent = t;
  return d.innerHTML;
}

function renderInputSourceOptions(sources, active) {
  const opts = [];
  for (const s of sources || []) {
    const sel = s.name === active ? " selected" : "";
    const tag = s.is_usb_mic ? " (webcam/USB)" : "";
    opts.push(
      `<option value="${escapeHtml(s.name)}"${sel}>${escapeHtml(s.label || s.name)}${escapeHtml(tag)}</option>`
    );
  }
  return opts.join("");
}

function renderOutputSinkOptions(sinks, active) {
  const opts = [];
  for (const s of sinks || []) {
    const sel = s.name === active ? " selected" : "";
    const tag = s.is_digital ? " · TOSLink" : s.is_creative ? " · analog" : "";
    opts.push(
      `<option value="${escapeHtml(s.name)}"${sel}>${escapeHtml(s.label || s.name)}${escapeHtml(tag)}</option>`
    );
  }
  return opts.join("");
}

function renderRecentList(items, emptyLabel, category = "") {
  if (!items?.length) return `<p class="audio-empty">${emptyLabel}</p>`;
  return `<ul class="audio-recent">${items.map((f) =>
    `<li class="audio-recent-item" draggable="true" data-path="${escapeHtml(f.path)}" data-category="${escapeHtml(category)}">
      <button type="button" class="audio-recent-btn" data-path="${escapeHtml(f.path)}" title="Play in player">${escapeHtml(f.name)}</button>
      <button type="button" class="audio-recent-del" data-path="${escapeHtml(f.path)}" data-category="${escapeHtml(category)}" title="Delete" aria-label="Delete ${escapeHtml(f.name)}">×</button>
    </li>`
  ).join("")}</ul>`;
}

async function loadAudioIntoPlayer(path, transcript = null) {
  if (!path) return;
  setAudioLastPath(path);
  showPlayback(path, transcript);
  await loadWaveform(path);
}

function selectedInputSource() {
  return document.getElementById("audioInputSource")?.value || "";
}

function selectedOutputSink() {
  return document.getElementById("audioOutputSink")?.value || "";
}

function selectedWhisperModel() {
  return document.getElementById("audioWhisperModel")?.value || "base";
}

function getTranscriptText() {
  return document.getElementById("audioTranscript")?.textContent?.trim() || "";
}

async function loadAudioStatus() {
  if (!audioStatusBar) return null;
  try {
    const res = await fetch("/api/audio/status");
    const data = await res.json();
    const d = data.devices || {};
    const tts = data.tts_engine || "none";
    const mix = d.creative_mixer || {};
    const micLabel = (d.input_source || "default input").split(".").pop().slice(0, 28);
    const outLabel = (d.output_sinks || []).find((s) => s.name === d.output_sink)?.label
      || (d.output_digital ? "TOSLink" : (d.output_sink || "output")).split(".").pop().slice(0, 28);
    const capVol = data.capture_volume || "100%";
    const route = data.mic_routing || d.mic_routing || {};
    const hw = route.hardware_input_source || mix.input_source || "";
    const routeTag = route.routing_ok === false ? " ⚠" : route.routing_ok ? " ✓" : "";
    let musicTag = "";
    try {
      const ms = await (await fetch("/api/audio/music/status")).json();
      musicTag = ms.installed ? ` · ♫ ${escapeHtml(ms.backend || "MusicGen")}` : "";
    } catch (_) { /* optional */ }
    audioStatusBar.innerHTML = `
      <span class="audio-stat">${data.whisper_cli ? "✓" : "✗"} Whisper (${escapeHtml(data.whisper_model || "base")})</span>
      <span class="audio-stat">${data.ffmpeg ? "✓" : "✗"} ffmpeg</span>
      <span class="audio-stat">${tts === "piper" ? "✓ Piper" : tts === "espeak" ? "espeak" : "✗ TTS"}${musicTag}</span>
      <span class="audio-stat" title="${escapeHtml(d.output_sink || "")}">🔊 ${escapeHtml(outLabel)}</span>
      <span class="audio-stat" title="${escapeHtml(d.input_source || "")}">🎤 ${escapeHtml(hw || micLabel)} · ${escapeHtml(capVol)}${routeTag}</span>`;
    return data;
  } catch (_) {
    audioStatusBar.textContent = "Could not load audio status.";
    return null;
  }
}

async function refreshRecentLists() {
  const grid = document.getElementById("audioRecentGrid");
  if (!grid) return;
  try {
    const recent = await (await fetch("/api/audio/recent")).json();
    grid.innerHTML = `
      <div><h4>Recent recordings</h4>${renderRecentList(recent.recordings, "No recordings yet.", "recordings")}</div>
      <div><h4>Generated speech</h4>${renderRecentList(recent.generated, "No generated speech yet.", "generated")}</div>
      <div><h4>Edited files</h4>${renderRecentList(recent.edited, "No edits yet.", "edited")}</div>
      <div><h4>Music</h4>${renderRecentList(recent.music, "No music yet.", "music")}</div>
      <div><h4>Songs</h4>${renderRecentList(recent.songs, "No songs yet.", "songs")}</div>`;
    bindRecentButtons(grid);
    bindPlayerDropZone();
  } catch (_) { /* keep existing list */ }
}

function bindRecentButtons(root) {
  root.querySelectorAll(".audio-recent-item").forEach((item) => {
    item.addEventListener("dragstart", (e) => {
      const path = item.dataset.path;
      if (!path) return;
      e.dataTransfer.setData("text/plain", path);
      e.dataTransfer.effectAllowed = "copy";
      item.classList.add("dragging");
    });
    item.addEventListener("dragend", () => item.classList.remove("dragging"));
  });
  root.querySelectorAll(".audio-recent-btn").forEach((btn) => {
    btn.onclick = async () => {
      await loadAudioIntoPlayer(btn.dataset.path, null);
      await playOnSpeakers(btn.dataset.path);
    };
  });
  root.querySelectorAll(".audio-recent-del").forEach((btn) => {
    btn.onclick = async (e) => {
      e.stopPropagation();
      const path = btn.dataset.path;
      const category = btn.dataset.category || "";
      if (!path) return;
      if (!confirm(`Delete ${path.split("/").pop()}?`)) return;
      const form = new FormData();
      form.append("path", path);
      form.append("category", category);
      const res = await fetch("/api/audio/delete", { method: "POST", body: form });
      const data = await res.json();
      if (!data.ok) {
        alert(data.message || "Delete failed");
        return;
      }
      if (audioLastPath === path) {
        showPlayback("", null);
        document.getElementById("audioWaveWrap")?.classList.add("hidden");
      }
      refreshRecentLists();
    };
  });
}

function bindPlayerDropZone() {
  const zone = document.getElementById("audioPlayerDropZone");
  if (!zone || zone.dataset.bound === "1") return;
  zone.dataset.bound = "1";
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", (e) => {
    if (!zone.contains(e.relatedTarget)) zone.classList.remove("drag-over");
  });
  zone.addEventListener("drop", async (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const path = e.dataTransfer.getData("text/plain");
    if (path) await loadAudioIntoPlayer(path, null);
  });
}

function setAudioLastPath(path) {
  audioLastPath = path || "";
  setEditPath(audioLastPath);
}

function showPlayback(path, transcript) {
  const preview = document.getElementById("audioPreview");
  const transcriptEl = document.getElementById("audioTranscript");
  const actions = document.getElementById("audioTranscriptActions");
  if (path) {
    audioLastPath = path;
    if (preview) {
      preview.src = audioFileUrl(path);
      preview.load();
      preview.classList.remove("hidden");
    }
  }
  if (transcriptEl) {
    if (transcript) {
      transcriptEl.textContent = transcript;
      transcriptEl.classList.remove("hidden");
      actions?.classList.remove("hidden");
    } else {
      transcriptEl.classList.add("hidden");
      transcriptEl.textContent = "";
      actions?.classList.add("hidden");
    }
  }
  const playBtn = document.getElementById("audioPlaySpeakersBtn");
  playBtn?.classList.toggle("hidden", !path);
}

function setEditPath(path) {
  const el = document.getElementById("audioEditPath");
  if (el && path) el.value = path;
  const wavePath = document.getElementById("audioWavePath");
  if (wavePath && path) wavePath.textContent = path.split("/").pop();
}

async function playOnSpeakers(path) {
  if (!path) return;
  const form = new FormData();
  form.append("path", path);
  await fetch("/api/audio/play", { method: "POST", body: form });
}

function formatPeak(peak) {
  if (peak == null || Number.isNaN(peak)) return "";
  return ` (peak ${peak.toFixed(1)} dB)`;
}

function updateRecordModeUi() {
  const mode = document.getElementById("audioRecordMode")?.value || "timed";
  document.getElementById("audioTimedRow")?.classList.toggle("hidden", mode !== "timed");
  document.getElementById("audioVadRow")?.classList.toggle("hidden", mode !== "vad");
  document.getElementById("audioPttRow")?.classList.toggle("hidden", mode !== "ptt");
  document.getElementById("audioLiveRow")?.classList.toggle("hidden", mode !== "live");
}

function drawWaveform() {
  const canvas = document.getElementById("audioWaveCanvas");
  if (!canvas || !waveState.peaks?.length) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "var(--wave-bg, #1a1d24)";
  ctx.fillRect(0, 0, w, h);
  const peaks = waveState.peaks;
  const barW = w / peaks.length;
  const trimL = waveState.trimStart * w;
  const trimR = waveState.trimEnd * w;
  ctx.fillStyle = "rgba(80, 120, 200, 0.25)";
  ctx.fillRect(trimL, 0, trimR - trimL, h);
  ctx.fillStyle = "var(--wave-bar, #6b9fff)";
  for (let i = 0; i < peaks.length; i++) {
    const x = i * barW;
    const bh = Math.max(1, peaks[i] * (h - 8));
    ctx.fillRect(x, (h - bh) / 2, Math.max(1, barW - 1), bh);
  }
  ctx.fillStyle = "var(--wave-handle, #f0a030)";
  ctx.fillRect(trimL - 2, 0, 4, h);
  ctx.fillRect(trimR - 2, 0, 4, h);
  const trimInfo = document.getElementById("audioTrimInfo");
  if (trimInfo && waveState.duration) {
    const s = (waveState.trimStart * waveState.duration).toFixed(2);
    const e = (waveState.trimEnd * waveState.duration).toFixed(2);
    trimInfo.textContent = `Trim: ${s}s – ${e}s`;
  }
}

async function loadWaveform(path) {
  if (!path) return;
  waveState = { path, duration: 0, peaks: [], trimStart: 0, trimEnd: 1 };
  const wrap = document.getElementById("audioWaveWrap");
  try {
    const res = await fetch(`/api/audio/waveform?path=${encodeURIComponent(path)}&samples=240`);
    const data = await res.json();
    if (!data.ok) {
      wrap?.classList.add("hidden");
      return;
    }
    waveState.duration = data.duration || 0;
    waveState.peaks = data.peaks || [];
    wrap?.classList.remove("hidden");
    drawWaveform();
  } catch (_) {
    wrap?.classList.add("hidden");
  }
}

function bindWaveformCanvas() {
  const canvas = document.getElementById("audioWaveCanvas");
  if (!canvas) return;
  let drag = null;
  const posToFrac = (clientX) => {
    const rect = canvas.getBoundingClientRect();
    return Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
  };
  canvas.onmousedown = (e) => {
    if (!waveState.peaks.length) return;
    const f = posToFrac(e.clientX);
    const dl = Math.abs(f - waveState.trimStart);
    const dr = Math.abs(f - waveState.trimEnd);
    drag = dl <= dr ? "start" : "end";
    if (drag === "start") waveState.trimStart = Math.min(f, waveState.trimEnd - 0.01);
    else waveState.trimEnd = Math.max(f, waveState.trimStart + 0.01);
    drawWaveform();
  };
  canvas.onmousemove = (e) => {
    if (!drag) return;
    const f = posToFrac(e.clientX);
    if (drag === "start") waveState.trimStart = Math.max(0, Math.min(f, waveState.trimEnd - 0.01));
    else waveState.trimEnd = Math.min(1, Math.max(f, waveState.trimStart + 0.01));
    drawWaveform();
  };
  canvas.onmouseup = () => { drag = null; };
  canvas.onmouseleave = () => { drag = null; };
}

async function loadAudioPanel() {
  if (!audioContent) return;
  const [recentRes, statusData, musicStatusRes] = await Promise.all([
    fetch("/api/audio/recent"),
    loadAudioStatus(),
    fetch("/api/audio/music/status"),
  ]);
  const recent = await recentRes.json();
  const musicStatus = await musicStatusRes.json().catch(() => ({ installed: false }));
  const d = statusData?.devices || {};
  const sources = statusData?.input_sources || d.input_sources || [];
  const sinks = statusData?.output_sinks || d.output_sinks || [];
  const activeSource = d.input_source || "";
  const activeSink = d.output_sink || "";
  const capVol = statusData?.capture_volume || "100%";
  const routing = statusData?.mic_routing || d.mic_routing || {};
  const activeProfile = routing.profile || "rear";
  const profiles = statusData?.mic_profiles || {};
  const whisperModels = statusData?.whisper_models || ["tiny", "base", "small", "medium", "large"];
  const activeModel = statusData?.whisper_model || "base";
  const whisperLangs = statusData?.whisper_languages || ["auto", "en"];
  const activeLang = statusData?.whisper_language || "en";
  const langOpts = whisperLangs.map((l) =>
    `<option value="${escapeHtml(l)}"${l === activeLang ? " selected" : ""}>${escapeHtml(l)}</option>`
  ).join("");
  const piperSpeed = statusData?.piper_speed || 1.0;
  const melodyOk = statusData?.melody_model === true;
  const whisperBackend = statusData?.whisper_backend || "cli";
  const profileOpts = Object.entries(profiles).map(([id, p]) =>
    `<option value="${escapeHtml(id)}"${id === activeProfile ? " selected" : ""}>${escapeHtml(p.label || id)}</option>`
  ).join("");
  const modelOpts = whisperModels.map((m) =>
    `<option value="${escapeHtml(m)}"${m === activeModel ? " selected" : ""}>${escapeHtml(m)}</option>`
  ).join("");
  const routingBanner = routing.routing_ok === false
    ? `<p class="audio-routing-warn">${escapeHtml(routing.routing_hint || "Check alsamixer Input Source.")}</p>`
    : `<p class="audio-hint">${escapeHtml(routing.routing_hint || profiles[activeProfile]?.hint || "")}</p>`;

  audioContent.innerHTML = `
    <section class="audio-section">
      <h3>Record &amp; transcribe</h3>
      <p class="audio-hint">Chat mic uses browser speech-to-text. This tab uses <strong>${escapeHtml(whisperBackend)}</strong> locally.</p>
      ${routingBanner}
      <div class="audio-row">
        <label>Whisper model
          <select id="audioWhisperModel" class="audio-source-select">${modelOpts}</select>
        </label>
        <label>Language
          <select id="audioWhisperLang" class="audio-source-select">${langOpts}</select>
        </label>
        <label>Piper speed
          <select id="audioPiperSpeed" class="audio-source-select">
            ${[0.8, 0.9, 1.0, 1.1, 1.2].map((s) =>
              `<option value="${s}"${Math.abs(s - piperSpeed) < 0.05 ? " selected" : ""}>${s}×</option>`
            ).join("")}
          </select>
        </label>
        <label>Mic setup
          <select id="audioMicProfile" class="audio-source-select">${profileOpts || '<option value="rear">Rear desk mic</option><option value="front">Front headset</option>'}</select>
        </label>
      </div>
      <div class="audio-row">
        <label>Microphone
          <select id="audioInputSource" class="audio-source-select">${renderInputSourceOptions(sources, activeSource)}</select>
        </label>
        <label>Output
          <select id="audioOutputSink" class="audio-source-select">${renderOutputSinkOptions(sinks, activeSink)}</select>
        </label>
        <label>PipeWire gain
          <select id="audioCaptureVolume" class="audio-source-select">
            ${["100%", "125%", "150%", "175%", "200%", "250%"].map((v) =>
              `<option value="${v}"${v === capVol ? " selected" : ""}>${v}</option>`
            ).join("")}
          </select>
        </label>
      </div>
      <div class="audio-row">
        <button type="button" id="audioProbeBtn" class="ghost-btn small">Test mic (2s)</button>
      </div>
      <div class="audio-row">
        <label>Record mode
          <select id="audioRecordMode" class="audio-source-select">
            <option value="timed">Fixed duration</option>
            <option value="vad">VAD (trim silence)</option>
            <option value="ptt">Push-to-talk (hold button)</option>
            <option value="live">Live (VU + streaming transcript)</option>
          </select>
        </label>
      </div>
      <div class="audio-row hidden" id="audioLiveRow">
        <button type="button" id="audioLiveStartBtn" class="apply-btn small">Start live record</button>
        <button type="button" id="audioLiveStopBtn" class="ghost-btn small">Stop + transcribe</button>
      </div>
      <div class="audio-row" id="audioTimedRow">
        <label>Duration <input type="number" id="audioRecordSec" min="1" max="120" value="5" /> sec</label>
        <button type="button" id="audioRecordBtn" class="ghost-btn small">Record only</button>
        <button type="button" id="audioRecordTranscribeBtn" class="apply-btn small">Record + transcribe</button>
      </div>
      <div class="audio-row hidden" id="audioVadRow">
        <label>Max <input type="number" id="audioVadMax" min="3" max="120" value="30" /> sec</label>
        <label>Silence <input type="number" id="audioVadSilence" min="0.3" max="3" step="0.1" value="0.8" /> sec</label>
        <button type="button" id="audioVadBtn" class="apply-btn small">Record (VAD)</button>
        <button type="button" id="audioVadTranscribeBtn" class="apply-btn small">VAD + transcribe</button>
      </div>
      <div class="audio-row hidden" id="audioPttRow">
        <button type="button" id="audioPttBtn" class="apply-btn small audio-ptt-btn">Hold to talk</button>
        <span class="audio-hint">Release to stop · uses Sound Blaster mic</span>
      </div>
      <div id="audioRecordStatus" class="audio-msg" aria-live="polite"></div>
      <div id="audioPlayerDropZone" class="audio-player-drop" title="Drag a file from the library below to play it here">
        <p class="audio-hint audio-drop-hint">Built-in player — drag files here from Recordings / Songs below</p>
        <audio id="audioPreview" controls class="audio-player hidden"></audio>
        <button type="button" id="audioPlaySpeakersBtn" class="ghost-btn small hidden">Play on Sound Blaster</button>
      </div>
      <div id="audioTranscriptActions" class="audio-transcript-actions hidden">
        <button type="button" id="audioCopyTranscriptBtn" class="ghost-btn small">Copy</button>
        <button type="button" id="audioSendChatBtn" class="ghost-btn small">Send to chat</button>
        <button type="button" id="audioJournalBtn" class="ghost-btn small">Add to journal</button>
        <button type="button" id="audioSummarizeBtn" class="ghost-btn small">Summarize</button>
      </div>
      <pre id="audioTranscript" class="audio-transcript hidden"></pre>
      <pre id="audioSummary" class="audio-summary hidden"></pre>
    </section>

    <section class="audio-section">
      <h3>Waveform &amp; trim</h3>
      <p class="audio-hint">Load a recording, drag orange handles, then Apply trim.</p>
      <div id="audioWaveWrap" class="audio-wave-wrap hidden">
        <p id="audioWavePath" class="audio-hint"></p>
        <canvas id="audioWaveCanvas" width="640" height="80" class="audio-wave-canvas"></canvas>
        <p id="audioTrimInfo" class="audio-hint"></p>
        <div class="audio-row">
          <button type="button" id="audioTrimApplyBtn" class="apply-btn small">Apply trim</button>
          <button type="button" id="audioNormalizeBtn" class="ghost-btn small">Normalize</button>
        </div>
      </div>
    </section>

    <section class="audio-section">
      <h3>Edit audio</h3>
      <div class="audio-row">
        <input type="text" id="audioEditPath" placeholder="Path to audio file…" class="audio-path-input" />
        <input type="text" id="audioEditInstruction" placeholder="e.g. fade in, make louder, trim first 5s" class="audio-path-input" />
        <button type="button" id="audioEditBtn" class="apply-btn small">Edit</button>
      </div>
      <div class="audio-row">
        <label>Convert to
          <input type="text" id="audioConvertOut" placeholder="data/audio/edited/out.mp3" class="audio-path-input" />
        </label>
        <button type="button" id="audioConvertBtn" class="ghost-btn small">Convert</button>
      </div>
    </section>

    <section class="audio-section">
      <h3>Transcribe file</h3>
      <div class="audio-row">
        <input type="file" id="audioUploadFile" accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac,.webm,.mp4" />
        <button type="button" id="audioTranscribeUploadBtn" class="apply-btn small">Transcribe upload</button>
      </div>
      <div class="audio-row">
        <input type="text" id="audioTranscribePath" placeholder="Or path under data/…" class="audio-path-input" />
        <button type="button" id="audioTranscribePathBtn" class="ghost-btn small">Transcribe path</button>
      </div>
    </section>

    <section class="audio-section">
      <h3>Text to speech</h3>
      <textarea id="audioTtsText" rows="3" placeholder="Text for Piper or espeak…"></textarea>
      <div class="audio-row">
        <button type="button" id="audioTtsBtn" class="apply-btn small">Generate speech</button>
        <button type="button" id="audioTtsPlayBtn" class="ghost-btn small">Generate + play</button>
      </div>
      <audio id="audioTtsPreview" controls class="audio-player hidden"></audio>
    </section>

    ${typeof renderSongStudioSection === "function" ? renderSongStudioSection(melodyOk) : ""}
    ${typeof renderAdvancedSection === "function" ? renderAdvancedSection() : ""}

    <section class="audio-section">
      <h3>Search transcripts</h3>
      <div class="audio-row">
        <input type="search" id="audioSearchQ" placeholder="Search indexed transcripts…" class="audio-path-input" />
        <button type="button" id="audioSearchBtn" class="ghost-btn small">Search</button>
      </div>
      <div id="audioSearchResults" class="audio-search-results"></div>
    </section>

    <section class="audio-section">
      <h3>Batch transcribe</h3>
      <textarea id="audioBatchPaths" rows="3" placeholder="One path per line under data/…"></textarea>
      <button type="button" id="audioBatchBtn" class="ghost-btn small">Transcribe all</button>
      <pre id="audioBatchOut" class="audio-transcript hidden"></pre>
    </section>

    <section class="audio-section">
      <h3>MusicGen</h3>
      <p class="audio-hint" id="audioMusicHint">${musicStatus.installed ? `Generate music (${escapeHtml(musicStatus.backend || "ready")}, GPU recommended).` : `Not installed — ${escapeHtml(musicStatus.hint || "pip install transformers scipy accelerate")}`}</p>
      <textarea id="audioMusicPrompt" rows="2" placeholder="Calm piano, 90 BPM…"></textarea>
      <div class="audio-row">
        <label>Duration <input type="number" id="audioMusicDur" min="5" max="30" value="10" /> sec</label>
        <button type="button" id="audioMusicBtn" class="apply-btn small" ${musicStatus.installed ? "" : "disabled"}>Generate music</button>
      </div>
      <audio id="audioMusicPreview" controls class="audio-player hidden"></audio>
    </section>

    <section class="audio-section audio-recent-grid" id="audioRecentGrid">
      <p class="audio-hint">Drag any file to the player above, or click to load. × deletes the file.</p>
      <div><h4>Recent recordings</h4>${renderRecentList(recent.recordings, "No recordings yet.", "recordings")}</div>
      <div><h4>Generated speech</h4>${renderRecentList(recent.generated, "No generated speech yet.", "generated")}</div>
      <div><h4>Edited files</h4>${renderRecentList(recent.edited, "No edits yet.", "edited")}</div>
      <div><h4>Music</h4>${renderRecentList(recent.music, "No music yet.", "music")}</div>
      <div><h4>Songs</h4>${renderRecentList(recent.songs, "No songs yet.", "songs")}</div>
    </section>`;

  const statusEl = document.getElementById("audioRecordStatus");
  const playSpeakersBtn = document.getElementById("audioPlaySpeakersBtn");

  document.getElementById("audioRecordMode")?.addEventListener("change", updateRecordModeUi);
  updateRecordModeUi();

  document.getElementById("audioWhisperModel")?.addEventListener("change", async () => {
    const form = new FormData();
    form.append("model", selectedWhisperModel());
    await fetch("/api/audio/whisper-model", { method: "POST", body: form });
    loadAudioStatus();
  });

  document.getElementById("audioWhisperLang")?.addEventListener("change", async () => {
    const form = new FormData();
    form.append("language", document.getElementById("audioWhisperLang")?.value || "en");
    await fetch("/api/audio/whisper-language", { method: "POST", body: form });
  });

  document.getElementById("audioPiperSpeed")?.addEventListener("change", async () => {
    const form = new FormData();
    form.append("speed", document.getElementById("audioPiperSpeed")?.value || "1");
    await fetch("/api/audio/piper-speed", { method: "POST", body: form });
  });

  document.getElementById("audioMicProfile")?.addEventListener("change", async () => {
    const profile = document.getElementById("audioMicProfile")?.value || "rear";
    const form = new FormData();
    form.append("profile", profile);
    const res = await fetch("/api/audio/mic-profile", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "Profile failed";
      return;
    }
    statusEl.textContent = data.hint || `Profile: ${data.label}`;
    loadAudioPanel();
  });

  document.getElementById("audioInputSource")?.addEventListener("change", async () => {
    const form = new FormData();
    form.append("source", selectedInputSource());
    await fetch("/api/audio/input-source", { method: "POST", body: form });
    loadAudioStatus();
    statusEl.textContent = `Input saved: ${selectedInputSource().split(".").pop()}`;
  });

  document.getElementById("audioOutputSink")?.addEventListener("change", async () => {
    const form = new FormData();
    form.append("sink", selectedOutputSink());
    const res = await fetch("/api/audio/output-sink", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "Output failed";
      return;
    }
    statusEl.textContent = `Output saved: ${selectedOutputSink().split(".").pop()}`;
    loadAudioPanel();
  });

  document.getElementById("audioCaptureVolume")?.addEventListener("change", async () => {
    const vol = document.getElementById("audioCaptureVolume")?.value || "100%";
    const form = new FormData();
    form.append("volume", vol);
    form.append("source", selectedInputSource());
    const res = await fetch("/api/audio/capture-volume", { method: "POST", body: form });
    const data = await res.json();
    statusEl.textContent = `PipeWire capture gain → ${data.capture_volume || vol}`;
    loadAudioStatus();
  });

  playSpeakersBtn?.addEventListener("click", () => playOnSpeakers(audioLastPath));

  document.getElementById("audioProbeBtn")?.addEventListener("click", async () => {
    statusEl.textContent = "Testing mic (speak now)…";
    const form = new FormData();
    form.append("duration", "2");
    form.append("source", selectedInputSource());
    const res = await fetch("/api/audio/probe-capture", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "Probe failed";
      return;
    }
    const ok = data.likely_ok;
    const routeWarn = data.mic_routing?.routing_ok === false
      ? ` — ${data.mic_routing.routing_hint}`
      : "";
    statusEl.textContent = ok
      ? `Mic OK — peak ${data.peak_db?.toFixed(1)} dB (PipeWire ${data.pipewire_volume})`
      : `Mic weak — peak ${data.peak_db?.toFixed(1)} dB.${routeWarn || " Check alsamixer Input Source and Mic Boost."}`;
  });

  async function finishRecording(data, transcribed) {
    if (!data.ok) {
      statusEl.textContent = data.message || "Failed";
      if (data.audio_path) {
        setAudioLastPath(data.audio_path);
        showPlayback(data.audio_path, null);
        playSpeakersBtn?.classList.remove("hidden");
        await loadWaveform(data.audio_path);
      }
      return;
    }
    setAudioLastPath(data.audio_path);
    let transcript = null;
    if (transcribed) {
      if (data.transcript_error) {
        statusEl.textContent = `Recorded${formatPeak(data.peak_db)} — transcribe failed`;
        showPlayback(data.audio_path, null);
        playSpeakersBtn?.classList.remove("hidden");
        await loadWaveform(data.audio_path);
        refreshRecentLists();
        return;
      }
      transcript = data.transcript?.trim() ? data.transcript : "(no speech detected)";
      statusEl.textContent = data.transcript?.trim()
        ? `Done${formatPeak(data.peak_db)}`
        : `Recorded${formatPeak(data.peak_db)} but no speech detected`;
    } else {
      statusEl.textContent = `Done${formatPeak(data.peak_db)}`;
    }
    showPlayback(data.audio_path, transcript);
    playSpeakersBtn?.classList.remove("hidden");
    await loadWaveform(data.audio_path);
    refreshRecentLists();
    if (transcript && data.audio_path) {
      const sf = new FormData();
      sf.append("audio_path", data.audio_path);
      sf.append("transcript", transcript);
      fetch("/api/audio/session", { method: "POST", body: sf });
    }
  }

  document.getElementById("audioRecordBtn")?.addEventListener("click", async () => {
    const sec = document.getElementById("audioRecordSec")?.value || "5";
    statusEl.textContent = "Recording…";
    setAudioBusy(true);
    playSpeakersBtn?.classList.add("hidden");
    const form = new FormData();
    form.append("duration", sec);
    form.append("source", selectedInputSource());
    const res = await fetch("/api/audio/record", { method: "POST", body: form });
    await finishRecording(await res.json(), false);
    setAudioBusy(false);
  });

  document.getElementById("audioRecordTranscribeBtn")?.addEventListener("click", async () => {
    const sec = document.getElementById("audioRecordSec")?.value || "5";
    statusEl.textContent = "Recording + transcribing…";
    playSpeakersBtn?.classList.add("hidden");
    const form = new FormData();
    form.append("duration", sec);
    form.append("source", selectedInputSource());
    form.append("model", selectedWhisperModel());
    form.append("language", document.getElementById("audioWhisperLang")?.value || "en");
    setAudioBusy(true);
    const res = await fetch("/api/audio/record-transcribe", { method: "POST", body: form });
    await finishRecording(await res.json(), true);
    setAudioBusy(false);
  });

  async function runVad(transcribe) {
    statusEl.textContent = transcribe ? "VAD recording + transcribing…" : "VAD recording…";
    playSpeakersBtn?.classList.add("hidden");
    const form = new FormData();
    form.append("max_duration", document.getElementById("audioVadMax")?.value || "30");
    form.append("min_silence", document.getElementById("audioVadSilence")?.value || "0.8");
    form.append("source", selectedInputSource());
    form.append("transcribe", transcribe ? "1" : "0");
    form.append("model", selectedWhisperModel());
    const res = await fetch("/api/audio/record-vad", { method: "POST", body: form });
    await finishRecording(await res.json(), transcribe);
  }

  document.getElementById("audioVadBtn")?.addEventListener("click", () => runVad(false));
  document.getElementById("audioVadTranscribeBtn")?.addEventListener("click", () => runVad(true));

  const pttBtn = document.getElementById("audioPttBtn");
  async function pttStart() {
    if (pttActive) return;
    pttActive = true;
    pttBtn?.classList.add("active");
    statusEl.textContent = "Recording (hold)…";
    const form = new FormData();
    form.append("source", selectedInputSource());
    const res = await fetch("/api/audio/record/ptt/start", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "PTT start failed";
      pttActive = false;
      pttBtn?.classList.remove("active");
      return;
    }
    pttSessionId = data.session_id;
  }

  async function pttStop(transcribe) {
    if (!pttActive || !pttSessionId) return;
    pttActive = false;
    pttBtn?.classList.remove("active");
    statusEl.textContent = transcribe ? "Processing + transcribing…" : "Processing…";
    const form = new FormData();
    form.append("session_id", pttSessionId);
    form.append("transcribe", transcribe ? "1" : "0");
    form.append("model", selectedWhisperModel());
    pttSessionId = "";
    const res = await fetch("/api/audio/record/ptt/stop", { method: "POST", body: form });
    await finishRecording(await res.json(), transcribe);
  }

  if (pttBtn) {
    pttBtn.addEventListener("mousedown", (e) => { e.preventDefault(); pttStart(); });
    pttBtn.addEventListener("mouseup", () => pttStop(true));
    pttBtn.addEventListener("mouseleave", () => { if (pttActive) pttStop(true); });
    pttBtn.addEventListener("touchstart", (e) => { e.preventDefault(); pttStart(); }, { passive: false });
    pttBtn.addEventListener("touchend", (e) => { e.preventDefault(); pttStop(true); });
  }

  document.getElementById("audioCopyTranscriptBtn")?.addEventListener("click", async () => {
    const text = getTranscriptText();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      statusEl.textContent = "Transcript copied";
    } catch (_) {
      statusEl.textContent = "Copy failed";
    }
  });

  document.getElementById("audioSendChatBtn")?.addEventListener("click", () => {
    const text = getTranscriptText();
    if (!text || !window.jarvisSendToChat) return;
    window.jarvisSendToChat(text);
    statusEl.textContent = "Sent to chat";
  });

  document.getElementById("audioJournalBtn")?.addEventListener("click", async () => {
    const text = getTranscriptText();
    if (!text) return;
    const form = new FormData();
    form.append("text", text);
    form.append("audio_path", audioLastPath || "");
    form.append("bullet_type", "note");
    const res = await fetch("/api/audio/journal-with-audio", { method: "POST", body: form });
    const data = await res.json();
    statusEl.textContent = data.ok ? "Added to today's journal" : (data.message || "Journal failed");
  });

  document.getElementById("audioSummarizeBtn")?.addEventListener("click", async () => {
    const path = audioLastPath || document.getElementById("audioEditPath")?.value.trim();
    if (!path) {
      statusEl.textContent = "Record or pick a file first";
      return;
    }
    statusEl.textContent = "Summarizing…";
    const form = new FormData();
    form.append("path", path);
    form.append("model", selectedWhisperModel());
    const res = await fetch("/api/audio/analyze", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "Summarize failed";
      return;
    }
    const summaryEl = document.getElementById("audioSummary");
    if (summaryEl) {
      summaryEl.textContent = data.summary || "";
      summaryEl.classList.remove("hidden");
    }
    if (data.transcript) showPlayback(path, data.transcript);
    statusEl.textContent = "Summary ready";
  });

  document.getElementById("audioTrimApplyBtn")?.addEventListener("click", async () => {
    if (!waveState.path || !waveState.duration) return;
    const start = waveState.trimStart * waveState.duration;
    const end = waveState.trimEnd * waveState.duration;
    statusEl.textContent = "Trimming…";
    const form = new FormData();
    form.append("path", waveState.path);
    form.append("start_sec", String(start));
    form.append("end_sec", String(end));
    const res = await fetch("/api/audio/edit", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "Trim failed";
      return;
    }
    setAudioLastPath(data.audio_path);
    showPlayback(data.audio_path, null);
    statusEl.textContent = "Trim saved";
    await loadWaveform(data.audio_path);
    refreshRecentLists();
  });

  document.getElementById("audioNormalizeBtn")?.addEventListener("click", async () => {
    const path = waveState.path || lastPath;
    if (!path) return;
    const form = new FormData();
    form.append("path", path);
    form.append("normalize", "1");
    const res = await fetch("/api/audio/edit", { method: "POST", body: form });
    const data = await res.json();
    statusEl.textContent = data.ok ? "Normalized" : (data.message || "Failed");
    if (data.ok) {
      setAudioLastPath(data.audio_path);
      showPlayback(data.audio_path, null);
      refreshRecentLists();
    }
  });

  document.getElementById("audioEditBtn")?.addEventListener("click", async () => {
    const path = document.getElementById("audioEditPath")?.value.trim();
    const instruction = document.getElementById("audioEditInstruction")?.value.trim();
    if (!path) return;
    statusEl.textContent = "Editing…";
    const form = new FormData();
    form.append("path", path);
    form.append("instruction", instruction);
    const res = await fetch("/api/audio/edit", { method: "POST", body: form });
    const data = await res.json();
    statusEl.textContent = data.ok ? `Saved: ${data.audio_path}` : (data.message || "Edit failed");
    if (data.ok) {
      setAudioLastPath(data.audio_path);
      showPlayback(data.audio_path, null);
      refreshRecentLists();
    }
  });

  document.getElementById("audioConvertBtn")?.addEventListener("click", async () => {
    const path = document.getElementById("audioEditPath")?.value.trim();
    const output = document.getElementById("audioConvertOut")?.value.trim();
    if (!path || !output) {
      statusEl.textContent = "Need source path and output path";
      return;
    }
    const form = new FormData();
    form.append("path", path);
    form.append("output", output);
    const res = await fetch("/api/audio/convert", { method: "POST", body: form });
    const data = await res.json();
    statusEl.textContent = data.ok ? `Converted: ${data.audio_path}` : (data.message || "Convert failed");
    if (data.ok) refreshRecentLists();
  });

  document.getElementById("audioTranscribeUploadBtn")?.addEventListener("click", async () => {
    const file = document.getElementById("audioUploadFile")?.files?.[0];
    if (!file) {
      statusEl.textContent = "Choose a file first";
      return;
    }
    statusEl.textContent = "Transcribing…";
    const form = new FormData();
    form.append("file", file);
    form.append("model", selectedWhisperModel());
    const res = await fetch("/api/audio/transcribe-upload", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "Transcribe failed";
      return;
    }
    setAudioLastPath(data.path);
    statusEl.textContent = "Transcript ready";
    showPlayback(data.path, data.transcript);
    await loadWaveform(data.path);
  });

  document.getElementById("audioTranscribePathBtn")?.addEventListener("click", async () => {
    const path = document.getElementById("audioTranscribePath")?.value.trim();
    if (!path) return;
    statusEl.textContent = "Transcribing…";
    const form = new FormData();
    form.append("path", path);
    form.append("model", selectedWhisperModel());
    const res = await fetch("/api/audio/transcribe", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "Transcribe failed";
      return;
    }
    setAudioLastPath(path);
    statusEl.textContent = "Transcript ready";
    showPlayback(path, data.transcript);
    await loadWaveform(path);
  });

  async function runTts(play) {
    const text = document.getElementById("audioTtsText")?.value.trim();
    if (!text) return;
    statusEl.textContent = "Generating speech…";
    const form = new FormData();
    form.append("text", text);
    form.append("auto_play", play ? "1" : "0");
    const res = await fetch("/api/audio/generate", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "TTS failed";
      return;
    }
    statusEl.textContent = play ? "Playing on Sound Blaster…" : `Saved: ${data.audio_path}`;
    const ttsPreview = document.getElementById("audioTtsPreview");
    if (ttsPreview && data.audio_path) {
      ttsPreview.src = audioFileUrl(data.audio_path);
      ttsPreview.load();
      ttsPreview.classList.remove("hidden");
    }
    refreshRecentLists();
  }

  document.getElementById("audioTtsBtn")?.addEventListener("click", () => runTts(false));
  document.getElementById("audioTtsPlayBtn")?.addEventListener("click", () => runTts(true));

  document.getElementById("audioMusicBtn")?.addEventListener("click", async () => {
    const prompt = document.getElementById("audioMusicPrompt")?.value.trim();
    if (!prompt) return;
    statusEl.textContent = "Queueing music generation…";
    const form = new FormData();
    form.append("prompt", prompt);
    form.append("duration", document.getElementById("audioMusicDur")?.value || "10");
    form.append("async_job", "1");
    const res = await fetch("/api/audio/music", { method: "POST", body: form });
    const data = await res.json();
    if (!data.ok) {
      statusEl.textContent = data.message || "MusicGen failed";
      return;
    }
    if (data.job_id && typeof window.pollAudioJob === "function") {
      await window.pollAudioJob(data.job_id, statusEl, (result) => {
        const path = result?.audio_path;
        if (!path) return;
        statusEl.textContent = `Saved: ${path}`;
        const mp = document.getElementById("audioMusicPreview");
        if (mp) {
          mp.src = audioFileUrl(path);
          mp.load();
          mp.classList.remove("hidden");
        }
        refreshRecentLists();
      });
      return;
    }
    if (data.audio_path) {
      statusEl.textContent = `Saved: ${data.audio_path}`;
      const mp = document.getElementById("audioMusicPreview");
      if (mp) {
        mp.src = audioFileUrl(data.audio_path);
        mp.load();
        mp.classList.remove("hidden");
      }
      refreshRecentLists();
    }
  });

  document.getElementById("audioSearchBtn")?.addEventListener("click", async () => {
    const q = document.getElementById("audioSearchQ")?.value.trim();
    if (!q) return;
    const res = await fetch(`/api/audio/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    const box = document.getElementById("audioSearchResults");
    if (!box) return;
    box.innerHTML = (data.results || []).map((r) =>
      `<div class="audio-search-hit"><strong>${escapeHtml(r.title || "")}</strong>
        <p>${escapeHtml(r.snippet || "")}</p>
        <button type="button" class="ghost-btn small audio-search-open" data-path="${escapeHtml(r.path)}">Open</button></div>`
    ).join("") || "<p class='audio-empty'>No matches</p>";
    box.querySelectorAll(".audio-search-open").forEach((btn) => {
      btn.onclick = () => {
        setAudioLastPath(btn.dataset.path);
        showPlayback(btn.dataset.path, null);
        loadWaveform(btn.dataset.path);
      };
    });
  });

  document.getElementById("audioBatchBtn")?.addEventListener("click", async () => {
    const paths = document.getElementById("audioBatchPaths")?.value.trim();
    if (!paths) return;
    setAudioBusy(true);
    statusEl.textContent = "Batch transcribing…";
    const form = new FormData();
    form.append("paths", paths);
    form.append("model", selectedWhisperModel());
    form.append("language", document.getElementById("audioWhisperLang")?.value || "en");
    const res = await fetch("/api/audio/batch-transcribe", { method: "POST", body: form });
    const data = await res.json();
    const out = document.getElementById("audioBatchOut");
    if (out) {
      out.textContent = (data.results || []).map((r) =>
        `${r.path}\n${r.ok ? r.transcript : r.transcript}\n---`
      ).join("\n");
      out.classList.remove("hidden");
    }
    statusEl.textContent = "Batch done";
    setAudioBusy(false);
  });

  window.finishAudioRecording = finishRecording;

  bindWaveformCanvas();
  bindRecentButtons(audioContent);
  bindPlayerDropZone();
  if (typeof bindSongStudio === "function") bindSongStudio(statusEl);
  if (typeof bindAdvanced === "function") bindAdvanced(statusEl);

  document.getElementById("audioLiveStartBtn")?.addEventListener("click", () => {
    if (typeof startLiveRecord === "function") startLiveRecord(statusEl);
  });
  document.getElementById("audioLiveStopBtn")?.addEventListener("click", () => {
    if (typeof stopLiveRecord === "function") stopLiveRecord(statusEl);
  });

  try {
    const sess = await (await fetch("/api/audio/session")).json();
    if (sess.session?.audio_path) {
      setAudioLastPath(sess.session.audio_path);
      showPlayback(sess.session.audio_path, sess.session.transcript || null);
      if (sess.session.summary) {
        const summaryEl = document.getElementById("audioSummary");
        if (summaryEl) {
          summaryEl.textContent = sess.session.summary;
          summaryEl.classList.remove("hidden");
        }
      }
      loadWaveform(sess.session.audio_path);
    }
  } catch (_) { /* optional */ }
}

window.initAudio = () => {
  if (audioPanelMounted && audioContent?.querySelector("#audioRecordBtn")) {
    loadAudioStatus();
    refreshRecentLists();
    return;
  }
  audioPanelMounted = true;
  loadAudioPanel();
};
