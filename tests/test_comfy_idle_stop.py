"""ComfyUI must not hoard system RAM: RAM-pressure caching, idle auto-stop, adoption after restarts."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import time

import pytest

from jarvis import services


def _fake_comfy(main_py: str, *extra: str) -> subprocess.Popen:
    """A sleeping process whose argv looks like an ARIA-launched ComfyUI."""
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", main_py, *extra])


@pytest.fixture
def fast_watch(monkeypatch):
    monkeypatch.setattr(services, "COMFY_IDLE_STOP_S", 1)
    monkeypatch.setattr(services, "COMFY_IDLE_POLL_S", 0.1)
    monkeypatch.setattr(services, "_log", lambda msg: None)
    services._watched_comfy_pids.clear()
    yield
    services._watched_comfy_pids.clear()


def test_launch_args_use_ram_pressure_caching(monkeypatch):
    monkeypatch.delenv("JARVIS_COMFYUI_ARGS", raising=False)
    monkeypatch.delenv("JARVIS_COMFYUI_CACHE_RAM_GB", raising=False)
    monkeypatch.setattr("jarvis.comfyui_settings.effective_cpu_mode", lambda: False)
    args = services._comfy_extra_args()
    assert args[args.index("--cache-ram") + 1] == "24"
    monkeypatch.setenv("JARVIS_COMFYUI_CACHE_RAM_GB", "0")
    assert "--cache-ram" not in services._comfy_extra_args()


def _urlopen_with(queue: dict, history: dict):
    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake(url, timeout=5):
        return Resp(json.dumps(queue if "/queue" in url else history).encode())

    return fake


def test_busy_queue_is_never_idle(monkeypatch):
    monkeypatch.setattr(services.urllib.request, "urlopen", _urlopen_with({"queue_running": [[1]]}, {}))
    assert services._comfy_last_activity(time.time() - 3600) is None


def test_last_activity_is_the_newest_history_timestamp(monkeypatch):
    now = time.time()
    hist = {"a": {"status": {"messages": [["execution_start", {"timestamp": (now - 900) * 1000}],
                                          ["execution_success", {"timestamp": (now - 600) * 1000}]]}}}
    monkeypatch.setattr(services.urllib.request, "urlopen", _urlopen_with({}, hist))
    monkeypatch.setattr("jarvis.gpu_scheduler.status", lambda: {"heavy_active": None})
    assert services._comfy_last_activity(now - 3600) == pytest.approx(now - 600)
    monkeypatch.setattr("jarvis.gpu_scheduler.status", lambda: {"heavy_active": "image"})
    assert services._comfy_last_activity(now - 3600) is None  # an admitted ARIA job is running


def test_idle_adopted_comfyui_is_stopped(monkeypatch, fast_watch, tmp_path):
    main = str(tmp_path / "ComfyUI" / "main.py")
    proc = _fake_comfy(main, "--listen", "127.0.0.1", "--fp32-text-enc")
    try:
        monkeypatch.setattr(services, "_comfy_main_py", lambda: main)
        monkeypatch.setattr(services, "_comfy_last_activity", lambda started: time.time() - 3600)
        assert services.adopt_running_comfyui() == proc.pid
        proc.wait(timeout=10)
        assert proc.returncode is not None
    finally:
        proc.kill()


def test_busy_comfyui_keeps_running(monkeypatch, fast_watch, tmp_path):
    main = str(tmp_path / "ComfyUI" / "main.py")
    proc = _fake_comfy(main, "--listen", "127.0.0.1", "--fp32-text-enc")
    try:
        monkeypatch.setattr(services, "_comfy_main_py", lambda: main)
        monkeypatch.setattr(services, "_comfy_last_activity", lambda started: None)
        services.adopt_running_comfyui()
        time.sleep(0.8)
        assert proc.poll() is None
    finally:
        proc.kill()


def test_hand_started_comfyui_is_never_adopted(monkeypatch, fast_watch, tmp_path):
    main = str(tmp_path / "ComfyUI" / "main.py")
    proc = _fake_comfy(main, "--listen", "127.0.0.1")  # no ARIA launch flags
    try:
        monkeypatch.setattr(services, "_comfy_main_py", lambda: main)
        assert services.adopt_running_comfyui() is None
    finally:
        proc.kill()
