"""One-shot RX 7600 / 8GB tuning — env, models, audio settings."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from jarvis.config import DATA_DIR, PROJECT_ROOT

# Models that fit 8GB VRAM (one heavy job at a time)
OLLAMA_8GB_PULL = (
    "qwen2.5:7b",
    "qwen2.5-coder:7b",
    "moondream:latest",
    "nomic-embed-text:latest",
    "dolphin-mistral:latest",
)

ENV_8GB_DEFAULTS: dict[str, str] = {
    "JARVIS_WHISPER_MODEL": "small",
    "JARVIS_WHISPER_DEVICE": "cpu",
    "JARVIS_WHISPER_COMPUTE": "int8",
    "JARVIS_VRAM_GUARD": "1",
    "JARVIS_TORCH_DEVICE": "cuda",
    "JARVIS_ROCM_GFX": "11.0.0",
    "HSA_OVERRIDE_GFX_VERSION": "11.0.0",
    "JARVIS_COMFYUI_INPAINT_MAX_DIM": "1024",
    "JARVIS_SONG_MODE": "auto",
    "JARVIS_SONG_VOCAL_DEVICE": "cpu",
    "OLLAMA_KEEP_ALIVE": "15m",
}


def patch_env_file(env_path: Path, updates: dict[str, str]) -> list[str]:
    """Set or append export KEY=\"value\" lines; never removes unrelated keys."""
    changed: list[str] = []
    text = env_path.read_text(encoding="utf-8") if env_path.is_file() else ""
    for key, value in updates.items():
        pattern = re.compile(rf'^export\s+{re.escape(key)}=.*$', re.MULTILINE)
        line = f'export {key}="{value}"'
        if pattern.search(text):
            new_text = pattern.sub(line, text)
            if new_text != text:
                changed.append(key)
            text = new_text
        else:
            if text and not text.endswith("\n"):
                text += "\n"
            text += f"\n# 8GB tune\n{line}\n"
            changed.append(key)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(text, encoding="utf-8")
    return changed


def apply_audio_settings(*, whisper_model: str = "small") -> None:
    from jarvis.audio_settings import save_settings

    save_settings({"whisper_model": whisper_model})


def apply_model_preset_fast() -> None:
    """Apply 8GB-safe models for both standard and uncensored modes."""
    from jarvis.model_store import apply_preset

    apply_preset("quality", "standard")
    apply_preset("quality", "uncensored")


def apply_work_profile() -> None:
    from jarvis.profiles import apply_profile

    apply_profile("work")


def prefetch_whisper(model: str = "small") -> str:
    """Download faster-whisper weights into cache."""
    try:
        from faster_whisper import WhisperModel

        WhisperModel(model, device="cpu", compute_type="int8")
        return f"Whisper '{model}' cached"
    except ImportError:
        return "faster-whisper not installed — using CLI whisper if available"
    except Exception as e:
        return f"Whisper prefetch: {e}"


def pull_ollama_models(models: tuple[str, ...] = OLLAMA_8GB_PULL) -> list[str]:
    pulled: list[str] = []
    for name in models:
        try:
            proc = subprocess.run(
                ["ollama", "pull", name],
                capture_output=True,
                text=True,
                timeout=3600,
            )
            if proc.returncode == 0:
                pulled.append(name)
        except Exception:
            pass
    return pulled


def run_optimizations(
    *,
    env_path: Path | None = None,
    pull_models: bool = True,
    prefetch_whisper_model: bool = True,
) -> dict:
    env_path = env_path or (DATA_DIR / "jarvis.env")
    env_changed = patch_env_file(env_path, ENV_8GB_DEFAULTS)
    apply_audio_settings(whisper_model="small")
    apply_model_preset_fast()
    whisper_msg = prefetch_whisper("small") if prefetch_whisper_model else "skipped"
    pulled = pull_ollama_models() if pull_models else []
    return {
        "ok": True,
        "env_path": str(env_path),
        "env_keys_updated": env_changed,
        "model_preset": "fast",
        "whisper_model": "small",
        "whisper_prefetch": whisper_msg,
        "ollama_pulled": pulled,
    }
