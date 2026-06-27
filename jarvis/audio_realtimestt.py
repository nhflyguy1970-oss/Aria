"""RealTimeSTT adapter (optional pip install realtimestt)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.realtimestt")
RECORDINGS_DIR = DATA_DIR / "audio" / "recordings"


def available() -> bool:
    try:
        from RealtimeSTT import AudioToTextRecorder  # noqa: F401

        return True
    except ImportError:
        return False


def _model() -> str:
    return (
        os.getenv("JARVIS_WAKEWORD_WHISPER_MODEL")
        or os.getenv("JARVIS_WHISPER_MODEL")
        or "small"
    ).strip() or "small"


def _wav_to_pcm16(path: Path, *, sample_rate: int = 16000) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg required for RealTimeSTT file transcription")
    proc = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-f",
            "s16le",
            "pipe:1",
        ],
        capture_output=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or b"").decode(errors="replace") or "ffmpeg failed")
    return proc.stdout


def transcribe_file(path: str | Path, *, model: str | None = None, language: str | None = None) -> str:
    if not available():
        return "ERROR: RealTimeSTT not installed (pip install 'realtimestt[faster-whisper]')"
    from RealtimeSTT import AudioToTextRecorder

    p = Path(path)
    if not p.exists():
        return f"ERROR: File not found: {p}"
    model_name = (model or _model()).strip() or "small"
    lang = (language or "").strip()
    try:
        pcm = _wav_to_pcm16(p)
        recorder = AudioToTextRecorder(
            use_microphone=False,
            spinner=False,
            level=logging.ERROR,
            model=model_name,
            language=lang or "",
        )
        recorder.feed_audio(pcm, original_sample_rate=16000)
        text = (recorder.text() or "").strip()
        recorder.shutdown()
        return text or "ERROR: RealTimeSTT returned empty transcript"
    except Exception as exc:
        log.warning("RealTimeSTT file transcribe failed: %s", exc)
        return f"ERROR: {exc}"


def record_until_silence(
    *,
    max_sec: float = 8.0,
    silence_sec: float = 1.0,
    speech_threshold_db: float = -42.0,
    source: str | None = None,
) -> str:
    """Capture one utterance via RealTimeSTT microphone mode; returns .txt path."""
    del silence_sec, speech_threshold_db, source  # VAD handled by RealTimeSTT
    if not available():
        return "ERROR: RealTimeSTT not installed"
    from RealtimeSTT import AudioToTextRecorder

    model_name = _model()
    partial_holder: dict[str, str] = {"text": ""}
    result_holder: dict[str, str] = {"text": ""}
    error_holder: dict[str, str] = {}

    def on_partial(text: str) -> None:
        partial_holder["text"] = (text or "").strip()

    def _run(recorder) -> None:
        try:
            result_holder["text"] = (recorder.text() or "").strip()
        except Exception as exc:
            error_holder["error"] = str(exc)

    try:
        recorder = AudioToTextRecorder(
            enable_realtime_transcription=True,
            on_realtime_transcription_update=on_partial,
            spinner=False,
            level=logging.WARNING,
            model=model_name,
        )
    except Exception as exc:
        return f"ERROR: RealTimeSTT init failed: {exc}"

    thread = threading.Thread(target=_run, args=(recorder,), daemon=True, name="jarvis-rts-record")
    thread.start()
    thread.join(timeout=max(3.0, min(max_sec, 30.0)))
    try:
        recorder.shutdown()
    except Exception:
        pass

    text = (result_holder["text"] or partial_holder["text"] or "").strip()
    if error_holder.get("error") and not text:
        return f"ERROR: {error_holder['error']}"
    if not text:
        return "ERROR: RealTimeSTT: no speech detected"

    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    dest = RECORDINGS_DIR / f"rts_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    dest.write_text(text, encoding="utf-8")
    return str(dest)
