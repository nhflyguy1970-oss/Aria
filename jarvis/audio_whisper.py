"""Transcription via faster-whisper (preferred) or Whisper CLI fallback."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterator

from jarvis.audio_device import ffmpeg_env
from jarvis.audio_settings import saved_whisper_language, saved_whisper_model
from jarvis.config import DATA_DIR

AUDIO_DIR = DATA_DIR / "audio"
_FW_MODEL: object | None = None
_FW_MODEL_KEY: str | None = None


def whisper_backend() -> str:
    try:
        import faster_whisper  # noqa: F401
        return "faster-whisper"
    except ImportError:
        pass
    return "cli" if shutil.which("whisper") else "none"


def _effective_language(language: str | None) -> str | None:
    """None means Whisper auto-detect."""
    lang = (
        language
        or saved_whisper_language()
        or os.getenv("JARVIS_WHISPER_LANGUAGE", "auto")
    ).strip().lower()
    if not lang or lang == "auto":
        return None
    return lang


def detect_language(path: str | Path, model: str | None = None) -> dict:
    """Detect spoken language (faster-whisper). Returns {ok, language, probability}."""
    model = (model or default_model()).strip() or "base"
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"File not found: {p}"}
    if whisper_backend() != "faster-whisper":
        return {"ok": False, "error": "Language detection needs faster-whisper"}
    try:
        fw = _get_fw_model(model)
        segments, info = fw.transcribe(str(p), language=None, beam_size=1, vad_filter=True)
        # consume one segment so detection runs
        for _ in segments:
            break
        lang = getattr(info, "language", None) or "unknown"
        prob = float(getattr(info, "language_probability", 0) or 0)
        return {"ok": True, "language": lang, "probability": round(prob, 3)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def default_model() -> str:
    saved = saved_whisper_model()
    if saved:
        return saved
    return os.getenv("JARVIS_WHISPER_MODEL", "base").strip() or "base"


def _cli_transcribe(path: Path, model: str, language: str | None) -> str:
    import hashlib

    whisper = shutil.which("whisper")
    if not whisper:
        return "ERROR: whisper not found. pip install openai-whisper or faster-whisper"

    transcript_dir = AUDIO_DIR / "transcripts" / hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
    transcript_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        whisper, str(path), "--model", model,
        "--output_dir", str(transcript_dir), "--output_format", "txt",
        "--task", "transcribe",
    ]
    if language and language != "auto":
        cmd.extend(["--language", language])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=ffmpeg_env())
    if result.returncode != 0:
        return f"ERROR: {result.stderr or result.stdout}"
    txt_path = transcript_dir / f"{path.stem}.txt"
    if txt_path.exists():
        return txt_path.read_text(encoding="utf-8").strip()
    return "ERROR: Transcription file not created"


def _get_fw_model(model: str):
    global _FW_MODEL, _FW_MODEL_KEY
    if _FW_MODEL is None or _FW_MODEL_KEY != model:
        from faster_whisper import WhisperModel

        from jarvis.torch_device import whisper_device

        device = whisper_device()
        compute = os.getenv("JARVIS_WHISPER_COMPUTE", "default")
        if device == "cpu" and compute == "default":
            compute = "int8"
        _FW_MODEL = WhisperModel(model, device=device, compute_type=compute)
        _FW_MODEL_KEY = model
    return _FW_MODEL


def _fw_transcribe(path: Path, model: str, language: str | None) -> str:
    fw = _get_fw_model(model)
    lang = None if not language or language == "auto" else language
    segments, _info = fw.transcribe(str(path), language=lang, beam_size=5, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()


def transcribe(path: str | Path, model: str | None = None, language: str | None = None) -> str:
    model = (model or default_model()).strip() or "base"
    p = Path(path)
    if not p.exists():
        return f"ERROR: File not found: {p}"
    lang = _effective_language(language)
    if whisper_backend() == "faster-whisper":
        try:
            return _fw_transcribe(p, model, lang)
        except Exception as e:
            cli = _cli_transcribe(p, model, lang)
            if not cli.startswith("ERROR:"):
                return cli
            return f"ERROR: {e}"
    return _cli_transcribe(p, model, lang)


def transcribe_stream_events(path: str | Path, model: str | None = None, language: str | None = None):
    """Yield SSE-ready dict events for streaming transcript UI."""
    for seg in transcribe_segments(path, model=model, language=language):
        if seg.get("final"):
            yield {"type": "done", "text": seg.get("text", "")}
        else:
            yield {
                "type": "segment",
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text", ""),
            }


def transcribe_segments(path: str | Path, model: str | None = None, language: str | None = None) -> Iterator[dict]:
    """Yield partial transcript segments for streaming UI."""
    model = (model or default_model()).strip() or "base"
    p = Path(path)
    lang_arg = _effective_language(language)
    if whisper_backend() != "faster-whisper":
        text = transcribe(p, model, lang_arg)
        yield {"text": text, "final": True}
        return
    fw = _get_fw_model(model)
    segments, _ = fw.transcribe(str(p), language=lang_arg, beam_size=5, vad_filter=True)
    for seg in segments:
        yield {"start": seg.start, "end": seg.end, "text": seg.text.strip(), "final": False}
    yield {"text": transcribe(p, model, lang_arg), "final": True}
