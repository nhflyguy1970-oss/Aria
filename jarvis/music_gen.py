"""Music generation via Hugging Face MusicGen (recommended) or AudioCraft (legacy)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable

from jarvis.config import DATA_DIR

MUSIC_DIR = DATA_DIR / "audio" / "music"

_HF_MODEL = None
_HF_PROCESSOR = None
_HF_MODEL_ID: str | None = None


def _transformers_available() -> bool:
    try:
        import scipy.io.wavfile  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _audiocraft_available() -> bool:
    try:
        import audiocraft  # noqa: F401
        return True
    except ImportError:
        return False


def musicgen_available() -> bool:
    return _transformers_available() or _audiocraft_available()


def musicgen_backend() -> str:
    if _transformers_available():
        return "transformers"
    if _audiocraft_available():
        return "audiocraft"
    return "none"


def install_hint() -> str:
    return "pip install transformers scipy accelerate  (torch already required for Whisper)"


def _generate_hf(
    prompt: str,
    duration: int,
    out_path: Path,
    *,
    on_progress: Callable[[int, str], None] | None = None,
    device: str | None = None,
) -> str:
    import scipy.io.wavfile
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    from jarvis.torch_device import torch_device

    global _HF_MODEL, _HF_PROCESSOR, _HF_MODEL_ID
    model_id = os.getenv("JARVIS_MUSICGEN_MODEL", "facebook/musicgen-small")
    dev_env = os.getenv("JARVIS_SONG_MUSIC_DEVICE", "auto").strip().lower()
    if device:
        dev = device
    elif dev_env in ("cpu", "cuda"):
        dev = dev_env
    else:
        dev = torch_device()

    if on_progress:
        on_progress(28, f"Loading MusicGen on {dev}…")
    if _HF_MODEL is None or _HF_MODEL_ID != model_id:
        _HF_PROCESSOR = AutoProcessor.from_pretrained(model_id)
        dtype = torch.float16 if dev != "cpu" and torch.cuda.is_available() else torch.float32
        loaded = MusicgenForConditionalGeneration.from_pretrained(model_id, torch_dtype=dtype)
        loaded.to(dev)  # type: ignore[arg-type]
        _HF_MODEL = loaded
        _HF_MODEL_ID = model_id
    model = _HF_MODEL
    processor = _HF_PROCESSOR
    assert model is not None and processor is not None
    if on_progress:
        hint = "first run downloads weights" if dev != "cpu" else "CPU mode — slow but uses RAM"
        on_progress(40, f"Generating music ({hint})…")
    inputs = processor(text=[prompt], padding=True, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    max_new_tokens = int(min(max(duration, 5), 30) * 50)
    with torch.inference_mode():
        audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)
    if on_progress:
        on_progress(62, "Saving music…")
    import numpy as np

    cfg = model.config
    sampling_rate = int(getattr(getattr(cfg, "audio_encoder", cfg), "sampling_rate", 32000))
    audio = audio_values[0, 0].detach().cpu().numpy()
    audio = np.clip(audio, -1.0, 1.0)
    scipy.io.wavfile.write(str(out_path), rate=sampling_rate, data=(audio * 32767).astype(np.int16))
    return str(out_path)


def unload_musicgen() -> None:
    """Drop cached MusicGen weights from VRAM."""
    global _HF_MODEL, _HF_PROCESSOR, _HF_MODEL_ID
    _HF_MODEL = None
    _HF_PROCESSOR = None
    _HF_MODEL_ID = None
    from jarvis.ml_memory import release_torch_memory

    release_torch_memory()


def _generate_audiocraft(prompt: str, duration: int, out_path: Path) -> str:
    import scipy.io.wavfile
    from audiocraft.models import MusicGen

    model_name = os.getenv("JARVIS_MUSICGEN_MODEL", "facebook/musicgen-small")
    model = MusicGen.get_pretrained(model_name)
    model.set_generation_params(duration=min(duration, 30))
    wav = model.generate([prompt])
    audio = wav[0].cpu().numpy().T
    scipy.io.wavfile.write(str(out_path), model.sample_rate, audio)
    return str(out_path)


def generate_music(
    prompt: str,
    duration: int = 10,
    output: str | None = None,
    *,
    on_progress: Callable[[int, str], None] | None = None,
    device: str | None = None,
) -> str:
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    if output:
        out_path = Path(output)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = MUSIC_DIR / f"music_{stamp}.wav"

    duration = min(max(int(duration), 5), 30)
    errors: list[str] = []

    from jarvis.vram_guard import prepare_for_torch_ml

    prepare_for_torch_ml()

    if _transformers_available():
        try:
            return _generate_hf(prompt, duration, out_path, on_progress=on_progress, device=device)
        except Exception as e:
            errors.append(f"transformers: {e}")

    if _audiocraft_available():
        try:
            return _generate_audiocraft(prompt, duration, out_path)
        except Exception as e:
            errors.append(f"audiocraft: {e}")

    manifest = {
        "prompt": prompt,
        "duration": duration,
        "created": datetime.now().isoformat(),
        "instructions": install_hint(),
    }
    manifest_path = out_path.with_suffix(".prompt.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    detail = f" ({'; '.join(errors)})" if errors else ""
    return (
        f"ERROR: MusicGen not installed ({install_hint()}).{detail} "
        f"Prompt saved to `{manifest_path}`"
    )
