"""Voice product boundaries."""

TERMINOLOGY = {
    "product": "Voice",
    "pipeline": "shared_conversation_pipeline",
}

BOUNDARIES = {
    "philosophy": (
        "Voice owns conversation I/O: listen, route, speak. "
        "Audio Studio owns production audio; Chat owns typed dialogue; Mission Control owns health."
    ),
    "owns": [
        "speech_to_text",
        "text_to_speech",
        "push_to_talk",
        "wake_word",
        "duplex",
        "voice_routing",
        "voice_profiles",
        "voice_settings",
        "cloud_live",
        "local_voice",
        "voice_pipeline",
    ],
    "does_not_own": [
        "audio_studio",
        "chat_conversation_ui",
        "memory",
        "documents",
        "mission_control",
        "gallery",
        "browser",
        "video",
        "image_generation",
        "daw_editing",
        "always_on_cloud_listening",
        "silent_memory_ingest",
        "fake_duplex",
    ],
}
