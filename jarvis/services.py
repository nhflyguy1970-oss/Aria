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
    from jarvis.security.owner.env_boundary import copy_process_env

    env = copy_process_env()
    # Tensors of 1-32 MB (most Qwen-Image layers) came from glibc's heap, which ComfyUI's
    # /free could not hand back: 6.0 GB RSS + swap stayed after one Qwen job. Allocating
    # them with mmap returns them on free (1.8 GB; idle is 1.1 GB) — measured 2026-10-14.
    threshold = os.getenv("JARVIS_COMFYUI_MMAP_THRESHOLD", "1048576").strip()
    if threshold and threshold != "0":
        env.setdefault("MALLOC_MMAP_THRESHOLD_", threshold)
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
    # ARIA's own nodes (GPU text-encoder loader for Qwen-Image); the ComfyUI install is untouched.
    nodes_cfg = PROJECT_ROOT / "comfy_nodes" / "extra_paths.yaml"
    if nodes_cfg.is_file():
        args.extend(["--extra-model-paths-config", str(nodes_cfg)])
    try:
        from jarvis.gpu_routing import gpu_preference, nvidia_available

        if gpu_preference() in ("nvidia", "both", "auto") and nvidia_available():
            idx = (os.getenv("JARVIS_CUDA_DEVICE") or "0").strip()
            args.extend(["--cuda-device", idx])
            # Phase 8 qualified FLUX profile: offload and keep 2.5 GiB of the RTX 3060 free.
            args.extend(["--lowvram", "--reserve-vram", "2.5", "--disable-dynamic-vram"])
    except Exception:
        pass
    # ComfyUI keeps every model it has loaded in system RAM (and later swap): 19 GB after
    # one afternoon (2026-10-13). RAM-pressure caching drops cached models whenever free
    # RAM falls below this many GB, which covers ARIA's largest image admission (24 GiB).
    cache_gb = os.getenv("JARVIS_COMFYUI_CACHE_RAM_GB", "24").strip()
    if cache_gb and cache_gb != "0":
        args.extend(["--cache-ram", cache_gb])
    return args


def _comfy_main_py() -> str | None:
    """Path of the ComfyUI main.py ARIA launches — a plain lookup with no GPU probing, safe
    from background threads (the full _comfy_cmd() also builds GPU launch flags)."""
    custom = os.getenv("JARVIS_COMFYUI_CMD", "").strip()
    if custom:
        return next((part for part in custom.split() if part.endswith("main.py")), None)
    for main_py in (PROJECT_ROOT / "tools" / "ComfyUI" / "main.py", Path.home() / "ComfyUI" / "main.py"):
        if main_py.exists():
            return str(main_py)
    return None


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
    from jarvis.security.owner.env_boundary import copy_process_env

    ollama_env = copy_process_env()
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
        if not (_comfy_proc and _comfy_proc.poll() is None):
            adopt_running_comfyui()
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
            from jarvis.logging_config import open_rotating_log

            log_f = open_rotating_log(log_path)
            _comfy_proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=log_f,
                stderr=subprocess.STDOUT,
                env=_comfy_env(),
                start_new_session=True,
            )
            _log("ComfyUI: starting in background…")
            _start_idle_watch(_comfy_proc.pid, _comfy_proc)
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


COMFY_IDLE_STOP_S = int(os.getenv("JARVIS_COMFYUI_IDLE_STOP_MIN", "15")) * 60  # 0 disables
COMFY_IDLE_POLL_S = 60


def _comfy_last_activity(started: float) -> float | None:
    """Epoch seconds of ComfyUI's latest activity, or None while it is busy.

    Busy = a queued/running prompt (from ARIA or ComfyUI's own web page) or an admitted ARIA
    RTX job. Otherwise the newest prompt-history timestamp, never earlier than start-up."""
    import json

    base = os.getenv("JARVIS_COMFYUI_URL", f"http://127.0.0.1:{os.getenv('JARVIS_COMFYUI_PORT', '8188')}")
    try:
        with urllib.request.urlopen(f"{base}/queue", timeout=5) as resp:
            q = json.loads(resp.read().decode())
        if q.get("queue_running") or q.get("queue_pending"):
            return None
        with urllib.request.urlopen(f"{base}/history?max_items=5", timeout=5) as resp:
            hist = json.loads(resp.read().decode())
    except Exception:
        return None  # unreachable or mid-start: never stop on uncertainty
    try:
        from jarvis.gpu_scheduler import status as gpu_status

        if gpu_status().get("heavy_active"):
            return None
    except Exception:
        pass
    last = started
    for entry in hist.values():
        for msg in (entry.get("status") or {}).get("messages") or []:
            ts = (msg[1] or {}).get("timestamp") if len(msg) > 1 and isinstance(msg[1], dict) else None
            if ts:
                last = max(last, ts / 1000.0)
    return last


_watched_comfy_pids: set[int] = set()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:  # a zombie child still answers kill(0)
        return Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1][0] != "Z"
    except (OSError, IndexError):
        return True


def _aria_comfy_pid() -> int | None:
    """PID of a running ComfyUI that ARIA launched (its main.py plus ARIA's --fp32-text-enc),
    found even after an ARIA restart lost the Popen handle. A ComfyUI started by hand is not."""
    main = _comfy_main_py()
    if not main:
        return None
    for proc_dir in Path("/proc").iterdir():
        if not proc_dir.name.isdigit():
            continue
        try:
            args = (proc_dir / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        argv = [a.decode(errors="replace") for a in args if a]
        if main in argv and "--fp32-text-enc" in argv and "--listen" in argv:
            return int(proc_dir.name)
    return None


def _terminate_pid(pid: int) -> None:
    import signal

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.time() + 10
    while time.time() < deadline and _pid_alive(pid):
        time.sleep(0.5)
    if _pid_alive(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def _watch_comfy_idle(pid: int, started: float, proc: subprocess.Popen | None = None) -> None:
    """Stop an ARIA-launched ComfyUI once idle COMFY_IDLE_STOP_S; the next image job starts it
    again on demand. Never touches a ComfyUI ARIA did not launch."""
    try:
        while COMFY_IDLE_STOP_S > 0:
            time.sleep(COMFY_IDLE_POLL_S)
            if not _pid_alive(pid) or (proc is not None and _comfy_proc is not proc):
                return
            last = _comfy_last_activity(started)
            if last is None:
                continue
            idle = time.time() - last
            if idle < COMFY_IDLE_STOP_S:
                continue
            with _lock:
                if not _pid_alive(pid) or _comfy_last_activity(started) is None:
                    continue
                _log(f"ComfyUI: idle {int(idle // 60)} min — stopping to return its RAM "
                     "(restarts on the next image job)")
                if proc is not None and _comfy_proc is proc:
                    _stop_comfyui()
                else:
                    _terminate_pid(pid)
            return
    finally:
        _watched_comfy_pids.discard(pid)


def _start_idle_watch(pid: int, proc: subprocess.Popen | None = None) -> None:
    if COMFY_IDLE_STOP_S <= 0 or pid in _watched_comfy_pids:
        return
    _watched_comfy_pids.add(pid)
    _log(f"ComfyUI: pid {pid} will stop after {COMFY_IDLE_STOP_S // 60} min idle")
    threading.Thread(target=_watch_comfy_idle, args=(pid, time.time(), proc),
                     name="comfyui-idle-stop", daemon=True).start()


RETAIN_MAX_MIB = int(os.getenv("JARVIS_COMFYUI_RETAIN_MAX_MIB", "6144"))


def _retained_mib(pid: int) -> int:
    """RSS + swap of a process, MiB (0 when unreadable)."""
    try:
        fields = dict(line.split(":", 1) for line in Path(f"/proc/{pid}/status").read_text().splitlines() if ":" in line)
        return sum(int(fields.get(k, "0 kB").split()[0]) for k in ("VmRSS", "VmSwap")) // 1024
    except (OSError, ValueError):
        return 0


def release_comfyui(reason: str, *, settle_s: float = 15.0) -> bool:
    """After a large job: stop the ARIA-launched ComfyUI if it still holds more than
    RETAIN_MAX_MIB of host memory once its /free has landed, and nothing else needs it.

    Qwen-Image left 6.0 GB (one job) to 25.6 GB (many jobs without /free) behind before the
    MALLOC_MMAP_THRESHOLD_ fix in _comfy_env; with it /free returns ComfyUI to ~1.8 GB, so this
    normally keeps ComfyUI running. Skipped while ComfyUI has a prompt, an RTX job is admitted
    or another media job is queued; a stopped ComfyUI restarts on the next image (~10 s)."""
    try:
        from jarvis.media_jobs import busy_state

        if busy_state().get("pending"):
            return False
    except Exception:  # noqa: BLE001
        pass
    proc = _comfy_proc if _comfy_proc is not None and _comfy_proc.poll() is None else None
    pid = proc.pid if proc else _aria_comfy_pid()
    if not pid:
        return False
    deadline = time.monotonic() + settle_s
    while (held := _retained_mib(pid)) > RETAIN_MAX_MIB and time.monotonic() < deadline:
        time.sleep(1)
    if held <= RETAIN_MAX_MIB:
        return False
    with _lock:
        if _comfy_last_activity(time.time()) is None:
            return False
        _log(f"ComfyUI: holds {held} MiB after {reason} — stopping to return it (restarts on the next image job)")
        if proc is not None:
            _stop_comfyui()
        else:
            _terminate_pid(pid)
        return True


def adopt_running_comfyui() -> int | None:
    """Watch an ARIA-launched ComfyUI left running by a previous ARIA process."""
    pid = _aria_comfy_pid()
    if pid and not (_comfy_proc and _comfy_proc.pid == pid):
        _start_idle_watch(pid)
    return pid


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


def fallback_comfyui_to_cpu(*, timeout: float = 120) -> bool:
    """Restart ComfyUI in CPU mode after a GPU failure. Safe to call repeatedly."""
    try:
        from jarvis.comfyui_settings import auto_fallback_enabled, mark_runtime_cpu_fallback

        if not auto_fallback_enabled():
            _log("ComfyUI: GPU failed — auto fallback disabled (mode is not auto)")
            return False
        mark_runtime_cpu_fallback()
        _log("ComfyUI: GPU failed — switching to CPU and retrying")
        _stop_comfyui()
        return ensure_comfyui(block=True, timeout=timeout, on_demand=True)
    except Exception as exc:
        _log(f"ComfyUI: CPU fallback failed: {exc}")
        return False


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
    if checkpoint == "zimage" and not result["installed"].get("zimage"):
        result["ok"] = False
        result["message"] = "Z-Image Turbo runtime or model files are not installed"
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
    ollama = check_ollama(soft_probe=False)
    # Kick a cached soft probe off-request so we don't block status on a wedged generate.
    try:

        def _bg_probe():
            try:
                from jarvis.ollama_health import check_ollama as _co

                _co(soft_probe=True, force_probe=False)
            except Exception:
                pass

        threading.Thread(target=_bg_probe, name="ollama-health-probe", daemon=True).start()
    except Exception:
        pass
    health_state = ollama.get("health_state") or (
        "healthy" if ollama.get("running") else "unavailable"
    )
    ollama_msg = {
        "healthy": "ready",
        "degraded": "degraded",
        "unavailable": "offline",
    }.get(health_state, "offline")
    ollama_detail_parts = []
    if ollama.get("running"):
        ollama_detail_parts.append(f"{len(ollama.get('models', []))} models")
    probe = ollama.get("probe") or {}
    if health_state == "degraded" and probe.get("detail"):
        ollama_detail_parts.append(str(probe["detail"])[:80])
    elif health_state == "healthy" and probe.get("model"):
        ollama_detail_parts.append(f"probe {probe.get('model')}")
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
            running=bool(ollama.get("running")),
            autostart=True,
            required=True,
            message=ollama_msg,
            detail=" · ".join(ollama_detail_parts),
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

    ready = ollama.get("health_state") == "healthy"
    payload = {
        "ready": ready,
        "ollama_health": ollama.get("health_state") or "unavailable",
        "services": [s.__dict__ for s in services],
        "boot_log": list(_boot_log[-20:]),
        "ollama": ollama,
        "comfyui_settings": comfy_settings,
    }
    _status_cache["at"] = time.time()
    _status_cache["data"] = payload
    return payload


def check_ollama(**kwargs) -> dict:
    from jarvis.ollama_health import check_ollama as _check

    return _check(**kwargs)


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
            from jarvis.ollama_runtime import warmup_chat_model

            result = warmup_chat_model()
            if result.get("ok"):
                _log(f"Chat model warmed: {result.get('model')} ({result.get('total_s')}s)")
            else:
                _log(f"Chat model warmup failed: {result.get('detail', 'unknown')}")
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
