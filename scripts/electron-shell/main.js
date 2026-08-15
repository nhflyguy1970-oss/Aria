/**
 * Aria Runtime R1 — Electron-class Living Workspace host.
 * Product identity: Aria. Runtime must disappear.
 */
const { app, BrowserWindow, shell, Menu } = require("electron");
const path = require("path");

const TITLE = process.env.JARVIS_WINDOW_TITLE || "Aria";
const START = (() => {
  const base =
    process.env.JARVIS_URL ||
    process.env.ARIA_URL ||
    "http://127.0.0.1:8765/";
  const u = new URL(base.endsWith("/") ? base : base + "/");
  u.searchParams.set("app", "1");
  u.searchParams.set("shell", "electron");
  u.searchParams.set("workspace", "1");
  return u.toString();
})();

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: Number(process.env.JARVIS_WIDTH || 1440),
    height: Number(process.env.JARVIS_HEIGHT || 900),
    minWidth: 960,
    minHeight: 640,
    title: TITLE,
    backgroundColor: "#0c0908",
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: true,
    },
  });

  // Minimal application menu — avoid browser-like chrome theater
  const menu = Menu.buildFromTemplate([
    {
      label: "Aria",
      submenu: [
        { role: "about", label: "About Aria" },
        { type: "separator" },
        { role: "quit", label: "Quit Aria" },
      ],
    },
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "toggleDevTools", visible: process.env.ARIA_DEVTOOLS === "1" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
  ]);
  Menu.setApplicationMenu(menu);

  mainWindow.once("ready-to-show", () => mainWindow.show());
  mainWindow.loadURL(START);

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("page-title-updated", (e) => {
    e.preventDefault();
    mainWindow.setTitle(TITLE);
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    createWindow();
    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
  });
}
