
const { app, BrowserWindow } = require("electron");
const rooms = (process.env.ARIA_SPIKE_ROOMS || "chat").split(",");
const dwell = Number(process.env.ARIA_SPIKE_DWELL_MS || 4000);
const soakMs = Number(process.env.ARIA_SPIKE_SOAK_MS || 120000);
const url = process.env.JARVIS_URL || "http://127.0.0.1:8765/";
const fs = require("fs");
const path = require("path");
const outPath = process.env.ARIA_SPIKE_OUT || "";

let win;
const state = {
  candidate: "E1",
  mode: "electron_stage",
  url,
  events: [],
  room_tour: [],
  started: Date.now(),
};

function log(msg) {
  state.events.push({ t: (Date.now() - state.started) / 1000, msg });
}

app.whenReady().then(async () => {
  win = new BrowserWindow({
    width: 1440,
    height: 900,
    title: "Aria · Runtime Spike E1",
    autoHideMenuBar: true,
    backgroundColor: "#0c0908",
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  log("window_shown");
  try {
    await win.loadURL(url.endsWith("/") ? url : url + "/");
    state.load_ok = true;
    log("load_ok");
  } catch (e) {
    state.load_ok = false;
    state.error = String(e);
    log("load_fail");
    finish(1);
    return;
  }

  let i = 0;
  const tick = async () => {
    if (i < rooms.length) {
      const room = rooms[i++];
      const js = `window.location.hash='${room}'; if (window.switchToView) window.switchToView('${room}');`;
      try {
        await win.webContents.executeJavaScript(js);
        state.room_tour.push({ room, t: (Date.now() - state.started) / 1000 });
        log("navigate " + room);
      } catch (e) {
        state.errors = state.errors || [];
        state.errors.push(String(e));
      }
      setTimeout(tick, dwell);
      return;
    }
    // idle until soak
    const left = soakMs - (Date.now() - state.started);
    setTimeout(() => finish(0), Math.max(1000, left));
  };
  setTimeout(tick, 1500);
});

function finish(code) {
  state.wall_sec = (Date.now() - state.started) / 1000;
  state.feels_like_browser = "risk_medium_electron_identity_needs_branding";
  state.invisible_computer_notes =
    "No browser chrome when packaged; unpackaged Electron can feel like a web wrapper. Branding + asar packaging critical.";
  if (outPath) {
    try {
      fs.writeFileSync(outPath, JSON.stringify(state, null, 2));
    } catch (e) {}
  }
  app.exit(code);
}

app.on("window-all-closed", () => app.quit());
