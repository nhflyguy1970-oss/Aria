/** AriaActions — stable product APIs for the Command Palette (no silent failures). */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function toast(msg, kind = "err", ms = 4000) {
    window.showAriaToast?.(String(msg || "Action failed"), kind, ms);
  }

  function goView(view) {
    if (typeof window.switchToView === "function") {
      window.switchToView(view);
      return true;
    }
    toast(`Cannot open view: ${view}`);
    return false;
  }

  function goMc(tab) {
    if (!goView("workstation") && !goView("mission")) return false;
    setTimeout(() => {
      if (typeof window.switchMcTab === "function") window.switchMcTab(tab);
      else toast(`Mission Control tab unavailable: ${tab}`);
    }, 50);
    return true;
  }

  function focusAfter(view, id, delay = 80) {
    if (view) goView(view);
    setTimeout(() => {
      const el = $(id);
      if (!el) {
        toast(`${id} unavailable`, "warn");
        return;
      }
      el.focus?.();
      el.select?.();
    }, delay);
    return true;
  }

  /** Invoke a control by id — fails loudly if missing. */
  function invoke(id, label) {
    const el = $(id);
    if (!el) {
      toast(`${label || id} unavailable`);
      return false;
    }
    try {
      el.click();
      return true;
    } catch (e) {
      toast(e.message || `Could not run ${label || id}`);
      return false;
    }
  }

  function openModal(id, label) {
    window.AriaModalPortal?.ensure?.();
    if (window.AriaModalPortal?.open?.(id)) return true;
    const el = $(id);
    if (!el) {
      toast(`${label || id} unavailable`);
      return false;
    }
    el.classList.remove("hidden");
    return true;
  }

  function runBackup() {
    const btn = $("backupDataBtn");
    if (btn && !btn.closest("[inert]")) {
      btn.click();
      return true;
    }
    window.showAriaToast?.("Backup starting…", "info");
    void (async () => {
      try {
        const res = await fetch("/api/admin/backup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ async: true }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.ok) {
          toast(data.message || "Backup failed");
          return;
        }
        if (data.pending && data.job_id) {
          window.showAriaToast?.(`Backup queued (${String(data.job_id).slice(0, 8)}…)`, "ok");
          window.jarvisJobs?.refreshJobCenter?.();
        } else {
          window.showAriaToast?.(data.message || "Backup complete", "ok");
        }
      } catch (e) {
        toast(e.message || "Backup failed");
      }
    })();
    return true;
  }

  function runDebugBundle() {
    const btn = $("debugBundleBtn");
    if (btn && !btn.closest("[inert]")) {
      btn.click();
      return true;
    }
    void (async () => {
      try {
        const res = await fetch("/api/debug/bundle");
        const data = await res.json();
        const text = data.text || JSON.stringify(data, null, 2);
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(text);
          window.showAriaToast?.("Debug bundle copied", "ok", 2500);
        } else {
          if (window.ariaPrompt) {
            await window.ariaPrompt("Copy debug bundle:", text.slice(0, 8000), {
              title: "Debug bundle",
              okLabel: "Close",
            });
          } else {
            prompt("Copy debug bundle:", text.slice(0, 8000));
          }
        }
      } catch (e) {
        toast(`Debug bundle failed: ${e.message || e}`);
      }
    })();
    return true;
  }

  function toggleUncensored() {
    if (typeof window.toggleAriaUncensored === "function") {
      return window.toggleAriaUncensored();
    }
    window.AriaModalPortal?.ensure?.();
    const el = $("uncensoredToggle");
    if (!el) {
      toast("Uncensored unavailable");
      return false;
    }
    const currentlyOn = document.body.classList.contains("uncensored-mode") || el.checked;
    el.checked = !currentlyOn;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function toggleTheme() {
    const next = document.body.classList.contains("light-theme") ? "dark" : "light";
    if (typeof window.setAriaTheme === "function") {
      window.setAriaTheme(next, {
        successToast: next === "light" ? "Professional Light" : "Professional Dark",
      });
      return true;
    }
    return invoke("themeToggle", "Theme");
  }

  function askAria(text, opts = {}) {
    const msg = String(text || "").trim();
    if (!msg) {
      toast("Nothing to ask", "warn");
      return false;
    }
    const ask = window.jarvisAskAria || window.AriaChatOS?.askAria;
    if (typeof ask === "function") {
      ask(msg, { autoSend: true, switchView: opts.switchView !== false, ...opts });
      return true;
    }
    // Fallback path still auto-sends
    goView("chat");
    setTimeout(() => {
      if (typeof window.sendMessage === "function") window.sendMessage(msg);
      else {
        const input = $("messageInput");
        if (input) input.value = msg;
        $("chatForm")?.requestSubmit?.();
      }
    }, 60);
    return true;
  }

  function newChat(title) {
    if (window.AriaChatOS?.newChat) {
      window.AriaChatOS.newChat(title);
      return true;
    }
    return invoke("chatNewBtn", "New Chat");
  }

  function setSelect(id, value, label) {
    const el = $(id);
    if (!el) {
      toast(`${label || id} unavailable`);
      return false;
    }
    el.value = value;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function openVisionAction(action, label) {
    goView("vision");
    setTimeout(() => {
      const path = $("visionHomePath");
      const btn = [...document.querySelectorAll("#visionHomeActions button")].find((el) => el.title === action);
      document.getElementById("visionView")?.scrollIntoView({ block: "start", behavior: "smooth" });
      if (!path?.value?.trim()) {
        path?.focus?.();
        toast(`${label}: enter an image path, then run ${label}`, "info", 5000);
        return;
      }
      if (btn) btn.click();
      else toast(`${label} action unavailable`, "warn");
    }, 180);
    return true;
  }

  const AriaActions = {
    goView,
    goMc,
    focusAfter,
    invoke,
    openModal,
    askAria,
    newChat,
    setSelect,

    chat: {
      focus: () => focusAfter("chat", "messageInput"),
      clear: () => invoke("clearBtn", "Clear conversation"),
      stop: () => invoke("stopChatBtn", "Stop responding"),
      readAloud: () => invoke("readAloudBtn", "Read aloud"),
      exportMd: () => invoke("exportChatBtn", "Export Markdown"),
      exportPdf: () => invoke("exportChatPdfBtn", "Export PDF"),
      newBranch: () => invoke("newBranchBtn", "Fork / new branch") || newChat(),
      compare: () => {
        goView("chat");
        return invoke("compareModeBtn", "Compare images");
      },
      webcam: () => invoke("webcamBtn", "Webcam"),
    },

    planner: {
      open: () => goView("planner"),
      focusTask: () => focusAfter("planner", "plannerTaskInput"),
      pomodoro: () => {
        goView("planner");
        setTimeout(() => {
          if (!invoke("plannerPomodoroBtn", "Pomodoro")) {
            document.querySelector('[data-pf="focus"]')?.click();
          }
        }, 80);
        return true;
      },
      triage: () => {
        goView("planner");
        setTimeout(() => {
          const btn = document.querySelector('[data-pf="triage"]');
          if (btn) btn.click();
          else toast("Plan My Day unavailable", "warn");
        }, 120);
        return true;
      },
      undo: () => {
        goView("planner");
        setTimeout(() => {
          const btn = document.querySelector('[data-pf="undo"]');
          if (btn) btn.click();
          else toast("Planner undo unavailable", "warn");
        }, 120);
        return true;
      },
    },

    calendar: {
      open: () => goView("calendar"),
      today: () => {
        goView("calendar");
        setTimeout(() => {
          if ($("calendarTodayBtn")) invoke("calendarTodayBtn", "Calendar today");
          else {
            const day = new Date().toISOString().slice(0, 10);
            if (typeof window.openCalendarDay === "function") window.openCalendarDay(day);
            else toast("Calendar today unavailable");
          }
        }, 80);
        return true;
      },
      view: (name) => {
        goView("calendar");
        setTimeout(() => {
          const btn = document.querySelector(`[data-cal-view="${name}"]`);
          if (btn) btn.click();
          else toast(`Calendar ${name} view unavailable`, "warn");
        }, 100);
        return true;
      },
      focusNl: () => focusAfter("calendar", "calNlInput", 120),
      focusIcs: () => {
        goView("calendar");
        setTimeout(() => {
          const details = $("calendarIcsUrl")?.closest("details");
          if (details) details.open = true;
          focusAfter(null, "calendarIcsUrl", 0);
        }, 100);
        return true;
      },
    },

    journal: {
      open: () => goView("journal"),
      rapid: () => focusAfter("journal", "rapidLogInput"),
      search: () => focusAfter("journal", "journalSearch"),
      today: () => askAria("Journal today", { returnView: "journal" }),
    },

    health: {
      open: () => goView("health"),
      checkin: () => {
        goView("health");
        setTimeout(() => document.querySelector('.health-tab[data-htab="checkin"]')?.click(), 60);
        return true;
      },
      search: () => focusAfter("health", "healthSearch"),
      doctor: () => askAria("Prepare for my doctor appointment.", { returnView: "health" }),
      emergency: () => askAria("Emergency summary", { returnView: "health" }),
    },

    memory: {
      open: () => goView("memory"),
      search: () => focusAfter("memory", "memorySearch"),
      recall: () => askAria("What do you remember about me?", { returnView: "memory" }),
      research: () => invoke("runResearchBtn", "Knowledge research") || askAria("Run nightly knowledge research now"),
    },

    documents: {
      open: () => goView("documents"),
      search: () => focusAfter("documents", "documentsSearchInput"),
      rebuild: () => {
        goView("documents");
        setTimeout(() => invoke("documentsRebuildBtn", "Rebuild document index"), 80);
        return true;
      },
      upload: () => {
        goView("documents");
        setTimeout(() => invoke("documentsFileInput", "Upload documents"), 80);
        return true;
      },
    },

    connections: {
      open: () => goView("connections"),
      search: () => focusAfter("connections", "connectionsSearchInput"),
      import: () => {
        goView("connections");
        setTimeout(() => invoke("connectionsImportBtn", "Import connections"), 80);
        return true;
      },
      cleanup: () => {
        goView("connections");
        setTimeout(() => invoke("connectionsCleanupBtn", "Cleanup connections"), 80);
        return true;
      },
    },

    projects: {
      open: () => goView("projects"),
      create: () => focusAfter("projects", "projectsTitleInput"),
      codingMode: () => {
        if (window.openCodingHome) {
          window.openCodingHome();
          return true;
        }
        goView("chat");
        setTimeout(() => {
          const chip = document.querySelector('.module-chip[data-module="coding"]');
          if (chip) chip.click();
          else toast("Coding mode chip unavailable", "warn");
        }, 80);
        return true;
      },
    },

    coding: {
      open: () => window.openCodingHome?.() || goView("coding"),
      history: () => window.openCodingHome?.("history") || goView("coding"),
      verify: () => window.AriaCodingVerify?.promptLast?.() || false,
      undo: () => {
        fetch("/api/undo-apply", { method: "POST" })
          .then((r) => r.json())
          .then((d) => toast(d.message || "Undo", d.ok === false ? "err" : "ok"))
          .catch((e) => toast(e.message || "Undo failed", "err"));
        return true;
      },
    },

    gallery: {
      open: () => window.openGalleryHome?.() || goView("gallery"),
      focusPrompt: () => focusAfter("gallery", "galleryPromptInput"),
      generate: () => {
        window.openGalleryHome?.() || goView("gallery");
        focusAfter("gallery", "galleryPromptInput");
        setTimeout(() => {
          const prompt = document.getElementById("galleryPromptInput")?.value?.trim();
          if (!prompt) {
            document.getElementById("galleryPromptInput")?.focus();
            toast("Enter an image description, then Generate", "warn");
            return;
          }
          if (typeof window.galleryGenerateInGallery === "function") {
            window.galleryGenerateInGallery();
          } else {
            document.getElementById("galleryGenerateBtn")?.click();
          }
        }, 80);
      },
    },

    vision: {
      open: () => goView("vision"),
      focusPath: () => focusAfter("vision", "visionHomePath"),
      ocr: () => openVisionAction("ocr", "OCR"),
      structuredOcr: () => openVisionAction("ocr_structured", "Structured OCR"),
    },

    video: {
      open: () => goView("video"),
      studio: () => invoke("openVideoStudioBtn", "Video studio") || goView("video"),
      storyboard: () => focusAfter("video", "storyboardPathsInput"),
      generate: () => {
        window.openVideoStudio?.() || goView("video");
        focusAfter("video", "videoPromptInput");
        setTimeout(() => {
          const prompt = document.getElementById("videoPromptInput")?.value?.trim();
          if (!prompt) {
            document.getElementById("videoPromptInput")?.focus();
            toast("Enter a video description, then Generate", "warn");
            return;
          }
          if (typeof window.videoGenerateInStudio === "function") {
            window.videoGenerateInStudio();
          } else {
            document.getElementById("videoGenerateBtn")?.click();
          }
        }, 80);
      },
    },

    audio: {
      open: () => goView("audio"),
    },

    browser: {
      open: () => window.openBrowserHome?.() || goView("browser"),
      focusUrl: () => focusAfter("browser", "browserUrlInput"),
      focusTask: () => focusAfter("browser", "browserGoalInput") || focusAfter("browser", "browserTaskInput"),
      research: () => {
        window.openBrowserHome?.("research");
        return askAria("Help me research a topic. Ask what I want to look up and how deep to go.");
      },
    },

    voice: {
      mute: () => invoke("voiceMuteBtn", "Mute TTS"),
      speakToggle: () => {
        const cb = $("speakRepliesToggle");
        if (!cb) {
          toast("Read aloud unavailable");
          return false;
        }
        cb.checked = !cb.checked;
        cb.dispatchEvent(new Event("change", { bubbles: true }));
        return true;
      },
      stopSpeaking: () => invoke("audioStopBtn", "Stop speaking"),
      cloudLive: () => invoke("cloudLiveBtn", "Cloud Live"),
      smoke: () => invoke("voiceSmokeBtn", "Voice smoke") || askAria("Run voice smoke test"),
      serverWhisper: () => invoke("serverWhisperToggle", "Server Whisper"),
    },

    mission: {
      diagnostics: () => goMc("inference"),
      recovery: () => goMc("recovery"),
      jobs: () => invoke("jobCenterBtn", "Job center"),
      activity: () => {
        if (window.AriaActivity?.open) { window.AriaActivity.open(); return true; }
        return invoke("activityCenterBtn", "Activity Center");
      },
      routingSearch: () => {
        goMc("routing");
        setTimeout(() => focusAfter(null, "mcRoutingSearch", 0), 200);
        return true;
      },
    },

    system: {
      settings: () => {
        window.openSettingsHome?.() || window.switchToView?.("settings");
      },
      voiceChatSettings: () => window.openVoiceChatSettings?.(),
      shortcuts: () => openModal("shortcutsModal", "Shortcuts") || invoke("shortcutsBtn", "Shortcuts"),
      backup: () => runBackup(),
      debugBundle: () => runDebugBundle(),
      reloadUi: () => {
        if (typeof window.reloadJarvisUi === "function") {
          window.reloadJarvisUi();
          return true;
        }
        return invoke("reloadUiBtn", "Reload UI");
      },
      resetSidebar: () => invoke("resetLayoutBtn", "Expand sidebar"),
      theme: () => toggleTheme(),
      freeVram: () => {
        if (typeof window.freeJarvisVram === "function") {
          void window.freeJarvisVram(document.getElementById("statusText"));
          return true;
        }
        return invoke("freeVramBtn", "Free VRAM");
      },
      lock: () => {
        if (typeof window.jarvisLockHouse === "function") {
          void window.jarvisLockHouse({ hard: true });
          return true;
        }
        return invoke("ownerLockBtn", "Lock Aria") || invoke("securityLockBtn", "Lock now") || goView("security");
      },
      uncensored: () => toggleUncensored(),
      lanCopy: () => invoke("lanCopyBtn", "Copy LAN URL"),
      upgrade: () => invoke("upgradeWizardBtn", "Upgrade wizard") || openModal("upgradeWizardModal", "Upgrade wizard"),
      haSetup: () => invoke("haSetupWizardBtn", "HA setup") || openModal("haSetupModal", "HA setup"),
      haTest: () => invoke("haTestBtn", "HA test"),
      imageEngine: () => {
        window.openGalleryHome?.() || goView("gallery");
        setTimeout(() => {
          document.getElementById("imageEnginePanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
          document.getElementById("galleryCheckpointSelect")?.focus();
        }, 80);
        return true;
      },
      apiKeys: () => invoke("apiKeysBtn", "API keys") || openModal("apiKeyModal", "API keys"),
      gitStatus: () => invoke("gitRefreshBtn", "Git status"),
      pullModels: () => invoke("pullMissingBtn", "Pull missing models") || invoke("pullModelsBtn", "Pull models"),
      lsp: () => invoke("lspDiagBtn", "LSP diagnostics"),
      reindexCode: () => invoke("reindexCodeBtn", "Reindex code"),
      checklist: () => invoke("firstFlightBtn", "First-flight checklist") || goView("actions"),
      resumeMedia: () => {
        if (typeof window.resumePendingMediaJobs === "function") {
          window.resumePendingMediaJobs();
          return true;
        }
        toast("Resume media jobs unavailable", "warn");
        return false;
      },
      modelsEditor: () => {
        if (window.openModelsHome) {
          window.openModelsHome("roles");
          return true;
        }
        if (goView("models")) return true;
        const tog = $("modelsToggle") || $("modelsEditorToggle") || document.querySelector("[data-models-editor]");
        if (tog) {
          tog.click();
          return true;
        }
        return invoke("modelsHomeOpenBtn", "Models Home");
      },
      modelsHome: () => window.openModelsHome?.() || goView("models"),
      codingHome: () => window.openCodingHome?.() || goView("coding"),
      warmRouter: () => invoke("routerWarmBtn", "Warm router") || askAria("Warm the model router"),
    },

    shell: {
      activity: () => AriaActions.mission.activity(),
      workspaces: () => {
        if (window.AriaLayouts?.openModal) {
          window.AriaLayouts.openModal();
          return true;
        }
        if (window.AriaWorkspaces?.openModal) {
          window.AriaWorkspaces.openModal();
          return true;
        }
        toast("Layouts unavailable", "warn");
        return false;
      },
      split: () => {
        if (window.AriaSplitView?.toggle) { window.AriaSplitView.toggle(); return true; }
        toast("Split view unavailable", "warn");
        return false;
      },
      miniChat: () => {
        if (window.AriaMiniChat?.toggle) { window.AriaMiniChat.toggle(); return true; }
        toast("Mini chat unavailable", "warn");
        return false;
      },
      workflows: () => {
        if (window.AriaViewPaths?.openModal) { window.AriaViewPaths.openModal(); return true; }
        if (window.AriaWorkflows?.openModal) { window.AriaWorkflows.openModal(); return true; }
        return invoke("workflowOpenBtn", "View Paths");
      },
      automation: () => goView("automation"),
      viewPaths: () => AriaActions.shell.workflows(),
      customizeDash: () => {
        if (window.AriaDashboardWidgets?.openCustomize) {
          window.AriaDashboardWidgets.openCustomize();
          return true;
        }
        toast("Dashboard customize unavailable", "warn");
        return false;
      },
    },

    maker: {
      open: () => goView("maker"),
      design: () => askAria("Help me design a printable part. Ask for dimensions, material, and constraints."),
    },

    flytying: {
      open: () => goView("flytying"),
      search: () => focusAfter("flytying", "flytyingSearchInput"),
      seasonal: () => {
        goView("flytying");
        setTimeout(() => invoke("flytyingSeasonalBtn", "Seasonal patterns"), 80);
        return true;
      },
    },

    meme: {
      open: () => goView("meme"),
    },

    audit: {
      open: () => goView("audit"),
      run: () => {
        goView("audit");
        setTimeout(() => invoke("auditRunBtn", "Run audit"), 80);
        return true;
      },
    },
  };

  window.AriaActions = AriaActions;
})();
