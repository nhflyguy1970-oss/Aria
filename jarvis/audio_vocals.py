"""Optional AI vocals — Bark (singing-ish) and Coqui XTTS (voice clone TTS)."""

from __future__ import annotations

import os
from pathlib import Path

from jarvis.config import DATA_DIR

VOCALS_DIR = DATA_DIR / "audio" / "vocals"
_BARK_MODEL = None
_BARK_USE_GPU: bool | None = None
_XTTS = None
_XTTS_DEVICE: str | None = None
_TTS_COMPAT_APPLIED = False


def _ensure_tts_transformers_compat() -> None:
    """coqui-tts 0.27.x imports isin_mps_friendly removed in transformers>=5.1."""
    global _TTS_COMPAT_APPLIED
    if _TTS_COMPAT_APPLIED:
        return
    try:
        import torch
        import transformers.pytorch_utils as pu

        if not hasattr(pu, "isin_mps_friendly"):
            def isin_mps_friendly(elements: torch.Tensor, test_elements: torch.Tensor | int) -> torch.Tensor:
                if elements.device.type == "mps":
                    test_elements = torch.tensor(test_elements, device=elements.device)
                    if test_elements.ndim == 0:
                        test_elements = test_elements.unsqueeze(0)
                    return (
                        elements.tile(test_elements.shape[0], 1)
                        .eq(test_elements.unsqueeze(1))
                        .sum(dim=0)
                        .bool()
                        .squeeze()
                    )
                return torch.isin(elements, test_elements)

            pu.isin_mps_friendly = isin_mps_friendly  # type: ignore[attr-defined]
        _TTS_COMPAT_APPLIED = True
    except ImportError:
        pass


def bark_available() -> bool:
    try:
        import numpy  # noqa: F401
        from bark import SAMPLE_RATE  # noqa: F401
        return True
    except ImportError:
        return False


def xtts_available() -> bool:
    try:
        _ensure_tts_transformers_compat()
        from TTS.api import TTS  # noqa: F401
        return True
    except ImportError:
        return False


def install_hint() -> str:
    parts = []
    if not bark_available():
        parts.append("Bark vocals: pip install git+https://github.com/suno-ai/bark.git")
    if not xtts_available():
        parts.append("XTTS clone: pip install coqui-tts")
    return " · ".join(parts) if parts else ""


def _lyrics_for_vocals(lyrics: str, max_chars: int = 520) -> str:
    """Keep vocal generation bounded on CPU (full lyrics can take 30+ minutes)."""
    text = lyrics.strip()
    if len(text) <= max_chars:
        return text
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    kept: list[str] = []
    total = 0
    for ln in lines:
        if total + len(ln) + 1 > max_chars:
            break
        kept.append(ln)
        total += len(ln) + 1
    return "\n".join(kept) if kept else text[:max_chars]


def _bark_text(lyrics: str) -> str:
    text = _lyrics_for_vocals(lyrics)
    if not text.startswith("♪") and "\n" in text:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        text = " ♪ ".join(lines[:12])
    if not text.startswith("♪"):
        text = f"♪ {text[:400]}"
    return text


def _get_bark(*, use_gpu: bool):
    global _BARK_MODEL, _BARK_USE_GPU
    if _BARK_MODEL is None or _BARK_USE_GPU != use_gpu:
        from bark import SAMPLE_RATE, generate_audio, preload_models

        preload_models(
            text_use_gpu=use_gpu,
            coarse_use_gpu=use_gpu,
            fine_use_gpu=use_gpu,
            codec_use_gpu=use_gpu,
            text_use_small=not use_gpu,
            coarse_use_small=not use_gpu,
            fine_use_small=not use_gpu,
            force_reload=True,
        )
        _BARK_MODEL = (generate_audio, SAMPLE_RATE)
        _BARK_USE_GPU = use_gpu
    return _BARK_MODEL


def generate_bark_vocals(
    lyrics: str,
    output: Path,
    *,
    voice_preset: str = "v2/en_speaker_6",
    device: str | None = None,
) -> str:
    """Generate sung/spoken vocals with Suno Bark."""
    if not bark_available():
        return "ERROR: Bark not installed"
    use_gpu = (device or os.getenv("JARVIS_SONG_VOCAL_DEVICE", "auto")).lower() == "cuda"
    try:
        import numpy as np
        import scipy.io.wavfile

        generate_audio, sample_rate = _get_bark(use_gpu=use_gpu)
        text = _bark_text(lyrics)
        audio = generate_audio(text, history_prompt=voice_preset)
        output.parent.mkdir(parents=True, exist_ok=True)
        arr = np.clip(np.asarray(audio), -1.0, 1.0)
        scipy.io.wavfile.write(str(output), sample_rate, (arr * 32767).astype(np.int16))
        return str(output)
    except Exception as e:
        return f"ERROR: Bark failed: {e}"


def generate_xtts(
    text: str,
    output: Path,
    *,
    speaker_wav: str | None = None,
    language: str = "en",
    device: str | None = None,
) -> str:
    """Coqui XTTS — clone voice from reference wav or default speaker."""
    if not xtts_available():
        return "ERROR: Coqui TTS not installed (pip install coqui-tts)"
    global _XTTS, _XTTS_DEVICE
    try:
        _ensure_tts_transformers_compat()
        from TTS.api import TTS

        from jarvis.torch_device import torch_device

        dev = device or os.getenv("JARVIS_SONG_VOCAL_DEVICE", "auto")
        if dev == "auto":
            dev = torch_device()
        if _XTTS is None or _XTTS_DEVICE != dev:
            model = os.getenv("JARVIS_XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
            _XTTS = TTS(model).to(dev)
            _XTTS_DEVICE = dev
        output.parent.mkdir(parents=True, exist_ok=True)
        snippet = _lyrics_for_vocals(text, max_chars=800)
        ref = speaker_wav or os.getenv("JARVIS_XTTS_SPEAKER_WAV", "")
        if ref and Path(ref).exists():
            _XTTS.tts_to_file(text=snippet, file_path=str(output), speaker_wav=ref, language=language)
        else:
            _XTTS.tts_to_file(text=snippet, file_path=str(output), language=language)
        return str(output)
    except Exception as e:
        return f"ERROR: XTTS failed: {e}"


def generate_vocals_for_song(
    lyrics: str,
    output: Path,
    *,
    engine: str = "auto",
    speaker_wav: str | None = None,
    device: str | None = None,
) -> str:
    """Best available vocal engine for song lyrics."""
    engine = (engine or os.getenv("JARVIS_VOCAL_ENGINE", "auto")).lower()
    if engine == "none":
        return "ERROR: Vocal engine disabled"
    if engine == "bark" or (engine == "auto" and bark_available()):
        r = generate_bark_vocals(lyrics, output, device=device)
        if not r.startswith("ERROR:"):
            return r
    if engine in ("xtts", "coqui", "auto") and xtts_available():
        return generate_xtts(lyrics, output, speaker_wav=speaker_wav, device=device)
    if bark_available():
        return generate_bark_vocals(lyrics, output, device=device)
    return f"ERROR: No vocal engine. {install_hint()}"


def unload_vocal_models() -> None:
    global _BARK_MODEL, _BARK_USE_GPU, _XTTS, _XTTS_DEVICE
    _BARK_MODEL = None
    _BARK_USE_GPU = None
    _XTTS = None
    _XTTS_DEVICE = None
    from jarvis.ml_memory import release_torch_memory

    release_torch_memory()
