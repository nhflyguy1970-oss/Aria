/** Activity event producers — instrument Aria OS subsystems into the durable inbox. */
(function () {
  "use strict";

  const seen = {
    ollamaUp: null,
    startup: false,
  };

  function pub(evt) {
    return window.AriaActivityStore?.publish?.(evt) || window.AriaActivity?.publish?.(evt);
  }

  function emit(category, type, severity, title, detail, deepLink, extra = {}) {
    return pub({
      category,
      type,
      severity,
      title,
      summary: detail,
      detail,
      source: extra.source || category,
      deepLink: deepLink || extra.deepLink || category,
      context: extra.context || {},
      metadata: extra.metadata || {},
      groupId: extra.groupId || "",
      actions: extra.actions,
      read: extra.read === true,
      priority: extra.priority,
    });
  }

  const Producers = {
    chat: {
      failure: (msg) => emit("chat", "conversation_failure", "error", "Chat failure", msg, "chat"),
      provider: (msg) => emit("chat", "provider_failure", "error", "Provider failure", msg, "providers", { source: "inference" }),
      stream: (msg) => emit("chat", "stream_interrupt", "warning", "Streaming interrupted", msg, "chat"),
      context: (msg) => emit("chat", "context_failure", "warning", "Context failure", msg, "chat"),
    },
    memory: {
      staged: (msg) => emit("memory", "candidate_staged", "info", "Memory candidate staged", msg, "memory", { read: true }),
      merge: (msg) => emit("memory", "merge", "info", "Memory merge", msg, "memory", { read: true }),
      conflict: (msg) => emit("memory", "conflict", "warning", "Memory conflict", msg, "memory"),
      repair: (msg) => emit("memory", "repair", "info", "Memory repair", msg, "memory", { read: true }),
    },
    documents: {
      import: (msg) => emit("documents", "import", "info", "Document import", msg, "documents", { read: true }),
      indexing: (msg) => emit("documents", "indexing", "info", "Document indexing", msg, "documents", { read: true }),
      extraction: (msg) => emit("documents", "extraction", "info", "Document extraction", msg, "documents", { read: true }),
      ocr: (msg) => emit("documents", "ocr", "info", "OCR complete", msg, "documents", { read: true }),
      failure: (msg) => emit("documents", "failure", "error", "Document failure", msg, "documents"),
      complete: (msg) => emit("documents", "complete", "success", "Document ready", msg, "documents", { read: true }),
    },
    connections: {
      import: (msg) => emit("connections", "import", "info", "Connections import", msg, "connections", { read: true }),
      merge: (msg) => emit("connections", "merge", "info", "Connections merge", msg, "connections", { read: true }),
      repair: (msg) => emit("connections", "repair", "info", "Connections repair", msg, "connections", { read: true }),
      review: (msg) => emit("connections", "review", "warning", "Connections need review", msg, "connections"),
    },
    planner: {
      created: (msg) => emit("planner", "created", "info", "Planner item created", msg, "planner", { read: true }),
      completed: (msg) => emit("planner", "completed", "success", "Planner item completed", msg, "planner", { read: true }),
      failed: (msg) => emit("planner", "failed", "error", "Planner failure", msg, "planner"),
      reminder: (msg) => emit("planner", "reminder", "warning", "Planner reminder", msg, "planner"),
    },
    calendar: {
      missed: (msg) => emit("calendar", "missed", "warning", "Missed calendar event", msg, "calendar"),
      reminder: (msg) => emit("calendar", "reminder", "warning", "Calendar reminder", msg, "calendar"),
      conflict: (msg) => emit("calendar", "conflict", "warning", "Calendar conflict", msg, "calendar"),
    },
    journal: {
      save: (msg) => emit("journal", "save", "info", "Journal saved", msg, "journal", { read: true }),
      sync: (msg) => emit("journal", "sync", "info", "Journal sync", msg, "journal", { read: true }),
      failure: (msg) => emit("journal", "failure", "error", "Journal failure", msg, "journal"),
    },
    projects: {
      created: (msg) => emit("projects", "created", "info", "Project created", msg, "projects", { read: true }),
      deleted: (msg) => emit("projects", "deleted", "warning", "Project deleted", msg, "projects"),
      build: (msg) => emit("projects", "build", "info", "Project build", msg, "projects", { read: true }),
      failure: (msg) => emit("projects", "failure", "error", "Project failure", msg, "projects"),
    },
    gallery: {
      complete: (msg) => emit("gallery", "generation_complete", "success", "Generation complete", msg, "gallery", { read: true }),
      failed: (msg) => emit("gallery", "generation_failed", "error", "Generation failed", msg, "gallery"),
      compare: (msg) => emit("gallery", "comparison_complete", "success", "Comparison complete", msg, "gallery", { read: true }),
    },
    video: {
      complete: (msg) => emit("video", "generation_complete", "success", "Video ready", msg, "video", { read: true }),
      failed: (msg) => emit("video", "generation_failed", "error", "Video failed", msg, "video"),
    },
    voice: {
      recognition: (msg) => emit("voice", "recognition_failure", "error", "Voice recognition failed", msg, "voice"),
      wake: (msg) => emit("voice", "wake_failure", "warning", "Wake word failure", msg, "voice"),
      recording: (msg) => emit("voice", "recording_complete", "success", "Recording complete", msg, "voice", { read: true }),
    },
    vision: {
      complete: (msg) => emit("vision", "analysis_complete", "success", "Vision analysis complete", msg, "chat", { read: true }),
      failure: (msg) => emit("vision", "analysis_failure", "error", "Vision analysis failed", msg, "chat"),
    },
    coding: {
      applied: (msg) => emit("coding", "patch_applied", "success", "Patch applied", msg, "projects", { read: true }),
      rejected: (msg) => emit("coding", "rejected", "warning", "Patch rejected", msg, "projects"),
      conflict: (msg) => emit("coding", "merge_conflict", "error", "Merge conflict", msg, "projects"),
    },
    automation: {
      complete: (msg) => emit("automation", "workflow_complete", "success", "Workflow complete", msg, "jobs", { read: true }),
      failed: (msg) => emit("automation", "workflow_failed", "error", "Workflow failed", msg, "jobs"),
    },
    models: {
      switched: (msg) => emit("models", "model_switched", "success", "Model switched", msg, "models", { read: true }),
      pullFailed: (msg) => emit("models", "pull_failed", "error", "Model pull failed", msg, "models"),
      vram: (msg) => emit("models", "vram_warning", "warning", "VRAM warning", msg, "mc:inference"),
    },
    mission: {
      health: (msg) => emit("mission", "health", "warning", "Mission Control health", msg, "mission"),
      warning: (msg) => emit("mission", "warning", "warning", "System warning", msg, "mission"),
      recovery: (msg) => emit("mission", "recovery", "info", "Recovery action", msg, "recovery", { read: true }),
      critical: (msg, fix) => emit("mission", "critical_health", "error", "Mission Control · critical health", msg, fix || "mc:recovery"),
      verified: (msg) => emit("mission", "verification", "success", "Post-repair verification", msg, "mc:overview", { read: true }),
    },
    providers: {
      offline: (msg) => emit("providers", "offline", "error", "Provider offline", msg, "providers"),
      recovered: (msg) => emit("providers", "recovered", "success", "Provider recovered", msg, "providers", { read: true }),
      restarted: (msg) => emit("providers", "inference_restarted", "info", "Inference restarted", msg, "providers", { read: true }),
    },
    browser: {
      read: (msg) => emit("browser", "read_page", "info", "Page read", msg, "chat", { read: true }),
      capture: (msg) => emit("browser", "capture_failure", "error", "Browser capture failed", msg, "chat"),
    },
    home: {
      finished: (msg) => emit("home", "automation_finished", "success", "HA automation finished", msg, "ha", { read: true }),
      failed: (msg) => emit("home", "automation_failed", "error", "HA automation failed", msg, "ha"),
      offline: (msg) => emit("home", "device_offline", "warning", "HA device offline", msg, "ha"),
    },
    system: {
      startup: (msg) => emit("system", "startup", "info", "Aria started", msg, "", { read: true, source: "system" }),
      shutdown: (msg) => emit("system", "shutdown", "info", "Aria shutting down", msg, "", { read: true, source: "system" }),
      updates: (msg) => emit("system", "updates", "info", "Update available", msg, "settings"),
    },
  };

  function classifyChatError(text) {
    const t = String(text || "").toLowerCase();
    if (/ollama|provider|timeout|connect|refus|inference/.test(t)) return Producers.chat.provider(text);
    if (/stream|abort|network/.test(t)) return Producers.chat.stream(text);
    if (/context|token|truncat/.test(t)) return Producers.chat.context(text);
    return Producers.chat.failure(text);
  }

  function hookShowError() {
    const orig = window.showError;
    if (typeof orig !== "function" || orig._ariaActivityWrapped) return;
    const wrapped = function (msg) {
      const plain = String(msg || "").replace(/\*\*/g, "").slice(0, 500);
      window.__ariaActivitySuppressToast = true;
      try {
        classifyChatError(plain);
        return orig.apply(this, arguments);
      } finally {
        window.__ariaActivitySuppressToast = false;
      }
    };
    wrapped._ariaActivityWrapped = true;
    window.showError = wrapped;
  }

  function hookProviderRecovery() {
    const orig = window.showProviderRecovery;
    if (typeof orig !== "function" || orig._ariaActivityWrapped) return;
    const wrapped = function (message, opts) {
      Producers.chat.provider(message || opts?.reason || "Provider timeout");
      Producers.mission.warning(message || "Model provider timed out");
      return orig.apply(this, arguments);
    };
    wrapped._ariaActivityWrapped = true;
    window.showProviderRecovery = wrapped;
  }

  function hookJarvisNotifySuccess() {
    // gallery / coding completions often go through jarvisNotify — center already wraps it;
    // enrich category when title matches known patterns via a secondary listener.
    window.addEventListener("aria-activity-change", () => {
      /* badge handled elsewhere */
    });
  }

  async function pollProviders() {
    if (document.hidden) return;
    try {
      const res = await fetch("/api/mission-control/health", { cache: "no-store" });
      if (!res.ok) {
        // soft fallback
        const r2 = await fetch("/api/status", { cache: "no-store" }).catch(() => null);
        if (!r2 || !r2.ok) return;
        const st = await r2.json().catch(() => ({}));
        const up = st.ollama_running ?? st.ollama ?? null;
        if (up === false && seen.ollamaUp !== false) {
          Producers.providers.offline("Ollama / inference appears offline");
        } else if (up === true && seen.ollamaUp === false) {
          Producers.providers.recovered("Ollama / inference is back");
        }
        if (up != null) seen.ollamaUp = Boolean(up);
        return;
      }
      const data = await res.json().catch(() => ({}));
      if (data.dangerous || data.overall === "critical" || data.severity === "critical") {
        const msg = String((data.critical_issues && data.critical_issues[0]) || data.reason || "Critical infrastructure health").slice(0, 200);
        const key = `mc_crit_${msg}`;
        if (seen[key] !== true) {
          seen[key] = true;
          Producers.mission.critical(msg, "mc:recovery");
        }
      } else if (data.ok === false || data.overall === "degraded") {
        Producers.mission.health(String(data.reason || "Mission Control degraded").slice(0, 200));
      }
    } catch {
      /* offline */
    }
  }

  async function pollCalendarMissed() {
    if (document.hidden) return;
    try {
      const today = new Date().toISOString().slice(0, 10);
      const res = await fetch(`/api/calendar/day?date=${encodeURIComponent(today)}`, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json().catch(() => ({}));
      const items = data.items || data.events || [];
      const nowMin = new Date().getHours() * 60 + new Date().getMinutes();
      items.forEach((it) => {
        const time = String(it.time || it.start || "").slice(0, 5);
        const m = time.match(/^(\d{1,2}):(\d{2})$/);
        if (!m) return;
        const mins = Number(m[1]) * 60 + Number(m[2]);
        if (mins < nowMin - 15 && !it.completed && !it.done) {
          const key = `cal_missed_${today}_${it.id || it.title || time}`;
          const exists = window.AriaActivityStore?.all?.()?.some((e) => e.metadata?.missKey === key);
          if (exists) return;
          emit("calendar", "missed", "warning", `Missed: ${it.title || it.content || "event"}`,
            `Scheduled ${time}`, "calendar", { metadata: { missKey: key } });
        }
      });
    } catch {
      /* calendar optional */
    }
  }

  function seedStartup() {
    if (seen.startup) return;
    seen.startup = true;
    const flag = sessionStorage.getItem("aria_activity_startup_v1");
    if (flag) return;
    Producers.system.startup("Aria UI session ready — Activity Center is listening.");
    try {
      sessionStorage.setItem("aria_activity_startup_v1", "1");
    } catch {
      /* ignore */
    }
  }

  function rehook() {
    hookShowError();
    hookProviderRecovery();
    window.AriaActivity?.open && window.AriaActivityCenter?.hookToasts?.();
  }

  function init() {
    seedStartup();
    hookShowError();
    hookProviderRecovery();
    hookJarvisNotifySuccess();
    setTimeout(pollProviders, 5000);
    setInterval(pollProviders, 120000);
    setTimeout(pollCalendarMissed, 12000);
    setInterval(pollCalendarMissed, 5 * 60 * 1000);
    // showError / toast may load late — rehook a few times
    [500, 2000, 5000].forEach((ms) => setTimeout(rehook, ms));
  }

  window.AriaActivityProducers = Producers;
  window.emitAriaActivity = emit;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
