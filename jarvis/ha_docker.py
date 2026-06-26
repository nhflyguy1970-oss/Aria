"""Start Home Assistant Docker container when Jarvis boots (optional)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

from jarvis.env_loader import PROJECT_ROOT, load_jarvis_env

logger = logging.getLogger("jarvis.ha_docker")


def ha_container_name() -> str:
    return (os.getenv("JARVIS_HA_CONTAINER") or "homeassistant").strip()


def ha_config_dir() -> Path:
    raw = (os.getenv("JARVIS_HA_CONFIG") or "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / "homeassistant"


def ha_image() -> str:
    return (os.getenv("JARVIS_HA_IMAGE") or "ghcr.io/home-assistant/home-assistant:stable").strip()


def ha_api_url() -> str:
    load_jarvis_env()
    from jarvis.home_assistant import ha_url

    url = ha_url() or "http://127.0.0.1:8123"
    return url.rstrip("/")


def should_autostart_ha() -> bool:
    load_jarvis_env()
    if os.getenv("JARVIS_HA_AUTOSTART", "1").lower() in ("0", "false", "no", "off"):
        return False
    return shutil.which("docker") is not None


def docker_available() -> bool:
    return shutil.which("docker") is not None


def container_running(name: str | None = None) -> bool:
    if not docker_available():
        return False
    target = name or ha_container_name()
    try:
        proc = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return target in (proc.stdout or "").splitlines()
    except Exception:
        return False


def container_exists(name: str | None = None) -> bool:
    if not docker_available():
        return False
    target = name or ha_container_name()
    try:
        proc = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return target in (proc.stdout or "").splitlines()
    except Exception:
        return False


def ha_api_healthy(timeout: float = 3) -> bool:
    try:
        with urllib.request.urlopen(f"{ha_api_url()}/api/", timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _wait_for_api(timeout: float = 180, interval: float = 2) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ha_api_healthy(timeout=min(3, interval)):
            return True
        if not container_running() and not container_exists():
            return False
        time.sleep(interval)
    return ha_api_healthy()


def ensure_homeassistant(*, block: bool = False, timeout: float = 180) -> bool:
    """Start the HA Docker container if autostart is enabled."""
    if not should_autostart_ha():
        return ha_api_healthy() or container_running()

    name = ha_container_name()
    if ha_api_healthy():
        logger.info("Home Assistant: API already up at %s", ha_api_url())
        return True
    if container_running(name):
        if block:
            ok = _wait_for_api(timeout=timeout)
            logger.info("Home Assistant: %s", "ready" if ok else "container up, API still starting")
            return ok
        logger.info("Home Assistant: container running, API still starting")
        return True

    if not docker_available():
        logger.warning("Home Assistant autostart skipped — docker not found")
        return False

    config_dir = ha_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        if container_exists(name):
            logger.info("Home Assistant: starting container %s", name)
            subprocess.run(["docker", "start", name], check=True, timeout=60)
        else:
            logger.info("Home Assistant: creating container %s", name)
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--restart=unless-stopped",
                    "--network=host",
                    "-v",
                    f"{config_dir}:/config",
                    ha_image(),
                ],
                check=True,
                timeout=120,
            )
    except subprocess.CalledProcessError as exc:
        logger.warning("Home Assistant docker start failed: %s", exc)
        return False

    if block:
        ok = _wait_for_api(timeout=timeout)
        logger.info("Home Assistant: %s", "ready" if ok else "still starting")
        return ok
    return True


def ensure_homeassistant_background() -> None:
    threading.Thread(
        target=lambda: ensure_homeassistant(block=True, timeout=180),
        daemon=True,
        name="jarvis-ha-docker",
    ).start()
