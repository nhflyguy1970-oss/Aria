"""Aria-specific workstation components registered with AI Platform."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiplatform.workstation.registry import WorkstationComponent


def aria_components() -> list[WorkstationComponent]:
    from aiplatform.workstation.registry import WorkstationComponent

    from jarvis.config import piper_ready, piper_voice_label
    from jarvis.ha_docker import (
        container_running,
        ensure_homeassistant,
        ha_api_healthy,
        should_autostart_ha,
    )
    from jarvis.services import (
        _comfy_healthy,
        _jarvis_port_open,
        _should_autostart_comfy,
        ensure_comfyui,
        restart_comfyui,
        stop_comfyui,
    )

    def _start_ha() -> bool:
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

    return [
        WorkstationComponent(
            id="aria",
            label="Aria",
            category="interface",
            required=True,
            autostart=True,
            application_id="aria",
            config_keys=["JARVIS_HOST", "JARVIS_PORT"],
            health=_jarvis_port_open,
            detail=lambda: (
                f"{os.getenv('JARVIS_HOST', '127.0.0.1')}:{os.getenv('JARVIS_PORT', '8765')}"
            ),
        ),
        WorkstationComponent(
            id="piper",
            label="Piper TTS",
            category="voice",
            application_id="aria",
            health=piper_ready,
            detail=piper_voice_label,
        ),
        WorkstationComponent(
            id="whisper",
            label="Whisper STT",
            category="voice",
            application_id="aria",
            health=lambda: bool(shutil.which("whisper")) or True,
            detail=lambda: os.getenv("JARVIS_WHISPER_MODEL", "faster-whisper"),
        ),
        WorkstationComponent(
            id="comfyui",
            label="ComfyUI",
            category="media",
            application_id="aria",
            autostart=_should_autostart_comfy(),
            managed=True,
            health=_comfy_healthy,
            start=lambda: ensure_comfyui(block=True, on_demand=True),
            stop=lambda: (stop_comfyui(), True)[1],
            restart=lambda: restart_comfyui(block=True),
        ),
        WorkstationComponent(
            id="homeassistant",
            label="Home Assistant",
            category="automation",
            application_id="aria",
            autostart=should_autostart_ha(),
            managed=True,
            health=lambda: ha_api_healthy(timeout=2) or container_running(),
            start=_start_ha,
            stop=_stop_ha,
            restart=lambda: (_stop_ha(), _start_ha())[1],
        ),
    ]


def register_with_platform() -> None:
    from aiplatform.workstation.extensions import register_components, register_probe

    from jarvis.application import acceptance_catalog
    from jarvis.application import probes as aria_probes

    register_components(aria_components)
    for probe_id, fn in aria_probes.PROBE_MAP.items():
        register_probe(probe_id, fn)
    acceptance_catalog.register()
