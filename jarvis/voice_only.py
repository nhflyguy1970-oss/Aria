"""Voice-only demo — minimal assistant without the web GUI (P1 #34)."""

from __future__ import annotations

import logging
import os
import re
import signal
import sys
import threading
from typing import Any

log = logging.getLogger("jarvis.voice_only")

_stop = threading.Event()
_console_state = "idle"
_last_confirm_id: str | None = None


def prepare_voice_only_env() -> None:
    """Sensible defaults for headless voice demo."""
    os.environ.setdefault("JARVIS_VOICE_ONLY", "1")
    os.environ.setdefault("JARVIS_WAKEWORD_TO_CHAT", "1")
    os.environ.setdefault("JARVIS_WAKEWORD_SPEAK", "0")
    os.environ.setdefault("JARVIS_WAKEWORD_RECORD", "1")
    os.environ.setdefault("JARVIS_AUTO_PLAY", "1")
    os.environ.setdefault("JARVIS_NO_BROWSER", "1")


def strip_for_speech(text: str) -> str:
    """Remove markdown/code/citations so TTS sounds natural."""
    from jarvis.tts_stream import sanitize_for_speech

    return sanitize_for_speech(text)


def speak_max_chars() -> int:
    raw = os.getenv("JARVIS_VOICE_SPEAK_MAX_CHARS", "1200").strip()
    try:
        return max(80, min(int(raw), 4000))
    except ValueError:
        return 1200


def speak_text(text: str, *, assistant=None) -> str:
    """Generate Piper audio and play through the default sink."""
    from jarvis.events import emit_voice_state

    cleaned = strip_for_speech(text)
    if not cleaned:
        return ""
    limit = speak_max_chars()
    if len(cleaned) > limit:
        cleaned = cleaned[: limit - 3].rstrip() + "…"
    emit_voice_state("speaking", detail="voice-only")
    try:
        if assistant is None:
            from jarvis.assistant_instance import get_assistant

            assistant = get_assistant()
        path = assistant.audio.generate(cleaned, auto_play=True)
        if str(path).startswith("ERROR"):
            log.warning("TTS failed: %s", path)
            return ""
        return str(path)
    finally:
        emit_voice_state("idle")


def voice_chat_processor(message: str, voice: bool = True, *, assistant=None) -> dict[str, Any]:
    """Process one utterance and speak the reply (no GUI)."""
    global _last_confirm_id
    from jarvis.assistant_instance import get_assistant

    assistant = assistant or get_assistant()
    result = assistant.process(message, voice=True)
    reply = (result.get("message") or "").strip()
    if result.get("type") == "confirm_required":
        _last_confirm_id = (result.get("confirm_id") or "").strip() or None
        speak_text(
            "That action needs confirmation. Say yes to confirm, or no to cancel.",
            assistant=assistant,
        )
        return result
    _last_confirm_id = None
    if reply and result.get("ok", True):
        speak_text(reply, assistant=assistant)
    elif not result.get("ok", True) and reply:
        speak_text(reply, assistant=assistant)
    return result


def _console_voice_state(event: str = "", **payload: Any) -> None:
    global _console_state
    state = (payload.get("state") or "idle").strip().lower()
    detail = (payload.get("detail") or "").strip()
    if state == _console_state and not detail:
        return
    _console_state = state
    labels = {
        "idle": "○ idle",
        "listening": "● listening",
        "thinking": "◐ thinking",
        "speaking": "♪ speaking",
    }
    line = labels.get(state, state)
    if detail:
        line = f"{line} ({detail})"
    print(line, flush=True)


def _voice_on_detect(model: str, score: float) -> None:
    from jarvis.audio_wakeword import _start_record_after_detect, wakeword_phrase

    print(f"\n● {wakeword_phrase(model)} ({score:.0%})", flush=True)
    _start_record_after_detect(model, score)


def _execute_confirm(confirm_id: str, approved: bool, *, assistant) -> dict[str, Any]:
    from jarvis.action_log import log_event
    from jarvis.handlers.registry import call_action, has_action
    from jarvis.tool_permissions import pop_pending

    row = pop_pending(confirm_id)
    if not row:
        return {"ok": False, "message": "Confirm expired."}
    log_event(
        "tool_confirm",
        tool=row.get("tool"),
        action=row.get("action"),
        approved=approved,
        message=(row.get("message") or "")[:200],
    )
    if not approved:
        return {"ok": True, "message": "Cancelled."}
    action = row.get("action") or ""
    params = dict(row.get("params") or {})
    params["_confirmed"] = True
    message = row.get("message") or ""
    if has_action(action):
        return call_action(assistant, action, params, message)
    if action == "ha_control":
        return assistant._ha_control(params, message)
    if action == "ha_scene":
        return assistant._ha_scene(params, message)
    return {"ok": False, "message": f"Unknown confirmed action: {action}"}


def _handle_confirm_followup(text: str, assistant) -> bool:
    """If the last turn needs confirmation, accept yes/no by voice."""
    global _last_confirm_id
    if not _last_confirm_id:
        return False
    lower = text.strip().lower()
    if lower in ("yes", "yeah", "yep", "confirm", "do it", "go ahead", "approve"):
        result = _execute_confirm(_last_confirm_id, True, assistant=assistant)
        _last_confirm_id = None
        reply = (result.get("message") or "").strip()
        if reply:
            speak_text(reply, assistant=assistant)
        return True
    if lower in ("no", "nope", "cancel", "stop", "deny"):
        _execute_confirm(_last_confirm_id, False, assistant=assistant)
        _last_confirm_id = None
        speak_text("Cancelled.", assistant=assistant)
        return True
    return False


def process_utterance(text: str, *, assistant=None) -> dict[str, Any]:
    from jarvis.assistant_instance import get_assistant

    assistant = assistant or get_assistant()
    cleaned = (text or "").strip()
    if not cleaned:
        return {"ok": False, "message": "Empty transcript"}
    if _handle_confirm_followup(cleaned, assistant):
        return {"ok": True, "message": "confirmation handled"}
    return voice_chat_processor(cleaned, voice=True, assistant=assistant)


def run_ptt_loop(*, assistant=None) -> None:
    from jarvis.audio_live import record_until_silence
    from jarvis.events import emit_voice_state, on
    from jarvis.stt import transcribe

    if assistant is None:
        from jarvis.assistant_instance import get_assistant

        assistant = get_assistant()

    on("voice_state", _console_voice_state)
    print("Push-to-talk — press Enter, speak, then pause. Ctrl+C to quit.", flush=True)
    while not _stop.is_set():
        try:
            input("\n[Enter] listen… ")
        except (EOFError, KeyboardInterrupt):
            break
        if _stop.is_set():
            break
        emit_voice_state("listening", detail="ptt")
        audio_path = record_until_silence()
        if audio_path.startswith("ERROR:"):
            print(audio_path, flush=True)
            emit_voice_state("idle")
            continue
        text = transcribe(audio_path)
        if text.startswith("ERROR:"):
            print(text, flush=True)
            emit_voice_state("idle")
            continue
        print(f"You: {text}", flush=True)
        result = process_utterance(text, assistant=assistant)
        reply = (result.get("message") or "").strip()
        if reply:
            print(f"{assistant_name()}: {reply[:500]}", flush=True)


def run_wakeword_loop(*, assistant=None) -> None:
    from jarvis import audio_wakeword
    from jarvis.events import on

    if assistant is None:
        from jarvis.assistant_instance import get_assistant

        assistant = get_assistant()

    audio_wakeword.configure(chat_processor=voice_chat_processor)
    on("voice_state", _console_voice_state)

    phrase = audio_wakeword.wakeword_phrase()
    print(f"Wake word active — say “{phrase}”, then your request. Ctrl+C to quit.", flush=True)
    result = audio_wakeword.start_listener(on_detect=_voice_on_detect)
    if result.startswith("ERROR"):
        raise RuntimeError(result)
    print("○ idle (waiting for wake word)", flush=True)
    while not _stop.is_set():
        _stop.wait(0.5)


def run_once(text: str, *, assistant=None) -> dict[str, Any]:
    """Single command for scripting / smoke tests."""
    if assistant is None:
        from jarvis.assistant_instance import get_assistant

        assistant = get_assistant()
    print(f"You: {text}", flush=True)
    result = process_utterance(text, assistant=assistant)
    reply = (result.get("message") or "").strip()
    if reply:
        from jarvis.branding import assistant_name

        print(f"{assistant_name()}: {reply}", flush=True)
    return result


def assistant_name() -> str:
    from jarvis.branding import assistant_name as _name

    return _name()


def _install_signal_handlers() -> None:
    def _shutdown(signum, _frame):
        _stop.set()
        try:
            from jarvis import audio_wakeword

            audio_wakeword.stop_listener()
        except Exception:
            pass
        print("\nVoice demo stopped.", flush=True)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)


def run_voice_only(argv: list[str] | None = None) -> int:
    """Entry for `python main.py voice`. Returns process exit code."""
    from jarvis.env_loader import load_jarvis_env

    argv = list(argv or sys.argv[2:])
    load_jarvis_env()
    prepare_voice_only_env()

    once_text = ""
    force_ptt = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--ptt", "-p"):
            force_ptt = True
        elif arg in ("--once", "-1") and i + 1 < len(argv):
            once_text = argv[i + 1]
            i += 1
        elif arg in ("-h", "--help"):
            _print_help()
            return 0
        i += 1

    _install_signal_handlers()

    from jarvis.assistant import JarvisAssistant
    from jarvis.assistant_instance import set_assistant
    from jarvis.config import is_uncensored
    from jarvis.services import ensure_services

    name = assistant_name()
    print(f"\n{name} voice-only demo (no web GUI)\n", flush=True)

    ensure_services(pull_models=os.getenv("JARVIS_AUTO_PULL_MODELS", "1") != "0")
    assistant = JarvisAssistant(uncensored=is_uncensored())
    set_assistant(assistant)

    if os.getenv("JARVIS_FIRST_RUN_MODELS", "1") != "0":
        try:
            from jarvis.first_run_models import ensure_optional_models

            ensure_optional_models()
        except Exception as exc:
            log.debug("first-run model check skipped: %s", exc)

    if once_text:
        run_once(once_text, assistant=assistant)
        return 0

    use_wakeword = not force_ptt
    if use_wakeword:
        from jarvis.audio_wakeword import wakeword_available

        if not wakeword_available():
            print("Wake word unavailable — falling back to push-to-talk.", flush=True)
            use_wakeword = False

    try:
        if use_wakeword:
            run_wakeword_loop(assistant=assistant)
        else:
            run_ptt_loop(assistant=assistant)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", flush=True)
        return 1
    return 0


def _print_help() -> None:
    name = assistant_name()
    print(
        f"""
{name} voice-only demo (P1 #34) — minimal assistant without the web GUI.

Usage:
  python main.py voice              Wake word loop (fallback: push-to-talk)
  python main.py voice --ptt        Push-to-talk only (Enter to record)
  python main.py voice --once "…"   Single command, speak reply, exit

Environment:
  JARVIS_WAKEWORD_SPEAK=0           voice-only speaks via Piper (avoid double TTS)
  JARVIS_VOICE_SPEAK_MAX_CHARS=1200 Truncate long TTS
  JARVIS_WAKEWORD_MODEL=hey_jarvis  Wake phrase model
"""
    )
