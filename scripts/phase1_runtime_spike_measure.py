#!/usr/bin/env python3
"""Phase 1 runtime spike measurements — evidence only, no selection.

Usage (from repo root, with display):
  ./venv/bin/python scripts/phase1_runtime_spike_measure.py --candidate e3
  ./venv/bin/python scripts/phase1_runtime_spike_measure.py --candidate e1
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "phase1_runtime_spikes"


def rss_kb() -> int:
    # Linux: ru_maxrss is KB
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def measure_e3_pyside(auto_quit_ms: int = 2500) -> dict:
    """Cold import + window + about:blank load; auto-quit."""
    start = time.perf_counter()
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false")
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication, QMainWindow

    import_ms = (time.perf_counter() - start) * 1000
    rss_after_import = rss_kb()

    t0 = time.perf_counter()
    app = QApplication.instance() or QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("Aria Spike E3")
    view = QWebEngineView()
    win.setCentralWidget(view)
    win.resize(1280, 800)
    loaded = {"ok": False}

    def on_load(ok: bool) -> None:
        loaded["ok"] = bool(ok)

    view.loadFinished.connect(on_load)
    view.load(QUrl("about:blank"))
    win.show()
    show_ms = (time.perf_counter() - t0) * 1000

    QTimer.singleShot(auto_quit_ms, app.quit)
    t1 = time.perf_counter()
    app.exec()
    loop_ms = (time.perf_counter() - t1) * 1000
    rss_peak = rss_kb()

    return {
        "candidate": "E3",
        "engine": "PySide6.QtWebEngine",
        "host": "QMainWindow",
        "import_ms": round(import_ms, 1),
        "show_to_eventloop_ms": round(show_ms, 1),
        "eventloop_ms": round(loop_ms, 1),
        "total_wall_ms": round((time.perf_counter() - start) * 1000, 1),
        "rss_after_import_kb": rss_after_import,
        "rss_peak_self_kb": rss_peak,
        "load_ok": loaded["ok"],
        "notes": "ru_maxrss is process self only; WebEngine child processes not fully included.",
    }


def measure_e1_electron(auto_quit_ms: int = 4000) -> dict:
    electron_dir = ROOT / "scripts" / "electron-shell"
    binary = electron_dir / "node_modules" / "electron" / "dist" / "electron"
    if not binary.is_file():
        alt = electron_dir / "node_modules" / ".bin" / "electron"
        binary = alt if alt.exists() else binary
    if not binary.exists():
        return {
            "candidate": "E1",
            "ok": False,
            "error": "Electron not installed — run ./scripts/install-electron-shell.sh",
        }

    env = os.environ.copy()
    env["JARVIS_URL"] = "about:blank"
    env["JARVIS_WINDOW_TITLE"] = "Aria Spike E1"
    env["JARVIS_ELECTRON_QUIT_ON_CLOSE"] = "1"
    env["ARIA_SPIKE_AUTO_QUIT_MS"] = str(auto_quit_ms)
    env["ELECTRON_ENABLE_LOGGING"] = "0"

    t0 = time.perf_counter()
    proc = subprocess.Popen(
        [str(binary), str(electron_dir)],
        env=env,
        cwd=str(electron_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        # Sample RSS via /proc while running
        peak_kb = 0
        samples = 0
        while proc.poll() is None and samples < 80:
            time.sleep(0.05)
            samples += 1
            try:
                # Sum RSS of process tree (electron + renderers)
                out = subprocess.check_output(
                    ["ps", "-o", "rss=", "--ppid", str(proc.pid)],
                    text=True,
                )
                kids = sum(int(x) for x in out.split() if x.strip().isdigit())
                self_rss = int(
                    subprocess.check_output(["ps", "-o", "rss=", "-p", str(proc.pid)], text=True).strip()
                    or "0"
                )
                peak_kb = max(peak_kb, self_rss + kids)
            except Exception:
                pass
        code = proc.wait(timeout=30)
        wall = (time.perf_counter() - t0) * 1000
        stderr = (proc.stderr.read() if proc.stderr else "")[-400:]
        return {
            "candidate": "E1",
            "ok": code == 0,
            "exit_code": code,
            "wall_ms": round(wall, 1),
            "peak_rss_tree_kb": peak_kb,
            "peak_rss_tree_mb": round(peak_kb / 1024, 1) if peak_kb else None,
            "stderr_tail": stderr,
            "binary": str(binary),
        }
    finally:
        if proc.poll() is None:
            proc.kill()


def qualitative_e2_tauri() -> dict:
    cargo = subprocess.run(["cargo", "-V"], capture_output=True, text=True)
    rustc = subprocess.run(["rustc", "-V"], capture_output=True, text=True)
    return {
        "candidate": "E2",
        "engine": "Tauri (system/pinned webview — policy TBD)",
        "cargo": (cargo.stdout or cargo.stderr or "").strip(),
        "rustc": (rustc.stdout or rustc.stderr or "").strip(),
        "in_repo_scaffold": False,
        "law2_risk": (
            "On Linux, default Tauri often uses WebKitGTK — not an external browser install, "
            "but engine version is OS-coupled unless a pinned/bundled webview strategy is used. "
            "Spike must prove Law 2 on Linux/Windows/macOS with explicit pinning policy."
        ),
        "measured_runtime": False,
        "notes": "Tooling present; no product scaffold yet. Defer binary size/startup numbers to dedicated Tauri hello-world spike if shortlisted.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=["e1", "e2", "e3", "all"], default="all")
    parser.add_argument("--write", action="store_true", help="Write JSON under docs/phase1_runtime_spikes/")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    results = []
    if args.candidate in ("e3", "all"):
        results.append(measure_e3_pyside())
    if args.candidate in ("e1", "all"):
        results.append(measure_e1_electron())
    if args.candidate in ("e2", "all"):
        results.append(qualitative_e2_tauri())

    payload = {
        "phase": 1,
        "purpose": "runtime spike evidence — not a selection",
        "host": {
            "display": os.environ.get("DISPLAY"),
            "platform": sys.platform,
        },
        "results": results,
    }
    text = json.dumps(payload, indent=2)
    print(text)
    if args.write:
        path = OUT / f"measure_{int(time.time())}.json"
        path.write_text(text + "\n", encoding="utf-8")
        latest = OUT / "measure_latest.json"
        latest.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
