/** P1 voice bar (#30), duplex (#27), cloud live (#84), WebSocket events */

let _cloudSessionId = null;
let _voiceMuted = false;

function showToast(message, type = "info", ms = 4200) {
  let el = document.getElementById("ariaToast");
  if (!el) {
    el = document.createElement("div");
    el.id = "ariaToast";
    el.className = "aria-toast hidden";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.className = `aria-toast aria-toast--${type}`;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => el.classList.add("hidden"), ms);
}

function isNativeApp() {
  return document.documentElement.classList.contains("jarvis-app");
}

function setVoiceBarState(state) {
  if (_voiceMuted && state !== "muted" && state !== "idle") {
    /* keep muted indicator unless explicitly idle */
  }
  const bar = document.getElementById("voiceBar");
  if (!bar) return;
  const effective = _voiceMuted && state === "speaking" ? "muted" : state;
  bar.dataset.state = effective;
  const label = bar.querySelector(".voice-bar-label");
  const map = {
    idle: "Voice idle",
    listening: "Listening…",
    thinking: "Thinking…",
    speaking: "Speaking…",
    muted: "Muted",
    "cloud-live": "Cloud live",
  };
  if (label) label.textContent = map[effective] || effective;
  document.getElementById("ariaVoiceStrip")?.classList.toggle("voice-strip-active", effective !== "idle");
}

function updateDuplexHint(data) {
  const el = document.getElementById("voiceBarMode");
  if (!el) return;
  const mode = data?.duplex_mode || data?.mode || "half";
  const help = data?.duplex?.help || data?.help || "";
  el.textContent = { off: "Off", half: "Half", full: "Full" }[mode] || mode;
  el.title = help || `Duplex: ${mode}`;
}

function syncMuteButton() {
  const btn = document.getElementById("voiceMuteBtn");
  const speakCb = document.getElementById("speakRepliesToggle");
  if (speakCb) _voiceMuted = !speakCb.checked;
  if (!btn) return;
  btn.textContent = _voiceMuted ? "Muted" : "Speak on";
  btn.classList.toggle("active", _voiceMuted);
  if (_voiceMuted) setVoiceBarState("muted");
}

function dispatchWsEvent(data) {
  window.dispatchEvent(new CustomEvent("jarvis-ws", { detail: data }));
}

let ws;
function connectJobWs() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws/events`);
  ws.onopen = () => {
    window.jarvisWsConnected = true;
  };
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      dispatchWsEvent(data);
      if (data.event === "job_done") {
        const ok = data.ok ? "completed" : "failed";
        showToast(`${data.label || data.job_id || "Job"} ${ok}`, data.ok ? "ok" : "err");
        window.jarvisJobs?.refreshJobCenter?.();
      } else if (data.event === "job_progress") {
        window.jarvisJobs?.onJobProgress?.(data);
      } else if (data.event === "voice_state") {
        const st = data.state || "idle";
        if (data.detail === "cloud-live" || data.detail === "cloud-live-end") {
          setVoiceBarState(st === "idle" ? "idle" : "cloud-live");
        } else {
          setVoiceBarState(st);
        }
        if (window.showListeningOverlay) {
          window.showListeningOverlay(st === "listening");
        }
      }
    } catch (_) {}
  };
  ws.onclose = () => {
    window.jarvisWsConnected = false;
    setTimeout(connectJobWs, 5000);
  };
  ws.onerror = () => {
    window.jarvisWsConnected = false;
  };
}

async function saveVoiceSetting(patch) {
  const res = await fetch("/api/voice/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  return res.json().catch(() => ({}));
}

async function refreshVoiceUi() {
  try {
    const [settings, duplex] = await Promise.all([
      fetch("/api/voice/settings").then((r) => r.json()),
      fetch("/api/voice/duplex").then((r) => r.json()),
    ]);
    const duplexSel = document.getElementById("duplexModeSelect");
    if (duplexSel && settings.duplex_mode) duplexSel.value = settings.duplex_mode;
    const stt = document.getElementById("sttBackendSelect");
    if (stt && settings.stt_backend) stt.value = settings.stt_backend;
    updateDuplexHint({ ...duplex, duplex_mode: settings.duplex_mode });
    window.jarvisTtsChunkMaxChars = settings.tts_chunk_max_chars || 120;
  } catch (_) {}
  try {
    const cloud = await fetch("/api/voice/cloud-live/status").then((r) => r.json());
    const btn = document.getElementById("cloudLiveBtn");
    if (btn) {
      btn.disabled = !cloud.available;
      btn.title = cloud.message || "Cloud live voice";
      btn.classList.toggle("active", Boolean(_cloudSessionId));
    }
  } catch (_) {}
  syncMuteButton();
}

async function toggleCloudLive() {
  const btn = document.getElementById("cloudLiveBtn");
  if (_cloudSessionId) {
    await fetch(`/api/voice/cloud-live/${encodeURIComponent(_cloudSessionId)}/end`, { method: "POST" });
    _cloudSessionId = null;
    btn?.classList.remove("active");
    setVoiceBarState("idle");
    showToast("Cloud live ended", "info");
    return;
  }
  const res = await fetch("/api/voice/cloud-live/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const data = await res.json();
  if (!data.ok) {
    showToast(data.message || "Cloud live unavailable", "err");
    return;
  }
  _cloudSessionId = data.session_id;
  btn?.classList.add("active");
  setVoiceBarState("cloud-live");
  if (data.client_secret) {
    showToast(`OpenAI Realtime ready (${data.model || "realtime"})`, "ok", 6000);
  } else {
    showToast(data.message || "Cloud live session started", "ok", 5000);
  }
}

window.showAriaToast = showToast;
window.setVoiceBarState = setVoiceBarState;
window.jarvisRefreshVoiceUi = refreshVoiceUi;

document.addEventListener("DOMContentLoaded", () => {
  connectJobWs();
  refreshVoiceUi();

  document.getElementById("duplexModeSelect")?.addEventListener("change", async (ev) => {
    const mode = ev.target.value;
    await saveVoiceSetting({ duplex_mode: mode });
    const duplex = await fetch("/api/voice/duplex").then((r) => r.json()).catch(() => ({}));
    updateDuplexHint({ ...duplex, duplex_mode: mode });
    showToast(duplex.help || `Duplex: ${mode}`);
  });

  document.getElementById("sttBackendSelect")?.addEventListener("change", async (ev) => {
    await saveVoiceSetting({ stt_backend: ev.target.value });
    showToast(`STT: ${ev.target.value}`);
  });

  document.getElementById("voiceMuteBtn")?.addEventListener("click", () => {
    const cb = document.getElementById("speakRepliesToggle");
    if (cb) {
      cb.checked = !cb.checked;
      cb.dispatchEvent(new Event("change"));
    } else {
      _voiceMuted = !_voiceMuted;
    }
    syncMuteButton();
    showToast(_voiceMuted ? "Auto-speak muted" : "Auto-speak on", "info");
  });

  document.getElementById("speakRepliesToggle")?.addEventListener("change", syncMuteButton);

  document.getElementById("cloudLiveBtn")?.addEventListener("click", () => {
    toggleCloudLive().catch((e) => showToast(String(e.message || e), "err"));
  });

  document.getElementById("audioStopBtn")?.addEventListener("click", async () => {
    await fetch("/api/audio/stop", { method: "POST" });
    setVoiceBarState("idle");
  });
});
