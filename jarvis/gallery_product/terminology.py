"""Gallery product terminology and boundaries."""

TERMINOLOGY = {
    "product": "Gallery",
    "home": "Gallery Home",
    "engine": "Image Engine",
    "library": "Library",
    "generation": "Generation",
    "editing": "Editing",
}

BOUNDARIES = {
    "philosophy": (
        "Gallery is Aria's local AI image product — generate, browse, organize, "
        "and edit stills without being forced into Chat."
    ),
    "owns": [
        "image_generation",
        "generated_stills",
        "image_browsing",
        "image_editing",
        "prompt_history",
        "image_organization",
        "image_search",
        "local_image_workflows",
    ],
    "does_not_own": [
        "google_photos_clone",
        "cloud_sync",
        "documents",
        "memory",
        "chat_conversation",
        "video_studio",
        "meme_studio",
        "mission_control",
        "automatic_memory_ingestion",
        "second_generation_pipeline",
    ],
}
