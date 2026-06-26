"""Persistent model configuration — optimized defaults + user overrides."""

import json

from jarvis.config import DATA_DIR, is_uncensored
from jarvis.ollama_health import check_ollama

SETTINGS_FILE = DATA_DIR / "model_settings.json"

ROLES = ("general", "coder", "review", "vision", "image", "embed")

# Image backends and other non-Ollama roles — never passed to `ollama pull`.
NON_OLLAMA_BACKENDS = frozenset({"comfyui", "a1111", "automatic1111"})
ROLE_LABELS = {
    "general": "Chat",
    "coder": "Code",
    "review": "Review",
    "vision": "Vision",
    "image": "Image",
    "embed": "Memory embeddings",
}

# Optimized for: Ryzen 5600X, RX 7600 8GB VRAM, 62GB RAM, CPU/GPU hybrid via Ollama
# Quality preset uses 7B models so one Ollama model fits GPU VRAM alongside ComfyUI unload.
OPTIMIZED_STANDARD = {
    "general": "qwen2.5:7b",
    "coder": "qwen2.5-coder:7b",
    "review": "qwen2.5:7b",
    "vision": "moondream:latest",
    "image": "comfyui",
    "embed": "nomic-embed-text",
}

OPTIMIZED_UNCENSORED = {
    "general": "dolphin-mistral:latest",
    "coder": "qwen2.5-coder:7b",
    "review": "dolphin-mistral:latest",
    "vision": "moondream:latest",
    "image": "comfyui",
    "embed": "nomic-embed-text",
}

# Fast presets — 7B/light models for speed on RX 7600
FAST_STANDARD = {
    "general": "qwen2.5:7b",
    "coder": "qwen2.5-coder:7b",
    "review": "qwen2.5:7b",
    "vision": "moondream:latest",
    "image": "comfyui",
    "embed": "nomic-embed-text",
}

FAST_UNCENSORED = {
    "general": "dolphin-mistral:latest",
    "coder": "qwen2.5-coder:7b",
    "review": "dolphin-mistral:latest",
    "vision": "moondream:latest",
    "image": "comfyui",
    "embed": "nomic-embed-text",
}

PRESETS = {
    "quality": {"standard": OPTIMIZED_STANDARD, "uncensored": OPTIMIZED_UNCENSORED},
    "fast": {"standard": FAST_STANDARD, "uncensored": FAST_UNCENSORED},
}

# Fallback priority if optimized model not installed
FALLBACK_PRIORITY = {
    "general": [
        "qwen2.5:14b", "qwen2.5:7b", "llama3.1:8b", "gemma3:12b", "dolphin3:latest",
        "dolphin-mistral:latest", "mistral-nemo:latest", "qwen3:14b",
    ],
    "coder": [
        "qwen2.5-coder:14b", "deepseek-coder-v2:16b", "deepseek-coder-v2:latest",
        "coder-stable:latest", "devstral:latest", "qwen2.5-coder:7b",
    ],
    "review": [
        "deepseek-r1:14b", "qwen2.5:14b", "gemma3:12b", "dolphin3:latest",
    ],
    "vision": [
        "llava:13b", "moondream:latest", "moondream", "llama3.2-vision:11b",
    ],
    "image": [
        "comfyui",
    ],
    "embed": [
        "nomic-embed-text:latest", "nomic-embed-text",
    ],
}


def is_ollama_pullable(model: str) -> bool:
    name = (model or "").strip().lower()
    return bool(name) and name not in NON_OLLAMA_BACKENDS


def _installed() -> list[str]:
    ollama = check_ollama()
    return ollama.get("models", []) if ollama.get("running") else []


def _match_installed(preferred: str, installed: list[str]) -> str | None:
    if not preferred or not installed:
        return None
    pref_lower = preferred.lower()
    for name in installed:
        if name.lower() == pref_lower:
            return name
    pref_base = pref_lower.split(":")[0]
    for name in installed:
        if name.lower().startswith(pref_base):
            return name
    return None


def _pick_for_role(role: str, defaults: dict, installed: list[str]) -> str:
    preferred = defaults.get(role, "")
    match = _match_installed(preferred, installed)
    if match:
        return match
    for candidate in FALLBACK_PRIORITY.get(role, []):
        match = _match_installed(candidate, installed)
        if match:
            return match
    return preferred or "qwen2.5:7b"


def build_optimized_defaults(installed: list[str] | None = None) -> dict:
    installed = installed if installed is not None else _installed()
    return {
        "standard": {role: _pick_for_role(role, OPTIMIZED_STANDARD, installed) for role in ROLES},
        "uncensored": {role: _pick_for_role(role, OPTIMIZED_UNCENSORED, installed) for role in ROLES},
    }


def _load_raw() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_raw(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _saved_vision_model(data: dict, mode: str, installed: list[str]) -> str | None:
    """Return vision model from model_settings (matched to an installed tag if possible)."""
    if not data:
        return None
    saved = (data.get(mode) or {}).get("vision", "").strip()
    if not saved:
        return None
    matched = _match_installed(saved, installed)
    return matched or saved


def _vision_fallback_for_ollama(model: str, installed: list[str]) -> str:
    """Use moondream/llava when Ollama is too old for llama3.2-vision (mllama)."""
    from jarvis.ollama_health import requires_mllama, supports_mllama

    if not requires_mllama(model) or supports_mllama():
        return model
    for candidate in ("llava:13b", "llava", "moondream:latest", "moondream"):
        match = _match_installed(candidate, installed)
        if match:
            return match
    return model


def get_models() -> dict:
    """Active models for current mode (standard or uncensored)."""
    from jarvis.config import load_vision_quality
    from jarvis.gpu import is_low_vram

    data = _load_raw()
    mode = "uncensored" if is_uncensored() else "standard"
    optimized = build_optimized_defaults()
    installed = _installed()

    if not data:
        result = optimized[mode].copy()
    else:
        saved = data.get(mode, {})
        result = optimized[mode].copy()
        for role in ROLES:
            if role in saved and saved[role]:
                result[role] = saved[role]

    quality = load_vision_quality()
    if quality == "custom":
        user_vision = _saved_vision_model(data, mode, installed) if data else None
        if user_vision:
            result["vision"] = user_vision

    if quality == "quality":
        if is_low_vram():
            heavy = (
                _match_installed("llama3.2-vision:11b", installed)
                or _match_installed("llama3.2-vision", installed)
                or _match_installed("llava:13b", installed)
            )
        else:
            heavy = (
                _match_installed("llava:13b", installed)
                or _match_installed("llama3.2-vision:11b", installed)
                or _match_installed("llama3.2-vision", installed)
            )
        if heavy:
            result["vision"] = heavy
    elif quality == "fast":
        light = _match_installed("moondream:latest", installed) or _match_installed("moondream", installed)
        if light:
            result["vision"] = light
        elif is_low_vram() and "llava" in result.get("vision", "").lower():
            fallback = _match_installed("moondream:latest", installed)
            if fallback:
                result["vision"] = fallback

    result["vision"] = _vision_fallback_for_ollama(result.get("vision", ""), installed)
    return result


def get_all_settings() -> dict:
    data = _load_raw()
    optimized = build_optimized_defaults()
    installed = _installed()

    if not data:
        data = {
            "standard": optimized["standard"],
            "uncensored": optimized["uncensored"],
            "customized": False,
        }
        _save_raw(data)

    std = {**optimized["standard"], **data.get("standard", {})}
    unc = {**optimized["uncensored"], **data.get("uncensored", {})}
    active = get_models()

    # Build full choice list for GUI dropdowns (never empty)
    all_choices = set(installed)
    for preset in (std, unc, active, optimized["standard"], optimized["uncensored"]):
        all_choices.update(preset.values())
    for candidates in FALLBACK_PRIORITY.values():
        all_choices.update(candidates)
    all_choices.discard("")
    choices_sorted = sorted(all_choices, key=str.lower)

    return {
        "standard": std,
        "uncensored": unc,
        "active": active,
        "mode": "uncensored" if is_uncensored() else "standard",
        "installed": installed,
        "choices": choices_sorted,
        "role_choices": {
            role: (["comfyui"] if role == "image" else choices_sorted)
            for role in ROLES
        },
        "ollama_running": bool(installed),
        "optimized": optimized,
        "customized": data.get("customized", False),
        "hardware": {
            "gpu": "AMD RX 7600 (8GB VRAM)",
            "ram": "62GB",
            "cpu": "Ryzen 5 5600X",
            "note": "14B models use GPU + RAM offload. Use 7B variants for faster replies.",
        },
        "roles": {k: ROLE_LABELS[k] for k in ROLES},
        "presets": list(PRESETS.keys()),
        "missing_active": get_missing_models(),
    }


def update_models(mode: str, models: dict) -> dict:
    data = _load_raw()
    if not data:
        data = build_optimized_defaults()
        data["customized"] = False

    mode_key = "uncensored" if mode == "uncensored" else "standard"
    current = data.get(mode_key, build_optimized_defaults()[mode_key])
    for role in ROLES:
        if role in models and models[role]:
            current[role] = models[role].strip()
    data[mode_key] = current
    data["customized"] = True
    _save_raw(data)
    return get_all_settings()


def apply_preset(preset: str, mode: str | None = None) -> dict:
    """Apply fast or quality preset for current or given mode."""
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset: {preset}")

    mode_key = mode or ("uncensored" if is_uncensored() else "standard")
    if mode_key not in ("standard", "uncensored"):
        mode_key = "standard"

    raw_preset = PRESETS[preset][mode_key]
    installed = _installed()
    resolved = {
        role: _pick_for_role(role, raw_preset, installed)
        for role in ROLES
    }
    return update_models(mode_key, resolved)


def get_missing_models() -> list[str]:
    active = get_models()
    installed = _installed()
    from jarvis.ollama_health import models_missing

    required = [m for m in active.values() if is_ollama_pullable(m)]
    return models_missing(required, installed)


def reset_to_optimized(mode: str | None = None) -> dict:
    optimized = build_optimized_defaults()
    data = _load_raw() or {}
    if mode in ("standard", "uncensored"):
        data[mode] = optimized[mode]
    else:
        data["standard"] = optimized["standard"]
        data["uncensored"] = optimized["uncensored"]
        data["customized"] = False
    _save_raw(data)
    return get_all_settings()


def model_for(role: str) -> str:
    return get_models().get(role, OPTIMIZED_STANDARD.get(role, "qwen2.5:7b"))
