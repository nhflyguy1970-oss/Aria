"""Intentional whole-application quit. Shared model services are not ARIA-owned.

Only this checkout's identified tray, server and desktop processes are signalled.
No forced kills, lock-file removal, credential reads, or service enablement changes.
"""
from __future__ import annotations

import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from jarvis.config import DATA_DIR, PROJECT_ROOT

QUIT_FLAG = DATA_DIR / "quit_aria.request"
SHELL_MODULES = {"jarvis.native_window", "jarvis.pyside_shell", "jarvis.electron_shell"}


def quit_requested() -> bool:
    return QUIT_FLAG.exists()


def mark_quit() -> None:
    QUIT_FLAG.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(QUIT_FLAG, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write("Intentional quit; cleared by explicit startup.\n")
        stream.flush()
        os.fsync(stream.fileno())


def clear_quit() -> None:
    QUIT_FLAG.unlink(missing_ok=True)


def authorize_quit(client: str, origin: str, base_url: str) -> dict:
    # Local desktop only, existing Owner Vault permission and session checks.
    if client not in {"127.0.0.1", "::1"} or (origin and origin != base_url):
        return {"ok": False, "reason": "Quit requires the local ARIA interface"}
    from jarvis.security.owner.provider_credentials import bound_owner_service

    try:
        return bound_owner_service().authorize("integrations.modify", room="providers")
    except Exception:
        return {"ok": False, "reason": "Unlock the Owner Vault, or quit from a local terminal"}


def process_identity(pid: int) -> tuple[str, str] | None:
    """Role + kernel start time protect against stale PID files / PID reuse."""
    proc = Path("/proc") / str(pid)
    try:
        if proc.stat().st_uid != os.getuid():
            return None
        args = [a.decode() for a in (proc / "cmdline").read_bytes().split(b"\0") if a]
        start = (proc / "stat").read_text().rsplit(")", 1)[1].split()[19]
        cwd = (proc / "cwd").resolve()
        script = Path(args[1]) if len(args) >= 2 else Path("/not-an-aria-script")
        if not script.is_absolute():
            script = cwd / script
        if len(args) >= 3 and script.resolve() == (PROJECT_ROOT / "main.py").resolve():
            mode = args[2]
            if mode in {"tray", "tray-uncensored", "serve", "gui", "gui-uncensored"}:
                return ("tray" if mode.startswith("tray") else "server", start)
        if len(args) >= 3 and args[1] == "-m" and args[2] in SHELL_MODULES:
            if (proc / "cwd").resolve() == PROJECT_ROOT.resolve():
                return ("desktop", start)
        binary = PROJECT_ROOT / "scripts/electron-shell/node_modules/electron/dist/electron"
        if args and Path(args[0]).resolve() == binary.resolve() and str(PROJECT_ROOT / "scripts/electron-shell") in args[1:]:
            return ("desktop", start)
    except (OSError, ValueError, UnicodeError, IndexError):
        return None
    return None


def owned_processes() -> dict[int, tuple[str, str]]:
    result = {}
    for proc in Path("/proc").glob("[0-9]*"):
        identity = process_identity(int(proc.name))
        if identity is not None:
            result[int(proc.name)] = identity
    return result


def stop_processes(processes: dict[int, tuple[str, str]], timeout: float = 30) -> None:
    # Recheck identity immediately before every signal; never act on a PID file.
    for pid, identity in processes.items():
        if pid == os.getpid():
            raise RuntimeError("Quit coordinator cannot be an ARIA runtime process")
        if process_identity(pid) == identity:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + timeout
    while any(process_identity(pid) == identity for pid, identity in processes.items()):
        if time.monotonic() >= deadline:
            raise RuntimeError("ARIA did not close gracefully; no forced termination performed")
        time.sleep(0.1)


def verify_closed() -> None:
    if owned_processes():
        raise RuntimeError("ARIA processes remain or relaunched")
    for name in ("launch", "gui_shell", "native_window", "electron_shell", "pyside_shell"):
        path = DATA_DIR / f"{name}.lock"
        if path.is_file():
            with path.open("r+") as stream:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    # Connections must be closed, not merely checkpointed. Preserve WAL/SHM.
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            for fd in (proc / "fd").iterdir():
                try:
                    path = Path(os.readlink(fd).removesuffix(" (deleted)"))
                    if path.is_absolute() and path.is_relative_to(DATA_DIR.resolve()):
                        if path.name.endswith((".db", ".sqlite", ".sqlite3", "-wal", "-shm")):
                            raise RuntimeError(f"Database handle remains open: PID {proc.name}, {path.name}")
                except FileNotFoundError:
                    continue
        except (FileNotFoundError, PermissionError):
            # Privileged/unrelated writers remain the stopped-backup guard's gate.
            continue


def quit_completely() -> dict:
    from jarvis.launch_ownership import systemd_stop, systemd_unit_installed

    mark_quit()  # Fence watchdogs before stopping any process.
    processes = owned_processes()
    stop_processes({p: i for p, i in processes.items() if i[0] == "tray"})
    stop_processes({p: i for p, i in processes.items() if i[0] == "desktop"})
    if systemd_unit_installed() and not systemd_stop():
        raise RuntimeError("Could not stop jarvis.service")
    stop_processes({p: i for p, i in owned_processes().items() if i[0] == "server"})
    verify_closed()
    return {"ok": True, "message": "ARIA quit completely; shared services retained"}


def request_quit() -> dict:
    """Detached coordinator survives systemd stopping the HTTP service's cgroup."""
    from jarvis.security.owner.env_boundary import copy_process_env

    mark_quit()
    try:
        result = subprocess.run(
            ["systemd-run", "--user", "--collect", "--quiet", "--property=Type=exec",
             f"--working-directory={PROJECT_ROOT}", f"--setenv=JARVIS_DATA_DIR={DATA_DIR}",
             sys.executable, "-m", "jarvis.shutdown", "quit"],
            capture_output=True, text=True, timeout=10, env=copy_process_env(), check=False,
        )
        if result.returncode:
            raise RuntimeError("Could not start independent quit coordinator")
    except Exception:
        clear_quit()
        raise
    return {"ok": True, "message": "Quitting ARIA completely…"}


def close_acm() -> None:
    """Close only an already-created engine, after its producers have stopped."""
    from aria_core import acm_bridge

    with acm_bridge._ENGINE_LOCK:
        eng = acm_bridge._ENGINE
        if eng is not None and getattr(eng, "durable", None) is not None:
            eng.flush(kind="shutdown")
            eng.durable.close()
            acm_bridge._ENGINE = None


if __name__ == "__main__":
    if sys.argv[1:] == ["clear"]:
        clear_quit()
    elif sys.argv[1:] == ["quit"]:
        print(json.dumps(quit_completely()))
    else:
        raise SystemExit("Usage: python -m jarvis.shutdown quit|clear")
