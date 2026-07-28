/** Voice tab — settings, duplex, profiles, recovery, cloud live, cheatsheet */

function $(id) {
  return document.getElementById(id);
}

async function saveVoiceTabSetting(patch) {
  const res = await fetch("/api/voice/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.ok === false) {
    throw new Error(data.message || data.detail || `Save failed (${res.status})`);
  }
  return data;
}

async function loadVoiceCheatsheet(key) {
  const body = $("voiceTabCheatsheetBody");
  if (!body) return;
  const slug = key || $("voiceTabCheatsheetSelect")?.value || "voice";
  try {
    const res = await fetch(`/api/cheatsheets/${encodeURIComponent(slug)}`);
    const data = await res.json();
    body.textContent = data.cheatsheet?.content || data.content || "(empty cheatsheet)";
  } catch (e) {
    body.textContent = e.message || "Could not load cheatsheet";
    window.showAriaToast?.(e.message || "Could not load cheatsheet", "err", 4000);
  }
}

async function loadVoiceProfiles() {
  const sel = $("voiceTabProfileSelect");
  if (!sel) return;
  try {
    const data = await fetch("/api/voice/profiles").then((r) => r.json());
    const active = data.active || "";
    sel.innerHTML = '<option value="">— none —</option>';
    (data.profiles || []).forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name + (p.builtin ? "" : " *");
      if (p.id === active) opt.selected = true;
      sel.appendChild(opt);
    });
  } catch (_) {}
}

async function loadVoiceRecovery() {
  const el = $("voiceTabRecovery");
  if (!el) return;
  try {
    const data = await fetch("/api/voice/recovery").then((r) => r.json());
    const issues = data.issues || [];
    if (!issues.length) {
      el.textContent = `Healthy: ${(data.healthy || []).join(", ") || "ok"}`;
      return;
    }
    el.innerHTML = issues
      .map((i) => {
        const acts = (i.actions || [])
          .map(
            (a) =>
              `<button type="button" class="ghost-btn tiny voice-recovery-act" data-action="${a.id}">${a.label}</button>`,
          )
          .join(" ");
        return `<div class="voice-recovery-issue"><strong>${i.code}</strong> — ${i.message} ${acts}</div>`;
      })
      .join("");
    el.querySelectorAll(".voice-recovery-act").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await fetch("/api/voice/recovery/action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action: btn.dataset.action }),
        });
        window.showAriaToast?.(`Recovery: ${btn.dataset.action}`, "ok");
        loadVoiceRecovery();
      });
    });
  } catch (e) {
    el.textContent = e.message || "Recovery unavailable";
  }
}

async function loadVoiceTab() {
  const status = $("voiceTabStatus");
  const model = $("voiceTabModel");
  const cloud = $("voiceTabCloud");
  const cloudDetail = $("voiceTabCloudDetail");
  if (!status) return;
  try {
    const [settings, duplex, cloudSt, product] = await Promise.all([
      fetch("/api/voice/settings").then((r) => r.json()).catch(() => ({})),
      fetch("/api/voice/duplex").then((r) => r.json()).catch(() => ({})),
      fetch("/api/voice/cloud-live/status").then((r) => r.json()).catch(() => ({})),
      fetch("/api/voice/product").then((r) => r.json()).catch(() => ({})),
    ]);
    const state = product.state?.state || "idle";
    status.textContent = `State: ${state} · Duplex: ${duplex.mode || settings.duplex_mode || "off"} · STT: ${settings.stt_backend || "whisper"}`;
    status.title = duplex.help || "";
    if (model) {
      model.textContent = `TTS engine: ${settings.tts_engine || "piper"}`;
      model.title = `chunk ${settings.tts_chunk_max_chars || 220} chars · target ${settings.tts_latency_target_ms || "?"}ms`;
    }
    const cloudMsg = cloudSt.message || (cloudSt.available ? "Cloud live available" : "Cloud live unavailable");
    if (cloud) cloud.textContent = cloudMsg + (cloudSt.openai_hidden ? " · OpenAI Realtime hidden (no WebRTC)" : "");
    if (cloudDetail) {
      const active = (cloudSt.active || 0) > 0 || (cloudSt.active_sessions || 0) > 0;
      cloudDetail.textContent = active
        ? "Cloud live session is active."
        : cloudSt.available
          ? "Gemini Live ready — click Toggle or use the header Cloud live button."
          : cloudMsg;
    }
    const cloudBtn = $("voiceTabCloudBtn");
    if (cloudBtn) {
      const active = (cloudSt.active || 0) > 0;
      cloudBtn.textContent = active ? "Stop cloud live" : "Start cloud live";
      cloudBtn.disabled = cloudSt.available === false && !active;
    }

    const duplexSel = $("voiceTabDuplexSelect");
    if (duplexSel && settings.duplex_mode) duplexSel.value = settings.duplex_mode;
    const sttSel = $("voiceTabSttSelect");
    if (sttSel && settings.stt_backend) sttSel.value = settings.stt_backend;
    const chunk = $("voiceTabChunkChars");
    if (chunk && settings.tts_chunk_max_chars) chunk.value = String(settings.tts_chunk_max_chars);
    const interrupt = $("voiceTabInterrupt");
    if (interrupt) interrupt.checked = Boolean(settings.interrupt_on_speak);
    const chunkSent = $("voiceTabChunkSentences");
    if (chunkSent) chunkSent.checked = settings.speak_chunk_sentences !== false;
    const speak = $("voiceTabSpeakReplies");
    if (speak) speak.checked = Boolean(settings.speak_replies);
    const sw = $("voiceTabServerWhisper");
    if (sw) sw.checked = settings.server_whisper !== false;

    await loadVoiceProfiles();
    await loadVoiceCheatsheet();
    window.jarvisRefreshVoiceUi?.();
  } catch (e) {
    status.textContent = e.message;
    window.showAriaToast?.(e.message || "Voice tab load failed", "err", 5000);
  }
}

window.initVoiceTab = function initVoiceTab() {
  const root = $("voiceView");
  if (!root || root.dataset.bound === "1") return;
  root.dataset.bound = "1";
  loadVoiceTab();
  $("voiceTabRefreshBtn")?.addEventListener("click", loadVoiceTab);
  $("voiceTabRecoveryBtn")?.addEventListener("click", loadVoiceRecovery);
  $("voiceOpenAudioBtn")?.addEventListener("click", () => window.switchToView?.("audio"));
  $("voiceOpenPresenceBtn")?.addEventListener("click", () => window.switchToView?.("presence"));
  $("voiceTabDuplexSelect")?.addEventListener("change", async (ev) => {
    try {
      await saveVoiceTabSetting({ duplex_mode: ev.target.value });
      window.showAriaToast?.(`Duplex: ${ev.target.value}`, "ok");
      loadVoiceTab();
    } catch (err) {
      window.showAriaToast?.(err.message || "Duplex save failed", "err", 5000);
    }
  });
  $("voiceTabSttSelect")?.addEventListener("change", async (ev) => {
    try {
      await saveVoiceTabSetting({ stt_backend: ev.target.value });
      window.showAriaToast?.(`STT: ${ev.target.value}`, "ok");
      loadVoiceTab();
    } catch (err) {
      window.showAriaToast?.(err.message || "STT save failed", "err", 5000);
    }
  });
  $("voiceTabSpeakReplies")?.addEventListener("change", async (ev) => {
    await saveVoiceTabSetting({ speak_replies: !!ev.target.checked });
    const cb = $("speakRepliesToggle");
    if (cb) {
      cb.checked = !!ev.target.checked;
      cb.dispatchEvent(new Event("change"));
    }
  });
  $("voiceTabServerWhisper")?.addEventListener("change", async (ev) => {
    await saveVoiceTabSetting({ server_whisper: !!ev.target.checked });
    const cb = $("serverWhisperToggle");
    if (cb) {
      cb.checked = !!ev.target.checked;
      cb.dispatchEvent(new Event("change"));
    }
  });
  $("voiceTabActivateProfileBtn")?.addEventListener("click", async () => {
    const id = $("voiceTabProfileSelect")?.value;
    if (!id) return;
    try {
      const res = await fetch(`/api/voice/profiles/${encodeURIComponent(id)}/activate`, { method: "POST" });
      const data = await res.json();
      if (!data.ok) throw new Error(data.message || "Activate failed");
      window.showAriaToast?.(`Profile: ${data.profile?.name || id}`, "ok");
      loadVoiceTab();
    } catch (err) {
      window.showAriaToast?.(err.message || "Profile activate failed", "err", 5000);
    }
  });
  $("voiceTabSaveBtn")?.addEventListener("click", async () => {
    const patch = {
      duplex_mode: $("voiceTabDuplexSelect")?.value,
      stt_backend: $("voiceTabSttSelect")?.value,
      tts_chunk_max_chars: parseInt($("voiceTabChunkChars")?.value || "220", 10),
      interrupt_on_speak: Boolean($("voiceTabInterrupt")?.checked),
      speak_chunk_sentences: Boolean($("voiceTabChunkSentences")?.checked),
      speak_replies: Boolean($("voiceTabSpeakReplies")?.checked),
      server_whisper: Boolean($("voiceTabServerWhisper")?.checked),
    };
    try {
      await saveVoiceTabSetting(patch);
      window.showAriaToast?.("Voice settings saved", "ok");
      loadVoiceTab();
    } catch (err) {
      window.showAriaToast?.(err.message || "Voice settings save failed", "err", 5000);
    }
  });
  $("voiceTabCloudBtn")?.addEventListener("click", () => {
    $("cloudLiveBtn")?.click();
    setTimeout(loadVoiceTab, 800);
  });
  $("voiceTabCheatsheetSelect")?.addEventListener("change", (ev) => {
    loadVoiceCheatsheet(ev.target.value);
  });

  // Live status from WS
  window.addEventListener("jarvis-ws", (ev) => {
    const data = ev.detail || {};
    if (data.event === "voice_state" && $("voiceTabStatus")) {
      const cur = $("voiceTabStatus").textContent || "";
      $("voiceTabStatus").textContent = cur.replace(/^State:\s*\w+/, `State: ${data.state || "idle"}`);
    }
  });
};
