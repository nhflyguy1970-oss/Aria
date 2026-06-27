/** Gemini Live voice bridge — mic capture + PCM playback via /ws/gemini-live */
(function () {
  let ws = null;
  let audioCtx = null;
  let micStream = null;
  let processor = null;
  let playCtx = null;
  let playTime = 0;
  let active = false;
  let primedStream = null;
  let primedCaptureCtx = null;
  let primedPlayCtx = null;
  let serverCapture = false;
  let serverPlayback = false;
  let chunksSent = 0;
  let pendingInput = "";
  let pendingOutput = "";
  let activeSources = [];
  let speakingUntil = 0;
  const PLAYBACK_TAIL_MS = 350;

  async function resumeCtx(ctx) {
    if (!ctx) return ctx;
    if (ctx.state === "suspended") await ctx.resume();
    return ctx;
  }

  function micOpen() {
    return performance.now() >= speakingUntil;
  }

  function extendSpeaking(durationSec) {
    const until = performance.now() + durationSec * 1000 + PLAYBACK_TAIL_MS;
    speakingUntil = Math.max(speakingUntil, until);
  }

  function stopPlayback() {
    activeSources.forEach((src) => {
      try {
        src.stop();
      } catch (_) {}
    });
    activeSources = [];
    playTime = playCtx?.currentTime || 0;
    speakingUntil = performance.now() + PLAYBACK_TAIL_MS;
  }

  function floatTo16(float32) {
    const out = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return out;
  }

  function b64FromBytes(bytes) {
    let bin = "";
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(bin);
  }

  function resampleFloat32(samples, inputRate, targetRate) {
    if (inputRate === targetRate) return samples;
    const ratio = inputRate / targetRate;
    const outLen = Math.max(1, Math.floor(samples.length / ratio));
    const out = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) {
      const pos = i * ratio;
      const idx = Math.floor(pos);
      const frac = pos - idx;
      const a = samples[idx] || 0;
      const b = samples[idx + 1] || a;
      out[i] = a + (b - a) * frac;
    }
    return out;
  }

  function parseRate(mime) {
    const m = String(mime || "").match(/rate=(\d+)/i);
    return m ? parseInt(m[1], 10) : 24000;
  }

  async function schedulePcm(b64, mimeType) {
    if (!playCtx) playCtx = primedPlayCtx || new AudioContext();
    primedPlayCtx = null;
    await resumeCtx(playCtx);
    const rate = parseRate(mimeType);
    const raw = atob(b64);
    const bytes = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
    const pcm = new Int16Array(bytes.buffer, bytes.byteOffset, Math.floor(bytes.byteLength / 2));
    const buf = playCtx.createBuffer(1, pcm.length, rate);
    const ch = buf.getChannelData(0);
    for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 32768;
    const src = playCtx.createBufferSource();
    src.buffer = buf;
    src.connect(playCtx.destination);
    const start = Math.max(playCtx.currentTime, playTime);
    src.start(start);
    playTime = start + buf.duration;
    extendSpeaking(buf.duration);
    activeSources.push(src);
    src.onended = () => {
      activeSources = activeSources.filter((s) => s !== src);
    };
  }

  function stopMic() {
    if (processor) {
      processor.disconnect();
      processor.onaudioprocess = null;
      processor = null;
    }
    if (micStream) {
      micStream.getTracks().forEach((t) => t.stop());
      micStream = null;
    }
    if (audioCtx) {
      audioCtx.close().catch(() => {});
      audioCtx = null;
    }
    if (primedStream) {
      primedStream.getTracks().forEach((t) => t.stop());
      primedStream = null;
    }
    if (primedCaptureCtx) {
      primedCaptureCtx.close().catch(() => {});
      primedCaptureCtx = null;
    }
  }

  function cleanupPlayback() {
    stopPlayback();
    if (playCtx) {
      playCtx.close().catch(() => {});
      playCtx = null;
    }
    if (primedPlayCtx) {
      primedPlayCtx.close().catch(() => {});
      primedPlayCtx = null;
    }
  }

  function notifyEnded() {
    window.jarvisOnCloudLiveEnded?.();
  }

  /** Call on button click (user gesture) before any await — unlocks mic + speakers in PySide. */
  async function primeAudio() {
    primedStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 },
    });
    primedCaptureCtx = new AudioContext();
    primedPlayCtx = new AudioContext();
    await resumeCtx(primedCaptureCtx);
    await resumeCtx(primedPlayCtx);
    return true;
  }

  async function startMic() {
    micStream = primedStream
      || (await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 },
      }));
    primedStream = null;
    audioCtx = primedCaptureCtx || new AudioContext();
    primedCaptureCtx = null;
    await resumeCtx(audioCtx);
    if (!playCtx) {
      playCtx = primedPlayCtx || new AudioContext();
      primedPlayCtx = null;
      await resumeCtx(playCtx);
    }
    const inputRate = audioCtx.sampleRate;
    const targetRate = 16000;
    const src = audioCtx.createMediaStreamSource(micStream);
    processor = audioCtx.createScriptProcessor(4096, 1, 1);
    const silent = audioCtx.createGain();
    silent.gain.value = 0;
    chunksSent = 0;
    processor.onaudioprocess = (ev) => {
      if (!ws || ws.readyState !== WebSocket.OPEN || !active) return;
      if (!micOpen()) return;
      let samples = ev.inputBuffer.getChannelData(0);
      samples = resampleFloat32(samples, inputRate, targetRate);
      const pcm = floatTo16(samples);
      const b64 = b64FromBytes(new Uint8Array(pcm.buffer));
      ws.send(JSON.stringify({ type: "audio", data: b64 }));
      chunksSent += 1;
      if (chunksSent === 1) {
        window.setVoiceBarState?.("listening");
      }
    };
    src.connect(processor);
    processor.connect(silent);
    silent.connect(audioCtx.destination);
  }

  async function start(sessionId, bridgePath) {
    if (!serverCapture && !primedStream) {
      try {
        await primeAudio();
      } catch (e) {
        window.showAriaToast?.(`Mic unlock failed: ${e.message}`, "err", 6000);
        throw e;
      }
    }
    await stop();
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const path = bridgePath || `/ws/gemini-live/${encodeURIComponent(sessionId)}`;
    ws = new WebSocket(`${proto}://${location.host}${path}`);
    active = false;
    playTime = 0;
    chunksSent = 0;
    pendingInput = "";
    pendingOutput = "";
    speakingUntil = 0;

    const connectPromise = new Promise((resolve, reject) => {
      let ready = false;
      let heardReply = false;
      let settled = false;

      const fail = (err) => {
        if (settled) return;
        settled = true;
        reject(err);
      };

      const onDisconnect = () => {
        active = false;
        stopMic();
        cleanupPlayback();
        notifyEnded();
      };

      ws.onopen = () => {
        window.setVoiceBarState?.("thinking");
      };
      ws.onerror = () => {
        onDisconnect();
        fail(new Error("Gemini Live WebSocket failed"));
      };
      ws.onmessage = async (ev) => {
        let msg;
        try {
          msg = JSON.parse(ev.data);
        } catch (_) {
          return;
        }
        if (msg.type === "connecting") {
          window.setVoiceBarState?.("thinking");
          return;
        }
        if (msg.type === "ready") {
          ready = true;
          active = true;
          serverCapture = msg.capture === "server";
          serverPlayback = msg.playback === "server";
          window.setVoiceBarState?.("cloud-live");
          if (!serverCapture) {
            try {
              await startMic();
            } catch (e) {
              window.showAriaToast?.(`Mic failed: ${e.message}`, "err", 6000);
              fail(e);
              return;
            }
          }
          const hint = serverCapture
            ? "Server mic live — speak, then pause"
            : "Speak now — pause when done";
          window.showAriaToast?.(hint, "ok", 5000);
          if (!settled) {
            settled = true;
            resolve();
          }
          return;
        }
        if (msg.type === "speaking") {
          window.setVoiceBarState?.("speaking");
        } else if (msg.type === "playback_idle") {
          window.setVoiceBarState?.("cloud-live");
        } else if (msg.type === "audio" && msg.data) {
          heardReply = true;
          if (!serverPlayback) {
            await schedulePcm(msg.data, msg.mimeType);
          }
          window.setVoiceBarState?.("speaking");
        } else if (msg.type === "interrupted") {
          stopPlayback();
          pendingOutput = "";
        } else if (msg.type === "transcript" && msg.text) {
          const role = msg.role === "input" ? "user" : "assistant";
          if (role === "input") {
            pendingInput = msg.text;
          } else {
            pendingOutput = msg.text;
            if (serverPlayback) {
              window.setVoiceBarState?.("speaking");
            }
          }
        } else if (msg.type === "error") {
          window.showAriaToast?.(msg.message || "Gemini Live error", "err");
          fail(new Error(msg.message || "Gemini Live error"));
        } else if (msg.type === "turn_complete") {
          if (pendingInput) {
            window.addMessage?.("user", pendingInput, { type: "cloud-live" });
            pendingInput = "";
          }
          if (pendingOutput) {
            heardReply = true;
            window.addMessage?.("assistant", pendingOutput, { type: "cloud-live" });
            window.showAriaToast?.(pendingOutput.slice(0, 120), "info", 3500);
            pendingOutput = "";
          }
          window.setVoiceBarState?.("cloud-live");
          if (!heardReply && !serverCapture && chunksSent > 10) {
            window.showAriaToast?.("No reply heard — try speaking louder or closer to the mic", "warn", 5000);
          }
        }
      };
      ws.onclose = (ev) => {
        onDisconnect();
        if (!ready) {
          const reason = ev?.reason ? `: ${ev.reason}` : "";
          fail(new Error(`Gemini Live WebSocket closed${reason}`));
        }
      };
    });

    return connectPromise;
  }

  async function stop() {
    active = false;
    pendingInput = "";
    pendingOutput = "";
    speakingUntil = 0;
    stopMic();
    cleanupPlayback();
    if (ws) {
      try {
        ws.close();
      } catch (_) {}
      ws = null;
    }
  }

  window.jarvisGeminiLive = { start, stop, primeAudio };
})();
