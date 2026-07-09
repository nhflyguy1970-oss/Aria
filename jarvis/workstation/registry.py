"""Workstation component registry — every subsystem Aria knows about."""

from __future__ import annotations

import logging
import os
import shutil
import socket
import subprocess
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.workstation")

CATEGORIES = (
    "inference",
    "interface",
    "knowledge",
    "database",
    "voice",
    "vision",
    "media",
    "automation",
    "monitoring",
    "tool",
)


def _http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _tcp_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _docker_running(container: str) -> bool:
    if not container or not shutil.which("docker"):
        return False
    try:
        proc = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return proc.returncode == 0 and proc.stdout.strip() == "true"
    except Exception:
        return False


def _docker_start(container: str) -> bool:
    if not container or not shutil.which("docker"):
        return False
    try:
        proc = subprocess.run(["docker", "start", container], capture_output=True, text=True, timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


def _docker_stop(container: str) -> bool:
    if not container or not shutil.which("docker"):
        return False
    try:
        proc = subprocess.run(["docker", "stop", container], capture_output=True, text=True, timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


def _platform_start_service(name: str) -> bool:
    try:
        import logging as _logging

        from aiplatform.runtime.docker import DockerRuntime

        DockerRuntime(_logging.getLogger("jarvis.workstation")).start_service(name)
        return component(name).healthy() if component(name) else False
    except Exception as exc:
        logger.debug("Platform docker start %s: %s", name, exc)
        return False


def _platform_start_profile(profile: str) -> bool:
    try:
        import logging as _logging

        from aiplatform.runtime.docker import DockerRuntime

        DockerRuntime(_logging.getLogger("jarvis.workstation")).start_profile(profile)
        return True
    except Exception as exc:
        logger.debug("Platform docker profile %s: %s", profile, exc)
        return False


@dataclass
class WorkstationComponent:
    """A managed or observed workstation subsystem."""

    id: str
    label: str
    category: str
    required: bool = False
    autostart: bool = False
    managed: bool = False
    docker_container: str = ""
    platform_service: str = ""
    config_keys: list[str] = field(default_factory=list)
    health: Callable[[], bool] = field(default=lambda: False, repr=False)
    detail: Callable[[], str] = field(default=lambda: "", repr=False)
    start: Callable[[], bool] | None = field(default=None, repr=False)
    stop: Callable[[], bool] | None = field(default=None, repr=False)
    restart: Callable[[], bool] | None = field(default=None, repr=False)

    def healthy(self) -> bool:
        try:
            return bool(self.health())
        except Exception:
            return False

    def status_detail(self) -> str:
        try:
            return self.detail()
        except Exception:
            return ""

    def to_dict(self, *, include_actions: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "required": self.required,
            "autostart": self.autostart,
            "managed": self.managed,
            "running": self.healthy(),
            "detail": self.status_detail(),
            "config_keys": list(self.config_keys),
        }
        if self.docker_container:
            payload["docker_container"] = self.docker_container
        if include_actions:
            payload["actions"] = {
                "start": self.managed and self.start is not None,
                "stop": self.managed and self.stop is not None,
                "restart": self.managed and self.restart is not None,
            }
        return payload


_REGISTRY: dict[str, WorkstationComponent] = {}
_built = False


def _docker_component(
    *,
    id: str,
    label: str,
    category: str,
    container: str,
    health: Callable[[], bool],
    platform_service: str = "",
    required: bool = False,
    autostart: bool = False,
    config_keys: list[str] | None = None,
) -> WorkstationComponent:
    def _start() -> bool:
        if platform_service and _platform_start_service(platform_service):
            return health()
        if _docker_start(container):
            return health()
        return False

    def _stop() -> bool:
        return _docker_stop(container)

    def _restart() -> bool:
        _stop()
        return _start()

    return WorkstationComponent(
        id=id,
        label=label,
        category=category,
        required=required,
        autostart=autostart,
        managed=True,
        docker_container=container,
        platform_service=platform_service,
        config_keys=config_keys or [],
        health=health,
        detail=lambda: container if _docker_running(container) else "container stopped",
        start=_start,
        stop=_stop,
        restart=_restart,
    )


def _build_registry() -> None:
    global _built
    if _built:
        return

    from jarvis import web_search
    from jarvis.config import piper_ready, piper_voice_label
    from jarvis.ha_docker import container_running, ha_api_healthy, should_autostart_ha

    def _ollama_health() -> bool:
        from jarvis.services import _ollama_healthy

        return _ollama_healthy()

    def _jarvis_health() -> bool:
        from jarvis.services import _jarvis_port_open

        return _jarvis_port_open()

    def _comfy_health() -> bool:
        from jarvis.services import _comfy_healthy

        return _comfy_healthy()

    def _comfy_autostart() -> bool:
        from jarvis.services import _should_autostart_comfy

        return _should_autostart_comfy()

    def _ollama_detail() -> str:
        from jarvis.services import check_ollama

        info = check_ollama()
        if info.get("running"):
            models = info.get("models") or []
            return f"{len(models)} models"
        return "offline"

    def _ensure_ollama() -> bool:
        from jarvis.services import ensure_ollama

        return ensure_ollama(timeout=45)

    def _ensure_comfyui() -> bool:
        from jarvis.services import ensure_comfyui

        return ensure_comfyui(block=True, on_demand=True)

    def _restart_comfyui() -> bool:
        from jarvis.services import restart_comfyui

        return restart_comfyui(block=True)

    def _stop_comfyui_managed() -> bool:
        from jarvis.services import stop_comfyui

        stop_comfyui()
        return True

    def _ensure_services() -> bool:
        from jarvis.services import ensure_services

        ensure_services(pull_models=False)
        return _ollama_health()

    from jarvis.ha_docker import ensure_homeassistant

    def _start_ha() -> bool:
        from jarvis.ha_docker import ensure_homeassistant

        ensure_homeassistant(block=True)
        return ha_api_healthy(timeout=5)

    def _stop_ha() -> bool:
        if not shutil.which("docker"):
            return False
        try:
            subprocess.run(["docker", "stop", "homeassistant"], capture_output=True, timeout=30)
            return True
        except Exception:
            return False

    _REGISTRY["ollama"] = WorkstationComponent(
        id="ollama",
        label="Ollama",
        category="inference",
        required=True,
        autostart=True,
        managed=True,
        config_keys=["OLLAMA_HOST", "JARVIS_GPU_PREFER"],
        health=_ollama_health,
        detail=_ollama_detail,
        start=_ensure_ollama,
    )

    litellm_url = os.getenv("JARVIS_LITELLM_URL", "http://127.0.0.1:4000").rstrip("/")
    _REGISTRY["litellm"] = _docker_component(
        id="litellm",
        label="LiteLLM",
        category="inference",
        container="ai-litellm",
        platform_service="litellm",
        autostart=False,
        config_keys=["JARVIS_LITELLM_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"],
        health=lambda: _http_ok(f"{litellm_url}/health/readiness"),
    )

    lmstudio_url = os.getenv("JARVIS_LMSTUDIO_URL", "http://127.0.0.1:1234").rstrip("/")
    _REGISTRY["lmstudio"] = WorkstationComponent(
        id="lmstudio",
        label="LM Studio",
        category="inference",
        managed=False,
        config_keys=["JARVIS_LMSTUDIO_URL"],
        health=lambda: _http_ok(f"{lmstudio_url}/v1/models"),
        detail=lambda: lmstudio_url,
    )

    _REGISTRY["aria"] = WorkstationComponent(
        id="aria",
        label="Aria",
        category="interface",
        required=True,
        autostart=True,
        managed=False,
        config_keys=["JARVIS_HOST", "JARVIS_PORT"],
        health=_jarvis_health,
        detail=lambda: f"{os.getenv('JARVIS_HOST', '127.0.0.1')}:{os.getenv('JARVIS_PORT', '8765')}",
    )

    openwebui_url = os.getenv("JARVIS_OPENWEBUI_URL", "http://127.0.0.1:3000").rstrip("/")
    _REGISTRY["open_webui"] = _docker_component(
        id="open_webui",
        label="Open WebUI",
        category="interface",
        container=os.getenv("JARVIS_OPENWEBUI_CONTAINER", "ai-open-webui"),
        autostart=False,
        config_keys=["JARVIS_OPENWEBUI_URL", "JARVIS_OPENWEBUI_CONTAINER"],
        health=lambda: _http_ok(f"{openwebui_url}/health") or _http_ok(openwebui_url),
    )

    searx_url = web_search.searxng_url()
    _REGISTRY["searxng"] = WorkstationComponent(
        id="searxng",
        label="SearXNG",
        category="knowledge",
        managed=False,
        autostart=False,
        config_keys=["JARVIS_SEARXNG_URL"],
        health=web_search.searxng_available,
        detail=lambda: searx_url if web_search.searxng_available() else web_search.backend_name(),
    )

    _REGISTRY["web_search"] = WorkstationComponent(
        id="web_search",
        label="Web Search",
        category="knowledge",
        managed=False,
        health=web_search.is_available,
        detail=web_search.backend_name,
    )

    pg_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    _REGISTRY["postgres"] = _docker_component(
        id="postgres",
        label="PostgreSQL",
        category="database",
        container="ai-postgres",
        platform_service="postgres",
        autostart=False,
        config_keys=["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_DB"],
        health=lambda: _tcp_open(pg_host, pg_port),
    )

    redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    _REGISTRY["redis"] = _docker_component(
        id="redis",
        label="Redis",
        category="database",
        container="ai-redis",
        platform_service="redis",
        autostart=False,
        config_keys=["REDIS_HOST", "REDIS_PORT"],
        health=lambda: _tcp_open(redis_host, redis_port),
    )

    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    _REGISTRY["qdrant"] = _docker_component(
        id="qdrant",
        label="Qdrant",
        category="database",
        container=os.getenv("JARVIS_QDRANT_CONTAINER", "ai-qdrant"),
        platform_service="qdrant",
        autostart=False,
        config_keys=["QDRANT_URL", "QDRANT_COLLECTION"],
        health=lambda: _http_ok(f"{qdrant_url}/healthz") or _http_ok(qdrant_url),
    )

    mongo_host = os.getenv("MONGODB_HOST", "127.0.0.1")
    mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
    _REGISTRY["mongodb"] = _docker_component(
        id="mongodb",
        label="MongoDB",
        category="database",
        container=os.getenv("JARVIS_MONGODB_CONTAINER", "ai-mongodb"),
        platform_service="mongodb",
        autostart=False,
        config_keys=["MONGODB_HOST", "MONGODB_PORT", "MONGODB_URI"],
        health=lambda: _tcp_open(mongo_host, mongo_port),
    )

    _REGISTRY["piper"] = WorkstationComponent(
        id="piper",
        label="Piper TTS",
        category="voice",
        managed=False,
        health=piper_ready,
        detail=piper_voice_label,
    )

    _REGISTRY["whisper"] = WorkstationComponent(
        id="whisper",
        label="Whisper STT",
        category="voice",
        managed=False,
        health=lambda: bool(shutil.which("whisper")) or True,
        detail=lambda: os.getenv("JARVIS_WHISPER_MODEL", "faster-whisper"),
    )

    _REGISTRY["vision"] = WorkstationComponent(
        id="vision",
        label="Vision",
        category="vision",
        managed=False,
        health=lambda: _ollama_health(),
        detail=lambda: "ollama vision models",
    )

    _REGISTRY["comfyui"] = WorkstationComponent(
        id="comfyui",
        label="ComfyUI",
        category="media",
        autostart=_comfy_autostart(),
        managed=True,
        config_keys=["JARVIS_COMFYUI_URL", "JARVIS_COMFYUI_PORT", "JARVIS_AUTOSTART_COMFYUI"],
        health=_comfy_health,
        start=_ensure_comfyui,
        stop=_stop_comfyui_managed,
        restart=_restart_comfyui,
    )

    _REGISTRY["homeassistant"] = WorkstationComponent(
        id="homeassistant",
        label="Home Assistant",
        category="automation",
        autostart=should_autostart_ha(),
        managed=True,
        health=lambda: ha_api_healthy(timeout=2) or container_running(),
        detail=lambda: "api ready" if ha_api_healthy(timeout=2) else "container only",
        start=_start_ha,
        stop=_stop_ha,
        restart=lambda: (_stop_ha(), _start_ha())[1],
    )

    n8n_url = os.getenv("JARVIS_N8N_URL", "http://127.0.0.1:5678").rstrip("/")
    _REGISTRY["n8n"] = _docker_component(
        id="n8n",
        label="n8n",
        category="automation",
        container=os.getenv("JARVIS_N8N_CONTAINER", "ai-n8n"),
        autostart=False,
        config_keys=["JARVIS_N8N_URL", "JARVIS_N8N_CONTAINER"],
        health=lambda: _http_ok(f"{n8n_url}/healthz") or _http_ok(n8n_url),
    )

    _REGISTRY["scheduler"] = WorkstationComponent(
        id="scheduler",
        label="Platform Scheduler",
        category="automation",
        managed=False,
        health=lambda: True,
        detail=lambda: "aiplatform scheduler + proactive timers",
    )

    _REGISTRY["prometheus"] = WorkstationComponent(
        id="prometheus",
        label="Prometheus",
        category="monitoring",
        managed=False,
        config_keys=["JARVIS_PROMETHEUS_URL"],
        health=lambda: _http_ok(os.getenv("JARVIS_PROMETHEUS_URL", "http://127.0.0.1:9090") + "/-/healthy"),
    )

    _REGISTRY["grafana"] = WorkstationComponent(
        id="grafana",
        label="Grafana",
        category="monitoring",
        managed=False,
        config_keys=["JARVIS_GRAFANA_URL"],
        health=lambda: _http_ok(os.getenv("JARVIS_GRAFANA_URL", "http://127.0.0.1:3001") + "/api/health"),
    )

    def _workstation_up() -> bool:
        return _ensure_services()

    _REGISTRY["workstation"] = WorkstationComponent(
        id="workstation",
        label="Workstation Bootstrap",
        category="automation",
        required=True,
        autostart=True,
        managed=True,
        health=lambda: _ollama_health() and _jarvis_health(),
        detail=lambda: "core services",
        start=_workstation_up,
    )

    _built = True


def get_registry() -> dict[str, WorkstationComponent]:
    _build_registry()
    return dict(_REGISTRY)


def all_components(*, category: str | None = None) -> list[WorkstationComponent]:
    reg = get_registry()
    items = list(reg.values())
    if category:
        items = [c for c in items if c.category == category]
    return sorted(items, key=lambda c: (c.category, c.label))


def component(component_id: str) -> WorkstationComponent | None:
    return get_registry().get(component_id)


def registry_snapshot(*, force: bool = False) -> dict[str, Any]:
    """Full registry status for API and operations."""
    del force
    from jarvis.environment import snapshot as env_snapshot
    from jarvis.resource_router import snapshot as resource_snapshot

    components = [c.to_dict() for c in all_components()]
    required = [c for c in components if c.get("required")]
    required_down = [c["id"] for c in required if not c.get("running")]
    optional_down = [
        c["id"] for c in components if not c.get("required") and c.get("managed") and not c.get("running")
    ]
    return {
        "ready": not required_down,
        "components": components,
        "categories": list(CATEGORIES),
        "required_down": required_down,
        "optional_down": optional_down[:8],
        "environment": env_snapshot(include_resources=True),
        "resources": resource_snapshot(),
        "summary": {
            "total": len(components),
            "running": sum(1 for c in components if c.get("running")),
            "managed": sum(1 for c in components if c.get("managed")),
        },
    }


def components_as_service_status() -> list[dict[str, Any]]:
    """Bridge for legacy services consumers."""
    return [
        {
            **{k: v for k, v in c.to_dict(include_actions=False).items() if k != "config_keys"},
            "name": c.id,
            "message": "ready" if c.healthy() else "offline",
        }
        for c in all_components()
        if c.id not in ("workstation",)
    ]
