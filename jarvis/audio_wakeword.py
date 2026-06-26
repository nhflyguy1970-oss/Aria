"""Wake word listener via openwakeword (optional)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
import time
import uuid
from typing import Callable

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_WAKEWORD_MODEL = "hey_jarvis"
OWW_FRAME_SAMPLES = 1280  # 80 ms @ 16 kHz
OWW_FRAME_BYTES = OWW_FRAME_SAMPLES * 2

WAKEWORD_PHRASES = {
    "hey_jarvis": "Hey Jarvis",
    "alexa": "Alexa",
    "hey_mycroft": "Hey Mycroft",
}

_listener_thread: threading.Thread | None = None
_stop_flag = threading.Event()
_last_detection: dict = {}
_on_detect: Callable[[str, float], None] | None = None
_last_record_ts = 0.0
_active_record_session: str = ""
_listener_state: dict = {}
_chat_processor: Callable[[str], dict] | None = None


def configure(*, chat_processor: Callable[[str], dict] | None = None) -> None:
    """Register server-side chat handler (set from gui.server on startup)."""
    global _chat_processor
    if chat_processor is not None:
        _chat_processor = chat_processor


def wakeword_phrase(model: str | None = None) -> str:
    name = (model or os.getenv("JARVIS_WAKEWORD_MODEL", DEFAULT_WAKEWORD_MODEL)).strip()
    return WAKEWORD_PHRASES.get(name, name.replace("_", " "))


def wakeword_available() -> bool:
    try:
        import openwakeword  # noqa: F401
        import onnxruntime  # noqa: F401
    except ImportError:
        return False
    return bool(shutil.which("ffmpeg") or shutil.which("pw-record"))


def _model_path(model_name: str) -> str:
    import openwakeword

    entry = openwakeword.models.get(model_name)
    if not entry:
        known = ", ".join(sorted(openwakeword.models))
        raise ValueError(f"Unknown wake word model '{model_name}'. Known: {known}")
    path = entry.get("model_path", "")
    if not path or not os.path.isfile(path):
        raise ValueError(f"Wake word model file missing for '{model_name}'")
    return path


def load_wakeword_model(model_name: str | None = None):
    """Load openWakeWord model (v0.4+ API uses wakeword_model_paths)."""
    from openwakeword.model import Model

    name = (model_name or os.getenv("JARVIS_WAKEWORD_MODEL", DEFAULT_WAKEWORD_MODEL)).strip()
    return Model(wakeword_model_paths=[_model_path(name)])


def _start_wakeword_capture(source: str) -> subprocess.Popen:
    """16 kHz mono int16 PCM on stdout — matches openWakeWord examples."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return subprocess.Popen(
            [
                ffmpeg, "-hide_banner", "-loglevel", "error",
                "-f", "pulse", "-i", source,
                "-ar", "16000", "-ac", "1",
                "-f", "s16le", "pipe:1",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    if not shutil.which("pw-record"):
        raise RuntimeError("Need ffmpeg or pw-record for wake word capture")
    return subprocess.Popen(
        [
            "pw-record", "--target", source,
            "--rate", "16000", "--channels", "1",
            "--format", "s16", "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _iter_pcm_frames(raw: bytes, carry: bytearray) -> list[np.ndarray]:
    """Split raw s16le bytes into 1280-sample int16 frames for openWakeWord."""
    if raw:
        carry.extend(raw)
    frames: list[np.ndarray] = []
    while len(carry) >= OWW_FRAME_BYTES:
        chunk = bytes(carry[:OWW_FRAME_BYTES])
        del carry[:OWW_FRAME_BYTES]
        frames.append(np.frombuffer(chunk, dtype=np.int16).copy())
    return frames


def _update_input_levels(frame: np.ndarray) -> None:
    if frame.size == 0:
        return
    peak = int(np.max(np.abs(frame)))
    _listener_state["input_peak"] = peak
    _listener_state["input_db"] = round(20.0 * np.log10(peak / 32768.0 + 1e-9), 1)


def _wakeword_to_chat_enabled() -> bool:
    return os.getenv("JARVIS_WAKEWORD_TO_CHAT", "1").lower() in ("1", "true", "yes")


def _clean_wakeword_transcript(text: str) -> str:
    """Drop the wake phrase from the start of a Whisper transcript."""
    import re

    cleaned = re.sub(r"^(hey[\s,]*jarvis)[\s,.:!?-]*", "", text.strip(), flags=re.I).strip()
    return cleaned or text.strip()


def status() -> dict:
    running = _listener_thread is not None and _listener_thread.is_alive()
    input_db = _listener_state.get("input_db")
    if input_db is not None:
        input_db = float(input_db)
    return {
        "available": wakeword_available(),
        "running": running,
        "model": os.getenv("JARVIS_WAKEWORD_MODEL", DEFAULT_WAKEWORD_MODEL),
        "phrase": wakeword_phrase(),
        "record_on_detect": _record_on_detect_enabled(),
        "to_chat": _wakeword_to_chat_enabled(),
        "active_record_session": _active_record_session,
        "source": _listener_state.get("source"),
        "error": None if running else _listener_state.get("error"),
        "last_score": float(_listener_state.get("last_score", 0.0)),
        "input_db": input_db,
        "mic_live": bool(input_db is not None and input_db > -55),
        "last": dict(_last_detection),
    }


def _record_on_detect_enabled() -> bool:
    return os.getenv("JARVIS_WAKEWORD_RECORD", "1").lower() in ("1", "true", "yes")


def _wakeword_record_limits() -> tuple[float, float, float]:
    max_sec = float(os.getenv("JARVIS_WAKEWORD_RECORD_MAX_SEC", os.getenv("JARVIS_WAKEWORD_RECORD_SEC", "8")))
    silence = float(os.getenv("JARVIS_WAKEWORD_SILENCE_SEC", "0.9"))
    speech_db = float(os.getenv("JARVIS_WAKEWORD_SPEECH_DB", "-42"))
    return max(3.0, min(max_sec, 30.0)), max(0.4, min(silence, 3.0)), speech_db


def _dispatch_to_chat(payload: dict, chat_msg: str) -> None:
    """Run chat on the server and update payload for the GUI poller."""
    global _last_detection

    event_id = uuid.uuid4().hex[:12]
    payload["chat_event_id"] = event_id
    payload["chat_message"] = chat_msg
    payload["to_chat"] = True
    payload["chat_status"] = "pending"
    _last_detection = dict(payload)

    if not _chat_processor:
        payload["chat_status"] = "ready"
        _last_detection = dict(payload)
        return

    def _run() -> None:
        global _last_detection
        try:
            result = _chat_processor(chat_msg)
            _last_detection.update({
                "chat_status": "done",
                "chat_ok": result.get("ok", True),
                "chat_response": result.get("message", ""),
                "chat_module": result.get("module"),
                "chat_type": result.get("type"),
            })
            if os.getenv("JARVIS_WAKEWORD_SPEAK", "0") in ("1", "true", "yes"):
                reply = (result.get("message") or "").strip()
                if reply and result.get("ok", True):
                    try:
                        from jarvis.assistant_instance import get_assistant

                        get_assistant().audio.generate(reply[:800])
                    except Exception as exc:
                        logger.debug("Wake word TTS failed: %s", exc)
        except Exception as e:
            logger.warning("Wake word chat failed: %s", e)
            _last_detection.update({"chat_status": "error", "chat_error": str(e)})

    threading.Thread(target=_run, daemon=True, name="jarvis-wakeword-chat").start()


def _default_on_detect(model: str, score: float) -> None:
    """Desktop notify on wake word (used by GUI + daemon)."""
    try:
        subprocess.run(
            [
                "notify-send", "-a", "Jarvis",
                "Wake word",
                f'{wakeword_phrase(model)} ({score:.0%}) — listening…',
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except Exception:
        pass


def _start_record_after_detect(model: str, score: float) -> None:
    """Release wake-word mic and start a timed live capture + transcribe."""
    global _last_record_ts, _active_record_session, _last_detection

    if not _record_on_detect_enabled():
        return
    now = time.time()
    if now - _last_record_ts < 8:
        return
    _last_record_ts = now
    _stop_flag.set()

    def _run():
        global _active_record_session, _last_detection
        time.sleep(0.35)
        try:
            from jarvis.audio_live import record_until_silence

            max_sec, silence_sec, speech_db = _wakeword_record_limits()
            _last_detection = {
                "model": model,
                "score": score,
                "ts": time.time(),
                "action": "recording",
            }
            result = record_until_silence(
                max_sec=max_sec,
                silence_sec=silence_sec,
                speech_threshold_db=speech_db,
            )
            _active_record_session = ""
            payload = {
                "model": model,
                "score": score,
                "ts": time.time(),
                "action": "recorded",
                "audio_path": result if not result.startswith("ERROR:") else "",
            }
            if result.startswith("ERROR:"):
                payload["error"] = result
            else:
                try:
                    from jarvis.modules.audio import AudioEngine

                    whisper_model = os.getenv("JARVIS_WAKEWORD_WHISPER_MODEL", "small").strip() or "small"
                    text = AudioEngine().transcribe(result, model=whisper_model)
                    if text.startswith("ERROR:"):
                        payload["transcript_error"] = text
                        _last_detection = payload
                    else:
                        payload["transcript"] = text
                        chat_msg = _clean_wakeword_transcript(text)
                        if _wakeword_to_chat_enabled() and chat_msg:
                            _dispatch_to_chat(payload, chat_msg)
                        else:
                            payload["chat_message"] = chat_msg
                            _last_detection = payload
                except Exception as e:
                    payload["transcript_error"] = str(e)
                    _last_detection = payload
            try:
                chat_msg = _last_detection.get("chat_message") or _last_detection.get("transcript", "")
                if _last_detection.get("to_chat") and chat_msg:
                    msg = f"Chat: {chat_msg[:100]}"
                elif _last_detection.get("error"):
                    msg = str(_last_detection["error"])[:120]
                else:
                    msg = (_last_detection.get("transcript") or "Recording saved")[:120]
                subprocess.run(
                    ["notify-send", "-a", "Jarvis", "Jarvis heard you", msg],
                    check=False, timeout=3,
                )
            except Exception:
                pass
            start_listener()
        except Exception as e:
            _last_detection = {"model": model, "score": score, "ts": time.time(), "error": str(e)}
            start_listener()

    threading.Thread(target=_run, daemon=True, name="jarvis-wakeword-record").start()


def _combined_on_detect(model: str, score: float) -> None:
    global _last_detection
    _last_detection = {"model": model, "score": score, "ts": time.time()}
    _default_on_detect(model, score)
    _start_record_after_detect(model, score)


def start_listener(on_detect: Callable[[str, float], None] | None = None) -> str:
    global _listener_thread, _on_detect, _listener_state
    if not wakeword_available():
        return "ERROR: openwakeword not installed (pip install openwakeword onnxruntime)"
    if not shutil.which("ffmpeg") and not shutil.which("pw-record"):
        return "ERROR: ffmpeg or pw-record required for wake word capture"
    if _listener_thread and _listener_thread.is_alive():
        return "already running"
    _stop_flag.clear()
    _on_detect = on_detect or _combined_on_detect
    _listener_state = {
        "error": None,
        "source": None,
        "last_score": 0.0,
        "input_db": None,
        "input_peak": 0,
    }

    def _run():
        proc = None
        try:
            from jarvis.audio_device import effective_input_source, prepare_input_source

            model_name = os.getenv("JARVIS_WAKEWORD_MODEL", DEFAULT_WAKEWORD_MODEL)
            oww = load_wakeword_model(model_name)
            model_keys = list(oww.models.keys())
            src = effective_input_source()
            if not src:
                raise RuntimeError("No capture source configured — pick a mic in Audio settings")
            _listener_state["source"] = src
            prepare_input_source(src)
            proc = _start_wakeword_capture(src)
            time.sleep(0.2)
            if proc.poll() is not None:
                err = (proc.stderr.read().decode(errors="replace") if proc.stderr else "").strip()
                raise RuntimeError(err[-300:] or "Capture process exited immediately")

            threshold = float(os.getenv("JARVIS_WAKEWORD_THRESHOLD", "0.5"))
            patience_n = int(os.getenv("JARVIS_WAKEWORD_PATIENCE", "3"))
            patience = {k: patience_n for k in model_keys}
            thresholds = {k: threshold for k in model_keys}
            carry = bytearray()
            while not _stop_flag.is_set() and proc.stdout:
                raw = proc.stdout.read(OWW_FRAME_BYTES * 4)
                if not raw:
                    if proc.poll() is not None:
                        err = (proc.stderr.read().decode(errors="replace") if proc.stderr else "").strip()
                        raise RuntimeError(err[-300:] or "Capture stopped")
                    break
                for frame in _iter_pcm_frames(raw, carry):
                    _update_input_levels(frame)
                    pred = oww.predict(frame, patience=patience, threshold=thresholds)
                    for m, score in pred.items():
                        score_f = float(score)
                        _listener_state["last_score"] = max(_listener_state.get("last_score", 0.0), score_f)
                        if score_f >= threshold:
                            if _on_detect is not None:
                                _on_detect(m, score_f)
                            if _stop_flag.is_set():
                                break
        except Exception as e:
            _listener_state["error"] = str(e)
            logger.warning("Wake word listener stopped: %s", e)
        finally:
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()

    _listener_thread = threading.Thread(target=_run, daemon=True, name="jarvis-wakeword")
    _listener_thread.start()
    time.sleep(0.45)
    if _listener_state.get("error"):
        return f"ERROR: {_listener_state['error']}"
    if not (_listener_thread and _listener_thread.is_alive()):
        return f"ERROR: {_listener_state.get('error') or 'Wake word listener stopped immediately'}"
    return "ok"


def stop_listener() -> None:
    _stop_flag.set()
