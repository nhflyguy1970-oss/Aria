"""Duplex voice helpers — barge-in and playback/listen coordination."""

from __future__ import annotations

from jarvis.voice_settings import duplex_mode, load_voice_settings

_DUPLEX_HELP = {
    "off": "Wake word ignored during TTS; no barge-in.",
    "half": "Wake or PTT stops playback, then listens (no mid-sentence interrupt).",
    "full": "Speak during TTS to barge-in; assistant turn truncated in memory.",
}


def duplex_status() -> dict:
    mode = duplex_mode()
    return {
        "mode": mode,
        "label": {
            "off": "Duplex off",
            "half": "Half duplex",
            "full": "Full duplex",
        }.get(mode, mode),
        "help": _DUPLEX_HELP.get(mode, ""),
        "barge_in": mode == "full",
        "stop_before_listen": mode != "full",
        "wake_during_playback": mode != "off",
        "interrupt_on_speak": bool(load_voice_settings().get("interrupt_on_speak", True)),
    }


def ignore_wake_during_playback() -> bool:
    return duplex_mode() == "off"


def before_listen() -> None:
    """Stop assistant playback before capture unless full-duplex barge-in is active."""
    if duplex_mode() == "full":
        return
    from jarvis.audio_device import stop_playback

    stop_playback()


def on_wake_during_playback() -> bool:
    """Whether a wake word hit during TTS should start capture."""
    mode = duplex_mode()
    if mode == "off":
        return False
    from jarvis.audio_device import stop_playback

    stop_playback()
    if mode == "half":
        try:
            from jarvis.events import emit_voice_state

            emit_voice_state("listening", detail="half-duplex-wake")
        except Exception:
            pass
    return True


def maybe_barge_in(peak_db: float | None = None, speech_threshold_db: float | None = None) -> bool:
    """Interrupt TTS when the user speaks during full-duplex playback."""
    if not load_voice_settings().get("interrupt_on_speak", True):
        return False
    if duplex_mode() != "full":
        return False
    from jarvis.audio_device import playback_active, stop_playback

    if not playback_active():
        return False
    if peak_db is not None and speech_threshold_db is not None and peak_db < speech_threshold_db:
        return False
    stop_playback()
    try:
        from jarvis.assistant_instance import get_assistant

        assistant = get_assistant()
        if assistant and assistant.conversation.truncate_last_assistant():
            assistant.branches.persist(session=assistant.session)
    except Exception:
        pass
    try:
        from jarvis.events import emit_voice_state

        emit_voice_state("listening", detail="barge-in")
    except Exception:
        pass
    return True
