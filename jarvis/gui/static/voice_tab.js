/** Voice tab — settings, duplex, cloud live, cheatsheet */

function $(id) {
  return document.getElementById(id);
}

async function saveVoiceTabSetting(patch) {
  const res = await fetch("/api/voice/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  return res.json().catch(() => ({}));
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
  }
}

async function loadVoiceTab() {
  const status = $("voiceTabStatus");
  const model = $("voiceTabModel");
  const cloud = $("voiceTabCloud");
  const cloudDetail = $("voiceTabCloudDetail");
  if (!status) return;
  try {
    const [settings, duplex, cloudSt] = await Promise.all([
      fetch("/api/voice/settings").then((r) => r.json()).catch(() => ({})),
      fetch("/api/voice/duplex").then((r) => r.json()).catch(() => ({})),
      fetch("/api/voice/cloud-live/status").then((r) => r.json()).catch(() => ({})),
    ]);
    status.textContent = `Duplex: ${duplex.mode || settings.duplex_mode || "off"} · STT: ${settings.stt_backend || "whisper"}`;
    status.title = duplex.help || "";
    if (model) {
      model.textContent = settings.tts_model || settings.model || "default TTS";
      model.title = `chunk ${settings.tts_chunk_max_chars || 220} chars · target ${settings.tts_latency_target_ms || "?"}ms`;
    }
    const cloudMsg = cloudSt.message || (cloudSt.available ? "Cloud live available" : "Cloud live unavailable");
    if (cloud) cloud.textContent = cloudMsg;
    if (cloudDetail) {
      cloudDetail.textContent = cloudSt.active
        ? "Cloud live session is active."
        : cloudSt.available
          ? "Cloud live ready — click Toggle or use the header Cloud live button."
          : cloudMsg;
    }
    const cloudBtn = $("voiceTabCloudBtn");
    if (cloudBtn) {
      cloudBtn.textContent = cloudSt.active ? "Stop cloud live" : "Start cloud live";
      cloudBtn.disabled = cloudSt.available === false && !cloudSt.active;
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

    await loadVoiceCheatsheet();
    window.jarvisRefreshVoiceUi?.();
  } catch (e) {
    status.textContent = e.message;
  }
}

window.initVoiceTab = function initVoiceTab() {
  const root = $("voiceView");
  if (!root || root.dataset.bound === "1") return;
  root.dataset.bound = "1";
  loadVoiceTab();
  $("voiceTabRefreshBtn")?.addEventListener("click", loadVoiceTab);
  $("voiceTabDuplexSelect")?.addEventListener("change", async (ev) => {
    await saveVoiceTabSetting({ duplex_mode: ev.target.value });
    window.showAriaToast?.(`Duplex: ${ev.target.value}`);
    loadVoiceTab();
  });
  $("voiceTabSttSelect")?.addEventListener("change", async (ev) => {
    await saveVoiceTabSetting({ stt_backend: ev.target.value });
    window.showAriaToast?.(`STT: ${ev.target.value}`);
    loadVoiceTab();
  });
  $("voiceTabSaveBtn")?.addEventListener("click", async () => {
    const patch = {
      duplex_mode: $("voiceTabDuplexSelect")?.value,
      stt_backend: $("voiceTabSttSelect")?.value,
      tts_chunk_max_chars: parseInt($("voiceTabChunkChars")?.value || "220", 10),
      interrupt_on_speak: Boolean($("voiceTabInterrupt")?.checked),
      speak_chunk_sentences: Boolean($("voiceTabChunkSentences")?.checked),
    };
    await saveVoiceTabSetting(patch);
    window.showAriaToast?.("Voice settings saved", "ok");
    loadVoiceTab();
  });
  $("voiceTabCloudBtn")?.addEventListener("click", () => {
    $("cloudLiveBtn")?.click();
    setTimeout(loadVoiceTab, 800);
  });
  $("voiceTabCheatsheetSelect")?.addEventListener("change", (ev) => {
    loadVoiceCheatsheet(ev.target.value);
  });
};
