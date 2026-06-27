"""P0/P1 upgrade dependency and model inventory with live status."""

from __future__ import annotations

import importlib.util
import os
import shutil
from typing import Any

# pip packages introduced or required by P0/P1 features
PIP_PACKAGES: list[dict[str, Any]] = [
    {
        "id": "faster_whisper",
        "module": "faster_whisper",
        "package": "faster-whisper>=1.0.0",
        "feature": "Whisper STT (default voice transcription)",
        "tier": "P1",
        "required": False,
        "install": "pip install -r requirements-optional.txt",
        "notes": "Included in requirements-optional.txt; pulls PyTorch.",
    },
    {
        "id": "openwakeword",
        "module": "openwakeword",
        "package": "openwakeword>=0.4.0",
        "feature": "Wake word detection",
        "tier": "P1",
        "required": False,
        "install": "pip install openwakeword onnxruntime",
        "notes": "Also needs onnxruntime. Wake models download on first use.",
    },
    {
        "id": "onnxruntime",
        "module": "onnxruntime",
        "package": "onnxruntime",
        "feature": "Wake word (openWakeWord runtime)",
        "tier": "P1",
        "required": False,
        "install": "pip install onnxruntime",
    },
    {
        "id": "realtimestt",
        "module": "RealtimeSTT",
        "package": "realtimestt[faster-whisper]",
        "feature": "RealTimeSTT low-latency voice pipeline",
        "tier": "P1",
        "required": False,
        "env_flag": "JARVIS_REALTIMESTT",
        "install": "pip install 'realtimestt[faster-whisper]'",
        "notes": "Optional; set JARVIS_REALTIMESTT=1 and pick RealTimeSTT in GUI.",
    },
    {
        "id": "ddgs",
        "module": "ddgs",
        "package": "ddgs>=9.0.0",
        "feature": "P0 curated news / web headlines",
        "tier": "P0",
        "required": False,
        "install": "pip install ddgs",
        "notes": "Fallback: duckduckgo-search in requirements-optional.txt.",
    },
    {
        "id": "weasyprint",
        "module": "weasyprint",
        "package": "weasyprint>=62.0",
        "feature": "Journal PDF export",
        "tier": "P0",
        "required": False,
        "install": "pip install weasyprint",
    },
]

# Ollama models for P1 routing / brain selection (auto-pulled on first run when enabled)
OLLAMA_MODELS: list[dict[str, Any]] = [
    {
        "id": "router",
        "model": "qwen3:1.7b",
        "env": "JARVIS_ROUTER_MODEL",
        "feature": "P1 local intent router",
        "tier": "P1",
        "required": True,
        "size_approx": "~1.2 GB",
        "pull": "ollama pull qwen3:1.7b",
        "fallbacks": ["qwen2.5:3b", "qwen2.5:7b"],
    },
    {
        "id": "fast_chat",
        "model": "qwen3:1.7b",
        "env": "JARVIS_FAST_MODEL",
        "feature": "P1 fast / voice chat model",
        "tier": "P1",
        "required": True,
        "size_approx": "~1.2 GB",
        "pull": "ollama pull qwen3:1.7b",
        "fallbacks": ["qwen2.5:3b", "qwen2.5:7b"],
    },
    {
        "id": "reasoning",
        "model": "deepseek-r1:7b",
        "env": "JARVIS_REASONING_MODEL",
        "feature": "P1 deep thinking / reasoning chat",
        "tier": "P1",
        "required": False,
        "size_approx": "~4.7 GB",
        "pull": "ollama pull deepseek-r1:7b",
        "fallbacks": ["deepseek-r1:1.5b", "qwen2.5:14b", "qwen2.5:7b"],
    },
]

# Non-Ollama models / binaries
OTHER_MODELS: list[dict[str, Any]] = [
    {
        "id": "whisper_small",
        "name": "whisper small",
        "env": "JARVIS_WHISPER_MODEL",
        "default": "small",
        "feature": "Wake-word & live STT accuracy",
        "tier": "P1",
        "cache": "~/.cache/huggingface/hub or ~/.cache/whisper",
        "install": "Used automatically on first transcribe; pre-cache: python -c \"from faster_whisper import WhisperModel; WhisperModel('small')\"",
    },
    {
        "id": "openwakeword_hey_jarvis",
        "name": "hey_jarvis",
        "env": "JARVIS_WAKEWORD_MODEL",
        "default": "hey_jarvis",
        "feature": "Wake word model",
        "tier": "P1",
        "install": "Downloaded by openwakeword on first wake-word start",
    },
    {
        "id": "piper_voice",
        "name": "en_US-lessac-medium",
        "env": "JARVIS_PIPER_MODEL",
        "feature": "TTS voice (preferred over espeak)",
        "tier": "core",
        "install": "./scripts/install-dependencies.sh or install-piper.sh",
    },
]

SYSTEM_TOOLS: list[dict[str, Any]] = [
    {"id": "ffmpeg", "binary": "ffmpeg", "feature": "Audio capture, RealTimeSTT file feed, TTS", "tier": "P1"},
    {"id": "pw_record", "binary": "pw-record", "feature": "PipeWire live recording", "tier": "P1"},
    {"id": "espeak", "binary": "espeak-ng", "feature": "Fallback TTS", "tier": "core"},
]


def _module_installed(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _env_flag_enabled(name: str | None) -> bool:
    if not name:
        return True
    return os.getenv(name, "1").strip().lower() not in ("0", "false", "no", "off")


def _ollama_model_status(model: str, fallbacks: list[str] | None = None) -> dict[str, Any]:
    from jarvis.ollama_health import check_ollama, model_available

    ollama = check_ollama()
    if not ollama.get("running"):
        return {"installed": False, "reason": "ollama not running", "resolved": None}
    if model_available(model):
        return {"installed": True, "resolved": model}
    for fb in fallbacks or []:
        if model_available(fb):
            return {"installed": True, "resolved": fb, "fallback": True}
    return {"installed": False, "resolved": None}


def dependency_report(*, include_optional: bool = True) -> dict[str, Any]:
    """Full inventory with installed/missing status."""
    pip_rows: list[dict[str, Any]] = []
    missing_pip: list[str] = []
    for row in PIP_PACKAGES:
        if row.get("env_flag") and not _env_flag_enabled(row["env_flag"]):
            if not include_optional:
                continue
            status = "disabled"
            installed = None
        else:
            installed = _module_installed(row["module"])
            status = "ok" if installed else ("missing" if row.get("required") else "optional_missing")
            if not installed and (row.get("required") or row.get("env_flag") and _env_flag_enabled(row["env_flag"])):
                missing_pip.append(row["install"])
        pip_rows.append({**row, "installed": installed, "status": status})

    ollama_rows: list[dict[str, Any]] = []
    missing_models: list[str] = []
    for row in OLLAMA_MODELS:
        model = (os.getenv(row["env"]) or row["model"]).strip()
        st = _ollama_model_status(model, row.get("fallbacks"))
        needs = row.get("required") or _env_flag_enabled("JARVIS_BRAIN_ROUTING")
        if not st["installed"] and needs and row["id"] != "reasoning":
            missing_models.append(row["pull"].replace(row["model"], model))
        elif not st["installed"] and row["id"] == "reasoning" and _env_flag_enabled("JARVIS_BRAIN_ROUTING"):
            missing_models.append(row["pull"].replace(row["model"], model))
        ollama_rows.append(
            {
                **row,
                "configured_model": model,
                "installed": st["installed"],
                "resolved_model": st.get("resolved"),
                "fallback_in_use": st.get("fallback", False),
                "status": "ok" if st["installed"] else "missing",
            }
        )

    system_rows: list[dict[str, Any]] = []
    missing_system: list[str] = []
    for row in SYSTEM_TOOLS:
        ok = bool(shutil.which(row["binary"]))
        if not ok:
            missing_system.append(row["binary"])
        system_rows.append({**row, "installed": ok, "status": "ok" if ok else "missing"})

    stt_backend = "whisper"
    realtimestt_ok = False
    try:
        from jarvis.stt import stt_status

        st = stt_status()
        stt_backend = st.get("backend", "whisper")
        realtimestt_ok = bool(st.get("realtimestt"))
    except Exception:
        pass

    return {
        "ok": not missing_pip and not missing_models and not missing_system,
        "stt_backend": stt_backend,
        "realtimestt_ready": realtimestt_ok,
        "pip": pip_rows,
        "ollama_models": ollama_rows,
        "other_models": OTHER_MODELS,
        "system_tools": system_rows,
        "missing": {
            "pip_install": sorted(set(missing_pip)),
            "ollama_pull": sorted(set(missing_models)),
            "system_apt": [f"sudo apt install {b}" for b in missing_system if b in ("ffmpeg", "espeak-ng")],
            "system_tools": missing_system,
        },
        "install_scripts": [
            "./scripts/install-dependencies.sh",
            "./scripts/pull-models.sh",
            "./scripts/pull-p1-models.sh",
        ],
    }


def dependency_summary() -> dict[str, Any]:
    """Compact counts for checklist / dashboard."""
    report = dependency_report(include_optional=False)
    pip_missing = [r for r in report["pip"] if r.get("status") == "missing"]
    model_missing = [r for r in report["ollama_models"] if r.get("status") == "missing" and r.get("required")]
    optional_model_missing = [r for r in report["ollama_models"] if r.get("status") == "missing" and not r.get("required")]
    return {
        "pip_missing": len(pip_missing),
        "models_missing": len(model_missing),
        "optional_models_missing": len(optional_model_missing),
        "system_missing": len([r for r in report["system_tools"] if not r.get("installed")]),
        "missing_pip": [r["package"] for r in pip_missing],
        "missing_models": [r.get("configured_model") for r in model_missing + optional_model_missing],
        "pull_commands": report["missing"]["ollama_pull"],
    }
