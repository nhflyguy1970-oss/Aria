#!/usr/bin/env python3
"""Phase 1 Runtime Certification — live Aria inside each candidate.

Evidence only. Does not select R1. Does not touch Workspace/rooms product code.

Examples:
  ./venv/bin/python scripts/phase1_runtime_certify.py --candidate e3 --soak-sec 180
  ./venv/bin/python scripts/phase1_runtime_certify.py --candidate e1 --soak-sec 180
  ./venv/bin/python scripts/phase1_runtime_certify.py --candidate all --soak-sec 120
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "phase1_runtime_spikes"
DEFAULT_URL = os.environ.get("JARVIS_URL", "http://127.0.0.1:8765/")

# Rooms Jeff would enter during a natural day (hash views)
ROOM_TOUR = [
    "chat",
    "health",
    "flytying",
    "workstation",
    "planner",
    "gallery",
    "documents",
    "coding",
    "search",
    "dashboard",
]


def api_live(base: str) -> dict:
    url = base.rstrip("/") + "/api/live"
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read().decode())


def tree_rss_kb(pid: int) -> int:
    def kids(p: int) -> list[int]:
        try:
            return [int(x) for x in subprocess.check_output(["pgrep", "-P", str(p)], text=True).split()]
        except subprocess.CalledProcessError:
            return []

    def walk(p: int) -> int:
        s = 0
        try:
            with open(f"/proc/{p}/status", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        s = int(line.split()[1])
                        break
        except OSError:
            return 0
        for c in kids(p):
            s += walk(c)
        return s

    return walk(pid)


def gpu_snapshot() -> dict:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5,
        ).strip()
        parts = [p.strip() for p in out.split(",")]
        return {
            "gpu_util_pct": int(parts[0]) if parts else None,
            "mem_used_mb": int(parts[1]) if len(parts) > 1 else None,
            "mem_total_mb": int(parts[2]) if len(parts) > 2 else None,
        }
    except Exception as exc:
        return {"error": str(exc)}


def certify_e3(url: str, soak_sec: int, dwell_sec: float) -> dict:
    """Stage-only QMainWindow + WebEngine — no Fluent chrome (Living Workspace constraint)."""
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false")
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication, QMainWindow

    t0 = time.perf_counter()
    app = QApplication.instance() or QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("Aria · Runtime Spike E3 Stage")
    view = QWebEngineView()
    win.setCentralWidget(view)
    win.resize(1440, 900)

    state: dict = {
        "candidate": "E3",
        "mode": "stage_only_webengine",
        "fluent_chrome": False,
        "url": url,
        "events": [],
        "rss_samples_kb": [],
        "gpu_samples": [],
        "room_tour": [],
        "errors": [],
        "feels_like_browser": None,
    }

    def log(msg: str) -> None:
        state["events"].append({"t": round(time.perf_counter() - t0, 2), "msg": msg})

    def sample() -> None:
        state["rss_samples_kb"].append(tree_rss_kb(os.getpid()))
        state["gpu_samples"].append(gpu_snapshot())

    loaded = {"ok": False, "at": None}

    def on_load(ok: bool) -> None:
        loaded["ok"] = bool(ok)
        loaded["at"] = round(time.perf_counter() - t0, 2)
        log(f"loadFinished ok={ok}")

    view.loadFinished.connect(on_load)
    view.load(QUrl(url if url.endswith("/") else url + "/"))
    win.show()
    log("window_shown")

    tour_i = {"i": 0}
    soak_end = time.perf_counter() + soak_sec

    def next_room() -> None:
        sample()
        if tour_i["i"] < len(ROOM_TOUR):
            room = ROOM_TOUR[tour_i["i"]]
            tour_i["i"] += 1
            js = f"window.location.hash = '{room}'; window.switchToView && window.switchToView('{room}');"
            view.page().runJavaScript(js)
            state["room_tour"].append({"room": room, "t": round(time.perf_counter() - t0, 2)})
            log(f"navigate {room}")
            QTimer.singleShot(int(dwell_sec * 1000), next_room)
            return
        # idle soak remainder
        if time.perf_counter() < soak_end:
            sample()
            QTimer.singleShot(5000, next_room)
        else:
            # backend still alive?
            try:
                live = api_live(url)
                state["backend_live_after"] = live.get("ok")
                state["backend_version"] = live.get("version")
            except Exception as exc:
                state["errors"].append(f"backend_after: {exc}")
                state["backend_live_after"] = False
            sample()
            # heuristic: Stage-only WebEngine still embeds Chromium — may feel webby if window chrome is OS-default
            state["feels_like_browser"] = "risk_medium_chromium_engine_but_native_window"
            state["invisible_computer_notes"] = (
                "Native window title controllable; no browser URL bar. "
                "Still Chromium under the hood — identity depends on branding/packaging."
            )
            state["peak_rss_mb"] = round(max(state["rss_samples_kb"]) / 1024, 1) if state["rss_samples_kb"] else None
            state["load_ok"] = loaded["ok"]
            state["load_sec"] = loaded["at"]
            state["wall_sec"] = round(time.perf_counter() - t0, 1)
            log("cert_complete")
            app.quit()

    def kickoff() -> None:
        if not loaded["ok"] and loaded["at"] is None:
            # wait a bit more for first load
            QTimer.singleShot(500, kickoff)
            return
        next_room()

    QTimer.singleShot(1500, kickoff)
    # hard ceiling
    QTimer.singleShot(int((soak_sec + 60) * 1000), app.quit)
    app.exec()
    return state


def certify_e1(url: str, soak_sec: int, dwell_sec: float) -> dict:
    electron_dir = ROOT / "scripts" / "electron-shell"
    binary = electron_dir / "node_modules" / "electron" / "dist" / "electron"
    if not binary.is_file():
        return {"candidate": "E1", "ok": False, "error": "electron binary missing"}

    preload = electron_dir / "cert_preload_tour.js"
    preload.write_text(
        f"""
// Injected via executeJavaScript from main — tour driven by env schedule in main_cert.js
window.__ARIA_SPIKE_ROOMS = {json.dumps(ROOM_TOUR)};
window.__ARIA_SPIKE_DWELL_MS = {int(dwell_sec * 1000)};
""",
        encoding="utf-8",
    )

    # Use dedicated cert main that tours then quits
    cert_main = electron_dir / "main_cert.js"
    cert_main.write_text(
        r"""
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
""",
        encoding="utf-8",
    )

    out_file = OUT / f"e1_cert_live_{int(time.time())}.json"
    OUT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["JARVIS_URL"] = url if url.endswith("/") else url + "/"
    env["ARIA_SPIKE_ROOMS"] = ",".join(ROOM_TOUR)
    env["ARIA_SPIKE_DWELL_MS"] = str(int(dwell_sec * 1000))
    env["ARIA_SPIKE_SOAK_MS"] = str(int(soak_sec * 1000))
    env["ARIA_SPIKE_OUT"] = str(out_file)
    env["JARVIS_WINDOW_TITLE"] = "Aria · Runtime Spike E1"

    t0 = time.perf_counter()
    proc = subprocess.Popen(
        [str(binary), str(cert_main)],
        cwd=str(electron_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    rss_samples = []
    gpu_samples = []
    try:
        while proc.poll() is None:
            rss_samples.append(tree_rss_kb(proc.pid))
            gpu_samples.append(gpu_snapshot())
            time.sleep(2.0)
            if time.perf_counter() - t0 > soak_sec + 90:
                proc.send_signal(signal.SIGTERM)
                break
        code = proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()

    live_state = {}
    if out_file.is_file():
        live_state = json.loads(out_file.read_text(encoding="utf-8"))

    try:
        backend = api_live(url)
        backend_ok = bool(backend.get("ok"))
    except Exception as exc:
        backend_ok = False
        live_state["backend_error"] = str(exc)

    return {
        **live_state,
        "candidate": "E1",
        "ok": code == 0 and live_state.get("load_ok", False),
        "exit_code": code,
        "rss_samples_kb": rss_samples,
        "peak_rss_mb": round(max(rss_samples) / 1024, 1) if rss_samples else None,
        "gpu_samples": gpu_samples,
        "backend_live_after": backend_ok,
        "stderr_tail": (proc.stderr.read() if proc.stderr else "")[-500:],
        "wall_sec_harness": round(time.perf_counter() - t0, 1),
    }


def certify_e2_qualitative() -> dict:
    """Law-2 and Living Workspace viability without claiming measured winner."""
    webkit = subprocess.run(["pkg-config", "--modversion", "webkit2gtk-4.1"], capture_output=True, text=True)
    if webkit.returncode != 0:
        webkit = subprocess.run(["pkg-config", "--modversion", "webkit2gtk-4.0"], capture_output=True, text=True)
    return {
        "candidate": "E2",
        "mode": "tauri_class_assessment",
        "measured_live_aria": False,
        "cargo": subprocess.check_output(["cargo", "-V"], text=True).strip(),
        "webkitgtk": (webkit.stdout or webkit.stderr or "").strip() or None,
        "law2": {
            "external_browser_required": False,
            "engine_bundled_by_default_linux": False,
            "engine_source_linux": "WebKitGTK (OS package) unless alternate pinning strategy",
            "risk": "OS webview drift across distros; Windows WebView2 Evergreen may require runtime install — must be proven for Law 2",
            "pass_if": "Pinned/bundled engine on all target OSes with Aria-owned updates",
        },
        "living_workspace": {
            "can_host_stage": True,
            "risk": "Smaller ecosystem; custom tooling for Python sidecar; easy to under-invest in polish",
        },
        "python_integration": "Separate process + HTTP/IPC (same as Electron)",
        "reasons_to_continue_spike": [
            "Potential smaller host binary",
            "Rust security posture",
        ],
        "reasons_to_defer_r1": [
            "No live Aria measurement yet",
            "Law 2 not proven under pinning policy",
            "Higher near-term delivery risk vs E1/E3 for Jeff's decade-local Linux daily driver",
        ],
        "feels_like_browser": "depends_on_webview_chrome_and_branding",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=["e1", "e2", "e3", "all"], default="all")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--soak-sec", type=int, default=150)
    parser.add_argument("--dwell-sec", type=float, default=4.0)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    try:
        live = api_live(args.url)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"backend not reachable: {exc}"}))
        return 2

    report = {
        "phase": 1,
        "certification": "runtime_live",
        "purpose": "Runtime Certification evidence — not R1 selection by this script alone",
        "backend_before": {"ok": live.get("ok"), "version": live.get("version")},
        "url": args.url,
        "soak_sec": args.soak_sec,
        "results": [],
    }

    if args.candidate in ("e3", "all"):
        print("CERT E3 …", file=sys.stderr)
        report["results"].append(certify_e3(args.url, args.soak_sec, args.dwell_sec))
    if args.candidate in ("e1", "all"):
        print("CERT E1 …", file=sys.stderr)
        report["results"].append(certify_e1(args.url, args.soak_sec, args.dwell_sec))
    if args.candidate in ("e2", "all"):
        print("CERT E2 qualitative …", file=sys.stderr)
        report["results"].append(certify_e2_qualitative())

    path = OUT / f"cert_{int(time.time())}.json"
    latest = OUT / "cert_latest.json"
    text = json.dumps(report, indent=2)
    path.write_text(text + "\n", encoding="utf-8")
    latest.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
