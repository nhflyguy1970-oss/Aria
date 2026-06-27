/** Browser agent tab */

function $(id) {
  return document.getElementById(id);
}

let browserPollTimer = null;

async function loadBrowserPanel() {
  const status = $("browserStatus");
  const log = $("browserLog");
  if (!status) return;
  try {
    const data = await fetch("/api/browser/status").then((r) => r.json());
    const stack = data.chromium ? "Chromium ready" : data.playwright ? "Playwright (no Chromium)" : "Playwright not installed";
    status.textContent = `${data.status || "idle"} · ${stack}${data.url ? ` · ${data.url}` : ""}`;
    if (log && data.message) log.textContent = data.message;
  } catch (e) {
    status.textContent = e.message;
  }
}

async function runBrowserTask() {
  const url = $("browserUrlInput")?.value?.trim();
  const task = $("browserTaskInput")?.value?.trim();
  const log = $("browserLog");
  if (!url && !task) return;
  if (log) log.textContent = "Running…";
  try {
    const data = await fetch("/api/browser/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, task }),
    }).then((r) => r.json());
    if (log) log.textContent = data.message || JSON.stringify(data, null, 2);
    loadBrowserPanel();
  } catch (e) {
    if (log) log.textContent = e.message;
  }
}

async function browserAction(path) {
  const log = $("browserLog");
  try {
    const data = await fetch(path, { method: "POST" }).then((r) => r.json());
    if (log) log.textContent = data.message || JSON.stringify(data.status || data, null, 2);
    loadBrowserPanel();
  } catch (e) {
    if (log) log.textContent = e.message;
  }
}

function startBrowserPolling() {
  if (browserPollTimer) clearInterval(browserPollTimer);
  browserPollTimer = setInterval(loadBrowserPanel, 4000);
}

window.initBrowserPanel = function initBrowserPanel() {
  loadBrowserPanel();
  startBrowserPolling();
  $("browserRunBtn")?.addEventListener("click", runBrowserTask);
  $("browserPauseBtn")?.addEventListener("click", () => browserAction("/api/browser/pause"));
  $("browserResumeBtn")?.addEventListener("click", () => browserAction("/api/browser/resume"));
  $("browserTakeoverBtn")?.addEventListener("click", () => browserAction("/api/browser/takeover"));
  $("browserStopBtn")?.addEventListener("click", () => browserAction("/api/browser/stop"));
};
