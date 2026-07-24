/** Movie Jarvis tiers 1–4 UI hooks */
(function () {
  const LS = {
    speakReplies: "jarvis_speak_replies",
    serverWhisper: "jarvis_chat_server_whisper",
    jarvisBlue: "jarvis_blue_theme",
    moduleFilter: "jarvis_module_filter",
    collapsed: "jarvis_sidebar_collapsed",
  };

  function $(id) { return document.getElementById(id); }

  function escapeHtml(s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts);
    return res.json();
  }

  /* --- Environment strip (Tier 1 #6) --- */
  async function refreshEnvStrip() {
    const el = $("envStrip");
    if (!el) return;
    try {
      const [envData, liveData] = await Promise.all([
        fetchJson("/api/environment"),
        fetchJson("/api/live").catch(() => ({})),
      ]);
      const gpu = envData.gpu || {};
      const prof = envData.profile || "default";
      const off = !envData.ollama_running ? " · Ollama starting" : "";
      const vram = gpu.free_vram_mb != null ? `${gpu.free_vram_mb}MB VRAM` : "";
      const uiMeta = document.querySelector('meta[name="jarvis-ui-version"]')?.content || "";
      let versionHint = "";
      if (liveData.ui_version && uiMeta && liveData.ui_version !== uiMeta) {
        el.classList.add("version-warn");
        versionHint = " · reload UI";
        el.title = `UI build ${uiMeta} · server expects ${liveData.ui_version}. Use Reload UI in sidebar.`;
      } else {
        el.classList.remove("version-warn");
      }
      el.textContent = `${prof}${vram ? " · " + vram : ""}${off}${versionHint}`;
      if (!versionHint) {
        el.title = `Disk ${envData.disk_free_gb || "?"}GB free · ${envData.services_ready ? "services ready" : "warming up"}`;
      }
    } catch (_) {
      el.textContent = "Environment unavailable";
    }
  }

  /* --- Profile banner (Tier 2 #20) --- */
  async function refreshProfileBanner() {
    const bar = $("profileBanner");
    if (!bar) return;
    try {
      const data = await fetchJson("/api/movie/profile-banner");
      if (data.show) {
        bar.textContent = data.message.replace(/\*\*/g, "");
        bar.classList.remove("hidden");
      } else {
        bar.classList.add("hidden");
      }
    } catch (_) {}
  }

  /* --- Pinned briefing card (Tier 1 #4) --- */
  async function loadPinnedBriefing() {
    const card = $("pinnedBriefing");
    if (!card) return;
    try {
      const res = await fetch("/api/briefing?launch=1");
      const data = await res.json();
      if (!data.ok || data.show === false || !data.markdown) {
        card.classList.add("hidden");
        return;
      }
      card.classList.remove("hidden");
      card.querySelector(".pinned-body").innerHTML = window.marked
        ? marked.parse(data.markdown)
        : `<pre>${escapeHtml(data.markdown)}</pre>`;
      const tasks = (data.open_tasks || data.tasks || []).slice(0, 6);
      const taskEl = card.querySelector(".pinned-tasks");
      if (taskEl && tasks.length) {
        taskEl.innerHTML = tasks.map((t) => `<li>${escapeHtml(typeof t === "string" ? t : t.content || t.text || "")}</li>`).join("");
        taskEl.closest(".pinned-task-block")?.classList.remove("hidden");
      }
    } catch (_) {
      card.classList.add("hidden");
    }
  }

  /* --- Wake pill (Tier 1 #3) --- */
  async function refreshWakePill() {
    const pill = $("wakePill");
    if (!pill) return;
    try {
      const data = await fetchJson("/api/audio/wakeword/status");
      const on = !!(data.running ?? data.listening);
      pill.textContent = on ? "Wake: on" : "Wake: off";
      pill.classList.toggle("wake-on", on);
      pill.title = on ? "Click to stop wake word" : "Click to start wake word";
    } catch (_) {
      pill.textContent = "Wake: —";
    }
  }

  async function toggleWake() {
    try {
      const data = await fetchJson("/api/audio/wakeword/status");
      const path = (data.running ?? data.listening) ? "/api/audio/wakeword/stop" : "/api/audio/wakeword/start";
      await fetch(path, { method: "POST" });
      refreshWakePill();
    } catch (_) {}
  }

  /* --- Speak replies (Tier 1 #2) --- */
  function speakRepliesEnabled() {
    return localStorage.getItem(LS.speakReplies) === "1";
  }

  function initSpeakToggle() {
    const cb = $("speakRepliesToggle");
    const settingsCb = $("settingsSpeakToggle");
    if (!cb && !settingsCb) return;
    const enabled = speakRepliesEnabled();
    if (cb) cb.checked = enabled;
    if (settingsCb) settingsCb.checked = enabled;
    const sync = (src) => {
      const on = !!src.checked;
      localStorage.setItem(LS.speakReplies, on ? "1" : "0");
      if (cb && src !== cb) cb.checked = on;
      if (settingsCb && src !== settingsCb) settingsCb.checked = on;
      window.syncMuteButton?.();
    };
    cb?.addEventListener("change", () => sync(cb));
    settingsCb?.addEventListener("change", () => sync(settingsCb));
  }

  window.jarvisMaybeSpeakReply = async function (text) {
    if (!speakRepliesEnabled() || !text) return;
    const plain = String(text).replace(/[*_#`>\[\]()]/g, " ").replace(/\s+/g, " ").trim().slice(0, 800);
    if (!plain) return;
    try {
      const form = new FormData();
      form.append("text", plain);
      await fetch("/api/audio/speak", { method: "POST", body: form });
    } catch (_) {}
  };

  /* --- Collapsible sidebar (Tier 1 #5, Tier 4 #40 mobile accordion) --- */
  function initCollapsibleSections() {
    let collapsed = {};
    try { collapsed = JSON.parse(localStorage.getItem(LS.collapsed) || "{}"); } catch (_) {}
    if (collapsed.models === undefined) collapsed.models = true;
    document.querySelectorAll(".sidebar-section[data-section]").forEach((sec) => {
      const key = sec.dataset.section;
      const head = sec.querySelector(".sidebar-section-head");
      if (!head) return;
      if (collapsed[key]) sec.classList.add("collapsed");
      head.addEventListener("click", () => {
        sec.classList.toggle("collapsed");
        collapsed[key] = sec.classList.contains("collapsed");
        localStorage.setItem(LS.collapsed, JSON.stringify(collapsed));
        head.setAttribute("aria-expanded", sec.classList.contains("collapsed") ? "false" : "true");
        if (key === "models" && !sec.classList.contains("collapsed")) {
          document.getElementById("modelsEditor")?.classList.remove("hidden");
          if (typeof window.loadModelSettings === "function") window.loadModelSettings();
        }
      });
      head.setAttribute("aria-expanded", sec.classList.contains("collapsed") ? "false" : "true");
    });
  }

  async function refreshWorldStateHud() {
    const el = $("globalWorldStateHud");
    const dot = document.querySelector(".world-state-dot");
    if (!el) return;
    try {
      const [envData, liveData] = await Promise.all([
        fetchJson("/api/environment"),
        fetchJson("/api/live").catch(() => ({})),
      ]);
      const svc = envData.services_ready ? "systems online" : "warming up";
      const gpu = envData.gpu?.name ? envData.gpu.name.replace(/^.*\[AMD\/ATI\]\s*/, "").split("(")[0].trim() : "";
      const ollama = liveData.ready === false ? " · Ollama starting" : "";
      el.textContent = `${svc}${gpu ? " · " + gpu : ""}${ollama}`;
      if (dot) dot.style.background = envData.services_ready ? "var(--accent)" : "#fbbf24";
    } catch (_) {
      el.textContent = "World state unavailable";
    }
  }

  /* --- Module chip filter (Tier 1 #10) — navigate + set preferred mode --- */
  const MODULE_NAV = {
    all: { view: "chat", hint: "Unified mode — Aria routes by intent" },
    general: { view: "chat", hint: "Chat mode" },
    coding: { view: "chat", hint: "Coding mode — ask about code, files, or fixes" },
    vision: { view: "chat", hint: "Vision mode — attach an image or use the camera" },
    audio: { view: "audio", hint: "Audio workspace" },
    image: { view: "gallery", hint: "Image gallery & generation" },
    video: { view: "video", hint: "Video workspace" },
    meme: { view: "meme", hint: "Meme engine" },
    data: { view: "chat", hint: "Data mode — attach CSV/JSON or ask about datasets" },
    memory: { view: "memory", hint: "Memory browser" },
    journal: { view: "journal", hint: "Bullet journal" },
  };

  function applyModuleFilter(mod) {
    const target = MODULE_NAV[mod] || MODULE_NAV.all;
    window.jarvisPreferredModule = mod === "all" ? "" : mod;
    localStorage.setItem(LS.moduleFilter, mod);
    document.querySelectorAll(".module-chip").forEach((c) => {
      c.classList.toggle("active", (c.dataset.module || "all") === mod);
      c.setAttribute("aria-pressed", (c.dataset.module || "all") === mod ? "true" : "false");
    });
    if (target.view) window.switchToView?.(target.view);
    const status = document.getElementById("statusText");
    if (status && target.hint) status.textContent = target.hint;
    window.showAriaToast?.(target.hint || `Mode: ${mod}`, "ok", 2500);
    window.dispatchEvent(new CustomEvent("jarvis-module-filter", { detail: { module: mod } }));
  }

  function initModuleFilter() {
    const saved = localStorage.getItem(LS.moduleFilter) || "all";
    window.jarvisPreferredModule = saved === "all" ? "" : saved;
    document.querySelectorAll(".module-chip").forEach((chip) => {
      if (!chip.getAttribute("role")) chip.setAttribute("role", "button");
      if (!chip.hasAttribute("tabindex")) chip.setAttribute("tabindex", "0");
      const isActive = chip.dataset.module === saved || (saved === "all" && chip.dataset.module === "all");
      chip.classList.toggle("active", isActive);
      chip.setAttribute("aria-pressed", isActive ? "true" : "false");
      const activate = () => applyModuleFilter(chip.dataset.module || "all");
      chip.addEventListener("click", activate);
      chip.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          activate();
        }
      });
    });
  }

  /* --- Context suggestion chips (Tier 1 #7) --- */
  function refreshContextSuggestions() {
    const el = $("suggestions");
    if (!el || el.querySelector(".data-chip, .vision-chip")) return;
    const hour = new Date().getHours();
    const chips = [];
    if (hour < 11) chips.push("Morning briefing");
    if (window.jarvisAttachmentKind === "document") chips.push("Summarize this document");
    if (window.jarvisEditorPath) chips.push("Run tests for " + window.jarvisEditorPath);
    if (!chips.length) return;
    const existing = new Set([...el.querySelectorAll(".suggestion-chip")].map((c) => c.textContent));
    chips.forEach((label) => {
      if (existing.has(label)) return;
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "suggestion-chip context-chip";
      chip.textContent = label;
      chip.addEventListener("click", () => {
        const input = $("messageInput");
        if (input) { input.value = label; input.focus(); }
      });
      el.prepend(chip);
    });
  }

  /* --- Chat mic → server Whisper + global PTT (Tier 1 #1, Tier 4 #34) --- */
  let pttSession = null;
  let pttActive = false;

  function useServerWhisper() {
    return localStorage.getItem(LS.serverWhisper) !== "0";
  }

  async function chatMicDown() {
    if (!useServerWhisper()) return false;
    try {
      const form = new FormData();
      form.append("source", "default");
      const data = await fetchJson("/api/audio/record/ptt/start", { method: "POST", body: form });
      if (data.ok) { pttSession = data.session_id; pttActive = true; return true; }
    } catch (_) {}
    return false;
  }

  async function chatMicUp() {
    if (!pttActive || !pttSession) return;
    pttActive = false;
    const form = new FormData();
    form.append("session_id", pttSession);
    form.append("transcribe", "1");
    try {
      const data = await fetchJson("/api/audio/record/ptt/stop", { method: "POST", body: form });
      pttSession = null;
      if (data.transcript) {
        const text = data.transcript.trim();
        if (text && typeof window.sendMessage === "function") {
          window.sendMessage(text);
        } else {
          const input = $("messageInput");
          if (input) {
            input.value = (input.value ? input.value + " " : "") + data.transcript;
            input.dispatchEvent(new Event("input"));
          }
        }
      }
    } catch (_) {}
  }

  function initChatMicPtt() {
    const mic = $("micBtn");
    const ptt = $("pttBtn");
    const cb = $("serverWhisperToggle");
    if (cb) {
      cb.checked = useServerWhisper();
      cb.addEventListener("change", () => localStorage.setItem(LS.serverWhisper, cb.checked ? "1" : "0"));
    }
    if (ptt) {
      ptt.addEventListener("mousedown", async () => {
        ptt.classList.add("listening");
        await chatMicDown();
      });
      ptt.addEventListener("mouseup", () => { ptt.classList.remove("listening"); chatMicUp(); });
      ptt.addEventListener("mouseleave", () => { if (pttActive) { ptt.classList.remove("listening"); chatMicUp(); } });
    }
    if (mic && useServerWhisper()) {
      mic.title = "Hold for local Whisper (server)";
      let holding = false;
      mic.addEventListener("mousedown", async (e) => {
        if (e.button !== 0) return;
        holding = await chatMicDown();
        if (holding) mic.classList.add("listening");
      });
      mic.addEventListener("mouseup", () => {
        if (holding) { mic.classList.remove("listening"); chatMicUp(); holding = false; }
      });
    }
  }

  /* --- Service restart (Tier 3 #27) --- */
  function initServiceRestart() {
    document.querySelectorAll(".service-row[data-svc]").forEach((row) => {
      if (row.querySelector(".svc-restart")) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ghost-btn tiny svc-restart";
      btn.textContent = "↻";
      btn.title = "Restart service";
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const svc = row.dataset.svc;
        if (!confirm(`Restart ${svc}?`)) return;
        await fetch("/api/services/restart", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ service: svc }),
        });
        setTimeout(() => window.loadServicesPanel?.(), 2000);
      });
      row.appendChild(btn);
    });
  }

  /* --- HA entity browser + scene composer (Tier 3 #25–26, Tier 4 #36) --- */
  async function loadHaEntities() {
    const list = $("haEntityList");
    if (!list) return;
    const domain = $("haDomainFilter")?.value || "light";
    list.innerHTML = "<li class='muted'>Loading…</li>";
    try {
      const q = domain ? `?domain=${encodeURIComponent(domain)}&limit=60` : "?limit=60";
      const data = await fetchJson(`/api/homeassistant/entities${q}`);
      const ents = data.entities || [];
      const isScene = domain === "scene";
      list.innerHTML = ents.length
        ? ents.map((e) => {
          const id = e.entity_id || "";
          const name = e.attributes?.friendly_name || id;
          const st = e.state || "?";
          const chatBtn = `<button type="button" class="ghost-btn tiny ha-ent-chat" data-eid="${escapeHtml(id)}" title="Insert in chat">Chat</button>`;
          const actBtn = isScene
            ? `<button type="button" class="ghost-btn tiny ha-ent-scene" data-eid="${escapeHtml(id)}">Activate</button>`
            : `<button type="button" class="ghost-btn tiny ha-ent-toggle" data-eid="${escapeHtml(id)}">${escapeHtml(st)}</button>`;
          return `<li><span>${escapeHtml(name)}</span><code>${escapeHtml(id)}</code>${actBtn}${chatBtn}</li>`;
        }).join("")
        : `<li class='muted'>No ${domain || "entities"} found — add integrations in HA.</li>`;
      list.querySelectorAll(".ha-ent-toggle").forEach((btn) => {
        btn.addEventListener("click", async () => {
          await fetch("/api/homeassistant/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ entity_id: btn.dataset.eid, action: "toggle" }),
          });
          loadHaEntities();
        });
      });
      list.querySelectorAll(".ha-ent-scene").forEach((btn) => {
        btn.addEventListener("click", async () => {
          await fetch("/api/homeassistant/scene", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ entity_id: btn.dataset.eid }),
          });
          loadHaEntities();
        });
      });
      list.querySelectorAll(".ha-ent-chat").forEach((btn) => {
        btn.addEventListener("click", () => {
          const input = $("messageInput");
          if (input) {
            input.value = `${isScene ? "activate scene" : "toggle"} ${btn.dataset.eid}`;
            input.focus();
          }
        });
      });
    } catch (_) {
      list.innerHTML = "<li>Could not load entities</li>";
    }
  }

  function initHaExtras() {
    $("haDomainFilter")?.addEventListener("change", loadHaEntities);
    $("haEntitiesRefreshBtn")?.addEventListener("click", loadHaEntities);
    $("haSceneSaveBtn")?.addEventListener("click", async () => {
      const scene = $("haSceneComposerInput")?.value?.trim();
      if (!scene) return;
      await fetch("/api/homeassistant/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ leave_scene: scene }),
      });
      $("haLeaveSceneInput").value = scene;
    });
    $("haSetupWizardBtn")?.addEventListener("click", () => $("haSetupModal")?.classList.remove("hidden"));
    $("haSetupCloseBtn")?.addEventListener("click", () => $("haSetupModal")?.classList.add("hidden"));
    loadHaEntities();
  }

  /* --- Trust health (Tier 3 #30) --- */
  async function refreshTrustHealth() {
    const el = $("trustHealthCard");
    if (!el) return;
    try {
      const d = await fetchJson("/api/movie/trust-health");
      el.innerHTML = `<span>${d.disk_free_gb}GB free</span> · `
        + `<span>scrub: ${escapeHtml(d.last_scrub)}</span> · `
        + `<span>${d.strategy_entries} strategies</span> · `
        + `<span>filter: ${d.test_filter}</span>`;
    } catch (_) {
      el.textContent = "Trust layer: —";
    }
  }

  /* --- Server restart --- */
  async function restartJarvisServer() {
    if (!confirm(`Restart ${typeof ariaName === "function" ? ariaName() : "ARIA"} server now? Chat will reconnect in a few seconds.`)) return;
    const btn = $("restartServerBtn");
    const prev = btn?.textContent;
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Restarting…";
    }
    try {
      const res = await fetch("/api/jarvis/restart-server", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.ok === false) {
        alert(data.message || "Restart failed.");
        return;
      }
      const st = $("statusText");
      if (st) st.textContent = "Restarting server…";
      const back = await waitForServerBack();
      if (st) {
        st.textContent = back
          ? "Back online — reloading…"
          : "Restart slow — hard refresh if this stays stuck";
      }
      if (back) {
        if (window.mediaWorkActive?.()) {
          if (st) st.textContent = "Server back — image job still running (no reload)";
        } else {
          location.reload();
        }
      } else {
        alert(
          `${typeof ariaName === "function" ? ariaName() : "ARIA"} may still be restarting.\n\n`
          + "Try Ctrl+Shift+R to hard-refresh the page."
        );
      }
    } catch (_) {
      const back = await waitForServerBack();
      if (back) {
        if (window.mediaWorkActive?.()) {
          if (st) st.textContent = "Server back — image job still running (no reload)";
        } else {
          location.reload();
        }
      } else {
        const st = $("statusText");
        if (st) st.textContent = "Restart slow — hard refresh (Ctrl+Shift+R)";
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        if (prev) btn.textContent = prev;
      }
    }
  }

  async function waitForServerBack(maxMs = 90000) {
    const start = Date.now();
    const deadline = start + maxMs;

    // Let the tray begin shutdown before we treat /api/health as "back".
    await new Promise((r) => setTimeout(r, 500));

    let sawDown = false;
    const downDeadline = Math.min(deadline, Date.now() + 10000);
    while (Date.now() < downDeadline) {
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        if (!res.ok) {
          sawDown = true;
          break;
        }
      } catch (_) {
        sawDown = true;
        break;
      }
      await new Promise((r) => setTimeout(r, 350));
    }

    if (!sawDown) {
      await new Promise((r) => setTimeout(r, 1500));
    }

    while (Date.now() < deadline) {
      try {
        const res = await fetch("/api/health", { cache: "no-store" });
        if (res.ok) {
          const data = await res.json().catch(() => ({}));
          if (data.version) return true;
        }
      } catch (_) {}
      await new Promise((r) => setTimeout(r, 600));
    }
    return false;
  }

  function initServerRestart() {
    $("restartServerBtn")?.addEventListener("click", restartJarvisServer);
  }

  /* --- Upgrade restart (Tier 3 #24) --- */
  function initUpgradeRestart() {
    $("upgradeRestartBtn")?.addEventListener("click", restartJarvisServer);
  }

  /* --- Jarvis blue theme (Tier 4 #39) --- */
  function initJarvisBlue() {
    const btn = $("jarvisBlueToggle");
    const apply = (on) => {
      document.documentElement.classList.toggle("theme-jarvis-blue", on);
      localStorage.setItem(LS.jarvisBlue, on ? "1" : "0");
    };
    apply(localStorage.getItem(LS.jarvisBlue) !== "0");
    /* HUD toggle click handled by jarvis_ambient.js */
  }

  /* --- Keyboard shortcuts (Tier 4 #38) --- */
  function initShortcuts() {
    const modal = $("shortcutsModal");
    $("shortcutsBtn")?.addEventListener("click", () => modal?.classList.remove("hidden"));
    $("shortcutsCloseBtn")?.addEventListener("click", () => modal?.classList.add("hidden"));
    document.addEventListener("keydown", (e) => {
      if (e.target.matches("textarea, input") && !e.ctrlKey && !e.metaKey) return;
      if ((e.ctrlKey || e.metaKey) && e.key === "/") {
        e.preventDefault();
        modal?.classList.toggle("hidden");
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && e.shiftKey) {
        $("chatForm")?.requestSubmit();
      }
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && String(e.key).toLowerCase() === "r") {
        e.preventDefault();
        window.reloadJarvisUi?.();
      }
      if (e.key === "Escape") {
        modal?.classList.add("hidden");
        $("settingsModal")?.classList.add("hidden");
      }
    });
  }

  /* --- Integrations sidebar (API keys) --- */
  async function loadIntegrationsPanel() {
    const setLine = (el, set, preview) => {
      if (!el) return;
      el.textContent = set ? `Saved (${preview})` : "Not set";
    };
    try {
      const data = await fetchJson("/api/integrations/secrets");
      setLine($("integrationsGeminiStatus"), data.gemini_api_key_set, data.gemini_api_key_preview);
      setLine($("integrationsOpenaiStatus"), data.openai_api_key_set, data.openai_api_key_preview);
      setLine($("integrationsHfStatus"), data.hf_token_set, data.hf_token_preview);
      const line = $("integrationsStatusLine");
      if (line) {
        line.textContent = data.gemini_api_key_set
          ? "Cloud Live ready — use voice bar → Cloud live"
          : "Paste Gemini key below for Cloud Live voice";
      }
    } catch (_) {
      const line = $("integrationsStatusLine");
      if (line) line.textContent = "Could not load key status";
    }
  }

  async function loadIntegrationSecrets() {
    await loadIntegrationsPanel();
  }

  function initIntegrationsPanel() {
    loadIntegrationsPanel();
    $("integrationsSaveBtn")?.addEventListener("click", async () => {
      const body = {};
      const g = $("integrationsGeminiKey")?.value?.trim();
      const o = $("integrationsOpenaiKey")?.value?.trim();
      const h = $("integrationsHfToken")?.value?.trim();
      if (g) body.gemini_api_key = g;
      if (o) body.openai_api_key = o;
      if (h) body.hf_token = h;
      const msg = $("integrationsPanelMsg");
      if (!Object.keys(body).length) {
        if (msg) msg.textContent = "Paste at least one key, then Save.";
        return;
      }
      if (msg) msg.textContent = "Saving…";
      try {
        const res = await fetch("/api/integrations/secrets", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (res.status === 404) {
          if (msg) msg.textContent = "Server needs a restart first — sidebar → Restart server, then Save again.";
          return;
        }
        const data = await res.json().catch(() => ({}));
        if (!res.ok || data.ok === false) {
          if (msg) msg.textContent = data.message || data.detail || `Save failed (HTTP ${res.status})`;
          return;
        }
        if ($("integrationsGeminiKey") && g) $("integrationsGeminiKey").value = "";
        if ($("integrationsOpenaiKey") && o) $("integrationsOpenaiKey").value = "";
        if ($("integrationsHfToken") && h) $("integrationsHfToken").value = "";
        if (msg) {
          msg.textContent = data.gemini_api_key_set
            ? "Saved — Cloud Live is ready."
            : "Saved.";
        }
        await loadIntegrationsPanel();
      } catch (e) {
        if (msg) msg.textContent = String(e);
      }
    });
    $("integrationsSettingsBtn")?.addEventListener("click", () => {
      $("settingsModal")?.classList.remove("hidden");
    });
  }

  /* --- Settings modal (Tier 2 voice unified #8) --- */
  function initSettingsModal() {
    const modal = $("settingsModal");
    $("settingsBtn")?.addEventListener("click", () => modal?.classList.remove("hidden"));
    $("settingsCloseBtn")?.addEventListener("click", () => modal?.classList.add("hidden"));
  }

  /* --- Actions filter (Tier 4 #33) --- */
  function initActionsFilter() {
    const sel = $("actionsFilter");
    if (!sel) return;
    sel.addEventListener("change", () => {
      window.loadActions?.(sel.value);
    });
  }

  window.loadActions = async function (moduleFilter) {
    const el = $("actionsList");
    if (!el) return;
    const mod = moduleFilter ?? $("actionsFilter")?.value ?? "";
    const q = mod ? `?module=${encodeURIComponent(mod)}` : "";
    try {
      const data = await fetchJson(`/api/actions${q}`);
      const acts = data.actions || [];
      el.innerHTML = acts.length
        ? acts.map((a) => `<li><span class="act-time">${escapeHtml((a.time || "").slice(0, 19))}</span> `
          + `<strong>${escapeHtml(a.action || a.event || "")}</strong> `
          + `${a.module ? `<code>${escapeHtml(a.module)}</code> ` : ""}`
          + `${escapeHtml((a.detail || "").slice(0, 80))}</li>`).join("")
        : "<li class='muted'>No actions logged yet.</li>";
    } catch (_) {
      el.innerHTML = "<li>Could not load actions.</li>";
    }
  };

  /* --- Documents tab (Tier 2 #11) --- */
  async function loadDocumentsTab() {
    const list = $("documentsList");
    if (!list) return;
    try {
      const data = await fetchJson("/api/documents");
      const docs = data.documents || [];
      list.innerHTML = docs.length
        ? docs.map((d) => {
          const name = d.name || d.path || "?";
          const path = d.path || name;
          return `<li class="documents-row"><strong>${escapeHtml(name)}</strong> `
            + `<span class="muted">${escapeHtml(path)}</span> `
            + `<button type="button" class="ghost-btn tiny doc-attach" data-path="${escapeHtml(path)}">Attach</button> `
            + `<button type="button" class="ghost-btn tiny doc-summarize" data-path="${escapeHtml(path)}">Summarize</button> `
            + `<button type="button" class="ghost-btn tiny doc-learn" data-path="${escapeHtml(path)}">Learn</button></li>`;
        }).join("")
        : "<li class='muted'>Drop PDFs/DOCX in data/documents/</li>";
      list.querySelectorAll(".doc-attach").forEach((btn) => {
        btn.addEventListener("click", () => {
          const p = btn.dataset.path || "";
          const input = $("messageInput");
          if (input) {
            input.value = `summarize document ${p}`;
            input.focus();
          }
        });
      });
      list.querySelectorAll(".doc-summarize").forEach((btn) => {
        btn.addEventListener("click", () => {
          const p = btn.dataset.path || "";
          if (typeof window.sendMessage === "function") {
            window.sendMessage(`summarize ${p}`);
          }
        });
      });
      list.querySelectorAll(".doc-learn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const p = btn.dataset.path || "";
          if (!p) return;
          btn.disabled = true;
          const label = btn.textContent;
          btn.textContent = "Learning…";
          try {
            const data = await fetchJson("/api/documents/learn", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ path: p }),
            });
            if (typeof window.appendAssistantMessage === "function") {
              const msg = data.message
                || (data.ok ? `Learned from ${p}` : "Document learn failed");
              window.appendAssistantMessage(msg);
            } else if (typeof window.sendMessage === "function") {
              window.sendMessage(`learn from document ${p}`);
            }
          } catch (_) {
            if (typeof window.sendMessage === "function") {
              window.sendMessage(`learn from document ${p}`);
            }
          } finally {
            btn.disabled = false;
            btn.textContent = label;
          }
        });
      });
    } catch (_) {
      list.innerHTML = "<li>Could not load library</li>";
    }
  }

  async function searchDocumentsLibrary() {
    const q = $("documentsSearchInput")?.value?.trim();
    const out = $("documentsSearchResults");
    const list = $("documentsList");
    if (!out || !q) return;
    out.classList.remove("hidden");
    if (list) list.classList.add("hidden");
    out.innerHTML = "<li class='muted'>Searching…</li>";
    try {
      const data = await fetchJson(`/api/documents/search?q=${encodeURIComponent(q)}&limit=8`);
      const hits = data.hits || [];
      out.innerHTML = hits.length
        ? hits.map((h) => `<li><strong>${escapeHtml(h.title || h.source || "?")}</strong> `
          + `<span class="muted">${escapeHtml((h.text || "").slice(0, 120))}…</span></li>`).join("")
        : "<li class='muted'>No matches</li>";
    } catch (_) {
      out.innerHTML = "<li>Search failed</li>";
    }
  }

  $("documentsSearchBtn")?.addEventListener("click", searchDocumentsLibrary);
  $("documentsSearchInput")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") searchDocumentsLibrary();
  });

  $("documentsReindexBtn")?.addEventListener("click", async () => {
    const data = await fetchJson("/api/documents/reindex", { method: "POST" });
    const status = $("documentsIndexStatus");
    if (status) status.textContent = data.ok ? `Indexed ${data.chunks} chunks` : "Reindex failed";
    loadDocumentsTab();
    $("documentsList")?.classList.remove("hidden");
    $("documentsSearchResults")?.classList.add("hidden");
  });

  /* --- ICS wizard in journal (Tier 2 #12) --- */
  function initIcsWizard() {
    $("icsTestBtn")?.addEventListener("click", async () => {
      const url = $("icsUrlInput")?.value?.trim();
      const data = await fetchJson("/api/calendar/ics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, test_only: true }),
      });
      $("icsWizardStatus").textContent = data.message || (data.ok ? "OK" : "Failed");
    });
    $("icsSaveBtn")?.addEventListener("click", async () => {
      const url = $("icsUrlInput")?.value?.trim();
      const data = await fetchJson("/api/calendar/ics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      $("icsWizardStatus").textContent = data.message || "Saved";
    });
  }

  /* --- Task nudge (Tier 2 #19) --- */
  async function maybeTaskNudge() {
    try {
      const data = await fetchJson("/api/movie/task-nudge");
      if (!data.nudge) return;
      if (!confirm(data.message + "\n\nOpen journal?")) {
        await fetch("/api/movie/task-nudge/dismiss", { method: "POST" });
        return;
      }
      document.querySelector('.view-tab[data-view="journal"]')?.click();
      await fetch("/api/movie/task-nudge/dismiss", { method: "POST" });
    } catch (_) {}
  }

  /* --- Compact HUD (Tier 4 #32) --- */
  function initHud() {
    const hud = $("compactHud");
    $("hudToggleBtn")?.addEventListener("click", () => hud?.classList.toggle("hidden"));
    $("hudPttBtn")?.addEventListener("mousedown", () => chatMicDown());
    $("hudPttBtn")?.addEventListener("mouseup", () => chatMicUp());
  }

  /* --- Gallery last good (Tier 3 #28) --- */
  async function showLastGoodSettings() {
    const el = $("galleryLastGood");
    if (!el) return;
    try {
      const d = await fetchJson("/api/resources/last-good");
      const img = d.image || {};
      const vid = d.video || {};
      el.textContent = [
        img.width ? `Image: ${img.width}×${img.height}` : "",
        vid.frames ? `Video: ${vid.frames}f` : "",
      ].filter(Boolean).join(" · ") || "No successful renders yet";
    } catch (_) {}
  }

  /* --- Memory citations footer hook --- */
  window.jarvisRenderMemoryCitations = function (bubble, citations) {
    if (!bubble || !citations?.length) return;
    const foot = document.createElement("div");
    foot.className = "memory-citations muted";
    foot.innerHTML = citations.map((c) =>
      `From memory · ${escapeHtml(c.type)} · ${escapeHtml(c.date)} · ${escapeHtml(c.content.slice(0, 80))}`).join("<br>");
    bubble.appendChild(foot);
  };

  /* --- Coding job polling lives in app.js (jarvisPollCodingJob) --- */

  document.addEventListener("DOMContentLoaded", () => {
    $("pinnedBriefingDismiss")?.addEventListener("click", () => {
      $("pinnedBriefing")?.classList.add("hidden");
      fetch("/api/briefing/dismiss", { method: "POST" }).catch(() => {});
    });

    window.loadDocumentsTab = loadDocumentsTab;
    initSpeakToggle();
    initCollapsibleSections();
    initModuleFilter();
    initIntegrationsPanel();
    initChatMicPtt();
    initServiceRestart();
    initHaExtras();
    initUpgradeRestart();
    initServerRestart();
    initJarvisBlue();
    initShortcuts();
    initSettingsModal();
    initActionsFilter();
    initIcsWizard();
    initHud();
    $("wakePill")?.addEventListener("click", toggleWake);
    refreshEnvStrip();
    refreshWorldStateHud();
    refreshProfileBanner();
    refreshWakePill();
    loadPinnedBriefing();
    refreshTrustHealth();
    showLastGoodSettings();
    refreshContextSuggestions();
    setInterval(() => {
      if (window.mediaWorkActive?.()) return;
      refreshEnvStrip();
      refreshWorldStateHud();
    }, 60000);
    setInterval(() => {
      if (window.mediaWorkActive?.()) return;
      refreshWakePill();
    }, 15000);
    setTimeout(maybeTaskNudge, 8000);
    document.querySelectorAll(".view-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        if (tab.dataset.view === "documents") loadDocumentsTab();
      });
    });
  });
})();
