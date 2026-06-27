"""Resolve Jarvis install paths for system audit (any disk / layout)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from jarvis.config import DATA_DIR, PROJECT_ROOT


def _env_files() -> list[Path]:
    """jarvis.env locations without calling jarvis_root() (avoids circular imports)."""
    out: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)

    for raw in (os.environ.get("JARVIS_ROOT", ""), os.environ.get("ARIA_ROOT", "")):
        if raw.strip():
            add(Path(raw.strip()).expanduser() / "data" / "jarvis.env")
    add(PROJECT_ROOT / "data" / "jarvis.env")
    add(Path.home() / ".config" / "jarvis" / "jarvis.env")
    return out


def read_env_file_var(name: str) -> str:
    for env_path in _env_files():
        if not env_path.is_file():
            continue
        try:
            text = env_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if not line.startswith(f"{name}="):
                continue
            val = line.split("=", 1)[1].strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            val = val.replace("$HOME", str(Path.home())).replace("${HOME}", str(Path.home()))
            if val:
                return val
    return ""


def jarvis_root() -> Path:
    """Active Jarvis tree — env override, jarvis.env, else package location."""
    for raw in (
        os.environ.get("JARVIS_ROOT", ""),
        os.environ.get("ARIA_ROOT", ""),
        read_env_file_var("JARVIS_ROOT"),
        read_env_file_var("ARIA_ROOT"),
    ):
        if not raw.strip():
            continue
        root = Path(raw.strip()).expanduser().resolve()
        if (root / "jarvis" / "config.py").is_file() or (root / "scripts").is_dir():
            return root
    return PROJECT_ROOT.resolve()


def _read_env_file_paths() -> list[str]:
    extra: list[str] = []
    files = list(_env_files())
    root_env = jarvis_root() / "data" / "jarvis.env"
    if root_env not in files:
        files.append(root_env)
    for env_path in files:
        if not env_path.is_file():
            continue
        try:
            text = env_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#") or "PATH=" not in line:
                continue
            m = re.search(r'PATH=(?:"([^"]*)"|\'([^\']*)\'|([^;\s]+))', line)
            if m:
                val = m.group(1) or m.group(2) or m.group(3) or ""
                for part in val.split(":"):
                    part = part.strip().replace("$HOME", str(Path.home()))
                    part = part.replace("${HOME}", str(Path.home()))
                    if part:
                        extra.append(part)
    return extra


def _login_shell_path() -> str:
    try:
        proc = subprocess.run(
            ["bash", "-lc", "echo $PATH"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode == 0 and (proc.stdout or "").strip():
            return proc.stdout.strip()
    except Exception:
        pass
    return ""


def _standard_tool_dirs() -> list[str]:
    home = Path.home()
    dirs = [
        home / ".cargo" / "bin",
        home / ".local" / "bin",
        Path("/usr/local/bin"),
        Path("/usr/bin"),
        Path("/snap/bin"),
    ]
    nvm = home / ".nvm" / "versions" / "node"
    if nvm.is_dir():
        for ver in sorted(nvm.iterdir(), reverse=True):
            b = ver / "bin"
            if b.is_dir():
                dirs.append(b)
                break
    rustup = home / ".rustup" / "toolchains"
    if rustup.is_dir():
        for tc in sorted(rustup.iterdir(), reverse=True):
            b = tc / "bin"
            if b.is_dir():
                dirs.append(b)
    return [str(d) for d in dirs if d.is_dir()]


def audit_path_env() -> dict[str, str]:
    """Full PATH for subprocess + shutil.which during audit."""
    parts: list[str] = []
    seen: set[str] = set()

    def add(chunk: str) -> None:
        for p in chunk.split(os.pathsep):
            p = p.strip()
            if not p or p in seen:
                continue
            seen.add(p)
            parts.append(p)

    extra = os.environ.get("JARVIS_AUDIT_EXTRA_PATH", "")
    if extra.strip():
        add(extra.strip())
    for p in _read_env_file_paths():
        add(p)
    for p in _standard_tool_dirs():
        add(p)
    login = _login_shell_path()
    if login:
        add(login)
    add(os.environ.get("PATH", ""))

    env = os.environ.copy()
    if not env.get("HOME") and env.get("USER"):
        env["HOME"] = f"/home/{env['USER']}"
    env["PATH"] = os.pathsep.join(parts)
    env["JARVIS_ROOT"] = str(jarvis_root())
    return env


def prepare_gui_sudo_env(env: dict[str, str] | None = None) -> dict[str, str] | None:
    """Set SUDO_ASKPASS + DISPLAY for zenity sudo from ARIA server (returns None if unavailable)."""
    base = dict(env) if env else audit_path_env()
    askpass = resolve_script("sudo-askpass-zenity.sh")
    if not (askpass.is_file() and os.access(askpass, os.X_OK)):
        return None
    zen = shutil.which("zenity", path=base.get("PATH", ""))
    kdialog = shutil.which("kdialog", path=base.get("PATH", ""))
    if not zen and not kdialog:
        return None
    if base.get("DISPLAY") or base.get("WAYLAND_DISPLAY"):
        base["SUDO_ASKPASS"] = str(askpass)
        return base
    for display in (":0", ":1", ":2"):
        if Path(f"/tmp/.X11-unix/X{display.lstrip(':')}").exists():
            base["DISPLAY"] = display
            base["SUDO_ASKPASS"] = str(askpass)
            return base
    return None


def audit_path_string() -> str:
    return audit_path_env()["PATH"]


def resolve_venv_python() -> Path | None:
    """Jarvis venv — may live on another disk via JARVIS_VENV."""
    candidates: list[Path] = []
    for raw in (
        os.environ.get("JARVIS_VENV", ""),
        os.environ.get("VIRTUAL_ENV", ""),
        read_env_file_var("JARVIS_VENV"),
    ):
        if raw.strip():
            p = Path(raw.strip()).expanduser()
            candidates.append(p / "bin" / "python" if p.is_dir() else p)
    root = jarvis_root()
    candidates.extend([
        root / "venv" / "bin" / "python",
        root / ".venv" / "bin" / "python",
    ])
    for c in candidates:
        try:
            if c.is_file() and os.access(c, os.X_OK):
                return Path(c)
        except OSError:
            continue
    return None


def resolve_script(rel: str) -> Path:
    """Resolve scripts/foo.sh under the active Jarvis root."""
    rel = rel.removeprefix("/")
    if rel.startswith("scripts/"):
        return jarvis_root() / rel
    return jarvis_root() / "scripts" / rel


def install_command(rel: str, *, note: str = "") -> str:
    script = resolve_script(rel)
    cmd = f"bash {script}"
    if note:
        return f"{cmd}  # {note}"
    return cmd


def configured_gpu_preference() -> str:
    raw = (
        os.environ.get("JARVIS_GPU_PREFER", "")
        or read_env_file_var("JARVIS_GPU_PREFER")
        or "auto"
    ).strip().lower()
    if raw in ("nvidia", "amd", "both", "hybrid", "auto"):
        return "both" if raw in ("both", "hybrid") else raw
    return "auto"


def nvidia_ai_hybrid_configured() -> bool:
    """AMD + NVIDIA present and Jarvis env routes AI to NVIDIA."""
    return configured_gpu_preference() == "nvidia" and (
        read_env_file_var("HIP_VISIBLE_DEVICES") == "-1"
        or os.environ.get("HIP_VISIBLE_DEVICES", "").strip() == "-1"
    )


def audit_locations() -> dict[str, str]:
    root = jarvis_root()
    venv = resolve_venv_python()
    data = root / "data"
    if not data.is_dir():
        data = DATA_DIR
    return {
        "jarvis_root": str(root),
        "data_dir": str(data),
        "venv_python": str(venv) if venv else "",
    }
