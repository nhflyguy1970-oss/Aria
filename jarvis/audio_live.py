"""Live recording sessions — VU meter + partial transcription."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
import uuid
from pathlib import Path

from jarvis.audio_device import (
    _is_creative_input,
    _ptt_record_cmd,
    effective_input_source,
    measure_peak_db,
    prepare_input_source,
)
from jarvis.config import DATA_DIR

SESSIONS: dict[str, dict] = {}
RECORDINGS_DIR = DATA_DIR / "audio" / "recordings"


def start_live_record(source: str | None = None) -> tuple[str, str]:
    """Start open-ended capture. Returns (session_id, dest_path)."""
    import shutil
    if not shutil.which("pw-record"):
        return "", "ERROR: pw-record not available"
    input_source = (source or effective_input_source()).strip()
    if not input_source:
        return "", "ERROR: No capture source"
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dest = RECORDINGS_DIR / f"live_{stamp}.wav"
    tmp = dest.with_name(dest.stem + "_raw.wav")
    stereo = _is_creative_input(input_source)
    if shutil.which("pactl"):
        prepare_input_source(input_source)
    proc = subprocess.Popen(
        _ptt_record_cmd(tmp, input_source, stereo=stereo),
        stderr=subprocess.PIPE,
        text=True,
    )
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = {
        "proc": proc,
        "tmp": tmp,
        "dest": dest,
        "source": input_source,
        "stereo": stereo,
        "partial_text": "",
        "peak_db": -60.0,
        "started": time.time(),
    }
    threading.Thread(target=_poll_session, args=(sid,), daemon=True).start()
    threading.Thread(target=_partial_transcribe_loop, args=(sid,), daemon=True).start()
    return sid, str(dest)


def _partial_transcribe_loop(sid: str) -> None:
    from jarvis.audio_whisper import transcribe

    entry = SESSIONS.get(sid)
    if not entry:
        return
    tmp: Path = entry["tmp"]
    last_size = 0
    partial_model = os.getenv("JARVIS_LIVE_PARTIAL_MODEL", "tiny").strip() or "tiny"
    interval = float(os.getenv("JARVIS_LIVE_PARTIAL_INTERVAL", "4.0"))
    while entry.get("proc") and entry["proc"].poll() is None:
        if tmp.exists():
            size = tmp.stat().st_size
            if size > 12000 and size - last_size > 8000:
                last_size = size
                text = transcribe(tmp, model=partial_model)
                if not text.startswith("ERROR:"):
                    entry["partial_text"] = text
        time.sleep(max(2.0, interval))


def _poll_session(sid: str) -> None:
    entry = SESSIONS.get(sid)
    if not entry:
        return
    tmp: Path = entry["tmp"]
    while entry.get("proc") and entry["proc"].poll() is None:
        if tmp.exists() and tmp.stat().st_size > 500:
            entry["peak_db"] = measure_peak_db(tmp) or entry.get("peak_db", -60)
        time.sleep(0.35)


def live_level(sid: str) -> dict:
    entry = SESSIONS.get(sid)
    if not entry:
        return {"ok": False, "message": "Unknown session"}
    return {
        "ok": True,
        "peak_db": entry.get("peak_db"),
        "partial_text": entry.get("partial_text", ""),
        "elapsed": round(time.time() - entry.get("started", time.time()), 1),
    }


def update_partial_transcript(sid: str, text: str) -> None:
    if sid in SESSIONS:
        SESSIONS[sid]["partial_text"] = text


def record_until_silence(
    *,
    max_sec: float = 8.0,
    silence_sec: float = 1.0,
    speech_threshold_db: float = -42.0,
    source: str | None = None,
) -> str:
    """Record until silence after speech, or max_sec — returns path or ERROR."""
    sid, path_or_err = start_live_record(source=source)
    if not sid:
        return path_or_err if path_or_err.startswith("ERROR:") else f"ERROR: {path_or_err}"

    speech_seen = False
    quiet_since: float | None = None
    deadline = time.time() + max(2.0, max_sec)
    poll = float(os.getenv("JARVIS_WAKEWORD_POLL_SEC", "0.12"))

    while time.time() < deadline:
        info = live_level(sid)
        peak = info.get("peak_db")
        if peak is None:
            peak = -60.0
        if peak >= speech_threshold_db:
            speech_seen = True
            quiet_since = None
        elif speech_seen:
            if quiet_since is None:
                quiet_since = time.time()
            elif time.time() - quiet_since >= silence_sec:
                break
        time.sleep(poll)

    return stop_live_record(sid)


def stop_live_record(sid: str) -> str:
    from jarvis.audio_device import _convert_to_whisper_wav, _finalize_recording

    entry = SESSIONS.pop(sid, None)
    if not entry:
        return "ERROR: Unknown session"
    proc = entry["proc"]
    tmp: Path = entry["tmp"]
    dest: Path = entry["dest"]
    source = entry["source"]
    stereo = entry["stereo"]
    try:
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=8)
    except Exception:
        proc.kill()
    if not tmp.exists() or tmp.stat().st_size < 500:
        tmp.unlink(missing_ok=True)
        return "ERROR: Recording too short"
    if stereo:
        ok, msg = _convert_to_whisper_wav(tmp, dest, 16000, source=source)
        tmp.unlink(missing_ok=True)
        if not ok:
            return f"ERROR: {msg}"
    elif tmp != dest:
        tmp.replace(dest)
    return _finalize_recording(dest, source, -45.0)
