"""System audit runner for CLI and ARIA API."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from jarvis.audit_paths import audit_path_env, jarvis_root, prepare_gui_sudo_env, resolve_script
from jarvis.system_audit_engine import run_engine

_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, Any] | None = None
_CACHE_AT: float = 0.0
_RUNNING = False
_DEFAULT_TTL = float(os.getenv("JARVIS_AUDIT_CACHE_SEC", "30"))
_DEFAULT_ETA = float(os.getenv("JARVIS_AUDIT_ETA_SEC", "90"))
_PROGRESS: dict[str, Any] = {
    "running": False,
    "phase": 0,
    "total": 14,
    "phase_id": "",
    "title": "",
    "percent": 0,
    "started_at": 0.0,
    "elapsed_sec": 0,
    "eta_sec": 0,
}


def _reset_progress(*, eta_sec: int | None = None) -> None:
    now = time.time()
    _PROGRESS.update({
        "running": True,
        "phase": 0,
        "total": 14,
        "phase_id": "start",
        "title": "Starting audit…",
        "percent": 0,
        "started_at": now,
        "elapsed_sec": 0,
        "eta_sec": eta_sec if eta_sec is not None else int(_DEFAULT_ETA),
    })


def _update_progress(phase: int, total: int, phase_id: str, title: str) -> None:
    now = time.time()
    started = float(_PROGRESS.get("started_at") or now)
    elapsed = max(0.0, now - started)
    if phase > total:
        pct = 100
        eta = 0
    else:
        pct = min(99, int((phase - 1) / total * 100)) if phase >= 1 else 0
        if phase > 1 and elapsed > 0:
            eta = max(0, int(elapsed / (phase - 1) * (total - phase + 1)))
        else:
            eta = int(_DEFAULT_ETA)
    _PROGRESS.update({
        "running": True,
        "phase": min(phase, total),
        "total": total,
        "phase_id": phase_id,
        "title": title,
        "percent": pct,
        "started_at": started,
        "elapsed_sec": int(elapsed),
        "eta_sec": eta,
    })


def _finish_progress() -> None:
    started = float(_PROGRESS.get("started_at") or time.time())
    _PROGRESS.update({
        "running": False,
        "phase": _PROGRESS.get("total", 14),
        "title": "Complete",
        "percent": 100,
        "elapsed_sec": int(time.time() - started),
        "eta_sec": 0,
    })


def get_audit_progress() -> dict[str, Any]:
    with _CACHE_LOCK:
        return dict(_PROGRESS)


def _sudoers_install_script() -> Path:
    return resolve_script("install-audit-sudoers.sh")


def _gui_sudo_available() -> bool:
    return prepare_gui_sudo_env() is not None


def _sudo_askpass_env() -> dict[str, str]:
    env = prepare_gui_sudo_env()
    if env:
        return env
    return audit_path_env()


def sudo_audit_available() -> bool:
    script = str(resolve_script("audit-system.sh"))
    try:
        proc = subprocess.run(
            ["sudo", "-n", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return proc.returncode == 0 and script in (proc.stdout or "")
    except Exception:
        return False


def _try_install_passwordless_sudo(env: dict[str, str] | None) -> None:
    install = _sudoers_install_script()
    if sudo_audit_available() or not install.is_file():
        return
    try:
        cmd = ["sudo", "-A", str(install)] if env else ["sudo", "-n", str(install)]
        subprocess.run(cmd, env=env, timeout=120, check=False, cwd=str(jarvis_root()))
    except Exception:
        pass


def _elevated_for_smart() -> bool:
    if os.geteuid() == 0:
        return True
    if sudo_audit_available():
        return True
    if _run_sudo_probe():
        return True
    return False


def _run_sudo_probe() -> bool:
    try:
        if _gui_sudo_available():
            env = _sudo_askpass_env()
            proc = subprocess.run(
                ["sudo", "-A", "true"],
                env=env,
                timeout=30,
                check=False,
            )
            if proc.returncode == 0:
                _try_install_passwordless_sudo(env)
                return True
        return subprocess.run(["sudo", "-n", "true"], timeout=5, check=False).returncode == 0
    except Exception:
        return False


def clear_audit_cache() -> None:
    global _CACHE, _CACHE_AT
    with _CACHE_LOCK:
        _CACHE = None
        _CACHE_AT = 0.0


def _audit_running_payload(*, message: str = "Audit in progress") -> dict[str, Any]:
    """Build running response; caller must hold _CACHE_LOCK."""
    out: dict[str, Any] = {
        "ok": True,
        "running": True,
        "message": message,
        "progress": dict(_PROGRESS),
        "cached": _CACHE is not None,
    }
    if _CACHE:
        out["data"] = dict(_CACHE)
    return out


def _audit_running_response(*, message: str = "Audit in progress") -> dict[str, Any]:
    with _CACHE_LOCK:
        return _audit_running_payload(message=message)


def _execute_audit() -> dict[str, Any]:
    with _CACHE_LOCK:
        _reset_progress()
    try:
        if os.getenv("JARVIS_AUDIT_NO_SUDO", "").strip() not in ("1", "true", "yes"):
            if not sudo_audit_available() and _gui_sudo_available():
                _run_sudo_probe()
        sudo_smart = _elevated_for_smart()

        def on_progress(phase: int, total: int, phase_id: str, title: str) -> None:
            with _CACHE_LOCK:
                _update_progress(phase, total, phase_id, title)

        data = run_engine(sudo_smart=sudo_smart, progress=on_progress)
        data["cached"] = False
        data["cache_age_sec"] = 0
        data["exit_code"] = 1 if data.get("result") == "fail" else 0
        return data
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "result": "fail",
            "summary": {"pass": 0, "warn": 0, "fail": 1, "total": 1, "phases": 0},
            "phases": [],
            "pass": [],
            "warn": [],
            "fail": [{"message": f"Audit runner error: {exc}"}],
            "cached": False,
            "sudo_smart": False,
            "exit_code": 1,
        }
    finally:
        with _CACHE_LOCK:
            _finish_progress()


def run_audit(*, use_cache: bool = True, cache_ttl: float | None = None, background: bool = False) -> dict[str, Any]:
    """Run 14-phase system audit and return structured results."""
    global _CACHE, _CACHE_AT, _RUNNING

    ttl = _DEFAULT_TTL if cache_ttl is None else cache_ttl
    now = time.time()
    with _CACHE_LOCK:
        if use_cache and _CACHE is not None and now - _CACHE_AT < ttl and not background:
            out = dict(_CACHE)
            out["cached"] = True
            out["cache_age_sec"] = int(now - _CACHE_AT)
            return out
        if _RUNNING:
            return _audit_running_payload(message="Audit already in progress")

    if background:
        with _CACHE_LOCK:
            _RUNNING = True
            _reset_progress()

        def _worker() -> None:
            global _RUNNING
            try:
                data = _execute_audit()
            except Exception as exc:
                data = {
                    "ok": False,
                    "error": str(exc),
                    "result": "fail",
                    "summary": {"pass": 0, "warn": 0, "fail": 1, "total": 1, "phases": 0},
                    "phases": [],
                    "pass": [],
                    "warn": [],
                    "fail": [{"message": f"Audit runner error: {exc}"}],
                    "cached": False,
                    "sudo_smart": False,
                    "exit_code": 1,
                }
            with _CACHE_LOCK:
                _CACHE = dict(data)
                _CACHE_AT = time.time()
                _RUNNING = False

        threading.Thread(target=_worker, daemon=True, name="jarvis-audit").start()
        return _audit_running_response(message="Audit started")

    with _CACHE_LOCK:
        _RUNNING = True
        _reset_progress()
    try:
        data = _execute_audit()
    finally:
        with _CACHE_LOCK:
            _RUNNING = False

    with _CACHE_LOCK:
        _CACHE = dict(data)
        _CACHE_AT = time.time()
    return data


def get_cached_audit() -> dict[str, Any] | None:
    with _CACHE_LOCK:
        return dict(_CACHE) if _CACHE else None


def get_audit_status(*, use_cache: bool = True) -> dict[str, Any]:
    """Current audit state for polling — includes progress while running."""
    with _CACHE_LOCK:
        if _RUNNING:
            return _audit_running_payload()
        if use_cache and _CACHE is not None:
            out = dict(_CACHE)
            out["cached"] = True
            out["cache_age_sec"] = int(time.time() - _CACHE_AT)
            out["running"] = False
            return out
    return {"ok": False, "running": False, "message": "No audit cached"}


def cli_main() -> None:
    import sys

    data = run_audit(use_cache=False)
    print(json.dumps(data, indent=2))
    sys.exit(data.get("exit_code", 1 if data.get("result") == "fail" else 0))


if __name__ == "__main__":
    cli_main()
