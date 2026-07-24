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
  el.classList.remove("hidden");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => el.classList.add("hidden"), ms);
}

async function refreshRouterStatus() {
  const pill = document.getElementById("routerStatusPill");
  if (!pill) return;
  try {
    const st = await fetch("/api/router/status").then((r) => r.json());
    const fg = st.functiongemma || {};
    const backend = st.backend || "auto";
    const loaded = fg.loaded ? "loaded" : fg.ready ? "ready" : "off";
    const model = (fg.active_model || fg.model || st.model || "?").split("/").pop();
    const fb = fg.fallback ? " · fb" : "";
    pill.textContent = `Router: ${backend}/${loaded}${fb}`;
    pill.title = `Backend ${backend} · ${model} · parse=${fg.parse_probe ?? "?"}`;
  } catch (_) {
    pill.textContent = "Router: ?";
  }
}

async function warmFunctionGemma() {
  const btn = document.getElementById("routerWarmBtn");
  if (btn) btn.disabled = true;
  try {
    const res = await fetch("/api/router/functiongemma/warm", { method: "POST" });
    const data = await res.json();
    const ok = Boolean(data.ok);
    const detail = data.fallback ? " (base fallback)" : "";
    showToast(
      ok ? `FunctionGemma warm OK${detail}` : "FunctionGemma warm failed",
      ok ? "ok" : "err",
      5000,
    );
    await refreshRouterStatus();
  } catch (e) {
    showToast(String(e.message || e), "err");
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function runVoiceSmoke() {
  const btn = document.getElementById("voiceSmokeBtn");
  if (btn) btn.disabled = true;
  try {
    const res = await fetch("/api/voice/smoke");
    const data = await res.json();
    const ok = Boolean(data.ok);
    showToast(
      ok ? `Voice smoke ${data.passed}/${data.total}` : `Smoke failed ${data.passed}/${data.total}`,
      ok ? "ok" : "err",
      6000,
    );
    await refreshRouterStatus();
  } catch (e) {
    showToast(String(e.message || e), "err");
  } finally {
    if (btn) btn.disabled = false;
  }
}

window.jarvisRefreshRouterStatus = refreshRouterStatus;

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
  if (label && !bar.dataset.partialText) {
    label.textContent = map[effective] || effective;
  }
  document.getElementById("ariaVoiceStrip")?.classList.toggle("voice-strip-active", effective !== "idle");
  document.documentElement.dataset.voiceState = effective;
  document.documentElement.classList.toggle(
    "voice-active",
    effective !== "idle" && effective !== "muted",
  );
  document.querySelector(".brand-icon")?.classList.toggle(
    "brand-live",
    effective !== "idle" && effective !== "muted",
  );
}

function showSttPartial(text, final) {
  const bar = document.getElementById("voiceBar");
  const label = bar?.querySelector(".voice-bar-label");
  const partialEl = document.getElementById("listeningPartial");
  const t = String(text || "").trim();
  if (!t) return;
  const short = t.length > 56 ? `${t.slice(0, 53)}…` : t;
  if (bar) bar.dataset.partialText = final ? "" : t;
  if (label) label.textContent = short;
  if (partialEl) partialEl.textContent = t;
  if (final && window.showListeningOverlay) window.showListeningOverlay(false);
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
        if (st !== "listening") {
          const partialEl = document.getElementById("listeningPartial");
          if (partialEl) partialEl.textContent = "";
        }
      } else if (data.event === "stt_partial") {
        showSttPartial(data.text, Boolean(data.final));
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
    const sttInfo = settings.stt || {};
    if (stt) {
      const rtsOpt = stt.querySelector('option[value="realtimestt"]');
      const rtsReady = Boolean(sttInfo.realtimestt_ready);
      if (rtsOpt) {
        rtsOpt.disabled = !rtsReady;
        rtsOpt.title = rtsReady
          ? "Low-latency local STT"
          : "Set JARVIS_REALTIMESTT=1 and pip install realtimestt";
      }
      if (settings.stt_backend) stt.value = settings.stt_backend;
      if (!rtsReady && stt.value === "realtimestt") stt.value = "whisper";
    }
    updateDuplexHint({ ...duplex, duplex_mode: settings.duplex_mode });
    window.jarvisTtsChunkMaxChars = settings.tts_chunk_max_chars || 220;
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

async function endCloudLiveSession() {
  if (_cloudSessionId) {
    const sid = _cloudSessionId;
    _cloudSessionId = null;
    await window.jarvisGeminiLive?.stop(true);
    await fetch(`/api/voice/cloud-live/${encodeURIComponent(sid)}/end`, { method: "POST" }).catch(() => {});
    document.getElementById("cloudLiveBtn")?.classList.remove("active");
    setVoiceBarState("idle");
  } else {
    await window.jarvisGeminiLive?.stop();
  }
}

function handleCloudLiveEnded() {
  if (!_cloudSessionId) return;
  const sid = _cloudSessionId;
  _cloudSessionId = null;
  document.getElementById("cloudLiveBtn")?.classList.remove("active");
  setVoiceBarState("idle");
  fetch(`/api/voice/cloud-live/${encodeURIComponent(sid)}/end`, { method: "POST" }).catch(() => {});
}

async function toggleCloudLive() {
  const btn = document.getElementById("cloudLiveBtn");
  if (_cloudSessionId) {
    await endCloudLiveSession();
    showToast("Cloud live ended", "info");
    return;
  }
  if (btn?.disabled) return;
  const primePromise = window.jarvisGeminiLive?.primeAudio?.().catch((e) => {
    showToast(`Mic unlock failed: ${e.message}`, "warn");
    return false;
  });
  if (btn) btn.disabled = true;
  setVoiceBarState("thinking");
  try {
    const status = await fetch("/api/voice/cloud-live/status").then((r) => r.json()).catch(() => ({}));
    let provider = status.provider || "";
    if (status.openai_key && !status.openai_key_usable && status.gemini_key_usable) {
      provider = "gemini_live";
    }
    const startSession = async (pick) => {
      const res = await fetch("/api/voice/cloud-live/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pick ? { provider: pick } : {}),
      });
      return res.json();
    };
    let data = await startSession(provider);
    if (!data.ok && provider === "openai_realtime" && status.gemini_key_usable) {
      data = await startSession("gemini_live");
    }
    if (!data.ok) {
      const hint = data.message || status.gemini_key_warning || "Cloud live unavailable";
      showToast(hint, "err", 8000);
      setVoiceBarState("idle");
      return;
    }
    _cloudSessionId = data.session_id;
    btn?.classList.add("active");
    if (data.provider === "openai_realtime") {
      const sid = _cloudSessionId;
      _cloudSessionId = null;
      btn?.classList.remove("active");
      await fetch(`/api/voice/cloud-live/${encodeURIComponent(sid)}/end`, { method: "POST" }).catch(() => {});
      showToast(
        data.message || "OpenAI Realtime WebRTC is not available — use Gemini Live",
        "err",
        8000,
      );
      setVoiceBarState("idle");
      return;
    }
    if (data.provider === "gemini_live" && data.bridge_ws) {
      await primePromise;
      const connectMs = 30000;
      await Promise.race([
        window.jarvisGeminiLive.start(data.session_id, data.bridge_ws),
        new Promise((_, reject) => {
          setTimeout(
            () => reject(new Error("Cloud live timed out — sidebar → Restart server, then try again")),
            connectMs,
          );
        }),
      ]);
    } else {
      showToast(data.message || "Cloud live session started", "ok", 5000);
      setVoiceBarState("cloud-live");
    }
  } catch (e) {
    showToast(e.message || "Gemini Live failed", "err");
    if (_cloudSessionId) {
      await fetch(`/api/voice/cloud-live/${encodeURIComponent(_cloudSessionId)}/end`, { method: "POST" }).catch(() => {});
      _cloudSessionId = null;
    }
    btn?.classList.remove("active");
    setVoiceBarState("idle");
  } finally {
    if (btn) btn.disabled = false;
  }
}

window.syncMuteButton = syncMuteButton;
window.showAriaToast = showToast;
window.setVoiceBarState = setVoiceBarState;
window.jarvisRefreshVoiceUi = refreshVoiceUi;
window.jarvisEndCloudLive = endCloudLiveSession;
window.jarvisOnCloudLiveEnded = handleCloudLiveEnded;

document.addEventListener("DOMContentLoaded", () => {
  connectJobWs();
  refreshVoiceUi();
  refreshRouterStatus();

  document.getElementById("routerWarmBtn")?.addEventListener("click", () => {
    warmFunctionGemma().catch((e) => showToast(String(e.message || e), "err"));
  });

  document.getElementById("voiceSmokeBtn")?.addEventListener("click", () => {
    runVoiceSmoke().catch((e) => showToast(String(e.message || e), "err"));
  });

  document.getElementById("duplexModeSelect")?.addEventListener("change", async (ev) => {
    const mode = ev.target.value;
    await saveVoiceSetting({ duplex_mode: mode });
    const duplex = await fetch("/api/voice/duplex").then((r) => r.json()).catch(() => ({}));
    updateDuplexHint({ ...duplex, duplex_mode: mode });
    showToast(duplex.help || `Duplex: ${mode}`);
  });

  document.getElementById("sttBackendSelect")?.addEventListener("change", async (ev) => {
    const res = await saveVoiceSetting({ stt_backend: ev.target.value });
    if (res.message) showToast(res.message, "warn");
    else showToast(`STT: ${res.stt_backend || ev.target.value}`);
    refreshVoiceUi();
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
    if (_cloudSessionId) {
      await endCloudLiveSession();
    } else {
      await window.jarvisGeminiLive?.stop();
    }
    await fetch("/api/audio/stop", { method: "POST" });
    setVoiceBarState("idle");
  });
});
