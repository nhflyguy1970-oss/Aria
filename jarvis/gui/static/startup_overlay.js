/** Startup overlay / service wait — extracted from app.js. */
(function () {
  "use strict";

const overlay = document.getElementById("startupOverlay");
const startupStatus = document.getElementById("startupStatus");
const startupLog = document.getElementById("startupLog");
const fetchWithTimeout = (...args) => window.fetchWithTimeout(...args);
const ariaName = () => window.ariaName?.() || "Aria";
const renderServices = (...args) => window.renderServices?.(...args);

function hideStartupOverlay(message) {
  if (startupStatus && message) startupStatus.textContent = message;
  overlay?.classList.add("hidden");
  window.jarvisFlashSystemsOnline?.();
}

function appendStartupLog(msg) {
  if (!startupLog || !msg) return;
  const li = document.createElement("li");
  li.textContent = msg;
  startupLog.appendChild(li);
  startupLog.scrollTop = startupLog.scrollHeight;
}

async function waitForServices(maxAttempts = 12) {
  if (!overlay) return true;
  try {
    const live = await fetchWithTimeout("/api/live", {}, 2500);
    if (live.ok) {
      const data = await live.json();
      if (data.ready) {
        hideStartupOverlay(`${ariaName()} ready.`);
        return true;
      }
    }
  } catch (_) {
    /* server may be busy with ComfyUI — show overlay below */
  }
  overlay.classList.remove("hidden");
  startupStatus.textContent = "Bringing services online…";
  let ensured = false;

  for (let i = 0; i < maxAttempts; i++) {
    try {
      let res = await fetchWithTimeout("/api/services", {}, 4000);
      if (!res.ok && !ensured) {
        ensured = true;
        await fetchWithTimeout("/api/services/ensure", { method: "POST" }, 8000);
        await new Promise((r) => setTimeout(r, 800));
        res = await fetchWithTimeout("/api/services", {}, 4000);
      }
      if (res.ok) {
        const data = await res.json();
        if (data.boot_log) data.boot_log.slice(-5).forEach(appendStartupLog);
        renderServices(data.services, data.comfyui_settings);
        if (data.ready) {
          try {
            const sumRes = await fetchWithTimeout("/api/workstation/startup-summary", {}, 4000);
            if (sumRes.ok) {
              const summary = await sumRes.json();
              const md = summary.summary || summary.markdown || "";
              appendStartupLog(md.split("\n").filter((l) => l.trim()).slice(0, 8).join(" · "));
              hideStartupOverlay(summary.greeting ? `${summary.greeting} — ready.` : `All set — ${ariaName()} is ready.`);
              return true;
            }
          } catch (_) {
            /* fall through */
          }
          hideStartupOverlay(`All set — ${ariaName()} is ready.`);
          return true;
        }
        const pending = (data.services || []).filter((s) => s.required && !s.running).map((s) => s.label);
        startupStatus.textContent = pending.length
          ? `Waiting for ${pending.join(", ")}…`
          : "Almost ready…";
      }
    } catch (_) {
      startupStatus.textContent = i > 2
        ? `${ariaName()} is busy (video/image gen?) — click Skip or wait…`
        : `Connecting to ${ariaName()}…`;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  hideStartupOverlay(`Some services still starting — you can use ${ariaName()} now.`);
  return false;
}

document.getElementById("startupSkipBtn")?.addEventListener("click", () => {
  hideStartupOverlay("");
});


  window.hideStartupOverlay = hideStartupOverlay;
  window.waitForServices = waitForServices;
  waitForServices().then(() => window.__ariaPostStartup?.());
})();
