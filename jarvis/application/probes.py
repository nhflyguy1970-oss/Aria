"""Aria-specific integration probes (registered with platform when attached)."""

from __future__ import annotations

from jarvis.application.standalone.workstation_impl.integration_probes import (
    probe_cli_tool,
    probe_ocr,
)

PROBE_MAP = {
    "aria": lambda: _probe_aria_api(),
    "opencode": lambda: probe_cli_tool("opencode"),
    "claude_code": lambda: probe_cli_tool("claude_code"),
    "gemini_cli": lambda: probe_cli_tool("gemini_cli"),
    "piper": lambda: _probe_piper(),
    "whisper": lambda: _probe_whisper(),
    "tesseract": probe_ocr,
}


def _probe_aria_api():
    from jarvis.application.standalone.workstation_impl.integration_probes import probe_aria_api

    return probe_aria_api()


def _probe_piper():
    from jarvis.application.standalone.workstation_impl.integration_probes import probe_piper

    return probe_piper()


def _probe_whisper():
    from jarvis.application.standalone.workstation_impl.integration_probes import probe_whisper

    return probe_whisper()
