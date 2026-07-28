/** Activity deep-links & row actions — uses AriaActions, never silent .click()-only paths. */
(function () {
  "use strict";

  function toast(msg, kind = "info") {
    window.showAriaToast?.(msg, kind, 3000);
  }

  function openDeepLink(link, event) {
    const A = window.AriaActions;
    const raw = String(link || event?.deepLink || event?.source || "").trim();
    if (!raw) {
      toast("No destination for this event", "warn");
      return false;
    }
    if (typeof event?._actionFn === "function") {
      try {
        event._actionFn();
        return true;
      } catch (e) {
        toast(e.message || "Action failed", "err");
      }
    }
    if (raw === "automation") return A?.goView?.("automation");
    if (raw === "jobs" || raw.startsWith("job:")) {
      return A?.mission?.jobs?.() || A?.invoke?.("jobCenterBtn", "Job center");
    }
    if (raw.startsWith("view:")) return A?.goView?.(raw.slice(5));
    if (raw.startsWith("mc:")) return A?.goMc?.(raw.slice(3));
    if (raw === "mission" || raw === "workstation") return A?.goView?.("workstation");
    if (raw === "providers" || raw === "inference") return A?.goMc?.("inference");
    if (raw === "recovery") return A?.goMc?.("recovery");
    if (raw === "chat") return A?.goView?.("chat");
    if (raw === "memory") return A?.memory?.open?.();
    if (raw === "documents") return A?.documents?.open?.();
    if (raw === "connections") return A?.connections?.open?.();
    if (raw === "planner") return A?.planner?.open?.();
    if (raw === "calendar") return A?.calendar?.open?.();
    if (raw === "journal") return A?.journal?.open?.();
    if (raw === "projects") return A?.projects?.open?.();
    if (raw === "gallery") return A?.gallery?.open?.();
    if (raw === "voice") return A?.goView?.("voice");
    if (raw === "audit") return A?.audit?.open?.();
    // bare view id
    if (/^[a-z_]+$/i.test(raw)) return A?.goView?.(raw) ?? false;
    toast(`Unknown link: ${raw}`, "warn");
    return false;
  }

  function askAbout(event) {
    const e = event || {};
    const prompt = [
      "Explain this Aria Activity Center event and suggest concrete next steps.",
      `Title: ${e.title || ""}`,
      `Severity: ${e.severity || e.tone || ""}`,
      `Category: ${e.category || e.kind || ""}`,
      `Source: ${e.source || ""}`,
      `Detail: ${(e.detail || e.summary || "").slice(0, 800)}`,
      "If this looks like an inference/provider issue, recommend Mission Control diagnostics.",
      "Do not invent logs you cannot see.",
    ].join("\n");
    return window.AriaActions?.askAria?.(prompt, { autoSend: true, switchView: true }) ?? false;
  }

  function suggestFix(event) {
    const hay = `${event?.title || ""} ${event?.detail || ""} ${event?.category || ""}`.toLowerCase();
    if (/ollama|provider|model|inference|timeout/.test(hay)) {
      window.AriaActions?.goMc?.("inference");
      toast("Opening Mission Control · inference", "info");
      return true;
    }
    if (/job|media|comfy|video|image|coding/.test(hay)) {
      window.AriaActions?.mission?.jobs?.();
      return true;
    }
    if (/home assistant|ha |device/.test(hay)) {
      window.AriaActions?.system?.haTest?.();
      return true;
    }
    return askAbout(event);
  }

  function retry(event) {
    const hay = `${event?.title || ""} ${event?.category || ""}`.toLowerCase();
    if (/job/.test(hay) || event?.category === "job") {
      window.AriaActions?.system?.resumeMedia?.();
      window.AriaActions?.mission?.jobs?.();
      return true;
    }
    if (/document|index/.test(hay)) {
      window.AriaActions?.documents?.rebuild?.();
      return true;
    }
    if (/provider|ollama|router/.test(hay)) {
      window.AriaActions?.system?.warmRouter?.();
      window.AriaActions?.goMc?.("recovery");
      return true;
    }
    return suggestFix(event);
  }

  function whatsWrong() {
    const summary = window.AriaActivityStore?.summarizeUnread?.() || "No unread activity.";
    return window.AriaActions?.askAria?.(
      `Aria, what's wrong? Here is my Activity Center unread summary:\n\n${summary}\n\nPrioritize failures and suggest fixes.`,
      { autoSend: true, switchView: true },
    );
  }

  window.AriaActivityActions = {
    openDeepLink,
    askAbout,
    suggestFix,
    retry,
    whatsWrong,
  };

  function attachToAriaActions() {
    if (!window.AriaActions) return false;
    window.AriaActions.shell = window.AriaActions.shell || {};
    window.AriaActions.shell.activityWhatsWrong = whatsWrong;
    window.AriaActions.activity = {
      open: () => window.AriaActivity?.open?.(),
      whatsWrong,
      summarize: () => {
        const s = window.AriaActivityStore?.summarizeUnread?.() || "";
        toast(s.slice(0, 160), "info");
        return s;
      },
    };
    return true;
  }
  if (!attachToAriaActions()) {
    document.addEventListener("DOMContentLoaded", attachToAriaActions, { once: true });
    setTimeout(attachToAriaActions, 0);
  }
})();
