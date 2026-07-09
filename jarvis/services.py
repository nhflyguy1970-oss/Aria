"""Unified service orchestration — auto-start Ollama, ComfyUI, and report tool readiness."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from jarvis.env_loader import PROJECT_ROOT, load_jarvis_env
from jarvis.ha_docker import container_running, ha_api_healthy, should_autostart_ha

logger = logging.getLogger("jarvis.services")

_ollama_proc: subprocess.Popen | None = None
_comfy_proc: subprocess.Popen | None = None
_lock = threading.Lock()
_boot_log: list[str] = []


def _log(msg: str) -> None:
    logger.info(msg)
    _boot_log.append(msg)
    if len(_boot_log) > 50:
        _boot_log.pop(0)


def _http_ok(url: str, timeout: float = 3) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _jarvis_port_open(timeout: float = 1) -> bool:
    """TCP check only — never call /api/health from here (deadlocks health handler)."""
    import socket

    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    port = int(os.getenv("JARVIS_PORT", "8765"))
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for(check: Callable[[], bool], timeout: float = 30, interval: float = 1) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if check():
            return True
        time.sleep(interval)
    return False


@dataclass
class ServiceStatus:
    name: str
    label: str
    running: bool
    autostart: bool
    required: bool
    message: str = ""
    detail: str = ""


def _ollama_healthy() -> bool:
    return _http_ok("http://127.0.0.1:11434/api/tags")


def _comfy_healthy() -> bool:
    url = os.getenv("JARVIS_COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
    return _http_ok(f"{url}/system_stats", timeout=1.5)


def _comfy_python(comfy_root: Path) -> str:
    """Use ComfyUI's venv Python, not Jarvis's."""
    override = os.getenv("JARVIS_COMFYUI_PYTHON", "").strip()
    if override and Path(override).exists():
        return override
    for name in ("python", "python3"):
        venv_py = comfy_root / "venv" / "bin" / name
        if venv_py.exists():
            return str(venv_py)
    return sys.executable


def _comfy_env() -> dict:
    env = os.environ.copy()
    try:
        from jarvis.gpu_routing import gpu_env_for_subprocess, gpu_preference, nvidia_available

        overrides = gpu_env_for_subprocess()
        for key, value in overrides.items():
            if value == "":
                env.pop(key, None)
            else:
                env[key] = value
        pref = gpu_preference()
        if pref != "nvidia" and not (nvidia_available() and pref in ("both", "auto")):
            gfx = os.getenv("JARVIS_ROCM_GFX", "11.0.0").strip()
            if gfx:
                env.setdefault("HSA_OVERRIDE_GFX_VERSION", gfx)
    except Exception:
        pref = (os.getenv("JARVIS_GPU_PREFER") or "auto").strip().lower()
        if pref != "nvidia":
            gfx = os.getenv("JARVIS_ROCM_GFX", "11.0.0").strip()
            if gfx:
                env.setdefault("HSA_OVERRIDE_GFX_VERSION", gfx)
    return env


def _comfy_extra_args() -> list[str]:
    custom = os.getenv("JARVIS_COMFYUI_ARGS", "").strip()
    if custom:
        return custom.split()
    from jarvis.comfyui_settings import effective_cpu_mode

    if effective_cpu_mode():
        return ["--cpu"]
    args = ["--fp32-text-enc"]
    try:
        from jarvis.gpu_routing import gpu_preference, nvidia_available

        if gpu_preference() in ("nvidia", "both", "auto") and nvidia_available():
            idx = (os.getenv("JARVIS_CUDA_DEVICE") or "0").strip()
            args.extend(["--cuda-device", idx])
    except Exception:
        pass
    return args


def _comfy_cmd() -> tuple[list[str], Path] | None:
    custom = os.getenv("JARVIS_COMFYUI_CMD", "").strip()
    if custom:
        parts = custom.split()
        cwd = Path(parts[0]).parent if parts else PROJECT_ROOT
        if parts and parts[0].endswith(".py"):
            cwd = Path(parts[1] if parts[0] == sys.executable else parts[0]).parent
        return parts, cwd

    candidates = [
        PROJECT_ROOT / "tools" / "ComfyUI" / "main.py",
        Path.home() / "ComfyUI" / "main.py",
    ]
    for main_py in candidates:
        if main_py.exists():
            port = os.getenv("JARVIS_COMFYUI_PORT", "8188")
            py = _comfy_python(main_py.parent)
            cmd = [py, str(main_py), "--listen", "127.0.0.1", "--port", port, *_comfy_extra_args()]
            return cmd, main_py.parent
    return None


def _should_autostart_comfy() -> bool:
    if os.getenv("JARVIS_AUTOSTART_COMFYUI", "1").lower() in ("0", "false", "no", "off"):
        return False
    return _comfy_cmd() is not None


def ensure_ollama(timeout: float = 45) -> bool:
    global _ollama_proc
    if _ollama_healthy():
        _log("Ollama: already running")
        return True
    if not shutil.which("ollama"):
        _log("Ollama: binary not found in PATH")
        return False
    ollama_env = os.environ.copy()
    try:
        from jarvis.gpu_routing import gpu_env_for_subprocess

        ollama_env.update(gpu_env_for_subprocess())
    except Exception:
        pass
    with _lock:
        if _ollama_healthy():
            return True
        try:
            _ollama_proc = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=ollama_env,
            )
            _log("Ollama: starting…")
        except Exception as e:
            _log(f"Ollama: failed to start — {e}")
            return False
    ok = _wait_for(_ollama_healthy, timeout=timeout)
    _log("Ollama: ready" if ok else "Ollama: timed out waiting for health")
    return ok


def ensure_comfyui(timeout: float = 120, *, block: bool = False, on_demand: bool = False) -> bool:
    global _comfy_proc
    if _comfy_healthy():
        _log("ComfyUI: already running")
        return True
    if not on_demand and not _should_autostart_comfy():
        return False
    spec = _comfy_cmd()
    if not spec:
        return False
    cmd, cwd = spec
    with _lock:
        if _comfy_healthy():
            return True
        if _comfy_proc and _comfy_proc.poll() is None:
            if block:
                ok = _wait_for(_comfy_healthy, timeout=timeout, interval=2)
                _log("ComfyUI: ready" if ok else "ComfyUI: still starting")
                return ok
            return False
        try:
            log_path = PROJECT_ROOT / "data" / "logs" / "comfyui.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_f = open(log_path, "a", encoding="utf-8")
            _comfy_proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=log_f,
                stderr=subprocess.STDOUT,
                env=_comfy_env(),
                start_new_session=True,
            )
            _log("ComfyUI: starting in background…")
        except Exception as e:
            _log(f"ComfyUI: failed to start — {e}")
            return False

    if not block:
        time.sleep(2)
        if _comfy_proc and _comfy_proc.poll() is not None:
            _log("ComfyUI: exited on startup (using Ollama for images)")
            return False
        return False

    ok = _wait_for(_comfy_healthy, timeout=timeout, interval=2)
    _log("ComfyUI: ready" if ok else "ComfyUI: still starting (image gen may use Ollama fallback)")
    return ok


def ensure_comfyui_background() -> None:
    threading.Thread(
        target=lambda: ensure_comfyui(timeout=120, block=True),
        daemon=True,
        name="jarvis-comfyui",
    ).start()


def stop_comfyui() -> None:
    """Stop the Jarvis-managed ComfyUI process."""
    _stop_comfyui()


def _stop_comfyui() -> None:
    global _comfy_proc
    port = os.getenv("JARVIS_COMFYUI_PORT", "8188")
    if _comfy_proc and _comfy_proc.poll() is None:
        _comfy_proc.terminate()
        try:
            _comfy_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _comfy_proc.kill()
    _comfy_proc = None
    if _comfy_healthy():
        try:
            subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True,
                timeout=5,
                check=False,
            )
        except Exception:
            pass
        time.sleep(2)


def restart_comfyui(*, block: bool = True, timeout: float = 120) -> bool:
    """Stop ComfyUI and start again with current GPU env (NVIDIA when configured)."""
    _log("ComfyUI: restarting for GPU routing")
    _stop_comfyui()
    return ensure_comfyui(timeout=timeout, block=block, on_demand=True)


def ensure_comfyui_nvidia(*, block: bool = True, timeout: float = 120) -> bool:
    """Start or restart ComfyUI on NVIDIA when JARVIS_GPU_PREFER=nvidia."""
    try:
        from jarvis.comfyui import comfyui_device_name, nvidia_comfyui_required
    except Exception:
        return ensure_comfyui(timeout=timeout, block=block, on_demand=True)

    if not nvidia_comfyui_required():
        return ensure_comfyui(timeout=timeout, block=block, on_demand=True)

    name = comfyui_device_name()
    if name and not any(
        token in name.lower() for token in ("nvidia", "geforce", "rtx", "quadro", "tesla")
    ):
        _log(f"ComfyUI: wrong GPU ({name}) — restarting on NVIDIA")
        return restart_comfyui(block=block, timeout=timeout)

    if _comfy_healthy():
        return True
    return ensure_comfyui(timeout=timeout, block=block, on_demand=True)
    from jarvis.comfyui_settings import auto_fallback_enabled, mark_runtime_cpu_fallback

    if not auto_fallback_enabled():
        return False
    mark_runtime_cpu_fallback()
    _log("ComfyUI: GPU failed — switching to CPU and retrying")
    _stop_comfyui()
    return ensure_comfyui(block=True, timeout=120)


def set_comfyui_mode(mode: str) -> dict:
    from jarvis.comfyui_settings import get_settings_dict, save_mode

    save_mode(mode)
    _log(f"ComfyUI: mode set to {mode}")
    _stop_comfyui()
    ok = ensure_comfyui(block=True, timeout=120)
    result = get_settings_dict()
    result["ok"] = ok
    result["restarted"] = ok
    if not ok:
        result["message"] = "ComfyUI failed to restart — check data/logs/comfyui.log"
    return result


def set_comfyui_checkpoint(checkpoint: str) -> dict:
    from jarvis.comfyui_settings import get_settings_dict, save_checkpoint

    save_checkpoint(checkpoint)
    _log(f"ComfyUI: checkpoint set to {checkpoint}")
    result = get_settings_dict()
    if checkpoint == "quality" and not result["installed"].get("quality"):
        result["ok"] = False
        result["message"] = "SDXL 1.0 not installed — run: ./scripts/install-sdxl-base.sh"
        return result
    if checkpoint == "flux" and not result["installed"].get("flux"):
        result["ok"] = False
        result["message"] = "Flux Schnell not installed — run: ./scripts/install-flux-schnell.sh"
        return result
    result["ok"] = True
    return result


def set_comfyui_checkpoint_file(filename: str) -> dict:
    from jarvis.comfyui_settings import (
        clear_checkpoint_file,
        get_settings_dict,
        save_checkpoint_file,
    )

    if not filename or filename in ("__preset__", "clear"):
        clear_checkpoint_file()
        _log("ComfyUI: using preset checkpoint")
    else:
        save_checkpoint_file(filename)
        _log(f"ComfyUI: checkpoint file set to {filename}")
    result = get_settings_dict()
    result["ok"] = True
    return result


def _whisper_model_label() -> str:
    try:
        from jarvis.audio_settings import saved_whisper_model

        saved = saved_whisper_model()
        if saved:
            return saved
    except Exception:
        pass
    return os.getenv("JARVIS_WHISPER_MODEL", "base")


def _musicgen_status() -> ServiceStatus:
    try:
        from jarvis.music_gen import musicgen_available, musicgen_backend

        ok = musicgen_available()
        backend = musicgen_backend() if ok else ""
    except Exception:
        ok, backend = False, ""
    return ServiceStatus(
        name="musicgen",
        label="MusicGen",
        running=ok,
        autostart=False,
        required=False,
        message="ready" if ok else "not installed",
        detail=backend,
    )


def _homeassistant_status() -> ServiceStatus:
    try:
        from jarvis.home_assistant import check_connection, ha_enabled, ha_url

        docker_up = container_running()
        api_up = ha_api_healthy(timeout=2)
        autostart = should_autostart_ha()

        if not ha_enabled():
            msg = "ready" if api_up else ("starting" if docker_up else "off")
            return ServiceStatus(
                name="homeassistant",
                label="Home Assistant",
                running=api_up,
                autostart=autostart,
                required=False,
                message=msg,
                detail=(ha_url() or "Configure in sidebar") if api_up else "Configure in sidebar",
            )
        conn = check_connection()
        ok = bool(conn.get("ok"))
        detail = conn.get("version") or ha_url() or ""
        if not ok:
            if api_up:
                detail = (conn.get("message") or "needs token")[:80]
            elif docker_up:
                detail = "container up — waiting for API"
            else:
                detail = (conn.get("message") or "needs token")[:80]
        return ServiceStatus(
            name="homeassistant",
            label="Home Assistant",
            running=ok or api_up,
            autostart=autostart,
            required=False,
            message="ready" if ok else ("starting" if (docker_up or api_up) else "setup"),
            detail=detail,
        )
    except Exception as exc:
        return ServiceStatus(
            name="homeassistant",
            label="Home Assistant",
            running=False,
            autostart=should_autostart_ha(),
            required=False,
            message="error",
            detail=str(exc)[:80],
        )


def _tool_status(name: str, check: Callable[[], bool], detail: str = "") -> ServiceStatus:
    ok = check()
    return ServiceStatus(
        name=name,
        label=name.replace("_", " ").title(),
        running=ok,
        autostart=False,
        required=False,
        message="ready" if ok else "not installed",
        detail=detail,
    )


_status_cache: dict = {"at": 0.0, "data": None}
_STATUS_TTL = float(os.getenv("JARVIS_SERVICES_CACHE_SEC", "15"))


def get_status(*, force: bool = False) -> dict:
    now = time.time()
    if not force and _status_cache["data"] is not None and now - _status_cache["at"] < _STATUS_TTL:
        return _status_cache["data"]
    load_jarvis_env()
    ollama = check_ollama()
    comfy = _comfy_healthy()
    from jarvis.config import piper_ready, piper_voice_label

    piper = piper_ready()
    ffmpeg = bool(shutil.which("ffmpeg"))
    whisper_cli = bool(shutil.which("whisper"))
    espeak = bool(shutil.which("espeak-ng") or shutil.which("espeak"))

    from jarvis import web_search
    from jarvis.comfyui_settings import get_settings_dict

    comfy_settings = get_settings_dict()
    comfy_settings["running"] = comfy

    services = [
        ServiceStatus(
            name="ollama",
            label="Ollama",
            running=ollama["running"],
            autostart=True,
            required=True,
            message="ready" if ollama["running"] else "offline",
            detail=f"{len(ollama.get('models', []))} models" if ollama["running"] else "",
        ),
        ServiceStatus(
            name="jarvis",
            label="ARIA GUI",
            running=_jarvis_port_open(),
            autostart=True,
            required=True,
            message="ready",
        ),
        ServiceStatus(
            name="comfyui",
            label="ComfyUI",
            running=comfy,
            autostart=_should_autostart_comfy(),
            required=False,
            message=(
                "ready"
                if comfy
                else ("starting" if _comfy_proc and _comfy_proc.poll() is None else "offline")
            ),
            detail=f"{comfy_settings['checkpoint_label']} · {comfy_settings['label']}"
            if comfy
            else "",
        ),
        ServiceStatus(
            name="web_search",
            label="Web search",
            running=web_search.is_available(),
            autostart=False,
            required=False,
            message="ready",
            detail=web_search.backend_name(),
        ),
        ServiceStatus(
            name="piper",
            label="Voice (Piper)",
            running=piper,
            autostart=False,
            required=False,
            message="ready" if piper else "not installed",
            detail=piper_voice_label() if piper else "",
        ),
        _tool_status("ffmpeg", lambda: ffmpeg),
        _tool_status("whisper", lambda: whisper_cli, detail=_whisper_model_label()),
        _tool_status("espeak", lambda: espeak),
        _musicgen_status(),
        _homeassistant_status(),
    ]

    ready = ollama["running"]
    payload = {
        "ready": ready,
        "services": [s.__dict__ for s in services],
        "boot_log": list(_boot_log[-20:]),
        "ollama": ollama,
        "comfyui_settings": comfy_settings,
    }
    _status_cache["at"] = time.time()
    _status_cache["data"] = payload
    return payload


def check_ollama() -> dict:
    from jarvis.ollama_health import check_ollama as _check

    return _check()


def ensure_services(*, pull_models: bool = False) -> dict:
    """Start required services. Never blocks on optional ComfyUI."""
    load_jarvis_env()
    _log("Starting Jarvis services…")
    ensure_ollama()
    from jarvis.ha_docker import ensure_homeassistant

    ensure_homeassistant(block=False)
    ensure_comfyui(block=False)
    if pull_models:
        pull_missing_models_background()
    warmup_chat_model_background()
    status = get_status()
    _log("Services bootstrap complete" if status["ready"] else "Waiting for Ollama…")
    return status


def pull_missing_models_background() -> None:
    def _run():
        try:
            from jarvis.model_pull import pull_model
            from jarvis.model_store import get_missing_models

            missing = get_missing_models()
            if not missing:
                return
            _log(f"Pulling {len(missing)} missing model(s) in background…")
            for model in missing[:3]:
                for event in pull_model(model):
                    if event.get("type") == "done":
                        _log(f"Model ready: {model}")
        except Exception as e:
            logger.debug("Background model pull: %s", e)

    threading.Thread(target=_run, daemon=True, name="jarvis-model-pull").start()


def warmup_chat_model_background() -> None:
    """Pre-load the default chat model into Ollama memory (non-blocking)."""
    if os.getenv("JARVIS_MODEL_WARMUP", "1").lower() in ("0", "false", "no"):
        return

    def _run():
        try:
            from jarvis.llm import ask
            from jarvis.model_store import get_models

            model = get_models().get("general") or "qwen2.5:7b"
            ask(model, [{"role": "user", "content": "hi"}], options={"num_predict": 1})
            _log(f"Chat model warmed: {model}")
        except Exception as e:
            logger.debug("Model warmup: %s", e)

    threading.Thread(target=_run, daemon=True, name="jarvis-model-warmup").start()


def stop_managed_services() -> None:
    global _ollama_proc, _comfy_proc
    for proc, name in ((_comfy_proc, "ComfyUI"), (_ollama_proc, "Ollama")):
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                _log(f"{name}: stopped")
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
    _comfy_proc = None
    # Do not stop Ollama by default — other apps may use it
    _ollama_proc = None


class ServicesWatchdog:
    """Keep Ollama (and optional ComfyUI) alive alongside the Jarvis server."""

    def __init__(self, interval: int = 30):
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            if not _ollama_healthy():
                logger.warning("Ollama down — restarting")
                ensure_ollama(timeout=30)
            if should_autostart_ha() and not container_running() and not ha_api_healthy(timeout=2):
                from jarvis.ha_docker import ensure_homeassistant

                logger.warning("Home Assistant container down — restarting")
                ensure_homeassistant(block=False)
            if _should_autostart_comfy() and not _comfy_healthy():
                global _comfy_proc
                if _comfy_proc is None or _comfy_proc.poll() is not None:
                    ensure_comfyui(block=False)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="jarvis-services-watchdog"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
