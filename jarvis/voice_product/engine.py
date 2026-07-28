"""One Voice engine — STT → Intent → Assistant → Speech Policy → TTS → Activity."""

from __future__ import annotations

import logging
import threading
from typing import Any

log = logging.getLogger("jarvis.voice.engine")

_speak_lock = threading.Lock()


def stop_speaking() -> dict[str, Any]:
    from jarvis.tts_playback_queue import clear_tts_queue
    from jarvis.voice_product.status_bus import set_voice_state

    clear_tts_queue()
    set_voice_state("idle", detail="stopped")
    return {"ok": True, "stopped": True}


def speak_text(
    text: str,
    *,
    assistant=None,
    force: bool = False,
    source: str = "api",
    queue: bool = True,
) -> dict[str, Any]:
    """
    Shared TTS path for Chat speak, Voice CLI, wake, automation, and API.
    Uses chunked generation + playback queue when queue=True.
    """
    from jarvis.tts_stream import sanitize_for_speech, split_speak_chunks
    from jarvis.voice_product.settings import load_unified_settings
    from jarvis.voice_product.speech_policy import should_speak_reply
    from jarvis.voice_product.status_bus import set_voice_state

    if not should_speak_reply(force=force) and not force:
        return {"ok": True, "skipped": True, "reason": "speak_replies_off"}

    plain = sanitize_for_speech(text or "")
    if not plain:
        return {"ok": False, "message": "Empty speech text"}

    settings = load_unified_settings()
    if settings.get("interrupt_on_speak", True):
        stop_speaking()

    if assistant is None:
        try:
            from jarvis.assistant_instance import get_assistant

            assistant = get_assistant()
        except Exception:
            assistant = None
    if assistant is None:
        return {"ok": False, "message": "Assistant unavailable"}

    set_voice_state("speaking", detail=source)
    paths: list[str] = []
    try:
        with _speak_lock:
            use_chunks = bool(settings.get("speak_chunk_sentences", True)) and queue
            chunks = split_speak_chunks(plain) if use_chunks else [plain]
            if not chunks:
                chunks = [plain]
            from jarvis.tts_playback_queue import enqueue_play

            for chunk in chunks:
                path = assistant.audio.generate(chunk, auto_play=not queue)
                if str(path).startswith("ERROR"):
                    set_voice_state("error", detail=str(path), error=str(path))
                    return {"ok": False, "message": str(path), "paths": paths}
                paths.append(str(path))
                if queue:
                    enqueue_play(path)
        try:
            from jarvis.action_log import log_event

            log_event("voice_speak", source=source, chunks=len(paths), detail=plain[:120])
        except Exception:
            pass
        return {"ok": True, "audio_path": paths[-1] if paths else "", "paths": paths, "queued": queue}
    except Exception as exc:
        log.warning("speak_text failed: %s", exc)
        set_voice_state("error", detail=str(exc), error=str(exc))
        return {"ok": False, "message": str(exc)}
    finally:
        # Idle when not queued, or when queue already idle
        try:
            from jarvis.tts_playback_queue import tts_queue_busy

            if not queue or not tts_queue_busy():
                set_voice_state("idle", detail=source)
        except Exception:
            set_voice_state("idle", detail=source)


def process_utterance(
    text: str,
    *,
    assistant=None,
    source: str = "api",
    speak: bool | None = None,
) -> dict[str, Any]:
    """
    Shared conversation pipeline for PTT, wake, CLI, automation, and API.
    Intent router handles product commands; otherwise assistant processes.
    """
    from jarvis.voice_product.intent_router import apply_route, route_utterance
    from jarvis.voice_product.settings import speak_replies_enabled
    from jarvis.voice_product.status_bus import set_voice_state

    cleaned = (text or "").strip()
    if not cleaned:
        return {"ok": False, "message": "Empty transcript"}

    set_voice_state("thinking", detail=source)

    route = route_utterance(cleaned)
    if route:
        result = apply_route(route)
        reply = (result.get("reply") or "").strip()
        do_speak = speak if speak is not None else speak_replies_enabled()
        if reply and do_speak:
            speak_text(reply, assistant=assistant, force=True, source=source)
        else:
            set_voice_state("idle", detail=source)
        return {**result, "pipeline": "voice_engine", "source": source}

    # Confirmation + chat via shared helpers (never a separate voice pipeline)
    try:
        if speak is False:
            result = _assistant_only(cleaned, assistant=assistant)
            set_voice_state("idle", detail=source)
            return {**result, "pipeline": "voice_engine", "source": source, "spoken": False}

        result = _process_with_engine_speak(cleaned, assistant=assistant, source=source)
        return {**result, "pipeline": "voice_engine", "source": source}
    except Exception as exc:
        log.warning("process_utterance fallback: %s", exc)
        result = _assistant_only(cleaned, assistant=assistant)
        do_speak = speak if speak is not None else speak_replies_enabled()
        reply = (result.get("message") or "").strip()
        if reply and do_speak:
            speak_text(reply, assistant=assistant, force=True, source=source)
        else:
            set_voice_state("idle", detail=source)
        return {**result, "pipeline": "voice_engine", "source": source}


def _assistant_only(text: str, *, assistant=None) -> dict[str, Any]:
    from jarvis.assistant_instance import get_assistant

    assistant = assistant or get_assistant()
    return assistant.process(text, voice=True)


def _process_with_engine_speak(text: str, *, assistant=None, source: str = "api") -> dict[str, Any]:
    """Mirror voice_only confirmation + chat, speaking via engine."""
    from jarvis.assistant_instance import get_assistant
    from jarvis.voice_only import _handle_confirm_followup, _last_confirm_id

    assistant = assistant or get_assistant()
    if _handle_confirm_followup(text, assistant):
        return {"ok": True, "message": "confirmation handled"}

    result = assistant.process(text, voice=True)
    reply = (result.get("message") or "").strip()
    if result.get("type") == "confirm_required":
        speak_text(
            "That action needs confirmation. Say yes to confirm, or no to cancel.",
            assistant=assistant,
            force=True,
            source=source,
        )
        return result
    if reply:
        # Voice entry points speak by default; Chat auto-speak is gated by speak_replies.
        voice_entry = source in ("ptt", "wake", "cli", "automation", "api", "cloud", "voice")
        from jarvis.voice_product.settings import speak_replies_enabled

        if voice_entry or speak_replies_enabled():
            speak_text(reply, assistant=assistant, force=True, source=source)
        else:
            from jarvis.voice_product.status_bus import set_voice_state

            set_voice_state("idle", detail=source)
    else:
        from jarvis.voice_product.status_bus import set_voice_state

        set_voice_state("idle", detail=source)
    return result


def begin_listen(*, source: str = "ptt") -> None:
    """Shared listen start — duplex coordination + status."""
    from jarvis.voice_duplex import before_listen
    from jarvis.voice_product.status_bus import set_voice_state

    before_listen()
    set_voice_state("listening", detail=source)


def product_status() -> dict[str, Any]:
    from jarvis.voice_product.profiles import active_profile_id, list_profiles
    from jarvis.voice_product.recovery import diagnose
    from jarvis.voice_product.settings import load_unified_settings
    from jarvis.voice_product.status_bus import get_voice_state
    from jarvis.voice_product.terminology import BOUNDARIES, TERMINOLOGY

    try:
        from jarvis.voice_duplex import duplex_status

        duplex = duplex_status()
    except Exception:
        duplex = {}
    try:
        from jarvis.cloud_live_voice import cloud_live_status

        cloud = cloud_live_status()
    except Exception:
        cloud = {}
    try:
        from jarvis.tts_playback_queue import get_queue_status

        queue = get_queue_status()
    except Exception:
        queue = {}

    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "boundaries": BOUNDARIES,
        "state": get_voice_state(),
        "settings": load_unified_settings(),
        "duplex": duplex,
        "cloud_live": cloud,
        "queue": queue,
        "profiles": {"active": active_profile_id(), "count": len(list_profiles())},
        "recovery": diagnose(),
        "pipeline": [
            "entry",
            "stt",
            "intent_router",
            "assistant",
            "speech_policy",
            "tts",
            "audio_output",
            "activity",
            "completion",
        ],
    }
