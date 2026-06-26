"""Start Memgraph Docker container when Jarvis boots (optional)."""

from __future__ import annotations

import logging
import os
import socket
import subprocess
import threading
import time

from jarvis.env_loader import load_jarvis_env

logger = logging.getLogger("jarvis.memgraph_docker")


def memgraph_container_name() -> str:
    return (os.getenv("JARVIS_MEMGRAPH_CONTAINER") or "jarvis-memgraph").strip()


def memgraph_bolt_port() -> int:
    try:
        return int(os.getenv("JARVIS_GRAPH_BOLT_PORT", "7687").strip())
    except ValueError:
        return 7687


def memgraph_http_port() -> int:
    try:
        return int(os.getenv("JARVIS_GRAPH_HTTP_PORT", "7444").strip())
    except ValueError:
        return 7444


def should_autostart_memgraph() -> bool:
    load_jarvis_env()
    from jarvis.service_policy import autostart_memgraph

    if not autostart_memgraph():
        return False
    from jarvis.ha_docker import docker_available

    return docker_available()


def memgraph_bolt_healthy(timeout: float = 2) -> bool:
    port = memgraph_bolt_port()
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_bolt(timeout: float = 60, interval: float = 2) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if memgraph_bolt_healthy(timeout=min(1.5, interval)):
            return True
        from jarvis.ha_docker import container_exists, container_running

        if not container_running(memgraph_container_name()) and not container_exists(memgraph_container_name()):
            return False
        time.sleep(interval)
    return memgraph_bolt_healthy()


def ensure_memgraph(*, block: bool = False, timeout: float = 60) -> bool:
    """Start the Memgraph Docker container when autostart is enabled."""
    from jarvis.ha_docker import container_exists, container_running, docker_available

    if not should_autostart_memgraph():
        return memgraph_bolt_healthy() or container_running(memgraph_container_name())

    name = memgraph_container_name()
    if memgraph_bolt_healthy():
        logger.info("Memgraph: bolt already up on port %s", memgraph_bolt_port())
        return True
    if container_running(name):
        if block:
            ok = _wait_for_bolt(timeout=timeout)
            logger.info("Memgraph: %s", "ready" if ok else "container up, bolt still starting")
            return ok
        return True

    if not docker_available():
        logger.warning("Memgraph autostart skipped — docker not found")
        return False

    port = memgraph_bolt_port()
    http_port = memgraph_http_port()
    try:
        if container_exists(name):
            logger.info("Memgraph: starting container %s", name)
            subprocess.run(["docker", "start", name], check=True, timeout=60)
        else:
            logger.info("Memgraph: creating container %s", name)
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--restart=unless-stopped",
                    "-p",
                    f"{port}:7687",
                    "-p",
                    f"{http_port}:7444",
                    "-v",
                    "jarvis-memgraph-data:/var/lib/memgraph",
                    "memgraph/memgraph-platform",
                ],
                check=True,
                timeout=120,
            )
    except subprocess.CalledProcessError as exc:
        logger.warning("Memgraph docker start failed: %s", exc)
        return False

    if block:
        ok = _wait_for_bolt(timeout=timeout)
        logger.info("Memgraph: %s", "ready" if ok else "still starting")
        return ok
    return True


def ensure_memgraph_background() -> None:
    if not should_autostart_memgraph():
        return
    threading.Thread(
        target=lambda: ensure_memgraph(block=True, timeout=60),
        daemon=True,
        name="jarvis-memgraph-docker",
    ).start()
