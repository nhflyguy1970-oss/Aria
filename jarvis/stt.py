"""Unified speech-to-text entry (Whisper or RealTimeSTT)."""

from __future__ import annotations

from pathlib import Path


def transcribe(path: str | Path, model: str | None = None, language: str | None = None) -> str:
    p = Path(path)
    if p.suffix.lower() == ".txt" and p.exists():
        return p.read_text(encoding="utf-8").strip()
    from jarvis.voice_settings import stt_backend

    if stt_backend() == "realtimestt":
        from jarvis.audio_realtimestt import available, transcribe_file

        if available():
            result = transcribe_file(p, model=model, language=language)
            if not result.startswith("ERROR:"):
                return result
    from jarvis.audio_whisper import transcribe as whisper_transcribe

    return whisper_transcribe(p, model=model, language=language)


def stt_status() -> dict:
    try:
        from jarvis.audio_realtimestt import available as rts_installed
    except Exception:
        def rts_installed() -> bool:
            return False

    from jarvis.p1_flags import realtime_stt_enabled
    from jarvis.voice_settings import stt_backend

    backend = stt_backend()
    flag_on = realtime_stt_enabled()
    rts_ready = flag_on and rts_installed()
    out: dict = {
        "backend": backend,
        "realtimestt_enabled": flag_on,
        "realtimestt": rts_installed(),
        "realtimestt_ready": rts_ready,
        "whisper": True,
    }
    if backend == "realtimestt":
        out["ok"] = rts_ready
        if not rts_ready:
            out["message"] = (
                "RealTimeSTT unavailable — set JARVIS_REALTIMESTT=1 and "
                "pip install 'realtimestt[faster-whisper]'"
            )
    else:
        from jarvis.audio_whisper import whisper_backend

        out["whisper_engine"] = whisper_backend()
        out["ok"] = whisper_backend() != "none"
    return out
